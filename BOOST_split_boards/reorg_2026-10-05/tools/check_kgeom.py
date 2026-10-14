"""Check ksch.py's geometric connectivity against KiCad's own netlist.  python check_kgeom.py SCH NETLIST

Groups pins by geometry (wires, junctions, points on wire interiors), then merges groups that share a label name,
power symbols by their value, and hidden power-input pins by their pin name (KiCad's implicit connections). The
resulting pin partition must equal the netlist's (real parts only; references starting with # are ignored).
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ksch, knet

sch = ksch.Sch(sys.argv[1])
comps, kpins, knets = knet.load(sys.argv[2])
f, pin_point = ksch.connectivity(sch)

par = {}


def F(a):
    par.setdefault(a, a)
    while par[a] != a:
        par[a] = par[par[a]]
        a = par[a]
    return a


def U(a, b):
    par[F(a)] = F(b)


for l in sch.labels:
    U(('pt', f((ksch.rnd(l['x']), ksch.rnd(l['y'])))), ('name', l['name']))
for s in sch.syms:
    for n, name, x, y, et, hid in sch.pins(s):
        root = ('pt', f((ksch.rnd(x), ksch.rnd(y))))
        if s['power'] and s['value'] != 'PWR_FLAG':      # PWR_FLAG marks a net as driven; it does not name it
            U(root, ('name', s['value']))
        elif hid and et == 'power_in':
            U(root, ('name', name))
# pins of real parts -> group
geo = collections.defaultdict(set)
for s in sch.syms:
    if s['power']:
        continue
    for n, name, x, y, et, hid in sch.pins(s):
        geo[F(('pt', f((ksch.rnd(x), ksch.rnd(y)))))].add((s['ref'], n))
geo_part = {frozenset(v) for v in geo.values()}
net_part = {frozenset((r, p) for r, p in v if not r.startswith('#')) for v in knets.values()}
net_part = {s for s in net_part if s}
# compare partitions over the pins both know
allg = set().union(*geo_part)
alln = set().union(*net_part)
print('pins: geometry %d, netlist %d, only geometry %d, only netlist %d' % (len(allg), len(alln), len(allg - alln),
                                                                          len(alln - allg)))
print('  only in netlist (first 10):', sorted(alln - allg)[:10])
gmap = {p: g for g in geo_part for p in g}
nmap = {p: g for g in net_part for p in g}
bad = [p for p in allg & alln if (gmap[p] & alln) != (nmap[p] & allg)]
print('pins whose net differs: %d' % len(bad))
seen = set()
for p in sorted(bad):
    g, n = gmap[p] & alln, nmap[p] & allg
    if (g, n) in seen:
        continue
    seen.add((g, n))
    print('  %s: geometry-only %s | netlist-only %s' % (p, sorted(g - n)[:8], sorted(n - g)[:8]))
    if len(seen) > 12:
        break
