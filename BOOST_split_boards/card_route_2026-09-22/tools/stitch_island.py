"""Tie an isolated fill island to the planes with one via of the zone's net (KiCad Python).

usage: python.exe stitch_island.py BOARD.kicad_pcb OUT.kicad_pcb NET LAYER X Y [R] [--avoid REF.PAD:MM]

--rings L1,L2,..: the via keeps rings only on these layers (unused rings removed, as the router's signal vias); on the
other layers only its hole needs clearance (0.2 mm copper to hole)
--avoid: keep the via this far from that pad's copper even though it is of the same net (a thermal-relief pad such as
J9.10 must not get a via in its ring, which would tie it straight to the planes and undo the relief).

Finds the filled piece of NET's zone on LAYER that holds (X, Y) or lies within R mm of it (default 1.5), then tries via
positions on a 0.05 mm grid inside that piece, nearest to (X, Y) first. A position is legal when the via (0.5 / 0.3,
rings on every layer, as the router's GND vias) keeps, on every copper layer, the larger of the two netclass
clearances from all copper of other nets, 0.2 mm hole clearance and 0.25 mm hole to hole, 0.3 mm from the board edge
and from non-plated holes, and stays out of the rule areas. The first legal position is used; the board is refilled
and saved. For GND the user's 2 mm rule round U2 In+ / Current does not apply (GND stitching is exempt), but the via
is still kept 2 mm from their copper here, to leave the corridors untouched.
"""
import math, sys
import pcbnew

AVOID = [x.split('=', 1)[1] if '=' in x else None for x in sys.argv if x.startswith('--avoid')]
av = sys.argv[sys.argv.index('--avoid') + 1] if '--avoid' in sys.argv else None
rg = sys.argv[sys.argv.index('--rings') + 1] if '--rings' in sys.argv else None
RINGS = set(rg.split(',')) if rg else None
argv = [x for x in sys.argv if x not in ('--avoid', av, '--rings', rg)]
SRC, OUT, NET, LAYER = argv[1:5]
X, Y = float(argv[5]), float(argv[6])
R = float(argv[7]) if len(argv) > 7 else 1.5
FM, MM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(SRC)
b.BuildConnectivity()
LID = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
CLR = {'GND': 0.25}


def clr(n):
    return CLR.get(n, 0.2)


zone = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == NET and z.IsOnLayer(LID[LAYER])]
piece = None
p0 = pcbnew.VECTOR2I(FM(X), FM(Y))
for z in zone:
    ps = z.GetFilledPolysList(LID[LAYER])
    for i in range(ps.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(ps.Outline(i))
        for h in range(ps.HoleCount(i)):
            one.AddHole(ps.Hole(i, h))
        if one.Collide(p0, FM(R)):
            if piece is None or one.Area() < piece.Area():
                piece = one
if piece is None:
    sys.exit('no %s fill piece on %s within %.1f mm of (%.2f, %.2f)' % (NET, LAYER, R, X, Y))
print('island: %.2f mm2' % (piece.Area() * 1e-12))
items = []      # (net, layer id or None for all, shape)
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        for ln, lid in LID.items():
            items.append((t.GetNetname(), lid, t.GetEffectiveShape(lid)))
        items.append(('<hole>', None, t.GetEffectiveHoleShape()))
    else:
        items.append((t.GetNetname(), t.GetLayer(), t.GetEffectiveShape(t.GetLayer())))
for f in b.GetFootprints():
    for p in f.Pads():
        for ln, lid in LID.items():
            if p.IsOnLayer(lid):
                items.append((p.GetNetname(), lid, p.GetEffectiveShape(lid)))
        if p.GetDrillSize().x > 0:
            items.append(('<npth>' if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else '<hole>', None,
                          p.GetEffectiveHoleShape()))
sens = [s for (n, l, s) in items if n in ('Net-(U2-In+)', 'Current')]
LNAME = {lid: ln for ln, lid in LID.items()}
avoid = []
if av:
    ref_pad, dmm = av.split(':')
    ref, num = ref_pad.split('.')
    for f in b.GetFootprints():
        if f.GetReference() == ref:
            for p in f.Pads():
                if p.GetNumber() == num:
                    avoid = [(p.GetEffectiveShape(lid), float(dmm)) for lid in LID.values() if p.IsOnLayer(lid)]
areas = [z for z in b.Zones() if z.GetIsRuleArea()]
bb = b.GetBoardEdgesBoundingBox()


def legal(x, y):
    c = pcbnew.VECTOR2I(FM(x), FM(y))
    if not piece.Collide(c, 0):
        return False
    if min(x - MM(bb.GetLeft()), MM(bb.GetRight()) - x, y - MM(bb.GetTop()), MM(bb.GetBottom()) - y) < 0.3 + 0.25:
        return False
    ring = pcbnew.SHAPE_CIRCLE(c, FM(0.25))
    hole = pcbnew.SHAPE_CIRCLE(c, FM(0.15))
    for z in areas:
        if z.Outline().Collide(c, FM(0.25)):
            return False
    for s in sens:
        if s.Collide(ring, FM(2.0)):
            return False
    for s, dmm in avoid:
        if s.Collide(ring, FM(dmm)):
            return False
    for n, l, s in items:
        if n == '<hole>':
            if s.Collide(hole, FM(0.25)) or s.Collide(ring, FM(0.2)):
                return False
        elif n == '<npth>':
            if s.Collide(ring, FM(0.3)):
                return False
        elif n != NET:
            ringed = RINGS is None or l is None or LNAME.get(l) in RINGS
            if ringed and s.Collide(ring, FM(max(clr(n), clr(NET)))):
                return False
            if not ringed and s.Collide(hole, FM(0.2)):
                return False
    return True


cands = []
for i in range(-60, 61):
    for j in range(-60, 61):
        x, y = round(X + i * 0.05, 3), round(Y + j * 0.05, 3)
        cands.append((math.hypot(x - X, y - Y), x, y))
cands.sort()
for d, x, y in cands:
    if legal(x, y):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
        v.SetWidth(FM(0.5))
        v.SetDrill(FM(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(b.FindNet(NET))
        v.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL if RINGS is None
                                             else pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_ALL)
        b.Add(v)
        b.BuildConnectivity()
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(OUT, b)
        print('%s via at (%.3f, %.3f), %.2f mm from (%.2f, %.2f) -> %s' % (NET, x, y, d, X, Y, OUT))
        break
else:
    sys.exit('no legal via position in the island')
