"""Fabrication facts for the fab drawing and the order, measured from a board file (KiCad Python).

usage: python.exe fab_facts.py BOARD.kicad_pcb OUT.json

Outline, holes (vias by drill and diameter, plated pad holes, non-plated holes and slots), the narrowest track on
outer and inner layers, via-in-pad counts (a via whose drill overlaps a pad's copper on F.Cu or B.Cu: those vias need
filling and capping so solder does not wick into them), annular rings, and the hole-to-hole distances JLCPCB limits
(via to via 0.2 mm; via-in-pad to a plated or non-plated pad hole more than 0.45 mm, edge to edge).
"""
import collections, json, math, sys
import pcbnew

MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
res = {'board': sys.argv[1].replace('\\', '/').split('/')[-1]}

bb = b.GetBoardEdgesBoundingBox()
res['outline_bbox_mm'] = [round(MM(bb.GetX()), 3), round(MM(bb.GetY()), 3), round(MM(bb.GetRight()), 3),
                          round(MM(bb.GetBottom()), 3)]
res['size_mm'] = [round(MM(bb.GetWidth()), 3), round(MM(bb.GetHeight()), 3)]
outline = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(outline, False)
res['outline_area_mm2'] = round(outline.Area() / 1e12, 1)
res['outline_vertices'] = [[(round(MM(outline.Outline(i).CPoint(k).x), 3), round(MM(outline.Outline(i).CPoint(k).y), 3))
                            for k in range(outline.Outline(i).PointCount())] for i in range(outline.OutlineCount())]
res['copper_layers'] = b.GetCopperLayerCount()
res['board_thickness_in_file_mm'] = round(MM(b.GetDesignSettings().GetBoardThickness()), 3)

vias, holes = [], []
tw = collections.defaultdict(lambda: 1e9)
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        vias.append((MM(t.GetPosition().x), MM(t.GetPosition().y), MM(t.GetDrill()), MM(t.GetWidth(pcbnew.F_Cu)),
                     t.GetNetname(), t))
    else:
        L = b.GetLayerName(t.GetLayer())
        tw[L] = min(tw[L], MM(t.GetWidth()))
res['min_track_by_layer_mm'] = {k: round(v, 3) for k, v in sorted(tw.items())}
outer = [v for k, v in tw.items() if k in ('F.Cu', 'B.Cu')]
inner = [v for k, v in tw.items() if k not in ('F.Cu', 'B.Cu')]
res['min_track_outer_mm'] = round(min(outer), 3) if outer else None
res['min_track_inner_mm'] = round(min(inner), 3) if inner else None
res['via_count'] = len(vias)
res['vias_by_drill_dia'] = {'%.2f/%.2f' % (d, w): n for (d, w), n in
                            sorted(collections.Counter((round(v[2], 3), round(v[3], 3)) for v in vias).items())}
res['via_min_annular_mm'] = round(min((v[3] - v[2]) / 2 for v in vias), 3) if vias else None

pth, npth, slots = collections.Counter(), collections.Counter(), []
pad_holes = []
min_ring_pth = 1e9
for f in b.GetFootprints():
    for p in f.Pads():
        if not p.HasHole():
            continue
        ds = p.GetDrillSize()
        dx, dy = MM(ds.x), MM(ds.y)
        pos = p.GetPosition()
        rec = (MM(pos.x), MM(pos.y), dx, dy, f.GetReference(), p.GetNumber(), p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH)
        pad_holes.append(rec)
        if abs(dx - dy) > 1e-6:
            slots.append({'ref': f.GetReference(), 'pad': p.GetNumber(), 'plated': not rec[6],
                          'size_mm': [round(dx, 3), round(dy, 3)], 'at': [round(rec[0], 3), round(rec[1], 3)],
                          'angle': round(p.GetOrientationDegrees(), 1)})
        elif rec[6]:
            npth[round(dx, 3)] += 1
        else:
            pth[round(dx, 3)] += 1
            sz = p.GetSize(pcbnew.F_Cu)
            min_ring_pth = min(min_ring_pth, (min(MM(sz.x), MM(sz.y)) - dx) / 2)
res['pth_by_drill'] = {'%.2f' % k: n for k, n in sorted(pth.items())}
res['npth_by_drill'] = {'%.2f' % k: n for k, n in sorted(npth.items())}
res['slots'] = slots
res['pth_min_annular_mm'] = round(min_ring_pth, 3) if pth else None
all_drills = [v[2] for v in vias] + [min(h[2], h[3]) for h in pad_holes]
res['min_drill_mm'] = round(min(all_drills), 3)
res['min_plated_drill_mm'] = round(min([v[2] for v in vias] + [min(h[2], h[3]) for h in pad_holes if not h[6]]), 3)
res['max_via_drill_mm'] = round(max(v[2] for v in vias), 3) if vias else None

# via-in-pad: the via's drill overlaps a pad's copper on an outer layer
pads_out = []
for f in b.GetFootprints():
    for p in f.Pads():
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(L) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                pads_out.append((p, L, f.GetReference()))
vip = []
for x, y, d, w, net, v in vias:
    hole = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), pcbnew.FromMM(d / 2))
    hit = [(r, b.GetLayerName(L)) for p, L, r in pads_out if p.GetEffectiveShape(L).Collide(hole, 0)]
    if hit:
        vip.append((x, y, d, net, sorted(set(hit))))
res['via_in_pad_count'] = len(vip)
res['via_in_pad_by_drill'] = {'%.2f' % k: n for k, n in sorted(collections.Counter(round(v[2], 3) for v in vip).items())}
res['via_in_pad_by_side'] = dict(collections.Counter(
    '+'.join(sorted(set(L for _, L in v[4]))) for v in vip))


def edge_gap(a, ra, c, rc):
    return math.hypot(a[0] - c[0], a[1] - c[1]) - ra - rc


# hole-to-hole: via to via, and via-in-pad to non-via holes (slots approximated by their short radius at the centre)
xy = [(v[0], v[1], v[2] / 2) for v in vias]
mvv = 1e9
cell = collections.defaultdict(list)
for i, (x, y, r) in enumerate(xy):
    cell[(int(x // 2), int(y // 2))].append(i)
for i, (x, y, r) in enumerate(xy):
    cx, cy = int(x // 2), int(y // 2)
    for gx in (cx - 1, cx, cx + 1):
        for gy in (cy - 1, cy, cy + 1):
            for j in cell[(gx, gy)]:
                if j > i:
                    mvv = min(mvv, edge_gap((x, y), r, xy[j][:2], xy[j][2]))
res['min_via_to_via_hole_gap_mm'] = round(mvv, 3) if len(xy) > 1 else None
vip_set = set((round(v[0], 4), round(v[1], 4)) for v in vip)
mvp, mvp_at = 1e9, None
mvp_any = 1e9
for x, y, r in xy:
    for h in pad_holes:
        g = edge_gap((x, y), r, h[:2], min(h[2], h[3]) / 2)
        if g < mvp_any:
            mvp_any = g
        if (round(x, 4), round(y, 4)) in vip_set and g < mvp:
            mvp, mvp_at = g, (round(x, 3), round(y, 3), h[4], h[5], 'NPTH' if h[6] else 'PTH')
res['min_via_to_pad_hole_gap_mm'] = round(mvp_any, 3)
res['min_via_in_pad_to_pad_hole_gap_mm'] = round(mvp, 3) if vip else None
res['min_via_in_pad_to_pad_hole_at'] = mvp_at
json.dump(res, open(sys.argv[2], 'w'), indent=1)
for k, v in res.items():
    if k != 'outline_vertices':
        print('%-36s %s' % (k, v))
