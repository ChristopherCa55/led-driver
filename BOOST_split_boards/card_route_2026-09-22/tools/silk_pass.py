"""Silk pass: move reference texts that DRC flags (silk over copper, silk overlap) to the nearest free spot (KiCad Python).

usage: python.exe silk_pass.py BOARD_IN.kicad_pcb DRC.json BOARD_OUT.kicad_pcb

Only the Reference fields named in silk_over_copper / silk_overlap warnings move; their size and stroke stay as they
are (the card's 1.0 / 0.15 mm text minimum is not touched). Candidates: rings round the footprint's courtyard, the text
upright or turned 90 degrees, stepping out at most 1.5 mm. A candidate must keep, on its own silk layer:
  0.10 mm from every pad and exposed copper of its side (pads are the mask openings; vias are tented),
  0.05 mm from every other silk item (footprint graphics and texts, already-moved texts included),
  0.30 mm inside the board edge and from every non-plated hole.
The nearest legal candidate to the footprint centre wins. A text with no legal spot moves to its side's Fab layer
(the assembly drawing), same size, and is reported.
"""
import json, math, sys
import pcbnew

MM, FM = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
rep = json.load(open(sys.argv[2]))
out = sys.argv[3]
want = set()
for v in rep['violations']:
    if v['type'] in ('silk_over_copper', 'silk_overlap'):
        for it in v['items']:
            d = it['description']
            if d.startswith('Reference field of '):
                want.add(d[len('Reference field of '):].split()[0])
fps = {f.GetReference(): f for f in b.GetFootprints()}
edge = b.GetBoardEdgesBoundingBox()
X0, Y0, X1, Y1 = MM(edge.GetX()), MM(edge.GetY()), MM(edge.GetRight()), MM(edge.GetBottom())


def silk_items(layer, skip):
    items = []
    for f in b.GetFootprints():
        for g in f.GraphicalItems():
            if g.GetLayer() == layer:
                items.append(g.GetEffectiveTextShape() if g.GetClass() in ('PCB_TEXT',) else g.GetEffectiveShape())
        for fld in f.GetFields():
            if fld is skip or not fld.IsVisible() or fld.GetLayer() != layer:
                continue
            items.append(fld.GetEffectiveTextShape())
    for d in b.GetDrawings():
        if d.GetLayer() == layer:
            items.append(d.GetEffectiveTextShape() if d.GetClass() == 'PCB_TEXT' else d.GetEffectiveShape())
    return items


def pads_of(side_cu):
    out = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                out.append((p.GetEffectiveHoleShape(), 0.30))
            elif p.IsOnLayer(side_cu):
                out.append((p.GetEffectiveShape(side_cu), 0.10))
    return out


moved, stuck = [], []
for ref in sorted(want):
    f = fps[ref]
    fld = f.Reference()
    if not fld.IsVisible():
        continue
    layer = fld.GetLayer()
    cu = pcbnew.F_Cu if layer == pcbnew.F_SilkS else pcbnew.B_Cu
    obst = pads_of(cu)
    silk = silk_items(layer, fld)
    cy = f.GetCourtyard(pcbnew.F_CrtYd if cu == pcbnew.F_Cu else pcbnew.B_CrtYd).BBox()
    cx0, cy0, cx1, cy1 = MM(cy.GetX()), MM(cy.GetY()), MM(cy.GetRight()), MM(cy.GetBottom())
    fx, fy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    old_pos, old_ang = fld.GetPosition(), fld.GetTextAngleDegrees()
    best = None
    for step in [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]:
        cands = []
        for ang in (0, 90):
            hw, hh = (0.9, 0.7) if ang == 0 else (0.7, 0.9)
            for t in [i / 8.0 for i in range(9)]:
                cands += [(cx0 + (cx1 - cx0) * t, cy0 - hh - step, ang), (cx0 + (cx1 - cx0) * t, cy1 + hh + step, ang),
                          (cx0 - hw - step, cy0 + (cy1 - cy0) * t, ang), (cx1 + hw + step, cy0 + (cy1 - cy0) * t, ang)]
        cands.sort(key=lambda c: math.hypot(c[0] - fx, c[1] - fy))
        for x, y, ang in cands:
            fld.SetTextAngleDegrees(ang)
            fld.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
            sh = fld.GetEffectiveTextShape()
            bb = sh.BBox()
            if MM(bb.GetX()) < X0 + 0.3 or MM(bb.GetY()) < Y0 + 0.3 or MM(bb.GetRight()) > X1 - 0.3 or \
                    MM(bb.GetBottom()) > Y1 - 0.3:
                continue
            if any(sh.Collide(o, FM(c)) for o, c in obst):
                continue
            if any(sh.Collide(s, FM(0.05)) for s in silk):
                continue
            best = (x, y, ang)
            break
        if best:
            break
    if best:
        fld.SetTextAngleDegrees(best[2])
        fld.SetPosition(pcbnew.VECTOR2I(FM(best[0]), FM(best[1])))
        moved.append('%s -> (%.2f, %.2f) %d deg' % (ref, best[0], best[1], best[2]))
    else:
        fld.SetTextAngleDegrees(old_ang)
        fld.SetPosition(old_pos)
        fld.SetLayer(pcbnew.F_Fab if layer == pcbnew.F_SilkS else pcbnew.B_Fab)
        stuck.append(ref)
pcbnew.SaveBoard(out, b)
print('moved %d reference texts: %s' % (len(moved), '; '.join(moved)))
print('no free spot within 1.5 mm, moved to Fab: %s' % (', '.join(stuck) or 'none'))
