"""List pads (and courtyards) inside a region, per side: python region.py DUMP x0 y0 x1 y1 [F|B|THT]"""
import json, sys
d = json.load(open(sys.argv[1]))
x0, y0, x1, y1 = map(float, sys.argv[2:6])
want = sys.argv[6] if len(sys.argv) > 6 else None
rows = []
for f in d['footprints']:
    for p in f['pads']:
        bx0, by0, bx1, by1 = p['bbox']
        if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
            continue
        kind = 'THT' if p['drill'] > 0 else f['side']
        if want and kind != want and not (want in 'FB' and kind == 'THT'):
            continue
        rows.append((kind, f['ref'] + '.' + p['num'], p['net'][:14], '%.2f-%.2f' % (bx0, bx1), '%.2f-%.2f' % (by0, by1)))
for r in sorted(rows, key=lambda r: (r[0], float(r[4].split('-')[0]))):
    print('%-3s %-8s %-14s x %-13s y %s' % r)
