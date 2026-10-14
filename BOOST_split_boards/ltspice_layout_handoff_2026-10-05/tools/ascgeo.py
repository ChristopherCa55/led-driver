"""LTspice .asc geometry helper: parse, symbol pin positions, point connectivity, region plots."""
import os, re, collections

LIBSYM = r'C:\Users\bubba\AppData\Local\LTspice\lib\sym'


class Asc:
    def __init__(self, path, symdirs=()):
        self.path = path
        self.lines = open(path, encoding='latin-1').read().split('\n')
        self.symdirs = [os.path.dirname(os.path.abspath(path))] + list(symdirs)
        self._asy = {}
        self.parse()

    # ---------------------------------------------------------------- parsing
    def parse(self):
        self.wires, self.flags, self.syms, self.texts = [], [], [], []
        cur = None
        for i, l in enumerate(self.lines):
            t = l.split(' ')
            if l.startswith('WIRE '):
                self.wires.append((i, int(t[1]), int(t[2]), int(t[3]), int(t[4])))
                cur = None
            elif l.startswith('FLAG '):
                self.flags.append((i, int(t[1]), int(t[2]), t[3] if len(t) > 3 else ''))
                cur = None
            elif l.startswith('SYMBOL '):
                cur = {'line': i, 'sym': t[1], 'x': int(t[2]), 'y': int(t[3]), 'rot': t[4], 'attr': {}, 'end': i}
                self.syms.append(cur)
            elif cur is not None and (l.startswith('SYMATTR ') or l.startswith('WINDOW ')):
                cur['end'] = i
                if l.startswith('SYMATTR '):
                    k, _, v = l[8:].partition(' ')
                    cur['attr'][k] = v
            else:
                cur = None
                if l.startswith('TEXT '):
                    self.texts.append((i, l))
        self.byname = {s['attr'].get('InstName', ''): s for s in self.syms}

    # ---------------------------------------------------------------- symbols
    def asy_pins(self, sym):
        if sym in self._asy:
            return self._asy[sym]
        rel = sym.replace('\\\\', os.sep).replace('\\', os.sep) + '.asy'
        cands = [os.path.join(d, rel) for d in self.symdirs] + [os.path.join(LIBSYM, rel)]
        path = next((c for c in cands if os.path.exists(c)), None)
        if path is None:
            raise FileNotFoundError(sym)
        raw = open(path, 'rb').read()
        txt = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('latin-1')
        pins, cur = [], None
        for l in txt.splitlines():
            if l.startswith('PIN '):
                t = l.split()
                cur = {'x': int(t[1]), 'y': int(t[2]), 'name': '', 'order': 0}
                pins.append(cur)
            elif l.startswith('PINATTR PinName') and cur is not None:
                cur['name'] = l.split(' ', 2)[2]
            elif l.startswith('PINATTR SpiceOrder') and cur is not None:
                cur['order'] = int(l.split()[2])
        self._asy[sym] = pins
        return pins

    @staticmethod
    def xform(px, py, rot):
        # rotate first, then mirror: checked 2026-10-05 on BOOST.asc's three M90 resistors (R8/R34/R42), whose pins
        # only land on their wires this way (the old mirror-first order left them floating)
        m = rot.startswith('M')
        a = int(rot[1:])
        for _ in range(a // 90):
            px, py = -py, px
        if m:
            px = -px
        return px, py

    def pins(self, s):
        out = []
        for p in self.asy_pins(s['sym']):
            dx, dy = self.xform(p['x'], p['y'], s['rot'])
            out.append((p['name'], s['x'] + dx, s['y'] + dy))
        return out

    # ---------------------------------------------------------------- connectivity (points)
    def nets(self):
        """Union-find over points: wire ends, wire interiors hit by other points, flags, pins."""
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
        for _, x1, y1, x2, y2 in self.wires:
            pts.add((x1, y1)); pts.add((x2, y2))
        for _, x, y, _n in self.flags:
            pts.add((x, y))
        for s in self.syms:
            for _, x, y in self.pins(s):
                pts.add((x, y))
        for _, x1, y1, x2, y2 in self.wires:
            u((x1, y1), (x2, y2))
            for (x, y) in pts:
                if (x, y) in ((x1, y1), (x2, y2)):
                    continue
                if x1 == x2 == x and min(y1, y2) < y < max(y1, y2):
                    u((x, y), (x1, y1))
                elif y1 == y2 == y and min(x1, x2) < x < max(x1, x2):
                    u((x, y), (x1, y1))
        for p in pts:
            f(p)
        return f

    def occupied(self):
        occ = []
        for _, x1, y1, x2, y2 in self.wires:
            occ.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        for _, x, y, _n in self.flags:
            occ.append((x - 16, y - 16, x + 16, y + 16))
        for s in self.syms:
            ps = self.pins(s)
            xs = [p[1] for p in ps] + [s['x']]
            ys = [p[2] for p in ps] + [s['y']]
            occ.append((min(xs), min(ys), max(xs), max(ys)))
        return occ

    def write(self, path, lines=None):
        open(path, 'w', encoding='latin-1', newline='\n').write('\n'.join(self.lines if lines is None else lines))


def plot_region(a, x0, y0, x1, y1, out, title=''):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 14 * (y1 - y0) / max(x1 - x0, 1)))
    for _, xa, ya, xb, yb in a.wires:
        if max(xa, xb) >= x0 and min(xa, xb) <= x1 and max(ya, yb) >= y0 and min(ya, yb) <= y1:
            ax.plot([xa, xb], [ya, yb], 'b-', lw=0.8)
    for _, x, y, n in a.flags:
        if x0 <= x <= x1 and y0 <= y <= y1:
            ax.plot(x, y, 'gs', ms=3)
            ax.text(x, y, n, color='g', fontsize=6)
    for s in a.syms:
        ps = a.pins(s)
        if not any(x0 <= x <= x1 and y0 <= y <= y1 for _, x, y in ps):
            continue
        xs = [p[1] for p in ps]; ys = [p[2] for p in ps]
        ax.add_patch(plt.Rectangle((min(xs), min(ys)), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, fill=False, ec='r', lw=0.5))
        ax.text(sum(xs) / len(xs), sum(ys) / len(ys), s['attr'].get('InstName', '') + ' ' + s['attr'].get('Value', '')[:12],
                color='r', fontsize=6, ha='center')
        for n, x, y in ps:
            ax.plot(x, y, 'r.', ms=3)
            ax.text(x, y, n, color='m', fontsize=4)
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal'); ax.grid(True, lw=0.2)
    ax.set_title(title)
    fig.savefig(out, dpi=110, bbox_inches='tight')
    plt.close(fig)
