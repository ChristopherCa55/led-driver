"""Power board, 8 layers -> 6 layers (2026-10-01 trial). Text edit of a COPY of the board; no track, via or
footprint moves. Adapted from ../../card6_2026-09-30/make_card6.py.

    python make_power6.py IN.kicad_pcb OUT.kicad_pcb VARIANT STACKUP

VARIANT
  A  drop In4 (the "5V plane" zone) and In6 (the In6 half of the "GND planes" zone); In5 becomes In4.
     The 5V net is then unconnected until it is routed as tracks.
  B  drop In1 and In6 (the whole "GND planes" zone); In2-In5 become In1-In4.
STACKUP  a JLC 6-layer 1.6 mm 1 oz / 1 oz stackup name from stackups.py (e.g. JLC061611-7628).

Handles: zones (plane zones, their fills, the 8 all-layer keepouts), tracks, vias' zone_layer_connections, the layer
table, the board thickness and the stackup. Asserts that nothing is left on a dropped layer. Zone fills must be
recomputed afterwards (kicad-cli pcb drc --refill-zones --save-board).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stackups import STACKS

BS = chr(92)
INNER = ['In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu']
MAPS = {
    'A': {'In1.Cu': 'In1.Cu', 'In2.Cu': 'In2.Cu', 'In3.Cu': 'In3.Cu', 'In4.Cu': None, 'In5.Cu': 'In4.Cu', 'In6.Cu': None},
    'B': {'In1.Cu': None, 'In2.Cu': 'In1.Cu', 'In3.Cu': 'In2.Cu', 'In4.Cu': 'In3.Cu', 'In5.Cu': 'In4.Cu', 'In6.Cu': None},
}


def block_end(t, i):
    depth, j = 0, i
    while True:
        c = t[j]
        if c == '"':
            j += 1
            while t[j] != '"':
                j += 2 if t[j] == BS else 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1


def cu(name, th):
    return '\t\t\t(layer "%s"\n\t\t\t\t(type "copper")\n\t\t\t\t(thickness %s)\n\t\t\t)\n' % (name, th)


def diel(n, kind, th):
    return ('\t\t\t(layer "dielectric %d"\n\t\t\t\t(type "%s")\n\t\t\t\t(thickness %s)\n\t\t\t\t(material "FR4")\n'
            '\t\t\t\t(epsilon_r 4.4)\n\t\t\t\t(loss_tangent 0.02)\n\t\t\t)\n' % (n, kind, th))


src, dst, variant, stack = sys.argv[1:5]
M = MAPS[variant]
g = STACKS[stack]
STACK6 = (cu('F.Cu', '0.035') + diel(1, 'prepreg', g[0]) + cu('In1.Cu', '0.03') + diel(2, 'core', g[1]) +
          cu('In2.Cu', '0.03') + diel(3, 'prepreg', g[2]) + cu('In3.Cu', '0.03') + diel(4, 'core', g[3]) +
          cu('In4.Cu', '0.03') + diel(5, 'prepreg', g[4]) + cu('B.Cu', '0.035'))
THICK = '%.3f' % (sum(g) + 2 * 0.035 + 4 * 0.03)
dropped = [k for k, v in M.items() if v is None]

t = open(src, encoding='utf-8', newline='').read().replace('\r\n', '\n')
assert t.count('(14 "In6.Cu" signal)') == 1, 'not the 8-layer power board'

# 1. zones
out, pos, nz_del, nz_mod = [], 0, 0, 0
for m in re.finditer(r'\n\t\(zone\n', t):
    a = m.start() + 1
    if a < pos:
        continue
    b = block_end(t, a)
    z = t[a:b]
    lm = re.search(r'\n\t\t\(layers? ([^)]*)\)', z)
    lays = re.findall(r'"([^"]+)"', lm.group(1))
    keep = [l for l in lays if l not in dropped]
    out.append(t[pos:a])
    if not keep:
        nz_del += 1
        print('deleted zone', re.search(r'\(name "([^"]*)"\)', z).group(1) if '(name' in z else lays)
        pos = b + 1 if t[b] == '\n' else b
        continue
    if len(keep) != len(lays):
        nz_mod += 1
        z = z[:lm.start()] + '\n\t\t(%s %s)' % ('layers' if len(keep) > 1 else 'layer',
                                                ' '.join('"%s"' % l for l in keep)) + z[lm.end():]
        # drop the fill blocks of dropped layers
        for L in dropped:
            while True:
                k = z.find('(filled_polygon\n\t\t\t(layer "%s")' % L)
                if k < 0:
                    break
                k0 = z.rfind('\n', 0, k)
                z = z[:k0] + z[block_end(z, k):]
        assert not any('"%s"' % L in z for L in dropped), 'zone still on a dropped layer'
    out.append(z)
    pos = b
out.append(t[pos:])
t = ''.join(out)
print('zones deleted %d, modified %d' % (nz_del, nz_mod))

# 2. vias: zone_layer_connections lose the dropped layers
def fix_zlc(m):
    lays = [l for l in re.findall(r'"([^"]+)"', m.group(1)) if l not in dropped]
    return '(zone_layer_connections %s)' % ' '.join('"%s"' % l for l in lays) if lays else '(zone_layer_connections)'
t, nzlc = re.subn(r'\(zone_layer_connections([^)]*)\)', fix_zlc, t)
print('via zone_layer_connections rewritten:', nzlc)

# 3. split off the head (layer table) and the setup (stackup)
s0 = t.index('\n\t(setup') + 1
s1 = block_end(t, s0)
head, setup, body = t[:s0], t[s0:s1], t[s1:]
for L in dropped:
    assert '"%s"' % L not in body, 'something still on %s' % L

# 4. body: renumber the kept inner layers (placeholders first, so the renames cannot chain)
for old, new in M.items():
    if new is not None:
        body = body.replace('"%s"' % old, '"@@%s@@"' % new)
body = re.sub(r'"@@(In\d\.Cu)@@"', r'"\1"', body)
assert 'In5.Cu' not in body and 'In6.Cu' not in body

# 5. layer table and thickness
for ln in ('\t\t(4 "In1.Cu" signal)\n', '\t\t(6 "In2.Cu" signal)\n', '\t\t(8 "In3.Cu" signal)\n',
           '\t\t(10 "In4.Cu" signal)\n', '\t\t(12 "In5.Cu" signal)\n', '\t\t(14 "In6.Cu" signal)\n'):
    assert head.count(ln) == 1, ln
for ln in ('\t\t(12 "In5.Cu" signal)\n', '\t\t(14 "In6.Cu" signal)\n'):
    head = head.replace(ln, '')
assert head.count('\t\t(thickness 1.654)\n') == 1
head = head.replace('\t\t(thickness 1.654)\n', '\t\t(thickness %s)\n' % THICK)

# 6. stackup
i = setup.index('\t\t\t(layer "F.Cu"')
j = block_end(setup, setup.index('\t\t\t(layer "B.Cu"') + 3) + 1
setup = setup[:i] + STACK6 + setup[j:]

t = head + setup + body
assert 'In5.Cu' not in t and 'In6.Cu' not in t
open(dst, 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n'))
print('wrote %s: variant %s, %s, %s mm (zone fills still to be recomputed)' % (dst, variant, stack, THICK))
