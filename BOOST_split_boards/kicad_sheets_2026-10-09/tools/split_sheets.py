"""Split the main schematic (the user's v3 layout) into the two board sheets (the user's choice, 2026-10-09).

    python split_sheets.py           BOOST_stuff/KiCad -> ../work/ (a copy; nothing shipped is touched)

BOOST.kicad_sch becomes the system root: two sheet symbols (power board, control card) and a short note; its uuid is
kept (BOOST.kicad_pro names it). BOOST_power_RC2.kicad_sch and BOOST_control_RC2.kicad_sch hold each board's parts
where they are in v3; each is also its board project's own schematic (KiCad 10 top_level_sheets).
  - parts go by the board assignment (the PCBs); GND symbols, PWR_FLAGs, labels, junctions and no-connect marks go
    with the wire they sit on,
  - a wire that joins parts of both boards is cut half way, on the grid; both cut ends get the net's global label
    (every net that crosses the boards already has its name through J10/J11, so no net is renamed),
  - notes go with the nearest part; section titles go to every board with parts under them,
  - each sheet's drawing is moved to the top-left corner and gets the smallest ANSI paper it fits.
"""
import os, sys, re, json, copy, uuid, shutil, collections, heapq
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(os.path.join(HERE, '..'))
SB = os.path.normpath(os.path.join(BASE, '..'))
sys.path.insert(0, os.path.join(SB, 'kicad_layout_2026-10-09', 'tools'))
from sexpr import parse, dump, find, findall, unq, q
import kgeo

SRC = os.path.normpath(os.path.join(SB, '..', 'BOOST_stuff', 'KiCad'))
WORK = os.path.join(BASE, 'work')
ASSIGN = os.path.join(SB, 'previous', '2026-09-30', 'precharge_record', 'tools', 'precharge',
                      'board_assignment_2026-09-29_precharge.json')
ROOT_UUID = 'dc4aa17e-0995-4bac-889e-471ae16ef44e'
BOARDS = [('POWER', 'BOOST_power_RC2', 'Power board'), ('CONTROL', 'BOOST_control_RC2', 'Control card')]
NS = uuid.UUID('5b0a1f2e-6c1d-4e8a-9a51-2f3d0c9b7a10')
G = 1.27
PAPERS = [('A', 279.4, 215.9), ('B', 431.8, 279.4), ('C', 558.8, 431.8), ('D', 863.6, 558.8), ('E', 1117.6, 863.6)]
SKIP = ('.history', '-backups', '.kicad_prl', '.lck')


def uid(name):
    return str(uuid.uuid5(NS, name))


def P(x, y):
    return (round(float(x), 3), round(float(y), 3))


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def snap(v):
    return round(round(v / G) * G, 3)


def on_int(p, a, b):
    return (a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1])) or \
        (a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]))


class UF:
    def __init__(self):
        self.p = {}

    def f(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


def label_node(name, p, d):
    ang, j = {(1, 0): (0, 'left'), (0, -1): (90, 'left'), (-1, 0): (180, 'right'), (0, 1): (270, 'right')}[d]
    X, Y = fmt(p[0]), fmt(p[1])
    return ['global_label', q(name), ['shape', 'passive'], ['at', X, Y, str(ang)], ['fields_autoplaced', 'yes'],
            ['effects', ['font', ['size', '1.27', '1.27']], ['justify', j]], ['uuid', q(str(uuid.uuid4()))],
            ['property', '"Intersheetrefs"', '"${INTERSHEET_REFS}"', ['at', X, Y, '0'], ['hide', 'yes'],
             ['show_name', 'no'], ['do_not_autoplace', 'no'], ['effects', ['font', ['size', '1.27', '1.27']]]]]


def wire_node(a, b):
    return ['wire', ['pts', ['xy', fmt(a[0]), fmt(a[1])], ['xy', fmt(b[0]), fmt(b[1])]],
            ['stroke', ['width', '0'], ['type', 'default']], ['uuid', q(str(uuid.uuid4()))]]


def text_center(t):
    at = find(t, 'at')
    x, y = float(at[1]), float(at[2])
    eff = find(t, 'effects')
    size = float(find(find(eff, 'font'), 'size')[1])
    lines = t[1][1:-1].split(chr(92) + 'n')
    w = max(len(l) for l in lines) * 0.78 * size
    j = find(eff, 'justify')
    hj = next((v for v in (j or [])[1:] if v in ('left', 'right')), 'center')
    cx = x + w / 2 if hj == 'left' else x - w / 2 if hj == 'right' else x
    return (cx, y), size


def main():
    if os.path.exists(WORK):
        raise SystemExit('%s exists: remove it first (it is a generated copy)' % WORK)
    shutil.copytree(SRC, WORK, ignore=lambda d, names: [n for n in names if any(s in n for s in SKIP)])
    A = json.load(open(ASSIGN))
    root = parse(open(os.path.join(SRC, 'BOOST.kicad_sch'), encoding='utf-8').read())
    assert unq(find(root, 'uuid')[1]) == ROOT_UUID
    libs = {unq(s[1]): s for s in findall(find(root, 'lib_symbols'), 'symbol')}

    # ---------------------------------------------------------------- items
    syms, pins = [], []                 # pins: (point, ref, real?)
    for s in findall(root, 'symbol'):
        i, pts = kgeo.pin_points(s, libs)
        syms.append((s, i, [P(x, y) for n, nm, x, y, h in pts]))
        for n, nm, x, y, h in pts:
            pins.append((P(x, y), i['ref'], not i['ref'].startswith('#')))
    wires = []
    for w in findall(root, 'wire'):
        xy = findall(find(w, 'pts'), 'xy')
        wires.append((P(xy[0][1], xy[0][2]), P(xy[1][1], xy[1][2]), w))
    juncs = [(P(find(j, 'at')[1], find(j, 'at')[2]), j) for j in findall(root, 'junction')]
    ncs = [(P(find(j, 'at')[1], find(j, 'at')[2]), j) for j in findall(root, 'no_connect')]
    labels = [(P(find(g, 'at')[1], find(g, 'at')[2]), g) for g in findall(root, 'global_label')]
    texts = findall(root, 'text')
    others = [c for c in root if isinstance(c, list) and c[0] not in (
        'version', 'generator', 'generator_version', 'uuid', 'paper', 'lib_symbols', 'symbol', 'wire', 'junction',
        'no_connect', 'global_label', 'text', 'sheet_instances', 'embedded_fonts', 'title_block')]
    assert not others, set(c[0] for c in others)

    # ---------------------------------------------------------------- wire islands (wires joined at ends / T points)
    uf = UF()
    pts = {a for a, b, w in wires} | {b for a, b, w in wires} | {p for p, r, real in pins} | \
          {p for p, j in juncs} | {p for p, g in labels}
    for a, b, w in wires:
        uf.u(a, b)
    for a, b, w in wires:
        for p in pts:
            if on_int(p, a, b):
                uf.u(p, a)
    sym_board = {}
    for s, i, pp in syms:
        if not i['ref'].startswith('#'):
            sym_board[id(s)] = A[i['ref']]
    isl_boards = collections.defaultdict(set)
    for s, i, pp in syms:
        if not i['ref'].startswith('#'):
            for p in pp:
                isl_boards[uf.f(p)].add(A[i['ref']])
    # net names of the shipped netlist, by island (any real pin on it)
    import knet
    net = os.path.join(BASE, 'ref.xml')
    if not os.path.exists(net):
        raise SystemExit('export the shipped netlist first: kicad-cli sch export netlist --format kicadxml -o ref.xml')
    comps, nets = knet.read(net)
    pin_net = {(r, p): n for n, v in nets.items() for r, p, f, t in v}
    real_pins = collections.defaultdict(list)
    for s, i, pp in syms:
        if i['ref'].startswith('#'):
            continue
        lib = libs[i['lib']]
        for (num, nm, x, y, h) in kgeo.pin_points(s, libs)[1]:
            real_pins[uf.f(P(x, y))].append((i['ref'], num))
    real_xy = [(P(x, y), A[i['ref']]) for s, i, pp in syms if not i['ref'].startswith('#')
               for (x, y) in pp + [(i['x'], i['y'])]]

    def nearest_board(p):
        return min(real_xy, key=lambda v: (v[0][0] - p[0]) ** 2 + (v[0][1] - p[1]) ** 2)[1]

    def island_board(p):
        bs = isl_boards.get(uf.f(p))
        if bs and len(bs) == 1:
            return next(iter(bs))
        return None

    # ---------------------------------------------------------------- cut the islands that hold parts of both boards
    point_board = {}
    out_wires = {b: [] for b, f, t in BOARDS}
    out_labels = {b: [] for b, f, t in BOARDS}
    cuts = []
    mixed = {k for k, v in isl_boards.items() if len(v) > 1}
    busy = {p for p, r, real in pins} | {p for p, g in labels} | {p for p, j in ncs}
    for k in mixed:
        iw = [(a, b, w) for a, b, w in wires if uf.f(a) == k]
        ipts = {p for p in pts if uf.f(p) == k}
        segs = []
        for a, b, w in iw:
            inner = sorted([p for p in ipts if on_int(p, a, b)] + [a, b])
            segs += list(zip(inner, inner[1:]))
        adj = collections.defaultdict(list)
        for a, b in segs:
            L = abs(a[0] - b[0]) + abs(a[1] - b[1])
            adj[a].append((b, L))
            adj[b].append((a, L))
        dist, own, heap = {}, {}, []
        for p, ref, real in pins:
            if real and uf.f(p) == k:
                dist[p], own[p] = 0, A[ref]
                heapq.heappush(heap, (0, p))
        while heap:
            d, p = heapq.heappop(heap)
            if d > dist[p]:
                continue
            for o, L in adj[p]:
                if d + L < dist.get(o, 1e9):
                    dist[o], own[o] = d + L, own[p]
                    heapq.heappush(heap, (d + L, o))
        names = {pin_net[rp] for rp in real_pins[k] if rp in pin_net}
        assert len(names) == 1, names
        name = names.pop()
        assert not name.startswith(('Net-(', 'unconnected-')), name
        point_board.update({p: own[p] for p in ipts if p in own})
        for a, b in segs:
            ba, bb = own[a], own[b]
            if ba == bb:
                out_wires[ba].append((a, b))
                continue
            L = abs(a[0] - b[0]) + abs(a[1] - b[1])
            d = ((b[0] > a[0]) - (b[0] < a[0]), (b[1] > a[1]) - (b[1] < a[1]))
            m = a
            if L >= 2 * G - 1e-6:
                # half way, on the grid, on no other wire and no pin (a label there would join that net)
                half = snap(L / 2)
                for t in sorted({snap(half + G * s) for s in range(-40, 41)}, key=lambda t: abs(t - half)):
                    if not 0 < t < L - 1e-6:
                        continue
                    c = (round(a[0] + d[0] * t, 3), round(a[1] + d[1] * t, 3))
                    if c in busy or any(uf.f(wa) != k and (c in (wa, wb) or on_int(c, wa, wb)) for wa, wb, ww in wires):
                        continue
                    m = c
                    break
            if m != a:
                out_wires[ba].append((a, m))
            if m != b:
                out_wires[bb].append((m, b))
            out_labels[ba].append((name, m, d))                  # points into the part that went to the other sheet
            out_labels[bb].append((name, m, (-d[0], -d[1])))
            cuts.append((name, m, ba, bb))

    def board_of(p):
        if p in point_board:
            return point_board[p]
        b = island_board(p)
        return b or nearest_board(p)

    for a, b, w in wires:
        if uf.f(a) in mixed:
            continue
        bd = board_of(a)
        out_wires[bd].append((a, b, w))

    # ---------------------------------------------------------------- texts: notes to the nearest part, titles to every board under them
    titles = [t for t in texts if text_center(t)[1] >= 1.9 or any(c == ['bold', 'yes'] for c in find(t, 'effects')[1])]
    tc = {id(t): text_center(t)[0] for t in texts}
    text_boards = collections.defaultdict(set)
    votes = collections.defaultdict(collections.Counter)
    for s, i, pp in syms:
        if i['ref'].startswith('#') or not titles:
            continue
        o = (i['x'], i['y'])
        t = min(titles, key=lambda t: (tc[id(t)][0] - o[0]) ** 2 + (tc[id(t)][1] - o[1]) ** 2)
        if ((tc[id(t)][0] - o[0]) ** 2 + (tc[id(t)][1] - o[1]) ** 2) ** 0.5 < 120:
            votes[id(t)][A[i['ref']]] += 1
    def tbox(t):
        (cx, cy), size = text_center(t)
        lines = t[1][1:-1].split(chr(92) + 'n')
        w, h = max(len(l) for l in lines) * 0.78 * size, size * 1.6 * len(lines)
        return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

    def box_dist(p, b):
        dx, dy = max(b[0] - p[0], 0, p[0] - b[2]), max(b[1] - p[1], 0, p[1] - b[3])
        return (dx * dx + dy * dy) ** 0.5

    for t in texts:
        b = tbox(t)
        near = {}
        for p, bd in real_xy:
            d = box_dist(p, b)
            near[bd] = min(near.get(bd, 1e9), d)
        if t in titles and votes[id(t)]:
            # a title goes to every board with parts under it (2+ parts nearest to it, one within 55 mm)
            text_boards[id(t)] = {bd for bd, n in votes[id(t)].items() if n >= 2 and near[bd] <= 55} or \
                {min(near, key=near.get)}
        else:
            text_boards[id(t)] = {min(near, key=near.get)}       # a note goes with the part nearest to its text

    # ---------------------------------------------------------------- sheets
    sheet_info = {}
    for bd, fname, title in BOARDS:
        file_uuid = uid(fname + ' sheet file')
        sheet_uuid = uid(fname + ' sheet symbol')
        sheet_info[bd] = {'file': fname + '.kicad_sch', 'uuid': file_uuid, 'sheet_uuid': sheet_uuid, 'title': title}
        items = []
        for wv in out_wires[bd]:
            items.append(wv[2] if len(wv) == 3 else wire_node(wv[0], wv[1]))
        for p, g in labels:
            if board_of(p) == bd:
                items.append(g)
        for name, m, d in out_labels[bd]:
            items.append(label_node(name, m, d))
        for p, n in ncs:
            if board_of(p) == bd:
                items.append(n)
        # junctions that still join 3 or more on this sheet
        ws = [wv[:2] for wv in out_wires[bd]]
        my_pins = set()
        for s, i, pp in syms:
            b = sym_board.get(id(s)) or board_of(pp[0] if pp else (i['x'], i['y']))
            if b == bd:
                my_pins |= set(pp)
        for p, j in juncs:
            if board_of(p) != bd:
                continue
            deg = sum((p in (a, b)) + 2 * on_int(p, a, b) for a, b in ws) + (p in my_pins)
            if deg >= 3:
                items.append(j)
        for t in texts:
            if bd in text_boards[id(t)]:
                if len(text_boards[id(t)]) > 1 and bd == 'CONTROL':     # a title on both sheets: own uuid here
                    t = copy.deepcopy(t)
                    find(t, 'uuid')[1] = q(uid('title copy ' + unq(find(t, 'uuid')[1])))
                items.append(t)
        used_libs = set()
        for s, i, pp in syms:
            b = sym_board.get(id(s)) or board_of(pp[0] if pp else (i['x'], i['y']))
            if b != bd:
                continue
            s2 = s
            inst = find(s2, 'instances')
            proj = find(inst, 'project')
            path = find(proj, 'path')
            ref_unit = [c for c in path if isinstance(c, list)]
            inst[:] = ['instances',
                       ['project', '"BOOST"', ['path', q('/%s/%s' % (ROOT_UUID, sheet_uuid))] + copy.deepcopy(ref_unit)],
                       ['project', q(fname), ['path', q('/%s' % file_uuid)] + copy.deepcopy(ref_unit)]]
            items.append(s2)
            used_libs.add(i['lib'])
        sheet_info[bd]['items'] = items
        sheet_info[bd]['libs'] = used_libs

    # ---------------------------------------------------------------- move each drawing to the corner, pick the paper
    for bd, fname, title in BOARDS:
        si = sheet_info[bd]
        xs, ys = [], []

        def walk(n):
            if isinstance(n, list) and n:
                if n[0] in ('at', 'xy') and len(n) >= 3:
                    try:
                        xs.append(float(n[1]))
                        ys.append(float(n[2]))
                    except ValueError:
                        pass
                for c in n[1:]:
                    walk(c)
        for it in si['items']:
            walk(it)
        # your v3 positions and paper, unless the drawing fits a smaller sheet (then it moves to the top-left corner)
        main_paper = unq(find(root, 'paper')[1])
        main_w = next(W for n, W, H in PAPERS if n == main_paper)
        w, h = max(xs) - min(xs) + 30, max(ys) - min(ys) + 30       # room for bodies / text beyond the anchors
        paper = next((n for n, W, H in PAPERS if W < main_w and w + 50.8 <= W and h + 50.8 + 30 <= H), main_paper)
        if paper == main_paper:
            dx = dy = 0
        else:
            dx, dy = snap(25.4 + 15 - min(xs)), snap(25.4 + 15 - min(ys))

        def shift(n):
            if isinstance(n, list) and n:
                if n[0] in ('at', 'xy') and len(n) >= 3:
                    n[1] = fmt(float(n[1]) + dx)
                    n[2] = fmt(float(n[2]) + dy)
                    return
                for c in n[1:]:
                    shift(c)
        for it in si['items']:
            shift(it)
        si['paper'] = paper
        si['shift'] = (dx, dy)

    # ---------------------------------------------------------------- write the sheets
    head = [c for c in root if isinstance(c, list) and c[0] in ('version', 'generator', 'generator_version')]
    for bd, fname, title in BOARDS:
        si = sheet_info[bd]
        lib_symbols = ['lib_symbols'] + [libs[n] for n in sorted(si['libs'])]
        out = ['kicad_sch'] + copy.deepcopy(head) + [
            ['uuid', q(si['uuid'])], ['paper', q(si['paper'])],
            ['title_block', ['title', q('BOOST LED driver - %s' % title)], ['rev', '"RC2"'],
             ['comment', '1', q('Nets to the other board: the global label of the same name (through J10 / J11)')]],
            lib_symbols]
        order = ('junction', 'no_connect', 'wire', 'global_label', 'text', 'symbol')
        for kind in order:
            out += [it for it in si['items'] if it[0] == kind]
        out += [['sheet_instances', ['path', '"/"', ['page', '"1"']]], ['embedded_fonts', 'no']]
        open(os.path.join(WORK, si['file']), 'w', encoding='utf-8', newline='\n').write(dump(out) + '\n')
        print('%-24s paper %s, moved by %s mm, %d items' % (si['file'], si['paper'], si['shift'], len(si['items'])))

    # ---------------------------------------------------------------- the root
    rt = ['kicad_sch'] + copy.deepcopy(head) + [['uuid', q(ROOT_UUID)], ['paper', '"A4"'],
          ['title_block', ['title', '"BOOST LED driver"'], ['rev', '"RC2"']], ['lib_symbols']]
    for k, (bd, fname, title) in enumerate(BOARDS):
        si = sheet_info[bd]
        x = 30.48 + k * 120.65
        rt.append(['sheet', ['at', fmt(x), '60.96'], ['size', '101.6', '63.5'], ['exclude_from_sim', 'no'],
                   ['in_bom', 'yes'], ['on_board', 'yes'], ['dnp', 'no'], ['stroke', ['width', '0.254'], ['type', 'solid']],
                   ['fill', ['color', '0', '0', '0', '0.0000']], ['uuid', q(si['sheet_uuid'])],
                   ['property', '"Sheetname"', q(title), ['at', fmt(x), '60.26', '0'],
                    ['effects', ['font', ['size', '2.54', '2.54']], ['justify', 'left', 'bottom']]],
                   ['property', '"Sheetfile"', q(si['file']), ['at', fmt(x), '125.06', '0'],
                    ['effects', ['font', ['size', '1.524', '1.524']], ['justify', 'left', 'top']]],
                   ['instances', ['project', '"BOOST"', ['path', q('/' + ROOT_UUID), ['page', q(str(k + 2))]]]]])
    notes = ['BOOST LED driver: the two boards',
             'Each board project (BOOST_power_RC2 / BOOST_control_RC2) opens its own sheet as its schematic.',
             'The boards connect through J10 (power board) and J11 (control card): the same label name on both sheets.']
    for k, n in enumerate(notes):
        size = '3.81' if k == 0 else '1.905'
        rt.append(['text', q(n), ['exclude_from_sim', 'no'], ['at', '30.48', fmt(30.48 + 6.35 * k), '0'],
                   ['effects', ['font', ['size', size, size]], ['justify', 'left', 'bottom']], ['uuid', q(uid('root note %d' % k))]])
    rt += [['sheet_instances', ['path', '"/"', ['page', '"1"']]], ['embedded_fonts', 'no']]
    open(os.path.join(WORK, 'BOOST.kicad_sch'), 'w', encoding='utf-8', newline='\n').write(dump(rt) + '\n')

    # ---------------------------------------------------------------- projects
    for bd, fname, title in BOARDS:
        p = os.path.join(WORK, fname + '.kicad_pro')
        t = open(p, encoding='utf-8', newline='').read()
        old = '"uuid": "00000000-0000-0000-0000-000000000000"'
        assert t.count(old) == 1, p
        t = t.replace(old, '"uuid": "%s"' % sheet_info[bd]['uuid'])
        open(p, 'w', encoding='utf-8', newline='').write(t)
        json.loads(t)
    p = os.path.join(WORK, 'BOOST.kicad_pro')
    d = json.load(open(p, encoding='utf-8'))
    t = open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    old = '  "sheets": [' + nl + '    [' + nl + '      "%s",' % ROOT_UUID + nl + '      ""' + nl + '    ]'
    assert t.count(old) == 1
    new = old
    for bd, fname, title in BOARDS:
        new += ',' + nl + '    [' + nl + '      "%s",' % sheet_info[bd]['sheet_uuid'] + nl + '      "%s"' % \
            sheet_info[bd]['title'] + nl + '    ]'
    t = t.replace(old, new)
    json.loads(t)
    open(p, 'w', encoding='utf-8', newline='').write(t)
    json.dump({'root': ROOT_UUID, 'sheets': {bd: {k: v for k, v in si.items() if k in ('file', 'uuid', 'sheet_uuid', 'paper', 'shift')}
                                             for bd, si in sheet_info.items()},
               'cuts': cuts}, open(os.path.join(BASE, 'split_info.json'), 'w'), indent=1)
    print('%d cross-board wires cut: %s' % (len(cuts), sorted({c[0] for c in cuts})))


if __name__ == '__main__':
    main()
