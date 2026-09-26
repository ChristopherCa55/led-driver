"""Distance from each FET body centre to the nearest fixing, and the residual bow there. Run from tools/placement
(PMODEL_INV=inv_power5.json, KiCad python); writes fetfix.json next to this script for pad_stack.py."""
import json, math, os, sys
sys.path.insert(0, os.getcwd())
import pmodel as M
lay = json.load(open('p15/p15_b10_k2_st.json'))
L = lay['layout']
fix = {'H%d' % (i + 5): tuple(p) for i, p in enumerate(lay['standoffs'])}
for m in lay['screwed']:
    fix[m + ' tab'] = M.tab_hole(L, m)
out = {}
for f in sorted(M.FETS):
    cx, cy = M.body_centre(L, f)
    name, dist = min(((k, math.hypot(cx - x, cy - y)) for k, (x, y) in fix.items()), key=lambda t: t[1])
    out[f] = dist
    # IPC-6012 bow limit b (fraction of length) over the 86 mm board: arc radius R = L / (8 b); deviation c^2 / 2R
    dev = {b: dist ** 2 / (2 * 86.0 / (8 * b)) for b in (0.0075, 0.005)}
    print('%-4s body centre (%.1f, %.1f): nearest fixing %-7s %5.1f mm; bow at 0.75 %% %.3f mm, at 0.50 %% %.3f mm'
          % (f, cx, cy, name, dist, dev[0.0075], dev[0.005]))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fetfix.json'), 'w'))
