"""Record standoff positions (from H5-H8 in the layout) and the screwed FETs in a result file.

  python pstand.py RESULT.json OUT.json [M1,M8,M9,M10]
"""
import sys, json

res = json.load(open(sys.argv[1]))
lay = res['layout']
res['standoffs'] = [lay[h][:2] for h in ('H5', 'H6', 'H7', 'H8') if h in lay]
res['screwed'] = (sys.argv[3] if len(sys.argv) > 3 else 'M1,M8,M9,M10').split(',')
json.dump(res, open(sys.argv[2], 'w'), indent=1)
print('standoffs', [[round(v, 1) for v in s] for s in res['standoffs']], 'screwed', res['screwed'])
