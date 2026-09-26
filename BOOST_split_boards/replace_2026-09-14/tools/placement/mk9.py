"""psa5 global-search config: random start, card and J10 free, legality-first weight ramp.

  python mk9.py BASE_CONFIG.json OUT.json [iters] [T0] [step0] [corner_mm]

BASE_CONFIG: any p7 config (goals, macros, swap groups, zones, corner, far_mm, screwed come from it).
- J10 becomes a movable single inside the card (in_card, any 90-degree rotation); nothing is fixed. The
  overlap term still keeps FET bodies and bottom parts out from under its pins.
- The 45 mm card moves over the whole board (x 30-59, y 30-71); the corner rule keeps it out of the lug
  corner and the L1 rule keeps it off L1.
- Standoffs H5-H8 keep to corner_mm squares in their own card corners (card_zones, moving with the card).
- random_init: every mover starts at a random position and rotation.
- Weights: base ov 20, t 10, ko 30, far 10, card 20; ramp x10 on ov, ko, far and card by 80 % of the run.
"""
import sys, json

base = json.load(open(sys.argv[1]))
out = sys.argv[2]
iters = int(sys.argv[3]) if len(sys.argv) > 3 else 400000
T0 = float(sys.argv[4]) if len(sys.argv) > 4 else 300.0
step0 = float(sys.argv[5]) if len(sys.argv) > 5 else 15.0
Z = float(sys.argv[6]) if len(sys.argv) > 6 else 17.0
CS = 45.0

cfg = dict(base)
cfg['fixed'] = {}
cfg['singles'] = dict(base['singles'], J10='F')
cfg['init'] = dict(base['init'], J10=[60.0, 80.0, 0, 'F'])
cfg['zones'] = {k: v for k, v in base.get('zones', {}).items() if k not in ('H5', 'H6', 'H7', 'H8')}
cfg['card_zones'] = {'H5': [0, 0, Z, Z], 'H6': [CS - Z, 0, CS, Z], 'H7': [0, CS - Z, Z, CS], 'H8': [CS - Z, CS - Z, CS, CS]}
cfg.update(in_card=['H5', 'H6', 'H7', 'H8', 'J10'], card_size=CS, card_fixed=False,
           card_x0=40.0, card_y0=60.0, card_x_range=[30.0, 104.0 - CS], card_y_range=[30.0, 116.0 - CS],
           random_init=True, iters=iters, T0=T0, T1=0.02, step0=step0,
           weights=dict(ov=20.0, t=10.0, ko=30.0, far=10.0, card=20.0),
           ramp=dict(ov=10.0, ko=10.0, far=10.0, card=10.0), ramp_end=0.8)
cfg.pop('only_move', None)
json.dump(cfg, open(out, 'w'), indent=1)
print('mk9: %s, iters %d, T0 %g, step0 %g, standoff corner squares %g mm' % (out, iters, T0, step0, Z))
