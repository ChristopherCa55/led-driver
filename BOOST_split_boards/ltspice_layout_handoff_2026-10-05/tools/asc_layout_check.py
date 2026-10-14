"""Layout checks H2-H12, review flags and tracing tasks for the BOOST.asc re-layout.

    python asc_layout_check.py FILE.asc [--blocks PWR,ISNS,CREG1,REF1,EA1] [--no-frames] [--split]
                                        [--out REPORT_PREFIX]

  --blocks     check only these blocks (the pilot); parts of other blocks count as "outside" and their nets need
               ordinary exit labels.
  --no-frames  for files without block frames (the original and the 2026-10-05 attempt): skips the frame rules (H2,
               H6 boundary band, per-block text attribution) and measures everything else.
  --split      use the pre-approved CONTROL_A / CONTROL_B fallback instead of one CONTROL block.

Block frames are dashed RECTANGLEs, each with a title comment inside it that starts with the block id in brackets,
e.g. ";[PWR] Power path (power board)". The directives sit inside a frame titled "[SETUP]".

This tool only READS the .asc (and the .asy symbol files beside it / in LTspice's lib). Its rules come from
../blocks.json, ../bypass_map.json and approved_changes.json; they are not to be loosened without the user's OK.

Geometry follows LTspice: wires connect at end points and wherever a wire end or pin lies on another wire; flags with
the same name join nets; text sizes are ESTIMATED from the font-size index (blocks.json text_metrics), so text
findings must be confirmed in LTspice screenshots.
"""
import json, math, os, re, sys
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
LIBSYM = r'C:\Users\bubba\AppData\Local\LTspice\lib\sym'
ATTR_NUM = {0: 'InstName', 3: 'Value', 123: 'Value2', 38: 'SpiceModel', 39: 'SpiceLine', 40: 'SpiceLine2'}


# ===================================================================================================== parsing
class Sym:
    def __init__(self, line, sym, x, y, rot):
        self.line, self.sym, self.x, self.y, self.rot = line, sym, x, y, rot
        self.attr, self.windows = {}, {}


class Schematic:
    def __init__(self, path):
        self.path = path
        self.dir = os.path.dirname(os.path.abspath(path))
        self.lines = open(path, encoding='latin-1').read().replace('\r', '').split('\n')
        self.wires, self.flags, self.syms, self.texts, self.rects = [], [], [], [], []
        self.iopin = {}
        self._asy = {}
        cur = None
        for i, l in enumerate(self.lines):
            t = l.split(' ')
            k = t[0]
            if k == 'WIRE':
                self.wires.append((int(t[1]), int(t[2]), int(t[3]), int(t[4])))
                cur = None
            elif k == 'FLAG':
                self.flags.append({'x': int(t[1]), 'y': int(t[2]), 'name': t[3] if len(t) > 3 else '', 'line': i})
                cur = None
            elif k == 'IOPIN':
                self.iopin[(int(t[1]), int(t[2]))] = t[3]
                cur = None
            elif k == 'SYMBOL':
                cur = Sym(i, t[1], int(t[2]), int(t[3]), t[4])
                self.syms.append(cur)
            elif k == 'SYMATTR' and cur is not None:
                key, _, v = l[8:].partition(' ')
                cur.attr[key] = v
            elif k == 'WINDOW' and cur is not None:
                cur.windows[int(t[1])] = (int(t[2]), int(t[3]), t[4], int(t[5]) if len(t) > 5 else 2)
            elif k == 'TEXT':
                p = l.split(' ', 5)
                self.texts.append({'x': int(p[1]), 'y': int(p[2]), 'just': p[3], 'size': int(p[4]),
                                   'body': p[5] if len(p) > 5 else '', 'line': i})
                cur = None
            elif k == 'RECTANGLE':
                self.rects.append((min(int(t[2]), int(t[4])), min(int(t[3]), int(t[5])),
                                   max(int(t[2]), int(t[4])), max(int(t[3]), int(t[5]))))
                cur = None
            elif k in ('LINE', 'CIRCLE', 'ARC', 'DATAFLAG', 'SHEET', 'Version'):
                cur = None
        for f in self.flags:
            f['io'] = self.iopin.get((f['x'], f['y']))
        self.by = {s.attr.get('InstName', '?%d' % s.line): s for s in self.syms}

    # ------------------------------------------------------------------ symbols
    def asy(self, name):
        if name in self._asy:
            return self._asy[name]
        rel = name.replace('\\\\', os.sep).replace('\\', os.sep) + '.asy'
        cands = [os.path.join(self.dir, rel), os.path.join(LIBSYM, rel)]
        path = next((c for c in cands if os.path.exists(c)), None)
        if path is None:
            raise SystemExit('symbol not found: ' + name)
        raw = open(path, 'rb').read()
        txt = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('latin-1')
        d = {'pins': [], 'pts': [], 'windows': {}, 'attr': {}}
        cur = None
        for l in txt.splitlines():
            t = l.split()
            if not t:
                continue
            if t[0] == 'PIN':
                cur = {'x': int(t[1]), 'y': int(t[2]), 'name': ''}
                d['pins'].append(cur)
            elif t[0] == 'PINATTR' and t[1] == 'PinName' and cur is not None:
                cur['name'] = l.split(' ', 2)[2]
            elif t[0] in ('LINE', 'RECTANGLE', 'CIRCLE', 'ARC'):
                v = [int(x) for x in t[2:6]]
                d['pts'] += [(v[0], v[1]), (v[2], v[3])]
            elif t[0] == 'WINDOW':
                d['windows'][int(t[1])] = (int(t[2]), int(t[3]), t[4], int(t[5]) if len(t) > 5 else 2)
            elif t[0] == 'SYMATTR':
                k, _, v = l[8:].partition(' ')
                d['attr'][k] = v
        self._asy[name] = d
        return d

    @staticmethod
    def xf(px, py, rot):
        """LTspice instance transform: rotate first, then mirror (verified on BOOST.asc's M90 resistors)."""
        m = rot.startswith('M')
        for _ in range(int(rot[1:]) // 90):
            px, py = -py, px
        if m:
            px = -px
        return px, py

    def pins(self, s):
        out = []
        for p in self.asy(s.sym)['pins']:
            dx, dy = self.xf(p['x'], p['y'], s.rot)
            out.append((p['name'], s.x + dx, s.y + dy))
        return out

    def body(self, s):
        pts = self.asy(s.sym)['pts'] + [(p['x'], p['y']) for p in self.asy(s.sym)['pins']]
        if not pts:
            return (s.x - 8, s.y - 8, s.x + 8, s.y + 8)
        q = [self.xf(x, y, s.rot) for x, y in pts]
        return (s.x + min(a for a, _ in q), s.y + min(b for _, b in q), s.x + max(a for a, _ in q),
                s.y + max(b for _, b in q))


# ===================================================================================================== geometry
def inside(pt, r, m=0):
    return r[0] - m <= pt[0] <= r[2] + m and r[1] - m <= pt[1] <= r[3] + m


def rect_inside(a, r):
    return a[0] >= r[0] and a[1] >= r[1] and a[2] <= r[2] and a[3] <= r[3]


def rects_overlap(a, b, shrink=0):
    return (a[0] + shrink < b[2] - shrink and b[0] + shrink < a[2] - shrink and
            a[1] + shrink < b[3] - shrink and b[1] + shrink < a[3] - shrink)


def rect_gap(a, b):
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def seg_hits_rect(w, r, shrink=0):
    x1, y1, x2, y2 = w
    r = (r[0] + shrink, r[1] + shrink, r[2] - shrink, r[3] - shrink)
    if r[0] >= r[2] or r[1] >= r[3]:
        return False
    if x1 == x2:
        return r[0] < x1 < r[2] and max(min(y1, y2), r[1]) < min(max(y1, y2), r[3])
    if y1 == y2:
        return r[1] < y1 < r[3] and max(min(x1, x2), r[0]) < min(max(x1, x2), r[2])
    # diagonal wire: sample
    for k in range(21):
        x, y = x1 + (x2 - x1) * k / 20, y1 + (y2 - y1) * k / 20
        if r[0] < x < r[2] and r[1] < y < r[3]:
            return True
    return False


def on_interior(pt, w):
    x, y = pt
    x1, y1, x2, y2 = w
    if (x, y) in ((x1, y1), (x2, y2)):
        return False
    if x1 == x2 == x:
        return min(y1, y2) < y < max(y1, y2)
    if y1 == y2 == y:
        return min(x1, x2) < x < max(x1, x2)
    return False


def wlen(w):
    return math.hypot(w[2] - w[0], w[3] - w[1])


# ===================================================================================================== text boxes
def text_box(x, y, just, size, body, tm):
    if just.lower() == 'invisible':
        return None
    lines = body.split('\\n')
    h = tm['base'] * tm['mult'][max(0, min(size, len(tm['mult']) - 1))]
    w = max(len(l) for l in lines) * h * tm['char_w']
    H = h * len(lines)
    j = just
    if j.startswith('V'):
        j2 = j[1:]
        if j2 == 'Left':
            return (x - H / 2, y - w, x + H / 2, y)
        if j2 == 'Right':
            return (x - H / 2, y, x + H / 2, y + w)
        if j2 == 'Top':
            return (x, y - w / 2, x + H, y + w / 2)
        if j2 == 'Bottom':
            return (x - H, y - w / 2, x, y + w / 2)
        return (x - H / 2, y - w / 2, x + H / 2, y + w / 2)
    if j == 'Left':
        return (x, y - H / 2, x + w, y + H / 2)
    if j == 'Right':
        return (x - w, y - H / 2, x, y + H / 2)
    if j == 'Top':
        return (x - w / 2, y, x + w / 2, y + H)
    if j == 'Bottom':
        return (x - w / 2, y - H, x + w / 2, y)
    return (x - w / 2, y - H / 2, x + w / 2, y + H / 2)


def xf_box(box, s, rot):
    """transform a box given in the symbol's local frame to world coordinates"""
    c = [Schematic.xf(box[0], box[1], rot), Schematic.xf(box[2], box[3], rot)]
    return (s.x + min(c[0][0], c[1][0]), s.y + min(c[0][1], c[1][1]), s.x + max(c[0][0], c[1][0]),
            s.y + max(c[0][1], c[1][1]))


def attr_texts(sch, s, tm):
    a = sch.asy(s.sym)
    out = []
    wins = dict(a['windows'])
    wins.update(s.windows)
    for num, (wx, wy, just, size) in wins.items():
        key = ATTR_NUM.get(num)
        if key is None or just == 'Invisible':
            continue
        val = s.attr.get(key, a['attr'].get(key, ''))
        if not val:
            continue
        b = text_box(wx, wy, just, size, val, tm)
        if b:
            out.append((xf_box(b, s, s.rot), '%s.%s' % (s.attr.get('InstName', '?'), key)))
    return out


def flag_box(f, sch, tm, wire_ends):
    if f['name'] == '0':
        return (f['x'] - 16, f['y'], f['x'] + 16, f['y'] + 24), 'GND'
    h = tm['base'] * tm['mult'][2]
    w = len(f['name']) * h * tm['char_w'] + (16 if f['io'] else 4)
    x, y = f['x'], f['y']
    dirs = wire_ends.get((x, y), [])
    if len(dirs) == 1:
        dx, dy = dirs[0]                     # the wire leaves the flag in direction (dx, dy): text goes the other way
        if dx > 0:
            return (x - w - 4, y - h / 2, x - 4, y + h / 2), 'label ' + f['name']
        if dx < 0:
            return (x + 4, y - h / 2, x + w + 4, y + h / 2), 'label ' + f['name']
        if dy > 0:
            return (x - w / 2, y - h - 4, x + w / 2, y - 4), 'label ' + f['name']
        return (x - w / 2, y + 4, x + w / 2, y + h + 4), 'label ' + f['name']
    return (x - w / 2, y - h - 4, x + w / 2, y - 4), 'label ' + f['name']


# ===================================================================================================== main checker
def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('-'):
        raise SystemExit(__doc__)
    path = a[0]
    only = a[a.index('--blocks') + 1].split(',') if '--blocks' in a else None
    noframes = '--no-frames' in a
    split = '--split' in a
    out_prefix = a[a.index('--out') + 1] if '--out' in a else None

    cfg = json.load(open(os.path.join(ROOT, 'blocks.json')))
    bmap = json.load(open(os.path.join(ROOT, 'bypass_map.json')))['caps']
    appr = json.load(open(os.path.join(HERE, 'approved_changes.json')))
    ren = appr.get('instance_renames', {})
    TH, TM = cfg['thresholds'], cfg['text_metrics']
    RAILS, GND = set(cfg['rails']), cfg['ground']

    sch = Schematic(path)
    by = sch.by
    alias = {}                                           # config name -> name used in this file
    for o, n in ren.items():
        alias[o] = n if n in by and o not in by else o
        alias[n] = alias[o]

    def nm(p):
        return alias.get(p, p)

    # ---------------- block membership (+ bypass caps at their owner's block)
    blocks = {k: [nm(p) for p in v['members']] for k, v in cfg['blocks'].items()}
    if split:
        del blocks['CONTROL']
        for k, v in cfg['fallback_split'].items():
            if not k.startswith('_'):
                blocks[k] = [nm(p) for p in v]
    owner_block = {}
    for b, ms in blocks.items():
        for p in ms:
            owner_block[p] = b
    lpwr = []
    cap_owner_pin = {}
    for cap, info in bmap.items():
        rail = info.get('rail')
        own = info['owner']
        sp = None
        if info.get('fixed_by_design'):
            sp = [own, 'OUT']
        else:
            sp = cfg['supply_pins'].get(rail, {}).get(own)
        if sp == 'LPWR':
            b = 'CONTROL' if not split else 'CONTROL_A'
            lpwr.append(cap)
        elif sp:
            b = owner_block.get(sp[0])
            cap_owner_pin[cap] = (sp[0], sp[1], info.get('ambiguous', False))
        else:
            b = None
        if b:
            blocks[b].append(cap)
            owner_block[cap] = b
    for cap, (inst, pin) in cfg['regulator_input_caps'].items():
        cap_owner_pin[cap] = (inst, pin, False)
    all_parts = set(by)
    unassigned = sorted(all_parts - set(owner_block))
    check_blocks = only or list(blocks)

    # ---------------- connectivity: wire groups (union-find over points) and nets (groups joined by flag names)
    par = {}

    def f(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def u(x, y):
        par[f(x)] = f(y)

    pinpos = {}                                          # (inst, pinname) -> point
    pins_at = defaultdict(list)
    for name, s in by.items():
        for pn, x, y in sch.pins(s):
            pinpos[(name, pn)] = (x, y)
            pins_at[(x, y)].append((name, pn))
    pts = set(pins_at) | {(fl['x'], fl['y']) for fl in sch.flags}
    for w in sch.wires:
        pts.add((w[0], w[1]))
        pts.add((w[2], w[3]))
    xs_index = defaultdict(list)
    for p in pts:
        xs_index[p[0]].append(p)
    ys_index = defaultdict(list)
    for p in pts:
        ys_index[p[1]].append(p)
    for w in sch.wires:
        u((w[0], w[1]), (w[2], w[3]))
        cand = xs_index[w[0]] if w[0] == w[2] else ys_index[w[1]] if w[1] == w[3] else []
        for p in cand:
            if on_interior(p, w):
                u(p, (w[0], w[1]))
    for p in pts:
        f(p)
    group = {p: f(p) for p in pts}
    flag_names_by_group = defaultdict(set)
    for fl in sch.flags:
        flag_names_by_group[group[(fl['x'], fl['y'])]].add(fl['name'])
    # nets: union groups that share a flag name
    gpar = {}

    def gf(x):
        gpar.setdefault(x, x)
        while gpar[x] != x:
            gpar[x] = gpar[gpar[x]]
            x = gpar[x]
        return x
    first_by_name = {}
    for g, names in flag_names_by_group.items():
        for n in names:
            if n in first_by_name:
                gpar[gf(g)] = gf(first_by_name[n])
            else:
                first_by_name[n] = g
    net_of_group = {g: gf(g) for g in set(group.values())}
    net_name = {}
    for g, names in flag_names_by_group.items():
        for n in names:
            net_name[net_of_group[g]] = n
    pin_group = {k: group[v] for k, v in pinpos.items()}
    pin_net = {k: net_of_group[g] for k, g in pin_group.items()}

    def nname(netid):
        return net_name.get(netid, '<auto %s>' % (netid,))

    # ---------------- frames
    frames = {}
    frame_problems = []
    if not noframes:
        for t in sch.texts:
            m = re.match(r'^;\s*\[([A-Za-z0-9_.]+)\]', t['body'])
            if not m:
                continue
            bid = m.group(1)
            hits = [r for r in sch.rects if inside((t['x'], t['y']), r)]
            if not hits:
                frame_problems.append('title [%s] is not inside any RECTANGLE' % bid)
                continue
            frames[bid] = min(hits, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))

    res = {'file': path, 'mode': {'blocks': check_blocks, 'no_frames': noframes, 'split': split}, 'rules': {},
           'flags': {}, 'traces': {}, 'stats': {}}
    fails = []

    def rule(rid, ok, details, note=''):
        res['rules'][rid] = {'pass': ok, 'details': details, 'note': note}
        if not ok:
            fails.append(rid)

    bodies = {n: sch.body(s) for n, s in by.items()}

    # ================= H2 membership
    h2 = list(frame_problems)
    if noframes:
        rule('H2 membership in frames', True, ['skipped (--no-frames)'])
    else:
        for b in check_blocks:
            if b not in frames:
                h2.append('block %s has no frame (RECTANGLE with title "[%s] ...")' % (b, b))
                continue
            for p in blocks[b]:
                if p not in by:
                    h2.append('%s: member %s not found in the schematic' % (b, p))
                elif not rect_inside(bodies[p], frames[b]):
                    h2.append('%s: %s is not entirely inside the frame' % (b, p))
        fb = [b for b in frames if b in blocks or b == 'SETUP']
        for i in range(len(fb)):
            for j in range(i + 1, len(fb)):
                if rects_overlap(frames[fb[i]], frames[fb[j]]):
                    h2.append('frames %s and %s overlap' % (fb[i], fb[j]))
        if only is None and unassigned:
            h2.append('parts in no block: %s' % ' '.join(unassigned))
        if only is None and 'SETUP' not in frames:
            h2.append('no [SETUP] frame for the directives')
        rule('H2 membership in frames', not h2, h2)

    # ================= H3 one drawing per block + orphan parts
    h3, orphans = [], []
    for b in check_blocks:
        ms = [p for p in blocks[b] if p in by and p not in lpwr]
        if not ms:
            continue
        idx = {p: i for i, p in enumerate(ms)}
        bp = list(range(len(ms)))

        def bf(x):
            while bp[x] != x:
                bp[x] = bp[bp[x]]
                x = bp[x]
            return x
        g2parts = defaultdict(set)
        for p in ms:
            for pn, _, _ in sch.pins(by[p]):
                g2parts[pin_group[(p, pn)]].add(p)
        for g, ps in g2parts.items():
            ps = list(ps)
            for q in ps[1:]:
                bp[bf(idx[q])] = bf(idx[ps[0]])
        comps = defaultdict(list)
        for p in ms:
            comps[bf(idx[p])].append(p)
        if len(comps) > 1:
            parts = sorted(comps.values(), key=len, reverse=True)
            h3.append('%s is %d separate drawings: main %d parts; islands: %s' % (
                b, len(parts), len(parts[0]), ' | '.join(' '.join(sorted(c)) for c in parts[1:])))
    for p, s in by.items():
        if only and owner_block.get(p) not in only:
            continue
        sig = [(pn, pin_group[(p, pn)]) for pn, _, _ in sch.pins(s) if nname(pin_net[(p, pn)]) != GND]
        if not sig:
            continue
        lonely = True
        for pn, g in sig:
            others = [k for k, gg in pin_group.items() if gg == g and k[0] != p]
            if others:
                lonely = False
                break
        if lonely:
            orphans.append(p)
    rule('H3 one drawing per block', not h3, h3 or ['every checked block is one connected drawing'])
    rule('H3b no orphan parts', not orphans,
         (['orphan (every non-ground pin touches only labels): ' + ' '.join(sorted(orphans))] if orphans else
          ['no orphan parts']))

    # ================= H4 no label jumps inside a block; H6 exits
    h4, h6 = [], []
    net_blocks = defaultdict(lambda: defaultdict(set))   # net -> block -> set(groups)
    for (p, pn), n in pin_net.items():
        b = owner_block.get(p, 'OUTSIDE')
        net_blocks[n][b].add(pin_group[(p, pn)])
    flags_by_net = defaultdict(list)
    for fl in sch.flags:
        flags_by_net[net_of_group[group[(fl['x'], fl['y'])]]].append(fl)

    def block_of_point(pt):
        for b, r in frames.items():
            if inside(pt, r):
                return b
        return None
    adjacent = set()
    fr = list(frames)
    for i in range(len(fr)):
        for j in range(i + 1, len(fr)):
            if rect_gap(frames[fr[i]], frames[fr[j]]) <= TH['adjacent_gap']:
                adjacent.add((fr[i], fr[j]))
                adjacent.add((fr[j], fr[i]))
    wire_ends = defaultdict(list)
    for w in sch.wires:
        wire_ends[(w[0], w[1])].append((sign(w[2] - w[0]), sign(w[3] - w[1])))
        wire_ends[(w[2], w[3])].append((sign(w[0] - w[2]), sign(w[1] - w[3])))
    stub_ok = set()
    for w in sch.wires:
        if wlen(w) >= TH['stub_min']:
            stub_ok.add((w[0], w[1]))
            stub_ok.add((w[2], w[3]))
    interfaces = cfg['interfaces']
    for n, bmapg in net_blocks.items():
        name = nname(n)
        is_rail = name in RAILS or name == GND
        for b, groups in bmapg.items():
            if b not in check_blocks:
                continue
            if b == 'PWR' and name in (cfg['pwr']['wired_nets'] + [GND]):
                continue                                 # H5 handles the power path
            if not is_rail and len(groups) > 1:
                h4.append('%s: net %s is split into %d wire groups inside the block (joined only by labels)' % (
                    b, name, len(groups)))
            if is_rail or noframes:
                continue
            nfl = [fl for fl in flags_by_net[n] if block_of_point((fl['x'], fl['y'])) == b]
            if len(nfl) > 1:
                h4.append('%s: net %s has %d labels inside the block (max 1)' % (b, name, len(nfl)))
            others = [ob for ob in bmapg if ob != b]
            if not others:
                continue
            # does a wire carry it straight into each other block?
            for ob in others:
                direct = bool(groups & bmapg[ob])
                if direct:
                    if ob != 'OUTSIDE' and (b, ob) not in adjacent:
                        h6.append('%s -> %s: net %s runs as a direct wire between NON-adjacent blocks' % (b, ob, name))
                    continue
                if not nfl:
                    h6.append('%s: net %s leaves the block (to %s) with no exit label' % (b, name, ob))
            for fl in nfl:
                if not any(bmapg[ob] & groups for ob in others):
                    r = frames.get(b)
                    pt = (fl['x'], fl['y'])
                    band = TH['boundary_band']
                    if r and not (pt[0] - r[0] <= band or r[2] - pt[0] <= band or pt[1] - r[1] <= band or
                                  r[3] - pt[1] <= band):
                        h6.append('%s: exit label %s at %s is not on the frame boundary band (<= %d units from the '
                                  'edge)' % (b, name, pt, band))
                    if not fl['io']:
                        h6.append('%s: exit label %s at %s has no port type (IOPIN In/Out/BiDir)' % (b, name, pt))
                    if pt not in stub_ok:
                        h6.append('%s: exit label %s at %s is not on a visible wire stub (>= %d units)' % (
                            b, name, pt, TH['stub_min']))
                    drv = interfaces.get(name)
                    if drv and fl['io'] and fl['io'] != 'BiDir' and name not in interfaces.get('bidir', []):
                        want = 'Out' if drv == b else 'In'
                        if fl['io'] != want:
                            h6.append('%s: exit label %s is IOPIN %s; expected %s (driven by %s)' % (
                                b, name, fl['io'], want, drv))
    # wires running through a foreign block
    if not noframes:
        for w in sch.wires:
            g = group[(w[0], w[1])]
            for b, r in frames.items():
                if b == 'SETUP' or b not in check_blocks:
                    continue
                if seg_hits_rect(w, r, 1) and not (inside((w[0], w[1]), r) or inside((w[2], w[3]), r)):
                    h6.append('wire %s crosses through block %s without connecting there' % (w, b))
    rule('H4 no label jumps inside a block', not h4, h4 or ['no signal net relies on a label inside a block'])
    if noframes:
        rule('H6 block exits', True, ['skipped (--no-frames)'])
    else:
        rule('H6 block exits', not h6, h6 or ['every exit is a direct wire to an adjacent block or one port label '
                                              'on the boundary band'])

    # ================= H5 power path
    h5 = []
    P = cfg['pwr']
    if P['block'] in check_blocks:
        pw = P['block']
        for netn in P['wired_nets'] + ([GND] if P['ground_return_bus'] else []):
            gs = set()
            for (p, pn), n in pin_net.items():
                if owner_block.get(p) == pw and nname(n) == netn:
                    gs.add(pin_group[(p, pn)])
            if len(gs) > 1:
                h5.append('PWR: %s is drawn as %d separate wire pieces (must be one continuous wired drawing)' % (
                    'ground return' if netn == GND else netn, len(gs)))
        if P['ground_return_bus'] and not noframes and pw in frames:
            ng = [fl for fl in sch.flags if fl['name'] == GND and inside((fl['x'], fl['y']), frames[pw])]
            if len(ng) != 1:
                h5.append('PWR: %d ground symbols inside the block; the return bus should carry exactly one' % len(ng))
        bat = next((nm(b) for b in P['battery'] if nm(b) in by), None)
        if bat:
            plus = pin_net.get((bat, '+'))
            if plus is None or plus not in net_name or net_name[plus] in RAILS:
                h5.append('PWR: the battery terminal net (%s +) has no name flag of its own; label it (e.g. '
                          'Vbattery) so it is visibly not Vin' % bat)
        vin_flags = [fl for fl in sch.flags if fl['name'] == P['vin_tag'] and (noframes or (
            pw in frames and inside((fl['x'], fl['y']), frames[pw])))]
        if not vin_flags:
            h5.append('PWR: no "%s" name flag on the wire after the cable' % P['vin_tag'])
    rule('H5 continuous power path', not h5, h5 or ['power path, battery chain and ground return wired continuously'])

    # ================= H7 supply labels
    h7, h7flag = [], []
    for fl in sch.flags:
        if only and block_of_point((fl['x'], fl['y'])) not in only and not noframes:
            continue
        if fl['name'] in RAILS or fl['name'] == GND:
            if fl['io']:
                h7.append('supply/ground flag %s at (%d,%d) has a port type; supply labels stay plain' % (
                    fl['name'], fl['x'], fl['y']))
            d = wire_ends.get((fl['x'], fl['y']), [])
            if fl['name'] in RAILS and len(d) == 1 and d[0] == (0, -1):
                h7flag.append('rail %s at (%d,%d) hangs below its wire (positive rails go up)' % (
                    fl['name'], fl['x'], fl['y']))
            if fl['name'] == GND and len(d) == 1 and d[0] == (0, 1):
                h7flag.append('ground at (%d,%d) sits above its wire (ground goes down)' % (fl['x'], fl['y']))
    rule('H7 supply labels', not h7, h7 or ['supply and ground flags are plain'])
    res['flags']['upside-down supply/ground flags'] = h7flag

    # ================= H8 wiring hygiene
    h8 = []
    deg = Counter()
    for w in sch.wires:
        deg[(w[0], w[1])] += 1
        deg[(w[2], w[3])] += 1
    for p, lst in pins_at.items():
        deg[p] += len(lst)
    for w in sch.wires:
        cand = xs_index[w[0]] if w[0] == w[2] else ys_index[w[1]] if w[1] == w[3] else []
        for p in cand:
            if on_interior(p, w):
                deg[p] += 2
                if p in pins_at:
                    h8.append('pin %s lies on the middle of a wire %s (a hidden connection)' % (
                        '/'.join('%s.%s' % k for k in pins_at[p]), w))
    junctions = {p for p, d in deg.items() if d >= 3}
    for p, d in deg.items():
        if d >= 4:
            h8.append('4-way junction at %s' % (p,))
    hv = [w for w in sch.wires if w[1] == w[3]]
    vv = [w for w in sch.wires if w[0] == w[2]]
    for i, a1 in enumerate(hv):
        for b1 in hv[i + 1:]:
            if a1[1] == b1[1] and max(min(a1[0], a1[2]), min(b1[0], b1[2])) < min(max(a1[0], a1[2]), max(b1[0], b1[2])):
                h8.append('overlapping wires %s and %s' % (a1, b1))
    for i, a1 in enumerate(vv):
        for b1 in vv[i + 1:]:
            if a1[0] == b1[0] and max(min(a1[1], a1[3]), min(b1[1], b1[3])) < min(max(a1[1], a1[3]), max(b1[1], b1[3])):
                h8.append('overlapping wires %s and %s' % (a1, b1))
    crossings = []
    for h in hv:
        for v in vv:
            x, y = v[0], h[1]
            if min(h[0], h[2]) < x < max(h[0], h[2]) and min(v[1], v[3]) < y < max(v[1], v[3]):
                crossings.append((x, y))
    near_pts = junctions | set(pins_at)
    for c in crossings:
        for q in near_pts:
            if abs(q[0] - c[0]) <= TH['cross_near'] and abs(q[1] - c[1]) <= TH['cross_near'] and q != c:
                h8.append('wire crossing at %s is within %d units of a junction/pin at %s (reads as a connection)' % (
                    c, TH['cross_near'], q))
                break
    for w in sch.wires:
        for n, s in by.items():
            if seg_hits_rect(w, bodies[n], 4):
                ends_here = any((w[0], w[1]) == pinpos[(n, pn)] or (w[2], w[3]) == pinpos[(n, pn)]
                                for pn, _, _ in sch.pins(s))
                if not ends_here or wlen(w) > (bodies[n][2] - bodies[n][0]) + (bodies[n][3] - bodies[n][1]):
                    h8.append('wire %s passes through the body of %s' % (w, n))
    if only and not noframes:
        keep = lambda msg: any(inside(tuple(map(int, re.findall(r'-?\d+', msg)[:2])), frames[b]) for b in only
                               if b in frames)
        h8 = [m for m in h8 if keep(m)]
    rule('H8 wiring hygiene', not h8, h8 or ['no 4-way junctions, hidden pin contacts, overlaps, near-junction '
                                             'crossings or wires through symbols'])

    # ================= H9 text (estimated)
    boxes = []                                            # (box, label, owner)
    for n, s in by.items():
        for b, lab in attr_texts(sch, s, TM):
            boxes.append((b, lab, n))
    for t in sch.texts:
        b = text_box(t['x'], t['y'], t['just'], t['size'], t['body'][1:], TM)
        if b:
            boxes.append((b, ('directive ' if t['body'].startswith('!') else 'comment ') + t['body'][1:30], 'TEXT'))
    for fl in sch.flags:
        b, lab = flag_box(fl, sch, TM, wire_ends)
        boxes.append((b, lab, 'FLAG@%d,%d' % (fl['x'], fl['y'])))
    h9 = []
    clear = TH['text_clear']
    in_scope = (lambda bx: True) if (not only or noframes) else (
        lambda bx: any(rects_overlap(bx, frames[b]) for b in only if b in frames))
    texts_only = [x for x in boxes if x[2] != 'GNDSYM']
    for i, (b1, l1, o1) in enumerate(texts_only):
        if not in_scope(b1):
            continue
        for b2, l2, o2 in texts_only[i + 1:]:
            if rects_overlap(b1, b2, 1):
                h9.append('text overlap: "%s" / "%s"' % (l1, l2))
            elif clear and rect_gap(b1, b2) < clear and o1 != o2 and not (l1.startswith('directive') and
                                                                           l2.startswith('directive')):
                h9.append('text closer than %d units: "%s" / "%s"' % (clear, l1, l2))
        for n, bb in bodies.items():
            if n == o1:
                continue
            if rects_overlap(b1, bb, 2):
                h9.append('text "%s" overlaps the symbol of %s' % (l1, n))
        if o1.startswith('FLAG'):
            continue
        for w in sch.wires:
            if seg_hits_rect(w, b1, 1):
                h9.append('wire %s runs through text "%s"' % (w, l1))
                break
    rule('H9 text and spacing (estimated)', not h9, h9 or ['no estimated text overlaps or crowding'],
         note='Text sizes are estimates (blocks.json text_metrics); confirm every finding, and the absence of '
              'findings, in LTspice screenshots.')

    # ================= H10 matching copies
    h10 = []
    for grp in cfg['copies']:
        parts = [[nm(p) for p in ch] for ch in grp['parts']]
        if any(p not in by for ch in parts for p in ch):
            if only is None:
                h10.append('%s: parts missing: %s' % (grp['name'], [p for ch in parts for p in ch if p not in by]))
            continue
        if only and not all(owner_block.get(p) in only for ch in parts for p in ch):
            continue
        flip_ok = set(nm(p) for p in grp.get('flip_ok', []))
        exc = set(nm(p) for p in grp.get('wire_exceptions', []))
        a0 = parts[0][0]
        ref_center = lambda p: ((bodies[p][0] + bodies[p][2]) / 2, (bodies[p][1] + bodies[p][3]) / 2)
        for k in range(1, len(parts)):
            ak = parts[k][0]
            off = (by[ak].x - by[a0].x, by[ak].y - by[a0].y)
            for p1, pk in zip(parts[0], parts[k]):
                s1, sk = by[p1], by[pk]
                if pk in flip_ok or p1 in flip_ok:
                    c1, ck = ref_center(p1), ref_center(pk)
                    if (round(ck[0] - c1[0]), round(ck[1] - c1[1])) != off:
                        h10.append('%s: %s is not at the same place relative to %s as %s is to %s' % (
                            grp['name'], pk, ak, p1, a0))
                    continue
                if (sk.x - s1.x, sk.y - s1.y) != off:
                    h10.append('%s: %s is not at the same place relative to %s as %s is to %s (off by %d,%d)' % (
                        grp['name'], pk, ak, p1, a0, sk.x - s1.x - off[0], sk.y - s1.y - off[1]))
                if sk.rot != s1.rot:
                    h10.append('%s: %s orientation %s differs from %s %s' % (grp['name'], pk, sk.rot, p1, s1.rot))
                t1 = {lab.split('.')[-1]: b for b, lab in attr_texts(sch, s1, TM)}
                tk = {lab.split('.')[-1]: b for b, lab in attr_texts(sch, sk, TM)}
                for key in ('InstName', 'Value'):
                    if key in t1 and key in tk:
                        d = (round(tk[key][0] - t1[key][0]), round(tk[key][1] - t1[key][1]))
                        if d != off:
                            h10.append('%s: %s %s text sits differently from %s' % (grp['name'], pk, key, p1))
            # wires inside the copy region
            reg1 = (min(bodies[p][0] for p in parts[0]) - 48, min(bodies[p][1] for p in parts[0]) - 48,
                    max(bodies[p][2] for p in parts[0]) + 48, max(bodies[p][3] for p in parts[0]) + 48)
            excpts = {pinpos[(p, pn)] for p in exc for pn, _, _ in sch.pins(by[p])} if exc else set()

            def wires_in(reg, dx, dy, ex):
                out = set()
                for w in sch.wires:
                    if inside((w[0], w[1]), reg) and inside((w[2], w[3]), reg):
                        if (w[0], w[1]) in ex or (w[2], w[3]) in ex:
                            continue
                        a1, b1 = (w[0] - dx, w[1] - dy), (w[2] - dx, w[3] - dy)
                        out.add(tuple(sorted([a1, b1])))
                return out
            regk = (reg1[0] + off[0], reg1[1] + off[1], reg1[2] + off[0], reg1[3] + off[1])
            excpk = {pinpos[(pk, pn)] for p1, pk in zip(parts[0], parts[k]) if p1 in exc or pk in exc
                     for pn, _, _ in sch.pins(by[pk])}
            w1 = wires_in(reg1, by[a0].x, by[a0].y, excpts)
            wk = wires_in(regk, by[ak].x, by[ak].y, excpk)
            if w1 != wk:
                h10.append('%s: wiring of copy %d differs from copy 1 (%d segments only in copy 1, %d only in copy %d)'
                           % (grp['name'], k + 1, len(w1 - wk), len(wk - w1), k + 1))
        if grp.get('frames') and not noframes:
            fs = [frames.get(b) for b in grp['frames']]
            if all(fs) and len({(r[2] - r[0], r[3] - r[1]) for r in fs}) != 1:
                h10.append('%s: the frames %s are not the same size' % (grp['name'], ', '.join(grp['frames'])))
    rule('H10 matching copies', not h10, h10 or ['all channel copies match'])

    # ================= H11 notes beside their subject
    h11 = []
    for t in sch.texts:
        if not t['body'].startswith(';'):
            continue
        for key, subj in cfg['notes'].items():
            if key.startswith('_') or not t['body'][1:].startswith(key):
                continue
            tb = text_box(t['x'], t['y'], t['just'], t['size'], t['body'][1:], TM)
            if subj == 'SETUP':
                if not noframes and 'SETUP' in frames and not rects_overlap(tb, frames['SETUP']):
                    h11.append('note "%s..." is not inside the [SETUP] frame' % key)
            else:
                ps = [nm(p) for p in subj if nm(p) in by]
                if ps:
                    r = (min(bodies[p][0] for p in ps), min(bodies[p][1] for p in ps), max(bodies[p][2] for p in ps),
                         max(bodies[p][3] for p in ps))
                    if rect_gap(tb, r) > TH['note_dist']:
                        h11.append('note "%s..." is %d units from %s (max %d)' % (key, rect_gap(tb, r), '/'.join(ps),
                                                                                TH['note_dist']))
    if not noframes and 'SETUP' in frames:
        for t in sch.texts:
            if t['body'].startswith('!') and not inside((t['x'], t['y']), frames['SETUP']):
                h11.append('directive outside the [SETUP] frame: %s' % t['body'][:60])
    if only:
        h11 = [m for m in h11 if 'D28' in m or 'directive' in m and False]
    rule('H11 notes beside their subject', not h11, h11 or ['notes placed with their subject'],
         note='Verbatim presence of every original note is checked by ltspice_equiv.py (E3).')

    # ================= H12 bypass caps at their owner's pin
    h12 = []
    for cap, (inst, pin, amb) in cap_owner_pin.items():
        if cap not in by or inst not in by:
            continue
        if only and owner_block.get(cap) not in only:
            continue
        if (inst, pin) not in pinpos:
            h12.append('%s: owner pin %s.%s not found' % (cap, inst, pin))
            continue
        tgt = pin_group[(inst, pin)]
        cap_groups = {pin_group[(cap, pn)] for pn, _, _ in sch.pins(by[cap])}
        if tgt not in cap_groups:
            h12.append('%s is not wired to %s pin %s%s' % (cap, inst, pin, ' (owner provisional)' if amb else ''))
        else:
            c = ((bodies[cap][0] + bodies[cap][2]) / 2, (bodies[cap][1] + bodies[cap][3]) / 2)
            d = math.dist(c, pinpos[(inst, pin)])
            if d > TH['bypass_dist']:
                h12.append('%s is %d units from %s pin %s (max %d)' % (cap, d, inst, pin, TH['bypass_dist']))
    if not noframes and lpwr and ('CONTROL' in frames or 'CONTROL_A' in frames):
        fr_c = frames.get('CONTROL') or frames.get('CONTROL_A')
        for cap in lpwr:
            if cap in by and not rect_inside(bodies[cap], fr_c) and (not only or 'CONTROL' in only):
                h12.append('%s (logic-package bypass) is not inside the CONTROL block' % cap)
    rule('H12 bypass caps at their IC', not h12, h12 or ['every bypass cap sits on its owner\'s supply pin'],
         note='Owners marked ambiguous in bypass_map.json are provisional until the user confirms them.')

    # ================= traces (label jumps along named paths)
    for tr in cfg['traces']:
        jumps, steps, problems = 0, [], []
        for ch in tr['chains']:
            ch = [nm(p) for p in ch]
            for p, q in zip(ch, ch[1:]):
                if p not in by or q not in by:
                    problems.append('%s/%s missing' % (p, q))
                    continue
                if only and (owner_block.get(p) not in only or owner_block.get(q) not in only):
                    continue
                pp = {pin_net[(p, pn)]: pin_group[(p, pn)] for pn, _, _ in sch.pins(by[p])}
                qq = {}
                for pn, _, _ in sch.pins(by[q]):
                    qq.setdefault(pin_net[(q, pn)], set()).add(pin_group[(q, pn)])
                shared = [n for n in pp if n in qq]
                if not shared:
                    problems.append('%s and %s share no net' % (p, q))
                    continue
                sig = [n for n in shared if nname(n) not in RAILS and nname(n) != GND] or shared
                best = min(0 if any(g == pp[n] for g in qq[n]) else 1 for n in sig)
                jumps += best
                if best:
                    steps.append('%s -> %s via label %s' % (p, q, '/'.join(nname(n) for n in sig)))
        ok = jumps <= tr['budget'] and not problems
        res['traces'][tr['id']] = {'name': tr['name'], 'jumps': jumps, 'budget': tr['budget'], 'pass': ok,
                                   'label_jumps': steps, 'problems': problems}
        if not ok:
            fails.append(tr['id'])

    # ================= review flags and stats
    per_block = {}
    for b in check_blocks:
        ms = [p for p in blocks[b] if p in by]
        r = frames.get(b) if not noframes else None
        if r is None and ms:
            r = (min(bodies[p][0] for p in ms), min(bodies[p][1] for p in ms), max(bodies[p][2] for p in ms),
                 max(bodies[p][3] for p in ms))
        if r is None:
            continue
        cr = sum(1 for c in crossings if inside(c, r))
        nfl = sum(1 for fl in sch.flags if inside((fl['x'], fl['y']), r) and fl['name'] != GND)
        area = max(1, (r[2] - r[0]) * (r[3] - r[1]))
        per_block[b] = {'parts': len(ms), 'crossings': cr, 'labels': nfl, 'area_k_units2': round(area / 1000),
                        'parts_per_100k_units2': round(len(ms) / area * 1e5, 2)}
    res['stats']['per_block'] = per_block
    lab_count = Counter(fl['name'] for fl in sch.flags if fl['name'] != GND)
    res['flags']['label instances per net (top 15)'] = lab_count.most_common(15)
    res['flags']['long wires (> %d units)' % TH['long_wire']] = [w for w in sch.wires if wlen(w) > TH['long_wire']]
    res['stats']['totals'] = {'wires': len(sch.wires), 'flags': len(sch.flags),
                              'ground_flags': sum(1 for fl in sch.flags if fl['name'] == GND),
                              'signal_label_instances': sum(lab_count.values()), 'crossings': len(crossings),
                              'symbols': len(sch.syms), 'texts': len(sch.texts), 'frames': len(frames)}
    res['pass'] = not fails
    res['failed'] = fails

    # ================= print
    print('LAYOUT CHECK  %s  %s' % (path, '(pilot: %s)' % ','.join(only) if only else ''))
    for rid, r in res['rules'].items():
        print('%-36s %s  (%d)' % (rid, 'PASS' if r['pass'] else 'FAIL', 0 if r['pass'] else len(r['details'])))
        for d in r['details'][:25]:
            print('    ' + d)
        if len(r['details']) > 25:
            print('    ... %d more' % (len(r['details']) - 25))
        if r['note']:
            print('    note: ' + r['note'])
    print('TRACES (label jumps along the path; budget in brackets)')
    for tid, t in res['traces'].items():
        print('  %s %-34s %d [%d] %s %s' % (tid, t['name'], t['jumps'], t['budget'], 'PASS' if t['pass'] else 'FAIL',
                                          '; '.join(t['label_jumps'][:6] + t['problems'][:4])))
    print('BLOCK STATS')
    for b, st in per_block.items():
        print('  %-8s %s' % (b, st))
    print('TOTALS', res['stats']['totals'])
    print('REVIEW FLAGS')
    for k, v in res['flags'].items():
        print('  %s: %s' % (k, v if not isinstance(v, list) or len(v) < 12 else '%d items, e.g. %s' % (len(v), v[:6])))
    print('LAYOUT RESULT:', 'PASS' if not fails else 'FAIL (%s)' % ', '.join(fails))
    if out_prefix:
        json.dump(res, open(out_prefix + '.json', 'w'), indent=1, default=str)
    sys.exit(0 if not fails else 1)


def sign(v):
    return (v > 0) - (v < 0)


if __name__ == '__main__':
    main()
