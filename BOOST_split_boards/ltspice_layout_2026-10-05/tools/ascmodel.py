"""A small read/write model of an LTspice .asc plus point connectivity (same rules as the checker).

Items keep their original lines so that untouched parts of a schematic are written back byte-for-byte.
"""
import os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOFF = os.path.normpath(os.path.join(HERE, '..', '..', 'ltspice_layout_handoff_2026-10-05'))
LIBSYM = r'C:\Users\bubba\AppData\Local\LTspice\lib\sym'


class Sym:
    def __init__(self, sym, x, y, rot, attrs, windows, extra=None):
        self.sym, self.x, self.y, self.rot = sym, x, y, rot
        self.attrs = attrs            # list of (key, value) in file order
        self.windows = windows        # dict num -> (x, y, just, size)
        self.extra = extra or []      # other lines inside the block (kept verbatim)

    @property
    def name(self):
        return dict(self.attrs).get('InstName', '')

    def lines(self):
        out = ['SYMBOL %s %d %d %s' % (self.sym, self.x, self.y, self.rot)]
        for n in sorted(self.windows):
            wx, wy, j, s = self.windows[n]
            out.append('WINDOW %d %d %d %s %d' % (n, wx, wy, j, s))
        for k, v in self.attrs:
            out.append('SYMATTR %s %s' % (k, v))
        return out + self.extra


class Asc:
    def __init__(self, path=None):
        self.head, self.wires, self.flags, self.syms, self.texts, self.shapes = [], [], [], [], [], []
        self.dir = os.path.dirname(os.path.abspath(path)) if path else None
        self._asy = {}
        if path:
            self.read(path)

    def read(self, path):
        L = open(path, encoding='latin-1').read().replace('\r', '').split('\n')
        i = 0
        while i < len(L):
            l = L[i]
            t = l.split(' ')
            k = t[0]
            if k in ('Version', 'SHEET'):
                self.head.append(l)
            elif k == 'WIRE':
                self.wires.append(tuple(int(v) for v in t[1:5]))
            elif k == 'FLAG':
                io = None
                if i + 1 < len(L) and L[i + 1].startswith('IOPIN ') and L[i + 1].split(' ')[1:3] == t[1:3]:
                    io = L[i + 1].split(' ')[3]
                    i += 1
                self.flags.append([int(t[1]), int(t[2]), ' '.join(t[3:]), io])
            elif k == 'IOPIN':
                x, y = int(t[1]), int(t[2])
                for f in self.flags:
                    if f[0] == x and f[1] == y:
                        f[3] = t[3]
            elif k == 'SYMBOL':
                s = Sym(t[1], int(t[2]), int(t[3]), t[4], [], {})
                j = i + 1
                while j < len(L) and L[j].startswith(('SYMATTR ', 'WINDOW ')):
                    m = L[j]
                    if m.startswith('SYMATTR '):
                        kk, _, v = m[8:].partition(' ')
                        s.attrs.append((kk, v))
                    else:
                        u = m.split(' ')
                        s.windows[int(u[1])] = (int(u[2]), int(u[3]), u[4], int(u[5]) if len(u) > 5 else 2)
                    j += 1
                self.syms.append(s)
                i = j
                continue
            elif k == 'TEXT':
                self.texts.append(l)
            elif k in ('RECTANGLE', 'LINE', 'CIRCLE', 'ARC'):
                self.shapes.append(l)
            elif l.strip():
                raise SystemExit('unknown line: ' + l)
            i += 1

    def write(self, path, overwrite=False):
        # never replace an existing schematic (the user edits the work files in LTspice); temp files pass overwrite=True
        if os.path.exists(path) and not overwrite:
            raise SystemExit('%s already exists: not overwritten (pick a new output name)' % path)
        out = list(self.head)
        out += ['WIRE %d %d %d %d' % w for w in self.wires]
        for x, y, n, io in self.flags:
            out.append('FLAG %d %d %s' % (x, y, n))
            if io:
                out.append('IOPIN %d %d %s' % (x, y, io))
        for s in self.syms:
            out += s.lines()
        out += self.texts + self.shapes
        data = '\n'.join(out) + '\n'
        assert '\u00a7' not in data
        open(path, 'w', encoding='latin-1', newline='\n').write(data)

    # ------------------------------------------------------------------ symbols
    def asy(self, name):
        if name in self._asy:
            return self._asy[name]
        rel = name.replace('\\\\', os.sep).replace('\\', os.sep) + '.asy'
        cands = [os.path.join(self.dir or '.', rel), os.path.join(LIBSYM, rel)]
        path = next((c for c in cands if os.path.exists(c)), None)
        if path is None:
            raise SystemExit('symbol not found: ' + name)
        raw = open(path, 'rb').read()
        txt = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('latin-1')
        d = {'pins': [], 'pts': [], 'windows': {}, 'attr': {}, 'shapes': []}
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
                v = [int(x) for x in t[2:]]
                d['pts'] += [(v[0], v[1]), (v[2], v[3])]
                d['shapes'].append((t[0], v))
            elif t[0] == 'WINDOW':
                d['windows'][int(t[1])] = (int(t[2]), int(t[3]), t[4], int(t[5]) if len(t) > 5 else 2)
            elif t[0] == 'SYMATTR':
                k, _, v = l[8:].partition(' ')
                d['attr'][k] = v
        self._asy[name] = d
        return d

    @staticmethod
    def xf(px, py, rot):
        m = rot.startswith('M')
        for _ in range(int(rot[1:]) // 90):
            px, py = -py, px
        if m:
            px = -px
        return px, py

    def pins(self, s):
        return [(p['name'], s.x + self.xf(p['x'], p['y'], s.rot)[0], s.y + self.xf(p['x'], p['y'], s.rot)[1])
                for p in self.asy(s.sym)['pins']]

    def pin(self, s, name):
        for n, x, y in self.pins(s):
            if n == name:
                return (x, y)
        raise KeyError('%s has no pin %s' % (s.name, name))

    def body(self, s):
        a = self.asy(s.sym)
        pts = a['pts'] + [(p['x'], p['y']) for p in a['pins']]
        q = [self.xf(x, y, s.rot) for x, y in pts]
        return (s.x + min(a for a, _ in q), s.y + min(b for _, b in q), s.x + max(a for a, _ in q),
                s.y + max(b for _, b in q))

    def by(self):
        return {s.name: s for s in self.syms}


# ---------------------------------------------------------------------------------------------- connectivity
def on_interior(p, w):
    x, y = p
    x1, y1, x2, y2 = w
    if p in ((x1, y1), (x2, y2)):
        return False
    if x1 == x2 == x:
        return min(y1, y2) < y < max(y1, y2)
    if y1 == y2 == y:
        return min(x1, x2) < x < max(x1, x2)
    return False


def connectivity(a, skip=()):
    """-> (pin_group {(inst,pin): gid}, group_of_point, net_of_group, names_of_net, pins_at)"""
    par = {}

    def f(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    pins_at = defaultdict(list)
    for s in a.syms:
        if s.name in skip:
            continue
        for n, x, y in a.pins(s):
            pins_at[(x, y)].append((s.name, n))
    pts = set(pins_at) | {(fl[0], fl[1]) for fl in a.flags}
    for w in a.wires:
        pts.add((w[0], w[1]))
        pts.add((w[2], w[3]))
    xs, ys = defaultdict(list), defaultdict(list)
    for p in pts:
        xs[p[0]].append(p)
        ys[p[1]].append(p)
    for w in a.wires:
        par[f((w[0], w[1]))] = f((w[2], w[3]))
        cand = xs[w[0]] if w[0] == w[2] else ys[w[1]] if w[1] == w[3] else []
        for p in cand:
            if on_interior(p, w):
                par[f(p)] = f((w[0], w[1]))
    group = {p: f(p) for p in pts}
    names_by_group = defaultdict(set)
    for fl in a.flags:
        names_by_group[group[(fl[0], fl[1])]].add(fl[2])
    gpar = {}

    def gf(x):
        gpar.setdefault(x, x)
        while gpar[x] != x:
            gpar[x] = gpar[gpar[x]]
            x = gpar[x]
        return x
    first = {}
    for g, ns in names_by_group.items():
        for n in ns:
            if n in first:
                gpar[gf(g)] = gf(first[n])
            else:
                first[n] = g
    net_of_group = {g: gf(g) for g in set(group.values())}
    names = defaultdict(set)
    for g, ns in names_by_group.items():
        names[net_of_group[g]] |= ns
    pin_group = {}
    for p, lst in pins_at.items():
        for k in lst:
            pin_group[k] = group[p]
    return pin_group, group, net_of_group, names, pins_at


def partition(a, rename=None):
    """-> {frozenset((inst,pin)...): set(names)} for every net that has at least one pin"""
    rename = rename or {}
    pg, group, nog, names, _ = connectivity(a)
    nets = defaultdict(set)
    for k, g in pg.items():
        nets[nog[g]].add((rename.get(k[0], k[0]), k[1]))
    return {frozenset(v): frozenset(names.get(n, ())) for n, v in nets.items()}
