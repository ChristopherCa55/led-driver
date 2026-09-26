"""Prepare the placed control card for routing (KiCad Python): planes, fills and pad connections.

usage: python.exe prep_card.py PLACED.kicad_pcb OUT.kicad_pcb [--open-plan]
then:  python set_stackup.py OUT.kicad_pcb        (the JLCPCB 8-layer 1 oz / 1 oz stackup, as on the power board)

Layer plan approved by the user (check-in 2, 2026-09-22):
  F.Cu   parts, fan-outs, short links      GND fill (yields to routes)
  In1    GND plane
  In2    logic and I2C                      GND fill
  In3    5 V plane (analog_5V and 12V may cut through it)
  In4    GND plane
  In5    analog                             GND fill (the guard beside U2 In+ and the Current / V_err runs)
  In6    GND plane
  B.Cu   parts, fan-outs, short links       GND fill
--open-plan (user, 2026-09-24): In4 is a signal layer with a GND fill (solid over the U2 In+ / Current corridors,
which the router keeps free of other nets), In3 a signal layer beside the 5 V pour, In1 and In6 the only GND planes.
Pads join their zones solidly except through-hole pads, which get thermal spokes (zone mode "THT thermal"), with two
overrides: J11's ten GND pads are solid (user decision, check-in 2 routing plan) and J9's GND pad keeps its spokes
explicitly (it is hand-soldered to a wire; user, 2026-09-22).
The H1-H4 rule areas (no copper, no footprints) stay as they are.
"""
import sys
import pcbnew

src, out = sys.argv[1:3]
OPEN = '--open-plan' in sys.argv
FM = pcbnew.FromMM
b = pcbnew.LoadBoard(src)
for z in list(b.Zones()):
    if not z.GetIsRuleArea():
        b.Remove(z)
X0, Y0, X1, Y1 = 45.8905, 70.0226, 90.8905, 115.0226     # card outline (edge clearance keeps fills 0.3 mm inside)


def zone(name, net, layers, prio, clearance):
    z = pcbnew.ZONE(b)
    ls = pcbnew.LSET()
    for ln in layers:
        ls.AddLayer(b.GetLayerID(ln))
    z.SetLayerSet(ls)
    z.SetNet(b.FindNet(net))
    z.SetZoneName(name)
    z.SetAssignedPriority(prio)
    o = z.Outline()
    o.NewOutline()
    for x, y in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)):
        o.Append(FM(x), FM(y))
    z.SetLocalClearance(FM(clearance))
    z.SetMinThickness(FM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    z.SetThermalReliefGap(FM(0.3))
    z.SetThermalReliefSpokeWidth(FM(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)
    return z


if OPEN:
    zone('GND planes', 'GND', ['In1.Cu', 'In6.Cu'], 1, 0.25)
    zone('GND fill', 'GND', ['F.Cu', 'In2.Cu', 'In4.Cu', 'In5.Cu', 'B.Cu'], 0, 0.25)
    zone('5V pour', '5V', ['In3.Cu'], 0, 0.2)
else:
    zone('GND planes', 'GND', ['In1.Cu', 'In4.Cu', 'In6.Cu'], 1, 0.25)
    zone('GND fill', 'GND', ['F.Cu', 'In2.Cu', 'In5.Cu', 'B.Cu'], 0, 0.25)
    zone('5V plane', '5V', ['In3.Cu'], 0, 0.2)
fps = {f.GetReference(): f for f in b.GetFootprints()}
solid = []
for p in fps['J11'].Pads():
    if p.GetNetname() == 'GND':
        p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        solid.append(p.GetNumber())
for p in fps['J9'].Pads():
    if p.GetNetname() == 'GND':
        p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)
assert len(solid) == 10, solid
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(out, b)
print('zones: %s; J11 GND pads solid (%s); J9.10 thermal; saved %s' % (
    'GND planes In1/In6, GND fill F/In2/In4/In5/B, 5V pour In3 (open plan)' if OPEN else
    'GND planes In1/In4/In6, GND fill F/In2/In5/B, 5V plane In3', ' '.join(sorted(solid, key=int)), out))
