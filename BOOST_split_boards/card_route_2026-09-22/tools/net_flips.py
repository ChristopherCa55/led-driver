"""Router items whose net changed on the board (KiCad Python).

usage: python.exe net_flips.py BOARD.kicad_pcb ROUTES.json

Every track and via in ROUTES.json is looked up on BOARD by geometry (layer, end points / position); prints the ones
that are missing or that carry a different net there. KiCad can reassign the net of a router item it considers
connected only to another net's copper, which DRC does not report when nothing ends up unconnected.
"""
import json, sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
r = json.load(open(sys.argv[2]))
mm = lambda v: round(pcbnew.ToMM(v), 3)
tracks, vias = {}, {}
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        p = t.GetPosition()
        vias.setdefault((mm(p.x), mm(p.y)), []).append(t.GetNetname())
    else:
        s, e = t.GetStart(), t.GetEnd()
        k = (t.GetLayerName(), mm(s.x), mm(s.y), mm(e.x), mm(e.y))
        tracks.setdefault(k, []).append(t.GetNetname())
flips = missing = 0
for t in r['tracks']:
    k = (t['layer'], round(t['x0'], 3), round(t['y0'], 3), round(t['x1'], 3), round(t['y1'], 3))
    nets = tracks.get(k)
    if nets is None:
        missing += 1
    elif t['net'] not in nets:
        flips += 1
        print('track %s %s: routed %s, board %s' % (k[0], k[1:], t['net'], ','.join(nets)))
for v in r['vias']:
    nets = vias.get((round(v['x'], 3), round(v['y'], 3)))
    if nets is None:
        missing += 1
    elif v['net'] not in nets:
        flips += 1
        print('via (%.3f, %.3f): routed %s, board %s' % (v['x'], v['y'], v['net'], ','.join(nets)))
print('%d router items, %d with another net on the board, %d not found (pruned)' % (
    len(r['tracks']) + len(r['vias']), flips, missing))
