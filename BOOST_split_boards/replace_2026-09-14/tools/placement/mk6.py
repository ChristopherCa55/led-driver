"""psa4 config after check-in 3 (user decisions 2026-09-15).

  python mk6.py SEED_RESULT.json OUT.json explore|legal [iters] [T0]

Changes from mk5:
  - LED pad pairs J3/J4, J8/J7, J5/J6 on the bottom edge, left half (zone x 30-67, y 109-116).
  - Lugs J1/J2 movable on the right edge below the notch (zone x 93.5-104, y 50-88); the cable corner
    (no L1, output cans or card) covers x 88-104, y 30-52 so the 10 AWG cable can run down to the lugs.
  - Control card anywhere (x 30-62, y 31-74), not over L1, not in the cable corner.
  - M2-M7: 25 mm to the nearest screw (tab screw or card standoff).
  - Goals with priorities (limit mm, weight): hard on rail FET -> own caps, D19 at M1, R1 Kelvin, sink loop;
    loose on input caps (20 mm) and switch-node drains other than M1 (22 mm, light weight).
Seed: macros and singles from SEED_RESULT where present; LED pads and lugs re-seeded into their new zones.
"""
import sys, json

seed = json.load(open(sys.argv[1]))
phase = sys.argv[3]
iters = int(sys.argv[4]) if len(sys.argv) > 4 else 200000
T0 = float(sys.argv[5]) if len(sys.argv) > 5 else (30.0 if phase == 'explore' else 3.0)
lay = seed['layout']
mv = seed.get('movers', {})

PAIRS = {'PAIR_1': ('M7', 'M2'), 'PAIR_2': ('M6', 'M3'), 'PAIR_3': ('M5', 'M4')}
SINKS = {'SINK_1': ('M10', 'R52'), 'SINK_2': ('M9', 'R53'), 'SINK_3': ('M8', 'R7')}
LEDS = {'LED_1': ('J3', 'J4'), 'LED_2': ('J8', 'J7'), 'LED_3': ('J5', 'J6')}
LED_SEED = {'LED_1': [33.0, 113.0, 90], 'LED_2': [44.5, 113.0, 90], 'LED_3': [56.0, 113.0, 90]}

macros = {}
for name, (lx, rail) in PAIRS.items():
    macros[name] = dict(members=[[lx, 0, 0, 180, 'B'], [rail, -12.7, 0, 0, 'B']],
                        init=mv.get(name, [lay[lx][0], lay[lx][1], (lay[lx][2] - 180) % 360]))
for name, (fet, sh) in SINKS.items():
    macros[name] = dict(members=[[fet, 0, 0, 180, 'B'], [sh, -5.08, -5.94, 90, 'F']],
                        init=mv.get(name, [lay[fet][0], lay[fet][1], (lay[fet][2] - 180) % 360]))
for name, (an, ca) in LEDS.items():
    keep = mv.get(name) if phase == 'legal' else None
    macros[name] = dict(members=[[an, 0, 0, 0, 'F'], [ca, 0, 6.5, 0, 'F']], init=keep or LED_SEED[name])

SIDES = {'M1': 'B', 'U19': 'B', 'U15': 'B', 'U10': 'B', 'U8': 'B', 'D19': 'B'}
names = ['L1', 'R1', 'U25', 'C40', 'C69', 'C85', 'D19', 'C70', 'C86', 'C88', 'C71', 'C78', 'C87', 'C74', 'C75', 'C77',
         'M1', 'U19', 'U15', 'U10', 'U8', 'U16', 'J10', 'H5', 'H6', 'H7', 'H8', 'J1', 'J2']
init = {}
for r in names:
    side = SIDES.get(r, 'F')
    if r in ('J1', 'J2') and phase == 'explore':
        init[r] = [99.0, 58.0 if r == 'J1' else 70.0, 0, 'F']
    else:
        init[r] = list(lay[r][:3]) + [side] if r in lay else [80.0, 60.0, 0, side]
singles = {r: v[3] for r, v in init.items()}
zones = {j: [30.0, 109.0, 67.0, 116.0] for j in ('J3', 'J4', 'J8', 'J7', 'J5', 'J6')}
zones.update({'J1': [93.5, 50.0, 104.0, 88.0], 'J2': [93.5, 50.0, 104.0, 88.0]})
goals = {
    # substring of the pcheck label -> [limit mm, weight]; later matches win, so strict entries come last
    'OUTA -> M': [15.0, 1.0], 'OUTB -> M': [15.0, 1.0],
    'drain -> J': [15.0, 1.0],
    # loose: input caps carry smooth ripple current; far switch-node drains
    'GND -> M1 source': [20.0, 1.0], 'Vin -> R1 Vin force pad': [20.0, 1.0],
    'L1 LX pad -> M7 drain': [22.0, 0.7], 'L1 LX pad -> M6 drain': [22.0, 0.7], 'L1 LX pad -> M5 drain': [22.0, 0.7],
    # hard: rail FET -> its own caps (the commutation loop), M1 clamp and gate, Kelvin sense
    ' drain -> C': [15.0, 3.0],
    'L1 LX pad -> M1 drain': [15.0, 3.0],
    'R1 rsense_lo pad -> L1.2': [10.0, 2.0], 'U25 IN': [10.0, 2.0],
    'U19 OUTA -> M1 gate': [12.0, 2.0],
    'D19 LX -> M1 drain': [5.5, 3.0], 'D19 GND -> M1 source': [5.5, 3.0],
}
cfg = dict(fixed={}, singles=singles, init=init, macros=macros,
           swap_groups=[['C70', 'C86', 'C88', 'C71', 'C78', 'C87', 'C74', 'C75', 'C77'],
                        ['SINK_1', 'SINK_2', 'SINK_3'], ['LED_1', 'LED_2', 'LED_3'], ['C85', 'C40', 'C69'], ['J1', 'J2']],
           zones=zones, in_card=['J10', 'H5', 'H6', 'H7', 'H8'], screwed=['M1', 'M8', 'M9', 'M10'],
           corner=[88.0, 30.0, 104.0, 52.0], far_mm=25.0, goals=goals,
           card_size=42, card_x=30.0, card_x0=seed['card'][0], card_x_range=[30.0, 62.0], card_y_range=[31.0, 74.0],
           card_y0=seed['card'][1], iters=iters, T0=T0,
           T1=0.02 if phase == 'explore' else 0.005, step0=8.0 if phase == 'explore' else 2.0)
if phase == 'legal':
    cfg['weights'] = dict(ov=400.0, ko=300.0, card=400.0, t=10.0, far=3.0)
json.dump(cfg, open(sys.argv[2], 'w'), indent=1)
print('mk6 %s config: %d singles, %d macros, iters %d, T0 %g' % (phase, len(singles), len(macros), iters, T0))
