"""Draw an LTspice .asc to PNG with its symbols' own graphics (matplotlib).

    python render_asc.py FILE.asc OUT_PREFIX [--tiles C R] [--dpi N]

Writes OUT_PREFIX_overview.png and, with --tiles, OUT_PREFIX_rRcC.png zooms. Symbol bodies come from the .asy files
(LINE, RECTANGLE, CIRCLE, ARC) beside the .asc or in LTspice's lib/sym; wires blue, net labels green (ground as a
triangle), part names and values dark red, comments in grey, directives in black.
"""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ascgeo import Asc, LIBSYM
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Arc

_shapes = {}


def asy_shapes(a, sym):
    if sym in _shapes:
        return _shapes[sym]
    rel = sym.replace('\\\\', os.sep).replace('\\', os.sep) + '.asy'
    cands = [os.path.join(d, rel) for d in a.symdirs] + [os.path.join(LIBSYM, rel)]
    path = next((c for c in cands if os.path.exists(c)), None)
    shapes = []
    if path:
        raw = open(path, 'rb').read()
        txt = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('latin-1')
        for l in txt.splitlines():
            t = l.split()
            if not t:
                continue
            if t[0] in ('LINE', 'RECTANGLE', 'CIRCLE'):
                shapes.append((t[0], [int(v) for v in t[2:6]]))
            elif t[0] == 'ARC':
                shapes.append(('ARC', [int(v) for v in t[2:10]]))
    _shapes[sym] = shapes
    return shapes


def draw(a, ax):
    for (ln, x1, y1, x2, y2) in a.wires:
        ax.plot([x1, x2], [y1, y2], color='#1f4ea3', lw=0.6)
    for s in a.syms:
        X = lambda px, py: a.xform(px, py, s['rot'])
        for kind, v in asy_shapes(a, s['sym']):
            if kind == 'LINE':
                (x1, y1), (x2, y2) = X(v[0], v[1]), X(v[2], v[3])
                ax.plot([s['x'] + x1, s['x'] + x2], [s['y'] + y1, s['y'] + y2], color='#8b1a1a', lw=0.5)
            elif kind == 'RECTANGLE':
                pts = [X(v[0], v[1]), X(v[2], v[1]), X(v[2], v[3]), X(v[0], v[3]), X(v[0], v[1])]
                ax.plot([s['x'] + p[0] for p in pts], [s['y'] + p[1] for p in pts], color='#8b1a1a', lw=0.5)
            elif kind in ('CIRCLE', 'ARC'):
                (x1, y1), (x2, y2) = X(v[0], v[1]), X(v[2], v[3])
                cx, cy = s['x'] + (x1 + x2) / 2, s['y'] + (y1 + y2) / 2
                ax.add_patch(Arc((cx, cy), abs(x2 - x1), abs(y2 - y1), color='#8b1a1a', lw=0.5))
        ps = a.pins(s)
        xs = [p[1] for p in ps] or [s['x']]
        ys = [p[2] for p in ps] or [s['y']]
        nm = s['attr'].get('InstName', '')
        val = s['attr'].get('Value', '')[:14]
        ax.text(max(xs) + 6, (min(ys) + max(ys)) / 2, nm + ('\n' + val if val else ''), fontsize=3.2,
                color='#5a0e0e', va='center', clip_on=True)
    for (ln, x, y, n) in a.flags:
        if n == '0':
            ax.plot([x - 8, x + 8, x, x - 8], [y, y, y + 10, y], color='#1b7a1b', lw=0.6)
        else:
            ax.plot(x, y, 's', ms=1.5, color='#1b7a1b')
            ax.text(x + 4, y - 4, n, fontsize=3.4, color='#1b7a1b', clip_on=True)
    for (ln, l) in a.texts:
        t = l.split(' ', 5)
        if len(t) < 6:
            continue
        x, y, size, body = int(t[1]), int(t[2]), int(t[4]), t[5]
        directive = body.startswith('!')
        body = body[1:].replace('\\n', '\n')
        ax.text(x, y, body, fontsize=2.6 + 1.6 * size, color='black' if directive else '#555555', va='top',
                family='monospace' if directive else 'sans-serif', weight='bold' if size >= 3 else 'normal', clip_on=True)


def main():
    path, prefix = sys.argv[1], sys.argv[2]
    tiles = None
    if '--tiles' in sys.argv:
        i = sys.argv.index('--tiles')
        tiles = (int(sys.argv[i + 1]), int(sys.argv[i + 2]))
    dpi = int(sys.argv[sys.argv.index('--dpi') + 1]) if '--dpi' in sys.argv else 200
    a = Asc(path)
    xs = [w[1] for w in a.wires] + [w[3] for w in a.wires] + [s['x'] for s in a.syms] + [int(t[1].split()[1]) for t in a.texts]
    ys = [w[2] for w in a.wires] + [w[4] for w in a.wires] + [s['y'] for s in a.syms] + [int(t[1].split()[2]) for t in a.texts]
    x0, x1, y0, y1 = min(xs) - 100, max(xs) + 400, min(ys) - 100, max(ys) + 200
    W = 24
    fig, ax = plt.subplots(figsize=(W, W * (y1 - y0) / (x1 - x0)))
    draw(a, ax)
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(prefix + '_overview.png', dpi=dpi // 2, bbox_inches='tight')
    if tiles:
        C, R = tiles
        tw, th = (x1 - x0) / C, (y1 - y0) / R
        for r in range(R):
            for c in range(C):
                ax.set_xlim(x0 + c * tw - 50, x0 + (c + 1) * tw + 50)
                ax.set_ylim(y0 + (r + 1) * th + 50, y0 + r * th - 50)
                fig.set_size_inches(W, W * (th + 100) / (tw + 100))
                fig.savefig('%s_r%dc%d.png' % (prefix, r, c), dpi=dpi, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main()
