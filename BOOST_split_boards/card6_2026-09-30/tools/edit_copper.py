"""Scripted copper edits on a routed board (KiCad Python): the last few fixes the routers leave.

usage: python.exe edit_copper.py BOARD_IN.kicad_pcb EDITS.json BOARD_OUT.kicad_pcb

EDITS.json is a list of operations, applied in order:
  {"op": "move_via", "net": N, "x": X, "y": Y, "dx": DX, "dy": DY}
      moves the via of net N at (X, Y) by (DX, DY) mm, with every track end of N that sat on its centre
  {"op": "track", "net": N, "layer": L, "x0": .., "y0": .., "x1": .., "y1": .., "w": W}
      adds a track (a via that only touches a pad's edge counts as connected in route_card.py but not in KiCad:
      a short track from the via centre to the pad centre makes the joint real)
  {"op": "via", "net": N, "x": X, "y": Y, "dia": 0.5, "drill": 0.3}
  {"op": "delete_track", "net": N, "layer": L, "x0": .., "y0": .., "x1": .., "y1": ..}
Zones are emptied before the edits and refilled after (KiCad otherwise pulls new copper onto the fill's net), and
every item keeps its net. Check the result with KiCad DRC.
"""
import json, sys
import pcbnew

src, edits_path, out = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
FM, MM = pcbnew.FromMM, pcbnew.ToMM
KEEP = []
for z in b.Zones():
    z.UnFill()
tracks = list(b.GetTracks())
nets = {t.m_Uuid.AsString(): t.GetNetname() for t in tracks}
TOL = FM(0.001)


def at(p, x, y, tol=TOL):
    return abs(p.x - FM(x)) <= tol and abs(p.y - FM(y)) <= tol


for e in json.load(open(edits_path)):
    if e['op'] == 'move_via':
        vias = [t for t in tracks if t.GetClass() == 'PCB_VIA' and t.GetNetname() == e['net'] and
                at(t.GetPosition(), e['x'], e['y'], FM(0.002))]
        if len(vias) != 1:
            sys.exit('move_via: %d vias of %s at (%.3f, %.3f)' % (len(vias), e['net'], e['x'], e['y']))
        v = vias[0]
        old = v.GetPosition()
        new = pcbnew.VECTOR2I(old.x + FM(e['dx']), old.y + FM(e['dy']))
        moved = 0
        for t in tracks:
            if t.GetClass() == 'PCB_VIA' or t.GetNetname() != e['net']:
                continue
            if at(t.GetStart(), MM(old.x), MM(old.y), FM(0.002)):
                t.SetStart(new)
                moved += 1
            if at(t.GetEnd(), MM(old.x), MM(old.y), FM(0.002)):
                t.SetEnd(new)
                moved += 1
        v.SetPosition(new)
        print('moved via %s (%.3f, %.3f) -> (%.3f, %.3f), %d track ends' % (
            e['net'], MM(old.x), MM(old.y), MM(new.x), MM(new.y), moved))
    elif e['op'] == 'track':
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(FM(e['x0']), FM(e['y0'])))
        t.SetEnd(pcbnew.VECTOR2I(FM(e['x1']), FM(e['y1'])))
        t.SetWidth(FM(e['w']))
        t.SetLayer(b.GetLayerID(e['layer']))
        t.SetNet(b.FindNet(e['net']))
        b.Add(t)
        KEEP.append(t)
        tracks.append(t)
        nets[t.m_Uuid.AsString()] = e['net']
        print('added track %s %s (%.3f, %.3f)-(%.3f, %.3f) w %.2f' % (
            e['net'], e['layer'], e['x0'], e['y0'], e['x1'], e['y1'], e['w']))
    elif e['op'] == 'via':
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(FM(e['x']), FM(e['y'])))
        v.SetWidth(FM(e.get('dia', 0.5)))
        v.SetDrill(FM(e.get('drill', 0.3)))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(b.FindNet(e['net']))
        v.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL if e['net'] == 'GND'
                                             else pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_ALL)
        b.Add(v)
        KEEP.append(v)
        tracks.append(v)
        nets[v.m_Uuid.AsString()] = e['net']
        print('added via %s (%.3f, %.3f)' % (e['net'], e['x'], e['y']))
    elif e['op'] == 'delete_track':
        hit = [t for t in tracks if t.GetClass() != 'PCB_VIA' and t.GetNetname() == e['net'] and
               b.GetLayerName(t.GetLayer()) == e['layer'] and
               ((at(t.GetStart(), e['x0'], e['y0'], FM(0.002)) and at(t.GetEnd(), e['x1'], e['y1'], FM(0.002))) or
                (at(t.GetStart(), e['x1'], e['y1'], FM(0.002)) and at(t.GetEnd(), e['x0'], e['y0'], FM(0.002))))]
        for t in hit:
            b.Remove(t)
            KEEP.append(t)
            tracks.remove(t)
        print('deleted %d track(s) of %s' % (len(hit), e['net']))
for rnd in range(3):
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    moved = [t for t in tracks if nets.get(t.m_Uuid.AsString()) not in (None, t.GetNetname())]
    for t in moved:
        t.SetNet(b.FindNet(nets[t.m_Uuid.AsString()]))
    if not moved:
        break
    print('round %d: %d items put back on their nets' % (rnd, len(moved)))
pcbnew.SaveBoard(out, b)
print('saved', out)
