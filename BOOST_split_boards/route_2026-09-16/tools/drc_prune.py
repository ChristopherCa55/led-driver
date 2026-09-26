"""Read a KiCad DRC JSON report; add the positions of vias involved in errors to a blacklist; summarise.

usage: python drc_prune.py REPORT.json BLACKLIST.json [--dry]
A via is blacklisted when a violation of error severity (clearance, hole clearance, hole-to-hole, edge,
shorting, ...) names it, or when KiCad reports it dangling. In a via-to-via violation only one via goes.
"""
import json, sys, collections

rep = json.load(open(sys.argv[1]))
bl_path = sys.argv[2]
dry = '--dry' in sys.argv
try:
    black = set(tuple(p) for p in json.load(open(bl_path)))
except Exception:
    black = set()
counts = collections.Counter()
added = 0
for v in rep.get('violations', []):
    counts[(v['type'], v['severity'])] += 1
    vias = [it for it in v.get('items', []) if it.get('description', '').startswith('Via')]
    if not vias:
        continue
    if v['severity'] == 'error' or v['type'] in ('via_dangling', 'hole_to_hole'):
        it = vias[-1]
        key = (round(it['pos']['x'], 2), round(it['pos']['y'], 2))
        if key not in black:
            black.add(key)
            added += 1
print('violations:', dict(counts))
print('unconnected items:', len(rep.get('unconnected_items', [])))
print('vias blacklisted this pass: %d (total %d)' % (added, len(black)))
if not dry:
    json.dump(sorted(black), open(bl_path, 'w'))
