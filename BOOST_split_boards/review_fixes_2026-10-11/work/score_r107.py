"""R106 (0603, F side) candidates near J9.7, scored by what would have to move.

Unlike score_r106.py this lets R106 sit in J9's row-1 label row (the labels can move) and reports, per candidate:
  - copper items of other nets closer than their clearance (tracks / flashed vias 0.2, GND 0.25; unflashed via holes
    0.2 from the hole edge, i.e. 0.35 from the centre),
  - same-net via holes that would land inside a pad (via-in-pad),
  - F courtyard overlaps (C102 / R103 / C26 / U3 from the board; J9's pad-hugging courtyard top = the J9 pad tops
    minus MARGIN),
  - J9 row-1 labels whose box overlaps a pad.
R107 / SDA below J9 row 2. The redundant 5V F.Cu stretch (55.825, 94.225)-(58.425, 92.625) is treated as removed.
"""
import json, math, sys

cu = json.load(open('step04/card_cu.json'))
MARGIN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.15
J9_BOT = 99.44 + MARGIN
STRETCH = lambda t: (t['net'] == '5V' and t['layer'] == 'F.Cu' and 55.7 <= min(t['x0'], t['x1']) and
                     max(t['x0'], t['x1']) <= 58.5 and 92.6 <= min(t['y0'], t['y1']) and max(t['y0'], t['y1']) <= 94.3)
NEAR = lambda x, y: 52 <= x <= 66 and 98 <= y <= 104.5
tracks = [t for t in cu['tracks'] if t['layer'] == 'F.Cu' and not STRETCH(t) and (NEAR(t['x0'], t['y0']) or NEAR(t['x1'], t['y1']))]
vias = [v for v in cu['vias'] if NEAR(v['x'], v['y'])]
pads = [p for p in cu['pads'] if 'F.Cu' in p['layers'] and p['ref'] != 'J9' and NEAR(p['x'], p['y'])]
j9 = [p for p in cu['pads'] if p['ref'] == 'J9']
# F courtyards (x1, y1, x2, y2) of the neighbours, from the board (measured earlier)
CRT = json.load(open('crt_below.json'))
# row-1 labels (approx. boxes, size 1 text centred at y 94.075): name -> (x1, x2)
LABELS = {'V2': (51.5, 53.1), 'I1': (54.3, 55.5), 'I3': (56.8, 58.0), 'SDA': (58.35, 60.0), 'GND': (61.5, 64.3)}
LAB_Y = (99.65, 100.8)


def rect_pt(px, py, r):
    x1, y1, x2, y2 = r
    return math.hypot(max(x1 - px, 0, px - x2), max(y1 - py, 0, py - y2))


def seg_rect(t, r):
    return min(rect_pt(t['x0'] + (t['x1'] - t['x0']) * k / 40, t['y0'] + (t['y1'] - t['y0']) * k / 40, r)
               for k in range(41)) - t['w'] / 2


def overl(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


out = []
for cx100 in range(5500, 6500, 5):
    cx = cx100 / 100
    for cy100 in range(10010, 10200, 5):
        cy = cy100 / 100
        for rot in (0, 180):
            crt = (cx - 1.48, cy - 0.73, cx + 1.48, cy + 0.73)
            if crt[1] < J9_BOT:
                continue
            bad_crt = [k for k, r in CRT.items() if overl(crt, r)]
            if bad_crt:
                continue
            p5x = cx - 0.825 if rot == 0 else cx + 0.825
            pSx = cx + 0.825 if rot == 0 else cx - 0.825
            block, vip = set(), set()
            for px, net in ((p5x, '5V'), (pSx, 'SDA')):
                r = (px - 0.4, cy - 0.475, px + 0.4, cy + 0.475)
                for t in tracks:
                    if t['net'] != net and seg_rect(t, r) < (0.25 if t['net'] == 'GND' else 0.2):
                        block.add('trk %s' % t['net'])
                for v in vias:
                    d = rect_pt(v['x'], v['y'], r)
                    tag = '%s(%.3f,%.3f)%s' % (v['net'], v['x'], v['y'], '' if 'F.Cu' in v['layers'] else 'h')
                    if v['net'] == net:
                        if d < 0.15 + 0.05:          # hole inside / touching the pad
                            vip.add(tag)
                        continue
                    flashed = 'F.Cu' in v['layers']
                    need = (0.25 if v['net'] == 'GND' else 0.2) + (v['dia'] / 2 if flashed else v['drill'] / 2)
                    if d < need:
                        block.add(tag)
                for p in pads:
                    if p['net'] == net:
                        continue
                    for poly in p['polys'].get('F.Cu', []):
                        for ring in [poly[0]] if isinstance(poly[0][0], list) else [poly]:
                            d = min(rect_pt(x, y, r) for x, y in ring)
                            if d < 0.2:
                                block.add('pad %s.%s' % (p['ref'], p['num']))
            labs = [k for k, (a, b) in LABELS.items() if overl((a, LAB_Y[0], b, LAB_Y[1]),
                                                               (cx - 1.225, cy - 0.475, cx + 1.225, cy + 0.475))]
            out.append((len(block) + len(vip), sorted(block), sorted(vip), labs, cx, cy, rot))
out.sort(key=lambda o: (o[0], len(o[3]), abs(o[4] - 59.95)))
seen = set()
for n, b, v, labs, cx, cy, rot in out:
    k = (tuple(b), tuple(v), tuple(labs))
    if k in seen:
        continue
    seen.add(k)
    print(n, (cx, cy, rot), 'block', b, 'via-in-pad', v, 'labels', labs)
    if len(seen) >= 25:
        break
