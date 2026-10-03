import sys, math, pcbnew
MM, FM = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); vout = sys.argv[2]
L = list(b.GetEnabledLayers().CuStack())
def copper(net, l):
    ps = pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.IsOnLayer(l) and z.GetNetname() == net:
            ps.BooleanAdd(z.GetFilledPolysList(l))
    return ps
def show(tag, x):
    print('%s: %.1f mm2 in %d pieces' % (tag, x.Area() / 1e12, x.OutlineCount()))
    for i in range(x.OutlineCount()):
        bb = x.Outline(i).BBox()
        if (bb.GetWidth() > FM(0.5)):
            print('    x %.1f-%.1f  y %.1f-%.1f' % (MM(bb.GetX()), MM(bb.GetRight()), MM(bb.GetY()), MM(bb.GetBottom())))
inner = [l for l in L if l not in (pcbnew.F_Cu, pcbnew.B_Cu)]
vin_in = pcbnew.SHAPE_POLY_SET(); vo_in = pcbnew.SHAPE_POLY_SET()
for l in inner:
    vin_in.BooleanAdd(copper('Vin', l)); vo_in.BooleanAdd(copper(vout, l))
D = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
for tag, bnet, inner_other in (('B.Cu Vin pour near inner ' + vout, 'Vin', vo_in), ('B.Cu %s pour near inner Vin' % vout, vout, vin_in),
                                ('B.Cu GND near inner Vin AND inner ' + vout, 'GND', None)):
    bc = copper(bnet, pcbnew.B_Cu)
    if inner_other is None:
        g1 = pcbnew.SHAPE_POLY_SET(vin_in); g1.Inflate(FM(D), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.01))
        g2 = pcbnew.SHAPE_POLY_SET(vo_in); g2.Inflate(FM(D), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.01))
        bc.BooleanIntersection(g1); bc.BooleanIntersection(g2)
    else:
        g = pcbnew.SHAPE_POLY_SET(inner_other); g.Inflate(FM(D), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.01))
        bc.BooleanIntersection(g)
    show(tag + ' (within %.1f mm)' % D, bc)
