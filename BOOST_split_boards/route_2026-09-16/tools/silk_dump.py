"""Dump one side's silk, mask openings, Fab outlines and board outline as polygons (KiCad Python), for silk_view.py.

usage: python.exe silk_dump.py BOARD.kicad_pcb F|B OUT.json
"""
import json, sys
import pcbnew

MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
side = sys.argv[2]
L = {'F': (pcbnew.F_SilkS, pcbnew.F_Mask, pcbnew.F_Fab), 'B': (pcbnew.B_SilkS, pcbnew.B_Mask, pcbnew.B_Fab)}[side]


def polys(item, layer):
    ps = pcbnew.SHAPE_POLY_SET()
    if item.GetClass() in ('PCB_TEXT', 'PCB_FIELD'):
        item.TransformTextToPolySet(ps, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
    else:
        item.TransformShapeToPolygon(ps, layer, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
    ps.Fracture()
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out.append([(round(MM(o.CPoint(k).x), 3), round(MM(o.CPoint(k).y), 3)) for k in range(o.PointCount())])
    return out


res = {'silk': [], 'mask': [], 'fab': [], 'edge': [], 'labels': []}
for f in b.GetFootprints():
    for g in f.GraphicalItems():
        if g.GetLayer() == L[0]:
            res['silk'] += polys(g, L[0])
        elif g.GetLayer() == L[2]:
            res['fab'] += polys(g, L[2])
    for fld in f.GetFields():
        if fld.IsVisible() and fld.GetLayer() == L[0]:
            res['silk'] += polys(fld, L[0])
    for p in f.Pads():
        if p.IsOnLayer(L[1]):
            res['mask'] += polys(p, L[1])
    c = f.GetPosition()
    res['labels'].append((f.GetReference(), MM(c.x), MM(c.y), f.GetLayer() == (pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu)))
for d in b.GetDrawings():
    if d.GetLayer() == L[0]:
        res['silk'] += polys(d, L[0])
    elif d.GetLayer() == pcbnew.Edge_Cuts:
        res['edge'] += [[(MM(d.GetStart().x), MM(d.GetStart().y)), (MM(d.GetEnd().x), MM(d.GetEnd().y))]]
json.dump(res, open(sys.argv[3], 'w'))
print('silk %d, mask %d, fab %d' % (len(res['silk']), len(res['mask']), len(res['fab'])))
