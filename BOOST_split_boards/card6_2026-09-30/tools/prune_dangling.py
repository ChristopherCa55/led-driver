"""Delete the tracks and vias a DRC report flags as track_dangling / via_dangling, rebuild connectivity, refill zones
twice, save (KiCad Python).

usage: python.exe prune_dangling.py BOARD_IN.kicad_pcb DRC.json BOARD_OUT.kicad_pcb
A track is matched by net, layer, an end point at the reported position and its length. Run DRC again afterwards:
removing an end segment can expose the next one, and the unconnected count must stay 0.
"""
import json, math, re, sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
rep = json.load(open(sys.argv[2]))
MM = pcbnew.ToMM
want = []
for v in rep['violations']:
    if v['type'] != 'track_dangling':
        continue
    for it in v['items']:
        m = re.match(r'Track \[(.*)\] on (\S+), length ([0-9.]+) mm', it['description'])
        if m:
            want.append((m.group(1), m.group(2), float(m.group(3)), it['pos']['x'], it['pos']['y']))
vias = []
for v in rep['violations']:
    if v['type'] != 'via_dangling':
        continue
    for it in v['items']:
        m = re.match(r'Via \[(.*)\] on', it['description'])
        if m:
            vias.append((m.group(1), it['pos']['x'], it['pos']['y']))
gone = 0
for t in list(board.GetTracks()):
    if t.GetClass() == 'PCB_VIA':
        for net, x, y in vias:
            if t.GetNetname() == net and math.hypot(MM(t.GetPosition().x) - x, MM(t.GetPosition().y) - y) < 1e-3:
                board.Remove(t)
                gone += 1
                print('removed via %s at (%.3f, %.3f)' % (net, x, y))
                break
        continue
    if t.GetClass() != 'PCB_TRACK':
        continue
    for net, layer, length, x, y in want:
        if t.GetNetname() != net or board.GetLayerName(t.GetLayer()) != layer or abs(MM(t.GetLength()) - length) > 1e-3:
            continue
        ends = [(MM(t.GetStart().x), MM(t.GetStart().y)), (MM(t.GetEnd().x), MM(t.GetEnd().y))]
        if any(math.hypot(ex - x, ey - y) < 1e-3 for ex, ey in ends):
            board.Remove(t)
            gone += 1
            print('removed %s %s %.3f mm at (%.3f, %.3f)' % (net, layer, length, x, y))
            break
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[3], board)
print('removed %d of %d flagged tracks and vias -> %s' % (gone, len(want) + len(vias), sys.argv[3]))
