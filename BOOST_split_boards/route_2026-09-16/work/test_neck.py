import json
# 20 mm x 4 mm strip with a 1 mm-wide, L mm-long constriction in the middle (1 oz outer), pads at both ends
def case(L, name):
    left = [[0, 0], [9.5 - L / 2, 0], [9.5 - L / 2, 4], [0, 4]]
    neck = [[9.5 - L / 2 - 0.05, 1.5], [10.5 + L / 2 - 1 + 0.05, 1.5], [10.5 + L / 2 - 1 + 0.05, 2.5], [9.5 - L / 2 - 0.05, 2.5]]
    right = [[10.5 + L / 2 - 1, 0], [20, 0], [20, 4], [10.5 + L / 2 - 1, 4]]
    pa = [[-2, 0], [0, 0], [0, 4], [-2, 4]]
    pb = [[20, 0], [22, 0], [22, 4], [20, 4]]
    return {name: {'F.Cu': [left, neck, right, pa, pb]}}, [
        dict(ref=name + 'A', num='1', net=name, polys={'F.Cu': [pa]}, x=-1, y=2, drill=0),
        dict(ref=name + 'B', num='1', net=name, polys={'F.Cu': [pb]}, x=21, y=2, drill=0)]
nets, pads = {}, []
for L, nm in ((1.0, 'N1'), (5.0, 'N5')):
    n, p = case(L, nm)
    nets.update(n); pads += p
json.dump(dict(layers=[], nets=nets, barrels=[], pads=pads), open('work/test_neck_cop.json', 'w'))
json.dump([dict(name='neck 1mm', net='N1', I=5.0, src=[['N1A', '1']], snk=[['N1B', '1']], grid=0.05),
           dict(name='neck 5mm', net='N5', I=5.0, src=[['N5A', '1']], snk=[['N5B', '1']], grid=0.05)],
          open('work/test_neck_br.json', 'w'))
print('expected neck rise (1 mm wide, 5 A, 1 oz outer): %.1f C' % ((5 / (0.048 * (0.035 * 1550.0031) ** 0.725)) ** (1 / 0.44)))
print('expected 4 mm section rise: %.1f C' % ((5 / (0.048 * (4 * 0.035 * 1550.0031) ** 0.725)) ** (1 / 0.44)))
