"""Side-by-side IPC-2221 results of solve_copper(6).py runs (DC branches; the 'loop' branches carry pulse current).

    python compare_solves6.py NAME=SOLVE.json [NAME=SOLVE.json ...]

Per branch: resistance, the worst neck rise (any length; per the ipc2221-short-necks note this is reported, not judged,
when the neck is under about 5 mm) and the long-neck rise (the worst neck at least 2 mm long), and vias over rating.
"""
import json, sys

runs = [(a.split('=', 1)[0], {r['name']: r for r in json.load(open(a.split('=', 1)[1]))}) for a in sys.argv[1:]]
names = [n for n in runs[0][1]]
hdr = '%-28s %6s ' % ('branch', 'I (A)') + ' | '.join('%-34s' % n for n, _ in runs)
print(hdr)
print('%-28s %6s ' % ('', '') + ' | '.join('%-34s' % 'R mOhm / neck C (len) / long C / v>' for _ in runs))
for b in names:
    if b.startswith('loop'):
        continue
    row = '%-28s %6.2f ' % (b, runs[0][1][b]['I'])
    cells = []
    for _, r in runs:
        x = r.get(b)
        if not x or 'neck' not in x:
            cells.append('%-34s' % 'n/a')
            continue
        nk, nl = x['neck'], x.get('neck_long') or {}
        cells.append('%-34s' % ('%6.3f / %5.1f (%3.1f) / %5.1f / %d' % (
            x['R_mohm'], nk.get('rise', 0), nk.get('length', 0) or 0, nl.get('rise', 0), x.get('vias_over', 0))))
    print(row + ' | '.join(cells))
