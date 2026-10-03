"""U16 thermal model (u16_thermal_2026-10-01/tools) for any layer count and stackup.

    python thermal6.py board|background COPPER.json STACK h        (run from u16_thermal_2026-10-01)

COPPER.json is an export by u16_thermal_2026-10-01/tools/export_copper.py. STACK is 'L8' (the board file's
8-layer stackup: 0.109 / 0.25 / 0.218 / 0.25 / 0.218 / 0.25 / 0.109) or a JLC 6-layer name from stackups.py.
'board' prints the tab-to-air resistance of U16's TO-263 tab; 'background' the battery-current, lug and other-part
rise at the tab (both as the u16 study, config 'to263').
Note: the u16 study itself ran with 0.109 mm for the two 0.218 mm (two-ply) gaps; this wrapper uses the real values.
"""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, 'tools')
from stackups import STACKS
import run_board

mode, cop, stack, h = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
if stack == 'L8':
    run_board.T_CU = [0.035] + [0.030] * 6 + [0.035]
    run_board.T_D = [0.109, 0.25, 0.218, 0.25, 0.218, 0.25, 0.109]
else:
    run_board.T_CU = [0.035] + [0.030] * 4 + [0.035]
    run_board.T_D = list(STACKS[stack])
print('stack %s: copper %s, gaps %s' % (stack, run_board.T_CU, run_board.T_D))
if mode == 'board':
    # run_board.py's own __main__ logic, through the patched module (runpy would reset T_CU / T_D)
    import numpy as np
    from raster import load
    hh = float(h)
    m, cells, added, _ = run_board.setup(load(cop), 'to263')
    j = m.add_device(0, cells, 1.0)
    m.build(hh, hh)
    q = np.zeros(m.N); q[j] = 1.0
    T = m.solve(q)
    print('%s h=%.0f: tab-to-ambient %.2f K/W (energy balance %.4f W), theta_JA with TI R_jt 0.8: %.1f K/W, '
          'onsemi R_jc 5: %.1f K/W' % (stack, hh, T[j] - 1.0, m.surface_loss(T, hh, hh), T[j] - 0.2, T[j] + 4.0))
else:
    sys.argv = ['run_background.py', cop, 'to263', h]
    runpy.run_path('tools/run_background.py', run_name='__main__')
