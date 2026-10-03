"""Search where a bigger diode land fits at the D28/D29/D30 sites (KiCad 10 Python, read-only on the board).

usage: python.exe fit_search.py BOARD.kicad_pcb PKG [REF ...]
PKG: SMAF | SMBF | SMB  (pads from the data sheets / KiCad D_SMB; see LANDS)

For each candidate centre (0.05 mm grid in a window round the old diode) and rotation, with the old diode removed:
  - each pad, grown by the clearance it needs (Power 0.25 mm, or the other item's if larger), must not touch any
    other-net B.Cu copper: tracks, vias, pads, and zone fills of nets other than GND. GND zone fill may be cut
    (it refills), GND tracks / vias / pads may not;
  - pads at least 0.3 mm from the board edge; the body and courtyard inside the board outline;
  - courtyard clear of every other B-side courtyard and of B.Cu rule areas;
  - pad 1 (K) must touch the old diode's Vout_n copper and pad 2 (A) its Vin copper as they are now (tracks, vias or
    own-net zone fill on B.Cu), so no track has to be added or moved ("no reroute").
Prints the feasible placements, best first (largest spare clearance), and how much GND fill each cuts.
"""
import sys, math
import pcbnew

MM, FM = pcbnew.ToMM, pcbnew.FromMM
# (pad axial length, pad transverse width, pad centre offset, courtyard half-length, courtyard half-width,
#  body half-length incl. leads, body half-width)
LANDS = {
    # the present part, as a check that the search accepts today's placement
    'SOD123F': (1.1, 1.1, 1.4, 2.245, 1.195, 1.9, 0.95),
    # SMAF, Jingdao/Shikues/WildGoose recommended land: pads 1.6 x 1.8, 2.2 gap; body E max 2.7, HE max 4.9
    'SMAF': (1.6, 1.8, 1.9, 2.95, 1.6, 2.45, 1.35),
    # SMBF, Shikues S5MBF land: pads 1.8 x 2.54, 3.0 gap; body E max 3.7, HE max 5.5
    'SMBF': (1.8, 2.54, 2.4, 3.55, 2.1, 2.75, 1.85),
    # SMB, KiCad Diode_SMD:D_SMB: pads 2.5 x 2.3 at +/-2.15; courtyard 7.39 x 4.59; body J max 3.94, G max 5.59
    'SMB': (2.5, 2.3, 2.15, 3.695, 2.295, 2.8, 1.97),
}
board = pcbnew.LoadBoard(sys.argv[1])
pkg = sys.argv[2]
refs = sys.argv[3:] or ['D28', 'D29', 'D30']
PL, PW, PO, CHL, CHW, BHL, BHW = LANDS[pkg]
BL = pcbnew.B_Cu
CLR_PWR = 0.25
EDGE_CLR = 0.3
import os
GRID = float(os.environ.get('GRID', '0.1'))
STEPS = int(float(os.environ.get('SPAN', '3')) / GRID)
VOUT = {'D28': 'Vout_1', 'D29': 'Vout_2', 'D30': 'Vout_3'}

edges = pcbnew.SHAPE_POLY_SET()
board.GetBoardPolygonOutlines(edges, False)


def rect(cx, cy, hx, hy, ang):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
        ps.Append(FM(cx + dx * c - dy * s), FM(cy + dx * s + dy * c))
    return ps


def area(ps):
    return ps.Area() / 1e12


def inter(a, b):
    r = pcbnew.SHAPE_POLY_SET(a)
    r.BooleanIntersection(b)
    return area(r)


def grown(ps, d):
    r = pcbnew.SHAPE_POLY_SET(ps)
    r.Inflate(FM(d), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.005))
    return r


for ref in refs:
    old = board.FindFootprintByReference(ref)
    vout = VOUT[ref]
    ox, oy = MM(old.GetPosition().x), MM(old.GetPosition().y)
    # obstacles per clearance class, as polygon sets, collected within 8 mm
    win = (ox - 8, oy - 8, ox + 8, oy + 8)

    def near(x, y, r=0):
        return win[0] - r <= x <= win[2] + r and win[1] - r <= y <= win[3] + r

    obst = pcbnew.SHAPE_POLY_SET()      # other-net copper, already grown by (its clearance vs ours) - see below
    own = {vout: pcbnew.SHAPE_POLY_SET(), 'Vin': pcbnew.SHAPE_POLY_SET()}
    gndfill = pcbnew.SHAPE_POLY_SET()
    for t in board.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
            if not near(x, y, 2):
                continue
            sh = pcbnew.SHAPE_POLY_SET()
            t.TransformShapeToPolygon(sh, BL, 0, FM(0.005), pcbnew.ERROR_INSIDE)
        else:
            if t.GetLayer() != BL:
                continue
            s, e = t.GetStart(), t.GetEnd()
            if not (near(MM(s.x), MM(s.y), 3) or near(MM(e.x), MM(e.y), 3)):
                continue
            sh = pcbnew.SHAPE_POLY_SET()
            t.TransformShapeToPolygon(sh, BL, 0, FM(0.005), pcbnew.ERROR_INSIDE)
        if net in own:
            own[net].BooleanAdd(sh)
        else:
            obst.BooleanAdd(grown(sh, max(CLR_PWR, MM(t.GetOwnClearance(BL)))))
    for f in board.GetFootprints():
        if f.GetReference() == ref:
            continue
        for p in f.Pads():
            if not p.IsOnLayer(BL):
                continue
            x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
            if not near(x, y, 4):
                continue
            sh = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(sh, BL, 0, FM(0.005), pcbnew.ERROR_INSIDE)
            if p.GetNetname() in own:
                own[p.GetNetname()].BooleanAdd(sh)
            else:
                obst.BooleanAdd(grown(sh, max(CLR_PWR, MM(p.GetOwnClearance(BL)))))
            if p.GetDrillSize().x > 0:   # hole clearance 0.2 to any hole (also own-net THT holes)
                pass
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(BL):
            continue
        fill = z.GetFilledPolysList(BL)
        net = z.GetNetname()
        if net == 'GND':
            gndfill.BooleanAdd(fill)
        elif net in own:
            own[net].BooleanAdd(fill)
        else:
            obst.BooleanAdd(grown(fill, CLR_PWR))
    # courtyards of other B-side footprints and B.Cu rule areas
    crt = pcbnew.SHAPE_POLY_SET()
    for f in board.GetFootprints():
        if f.GetReference() == ref or not f.IsFlipped():
            continue
        c = f.GetCourtyard(pcbnew.B_CrtYd)
        if c.OutlineCount():
            crt.BooleanAdd(c)
    # M4 bolt terminals (J1-J8): nut + DIN 125 washer on the underside; courtyards stay > 4.6 mm from the centre
    for f in board.GetFootprints():
        if 'MountingHole_4.3mm_M4' in f.GetFPIDAsString() and f.GetReference().startswith('J'):
            circ = pcbnew.SHAPE_POLY_SET()
            circ.NewOutline()
            jx, jy = MM(f.GetPosition().x), MM(f.GetPosition().y)
            for q in range(72):
                circ.Append(FM(jx + 4.6 * math.cos(q * math.pi / 36)), FM(jy + 4.6 * math.sin(q * math.pi / 36)))
            crt.BooleanAdd(circ)
    rules = pcbnew.SHAPE_POLY_SET()
    for z in board.Zones():
        if z.GetIsRuleArea() and z.IsOnLayer(BL) and (z.GetDoNotAllowFootprints() or z.GetDoNotAllowPads()):
            rules.BooleanAdd(z.Outline())
    edge_in = pcbnew.SHAPE_POLY_SET(edges)
    edge_in.Deflate(FM(EDGE_CLR), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.005))
    W = rect(ox, oy, 8, 8, 0)
    ed = pcbnew.SHAPE_POLY_SET(edges)
    for ps in (obst, own[vout], own['Vin'], gndfill, crt, rules, edge_in, ed):
        ps.BooleanIntersection(W)
    edges_w = ed

    res = []
    for ang in (0, 90, 180, 270, 45, 135, 225, 315):
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for i in range(-STEPS, STEPS + 1):
            for j in range(-STEPS, STEPS + 1):
                cx, cy = round(ox + i * GRID, 3), round(oy + j * GRID, 3)
                # pad 1 (K) at local -PO, pad 2 (A) at +PO
                k = rect(cx - PO * c, cy - PO * s, PL / 2, PW / 2, ang)
                a = rect(cx + PO * c, cy + PO * s, PL / 2, PW / 2, ang)
                body = rect(cx, cy, BHL, BHW, ang)
                cy_ = rect(cx, cy, CHL, CHW, ang)
                # inside the board
                if inter(k, edge_in) < area(k) - 1e-4 or inter(a, edge_in) < area(a) - 1e-4:
                    continue
                if inter(body, edges_w) < area(body) - 1e-4:
                    continue
                if inter(k, obst) > 1e-5 or inter(a, obst) > 1e-5:
                    continue
                if inter(cy_, crt) > 1e-5 or inter(cy_, rules) > 1e-5:
                    continue
                # each pad must already touch its own net's copper
                tk, ta = inter(k, own[vout]), inter(a, own['Vin'])
                if tk < 0.05 or ta < 0.05:
                    continue
                # pads must not touch the other own-net copper (K on Vin or A on Vout)
                if inter(k, own['Vin']) > 1e-5 or inter(a, own[vout]) > 1e-5:
                    continue
                # spare: how far each pad could still grow before hitting an obstacle (coarse: 0.05 steps)
                spare = 0
                for d in (0.05, 0.1, 0.15, 0.2, 0.3):
                    if inter(grown(k, d), obst) > 1e-5 or inter(grown(a, d), obst) > 1e-5:
                        break
                    spare = d
                cut = inter(grown(k, CLR_PWR), gndfill) + inter(grown(a, CLR_PWR), gndfill)
                res.append((spare, -cut, -math.hypot(cx - ox, cy - oy), cx, cy, ang, tk, ta, cut))
    res.sort(reverse=True)
    print('%s %s: %d feasible placements (old centre %.2f, %.2f)' % (ref, pkg, len(res), ox, oy))
    for r in res[:int(os.environ.get("TOP", "12"))]:
        print('   centre (%.2f, %.2f) rot %3d  spare >= %.2f mm  K/A overlap on own copper %.2f / %.2f mm2  '
              'GND fill cut %.2f mm2' % (r[3], r[4], r[5], r[0], r[6], r[7], r[8]))
