# U16 thermal resistance on the real power board (2026-10-01).
# Usage: python tools/run_board.py COPPER.json CONFIG [h_top h_bot] [--save NAME]
#   CONFIG: sot223 | sot223_vias_around | sot223_vias_all | to263
# Prints theta (junction rise per watt) for R_jt values and saves the F.Cu temperature map.
import sys, json, time
import numpy as np
sys.path.insert(0, 'tools')
from raster import load, rasterize
from thermal import Model

import os
A = float(os.environ.get("GRID_MM", "0.25"))
T_CU = [0.035] + [0.030] * 6 + [0.035]
T_D = [0.109, 0.25, 0.109, 0.25, 0.109, 0.25, 0.109]

from vias import TABS, CONFIGS, VIAS_IN_TAB, VIAS_TAB_REST, VIAS_UNDER_BODY, VIAS_WEST, VIAS_NORTH, VIAS_EAST


def setup(d, cfg, extra_from_board=True):
    xs, ys, nets, arr, board = rasterize(d, A)
    x0, y0 = xs[0] - A / 2, ys[0] - A / 2
    netid = {n: i for i, n in enumerate(nets)}
    m = Model(arr, board, A, T_CU, T_D)
    L = d['layers']
    nb = 0
    for v in d['vias']:
        iy, ix = m.cell(v['x'], v['y'], x0, y0)
        m.add_barrel(iy, ix, [li for li, ln in enumerate(L) if ln in v['flash']], v['drill']); nb += 1
    for p in d['pth']:
        iy, ix = m.cell(p['x'], p['y'], x0, y0)
        lay = [li for li in range(len(L)) if arr[li, iy, ix] == netid.get(p['net'], -1)]
        m.add_barrel(iy, ix, lay, p['drill'])
    tab, vias = CONFIGS[cfg]
    gnd = netid['GND']
    added = []
    for x, y in vias:
        iy, ix = m.cell(x, y, x0, y0)
        lay = [li for li in range(len(L)) if arr[li, iy, ix] == gnd]
        # the via's own pad is copper on F and B; the zone fill joins it where the layer is GND
        added.append((x, y, [L[i] for i in lay]))
        m.add_barrel(iy, ix, lay, 0.4)
    tx0, ty0, tx1, ty1 = TABS[tab]
    cells = [(iy, ix) for iy in range(len(ys)) for ix in range(len(xs))
             if tx0 <= xs[ix] <= tx1 and ty0 <= ys[iy] <= ty1 and arr[0, iy, ix] == gnd]
    return m, cells, added, (xs, ys)


if __name__ == '__main__':
    fn, cfg = sys.argv[1], sys.argv[2]
    h_top = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    h_bot = float(sys.argv[4]) if len(sys.argv) > 4 else h_top
    d = load(fn)
    t = time.time()
    m, cells, added, (xs, ys) = setup(d, cfg)
    j = m.add_device(0, cells, 1.0)  # R_jt = 1 K/W placeholder; the real R_jt adds in series
    m.build(h_top, h_bot)
    q = np.zeros(m.N); q[j] = 1.0
    T = m.solve(q)
    tab_rise = T[j] - 1.0  # rise of the tab copper (mean) per watt
    print('%s h_top=%.1f h_bot=%.1f: tab-to-ambient %.2f K/W  (nodes %d, %.0f s, tab cells %d, added vias %d)'
          % (cfg, h_top, h_bot, tab_rise, m.N, time.time() - t, len(cells), len(added)))
    print('  energy balance: surface loss %.4f W for 1 W in' % m.surface_loss(T, h_top, h_bot))
    for x, y, lay in added:
        if len(lay) < 2:
            print('  via at (%.2f, %.2f) joins only %s' % (x, y, lay))
    for R in (8.1, 15.0, 0.8, 4.0):
        print('  theta_JA with R_jt %.1f: %.1f K/W' % (R, tab_rise + R))
    if '--save' in sys.argv:
        name = sys.argv[sys.argv.index('--save') + 1]
        np.savez_compressed('work/T_%s.npz' % name, F=m.layer_map(T, 0), B=m.layer_map(T, m.nl - 1),
                            In1=m.layer_map(T, 1), xs=xs, ys=ys, tab=tab_rise)
