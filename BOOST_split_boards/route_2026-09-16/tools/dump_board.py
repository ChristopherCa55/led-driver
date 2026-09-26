"""Dump a board's footprints, pads, zones, outline and rules to JSON (KiCad Python).

usage: python.exe dump_board.py BOARD.kicad_pcb OUT.json
"""
import json, sys
import pcbnew

MM = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
out = {'footprints': [], 'zones': [], 'tracks': 0, 'vias': 0, 'layers': {}, 'rules': {}}
for lid in range(pcbnew.PCB_LAYER_ID_COUNT):
    if board.IsLayerEnabled(lid) and pcbnew.IsCopperLayer(lid):
        out['layers'][board.GetLayerName(lid)] = lid

for fp in board.GetFootprints():
    bb = fp.GetCourtyard(pcbnew.B_CrtYd if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_CrtYd).BBox() \
        if hasattr(fp, 'GetCourtyard') else None
    f = dict(ref=fp.GetReference(), value=fp.GetValue(), fpid=fp.GetFPIDAsString(),
             side='B' if fp.GetLayer() == pcbnew.B_Cu else 'F',
             x=MM(fp.GetPosition().x), y=MM(fp.GetPosition().y), rot=fp.GetOrientationDegrees(),
             pads=[])
    if bb is not None and bb.GetWidth() > 0:
        f['crtyd'] = [MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())]
    for p in fp.Pads():
        ls = p.GetLayerSet()
        cu = [board.GetLayerName(l) for l in ls.CuStack()]
        bbp = p.GetBoundingBox()
        f['pads'].append(dict(
            num=p.GetNumber(), net=p.GetNetname(), x=MM(p.GetPosition().x), y=MM(p.GetPosition().y),
            sx=MM(p.GetSize(pcbnew.F_Cu).x) if hasattr(p, 'GetSize') else None,
            sy=MM(p.GetSize(pcbnew.F_Cu).y) if hasattr(p, 'GetSize') else None,
            drill=MM(p.GetDrillSize().x), attr=int(p.GetAttribute()), shape=int(p.GetShape(pcbnew.F_Cu)),
            orient=p.GetOrientationDegrees(), layers=cu,
            bbox=[MM(bbp.GetLeft()), MM(bbp.GetTop()), MM(bbp.GetRight()), MM(bbp.GetBottom())]))
    out['footprints'].append(f)

for z in board.Zones():
    o = z.Outline()
    pts = []
    if o.OutlineCount():
        ol = o.Outline(0)
        pts = [[MM(ol.CPoint(i).x), MM(ol.CPoint(i).y)] for i in range(ol.PointCount())]
    out['zones'].append(dict(net=z.GetNetname(), keepout=bool(z.GetIsRuleArea()),
                             layers=[board.GetLayerName(l) for l in z.GetLayerSet().CuStack()], outline=pts,
                             name=z.GetZoneName()))

out['tracks'] = sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK')
out['vias'] = sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_VIA')
edge = []
for d in board.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        edge.append([MM(d.GetStart().x), MM(d.GetStart().y), MM(d.GetEnd().x), MM(d.GetEnd().y), d.GetShapeStr()])
out['edge'] = edge
ds = board.GetDesignSettings()
out['rules'] = dict(min_clearance=MM(ds.m_MinClearance), min_track=MM(ds.m_TrackMinWidth),
                    min_via_d=MM(ds.m_ViasMinSize), min_through_hole=MM(ds.m_MinThroughDrill),
                    copper_edge=MM(ds.m_CopperEdgeClearance), hole_clearance=MM(ds.m_HoleClearance),
                    hole_to_hole=MM(ds.m_HoleToHoleMin), board_thickness=MM(ds.GetBoardThickness()))
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print('footprints', len(out['footprints']), 'zones', len(out['zones']), 'tracks', out['tracks'], 'vias', out['vias'],
      'layers', list(out['layers']))
