"""Replace the stackup (and the board thickness) of a 6-layer board file with a JLC 6-layer stackup (text edit).

    python set_stack6.py BOARD.kicad_pcb STACKUP

Same stackup text as make_power6.py writes; copper is untouched, so no refill is needed for the copper itself.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stackups import STACKS

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


def diel(n, kind, th):
    return ('\t\t\t(layer "dielectric %d"\n\t\t\t\t(type "%s")\n\t\t\t\t(thickness %s)\n\t\t\t\t(material "FR4")\n'
            '\t\t\t\t(epsilon_r 4.4)\n\t\t\t\t(loss_tangent 0.02)\n\t\t\t)\n' % (n, kind, th))


p, stack = sys.argv[1], sys.argv[2]
g = STACKS[stack]
STACK6 = (cu('F.Cu', '0.035') + diel(1, 'prepreg', g[0]) + cu('In1.Cu', '0.03') + diel(2, 'core', g[1]) +
          cu('In2.Cu', '0.03') + diel(3, 'prepreg', g[2]) + cu('In3.Cu', '0.03') + diel(4, 'core', g[3]) +
          cu('In4.Cu', '0.03') + diel(5, 'prepreg', g[4]) + cu('B.Cu', '0.035'))
THICK = '%.3f' % (sum(g) + 2 * 0.035 + 4 * 0.03)
t = open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n')
assert '"In5.Cu"' not in t, 'not a 6-layer board'
s0 = t.index('\n\t(setup') + 1
s1 = block_end(t, s0)
head, setup, body = t[:s0], t[s0:s1], t[s1:]
i = setup.index('\t\t\t(layer "F.Cu"')
j = block_end(setup, setup.index('\t\t\t(layer "B.Cu"') + 3) + 1
setup = setup[:i] + STACK6 + setup[j:]
head, n = re.subn(r'\n\t\t\(thickness [\d.]+\)\n', '\n\t\t(thickness %s)\n' % THICK, head, count=1)
assert n == 1
open(p, 'w', encoding='utf-8', newline='').write((head + setup + body).replace('\n', '\r\n'))
print('%s: stackup %s, %s mm' % (p, stack, THICK))
