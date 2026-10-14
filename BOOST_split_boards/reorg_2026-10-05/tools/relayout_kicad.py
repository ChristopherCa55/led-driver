"""Split the flat KiCad schematic into a system root and one sheet per board, laid out by block (2026-10-05).

    python relayout_kicad.py ORIG.kicad_sch ORIG.net BLOCKS.json OUTDIR

Writes OUTDIR/BOOST.kicad_sch (root: two sheet symbols and notes), OUTDIR/BOOST_power_RC2.kicad_sch and
OUTDIR/BOOST_control_RC2.kicad_sch, plus OUTDIR/split_info.json (uuids, renamed nets, counts).

Same engine and block arrangement as relayout_asc.py (rows below), so each block sits in the same place as in the
LTspice schematic. Every symbol keeps its uuid and fields; its instance data holds the system project 'BOOST'
(path /<root>/<sheet>) and its board project (path /<board file uuid>), so the PCB footprint links (/<symbol uuid>)
stay valid. Wires between blocks and long wiring become global labels; a net without a name gets the KiCad auto name
made readable ('Net-(U19-OUTA)' -> 'U19_OUTA'). GND cut points get a power:GND symbol.
"""
import sys, os, re, json, math, uuid, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ksch, knet
import relayout_core as RC
from netnames import kname

NL, TAB = chr(10), chr(9)
ROOT_UUID = None
ROWS = {'POWER': [['P5', 'P1', 'P2', 'PJ'], ['P3a', 'P3b', 'P3c'], ['P4a', 'P4b', 'P4c', 'P4d']],
        'CONTROL': [['C1', 'C4', 'C3'], ['C2a', 'C2b', 'C2c'], ['C5a', 'C5b', 'C5c'], ['C6', 'C7', 'CJ']]}
FILES = {'POWER': ('BOOST_power_RC2', 'Power board'), 'CONTROL': ('BOOST_control_RC2', 'Control card')}
GAP_ISLAND, GAP_BLOCK, HEAD, MARGIN = 5.08, 15.24, 10.16, 25.4
PAPERS = [('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594), ('A0', 1189, 841)]


def snap(v):
    return round(round(v / 2.54) * 2.54, 4)


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def nid():
    return str(uuid.uuid4())


def shift_at(block, dx, dy):
    """Translate every (at x y ...) and (xy x y) in an S-expression block."""
    block = re.sub(r'\(at ([-\d.]+) ([-\d.]+)', lambda m: '(at %s %s' % (fmt(float(m.group(1)) + dx),
                                                                         fmt(float(m.group(2)) + dy)), block)
    return re.sub(r'\(xy ([-\d.]+) ([-\d.]+)', lambda m: '(xy %s %s' % (fmt(float(m.group(1)) + dx),
                                                                         fmt(float(m.group(2)) + dy)), block)


def set_instances(block, ref, unit, sheet_uuid, board_proj, board_uuid):
    i = block.find(NL + TAB + TAB + '(instances')
    j = block.find(NL + TAB + TAB + ')', i + 1)
    new = (NL + TAB * 2 + '(instances' +
           NL + TAB * 3 + '(project "BOOST"' + NL + TAB * 4 + '(path "/%s/%s"' % (ROOT_UUID, sheet_uuid) +
           NL + TAB * 5 + '(reference "%s")' % ref + NL + TAB * 5 + '(unit %d)' % unit + NL + TAB * 4 + ')' +
           NL + TAB * 3 + ')' +
           NL + TAB * 3 + '(project "%s"' % board_proj + NL + TAB * 4 + '(path "/%s"' % board_uuid +
           NL + TAB * 5 + '(reference "%s")' % ref + NL + TAB * 5 + '(unit %d)' % unit + NL + TAB * 4 + ')' +
           NL + TAB * 3 + ')' + NL + TAB * 2 + ')')
    return block[:i] + new + block[j + 4:]          # skip the old block's closing NL TAB TAB ')'


def main():
    global ROOT_UUID
    orig, netlist, blocks_path, outdir = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True)
    sch = ksch.Sch(orig)
    ROOT_UUID = re.search(r'\(uuid "([^"]+)"\)', sch.t).group(1)
    comps, kpins, knets = knet.load(netlist)
    bj = json.load(open(blocks_path))
    member = bj['member']
    titles = {b['id']: b['title'] for b in bj['blocks']}
    board_of = {b['id']: b['board'] for b in bj['blocks']}
    m = RC.Model()
    sym_by_id, lab_by_id = {}, {}
    gnd_template = pwr_numbers = None
    pwr_numbers = [int(x) for x in re.findall(r'"#PWR0*(\d+)"', sch.t)] + [0]
    for s in sch.syms:
        sym_by_id[s['uuid']] = s
        pins = [p for p in sch.pins(s) if not p[5]]
        if s['power']:
            pins = sch.pins(s)            # power symbols' pins are usually hidden power inputs
            if s['value'] == 'PWR_FLAG':
                m.attach.append(RC.Attach(s['uuid'], (ksch.rnd(pins[0][2]), ksch.rnd(pins[0][3]))))
            else:
                m.labels.append(RC.Label(s['uuid'], s['value'], (ksch.rnd(pins[0][2]), ksch.rnd(pins[0][3])), 'power'))
                if s['lib_id'] == 'power:GND' and gnd_template is None:
                    gnd_template = s
            continue
        k = sch.key(s)
        b = member[k]
        m.item_block[s['uuid']] = b
        xs = [p[2] for p in pins] + [s['x']]
        ys = [p[3] for p in pins] + [s['y']]
        for pm in re.finditer(r'\(property "(Reference|Value)" "([^"]*)"\s+\(at ([-\d.]+) ([-\d.]+)[^)]*\)(.*?)\n'
                              + TAB * 2 + r'\)', s['text'], re.S):
            if '(hide yes)' in pm.group(5):
                continue
            px, py, w = float(pm.group(3)), float(pm.group(4)), 0.8 * len(pm.group(2))
            xs += [px - w, px + w]; ys += [py - 1.3, py + 1.3]
        m.item_bbox[s['uuid']] = (min(xs) - 1.27, min(ys) - 1.27, max(xs) + 1.27, max(ys) + 1.27)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        for num, name, x, y, et, hid in pins:
            d = (x - cx, y - cy)
            out_v = (1 if d[0] > 0 else -1, 0) if abs(d[0]) >= abs(d[1]) else (0, 1 if d[1] > 0 else -1)
            m.pins.append(RC.Pin(s['uuid'], num, (ksch.rnd(x), ksch.rnd(y)), out_v))
    for w in sch.wires:
        wid = re.search(r'\(uuid "([^"]+)"\)', w['text']).group(1)
        m.wires.append(RC.Wire(wid, (ksch.rnd(w['x1']), ksch.rnd(w['y1'])), (ksch.rnd(w['x2']), ksch.rnd(w['y2']))))
    for l in sch.labels:
        lid = re.search(r'\(uuid "([^"]+)"\)', l['text']).group(1)
        lab_by_id[lid] = l
        m.labels.append(RC.Label(lid, l['name'], (ksch.rnd(l['x']), ksch.rnd(l['y'])), l['kind']))
    nc_by_id = {}
    for n in sch.noconn:
        nid_ = re.search(r'\(uuid "([^"]+)"\)', n['text']).group(1)
        nc_by_id[nid_] = n
        m.attach.append(RC.Attach(nid_, (ksch.rnd(n['x']), ksch.rnd(n['y']))))
    res = RC.solve(m, label_reach=25.4, long_len=63.5, long_span=50.8)
    edges, keep, net_of = res['edges'], res['keep_edge'], res['net_of']
    # ---- names
    net_name = {}
    for l in m.labels:
        net_name.setdefault(net_of(l.pt), l.name)
    pin_net = {}
    for r, ps in kpins.items():
        for p, n in ps:
            pin_net[(r, p)] = n
    renamed = {}

    def name_for(net):
        if net in net_name:
            return net_name[net]
        for p in m.pins:
            if net_of(p.pt) == net:
                kn = pin_net[(sym_by_id[p.owner]['ref'], p.pid)]
                nm = kname(kn)
                renamed[kn] = nm
                net_name[net] = nm
                return nm
        raise SystemExit('no name for net')
    global_names = {l['name'] for l in sch.labels if l['kind'] == 'global_label'}
    # ---- islands and their bboxes
    iuf = res['iuf']
    island_items = collections.defaultdict(list)
    for iid in m.item_block:
        island_items[iuf.f(('item', iid))].append(('item', iid))
    for eid in keep:
        island_items[iuf.f(('edge', eid))].append(('edge', eid))
    for lid in res['label_block']:
        island_items[iuf.f(('label', lid))].append(('label', lid))
    for nd in res['need']:
        island_items[iuf.f(('need', id(nd)))].append(('need', nd))
    for a in m.attach:
        k = ('attach', a.id)
        if iuf.p.get(k) is not None:
            island_items[iuf.f(k)].append(('attach', a.id))
    lab = {l.id: l for l in m.labels}
    island_block, island_bbox = {}, {}
    for isl, its in island_items.items():
        bs, xs, ys = set(), [], []
        for kind, v in its:
            if kind == 'item':
                bs.add(m.item_block[v]); x0, y0, x1, y1 = m.item_bbox[v]; xs += [x0, x1]; ys += [y0, y1]
            elif kind == 'edge':
                bs.add(keep[v]); e = edges[v]; xs += [e[2][0], e[3][0]]; ys += [e[2][1], e[3][1]]
            elif kind == 'label':
                l = lab[v]; bs.add(res['label_block'][v])
                w = 0.85 * len(l.name) + 3
                xs += [l.pt[0] - w, l.pt[0] + w]; ys += [l.pt[1] - 2.5, l.pt[1] + 2.5]
            elif kind == 'need':
                bs.add(v['block']); w = 0.85 * len(name_for(v['net'])) + 4
                xs += [v['pt'][0] - w, v['pt'][0] + w]; ys += [v['pt'][1] - 3, v['pt'][1] + 3]
            else:
                b, pin_pt = res['attach_block'][v]
                bs.add(b)
        bs.discard(None)
        assert len(bs) == 1, (bs, its[:3])
        island_block[isl] = bs.pop()
        island_bbox[isl] = (min(xs), min(ys), max(xs), max(ys))
    # ---- pack per board
    blk_islands = collections.defaultdict(list)
    for isl, b in island_block.items():
        blk_islands[b].append(isl)
    info = {'root': ROOT_UUID, 'renamed': {}, 'sheets': {}}
    off = {}
    sheets = {}
    for board, rows in ROWS.items():
        layout, origin = {}, {}
        y = MARGIN
        right = 0
        for row in rows:
            x, rh = MARGIN, 0
            for b in row:
                isls = blk_islands.get(b)
                if not isls:
                    continue
                area = sum((island_bbox[i][2] - island_bbox[i][0]) * (island_bbox[i][3] - island_bbox[i][1]) for i in isls)
                widest = max(island_bbox[i][2] - island_bbox[i][0] for i in isls)
                pos, (W, H) = RC.shelf_pack([(i, island_bbox[i][2] - island_bbox[i][0],
                                              island_bbox[i][3] - island_bbox[i][1]) for i in isls],
                                            max(widest, math.sqrt(area) * 1.6), GAP_ISLAND)
                W = max(W, 2.1 * len(titles[b]))
                layout[b] = dict(x=x, y=y, w=W, h=H + HEAD)
                for i in isls:
                    px, py = pos[i]
                    off[i] = (snap(x + px - island_bbox[i][0]), snap(y + HEAD + py - island_bbox[i][1]))
                x += W + GAP_BLOCK
                rh = max(rh, H + HEAD)
            right = max(right, x)
            y += rh + GAP_BLOCK
        def fits(w, h):        # inside the frame, and clear of the title block (bottom right, about 115 x 45 mm)
            if right + 10 > w or y + 5 > h:
                return False
            return all(lay['x'] + lay['w'] < w - 120 or lay['y'] + lay['h'] < h - 50 for lay in layout.values())
        paper = next(((n, w, h) for n, w, h in PAPERS if fits(w, h)), PAPERS[-1])
        sheets[board] = dict(layout=layout, paper=paper, uuid=nid(), sheet_uuid=nid())
    # ---- emit items per board
    item_off = {}
    for isl, its in island_items.items():
        for kind, v in its:
            item_off[(kind, v if kind != 'need' else id(v))] = off[isl]
    body = collections.defaultdict(list)
    pts_used = collections.defaultdict(collections.Counter)          # board -> point -> connection count
    pin_pts = collections.defaultdict(set)
    for s in sch.syms:
        if s['power']:
            continue
        b = m.item_block[s['uuid']]
        bd = board_of[b]
        dx, dy = item_off[('item', s['uuid'])]
        sh = sheets[bd]
        blk = shift_at(s['text'], dx, dy)
        blk = set_instances(blk, s['ref'], s['unit'], sh['sheet_uuid'], FILES[bd][0], sh['uuid'])
        body[bd].append(blk)
        for num, name, x, y, et, hid in sch.pins(s):
            if not hid:
                pts_used[bd][(ksch.rnd(x + dx), ksch.rnd(y + dy))] += 1
                pin_pts[bd].add((ksch.rnd(x + dx), ksch.rnd(y + dy)))
    for eid, b in keep.items():
        e = edges[eid]
        bd = board_of[b]
        dx, dy = item_off[('edge', eid)]
        a_, b_ = (ksch.rnd(e[2][0] + dx), ksch.rnd(e[2][1] + dy)), (ksch.rnd(e[3][0] + dx), ksch.rnd(e[3][1] + dy))
        body[bd].append(TAB + '(wire' + NL + TAB * 2 + '(pts' + NL + TAB * 3 + '(xy %s %s) (xy %s %s)'
                        % (fmt(a_[0]), fmt(a_[1]), fmt(b_[0]), fmt(b_[1])) + NL + TAB * 2 + ')' + NL + TAB * 2 +
                        '(stroke' + NL + TAB * 3 + '(width 0)' + NL + TAB * 3 + '(type default)' + NL + TAB * 2 + ')' +
                        NL + TAB * 2 + '(uuid "%s")' % nid() + NL + TAB + ')')
        pts_used[bd][a_] += 1
        pts_used[bd][b_] += 1
    pnum = [max(pwr_numbers)]

    def power_block(s, x, y, bd, new=False, prefix='#PWR'):
        """A power symbol (existing block s, or a new copy of s / the GND template) at (x, y) on board bd."""
        src = s if s is not None else gnd_template
        dx, dy = x - src['x'], y - src['y']
        blk = shift_at(src['text'], dx, dy)
        ref = src['ref']
        if new:
            pnum[0] += 1
            ref = '%s%04d' % (prefix, pnum[0])
            blk = re.sub(r'\(property "Reference" "[^"]*"', '(property "Reference" "%s"' % ref, blk)
            blk = re.sub(r'\(uuid "[^"]+"\)', lambda mm: '(uuid "%s")' % nid(), blk)
        sh = sheets[bd]
        return set_instances(blk, ref, src['unit'], sh['sheet_uuid'], FILES[bd][0], sh['uuid'])

    for l in m.labels:
        if l.id not in res['label_block']:
            continue
        b = res['label_block'][l.id]
        bd = board_of[b]
        dx, dy = item_off[('label', l.id)]
        if l.kind == 'power':
            s = sym_by_id[l.id]
            body[bd].append(power_block(s, s['x'] + dx, s['y'] + dy, bd))
        else:
            body[bd].append(shift_at(lab_by_id[l.id]['text'], dx, dy))
    gl_template = next(l for l in sch.labels if l['kind'] == 'global_label')
    ANG = {(1, 0): (0, 'left'), (-1, 0): (180, 'right'), (0, -1): (90, 'left'), (0, 1): (270, 'right')}
    new_names = collections.Counter()
    for nd in res['need']:
        bd = board_of[nd['block']]
        dx, dy = item_off[('need', id(nd))]
        x, y = ksch.rnd(nd['pt'][0] + dx), ksch.rnd(nd['pt'][1] + dy)
        name = name_for(nd['net'])
        new_names[name] += 1
        if name == 'GND':
            body[bd].append(power_block(None, x, y, bd, new=True))
            continue
        ang, just = ANG.get(tuple(nd['dir']), (0, 'left'))
        blk = gl_template['text']
        blk = re.sub(r'\(global_label "[^"]*"', '(global_label "%s"' % name.replace('"', ''), blk, count=1)
        blk = re.sub(r'\n\t\t\(at [-\d.]+ [-\d.]+ [-\d.]+\)', NL + TAB * 2 + '(at %s %s %d)' % (fmt(x), fmt(y), ang),
                     blk, count=1)
        blk = re.sub(r'\(justify (left|right)\)', '(justify %s)' % just, blk)
        blk = re.sub(r'\(property "Intersheetrefs" "\$\{INTERSHEET_REFS\}"\s+\(at [-\d.]+ [-\d.]+ [-\d.]+\)',
                     '(property "Intersheetrefs" "${INTERSHEET_REFS}"' + NL + TAB * 3 + '(at %s %s 0)' % (fmt(x), fmt(y)),
                     blk)
        blk = re.sub(r'\(uuid "[^"]+"\)', lambda mm: '(uuid "%s")' % nid(), blk)
        body[bd].append(blk)
    for a in m.attach:
        b, pin_pt = res['attach_block'][a.id]
        if b is None:
            print('attach item without a block, left out:', a.id)
            continue
        bd = board_of[b]
        dx, dy = item_off.get(('attach', a.id), (None, None))
        if dx is None:
            print('attach item not in an island, left out:', a.id)
            continue
        target = pin_pt or a.pt
        x, y = target[0] + dx, target[1] + dy
        if a.id in nc_by_id:
            n = nc_by_id[a.id]
            body[bd].append(shift_at(n['text'], x - n['x'], y - n['y']))
        else:
            s = sym_by_id[a.id]
            pin = [p for p in sch.pins(s)][0]
            body[bd].append(power_block(s, x - (pin[2] - s['x']), y - (pin[3] - s['y']), bd))
    # (Tried 2026-10-05: PWR_FLAGs on the card's 5V and GND at J11 clear the card-only ERC, but in the system ERC they
    # meet the power board's drivers: "power output connected to power output". Left out; no ERC exclusions.)
    if False:
     flag_t = next(s for s in sch.syms if s['value'] == 'PWR_FLAG')
     j11 = next(s for s in sch.syms if s['ref'] == 'J11')
     dx, dy = item_off[('item', j11['uuid'])]
     done = set()
     for num, name, x, y, et, hid in sch.pins(j11):
         net = pin_net.get(('J11', num))
         if net in ('5V', 'GND') and net not in done:
             done.add(net)
             fx, fy = ksch.rnd(x + dx), ksch.rnd(y + dy)
             fp = sch.pins(flag_t)[0]
             body['CONTROL'].append(power_block(flag_t, fx - (fp[2] - flag_t['x']), fy - (fp[3] - flag_t['y']),
                                                'CONTROL', new=True, prefix='#FLG'))
             pts_used['CONTROL'][(fx, fy)] += 1
    # junctions where three or more connections meet
    for bd in sheets:
        for p, c in pts_used[bd].items():
            if c >= 3:
                body[bd].append(TAB + '(junction' + NL + TAB * 2 + '(at %s %s)' % (fmt(p[0]), fmt(p[1])) + NL + TAB * 2 +
                                '(diameter 0)' + NL + TAB * 2 + '(color 0 0 0 0)' + NL + TAB * 2 + '(uuid "%s")' % nid() +
                                NL + TAB + ')')
    # block headings and frames
    for bd, sh in sheets.items():
        for b, lay in sh['layout'].items():
            x0, y0, x1, y1 = lay['x'] - 2.54, lay['y'] - 2.54, lay['x'] + lay['w'] + 2.54, lay['y'] + lay['h'] + 2.54
            body[bd].append(TAB + '(rectangle' + NL + TAB * 2 + '(start %s %s)' % (fmt(x0), fmt(y0)) + NL + TAB * 2 +
                            '(end %s %s)' % (fmt(x1), fmt(y1)) + NL + TAB * 2 + '(stroke' + NL + TAB * 3 + '(width 0.254)' +
                            NL + TAB * 3 + '(type dash)' + NL + TAB * 3 + '(color 132 0 0 1)' + NL + TAB * 2 + ')' + NL +
                            TAB * 2 + '(fill' + NL + TAB * 3 + '(type none)' + NL + TAB * 2 + ')' + NL + TAB * 2 +
                            '(uuid "%s")' % nid() + NL + TAB + ')')
            body[bd].append(TAB + '(text "%s"' % titles[b] + NL + TAB * 2 + '(exclude_from_sim no)' + NL + TAB * 2 +
                            '(at %s %s 0)' % (fmt(lay['x']), fmt(lay['y'] + 5.08)) + NL + TAB * 2 + '(effects' + NL +
                            TAB * 3 + '(font' + NL + TAB * 4 + '(size 2.54 2.54)' + NL + TAB * 4 + '(thickness 0.508)' +
                            NL + TAB * 4 + '(bold yes)' + NL + TAB * 3 + ')' + NL + TAB * 3 + '(justify left bottom)' + NL +
                            TAB * 2 + ')' + NL + TAB * 2 + '(uuid "%s")' % nid() + NL + TAB + ')')
    # ---- write the two board sheets
    t = sch.t
    a0 = t.find(NL + TAB + '(lib_symbols')
    a1 = t.find(NL + TAB + ')', a0 + 1)
    libsyms = t[a0 + 1:a1 + 3]
    for bd, sh in sheets.items():
        fname, title = FILES[bd]
        pname, pw, ph = sh['paper']
        head = ('(kicad_sch' + NL + TAB + '(version 20260306)' + NL + TAB + '(generator "eeschema")' + NL + TAB +
                '(generator_version "10.0")' + NL + TAB + '(uuid "%s")' % sh['uuid'] + NL + TAB + '(paper "%s")' % pname +
                NL + TAB + '(title_block' + NL + TAB * 2 + '(title "BOOST LED driver - %s")' % title + NL + TAB * 2 +
                '(date "2026-10-05")' + NL + TAB * 2 + '(rev "RC2")' + NL + TAB * 2 +
                '(comment 1 "One block per circuit; the LTspice schematic uses the same arrangement")' + NL + TAB * 2 +
                '(comment 2 "Nets between blocks are joined by global labels of the same name")' + NL + TAB + ')' + NL)
        tail = (NL + TAB + '(sheet_instances' + NL + TAB * 2 + '(path "/"' + NL + TAB * 3 + '(page "1")' + NL + TAB * 2 +
                ')' + NL + TAB + ')' + NL + TAB + '(embedded_fonts no)' + NL + ')' + NL)
        txt = head + libsyms + NL + (NL + NL).join(body[bd]) + NL + tail
        open(os.path.join(outdir, fname + '.kicad_sch'), 'w', encoding='utf-8', newline=NL).write(txt)
        info['sheets'][bd] = dict(file=fname + '.kicad_sch', uuid=sh['uuid'], sheet_uuid=sh['sheet_uuid'], paper=pname,
                                  items=len(body[bd]))
    # ---- the root
    sheet_blocks = []
    for k, bd in enumerate(('POWER', 'CONTROL')):
        fname, title = FILES[bd]
        sh = sheets[bd]
        x, y, w, h = 30.48 + k * 120.65, 60.96, 101.6, 63.5
        sheet_blocks.append(
            TAB + '(sheet' + NL + TAB * 2 + '(at %s %s)' % (fmt(x), fmt(y)) + NL + TAB * 2 + '(size %s %s)' % (fmt(w), fmt(h)) +
            NL + TAB * 2 + '(exclude_from_sim no)' + NL + TAB * 2 + '(in_bom yes)' + NL + TAB * 2 + '(on_board yes)' + NL +
            TAB * 2 + '(dnp no)' + NL + TAB * 2 + '(stroke' + NL + TAB * 3 + '(width 0.254)' + NL + TAB * 3 + '(type solid)' +
            NL + TAB * 2 + ')' + NL + TAB * 2 + '(fill' + NL + TAB * 3 + '(color 0 0 0 0.0000)' + NL + TAB * 2 + ')' + NL +
            TAB * 2 + '(uuid "%s")' % sh['sheet_uuid'] + NL +
            TAB * 2 + '(property "Sheetname" "%s"' % title + NL + TAB * 3 + '(at %s %s 0)' % (fmt(x), fmt(y - 0.7)) + NL +
            TAB * 3 + '(effects' + NL + TAB * 4 + '(font' + NL + TAB * 5 + '(size 2.54 2.54)' + NL + TAB * 4 + ')' + NL +
            TAB * 4 + '(justify left bottom)' + NL + TAB * 3 + ')' + NL + TAB * 2 + ')' + NL +
            TAB * 2 + '(property "Sheetfile" "%s.kicad_sch"' % fname + NL + TAB * 3 + '(at %s %s 0)' % (fmt(x), fmt(y + h + 0.6)) +
            NL + TAB * 3 + '(effects' + NL + TAB * 4 + '(font' + NL + TAB * 5 + '(size 1.524 1.524)' + NL + TAB * 4 + ')' +
            NL + TAB * 4 + '(justify left top)' + NL + TAB * 3 + ')' + NL + TAB * 2 + ')' + NL +
            TAB * 2 + '(instances' + NL + TAB * 3 + '(project "BOOST"' + NL + TAB * 4 + '(path "/%s"' % ROOT_UUID + NL +
            TAB * 5 + '(page "%d")' % (k + 2) + NL + TAB * 4 + ')' + NL + TAB * 3 + ')' + NL + TAB * 2 + ')' + NL + TAB + ')')
    notes = [
        ('BOOST LED driver: system schematic', 30.48, 30.48, 3.81, True),
        ('Two boards, two KiCad projects. Open the power board with BOOST_power_RC2.kicad_pro and the control card with '
         'BOOST_control_RC2.kicad_pro:', 30.48, 40.64, 1.905, False),
        ('each board project opens its own sheet (below) as its schematic, and its PCB updates from it. This root sheet '
         'ties both together for whole-system ERC.', 30.48, 45.72, 1.905, False),
        ('The boards connect through the 30-pin J10 (power board) / J11 (control card) pair: every signal that crosses '
         'between them carries the same global label on both sheets.', 30.48, 137.16, 1.905, False),
        ('LTspice: LTspice/BOOST.asc simulates both boards together, laid out in the same blocks as these sheets '
         '(power board left, control card right, test bench below).', 30.48, 142.24, 1.905, False),
    ]
    note_blocks = []
    for txt_, x, y, size, bold in notes:
        note_blocks.append(TAB + '(text "%s"' % txt_ + NL + TAB * 2 + '(exclude_from_sim no)' + NL + TAB * 2 +
                           '(at %s %s 0)' % (fmt(x), fmt(y)) + NL + TAB * 2 + '(effects' + NL + TAB * 3 + '(font' + NL +
                           TAB * 4 + '(size %s %s)' % (fmt(size), fmt(size)) + (NL + TAB * 4 + '(bold yes)' if bold else '') +
                           NL + TAB * 3 + ')' + NL + TAB * 3 + '(justify left bottom)' + NL + TAB * 2 + ')' + NL +
                           TAB * 2 + '(uuid "%s")' % nid() + NL + TAB + ')')
    root = ('(kicad_sch' + NL + TAB + '(version 20260306)' + NL + TAB + '(generator "eeschema")' + NL + TAB +
            '(generator_version "10.0")' + NL + TAB + '(uuid "%s")' % ROOT_UUID + NL + TAB + '(paper "A4")' + NL + TAB +
            '(title_block' + NL + TAB * 2 + '(title "BOOST LED driver - system")' + NL + TAB * 2 + '(date "2026-10-05")' +
            NL + TAB * 2 + '(rev "RC2")' + NL + TAB + ')' + NL + TAB + '(lib_symbols' + NL + TAB + ')' + NL +
            (NL + NL).join(sheet_blocks + note_blocks) + NL + NL + TAB + '(sheet_instances' + NL + TAB * 2 + '(path "/"' + NL +
            TAB * 3 + '(page "1")' + NL + TAB * 2 + ')' + NL + TAB + ')' + NL + TAB + '(embedded_fonts no)' + NL + ')' + NL)
    open(os.path.join(outdir, 'BOOST.kicad_sch'), 'w', encoding='utf-8', newline=NL).write(root)
    info['renamed'] = renamed
    info['counts'] = dict(edges=len(edges), kept=len(keep), labels_kept=len(res['label_block']),
                          labels_dropped=len(res['dropped']), new_labels=len(res['need']), islands=len(island_items),
                          span_cut=res['span_cut'])
    json.dump(info, open(os.path.join(outdir, 'split_info.json'), 'w'), indent=1)
    print(json.dumps(info['counts']), {bd: (s['paper'], s['items']) for bd, s in info['sheets'].items()},
          'renamed nets', len(renamed))


if __name__ == '__main__':
    main()
