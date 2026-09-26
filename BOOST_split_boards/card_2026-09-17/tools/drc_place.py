"""DRC verdict for an unrouted placement (system Python).

usage: python drc_place.py REPORT.json

Reads a kicad-cli DRC JSON report (run with --severity-all and --schematic-parity off) and prints the counts by
type and severity. Before routing every net is expected to be unconnected, so unconnected items are counted, not
failed. Every other violation at error severity fails the placement (exit status 1): courtyard overlaps, clearance,
shorting items, hole clearance, PTH inside a courtyard, mask bridges, items on the edge or in a keep-out, and so on.
Warnings (silkscreen) are listed for the silk pass; nothing is excluded or re-rated here.
"""
import collections, json, sys

r = json.load(open(sys.argv[1]))
c = collections.Counter((v['type'], v['severity']) for v in r['violations'])
err = [v for v in r['violations'] if v['severity'] == 'error']
for (t, s), n in sorted(c.items()):
    print('%-26s %-8s %d' % (t, s, n))
for v in err:
    print('  ERROR %-22s %s' % (v['type'], ' || '.join('%s @(%.2f,%.2f)' % (i['description'][:60], i['pos']['x'],
                                                                           i['pos']['y']) for i in v['items'])))
print('unconnected items: %d (expected before routing)' % len(r['unconnected_items']))
print('placement DRC: %s (%d errors, %d warnings)' % ('PASS' if not err else 'FAIL', len(err),
                                                     sum(1 for v in r['violations'] if v['severity'] == 'warning')))
sys.exit(1 if err else 0)
