"""Compact per-branch table from solver JSON: python summarise.py A_B.json A_C.json [B_B.json B_C.json]"""
import json, sys
def load(p):
    return {r['name']: r for r in json.load(open(p))}
sets = [(load(sys.argv[i]), load(sys.argv[i + 1])) for i in range(1, len(sys.argv), 2)]
names = [n for n in sets[0][0] if not n.startswith('loop')]
hdr = '%-26s %6s' % ('branch', 'I')
for k in range(len(sets)):
    hdr += ' | %-44s' % ('set %d: neck C (len) long / worst via x [over]  1oz || 2oz' % (k + 1))
print(hdr)
for n in names:
    row = '%-26s %6.2f' % (n[:26], sets[0][0][n]['I'])
    for rb, rc in sets:
        cells = []
        for r in (rb[n], rc[n]):
            nk, lg = r.get('neck', {}), r.get('neck_long', {})
            wv = r['worst_vias'][0]['ratio'] if r.get('worst_vias') else 0
            cells.append('%5.1f(%4.1f) %5.1f %4.2fx[%d]' % (nk.get('rise', 0), nk.get('length', 0), lg.get('rise', 0), wv, r.get('vias_over', 0)))
        row += ' | ' + ' || '.join(cells)
    print(row)
