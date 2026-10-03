"""Add the local GND shield on In3 over U2 In+'s In4 run (8-layer frame; In3 becomes the 6-layer card's In2), refill,
save (KiCad Python).

    python.exe add_inp_shield.py BOARD_IN.kicad_pcb BOARD_OUT.kicad_pcb [MARGIN_MM]

The zone outline is In+'s In4 tracks grown by MARGIN (default 1.8 mm, inside the 2 mm band the router keeps clear of
every other net on In3). Net GND, priority above the 5 V pour, fill settings copied from the board's GND fill zone.
Copy the rules .kicad_pro back beside the output afterwards (SaveBoard).
"""
import sys
import pcbnew

FM, MM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
margin = float(sys.argv[3]) if len(sys.argv) > 3 else 1.8
L3, L4 = b.GetLayerID('In3.Cu'), b.GetLayerID('In4.Cu')
run = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'Net-(U2-In+)' and t.GetLayer() == L4]
assert run, 'no U2 In+ track on In4'
ps = pcbnew.SHAPE_POLY_SET()
for t in run:
    t.TransformShapeToPolygon(ps, L4, FM(margin), FM(0.005), pcbnew.ERROR_OUTSIDE)
ps.Simplify()
ps.Fracture()          # zone outlines have no holes
ref = [z for z in b.Zones() if z.GetNetname() == 'GND' and not z.GetIsRuleArea() and z.IsOnLayer(b.GetLayerID('In4.Cu'))]
assert ref, 'no GND fill zone to copy settings from'
ref = ref[0]
five = [z for z in b.Zones() if z.GetNetname() == '5V' and z.IsOnLayer(L3)]
z = pcbnew.ZONE(b)
z.SetLayer(L3)
z.SetNetCode(b.FindNet('GND').GetNetCode())
z.SetZoneName('In+ shield')
z.SetAssignedPriority(max([x.GetAssignedPriority() for x in five] + [0]) + 2)
z.SetLocalClearance(ref.GetLocalClearance())
z.SetMinThickness(ref.GetMinThickness())
z.SetPadConnection(ref.GetPadConnection())
z.SetThermalReliefGap(ref.GetThermalReliefGap())
z.SetThermalReliefSpokeWidth(ref.GetThermalReliefSpokeWidth())
z.SetIslandRemovalMode(ref.GetIslandRemovalMode())
z.Outline().RemoveAllContours()
z.Outline().Append(ps)
b.Add(z)
bb = ps.BBox()
print('shield zone on In3: %d outline(s), bbox (%.2f, %.2f)-(%.2f, %.2f), %.1f mm2, priority %d' % (
    ps.OutlineCount(), MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom()), abs(ps.Area()) / 1e12,
    z.GetAssignedPriority()))
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.BuildConnectivity()
pcbnew.SaveBoard(sys.argv[2], b)
print('saved', sys.argv[2])
