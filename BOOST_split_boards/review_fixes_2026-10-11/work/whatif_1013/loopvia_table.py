"""Loop-via cost / benefit per location (2026-10-13): every branch's R, neck, long-neck, vias over rating and worst
via ratio, base (step06b = the copy's power board) against each what-if solve that exists.

    python loopvia_table.py            (from this folder; writes loopvia_table.txt)
"""
import json, os

H = os.path.dirname(os.path.abspath(__file__))
SOLVES = [('base', os.path.join(H, '..', 'step06b', 'power_solve.json'))] + \
         [(v, os.path.join(H, v + '_solve.json')) for v in ('ch1', 'ch3', 'vout3') if os.path.exists(os.path.join(H, v + '_solve.json'))]
data = {k: {b['name']: b for b in json.load(open(p))} for k, p in SOLVES}
names = list(data['base'])


def fmt(b):
    w = b.get('worst_vias') or [{}]
    return '%6.3f %5.1f %5.1f %2d %5.2fx' % (b['R_mohm'], b['neck']['rise'], b['neck_long']['rise'], b.get('vias_over', 0),
                                            w[0].get('ratio', 0) if w[0] else 0)


out = ['branch'.ljust(30) + ' | '.join(k.center(30) for k, _ in SOLVES),
       ' ' * 30 + ' | '.join('R mOhm  neck long ov  worst'.center(30) for _ in SOLVES)]
for n in names:
    row = n[:30].ljust(30)
    cells = []
    for k, _ in SOLVES:
        b = data[k].get(n)
        cells.append(fmt(b).center(30) if b else '-'.center(30))
    changed = any(data[k].get(n) and fmt(data[k][n]) != fmt(data['base'][n]) for k, _ in SOLVES[1:])
    out.append(row + ' | '.join(cells) + ('   <- changed' if changed else ''))
# worst via per loop branch, with its position
out.append('')
for n in names:
    if not n.lower().startswith('loop'):
        continue
    for k, _ in SOLVES:
        b = data[k].get(n)
        if b and b.get('worst_vias'):
            w = b['worst_vias'][:3]
            out.append('%-28s %-6s ' % (n[:28], k) + '; '.join('(%.2f, %.2f) d%.2f %.2f A %.2fx' % (v['x'], v['y'], v['drill'], v['I'], v['ratio']) for v in w))
open(os.path.join(H, 'loopvia_table.txt'), 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
