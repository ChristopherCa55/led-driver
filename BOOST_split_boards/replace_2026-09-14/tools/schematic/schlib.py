"""Minimal KiCad schematic reader: s-expression parse, symbol instances, pin
positions in sheet coordinates, and what touches each pin.

Geometry only. Connectivity is always confirmed from a kicad-cli netlist
export, never from this file.
"""
import math, re

BS = chr(92)


class Q(str):
    """A quoted string atom."""


def parse(text):
    stack, cur, i, n = [], [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '(':
            stack.append(cur); cur = []; i += 1
        elif c == ')':
            done = cur; cur = stack.pop(); cur.append(done); i += 1
        elif c == '"':
            j = i + 1; buf = []
            while text[j] != '"':
                if text[j] == BS:
                    buf.append(text[j + 1]); j += 2
                else:
                    buf.append(text[j]); j += 1
            cur.append(Q(''.join(buf))); i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()':
                j += 1
            cur.append(text[i:j]); i = j
    return cur[0]


def head(node):
    return node[0] if isinstance(node, list) and node else None


def kids(node, name):
    return [k for k in node if isinstance(k, list) and head(k) == name]


def kid(node, name):
    r = kids(node, name)
    return r[0] if r else None


def prop(node, name):
    for p in kids(node, 'property'):
        if p[1] == name:
            return str(p[2])
    return None


class Sheet:
    def __init__(self, path):
        self.path = path
        self.text = open(path, encoding='utf8').read()
        self.root = parse(self.text)
        self.libs = {}
        ls = kid(self.root, 'lib_symbols')
        for s in kids(ls, 'symbol'):
            self.libs[str(s[1])] = s
        self.instances = kids(self.root, 'symbol')
        self.wires = []
        for w in kids(self.root, 'wire'):
            pts = [(float(p[1]), float(p[2])) for p in kid(w, 'pts') if head(p) == 'xy']
            self.wires.append(pts)
        self.labels = []
        for kind in ('label', 'global_label', 'hierarchical_label'):
            for l in kids(self.root, kind):
                at = kid(l, 'at')
                self.labels.append((kind, str(l[1]), (float(at[1]), float(at[2]))))
        self.junctions = [(float(kid(j, 'at')[1]), float(kid(j, 'at')[2])) for j in kids(self.root, 'junction')]
        self.no_connects = [(float(kid(j, 'at')[1]), float(kid(j, 'at')[2])) for j in kids(self.root, 'no_connect')]

    def ref(self, inst):
        # KiCad 7+: reference lives in (instances (project .. (path .. (reference "R1") (unit 1))))
        ins = kid(inst, 'instances')
        if ins:
            for proj in kids(ins, 'project'):
                for pth in kids(proj, 'path'):
                    r = kid(pth, 'reference')
                    if r:
                        return str(r[1])
        return prop(inst, 'Reference')

    def lib_pins(self, lib_id, unit, body=1):
        lib = self.libs[lib_id]
        name = lib_id.split(':')[-1]
        pins = []

        def walk(sym):
            for sub in kids(sym, 'symbol'):
                m = re.match(r'^(.*)_(\d+)_(\d+)$', str(sub[1]))
                if not m:
                    continue
                u, b = int(m.group(2)), int(m.group(3))
                if u not in (0, unit) or b not in (0, body):
                    continue
                for p in kids(sub, 'pin'):
                    at = kid(p, 'at')
                    num = kid(p, 'number'); nm = kid(p, 'name')
                    pins.append(dict(type=str(p[1]), number=str(num[1]), name=str(nm[1]),
                                     x=float(at[1]), y=float(at[2]), angle=float(at[3]) if len(at) > 3 else 0.0))
        walk(lib)
        ext = kid(lib, 'extends')
        if ext and not pins:
            parent = [k for k in self.libs if k.split(':')[-1] == str(ext[1])]
            if parent:
                walk(self.libs[parent[0]])
        return pins

    ORDER = 'mirror_first'

    @classmethod
    def xform(cls, px, py, X, Y, rot, mirror):
        # KiCad: symbol coordinates are y-up; sheet is y-down.
        x, y = px, py
        a = math.radians(rot)

        def rotate(x, y):
            return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)

        def mir(x, y):
            if mirror == 'x':
                return x, -y
            if mirror == 'y':
                return -x, y
            return x, y
        if cls.ORDER == 'mirror_first':
            x, y = rotate(*mir(x, y))
        else:
            x, y = mir(*rotate(x, y))
        return (round(X + x, 4), round(Y - y, 4))

    def inst_info(self, inst):
        at = kid(inst, 'at')
        X, Y, rot = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
        mir = kid(inst, 'mirror')
        mirror = str(mir[1]) if mir else None
        unit = int(kid(inst, 'unit')[1]) if kid(inst, 'unit') else 1
        lib_id = str(kid(inst, 'lib_id')[1])
        pins = []
        for p in self.lib_pins(lib_id, unit):
            pins.append(dict(p, pos=self.xform(p['x'], p['y'], X, Y, rot, mirror)))
        return dict(ref=self.ref(inst), lib_id=lib_id, at=(X, Y, rot), mirror=mirror, unit=unit,
                    value=prop(inst, 'Value'), footprint=prop(inst, 'Footprint'), pins=pins, node=inst)

    def touching(self, pos, tol=1e-3):
        out = []
        for i, pts in enumerate(self.wires):
            hit = False
            for k, p in enumerate(pts):
                if abs(p[0] - pos[0]) < tol and abs(p[1] - pos[1]) < tol:
                    out.append(('wire', i, k)); hit = True
            if not hit and len(pts) == 2:
                (x0, y0), (x1, y1) = pts
                if (min(x0, x1) - tol <= pos[0] <= max(x0, x1) + tol and min(y0, y1) - tol <= pos[1] <= max(y0, y1) + tol
                        and abs((x1 - x0) * (pos[1] - y0) - (y1 - y0) * (pos[0] - x0)) < tol * max(abs(x1 - x0), abs(y1 - y0), 1)):
                    out.append(('wire_mid', i))
        for kind, name, p in self.labels:
            if abs(p[0] - pos[0]) < tol and abs(p[1] - pos[1]) < tol:
                out.append((kind, name))
        for p in self.junctions:
            if abs(p[0] - pos[0]) < tol and abs(p[1] - pos[1]) < tol:
                out.append(('junction',))
        for p in self.no_connects:
            if abs(p[0] - pos[0]) < tol and abs(p[1] - pos[1]) < tol:
                out.append(('no_connect',))
        return out
