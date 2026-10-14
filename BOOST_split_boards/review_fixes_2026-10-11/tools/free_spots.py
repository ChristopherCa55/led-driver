"""Where does a small SMD part fit on a board side? (KiCad's python.exe, read-only use of pcbnew on the given file.)

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" free_spots.py BOARD.kicad_pcb SIDE x1 y1 x2 y2 OUT.png
                 [--w 3.0 --h 1.5] [--clr 0.25] [--near NET[,NET]]

SIDE = F or B. Blocked: rule areas that forbid footprints, courtyards of that side's footprints (their polygons), that side's pads, tracks and graphic
copper (each grown by --clr), every via (both sides, grown by --clr), and 0.5 mm from the
board edge. Zones are NOT obstacles (their fill moves aside). A spot is free when a W x H rectangle (the new part's
courtyard; tried at 0 and 90 degrees) fits there. Writes OUT.png (free centres in green, nets named by --near in
blue) and prints the free centres closest to the --near nets' copper on that side and to their pads / vias.
"""
import math, sys
import numpy as np
import pcbnew

G = 0.05


def main():
    a = sys.argv[1:]
    path, side = a[0], a[1]
    x1, y1, x2, y2 = map(float, a[2:6])
    out = a[6]
    W = float(a[a.index('--w') + 1]) if '--w' in a else 3.0
    H = float(a[a.index('--h') + 1]) if '--h' in a else 1.5
    clr = float(a[a.index('--clr') + 1]) if '--clr' in a else 0.25
    near = a[a.index('--near') + 1].split(',') if '--near' in a else []
    b = pcbnew.LoadBoard(path)
    cu = pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu
    cy = pcbnew.F_CrtYd if side == 'F' else pcbnew.B_CrtYd
    nx, ny = int((x2 - x1) / G) + 1, int((y2 - y1) / G) + 1
    X, Y = np.meshgrid(x1 + G * np.arange(nx), y1 + G * np.arange(ny))
    blk = np.zeros(X.shape, bool)
    netmask = np.zeros(X.shape, bool)
    mm = pcbnew.ToMM

    def poly_fill(pts, mask):
        # even-odd ray cast over the grid
        P = np.array(pts)
        ins = np.zeros(X.shape, bool)
        j = len(P) - 1
        for i in range(len(P)):
            xi, yi = P[i]
            xj, yj = P[j]
            c = ((yi > Y) != (yj > Y)) & (X < (xj - xi) * (Y - yi) / (yj - yi + 1e-12) + xi)
            ins ^= c
            j = i
        mask |= ins

    def grow(mask, r):
        k = int(math.ceil(r / G))
        if k <= 0:
            return mask
        out_ = mask.copy()
        for dy in range(-k, k + 1):
            for dx in range(-k, k + 1):
                if dx * dx + dy * dy <= k * k:
                    out_ |= np.roll(np.roll(mask, dy, 0), dx, 1)
        return out_

    def seg(xa, ya, xb, yb, r, mask):
        vx, vy = xb - xa, yb - ya
        L2 = vx * vx + vy * vy
        t = np.clip(((X - xa) * vx + (Y - ya) * vy) / L2, 0, 1) if L2 > 0 else 0
        mask |= (X - xa - t * vx) ** 2 + (Y - ya - t * vy) ** 2 <= r * r

    def polyset_pts(ps):
        res = []
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            res.append([(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())])
        return res

    crt = np.zeros(X.shape, bool)
    padm = np.zeros(X.shape, bool)
    for fp in b.GetFootprints():
        fp.BuildCourtyardCaches()
        for pts in polyset_pts(fp.GetCourtyard(cy)):
            poly_fill(pts, crt)
        for p in fp.Pads():
            if p.IsOnLayer(cu) or p.GetDrillSizeX() > 0:
                ps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(ps, cu if p.IsOnLayer(cu) else pcbnew.F_Cu, 0, pcbnew.FromMM(0.01),
                                          pcbnew.ERROR_INSIDE)
                m = np.zeros(X.shape, bool)
                for pts in polyset_pts(ps):
                    poly_fill(pts, m)
                padm |= m
                if p.GetNetname() in near and p.IsOnLayer(cu):
                    netmask |= m
    blk |= crt | grow(padm, clr)
    trk = np.zeros(X.shape, bool)
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            c = t.GetPosition()
            r = mm(t.GetWidth(pcbnew.F_Cu)) / 2
            m = np.zeros(X.shape, bool)
            seg(mm(c.x), mm(c.y), mm(c.x), mm(c.y), r + clr, m)
            blk |= m
            if t.GetNetname() in near:
                seg(mm(c.x), mm(c.y), mm(c.x), mm(c.y), r, netmask)
        elif t.GetLayer() == cu:
            s, e = t.GetStart(), t.GetEnd()
            seg(mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(t.GetWidth()) / 2 + clr, trk)
            if t.GetNetname() in near:
                seg(mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(t.GetWidth()) / 2, netmask)
    blk |= trk
    # rule areas that forbid footprints (the washer / screw-head circles at H1-H4) block the whole area
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowFootprints() and z.IsOnLayer(cu):
            m = np.zeros(X.shape, bool)
            for pts in polyset_pts(z.Outline()):
                poly_fill(pts, m)
            blk |= m
    bb = b.GetBoardEdgesBoundingBox()
    ex1, ey1, ex2, ey2 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
    blk |= (X < ex1 + 0.5) | (X > ex2 - 0.5) | (Y < ey1 + 0.5) | (Y > ey2 - 0.5)
    # free centres: the W x H box around the centre is all unblocked (box filter via integral image)
    I = np.pad(blk.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    free = {}
    for ang, (w, h) in ((0, (W, H)), (90, (H, W))):
        hw, hh = int(round(w / 2 / G)), int(round(h / 2 / G))
        f = np.zeros(X.shape, bool)
        r0, r1 = hh, ny - hh - 1
        c0, c1 = hw, nx - hw - 1
        if r1 > r0 and c1 > c0:
            rr, cc = np.mgrid[r0:r1, c0:c1]
            s = (I[rr + hh + 1, cc + hw + 1] - I[rr - hh, cc + hw + 1] - I[rr + hh + 1, cc - hw] + I[rr - hh, cc - hw])
            f[r0:r1, c0:c1] = s == 0
        free[ang] = f
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        img = np.ones(X.shape + (3,))
        img[blk] = (0.75, 0.75, 0.75)
        img[netmask] = (0.2, 0.3, 1.0)
        img[free[0]] = (0.1, 0.7, 0.1)
        img[free[90] & ~free[0]] = (0.6, 0.9, 0.2)
        fig = plt.figure(figsize=(nx / 60, ny / 60), dpi=100)
        plt.imshow(img, extent=(x1, x2, y2, y1), interpolation='nearest')
        plt.grid(True, lw=0.3)
        plt.xticks(np.arange(math.ceil(x1), x2, 1))
        plt.yticks(np.arange(math.ceil(y1), y2, 1))
        plt.tick_params(labelsize=5)
        plt.title('%s side: free centres for a %.1f x %.1f part (dark green 0 deg, light green 90 deg only)' % (
            side, W, H), fontsize=7)
        fig.savefig(out, dpi=150, bbox_inches='tight')
        print('wrote', out)
    except ImportError:
        np.savez_compressed(out.replace('.png', '.npz'), blk=blk, free0=free[0], free90=free[90], net=netmask)
        print('no matplotlib here: wrote', out.replace('.png', '.npz'))
    if near and netmask.any():
        ny_, nx_ = np.nonzero(netmask)
        for ang in (0, 90):
            fy, fx = np.nonzero(free[ang])
            if not len(fx):
                continue
            d = np.full(len(fx), 1e9)
            for k in range(0, len(nx_), 50):
                dd = np.hypot(X[fy, fx][:, None] - X[ny_[k:k + 50], nx_[k:k + 50]][None, :],
                              Y[fy, fx][:, None] - Y[ny_[k:k + 50], nx_[k:k + 50]][None, :]).min(1)
                d = np.minimum(d, dd)
            order = np.argsort(d)[:8]
            for o in order:
                print('  %3d deg centre (%.2f, %.2f): %.2f mm from %s copper on %s.Cu' % (
                    ang, X[fy[o], fx[o]], Y[fy[o], fx[o]], d[o], '/'.join(near), side))


if __name__ == '__main__':
    main()
