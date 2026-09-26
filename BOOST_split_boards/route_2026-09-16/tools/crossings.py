"""Where the routed board's new tracks and vias cut power copper (system Python).

usage: python crossings.py UNROUTED_CU.json ROUTED_CU.json SHEET_CURRENT.npz [OUT.json]

A new track cell counts as a crossing when, on the unrouted board, another net's zone or fill lies under the track's
width plus clearance and that copper carries more than route_signals.J_FORBID A/mm (the solver's sheet current,
spread as the router spreads it). Crossing cells are grouped per net and layer into runs; each run reports its length,
peak sheet current and position. New vias are listed per net with the peak current on any layer they pierce.
"""
import json, math, sys, collections
import numpy as np
from scipy import ndimage

sys.path.insert(0, __file__.rsplit('\\', 1)[0] if '\\' in __file__ else __file__.rsplit('/', 1)[0])
import route_signals as R

base = json.load(open(sys.argv[1]))
routed = json.load(open(sys.argv[2]))
bd = R.Board(base)
bd.load_jmap(sys.argv[3])
key = lambda v: (round(v['x'], 3), round(v['y'], 3))
old = {key(v) for v in base['vias']}
reach = int(math.ceil(0.5 / R.H))

runs = []
for t in routed['tracks']:
    l = R.LI[t['layer']]
    if l not in bd.jcut:
        continue
    n = bd.nid[t['net']]
    steps = max(1, int(math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']) / R.H))
    hot = []
    for s_ in range(steps + 1):
        x = t['x0'] + (t['x1'] - t['x0']) * s_ / steps
        y = t['y0'] + (t['y1'] - t['y0']) * s_ / steps
        i, j = R.cell(x, y)
        win = (slice(max(j - reach, 0), j + reach + 1), slice(max(i - reach, 0), i + reach + 1))
        foreign = ((bd.zonehard[l][win] & (bd.hard[l][win] >= 0) & (bd.hard[l][win] != n)) |
                   ((bd.yld[l][win] >= 0) & (bd.yld[l][win] != n))).any()
        S = float(bd.jcut[l][j, i])
        hot.append((foreign and S > R.J_FORBID, S, x, y))
    k = 0
    while k < len(hot):
        if not hot[k][0]:
            k += 1
            continue
        m = k
        while m + 1 < len(hot) and hot[m + 1][0]:
            m += 1
        seg = hot[k:m + 1]
        smax = max(seg, key=lambda h: h[1])
        runs.append(dict(net=t['net'], layer=t['layer'], width=t['w'], length_mm=round(len(seg) * R.H, 1),
                         max_A_per_mm=round(smax[1], 2), x=round(smax[2], 2), y=round(smax[3], 2)))
        k = m + 1

# merge runs of one net on one layer that touch (consecutive segments of one track path)
merged = []
for r in sorted(runs, key=lambda r: (r['net'], r['layer'], r['x'], r['y'])):
    if merged and merged[-1]['net'] == r['net'] and merged[-1]['layer'] == r['layer'] and \
            math.hypot(merged[-1]['x'] - r['x'], merged[-1]['y'] - r['y']) < merged[-1]['length_mm'] + r['length_mm'] + 0.5:
        m = merged[-1]
        m['length_mm'] = round(m['length_mm'] + r['length_mm'], 1)
        if r['max_A_per_mm'] > m['max_A_per_mm']:
            m.update(max_A_per_mm=r['max_A_per_mm'], x=r['x'], y=r['y'])
    else:
        merged.append(dict(r))

vias = collections.defaultdict(list)
for v in routed['vias']:
    if key(v) in old:
        continue
    n = bd.nid[v['net']]
    i, j = R.cell(v['x'], v['y'])
    worst = 0.0
    for l in bd.jvia:
        win = (slice(max(j - reach, 0), j + reach + 1), slice(max(i - reach, 0), i + reach + 1))
        foreign = ((bd.zonehard[l][win] & (bd.hard[l][win] >= 0) & (bd.hard[l][win] != n)) |
                   ((bd.yld[l][win] >= 0) & (bd.yld[l][win] != n))).any()
        if foreign:
            worst = max(worst, float(bd.jvia[l][j, i]))
    vias[v['net']].append(worst)

print('track crossings of power copper above %.2f A/mm (unrouted-board sheet current):' % R.J_FORBID)
for r in sorted(merged, key=lambda r: -r['max_A_per_mm'] * r['length_mm']):
    print('  %-16s %-7s w %.1f  %4.1f mm  up to %.2f A/mm  at (%.1f, %.1f)' % (
        r['net'], r['layer'].replace('.Cu', ''), r['width'], r['length_mm'], r['max_A_per_mm'], r['x'], r['y']))
print('new vias piercing power copper above %.2f A/mm (count, peak A/mm):' % R.J_FORBID)
vsum = {n: (sum(1 for s in l if s > R.J_FORBID), round(max(l), 2)) for n, l in vias.items()}
for n, (c, pk) in sorted(vsum.items(), key=lambda kv: -kv[1][0]):
    if c:
        print('  %-16s %2d  peak %.2f' % (n, c, pk))
print('total: %d track crossings (%.1f mm), %d vias in copper above %.2f A/mm' % (
    len(merged), sum(r['length_mm'] for r in merged), sum(c for c, _ in vsum.values()), R.J_FORBID))
if len(sys.argv) > 4:
    json.dump(dict(tracks=merged, vias={n: dict(count=c, peak=pk) for n, (c, pk) in vsum.items()}), open(sys.argv[4], 'w'), indent=1)
