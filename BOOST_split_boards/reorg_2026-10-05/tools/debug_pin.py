"""Debug: list power-symbol kinds, and what sits on the net of given pins.  python debug_pin.py SCH REF:PIN ..."""
import sys, os, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ksch

sch = ksch.Sch(sys.argv[1])
kinds = collections.Counter((s['lib_id'], s['value']) for s in sch.syms if s['power'])
print('power symbols:', dict(kinds))
f, pp = ksch.connectivity(sch)
for arg in sys.argv[2:]:
    ref, pin = arg.split(':')
    s = next(s for s in sch.syms if s['ref'] == ref)
    pt = pp[(sch.key(s), pin)]
    root = f(pt)
    print(arg, 'at', pt)
    for t in sch.syms:
        for n, name, x, y, et, hid in sch.pins(t):
            if f((ksch.rnd(x), ksch.rnd(y))) == root:
                print('   ', t['ref'], t['lib_id'], t['value'], 'pin', n, name, (x, y), 'hidden' if hid else '')
    for l in sch.labels:
        if f((ksch.rnd(l['x']), ksch.rnd(l['y']))) == root:
            print('    label', l['kind'], l['name'])
