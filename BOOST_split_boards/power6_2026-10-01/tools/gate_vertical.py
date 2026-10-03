"""Gate-drive loops: vertical distance from the drive tracks to their return copper, per board and stackup.

    python gate_vertical.py GATES.json COPPER.json STACK [COPPER.json STACK ...]

GATES.json: route_2026-09-16/tools/gate_paths.py output for the 8-layer board (it lists each FET's drive nets).
For every point (0.1 mm) along the drive tracks (driver output -> resistor / diode -> gate), the return copper is the
FET's source net (M2/M7 m2_source, M3/M6 m3_source, M4/M5 m4_source; GND for M1 and M8-M10) on any layer within
1.0 mm in plan view. Reported: the length-weighted mean vertical distance to the nearest such layer (the drive
track's own layer counts as 0 when the return runs beside it), and the share of drive length with no return copper
within 1 mm on any layer.
"""
import json, sys
import numpy as np
from matplotlib.path import Path
sys.path.insert(0, __file__.rsplit('\\', 1)[0] if '\\' in __file__ else __file__.rsplit('/', 1)[0])
from stackups import STACKS

RET = {'M2': 'm2_source', 'M7': 'm2_source', 'M3': 'm3_source', 'M6': 'm3_source', 'M4': 'm4_source',
       'M5': 'm4_source', 'M1': 'GND', 'M8': 'GND', 'M9': 'GND', 'M10': 'GND'}
L8GAPS = [0.109, 0.25, 0.218, 0.25, 0.218, 0.25, 0.109]


def zpos(layers, stack):
    gaps = L8GAPS if stack == 'L8' else STACKS[stack]
    cu = [0.035] + [0.03] * (len(layers) - 2) + [0.035]
    z, acc = {}, 0.0
    for i, l in enumerate(layers):
        z[l] = acc + cu[i] / 2
        acc += cu[i] + (gaps[i] if i < len(gaps) else 0)
    return z


def near(paths, pts, r=1.0):
    """True where a polygon lies within r of the point (tested at the point and 8 offsets)."""
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


gates = json.load(open(sys.argv[1]))
pairs = list(zip(sys.argv[2::2], sys.argv[3::2]))
for fn, stack in pairs:
    cop = json.load(open(fn))
    L = cop['layers']
    z = zpos(L, stack)
    print('== %s, %s' % (fn, stack))
    for g in gates:
        fet = g['fet']
        drive = {g.get('drive_net'), g.get('gate_net')}
        for link in g.get('gate_net_links', []):
            for n in link.get('other_pad_nets', []):
                if n.startswith('Net-(D') or n.startswith('Net-(U'):
                    drive.add(n)
        drive.discard(None)
        ret = RET[fet]
        rpaths = {l: [Path(np.asarray(p)) for p in cop['nets'].get(ret, {}).get(l, []) if not isinstance(p, dict)] for l in L}
        tot = dist = none = 0.0
        for t in cop['tracks']:
            if t['net'] not in drive:
                continue
            ln = float(np.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']))
            k = max(2, int(ln / 0.1) + 1)
            pts = np.column_stack([np.linspace(t['x0'], t['x1'], k), np.linspace(t['y0'], t['y1'], k)])
            best = np.full(k, np.inf)
            for l in L:
                h = near(rpaths[l], pts)
                best = np.where(h, np.minimum(best, abs(z[l] - z[t['layer']])), best)
            tot += ln
            fin = np.isfinite(best)
            none += ln * (~fin).mean()
            if fin.any():
                dist += ln * fin.mean() * best[fin].mean()
        if tot:
            print('  %-4s return %-10s drive %5.1f mm: mean vertical distance %.3f mm, no return within 1 mm %3.0f %%'
                  % (fet, ret, tot, dist / max(tot - none, 1e-9), 100 * none / tot))
