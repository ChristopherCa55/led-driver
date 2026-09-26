"""Merge router output into a copper export for quick measurements (system Python): tracks and vias only; zones and
fills stay as exported, so use it for path lengths and pairing, not for copper solves.

usage: python merge_routes.py BASE_CU.json ROUTES.json OUT_CU.json
"""
import json, sys

cu = json.load(open(sys.argv[1]))
rt = json.load(open(sys.argv[2]))
cu['tracks'] = cu.get('tracks', []) + rt['tracks']
cu['vias'] = cu['vias'] + [dict(net=v['net'], x=v['x'], y=v['y'], dia=v['dia'], drill=v['drill'], layers=v['layers']) for v in rt['vias']]
json.dump(cu, open(sys.argv[3], 'w'))
print('merged %d tracks, %d vias' % (len(rt['tracks']), len(rt['vias'])))
