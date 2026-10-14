"""Drawing helpers for the BOOST.asc re-layout: old-area cleanup, a small drawing DSL, and an electrical self-check.

Coordinates are LTspice units (16 = one grid step). Text positions are given in WORLD terms (where the text should
appear on screen) and converted to the instance WINDOW for the part's rotation, using the same transform as the
checker (rotate first, then mirror).
"""
import os, sys, json
from collections import defaultdict, Counter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ascmodel import Asc, Sym, connectivity, partition, on_interior, HANDOFF

ORIG = os.path.join(HANDOFF, 'reference', 'LTspice_original', 'BOOST.asc')
CFG = json.load(open(os.path.join(HANDOFF, 'blocks.json')))
BMAP = json.load(open(os.path.join(HANDOFF, 'bypass_map.json')))['caps']
RENAME = json.load(open(os.path.join(HANDOFF, 'tools', 'approved_changes.json')))['instance_renames']


def block_members():
    own = {}
    for b, v in CFG['blocks'].items():
        for p in v['members']:
            own[p] = b
    for cap, info in BMAP.items():
        o, rail = info['owner'], info.get('rail')
        sp = [o, 'OUT'] if info.get('fixed_by_design') else CFG['supply_pins'].get(rail, {}).get(o)
        if sp == 'LPWR':
            own[cap] = 'CONTROL'
        elif sp:
            own[cap] = own.get(sp[0])
    return own


# ------------------------------------------------------------------------------------------- text windows
_H = {'Left': 'Right', 'Right': 'Left', 'Top': 'Top', 'Bottom': 'Bottom', 'Center': 'Center'}
_V = {'Left': 'Left', 'Right': 'Right', 'Top': 'Bottom', 'Bottom': 'Top', 'Center': 'Center'}


def window(rot, just, wx, wy, size=2):
    """world justification + world offset from the symbol origin -> (lx, ly, local_just, size)"""
    if rot == 'R0':
        return (wx, wy, just, size)
    if rot == 'R180':
        return (-wx, -wy, {'Left': 'Right', 'Right': 'Left', 'Top': 'Bottom', 'Bottom': 'Top'}.get(just, just), size)
    if rot == 'M0':
        return (-wx, wy, _H[just], size)
    if rot == 'M180':
        return (wx, -wy, _V[just], size)
    if rot == 'R90':
        return (wy, -wx, 'V' + just, size)
    if rot == 'R270':
        return (-wy, wx, 'V' + {'Left': 'Right', 'Right': 'Left', 'Top': 'Bottom', 'Bottom': 'Top'}[just], size)
    if rot == 'M90':
        return (wy, wx, 'V' + {'Left': 'Right', 'Right': 'Left', 'Top': 'Top', 'Bottom': 'Bottom'}[just], size)
    if rot == 'M270':
        return (-wy, -wx, 'V' + {'Left': 'Left', 'Right': 'Right', 'Top': 'Bottom', 'Bottom': 'Top'}[just], size)
    raise ValueError(rot)


ATTR_WIN = {'name': 0, 'value': 3, 'spiceline': 39, 'value2': 123}


# ------------------------------------------------------------------------------------------- drawing DSL
class Draw:
    def __init__(self, asc, pool):
        self.a, self.pool = asc, pool
        self.placed = []

    def P(self, name, x, y, rot, texts=None, keep=()):
        """place a part; texts = {'name': (just, wx, wy[, size]), 'value': ...} in world offsets from (x, y);
        a text set to None is hidden (Invisible); attributes not listed keep the symbol's default window."""
        s = self.pool.pop(name)
        s.x, s.y, s.rot = x, y, rot
        s.windows = {k: v for k, v in s.windows.items() if k in keep}
        for k, spec in (texts or {}).items():
            n = ATTR_WIN[k]
            if spec is None:
                s.windows[n] = (0, 0, 'Invisible', 2)
            else:
                s.windows[n] = window(rot, *spec)
        self.a.syms.append(s)
        self.placed.append(name)
        return s

    def Pa(self, name, x, y, rot, texts=None, keep=()):
        """like P, but text anchors are ABSOLUTE world coordinates"""
        rel = {}
        for k, spec in (texts or {}).items():
            rel[k] = None if spec is None else (spec[0], spec[1] - x, spec[2] - y) + tuple(spec[3:])
        return self.P(name, x, y, rot, rel, keep)

    def cap(self, name, x, ytop, flip=False, texts=None):
        """vertical capacitor whose body spans x-16..x+16, ytop..ytop+64. Pin A is at the top unless flip (then
        A is at the bottom: used for caps netlisted with pin 1 on ground). Text anchors absolute."""
        if flip:
            return self.Pa(name, x + 16, ytop + 64, 'R180', texts)
        return self.Pa(name, x - 16, ytop, 'R0', texts)

    def res_v(self, name, x, ytop, flip=False, texts=None):
        """vertical resistor with pins at (x, ytop) and (x, ytop+80); A on top unless flip"""
        if flip:
            return self.Pa(name, x + 16, ytop + 96, 'R180', texts)
        return self.Pa(name, x - 16, ytop - 16, 'R0', texts)

    def res_h(self, name, xleft, y, a_left=True, texts=None):
        """horizontal resistor with pins at (xleft, y) and (xleft+80, y); pin A on the left unless a_left=False"""
        if a_left:
            return self.Pa(name, xleft - 16, y + 16, 'R270', texts)
        return self.Pa(name, xleft + 96, y - 16, 'R90', texts)

    def cap_h(self, name, xleft, y, a_left=True, texts=None):
        """horizontal capacitor with pins at (xleft, y) and (xleft+64, y); pin A on the left unless a_left=False"""
        if a_left:
            return self.Pa(name, xleft, y + 16, 'R270', texts)
        return self.Pa(name, xleft + 64, y - 16, 'R90', texts)

    def pin(self, name, pn):
        s = next(s for s in self.a.syms if s.name == name)
        return self.a.pin(s, pn)

    def W(self, *pts):
        for p, q in zip(pts, pts[1:]):
            assert p[0] == q[0] or p[1] == q[1], ('diagonal wire', p, q)
            assert p != q, ('zero wire', p)
            for v in p + q:
                assert v % 16 == 0, ('off grid', p, q)
            self.a.wires.append((p[0], p[1], q[0], q[1]))

    def F(self, x, y, name, io=None):
        assert x % 16 == 0 and y % 16 == 0, ('flag off grid', x, y, name)
        self.a.flags.append([x, y, name, io])

    def G(self, p):
        self.F(p[0], p[1], '0')

    def T(self, x, y, text, size=2, just='Left'):
        assert '§' not in text and all(ord(c) < 256 for c in text), text
        self.a.texts.append('TEXT %d %d %s %d ;%s' % (x, y, just, size, text))

    def frame(self, x1, y1, x2, y2, style=2):
        self.a.shapes.append('RECTANGLE Normal %d %d %d %d %d' % (x1, y1, x2, y2, style))


# ------------------------------------------------------------------------------------------- old-area cleanup
def strip_old(a, remove):
    """Remove the symbols in `remove` from Asc `a` (returned as a pool name -> Sym), then delete wire groups that no
    longer touch any remaining pin and trim dangling wire ends. Returns (pool, attach) where attach maps a remaining
    wire group's representative point -> points where trimmed wires used to continue."""
    pool = {}
    keep = []
    for s in a.syms:
        if s.name in remove:
            pool[s.name] = s
        else:
            keep.append(s)
    a.syms = keep
    # dead groups
    pg, group, nog, names, pins_at = connectivity(a)
    live = {group[p] for p in pins_at}
    a.wires = [w for w in a.wires if group[(w[0], w[1])] in live]
    a.flags = [f for f in a.flags if group[(f[0], f[1])] in live]
    # trim dangling ends
    trimmed_at = []
    while True:
        pins = set()
        for s in a.syms:
            for _, x, y in a.pins(s):
                pins.add((x, y))
        flagp = {(f[0], f[1]) for f in a.flags}
        ends = Counter()
        for w in a.wires:
            ends[(w[0], w[1])] += 1
            ends[(w[2], w[3])] += 1
        allpts = set(ends) | pins | flagp

        def interior_hits(w):
            return [p for p in allpts if on_interior(p, w)]

        def on_some_wire(p):
            return any(on_interior(p, w) for w in a.wires)
        changed = False
        new = []
        for w in a.wires:
            e1, e2 = (w[0], w[1]), (w[2], w[3])
            d1 = ends[e1] == 1 and e1 not in pins and e1 not in flagp and not on_some_wire(e1)
            d2 = ends[e2] == 1 and e2 not in pins and e2 not in flagp and not on_some_wire(e2)
            if not d1 and not d2:
                new.append(w)
                continue
            changed = True
            hits = interior_hits(w)
            if d1 and d2:
                if hits:
                    raise SystemExit('wire dangling at both ends with interior contacts: %s' % (w,))
                continue                                    # an isolated wire: drop it
            dang, other = (e1, e2) if d1 else (e2, e1)
            if hits:
                # shorten to the interior contact nearest the dangling end
                h = min(hits, key=lambda p: abs(p[0] - dang[0]) + abs(p[1] - dang[1]))
                new.append((h[0], h[1], other[0], other[1]))
                trimmed_at.append(h)
            else:
                trimmed_at.append(other)
        a.wires = new
        if not changed:
            break
    # isolated flags (nothing at their point any more)
    ends = Counter()
    for w in a.wires:
        ends[(w[0], w[1])] += 1
        ends[(w[2], w[3])] += 1
    pins = set()
    for s in a.syms:
        for _, x, y in a.pins(s):
            pins.add((x, y))
    a.flags = [f for f in a.flags if (f[0], f[1]) in ends or (f[0], f[1]) in pins or
               any(on_interior((f[0], f[1]), w) for w in a.wires)]
    return pool, trimmed_at


def name_cut_groups(a, orig_part, trimmed_at, rename):
    """Every remaining old wire group whose original net had a name must still carry that name; add a plain flag at
    a trimmed point of that group if it lost it. Returns the flags added."""
    pg, group, nog, names, pins_at = connectivity(a)
    # original net name for each (inst, pin)
    want = {}
    for pins, nm in orig_part.items():
        if len(nm) == 1:
            n = next(iter(nm))
            for k in pins:
                want[k] = n
    added = []
    groups_pins = defaultdict(set)
    for k, g in pg.items():
        groups_pins[g].add(k)
    for g, ks in groups_pins.items():
        net = nog[g]
        have = names.get(net, set())
        wanted = {want.get((rename.get(i, i), p)) for i, p in ks} - {None}
        if not wanted:
            continue
        assert len(wanted) == 1, (ks, wanted)
        n = wanted.pop()
        if n in have:
            continue
        cands = [p for p in trimmed_at if p in group and group[p] == g]
        if not cands:
            cands = [p for p in group if group[p] == g and p not in pins_at]
        if not cands:
            cands = [p for p in group if group[p] == g]
        p = sorted(cands)[0]
        a.flags.append([p[0], p[1], n, None])
        added.append((p, n))
    return added


# ------------------------------------------------------------------------------------------- electrical self-check
def compare(orig, new):
    """pin partition + names of `new` against `orig` (approved renames applied). Returns a list of problems."""
    po = partition(orig, RENAME)
    pn = partition(new)
    probs = []
    for pins, nm in po.items():
        if pins not in pn:
            # find the closest
            best = max(pn, key=lambda q: len(q & pins))
            probs.append('net %s differs: only orig %s; only new %s' % (
                sorted(nm) or 'AUTO', sorted(pins - best)[:8], sorted(best - pins)[:8]))
        elif nm and pn[pins] != nm:
            probs.append('net %s renamed to %s' % (sorted(nm), sorted(pn[pins])))
        elif len(pn[pins]) > 1:
            probs.append('net %s carries several names %s' % (sorted(nm), sorted(pn[pins])))
    newnames = [(sorted(pn[p]), len(p)) for p in pn if p in po and not po[p] and pn[p]]
    return probs, newnames
