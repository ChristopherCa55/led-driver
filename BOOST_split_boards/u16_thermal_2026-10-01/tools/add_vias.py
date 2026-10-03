# Add GND stitching vias around U16 on a COPY of the power board, refill the zones and save (KiCad Python).
# Usage: "C:/Program Files/KiCad/10.0/bin/python.exe" tools/add_vias.py IN.kicad_pcb OUT.kicad_pcb CONFIG
# The vias copy an existing 0.4/0.8 mm GND via (Power netclass), so they get the board's own via settings.
import sys
sys.path.insert(0, 'tools')
import pcbnew
from vias import CONFIGS

src, dst, cfg = sys.argv[1], sys.argv[2], sys.argv[3]
b = pcbnew.LoadBoard(src)
proto = None
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND' and abs(t.GetDrillValue() - 400000) < 1 \
            and abs(t.GetWidth(pcbnew.F_Cu) - 800000) < 1:
        proto = t
        break
assert proto is not None
n = 0
for x, y in CONFIGS[cfg][1]:
    v = proto.Duplicate()
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    b.Add(v)
    n += 1
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(dst)
print('added %d vias, refilled, saved %s' % (n, dst))
