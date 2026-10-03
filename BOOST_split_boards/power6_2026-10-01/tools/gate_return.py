"""Share of a drive path with no return copper within 1 mm on any layer, and its unreturned segments.

    python gate_return.py COPPER.json RETURN_NET NET [NET ...]

Example (M2's gate drive): gate_return.py work/U3_cu.json m2_source "Net-(D11--)" GATE_M2
Points every 0.1 mm along each track; a point is returned when RETURN_NET copper on any layer lies within 1 mm in
plan view (gate_vertical.py's test). Segments over 0.3 mm long that are more than half unreturned are listed.
"""
import json, sys
import numpy as np
from matplotlib.path import Path


def near(paths, pts, r=1.0):
    hit = np.zeros(len(pts), bool)
    offs = [(0, 0)] + [(r * np.cos(a), r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)]
    for p in paths:
        bb = p.get_extents()
        for dx, dy in offs:
            q = pts + (dx, dy)
            m = (q[:, 0] >= bb.x0) & (q[:, 0] <= bb.x1) & (q[:, 1] >= bb.y0) & (q[:, 1] <= bb.y1) & ~hit
            if m.any():
                hit[m] = p.contains_points(q[m])
    return hit


cop = json.load(open(sys.argv[1]))
ret, nets = sys.argv[2], set(sys.argv[3:])
rp = [Path(np.asarray(p)) for l in cop['layers'] for p in cop['nets'].get(ret, {}).get(l, []) if not isinstance(p, dict)]
tot = bad = 0.0
segs = []
for t in cop['tracks']:
    if t['net'] not in nets:
        continue
    ln = float(np.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']))
    k = max(2, int(ln / 0.1) + 1)
    pts = np.column_stack([np.linspace(t['x0'], t['x1'], k), np.linspace(t['y0'], t['y1'], k)])
    h = near(rp, pts)
    tot += ln
    bad += ln * (~h).mean()
    if (~h).mean() > 0.5 and ln > 0.3:
        segs.append('  %-12s %-6s (%.1f, %.1f) -> (%.1f, %.1f) %.1f mm' % (t['net'], t['layer'], t['x0'], t['y0'],
                                                                         t['x1'], t['y1'], ln))
print('%s: drive %.1f mm, %.0f %% with no %s within 1 mm' % (sys.argv[1], tot, 100 * bad / tot, ret))
print('\n'.join(segs))
