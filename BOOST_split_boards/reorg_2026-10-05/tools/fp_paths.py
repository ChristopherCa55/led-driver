"""Footprints of a .kicad_pcb and their symbol links: python fp_paths.py BOARD.kicad_pcb [SCHEMATIC.kicad_sch]

Prints the footprints without a (path ...) and, with a schematic, whether each path's symbol uuid exists there and
carries the same reference.
"""
import re, sys

t = open(sys.argv[1], encoding='utf-8').read()
fps = []
for m in re.finditer(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', t, re.S):
    body = m.group(2)
    ref = re.search(r'\(property "Reference" "([^"]*)"', body)
    path = re.search(r'\n\t\t\(path "([^"]*)"\)', body)
    fps.append((ref.group(1) if ref else '?', m.group(1), path.group(1) if path else None))
print(len(fps), 'footprints,', sum(1 for f in fps if f[2] is None), 'without a path')
print('without:', sorted(f[0] for f in fps if f[2] is None))
if len(sys.argv) > 2:
    s = open(sys.argv[2], encoding='utf-8').read()
    sym = {}
    for b in re.findall(r'\n\t\(symbol\n(.*?)\n\t\)', s, re.S):
        u = re.search(r'\n\t\t\(uuid "([^"]+)"\)', b).group(1)
        r = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        sym[u] = r
    bad = [(r, p) for r, _, p in fps if p and sym.get(p.split('/')[-1]) != r]
    print('paths whose symbol is missing or has another reference:', bad[:20], len(bad))
