import json, math, subprocess, sys
# 1) 10 mm x 2 mm strip on F.Cu between two 2x2 pads (pads outside the strip length)
strip = [[0, 0], [10, 0], [10, 2], [0, 2]]
padA = [[-2, 0], [0, 0], [0, 2], [-2, 2]]
padB = [[10, 0], [12, 0], [12, 2], [10, 2]]
cop = dict(layers=[], nets={'T': {'F.Cu': [strip, padA, padB]}}, barrels=[],
           pads=[dict(ref='A', num='1', net='T', polys={'F.Cu': [padA]}, x=-1, y=1, drill=0),
                 dict(ref='B', num='1', net='T', polys={'F.Cu': [padB]}, x=11, y=1, drill=0)])
# 2) two-layer: F strip 0..5, via at 5, B strip 5..10, one 0.4 via
f2 = [[0, 0], [5.5, 0], [5.5, 2], [0, 2]]
b2 = [[4.5, 0], [10, 0], [10, 2], [4.5, 2]]
cop['nets']['U'] = {'F.Cu': [f2, padA], 'B.Cu': [b2, padB]}
cop['barrels'].append(dict(net='U', x=5.0, y=1.0, drill=0.4, dia=0.8, kind='via', layers=['F.Cu', 'B.Cu']))
cop['pads'] += [dict(ref='C', num='1', net='U', polys={'F.Cu': [padA]}, x=-1, y=1, drill=0),
                dict(ref='D', num='1', net='U', polys={'B.Cu': [padB]}, x=11, y=1, drill=0)]
json.dump(cop, open('work/test_cop.json', 'w'))
br = [dict(name='strip', net='T', I=5.0, src=[['A', '1']], snk=[['B', '1']], grid=0.05),
      dict(name='via', net='U', I=0.5, src=[['C', '1']], snk=[['D', '1']], grid=0.05)]
json.dump(br, open('work/test_br.json', 'w'))
rho = 1.72e-5
print('expected strip R %.3f mOhm, IPC rise 5 A on 2 mm 1 oz outer %.1f C' % (rho * 10 / (2 * 0.035) * 1e3,
      (5 / (0.048 * (2 * 0.035 * 1550.0031) ** 0.725)) ** (1 / 0.44)))
Rv = rho * 1.6 / (math.pi * 0.38 * 0.02)
print('expected via test R approx %.3f mOhm (strips) + %.3f (barrel, 1.6 mm)' % (rho * 10 / (2 * 0.035) * 1e3, Rv * 1e3))
