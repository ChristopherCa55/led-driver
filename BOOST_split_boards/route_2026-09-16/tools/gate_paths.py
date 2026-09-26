"""Gate-drive path lengths on a routed board, from its copper export (system Python).

usage: python gate_paths.py ROUTED_CU.json [OUT.json]

"Beside": the share of the forward path (driver OUT -> series R -> gate pin on the LX side; driver OUT -> turn-off
diode -> gate pin on the rail side, the hold-off path) whose track lies within BESIDE_MM of the return path
(driver VSS pin -> source copper), centre line to centre line, on the same layer, or within 0.5 mm on the other
layer of the In2/In3 pair (the only two routing layers with no plane between them). Reported yes at >= 70 %.

For each gate: shortest copper path driver output pin -> series resistor (routed net 1), resistor -> FET gate
(routed net 2), and the driver return pin -> the FET's source copper (the source net's pour or the source pin).
Paths follow track centre lines; vias join layers; a pad is reached when a track end lies inside it. Distances
inside pads and pours are not counted (a pour is treated as one node), so the figures are routed track length.
"""
import json, math, sys, heapq, collections
from matplotlib.path import Path

cop = json.load(open(sys.argv[1]))
GATES = [  # FET, driver out pad, series R, gate net, return pad, source net, turn-off diode, paired leg ('R' or 'D')
    ('M1', ('U19', '15'), 'R15', 'GATE_M1', None, None, None, 'R'),
    ('M7', ('U15', '10'), 'R60', 'GATE_M7', ('U15', '9'), 'm2_source', 'D2', 'R'),
    ('M5', ('U8', '10'), 'R59', 'GATE_M5', ('U8', '9'), 'm4_source', 'D22', 'R'),
    ('M6', ('U10', '10'), 'R70', 'GATE_M6', ('U10', '9'), 'm3_source', 'D8', 'R'),
    ('M2', ('U15', '15'), 'R13', 'GATE_M2', ('U15', '14'), 'm2_source', 'D11', 'D'),
    ('M3', ('U10', '15'), 'R23', 'GATE_M3', ('U10', '14'), 'm3_source', 'D14', 'D'),
    ('M4', ('U8', '15'), 'R47', 'GATE_M4', ('U8', '14'), 'm4_source', 'D13', 'D'),
    ('M10', ('U11', '1'), 'R56', 'Net-(M10-G)', None, None, None, 'R'),
    ('M9', ('U12', '1'), 'R50', 'Net-(M9-G)', None, None, None, 'R'),
    ('M8', ('U6', '1'), 'R22', 'Net-(M8-G)', None, None, None, 'R'),
]
pads = {(p['ref'], p['num']): p for p in cop['pads']}


def graph(net):
    """Nodes: (layer, x, y) track ends; pads 'P:ref.num'; pour 'Z'. Edge weights in mm."""
    adj = collections.defaultdict(list)

    def link(a, b, w):
        adj[a].append((b, w))
        adj[b].append((a, w))

    ends = []
    for t in cop['tracks']:
        if t['net'] != net:
            continue
        a = (t['layer'], round(t['x0'], 3), round(t['y0'], 3))
        b = (t['layer'], round(t['x1'], 3), round(t['y1'], 3))
        link(a, b, math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']))
        ends += [a, b]
    segs = [t for t in cop['tracks'] if t['net'] == net]
    for e in set(ends):          # T-junctions: a track end lying on another segment of the same layer
        for t in segs:
            if t['layer'] != e[0]:
                continue
            dx, dy = t['x1'] - t['x0'], t['y1'] - t['y0']
            L2 = dx * dx + dy * dy
            if L2 == 0:
                continue
            u = ((e[1] - t['x0']) * dx + (e[2] - t['y0']) * dy) / L2
            if 1e-6 < u < 1 - 1e-6 and math.hypot(t['x0'] + u * dx - e[1], t['y0'] + u * dy - e[2]) < 0.01:
                L = math.sqrt(L2)
                link(e, (t['layer'], round(t['x0'], 3), round(t['y0'], 3)), u * L)
                link(e, (t['layer'], round(t['x1'], 3), round(t['y1'], 3)), (1 - u) * L)
    for v in cop['vias']:
        if v['net'] != net:
            continue
        here = [e for e in set(ends) if math.hypot(e[1] - v['x'], e[2] - v['y']) < v['dia'] / 2]
        for e in here:
            link(e, ('V', round(v['x'], 3), round(v['y'], 3)), 0.0)
    for p in cop['pads']:
        if p['net'] != net:
            continue
        name = 'P:%s.%s' % (p['ref'], p['num'])
        adj[name]
        tht = p['drill'] > 0
        for ln, polys in p['polys'].items():
            for poly in polys:
                if isinstance(poly, dict):
                    continue
                path = Path(poly)
                for e in set(ends):     # a through-hole pin is reachable from a track end over it on any layer
                    if (e[0] == ln or tht) and path.contains_point((e[1], e[2]), radius=1e-3):
                        link(name, e, 0.0)
                for v in cop['vias']:   # via in pad
                    if v['net'] == net and ln in v['layers'] and path.contains_point((v['x'], v['y'])):
                        link(name, ('V', round(v['x'], 3), round(v['y'], 3)), 0.0)
    for z in cop['zones']:
        if z['net'] != net or z['prio'] <= 1:
            continue
        for poly in z['polys']:
            if isinstance(poly, dict):
                continue
            path = Path(poly)
            for e in set(ends):
                if e[0] == z['layer'] and path.contains_point((e[1], e[2])):
                    link('Z', e, 0.0)
    for v in cop['vias']:     # vias standing in a pour join it
        if v['net'] == net and 'Z' in adj:
            node = ('V', round(v['x'], 3), round(v['y'], 3))
            if node in adj:
                for z in cop['zones']:
                    if z['net'] == net and z['prio'] > 1 and z['layer'] in v['layers'] and any(
                            not isinstance(pl, dict) and Path(pl).contains_point((v['x'], v['y'])) for pl in z['polys']):
                        link('Z', node, 0.0)
                        break
    return adj


BESIDE_MM = 1.5


def dist(adj, src, dsts, want_path=False):
    best = {src: 0.0}
    prev = {}
    heap = [(0.0, 0, src)]
    k = 1
    while heap:
        d, _, u = heapq.heappop(heap)
        if u in dsts:
            if not want_path:
                return d
            nodes = [u]
            while nodes[-1] in prev:
                nodes.append(prev[nodes[-1]])
            return d, nodes[::-1]
        if d > best.get(u, 1e18):
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < best.get(v, 1e18):
                best[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, k, v))
                k += 1
    return (None, []) if want_path else None


def segments(nodes):
    """Consecutive track-end nodes on one layer are track pieces (T-junction splits included)."""
    out = []
    for a, b in zip(nodes, nodes[1:]):
        if isinstance(a, tuple) and isinstance(b, tuple) and a[0] == b[0] and a[0] != 'V' and (a[1], a[2]) != (b[1], b[2]):
            out.append((a[0], a[1], a[2], b[1], b[2]))
    return out


def seg_dist(px, py, s):
    _, x0, y0, x1, y1 = s
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L2))
    return math.hypot(x0 + u * dx - px, y0 + u * dy - py)


def beside_share(drive, ret):
    total = near = 0.0
    for s in drive:
        _, x0, y0, x1, y1 = s
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / 0.1))
        for i in range(n):
            px, py = x0 + (x1 - x0) * (i + 0.5) / n, y0 + (y1 - y0) * (i + 0.5) / n
            ok = any(seg_dist(px, py, r) <= BESIDE_MM for r in ret if r[0] == s[0])
            if not ok and s[0] in ('In2.Cu', 'In3.Cu'):
                other = 'In3.Cu' if s[0] == 'In2.Cu' else 'In2.Cu'
                ok = any(seg_dist(px, py, r) <= 0.5 for r in ret if r[0] == other)
            total += L / n
            near += L / n if ok else 0.0
    return near / total if total else None


def resistor_pad(ref, net):
    for (r, num), p in pads.items():
        if r == ref and p['net'] == net:
            return 'P:%s.%s' % (r, num)


def xy(node):
    if isinstance(node, tuple):
        return node[1], node[2]
    if isinstance(node, str) and node.startswith('P:'):
        r, num = node[2:].rsplit('.', 1)
        return pads[(r, num)]['x'], pads[(r, num)]['y']
    return None


def loop_area(points, h=0.05):
    """Area (mm2) enclosed by the closed outline POINTS, even-odd, on an H grid: the gate loop's footprint in plan
    view (layer spacing ignored; a lobe that crosses itself counts once, not cancelled)."""
    import numpy as np
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    gx, gy = np.meshgrid(np.arange(min(xs), max(xs) + h, h), np.arange(min(ys), max(ys) + h, h))
    inside = Path(points + [points[0]], closed=True).contains_points(np.c_[gx.ravel() + h / 2, gy.ravel() + h / 2])
    return float(inside.sum() * h * h)


def vias_on(nodes):
    return sum(1 for x in nodes if isinstance(x, tuple) and x[0] == 'V')


def main():
    rows = []
    for fet, drv, rref, gnet, ret, snet, diode, leg in GATES:
        dnet = pads[drv]['net']
        dadj = graph(dnet)
        a, apath = dist(dadj, 'P:%s.%s' % drv, {resistor_pad(rref, dnet)}, want_path=True)
        g = dist(graph(gnet), resistor_pad(rref, gnet), {'P:%s.1' % fet})
        row = dict(fet=fet, drive_net=dnet, driver_to_R=a, gate_net=gnet, R_to_gate=g)
        dd = dpath = dg = None
        if diode:
            dd, dpath = dist(dadj, 'P:%s.%s' % drv, {'P:%s.1' % diode}, want_path=True)
            dg = dist(graph(gnet), 'P:%s.2' % diode, {'P:%s.1' % fet})
            row.update(driver_to_diode=dd, diode_to_gate=dg)
        share = None
        if ret:
            rlen, rpath = dist(graph(snet), 'P:%s.%s' % ret, {'Z', 'P:%s.3' % fet}, want_path=True)
            row['return_to_source_copper'] = rlen
            if leg == 'R':
                _, gpath = dist(graph(gnet), resistor_pad(rref, gnet), {'P:%s.1' % fet}, want_path=True)
                fwd = segments(apath) + segments(gpath)
            else:
                _, gpath = dist(graph(gnet), 'P:%s.2' % diode, {'P:%s.1' % fet}, want_path=True)
                fwd = segments(dpath) + segments(gpath)
            share = beside_share(fwd, segments(rpath))
            # plan-view loop: driver OUT -> forward path -> gate pin -> source pin -> return path back -> driver VSS
            fnodes = (apath + gpath[1:]) if leg == 'R' else (dpath + gpath[1:])
            outline = [q for q in (xy(x) for x in fnodes) if q] + [xy('P:%s.3' % fet)] +                 [q for q in (xy(x) for x in reversed(rpath)) if q]
            row['loop_area_mm2'] = loop_area(outline) if len(outline) >= 3 else None
            row['paired_path'] = 'driver->R->gate' if leg == 'R' else 'driver->diode->gate'
            row['forward_beside_return_share'] = share
        rows.append(row)
        f = lambda x: '%5.1f' % x if x is not None else '  n/a'
        print('%-4s driver->R %s, R->gate %s; driver->diode %s, diode->gate %s; return %s; %s beside return %s; loop %s mm2' % (
            fet, f(a), f(g), f(dd), f(dg), f(row.get('return_to_source_copper')) if ret else '(GND)',
            row.get('paired_path', '-'), ('%3.0f %% (%s)' % (100 * share, 'yes' if share >= 0.7 else 'no')) if share is not None else '-',
            f(row.get('loop_area_mm2'))))
        # every pad of the gate net (series R, pull-down, turn-off diode) -> gate pin; the other pad's net shows its role
        links = []
        gadj = graph(gnet)
        for (r, num), pd in sorted(pads.items()):
            if pd['net'] != gnet or r == fet:
                continue
            d, nodes = dist(gadj, 'P:%s.%s' % (r, num), {'P:%s.1' % fet}, want_path=True)
            other = sorted({q['net'] for (rr, nn), q in pads.items() if rr == r and nn != num})
            gp = pads[(fet, '1')]
            links.append(dict(pad='%s.%s' % (r, num), to_gate_mm=d, vias=vias_on(nodes) if d is not None else None,
                              straight_mm=math.hypot(pd['x'] - gp['x'], pd['y'] - gp['y']), other_pad_nets=other))
        row['gate_net_links'] = links
        print('     ' + '; '.join('%s->%s.1 %s mm routed (%.1f straight) %d via (other pad %s)' % (
            k['pad'], fet, '%.1f' % k['to_gate_mm'] if k['to_gate_mm'] is not None else 'n/a', k['straight_mm'],
            k['vias'] or 0, ','.join(k['other_pad_nets'])) for k in links))
    if len(sys.argv) > 2:
        json.dump(rows, open(sys.argv[2], 'w'), indent=1)


if __name__ == '__main__':
    main()
