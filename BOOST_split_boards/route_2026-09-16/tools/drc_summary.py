"""Summarise a kicad-cli DRC JSON report: counts by type/severity, every error with its items, unconnected pairs.

usage: python drc_summary.py REPORT.json [--brief]
"""
import json, sys, collections

r = json.load(open(sys.argv[1]))
brief = '--brief' in sys.argv
c = collections.Counter((v['type'], v['severity']) for v in r['violations'])
print(dict(c))
if not brief:
    for v in r['violations']:
        if v['severity'] == 'error':
            print('  %-16s %-42s | %s' % (v['type'], v['description'][:42],
                  ' || '.join('%s @(%.2f,%.2f)' % (i['description'][:55], i['pos']['x'], i['pos']['y']) for i in v['items'])))
print('unconnected', len(r['unconnected_items']))
if not brief:
    for u in r['unconnected_items']:
        print('  U', ' || '.join('%s @(%.2f,%.2f)' % (i['description'][:55], i['pos']['x'], i['pos']['y']) for i in u['items']))
