"""What-if on a copper export (export_copper6.py JSON): add vias, as if placed on the board and the zones refilled.

    python whatif_vias.py IN_cu.json OUT_cu.json NET:X:Y:DRILL:DIA [NET:X:Y:DRILL:DIA ...]

For each new via and each copper layer:
  - the via's own net already has copper (fill or pad) at the point -> the via flashes there: a ring of that net is
    added and the layer is listed on the barrel, so the solver joins the layers;
  - another net's copper is there -> an antipad: a hole of radius DIA/2 + that copper's clearance (the zone's own
    clearance if a zone of that net covers the point, else the Power netclass 0.25 mm) is cut from that net;
  - nothing there -> nothing.
Approximations: the via's drill hole is not removed from its own net's copper; KiCad's refill could also move
nearby fill edges and thermal spokes, which this does not model. Use it to rank options, then confirm on a board.
"""
import json, math, sys
from matplotlib.path import Path


def circle(x, y, r, n=24):
    return [[round(x + r * math.cos(2 * math.pi * k / n), 4), round(y + r * math.sin(2 * math.pi * k / n), 4)]
            for k in range(n)]


def covers(polys, x, y):
    return any(isinstance(p, list) and len(p) > 2 and Path(p).contains_point((x, y)) for p in polys)


def seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L2))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def conflicts(d, net, x, y, drill, dia, clr=0.25, hole_clr=0.25):
    """Fixed copper of other nets (tracks, vias, pads) too close on any layer, and holes too close (any net)."""
    out = []
    for t in d['tracks']:
        if t['net'] != net and seg_dist(x, y, t['x0'], t['y0'], t['x1'], t['y1']) < dia / 2 + t['w'] / 2 + clr:
            out.append('track %s %s' % (t['net'], t['layer']))
    for v in d['barrels']:
        dd = math.hypot(v['x'] - x, v['y'] - y)
        if dd < drill / 2 + v['drill'] / 2 + hole_clr:
            out.append('hole %s (%.2f, %.2f)' % (v['net'], v['x'], v['y']))
        elif v['net'] != net and dd < dia / 2 + v.get('dia', v['drill'] + 0.4) / 2 + clr:
            out.append('via/pin %s (%.2f, %.2f)' % (v['net'], v['x'], v['y']))
    ring = circle(x, y, dia / 2 + clr, 16) + [[x, y]]
    for p in d['pads']:
        if p['net'] == net:
            continue
        for ln, polys in p['polys'].items():
            if any(isinstance(q, list) and len(q) > 2 and any(Path(q).contains_point(pt) for pt in ring) for q in polys):
                out.append('pad %s.%s %s' % (p['ref'], p['num'], ln))
    for k in d.get('keepouts', []):
        if Path(k['pts']).contains_point((x, y)):
            out.append('keepout %s' % k['name'])
    return sorted(set(out))


def main():
    src, out = sys.argv[1], sys.argv[2]
    d = json.load(open(src))
    for spec in sys.argv[3:]:
        net, x, y, drill, dia = spec.split(':')
        x, y, drill, dia = float(x), float(y), float(drill), float(dia)
        bad = conflicts(d, net, x, y, drill, dia)
        if bad:
            print('REFUSED %s via at (%.2f, %.2f): %s' % (net, x, y, bad))
            continue
        flashed, cut = [], []
        for ln in d['layers']:
            if covers(d['nets'].get(net, {}).get(ln, []), x, y):
                d['nets'][net][ln].append(circle(x, y, dia / 2))
                flashed.append(ln)
                continue
            for other, L in d['nets'].items():
                if other == net or not covers(L.get(ln, []), x, y):
                    continue
                clr = 0.25
                for z in d['zones']:
                    if z['net'] == other and z['layer'] == ln and covers(z['polys'], x, y):
                        clr = max(clr, z['clearance'] or 0.25)
                L[ln].append({'hole': circle(x, y, dia / 2 + clr)})
                cut.append('%s %s (%.2f)' % (ln, other, clr))
        d['barrels'].append(dict(net=net, x=x, y=y, drill=drill, dia=dia, kind='via', layers=flashed))
        d['vias'].append(dict(net=net, x=x, y=y, drill=drill, dia=dia, layers=flashed))
        print('%s via at (%.2f, %.2f) d%.2f: flashes %s; antipads %s' % (net, x, y, drill, flashed, cut or 'none'))
    json.dump(d, open(out, 'w'))


if __name__ == '__main__':
    main()
