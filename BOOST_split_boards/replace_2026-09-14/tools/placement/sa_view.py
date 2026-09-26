"""Render an optimizer result: python sa_view.py RESULT.json CONFIG.json OUT.png"""
import sys, json
import pplot

res = json.load(open(sys.argv[1]))
cfg = json.load(open(sys.argv[2]))
L = {k: tuple(v) for k, v in res['layout'].items()}
cs = res['card_size']
card = (res['card'][0], res['card'][1], res['card'][0] + cs, res['card'][1] + cs)
if all(h in L for h in ('H5', 'H6', 'H7', 'H8')):
    scr = {h: L[h][:2] for h in ('H5', 'H6', 'H7', 'H8')}
else:
    scr = {'H%d' % i: p for i, p in enumerate(((card[0] + 4, card[1] + 4), (card[2] - 4, card[1] + 4),
                                               (card[0] + 4, card[3] - 4), (card[2] - 4, card[3] - 4)), 5)}
meta = dict(screws=scr, screwed=cfg['screwed'], card=card, corner=cfg['corner'], far_mm=cfg.get('far_mm', 15.0),
            tall_tab_mm=cfg.get('tall_tab_mm', 5.5), tall_standoff_mm=cfg.get('tall_standoff_mm', 5.5))
lines, msgs = pplot.run(L, meta, sys.argv[3], sys.argv[1].split('/')[-1])
print('card', [round(v, 1) for v in card])
print('\n'.join(l for l in lines if 'MISS' in l))
print('targets met %d / %d' % (sum('ok' in l for l in lines), len(lines)))
print('--- %d mechanical messages' % len(msgs))
print('\n'.join(msgs[:50]))
