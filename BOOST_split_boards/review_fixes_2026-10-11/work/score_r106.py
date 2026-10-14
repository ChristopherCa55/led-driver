"""Score candidate R106 (0603, F side) spots above J9 row 1: which copper items would block each one.
Pads 0.8 x 0.95 at +-0.825 (rot 0 or 180 = which side is 5V). Clearance 0.2 (0.25 to GND), hole clearance 0.2 to
unflashed via holes (radius 0.15), courtyard 2.96 x 1.46 must clear the F courtyards of C102 / R103 / C26 (bottoms at
92.46 / 92.49 / 92.32) and J9's pad-hugging courtyard (top 94.65). Pads must stay above the shrunk label row
(label top 93.85 -> pad bottom <= 93.70). The redundant 5V stretch is already gone (scan board)."""
import json, math
cu = json.load(open('step04/card_cu.json'))
REMOVED_5V = lambda t: (t['net'] == '5V' and t['layer'] == 'F.Cu' and 55.7 <= min(t['x0'], t['x1']) and
                        max(t['x0'], t['x1']) <= 58.5 and 92.6 <= min(t['y0'], t['y1']) and max(t['y0'], t['y1']) <= 94.3)
tracks = [t for t in cu['tracks'] if t['layer'] == 'F.Cu' and not REMOVED_5V(t)]
vias = cu['vias']
pads = [p for p in cu['pads'] if 'F.Cu' in p['layers']]
CRT = [(56.07, 57.62, 92.46), (52.32, 55.37, 92.49), (57.62, 60.67, 92.32)]   # x1, x2, bottom


def rect_d(px, py, x1, y1, x2, y2):
    dx = max(x1 - px, 0, px - x2)
    dy = max(y1 - py, 0, py - y2)
    return math.hypot(dx, dy)


def seg_rect(t, x1, y1, x2, y2):
    best = 9
    for k in range(21):
        u = k / 20
        x = t['x0'] + (t['x1'] - t['x0']) * u
        y = t['y0'] + (t['y1'] - t['y0']) * u
        best = min(best, rect_d(x, y, x1, y1, x2, y2))
    return best - t['w'] / 2


res = []
for cx10 in range(5400, 6250, 5):
    cx = cx10 / 100
    for cy10 in range(9290, 9326, 5):
        cy = cy10 / 100
        if cy - 0.73 < 92.49 and cx - 1.48 < 57.62 + 3:      # courtyard tops
            ok = all(not (cx + 1.48 > x1 and cx - 1.48 < x2 and cy - 0.73 < bot) for x1, x2, bot in CRT)
            if not ok:
                continue
        for rot in (0, 180):
            p5 = cx - 0.825 if rot == 0 else cx + 0.825          # 5V pad
            psc = cx + 0.825 if rot == 0 else cx - 0.825         # SCL pad
            block = []
            for (px, net) in ((p5, '5V'), (psc, 'SCL')):
                x1, y1, x2, y2 = px - 0.4, cy - 0.475, px + 0.4, cy + 0.475
                for t in tracks:
                    if t['net'] in (net,):
                        continue
                    need = 0.25 if t['net'] == 'GND' else 0.2
                    if seg_rect(t, x1, y1, x2, y2) < need:
                        block.append('track %s' % t['net'])
                for v in vias:
                    if v['net'] == net:
                        continue
                    flashed = 'F.Cu' in v['layers']
                    r = v['dia'] / 2 if flashed else v['drill'] / 2
                    need = (0.25 if v['net'] == 'GND' else 0.2)
                    if rect_d(v['x'], v['y'], x1, y1, x2, y2) - r < need:
                        block.append('via %s (%.3f, %.3f)' % (v['net'], v['x'], v['y']))
                for p in pads:
                    if p['net'] == net:
                        continue
                    if rect_d(p['x'], p['y'], x1, y1, x2, y2) < 1.25 and p['ref'] == 'J9':
                        block.append('pad J9.%s' % p['num'])
            res.append((len(set(block)), sorted(set(block)), cx, cy, rot))
res.sort(key=lambda r: (r[0], abs(r[2] - 57.6)))
seen = set()
for n, b, cx, cy, rot in res:
    k = tuple(b)
    if k in seen:
        continue
    seen.add(k)
    print(n, (cx, cy, rot), b)
    if len(seen) > 14:
        break
