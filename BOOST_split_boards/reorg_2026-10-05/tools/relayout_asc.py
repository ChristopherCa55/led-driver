"""Re-lay out the LTspice BOOST.asc by functional block (2026-10-05).

    python relayout_asc.py IN.asc BLOCKS.json NETNAMES.json OUT.asc LAYOUT.json

BLOCKS.json comes from blocks.py; every LTspice part is keyed by its InstName (U101A, R13, ...), and the SIM_* parts
form the test bench "TB". NETNAMES.json maps a net (frozen set of 'INST:pin' terminals) to the shared label name;
nets not in it keep their FLAG name, or get one from netnames_fallback().

Geometry: blocks are packed in the rows below (power board left, control card right, test bench at the bottom);
inside a block its islands (parts joined by kept wires) are shelf-packed. LAYOUT.json records every block's origin and
size, so the KiCad sheets can use the same arrangement.
"""
import sys, os, json, re, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ascgeo import Asc
import relayout_core as RC

G = 16                     # LTspice grid
ROWS_POWER = [['P5', 'P1', 'P2'], ['P3a', 'P3b', 'P3c'], ['P4a', 'P4b', 'P4c', 'P4d']]
ROWS_CONTROL = [['C1', 'C4', 'C3'], ['C2a', 'C2b', 'C2c'], ['C5a', 'C5b', 'C5c'], ['C6', 'C7']]
ROWS_TB = [['TB']]
GAP_ISLAND, GAP_BLOCK, GAP_AREA, HEAD = 64, 192, 512, 96


def snap(v):
    return int(round(v / G)) * G


def main():
    src, blocks_path, names_path, out, layout_path = sys.argv[1:6]
    a = Asc(src)
    bj = json.load(open(blocks_path))
    member, titles = bj['member'], {b['id']: b['title'] for b in bj['blocks']}
    titles['TB'] = 'Simulation test bench (LTspice only): battery, cable, LED loads, Arduino stimulus, directives'
    names = json.load(open(names_path)) if os.path.exists(names_path) else {}
    m = RC.Model()
    sid = {}
    for i, s in enumerate(a.syms):
        inst = s['attr'].get('InstName', '')
        b = 'TB' if inst.startswith('SIM_') else member.get(inst)
        if b is None:
            raise SystemExit('no block for %s' % inst)
        iid = ('sym', i)
        sid[iid] = s
        m.item_block[iid] = b
        ps = a.pins(s)
        xs = [p[1] for p in ps] + [s['x']]
        ys = [p[2] for p in ps] + [s['y']]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        m.item_bbox[iid] = (min(xs) - 24, min(ys) - 24, max(xs) + 24, max(ys) + 24)
        for name, x, y in ps:
            d = (x - cx, y - cy)
            out_v = (1 if d[0] > 0 else -1, 0) if abs(d[0]) >= abs(d[1]) else (0, 1 if d[1] > 0 else -1)
            m.pins.append(RC.Pin(iid, name, (x, y), out_v))
    for (ln, x1, y1, x2, y2) in a.wires:
        m.wires.append(RC.Wire(('wire', ln), (x1, y1), (x2, y2)))
    for (ln, x, y, n) in a.flags:
        m.labels.append(RC.Label(('flag', ln), n, (x, y), 'flag'))
    res = RC.solve(m, label_reach=20 * G, long_len=50 * G, long_span=40 * G)
    edges, keep, net_of = res['edges'], res['keep_edge'], res['net_of']
    # ---- net names for the new labels
    net_name = {}
    for (ln, x, y, n) in a.flags:
        net_name.setdefault(net_of((x, y)), n)
    term = collections.defaultdict(set)
    for p in m.pins:
        term[net_of(p.pt)].add('%s:%s' % (sid[p.owner]['attr'].get('InstName', ''), p.pid))
    used = {n.lower() for n in net_name.values()}

    def name_for(net):
        if net in net_name:
            return net_name[net]
        key = '|'.join(sorted(term[net]))
        n = names.get(key)
        if not n:
            insts = sorted(t.split(':')[0] for t in term[net])
            n = 'N_' + '_'.join(insts[:2])
            print('fallback name', n, sorted(term[net])[:6])
        base, k = n, 2
        while n.lower() in used and net_name.get(net) != n:
            n = '%s_%d' % (base, k)
            k += 1
        used.add(n.lower())
        net_name[net] = n
        return n
    # ---- islands
    iuf = res['iuf']
    island_items = collections.defaultdict(list)
    for iid in m.item_block:
        island_items[iuf.f(('item', iid))].append(('item', iid))
    for eid, b in keep.items():
        island_items[iuf.f(('edge', eid))].append(('edge', eid))
    lab_by_id = {l.id: l for l in m.labels}
    for lid in res['label_block']:
        island_items[iuf.f(('label', lid))].append(('label', lid))
    for nd in res['need']:
        island_items[iuf.f(('need', id(nd)))].append(('need', nd))
    island_block, island_bbox = {}, {}
    for isl, its in island_items.items():
        bs, xs, ys = set(), [], []
        for kind, v in its:
            if kind == 'item':
                bs.add(m.item_block[v])
                x0, y0, x1, y1 = m.item_bbox[v]
                xs += [x0, x1]; ys += [y0, y1]
            elif kind == 'edge':
                bs.add(keep[v])
                e = edges[v]
                xs += [e[2][0], e[3][0]]; ys += [e[2][1], e[3][1]]
            elif kind == 'label':
                l = lab_by_id[v]
                bs.add(res['label_block'][v])
                w = 12 * len(l.name) + 16
                xs += [l.pt[0] - w, l.pt[0] + w]; ys += [l.pt[1] - 16, l.pt[1] + 16]
            else:
                bs.add(v['block'])
                w = 12 * len(name_for(v['net'])) + 32
                xs += [v['pt'][0] - w, v['pt'][0] + w]; ys += [v['pt'][1] - 24, v['pt'][1] + 24]
        assert len(bs) == 1, (bs, its[:4])
        island_block[isl] = bs.pop()
        island_bbox[isl] = (min(xs), min(ys), max(xs), max(ys))
    # ---- pack islands inside blocks
    blk_islands = collections.defaultdict(list)
    for isl, b in island_block.items():
        blk_islands[b].append(isl)
    blk_pos, blk_size = {}, {}
    for b, isls in blk_islands.items():
        area = sum((island_bbox[i][2] - island_bbox[i][0]) * (island_bbox[i][3] - island_bbox[i][1]) for i in isls)
        widest = max(island_bbox[i][2] - island_bbox[i][0] for i in isls)
        maxw = max(widest, math.sqrt(area) * 1.6)
        pos, (W, H) = RC.shelf_pack([(i, island_bbox[i][2] - island_bbox[i][0], island_bbox[i][3] - island_bbox[i][1])
                                     for i in isls], maxw, GAP_ISLAND)
        blk_pos[b], blk_size[b] = pos, (W, H)
    # ---- blocks in rows; areas side by side
    layout, origin = {}, {}

    def place_rows(rows, x0, y0):
        y = y0
        right = x0
        for row in rows:
            x, rh = x0, 0
            for b in row:
                if b not in blk_size:
                    continue
                W, H = blk_size[b]
                W = max(W, 30 * len(titles.get(b, b)))          # at least as wide as its heading
                origin[b] = (x, y + HEAD)
                layout[b] = dict(x=x, y=y, w=W, h=H + HEAD)
                x += W + GAP_BLOCK
                rh = max(rh, H + HEAD)
            right = max(right, x - GAP_BLOCK)
            y += rh + GAP_BLOCK
        return right, y - GAP_BLOCK

    pr, pb = place_rows(ROWS_POWER, 0, 0)
    cr, cb = place_rows(ROWS_CONTROL, pr + GAP_AREA, 0)
    tr, tb = place_rows(ROWS_TB, 0, max(pb, cb) + GAP_AREA)
    # ---- island offsets
    off = {}
    for isl, b in island_block.items():
        px, py = blk_pos[b][isl]
        ox, oy = origin[b]
        x0, y0 = island_bbox[isl][0], island_bbox[isl][1]
        off[isl] = (snap(ox + px - x0), snap(oy + py - y0))
    item_off = {}
    for isl, its in island_items.items():
        for kind, v in its:
            item_off[(kind, v if kind != 'need' else id(v))] = off[isl]
    # ---- write
    L = a.lines
    outl = [L[0], 'SHEET 1 %d %d' % (snap(max(cr, tr) + 400), snap(tb + 400))]
    for eid, b in sorted(keep.items()):
        e = edges[eid]
        dx, dy = item_off[('edge', eid)]
        outl.append('WIRE %d %d %d %d' % (e[2][0] + dx, e[2][1] + dy, e[3][0] + dx, e[3][1] + dy))
    for (ln, x, y, n) in a.flags:
        lid = ('flag', ln)
        if lid in res['label_block']:
            dx, dy = item_off[('label', lid)]
            outl.append('FLAG %d %d %s' % (x + dx, y + dy, n))
    for nd in res['need']:
        dx, dy = item_off[('need', id(nd))]
        outl.append('FLAG %d %d %s' % (nd['pt'][0] + dx, nd['pt'][1] + dy, name_for(nd['net'])))
    for i, s in enumerate(a.syms):
        dx, dy = item_off[('item', ('sym', i))]
        t = L[s['line']].split(' ')
        t[2], t[3] = str(s['x'] + dx), str(s['y'] + dy)
        outl.append(' '.join(t))
        outl += L[s['line'] + 1:s['end'] + 1]
    # block headings, then the directives and comments in the test-bench area
    for b, lay in layout.items():
        outl.append('TEXT %d %d Left 3 ;%s' % (snap(lay['x']), snap(lay['y'] + 16), titles.get(b, b)))
    outl.append('TEXT %d %d Left 4 ;BOOST LED driver - power board (left) and control card (right), one block per '
                'circuit; the KiCad sheets use the same arrangement' % (0, -256))
    tx, ty = snap(tr + GAP_AREA), snap(max(pb, cb) + GAP_AREA + HEAD)
    keep_text = []
    for (ln, txt) in a.texts:
        body = txt.split(' ', 5)[5] if len(txt.split(' ', 5)) > 5 else ''
        if 'I added a lot of capacitors' in body:       # the caps now sit beside their ICs
            continue
        keep_text.append((ln, txt, body))
    for ln, txt, body in keep_text:
        t = txt.split(' ', 5)
        x, y = int(t[1]), int(t[2])
        if body.startswith(';D28-D30'):
            continue
        t[1], t[2] = str(tx), str(ty)
        outl.append(' '.join(t))
        ty += snap(64 * (body.count('\\n') + 1) + 32)
    for ln, txt, body in keep_text:
        if body.startswith(';D28-D30'):
            lay = layout['P2']
            t = txt.split(' ', 5)
            t[1], t[2] = str(snap(lay['x'])), str(snap(lay['y'] + lay['h'] + 32))
            outl.append(' '.join(t))
    open(out, 'w', encoding='latin-1', newline='\n').write('\n'.join(outl) + '\n')
    json.dump(dict(layout=layout, power=[pr, pb], control=[pr + GAP_AREA, cr, cb], tb=[tr, tb]),
              open(layout_path, 'w'), indent=1)
    print('span cuts %d; wires kept %d of %d edges; flags kept %d, dropped %d, new %d; islands %d'
          % (res['span_cut'], len(keep), len(edges), len(res['label_block']), len(res['dropped']), len(res['need']),
             len(island_items)))


if __name__ == '__main__':
    main()
