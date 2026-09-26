"""Rank psa4/psa5 results: legal first, then agreed goals met, then weighted distance miss.

  python prank.py CONFIG.json RESULT.json [RESULT.json ...]

Legality uses CONFIG's rules (tall_tab_mm, tall_standoff_mm, far_mm, zones, card_zones) with unweighted totals:
overlap/outside < 0.01 mm2, keep-out intrusion < 0.01 mm, card and zone area < 0.01 mm2, screw distance < 0.01 mm.
Goals are the config's goals (the ptable --goals column): a path counts as met when its distance <= its limit.
"""
import sys, json, os, runpy, tempfile

cfgp, results = sys.argv[1], sys.argv[2:]
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
rows = []
for rp in results:
    res = json.load(open(rp))
    if 'layout' not in res:
        print('skipped (not a result): %s' % rp)
        continue
    cfg = json.load(open(cfgp))
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
    g = runpy.run_path(os.path.join(here, 'psa5.py'))
    refs, scr = g['refs'], g['screws']()
    ov = sum(g['part_ov'](p, half_pairs=True) for p in refs)
    ko = sum(g['part_ko'](p, scr) for p in refs)
    cd = sum(g['part_card'](p) for p in refs) + g['card_self']()
    far = g['far_rule'](scr)
    met = 0
    miss = 0.0
    for i, (a, pa, b, pb, lim, wgt) in enumerate(g['TG']):
        A, B = g['pad_pos'](a, pa), g['pad_pos'](b, pb)
        dd = ((A[0] - B[0]) ** 2 + (A[1] - B[1]) ** 2) ** 0.5
        met += dd <= lim + 1e-9
        miss += wgt * max(0.0, dd - lim)
    legal = ov < 0.01 and ko < 0.01 and cd < 0.01 and far < 0.01
    rows.append((not legal, -met, miss, os.path.basename(rp), ov, ko, cd, far, len(g['TG'])))
rows.sort()
print('%-26s %-5s %5s %8s %8s %8s %8s %8s' % ('result', 'legal', 'goals', 'miss', 'ov mm2', 'ko mm', 'card', 'far mm'))
for nl, nmet, miss, name, ov, ko, cd, far, n in rows:
    print('%-26s %-5s %2d/%-2d %8.1f %8.2f %8.2f %8.2f %8.2f' % (name, 'yes' if not nl else 'no', -nmet, n, miss, ov, ko, cd, far))
