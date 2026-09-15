"""Macro-based simulated annealing for the power-board placement (pmodel geometry).

  python psa4.py CONFIG.json OUT_PREFIX seed

Movers are single parts or rigid macros: a switch pair with its source pins side by side, a sink FET
with its shunt at the source pin, an LED pad pair. The brief's adjacency rules hold by construction;
the annealer only places movers. Cost terms as psa3: overlap/outside, target misses, card and corner
rules, zones, screw keep-outs (tab holes and standoffs), and the 15 mm rule.

CONFIG keys: fixed {ref: [x, y, rot, side]}, singles {ref: side}, init {ref: [x, y, rot, side]},
macros {name: {members: [[ref, dx, dy, rot, side], ...], init: [x, y, rot]}}, swap_groups [[mover, ...]],
zones {ref: [l, t, r, b]}, in_card [refs], screwed, corner, card_size, card_x, card_y_range, card_y0,
weights {ov, t, ko, far, card}, iters, T0, T1, step0.
"""
import sys, json, math, random
import pmodel as M
import pcheck as C

cfg = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
random.seed(int(sys.argv[3]))
W = dict(ov=20.0, t=10.0, ko=30.0, far=3.0, card=20.0)
W.update(cfg.get('weights', {}))
CS = cfg.get('card_size', 42.0)
CORNER = tuple(cfg['corner'])
SCREWED = set(cfg['screwed'])
CARD_X = cfg.get('card_x', 30.0)
CARD_XR = cfg.get('card_x_range', [CARD_X, CARD_X])
card_x = cfg.get('card_x0', CARD_X)
CARD_Y = cfg.get('card_y_range', [31.0, 74.0])
IN_CARD = set(cfg.get('in_card', []))
ZONES = {k: tuple(v) for k, v in cfg.get('zones', {}).items()}
STANDOFFS = ('H5', 'H6', 'H7', 'H8')
card_y = cfg.get('card_y0', 60.0)


def rot(a, x, y):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return x * c + y * s, -x * s + y * c


L = {k: tuple(v) for k, v in cfg['fixed'].items()}
MOVERS = {}
for name, side in cfg.get('singles', {}).items():
    MOVERS[name] = dict(members=[(name, 0.0, 0.0, 0, side)], pl=list(cfg['init'][name][:3]))
for name, m in cfg.get('macros', {}).items():
    MOVERS[name] = dict(members=[tuple(x) for x in m['members']], pl=list(m['init']))


def expand(name):
    X, Y, R = MOVERS[name]['pl']
    out = {}
    for ref, dx, dy, r, side in MOVERS[name]['members']:
        ox, oy = rot(R, dx, dy)
        out[ref] = (X + ox, Y + oy, int(round(R + r)) % 360, side)
    return out


for name in MOVERS:
    L.update(expand(name))
refs = list(L)
MEMBERS = {n: [m[0] for m in MOVERS[n]['members']] for n in MOVERS}
NAMES = list(MOVERS)

# targets, captured once from pcheck with a probe
TG = []
_orig = M.d


def _probe(Ld, a, pa, b, pb):
    TG.append((a, pa, b, pb))
    return 0.0


C.d = _probe
C.distances(L)
C.d = _orig
GOALS = cfg.get('goals', {})          # {substring of the pcheck label: [limit mm, weight]}
TG2 = []
for (a, pa, b, pb), trow in zip(TG, C.TARGETS):
    lim, label = trow[3], trow[1]
    if a not in L or b not in L or lim >= 90:
        continue
    wgt = 3.0 if lim <= 5 else 1.0
    for key, (glim, gw) in GOALS.items():
        if key in label:
            lim, wgt = glim, gw
    TG2.append((a, pa, b, pb, lim, wgt))
TG = TG2
FAR_MM = cfg.get('far_mm', 15.0)
by_part = {r: [i for i, t in enumerate(TG) if t[0] == r or t[2] == r] for r in refs}

rects = {r: M.areas(L, r) for r in refs}
padc = {}


def pad_pos(r, num):
    key = (r, num)
    if key not in padc:
        p = M.pad(L, r, num)
        padc[key] = (p[1], p[2])
    return padc[key]


def set_part(p, pl):
    L[p] = pl
    rects[p] = M.areas(L, p)
    for k in [k for k in padc if k[0] == p]:
        del padc[k]


def place(name, pl):
    MOVERS[name]['pl'] = list(pl)
    for ref, v in expand(name).items():
        set_part(ref, v)


def ov(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def outside(r):
    e = M.EDGE
    return (r[2] - r[0]) * (r[3] - r[1]) - ov(r, (30 + e, 30 + e, 104 - e, 116 - e)) + ov(r, (86 - e, 30, 104, 42 + e))


def part_ov(p, half_pairs=False):
    o, pr = 0.0, 0.0
    for side, r, kind in rects[p]:
        o += outside(r)
        for q in refs:
            if q == p:
                continue
            for s2, r2, k2 in rects[q]:
                if s2 == side:
                    pr += ov(r, r2)
    return o + (0.5 * pr if half_pairs else pr)


def tgt(i):
    a, pa, b, pb, lim, wgt = TG[i]
    A, B = pad_pos(a, pa), pad_pos(b, pb)
    dd = math.hypot(A[0] - B[0], A[1] - B[1])
    return wgt * max(0.0, dd - lim)


def card_rect():
    return (card_x, card_y, card_x + CS, card_y + CS)


def card_self():
    cr = card_rect()
    return 10.0 * (ov(cr, CORNER) + outside(cr))


def part_card(p):
    s = 0.0
    cr = card_rect()
    h = M.HEIGHT.get(p, 0.0)
    z = ZONES.get(p)
    if z:
        side0, r0, kind0 = rects[p][0]
        s += (r0[2] - r0[0]) * (r0[3] - r0[1]) - ov(r0, z)
    for side, r, kind in rects[p]:
        if p in IN_CARD and side == 'F':
            inner = (cr[0] + 2, cr[1] + 2, cr[2] - 2, cr[3] - 2)
            s += (r[2] - r[0]) * (r[3] - r[1]) - ov(r, inner)
        if side != 'F':
            continue
        if p == 'L1':
            s += ov((r[0] - 1, r[1] - 1, r[2] + 1, r[3] + 1), cr)
        if p == 'L1' or h > 16:
            s += ov(r, CORNER)
    return s


def screws():
    out = {m: M.tab_hole(L, m) for m in SCREWED if m in L}
    for h in STANDOFFS:
        if h in L:
            out[h] = L[h][:2]
    return out


def part_ko(p, scr):
    s = 0.0
    for m, (sx, sy) in scr.items():
        if m == p:
            continue
        for side, r, kind in rects[p]:
            if p in M.FETS and kind == 'body' and side == 'B':
                continue
            lim = 5.5 if (side == 'F' and M.HEIGHT.get(p, 0) > 3) else 3.75
            dd = M.rect_circle_dist(r, sx, sy)
            if dd < lim:
                s += lim - dd
    return s


def far_rule(scr):
    pts = list(scr.values())
    s = 0.0
    for m in M.FETS:
        if m in L and m not in SCREWED:
            bx, by = M.body_centre(L, m)
            s += max(0.0, min(math.hypot(bx - x, by - y) for x, y in pts) - FAR_MM)
    return s


def total():
    scr = screws()
    o = sum(part_ov(p, half_pairs=True) for p in refs)
    t = sum(tgt(i) for i in range(len(TG)))
    c = sum(part_card(p) for p in refs)
    ko = sum(part_ko(p, scr) for p in refs)
    return (W['ov'] * o + W['t'] * t + W['card'] * (c + card_self()) + W['ko'] * ko
            + W['far'] * far_rule(scr))


def needs_total(name):
    return any(r in SCREWED or r in STANDOFFS for r in MEMBERS[name])


def mover_local(name, scr):
    mem = MEMBERS[name]
    tg = set()
    s = 0.0
    for p in mem:
        tg.update(by_part[p])
        s += W['ov'] * part_ov(p) + W['card'] * part_card(p) + W['ko'] * part_ko(p, scr)
    s += W['t'] * sum(tgt(i) for i in tg)
    if any(p in M.FETS for p in mem):
        s += W['far'] * far_rule(scr)
    return s


def snapshot():
    return {n: list(MOVERS[n]['pl']) for n in NAMES}, (card_x, card_y)



def write_result(pls, cy, path, extra):
    lay = {}
    for n, pl in pls.items():
        X, Y, R = pl
        for ref, dx, dy, r, side in MOVERS[n]['members']:
            ox, oy = rot(R, dx, dy)
            lay[ref] = [X + ox, Y + oy, int(round(R + r)) % 360, side]
    for k, v in cfg['fixed'].items():
        lay.setdefault(k, list(v))
    d = dict(layout=lay, card=[cy[0], cy[1]], card_size=CS, movers=pls)
    d.update(extra)
    json.dump(d, open(path, 'w'), indent=1)



def checkpoint(b, it):
    write_result(b[1], b[2], OUT + '.json', dict(final=False, it=it, cost=b[0]))


ONLY = set(cfg.get('only_move') or NAMES)       # restrict a clean-up pass to a neighbourhood
NAMES_MOVE = [n for n in NAMES if n in ONLY]
GROUPS = [[n for n in g if n in MOVERS and n in ONLY] for g in cfg.get('swap_groups', [])]
GROUPS = [g for g in GROUPS if len(g) > 1]
CARDPARTS = [p for p in refs if p == 'L1' or p in IN_CARD]

cur = total()
best = (cur,) + snapshot()
N = cfg.get('iters', 300000)
T0, T1 = cfg.get('T0', 60.0), cfg.get('T1', 0.02)
for it in range(N):
    frac = it / N
    T = T0 * (T1 / T0) ** frac
    step = max(0.2, cfg.get('step0', 10.0) * (1 - frac) ** 1.5)
    u = random.random()
    if u < 0.04 and not cfg.get('card_fixed'):
        # the card carries J10 and the standoffs with it
        old = (card_x, card_y)
        oldp = {n: list(MOVERS[n]['pl']) for n in NAMES if n in IN_CARD}
        before = total()
        card_x = min(max(card_x + random.gauss(0, step), CARD_XR[0]), CARD_XR[1])
        card_y = min(max(card_y + random.gauss(0, step), CARD_Y[0]), CARD_Y[1])
        ddx, ddy = card_x - old[0], card_y - old[1]
        for n, pl in oldp.items():
            place(n, (pl[0] + ddx, pl[1] + ddy, pl[2]))
        dlt = total() - before
        if dlt <= 0 or random.random() < math.exp(-dlt / T):
            cur += dlt
            if cur < best[0] - 1e-9:
                best = (cur,) + snapshot()
        else:
            card_x, card_y = old
            for n, pl in oldp.items():
                place(n, pl)
        continue
    if u < 0.12 and GROUPS:
        a, b = random.sample(random.choice(GROUPS), 2)
        pa, pb = list(MOVERS[a]['pl']), list(MOVERS[b]['pl'])
        full = needs_total(a) or needs_total(b)
        scr = screws()
        before = total() if full else mover_local(a, scr) + mover_local(b, scr)
        place(a, pb)
        place(b, pa)
        after = total() if full else mover_local(a, scr) + mover_local(b, scr)
        dlt = after - before
        if dlt <= 0 or random.random() < math.exp(-dlt / T):
            cur += dlt
        else:
            place(a, pa)
            place(b, pb)
        if cur < best[0] - 1e-9:
            best = (cur,) + snapshot()
        continue
    name = random.choice(NAMES_MOVE)
    old = list(MOVERS[name]['pl'])
    x, y, a = old
    if random.random() < 0.15:
        a = (a + random.choice((90, 180, 270))) % 360
    else:
        x += random.gauss(0, step)
        y += random.gauss(0, step)
    full = needs_total(name)
    scr = screws()
    before = total() if full else mover_local(name, scr)
    place(name, (x, y, a))
    after = total() if full else mover_local(name, scr)
    dlt = after - before
    if dlt <= 0 or random.random() < math.exp(-dlt / T):
        cur += dlt
        if cur < best[0] - 1e-9:
            best = (cur,) + snapshot()
    else:
        place(name, old)
    if it % max(1, N // 20) == 0:
        print('it %7d T %7.3f step %5.2f cur %9.1f best %9.1f' % (it, T, step, cur, best[0]), flush=True)
        checkpoint(best, it)


_, pls, (card_x, card_y) = best
for n, pl in pls.items():
    place(n, pl)
print('final exact cost %.1f (tracked %.1f)' % (total(), best[0]))
write_result(pls, (card_x, card_y), OUT + '.json', dict(final=True))
