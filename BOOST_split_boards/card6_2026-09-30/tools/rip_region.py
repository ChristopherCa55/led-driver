"""Regional rip-up (text edit): remove every track with an end inside a box, and every via inside it, except for
fixed nets. The nets' copper outside the box stays as islands for route_card_in4.py to join again.

    python rip_region.py BOARD_IN.kicad_pcb BOARD_OUT.kicad_pcb X0,Y0,X1,Y1 [--keep NET,NET,...]

Always fixed: GND, 5V, analog_5V and the sensitive nets (Current, Net-(U2-In+), V_err).
"""
import re, sys
from collections import Counter

FIXED = {'GND', '5V', 'analog_5V', 'Current', 'Net-(U2-In+)', 'V_err'}
if '--keep' in sys.argv:
    FIXED |= set(sys.argv[sys.argv.index('--keep') + 1].split(','))
x0, y0, x1, y1 = map(float, sys.argv[3].split(','))
t = open(sys.argv[1], encoding='utf-8', newline='').read().replace('\r\n', '\n')
blk = re.compile(r'\t\((segment|via)\n(?:\t\t[^\n]*\n)*?\t\)\n')
gone = Counter()


def inside(x, y):
    return x0 <= x <= x1 and y0 <= y <= y1


def edit(m):
    s = m.group(0)
    net = re.search(r'\(net "((?:[^"\\]|\\.)*)"\)', s).group(1)
    if net in FIXED:
        return s
    pts = [(float(a), float(b)) for a, b in re.findall(r'\((?:start|end|at) ([-\d.]+) ([-\d.]+)\)', s)]
    if any(inside(x, y) for x, y in pts):
        gone[(m.group(1), net)] += 1
        return ''
    return s


t = blk.sub(edit, t)
open(sys.argv[2], 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n'))
nets = sorted({n for _, n in gone})
print('removed %d segments, %d vias of %d nets' % (sum(v for k, v in gone.items() if k[0] == 'segment'),
                                                   sum(v for k, v in gone.items() if k[0] == 'via'), len(nets)))
print(','.join(nets))
