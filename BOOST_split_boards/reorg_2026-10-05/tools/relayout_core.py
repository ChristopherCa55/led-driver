"""Format-independent block re-layout (2026-10-05), used by relayout_asc.py (LTspice) and relayout_kicad.py (KiCad).

The adapter builds a Model:
  pins     [Pin(owner, pt, outward)]           connection points of placed parts (owner = item id)
  wires    [Wire(id, p1, p2)]                  axis-aligned or not; split here at interior attach points
  labels   [Label(id, name, pt, kind)]         net names (LTspice FLAG, KiCad global label / power symbol)
  attach   [Attach(id, pt)]                    must-keep markers on a net (KiCad PWR_FLAG / no-connect)
  items    {id: Item(id, block, bbox, kind)}   placed parts (block set), and label/attach owners
Points are exact tuples on the format's grid.

solve() decides, per net:
  - each block B with pins on the net gets the Steiner tree of the wire graph joining its pins; an edge in exactly
    one block's tree is kept with that block, every other edge is deleted;
  - an existing label / attach is kept with block B when a path of at most LABEL_REACH from it to one of B's pins
    uses only unmarked edges or edges of B (those edges are kept with B), else the label is dropped (attach items are
    never dropped: they move to their nearest pin);
  - a net that ends up in more than one connected fragment gets a label on every fragment that lacks one.
Then the islands (connected kept items) are packed per block, the blocks in the given rows.
"""
import collections, heapq, math

Pin = collections.namedtuple('Pin', 'owner pid pt out')        # out: unit vector away from the part body
Wire = collections.namedtuple('Wire', 'id p1 p2')
Label = collections.namedtuple('Label', 'id name pt kind')
Attach = collections.namedtuple('Attach', 'id pt')


class Model:
    def __init__(self):
        self.pins, self.wires, self.labels, self.attach = [], [], [], []
        self.item_block = {}          # part id -> block
        self.item_bbox = {}           # part id -> (x0, y0, x1, y1) at the original position
        self.label_size = None        # function(label) -> (w, h) of its text, for island bboxes


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


def on_segment(p, a, b):
    if a[0] == b[0] == p[0]:
        return min(a[1], b[1]) < p[1] < max(a[1], b[1])
    if a[1] == b[1] == p[1]:
        return min(a[0], b[0]) < p[0] < max(a[0], b[0])
    return False


def solve(m, label_reach, keep_whole_single=True, long_len=None, long_span=None):
    """Returns a result dict: kept edges per block, kept labels per block, new labels needed, islands."""
    # ---- points and split edges
    pts = set()
    for w in m.wires:
        pts.add(w.p1); pts.add(w.p2)
    for p in m.pins:
        pts.add(p.pt)
    for l in m.labels:
        pts.add(l.pt)
    for a in m.attach:
        pts.add(a.pt)
    byx, byy = collections.defaultdict(list), collections.defaultdict(list)
    for p in pts:
        byx[p[0]].append(p); byy[p[1]].append(p)
    edges = []                                   # (eid, wire id, a, b, length)
    for w in m.wires:
        a, b = w.p1, w.p2
        inner = []
        if a[0] == b[0]:
            inner = [p for p in byx[a[0]] if min(a[1], b[1]) < p[1] < max(a[1], b[1])]
            inner.sort(key=lambda p: abs(p[1] - a[1]))
        elif a[1] == b[1]:
            inner = [p for p in byy[a[1]] if min(a[0], b[0]) < p[0] < max(a[0], b[0])]
            inner.sort(key=lambda p: abs(p[0] - a[0]))
        seq = [a] + inner + [b]
        for p, q in zip(seq, seq[1:]):
            edges.append((len(edges), w.id, p, q, math.hypot(q[0] - p[0], q[1] - p[1])))
    uf = UF()
    for p in pts:
        uf.f(p)
    for e in edges:
        uf.u(e[2], e[3])
    net_of = lambda p: uf.f(p)
    # wires longer than long_len are never kept: their ends get labels instead (keeps islands compact)
    wire_len = {w.id: math.hypot(w.p2[0] - w.p1[0], w.p2[1] - w.p1[1]) for w in m.wires}
    long_wire = {wid for wid, ln in wire_len.items() if long_len and ln > long_len}
    adj = collections.defaultdict(list)
    for e in edges:
        if e[1] in long_wire:
            continue
        adj[e[2]].append((e[3], e[0]))
        adj[e[3]].append((e[2], e[0]))
    # ---- pins per net per block
    pins_by_net = collections.defaultdict(lambda: collections.defaultdict(list))
    for p in m.pins:
        b = m.item_block[p.owner]
        pins_by_net[net_of(p.pt)][b].append(p)
    edge_net = {e[0]: net_of(e[2]) for e in edges}
    mark = collections.defaultdict(set)          # eid -> blocks

    def steiner(nodes):
        nodes = list(dict.fromkeys(nodes))
        tree_nodes, tree_edges = {nodes[0]}, set()
        rest = set(nodes[1:]) - tree_nodes
        while rest:
            dist = {n: 0.0 for n in tree_nodes}
            prev = {}
            hq = [(0.0, n) for n in tree_nodes]
            heapq.heapify(hq)
            hit = None
            while hq:
                d, n = heapq.heappop(hq)
                if d > dist.get(n, 1e18):
                    continue
                if n in rest:
                    hit = n
                    break
                for (o, eid) in adj[n]:
                    nd = d + edges[eid][4]
                    if nd < dist.get(o, 1e18):
                        dist[o] = nd
                        prev[o] = (n, eid)
                        heapq.heappush(hq, (nd, o))
            if hit is None:          # pins not wired together (joined by labels only)
                break
            n = hit
            while n not in tree_nodes:
                pn, eid = prev[n]
                tree_edges.add(eid)
                tree_nodes.add(n)
                n = pn
            rest -= tree_nodes
        return tree_edges

    for net, blocks in pins_by_net.items():
        for b, ps in blocks.items():
            for eid in steiner([p.pt for p in ps]):
                mark[eid].add(b)
    keep_edge = {}                               # eid -> block
    for e in edges:
        bs = mark.get(e[0], set())
        if len(bs) == 1:
            keep_edge[e[0]] = next(iter(bs))
    # single-block nets: keep the whole wire tree (stubs to labels included)
    if keep_whole_single:
        for e in edges:
            blocks = pins_by_net.get(edge_net[e[0]], {})
            if len(blocks) == 1 and e[0] not in keep_edge and e[1] not in long_wire:
                keep_edge[e[0]] = next(iter(blocks))
    # a (net, block) wiring that spans more than long_span is dropped: its pins get labels instead
    if long_span:
        span = collections.defaultdict(lambda: [1e18, 1e18, -1e18, -1e18])
        for eid, b in keep_edge.items():
            e = edges[eid]
            s = span[(edge_net[eid], b)]
            for p in (e[2], e[3]):
                s[0], s[1], s[2], s[3] = min(s[0], p[0]), min(s[1], p[1]), max(s[2], p[0]), max(s[3], p[1])
        too_long = {k for k, s in span.items() if max(s[2] - s[0], s[3] - s[1]) > long_span}
        for eid in [eid for eid, b in keep_edge.items() if (edge_net[eid], b) in too_long]:
            del keep_edge[eid]
            mark[eid] = {'#'}            # so no label path can use it
        self_cut = len(too_long)
    else:
        self_cut = 0
    # ---- labels and attach markers
    pin_nodes = collections.defaultdict(list)    # point -> blocks of pins there
    for p in m.pins:
        pin_nodes[p.pt].append(m.item_block[p.owner])

    def reach(start, limit):
        """Nearest pin (block) reachable from start within limit, through edges kept-or-unmarked of one block."""
        best = None
        dist = {start: 0.0}
        prev = {}
        hq = [(0.0, start)]
        while hq:
            d, n = heapq.heappop(hq)
            if d > dist.get(n, 1e18) or d > limit:
                continue
            if pin_nodes.get(n):
                best = (d, n)
                break
            for (o, eid) in adj[n]:
                nd = d + edges[eid][4]
                if nd < dist.get(o, 1e18):
                    dist[o] = nd
                    prev[o] = (n, eid)
                    heapq.heappush(hq, (nd, o))
        if not best:
            return None
        n = pin_node = best[1]
        blocks = set(pin_nodes[n])
        path = []
        while n != start:
            pn, eid = prev[n]
            path.append(eid)
            n = pn
        for b in sorted(blocks):
            if all(keep_edge.get(eid, b) == b and (not mark.get(eid) or mark[eid] == {b}) for eid in path):
                return b, path, pin_node
        return (None, path, pin_node) if strict is False else None

    strict = True
    label_block, dropped = {}, []
    for l in m.labels:
        r = reach(l.pt, label_reach) if pin_nodes.get(l.pt) is None else (pin_nodes[l.pt][0], [], l.pt)
        if r:
            b, path, _ = r
            label_block[l.id] = b
            for eid in path:
                keep_edge[eid] = b
        else:
            dropped.append(l)
    attach_block = {}
    for a in m.attach:
        r = reach(a.pt, label_reach) if pin_nodes.get(a.pt) is None else (pin_nodes[a.pt][0], [], a.pt)
        if r:
            attach_block[a.id] = (r[0], None)
            for eid in r[1]:
                keep_edge[eid] = r[0]
        else:            # move it onto its nearest pin (any distance, any edges)
            strict = False
            r = reach(a.pt, 1e18)
            strict = True
            if r and r[0] is None:
                r = (pin_nodes[r[2]][0], r[1], r[2])
            attach_block[a.id] = (r[0], r[2]) if r else (None, None)
    # ---- fragments after deletion: nodes are (point, block), so a point shared by two blocks splits in two
    kuf = UF()
    for p in m.pins:
        kuf.f(('pt', p.pt, m.item_block[p.owner]))
    for eid, b in keep_edge.items():
        e = edges[eid]
        kuf.u(('pt', e[2], b), ('pt', e[3], b))
    node_blocks = collections.defaultdict(set)
    for key in list(kuf.p):
        node_blocks[key[1]].add(key[2])
    frag_net, frag_block = {}, {}
    for key in list(kuf.p):
        fr = kuf.f(key)
        frag_net[fr] = net_of(key[1])
        frag_block[fr] = key[2]
    net_frags = collections.defaultdict(set)
    for fr, net in frag_net.items():
        net_frags[net].add(fr)
    frag_nodes = collections.defaultdict(list)
    for key in list(kuf.p):
        frag_nodes[kuf.f(key)].append(key[1])
    frag_labels = collections.defaultdict(list)
    for l in m.labels:
        if l.id in label_block:
            frag_labels[kuf.f(('pt', l.pt, label_block[l.id]))].append(l)
    # cut points: kept nodes that lost an edge, or that another block also uses
    deleted_at = collections.Counter()
    for e in edges:
        if e[0] not in keep_edge:
            deleted_at[e[2]] += 1
            deleted_at[e[3]] += 1
    dropped_nets = {net_of(l.pt) for l in dropped}
    need = []                                    # dict(frag, net, block, pt, dir)
    for net, frs in net_frags.items():
        if len(frs) < 2 and net not in dropped_nets:
            continue
        for fr in frs:
            if frag_labels.get(fr):
                continue
            b = frag_block[fr]
            nodes = frag_nodes[fr]
            cut = [n for n in nodes if deleted_at[n] or len(node_blocks[n]) > 1]
            ends = [n for n in nodes if len([1 for (o, eid) in adj[n] if keep_edge.get(eid) == b]) == 1]
            pin_here = [p for p in m.pins if p.pt in nodes and m.item_block[p.owner] == b]
            free_ends = [n for n in ends if not any(p.pt == n for p in pin_here)]
            if cut:
                pt = sorted(cut)[0]
            elif free_ends:
                pt = sorted(free_ends)[0]
            else:
                pt = sorted(p.pt for p in pin_here)[0]
            kept_nb = [o for (o, eid) in adj[pt] if keep_edge.get(eid) == b]
            if kept_nb:
                o = kept_nb[0]
                d = (pt[0] - o[0], pt[1] - o[1])
            else:
                pp = [p for p in pin_here if p.pt == pt]
                d = pp[0].out if pp else (1, 0)
            n = math.hypot(*d) or 1
            need.append(dict(frag=fr, net=net, block=b, pt=pt, dir=(round(d[0] / n), round(d[1] / n))))
    # ---- islands: union kept edges, pins of each part, labels, attach
    iuf = UF()
    for p in m.pins:
        iuf.u(('item', p.owner), ('frag', kuf.f(('pt', p.pt, m.item_block[p.owner]))))
    for eid, b in keep_edge.items():
        iuf.u(('edge', eid), ('frag', kuf.f(('pt', edges[eid][2], b))))
    for l in m.labels:
        if l.id in label_block:
            iuf.u(('label', l.id), ('frag', kuf.f(('pt', l.pt, label_block[l.id]))))
    for nd in need:
        iuf.u(('need', id(nd)), ('frag', nd['frag']))
    for a in m.attach:
        b, pin_pt = attach_block[a.id]
        pt = pin_pt or a.pt
        if b is not None and kuf.p.get(('pt', pt, b)) is not None:
            iuf.u(('attach', a.id), ('frag', kuf.f(('pt', pt, b))))
    for it in m.item_block:
        iuf.f(('item', it))
    return dict(edges=edges, keep_edge=keep_edge, label_block=label_block, dropped=dropped, need=need,
                attach_block=attach_block, iuf=iuf, net_of=net_of, kuf=kuf, frag_net=frag_net, span_cut=self_cut)


def shelf_pack(boxes, max_w, gap):
    """boxes: [(key, w, h)] -> {key: (x, y)}, total (W, H). Tallest first, rows left to right."""
    order = sorted(boxes, key=lambda b: (-b[2], -b[1], str(b[0])))
    pos, x, y, row_h, W = {}, 0.0, 0.0, 0.0, 0.0
    for k, w, h in order:
        if x > 0 and x + w > max_w:
            y += row_h + gap
            x, row_h = 0.0, 0.0
        pos[k] = (x, y)
        x += w + gap
        row_h = max(row_h, h)
        W = max(W, x - gap)
    return pos, (W, y + row_h)
