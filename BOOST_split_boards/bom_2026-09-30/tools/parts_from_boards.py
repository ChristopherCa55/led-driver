"""Every footprint on the two boards, in the schema build_bom.py reads (KiCad 10 Python), 2026-09-30.

usage: "C:/Program Files/KiCad/10.0/bin/python.exe" tools/parts_from_boards.py POWER.kicad_pcb CARD.kicad_pcb OUT.json

Per footprint: ref, value, fp, side, x / y relative to the board's drill/place origin (y down, as on screen), rot,
tht, npads (copper pads, i.e. solder joints), exclude_bom, plus the schematic fields MPN / LCSC when present.
"""
import json, sys
import pcbnew

MM = pcbnew.ToMM
out = {}
for name, path in (('power', sys.argv[1]), ('card', sys.argv[2])):
    b = pcbnew.LoadBoard(path)
    org = b.GetDesignSettings().GetAuxOrigin()
    rows = []
    for f in b.GetFootprints():
        pos = f.GetPosition()
        npads = len(list(f.Pads()))   # every pad, as the 2026-09-24 extractor counted them
        fields = {}
        for fl in f.GetFields():
            if fl.GetName() in ('MPN', 'LCSC', 'Manufacturer'):
                fields[fl.GetName()] = fl.GetText()
        rows.append(dict(ref=f.GetReference(), value=f.GetValue(), fp=f.GetFPIDAsString(),
                         side='bottom' if f.IsFlipped() else 'top', x=round(MM(pos.x - org.x), 4),
                         y=round(MM(pos.y - org.y), 4), rot=f.GetOrientationDegrees(),
                         tht=any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads()), npads=npads,
                         exclude_bom=bool(f.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM), **fields))
    rows.sort(key=lambda r: r['ref'])
    out[name] = rows
    print(name, len(rows), 'footprints, aux origin (%.3f, %.3f)' % (MM(org.x), MM(org.y)))
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
