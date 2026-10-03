"""Summarise a kicad-cli DRC JSON report and compare it with the accepted baseline of BOOST_power_RC2.

    python drc_summary.py REPORT.drc.json

Accepted baseline (shipped board, 2026-09-24 fab README, re-measured 2026-09-29): 0 errors, 0 unconnected items and
exactly these 49 warnings:
    46 x silk_over_copper   (the logos under L1)
     2 x silk_overlap       (C87/C71 and C86/C88 can outlines)
     1 x lib_footprint_mismatch (J10, 1.05 mm drill)
Prints PASS only if the report matches that exactly. Anything else is listed item by item.
"""
import sys, json
from collections import Counter
d = json.load(open(sys.argv[1], encoding='utf-8'))
v = d['violations']
unc = d['unconnected_items']
errors = [x for x in v if x['severity'] == 'error']
cnt = Counter((x['severity'], x['type']) for x in v)
print('errors %d, warnings %d, unconnected %d, schematic parity items %d' % (
    len(errors), sum(1 for x in v if x['severity'] == 'warning'), len(unc), len(d.get('schematic_parity', []))))
for k, n in sorted(cnt.items()):
    print('  %-8s %-26s %d' % (k[0], k[1], n))
expect = {('warning', 'silk_over_copper'): 46, ('warning', 'silk_overlap'): 2, ('warning', 'lib_footprint_mismatch'): 1}
ok = not errors and not unc and dict(cnt) == expect
known_overlaps = [{'C87', 'C71'}, {'C86', 'C88'}]
for x in v:
    refs = {w for i in x['items'] for w in i['description'].replace(',', ' ').split() if w[:1] in 'CDRJMUL' and w[1:].isdigit()}
    if x['type'] == 'silk_overlap' and refs in known_overlaps:
        continue
    if x['type'] == 'lib_footprint_mismatch' and 'J10' in json.dumps(x):
        continue
    if x['type'] == 'silk_over_copper' and not any(r in json.dumps(x) for r in ('D28', 'D29', 'D30', 'R47')):
        continue
    ok = False
    print('NOT IN BASELINE: %s %s %s' % (x['severity'], x['type'], x['description']))
    for i in x['items']:
        print('      %s at %s' % (i['description'], i.get('pos')))
for u in unc:
    print('UNCONNECTED: ' + ' | '.join('%s at %s' % (i['description'], i.get('pos')) for i in u['items']))
print('PASS - matches the accepted baseline' if ok else 'FAIL - does not match the accepted baseline')
