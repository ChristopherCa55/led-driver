"""Check psa5's local move costing against full re-evaluation, and report typical move deltas.

  python tdelta.py CONFIG.json [moves] [seed]

Loads the psa5 model (random_init as configured), makes random single-mover moves (shift or rotation),
and compares mover_local(after) - mover_local(before) with total(after) - total(before) for each.
Prints the worst disagreement (must be ~0) split by movers that own a screw point, and delta percentiles.
"""
import sys, os, runpy, random

cfgp = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
seed = sys.argv[3] if len(sys.argv) > 3 else '7'
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
sys.argv = ['psa5.py', cfgp, os.path.join(os.environ.get('TEMP', '.'), 'tdelta_out'), seed]
g = runpy.run_path(os.path.join(here, 'psa5.py'))
rng = random.Random(1)
worst = {True: 0.0, False: 0.0}
deltas = []
for k in range(n):
    name = rng.choice(g['NAMES_MOVE'])
    old = list(g['MOVERS'][name]['pl'])
    x, y, a = old
    if rng.random() < 0.15:
        a = (a + rng.choice((90, 180, 270))) % 360
    else:
        x += rng.gauss(0, 6)
        y += rng.gauss(0, 6)
    t0, l0 = g['total'](), g['mover_local'](name, g['screws']())
    g['place'](name, (x, y, a))
    t1, l1 = g['total'](), g['mover_local'](name, g['screws']())
    err = abs((l1 - l0) - (t1 - t0))
    own = g['owns_screw'](name)
    worst[own] = max(worst[own], err)
    deltas.append(abs(t1 - t0))
    if rng.random() < 0.5:
        g['place'](name, old)
deltas.sort()
print('worst |local - full| delta: screw movers %.3g, others %.3g (over %d moves)' % (worst[True], worst[False], n))
print('|delta| percentiles 25/50/75/90: %.0f / %.0f / %.0f / %.0f; total now %.0f' % tuple(
    [deltas[int(q * (len(deltas) - 1))] for q in (0.25, 0.5, 0.75, 0.9)] + [g['total']()]))
