"""Overlay check: the control card against the frozen power board (KiCad Python).

usage: python.exe card_overlay.py CARD.kicad_pcb POWER.kicad_pcb [OUT.json]

Reads both saved files and checks, to TOL mm:
- J11 on B.Cu, every pad n on J10 pad n (J10 on the power board's F.Cu);
- H1-H4 on H5-H8 (H1 over H5 ... H4 over H8);
- J11 and H1-H4 locked;
- the card outline (its Edge.Cuts centre lines) equal to CARD_RECT, the card rectangle the power board was placed
  for (layout file of the frozen v16).
Exit status 1 if anything fails, so the placement check can call it.
"""
import json, math, sys
import pcbnew

TOL = 0.001
CARD_RECT = (45.8905, 70.0226, 90.8905, 115.0226)     # from the power layout the frozen v16 was built on
MM = pcbnew.ToMM
card = pcbnew.LoadBoard(sys.argv[1])
power = pcbnew.LoadBoard(sys.argv[2])
cf = {f.GetReference(): f for f in card.GetFootprints()}
pf = {f.GetReference(): f for f in power.GetFootprints()}
rows, fails = [], 0


def check(name, ok, detail):
    global fails
    rows.append(dict(check=name, ok=bool(ok), detail=detail))
    fails += 0 if ok else 1
    print('%-4s %-34s %s' % ('ok' if ok else 'FAIL', name, detail))


j10 = {p.GetNumber(): p.GetPosition() for p in pf['J10'].Pads()}
j11 = {p.GetNumber(): p.GetPosition() for p in cf['J11'].Pads()}
worst = max(math.hypot(MM(j11[n].x - j10[n].x), MM(j11[n].y - j10[n].y)) for n in j10)
check('J11 pads on J10 pads', set(j10) == set(j11) and worst <= TOL,
      '%d pads, worst offset %.4f mm' % (len(j10), worst))
check('J11 on B.Cu', cf['J11'].IsFlipped(), cf['J11'].GetLayerName())
check('J10 on F.Cu (power board)', not pf['J10'].IsFlipped(), pf['J10'].GetLayerName())
for hc, hp in zip(['H1', 'H2', 'H3', 'H4'], ['H5', 'H6', 'H7', 'H8']):
    a, b = cf[hc].GetPosition(), pf[hp].GetPosition()
    d = math.hypot(MM(a.x - b.x), MM(a.y - b.y))
    check('%s on %s' % (hc, hp), d <= TOL, '(%.4f, %.4f), offset %.4f mm' % (MM(a.x), MM(a.y), d))
for r in ['J11', 'H1', 'H2', 'H3', 'H4']:
    check('%s locked' % r, cf[r].IsLocked(), '')
bb = card.GetBoardEdgesBoundingBox()
rect = (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))
# the edge bounding box includes half the 0.1 mm outline width on each side
d = max(abs(a - b) for a, b in zip(rect, (CARD_RECT[0] - 0.05, CARD_RECT[1] - 0.05, CARD_RECT[2] + 0.05,
                                           CARD_RECT[3] + 0.05)))
check('card outline = power-board card rect', d <= 0.002,
      'x %.4f-%.4f, y %.4f-%.4f (outline centre lines)' % (rect[0] + 0.05, rect[2] - 0.05, rect[1] + 0.05,
                                                          rect[3] - 0.05))
print('%d checks, %d failed' % (len(rows), fails))
if len(sys.argv) > 3:
    json.dump(dict(rows=rows, failed=fails), open(sys.argv[3], 'w'), indent=1)
sys.exit(1 if fails else 0)
