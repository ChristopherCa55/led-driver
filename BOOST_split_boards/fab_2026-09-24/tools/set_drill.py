"""Set the drill of every plated round hole of one footprint (KiCad Python). Pad sizes are not changed.

usage: python.exe set_drill.py BOARD_IN.kicad_pcb REF DRILL_MM BOARD_OUT.kicad_pcb

For J10 / J11 (the Samtec ESQ / TSW pair): the user's answer of 2026-09-15 was 1.05 mm, because Samtec's 1.02 +/- 0.03
is a finished hole and JLCPCB's plated-hole tolerance (+0.13 / -0.08 mm) can take a 1.00 mm drill down to 0.92 mm
against a 0.64 mm square post (0.90 mm across its diagonal). Zones are left as they are; run DRC with --refill-zones.
"""
import sys
import pcbnew

src, ref, drill, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
b = pcbnew.LoadBoard(src)
f = b.FindFootprintByReference(ref)
n = 0
ring = 1e9
for p in f.Pads():
    if p.HasHole() and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
        d = p.GetDrillSize()
        if d.x != d.y:
            continue
        p.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(drill), pcbnew.FromMM(drill)))
        sz = p.GetSize(pcbnew.F_Cu)
        ring = min(ring, (pcbnew.ToMM(min(sz.x, sz.y)) - drill) / 2)
        n += 1
pcbnew.SaveBoard(out, b)
print('%s: %d plated holes set to %.2f mm; smallest annular ring now %.3f mm; saved %s' % (ref, n, drill, ring, out))
