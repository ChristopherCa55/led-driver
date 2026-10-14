"""KiCad schematic geometry: symbol pin positions and a simple connectivity (wires join at end points and at
junctions/ends/pins lying on them; labels and power symbols join by name)."""
from collections import defaultdict
from sexpr import find, findall, unq, prop

ROT = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}


def xform(px, py, ang, mirror):
    """library point (y up) -> offset in the sheet (y down), KiCad order: rotate, then mirror"""
    x, y = px, -py
    c, s = ROT[ang % 360]
    x, y = x * c + y * s, -x * s + y * c
    if mirror == 'x':
        y = -y
    elif mirror == 'y':
        x = -x
    return x, y


def lib_pins(libsym, unit):
    """[(number, name, x, y, angle, hidden, type)] of one unit (unit-0 pins are common to all units)"""
    out = []
    for sub in findall(libsym, 'symbol'):
        parts = unq(sub[1]).rsplit('_', 2)
        u, style = int(parts[-2]), int(parts[-1])
        if u not in (0, unit) or style not in (0, 1):
            continue
        for p in findall(sub, 'pin'):
            at = find(p, 'at')
            hidden = any(c == ['hide', 'yes'] for c in p if isinstance(c, list)) or 'hide' in p
            out.append((unq(find(p, 'number')[1]), unq(find(p, 'name')[1]), float(at[1]), float(at[2]),
                        int(float(at[3])), hidden, p[1]))
    return out


def inst_info(s):
    at = find(s, 'at')
    m = find(s, 'mirror')
    path = find(find(find(s, 'instances'), 'project'), 'path')
    return {'lib': unq(find(s, 'lib_id')[1]), 'x': float(at[1]), 'y': float(at[2]), 'ang': int(float(at[3])),
            'mirror': m[1] if m else None, 'unit': int(find(s, 'unit')[1]), 'ref': unq(find(path, 'reference')[1])}


def pin_points(s, libs):
    i = inst_info(s)
    pts = []
    for num, name, px, py, ang, hidden, typ in lib_pins(libs[i['lib']], i['unit']):
        dx, dy = xform(px, py, i['ang'], i['mirror'])
        pts.append((num, name, round(i['x'] + dx, 3), round(i['y'] + dy, 3), hidden))
    return i, pts


def connectivity(root):
    libs = {unq(s[1]): s for s in findall(find(root, 'lib_symbols'), 'symbol')}
    P = lambda x, y: (round(float(x), 3), round(float(y), 3))
    par = {}

    def f(a):
        par.setdefault(a, a)
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    def u(a, b):
        par[f(a)] = f(b)
    wires = []
    for w in findall(root, 'wire'):
        xy = findall(find(w, 'pts'), 'xy')
        a, b = P(xy[0][1], xy[0][2]), P(xy[1][1], xy[1][2])
        wires.append((a, b))
        u(a, b)
    points = set()
    named = []
    pins = []
    for j in findall(root, 'junction'):
        points.add(P(find(j, 'at')[1], find(j, 'at')[2]))
    for kind in ('global_label', 'label'):
        for g in findall(root, kind):
            at = find(g, 'at')
            p = P(at[1], at[2])
            points.add(p)
            named.append((p, unq(g[1])))
    for s in findall(root, 'symbol'):
        i, pts = pin_points(s, libs)
        power = any(c == ['power'] or (isinstance(c, list) and c and c[0] == 'power') for c in libs[i['lib']])
        for num, name, x, y, hidden in pts:
            p = P(x, y)
            points.add(p)
            if power and i['ref'].startswith('#PWR') or (power and not i['ref'].startswith('#FLG')):
                named.append((p, unq(prop(s, 'Value')[2]) or name))
            pins.append((i['ref'], num, p, i['lib']))
    for a, b in wires:
        points.add(a)
        points.add(b)
    for a, b in wires:
        for p in points:
            if p in (a, b):
                continue
            if a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1]):
                u(p, a)
            elif a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]):
                u(p, a)
    for p in points:
        f(p)
    by_name = defaultdict(list)
    for p, n in named:
        by_name[n].append(p)
    for n, ps in by_name.items():
        for p in ps[1:]:
            u(p, ps[0])
    names = defaultdict(set)
    for p, n in named:
        names[f(p)].add(n)
    nets = defaultdict(list)
    for ref, num, p, lib in pins:
        nets[f(p)].append((ref, num))
    return nets, names, f, pins
