"""Hand-placed gate-loop pairs: check a polyline spec against the board and write it as router input.

usage: python handroute.py SPEC.json BASE_CU.json OUT_ROUTES.json [--jmap SHEET_CURRENT.npz]

SPEC: {"tracks": [{"net": ..., "layer": "B.Cu", "w": 1.0, "pts": [[x, y], ...]}, ...],
       "vias":   [{"net": ..., "x":, "y":, "dia": 0.6, "drill": 0.3, "layers": ["F.Cu", "B.Cu"]}, ...]}

Every segment is sampled and checked against the rasterised base board: foreign copper within the track's
half-width plus clearance, and foreign holes. With --jmap the peak sheet current under each track is reported, so a
pair that cuts power copper shows up before the board is built. The output carries "keep": true, so the router
commits these first and never rips them up.
"""
import json, math, sys
import numpy as np

sys.path.insert(0, __file__.rsplit('\\', 1)[0] if '\\' in __file__ else __file__.rsplit('/', 1)[0])
import route_signals as R

spec = json.load(open(sys.argv[1]))
cop = json.load(open(sys.argv[2]))
out = sys.argv[3]
bd = R.Board(cop)
jm = None
if '--jmap' in sys.argv:
    jm = np.load(sys.argv[sys.argv.index('--jmap') + 1])

MARGIN = 0.06
bad = 0
tracks = []
for t in spec['tracks']:
    l = R.LI[t['layer']]
    n = bd.nid[t['net']]
    w = t['w']
    clr = R.rules_for(t['net'], bd.classes)['clr']
    reach = w / 2 + clr + MARGIN
    hits, jpk = {}, 0.0
    pts = t['pts']
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(int(L / 0.05) + 1):
            u = min(1.0, k * 0.05 / L) if L else 0.0
            x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
            i, j = R.cell(x, y)
            rr = int(math.ceil(reach / R.H))
            win = bd.hard[l][max(j - rr, 0):j + rr + 1, max(i - rr, 0):i + rr + 1]
            for v in np.unique(win):
                if v >= 0 and v != n:
                    name = bd.nname[v]
                    hits.setdefault(name, (round(x, 2), round(y, 2)))
            hw = bd.holes[max(j - rr, 0):j + rr + 1, max(i - rr, 0):i + rr + 1]
            for v in np.unique(hw):
                if v >= 0 and v != n:
                    hits.setdefault('hole ' + bd.nname[v], (round(x, 2), round(y, 2)))
            if jm is not None:
                a_ = jm[t['layer'].replace('.', '_')]
                jpk = max(jpk, float(a_[max(j - 3, 0):j + 4, max(i - 3, 0):i + 4].max()))
        tracks.append(dict(net=t['net'], layer=t['layer'], w=w, x0=round(a[0], 3), y0=round(a[1], 3),
                           x1=round(b[0], 3), y1=round(b[1], 3), keep=True))
    ln = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    print('%-16s %-7s w %.2f  %5.1f mm  peak %.2f A/mm%s' % (
        t['net'], t['layer'], w, ln, jpk, ('  CLASH: ' + ', '.join('%s at (%.2f, %.2f)' % (k, v[0], v[1])
                                                                  for k, v in hits.items())) if hits else ''))
    bad += len(hits)
vias = []
for v in spec.get('vias', []):
    n = bd.nid[v['net']]
    i, j = R.cell(v['x'], v['y'])
    rr = int(math.ceil((v['dia'] / 2 + 0.25) / R.H))
    hits = {}
    for l in range(len(R.LAYERS)):
        win = bd.hard[l][max(j - rr, 0):j + rr + 1, max(i - rr, 0):i + rr + 1]
        for x in np.unique(win):
            if x >= 0 and x != n:
                hits.setdefault('%s on %s' % (bd.nname[x], R.LAYERS[l]), 1)
    hw = bd.holes[max(j - rr, 0):j + rr + 1, max(i - rr, 0):i + rr + 1]
    for x in np.unique(hw):
        if x >= 0 and x != n:
            hits.setdefault('hole ' + bd.nname[x], 1)
    jpk = max((float(jm[ln_.replace('.', '_')][max(j - 5, 0):j + 6, max(i - 5, 0):i + 6].max())
               for ln_ in R.LAYERS), default=0.0) if jm is not None else 0.0
    print('via %-12s (%.2f, %.2f) %s  peak %.2f A/mm%s' % (
        v['net'], v['x'], v['y'], '/'.join(v['layers']), jpk,
        ('  CLASH: ' + ', '.join(hits)) if hits else ''))
    bad += len(hits)
    vias.append(dict(net=v['net'], x=v['x'], y=v['y'], dia=v['dia'], drill=v['drill'], layers=v['layers'],
                     keep=True))
json.dump(dict(tracks=tracks, vias=vias, log=[], failures=0), open(out, 'w'), indent=1)
print('%d tracks, %d vias -> %s%s' % (len(tracks), len(vias), out,
                                      '' if not bad else '  (%d clashes above)' % bad))
