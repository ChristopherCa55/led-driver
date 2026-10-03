"""Share of signal-track length with GND copper directly above or below it on an adjacent copper layer.

    python plane_cover.py COPPER.json [COPPER.json ...]     (route_2026-09-16/tools/export_copper.py exports)

Signal tracks: every track not on a power net and not GND (gate drive, sense, logic, the 12 V / 5 V / analog_5V
rails). Points every 0.1 mm along each centre line; a point is covered when GND copper (plane or fill) lies under the
point on the layer directly above or below in the stack. Gate-drive tracks (GATE_*, Net-(M*-G)) are also reported
on their own.
"""
import json, sys
import numpy as np
from matplotlib.path import Path

POWER = {'GND', 'Vin', 'LX', 'rsense_lo', 'm2_source', 'm3_source', 'm4_source', 'Vout_1', 'Vout_2', 'Vout_3',
         'Output1_drain', 'Output2_drain', 'Output3_drain', 'Net-(M8-S)', 'Net-(M9-S)', 'Net-(M10-S)', 'Current'}


def is_gate(n):
    return n.startswith('GATE_') or (n.startswith('Net-(M') and n.endswith('-G)'))


def gnd_paths(cop, layer):
    return [Path(np.asarray(p)) for p in cop['nets'].get('GND', {}).get(layer, []) if not isinstance(p, dict)]


def covered(paths, pts):
    hit = np.zeros(len(pts), bool)
    for p in paths:
        bb = p.get_extents()
        m = (pts[:, 0] >= bb.x0) & (pts[:, 0] <= bb.x1) & (pts[:, 1] >= bb.y0) & (pts[:, 1] <= bb.y1) & ~hit
        if m.any():
            hit[m] = p.contains_points(pts[m])
    return hit


for fn in sys.argv[1:]:
    cop = json.load(open(fn))
    L = cop['layers']
    paths = {l: gnd_paths(cop, l) for l in L}
    tot, cov = {}, {}
    gtot, gcov = {}, {}
    for t in cop['tracks']:
        n = t['net']
        if n in POWER:
            continue
        l = t['layer']
        i = L.index(l)
        nb = [L[k] for k in (i - 1, i + 1) if 0 <= k < len(L)]
        x0, y0, x1, y1 = t['x0'], t['y0'], t['x1'], t['y1']
        ln = float(np.hypot(x1 - x0, y1 - y0))
        k = max(2, int(ln / 0.1) + 1)
        pts = np.column_stack([np.linspace(x0, x1, k), np.linspace(y0, y1, k)])
        hit = np.zeros(k, bool)
        for b in nb:
            hit |= covered(paths[b], pts)
        tot[l] = tot.get(l, 0) + ln
        cov[l] = cov.get(l, 0) + ln * hit.mean()
        if is_gate(n):
            gtot[l] = gtot.get(l, 0) + ln
            gcov[l] = gcov.get(l, 0) + ln * hit.mean()
    print('== %s (%d layers)' % (fn, len(L)))
    for l in L:
        if l in tot:
            print('  %-7s signal %6.0f mm, %3.0f %% over GND   | gate %5.0f mm, %3.0f %%' % (
                l, tot[l], 100 * cov[l] / tot[l], gtot.get(l, 0), 100 * gcov.get(l, 0) / gtot[l] if gtot.get(l) else 0))
    T, C = sum(tot.values()), sum(cov.values())
    GT, GC = sum(gtot.values()), sum(gcov.values())
    print('  all     signal %6.0f mm, %3.0f %% over GND   | gate %5.0f mm, %3.0f %%' % (T, 100 * C / T, GT, 100 * GC / GT))
