"""Place the small parts around an optimizer layout (greedy, net-driven).

  python psat.py LAYOUT.json CONFIG.json OUT.json

Each unplaced part gets an anchor: the mean position of the pads (on placed parts) that share
its signal nets. Rails and ground nets with many pads are ignored for the anchor. Parts are placed
in order of how tightly they are tied (fewest anchor pads first is wrong; most specific first):
gate parts, sense parts, then decoupling, then the rest. Each part takes the nearest free spot
(spiral on a 0.25 mm grid, rotations 0/90/180/270) on its preferred side, keeping clear of
courtyards, the board edge and notch, screw washer keep-outs, and FET bodies on the bottom.
Top-side parts taller than 3 mm also keep the tool-path radius around screws: LAYOUT.json keys
tall_tab_mm / tall_standoff_mm (default 5.5 mm each, as psa5).
CONFIG 'place_first' parts are placed before everything else (gate resistors, pulldowns and turn-off diodes
at their gate pin); CONFIG 'either_side' parts try both sides and take the nearer free spot.
"""
import sys, json, math
import pmodel as M

res = json.load(open(sys.argv[1]))
cfg = json.load(open(sys.argv[2]))
L = {k: tuple(v) for k, v in res['layout'].items()}
SCREWED = cfg['screwed']
BIGNETS = {'GND', 'Vin', '5V', '12V', 'analog_5V', 'LX', 'Vout_1', 'Vout_2', 'Vout_3', 'rsense_lo'}
B_SIDE = set(cfg.get('prefer_bottom', []))
GAP = 0.25

todo = [r for r in M.INV if r not in L]


def rects_of(ref):
    return M.areas(L, ref)


occupied = {'F': [], 'B': []}
for ref in L:
    for side, r, kind in rects_of(ref):
        occupied[side].append((r, ref))
screws = [M.tab_hole(L, m) + (res.get('tall_tab_mm', 5.5),) for m in SCREWED if m in L]
for i, c in enumerate(res.get('standoffs', [])):
    screws.append(tuple(c[:2]) + (res.get('tall_standoff_mm', 5.5),))


def free(ref, pl):
    L[ref] = pl
    ok = True
    for side, r, kind in M.areas(L, ref):
        if not M.in_board((r[0] - 0.3, r[1] - 0.3, r[2] + 0.3, r[3] + 0.3)):
            ok = False
            break
        for (o, oref) in occupied[side]:
            if M.overlap(r, o, GAP):
                ok = False
                break
        if not ok:
            break
        for sx, sy, tall in screws:
            lim = tall if (side == 'F' and M.HEIGHT.get(ref, 0) > 3) else 3.75     # washer; tall parts keep the tool path
            if M.rect_circle_dist(r, sx, sy) < lim:
                ok = False
                break
        if not ok:
            break
    del L[ref]
    return ok


ANCH = cfg.get('anchors', {})


def anchor(ref):
    if ref in ANCH:
        pts = []
        for a_ref, a_pad in ANCH[ref]:
            p = M.pad(L, a_ref, a_pad)
            pts.append((p[1], p[2]))
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)), 1
    pts = []
    for p in M.INV[ref]['pads']:
        net = p['net']
        if not net or net in BIGNETS or net.startswith('unconnected'):
            continue
        for other in L:
            for num, x, y, w, h, n2, dr in M.pads(L, other):
                if n2 == net:
                    pts.append((x, y))
    if not pts:
        for p in M.INV[ref]['pads']:
            if p['net'] in ('5V', '12V', 'analog_5V', 'Vin'):
                for other in L:
                    for num, x, y, w, h, n2, dr in M.pads(L, other):
                        if n2 == p['net'] and not other.startswith('C'):
                            pts.append((x, y))
    if not pts:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)), len(pts)


skip = set(cfg.get('skip', []))
PLACE_FIRST = cfg.get('place_first', [])        # critical parts get the spots next to their anchor
EITHER_SIDE = set(cfg.get('either_side', []))   # may go on either side: the nearer spot wins
queue = []
for ref in todo:
    if ref in skip:
        continue
    area = M.INV[ref]['cw'] * M.INV[ref]['ch']
    rank = PLACE_FIRST.index(ref) if ref in PLACE_FIRST else len(PLACE_FIRST)
    queue.append((rank, -area if area > 40 else 0.0, ref))     # place_first in its own order, then big parts, then the rest
queue.sort()
queue = [ref for rank, big, ref in queue]


def ready(ref):
    return all(a_ref in L for a_ref, a_pad in ANCH.get(ref, []))


order = []
placed, failed = [], []
while queue:
    progress = False
    for ref in list(queue):
        if not ready(ref):
            continue
        queue.remove(ref)
        progress = True
        order.append(ref)
        break
    if not progress:
        for ref in queue:
            failed.append((ref, 'anchor part never placed: %s' % [a for a, p in ANCH.get(ref, []) if a not in L]))
        break
    ref = order[-1]
    a = anchor(ref)
    anc = a[0] if a else None
    if anc is None:
        failed.append((ref, 'no anchor'))
        continue
    pref = 'B' if ref in B_SIDE else 'F'
    sides = [pref, 'F' if pref == 'B' else 'B'] if ref in EITHER_SIDE else [pref]
    best, best_rad = None, None
    for side in sides:
        for rad in [i * 0.25 for i in range(0, 161)]:
            if best_rad is not None and rad >= best_rad:
                break                      # the other side already has a nearer spot
            hit = None
            steps = max(1, int(2 * math.pi * rad / 0.5))
            for k in range(steps):
                ang = 2 * math.pi * k / steps
                x, y = anc[0] + rad * math.cos(ang), anc[1] + rad * math.sin(ang)
                for rot in (0, 90, 180, 270):
                    if free(ref, (x, y, rot, side)):
                        hit = (x, y, rot, side)
                        break
                if hit:
                    break
            if hit:
                best, best_rad = hit, rad
                break
    if best is None:
        failed.append((ref, 'no room within 40 mm of (%.1f, %.1f)' % anc))
        continue
    L[ref] = best
    for s, r, kind in M.areas(L, ref):
        occupied[s].append((r, ref))
    placed.append((ref, math.hypot(best[0] - anc[0], best[1] - anc[1])))

res['layout'] = {k: list(v) for k, v in L.items()}
json.dump(res, open(sys.argv[3], 'w'), indent=1)
print('placed %d, failed %d' % (len(placed), len(failed)))
for ref, dd in sorted(placed, key=lambda t: -t[1])[:15]:
    print('   %-5s %.1f mm from anchor' % (ref, dd))
for f in failed:
    print('   FAILED', f)
if failed:
    sys.exit(3)        # the pipeline must not build a board with parts left where they were
