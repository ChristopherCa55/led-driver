"""Before/after table of two solver runs on the same branches (system Python).

usage: python compare_solves.py BEFORE.json AFTER.json [--md]

One row per non-loop branch: resistance, worst neck (rise at IPC-2221, width, length, layer), worst via
(current / rating) and vias over rating, before -> after. Rows whose neck rise or worst via got worse by more than
2 C or 0.05x are flagged. With --md the table is printed as Markdown.
"""
import json, sys

a = {r['name']: r for r in json.load(open(sys.argv[1]))}
b = {r['name']: r for r in json.load(open(sys.argv[2]))}
md = '--md' in sys.argv


def via(r):
    return r['worst_vias'][0]['ratio'] if r.get('worst_vias') else 0.0


rows = []
for n, ra in a.items():
    if n.startswith('loop') or n not in b or 'error' in ra or 'error' in b[n]:
        continue
    rb = b[n]
    na, nb = ra.get('neck', {}), rb.get('neck', {})
    worse = (nb.get('rise', 0) - na.get('rise', 0) > 2.0) or (via(rb) - via(ra) > 0.05)
    rows.append((n, ra['I'], ra['R_mohm'], rb['R_mohm'], na, nb, via(ra), via(rb), ra.get('vias_over', 0),
                 rb.get('vias_over', 0), worse))
if md:
    print('| Branch | I (A) | R (mΩ) | Neck rise °C (width mm, length mm, layer) | Worst via × rating (vias over) |')
    print('|---|---|---|---|---|')
    for n, I, r0, r1, na, nb, v0, v1, o0, o1, worse in rows:
        f = lambda k: '%.1f (%.2f, %.1f, %s)' % (k.get('rise', 0), k.get('width', 0), k.get('length', 0),
                                                k.get('layer', '-').replace('.Cu', ''))
        print('| %s%s | %.2f | %.3f → %.3f | %s → %s | %.2f (%d) → %.2f (%d) |' % (
            '**' if worse else '', n + ('**' if worse else ''), I, r0, r1, f(na), f(nb), v0, o0, v1, o1))
else:
    for n, I, r0, r1, na, nb, v0, v1, o0, o1, worse in rows:
        print('%s %-28s %5.2f A  R %.3f -> %.3f mOhm | neck %5.1f C w %5.2f -> %5.1f C w %5.2f (%s) | via %.2fx[%d] -> %.2fx[%d]' % (
            '!' if worse else ' ', n, I, r0, r1, na.get('rise', 0), na.get('width', 0), nb.get('rise', 0),
            nb.get('width', 0), nb.get('layer', '-'), v0, o0, v1, o1))
