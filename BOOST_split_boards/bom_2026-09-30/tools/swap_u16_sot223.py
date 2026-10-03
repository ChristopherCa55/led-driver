"""Swap U16 (TO-263-3) for a SOT-223 12 V regulator on the power board (KiCad 10 Python). Test or apply.

    python.exe swap_u16_sot223.py IN.kicad_pcb OUT.kicad_pcb VALUE MPN LCSC

- Removes U16's TO-263-3_TabPin2 footprint (pads only; no tracks end on it: its Vin and 12 V connections are vias
  at (95.05, 67.35) and (100.15, 66.65), and the tab sits in the F.Cu GND pour).
- Places Package_TO_SOT_SMD:SOT-223-3_TabPin2 (pad 1 IN, pad 2 GND + tab, pad 3 OUT: the LM2940 SOT-223 pinout of
  both TI LM2940IMP(X)-12 and UTC LM2940G-12-AA3-R) with its pins along the bottom: pad 1 at (95.30, 66.90) over the
  Vin via, pad 3 at (99.90, 66.90) over the 12 V via, tab at (97.60, 60.60) in the GND pour.
- Keeps U16's reference, symbol link (path), value fields; sets Value / MPN / LCSC; ref text on F.Fab, as the
  other small parts.
- Refills every zone (needs the .kicad_pro / .kicad_dru beside OUT for the rules).
"""
import sys
import pcbnew

MM, FM = pcbnew.ToMM, pcbnew.FromMM
src, dst, value, mpn, lcsc = sys.argv[1:6]
b = pcbnew.LoadBoard(src)
old = b.FindFootprintByReference('U16')
assert old.GetFPIDAsString() == 'Package_TO_SOT_SMD:TO-263-3_TabPin2', old.GetFPIDAsString()
nets = {p.GetNumber(): p.GetNet() for p in old.Pads()}
path, sheetname, sheetfile = old.GetPath(), old.GetSheetname(), old.GetSheetfile()
new = pcbnew.FootprintLoad('C:/Program Files/KiCad/10.0/share/kicad/footprints/Package_TO_SOT_SMD.pretty',
                           'SOT-223-3_TabPin2')
new.SetReference('U16')
new.SetValue(value)
new.SetPath(path)
new.SetSheetname(sheetname)
new.SetSheetfile(sheetfile)
new.SetFPIDAsString('Package_TO_SOT_SMD:SOT-223-3_TabPin2') if hasattr(new, 'SetFPIDAsString') else None
b.Add(new)
new.SetOrientationDegrees(90)
new.SetPosition(pcbnew.VECTOR2I(FM(97.60), FM(63.75)))
# check where pad 1 landed; if the rotation put it on the wrong side, use 270
p1 = [p for p in new.Pads() if p.GetNumber() == '1'][0]
if MM(p1.GetPosition().y) < 64 or MM(p1.GetPosition().x) > 97.6:
    new.SetOrientationDegrees(270)
    new.SetPosition(pcbnew.VECTOR2I(FM(97.60), FM(63.75)))
for p in new.Pads():
    p.SetNet(nets[p.GetNumber()])
for f in list(new.GetFields()):
    pass
for name, val in (('MPN', mpn), ('LCSC', lcsc)):
    new.SetField(name, val)          # KiCad 10: adds a user field if missing
    fld = new.GetField(name)
    fld.SetVisible(False)
    fld.SetLayer(pcbnew.F_Fab)
new.Reference().SetLayer(pcbnew.F_Fab)
b.Remove(old)
for p in new.Pads():
    print('pad', p.GetNumber(), p.GetNetname(), round(MM(p.GetPosition().x), 3), round(MM(p.GetPosition().y), 3))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
print('wrote', dst)
