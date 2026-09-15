"""psa4 config after check-in 4: J10 fixed first inside a 45 mm card, FET-free underside beneath it.

  python mk7.py MK6_CONFIG.json SEED_RESULT.json CANDIDATE OUT.json [iters] [T0]

MK6_CONFIG: a config written by mk6.py (goals, zones, corner, far_mm, swap groups, macro geometry).
SEED_RESULT: the layout to start from (p6l_1). CANDIDATE: one of L, R, C, T, B (J10 position in the card).

Card: 45 x 45 mm, fixed, centred where the 42 mm card of the seed was centred. J10 (PinSocket 2x15,
courtyard x -1.815..4.365, y -1.825..37.385 at rot 0) is a fixed part, so its through-hole courtyard on B.Cu
keeps every FET body and bottom-side part out from under it. Standoffs H5-H8 start 4 mm in from the card
corners and stay movable inside the card. Candidates (pin 1 position):
  L  vertical, 8 mm inboard of the card's left inner edge (clear of the left standoffs)
  R  vertical, 8 mm inboard of the right inner edge
  C  vertical, centred
  T  horizontal (rot 90), 8 mm below the top inner edge
  B  horizontal (rot 90), 8 mm above the bottom inner edge
"""
import sys, json

base = json.load(open(sys.argv[1]))
seed = json.load(open(sys.argv[2]))
cand = sys.argv[3]
out = sys.argv[4]
iters = int(sys.argv[5]) if len(sys.argv) > 5 else 150000
T0 = float(sys.argv[6]) if len(sys.argv) > 6 else 20.0

CS = 45.0
cx0 = seed['card'][0] + seed.get('card_size', 42) / 2.0
cy0 = seed['card'][1] + seed.get('card_size', 42) / 2.0
card = [cx0 - CS / 2, cy0 - CS / 2]
il, it_, ir, ib = card[0] + 2, card[1] + 2, card[0] + CS - 2, card[1] + CS - 2     # inner edges
vert_y = it_ + 1.825 + (ib - it_ - 39.21) / 2                                       # courtyard centred vertically
horz_x = il + 1.825 + (ir - il - 39.21) / 2                                         # courtyard centred horizontally
pos = {
    'L': [il + 8 + 1.815, vert_y, 0],
    'R': [ir - 8 - 4.365, vert_y, 0],
    'C': [(il + ir) / 2 - 1.27, vert_y, 0],
    'T': [horz_x, it_ + 8 + 4.365, 90],      # rot 90: courtyard y from pin1.y - 4.365 to pin1.y + 1.815
    'B': [horz_x, ib - 8 - 1.815, 90],
}[cand]

cfg = dict(base)
lay = seed['layout']
mv = seed.get('movers', {})
cfg['fixed'] = dict(base.get('fixed', {}))
cfg['fixed']['J10'] = pos + ['F']
singles = {k: v for k, v in base['singles'].items() if k != 'J10'}
init = {}
for r, side in singles.items():
    if r in ('H5', 'H6', 'H7', 'H8'):
        continue
    init[r] = list(lay[r][:3]) + [side] if r in lay else base['init'][r]
for h, (x, y) in zip(('H5', 'H6', 'H7', 'H8'), ((card[0] + 4, card[1] + 4), (card[0] + CS - 4, card[1] + 4),
                                               (card[0] + 4, card[1] + CS - 4), (card[0] + CS - 4, card[1] + CS - 4))):
    init[h] = [x, y, 0, 'F']
macros = {}
for name, m in base['macros'].items():
    macros[name] = dict(members=m['members'], init=mv.get(name, m['init']))
cfg.update(singles=singles, init=init, macros=macros, in_card=['H5', 'H6', 'H7', 'H8'],
           card_size=CS, card_x0=card[0], card_y0=card[1], card_x_range=[card[0], card[0]],
           card_y_range=[card[1], card[1]], card_fixed=True, iters=iters, T0=T0, T1=0.02, step0=6.0)
cfg.pop('weights', None)
cfg.pop('only_move', None)
json.dump(cfg, open(out, 'w'), indent=1)
print('mk7 candidate %s: card (%.1f, %.1f) %g mm, J10 pin 1 (%.2f, %.2f) rot %d, iters %d, T0 %g' % (
    cand, card[0], card[1], CS, pos[0], pos[1], pos[2], iters, T0))
