"""Checks, distance table and plot for a pmodel layout.

  evaluate(L, meta, out_png)   meta: screws {ref or name: (x, y)}, card (l, t, r, b), corner (l, t, r, b)
"""
import math
import pmodel as M
from pmodel import pad, d

TARGETS = []


def T(stage, label, val, lim, kind='<='):
    if val != val:
        return
    ok = val <= lim if kind == '<=' else val >= lim
    TARGETS.append((stage, label, val, lim, kind, ok))


def distances(L):
    TARGETS.clear()
    for c in ('C40', 'C69', 'C85'):
        T(1, '%s Vin -> R1 Vin force pad' % c, d(L, c, '1', 'R1', '1'), 10)
        T(1, '%s GND -> M1 source' % c, d(L, c, '2', 'M1', '3'), 10)
    T(1, 'R1 rsense_lo pad -> L1.2', d(L, 'R1', '4', 'L1', '2'), 10)
    T(1, 'J1 -> R1 Vin pad (report)', d(L, 'J1', '1', 'R1', '1'), 99)
    T(1, 'D19 LX -> M1 drain', d(L, 'D19', '1', 'M1', '2'), 5)
    T(1, 'D19 GND -> M1 source', d(L, 'D19', '2', 'M1', '3'), 5)
    T(1, 'U19 OUTA -> M1 gate', d(L, 'U19', '15', 'M1', '1'), 10)
    T(1, 'U25 IN+ -> R1 sense P', d(L, 'U25', '8', 'R1', '2'), 10)
    T(1, 'U25 IN- -> R1 sense N', d(L, 'U25', '1', 'R1', '3'), 10)
    for m in ('M1', 'M7', 'M6', 'M5'):
        T(2, 'L1 LX pad -> %s drain' % m, d(L, 'L1', '1', m, '2'), 15)
    for lx, rail, drv, rg, rl in (('M7', 'M2', 'U15', 'R13', 'R60'), ('M6', 'M3', 'U10', 'R23', 'R70'), ('M5', 'M4', 'U8', 'R47', 'R59')):
        T(3, '%s source <-> %s source' % (lx, rail), d(L, lx, '3', rail, '3'), 11.25)
        T(3, '%s OUTA -> %s gate' % (drv, rail), d(L, drv, '15', rail, '1'), 15)
        T(3, '%s OUTB -> %s gate' % (drv, lx), d(L, drv, '10', lx, '1'), 15)
    for fet, caps in (('M2', ('C70', 'C86', 'C88')), ('M3', ('C71', 'C78', 'C87')), ('M4', ('C74', 'C75', 'C77'))):
        for c in caps:
            T(4, '%s drain -> %s' % (fet, c), d(L, fet, '2', c, '1'), 15)
    for a, b in (('J3', 'J4'), ('J8', 'J7'), ('J5', 'J6')):
        T(4, 'LED pads %s-%s' % (a, b), d(L, a, '1', b, '1'), 8)
    for fet, sh, j, u, rg, nt in (('M10', 'R52', 'J4', 'U11', 'R56', 'NT1'), ('M9', 'R53', 'J7', 'U12', 'R50', 'NT2'), ('M8', 'R7', 'J6', 'U6', 'R22', 'NT3')):
        T(5, '%s source -> %s' % (fet, sh), d(L, fet, '3', sh, '1'), 5)
        T(5, '%s drain -> %s' % (fet, j), d(L, fet, '2', j, '1'), 15)
        T(5, '%s IN- -> %s (net tie)' % (u, nt), d(L, u, '4', nt, '1'), 10)
        T(5, '%s OUT -> %s gate' % (u, fet), d(L, u, '1', fet, '1'), 10)
    return TARGETS


def mechanical(L, meta):
    msgs = []
    screws = dict(meta['screws'])
    for m in meta['screwed']:
        screws[m] = M.tab_hole(L, m)
    # washer keep-outs: no part area or pad within 3.75 mm of any screw, either side
    for s, (sx, sy) in screws.items():
        for ref in L:
            if ref == s:
                continue
            for side, r, kind in M.areas(L, ref):
                if kind == 'body' and ref in M.FETS and side == 'B':
                    continue          # FET bodies sit under the board: the screw passes beside the tab only
                if M.rect_circle_dist(r, sx, sy) < 3.75:
                    msgs.append('washer keep-out %s: %s %s (%.2f mm)' % (s, ref, kind, M.rect_circle_dist(r, sx, sy)))
    # tall parts over screws (screwdriver path): anything taller than 3 mm within 5 mm
    for s, (sx, sy) in screws.items():
        for ref, h in M.HEIGHT.items():
            if ref in L and h > 3:
                for side, r, kind in M.areas(L, ref):
                    if side == 'F' and M.rect_circle_dist(r, sx, sy) < 5.0:
                        msgs.append('screwdriver path %s blocked by %s (h %.1f)' % (s, ref, h))
    # 15 mm rule
    for m in M.FETS:
        if m in meta['screwed'] or m not in L:
            continue
        bx, by = M.body_centre(L, m)
        dn = min(math.hypot(bx - x, by - y) for x, y in screws.values())
        far = meta.get('far_mm', 15.0)
        if dn > far:
            msgs.append('%g mm rule: %s body centre %.1f mm from nearest screw' % (far, m, dn))
    # overlaps per side
    items = [(ref, side, r, kind) for ref in L for side, r, kind in M.areas(L, ref)]
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if a[0] != b[0] and a[1] == b[1] and M.overlap(a[2], b[2]):
                if a[3] == 'pins' and b[3] == 'pins' and a[0] in M.FETS and b[0] in M.FETS:
                    pass
                msgs.append('overlap %s: %s(%s) x %s(%s)' % (a[1], a[0], a[3], b[0], b[3]))
    for ref, side, r, kind in items:
        if not M.in_board(r):
            msgs.append('outside board / in notch: %s %s' % (ref, kind))
    # card: tall parts under it
    cl = meta['card']
    for ref, h in M.HEIGHT.items():
        if ref in L:
            lim = M.CARD_GAP - (M.CAN_VENT_CLEAR if ref.startswith('C') else 1.0)
            for side, r, kind in M.areas(L, ref):
                if side == 'F' and M.overlap(r, cl, 1.0) and (h > lim or ref == 'L1'):
                    msgs.append('under card: %s h %.1f > %.1f' % (ref, h, lim))
    co = meta['corner']
    for ref in list(L):
        if ref == 'L1' or M.HEIGHT.get(ref, 0) > 16:
            for side, r, kind in M.areas(L, ref):
                if side == 'F' and M.overlap(r, co):
                    msgs.append('corner zone: %s' % ref)
    if M.overlap(cl, co):
        msgs.append('corner zone: control card')
    return msgs, screws
