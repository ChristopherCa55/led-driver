"""Cost breakdown of a psa4/psa5 result under its config (which terms and parts dominate).

  python pcost.py RESULT.json CONFIG.json

Loads the psa5 model (a superset of psa4's) on a temporary copy of CONFIG whose init/macro positions and
card position come from RESULT, then prints each weighted term (at the config's final ramp weights) and
the worst parts per term.
"""
import sys, json, os, runpy, tempfile

res = json.load(open(sys.argv[1]))
cfg = json.load(open(sys.argv[2]))
lay, mv = res['layout'], res.get('movers', {})
for r in cfg['singles']:
    if r in lay:
        cfg['init'][r] = list(lay[r][:3]) + [cfg['singles'][r]]
for n in cfg['macros']:
    if n in mv:
        cfg['macros'][n]['init'] = mv[n]
cfg['card_x0'], cfg['card_y0'] = res['card']
cfg['random_init'] = False
tmp = tempfile.mkdtemp()
cp = os.path.join(tmp, 'cfg.json')
json.dump(cfg, open(cp, 'w'))
sys.argv = ['psa5.py', cp, os.path.join(tmp, 'out'), '1']
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
g = runpy.run_path(os.path.join(here, 'psa5.py'))          # run_name is not __main__: model only, no annealing

g['set_weights'](1.0)          # a config with a ramp is judged at its final weights
W, refs = g['W'], g['refs']
scr = g['screws']()
ov = {p: g['part_ov'](p, half_pairs=True) for p in refs}
cd = {p: g['part_card'](p) for p in refs}
ko = {p: g['part_ko'](p, scr) for p in refs}
tg = [(g['tgt'](i), g['TG'][i]) for i in range(len(g['TG']))]
far = g['far_rule'](scr)
cs = g['card_self']()
terms = [('overlap/outside', W['ov'] * sum(ov.values())), ('targets', W['t'] * sum(t for t, _ in tg)),
         ('card/zones', W['card'] * (sum(cd.values()) + cs)), ('screw keep-outs', W['ko'] * sum(ko.values())),
         ('far rule', W['far'] * far)]
print('total %.1f' % g['total']())
for name, v in terms:
    print('  %-16s %8.1f' % (name, v))
for name, dct, w in (('overlap', ov, W['ov']), ('card/zone', cd, W['card']), ('keep-out', ko, W['ko'])):
    top = sorted(((v * w, p) for p, v in dct.items() if v > 1e-6), reverse=True)[:8]
    if top:
        print('  %s: %s' % (name, ', '.join('%s %.0f' % (p, v) for v, p in top)))
top = sorted(((t * W['t'], '%s.%s-%s.%s' % (a, pa, b, pb)) for t, (a, pa, b, pb, lim, wgt) in tg if t > 1e-6), reverse=True)[:10]
print('  targets: %s' % ', '.join('%s %.0f' % (n, v) for v, n in top))
