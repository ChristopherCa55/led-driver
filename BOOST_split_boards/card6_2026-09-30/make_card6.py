"""Control card, 8 layers -> 6 layers (2026-09-30). Text edit of the board file; no track, via or footprint moves.

    python make_card6.py IN.kicad_pcb OUT.kicad_pcb

- Deletes the GND plane zone on In1/In6 (those two layers carry no tracks).
- Renumbers In2-In5 as In1-In4 (tracks, zones, fills, all-layer keepouts).
- Drops In5/In6 from the layer table.
- Writes JLCPCB's standard 6-layer 1.6 mm, 1 oz outer / 1 oz inner stackup (JLC061611-7628, the "no requirement"
  build, read from jlcpcb.com/impedance on 2026-09-30): 0.035 Cu / 7628 0.203 / 0.03 Cu / core 0.25 / 0.03 Cu /
  7628 0.203 + 3313 0.107 + 7628 0.203 / 0.03 Cu / core 0.25 / 0.03 Cu / 7628 0.203 / 0.035 Cu = 1.609 mm.
  Dielectric constants from the same page: 7628 4.4, 3313 4.1, core 4.6.
The zone fills must be recomputed afterwards (kicad-cli pcb drc --refill-zones --save-board).
"""
import sys

BS = chr(92)


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


def diel(n, kind, plies):
    s = '\t\t\t(layer "dielectric %d"\n\t\t\t\t(type "%s")\n' % (n, kind)
    parts = ['\t\t\t\t(thickness %s)\n\t\t\t\t(material "%s")\n\t\t\t\t(epsilon_r %s)\n\t\t\t\t(loss_tangent 0.02)'
             % p for p in plies]
    return s + ' addsublayer\n'.join(parts) + '\n\t\t\t)\n'


P7628, P3313, CORE = ('0.203', '7628', '4.4'), ('0.107', '3313', '4.1'), ('0.25', 'Core', '4.6')
STACK6 = (cu('F.Cu', '0.035') + diel(1, 'prepreg', [P7628]) + cu('In1.Cu', '0.03') + diel(2, 'core', [CORE]) +
          cu('In2.Cu', '0.03') + diel(3, 'prepreg', [P7628, P3313, P7628]) + cu('In3.Cu', '0.03') +
          diel(4, 'core', [CORE]) + cu('In4.Cu', '0.03') + diel(5, 'prepreg', [P7628]) + cu('B.Cu', '0.035'))
THICK = '1.609'

t = open(sys.argv[1], encoding='utf-8', newline='').read().replace('\r\n', '\n')
assert t.count('(4 "In1.Cu" signal)') == 1 and t.count('(14 "In6.Cu" signal)') == 1, 'not the 8-layer card'
# 1. the In1/In6 GND plane
k = t.index('(layers "In1.Cu" "In6.Cu")')
a = t.rindex('\n\t(zone', 0, k) + 1
b = block_end(t, a)
lines = t[a:b].split('\n')
print('removed zone', lines[1].strip(), lines[2].strip())
t = t[:a] + t[b:].lstrip('\n')
s0 = t.index('\n\t(setup') + 1
s1 = block_end(t, s0)
head, setup, body = t[:s0], t[s0:s1], t[s1:]
# 2. body: renumber the inner layers
L8 = '(layers "F.Cu" "B.Cu" "In1.Cu" "In2.Cu" "In3.Cu" "In4.Cu" "In5.Cu" "In6.Cu")'
n8 = body.count(L8)
body = body.replace(L8, '@@L6@@')
assert 'In1.Cu' not in body and 'In6.Cu' not in body, 'In1/In6 still referenced'
for k in (2, 3, 4, 5):
    body = body.replace('"In%d.Cu"' % k, '"In%d.Cu"' % (k - 1))
body = body.replace('@@L6@@', '(layers "F.Cu" "B.Cu" "In1.Cu" "In2.Cu" "In3.Cu" "In4.Cu")')
print('all-layer keepout lists rewritten:', n8)
# 3. layer table and board thickness
for ln in ('\t\t(12 "In5.Cu" signal)\n', '\t\t(14 "In6.Cu" signal)\n'):
    assert head.count(ln) == 1
    head = head.replace(ln, '')
assert head.count('\t\t(thickness 1.654)\n') == 1
head = head.replace('\t\t(thickness 1.654)\n', '\t\t(thickness %s)\n' % THICK)
# 4. stackup: everything from F.Cu to the end of B.Cu
i = setup.index('\t\t\t(layer "F.Cu"')
j = block_end(setup, setup.index('\t\t\t(layer "B.Cu"') + 3) + 1
setup = setup[:i] + STACK6 + setup[j:]
t = head + setup + body
assert 'In5.Cu' not in t and 'In6.Cu' not in t
open(sys.argv[2], 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n'))
print('wrote', sys.argv[2], '(zone fills still to be recomputed)')
