"""Route one connection on a finished board with KiCad's exact geometry (KiCad Python): the finishing tool for the few
connections the grid routers leave open (user, 2026-09-24: "finish them yourself with picked corridors and scripted
copper").

usage: python.exe exact_route.py BOARD.kicad_pcb NET REF.PAD REF.PAD X0,Y0,X1,Y1 LAYERS WIDTH OUT.json [--step S]
       LAYERS: comma list of copper layers the track may use (vias join them); WIDTH in mm; the search stays in the box.

Every item of another net is inflated by the larger of the two netclass clearances (Power 0.25, else 0.20) plus half
the track width (or the via radius for via sites) and rasterised at STEP (default 0.025 mm) by cell centre, with a
0.02 mm allowance for that; vias and pads count only on the layers where they are flashed (unused rings removed). A new
via needs its ring's clearance on the two layers it joins and 0.2 mm copper-to-hole everywhere else, 0.25 mm hole to
hole. Also blocked: 0.3 mm to the board edge and to non-plated holes; the rule areas. The card's sensitive-net rules (user 2026-09-22 / 09-24):
  - no via of another net within 2 mm of U2 In+ or Current copper (GND exempt), none within 0.3 mm of V_err copper;
  - Current: no other copper within 2 mm on B.Cu, In4 and In5 (measured from its B.Cu copper);
  - U2 In+: no other copper within 2 mm of its In4 run on In3 and In4 (2026-09-30 copy for the In4-plane card: the
    run moved up from In5 to In4, In3 over it is the local GND shield, In5 the solid plane; route without In5);
  - logic nets: 2 mm from U2 In+ and V_err copper on F.Cu and B.Cu.
The shortest path (via = 1.6 mm) from pad A's copper to pad B's copper is written as route_card.py routes JSON
(tracks and vias, keep False), to be merged into the board's routes and checked with KiCad DRC.
"""
import heapq, json, math, sys
import numpy as np
import pcbnew


class Path:
    """Even-odd point-in-polygon test in numpy (KiCad's Python has no matplotlib)."""
    def __init__(self, pts):
        self.p = np.asarray(pts, float)

    def contains_points(self, q):
        x, y = q[:, 0], q[:, 1]
        inside = np.zeros(len(q), bool)
        xa, ya = self.p[:, 0], self.p[:, 1]
        xb, yb = np.roll(xa, -1), np.roll(ya, -1)
        for x0, y0, x1, y1 in zip(xa, ya, xb, yb):
            if y0 == y1:
                continue
            c = ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0) + x0)
            inside ^= c
        return inside

sys.path.insert(0, 'tools')
from card_nets import is_logic

args = [x for x in sys.argv[1:] if not x.startswith('--')]
STEP = float(sys.argv[sys.argv.index('--step') + 1]) if '--step' in sys.argv else 0.025
if '--step' in sys.argv:
    args = [x for x in args if x != sys.argv[sys.argv.index('--step') + 1]]
BOARD, NET, PA, PB, BOX, LAYS, WIDTH, OUT = args[:8]
X0, Y0, X1, Y1 = map(float, BOX.split(','))
LAYS = LAYS.split(',')
W = float(WIDTH)
FM, MM = pcbnew.FromMM, pcbnew.ToMM
ALLOW = 0.02
VIA_D, VIA_H = 0.5, 0.3
POWER = {'GND', 'Vout_1', 'Vout_2', 'Vout_3', 'Output1_drain', 'Output2_drain', 'Output3_drain'}
clr = lambda n: 0.25 if n in POWER else 0.20

b = pcbnew.LoadBoard(BOARD)
b.BuildConnectivity()
LID = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
NXg = int(round((X1 - X0) / STEP)) + 1
NYg = int(round((Y1 - Y0) / STEP)) + 1
gx = X0 + np.arange(NXg) * STEP
gy = Y0 + np.arange(NYg) * STEP
GX, GY = np.meshgrid(gx, gy)
PTS = np.column_stack([GX.ravel(), GY.ravel()])


def poly_mask(ps):
    """Cells whose centre lies inside the polygon set (outlines minus holes)."""
    m = np.zeros(NXg * NYg, bool)
    for i in range(ps.OutlineCount()):
        ch = ps.Outline(i)
        pts = np.array([(MM(ch.CPoint(k).x), MM(ch.CPoint(k).y)) for k in range(ch.PointCount())])
        if len(pts) < 3:
            continue
        lo, hi = pts.min(0), pts.max(0)
        if hi[0] < X0 or lo[0] > X1 or hi[1] < Y0 or lo[1] > Y1:
            continue
        sel = (PTS[:, 0] >= lo[0]) & (PTS[:, 0] <= hi[0]) & (PTS[:, 1] >= lo[1]) & (PTS[:, 1] <= hi[1])
        if not sel.any():
            continue
        inside = Path(pts).contains_points(PTS[sel])
        for h in range(ps.HoleCount(i)):
            hc = ps.Hole(i, h)
            hp = np.array([(MM(hc.CPoint(k).x), MM(hc.CPoint(k).y)) for k in range(hc.PointCount())])
            if len(hp) >= 3:
                inside &= ~Path(hp).contains_points(PTS[sel])
        m[np.where(sel)[0][inside]] = True
    return m.reshape(NYg, NXg)


def grow(item, layer, d):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, FM(d), FM(0.005), pcbnew.ERROR_OUTSIDE)
    return ps


def near_box(item, d):
    bb = item.GetBoundingBox()
    return not (MM(bb.GetRight()) + d < X0 or MM(bb.GetLeft()) - d > X1 or MM(bb.GetBottom()) + d < Y0 or
                MM(bb.GetTop()) - d > Y1)


tracks = list(b.GetTracks())
pads = [(p, f) for f in b.GetFootprints() for p in f.Pads()]
# --escape REF.PAD:R (2026-09-30): this net has a pin on a sensitive net's own part (0A_hi on U2). As route_card.py's
# exemption, its track may run inside the 2 mm logic keep-out of U2 In+ / V_err on F.Cu / B.Cu within R mm of that pad
# (to escape it); vias keep the full 2 mm, and the In3 / In4 band over the In+ run stays closed.
ESCAPE = None
if '--escape' in sys.argv:
    _ref, _r = sys.argv[sys.argv.index('--escape') + 1].split(':')
    for _p, _f in pads:
        if '%s.%s' % (_f.GetReference(), _p.GetNumber()) == _ref:
            _x, _y = MM(_p.GetPosition().x), MM(_p.GetPosition().y)
            ESCAPE = (GX - _x) ** 2 + (GY - _y) ** 2 <= float(_r) ** 2
logic = is_logic(NET)
SOFT = '--soft' in sys.argv
# --soft: tracks and vias of other signal nets may be crossed at a cost; the path then names the nets in the way, to
# be ripped and re-routed by route_card.py. Pads, GND, 5V, analog_5V and the sensitive nets stay hard.
HARD_NETS = {'GND', '5V', 'analog_5V', 'Current', 'Net-(U2-In+)', 'V_err'}
track_block = {l: np.zeros((NYg, NXg), bool) for l in LAYS}
via_block = np.zeros((NYg, NXg), bool)
ring_block = {ln: np.zeros((NYg, NXg), bool) for ln in LID}
track_soft = {l: np.zeros((NYg, NXg), bool) for l in LAYS}
via_soft = np.zeros((NYg, NXg), bool)
ring_soft = {ln: np.zeros((NYg, NXg), bool) for ln in LID}
soft_items = []
vr = VIA_D / 2
for it in tracks + [p for p, f in pads]:
    n = it.GetNetname()
    c = max(clr(n), clr(NET))
    reach = 2.6
    if not near_box(it, reach):
        continue
    is_via = it.GetClass() == 'PCB_VIA'
    soft = SOFT and it.GetClass() != 'PAD' and n not in HARD_NETS and n != NET
    tb, vb, rb = (track_soft, via_soft, ring_soft) if soft else (track_block, via_block, ring_block)
    if soft:
        soft_items.append(it)
    for ln, lid in LID.items():
        if not it.IsOnLayer(lid):
            continue
        if (is_via or it.GetClass() == 'PAD') and not it.FlashLayer(lid):
            continue            # its unused ring is removed there: only the hole counts (below)
        if n != NET:
            if ln in tb:
                tb[ln] |= poly_mask(grow(it, lid, c + W / 2 + ALLOW))
            # a new via has its ring only on the two layers it joins (unused rings removed, as KiCad checks it):
            # the ring's clearance on those layers, the hole's 0.2 mm on every layer
            rb[ln] |= poly_mask(grow(it, lid, c + vr + ALLOW))
            vb |= poly_mask(grow(it, lid, 0.2 + VIA_H / 2 + ALLOW))
    # holes: vias and through-hole pads keep 0.2 mm copper-to-hole and 0.25 mm hole-to-hole from the new via
    if is_via or (it.GetClass() == 'PAD' and it.GetDrillSize().x > 0):
        hs = it.GetEffectiveHoleShape()
        ps = pcbnew.SHAPE_POLY_SET()
        hs.TransformToPolygon(ps, FM(0.005), pcbnew.ERROR_OUTSIDE)
        npth = it.GetClass() == 'PAD' and it.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
        g = pcbnew.SHAPE_POLY_SET(ps)
        g.Inflate(FM((0.3 if npth else 0.25) + VIA_H / 2 + ALLOW), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.005))
        vb |= poly_mask(g)
        g2 = pcbnew.SHAPE_POLY_SET(ps)
        g2.Inflate(FM((0.3 if npth else 0.2) + W / 2 + ALLOW), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.005))
        m2 = poly_mask(g2)
        for ln in tb:
            tb[ln] |= m2 if (n != NET or npth) else False
    # the sensitive-net rules
    if n in ('Net-(U2-In+)', 'Current') and n != NET and NET != 'GND':
        for ln, lid in LID.items():
            if it.IsOnLayer(lid):
                via_block |= poly_mask(grow(it, lid, 2.0 + vr + ALLOW))
    if n == 'V_err' and NET != 'V_err':
        for ln, lid in LID.items():
            if it.IsOnLayer(lid):
                via_block |= poly_mask(grow(it, lid, (2.0 if logic else 0.3) + vr + ALLOW))
    if n == 'Current' and NET != 'Current' and it.IsOnLayer(LID['B.Cu']):
        for ln in ('B.Cu', 'In4.Cu', 'In5.Cu'):
            if ln in track_block:
                m = poly_mask(grow(it, LID['B.Cu'], 2.0 + W / 2 + ALLOW))
                if ESCAPE is not None and ln == 'B.Cu':
                    m &= ~ESCAPE        # --escape: a pin net of U5 / U2 leaving its pad (the 8-layer card had Reset_raw at 1.63 mm)
                track_block[ln] |= m
    if n == 'Net-(U2-In+)' and NET != n and it.IsOnLayer(LID['In4.Cu']) and not is_via:
        for ln in ('In3.Cu', 'In4.Cu', 'In5.Cu'):
            if ln in track_block:
                track_block[ln] |= poly_mask(grow(it, LID['In4.Cu'], 2.0 + W / 2 + ALLOW))
    if n == 'Net-(U2-In+)' and NET != n and is_via and it.IsOnLayer(LID['In4.Cu']):
        for ln in ('In3.Cu', 'In4.Cu', 'In5.Cu'):          # its vias' barrels count as part of the run (conservative)
            if ln in track_block:
                track_block[ln] |= poly_mask(grow(it, LID['In4.Cu'], 2.0 + W / 2 + ALLOW))
    if logic and n in ('Net-(U2-In+)', 'V_err'):
        for ln in ('F.Cu', 'B.Cu'):
            if ln in track_block and it.IsOnLayer(LID[ln]):
                m = poly_mask(grow(it, LID[ln], 2.0 + W / 2 + ALLOW))
                if ESCAPE is not None:
                    m &= ~ESCAPE        # --escape: a pin of this net on the sensitive net's part (route_card.py's exemption)
                track_block[ln] |= m
# board edge and rule areas
bb = b.GetBoardEdgesBoundingBox()
ex0, ey0, ex1, ey1 = MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())
edge_t = (GX < ex0 + 0.3 + W / 2 + ALLOW) | (GX > ex1 - 0.3 - W / 2 - ALLOW) | (GY < ey0 + 0.3 + W / 2 + ALLOW) | \
         (GY > ey1 - 0.3 - W / 2 - ALLOW)
edge_v = (GX < ex0 + 0.3 + vr + ALLOW) | (GX > ex1 - 0.3 - vr - ALLOW) | (GY < ey0 + 0.3 + vr + ALLOW) | \
         (GY > ey1 - 0.3 - vr - ALLOW)
for ln in track_block:
    track_block[ln] |= edge_t
via_block |= edge_v
for z in b.Zones():
    if z.GetIsRuleArea():
        g = pcbnew.SHAPE_POLY_SET(z.Outline())
        g.Inflate(FM(vr + ALLOW), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FM(0.005))
        m = poly_mask(g)
        via_block |= m
        for ln in track_block:
            track_block[ln] |= m


class ViaEnd:
    """An end at an existing via of the net ('via@X,Y'): its barrel serves every layer."""
    def __init__(self, x, y):
        self.x, self.y = x, y


def pad_by_name(s):
    if s.startswith('via@'):
        x, y = map(float, s[4:].split(','))
        return ViaEnd(x, y)
    ref, num = s.split('.')
    for p, f in pads:
        if f.GetReference() == ref and p.GetNumber() == num:
            return p
    sys.exit('no pad ' + s)


def pad_cells(p):
    out = {}
    if isinstance(p, ViaEnd):
        disc = (GX - p.x) ** 2 + (GY - p.y) ** 2 <= (VIA_D / 2 - 0.05) ** 2
        return {ln: disc for ln in LAYS} if disc.any() else {}
    for ln in LAYS:
        if p.IsOnLayer(LID[ln]) and p.FlashLayer(LID[ln]):
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, LID[ln], FM(-W / 2 * 0.0), FM(0.005), pcbnew.ERROR_INSIDE)
            m = poly_mask(ps)
            if m.any():
                out[ln] = m
    return out


A = pad_cells(pad_by_name(PA))
if PB == 'any':
    # any copper of the net outside the start pad's own fill piece: its tracks, vias, pads and zone fills
    pa = pad_by_name(PA)
    B = {}
    own_piece = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != NET:
            continue
        for ln in LAYS:
            if not z.IsOnLayer(LID[ln]) or not z.HasFilledPolysForLayer(LID[ln]):
                continue
            ps = z.GetFilledPolysList(LID[ln])
            for i in range(ps.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET()
                one.AddOutline(ps.Outline(i))
                for h in range(ps.HoleCount(i)):
                    one.AddHole(ps.Hole(i, h))
                m = poly_mask(one)
                if not isinstance(pa, ViaEnd) and pa.IsOnLayer(LID[ln]) and one.Collide(pa.GetPosition(), 0):
                    own_piece[ln] = m
                    continue
                B.setdefault(ln, np.zeros((NYg, NXg), bool))
                B[ln] |= m
    # the net's vias (GND vias reach the planes) and its pads and tracks outside the start's piece
    for it in tracks + [p for p, f in pads]:
        if it.GetNetname() != NET or it is pa or not near_box(it, 0.5):
            continue
        for ln in LAYS:
            lid = LID[ln]
            if not it.IsOnLayer(lid):
                continue
            if it.GetClass() == 'PCB_VIA' or (it.GetClass() == 'PAD' and it.FlashLayer(lid)) or                     it.GetClass() == 'PCB_TRACK':
                m = poly_mask(grow(it, lid, -0.01)) if it.GetClass() != 'PCB_VIA' else                     ((GX - MM(it.GetPosition().x)) ** 2 + (GY - MM(it.GetPosition().y)) ** 2 <= (VIA_D / 2 - 0.05) ** 2)
                if ln in own_piece:
                    m = m & ~own_piece[ln]
                B.setdefault(ln, np.zeros((NYg, NXg), bool))
                B[ln] |= m
else:
    B = pad_cells(pad_by_name(PB))
if not A or not B:
    sys.exit('a pad has no copper on the allowed layers inside the box')
L = len(LAYS)
free = np.stack([~track_block[ln] for ln in LAYS])
for k, ln in enumerate(LAYS):         # the pads themselves are free to start and end in
    for M in (A, B):
        if ln in M:
            free[k] |= M[ln]
vok = ~via_block
ringok = [~ring_block[ln] for ln in LAYS]
if NET == 'GND':
    # KiCad rings a GND via on every layer a GND fill reaches it: the ring's clearance on all of them (not In3,
    # the 5 V pour, where it stays a hole)
    allring = np.ones((NYg, NXg), bool)
    for ln in LID:
        if ln != 'In3.Cu':
            allring &= ~ring_block[ln]
    vok = vok & allring
SOFT_PEN = 40.0          # crossing another net's movable copper: 40x the length
SOFT_VIA = 4.0           # a via site that needs another net's copper moved: +4 mm
tsoft = np.stack([track_soft[ln] for ln in LAYS])
vsoft = via_soft.copy()
rsoft = [ring_soft[ln] for ln in LAYS]
print('grid %d x %d; start cells %s; goal cells %s; free %% by layer %s; via sites %d' % (
    NXg, NYg, {k: int(v.sum()) for k, v in A.items()}, {k: int(v.sum()) for k, v in B.items()},
    {ln: round(100 * free[k].mean(), 1) for k, ln in enumerate(LAYS)}, int(vok.sum())))
import os as _os
if _os.environ.get('XR_DUMP'):
    np.savez(_os.environ['XR_DUMP'], free=free, vok=vok, gx=gx, gy=gy, lays=np.array(LAYS),
             A=np.stack([A.get(ln, np.zeros((NYg, NXg), bool)) for ln in LAYS]))
INF = 1e18
dist = np.full((L, NYg, NXg), INF)
prev = {}
pq = []
for k, ln in enumerate(LAYS):
    if ln in A:
        for j, i in zip(*np.where(A[ln] & free[k])):
            dist[k, j, i] = 0.0
            heapq.heappush(pq, (0.0, k, j, i))
goal = None
VIA_COST = 1.6
moves = [(0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142),
         (-1, -1, 1.4142)]
while pq:
    d, k, j, i = heapq.heappop(pq)
    if d > dist[k, j, i]:
        continue
    if LAYS[k] in B and B[LAYS[k]][j, i]:
        goal = (k, j, i)
        break
    for dj, di, c in moves:
        jj, ii = j + dj, i + di
        if 0 <= jj < NYg and 0 <= ii < NXg and free[k, jj, ii]:
            nd = d + c * STEP * (SOFT_PEN if tsoft[k, jj, ii] else 1.0)
            if nd < dist[k, jj, ii]:
                dist[k, jj, ii] = nd
                prev[(k, jj, ii)] = (k, j, i)
                heapq.heappush(pq, (nd, k, jj, ii))
    if vok[j, i] and ringok[k][j, i]:
        for kk in range(L):
            if kk != k and free[kk, j, i] and ringok[kk][j, i]:
                nd = d + VIA_COST + (SOFT_VIA if (vsoft[j, i] or rsoft[k][j, i] or rsoft[kk][j, i]) else 0.0)
                if nd < dist[kk, j, i]:
                    dist[kk, j, i] = nd
                    prev[(kk, j, i)] = (k, j, i)
                    heapq.heappush(pq, (nd, kk, j, i))
if goal is None:
    print('NO PATH for %s %s -> %s in box %s on %s at width %.2f' % (NET, PA, PB, BOX, ','.join(LAYS), W))
    sys.exit(1)
path = [goal]
while path[-1] in prev:
    path.append(prev[path[-1]])
path.reverse()
out = dict(tracks=[], vias=[])
seg = [path[0]]
for a_, b_ in zip(path, path[1:]):
    if a_[0] != b_[0]:
        # layer change: close the run, drop a via
        if len(seg) > 1:
            out['tracks'].append(seg)
        out['vias'].append((a_[1], a_[2], LAYS[a_[0]], LAYS[b_[0]]))
        seg = [b_]
    else:
        seg.append(b_)
if len(seg) > 1:
    out['tracks'].append(seg)


def xy(j, i):
    return round(float(gx[i]), 4), round(float(gy[j]), 4)


res = dict(tracks=[], vias=[], log=['exact_route %s %s -> %s' % (NET, PA, PB)], failures=[])
def clear_line(k, a, c):
    """The straight run from cell a to cell c on layer k stays in free cells (sampled every half cell)."""
    (ja, ia), (jc, ic) = a, c
    n = int(max(abs(jc - ja), abs(ic - ia)) * 2) + 1
    for t in np.linspace(0.0, 1.0, n + 1):
        j = int(round(ja + (jc - ja) * t))
        i = int(round(ia + (ic - ia) * t))
        if not free[k, j, i]:
            return False
    return True


for s in out['tracks']:
    # line of sight: from each kept point, jump to the farthest later point reachable in a straight free line
    k = s[0][0]
    pts = [s[0]]
    a = 0
    while a < len(s) - 1:
        c = len(s) - 1
        while c > a + 1 and not clear_line(k, s[a][1:], s[c][1:]):
            c -= 1
        pts.append(s[c])
        a = c
    for p, q in zip(pts, pts[1:]):
        x0, y0 = xy(p[1], p[2])
        x1, y1 = xy(q[1], q[2])
        res['tracks'].append(dict(net=NET, layer=LAYS[p[0]], w=W, x0=x0, y0=y0, x1=x1, y1=y1, keep=False))
for j, i, la, lb in out['vias']:
    x, y = xy(j, i)
    res['vias'].append(dict(net=NET, x=x, y=y, dia=VIA_D, drill=VIA_H, layers=[la, lb], keep=False))
# --soft: the other nets whose copper the new route needs moved (KiCad collision tests with the netclass clearances)
conflicts = {}
if SOFT:
    newsh = []
    for t in res['tracks']:
        newsh.append((t['layer'], pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(FM(t['x0']), FM(t['y0'])),
                                                       pcbnew.VECTOR2I(FM(t['x1']), FM(t['y1'])), FM(W)), 'track'))
    for v in res['vias']:
        c_ = pcbnew.VECTOR2I(FM(v['x']), FM(v['y']))
        for ln in v['layers']:
            newsh.append((ln, pcbnew.SHAPE_CIRCLE(c_, FM(vr)), 'ring'))
        for ln in LID:
            newsh.append((ln, pcbnew.SHAPE_CIRCLE(c_, FM(VIA_H / 2)), 'hole'))
    for it in soft_items:
        n = it.GetNetname()
        c = max(clr(n), clr(NET))
        is_via = it.GetClass() == 'PCB_VIA'
        for ln, sh, kind in newsh:
            lid = LID[ln]
            if not it.IsOnLayer(lid):
                continue
            flashed = not is_via or it.FlashLayer(lid)
            if flashed:
                other = it.GetEffectiveShape(lid)
                if other.Collide(sh, FM(0.2 if kind == 'hole' else c)):
                    conflicts.setdefault(n, set()).add(ln)
                    break
            if is_via and kind in ('hole', 'ring', 'track'):
                hs = it.GetEffectiveHoleShape()
                if hs.Collide(sh, FM(0.25 if kind == 'hole' else 0.2)):
                    conflicts.setdefault(n, set()).add(ln)
                    break
    res['conflicts'] = {n: sorted(v) for n, v in conflicts.items()}
    print('nets to move: %s' % ', '.join('%s (%s)' % (n, '/'.join(sorted(v))) for n, v in conflicts.items()))
json.dump(res, open(OUT, 'w'), indent=1)
L_mm = sum(math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']) for t in res['tracks'])
print('%s %s -> %s: %d segments, %.1f mm, %d vias (%s) -> %s' % (
    NET, PA, PB, len(res['tracks']), L_mm, len(res['vias']),
    ', '.join('%.2f,%.2f %s>%s' % (v['x'], v['y'], v['layers'][0], v['layers'][1]) for v in res['vias']), OUT))
