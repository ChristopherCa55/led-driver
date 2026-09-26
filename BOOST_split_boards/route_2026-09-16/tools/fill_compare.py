"""Does a refill change a board's stored zone fills? (KiCad Python)

usage: python.exe fill_compare.py BOARD.kicad_pcb
Reads the stored fills, refills every zone with the rules beside the board, and compares each zone's filled area and
outline count per layer. The board file is not written.
"""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])


def fills():
    out = {}
    for i, z in enumerate(b.Zones()):
        if z.GetIsRuleArea():
            continue
        for L in z.GetLayerSet().Seq():
            ps = z.GetFilledPolysList(L)
            out[(i, z.GetNetname(), b.GetLayerName(L))] = (round(ps.Area() / 1e12, 4), ps.OutlineCount(), ps.TotalVertices())
    return out


before = fills()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
after = fills()
diff = [(k, before[k], after.get(k)) for k in before if before[k] != after.get(k)]
print('%d zone-layers, %d differ after a refill' % (len(before), len(diff)))
for k, a, c in diff[:40]:
    print('  zone %d %-12s %-8s  stored %s  refilled %s  (area mm2, pieces, vertices)' % (k[0], k[1], k[2], a, c))
