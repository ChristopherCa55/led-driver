# Sanity check of the model against TI's published RthetaJA (LM2940 SNVS769J table 6.4, JEDEC high-K board):
# SOT-223 59.3 K/W (RthetaJB 8.1), TO-263 40.9 K/W (RthetaJC(bot) 0.8).
# Board per JESD51-7 as I understand it (not re-read for this check): 114.3 x 76.2 x 1.6 mm FR-4, 2 oz top traces,
# two solid 1 oz internal planes about 0.5 mm in from each surface, no bottom copper, no thermal vias.
# Top copper: the footprint pads plus a 0.25 mm x 25 mm trace from each pad (a minimal fan-out).
# Usage: python tools/jedec_check.py h1 h2 ...
import sys
import numpy as np
sys.path.insert(0, 'tools')
from thermal import Model

A = 0.25
W, H = 114.3, 76.2
nx, ny = int(W / A), int(H / A)
xs = A * (np.arange(nx) + 0.5); ys = A * (np.arange(ny) + 0.5)
cx, cy = W / 2, H / 2


def rect(arr, x0, y0, x1, y1, v):
    ix = (xs >= x0) & (xs <= x1); iy = (ys >= y0) & (ys <= y1)
    arr[np.ix_(iy, ix)] = v


def board(pkg):
    arr = np.zeros((4, ny, nx), np.int32)
    arr[1] = 1; arr[2] = 1
    if pkg == 'sot223':  # pads as KiCad SOT-223-3_TabPin2, tab towards -y
        tab = (cx - 1.9, cy - 3.15 - 1.0, cx + 1.9, cy - 3.15 + 1.0)
        pins = [(cx + dx - 0.75, cy + 3.15 - 1.0, cx + dx + 0.75, cy + 3.15 + 1.0) for dx in (-2.3, 0, 2.3)]
    else:  # TO-263-3 (KiCad TO-263-3_TabPin2): tab 9.4 x 10.8, leads 1.1 x 4.6 at 2.54 pitch
        tab = (cx - 5.4, cy - 4.7 - 3.0, cx + 5.4, cy + 4.7 - 3.0)
        pins = [(cx + dx - 0.55, cy + 4.7 - 3.0 + 1.2, cx + dx + 0.55, cy + 4.7 - 3.0 + 5.8) for dx in (-2.54, 0, 2.54)]
    rect(arr[0], *tab, 2)
    rect(arr[0], cx - 0.125, tab[1] - 25, cx + 0.125, tab[1], 2)
    for k, p in enumerate(pins):
        rect(arr[0], *p, 3 + k)
        mx = (p[0] + p[2]) / 2
        rect(arr[0], mx - 0.125, p[3], mx + 0.125, p[3] + 25, 3 + k)
    cells = [(iy, ix) for iy in range(ny) for ix in range(nx)
             if tab[0] <= xs[ix] <= tab[2] and tab[1] <= ys[iy] <= tab[3]]
    return arr, cells


import os
for pkg, R, ref in [c for c in (('sot223', 8.1, 59.3), ('to263', 0.8, 40.9)) if c[0] in os.environ.get('PKG', 'sot223 to263')]:
    arr, cells = board(pkg)
    for h in map(float, sys.argv[1:]):
        m = Model(arr, np.ones((ny, nx), bool), A, [0.070, 0.035, 0.035, 0.0], [0.5, 0.46, 0.5])
        j = m.add_device(0, cells, R)
        m.build(h, h)
        q = np.zeros(m.N); q[j] = 1
        T = m.solve(q)
        print('%s h=%.0f: theta_JA %.1f K/W (TI %.1f)' % (pkg, h, T[j], ref), flush=True)
