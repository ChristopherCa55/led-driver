"""Sense nets over GND on the power board: share of each sense net's track length with GND copper directly above or
below it on an adjacent copper layer (plane_cover.py's test, applied per net).

    python sense_cover.py COPPER.json [COPPER.json ...]

Rebuilt 2026-10-11 because the 10-02 readiness review's script is gone. The net list and the method were checked
against that review's figures on the same board before use (see the review_fixes README).
"""
import json, sys
import numpy as np
from matplotlib.path import Path

SENSE = ['SNS_CH1', 'SNS_CH2', 'SNS_CH3', 'ISNS_P', 'ISNS_N', 'Current', 'IREF1_input', 'IREF2_input', 'IREF3_input']


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


def run(fn):
    cop = json.load(open(fn))
    L = cop['layers']
    paths = {l: gnd_paths(cop, l) for l in L}
    tot, cov = {}, {}
    for t in cop['tracks']:
        n = t['net']
        if n not in SENSE:
            continue
        i = L.index(t['layer'])
        nb = [L[k] for k in (i - 1, i + 1) if 0 <= k < len(L)]
        ln = float(np.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']))
        k = max(2, int(ln / 0.1) + 1)
        pts = np.column_stack([np.linspace(t['x0'], t['x1'], k), np.linspace(t['y0'], t['y1'], k)])
        hit = np.zeros(k, bool)
        for b in nb:
            hit |= covered(paths[b], pts)
        tot[n] = tot.get(n, 0) + ln
        cov[n] = cov.get(n, 0) + ln * hit.mean()
    print('== %s' % fn)
    for n in SENSE:
        if n in tot:
            print('  %-12s %6.1f mm  %3.0f %% over GND' % (n, tot[n], 100 * cov[n] / tot[n]))
    T, C = sum(tot.values()), sum(cov.values())
    print('  %-12s %6.1f mm  %3.0f %% over GND' % ('all', T, 100 * C / T))
    return {n: (tot[n], cov[n] / tot[n]) for n in tot}, C / T


if __name__ == '__main__':
    for f in sys.argv[1:]:
        run(f)
