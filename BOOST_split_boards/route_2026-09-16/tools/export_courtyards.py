"""Export every footprint's courtyard outline, side and position, plus pads (KiCad Python), for placement edits.

usage: python.exe export_courtyards.py BOARD.kicad_pcb OUT.json
"""
import json, sys
import pcbnew

MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
out = []
for f in b.GetFootprints():
    side = 'B' if f.IsFlipped() else 'F'
    cy = f.GetCourtyard(pcbnew.B_CrtYd if side == 'B' else pcbnew.F_CrtYd)
    polys = []
    for i in range(cy.OutlineCount()):
        ol = cy.Outline(i)
        polys.append([[MM(ol.CPoint(j).x), MM(ol.CPoint(j).y)] for j in range(ol.PointCount())])
    pads = []
    for p in f.Pads():
        sps = pcbnew.SHAPE_POLY_SET()
        lid = pcbnew.B_Cu if side == 'B' else pcbnew.F_Cu
        p.TransformShapeToPolygon(sps, lid if p.IsOnLayer(lid) else p.GetPrincipalLayer(), 0, pcbnew.FromMM(0.01), pcbnew.ERROR_INSIDE)
        pp = []
        for i in range(sps.OutlineCount()):
            ol = sps.Outline(i)
            pp.append([[MM(ol.CPoint(j).x), MM(ol.CPoint(j).y)] for j in range(ol.PointCount())])
        pads.append(dict(num=p.GetNumber(), net=p.GetNetname(), x=MM(p.GetPosition().x), y=MM(p.GetPosition().y),
                         drill=MM(p.GetDrillSize().x), polys=pp))
    out.append(dict(ref=f.GetReference(), value=f.GetValue(), side=side, x=MM(f.GetPosition().x), y=MM(f.GetPosition().y),
                    rot=f.GetOrientationDegrees(), fpid=f.GetFPIDAsString(), courtyard=polys, pads=pads))
json.dump(out, open(sys.argv[2], 'w'))
print('exported %d footprints' % len(out))
