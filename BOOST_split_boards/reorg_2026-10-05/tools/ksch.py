"""KiCad 10 schematic reader: placed symbols (with units and pin positions), wires, labels, junctions, and the
lib-symbol pin tables.  Shared by blocks.py and relayout_kicad.py.

Coordinates are schematic mm (y down). A lib pin at (px, py) (y up) of a symbol placed at (x, y) with rotation r and
mirror m sits at (x, y) + R(r) . M(m) . (px, -py), KiCad's convention.
"""
import re, math, collections

NL, TAB = chr(10), chr(9)


def blocks_of(text, kind, depth=1):
    """Top-level (depth 1) S-expression blocks '(kind ...' of a .kicad_sch: list of (start, end, text)."""
    out = []
    pat = NL + TAB * depth + '(' + kind
    i = 0
    while True:
        i = text.find(pat, i)
        if i < 0:
            return out
        j = i + 1
        # the block ends at the first line that is exactly the closing paren at this depth
        k = text.find(NL + TAB * depth + ')', j)
        if text[i + len(pat)] not in (NL, ' '):
            i = j
            continue
        out.append((i + 1, k + 2 + depth, text[i + 1:k + 2 + depth]))
        i = k


def num(s):
    return float(s)


class Sch:
    def __init__(self, path):
        self.path = path
        self.t = open(path, encoding='utf-8', newline='').read().replace('\r\n', NL)
        self.parse_lib()
        self.parse_items()

    # ------------------------------------------------------------------ lib symbols
    def parse_lib(self):
        t = self.t
        a = t.find(NL + TAB + '(lib_symbols')
        b = t.find(NL + TAB + ')', a)
        lib = t[a:b]
        self.lib = {}           # name -> {'units': {unit: [(num, name, x, y, ang, len, type)]}, 'nunits': n}
        for m in re.finditer(NL + TAB + TAB + r'\(symbol "([^"]+)"', lib):
            name = m.group(1)
            end = lib.find(NL + TAB + TAB + ')', m.end())
            body = lib[m.end():end]
            units = collections.defaultdict(list)
            for sm in re.finditer(NL + TAB * 3 + r'\(symbol "([^"]+)_(\d+)_(\d+)"', body):
                u = int(sm.group(2))
                send = body.find(NL + TAB * 3 + ')', sm.end())
                sb = body[sm.end():send]
                for pm in re.finditer(r'\(pin (\S+) (\S+)\s+\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s+\(length ([-\d.]+)\)(.*?)'
                                      r'\(name "([^"]*)"(.*?)\(number "([^"]*)"', sb, re.S):
                    hidden = '(hide yes)' in pm.group(7)
                    units[u].append(dict(num=pm.group(10), name=pm.group(8), x=num(pm.group(3)), y=num(pm.group(4)),
                                         ang=num(pm.group(5)), len=num(pm.group(6)), etype=pm.group(1), hidden=hidden))
            nunits = max([u for u in units] + [1])
            self.lib[name] = {'units': units, 'nunits': nunits}

    # ------------------------------------------------------------------ placed items
    def parse_items(self):
        t = self.t
        self.syms, self.wires, self.labels, self.junctions, self.noconn, self.texts = [], [], [], [], [], []
        for s, e, b in blocks_of(t, 'symbol'):
            lib_id = re.search(r'\(lib_id "([^"]+)"', b).group(1)
            at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', b)
            mir = re.search(r'\n\t\t\(mirror (\w)\)', b)
            unit = int(re.search(r'\n\t\t\(unit (\d+)\)', b).group(1))
            uuid = re.search(r'\n\t\t\(uuid "([^"]+)"\)', b).group(1)
            ref = re.search(r'\(property "Reference" "([^"]*)"', b).group(1)
            val = re.search(r'\(property "Value" "([^"]*)"', b).group(1)
            lib = self.lib.get(lib_id, {'units': {}, 'nunits': 1})
            self.syms.append(dict(start=s, end=e, text=b, lib_id=lib_id, x=num(at.group(1)), y=num(at.group(2)),
                                  rot=num(at.group(3)), mirror=mir.group(1) if mir else None, unit=unit, uuid=uuid,
                                  ref=ref, value=val, nunits=lib['nunits'],
                                  power=lib_id.startswith('power:') or ref.startswith('#')))
        for s, e, b in blocks_of(t, 'wire'):
            p = re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', b)
            self.wires.append(dict(start=s, end=e, text=b, x1=num(p[0][0]), y1=num(p[0][1]), x2=num(p[1][0]),
                                   y2=num(p[1][1])))
        for kind in ('global_label', 'label', 'hierarchical_label'):
            for s, e, b in blocks_of(t, kind):
                m = re.match(TAB + r'\(' + kind + r' "([^"]*)"', b)
                at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', b)
                self.labels.append(dict(start=s, end=e, text=b, kind=kind, name=m.group(1), x=num(at.group(1)),
                                        y=num(at.group(2)), rot=num(at.group(3))))
        for s, e, b in blocks_of(t, 'junction'):
            at = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', b)
            self.junctions.append(dict(start=s, end=e, text=b, x=num(at.group(1)), y=num(at.group(2))))
        for s, e, b in blocks_of(t, 'no_connect'):
            at = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', b)
            self.noconn.append(dict(start=s, end=e, text=b, x=num(at.group(1)), y=num(at.group(2))))
        for kind in ('text', 'text_box', 'rectangle', 'polyline', 'bus', 'bus_entry', 'image', 'sheet'):
            for s, e, b in blocks_of(t, kind):
                self.texts.append(dict(start=s, end=e, text=b, kind=kind))

    # ------------------------------------------------------------------ geometry
    def key(self, s):
        """Instance key: the reference, plus a unit letter for multi-unit parts (U101A); power symbols by uuid."""
        if s['power']:
            return s['uuid']
        return s['ref'] + (chr(64 + s['unit']) if s['nunits'] > 1 else '')

    def pins(self, s):
        """[(number, name, x, y, etype, hidden)] of a placed symbol (its unit's pins plus the common unit 0)."""
        lib = self.lib.get(s['lib_id'])
        if not lib:
            return []
        out = []
        for p in lib['units'].get(0, []) + (lib['units'].get(s['unit'], []) if s['unit'] else []):
            # rotate first (counter-clockwise on screen, y down), then mirror: checked on this schematic, where it
            # puts all 1048 visible pins on a wire end, label, junction, no-connect or another pin
            px, py = p['x'], -p['y']
            a = math.radians(-s['rot'])
            ca, sa = round(math.cos(a)), round(math.sin(a))
            rx, ry = px * ca - py * sa, px * sa + py * ca
            if s['mirror'] == 'x':
                ry = -ry
            elif s['mirror'] == 'y':
                rx = -rx
            out.append((p['num'], p['name'], round(s['x'] + rx, 4), round(s['y'] + ry, 4), p['etype'], p['hidden']))
        return out


def rnd(v):
    return round(v, 3)


def connectivity(sch):
    """Union-find over points: wire ends (and points on wire interiors), pins, label anchors, junctions.
    Returns (find, pin_point {(key, pinnum): point})."""
    par = {}

    def f(a):
        par.setdefault(a, a)
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    def u(a, b):
        par[f(a)] = f(b)

    pts = set()
    for w in sch.wires:
        pts.add((rnd(w['x1']), rnd(w['y1'])))
        pts.add((rnd(w['x2']), rnd(w['y2'])))
    for l in sch.labels:
        pts.add((rnd(l['x']), rnd(l['y'])))
    for j in sch.junctions:
        pts.add((rnd(j['x']), rnd(j['y'])))
    pin_point = {}
    for s in sch.syms:
        for n, name, x, y, et, hid in sch.pins(s):
            p = (rnd(x), rnd(y))
            pts.add(p)
            pin_point[(sch.key(s), n)] = p
    # index points by x and by y for the interior test
    byx, byy = collections.defaultdict(list), collections.defaultdict(list)
    for p in pts:
        byx[p[0]].append(p)
        byy[p[1]].append(p)
    for w in sch.wires:
        a, b = (rnd(w['x1']), rnd(w['y1'])), (rnd(w['x2']), rnd(w['y2']))
        u(a, b)
        if a[0] == b[0]:
            lo, hi = sorted((a[1], b[1]))
            for p in byx[a[0]]:
                if lo < p[1] < hi:
                    u(p, a)
        elif a[1] == b[1]:
            lo, hi = sorted((a[0], b[0]))
            for p in byy[a[1]]:
                if lo < p[0] < hi:
                    u(p, a)
    for p in pts:
        f(p)
    return f, pin_point
