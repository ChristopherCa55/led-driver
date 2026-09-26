"""Build a copper version onto the placed board (KiCad Python).

usage: python.exe build_copper.py BASE.kicad_pcb SPEC.json OUT.kicad_pcb [BLACKLIST.json]

Adds the spec's zones (rect unions per zone, one ZONE per resulting outline, all listed layers) and via fields
(through vias, unconnected layers removed), skipping vias whose rounded position is in the blacklist, then
refills every zone and saves. Existing keep-out zones on the base board are kept.
"""
import json, sys
import pcbnew

base, spec_path, out = sys.argv[1:4]
black = set()
if len(sys.argv) > 4:
    black = set(tuple(p) for p in json.load(open(sys.argv[4])))
spec = json.load(open(spec_path))
board = pcbnew.LoadBoard(base)
FMM = pcbnew.FromMM
nets = board.GetNetsByName()


def netinfo(name):
    for k in (name,):
        try:
            return nets[k]
        except Exception:
            pass
    it = board.FindNet(name)
    if it is None:
        raise SystemExit('net not on board: ' + name)
    return it


def rect_chain(r):
    x0, y0, x1, y1 = r
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ch.Append(FMM(x), FMM(y))
    ch.SetClosed(True)
    return ch


nz = 0
for zs in spec['zones']:
    poly = pcbnew.SHAPE_POLY_SET()
    for r in zs['rects']:
        p = pcbnew.SHAPE_POLY_SET()
        p.AddOutline(rect_chain(r))
        poly.BooleanAdd(p)
    poly.Simplify()
    ls = pcbnew.LSET()
    for ln in zs['layers']:
        ls.AddLayer(board.GetLayerID(ln))
    ni = netinfo(zs['net'])
    for i in range(poly.OutlineCount()):
        z = pcbnew.ZONE(board)
        z.SetLayerSet(ls)
        z.SetNet(ni)
        z.SetZoneName(zs['name'])
        o = z.Outline()
        o.RemoveAllContours()
        o.AddOutline(poly.Outline(i))
        for h in range(poly.HoleCount(i)):
            o.AddHole(poly.Hole(i, h))
        z.SetAssignedPriority(int(zs['prio']))
        z.SetLocalClearance(FMM(zs['clearance']))
        z.SetMinThickness(FMM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
        board.Add(z)
        nz += 1

for ko in spec.get('keepouts', []):
    # rule area that only forbids zone fills (tracks, vias and pads stay allowed)
    ls = pcbnew.LSET()
    for ln in ko['layers']:
        ls.AddLayer(board.GetLayerID(ln))
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetLayerSet(ls)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName(ko['name'])
    o = z.Outline()
    o.RemoveAllContours()
    o.AddOutline(rect_chain(ko['rect']))
    board.Add(z)

nv, skipped = 0, 0
for v in spec['vias']:
    key = (round(v['x'], 2), round(v['y'], 2))
    if key in black:
        skipped += 1
        continue
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(FMM(v['x']), FMM(v['y'])))
    via.SetWidth(FMM(v['dia']))
    via.SetDrill(FMM(v['drill']))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(netinfo(v['net']))
    via.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_ALL)
    board.Add(via)
    nv += 1

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(out, board)
print('zones %d, vias %d (blacklisted %d) -> %s' % (nz, nv, skipped, out))
