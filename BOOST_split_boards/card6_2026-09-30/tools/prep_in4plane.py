"""Base board for the In4-plane re-route, in the 8-layer frame (old layer names; make_card6.py later turns old In5
into the 6-layer card's In4). Text edit only.

    python prep_in4plane.py CARD_8L.kicad_pcb OUT.kicad_pcb

- U2 In+'s run moves from In5 to In4, same geometry: nothing of another net lies within 2 mm of it on In4 (the old
  open plan kept In4 solid GND over the run).
- Every other non-GND track on In5 is removed: In5 becomes the solid GND plane.
- The In3 tracks of 0A_hi, 0err_hi, Verr1 and Net-(D5-+) are removed: the band over the In+ run on In3 becomes a
  local GND shield, so these nets are re-routed round it.
The router then reconnects the islands left behind; dangling stubs and vias are pruned first.
"""
import re, sys
from collections import Counter

MOVE_UP = 'Net-(U2-In+)'
CLEAR_IN3 = {'0A_hi', '0err_hi', 'Verr1', 'Net-(D5-+)'}
# --inp-on-plane (variant B): In+ keeps its In5 run inside the plane layer; In3 is left alone
if '--inp-on-plane' in sys.argv:
    MOVE_UP = None
    CLEAR_IN3 = set()
t = open(sys.argv[1], encoding='utf-8', newline='').read().replace('\r\n', '\n')
pat = re.compile(r'\t\(segment\n(?:\t\t[^\n]*\n)*?\t\)\n')
moved, removed, kept = Counter(), Counter(), 0


def edit(m):
    global kept
    s = m.group(0)
    layer = re.search(r'\(layer "([^"]+)"\)', s).group(1)
    net = re.search(r'\(net "((?:[^"\\]|\\.)*)"\)', s).group(1)
    if layer == 'In5.Cu' and net == MOVE_UP:
        moved[net] += 1
        return s.replace('(layer "In5.Cu")', '(layer "In4.Cu")')
    if layer == 'In5.Cu' and net in ('GND', 'Net-(U2-In+)'):
        kept += 1
        return s
    if layer == 'In5.Cu':
        removed[('In5', net)] += 1
        return ''
    if layer == 'In3.Cu' and net in CLEAR_IN3:
        removed[('In3', net)] += 1
        return ''
    kept += 1
    return s


t = pat.sub(edit, t)
open(sys.argv[2], 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n'))
print('moved to In4:', dict(moved))
print('removed: In5 %d segments of %d nets; In3 %d segments of %d nets' % (
    sum(v for k, v in removed.items() if k[0] == 'In5'), len({k[1] for k in removed if k[0] == 'In5'}),
    sum(v for k, v in removed.items() if k[0] == 'In3'), len({k[1] for k in removed if k[0] == 'In3'})))
print('segments kept:', kept)
