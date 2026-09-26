"""Plane and island checks on a saved board (KiCad Python): tracks per layer, fill outlines per zone per layer,
zone island-removal mode, and any zone fill outline that overlaps no flashed pad, via or track of its net.

usage: python.exe plane_checks.py BOARD.kicad_pcb
"""
import sys, collections
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
b.BuildConnectivity()
per_layer = collections.Counter(b.GetLayerName(t.GetLayer()) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK')
print('tracks per layer:', dict(sorted(per_layer.items())))
modes = collections.Counter()
untied = []
outlines = {}
items = collections.defaultdict(list)
for t in b.GetTracks():
    items[t.GetNetname()].append(t)
for f in b.GetFootprints():
    for p in f.Pads():
        items[p.GetNetname()].append(p)
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    modes[int(z.GetIslandRemovalMode())] += 1
    for lid in z.GetLayerSet().CuStack():
        if not z.HasFilledPolysForLayer(lid):
            continue
        polys = z.GetFilledPolysList(lid)
        outlines[(z.GetZoneName(), z.GetNetname(), b.GetLayerName(lid))] = polys.OutlineCount()
        for k in range(polys.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET()
            one.AddOutline(polys.Outline(k))
            tied = False
            bb = one.BBox()
            for it in items[z.GetNetname()]:
                if not it.IsOnLayer(lid) or not bb.Intersects(it.GetBoundingBox()):
                    continue
                if it.GetClass() in ('PCB_VIA', 'PCB_PAD') and hasattr(it, 'FlashLayer') and not it.FlashLayer(lid):
                    continue
                shape = pcbnew.SHAPE_POLY_SET()
                it.TransformShapeToPolygon(shape, lid, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
                shape.BooleanIntersection(one)
                if shape.Area() > 0:
                    tied = True
                    break
            if not tied:   # same-net zones that overlap or abut are joined by KiCad's connectivity
                grown = pcbnew.SHAPE_POLY_SET(one)
                grown.Inflate(pcbnew.FromMM(0.01), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.005))
                for z2 in b.Zones():
                    if z2 is z or z2.GetIsRuleArea() or z2.GetNetname() != z.GetNetname() or not z2.HasFilledPolysForLayer(lid):
                        continue
                    other = pcbnew.SHAPE_POLY_SET(z2.GetFilledPolysList(lid))
                    other.BooleanIntersection(grown)
                    if other.Area() > 0:
                        tied = True
                        break
            if not tied:
                untied.append((z.GetZoneName(), z.GetNetname(), b.GetLayerName(lid), round(one.Area() * 1e-12, 3)))
print('island removal modes (0 always, 1 never, 2 area):', dict(modes))
for key in (k for k in outlines if k[2] in ('In1.Cu', 'In4.Cu', 'In6.Cu')):
    print('plane outline count', key, outlines[key])
print('fill outlines touching no pad, via, track or other zone of their net: %d' % len(untied))
for u in untied[:30]:
    print('  ', u)
