"""Pour and routing checks on an export_copper6.py JSON (system Python: numpy, scipy, Pillow, matplotlib).

    python pcb_checks.py COPPER.json power|card OUTDIR [--solve DUMPDIR BRANCHES.json]

Read-only: works on the export, never on a board file. Grid 0.05 mm. Per copper layer and per checked net:
  islands  - separate pieces of the net's copper on that layer, with the vias/pins and pads that tie each piece in
  slices   - other-net tracks running through the net's copper (the net's copper on both sides within 1.2 mm of the
             track edge), grouped into runs. Per run: slot length; detour = shortest path through the net's copper
             between the two sides of the run's middle, minus the straight gap; and whether the run alone keeps two
             pieces apart (they would join if the track moved)
  necks    - passages narrower than 1 mm and 2 mm (morphological opening) that join two wide regions (>= 3 mm2)
  hot      - with --solve: the solver's largest sheet current over the net's DC branches (A per mm of width),
             grouped into spots
Routing: acute corners, short jogs (< 0.15 mm segments), and track runs longer than 1.5x their end-to-end distance.
Reference: tracks whose neighbouring plane layer has no GND copper under them for more than 1 mm (via antipads
within 0.7 mm of a barrel are not counted).
Outputs: OUTDIR/TAG_checks.txt, TAG_checks.json and OUTDIR/crops/*.png for the listed items.
"""
import json, math, os, sys, collections
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_layers import colour

H = 0.05
CFG = {
    'power': dict(
        nets={'Vin': 18.4, 'rsense_lo': 20.7, 'LX': 15.8, 'GND': 15.8, 'Vout_1': 7.05, 'Vout_2': 7.69,
              'Vout_3': 8.35, 'm2_source': 7.05, 'm3_source': 7.69, 'm4_source': 8.35, 'Output1_drain': 2.63,
              'Output2_drain': 2.37, 'Output3_drain': 2.37, 'Net-(M10-S)': 2.63, 'Net-(M9-S)': 2.37,
              'Net-(M8-S)': 2.37, '12V': 0.1},
        cu={'F.Cu': 0.035, 'In1.Cu': 0.030, 'In2.Cu': 0.030, 'In3.Cu': 0.030, 'In4.Cu': 0.030, 'B.Cu': 0.035},
        ref={'F.Cu': 'In1.Cu', 'In2.Cu': 'In1.Cu', 'In3.Cu': 'In4.Cu', 'B.Cu': 'In4.Cu'}, planes=['GND']),
    'card': dict(
        nets={'GND': 0.2, '5V': 0.2, '12V': 0.05, 'analog_5V': 0.05},
        cu={'F.Cu': 0.035, 'In1.Cu': 0.0152, 'In2.Cu': 0.0152, 'In3.Cu': 0.0152, 'In4.Cu': 0.0152, 'B.Cu': 0.035},
        ref={'F.Cu': 'In1.Cu', 'In2.Cu': 'In3.Cu', 'In3.Cu': 'In2.Cu', 'B.Cu': 'In4.Cu', 'In4.Cu': 'In3.Cu'},
        planes=['GND', '5V']),
}
SLICE_REACH = 1.2      # mm beyond the track edge to look for the pour on each side
SLICE_STEP = 0.2       # mm between samples along a track
MIN_RUN = 1.5          # mm: shorter runs are not listed
WIDE_AREA = 3.0        # mm2: a "wide region" for the neck test


class Grid:
    def __init__(self, d):
        xs = [v for s in d['edge'] for v in (s[0], s[2])]
        ys = [v for s in d['edge'] for v in (s[1], s[3])]
        self.x0, self.y0 = math.floor(min(xs)) - 0.5, math.floor(min(ys)) - 0.5
        self.nx = int(math.ceil((max(xs) + 0.5 - self.x0) / H))
        self.ny = int(math.ceil((max(ys) + 0.5 - self.y0) / H))

    def px(self, pts):
        return [((x - self.x0) / H - 0.5, (y - self.y0) / H - 0.5) for x, y in pts]

    def ij(self, x, y):
        return (np.clip(((np.asarray(y) - self.y0) / H).astype(int), 0, self.ny - 1),
                np.clip(((np.asarray(x) - self.x0) / H).astype(int), 0, self.nx - 1))

    def xy(self, j, i):
        return self.x0 + (i + 0.5) * H, self.y0 + (j + 0.5) * H


def draw_polys(g, polys):
    img = Image.new('1', (g.nx, g.ny), 0)
    dr = ImageDraw.Draw(img)
    for p in polys:
        hole = isinstance(p, dict)
        pts = p['hole'] if hole else p
        if len(pts) >= 3:
            dr.polygon(g.px(pts), fill=0 if hole else 1)
    return np.array(img, bool)


def build(d, g):
    names = sorted(d['nets'])
    idx = {n: k for k, n in enumerate(names)}
    owner = {}
    holes = Image.new('1', (g.nx, g.ny), 0)
    dr = ImageDraw.Draw(holes)
    for b in d['barrels']:
        r = b['drill'] / 2 / H
        cx, cy = (b['x'] - g.x0) / H - 0.5, (b['y'] - g.y0) / H - 0.5
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=1)
    holes = np.array(holes, bool)
    for ln in d['layers']:
        o = np.full((g.ny, g.nx), -1, np.int16)
        for n in names:
            polys = d['nets'][n].get(ln)
            if polys:
                o[draw_polys(g, polys)] = idx[n]
        o[holes] = -1
        owner[ln] = o
    return names, idx, owner, holes


def disk(r_px):
    r = int(math.ceil(r_px))
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r_px * r_px


# ---------------------------------------------------------------- islands
def islands(d, g, idx, owner, net, ln):
    m = owner[ln] == idx[net]
    lab, n = ndimage.label(m)
    if n == 0:
        return lab, []
    area = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1)) * H * H
    ties = collections.defaultdict(lambda: [0, 0, []])
    for b in d['barrels']:
        if b['net'] != net or ln not in b.get('layers', []):
            continue
        r = b['drill'] / 2 + 0.12
        j, i = g.ij([b['x'] + r, b['x'] - r, b['x'], b['x']], [b['y'], b['y'], b['y'] + r, b['y'] - r])
        ls = {int(v) for v in lab[j, i] if v}
        for v in ls:
            ties[v][0] += 1
    for p in d['pads']:
        if p['net'] != net or ln not in p.get('layers', []):
            continue
        j, i = g.ij(p['x'], p['y'])
        v = int(lab[j, i])
        if not v:
            for dx, dy in ((0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3), (0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6)):
                jj, ii = g.ij(p['x'] + dx, p['y'] + dy)
                if lab[jj, ii]:
                    v = int(lab[jj, ii])
                    break
        if v:
            ties[v][1] += 1
            ties[v][2].append('%s.%s' % (p['ref'], p['num']))
    sl = ndimage.find_objects(lab)
    out = []
    for k in range(n):
        a = float(area[k])
        if a < 0.3:
            continue
        s = sl[k]
        jc, ic = ndimage.center_of_mass(lab[s] == k + 1)
        cx, cy = g.xy(s[0].start + jc, s[1].start + ic)
        x1, y1 = g.xy(s[0].start, s[1].start)
        x2, y2 = g.xy(s[0].stop - 1, s[1].stop - 1)
        t = ties[k + 1]
        out.append(dict(label=k + 1, area=round(a, 2), centre=[round(float(cx), 1), round(float(cy), 1)],
                        bbox=[round(float(x1), 1), round(float(y1), 1), round(float(x2), 1), round(float(y2), 1)], vias=t[0], pads=t[1],
                        pad_names=sorted(set(t[2]))[:8]))
    out.sort(key=lambda r: -r['area'])
    return lab, out


# ---------------------------------------------------------------- slices
def samples(tracks):
    P, N, W, T = [], [], [], []
    for k, t in enumerate(tracks):
        a, b = np.array([t['x0'], t['y0']]), np.array([t['x1'], t['y1']])
        L = float(np.hypot(*(b - a)))
        if L < 1e-6:
            continue
        u = (b - a) / L
        n = np.array([-u[1], u[0]])
        m = max(int(L / SLICE_STEP), 1)
        for s in (np.arange(m) + 0.5) * (L / m):
            P.append(a + u * s)
            N.append(n)
            W.append(t['w'])
            T.append(k)
    return np.array(P).reshape(-1, 2), np.array(N).reshape(-1, 2), np.array(W), np.array(T, int)


def first_hit(g, o, P, N, W, own, sign):
    """Net index and gap (mm) of the first copper beyond the track edge on one side; -1 if none / board edge."""
    offs = np.arange(0.05, SLICE_REACH + 1e-9, 0.05)
    d = W[:, None] / 2 + offs[None, :]
    X = P[:, 0:1] + sign * N[:, 0:1] * d
    Y = P[:, 1:2] + sign * N[:, 1:2] * d
    j, i = g.ij(X, Y)
    v = o[j, i].astype(int)
    out_of = (X < g.x0) | (Y < g.y0) | (X > g.x0 + g.nx * H) | (Y > g.y0 + g.ny * H)
    v[out_of] = -2
    v[v == own[:, None]] = -1          # the track's own copper
    hit = v != -1
    k = np.where(hit.any(1), hit.argmax(1), -1)
    net = np.where(k >= 0, v[np.arange(len(v)), np.maximum(k, 0)], -1)
    gap = np.where(k >= 0, offs[np.maximum(k, 0)], np.nan)
    return net, gap


def geodesic(mask, a, b, g, win=25.0, step=2):
    """Shortest path (mm) through mask between points a and b, inside a window; inf if not reached."""
    xs, ys = sorted([a[0], b[0]]), sorted([a[1], b[1]])
    j0, i0 = g.ij(xs[0] - win, ys[0] - win)
    j1, i1 = g.ij(xs[1] + win, ys[1] + win)
    sub = mask[j0:j1 + 1, i0:i1 + 1]
    ny, nx = sub.shape
    ny2, nx2 = ny // step, nx // step
    sub = sub[:ny2 * step, :nx2 * step].reshape(ny2, step, nx2, step).any((1, 3))
    hh = H * step
    idxm = -np.ones(sub.shape, int)
    idxm[sub] = np.arange(sub.sum())
    rows, cols, wts = [], [], []
    for dj, di, w in ((0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))):
        xs_, xd_ = (slice(0, nx2 - di), slice(di, nx2)) if di >= 0 else (slice(-di, nx2), slice(0, nx2 + di))
        A = idxm[0:ny2 - dj, xs_]
        B = idxm[dj:ny2, xd_]
        ok = (A >= 0) & (B >= 0)
        rows.append(A[ok]); cols.append(B[ok]); wts.append(np.full(ok.sum(), w * hh))
    n = int(sub.sum())
    if n == 0:
        return math.inf
    G = sp.coo_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()

    def node(p):
        jj, ii = g.ij(p[0], p[1])
        jj, ii = (int(jj) - j0) // step, (int(ii) - i0) // step
        best = None
        for r in range(0, 4):
            for dj in range(-r, r + 1):
                for di in range(-r, r + 1):
                    y, x = jj + dj, ii + di
                    if 0 <= y < ny2 and 0 <= x < nx2 and idxm[y, x] >= 0:
                        return idxm[y, x]
        return best
    na, nb = node(a), node(b)
    if na is None or nb is None:
        return math.inf
    dist = dijkstra(G, directed=False, indices=na, limit=6 * win)
    return float(dist[nb])


def slices(d, g, names, idx, owner, holes, nets, labs):
    out = []
    labareas = {}
    by_layer = collections.defaultdict(list)
    for t in d['tracks']:
        by_layer[t['layer']].append(t)
    for ln, trs in by_layer.items():
        o = owner[ln]
        P, N, W, T = samples(trs)
        if not len(P):
            continue
        own = np.array([idx.get(trs[k]['net'], -9) for k in T])
        nl, gl = first_hit(g, o, P, N, W, own, +1)
        nr, gr = first_hit(g, o, P, N, W, own, -1)
        for net in nets:
            if net not in idx:
                continue
            q = idx[net]
            sel = np.where((nl == q) & (nr == q) & (own != q))[0]
            if not len(sel):
                continue
            if (ln, net) not in labareas:
                labareas[(ln, net)] = np.bincount(labs[(ln, net)].ravel()) * H * H
            # group samples of the same foreign net into runs
            groups = collections.defaultdict(list)
            for s in sel:
                groups[trs[T[s]]['net']].append(s)
            for fnet, ss in groups.items():
                ss = np.array(ss)
                tree = cKDTree(P[ss])
                pairs = tree.query_pairs(SLICE_STEP * 1.9 + 0.05)
                parent = list(range(len(ss)))

                def find(a):
                    while parent[a] != a:
                        parent[a] = parent[parent[a]]
                        a = parent[a]
                    return a
                for a, b in pairs:
                    ra, rb = find(a), find(b)
                    if ra != rb:
                        parent[ra] = rb
                runs = collections.defaultdict(list)
                for k in range(len(ss)):
                    runs[find(k)].append(ss[k])
                for run in runs.values():
                    run = np.array(run)
                    if len(run) * SLICE_STEP < MIN_RUN:
                        continue
                    c = P[run].mean(0)
                    mid = run[np.argmin(np.hypot(*(P[run] - c).T))]
                    p, n, w = P[mid], N[mid], W[mid]
                    A = p + n * (w / 2 + gl[mid] + 0.1)
                    B = p - n * (w / 2 + gr[mid] + 0.1)
                    straight = float(np.hypot(*(A - B)))
                    lab = labs[(ln, net)]
                    la, lb = lab[g.ij(*A)], lab[g.ij(*B)]
                    mask = o == q
                    if la and lb and la != lb:
                        geo = math.inf
                        sep = 'pieces %d / %d on this layer only meet through other layers' % (la, lb)
                    else:
                        geo = geodesic(mask, A, B, g)
                        sep = ''
                    # does this run alone keep pieces apart? fill its channel and relabel the touched pieces
                    jj, ii = g.ij(P[run, 0], P[run, 1])
                    rad = (w / 2 + np.nanmax(np.r_[gl[run], gr[run]]) + 0.06) / H
                    m_ = int(rad) + 6
                    wj = slice(max(jj.min() - m_, 0), min(jj.max() + m_ + 1, g.ny))
                    wi = slice(max(ii.min() - m_, 0), min(ii.max() + m_ + 1, g.nx))
                    corr = np.zeros((wj.stop - wj.start, wi.stop - wi.start), bool)
                    corr[jj - wj.start, ii - wi.start] = True
                    corr = ndimage.binary_dilation(corr, disk(rad))
                    corr &= (o[wj, wi] == -1) | (o[wj, wi] == idx.get(fnet, -9))
                    corr &= ~holes[wj, wi]
                    touched = sorted({int(v) for v in np.unique(lab[wj, wi][ndimage.binary_dilation(corr, disk(1.5))])
                                      if v})
                    joins = []
                    if len(touched) > 1:
                        areas = labareas[(ln, net)]
                        joins = [[v, round(float(areas[v]), 1)] for v in touched if areas[v] >= 0.5]
                        if len(joins) < 2:
                            joins = []
                    xs, ys = P[run, 0], P[run, 1]
                    out.append(dict(layer=ln, pour=net, track_net=fnet, length=round(float(len(run) * SLICE_STEP), 1),
                                    width=round(float(w), 2),
                                    gap=round(float(np.nanmedian(np.r_[gl[run], gr[run]])), 2),
                                    bbox=[round(float(xs.min()), 1), round(float(ys.min()), 1),
                                          round(float(xs.max()), 1), round(float(ys.max()), 1)],
                                    mid=[round(float(p[0]), 2), round(float(p[1]), 2)],
                                    straight=round(straight, 2),
                                    detour=(round(geo - straight, 1) if math.isfinite(geo) else None),
                                    note=sep, joins=joins))
    return out


# ---------------------------------------------------------------- necks
def necks(g, idx, owner, net, ln, hot=None):
    m = owner[ln] == idx[net]
    if m.sum() * H * H < 2 * WIDE_AREA:
        return []
    edt = ndimage.distance_transform_edt(m) * H
    out = []
    seen = np.zeros_like(m)
    for r in (0.5, 1.0):
        core = edt >= r
        opened = ndimage.distance_transform_edt(~core) * H <= r
        opened &= m
        wl, nw = ndimage.label(opened)
        if nw < 2:
            continue
        wa = ndimage.sum(np.ones_like(wl), wl, index=np.arange(1, nw + 1)) * H * H
        big = np.zeros(nw + 1, bool)
        big[1:] = wa >= WIDE_AREA
        neck = m & ~opened
        nl, nn = ndimage.label(neck, structure=np.ones((3, 3)))
        sl = ndimage.find_objects(nl)
        for k in range(nn):
            s = sl[k]
            pad = 3
            s2 = (slice(max(s[0].start - pad, 0), s[0].stop + pad), slice(max(s[1].start - pad, 0), s[1].stop + pad))
            comp = nl[s2] == k + 1
            ring = ndimage.binary_dilation(comp, np.ones((5, 5))) & ~comp
            touch = {int(v) for v in np.unique(wl[s2][ring]) if v and big[v]}
            if len(touch) < 2:
                continue
            if seen[s2][comp].mean() > 0.5:
                continue
            seen[s2] |= comp
            area = comp.sum() * H * H
            jc, ic = ndimage.center_of_mass(comp)
            cx, cy = g.xy(s2[0].start + jc, s2[1].start + ic)
            x1, y1 = g.xy(s[0].start, s[1].start)
            x2, y2 = g.xy(s[0].stop - 1, s[1].stop - 1)
            rec = dict(layer=ln, net=net, narrower_than=2 * r, area=round(float(area), 2),
                       centre=[round(float(cx), 1), round(float(cy), 1)],
                       bbox=[round(float(x1), 1), round(float(y1), 1), round(float(x2), 1), round(float(y2), 1)],
                       regions=sorted(round(float(wa[v - 1]), 1) for v in touch))
            if hot is not None:
                hv = hot[0][s2][comp]
                if hv.size:
                    kk = int(np.nanargmax(np.nan_to_num(hv, nan=-1)))
                    rec['A_per_mm'] = round(float(np.nan_to_num(hv[kk])), 2)
                    rec['branch'] = hot[1][s2][comp][kk]
            out.append(rec)
    return out


# ---------------------------------------------------------------- solver sheet current
def load_hot(g, d, names, dumpdir, branches, nets):
    """Per (net, layer): max |sheet current| A/mm over the net's DC branches, resampled to the grid, and which branch."""
    hot = {}
    Y, X = np.mgrid[0:g.ny, 0:g.nx]
    X = g.x0 + (X + 0.5) * H
    Y = g.y0 + (Y + 0.5) * H
    for br in branches:
        if br['name'].startswith('loop') or br['net'] not in nets:
            continue
        cands = [f for f in os.listdir(dumpdir) if f.endswith('.npz')]
        key = ''.join(ch if ch.isalnum() or ch in '_-' else '_' for ch in br['name'])
        match = [f for f in cands if f[:-4] == key]
        if not match:
            continue
        z = np.load(os.path.join(dumpdir, match[0]))
        x0, y0, h, nx, ny = float(z['x0']), float(z['y0']), float(z['h']), int(z['nx']), int(z['ny'])
        ii = np.floor((X - x0) / h).astype(int)
        jj = np.floor((Y - y0) / h).astype(int)
        ok = (ii >= 0) & (ii < nx) & (jj >= 0) & (jj < ny)
        for ln in [str(v) for v in z['layers']]:
            s = np.hypot(z['sx_' + ln], z['sy_' + ln]) * br['I']
            v = np.full((g.ny, g.nx), np.nan, np.float32)
            v[ok] = s[jj[ok], ii[ok]]
            key2 = (br['net'], ln)
            if key2 not in hot:
                hot[key2] = [np.full((g.ny, g.nx), np.nan, np.float32), np.full((g.ny, g.nx), '', object)]
            cur, who = hot[key2]
            better = np.nan_to_num(v, nan=-1) > np.nan_to_num(cur, nan=-1)
            cur[better] = v[better]
            who[better] = br['name']
    return hot


def hotspots(g, hot, idx, owner, cu, top=6):
    out = []
    for (net, ln), (v, who) in hot.items():
        m = owner[ln] == idx[net]
        vv = np.where(m, np.nan_to_num(v, nan=0), 0)
        thr = 2.0 if ln in ('F.Cu', 'B.Cu') else 1.0
        lab, n = ndimage.label(vv >= thr, structure=np.ones((3, 3)))
        if n == 0:
            continue
        peaks = ndimage.maximum(vv, lab, index=np.arange(1, n + 1))
        pos = ndimage.maximum_position(vv, lab, index=np.arange(1, n + 1))
        cnt = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
        order = np.argsort(-peaks)[:top]
        sl = ndimage.find_objects(lab)
        for k in order:
            j, i = pos[k]
            x, y = g.xy(j, i)
            s = sl[k]
            x1, y1 = g.xy(s[0].start, s[1].start)
            x2, y2 = g.xy(s[0].stop - 1, s[1].stop - 1)
            t = cu[ln]
            k_ipc = 0.048 if ln in ('F.Cu', 'B.Cu') else 0.024
            a_mil2 = 1.0 * t * 1550.0031
            rise1 = (peaks[k] / (k_ipc * a_mil2 ** 0.725)) ** (1 / 0.44)
            out.append(dict(net=net, layer=ln, peak_A_per_mm=round(float(peaks[k]), 2), at=[round(x, 2), round(y, 2)],
                            branch=who[j, i], area_above=round(float(cnt[k] * H * H), 2),
                            bbox=[round(float(x1), 1), round(float(y1), 1), round(float(x2), 1), round(float(y2), 1)],
                            J_A_per_mm2=round(float(peaks[k] / t), 1), ipc_rise_1mm_strip=round(float(rise1), 1)))
    out.sort(key=lambda r: -r['peak_A_per_mm'])
    return out


# ---------------------------------------------------------------- routing
def routing(d):
    acute, jogs, detours = [], collections.Counter(), []
    key = lambda x, y: (round(x, 3), round(y, 3))
    groups = collections.defaultdict(list)
    for t in d['tracks']:
        groups[(t['net'], t['layer'])].append(t)
    for (net, ln), trs in groups.items():
        adj = collections.defaultdict(list)
        for k, t in enumerate(trs):
            a, b = key(t['x0'], t['y0']), key(t['x1'], t['y1'])
            if a == b:
                continue
            adj[a].append((k, b))
            adj[b].append((k, a))
            if math.dist(a, b) < 0.15:
                jogs[(net, ln)] += 1
        for p, lst in adj.items():
            if len(lst) == 2:
                (k1, q1), (k2, q2) = lst
                v1 = np.subtract(q1, p); v2 = np.subtract(q2, p)
                c = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                ang = math.degrees(math.acos(max(-1, min(1, c))))
                if ang < 89.5:
                    acute.append(dict(net=net, layer=ln, at=[p[0], p[1]], angle=round(ang)))
        # chains between nodes of degree != 2
        used = set()
        ends = [p for p, l in adj.items() if len(l) != 2]
        for s in ends:
            for k, q in adj[s]:
                if k in used:
                    continue
                path_len, prev, cur, kk, pts = 0.0, s, q, k, [s]
                while True:
                    used.add(kk)
                    path_len += math.dist(prev, cur)
                    pts.append(cur)
                    nxt = [(k2, q2) for k2, q2 in adj[cur] if k2 != kk]
                    if len(adj[cur]) != 2 or not nxt:
                        break
                    kk, q2 = nxt[0]
                    prev, cur = cur, q2
                    if kk in used:
                        break
                straight = math.dist(s, cur)
                if path_len >= 4 and straight > 0.5 and path_len / straight >= 1.5:
                    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                    detours.append(dict(net=net, layer=ln, length=round(path_len, 1), straight=round(straight, 1),
                                        ratio=round(path_len / straight, 2), start=list(s), end=list(cur),
                                        bbox=[min(xs), min(ys), max(xs), max(ys)]))
    detours.sort(key=lambda r: -(r['length'] - r['straight']))
    return acute, jogs, detours


def reference(d, g, idx, owner, ref, skip_nets, planes):
    out = []
    pl = np.array([idx[n] for n in planes if n in idx])
    bar = np.array([[b['x'], b['y']] for b in d['barrels']]) if d['barrels'] else np.zeros((0, 2))
    tree = cKDTree(bar) if len(bar) else None
    for t in d['tracks']:
        ln = t['layer']
        if ln not in ref or t['net'] in skip_nets:
            continue
        a, b = np.array([t['x0'], t['y0']]), np.array([t['x1'], t['y1']])
        L = float(np.hypot(*(b - a)))
        if L < 0.2:
            continue
        m = max(int(L / 0.1), 1)
        P = a + np.outer((np.arange(m) + 0.5) / m, b - a)
        j, i = g.ij(P[:, 0], P[:, 1])
        miss = ~np.isin(owner[ref[ln]][j, i], pl)
        if tree is not None:
            dd, _ = tree.query(P)
            miss &= dd > 0.7
        if miss.sum() * (L / m) >= 1.0:
            # longest consecutive missing stretch
            best, cur = 0, 0
            for v in miss:
                cur = cur + 1 if v else 0
                best = max(best, cur)
            if best * (L / m) >= 1.0:
                k = int(np.argmax(miss))
                under = collections.Counter(int(owner[ref[ln]][j[q], i[q]]) for q in np.where(miss)[0])
                out.append(dict(net=t['net'], layer=ln, ref=ref[ln], length=round(best * L / m, 1),
                                at=[round(float(P[k, 0]), 2), round(float(P[k, 1]), 2)], seg=[t['x0'], t['y0'], t['x1'], t['y1']],
                                under=dict(under)))
    # merge per net/layer: total and worst
    return out


# ---------------------------------------------------------------- crops
def crop(g, d, names, owner, ln, box, title, path, marks=(), heat=None):
    x1, y1, x2, y2 = box
    j1, i1 = g.ij(x1, y1)
    j2, i2 = g.ij(x2, y2)
    o = owner[ln][j1:j2 + 1, i1:i2 + 1]
    pal = np.array([to_rgb(colour(n)) for n in names] + [(1, 1, 1)])
    img = pal[np.where(o < 0, len(names), o)]
    fig, ax = plt.subplots(figsize=(7, 7 * (y2 - y1) / max(x2 - x1, 1e-3) + 0.6), dpi=110)
    ax.imshow(img, extent=(x1, x2, y2, y1), interpolation='nearest')
    if heat is not None:
        hv = heat[j1:j2 + 1, i1:i2 + 1]
        im = ax.imshow(np.where(hv > 0.3, hv, np.nan), extent=(x1, x2, y2, y1), cmap='inferno', alpha=0.75,
                       interpolation='nearest')
        fig.colorbar(im, ax=ax, fraction=0.04, label='A per mm of width')
    for b in d['barrels']:
        if x1 <= b['x'] <= x2 and y1 <= b['y'] <= y2:
            ax.add_patch(plt.Circle((b['x'], b['y']), b['drill'] / 2, color='black', fill=False, lw=0.5))
    for mk in marks:
        kind = mk[0]
        if kind == 'box':
            _, bx = mk
            ax.add_patch(plt.Rectangle((bx[0], bx[1]), bx[2] - bx[0], bx[3] - bx[1], fill=False, ec='red', lw=1.6))
        elif kind == 'pt':
            _, (x, y), lab = mk
            ax.plot(x, y, 'x', color='red', ms=10, mew=2)
            if lab:
                ax.text(x, y, ' ' + lab, color='red', fontsize=8, va='bottom')
    ax.set_xlim(x1, x2)
    ax.set_ylim(y2, y1)
    ax.set_title(title, fontsize=9)
    ax.grid(True, color='#999999', lw=0.3)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    a = sys.argv[1:]
    js, tag, out = a[:3]
    cfg = CFG[tag]
    d = json.load(open(js))
    g = Grid(d)
    os.makedirs(os.path.join(out, 'crops'), exist_ok=True)
    names, idx, owner, holes = build(d, g)
    nets = [n for n in cfg['nets'] if n in idx]
    hot = {}
    if '--solve' in a:
        k = a.index('--solve')
        hot = load_hot(g, d, names, a[k + 1], json.load(open(a[k + 2])), set(nets))
    res = dict(islands={}, slices=[], necks=[], hot=[], acute=[], jogs={}, detours=[], reference=[])
    labs = {}
    for ln in d['layers']:
        for net in nets:
            lab, isl = islands(d, g, idx, owner, net, ln)
            labs[(ln, net)] = lab
            if isl:
                res['islands']['%s|%s' % (ln, net)] = isl
            res['necks'] += necks(g, idx, owner, net, ln, hot.get((net, ln)))
    res['slices'] = slices(d, g, names, idx, owner, holes, nets, labs)
    if hot:
        res['hot'] = hotspots(g, hot, idx, owner, cfg['cu'])
    res['acute'], jogs, res['detours'] = routing(d)
    res['jogs'] = {'%s|%s' % k: v for k, v in jogs.most_common()}
    res['reference'] = reference(d, g, idx, owner, cfg['ref'], skip_nets={'GND'} | set(n for n in nets if n != '12V'), planes=cfg['planes'])
    json.dump(res, open(os.path.join(out, '%s_checks.json' % tag), 'w'), indent=1, default=str)

    # ---- text summary
    L = []
    w = L.append
    w('%s: %s' % (tag, js))
    w('\n== islands (pieces >= 0.3 mm2 of each checked net, per layer; vias = barrels landing in the piece)')
    for key, isl in res['islands'].items():
        if len(isl) == 1:
            continue
        w('%s: %d pieces' % (key, len(isl)))
        for r in isl:
            w('   %7.1f mm2 at %s  vias %d  pads %d %s' % (r['area'], r['centre'], r['vias'], r['pads'],
                                                          ' '.join(r['pad_names'])))
    w('\n== slices (other-net tracks through a checked net\'s copper, runs >= %.1f mm), by pour current x length' % MIN_RUN)
    ss = sorted(res['slices'], key=lambda r: -(cfg['nets'].get(r['pour'], 0) * r['length']))
    for r in ss:
        w('%-6s %-14s cut by %-22s %5.1f mm  w %.2f gap %.2f  mid %s  detour %s  %s%s' % (
            r['layer'], r['pour'], r['track_net'], r['length'], r['width'], r['gap'], r['mid'],
            ('%.1f mm' % r['detour']) if r['detour'] is not None else 'n/a', r['note'],
            ('  SEPARATES pieces ' + str(r['joins'])) if r['joins'] else ''))
    w('\n== necks joining two wide regions')
    for r in sorted(res['necks'], key=lambda r: (-(r.get('A_per_mm') or 0), r['narrower_than'])):
        w('%-6s %-14s < %.0f mm  at %s  bbox %s  regions %s  %s' % (
            r['layer'], r['net'], r['narrower_than'], r['centre'], r['bbox'], r['regions'],
            ('%.2f A/mm (%s)' % (r['A_per_mm'], r['branch'])) if 'A_per_mm' in r else ''))
    if res['hot']:
        w('\n== hot spots (solver sheet current, A per mm of width; IPC rise of a long 1 mm strip at that density, '
          'for scale only)')
        for r in res['hot']:
            w('%-6s %-14s %5.2f A/mm (%6.1f A/mm2)  at %s  area %.2f mm2  1 mm strip %5.1f C  %s' % (
                r['layer'], r['net'], r['peak_A_per_mm'], r['J_A_per_mm2'], r['at'], r['area_above'],
                r['ipc_rise_1mm_strip'], r['branch']))
    w('\n== routing: track runs > 1.5x their end-to-end distance (>= 4 mm), worst 40')
    for r in res['detours'][:40]:
        w('%-6s %-22s %5.1f mm for %5.1f mm (x%.1f)  %s -> %s' % (r['layer'], r['net'], r['length'], r['straight'],
                                                               r['ratio'], r['start'], r['end']))
    w('\n== routing: acute corners (< 90 deg): %d' % len(res['acute']))
    for r in res['acute'][:40]:
        w('   %-6s %-22s %3d deg at %s' % (r['layer'], r['net'], r['angle'], r['at']))
    w('\n== routing: jogs (segments < 0.15 mm): %d in %d net/layers' % (sum(jogs.values()), len(jogs)))
    for k, v in list(res['jogs'].items())[:20]:
        w('   %-40s %d' % (k, v))
    w('\n== reference: signal tracks with no plane copper (%s) under them on the neighbouring layer for >= 1 mm'
      % '/'.join(cfg['planes']))
    for r in sorted(res['reference'], key=lambda r: -r['length']):
        under = ', '.join('%s %d' % (names[k] if k >= 0 else 'none', v) for k, v in r['under'].items())
        w('%-6s %-22s over %-6s %4.1f mm at %s  (under it: %s)' % (r['layer'], r['net'], r['ref'], r['length'], r['at'],
                                                                 under))
    open(os.path.join(out, '%s_checks.txt' % tag), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:5]))
    print('wrote', os.path.join(out, '%s_checks.txt' % tag))
    np.savez_compressed(os.path.join(out, '%s_grid.npz' % tag), **{('own_' + k): v for k, v in owner.items()},
                        x0=g.x0, y0=g.y0, h=H, names=np.array(names),
                        **{('hot_%s_%s' % k): v[0] for k, v in hot.items()})


if __name__ == '__main__':
    main()
