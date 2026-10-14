import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
import numpy as np, pcbnew
import route_new as R

b = pcbnew.LoadBoard(sys.argv[1])
g = R.Grid(52, 102, 64, 111)
lid = pcbnew.B_Cu
worst = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.IsOnLayer(lid) and p.FlashLayer(lid):
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, lid, pcbnew.FromMM(0.39), pcbnew.FromMM(0.005), pcbnew.ERROR_OUTSIDE)
            m = g.empty()
            for pts in R.polys(ps):
                g.poly(m, pts)
            if m.sum():
                worst.append((int(m.sum()), fp.GetReference(), p.GetNumber(), ps.OutlineCount(),
                              [len(x) for x in R.polys(ps)], round(R.mm(p.GetPosition().x), 2),
                              round(R.mm(p.GetPosition().y), 2)))
worst.sort(reverse=True)
for w in worst[:10]:
    print(w)
