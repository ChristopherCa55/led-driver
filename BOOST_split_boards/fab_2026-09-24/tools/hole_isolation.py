"""Nearest copper to each mounting hole, on every copper layer (KiCad Python), 2026-09-25.

usage: "<KiCad python>" tools/hole_isolation.py BOARD.kicad_pcb H5 H6 H7 H8
For each hole: the hole size and plating, then per layer the nearest track, via, pad or filled zone edge, measured
from the hole centre, with its net. A metal stud (M3, 3.0 mm) in a 3.2 mm hole shorts nothing if no copper lies
within the washer / hex footprint and the hole wall is unplated.
"""
import sys, math
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
cu = [l for l in range(pcbnew.PCB_LAYER_ID_COUNT) if pcbnew.IsCopperLayer(l) and b.IsLayerEnabled(l)]
for ref in sys.argv[2:]:
    fp = b.FindFootprintByReference(ref)
    pads = list(fp.Pads())
    c = fp.GetPosition()
    print('%s at (%.3f, %.3f): %s' % (ref, MM(c.x), MM(c.y), ', '.join(
        '%s pad %s drill %.2f %s, copper %s' % (ref, p.GetNumber(), MM(p.GetDrillSizeX()),
                                              'PTH' if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else 'NPTH',
                                              [b.GetLayerName(l) for l in cu if p.IsOnLayer(l)] or 'none') for p in pads)))
    for L in cu:
        best = (1e9, '')
        for t in b.GetTracks():
            if not t.IsOnLayer(L):
                continue
            # the real copper shape (arcs included: a chord would cut inside an arc that hugs the hole)
            d = math.sqrt(t.GetEffectiveShape(L).SquaredDistance(c))
            if d < best[0]:
                best = (d, 'track/via ' + t.GetNetname())
        for f in b.GetFootprints():
            for p in f.Pads():
                if f.GetReference() == ref or not p.IsOnLayer(L) or p.GetNetname() == '':
                    continue
                sh = p.GetEffectivePolygon(L)
                d = math.sqrt(sh.SquaredDistance(c)) if sh.OutlineCount() else 1e9
                if d < best[0]:
                    best = (d, 'pad %s.%s %s' % (f.GetReference(), p.GetNumber(), p.GetNetname()))
        for z in b.Zones():
            if not z.IsOnLayer(L) or z.GetIsRuleArea():
                continue
            fp_ = z.GetFilledPolysList(L)
            if fp_.OutlineCount() == 0:
                continue
            d = 0.0 if fp_.Contains(c) else math.sqrt(fp_.SquaredDistance(c))
            if d < best[0]:
                best = (d, 'zone ' + z.GetNetname())
        print('   %-7s nearest copper %.2f mm from the hole centre (%s)' % (b.GetLayerName(L), MM(int(best[0])), best[1]))
