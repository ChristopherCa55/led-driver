"""Final save of a routed board (KiCad Python): load, rebuild connectivity, refill every zone, save; then load the
saved file again in the same way, refill and save once more, so the file on disk is exactly what a fresh load and
refill produces.

usage: python.exe finalize.py BOARD_IN.kicad_pcb BOARD_OUT.kicad_pcb
Copy the rules .kicad_pro and .kicad_dru next to BOARD_OUT afterwards (SaveBoard drops the netclasses and rules).
"""
import sys
import pcbnew

src, out = sys.argv[1], sys.argv[2]
for path in (src, out):
    board = pcbnew.LoadBoard(path)
    board.BuildConnectivity()
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(out, board)
    n_t = sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK')
    n_v = sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_VIA')
    print('loaded %s, refilled %d zones, saved %s (%d tracks, %d vias)' % (path, board.GetAreaCount(), out, n_t, n_v))
