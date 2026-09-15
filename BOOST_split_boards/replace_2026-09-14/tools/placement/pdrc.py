"""Summarise a kicad-cli DRC json for a placement review (no copper yet).

  python pdrc.py DRC.json

Placement-relevant types are listed item by item; routing types (unconnected, clearance between
unrouted pads of one net, silk) are only counted.
"""
import sys, json, collections

d = json.load(open(sys.argv[1], encoding='utf8'))
v = d.get('violations', [])
PLACE = {'courtyards_overlap', 'items_not_allowed', 'npth_inside_courtyard', 'pth_inside_courtyard',
         'copper_edge_clearance', 'hole_clearance', 'shorting_items', 'clearance', 'malformed_courtyard',
         'missing_courtyard', 'footprint_type_mismatch', 'lib_footprint_mismatch'}
cnt = collections.Counter(x['type'] for x in v)
print('DRC violations by type:', dict(cnt), '| unconnected', len(d.get('unconnected_items', [])))
for x in v:
    if x['type'] in PLACE:
        items = '; '.join(i.get('description', '')[:70] for i in x.get('items', []))
        print('  %-24s %s' % (x['type'], items))
