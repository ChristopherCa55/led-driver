"""Which nets' tracks cut a pour into pieces (KiCad Python).

usage: python.exe pour_cutters.py BOARD.kicad_pcb NET LAYER

For every other net with tracks on LAYER, its tracks there are taken away, only NET's zone on LAYER is refilled, and the
number of filled pieces is counted; nets whose removal leaves the pour in fewer pieces are listed (the candidates to
move to another layer). The board file is not changed.
"""
import sys, collections
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
NET, LAYER = sys.argv[2], sys.argv[3]
lid = b.GetLayerID(LAYER)
b.BuildConnectivity()
zones = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == NET and z.IsOnLayer(lid)]
zv = pcbnew.ZONES()
for z in zones:
    zv.append(z)


def pieces():
    pcbnew.ZONE_FILLER(b).Fill(zv)
    return sum(z.GetFilledPolysList(lid).OutlineCount() for z in zones)


base = pieces()
print('%s on %s: %d pieces' % (NET, LAYER, base))
by_net = collections.defaultdict(list)
for t in b.GetTracks():
    if t.GetClass() != 'PCB_VIA' and t.GetLayer() == lid and t.GetNetname() != NET:
        by_net[t.GetNetname()].append(t)
KEEP = []
for n, ts in sorted(by_net.items()):
    for t in ts:
        b.Remove(t)
        KEEP.append(t)
    b.BuildConnectivity()
    k = pieces()
    for t in ts:
        b.Add(t)
    b.BuildConnectivity()
    L = sum(pcbnew.ToMM(t.GetLength()) for t in ts)
    if k < base:
        print('  without %-22s (%.1f mm on %s): %d pieces' % (n, L, LAYER, k))
print('done')
