"""Compare two KiCad s-expression netlists by content, not by net code.

  netdiff.py A.net B.net

Components are compared by reference (value, footprint). Nets are matched by
their node sets, so a renamed net with the same pins shows as a rename, and a
net whose pins changed shows the pins added/removed.
"""
import re, sys


def load(path):
    t = open(path, encoding='utf8', errors='replace').read()
    comps = {}
    for m in re.finditer(r'\(comp\s+\(ref\s+"([^"]+)"\)\s*\(value\s+"([^"]*)"\)(?:\s*\(footprint\s+"([^"]*)"\))?', t):
        comps[m.group(1)] = (m.group(2), m.group(3) or '')
    nets = {}
    i = t.find('(nets')
    for blk in re.split(r'\(net\s+\(code', t[i:])[1:]:
        name = re.search(r'\(name\s+"((?:[^"\\]|\\.)*)"\)', blk).group(1)
        nodes = frozenset('%s.%s' % (a, b) for a, b in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', blk))
        nets[name] = nodes
    return comps, nets


ca, na = load(sys.argv[1])
cb, nb = load(sys.argv[2])
print('components: %d -> %d' % (len(ca), len(cb)))
for r in sorted(set(ca) - set(cb)):
    print('   removed %-6s %s' % (r, ca[r]))
for r in sorted(set(cb) - set(ca)):
    print('   added   %-6s %s' % (r, cb[r]))
for r in sorted(set(ca) & set(cb)):
    if ca[r] != cb[r]:
        print('   changed %-6s %s -> %s' % (r, ca[r], cb[r]))
print('nets: %d -> %d' % (len(na), len(nb)))
by_nodes_b = {v: k for k, v in nb.items()}
matched_b = set()
for name, nodes in sorted(na.items()):
    if name in nb and nb[name] == nodes:
        matched_b.add(name); continue
    if nodes in by_nodes_b:
        print('   renamed %s -> %s (%d pins)' % (name, by_nodes_b[nodes], len(nodes)))
        matched_b.add(by_nodes_b[nodes]); continue
    if name in nb:
        add, rem = nb[name] - nodes, nodes - nb[name]
        print('   net %s: +%s -%s' % (name, sorted(add), sorted(rem)))
        matched_b.add(name); continue
    # best overlap
    best = max(nb.items(), key=lambda kv: len(kv[1] & nodes)) if nb else None
    if best and best[1] & nodes:
        print('   net %s -> %s: +%s -%s' % (name, best[0], sorted(best[1] - nodes), sorted(nodes - best[1])))
        matched_b.add(best[0])
    else:
        print('   net %s gone (%s)' % (name, sorted(nodes)))
for name in sorted(set(nb) - matched_b):
    if name not in na:
        print('   new net %s (%s)' % (name, sorted(nb[name])))
