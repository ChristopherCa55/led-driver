"""Move vias on a board (KiCad Python), refill zones, save.

usage: python.exe move_vias.py BOARD_IN.kicad_pcb MOVES.json BOARD_OUT.kicad_pcb
MOVES.json: [[net, x_from, y_from, x_to, y_to], ...] in mm; a via matches when its net is NET and its centre is
within 0.01 mm of (x_from, y_from).
"""
import json, math, sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
moves = json.load(open(sys.argv[2]))
MM, FMM = pcbnew.ToMM, pcbnew.FromMM
done = 0
for t in board.GetTracks():
    if t.GetClass() != 'PCB_VIA':
        continue
    for net, xf, yf, xt, yt in moves:
        if t.GetNetname() == net and math.hypot(MM(t.GetPosition().x) - xf, MM(t.GetPosition().y) - yf) < 0.01:
            t.SetPosition(pcbnew.VECTOR2I(FMM(xt), FMM(yt)))
            done += 1
            print('moved %s via (%.2f, %.2f) -> (%.2f, %.2f)' % (net, xf, yf, xt, yt))
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[3], board)
print('moved %d of %d vias -> %s' % (done, len(moves), sys.argv[3]))
