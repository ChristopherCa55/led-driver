"""Move footprints on a board (KiCad Python): position, orientation and side, then refill zones and save.

usage: python.exe move_parts.py BOARD_IN.kicad_pcb MOVES.json BOARD_OUT.kicad_pcb
MOVES.json: {"REF": [x_mm, y_mm, rotation_deg, "F"|"B"], ...}  (the layout JSON convention of the placement tools:
KiCad position and orientation as the footprint reports them after the side is set)
Tracks and vias are not touched; run on an unrouted board. Copy the rules .kicad_pro/.kicad_dru next to BOARD_OUT.
"""
import json, sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
moves = json.load(open(sys.argv[2]))
fps = {f.GetReference(): f for f in board.GetFootprints()}
MM, FMM = pcbnew.ToMM, pcbnew.FromMM
for ref, (x, y, rot, side) in moves.items():
    f = fps[ref]
    want_b = side == 'B'
    if f.IsFlipped() != want_b:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetPosition(pcbnew.VECTOR2I(FMM(x), FMM(y)))
    f.SetOrientationDegrees(rot)
    print('%s -> (%.3f, %.3f) rot %.0f side %s' % (ref, MM(f.GetPosition().x), MM(f.GetPosition().y),
                                                  f.GetOrientationDegrees(), 'B' if f.IsFlipped() else 'F'))
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[3], board)
print('saved', sys.argv[3])
