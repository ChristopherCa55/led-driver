"""Simulated-annealing placer for the control card (system Python, numpy).

usage: python card_place.py CONFIG.json OUT_LAYOUT.json [--seed N] [--iters N] [--start LAYOUT.json]

Both sides are used (the SMD courtyards need 110 % of one side). A part's state is (x, y, rot, side); x, y is the KiCad
footprint origin and rot the KiCad orientation. Pad offsets follow KiCad's own transform, measured on this board:
F: rot 0 (x, y), 90 (y, -x), 180 (-x, -y), 270 (-y, x); B: the same applied to (x, -y).

Cost (all in the config):
- legality: courtyard overlap on each side (through-hole parts block both sides), area outside the card, courtyard
  inside a mounting-hole keep-out circle; weights ramp up during the run so the end state is legal;
- half-perimeter wire length of every signal net (power nets GND / 5V / analog_5V / 12V go to planes and are left
  out), with per-net weights;
- decoupling: every IC supply pin is matched to its own decoupling capacitor on the same rail (greedy matching,
  refreshed during the run) and pays for the distance above DECAP_OK; unmatched capacitors stay near some supply pin;
- 'near': pin-to-pin distance limits (e.g. D27 at the M1_INHIBIT node);
- 'apart': minimum distances between groups of pins / parts (e.g. the Current node against the 74HC14s, M1_ON and I2C);
- a small penalty for an IC on the underside.
Fixed parts (config 'fixed') never move.
"""
import json, math, random, re, sys, time
import numpy as np

cfg = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
args = sys.argv[3:]
seed = int(args[args.index('--seed') + 1]) if '--seed' in args else 1
ITERS = int(args[args.index('--iters') + 1]) if '--iters' in args else cfg.get('iters', 300000)
START = args[args.index('--start') + 1] if '--start' in args else None
rng = random.Random(seed)
np.random.seed(seed)

inv = json.load(open(cfg['inventory']))
X0, Y0, X1, Y1 = cfg['card']
INSET = cfg.get('edge_inset', 0.25)
refs = sorted(inv)
idx = {r: i for i, r in enumerate(refs)}
n = len(refs)
fixed = cfg['fixed']
movable = np.array([r not in fixed for r in refs])
side_only = {idx[r]: (1 if sd == 'B' else 0) for r, sd in cfg.get('side_only', {}).items()}   # e.g. too tall for the top
tht = np.array([bool(inv[r]['tht']) for r in refs])
is_ic = np.array([r[0] in 'UQ' for r in refs])

MATS = [np.array([[1, 0], [0, 1]]), np.array([[0, -1], [1, 0]]), np.array([[-1, 0], [0, -1]]),
        np.array([[0, 1], [-1, 0]])]


def tf(pts, side, rot):
    p = np.array(pts, float)
    if side == 1:
        p = p * np.array([1, -1])
    return p @ MATS[rot]


# courtyard bbox offsets per (side, rot)
BB = np.zeros((n, 2, 4, 4))
for i, r in enumerate(refs):
    c = inv[r]['courtyard'] or [-0.5, -0.5, 0.5, 0.5]
    corners = [(c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3])]
    for s in (0, 1):
        for k in range(4):
            q = tf(corners, s, k)
            BB[i, s, k] = (q[:, 0].min(), q[:, 1].min(), q[:, 0].max(), q[:, 1].max())

# pins
POWER = set(cfg.get('power_nets', ['GND', '5V', 'analog_5V', '12V']))
pin_part, pin_off, pin_net, pin_name = [], [], [], []
for i, r in enumerate(refs):
    for p in inv[r]['pads']:
        if not p.get('num'):
            continue
        pin_part.append(i)
        pin_off.append([tf([(p['x'], p['y'])], s, k)[0] for s in (0, 1) for k in range(4)])
        pin_net.append(p.get('net', ''))
        pin_name.append('%s.%s' % (r, p['num']))
pin_part = np.array(pin_part)
pin_off = np.array(pin_off).reshape(len(pin_part), 2, 4, 2)
pin_id = {nm: k for k, nm in enumerate(pin_name)}
netw = cfg.get('net_weights', {})
nets = {}
for k, nn in enumerate(pin_net):
    if nn and nn not in POWER and not nn.startswith('unconnected'):
        nets.setdefault(nn, []).append(k)
nets = {nn: np.array(v) for nn, v in nets.items() if len(v) > 1}
net_names = sorted(nets)
net_w = np.array([netw.get(nn, 1.0) for nn in net_names])
part_nets = [[] for _ in range(n)]
for j, nn in enumerate(net_names):
    for p in set(pin_part[nets[nn]].tolist()):
        part_nets[p].append(j)

# decoupling
DECAP_OK = cfg.get('decap_ok_mm', 2.0)
W_DEC = cfg.get('w_decap', 8.0)
supply = {}          # rail -> ([ic pin idx], [cap pin idx])
for rail in cfg.get('decap_rails', ['5V', 'analog_5V']):
    ics = [k for k, nn in enumerate(pin_net) if nn == rail and refs[pin_part[k]][0] in 'UQ']
    caps = []
    for k, nn in enumerate(pin_net):
        r = refs[pin_part[k]]
        if nn == rail and r.startswith('C') and any(pin_net[q] == 'GND' for q in range(len(pin_net))
                                                        if pin_part[q] == pin_part[k] and q != k):
            caps.append(k)
    supply[rail] = (ics, caps)

# near / apart constraints
near = [(pin_id[a], pin_id[b], float(m), float(w)) for a, b, m, w in cfg.get('near', [])]


def expand(items):
    """'U2' -> all its pins; 'net:X' -> all pins of net X; 'U2.4' -> that pin."""
    out = []
    for it in items:
        if it.startswith('net:'):
            out += [k for k, nn in enumerate(pin_net) if nn == it[4:]]
        elif it in pin_id:
            out.append(pin_id[it])
        else:
            out += [k for k in range(len(pin_part)) if refs[pin_part[k]] == it]
    return np.array(sorted(set(out)))


apart = [(expand(a), expand(b), float(m), float(w)) for a, b, m, w in cfg.get('apart', [])]
# 'apart_seg': [[victim nets], [aggressor nets], min mm, weight]. Each net is drawn as the minimum spanning tree of
# its pins (a proxy for its route); every aggressor segment should stay min mm from every victim segment.
apart_seg = [([nets[v] for v in a], [nets[g] for g in b], float(m), float(w)) for a, b, m, w in cfg.get('apart_seg', [])]


def mst_segs(ks):
    p = pinxy(ks)
    k = len(p)
    if k == 2:
        return np.array([[p[0, 0], p[0, 1], p[1, 0], p[1, 1]]])
    D = np.hypot(p[:, None, 0] - p[None, :, 0], p[:, None, 1] - p[None, :, 1])
    inn = np.zeros(k, bool)
    inn[0] = True
    best = D[0].copy()
    par = np.zeros(k, int)
    seg = []
    for _ in range(k - 1):
        c = np.where(inn, np.inf, best)
        j = int(np.argmin(c))
        seg.append((p[par[j], 0], p[par[j], 1], p[j, 0], p[j, 1]))
        inn[j] = True
        upd = D[j] < best
        best = np.where(upd, D[j], best)
        par = np.where(upd, j, par)
    return np.array(seg)


def seg_dist(A, B):
    """Minimum distance between every segment of A (m, 4) and of B (n, 4); 0 where they cross."""
    def pt_seg(P, S):          # P (m, 2) against S (n, 4) -> (m, n)
        ax, ay, bx, by = S[None, :, 0], S[None, :, 1], S[None, :, 2], S[None, :, 3]
        dx, dy = bx - ax, by - ay
        L2 = np.maximum(dx * dx + dy * dy, 1e-12)
        t = np.clip(((P[:, None, 0] - ax) * dx + (P[:, None, 1] - ay) * dy) / L2, 0, 1)
        return np.hypot(P[:, None, 0] - ax - t * dx, P[:, None, 1] - ay - t * dy)
    d = np.minimum.reduce([pt_seg(A[:, :2], B), pt_seg(A[:, 2:], B), pt_seg(B[:, :2], A).T, pt_seg(B[:, 2:], A).T])

    def orient(P, Q, R):
        return (Q[..., 0] - P[..., 0]) * (R[..., 1] - P[..., 1]) - (Q[..., 1] - P[..., 1]) * (R[..., 0] - P[..., 0])
    a1, a2 = A[:, None, :2], A[:, None, 2:]
    b1, b2 = B[None, :, :2], B[None, :, 2:]
    a1, a2 = np.broadcast_to(a1, (len(A), len(B), 2)), np.broadcast_to(a2, (len(A), len(B), 2))
    b1, b2 = np.broadcast_to(b1, (len(A), len(B), 2)), np.broadcast_to(b2, (len(A), len(B), 2))
    cross = (orient(a1, a2, b1) * orient(a1, a2, b2) < 0) & (orient(b1, b2, a1) * orient(b1, b2, a2) < 0)
    return np.where(cross, 0.0, d)
KO = np.array(cfg.get('keepouts', []), float).reshape(-1, 3)      # x, y, r (both sides)
W_ICB = cfg.get('w_ic_bottom', 3.0)
# 'clear_under': rectangles [x0, y0, x1, y1] (top-side SOIC footprints) the underside should keep free, so through vias
# for those pins have somewhere to land; an underside part pays w_clear per mm2 of overlap (soft, not legality)
CLR = np.array(cfg.get('clear_under', []), float).reshape(-1, 4)
W_CLR = cfg.get('w_clear', 0.0)


def clear_cost(i, b):
    if not len(CLR) or side[i] != 1 or not movable[i]:
        return 0.0
    ww = np.clip(np.minimum(b[2], CLR[:, 2]) - np.maximum(b[0], CLR[:, 0]), 0, None)
    hh = np.clip(np.minimum(b[3], CLR[:, 3]) - np.maximum(b[1], CLR[:, 1]), 0, None)
    return W_CLR * float((ww * hh).sum())
W_DEC_SIDE = cfg.get('w_decap_side', 6.0)

# state
x = np.zeros(n); y = np.zeros(n); rot = np.zeros(n, int); side = np.zeros(n, int)
for r, (fx, fy, fr, fs) in fixed.items():
    i = idx[r]
    x[i], y[i], rot[i], side[i] = fx, fy, int(round(fr / 90)) % 4, 1 if fs == 'B' else 0
if START:
    st = json.load(open(START))['layout']
    for r, (fx, fy, fr, fs) in st.items():
        i = idx[r]
        if movable[i]:
            x[i], y[i], rot[i], side[i] = fx, fy, int(round(fr / 90)) % 4, 1 if fs == 'B' else 0
else:
    for i in range(n):
        if movable[i]:
            x[i] = rng.uniform(X0 + 3, X1 - 3)
            y[i] = rng.uniform(Y0 + 3, Y1 - 3)
            rot[i] = rng.randrange(4)
            side[i] = 0 if (is_ic[i] and rng.random() < 0.8) else rng.randrange(2)
for i, sd in side_only.items():
    side[i] = sd


def bbox(i, xi=None, yi=None, ri=None, si=None):
    xi = x[i] if xi is None else xi
    yi = y[i] if yi is None else yi
    ri = rot[i] if ri is None else ri
    si = side[i] if si is None else si
    o = BB[i, si, ri]
    return np.array([xi + o[0], yi + o[1], xi + o[2], yi + o[3]])


BOX = np.array([bbox(i) for i in range(n)])


def pinxy(ks):
    p = pin_part[ks]
    off = pin_off[ks, side[p], rot[p]]
    return np.stack([x[p] + off[:, 0], y[p] + off[:, 1]], axis=1)


def overlap_one(i, b, others_mask):
    """Overlap area of box b (part i) with every other part that shares a side with it."""
    o = BOX
    ww = np.clip(np.minimum(b[2], o[:, 2]) - np.maximum(b[0], o[:, 0]), 0, None)
    hh = np.clip(np.minimum(b[3], o[:, 3]) - np.maximum(b[1], o[:, 1]), 0, None)
    same = (side == side[i]) | tht | tht[i]
    m = others_mask & same
    m[i] = False
    return float((ww * hh)[m].sum())


def outside(b):
    ix0, iy0, ix1, iy1 = X0 + INSET, Y0 + INSET, X1 - INSET, Y1 - INSET
    w, h = b[2] - b[0], b[3] - b[1]
    iw = max(0.0, min(b[2], ix1) - max(b[0], ix0))
    ih = max(0.0, min(b[3], iy1) - max(b[1], iy0))
    return w * h - iw * ih


def keepout(b):
    if not len(KO):
        return 0.0
    dx = np.maximum(np.maximum(b[0] - KO[:, 0], 0), KO[:, 0] - b[2])
    dy = np.maximum(np.maximum(b[1] - KO[:, 1], 0), KO[:, 1] - b[3])
    d = np.hypot(dx, dy)
    return float((np.clip(KO[:, 2] - d, 0, None) ** 2).sum()) * 4


def net_cost(js):
    tot = 0.0
    for j in js:
        p = pinxy(nets[net_names[j]])
        tot += net_w[j] * ((p[:, 0].max() - p[:, 0].min()) + (p[:, 1].max() - p[:, 1].min()))
    return tot


match = {}


def rematch():
    """Greedy one-to-one: each IC supply pin gets its nearest free capacitor on the rail."""
    global match
    match = {}
    for rail, (ics, caps) in supply.items():
        if not ics or not caps:
            continue
        a, b = pinxy(np.array(ics)), pinxy(np.array(caps))
        d = np.hypot(a[:, None, 0] - b[None, :, 0], a[:, None, 1] - b[None, :, 1])
        used_i, used_c = set(), set()
        for flat in np.argsort(d, axis=None):
            ii, cc = divmod(int(flat), d.shape[1])
            if ii in used_i or cc in used_c:
                continue
            match[ics[ii]] = caps[cc]
            used_i.add(ii)
            used_c.add(cc)


def global_cost():
    c = 0.0
    for rail, (ics, caps) in supply.items():
        if not ics or not caps:
            continue
        a, b = pinxy(np.array(ics)), pinxy(np.array(caps))
        for k, ic in enumerate(ics):
            if ic in match:
                q = pinxy(np.array([match[ic]]))[0]
                c += W_DEC * max(0.0, math.hypot(a[k, 0] - q[0], a[k, 1] - q[1]) - DECAP_OK)
                if side[pin_part[ic]] != side[pin_part[match[ic]]]:
                    c += W_DEC_SIDE        # its capacitor on the other side: two vias in the loop
        # every capacitor near some supply pin of its rail
        d = np.hypot(b[:, None, 0] - a[None, :, 0], b[:, None, 1] - a[None, :, 1]).min(axis=1)
        c += 0.3 * W_DEC * float(np.clip(d - 3 * DECAP_OK, 0, None).sum())
    for a, b, m, w in near:
        p = pinxy(np.array([a, b]))
        c += w * max(0.0, math.hypot(*(p[0] - p[1])) - m)
    for a, b, m, w in apart:
        pa, pb = pinxy(a), pinxy(b)
        d = np.hypot(pa[:, None, 0] - pb[None, :, 0], pa[:, None, 1] - pb[None, :, 1])
        c += w * float((np.clip(m - d, 0, None) ** 2).sum())
    for vic, agg, m, w in apart_seg:
        A = np.vstack([mst_segs(k) for k in vic])
        B = np.vstack([mst_segs(k) for k in agg])
        c += w * float((np.clip(m - seg_dist(A, B), 0, None) ** 2).sum())
    c += W_ICB * float((is_ic & (side == 1) & movable).sum())
    return c


W = dict(ov=cfg.get('w_overlap_start', 5.0), out=cfg.get('w_out_start', 5.0), ko=cfg.get('w_ko_start', 5.0))


def local_cost(parts):
    mask = np.ones(n, bool)
    mask[list(parts)] = False
    c = 0.0
    js = set()
    for i in parts:
        b = BOX[i]
        c += W['ov'] * overlap_one(i, b, mask) + W['out'] * outside(b) + W['ko'] * keepout(b) + clear_cost(i, b)
        js.update(part_nets[i])
    ps = list(parts)
    for a in range(len(ps)):
        for bb in range(a + 1, len(ps)):
            i, j = ps[a], ps[bb]
            if side[i] == side[j] or tht[i] or tht[j]:
                bi, bj = BOX[i], BOX[j]
                c += W['ov'] * max(0, min(bi[2], bj[2]) - max(bi[0], bj[0])) * max(0, min(bi[3], bj[3]) - max(bi[1], bj[1]))
    return c + net_cost(js)


def total_cost():
    c = 0.0
    for i in range(n):
        b = BOX[i]
        mask = np.zeros(n, bool)
        mask[i + 1:] = True
        c += W['ov'] * overlap_one(i, b, mask) + W['out'] * outside(b) * movable[i] + W['ko'] * keepout(b) * movable[i]
        c += clear_cost(i, b)
    return c + net_cost(range(len(net_names))) + global_cost()


mov = [i for i in range(n) if movable[i]]
rematch()
cur = total_cost()
t0 = time.time()
T0 = cfg.get('t0', 8.0)
T1 = cfg.get('t1', 0.02)
ramp = cfg.get('w_legal_end', 400.0)
acc = 0
for it in range(ITERS):
    frac = it / ITERS
    T = T0 * (T1 / T0) ** frac
    if it % 2000 == 0:
        scale = W['ov']
        W['ov'] = W['out'] = W['ko'] = cfg.get('w_overlap_start', 5.0) * (ramp / cfg.get('w_overlap_start', 5.0)) ** frac
        rematch()
        cur = total_cost()
    mv = rng.random()
    i = rng.choice(mov)
    parts = [i]
    old = [(x[i], y[i], rot[i], side[i])]
    if mv < 0.08:                               # swap with a part of the same footprint class
        cls = inv[refs[i]]['fp']
        cand = [j for j in mov if j != i and inv[refs[j]]['fp'] == cls]
        if not cand:
            continue
        j = rng.choice(cand)
        if (i in side_only or j in side_only) and side[i] != side[j]:
            continue
        parts = [i, j]
        old.append((x[j], y[j], rot[j], side[j]))
    before = local_cost(parts) + global_cost()
    if len(parts) == 2:
        j = parts[1]
        x[i], y[i], x[j], y[j] = x[j], y[j], x[i], y[i]
        side[i], side[j] = side[j], side[i]
    elif mv < 0.18:
        rot[i] = (rot[i] + rng.choice((1, 2, 3))) % 4
    elif mv < 0.23:
        if i in side_only:
            continue
        side[i] = 1 - side[i]
    else:
        span = max(0.3, 20.0 * (1 - frac) ** 1.5)
        x[i] = min(max(x[i] + rng.gauss(0, span / 2), X0), X1)
        y[i] = min(max(y[i] + rng.gauss(0, span / 2), Y0), Y1)
    for p in parts:
        BOX[p] = bbox(p)
    after = local_cost(parts) + global_cost()
    d = after - before
    if d <= 0 or rng.random() < math.exp(-d / T):
        cur += d
        acc += 1
    else:
        for p, (ox, oy, orr, osd) in zip(parts, old):
            x[p], y[p], rot[p], side[p] = ox, oy, orr, osd
            BOX[p] = bbox(p)
    if it % 50000 == 0:
        print('it %7d T %.3f cost %.1f acc %.2f (%.0f s)' % (it, T, cur, acc / (it + 1), time.time() - t0), flush=True)

# final legality report at the end weights
W['ov'] = W['out'] = W['ko'] = ramp
rematch()


def illegal(i):
    b = BOX[i]
    mask = np.ones(n, bool)
    return overlap_one(i, b, mask) > 1e-6 or outside(b) > 1e-6 or keepout(b) > 1e-9


def legalize(rounds=40, tries=300):
    """Move each part that still overlaps something to the cheapest legal spot nearby (radius grows by round)."""
    for rd in range(rounds):
        bad = [i for i in mov if illegal(i)]
        if not bad:
            return rd
        rng.shuffle(bad)
        for i in bad:
            best = (local_cost([i]) + global_cost(), x[i], y[i], rot[i], side[i])
            r = 1.0 + 0.4 * rd
            for _ in range(tries):
                x[i] = min(max(best[1] + rng.uniform(-r, r), X0), X1)
                y[i] = min(max(best[2] + rng.uniform(-r, r), Y0), Y1)
                rot[i] = rng.randrange(4) if rng.random() < 0.3 else best[3]
                side[i] = (1 - best[4]) if (rng.random() < 0.15 and i not in side_only) else best[4]
                BOX[i] = bbox(i)
                c = local_cost([i]) + global_cost()
                if c < best[0]:
                    best = (c, x[i], y[i], rot[i], side[i])
            x[i], y[i], rot[i], side[i] = best[1], best[2], best[3], best[4]
            BOX[i] = bbox(i)
    return rounds


small = movable & ~is_ic & ~tht


def shove(i, step=0.5):
    """Grid search for part i where only small movable parts (passives, diodes) may be covered, cheaply; fixed
    parts, ICs, the card edge and the keep-outs stay hard. Returns the small parts it now covers (to re-legalize)."""
    x0, y0, r0, s0 = x[i], y[i], rot[i], side[i]
    sides = [side[i]] if i in side_only else [0, 1]
    best = None
    for sd in sides:
        for rr in range(4):
            e = BB[i, sd, rr]
            for xi in np.arange(X0 + INSET - e[0], X1 - INSET - e[2] + 1e-9, step):      # whole card, inside the inset
                for yi in np.arange(Y0 + INSET - e[1], Y1 - INSET - e[3] + 1e-9, step):
                    b = bbox(i, xi, yi, rr, sd)
                    o = BOX
                    ww = np.clip(np.minimum(b[2], o[:, 2]) - np.maximum(b[0], o[:, 0]), 0, None)
                    hh = np.clip(np.minimum(b[3], o[:, 3]) - np.maximum(b[1], o[:, 1]), 0, None)
                    same = (side == sd) | tht | tht[i]
                    same[i] = False
                    a = ww * hh * same
                    hard = float(a[~small].sum()) + outside(b) + keepout(b)
                    if hard > 1e-9:
                        continue
                    soft = float(a[small].sum())
                    if best is not None and 60.0 * soft > best[0]:
                        continue
                    x[i], y[i], rot[i], side[i] = xi, yi, rr, sd
                    BOX[i] = b
                    c = 60.0 * soft + net_cost(part_nets[i]) + global_cost()
                    if best is None or c < best[0]:
                        best = (c, xi, yi, rr, sd)
    if best is None:
        x[i], y[i], rot[i], side[i] = x0, y0, r0, s0
        BOX[i] = bbox(i)
        return []
    x[i], y[i], rot[i], side[i] = best[1], best[2], best[3], best[4]
    BOX[i] = bbox(i)
    b = BOX[i]
    ww = np.clip(np.minimum(b[2], BOX[:, 2]) - np.maximum(b[0], BOX[:, 0]), 0, None)
    hh = np.clip(np.minimum(b[3], BOX[:, 3]) - np.maximum(b[1], BOX[:, 1]), 0, None)
    same = (side == side[i]) | tht | tht[i]
    same[i] = False
    return [j for j in np.nonzero((ww * hh > 1e-9) & same & small)[0]]


W['ov'] = W['out'] = W['ko'] = max(ramp, 5000.0)
used = legalize()
print('legalized in %d rounds' % used)
for sh in range(6):
    big = [i for i in mov if illegal(i) and not small[i]]
    if not big:
        break
    for i in big:
        hit = shove(i)
        print('shove %s -> (%.2f, %.2f) rot %d %s, displaces %s' % (refs[i], x[i], y[i], rot[i] * 90, 'FB'[side[i]],
                                                                  ', '.join(refs[j] for j in hit) or 'nothing'))
    rematch()
    used = legalize()
    print('legalized in %d rounds' % used)
ov = sum(overlap_one(i, BOX[i], np.arange(n) > i) for i in range(n))
out_a = sum(outside(BOX[i]) for i in mov)
ko_a = sum(keepout(BOX[i]) for i in mov)
wl = net_cost(range(len(net_names)))
layout = {r: [round(float(x[i]), 4), round(float(y[i]), 4), int(rot[i]) * 90, 'B' if side[i] else 'F'] for i, r in enumerate(refs)}
json.dump(dict(layout=layout, overlap_mm2=ov, outside_mm2=out_a, keepout=ko_a, wirelength=wl, seed=seed,
               iters=ITERS, match={pin_name[a]: pin_name[b] for a, b in match.items()}), open(OUT, 'w'), indent=1)
print('done: overlap %.3f mm2, outside %.3f mm2, keep-out %.3f, weighted wire length %.0f; %d F / %d B (%.0f s)' % (
    ov, out_a, ko_a, wl, int((side[movable] == 0).sum()), int((side[movable] == 1).sum()), time.time() - t0))
