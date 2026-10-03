"""Remove dangling tracks and vias with KiCad's own connectivity test, several rounds per run, then refill and save
(KiCad Python). Faster than prune_dangling.py, which trims one segment per DRC round.

    python.exe prune_chains.py BOARD_IN.kicad_pcb BOARD_OUT.kicad_pcb [NET,NET,...]

KiCad 10's SWIG wrappers stop working after a few rounds of BOARD.Remove (GetTracks and the connectivity object turn
into bare SwigPyObjects), so a run stops there, saves, and prints "removed N"; run it again until N is 0.
With a net list only those nets are pruned. Copy the rules .kicad_pro back beside the output afterwards (SaveBoard).
"""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
only = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None
total = 0
tracks = list(b.GetTracks())
for rnd in range(50):
    try:
        b.BuildConnectivity()
        conn = b.GetConnectivity()
        dead = [t for t in tracks if (only is None or t.GetNetname() in only) and conn.TestTrackEndpointDangling(t, False)]
    except (AttributeError, TypeError):
        print('round %d: SWIG wrappers gone stale, saving what is done' % (rnd + 1))
        break
    if not dead:
        break
    for t in dead:
        b.Remove(t)
    gone = set(id(t) for t in dead)
    tracks = [t for t in tracks if id(t) not in gone]
    total += len(dead)
    print('round %d: removed %d' % (rnd + 1, len(dead)))
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print('removed %d' % total)
