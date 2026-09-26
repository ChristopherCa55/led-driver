"""Commutation-loop copper inductance per channel, two ways, from solved branches.

usage: python loop_inductance.py SOLVED_B.json SOLVED_C.json

1. Coupled over-plane model (this board's layers): for each forward leg (M1 drain -> LX FET drain; shared
   sources; rail FET drain -> ceramics) the solver sums the sheet currents of all layers at each point and uses
   the current-weighted height to the nearest GND plane: L = mu0 * integral(h_eff * |Js|^2 dA) / I^2. The GND
   return in the planes is the image of the forward legs and is not added.
2. The audit's method (BOOST_AUDIT.md item 4), for comparison with the 4.85 / 12.74 / 7.91 nH the simulations
   used: L = mu0 * 0.221 mm * squares, squares = leg resistance / 1 oz sheet resistance (0.491 mOhm), all four
   legs including the GND return (ceramic GND pads -> M1 source), resistances from the 1 oz solve.
Neither includes via barrels, pads, the FET leads or the die (the simulation's package model covers those).
"""
import json, sys, math
MU0 = 4e-7 * math.pi * 1e-3          # H/mm
RSHEET_1OZ = 1.72e-5 / 0.035          # ohm per square
LOOPS = {'ch1': ['loop LX M1->M7', 'm2_source M7->M2', 'loop Vout_1 M2->ceramics', 'loop GND ch1 ceramics->M1'],
         'ch2': ['loop LX M1->M6', 'm3_source M6->M3', 'loop Vout_2 M3->ceramics', 'loop GND ch2 ceramics->M1'],
         'ch3': ['loop LX M1->M5', 'm4_source M5->M4', 'loop Vout_3 M4->ceramics', 'loop GND ch3 ceramics->M1']}
SIM = {'ch1': 4.85, 'ch2': 12.74, 'ch3': 7.91}
out = {}
resB = {r['name']: r for r in json.load(open(sys.argv[1]))}
resC = {r['name']: r for r in json.load(open(sys.argv[2]))}
for ch, legs in LOOPS.items():
    fwd = legs[:3]
    lB = sum(resB[n].get('L_overplane_nH', 0) for n in fwd if n in resB)
    lC = sum(resC[n].get('L_overplane_nH', 0) for n in fwd if n in resC)
    sq = sum(resB[n]['R_mohm'] * 1e-3 / RSHEET_1OZ for n in legs if n in resB and 'R_mohm' in resB[n])
    la = MU0 * 0.221 * sq * 1e9
    detail = ', '.join('%s %.3f mOhm' % (n.split(' ', 1)[1], resB[n]['R_mohm']) for n in legs if n in resB and 'R_mohm' in resB[n])
    out[ch] = dict(overplane_B=lB, overplane_C=lC, audit_method=la, squares=sq, sim=SIM[ch])
    print('%s: over-plane %.2f nH (1 oz stack) / %.2f nH (2 oz stack); audit method %.2f nH (%.1f squares); '
          'simulated with %.2f nH  [%s]' % (ch, lB, lC, la, sq, SIM[ch], detail))
json.dump(out, open(sys.argv[1].replace('_B.json', '_L.json'), 'w'), indent=1)
