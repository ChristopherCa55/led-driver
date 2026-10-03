"""Copper area per net and layer, two copper exports side by side (export_copper6.py; 0.05 mm raster).

    python area_diff.py OLD_cu.json NEW_cu.json [--all]

Lists every (net, layer) whose area changed by more than 0.5 mm2 (all nets with --all), and the totals per layer.
"""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solve_copper6 as SC

H = 0.05
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
X0, Y0, NX, NY = 28.0, 28.0, int(80 / H), int(92 / H)


def areas(c):
    out = {}
    for net, per in c['nets'].items():
        for ln, polys in per.items():
            out[(net, ln)] = float(SC.raster(polys, X0, Y0, NX, NY, H).sum() * H * H)
    return out


A, B = areas(a), areas(b)
print('%-18s %-7s %9s %9s %8s' % ('net', 'layer', 'old mm2', 'new mm2', 'change'))
for k in sorted(set(A) | set(B), key=lambda k: (k[1], k[0])):
    d = B.get(k, 0) - A.get(k, 0)
    if '--all' in sys.argv or abs(d) > 0.5:
        print('%-18s %-7s %9.1f %9.1f %+8.1f' % (k[0], k[1].replace('.Cu', ''), A.get(k, 0), B.get(k, 0), d))
