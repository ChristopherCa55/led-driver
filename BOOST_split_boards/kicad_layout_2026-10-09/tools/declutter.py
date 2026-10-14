"""Text clean-up pass on a written KiCad schematic (connectivity is not touched). Text sizes are measured, not
estimated: kicad-cli's SVG export draws every text as a stroked group (svgtext.py).
  - a global label may turn to another free side of its point (labels connect only at their point),
  - comment texts and Reference/Value fields may shift by up to 2.54 mm,
each only when that lowers its collision count (texts, wires, symbol outlines and pin lines, other texts including
pin numbers). Rewrites the file in place.

    python declutter.py SCH.kicad_sch            moves, rewrites
    python declutter.py SCH.kicad_sch --report   only lists the collisions left
"""
import sys, uuid
from collections import Counter
from sexpr import parse, dump, find, findall, unq
import kgeo
import overlaps as O
import svgtext

DIRS = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}       # label angle -> direction it extends
JUST = {0: 'left', 90: 'left', 180: 'right', 270: 'right'}
STEPS = [0, 0.635, -0.635, 1.27, -1.27, 1.905, -1.905, 2.54, -2.54]
LABEL_PAD = 0.45    # label outline around its text (KiCad: labels on a 2.54 mm pitch just clear each other)
GAP = 0.25          # clearance wanted between a text and wires / outlines
TEXT_GAP = (1.0, 0.4)   # between two texts side by side / stacked (closer and two words read as one: 'C79C84')


def r3(p):
    return (round(p[0], 3), round(p[1], 3))


def grow(b, d):
    return (b[0] - d, b[1] - d, b[2] + d, b[3] + d)


def shift(b, dx, dy):
    return (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)


def dist(p, b):
    dx = max(b[0] - p[0], 0, p[0] - b[2])
    dy = max(b[1] - p[1], 0, p[1] - b[3])
    return (dx * dx + dy * dy) ** 0.5


def union(bs):
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def label_box(x, y, ang, L, T):
    """label outline: length L from the point in its direction, thickness T"""
    h = T / 2
    return {0: (x, y - h, x + L, y + h), 180: (x - L, y - h, x, y + h),
            90: (x - h, y - L, x + h, y), 270: (x - h, y, x + h, y + L)}[ang]


def load(path):
    root = parse(open(path, encoding='utf-8').read())
    _, wires, bodies = O.collect(root)
    svg = svgtext.export_svg(path)
    pool = list(dict.fromkeys(svgtext.text_boxes(svg)))          # (text, box), duplicates dropped
    used_box = set()
    items = []
    for g in findall(root, 'global_label'):
        at = find(g, 'at')
        items.append({'kind': 'label', 'node': g, 'lines': [unq(g[1])], 'x': float(at[1]), 'y': float(at[2]),
                      'ang': int(float(at[3]))})
    for t in findall(root, 'text'):
        at = find(t, 'at')
        txt = t[1][1:-1].replace(chr(92) + '"', '"')        # raw text: unq() would drop the \ of a line break
        items.append({'kind': 'text', 'node': t, 'lines': [l for l in txt.split(chr(92) + 'n') if l.strip()],
                      'x': float(at[1]), 'y': float(at[2])})
    for s in findall(root, 'symbol'):
        i = kgeo.inst_info(s)
        if i['ref'].startswith('#'):
            continue
        for p in findall(s, 'property'):
            if unq(p[1]) not in ('Reference', 'Value'):
                continue
            if O.effects(p)[3]:
                continue
            at = find(p, 'at')
            shown = unq(p[2])
            if unq(p[1]) == 'Reference' and i['unit'] > 1 or unq(p[1]) == 'Reference' and \
                    any(unq(q[1]) == 'Reference' for q in []):
                pass
            items.append({'kind': 'field', 'node': p, 'lines': [shown], 'x': float(at[1]), 'y': float(at[2]),
                          'ref': i['ref'], 'unit': i['unit']})
    # match each item's lines to measured boxes (same text, nearest the item's point)
    by_text = {}
    for k, (t, b) in enumerate(pool):
        by_text.setdefault(t.strip(), []).append(k)
    for it in items:
        boxes = []
        for ln in it['lines']:
            cands = [k for k in by_text.get(ln.strip(), []) if k not in used_box]
            if it['kind'] == 'field' and not cands:
                # multi-unit references are drawn with the unit letter (U26A); values as is
                cands = [k for t, ks in by_text.items() if t.startswith(ln) and len(t) == len(ln) + 1
                         for k in ks if k not in used_box]
            if not cands:
                continue
            k = min(cands, key=lambda k: dist((it['x'], it['y']), pool[k][1]))
            if dist((it['x'], it['y']), pool[k][1]) > 30:
                continue
            used_box.add(k)
            boxes.append(pool[k][1])
        it['box'] = union(boxes) if boxes else None
        if it['kind'] == 'label' and it['box']:
            b = grow(it['box'], LABEL_PAD)
            b = union([b, (it['x'], it['y'], it['x'], it['y'])])   # reaches back to its point
            tip = 0.8                                              # the outline's arrow / end beyond the text
            b = {0: (b[0], b[1], b[2] + tip, b[3]), 180: (b[0] - tip, b[1], b[2], b[3]),
                 90: (b[0], b[1] - tip, b[2], b[3]), 270: (b[0], b[1], b[2], b[3] + tip)}[it['ang']]
            it['box'] = b
            horiz = it['ang'] in (0, 180)
            it['L'] = (b[2] - b[0]) if horiz else (b[3] - b[1])
            it['T'] = (b[3] - b[1]) if horiz else (b[2] - b[0])
    items = [it for it in items if it['box']]
    static = [b for k, (t, b) in enumerate(pool) if k not in used_box]          # pin numbers / names etc.
    return root, items, static, wires, bodies


def make_cost(items, static, wires, bodies):
    segs = [((w[0], w[1]), (w[2], w[3])) for w in wires]

    def cost(it, bx, detail=False):
        hits = []
        g = grow(bx, GAP)
        for other in items:
            if other is it:
                continue
            both_labels = it['kind'] == other['kind'] == 'label'     # stacked labels may share an edge
            tg = (bx[0] - TEXT_GAP[0], bx[1] - TEXT_GAP[1], bx[2] + TEXT_GAP[0], bx[3] + TEXT_GAP[1])
            if O.hit(bx, other['box'], 0.15) if both_labels else O.hit(tg, other['box'], 0):
                hits.append(('text', other['lines'][0]))
        for b in static:
            if O.hit(g, b, 0):
                hits.append(('pin text', ''))
        for a, b in segs:
            if O.seg_hits(bx, (a, b), -GAP if it['kind'] != 'label' else 0.15):
                if it['kind'] == 'label' and (r3(a) == r3((it['x'], it['y'])) or r3(b) == r3((it['x'], it['y']))):
                    continue
                hits.append(('wire', ''))
        for owner, sg, areas in bodies:
            pad = 0.3 if it['kind'] == 'label' and owner.startswith('#GND') else 0.05   # side by side at a pin row
            if any(O.hit(bx, ar, pad) for ar in areas) or any(O.seg_hits(bx, s, pad) for s in sg):
                if it['kind'] == 'label' and any(r3(s[0]) == r3((it['x'], it['y'])) or
                                                 r3(s[1]) == r3((it['x'], it['y'])) for s in sg) and \
                        not any(O.hit(g, ar, 0) for ar in areas):
                    continue                     # label on a pin end: the pin line touches its point only
                hits.append(('body', owner))
        return hits if detail else len(hits)
    return cost


def free_dirs(it, wires, bodies, p=None):
    p = r3((it['x'], it['y']) if p is None else p)
    busy = set()
    segs = [((w[0], w[1]), (w[2], w[3])) for w in wires]
    for owner, sg, areas in bodies:
        segs += sg
    for a, b in segs:
        a, b = r3(a), r3(b)
        d = ((b[0] > a[0]) - (b[0] < a[0]), (b[1] > a[1]) - (b[1] < a[1]))
        if p == a:
            busy.add(d)
        elif p == b:
            busy.add((-d[0], -d[1]))
        elif (a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1])) or \
                (a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0])):
            busy |= {d, (-d[0], -d[1])}
    return [a for a, d in DIRS.items() if d not in busy]


def on_seg(p, a, b, ends=True):
    if ends and (r3(p) == r3(a) or r3(p) == r3(b)):
        return True
    vert = abs(a[0] - b[0]) < 1e-6 and abs(p[0] - a[0]) < 1e-6 and min(a[1], b[1]) < p[1] < max(a[1], b[1])
    horiz = abs(a[1] - b[1]) < 1e-6 and abs(p[1] - a[1]) < 1e-6 and min(a[0], b[0]) < p[0] < max(a[0], b[0])
    return vert or horiz


def label_spots(p, wires, step=1.27):
    """points on the label's own wire(s) where it could sit instead (still on the same wire: same net)"""
    out = [p]
    ends = sum(1 for w in wires if r3(p) in (r3((w[0], w[1])), r3((w[2], w[3]))))
    inner = any(on_seg(p, (w[0], w[1]), (w[2], w[3]), ends=False) for w in wires)
    if ends == 1 and not inner:
        return out                         # the label closes an open wire end: moving it would leave the end loose
    for w in wires:
        a, b = (w[0], w[1]), (w[2], w[3])
        if not on_seg(p, a, b):
            continue
        n = int(round((abs(b[0] - a[0]) + abs(b[1] - a[1])) / step))
        for k in range(n + 1):
            t = k / n if n else 0
            q = (round(a[0] + (b[0] - a[0]) * t, 4), round(a[1] + (b[1] - a[1]) * t, 4))
            if r3(q) not in {r3(o) for o in out}:
                out.append(q)
    return out


def all_points(wires, bodies):
    pts = set()
    for w in wires:
        pts |= {r3((w[0], w[1])), r3((w[2], w[3]))}
    for owner, sg, areas in bodies:
        for a, b in sg:
            pts |= {r3(a), r3(b)}
    return pts


def stub_blocked(q, e, wires, bodies, pts):
    """a stub q -> e must touch nothing but its own wire at q"""
    for p in pts:
        if p != r3(q) and on_seg(p, q, e):
            return True
    for w in wires:
        a, b = (w[0], w[1]), (w[2], w[3])
        if on_seg(q, a, b):
            if on_seg(e, a, b) or on_seg(a, q, e, False) or on_seg(b, q, e, False):
                return True                       # runs along its own wire
            continue
        # crossing: one vertical, one horizontal
        for (h1, h2), (v1, v2) in (((q, e), (a, b)), ((a, b), (q, e))):
            if abs(h1[1] - h2[1]) < 1e-6 and abs(v1[0] - v2[0]) < 1e-6:
                x, y = v1[0], h1[1]
                if min(h1[0], h2[0]) <= x <= max(h1[0], h2[0]) and min(v1[1], v2[1]) <= y <= max(v1[1], v2[1]):
                    return True
    d = (e[0] - q[0], e[1] - q[1])
    L = abs(d[0]) + abs(d[1])
    q2 = (q[0] + d[0] * 0.1 / L, q[1] + d[1] * 0.1 / L)
    bx = (min(q2[0], e[0]) - 0.05, min(q2[1], e[1]) - 0.05, max(q2[0], e[0]) + 0.05, max(q2[1], e[1]) + 0.05)
    for owner, sg, areas in bodies:
        if any(O.hit(bx, ar, 0) for ar in areas) or any(O.seg_hits(bx, s, 0) for s in sg):
            return True
    return False


def nid():
    return '"%s"' % uuid.uuid4()


def wire_node(a, b):
    return ['wire', ['pts', ['xy', fmt(a[0]), fmt(a[1])], ['xy', fmt(b[0]), fmt(b[1])]],
            ['stroke', ['width', '0'], ['type', 'default']], ['uuid', nid()]]


def add_stub(root, wires, q, e):
    """new wire q -> e; a wire passing through q is split there; a junction where 3 or more meet"""
    for k, node in enumerate(root):
        if not (isinstance(node, list) and node and node[0] == 'wire'):
            continue
        xy = findall(find(node, 'pts'), 'xy')
        a, b = (float(xy[0][1]), float(xy[0][2])), (float(xy[1][1]), float(xy[1][2]))
        if on_seg(q, a, b, ends=False):
            root[k:k + 1] = [wire_node(a, q), wire_node(q, b)]
            wires[:] = [w for w in wires if not (r3((w[0], w[1])) == r3(a) and r3((w[2], w[3])) == r3(b))]
            wires += [(a[0], a[1], q[0], q[1]), (q[0], q[1], b[0], b[1])]
            break
    root.append(wire_node(q, e))
    wires.append((q[0], q[1], e[0], e[1]))
    deg = sum(1 for w in wires if r3(q) in (r3((w[0], w[1])), r3((w[2], w[3]))))
    have = any(isinstance(n, list) and n and n[0] == 'junction' and r3((float(find(n, 'at')[1]), float(find(n, 'at')[2]))) == r3(q)
               for n in root)
    if deg >= 3 and not have:
        root.append(['junction', ['at', fmt(q[0]), fmt(q[1])], ['diameter', '0'], ['color', '0', '0', '0', '0'],
                     ['uuid', nid()]])


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def run(path, report_only=False):
    root, items, static, wires, bodies = load(path)
    cost = make_cost(items, static, wires, bodies)
    moved = 0
    for _ in range(0 if report_only else 4):
        changed = False
        for it in sorted(items, key=lambda it: -cost(it, it['box'])):
            c0 = cost(it, it['box'])
            if c0 == 0 or it.get('stubbed'):
                continue                                   # a label on its own new stub stays there
            best = (c0, 0, None)
            if it['kind'] == 'label':
                p = (it['x'], it['y'])
                spots = label_spots(p, wires)
                for q in spots:                            # turn, or slide along its own wire
                    for ang in free_dirs(it, wires, bodies, q):
                        if r3(q) == r3(p) and ang == it['ang']:
                            continue
                        bx = label_box(q[0], q[1], ang, it['L'], it['T'])
                        c = cost(it, bx)
                        pen = (abs(q[0] - p[0]) + abs(q[1] - p[1])) / 10
                        if c < best[0] or (c == best[0] and best[2] and pen < best[1]):
                            best = (c, pen, ('lab', q, ang, None, bx))
                if best[0] > 0:                            # a short stub off the wire, the label on its end
                    pts = all_points(wires, bodies) | {r3((o['x'], o['y'])) for o in items if o['kind'] == 'label'}
                    for q in spots:
                        for a1 in free_dirs(it, wires, bodies, q):
                            d1 = DIRS[a1]
                            e = (q[0] + 2.54 * d1[0], q[1] + 2.54 * d1[1])
                            if r3(e) in pts or stub_blocked(q, e, wires, bodies, pts):
                                continue
                            for ang, d2 in DIRS.items():
                                if d2 == (-d1[0], -d1[1]):
                                    continue
                                bx = label_box(e[0], e[1], ang, it['L'], it['T'])
                                c = cost(it, bx)
                                pen = 1 + (abs(q[0] - p[0]) + abs(q[1] - p[1])) / 10
                                if c < best[0] or (c == best[0] and best[2] and pen < best[1]):
                                    best = (c, pen, ('lab', e, ang, (q, e), bx))
            else:
                for dx in STEPS:
                    for dy in STEPS:
                        if dx == dy == 0:
                            continue
                        bx = shift(it['box'], dx, dy)
                        c = cost(it, bx)
                        pen = abs(dx) + abs(dy)
                        if c < best[0] or (c == best[0] and best[2] and pen < best[1]):
                            best = (c, pen, ('xy', dx, dy, bx))
            if best[2] is None:
                continue
            at = find(it['node'], 'at')
            if best[2][0] == 'lab':
                _, q, ang, stub, bx = best[2]
                if stub:
                    add_stub(root, wires, stub[0], stub[1])
                    it['stubbed'] = True
                it['x'], it['y'], it['ang'] = q[0], q[1], ang
                at[1], at[2], at[3] = fmt(q[0]), fmt(q[1]), str(ang)
                j = find(find(it['node'], 'effects'), 'justify')
                j[1:] = [JUST[it['ang']]]
                for prop in findall(it['node'], 'property'):
                    find(prop, 'at')[1:3] = [fmt(q[0]), fmt(q[1])]
            else:
                it['x'] += best[2][1]
                it['y'] += best[2][2]
                at[1], at[2] = fmt(it['x']), fmt(it['y'])
            it['box'] = best[2][-1]
            moved += 1
            changed = True
        if not changed:
            break
    left = [(it, cost(it, it['box'], True)) for it in items if cost(it, it['box'])]
    if not report_only:
        open(path, 'w', encoding='utf-8', newline='\n').write(dump(root) + '\n')
    return moved, left


def show(left):
    print(Counter(h[0] for it, hs in left for h in hs))
    for it, hs in sorted(left, key=lambda v: (v[0]['y'], v[0]['x'])):
        print('%-5s %-26s at LT %-14s %s' % (it['kind'], it['lines'][0][:26], O.lt((it['x'], it['y'])),
                                            ', '.join('%s %s' % h for h in hs)[:90]))


if __name__ == '__main__':
    rep = '--report' in sys.argv
    moved, left = run(sys.argv[1], rep)
    if not rep:
        print('moved', moved)
    show(left)
