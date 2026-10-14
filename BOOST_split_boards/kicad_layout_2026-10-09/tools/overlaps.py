"""Estimated text collisions in a KiCad schematic: visible Reference/Value fields, global labels, text items and pin
numbers against each other, against wires and against symbol bodies. Sizes are estimates (KiCad stroke font: about
0.75 x size per character), so small overlaps are only hints; the renders confirm.

    python overlaps.py SCH.kicad_sch [--lt]      (--lt: print positions in LTspice units of the layout)
"""
import sys
from sexpr import parse, find, findall, unq
import kgeo

S, OX, OY = 0.079375, 629.92, 805.18
CH = 0.75          # character width / font size
PAD = 0.15         # mm kept clear


def text_box(x, y, txt, size, angle, hj, vj='center', lines=None):
    lines = txt.split('\n') if lines is None else lines
    w = max(len(l) for l in lines) * CH * size
    h = size * (1 + 1.6 * (len(lines) - 1))
    x1 = {'left': 0, 'right': -w}.get(hj, -w / 2)
    y1 = {'top': 0, 'bottom': -h}.get(vj, -h / 2)
    box = (x1, y1, x1 + w, y1 + h)
    if angle in (90, 270):
        # rotated text: reading upwards; its "left" is towards -y
        bx = (box[1], -box[2], box[3], -box[0])
        box = (bx[0], bx[1], bx[2], bx[3])
    return (x + box[0], y + box[1], x + box[2], y + box[3])


def hit(a, b, pad=PAD):
    return a[0] < b[2] - pad and b[0] < a[2] - pad and a[1] < b[3] - pad and b[1] < a[3] - pad


def seg_hits(box, sg, pad=0.2):
    """does segment sg ((x1, y1), (x2, y2)) pass through the box (shrunk by pad)?"""
    x1, y1, x2, y2 = box[0] + pad, box[1] + pad, box[2] - pad, box[3] - pad
    if x1 >= x2 or y1 >= y2:
        return False
    (ax, ay), (bx, by) = sg
    t0, t1 = 0.0, 1.0
    dx, dy = bx - ax, by - ay
    for p, q in ((-dx, ax - x1), (dx, x2 - ax), (-dy, ay - y1), (dy, y2 - ay)):
        if p == 0:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    return t0 <= t1


def seg_box(w):
    return (min(w[0], w[2]) - 0.01, min(w[1], w[3]) - 0.01, max(w[0], w[2]) + 0.01, max(w[1], w[3]) + 0.01)


def effects(node):
    eff = find(node, 'effects')
    size = float(find(find(eff, 'font'), 'size')[1]) if eff and find(eff, 'font') else 1.27
    j = find(eff, 'justify') if eff else None
    hj = next((v for v in (j or [])[1:] if v in ('left', 'right')), 'center')
    vj = next((v for v in (j or [])[1:] if v in ('top', 'bottom')), 'center')
    hidden = any(c == ['hide', 'yes'] for c in node if isinstance(c, list)) or \
        (eff and any(c == ['hide', 'yes'] or c == 'hide' for c in eff))
    return size, hj, vj, hidden


def collect(root):
    libs = {unq(s[1]): s for s in findall(find(root, 'lib_symbols'), 'symbol')}
    items = []        # (kind, owner, box, text)
    wires = []
    bodies = []       # (owner, box)
    for w in findall(root, 'wire'):
        xy = findall(find(w, 'pts'), 'xy')
        wires.append((float(xy[0][1]), float(xy[0][2]), float(xy[1][1]), float(xy[1][2])))
    for g in findall(root, 'global_label'):
        at = find(g, 'at')
        x, y, ang = float(at[1]), float(at[2]), int(float(at[3]))
        name = unq(g[1])
        L = len(name) * CH * 1.27 + 2.0
        hh = 1.3
        box = {0: (x, y - hh, x + L, y + hh), 180: (x - L, y - hh, x, y + hh),
               90: (x - hh, y - L, x + hh, y), 270: (x - hh, y, x + hh, y + L)}[ang]
        items.append(('label', name, box, name, (x, y)))
    for t in findall(root, 'text'):
        at = find(t, 'at')
        size, hj, vj, hidden = effects(t)
        txt = unq(t[1]).replace('\\n', '\n')
        items.append(('text', txt[:20], text_box(float(at[1]), float(at[2]), txt, size, int(float(at[3])), hj, vj),
                      txt, None))
    for s in findall(root, 'symbol'):
        i = kgeo.inst_info(s)
        lib = libs[i['lib']]
        if i['ref'].startswith('#') and 'GND' not in i['lib'] and 'PWR_FLAG' not in i['lib']:
            pass
        for p in findall(s, 'property'):
            name = unq(p[1])
            if name not in ('Reference', 'Value'):
                continue
            size, hj, vj, hidden = effects(p)
            if hidden or i['ref'].startswith('#'):
                continue
            at = find(p, 'at')
            ang = (int(float(at[3])) + i['ang']) % 180
            items.append((name, i['ref'], text_box(float(at[1]), float(at[2]), unq(p[2]), size, 90 if ang else 0,
                                                    hj, vj), unq(p[2]), None))
        # body: graphics of the unit as segments (rectangles also as filled areas), transformed; pin lines too
        segs, areas = [], []
        X = lambda px, py: (lambda d: (i['x'] + d[0], i['y'] + d[1]))(kgeo.xform(px, py, i['ang'], i['mirror']))
        for sub in findall(lib, 'symbol'):
            parts = unq(sub[1]).rsplit('_', 2)
            if int(parts[-2]) not in (0, i['unit']) or int(parts[-1]) not in (0, 1):
                continue
            for r in findall(sub, 'rectangle'):
                a0, b0 = find(r, 'start'), find(r, 'end')
                c = [X(float(a0[1]), float(a0[2])), X(float(b0[1]), float(b0[2]))]
                areas.append((min(c[0][0], c[1][0]), min(c[0][1], c[1][1]), max(c[0][0], c[1][0]),
                              max(c[0][1], c[1][1])))
            for pl in findall(sub, 'polyline'):
                q = [X(float(v[1]), float(v[2])) for v in findall(find(pl, 'pts'), 'xy')]
                segs += list(zip(q, q[1:]))
            for c in findall(sub, 'circle'):
                q = find(c, 'center')
                rad = float(find(c, 'radius')[1])
                m = X(float(q[1]), float(q[2]))
                areas.append((m[0] - rad, m[1] - rad, m[0] + rad, m[1] + rad))
            for pn in findall(sub, 'pin'):
                if any(cc == ['hide', 'yes'] for cc in pn if isinstance(cc, list)) or 'hide' in pn:
                    continue
                at = find(pn, 'at')
                ln = float(find(pn, 'length')[1])
                a = int(float(at[3]))
                dx, dy = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[a]
                px, py = float(at[1]), float(at[2])
                segs.append((X(px, py), X(px + ln * dx, py + ln * dy)))
        if not i['ref'].startswith('#') or i['ref'].startswith(('#GND', '#FLG')):
            bodies.append((i['ref'] + ('' if i['unit'] == 1 else chr(64 + i['unit'])), segs, areas))
    return items, wires, bodies


def check(path):
    root = parse(open(path, encoding='utf-8').read())
    items, wires, bodies = collect(root)
    out = []
    for n, a in enumerate(items):
        for b in items[n + 1:]:
            if hit(a[2], b[2]):
                out.append(('text/text', a, b))
        for w in wires:
            if hit(a[2], seg_box(w), 0.3):
                if a[0] == 'label' and a[4] and (a[4] in ((w[0], w[1]), (w[2], w[3])) or
                                                  (w[0] == w[2] == a[4][0]) or (w[1] == w[3] == a[4][1])):
                    # a label's own wire, or a wire running through its anchor along the label's axis
                    if (w[0] == w[2] and abs(a[2][0] - a[2][2]) < 3) or (w[1] == w[3] and abs(a[2][1] - a[2][3]) < 3):
                        if a[4] in ((w[0], w[1]), (w[2], w[3])) or not hit(a[2], seg_box(w), 1.0):
                            continue
                out.append(('text/wire', a, w))
                break
        for owner, segs, areas in bodies:
            if any(hit(a[2], ar, 0.3) for ar in areas) or any(seg_hits(a[2], sg) for sg in segs):
                out.append(('text/body', a, (owner, None)))
    return out


def lt(v):
    return round((v[0] - OX) / S), round((v[1] - OY) / S)


if __name__ == '__main__':
    res = check(sys.argv[1])
    from collections import Counter
    print(Counter(r[0] for r in res))
    for kind, a, b in res:
        where = lt(a[2][:2])
        other = b[3] if isinstance(b, tuple) and len(b) == 5 else (b[0] if isinstance(b[0], str) else 'wire')
        print('%-9s %-7s %-12s at LT %s  vs %s' % (kind, a[0], a[3][:24].replace('\n', '/'), where,
                                                 str(other)[:24].replace('\n', '/')))
