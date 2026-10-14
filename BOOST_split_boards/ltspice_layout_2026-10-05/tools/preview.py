"""Quick preview of an .asc region for my own iteration (NOT the visual check; that is ltspice_capture.py).

    python preview.py FILE.asc OUT.png [x1,y1,x2,y2] [--scale S]

Draws symbols from their .asy graphics, wires, junction dots (3+ ends), flags with the CHECKER's estimated text
boxes, attribute texts at the checker's boxes, comments and rectangles. Text is drawn inside its estimated box so
that what I see is what H9 measures.
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'ltspice_layout_handoff_2026-10-05', 'tools'))
import asc_layout_check as C
from collections import Counter, defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle, Polygon
import json

CFG = json.load(open(os.path.join(HERE, '..', '..', 'ltspice_layout_handoff_2026-10-05', 'blocks.json')))
TM = CFG['text_metrics']


def main():
    a = sys.argv[1:]
    path, out = a[0], a[1]
    region = tuple(int(v) for v in a[2].split(',')) if len(a) > 2 and not a[2].startswith('--') else None
    scale = float(a[a.index('--scale') + 1]) if '--scale' in a else 0.012
    sch = C.Schematic(path)
    xs = [w[0] for w in sch.wires] + [w[2] for w in sch.wires]
    ys = [w[1] for w in sch.wires] + [w[3] for w in sch.wires]
    if region is None:
        region = (min(xs) - 100, min(ys) - 100, max(xs) + 100, max(ys) + 100)
    x0, y0, x1, y1 = region
    W, H = (x1 - x0) * scale, (y1 - y0) * scale
    fig, ax = plt.subplots(figsize=(W, H))
    lw = 1.0
    fs = 16 * 1.5 * scale * 72 * 0.62        # size-2 text height in points, roughly cap height
    for w in sch.wires:
        ax.plot([w[0], w[2]], [w[1], w[3]], color='#1f4ea3', lw=lw)
    deg = Counter()
    for w in sch.wires:
        deg[(w[0], w[1])] += 1
        deg[(w[2], w[3])] += 1
    for s in sch.syms:
        for pn, x, y in sch.pins(s):
            deg[(x, y)] += 1
    pts = set(deg)
    for w in sch.wires:
        for p in pts:
            if C.on_interior(p, w):
                deg[p] += 2
    for p, d in deg.items():
        if d >= 3:
            ax.add_patch(Rectangle((p[0] - 6, p[1] - 6), 12, 12, color='#1f4ea3'))
    for s in sch.syms:
        a_ = sch.asy(s.sym)
        X = lambda px, py: Schematic_xf(px, py, s.rot)
        raw = open_asy_shapes(sch, s.sym)
        for kind, v in raw:
            if kind == 'LINE':
                (p1, p2) = X(v[0], v[1]), X(v[2], v[3])
                ax.plot([s.x + p1[0], s.x + p2[0]], [s.y + p1[1], s.y + p2[1]], color='#8b1a1a', lw=lw * 0.8)
            elif kind == 'RECTANGLE':
                c = [X(v[0], v[1]), X(v[2], v[1]), X(v[2], v[3]), X(v[0], v[3]), X(v[0], v[1])]
                ax.plot([s.x + q[0] for q in c], [s.y + q[1] for q in c], color='#8b1a1a', lw=lw * 0.8)
            elif kind in ('CIRCLE', 'ARC'):
                (p1, p2) = X(v[0], v[1]), X(v[2], v[3])
                cx, cy = s.x + (p1[0] + p2[0]) / 2, s.y + (p1[1] + p2[1]) / 2
                ax.add_patch(Arc((cx, cy), abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), color='#8b1a1a', lw=lw * 0.8))
        for b, lab in C.attr_texts(sch, s, TM):
            key = lab.split('.')[-1]
            val = s.attr.get(key, a_['attr'].get(key, ''))
            draw_box_text(ax, b, val, '#5a0e0e', fs)
    wire_ends = defaultdict(list)
    for w in sch.wires:
        wire_ends[(w[0], w[1])].append((C.sign(w[2] - w[0]), C.sign(w[3] - w[1])))
        wire_ends[(w[2], w[3])].append((C.sign(w[0] - w[2]), C.sign(w[1] - w[3])))
    for fl in sch.flags:
        b, lab = C.flag_box(fl, sch, TM, wire_ends)
        if fl['name'] == '0':
            x, y = fl['x'], fl['y']
            ax.add_patch(Polygon([(x - 16, y + 8), (x + 16, y + 8), (x, y + 24)], fill=False, ec='#1b7a1b', lw=lw))
            ax.plot([x, x], [y, y + 8], color='#1b7a1b', lw=lw)
        else:
            draw_box_text(ax, b, fl['name'] + (' [%s]' % fl['io'] if fl['io'] else ''), '#1b7a1b', fs,
                          edge=True)
            ax.plot(fl['x'], fl['y'], 'o', ms=2, color='#1b7a1b')
    for t in sch.texts:
        b = C.text_box(t['x'], t['y'], t['just'], t['size'], t['body'][1:], TM)
        if b:
            draw_box_text(ax, b, t['body'][1:].replace('\\n', '\n'), 'black' if t['body'].startswith('!') else '#444',
                          fs * TM['mult'][t['size']] / 1.5)
    for r in sch.rects:
        ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fill=False, ec='#777', lw=lw, ls='--'))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(out, dpi=100, bbox_inches='tight')
    plt.close(fig)
    print('wrote', out)


def draw_box_text(ax, b, txt, color, fs, edge=False):
    ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=color, lw=0.3,
                           ls='-' if edge else ':'))
    vertical = (b[3] - b[1]) > (b[2] - b[0]) * 1.2 and '\n' not in txt
    ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, txt, color=color, fontsize=fs, ha='center', va='center',
            rotation=90 if vertical else 0, family='DejaVu Sans', clip_on=True)


def Schematic_xf(px, py, rot):
    return C.Schematic.xf(px, py, rot)


_shapes = {}


def open_asy_shapes(sch, name):
    if name in _shapes:
        return _shapes[name]
    rel = name.replace('\\\\', os.sep).replace('\\', os.sep) + '.asy'
    cands = [os.path.join(sch.dir, rel), os.path.join(C.LIBSYM, rel)]
    p = next((c for c in cands if os.path.exists(c)), None)
    raw = open(p, 'rb').read()
    txt = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('latin-1')
    out = []
    for l in txt.splitlines():
        t = l.split()
        if t and t[0] in ('LINE', 'RECTANGLE', 'CIRCLE', 'ARC'):
            out.append((t[0], [int(v) for v in t[2:]]))
    _shapes[name] = out
    return out


if __name__ == '__main__':
    main()
