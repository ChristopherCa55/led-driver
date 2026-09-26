"""Free-space probe on the rasterised base board (system Python).

usage: python free_probe.py BASE_CU.json LAYER X0 Y0 X1 Y1 [--axis x|y] [--net NET]

Prints, for each scan line, the runs of cells that carry no copper of another net and no foreign hole, so a
corridor for a hand-placed pair can be measured before it is drawn. --net treats that net's own copper as free.
Runs shorter than 0.4 mm are left out.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route_signals as R

cop = json.load(open(sys.argv[1]))
layer = sys.argv[2]
x0, y0, x1, y1 = map(float, sys.argv[3:7])
axis = sys.argv[sys.argv.index('--axis') + 1] if '--axis' in sys.argv else 'y'
net = sys.argv[sys.argv.index('--net') + 1] if '--net' in sys.argv else None
bd = R.Board(cop)
l = R.LI[layer]
n = bd.nid[net] if net else -99
i0, j0 = R.cell(x0, y0)
i1, j1 = R.cell(x1, y1)
free = ((bd.hard[l] < 0) | (bd.hard[l] == n)) & ((bd.holes < 0) | (bd.holes == n))
for k in (range(j0, j1 + 1) if axis == 'y' else range(i0, i1 + 1)):
    line = free[k, i0:i1 + 1] if axis == 'y' else free[j0:j1 + 1, k]
    runs, s = [], None
    for idx, v in enumerate(line):
        if v and s is None:
            s = idx
        elif not v and s is not None:
            runs.append((s, idx - 1))
            s = None
    if s is not None:
        runs.append((s, len(line) - 1))
    pos = R.Y0 + (k + 0.5) * R.H if axis == 'y' else R.X0 + (k + 0.5) * R.H
    base = x0 if axis == 'y' else y0
    txt = ', '.join('%.2f-%.2f (%.2f)' % (base + a * R.H, base + b * R.H, (b - a + 1) * R.H)
                    for a, b in runs if (b - a + 1) * R.H >= 0.4)
    print('%s %6.2f: %s' % ('y' if axis == 'y' else 'x', pos, txt or '-'))
