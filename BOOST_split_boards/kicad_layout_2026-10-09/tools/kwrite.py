"""Writing stage of build_kicad.py: turns the Builder's parts, wires, labels, ground symbols and texts into the
KiCad S-expression file, and compares the result with the original KiCad netlist."""
import copy, sys
from collections import defaultdict
from sexpr import parse, dump, find, findall, unq
import kgeo, knet
import build_kicad as BK
from build_kicad import Builder, S, OX, OY, fmt, nid, seg_dir, on_interior, to_mm, NEW_NAMES, REFNET, OUT

JUST = {'Left': 'left', 'Right': 'right', 'Center': None, 'Top': 'top', 'Bottom': 'bottom'}
FONT = {0: 0.8, 1: 1.0, 2: 1.27, 3: 2.0, 4: 2.5}
DIR_GND = {(0, 1): 0, (1, 0): 90, (-1, 0): 270, (0, -1): 180}
DIR_LABEL = {(1, 0): (0, 'left'), (0, -1): (90, 'left'), (-1, 0): (180, 'right'), (0, 1): (270, 'right')}


def qs(s):
    return '"' + s.replace('"', '\\"') + '"'


def mm(p):
    return (fmt(S * p[0] + OX), fmt(S * p[1] + OY))


def attach_dir(self, p, default=(0, 1)):
    """direction a symbol hung on point p should point: away from the wire(s) there"""
    ds = []
    for w in self.wires:
        if (w[0], w[1]) == p or (w[2], w[3]) == p:
            ds.append(seg_dir(w, p))
    if len(ds) == 1:
        return (-ds[0][0], -ds[0][1])
    if len(ds) >= 2 or any(on_interior(p, w) for w in self.wires):
        horiz = any(d[1] == 0 for d in ds) or any(on_interior(p, w) and w[1] == w[3] for w in self.wires)
        return (0, -1) if horiz else (1, 0)
    return default


def _hide(p, on):
    p[:] = [c for c in p if not (isinstance(c, list) and c[0] == 'hide')]
    if on:
        p.insert(3, ['hide', 'yes'])


def set_props(self, node, key):
    ang, mir, x, y = self.placed[key]
    X, Y = to_mm(x, y)
    lib = self.libs[self.lib_of(key)]
    libprops = {unq(p[1]): p for p in findall(lib, 'property')}
    pp = self.prop_pos.get(key)
    for p in findall(node, 'property'):
        name = unq(p[1])
        at = find(p, 'at')
        hidden = any(c == ['hide', 'yes'] for c in p if isinstance(c, list))
        eff = find(p, 'effects')
        if pp and name in ('Reference', 'Value') and pp.get(name):
            w = pp[name]
            if w == 'hide':
                _hide(p, True)
                at[1:4] = [fmt(X), fmt(Y), '0']
                continue
            wx, wy, just, size = w
            # written centred: KiCad re-maps left/top justification on rotated or mirrored symbols, a centred
            # text stays centred. The centre comes from your LTspice anchor + justification (measured stroke
            # font: about 0.78 x size per character)
            mmsize = FONT.get(size, 1.27)
            tw = len(unq(p[2])) * 0.78 * mmsize / S
            th = mmsize / S
            cx, cy = {'Left': (wx + tw / 2, wy), 'Right': (wx - tw / 2, wy), 'Top': (wx, wy + th / 2),
                      'Bottom': (wx, wy - th / 2)}.get(just, (wx, wy))
            at[1:4] = [fmt(S * cx + OX), fmt(S * cy + OY), '90' if ang in (90, 270) else '0']
            _hide(p, False)
            sz = find(find(eff, 'font'), 'size')
            sz[1:3] = [fmt(mmsize)] * 2
            eff[:] = [c for c in eff if not (isinstance(c, list) and c[0] == 'justify')]
        elif not hidden and name in libprops:
            la = find(libprops[name], 'at')
            dx, dy = kgeo.xform(float(la[1]), float(la[2]), ang, mir)
            at[1:4] = [fmt(X + dx), fmt(Y + dy), '90' if ang in (90, 270) else '0']
        else:
            at[1:4] = [fmt(X), fmt(Y), '0']


def write(self, path):
    root = self.root
    out = [c for c in root if not isinstance(c, list) or c[0] in ('version', 'generator', 'generator_version', 'uuid')]
    out.append(['paper', '"A0"'])
    lib_symbols = ['lib_symbols']
    for s in findall(find(root, 'lib_symbols'), 'symbol'):
        lib_symbols.append(self.libs[unq(s[1])])
    out.append(lib_symbols)
    for p in self.junctions:
        out.append(['junction', ['at', *mm(p)], ['diameter', '0'], ['color', '0', '0', '0', '0'], ['uuid', nid()]])
    for p in self.nocon:
        out.append(['no_connect', ['at', *mm(p)], ['uuid', nid()]])
    for w in self.wires:
        out.append(['wire', ['pts', ['xy', *mm(w[:2])], ['xy', *mm(w[2:])]],
                    ['stroke', ['width', '0'], ['type', 'default']], ['uuid', nid()]])
    for l in self.labels:
        x, y, name, shape = l[:4]
        d = l[4] if len(l) > 4 else attach_dir(self, (x, y), (0, -1))
        ang, j = DIR_LABEL[d]
        X, Y = mm((x, y))
        out.append(['global_label', qs(name), ['shape', shape], ['at', X, Y, str(ang)], ['fields_autoplaced', 'yes'],
                    ['effects', ['font', ['size', '1.27', '1.27']], ['justify', j]], ['uuid', nid()],
                    ['property', '"Intersheetrefs"', '"${INTERSHEET_REFS}"', ['at', X, Y, '0'], ['hide', 'yes'],
                     ['show_name', 'no'], ['do_not_autoplace', 'no'], ['effects', ['font', ['size', '1.27', '1.27']]]]])
    for x, y, just, size, txt in self.texts:
        X, Y = mm((x, y))
        f = fmt(FONT.get(size, 1.27))
        eff = ['effects', ['font', ['size', f, f]]]
        j = JUST.get(just, 'left')
        if j:
            eff.append(['justify', j])
        out.append(['text', qs(txt), ['exclude_from_sim', 'no'], ['at', X, Y, '0'], eff, ['uuid', nid()]])
    for key, node in self.inst.items():
        if key not in self.placed:
            raise SystemExit('KiCad part not placed: %s unit %d' % key)
        ang, mir, x, y = self.placed[key]
        X, Y = mm((x, y))
        at = find(node, 'at')
        at[1:4] = [X, Y, str(ang)]
        node[:] = [c for c in node if not (isinstance(c, list) and c[0] == 'mirror')]
        if mir:
            node.insert(node.index(at) + 1, ['mirror', mir])
        set_props(self, node, key)
        out.append(node)
    tmpl = self.power_templates['ltspice:GND']
    for n, g in enumerate(self.gnds, 1):
        x, y = g[:2]
        d = g[2] if len(g) > 2 else attach_dir(self, (x, y))
        node = copy.deepcopy(tmpl)
        X, Y = mm((x, y))
        find(node, 'at')[1:4] = [X, Y, str(DIR_GND.get(d, 0))]
        node[:] = [c for c in node if not (isinstance(c, list) and c[0] == 'mirror')]
        find(node, 'uuid')[1] = nid()
        ref = '"#GND%03d"' % n
        for p in findall(node, 'property'):
            find(p, 'at')[1:3] = [X, Y]
            if unq(p[1]) == 'Reference':
                p[2] = ref
        for pn in findall(node, 'pin'):
            find(pn, 'uuid')[1] = nid()
        find(find(find(find(node, 'instances'), 'project'), 'path'), 'reference')[1] = ref
        out.append(node)
    for c in root:
        if isinstance(c, list) and c[0] in ('sheet_instances', 'embedded_fonts'):
            out.append(c)
    open(path, 'w', encoding='utf-8', newline='\n').write(dump(out) + '\n')
    return out


def compare(path, refnet=REFNET):
    """net-by-net comparison of a written schematic against the original KiCad netlist"""
    root = parse(open(path, encoding='utf-8').read())
    nets, names, f, pins = kgeo.connectivity(root)
    comps, ref = knet.read(refnet)
    mine = {}
    for g, members in nets.items():
        ms = frozenset(m for m in members if not m[0].startswith('#'))
        if ms:
            mine[ms] = names.get(g, set())
    theirs = {frozenset((r, p) for r, p, _, _ in v): n for n, v in ref.items()}
    probs = []
    for ms, n in theirs.items():
        if ms not in mine:
            probs.append('net %s: pins %s not one net here' % (n, sorted(ms)[:8]))
        else:
            got = mine[ms]
            if n.startswith(('Net-(', 'unconnected-')):
                if got - NEW_NAMES:
                    probs.append('net %s gets name(s) %s' % (n, sorted(got)))
            elif n not in got:
                probs.append('net %s named %s here' % (n, sorted(got)))
    for ms in mine:
        if ms not in theirs:
            probs.append('extra net here: %s names %s' % (sorted(ms)[:8], sorted(mine[ms])))
    return probs


def main(out=OUT):
    import custom
    b = Builder().build()
    b.flags_to_items()
    b.lt_texts()
    custom.apply(b)
    b.connect_moved()
    b.sim_parts()
    b.trim()
    b.nettie()
    b.extras()
    b.noconnects()
    b.junctions_and_split()
    write(b, out)
    if '--no-declutter' not in sys.argv:
        import declutter
        moved, left = declutter.run(out)
        print('declutter: %d texts/labels moved, %d still touching something' % (moved, len(left)))
    for r in dict.fromkeys(b.report):
        print('note:', r)
    probs = compare(out)
    for p in probs:
        print('PROBLEM', p)
    print('%d problems; wrote %s' % (len(probs), out))
    return b


if __name__ == '__main__':
    main()
