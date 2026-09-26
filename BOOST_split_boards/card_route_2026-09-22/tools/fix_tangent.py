"""Join vias that overlap or touch an SMD pad of their net without KiCad counting it (KiCad Python).

usage: python.exe fix_tangent.py BOARD_IN.kicad_pcb OUT_EDITS.json [DRC.json]

With DRC.json, the track-end links are written only for nets that DRC reports unconnected (a segment end that sits in
another segment's joint is usually fine and would only add clutter).

route_card.py counts a via as joined to a pad when their rasters touch or overlap; KiCad's connectivity is anchor-based
and joins them only when the via centre lies in the pad or the pad centre in the via (2026-09-24, R77.1: 0.1 mm of
overlap, unconnected). Such a via comes out unconnected or dangling, and prune_dangling.py then deletes it. For every such via this writes an edit_copper.py 'track' from the via centre to the pad centre on the pad's
layer, at 0.2 mm (0.15 mm when the pad is narrower than 0.5 mm); KiCad DRC then checks it like any other track.
"""
import json, re, sys
import pcbnew

OPEN = None
if len(sys.argv) > 3:
    OPEN = set()
    for u in json.load(open(sys.argv[3]))['unconnected_items']:
        for it in u['items']:
            m = re.search(r'\[([^\]]+)\]', it['description'])
            if m:
                OPEN.add(m.group(1).replace('/', '{slash}'))
                OPEN.add(m.group(1))

b = pcbnew.LoadBoard(sys.argv[1])
b.BuildConnectivity()
FM, MM = pcbnew.FromMM, pcbnew.ToMM
L = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
pads = [(p, f) for f in b.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
edits = []
for v in b.GetTracks():
    if v.GetClass() != 'PCB_VIA':
        continue
    n = v.GetNetname()
    ring = pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetWidth(pcbnew.F_Cu) // 2)
    for p, f in pads:
        if p.GetNetname() != n:
            continue
        ln = 'B.Cu' if f.IsFlipped() else 'F.Cu'
        sh = p.GetEffectiveShape(L[ln])
        # KiCad joins a via and a pad only when one's centre lies inside the other (connectivity is anchor-based);
        # copper that merely overlaps, or touches, stays unconnected
        if not sh.Collide(ring, FM(0.03)):
            continue
        if sh.Collide(v.GetPosition(), 0) or (p.GetPosition() - v.GetPosition()).EuclideanNorm() <=                 v.GetWidth(pcbnew.F_Cu) // 2:
            continue
        c, q = v.GetPosition(), p.GetPosition()
        r = v.GetWidth(pcbnew.F_Cu) // 2
        linked = False
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA' or t.GetNetname() != n or t.GetLayer() != L[ln]:
                continue
            for e0, e1 in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
                if (e0 - c).EuclideanNorm() <= r and sh.Collide(e1, 0):
                    linked = True
        if linked:
            continue            # a track already runs from inside the via into the pad
        w = 0.15 if min(MM(p.GetSize(L[ln]).x), MM(p.GetSize(L[ln]).y)) < 0.5 else 0.2
        edits.append(dict(op='track', net=n, layer=ln, x0=round(MM(c.x), 4), y0=round(MM(c.y), 4),
                          x1=round(MM(q.x), 4), y1=round(MM(q.y), 4), w=w))
        print('%s: via (%.3f, %.3f) touches %s.%s -> link on %s' % (n, MM(c.x), MM(c.y), f.GetReference(),
                                                                    p.GetNumber(), ln))
# track ends: KiCad joins a track to a pad or via only when the end point lies inside it; an end whose round cap
# merely overlaps the pad or via (route_card.py's raster counts that) gets a short link to the item's centre
anchors = []            # (net, layer id, shape or via radius, centre, what)
for v in b.GetTracks():
    if v.GetClass() == 'PCB_VIA':
        for lid in L.values():
            if v.FlashLayer(lid):
                anchors.append((v.GetNetname(), lid, v.GetWidth(lid) // 2, v.GetPosition(), 'via'))
for p, f in [(p, f) for f in b.GetFootprints() for p in f.Pads()]:
    for lid in L.values():
        if p.IsOnLayer(lid) and p.FlashLayer(lid):
            anchors.append((p.GetNetname(), lid, p.GetEffectiveShape(lid), p.GetPosition(),
                            '%s.%s' % (f.GetReference(), p.GetNumber())))


def holds(a, e):
    return (e - a[3]).EuclideanNorm() <= a[2] if isinstance(a[2], int) else a[2].Collide(e, 0)


def touches(a, e, w):
    if isinstance(a[2], int):
        return (e - a[3]).EuclideanNorm() <= a[2] + w // 2
    return a[2].Collide(pcbnew.SHAPE_SEGMENT(e, e, w), 0)


for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        continue
    n, lid = t.GetNetname(), t.GetLayer()
    if OPEN is not None and n not in OPEN:
        continue
    mine = [a for a in anchors if a[0] == n and a[1] == lid]
    for e in (t.GetStart(), t.GetEnd()):
        if any(holds(a, e) for a in mine):
            continue            # the end lies in a pad or via: joined
        for a in mine:
            if touches(a, e, t.GetWidth()):
                c = a[3]
                edits.append(dict(op='track', net=n, layer=b.GetLayerName(lid), x0=round(MM(e.x), 4),
                                  y0=round(MM(e.y), 4), x1=round(MM(c.x), 4), y1=round(MM(c.y), 4),
                                  w=round(MM(t.GetWidth()), 3)))
                print('%s: track end (%.3f, %.3f) overlaps %s without lying in it -> link on %s' % (
                    n, MM(e.x), MM(e.y), a[4], b.GetLayerName(lid)))
                break
json.dump(edits, open(sys.argv[2], 'w'), indent=1)
print('%d links -> %s' % (len(edits), sys.argv[2]))
