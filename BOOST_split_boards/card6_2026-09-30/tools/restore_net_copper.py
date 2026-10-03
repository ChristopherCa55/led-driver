"""Put back tracks and vias of the given nets that exist in an earlier board but not in a later one (text edit).

    python restore_net_copper.py EARLIER.kicad_pcb LATER.kicad_pcb OUT.kicad_pcb NET,NET,...

Used for the In4-plane re-route: pruning removed the pad escapes (pad -> stub -> via) of nets whose middle section
had been taken out; their original escapes already met the sensitive-net rules, so they go back in and the router
only has to join the via ends. Items are matched on type, net, layer(s) and coordinates; UUIDs are kept.
"""
import re, sys

nets = set(sys.argv[4].split(','))
blk = re.compile(r'\t\((segment|via)\n(?:\t\t[^\n]*\n)*?\t\)\n')


def key(s):
    kind = s[2:s.index('\n')]
    net = re.search(r'\(net "((?:[^"\\]|\\.)*)"\)', s).group(1)
    geo = re.findall(r'\((?:start|end|at) ([-\d.]+) ([-\d.]+)\)', s)
    lay = re.search(r'\(layers? ([^)]*)\)', s).group(1)
    return kind, net, lay, tuple(geo)


early = open(sys.argv[1], encoding='utf-8', newline='').read().replace('\r\n', '\n')
later = open(sys.argv[2], encoding='utf-8', newline='').read().replace('\r\n', '\n')
have = {key(m.group(0)) for m in blk.finditer(later)}
add = [m.group(0) for m in blk.finditer(early) if key(m.group(0))[1] in nets and key(m.group(0)) not in have]
# insert before the first zone (tracks and vias come before zones in the file)
i = later.index('\n\t(zone') + 1
later = later[:i] + ''.join(add) + later[i:]
open(sys.argv[3], 'w', encoding='utf-8', newline='').write(later.replace('\n', '\r\n'))
from collections import Counter
print('restored:', dict(Counter((key(s)[1], key(s)[0]) for s in add)))
