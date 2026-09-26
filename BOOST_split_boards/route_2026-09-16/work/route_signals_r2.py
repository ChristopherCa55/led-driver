"""Grid router for the BOOST power board signals (system Python: numpy, scipy, matplotlib).

usage: python route_signals.py COPPER.json OUT_ROUTES.json [--nets a,b,...] [--skip a,b] [--report REPORT.txt]

Reads the copper export of a board whose power copper is fixed (export_copper.py), finds each net's copper
islands (layers joined through its own barrels), joins them with a minimum spanning tree, and routes every tree
edge on a 0.1 mm grid over F.Cu, In2, In3, In5 and B.Cu (In1/In6 are GND only, In4 is the 5 V plane) with
Dijkstra. Obstacles are other nets' pads, vias, tracks and non-yielding zone fills grown by
track half-width + clearance + margin, other nets' holes grown by the 0.2 mm hole clearance, keep-outs and the
board edge (0.3 mm). GND fill (zone priority <= 1) yields and is refilled afterwards. Vias must clear copper on
all eight layers and every hole by 0.25 mm. The 5 V net may land on the In4 plane, GND on In1/In6.
Output: tracks and vias, added to the board by add_routes.py.
"""
import json, math, sys, time
import numpy as np
from scipy import ndimage
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
from matplotlib.path import Path
from PIL import Image, ImageDraw

H = 0.1
X0, Y0 = 29.0, 29.0
NX, NY = 770, 890
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu', 'B.Cu']
LI = {n: i for i, n in enumerate(LAYERS)}
ROUTE = [0, 2, 3, 5, 7]
MARGIN = 0.06
HOLE_CLR = 0.20
HOLE_HOLE = 0.25
EDGE_CLR = 0.30
VIA_COST = 1.6            # mm-equivalent per via
LAYER_COST = {0: 1.0, 2: 1.25, 3: 1.25, 5: 1.1, 7: 1.0}

CLASS = {  # clearance from the project netclasses; widths chosen for these nets (DRU minimums respected)
    'Default': dict(clr=0.15, w=0.20, via=(0.6, 0.3)),
    'Sense': dict(clr=0.20, w=0.20, via=(0.6, 0.3)),
    'Gate': dict(clr=0.20, w=0.40, via=(0.6, 0.3)),
    'Rail': dict(clr=0.20, w=0.50, via=(0.6, 0.3)),
    'Power': dict(clr=0.25, w=0.50, via=(0.8, 0.4)),
}
HIGH_CURRENT = {'Vin', 'rsense_lo', 'LX', 'm2_source', 'm3_source', 'm4_source', 'Vout_1', 'Vout_2', 'Vout_3',
                'Output1_drain', 'Output2_drain', 'Output3_drain', 'Net-(M8-S)', 'Net-(M9-S)', 'Net-(M10-S)'}
QUIET = {'ISNS_P', 'ISNS_N', 'SNS_CH1', 'SNS_CH2', 'SNS_CH3', 'IREF1_input', 'IREF2_input', 'IREF3_input',
         'Current', 'analog_5V'}
PLANE_TARGET = {'5V': [4], 'GND': [1, 6]}
PAIRS = {'ISNS_N': 'ISNS_P'}
POUR_MULT_DRIVE = 3.0     # gate-drive nets may cut through a non-LX power pour at this cost multiplier
POUR_MULT_OTHER = 6.0


def pour_mult(net):
    if net.startswith(('GATE_', 'Net-(D', 'Net-(U19-OUT', 'Net-(U11-OUT', 'Net-(U12-OUT', 'Net-(U6-OUT'))             or net.endswith(('-VDDA)', '-G)')) or net in ('m2_source', 'm3_source', 'm4_source'):
        return POUR_MULT_DRIVE
    return POUR_MULT_OTHER


def cls_of(net, classes):
    c = classes.get(net, 'Default').split(',')[0]
    return c if c in CLASS else 'Default'


def rules_for(net, classes):
    c = dict(CLASS[cls_of(net, classes)])
    if net in HIGH_CURRENT:
        c['w'] = 1.0
        c['via'] = (0.8, 0.4)
    return c


def cell(x, y):
    return int(round((x - X0) / H - 0.5)), int(round((y - Y0) / H - 0.5))


def raster_poly(pts, into, val):
    # PIL polygon fill in cell units (cell k spans [k, k+1)); fills cells the outline passes through
    pts = np.asarray(pts, float)
    if len(pts) < 3:
        return
    i0 = max(int((pts[:, 0].min() - X0) / H) - 1, 0)
    i1 = min(int((pts[:, 0].max() - X0) / H) + 2, NX)
    j0 = max(int((pts[:, 1].min() - Y0) / H) - 1, 0)
    j1 = min(int((pts[:, 1].max() - Y0) / H) + 2, NY)
    if i1 <= i0 or j1 <= j0:
        return
    img = Image.new('1', (i1 - i0, j1 - j0), 0)
    xy = [((x - X0) / H - i0 - 0.5, (y - Y0) / H - j0 - 0.5) for x, y in pts]
    ImageDraw.Draw(img).polygon(xy, fill=1, outline=None)
    m = np.array(img, dtype=bool)
    into[j0:j1, i0:i1][m] = val


def raster_disc(x, y, r, into, val):
    i0 = max(int((x - r - X0) / H) - 1, 0)
    i1 = min(int((x + r - X0) / H) + 2, NX)
    j0 = max(int((y - r - Y0) / H) - 1, 0)
    j1 = min(int((y + r - Y0) / H) + 2, NY)
    xs = X0 + (np.arange(i0, i1) + 0.5) * H
    ys = Y0 + (np.arange(j0, j1) + 0.5) * H
    Xg, Yg = np.meshgrid(xs, ys)
    m = (Xg - x) ** 2 + (Yg - y) ** 2 <= r * r
    into[j0:j1, i0:i1][m] = val


def raster_seg(x0, y0, x1, y1, r, into, val):
    i0 = max(int((min(x0, x1) - r - X0) / H) - 1, 0)
    i1 = min(int((max(x0, x1) + r - X0) / H) + 2, NX)
    j0 = max(int((min(y0, y1) - r - Y0) / H) - 1, 0)
    j1 = min(int((max(y0, y1) + r - Y0) / H) + 2, NY)
    xs = X0 + (np.arange(i0, i1) + 0.5) * H
    ys = Y0 + (np.arange(j0, j1) + 0.5) * H
    Xg, Yg = np.meshgrid(xs, ys)
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = np.zeros_like(Xg) if L2 == 0 else np.clip(((Xg - x0) * dx + (Yg - y0) * dy) / L2, 0, 1)
    d2 = (Xg - (x0 + t * dx)) ** 2 + (Yg - (y0 + t * dy)) ** 2
    into[j0:j1, i0:i1][d2 <= r * r] = val


class Board:
    def __init__(self, cop):
        self.cop = cop
        self.classes = cop.get('classes', {})
        names = set(cop['nets']) | {p['net'] for p in cop['pads']}
        self.nid = {n: i for i, n in enumerate(sorted(names))}
        self.nname = {i: n for n, i in self.nid.items()}
        self.hard = [np.full((NY, NX), -1, np.int32) for _ in LAYERS]
        self.clr = [np.zeros((NY, NX), np.float32) for _ in LAYERS]
        self.yld = [np.full((NY, NX), -1, np.int32) for _ in LAYERS]
        self.zonehard = [np.zeros((NY, NX), bool) for _ in LAYERS]
        self.holes = np.full((NY, NX), -1, np.int32)
        self.keep_tracks = np.zeros((NY, NX), bool)
        self.keep_vias = np.zeros((NY, NX), bool)
        self.barrels = []           # (x, y, net id, [layers])
        tmp = np.zeros((NY, NX), bool)
        for z in cop['zones']:
            l = LI[z['layer']]
            n = self.nid[z['net']]
            if z['prio'] <= 1:
                for poly in z['polys']:
                    if not isinstance(poly, dict):
                        raster_poly(poly, self.yld[l], n)
            else:
                c = max(z['clearance'], rules_for(z['net'], self.classes)['clr'])
                for poly in z['polys']:
                    if not isinstance(poly, dict):
                        tmp[:] = False
                        raster_poly(poly, tmp, True)
                        self.hard[l][tmp] = n
                        self.clr[l][tmp] = c
                        self.zonehard[l][tmp] = True
        for p in cop['pads']:
            n = self.nid[p['net']]
            c = rules_for(p['net'], self.classes)['clr']
            for ln, polys in p['polys'].items():
                l = LI[ln]
                for poly in polys:
                    if not isinstance(poly, dict):
                        tmp[:] = False
                        raster_poly(poly, tmp, True)
                        self.hard[l][tmp] = n
                        self.clr[l][tmp] = c
                        self.zonehard[l][tmp] = False
        for v in cop['vias']:
            n = self.nid[v['net']]
            c = rules_for(v['net'], self.classes)['clr']
            for ln in v['layers']:
                tmp[:] = False
                raster_disc(v['x'], v['y'], v['dia'] / 2, tmp, True)
                self.hard[LI[ln]][tmp] = n
                self.clr[LI[ln]][tmp] = c
            raster_disc(v['x'], v['y'], v['drill'] / 2, self.holes, n)
        for b in cop['barrels']:
            n = self.nid[b['net']]
            if b['kind'] == 'tht':
                raster_disc(b['x'], b['y'], b['drill'] / 2, self.holes, n)
            self.barrels.append((b['x'], b['y'], n, [LI[l] for l in b['layers']]))
        for t in cop.get('tracks', []):
            n = self.nid[t['net']]
            c = rules_for(t['net'], self.classes)['clr']
            tmp[:] = False
            raster_seg(t['x0'], t['y0'], t['x1'], t['y1'], t['w'] / 2, tmp, True)
            self.hard[LI[t['layer']]][tmp] = n
            self.clr[LI[t['layer']]][tmp] = c
        for k in cop['keepouts']:
            tmp[:] = False
            raster_poly(k['pts'], tmp, True)
            if k['no_tracks']:
                self.keep_tracks |= tmp
            if k['no_vias']:
                self.keep_vias |= tmp
        # board outline: polygon from the edge segments (simple closed outline)
        segs = [tuple(map(tuple, (e[:2], e[2:]))) for e in cop['edge']]
        pts = [segs[0][0], segs[0][1]]
        used = {0}
        while len(used) < len(segs):
            for k, (a, b) in enumerate(segs):
                if k in used:
                    continue
                if np.hypot(a[0] - pts[-1][0], a[1] - pts[-1][1]) < 1e-3:
                    pts.append(b); used.add(k); break
                if np.hypot(b[0] - pts[-1][0], b[1] - pts[-1][1]) < 1e-3:
                    pts.append(a); used.add(k); break
            else:
                break
        inside = np.zeros((NY, NX), bool)
        raster_poly(pts, inside, True)
        self.edge_dist = ndimage.distance_transform_edt(inside) * H - H / 2
        self.lx_proj = ndimage.binary_dilation(self.hard[2] == self.nid.get('LX', -99), iterations=10)
        self.routes = []            # committed geometry

    # ------------------------------------------------------------------ islands
    def own_mask(self, n, l):
        return (self.hard[l] == n) | (self.yld[l] == n)

    def islands(self, n):
        labels, offs, total = {}, {}, 0
        for l in range(len(LAYERS)):
            m = self.own_mask(n, l)
            if not m.any():
                continue
            lab, k = ndimage.label(m, structure=np.ones((3, 3)))
            labels[l] = lab
            offs[l] = total
            total += k
        parent = list(range(total))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for x, y, bn, bl in self.barrels + [(r[1], r[2], r[3], r[4]) for r in self.routes if r[0] == 'via']:
            if bn != n:
                continue
            i, j = cell(x, y)
            ids = [offs[l] + labels[l][j, i] - 1 for l in bl if l in labels and labels[l][j, i] > 0]
            for a in ids[1:]:
                union(ids[0], a)
        groups = {}
        for l, lab in labels.items():
            for k in range(1, lab.max() + 1):
                groups.setdefault(find(offs[l] + k - 1), []).append((l, k))
        pads_cells = []
        for p in self.cop['pads']:
            if self.nid[p['net']] == n:
                i, j = cell(p['x'], p['y'])
                for ln in p['polys']:
                    l = LI[ln]
                    if l in labels and labels[l][j, i] > 0:
                        pads_cells.append(find(offs[l] + labels[l][j, i] - 1))
        keep = set(pads_cells)
        out = []
        for g, members in groups.items():
            if g in keep:
                out.append(members)
        return out, labels

    # ------------------------------------------------------------------ routing
    def blocked_layer(self, n, l, bb, r_extra, cN, items_only=False):
        j0, j1, i0, i1 = bb
        sub = self.hard[l][j0:j1, i0:i1]
        cl = self.clr[l][j0:j1, i0:i1]
        foreign = (sub >= 0) & (sub != n)
        if items_only:
            foreign &= ~self.zonehard[l][j0:j1, i0:i1]
        blk = np.zeros(sub.shape, bool)
        for cv in np.unique(cl[foreign]):
            d = ndimage.distance_transform_edt(~(foreign & (cl == cv))) * H - H / 2
            blk |= d < r_extra + max(cN, float(cv)) + MARGIN
        return blk

    def route_edge(self, n, A, B, labels, partner=None, full=False):
        net = self.nname[n]
        ru = rules_for(net, self.classes)
        w, cN = ru['w'], ru['clr']
        vdia, vdrill = ru['via']
        planes = PLANE_TARGET.get(net, [])
        layers = ROUTE + [l for l in planes if l not in ROUTE]
        amask = {}
        bmask = {}
        for l in layers:
            if l in labels:
                la = np.isin(labels[l], [k for (ll, k) in A if ll == l])
                lb = np.isin(labels[l], [k for (ll, k) in B if ll == l])
                if la.any():
                    amask[l] = la
                if lb.any():
                    bmask[l] = lb
        if not amask or not bmask:
            return None
        if full:
            bb = (0, NY, 0, NX)
        else:
            ys, xs = [], []
            for mm in list(amask.values()) + list(bmask.values()):
                jj, ii = np.nonzero(mm)
                ys += [jj.min(), jj.max()]
                xs += [ii.min(), ii.max()]
            pad = 80
            bb = (max(min(ys) - pad, 0), min(max(ys) + pad, NY), max(min(xs) - pad, 0), min(max(xs) + pad, NX))
        j0, j1, i0, i1 = bb
        ny, nx = j1 - j0, i1 - i0
        holes = self.holes[j0:j1, i0:i1]
        hole_foreign_d = ndimage.distance_transform_edt(~((holes >= 0) & (holes != n))) * H - H / 2
        hole_any_d = ndimage.distance_transform_edt(~(holes >= 0)) * H - H / 2
        edge = self.edge_dist[j0:j1, i0:i1]
        passable, cost = {}, {}
        for l in layers:
            own = self.own_mask(n, l)[j0:j1, i0:i1]
            if l in planes and l not in ROUTE:
                passable[l] = own & (hole_foreign_d >= vdrill / 2 + HOLE_CLR)
                cost[l] = np.ones((ny, nx))
                continue
            blk_all = self.blocked_layer(n, l, bb, w / 2, cN)
            blk = self.blocked_layer(n, l, bb, w / 2, cN, items_only=True)
            lxz = self.zonehard[l][j0:j1, i0:i1] & (self.hard[l][j0:j1, i0:i1] == self.nid.get('LX', -99)) & (n != self.nid.get('LX', -99))
            if lxz.any():
                blk |= ndimage.distance_transform_edt(~lxz) * H - H / 2 < w / 2 + 0.3 + MARGIN
            pour_only = blk_all & ~blk
            blk |= hole_foreign_d < w / 2 + HOLE_CLR + MARGIN
            blk |= self.keep_tracks[j0:j1, i0:i1]
            blk |= edge < w / 2 + EDGE_CLR + MARGIN
            passable[l] = ~blk
            c = np.full((ny, nx), LAYER_COST[l])
            c[pour_only] *= pour_mult(net)
            if net in QUIET:
                lx = self.lx_proj[j0:j1, i0:i1]
                if l == 3:
                    c[lx] *= 5.0
                if l == 2:
                    c[lx] *= 5.0
            if partner is not None:
                pm = self.hard[l][j0:j1, i0:i1] == partner
                if pm.any():
                    d = ndimage.distance_transform_edt(~pm) * H
                    band = (d > w / 2 + cN) & (d < w / 2 + cN + 0.45)
                    c[band] *= 0.45
                else:
                    c *= 1.3
            cost[l] = c
            # own terminal cells always enterable
            for mm in (amask.get(l), bmask.get(l)):
                if mm is not None:
                    passable[l] |= mm[j0:j1, i0:i1] & (hole_foreign_d >= 0)
        # via feasibility: annulus layers (the two ends) need full clearance, set per pair below; every other
        # layer only needs its pads, vias and tracks cleared by the hole (a power pour clears round the hole)
        vbase = hole_any_d >= vdrill / 2 + HOLE_HOLE + MARGIN
        vbase &= ~self.keep_vias[j0:j1, i0:i1]
        vbase &= edge >= vdia / 2 + EDGE_CLR + MARGIN
        items_block = np.zeros((ny, nx), bool)
        pour_count = np.zeros((ny, nx))
        full_block = {}
        for l in range(len(LAYERS)):
            items_block |= self.blocked_layer(n, l, bb, vdrill / 2 + HOLE_CLR - cN, cN, items_only=True)
            zh = self.zonehard[l][j0:j1, i0:i1] & (self.hard[l][j0:j1, i0:i1] != n)
            if l not in (1, 4, 6):
                pour_count += ndimage.binary_dilation(zh, iterations=4)
            if l in layers:
                fb = self.blocked_layer(n, l, bb, vdia / 2, cN, items_only=True)
                lxz = self.zonehard[l][j0:j1, i0:i1] & (self.hard[l][j0:j1, i0:i1] == self.nid.get('LX', -99)) & (n != self.nid.get('LX', -99))
                if lxz.any():
                    fb |= ndimage.distance_transform_edt(~lxz) * H - H / 2 < vdia / 2 + 0.3 + MARGIN
                full_block[l] = fb
        vbase &= ~items_block
        # graph
        L = len(layers)
        N = L * ny * nx
        rows, cols, wts = [], [], []
        idx = np.arange(ny * nx).reshape(ny, nx)
        for k, l in enumerate(layers):
            P = passable[l]
            C = cost[l]
            base = k * ny * nx
            for (dj, di, s) in ((0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))):
                if di >= 0:
                    a = (slice(0, ny - dj), slice(0, nx - di))
                    b = (slice(dj, ny), slice(di, nx))
                else:
                    a = (slice(0, ny - dj), slice(1, nx))
                    b = (slice(dj, ny), slice(0, nx - 1))
                ok = P[a] & P[b]
                if s > 1:   # no diagonal squeeze past a blocked corner
                    if di > 0:
                        ok &= P[a[0], b[1]] & P[b[0], a[1]]
                    else:
                        ok &= P[slice(0, ny - 1), slice(0, nx - 1)] & P[slice(1, ny), slice(1, nx)]
                rows.append(base + idx[a][ok])
                cols.append(base + idx[b][ok])
                wts.append((H * s * 0.5 * (C[a] + C[b]))[ok])
        for ka in range(L):
            for kb in range(ka + 1, L):
                la, lb = layers[ka], layers[kb]
                ok = vbase & passable[la] & passable[lb]
                if la in ROUTE:
                    ok &= ~full_block[la] | (amask.get(la, np.zeros((NY, NX), bool))[j0:j1, i0:i1]) | (bmask.get(la, np.zeros((NY, NX), bool))[j0:j1, i0:i1])
                if lb in ROUTE:
                    ok &= ~full_block[lb] | (amask.get(lb, np.zeros((NY, NX), bool))[j0:j1, i0:i1]) | (bmask.get(lb, np.zeros((NY, NX), bool))[j0:j1, i0:i1])
                ii = idx[ok]
                rows.append(ka * ny * nx + ii)
                cols.append(kb * ny * nx + ii)
                wts.append(VIA_COST + 3.0 * pour_count[ok])
        r_ = np.concatenate(rows)
        c_ = np.concatenate(cols)
        w_ = np.concatenate(wts)
        G = sp.coo_matrix((w_, (r_, c_)), shape=(N, N)).tocsr()
        src, dst = [], []
        for k, l in enumerate(layers):
            if l in amask:
                m = amask[l][j0:j1, i0:i1] & passable[l]
                src.append(k * ny * nx + idx[m])
            if l in bmask:
                m = bmask[l][j0:j1, i0:i1] & passable[l]
                dst.append(k * ny * nx + idx[m])
        src = np.concatenate(src) if src else np.array([], int)
        dst = np.concatenate(dst) if dst else np.array([], int)
        if src.size == 0 or dst.size == 0:
            return None
        if src.size > 4000:
            src = src[:: max(1, src.size // 4000)]
        dist, pred, sources = dijkstra(G, directed=False, indices=src, min_only=True, return_predecessors=True)
        dd = dist[dst]
        if not np.isfinite(dd).any():
            return None
        t = int(dst[np.argmin(dd)])
        path = []
        while t >= 0:
            path.append(t)
            if t == sources[t]:
                break
            t = pred[t]
        path.reverse()
        out = []
        for node in path:
            k, rem = divmod(node, ny * nx)
            j, i = divmod(rem, nx)
            out.append((layers[k], j + j0, i + i0))
        return out, ru

    def commit(self, n, path, ru):
        w, cN = ru['w'], ru['clr']
        vdia, vdrill = ru['via']
        pts = [(l, X0 + (i + 0.5) * H, Y0 + (j + 0.5) * H) for (l, j, i) in path]
        geoms = []
        k = 0
        while k < len(pts):
            l = pts[k][0]
            run = [pts[k]]
            k += 1
            while k < len(pts) and pts[k][0] == l:
                run.append(pts[k])
                k += 1
            if k < len(pts):
                geoms.append(('via', run[-1][1], run[-1][2], n, [l, pts[k][0]], vdia, vdrill))
            # simplify collinear points
            simp = [run[0]]
            for p in run[1:]:
                if len(simp) >= 2:
                    a, b = simp[-2], simp[-1]
                    if abs((b[1] - a[1]) * (p[2] - b[2]) - (b[2] - a[2]) * (p[1] - b[1])) < 1e-9:
                        simp[-1] = p
                        continue
                simp.append(p)
            if l in ROUTE:
                for a, b in zip(simp, simp[1:]):
                    geoms.append(('track', a[1], a[2], b[1], b[2], n, l, w))
        for g in geoms:
            if g[0] == 'track':
                _, x0, y0, x1, y1, nn, l, ww = g
                tmp = np.zeros((NY, NX), bool)
                raster_seg(x0, y0, x1, y1, ww / 2, tmp, True)
                self.hard[l][tmp] = nn
                self.clr[l][tmp] = cN
            else:
                _, x, y, nn, ls, dia, drill = g
                raster_disc(x, y, drill / 2, self.holes, nn)
                for l in ls:
                    if l in ROUTE:
                        tmp = np.zeros((NY, NX), bool)
                        raster_disc(x, y, dia / 2, tmp, True)
                        self.hard[l][tmp] = nn
                        self.clr[l][tmp] = cN
            self.routes.append(g)
        return geoms

    def route_net(self, net, log):
        n = self.nid[net]
        partner = self.nid[PAIRS[net]] if net in PAIRS else None
        failed = set()
        fails = 0
        for attempt in range(80):
            isl, labels = self.islands(n)
            if len(isl) <= 1:
                return fails
            proj, keys = [], []
            for members in isl:
                m = np.zeros((NY, NX), bool)
                for (l, k) in members:
                    m |= labels[l] == k
                proj.append(m)
                keys.append(int(np.flatnonzero(m)[0]))
            cands = []
            for a in range(len(proj)):
                da = ndimage.distance_transform_edt(~proj[a]) * H
                for b in range(a + 1, len(proj)):
                    if (keys[a], keys[b]) in failed:
                        continue
                    cands.append((float(da[proj[b]].min()), a, b))
                if a == 0 and len(proj) > 12:
                    break           # large nets (plane fan-outs): pair everything with island 0 only
            if not cands:
                return fails
            cands.sort()
            dist, a, b = cands[0]
            res = self.route_edge(n, isl[a], isl[b], labels, partner)
            if res is None:
                res = self.route_edge(n, isl[a], isl[b], labels, partner, full=True)
            if res is None:
                log.append('FAIL %s: island %d (%d cells) to island %d, gap %.1f mm' % (net, a, int(proj[a].sum()), b, dist))
                failed.add((keys[a], keys[b]))
                fails += 1
                continue
            path, ru = res
            g = self.commit(n, path, ru)
            nv = sum(1 for x in g if x[0] == 'via')
            ln = sum(math.hypot(x[3] - x[1], x[4] - x[2]) for x in g if x[0] == 'track')
            log.append('ok   %-16s %5.1f mm, %d via(s), w %.2f, gap %.1f' % (net, ln, nv, ru['w'], dist))
        return fails


ORDER = ['SNS_CH1', 'SNS_CH2', 'SNS_CH3', 'ISNS_P', 'ISNS_N',
         'Net-(U19-OUTA)', 'GATE_M1', 'Net-(U19-OUTB)',
         'Net-(D2--)', 'GATE_M7', 'Net-(D11--)', 'GATE_M2', 'Net-(D8--)', 'GATE_M6', 'Net-(D14--)', 'GATE_M3',
         'Net-(D22--)', 'GATE_M5', 'Net-(D13--)', 'GATE_M4',
         'Net-(U11-OUT)', 'Net-(M10-G)', 'Net-(U12-OUT)', 'Net-(M9-G)', 'Net-(U6-OUT)', 'Net-(M8-G)',
         'Net-(U15-VDDA)', 'Net-(U10-VDDA)', 'Net-(U8-VDDA)', 'Net-(D10--)', 'Net-(D21--)', 'Net-(D9--)',
         'm2_source', 'm3_source', 'm4_source',
         'IREF1_input', 'IREF2_input', 'IREF3_input', 'Current',
         'M1_ON', 'M2_ON', 'ena_out_1', 'out_2_on', 'ena_out_2', 'out_3_on', 'ena_out_3',
         'analog_5V', '12V', '5V', 'LX', 'Vin', 'Vout_1', 'Vout_2', 'Vout_3',
         'Output1_drain', 'Output2_drain', 'Output3_drain', 'GND']


def main():
    a = sys.argv[1:]
    cop = json.load(open(a[0]))
    out = a[1]
    only = a[a.index('--nets') + 1].split(',') if '--nets' in a else None
    skip = set(a[a.index('--skip') + 1].split(',')) if '--skip' in a else set()
    t0 = time.time()
    bd = Board(cop)
    log = ['board rasterised in %.1f s' % (time.time() - t0)]
    order = [n for n in ORDER if n in bd.nid and (only is None or n in only) and n not in skip]
    total_fail = 0
    for net in order:
        t1 = time.time()
        f = bd.route_net(net, log)
        total_fail += f
        log.append('     %-16s done in %.1f s%s' % (net, time.time() - t1, (' (%d failed)' % f) if f else ''))
        print('\n'.join(log[-3:]), flush=True)
    tracks, vias = [], []
    for g in bd.routes:
        if g[0] == 'track':
            _, x0, y0, x1, y1, n, l, w = g
            tracks.append(dict(net=bd.nname[n], layer=LAYERS[l], w=w, x0=round(x0, 3), y0=round(y0, 3),
                               x1=round(x1, 3), y1=round(y1, 3)))
        else:
            _, x, y, n, ls, dia, drill = g
            vias.append(dict(net=bd.nname[n], x=round(x, 3), y=round(y, 3), dia=dia, drill=drill,
                             layers=[LAYERS[l] for l in ls]))
    json.dump(dict(tracks=tracks, vias=vias, log=log, failures=total_fail), open(out, 'w'), indent=1)
    print('tracks %d, vias %d, failures %d, %.0f s' % (len(tracks), len(vias), total_fail, time.time() - t0))


if __name__ == '__main__':
    main()
