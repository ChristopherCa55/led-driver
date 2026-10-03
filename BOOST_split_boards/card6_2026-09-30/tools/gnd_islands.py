"""GND fill pieces with no GND via, through-hole pad or SMD pad touching them (KiCad Python, read-only)."""
import sys, pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
net = sys.argv[2] if len(sys.argv) > 2 else 'GND'
anchors = []   # (layer or None for all, point)
for t in b.GetTracks():
    if t.GetNetname() == net:
        if t.GetClass() == 'PCB_VIA':
            anchors.append((None, t.GetPosition()))
        else:
            anchors.append((t.GetLayer(), t.GetStart())); anchors.append((t.GetLayer(), t.GetEnd()))
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname() == net:
            anchors.append((None if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else (pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu), p.GetPosition()))
for z in b.Zones():
    if z.GetNetname() != net or z.GetIsRuleArea():
        continue
    for l in z.GetLayerSet().CuStack():
        if not z.HasFilledPolysForLayer(l):
            continue
        ps = z.GetFilledPolysList(l)
        for i in range(ps.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(ps.Outline(i))
            hit = any((al is None or al == l) and one.Contains(pt) for al, pt in anchors)
            if not hit:
                bb = ps.Outline(i).BBox()
                print('%s %s piece %d: no %s anchor, bbox (%.2f, %.2f)-(%.2f, %.2f), %.2f mm2' % (z.GetZoneName() or net, b.GetLayerName(l), i, net,
                      MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom()), abs(ps.Outline(i).Area()) / 1e12))
