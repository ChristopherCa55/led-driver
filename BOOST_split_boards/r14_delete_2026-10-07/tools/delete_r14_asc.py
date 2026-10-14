"""Delete R14 from a shipped-layout LTspice BOOST.asc.

    python delete_r14_asc.py IN.asc OUT.asc

Removes the R14 symbol, plus only the wires and ground flags that served nothing but R14's two pins (followed
outward from those pins). Applied as a line-level edit, so every other line of the file stays byte-for-byte as it was.
Approved by the user on 2026-10-07.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ltspice_layout_2026-10-05',
                                'tools'))
from ascmodel import Asc, on_interior

a = Asc(sys.argv[1])
r14 = next(s for s in a.syms if s.name == 'R14')
todo = [(x, y) for _, x, y in a.pins(r14)]
a.syms = [s for s in a.syms if s is not r14]
removed_w, removed_f = [], []

while todo:
    p = todo.pop()
    ends = [w for w in a.wires if (w[0], w[1]) == p or (w[2], w[3]) == p]
    pins = {(x, y) for s in a.syms for _, x, y in a.pins(s)}
    on_wire = any(on_interior(p, w) for w in a.wires)
    flags = [f for f in a.flags if (f[0], f[1]) == p]
    if p in pins or on_wire or len(ends) > 1:
        continue                          # p still joins other things: stop here
    if not ends:
        for f in flags:                   # a flag sitting only on R14's pin goes too
            a.flags.remove(f)
            removed_f.append(f)
        continue
    if flags and flags[0][2] != '0':
        continue                          # never drop a named label
    w = ends[0]
    a.wires.remove(w)
    removed_w.append(w)
    for f in flags:
        a.flags.remove(f)
        removed_f.append(f)
    todo.append((w[2], w[3]) if (w[0], w[1]) == p else (w[0], w[1]))

lines = open(sys.argv[1], encoding='latin-1', newline='').read().split('\n')
drop = set()
for i, l in enumerate(lines):
    if l.startswith('SYMBOL '):
        j = i + 1
        while j < len(lines) and lines[j].startswith(('SYMATTR ', 'WINDOW ')):
            j += 1
        if any(lines[k].rstrip('\r') == 'SYMATTR InstName R14' for k in range(i + 1, j)):
            drop.update(range(i, j))
for w in removed_w:
    cands = ('WIRE %d %d %d %d' % w, 'WIRE %d %d %d %d' % (w[2], w[3], w[0], w[1]))
    drop.update(i for i, l in enumerate(lines) if l.rstrip('\r') in cands)
for f in removed_f:
    hits = [i for i, l in enumerate(lines) if l.rstrip('\r') == 'FLAG %d %d %s' % (f[0], f[1], f[2])]
    assert len(hits) == 1, f
    drop.update(hits)
open(sys.argv[2], 'w', encoding='latin-1', newline='').write('\n'.join(l for i, l in enumerate(lines) if i not in drop))
print('R14 removed (%d lines dropped); wires removed %s; flags removed %s' % (len(drop), removed_w, removed_f))
