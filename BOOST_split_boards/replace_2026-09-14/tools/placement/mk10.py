"""psa5 config: legality weights high from the start (no ramp), teleport moves, optional start layout.

  python mk10.py MK9_CONFIG.json OUT.json [iters] [T0] [step0] [p_teleport] [START_RESULT.json]

MK9_CONFIG: a config written by mk9.py (card and J10 free, standoff corner zones).
- Weights ov 200, t 10, ko 300, far 100, card 200 for the whole run: a mm2 of overlap or a mm of keep-out
  intrusion costs 20-30 mm of distance-goal miss, so the search finds legal packings first and then
  shortens paths inside the legal space. The mk9 ramp raised these weights only late, when the
  temperature was too low for the several-part moves that clear a screw circle.
- p_teleport (default 0.03): share of single moves that jump a mover to a random spot.
- With START_RESULT the run starts from that layout (random_init off), for a polish pass.
"""
import sys, json

cfg = json.load(open(sys.argv[1]))
out = sys.argv[2]
iters = int(sys.argv[3]) if len(sys.argv) > 3 else 600000
T0 = float(sys.argv[4]) if len(sys.argv) > 4 else 3000.0
step0 = float(sys.argv[5]) if len(sys.argv) > 5 else 15.0
ptel = float(sys.argv[6]) if len(sys.argv) > 6 else 0.03
start = sys.argv[7] if len(sys.argv) > 7 else None

cfg.update(weights=dict(ov=200.0, t=10.0, ko=300.0, far=100.0, card=200.0), iters=iters, T0=T0, T1=0.05,
           step0=step0, p_teleport=ptel)
cfg.pop('ramp', None)
cfg.pop('ramp_end', None)
if start:
    res = json.load(open(start))
    lay, mv = res['layout'], res.get('movers', {})
    for r, side in cfg['singles'].items():
        if r in lay:
            cfg['init'][r] = list(lay[r][:3]) + [side]
    for n in cfg['macros']:
        if n in mv:
            cfg['macros'][n]['init'] = mv[n]
    cfg['card_x0'], cfg['card_y0'] = res['card']
    cfg['random_init'] = False
json.dump(cfg, open(out, 'w'), indent=1)
print('mk10: %s, iters %d, T0 %g, step0 %g, p_teleport %g, start %s' % (out, iters, T0, step0, ptel, start or 'random'))
