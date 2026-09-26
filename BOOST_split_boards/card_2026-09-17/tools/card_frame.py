"""Put the control card in the frozen power board's frame (KiCad Python).

usage: python.exe card_frame.py SRC_CARD.kicad_pcb ANCHOR.json OUT.kicad_pcb

ANCHOR.json comes from the frozen power board (v16): the card rectangle, H5-H8 and J10's pads.
- Board outline: the 45 x 45 mm card rectangle, in power-board coordinates.
- H1-H4 on H5-H8 (H1 over H5 ... H4 over H8), locked.
- J11 on B.Cu, placed so that pad n lies on J10 pad n (all 30 checked), locked.
- One rule area per mounting hole, radius HOLE_KEEPOUT on every copper layer: no copper, no footprints. It covers
  the 7 mm nylon washers under the card and the M3 screw head on top (nylon hardware, isolated NPTH, as on the
  power board's standoffs).
- A NOT FOR FABRICATION note on Cmts.User.
Every other footprint stays where it is (the staging column right of the board). Copy the shipped
BOOST_control.kicad_pro next to OUT after this runs (SaveBoard rewrites the project file).
"""
import json, math, re, sys

SRC, ANCHOR, OUT = sys.argv[1:4]
HOLE_KEEPOUT = 3.5          # mm: 7.0 mm washer OD under the card (TR NWE-34815-M3); the screw head is smaller
anchor = json.load(open(ANCHOR))
x0, y0, s = anchor['card']['x0'], anchor['card']['y0'], anchor['card']['size']
RECT = [(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)]

txt = open(SRC, encoding='utf8').read()
pat = re.compile(r'\n\t\(gr_line\n\t\t\(start [-\d.]+ [-\d.]+\)\n\t\t\(end [-\d.]+ [-\d.]+\)\n\t\t\(stroke\n\t\t\t\(width [\d.]+\)\n'
                 r'\t\t\t\(type \w+\)\n\t\t\)\n\t\t\(layer "Edge\.Cuts"\)\n\t\t\(uuid "[^"]+"\)\n\t\)')
n_edges = len(pat.findall(txt))
assert n_edges == 4, 'expected the 4-line rectangular outline, found %d Edge.Cuts lines' % n_edges
txt = pat.sub('', txt)
i = txt.rfind('\n\t(embedded_fonts')
new = ''
for k in range(4):
    (xa, ya), (xb, yb) = RECT[k], RECT[(k + 1) % 4]
    new += ('\n\t(gr_line\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type default)\n'
            '\t\t)\n\t\t(layer "Edge.Cuts")\n\t)' % (xa, ya, xb, yb))
new += ('\n\t(gr_text "CONTROL CARD - WORK IN PROGRESS - NOT FOR FABRICATION"\n\t\t(at %.2f %.2f 0)\n'
        '\t\t(layer "Cmts.User")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.5 1.5)\n\t\t\t\t(thickness 0.2)\n\t\t\t)\n'
        '\t\t)\n\t)' % (x0 + s / 2, y0 - 3))
txt = txt[:i] + new + txt[i:]
tmp = OUT + '.tmp.kicad_pcb'
open(tmp, 'w', encoding='utf8', newline='').write(txt)

import pcbnew
FM, MM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(tmp)
fps = {f.GetReference(): f for f in b.GetFootprints()}

# mounting holes on the power board's standoffs
for hc, hp in zip(['H1', 'H2', 'H3', 'H4'], ['H5', 'H6', 'H7', 'H8']):
    f = fps[hc]
    x, y = anchor['standoffs'][hp]
    f.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
    f.SetLocked(True)
    print('%s on %s at (%.4f, %.4f), locked' % (hc, hp, MM(f.GetPosition().x), MM(f.GetPosition().y)))

# J11 on B.Cu, pad n over J10 pad n
j = fps['J11']
if not j.IsFlipped():
    j.Flip(j.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
want = {k: tuple(v) for k, v in anchor['J10']['pads'].items()}
best = None
for rot in (0, 90, 180, 270):
    j.SetOrientationDegrees(rot)
    pads = {p.GetNumber(): p for p in j.Pads()}
    p1 = pads['1'].GetPosition()
    dx, dy = FM(want['1'][0]) - p1.x, FM(want['1'][1]) - p1.y
    j.SetPosition(pcbnew.VECTOR2I(j.GetPosition().x + dx, j.GetPosition().y + dy))
    err = max(math.hypot(MM(p.GetPosition().x) - want[p.GetNumber()][0], MM(p.GetPosition().y) - want[p.GetNumber()][1])
              for p in j.Pads())
    if best is None or err < best[1]:
        best = (rot, err, j.GetPosition())
rot, err, pos = best
j.SetOrientationDegrees(rot)
j.SetPosition(pos)
err = max(math.hypot(MM(p.GetPosition().x) - want[p.GetNumber()][0], MM(p.GetPosition().y) - want[p.GetNumber()][1])
          for p in j.Pads())
assert err < 1e-3, 'J11 does not land on J10: worst pad %.4f mm' % err
j.SetLocked(True)
print('J11 on B.Cu, rot %d, at (%.4f, %.4f): worst pad offset from J10 %.6f mm over %d pads, locked' % (
    rot, MM(pos.x), MM(pos.y), err, len(list(j.Pads()))))

# keep-outs round the mounting holes
all_cu = pcbnew.LSET.AllCuMask()
for hc in ['H1', 'H2', 'H3', 'H4']:
    c = fps[hc].GetPosition()
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    for fn in ('SetDoNotAllowTracks', 'SetDoNotAllowVias', 'SetDoNotAllowPads', 'SetDoNotAllowZoneFills',
               'SetDoNotAllowFootprints'):
        getattr(z, fn)(True)
    z.SetLayerSet(all_cu)
    z.SetZoneName('washer and screw head %s' % hc)
    ol = z.Outline()
    ol.NewOutline()
    for k in range(48):
        a = 2 * math.pi * k / 48
        ol.Append(c.x + FM(HOLE_KEEPOUT * math.cos(a)), c.y + FM(HOLE_KEEPOUT * math.sin(a)))
    b.Add(z)
pcbnew.SaveBoard(OUT, b)
import os
os.remove(tmp)
print('saved %s: outline x %.4f-%.4f, y %.4f-%.4f; %d footprints' % (OUT, x0, x0 + s, y0, y0 + s, len(fps)))
