"""Export each net's copper per layer from a saved board, after refilling every zone (KiCad Python).

usage: python.exe export_copper.py BOARD.kicad_pcb OUT.json [NET ...]      (no NET = every net)

Output: {layers: [names in stack order F..B], nets: {net: {layer: [polygon, ...]}},
         barrels: [{net, x, y, drill, kind: via|tht, ref, num, layers: [flashed layer names]}],
         pads: [{ref, num, net, layers, polys: {layer: [polygon]}}]}
A polygon is a list of [x, y] in mm (zone fills are fractured, so no separate holes).
"""
import json, sys
import pcbnew

MM = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
want = set(sys.argv[3:])
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

STACK = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu', 'B.Cu']
LID = {n: board.GetLayerID(n) for n in STACK}
MAXERR = pcbnew.FromMM(0.01)


def polys_of(sps):
    out = []
    for i in range(sps.OutlineCount()):
        ol = sps.Outline(i)
        out.append([[round(MM(ol.CPoint(j).x), 4), round(MM(ol.CPoint(j).y), 4)] for j in range(ol.PointCount())])
        for h in range(sps.HoleCount(i)):
            hl = sps.Hole(i, h)
            out.append({'hole': [[round(MM(hl.CPoint(j).x), 4), round(MM(hl.CPoint(j).y), 4)]
                                 for j in range(hl.PointCount())]})
    return out


nets = {}


def add(net, layer, sps):
    if want and net not in want:
        return
    if sps.OutlineCount() == 0:
        return
    nets.setdefault(net, {}).setdefault(layer, []).extend(polys_of(sps))


zones_out, keepouts = [], []
for z in board.Zones():
    if z.GetIsRuleArea():
        o = z.Outline()
        if o.OutlineCount():
            ol = o.Outline(0)
            keepouts.append(dict(name=z.GetZoneName(), layers=[ln for ln in STACK if z.IsOnLayer(LID[ln])],
                                 no_tracks=bool(z.GetDoNotAllowTracks()), no_vias=bool(z.GetDoNotAllowVias()),
                                 pts=[[MM(ol.CPoint(j).x), MM(ol.CPoint(j).y)] for j in range(ol.PointCount())]))
        continue
    for ln in STACK:
        if z.IsOnLayer(LID[ln]) and z.HasFilledPolysForLayer(LID[ln]):
            sps = z.GetFilledPolysList(LID[ln])
            add(z.GetNetname(), ln, sps)
            if not want or z.GetNetname() in want:
                zones_out.append(dict(net=z.GetNetname(), layer=ln, prio=z.GetAssignedPriority(),
                                      clearance=MM(z.GetLocalClearance() or 0), name=z.GetZoneName(),
                                      polys=polys_of(sps)))

barrels, pads, via_polys, tracks = [], [], [], []
for t in board.GetTracks():
    net = t.GetNetname()
    if want and net not in want:
        continue
    if t.GetClass() == 'PCB_VIA':
        fl = [ln for ln in STACK if t.FlashLayer(LID[ln])]
        for ln in fl:
            sps = pcbnew.SHAPE_POLY_SET()
            t.TransformShapeToPolygon(sps, LID[ln], 0, MAXERR, pcbnew.ERROR_INSIDE)
            add(net, ln, sps)
        barrels.append(dict(net=net, x=MM(t.GetPosition().x), y=MM(t.GetPosition().y), drill=MM(t.GetDrillValue()),
                            dia=MM(t.GetWidth(pcbnew.F_Cu)), kind='via', layers=fl))
        via_polys.append(dict(net=net, layers=fl, x=MM(t.GetPosition().x), y=MM(t.GetPosition().y),
                              dia=MM(t.GetWidth(pcbnew.F_Cu)), drill=MM(t.GetDrillValue())))
    else:
        ln = board.GetLayerName(t.GetLayer())
        if ln in LID:
            tracks.append(dict(net=net, layer=ln, w=MM(t.GetWidth()), x0=MM(t.GetStart().x), y0=MM(t.GetStart().y),
                               x1=MM(t.GetEnd().x), y1=MM(t.GetEnd().y)))
            sps = pcbnew.SHAPE_POLY_SET()
            t.TransformShapeToPolygon(sps, t.GetLayer(), 0, MAXERR, pcbnew.ERROR_INSIDE)
            add(net, ln, sps)

for fp in board.GetFootprints():
    for p in fp.Pads():
        net = p.GetNetname()
        if not net or (want and net not in want):
            continue
        rec = dict(ref=fp.GetReference(), num=p.GetNumber(), net=net, polys={},
                   x=MM(p.GetPosition().x), y=MM(p.GetPosition().y), drill=MM(p.GetDrillSize().x))
        for ln in STACK:
            if p.IsOnLayer(LID[ln]) and p.FlashLayer(LID[ln]):
                sps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(sps, LID[ln], 0, MAXERR, pcbnew.ERROR_INSIDE)
                rec['polys'][ln] = polys_of(sps)
                add(net, ln, sps)
        rec['layers'] = list(rec['polys'])
        pads.append(rec)
        if p.GetDrillSize().x > 0 and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            barrels.append(dict(net=net, x=rec['x'], y=rec['y'], drill=rec['drill'], dia=MM(p.GetSize(pcbnew.F_Cu).x),
                                kind='tht', ref=rec['ref'], num=rec['num'], layers=rec['layers']))

npth = []        # non-plated holes (J9 tie slots, mounting holes): board edge for DRC's 0.3 mm edge clearance
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            sps = pcbnew.SHAPE_POLY_SET()
            p.GetEffectiveHoleShape().TransformToPolygon(sps, MAXERR, pcbnew.ERROR_OUTSIDE)
            npth.append(dict(ref=fp.GetReference(), x=MM(p.GetPosition().x), y=MM(p.GetPosition().y),
                             polys=polys_of(sps)))

fp_copper = []   # copper graphics inside footprints, e.g. net-tie shapes (no net)
for fp in board.GetFootprints():
    for g in fp.GraphicalItems():
        ln = board.GetLayerName(g.GetLayer())
        if ln not in LID:
            continue
        sps = pcbnew.SHAPE_POLY_SET()
        g.TransformShapeToPolygon(sps, g.GetLayer(), 0, MAXERR, pcbnew.ERROR_INSIDE)
        if sps.OutlineCount():
            fp_copper.append(dict(ref=fp.GetReference(), layer=ln, polys=polys_of(sps)))

edge = []
for d in board.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        edge.append([MM(d.GetStart().x), MM(d.GetStart().y), MM(d.GetEnd().x), MM(d.GetEnd().y)])
classes = {}
for nm, ni in board.GetNetsByName().items():
    try:
        classes[str(nm)] = str(ni.GetNetClassName())
    except Exception:
        pass
json.dump(dict(board=sys.argv[1], layers=STACK, nets=nets, barrels=barrels, pads=pads, zones=zones_out,
               keepouts=keepouts, vias=via_polys, tracks=tracks, edge=edge, classes=classes, fp_copper=fp_copper, npth=npth), open(sys.argv[2], 'w'))
print('exported %d nets, %d barrels, %d pads' % (len(nets), len(barrels), len(pads)))
