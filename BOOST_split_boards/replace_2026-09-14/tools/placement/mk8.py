"""psa4 refinement config: legality first (weight ramp), standoffs kept near the card corners.

  python mk8.py CONFIG.json RESULT.json OUT.json [iters] [T0] [corner_mm]

CONFIG: a p7 config (mk7: J10 fixed, 45 mm card fixed). RESULT: the layout to start from.
- Starts every single part and macro at its RESULT position.
- Standoffs H5-H8: each keeps to a corner_mm square in its own card corner (default 17 mm), on top of the
  in_card 2 mm margin, so the four points span the card (centres 5.5-13.5 mm in from both edges). The p7
  runs had no such rule and the annealer lined the standoffs up to serve the screw-distance rule.
- Weights: base ov 20, t 10, ko 30, far 10, card 20; ramp x10 on ov, ko, far and card by 80 % of the run,
  so the final state pays 200 per mm2 of overlap, 300 per mm of keep-out intrusion and 100 per mm beyond
  the screw-distance limit, against 10 per mm of target miss.
"""
import sys, json

cfg = json.load(open(sys.argv[1]))
res = json.load(open(sys.argv[2]))
out = sys.argv[3]
iters = int(sys.argv[4]) if len(sys.argv) > 4 else 150000
T0 = float(sys.argv[5]) if len(sys.argv) > 5 else 30.0
Z = float(sys.argv[6]) if len(sys.argv) > 6 else 17.0

lay, mv = res['layout'], res.get('movers', {})
for r, side in cfg['singles'].items():
    if r in lay:
        cfg['init'][r] = list(lay[r][:3]) + [side]
for n in cfg['macros']:
    if n in mv:
        cfg['macros'][n]['init'] = mv[n]
cs = cfg['card_size']
cx, cy = cfg['card_x0'], cfg['card_y0']
corners = {'H5': (cx, cy), 'H6': (cx + cs - Z, cy), 'H7': (cx, cy + cs - Z), 'H8': (cx + cs - Z, cy + cs - Z)}
zones = dict(cfg.get('zones', {}))
for h, (x, y) in corners.items():          # as mk7: H5 top-left, H6 top-right, H7 bottom-left, H8 bottom-right
    zones[h] = [x, y, x + Z, y + Z]
    cfg['init'][h] = [x + Z / 2, y + Z / 2, 0, 'F']
cfg.update(zones=zones, iters=iters, T0=T0, T1=0.02, step0=6.0,
           weights=dict(ov=20.0, t=10.0, ko=30.0, far=10.0, card=20.0),
           ramp=dict(ov=10.0, ko=10.0, far=10.0, card=10.0), ramp_end=0.8)
json.dump(cfg, open(out, 'w'), indent=1)
print('mk8: %s from %s, iters %d, T0 %g, standoff corner squares %g mm' % (out, sys.argv[2], iters, T0, Z))
