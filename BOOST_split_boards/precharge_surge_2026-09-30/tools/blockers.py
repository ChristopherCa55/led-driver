"""For one site and package, list the placements blocked by the fewest board items, and name those items
(KiCad 10 Python, read-only). Same rules as fit_search.py, but pads may also connect through a short new track.

usage: python.exe blockers.py BOARD.kicad_pcb PKG REF [SPAN]
"""
import sys, math
import pcbnew
exec(open(__file__.replace('blockers.py', 'fit_search.py')).read().split('for ref in refs:')[0])
board = pcbnew.LoadBoard(sys.argv[1])
pkg, ref = sys.argv[2], sys.argv[3]
SPAN = float(sys.argv[4]) if len(sys.argv) > 4 else 4
PL, PW, PO, CHL, CHW, BHL, BHW = LANDS[pkg]
BL = pcbnew.B_Cu
vout = VOUT[ref]
old = board.FindFootprintByReference(ref)
ox, oy = MM(old.GetPosition().x), MM(old.GetPosition().y)
edges = pcbnew.SHAPE_POLY_SET()
board.GetBoardPolygonOutlines(edges, False)
W = rect(ox, oy, SPAN + 4, SPAN + 4, 0)
items = []   # (label, grown polygon)
for t in board.GetTracks():
    net = t.GetNetname()
    if net in (vout, 'Vin'):
        continue
    if t.GetClass() != 'PCB_VIA' and t.GetLayer() != BL:
        continue
    sh = pcbnew.SHAPE_POLY_SET()
    t.TransformShapeToPolygon(sh, BL, 0, FM(0.005), pcbnew.ERROR_INSIDE)
    g = grown(sh, max(CLR_PWR, MM(t.GetOwnClearance(BL))))
    if inter(g, W) < 1e-6:
        continue
    if t.GetClass() == 'PCB_VIA':
        lab = 'via %s (%.2f, %.2f) %.2f/%.2f' % (net, MM(t.GetPosition().x), MM(t.GetPosition().y),
                                                 MM(t.GetWidth(pcbnew.F_Cu)), MM(t.GetDrillValue()))
    else:
        lab = 'track %s (%.2f, %.2f)-(%.2f, %.2f) w%.2f' % (net, MM(t.GetStart().x), MM(t.GetStart().y),
                                                          MM(t.GetEnd().x), MM(t.GetEnd().y), MM(t.GetWidth()))
    items.append((lab, g))
for f in board.GetFootprints():
    if f.GetReference() == ref:
        continue
    for p in f.Pads():
        if not p.IsOnLayer(BL) or p.GetNetname() in (vout, 'Vin'):
            continue
        sh = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(sh, BL, 0, FM(0.005), pcbnew.ERROR_INSIDE)
        g = grown(sh, max(CLR_PWR, MM(p.GetOwnClearance(BL))))
        if inter(g, W) > 1e-6:
            items.append(('pad %s.%s %s' % (f.GetReference(), p.GetNumber(), p.GetNetname()), g))
    if f.IsFlipped():
        c = f.GetCourtyard(pcbnew.B_CrtYd)
        if c.OutlineCount() and inter(c, W) > 1e-6:
            items.append(('courtyard %s' % f.GetReference(), pcbnew.SHAPE_POLY_SET(c)))
for f in board.GetFootprints():
    if 'MountingHole_4.3mm_M4' in f.GetFPIDAsString() and f.GetReference().startswith('J'):
        circ = pcbnew.SHAPE_POLY_SET()
        circ.NewOutline()
        jx, jy = MM(f.GetPosition().x), MM(f.GetPosition().y)
        for q in range(72):
            circ.Append(FM(jx + 4.6 * math.cos(q * math.pi / 36)), FM(jy + 4.6 * math.sin(q * math.pi / 36)))
        if inter(circ, W) > 1e-6:
            items.append(('courtyard %s nut+washer r4.6' % f.GetReference(), circ))
for z in board.Zones():
    if not z.IsOnLayer(BL):
        continue
    if z.GetIsRuleArea():
        if z.GetDoNotAllowFootprints() or z.GetDoNotAllowPads():
            items.append(('rule area %s' % z.GetZoneName(), pcbnew.SHAPE_POLY_SET(z.Outline())))
        continue
    if z.GetNetname() in ('GND', vout, 'Vin'):
        continue
    g = grown(z.GetFilledPolysList(BL), CLR_PWR)
    g.BooleanIntersection(W)
    if area(g) > 1e-6:
        items.append(('zone %s "%s"' % (z.GetNetname(), z.GetZoneName()), g))
edge_in = pcbnew.SHAPE_POLY_SET(edges)
edge_in.Deflate(FM(EDGE_CLR), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.005))
for ps in (edge_in, edges):
    ps.BooleanIntersection(W)
print('%d items near %s' % (len(items), ref))
res = []
STEP = 0.1
n = int(SPAN / STEP)
for ang in (0, 90, 180, 270, 45, 135, 225, 315):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            cx, cy = round(ox + i * STEP, 3), round(oy + j * STEP, 3)
            k = rect(cx - PO * c, cy - PO * s, PL / 2, PW / 2, ang)
            a = rect(cx + PO * c, cy + PO * s, PL / 2, PW / 2, ang)
            cyd = rect(cx, cy, CHL, CHW, ang)
            if inter(k, edge_in) < area(k) - 1e-4 or inter(a, edge_in) < area(a) - 1e-4:
                continue
            if inter(cyd, edges) < area(cyd) - 1e-4:
                continue
            hit = []
            for lab, g in items:
                if lab.startswith('courtyard') or lab.startswith('rule'):
                    if inter(cyd, g) > 1e-5:
                        hit.append(lab)
                elif inter(k, g) > 1e-5 or inter(a, g) > 1e-5:
                    hit.append(lab)
                if len(hit) > 3:
                    break
            if len(hit) <= 3:
                res.append((len(hit), math.hypot(cx - ox, cy - oy), cx, cy, ang, hit))
res.sort(key=lambda r: (r[0], r[1]))
seen = set()
for r in res:
    key = tuple(r[5])
    if key in seen:
        continue
    seen.add(key)
    print('%d blockers  centre (%.2f, %.2f) rot %3d  %.1f mm from old: %s' % (r[0], r[2], r[3], r[4], r[1], '; '.join(r[5])))
    if len(seen) >= 15:
        break
