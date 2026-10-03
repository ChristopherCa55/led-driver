"""Control card: 1 oz -> 0.5 oz inner copper (2026-10-01). Text edit of the board file's stackup and thickness only.

    python set_stackup_05oz.py IN.kicad_pcb OUT.kicad_pcb

Writes JLCPCB's standard 6-layer 1.6 mm, 1 oz outer / 0.5 oz inner stackup (the "No requirement" build for that
copper choice, read from jlcpcb.com/impedance on 2026-10-01):
  0.035 Cu / 3313 0.0994 / 0.0152 Cu / core 0.55 / 0.0152 Cu / 2116 0.1164 / 0.0152 Cu / core 0.55 / 0.0152 Cu /
  3313 0.0994 / 0.035 Cu = 1.5468 mm.
Dielectric constants from the same page: 3313 4.1, 2116 4.16, core 4.6.
Nothing else changes: no track, via, zone or footprint is touched (copper thickness does not enter KiCad's DRC or
zone fill), so no refill is needed.
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


P3313, P2116, CORE = ('0.0994', '3313', '4.1'), ('0.1164', '2116', '4.16'), ('0.55', 'Core', '4.6')
STACK6H = (cu('F.Cu', '0.035') + diel(1, 'prepreg', [P3313]) + cu('In1.Cu', '0.0152') + diel(2, 'core', [CORE]) +
           cu('In2.Cu', '0.0152') + diel(3, 'prepreg', [P2116]) + cu('In3.Cu', '0.0152') +
           diel(4, 'core', [CORE]) + cu('In4.Cu', '0.0152') + diel(5, 'prepreg', [P3313]) + cu('B.Cu', '0.035'))
THICK = '1.5468'

t = open(sys.argv[1], encoding='utf-8', newline='').read().replace('\r\n', '\n')
assert t.count('(4 "In1.Cu" signal)') == 1 and '"In5.Cu"' not in t, 'not the 6-layer card'
s0 = t.index('\n\t(setup') + 1
s1 = block_end(t, s0)
head, setup, body = t[:s0], t[s0:s1], t[s1:]
assert head.count('\t\t(thickness 1.609)\n') == 1, 'expected the 1 oz card (1.609 mm)'
head = head.replace('\t\t(thickness 1.609)\n', '\t\t(thickness %s)\n' % THICK)
i = setup.index('\t\t\t(layer "F.Cu"')
j = block_end(setup, setup.index('\t\t\t(layer "B.Cu"') + 3) + 1
old = setup[i:j]
assert old.count('(thickness 0.03)') == 4, 'expected 1 oz inner copper'
setup = setup[:i] + STACK6H + setup[j:]
out = head + setup + body
open(sys.argv[2], 'w', encoding='utf-8', newline='').write(out.replace('\n', '\r\n'))
print('wrote', sys.argv[2], 'thickness', THICK)
