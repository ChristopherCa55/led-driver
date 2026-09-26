"""Replace a board's J9 with the current library footprint (KiCad Python).

usage: python.exe update_j9.py BOARD_IN.kicad_pcb LIB.pretty BOARD_OUT.kicad_pcb

The footprint name and pinout do not change (the schematic still points at BOOST:<name>), only its graphics, so
this is KiCad's "update footprint from library" for one part: the new instance takes the old one's position,
orientation, side, lock, reference, value, schematic path and sheet data, and every pad keeps its net. The script
stops if a pad number of the old footprint is missing from the new one. Copy the shipped .kicad_pro next to the
output afterwards (SaveBoard rewrites the project file).
"""
import sys
import pcbnew

src, lib, out = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
old = [f for f in b.GetFootprints() if f.GetReference() == 'J9'][0]
name = old.GetFPID().GetLibItemName().wx_str()
new = pcbnew.FootprintLoad(lib, name)
assert new is not None, 'footprint %s not found in %s' % (name, lib)
new.SetParent(b)
new.SetFPID(old.GetFPID())
new.SetPath(old.GetPath())
new.SetSheetname(old.GetSheetname())
new.SetSheetfile(old.GetSheetfile())
new.SetReference(old.GetReference())
new.SetValue(old.GetValue())
for fld in old.GetFields():
    if fld.GetName() not in ('Reference', 'Value', 'Footprint') and not new.HasField(fld.GetName()):
        f2 = pcbnew.PCB_FIELD(new, new.GetNextFieldOrdinal(), fld.GetName())
        f2.SetText(fld.GetText())
        f2.SetVisible(False)
        f2.SetLayer(pcbnew.F_Fab)
        new.Add(f2)
if old.IsFlipped():
    new.Flip(new.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
new.SetOrientationDegrees(old.GetOrientationDegrees())
new.SetPosition(old.GetPosition())
nets = {p.GetNumber(): p.GetNet() for p in old.Pads() if p.GetNumber()}
have = {p.GetNumber() for p in new.Pads() if p.GetNumber()}
assert set(nets) <= have, 'pads missing in the new footprint: %s' % sorted(set(nets) - have)
for p in new.Pads():
    if p.GetNumber() in nets:
        p.SetNet(nets[p.GetNumber()])
new.SetLocked(old.IsLocked())
b.Remove(old)
b.Add(new)
pcbnew.SaveBoard(out, b)
d = [(p.GetNumber(), pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y), p.GetNetname()) for p in new.Pads()
     if p.GetNumber() in ('1', '11')]
print('J9 replaced from %s (%d silk items); pads %s; saved %s' % (
    lib, sum(1 for g in new.GraphicalItems() if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)), d, out))
