"""GND vias: which copper layers each one connects to, and why the others are missed (KiCad Python, on a COPY:
LoadBoard writes a .kicad_prl beside the board).

    python.exe gnd_via_layers.py BOARD.kicad_pcb [--list]

The zones are refilled in memory first (nothing is saved). A layer counts as connected when a GND track ends at the
via or the via lies in GND zone fill on that layer (pads are not counted, so a via in a GND pad can show one fewer).
For each missed layer: a higher-priority pour of another net owns that spot, a GND pour exists there but its fill
does not reach the via (listed with --list), or only another net's pour / no pour is there.
"""
import sys, collections
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
LIST = '--list' in sys.argv
cu = list(b.GetEnabledLayers().CuStack())
name = {l: b.GetLayerName(l) for l in cu}
zones = [z for z in b.Zones() if not z.GetIsRuleArea()]
tracks_at = collections.defaultdict(set)
for t in b.Tracks():
    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GND':
        for p in (t.GetStart(), t.GetEnd()):
            tracks_at[(p.x, p.y)].add(t.GetLayer())

nconn = collections.Counter()
why = collections.Counter()
per_layer = collections.Counter()
nv = 0
for v in b.Tracks():
    if v.GetClass() != 'PCB_VIA' or v.GetNetname() != 'GND':
        continue
    nv += 1
    p = v.GetPosition()
    vp = pcbnew.VECTOR2I(p.x, p.y)
    conn = set(tracks_at.get((p.x, p.y), set()))
    for l in cu:
        for z in zones:
            if z.GetNetname() == 'GND' and z.IsOnLayer(l) and z.GetFilledPolysList(l).Contains(vp, -1, 1000):
                conn.add(l)
                break
    nconn[len(conn)] += 1
    for l in cu:
        if l in conn:
            continue
        per_layer[name[l]] += 1
        outl = [z for z in zones if z.IsOnLayer(l) and z.Outline().Contains(vp)]
        g = [z for z in outl if z.GetNetname() == 'GND']
        other = [z for z in outl if z.GetNetname() != 'GND']
        if g and other and max(o.GetAssignedPriority() for o in other) > max(x.GetAssignedPriority() for x in g):
            why['other-net pour has priority here'] += 1
        elif g:
            why['GND pour exists, fill blocked locally'] += 1
            if LIST:
                print('  blocked: %s at (%.2f, %.2f)' % (name[l], p.x / 1e6, p.y / 1e6))
        elif other:
            why['only an other-net pour here'] += 1
        else:
            why['no pour on this layer here'] += 1
print('GND vias:', nv)
print('layers connected (of %d):' % len(cu), dict(sorted(nconn.items())))
print('missed, by layer:', dict(per_layer))
print('missed, by reason:', dict(why))
