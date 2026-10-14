"""Small grid router for a few new connections on a board COPY (KiCad's python.exe; pcbnew is only read).

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" route_new.py BOARD.kicad_pcb JOB.json OUT_SPEC.json

JOB.json:
  {"region": [x1, y1, x2, y2], "clearance": 0.2, "via": [0.5, 0.3], "via_cost": 1.5,
   "foreign_via_keepout": {"Net-(U2-In+)": 2.0, "Current": 2.0},      (the card's .kicad_dru via rules)
   "connections": [{"pad": ["R106", "1"], "net": "5V", "goal": "plane", "plane_layer": "In2.Cu", "width": 0.3},
                   {"pad": ["R106", "2"], "net": "SCL", "goal": "copper", "width": 0.2}, ...]}

Routes on the job's 'layers' (default F.Cu / B.Cu; never a GND-plane layer, so no GND plane is cut) with
an optional cost factor per layer ('layer_cost'); a layer change is a through via.
- goal "plane": the route ends on a via whose centre lies in that net's filled pour on plane_layer; "plane_or_copper": either.
- goal "copper": the route ends on existing copper of the net: on F/B a pad, a via or a track (a track reached in
  its middle is split there), or a via dropped onto the net's inner-layer track (that track is split at the via).
Obstacles: every other-net pad, track and via on the layer (grown by clearance + half width, + 0.04 grid margin),
the board edge (0.3 mm), rule-area keepouts, and for vias also every layer's other-net copper and every hole (hole to
hole 0.25 mm). Zone FILLS are not obstacles (they refill around the new copper). Connections are routed in order and
each result becomes an obstacle for the next. Writes a pcb_text_edit.py spec (add_segments / add_vias /
remove_segments for splits) and prints each route.
"""
import heapq, json, math, sys
import numpy as np
import pcbnew

G = 0.05
MARGIN = 0.04
OUTER = ('F.Cu', 'B.Cu')


def mm(v):
    return pcbnew.ToMM(v)


class Grid:
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.nx, self.ny = int(round((x2 - x1) / G)) + 1, int(round((y2 - y1) / G)) + 1
        self.X, self.Y = np.meshgrid(x1 + G * np.arange(self.nx), y1 + G * np.arange(self.ny))

    def empty(self):
        return np.zeros((self.ny, self.nx), bool)

    def disc(self, m, x, y, r):
        i0, i1 = max(0, int((y - r - self.y1) / G) - 1), min(self.ny, int((y + r - self.y1) / G) + 2)
        j0, j1 = max(0, int((x - r - self.x1) / G) - 1), min(self.nx, int((x + r - self.x1) / G) + 2)
        if i0 >= i1 or j0 >= j1:
            return
        X, Y = self.X[i0:i1, j0:j1], self.Y[i0:i1, j0:j1]
        m[i0:i1, j0:j1] |= (X - x) ** 2 + (Y - y) ** 2 <= r * r

    def capsule(self, m, xa, ya, xb, yb, r):
        i0 = max(0, int((min(ya, yb) - r - self.y1) / G) - 1)
        i1 = min(self.ny, int((max(ya, yb) + r - self.y1) / G) + 2)
        j0 = max(0, int((min(xa, xb) - r - self.x1) / G) - 1)
        j1 = min(self.nx, int((max(xa, xb) + r - self.x1) / G) + 2)
        if i0 >= i1 or j0 >= j1:
            return
        X, Y = self.X[i0:i1, j0:j1], self.Y[i0:i1, j0:j1]
        vx, vy = xb - xa, yb - ya
        L2 = vx * vx + vy * vy
        t = np.clip(((X - xa) * vx + (Y - ya) * vy) / L2, 0, 1) if L2 > 0 else 0
        m[i0:i1, j0:j1] |= (X - xa - t * vx) ** 2 + (Y - ya - t * vy) ** 2 <= r * r

    def poly(self, m, pts):
        P = np.array(pts)
        if len(P) < 3:
            return
        i0, i1 = max(0, int((P[:, 1].min() - self.y1) / G) - 1), min(self.ny, int((P[:, 1].max() - self.y1) / G) + 2)
        j0, j1 = max(0, int((P[:, 0].min() - self.x1) / G) - 1), min(self.nx, int((P[:, 0].max() - self.x1) / G) + 2)
        if i0 >= i1 or j0 >= j1:
            return
        X, Y = self.X[i0:i1, j0:j1], self.Y[i0:i1, j0:j1]
        ins = np.zeros(X.shape, bool)
        j = len(P) - 1
        for i in range(len(P)):
            xi, yi = P[i]
            xj, yj = P[j]
            ins ^= ((yi > Y) != (yj > Y)) & (X < (xj - xi) * (Y - yi) / (yj - yi + 1e-12) + xi)
            j = i
        m[i0:i1, j0:j1] |= ins

    def cell(self, x, y):
        return int(round((y - self.y1) / G)), int(round((x - self.x1) / G))

    def xy(self, i, j):
        return round(self.x1 + G * j, 4), round(self.y1 + G * i, 4)


def polys(ps):
    out = []
    for k in range(ps.OutlineCount()):
        o = ps.Outline(k)
        out.append([(mm(o.CPoint(n).x), mm(o.CPoint(n).y)) for n in range(o.PointCount())])
    return out


def main():
    board, jobp, outp = sys.argv[1:4]
    job = json.load(open(jobp))
    b = pcbnew.LoadBoard(board)
    g = Grid(*job['region'])
    clr = job.get('clearance', 0.2)
    RL = job.get('layers', list(OUTER))           # routing layers
    lcost = job.get('layer_cost', {})              # cost factor per mm on a layer (default 1)
    vdia, vdrill = job.get('via', [0.5, 0.3])
    vr = vdia / 2
    layers = {pcbnew.BOARD.GetLayerName(b, l): l for l in b.GetEnabledLayers().CuStack()}
    # ---- collect copper items: (kind, net, layer, geometry)
    items = []        # dict(net, layer, kind, ...)
    holes = []        # (x, y, r, net)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            c = p.GetPosition()
            if p.GetDrillSizeX() > 0:
                holes.append((mm(c.x), mm(c.y), mm(p.GetDrillSizeX()) / 2, p.GetNetname()))
            for ln, l in layers.items():
                if p.IsOnLayer(l) and p.FlashLayer(l):
                    items.append(dict(kind='pad', net=p.GetNetname(), layer=ln, obj=p, lid=l, x=mm(c.x), y=mm(c.y),
                                      ref=fp.GetReference(), num=p.GetNumber()))
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            c = t.GetPosition()
            holes.append((mm(c.x), mm(c.y), mm(t.GetDrillValue()) / 2, t.GetNetname()))
            for ln, l in layers.items():
                if t.IsOnLayer(l):
                    flashed = t.FlashLayer(l)
                    items.append(dict(kind='via', net=t.GetNetname(), layer=ln, x=mm(c.x), y=mm(c.y),
                                      r=(mm(t.GetWidth(l)) / 2 if flashed else mm(t.GetDrillValue()) / 2 + 0.05)))
        else:
            s, e = t.GetStart(), t.GetEnd()
            items.append(dict(kind='track', net=t.GetNetname(), layer=pcbnew.BOARD.GetLayerName(b, t.GetLayer()),
                              x0=mm(s.x), y0=mm(s.y), x1=mm(e.x), y1=mm(e.y), r=mm(t.GetWidth()) / 2))
    keep = g.empty()
    for z in b.Zones():
        if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
            for pts in polys(z.Outline()):
                g.poly(keep, pts)
    bb = b.GetBoardEdgesBoundingBox()
    ex1, ey1, ex2, ey2 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())

    def edge_mask(r):
        return (g.X < ex1 + r) | (g.X > ex2 - r) | (g.Y < ey1 + r) | (g.Y > ey2 - r)

    def block(item, m, grow):
        if item['kind'] == 'pad':
            ps = pcbnew.SHAPE_POLY_SET()
            item['obj'].TransformShapeToPolygon(ps, item['lid'], pcbnew.FromMM(grow), pcbnew.FromMM(0.005),
                                                pcbnew.ERROR_OUTSIDE)
            for pts in polys(ps):
                g.poly(m, pts)
        elif item['kind'] == 'via':
            g.disc(m, item['x'], item['y'], item['r'] + grow)
        else:
            g.capsule(m, item['x0'], item['y0'], item['x1'], item['y1'], item['r'] + grow)

    added_tracks, added_vias, splits = [], [], []
    for con in job['connections']:
        net, w = con['net'], con['width']
        if 'pad' in con:
            ref, num = con['pad']
            start = [i for i in items if i['kind'] == 'pad' and i['ref'] == ref and i['num'] == num]
            assert start, con['pad']
            assert start[0]['net'] == net, (con['pad'], start[0]['net'], net)
            slayer = start[0]['layer']
            sx, sy = start[0]['x'], start[0]['y']
        else:
            # re-route from an existing point of the net's copper (e.g. a through via): 'start_xy': [x, y, layer]
            sx, sy, slayer = con['start_xy']
            ref, num = 'point', '%g,%g' % (sx, sy)
            start = [dict(kind='via', net=net, layer=slayer, x=sx, y=sy, r=0.2)]
        # masks
        tblk = {ln: g.empty() for ln in RL}
        for it in items:
            if it['layer'] in RL and it['net'] != net:
                block(it, tblk[it['layer']], clr + w / 2 + MARGIN)
        for ln in RL:
            tblk[ln] |= keep | edge_mask(0.3 + w / 2 + MARGIN)
            for hx, hy, hr, hn in holes:      # hole clearance on every layer (unflashed via / pad layers too)
                if hn != net:
                    g.disc(tblk[ln], hx, hy, hr + 0.3 + w / 2 + MARGIN)
        vblk = keep | edge_mask(0.3 + vr + MARGIN)
        for it in items:
            if it['net'] != net:
                block(it, vblk, clr + vr + MARGIN)
        for hx, hy, hr, hn in holes:
            g.disc(vblk, hx, hy, hr + 0.25 + vdrill / 2 + MARGIN)
        for fnet, dist in job.get('foreign_via_keepout', {}).items():
            if fnet != net and net != 'GND':
                for it in items:
                    if it['net'] == fnet:
                        block(it, vblk, dist + vr + MARGIN)
        # goals
        goal = {ln: g.empty() for ln in RL}
        vgoal = g.empty()
        hit = {}                       # for track goals: cell -> track item (to split)
        if con['goal'] in ('plane', 'plane_or_copper'):
            pz = g.empty()
            for z in b.Zones():
                if z.GetNetname() == net and not z.GetIsRuleArea() and z.IsOnLayer(layers[con['plane_layer']]):
                    for pts in polys(z.GetFilledPolysList(layers[con['plane_layer']])):
                        g.poly(pz, pts)
            inner = g.empty()          # stay a via radius + clearance inside the pour
            pin = pz.copy()
            k = int(math.ceil((vr + clr) / G))
            for dy in range(-k, k + 1):
                for dx in range(-k, k + 1):
                    if dx * dx + dy * dy <= k * k:
                        inner |= ~np.roll(np.roll(pz, dy, 0), dx, 1)
            vgoal = pin & ~inner & ~vblk
        if con['goal'] == 'points':
            # explicit landing points of the net's existing copper (e.g. the far via of a removed span):
            # 'goal_xy': [[x, y], ...], reachable on any routing layer the copper there is on (a through via: all)
            for gx_, gy_ in con['goal_xy']:
                for ln in RL:
                    g.disc(goal[ln], gx_, gy_, 0.1)
        if con['goal'] in ('copper', 'plane_or_copper'):
            for it in items:
                if it['net'] != net:
                    continue
                if it['kind'] == 'pad' and (it['ref'], it['num']) == (ref, num):
                    continue
                if it['layer'] in RL:
                    m = g.empty()
                    if it['kind'] == 'track':
                        g.capsule(m, it['x0'], it['y0'], it['x1'], it['y1'], max(it['r'] - 0.05, 0.02))
                        for c in zip(*np.nonzero(m)):
                            hit.setdefault((it['layer'],) + tuple(c), it)
                    elif it['kind'] == 'via':
                        g.disc(m, it['x'], it['y'], max(it['r'] - 0.1, 0.05))
                    else:
                        block(it, m, -0.05)
                    goal[it['layer']] |= m
                elif it['kind'] == 'track':
                    m = g.empty()
                    g.capsule(m, it['x0'], it['y0'], it['x1'], it['y1'], 0.03)
                    m &= ~vblk
                    for c in zip(*np.nonzero(m)):
                        hit.setdefault(('via',) + tuple(c), it)
                    vgoal |= m
        # A* over (layer, i, j)
        L = {ln: k for k, ln in enumerate(RL)}
        si, sj = g.cell(sx, sy)
        gx = [np.argwhere(goal[ln]) for ln in RL] + [np.argwhere(vgoal)]
        allg = np.vstack([a for a in gx if len(a)]) if any(len(a) for a in gx) else None
        if allg is None:
            print('NO GOAL CELLS for', con)
            sys.exit(1)

        def h(i, j):
            if len(allg) > 3000:         # a large goal (a pour): plain Dijkstra
                return 0.0
            d = np.min(np.hypot(allg[:, 0] - i, allg[:, 1] - j))
            return d * G * min([1.0] + list(lcost.values()))

        hc = {}
        DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]   # 45-degree steps, in order
        tpen = job.get('turn_cost', 0.15)
        start_state = (L[slayer], si, sj, 8)       # direction 8 = none yet (start, or just after a via)
        openq = [(0.0, 0.0, start_state)]
        came, cost = {start_state: None}, {start_state: 0.0}
        own = g.empty()
        block(start[0], own, 0.0)
        end = None
        n = 0
        while openq:
            f, c0, s = heapq.heappop(openq)
            if c0 > cost.get(s, 1e18) + 1e-9:
                continue
            n += 1
            li, i, j, dprev = s
            ln = RL[li]
            if goal[ln][i, j] and s != start_state:
                end = (s, 'track')
                break
            if vgoal[i, j] and not vblk[i, j]:
                end = (s, 'via')
                break
            nbrs = []
            for dk, (di, dj) in enumerate(DIRS):
                ii, jj = i + di, j + dj
                if 0 <= ii < g.ny and 0 <= jj < g.nx and (not tblk[ln][ii, jj] or own[ii, jj] and li == L[slayer]):
                    turn = 0 if dprev == 8 else min((dk - dprev) % 8, (dprev - dk) % 8)
                    if turn > 2:                    # no turns sharper than 90 degrees
                        continue
                    sc = (1.4142 if di and dj else 1.0) * G * lcost.get(ln, 1.0) + turn * tpen
                    nbrs.append(((li, ii, jj, dk), sc))
            if not vblk[i, j]:
                for lj in range(len(RL)):
                    if lj != li:
                        nbrs.append(((lj, i, j, 8), job.get('via_cost', 1.5)))
            for ns, sc in nbrs:
                nc = c0 + sc
                if nc < cost.get(ns, 1e18):
                    cost[ns] = nc
                    came[ns] = s
                    key = ns[1:3]
                    if key not in hc:
                        hc[key] = h(*key)
                    heapq.heappush(openq, (nc + hc[key], nc, ns))
        if end is None:
            print('NO ROUTE for', con, 'after', n, 'states')
            np.savez_compressed(outp.replace('.json', '_fail.npz'), tF=tblk[RL[0]], tB=tblk[RL[-1]], v=vblk,
                                vgoal=vgoal, gF=goal[RL[0]], gB=goal[RL[-1]], x1=g.x1, y1=g.y1,
                                seen=np.array([k[:3] for k in cost]))
            sys.exit(1)
        path = []
        s = end[0]
        while s is not None:
            path.append(s)
            s = came[s]
        path.reverse()
        path = [q[:3] for q in path]
        # turn the cell path into segments and vias
        pts = []
        for k, (li, i, j) in enumerate(path):
            x, y = g.xy(i, j)
            if k == 0:
                x, y = round(sx, 4), round(sy, 4)
            pts.append((RL[li], x, y))
        segs, vias = [], []
        run = [pts[0]]
        for p in pts[1:]:
            if p[0] != run[-1][0]:
                vias.append((run[-1][1], run[-1][2]))
                if len(run) > 1:
                    segs.append(run)
                run = [p]
            else:
                run.append(p)
        if len(run) > 1:
            segs.append(run)
        if end[1] == 'via':
            vias.append((pts[-1][1], pts[-1][2]))
        def clear_line(ln, p, q):
            # every grid cell along p-q (sampled at G/2) is free on this layer
            n_ = max(2, int(math.hypot(q[1] - p[1], q[2] - p[2]) / (G / 2)) + 1)
            for k_ in range(n_ + 1):
                x_ = p[1] + (q[1] - p[1]) * k_ / n_
                y_ = p[2] + (q[2] - p[2]) * k_ / n_
                ii_, jj_ = g.cell(x_, y_)
                if tblk[ln][ii_, jj_] and not (own[ii_, jj_] and ln == slayer):
                    return False
            return True

        def octo(p, q):      # 0 / 45 / 90 degree lines only; a short (<= 0.5 mm) leg out of the start pad centre or
            dx_, dy_ = round(q[1] - p[1], 4), round(q[2] - p[2], 4)       # into the end point may take any angle
            return (dx_ == 0 or dy_ == 0 or abs(abs(dx_) - abs(dy_)) < 1e-6 or
                    ((p is pts[0] or q is pts[-1]) and math.hypot(dx_, dy_) <= 0.5))

        out_segs = []
        for r in segs:
            # string pulling: from each kept point jump to the farthest later point in clear line of sight
            ln = r[0][0]
            keep_pts, a = [r[0]], 0
            while a < len(r) - 1:
                bq = len(r) - 1
                while bq > a + 1 and not (octo(r[a], r[bq]) and clear_line(ln, r[a], r[bq])):
                    bq -= 1
                keep_pts.append(r[bq])
                a = bq
            out_segs.append(dict(net=net, layer=ln, width=w, pts=[[p[1], p[2]] for p in keep_pts]))
        if con['goal'] == 'points' and end[1] == 'track' and out_segs:
            # finish exactly on the named point (it lies within 0.1 mm of the last cell)
            lx_, ly_ = out_segs[-1]['pts'][-1]
            gp = min(con['goal_xy'], key=lambda q: math.hypot(q[0] - lx_, q[1] - ly_))
            if [round(gp[0], 4), round(gp[1], 4)] != [lx_, ly_]:
                out_segs[-1]['pts'][-1] = [round(gp[0], 4), round(gp[1], 4)]
        # split an existing track where the route lands in its middle
        li, i, j = end[0][:3]
        key = ('via', i, j) if end[1] == 'via' else (RL[li], i, j)
        if key in hit:
            t = hit[key]
            ex, ey = (vias[-1] if end[1] == 'via' else (out_segs[-1]['pts'][-1][0], out_segs[-1]['pts'][-1][1]))
            # move the junction onto the track centre line
            vx, vy = t['x1'] - t['x0'], t['y1'] - t['y0']
            L2 = vx * vx + vy * vy
            tt = min(max(((ex - t['x0']) * vx + (ey - t['y0']) * vy) / L2, 0), 1) if L2 else 0
            L_ = math.sqrt(L2)
            if tt * L_ < 0.1 or (1 - tt) * L_ < 0.1:     # next to an end: use the end itself (no split, no stub)
                tt = 0 if tt * L_ < (1 - tt) * L_ else 1
            jx, jy = round(t['x0'] + tt * vx, 4), round(t['y0'] + tt * vy, 4)
            if end[1] == 'via':
                vias[-1] = (jx, jy)
                if out_segs and out_segs[-1]['pts'][-1] == [ex, ey]:
                    out_segs[-1]['pts'][-1] = [jx, jy]
            else:
                out_segs[-1]['pts'][-1] = [jx, jy]
            if 0 < tt < 1:
                splits.append(dict(remove=dict(net=t['net'], layer=t['layer'], seg=[t['x0'], t['y0'], t['x1'], t['y1']]),
                                   add=[dict(net=t['net'], layer=t['layer'], width=round(2 * t['r'], 4),
                                             pts=[[t['x0'], t['y0']], [jx, jy]]),
                                        dict(net=t['net'], layer=t['layer'], width=round(2 * t['r'], 4),
                                             pts=[[jx, jy], [t['x1'], t['y1']]])]))
        print('%s %s.%s -> %s: %d states; %s; vias %s' % (net, ref, num, end[1], n, '; '.join(
            '%s %s' % (s_['layer'], ' '.join('(%g, %g)' % tuple(p) for p in s_['pts'])) for s_ in out_segs), vias))
        added_tracks += out_segs
        added_vias += [dict(net=net, x=x, y=y, size=vdia, drill=vdrill) for x, y in vias]
        # the new copper becomes part of the board for the next connections
        for s_ in out_segs:
            for p, q in zip(s_['pts'], s_['pts'][1:]):
                items.append(dict(kind='track', net=net, layer=s_['layer'], x0=p[0], y0=p[1], x1=q[0], y1=q[1], r=w / 2))
        for x, y in vias:
            holes.append((x, y, vdrill / 2, net))
            for ln in layers:
                items.append(dict(kind='via', net=net, layer=ln, x=x, y=y, r=vr))
    spec = dict(_why=job.get('_why', 'route_new.py'), add_segments=added_tracks, add_vias=added_vias)
    if splits:
        spec['remove_segments'] = [s_['remove'] for s_ in splits]
        spec['add_segments'] = added_tracks + [a for s_ in splits for a in s_['add']]
        spec['expect'] = {'remove_segments': len(splits)}
    json.dump(spec, open(outp, 'w'), indent=1)
    print('wrote', outp)


if __name__ == '__main__':
    main()
