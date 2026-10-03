# Export every copper layer of a KiCad board as polygons per net, plus vias and plated holes (KiCad Python).
# Usage: "C:/Program Files/KiCad/10.0/bin/python.exe" export_copper.py BOARD.kicad_pcb OUT.json
# Run it on a copy: KiCad writes a .kicad_prl beside any board it loads.
import json, sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MAXERR = 5000  # 5 um
layers = [L for L in b.GetEnabledLayers().CuStack()]
names = [b.GetLayerName(L) for L in layers]


def polys(ps):
    ps.Fracture()  # simple outlines, holes joined by slits
    out = []
    for i in range(ps.OutlineCount()):
        ol = ps.Outline(i)
        out.append([[ol.CPoint(k).x / 1e6, ol.CPoint(k).y / 1e6] for k in range(ol.PointCount())])
    return out


res = {'layers': names, 'nets': {}, 'copper': {}, 'vias': [], 'pth': []}
for L, nm in zip(layers, names):
    per = {}

    def add(net, item_ps):
        per.setdefault(net, pcbnew.SHAPE_POLY_SET()).BooleanAdd(item_ps)

    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(L):
            continue
        add(z.GetNetname(), z.GetFilledPolysList(L).CloneDropTriangulation())
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            if not t.FlashLayer(L):
                continue
        elif t.GetLayer() != L:
            continue
        ps = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(ps, L, 0, MAXERR, pcbnew.ERROR_INSIDE)
        add(t.GetNetname(), ps)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.FlashLayer(L):
                continue
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, L, 0, MAXERR, pcbnew.ERROR_INSIDE)
            add(p.GetNetname(), ps)
    res['copper'][nm] = {net: polys(ps) for net, ps in per.items()}
    print(nm, len(per), 'nets', flush=True)

for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        res['vias'].append({'x': t.GetPosition().x / 1e6, 'y': t.GetPosition().y / 1e6, 'drill': t.GetDrillValue() / 1e6,
                            'dia': t.GetWidth(pcbnew.F_Cu) / 1e6, 'net': t.GetNetname(),
                            'flash': [nm for L, nm in zip(layers, names) if t.FlashLayer(L)]})
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetDrillSizeX() > 0:
            res['pth'].append({'ref': fp.GetReference(), 'pad': p.GetNumber(), 'x': p.GetPosition().x / 1e6,
                               'y': p.GetPosition().y / 1e6, 'drill': min(p.GetDrillSizeX(), p.GetDrillSizeY()) / 1e6,
                               'net': p.GetNetname()})
fps = []
for fp in b.GetFootprints():
    bb = fp.GetBoundingBox(False)
    fps.append({'ref': fp.GetReference(), 'value': fp.GetValue(), 'side': 'B' if fp.IsFlipped() else 'F',
                'x': fp.GetPosition().x / 1e6, 'y': fp.GetPosition().y / 1e6,
                'bbox': [bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6],
                'pads': [{'num': p.GetNumber(), 'net': p.GetNetname(), 'x': p.GetPosition().x / 1e6,
                          'y': p.GetPosition().y / 1e6} for p in fp.Pads()]})
res['footprints'] = fps
ol = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(ol, False)
res['outline'] = polys(ol)
json.dump(res, open(sys.argv[2], 'w'))
print('vias', len(res['vias']), 'pth', len(res['pth']))
