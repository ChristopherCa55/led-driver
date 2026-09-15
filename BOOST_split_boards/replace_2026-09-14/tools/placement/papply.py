"""Apply a pmodel layout to a synced power board (KiCad python).

  papply.py SRC.kicad_pcb LAYOUT.json OUT.kicad_pcb

Text pass (before KiCad loads the file): the rectangular Edge.Cuts outline becomes the notched
outline from pmodel.BOARD, and a "not for fabrication" note goes on Cmts.User.
KiCad pass: every footprint in the layout is moved, flipped to its side (Flip LEFT_RIGHT, then
SetOrientationDegrees, the convention pmodel was verified against) and rotated. Then rule areas
(no tracks, vias, pads, pours or footprints, all copper layers) are added:
  - 3.75 mm radius at every tab hole of the screwed FETs (the actual NPTH pad position);
  - 3.5 mm radius at each standoff hole listed in the layout (H5-H8).
The card outline goes on User.Eco1 as a rectangle for review.
Finally every pad position is written to OUT.pads.json so the distance table can be re-run on
the real board instead of the model.
"""
import sys, os, re, json, math

SRC, LAY, OUT = sys.argv[1:4]
res = json.load(open(LAY))
layout = res['layout']
screwed = res.get('screwed', ['M1', 'M8', 'M9', 'M10'])
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BOARD = [(30, 30), (86, 30), (86, 42), (104, 42), (104, 116), (30, 116)]

txt = open(SRC, encoding='utf8').read()
pat = re.compile(r'\n\t\(gr_line\n\t\t\(start [-\d.]+ [-\d.]+\)\n\t\t\(end [-\d.]+ [-\d.]+\)\n\t\t\(stroke\n\t\t\t\(width [\d.]+\)\n'
                 r'\t\t\t\(type \w+\)\n\t\t\)\n\t\t\(layer "Edge\.Cuts"\)\n\t\t\(uuid "[^"]+"\)\n\t\)')
n_edges = len(pat.findall(txt))
assert n_edges == 4, 'expected the 4-line rectangular outline, found %d Edge.Cuts lines' % n_edges
txt = pat.sub('', txt)
i = txt.rfind('\n\t(embedded_fonts')
new = ''
for k in range(len(BOARD)):
    (x1, y1), (x2, y2) = BOARD[k], BOARD[(k + 1) % len(BOARD)]
    new += ('\n\t(gr_line\n\t\t(start %g %g)\n\t\t(end %g %g)\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type default)\n\t\t)\n'
            '\t\t(layer "Edge.Cuts")\n\t)' % (x1, y1, x2, y2))
new += ('\n\t(gr_text "WORK IN PROGRESS - PLACEMENT REVIEW ONLY - NOT FOR FABRICATION"\n\t\t(at 67 27 0)\n\t\t(layer "Cmts.User")\n'
        '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.5 1.5)\n\t\t\t\t(thickness 0.2)\n\t\t\t)\n\t\t)\n\t)')
txt = txt[:i] + new + txt[i:]
tmp = OUT + '.tmp.kicad_pcb'
open(tmp, 'w', encoding='utf8', newline='').write(txt)

import pcbnew
FM, MM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(tmp)
fps = {f.GetReference(): f for f in b.GetFootprints()}
missing = [r for r in layout if r not in fps]
assert not missing, missing
unplaced = sorted(r for r in fps if r not in layout)
if unplaced and '--allow-unplaced' not in sys.argv:
    os.remove(tmp)
    sys.exit('refusing to save: %d footprints have no position in the layout: %s' % (len(unplaced), unplaced))
for ref, (x, y, rot, side) in layout.items():
    f = fps[ref]
    want_b = side == 'B'
    f.SetOrientationDegrees(0)
    f.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
    if f.IsFlipped() != want_b:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(rot)

all_cu = pcbnew.LSET.AllCuMask()


def keepout(cx, cy, r, name):
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowFootprints(True)
    z.SetLayerSet(all_cu)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for k in range(48):
        a = 2 * math.pi * k / 48
        ol.Append(FM(cx + r * math.cos(a)), FM(cy + r * math.sin(a)))
    b.Add(z)


holes = {}
for m in screwed:
    for p in fps[m].Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            c = p.GetPosition()
            holes[m] = (MM(c.x), MM(c.y))
            keepout(MM(c.x), MM(c.y), 3.75, 'washer %s' % m)
for i, (x, y) in enumerate(res.get('standoffs', [])):
    keepout(x, y, 3.5, 'standoff H%d' % (5 + i))
if 'card' in res:
    cx, cy = res['card']
    cs = res.get('card_size', 42)
    rect = pcbnew.PCB_SHAPE(b)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(pcbnew.VECTOR2I(FM(cx), FM(cy)))
    rect.SetEnd(pcbnew.VECTOR2I(FM(cx + cs), FM(cy + cs)))
    rect.SetLayer(pcbnew.Eco1_User)
    rect.SetWidth(FM(0.2))
    b.Add(rect)
pcbnew.SaveBoard(OUT, b)
os.remove(tmp)

pads = {}
for ref, f in fps.items():
    pads[ref] = dict(side='B' if f.IsFlipped() else 'F', x=MM(f.GetPosition().x), y=MM(f.GetPosition().y),
                     rot=f.GetOrientationDegrees(),
                     pads=[(p.GetNumber(), MM(p.GetPosition().x), MM(p.GetPosition().y), p.GetNetname()) for p in f.Pads()])
json.dump(dict(pads=pads, holes=holes), open(OUT + '.pads.json', 'w'), indent=1)
print('saved %s: %d footprints placed, %d washer keep-outs, %d standoff keep-outs' %
      (OUT, len(layout), len(holes), len(res.get('standoffs', []))))
