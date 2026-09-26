"""Power copper, version 2 (writes copper_v8.json). Changes from v1, from the v1 solve:

- no foreign via walls across the LX pour on In2 (C86 vias in rows along the flow, fields moved off the column);
- rsense_lo: thin F.Cu corridor removed; F.Cu and via rows between R1's force pads; a B.Cu path above U19;
- Vin inner copper widened north of R1.1 (rsense_lo inner copper stops at x 73); F.Cu strip C85.1 -> C69;
- M1.3 fed on F.Cu and B.Cu from the east; M1.2 / M7.2 wrapped on F.Cu;
- every rail FET drain pin (M2.2, M3.2, M4.2) fed from more layers, both sides where the pin row allows;
- LX at M6.2 with bigger F/B via fields; LX under M5 with its via field next to M5.2.
Layer plan unchanged: In1/In6 GND only, LX only on F.Cu / In2 / B.Cu, In4 left for the 5 V plane.
"""
import json

Z, V = [], []


def zone(net, layers, rects, prio, clr=0.3, name=''):
    Z.append(dict(net=net, layers=layers if isinstance(layers, list) else [layers], rects=rects, prio=prio,
                  clearance=clr, name=name or net))


def grid(net, x0, y0, x1, y1, pitch, dia=0.8, drill=0.4, name=''):
    n = int(round((x1 - x0) / pitch)) + 1
    m = int(round((y1 - y0) / pitch)) + 1
    for i in range(n):
        for j in range(m):
            x = x0 + i * (x1 - x0) / max(n - 1, 1)
            y = y0 + j * (y1 - y0) / max(m - 1, 1)
            V.append(dict(net=net, x=round(x, 3), y=round(y, 3), dia=dia, drill=drill, field=name or net))


def big(net, x0, y0, x1, y1, pitch=0.8, name=''):
    grid(net, x0, y0, x1, y1, pitch, dia=0.9, drill=0.5, name=name)


def edge_field(net, xs, ys, heavy, name=''):
    # 0.6 mm drill where heavy(x, y) is true (edges facing the current), 0.5 mm elsewhere
    for x in xs:
        for y in ys:
            h = heavy(x, y)
            V.append(dict(net=net, x=round(x, 3), y=round(y, 3), dia=1.0 if h else 0.9, drill=0.6 if h else 0.5,
                          field=name))


def pts(net, points, dia=0.8, drill=0.4, name=''):
    for x, y in points:
        V.append(dict(net=net, x=x, y=y, dia=dia, drill=drill, field=name or net))


BOARD = [30, 30, 104, 116]
INNER_POWER = ['In2.Cu', 'In3.Cu', 'In5.Cu']
# ---------------------------------------------------------------- GND planes and fills (lowest priority)
zone('GND', ['In1.Cu', 'In6.Cu'], [BOARD], 0, 0.25, 'GND planes')
zone('GND', ['F.Cu', 'In2.Cu', 'In3.Cu', 'In5.Cu', 'B.Cu'], [BOARD], 1, 0.3, 'GND fill')

# ---------------------------------------------------------------- rsense_lo  R1.4 -> L1.2
zone('rsense_lo', 'F.Cu', [[58.5, 36.2, 65.2, 44.9], [68.0, 31.4, 74.2, 37.0], [68.0, 37.0, 74.2, 38.55]], 20)
zone('rsense_lo', INNER_POWER, [[52.0, 30.3, 73.0, 38.6], [52.0, 30.3, 65.4, 45.3]], 20)
zone('rsense_lo', 'B.Cu', [[50.0, 30.3, 63.1, 43.5], [62.0, 30.3, 74.6, 33.0]], 20, name='rsense_lo B above U19')
edge_field('rsense_lo', [68.8, 69.65, 70.5, 71.35], [32.3, 33.15, 34.0, 34.85, 35.7, 36.55, 37.4, 38.25],
           lambda x, y: False, name='R1.4 pad')
edge_field('rsense_lo', [59.35, 60.2, 61.05, 61.9, 62.75 - 0.15], [37.0 + 0.85 * k for k in range(9)],
           lambda x, y: False, name='L1.2 pad')

# ---------------------------------------------------------------- Vin  J1 + C40/C69/C85 -> R1.1
VIN_IN = [[73.4, 30.3, 86.0, 47.3], [66.2, 38.9, 73.4, 47.3], [81.8, 41.7, 104, 82.3], [97.6, 82.3, 104, 87.3]]
zone('Vin', 'F.Cu', [[68.0, 39.4, 74.2, 46.4], [66.4, 44.7, 68.6, 46.4]], 20, name='Vin R1.1')
zone('Vin', 'F.Cu', [[79.3, 42.2, 90.8, 47.3]], 20, name='Vin C69')
zone('Vin', 'F.Cu', [[79.0, 59.7, 83.7, 62.7]], 20, name='Vin C85')
zone('Vin', 'F.Cu', [[80.5, 72.5, 94.6, 82.4], [94.6, 77.75, 104, 87.3], [94.3, 82.4, 104, 87.3]], 20,
     name='Vin C40-J1')
zone('Vin', ['In3.Cu', 'In5.Cu'], VIN_IN, 18)
zone('Vin', 'In2.Cu', [[73.4, 30.3, 86.0, 45.9], [66.2, 38.9, 73.4, 45.9], [86, 41.7, 104, 45.9],
                       [97.4, 45.9, 104, 87.3]], 18)
zone('Vin', 'B.Cu', [[94.0, 77.8, 104, 87.5]], 18, name='Vin J1 bottom')
edge_field('Vin', [68.8, 69.65, 70.5, 71.35, 72.25], [39.85, 40.7, 41.55, 42.4, 43.25, 44.1],
           lambda x, y: False, name='R1.1 pad')
edge_field('Vin', [68.8, 69.65, 70.5], [44.95, 45.8], lambda x, y: False, name='R1.1 pad south')
pts('Vin', [(67.5, 45.5)], name='R1.1 pad')
grid('Vin', 79.8, 42.7, 90.3, 45.7, 1.0, name='C69 area')
grid('Vin', 86.9, 75.9, 86.9, 79.4, 0.85, name='C40.1 pad')
grid('Vin', 97.8, 78.3, 103.5, 87.0, 1.2, name='J1 field')
big('Vin', 79.6, 60.45, 82.3, 61.95, 0.9, name='C85.1 pad')
grid('Vin', 88.5, 78.0, 93.9, 81.8, 1.35, name='C40-J1 row')

# ---------------------------------------------------------------- GND at the input and at M1.3
zone('GND', 'F.Cu', [[83.6, 48.0, 92.3, 59.6], [84.3, 59.6, 104, 72.2], [92.3, 52.5, 104, 59.6],
                     [94.7, 69.9, 104, 77.4]], 15, name='GND input caps')
zone('GND', 'F.Cu', [[79.1, 49.9, 84.0, 59.4]], 16, name='GND M1.3 to C69.2 F')
zone('GND', 'B.Cu', [[71.3, 50.0, 79.0, 54.5], [79.2, 49.8, 86.0, 57.6]], 15, name='GND M1.3 B')
zone('GND', 'B.Cu', [[94.0, 68.0, 104, 77.5]], 15, name='GND J2 bottom')
grid('GND', 79.65, 52.8, 79.65, 55.2, 0.8, name='M1.3 east column')
grid('GND', 85.55, 51.4, 85.55, 54.6, 0.8, name='C69.2 pad')
grid('GND', 84.1, 51.4, 84.1, 54.6, 0.8, name='C69.2 pad west')
big('GND', 91.3, 60.4, 91.3, 62.0, 0.8, name='C85.2 pad')
grid('GND', 86.9, 67.5, 86.9, 71.0, 0.85, name='C40.2 pad')
grid('GND', 102.8, 53.8, 102.8, 61.4, 1.9, name='U16 tab east edge')
grid('GND', 92.2, 70.3, 94.2, 77.0, 1.1, name='J2 west')

# ---------------------------------------------------------------- switch node
zone('LX', 'F.Cu', [[58.5, 48.2, 69.1, 57.3], [69.1, 51.45, 72.2, 54.85], [72.2, 46.8, 76.2, 60.2],
                    [64.9, 57.3, 72.2, 63.9], [58.5, 57.3, 64.9, 57.4],
                    [76.2, 47.3, 81.0, 49.6], [76.2, 58.1, 81.0, 59.65]], 20, name='LX F L1-M1-M7')
zone('LX', 'F.Cu', [[47.98, 60.3, 50.5, 66.3]], 20, name='LX F M6')
zone('LX', 'In2.Cu', [[56.5, 46.3, 80.0, 61.0], [79.0, 46.3, 97.0, 87.7], [47.0, 46.3, 58.5, 63.8],
                      [47.9, 63.8, 50.5, 66.4], [87.2, 87.7, 89.9, 90.2],
                      [53.03, 63.8, 58.5, 72.0], [47.95, 66.4, 53.1, 72.0],
                      [80.8, 87.7, 84.74, 93.5], [84.0, 90.29, 89.82, 93.5],
                      [56.5, 61.0, 81.0, 72.0]], 20, name='LX In2')
zone('LX', 'B.Cu', [[71.3, 44.7, 79.3, 49.8]], 20, name='LX B D19-M1')
zone('LX', 'B.Cu', [[83.0, 68.0, 94.2, 87.75], [87.2, 87.7, 89.8, 90.3]], 20, name='LX B M5')
zone('LX', 'B.Cu', [[47.98, 64.0, 50.5, 72.0], [47.0, 66.5, 53.3, 72.0]], 20, name='LX B M6')
grid('LX', 59.3, 49.0, 64.4, 56.1, 0.85, name='L1.1 pad')
grid('LX', 72.7, 47.3, 75.7, 59.7, 1.0, name='LX F strip')
grid('LX', 85.0, 82.65, 90.2, 83.4, 0.86, name='LX B M5')
pts('LX', [(48.6, 61.0), (48.6, 61.85), (48.6, 62.7), (48.6, 63.55)], dia=0.9, drill=0.5, name='LX F M6')
pts('LX', [(50.1, 63.45)], name='LX F M6')
grid('LX', 51.3, 66.9, 53.0, 71.5, 0.85, name='LX B M6')

# ---------------------------------------------------------------- channel pairs (shared sources)
for net, r in (('m2_source', [75.9, 60.9, 79.1, 65.71]), ('m3_source', [43.0, 63.78, 47.8, 66.38]),
               ('m4_source', [89.82, 87.69, 94.86, 90.29])):
    zone(net, ['F.Cu', 'In2.Cu', 'In3.Cu', 'In5.Cu', 'B.Cu'], [r], 22, name=net + ' link')

# ---------------------------------------------------------------- Vout_1 (M2.2, C1, C72, C88, C86, C70, J3)
zone('Vout_1', 'F.Cu', [[65.5, 55.1, 76.2, 70.2], [76.2, 65.7, 79.2, 68.3]], 18, name='Vout_1 bank F')
zone('Vout_1', 'F.Cu', [[71.4, 85.2, 76.4, 88.4]], 18, name='Vout_1 C70 F')
zone('Vout_1', 'In3.Cu', [[65.5, 55.0, 81.5, 71.9], [51.0, 66.4, 65.5, 72.5], [51.0, 72.5, 55.7, 88.4],
                          [42.9, 84.9, 55.7, 88.4], [42.9, 88.4, 47.2, 110.6], [42.1, 110.3, 46.8, 115.2]], 18,
     name='Vout_1 In3 to J3')
zone('Vout_1', 'In5.Cu', [[65.5, 55.0, 72.0, 70.2], [71.5, 62.5, 81.5, 71.9], [78.9, 71.9, 81.5, 88.3],
                          [71.5, 79.6, 81.5, 88.3]], 18, name='Vout_1 In5 bank+C70')
zone('Vout_1', 'B.Cu', [[60.0, 62.0, 76.17, 71.9]], 18, name='Vout_1 B under M2')
grid('Vout_1', 66.9, 64.65, 70.3, 66.25, 0.8, name='C88.1 pad')
pts('Vout_1', [(69.9, 59.1), (70.65, 59.1), (71.4, 59.1), (69.9, 55.6), (70.65, 55.6), (71.4, 55.6)],
    name='C86.1 pad')
grid('Vout_1', 73.4, 69.0, 75.1, 69.0, 0.85, name='C1.1 pad')
pts('Vout_1', [(73.2, 63.2), (73.2, 64.0)], name='C72.1 pad')
grid('Vout_1', 72.1, 86.0, 75.6, 87.6, 0.85, name='C70.1 pad')

# ---------------------------------------------------------------- Vout_2 (M3.2, C73, C3, C78, C87, C71, J8)
zone('Vout_2', 'F.Cu', [[30.3, 59.0, 43.0, 63.2], [30.3, 62.8, 35.7, 70.5], [40.3, 61.5, 42.7, 67.3],
                        [42.5, 66.0, 47.85, 75.0], [39.0, 74.3, 51.0, 85.0]], 18, name='Vout_2 bank F')
zone('Vout_2', 'In5.Cu', [[30.3, 66.4, 55.5, 94.6], [30.3, 55.0, 42.87, 63.8], [30.3, 62.5, 37.8, 66.4],
                          [40.36, 63.8, 42.87, 66.4], [39.4, 94.6, 47.2, 102.4], [30.3, 102.4, 47.2, 109.2],
                          [30.3, 102.4, 36.5, 110.5]], 18, name='Vout_2 In5 to J8')
zone('Vout_2', ['In2.Cu', 'In3.Cu'], [[36.0, 55.0, 42.87, 63.8], [40.36, 63.8, 42.87, 66.4]], 18,
     name='Vout_2 In2/In3 at M3')
zone('Vout_2', 'B.Cu', [[38.0, 50.0, 43.0, 63.8], [40.33, 63.8, 42.9, 66.4]], 18, name='Vout_2 B under M3')
pts('Vout_2', [(33.65, 63.95)], dia=0.9, drill=0.5, name='C73.1 pad')
big('Vout_2', 31.2, 59.8, 35.2, 62.4, 0.9, name='Vout_2 F north strip')
pts('Vout_2', [(33.5, 69.45), (34.2, 69.45)], name='C3.1 pad')
grid('Vout_2', 40.9, 60.6, 42.3, 62.7, 0.7, name='M3.2 north field')
grid('Vout_2', 38.6, 55.5, 42.4, 59.6, 1.25, name='Vout_2 B field')
grid('Vout_2', 39.4, 79.4, 42.9, 80.7, 0.85, name='C71.1 pad')
grid('Vout_2', 48.8, 75.5, 50.1, 79.0, 0.85, name='C78.1 pad')
grid('Vout_2', 48.6, 80.5, 49.9, 84.0, 0.85, name='C87.1 pad')
grid('Vout_2', 43.2, 67.0, 47.2, 73.8, 1.35, name='Vout_2 F field')

# ---------------------------------------------------------------- Vout_3 (M4.2, C4, C76, C74, C77, C75, J5)
zone('Vout_3', 'F.Cu', [[88.0, 85.4, 97.5, 87.69], [94.6, 86.95, 97.5, 90.3], [88.4, 90.3, 97.6, 94.3],
                        [83.2, 94.3, 97.6, 100.9], [94.6, 100.9, 97.7, 106.5]], 18, name='Vout_3 bank F')
zone('Vout_3', ['In3.Cu', 'In5.Cu'], [[89.5, 82.6, 97.44, 90.3], [88.4, 85.8, 97.44, 87.69], [83.0, 90.3, 104, 106.3], [71.8, 99.6, 81.3, 115.7],
                                     [64.2, 111.15, 81.3, 115.7], [81.3, 99.6, 98, 106.0]], 18,
     name='Vout_3 inner to J5')
zone('Vout_3', 'In2.Cu', [[91.0, 90.4, 104, 106.3], [94.86, 87.9, 97.44, 90.4]], 18, name='Vout_3 In2 at M4')
zone('Vout_3', 'B.Cu', [[92.9, 90.3, 100.0, 107.5], [94.86, 87.7, 97.44, 90.3]], 18, name='Vout_3 B under M4')
big('Vout_3', 91.2, 86.4, 92.8, 86.4, 0.8, name='C4.1 pad')
pts('Vout_3', [(94.2, 86.3), (94.2, 87.1), (88.9, 86.55)], name='C4/C76 link')
grid('Vout_3', 90.1, 95.3, 93.5, 96.35, 0.85, name='C74.1 pad')
grid('Vout_3', 84.0, 97.4, 87.4, 98.45, 0.85, name='C77.1 pad')
grid('Vout_3', 95.55, 102.3, 96.8, 105.7, 0.85, name='C75.1 pad')
grid('Vout_3', 89.0, 91.0, 96.8, 99.8, 1.3, name='Vout_3 F field')
grid('Vout_3', 94.0, 91.2, 99.2, 94.4, 1.05, name='Vout_3 B south of M4.2')

# ---------------------------------------------------------------- LED sinks
zone('Net-(M10-S)', 'F.Cu', [[50.9, 94.8, 56.1, 97.3]], 22)
zone('Net-(M9-S)', 'F.Cu', [[39.3, 87.9, 43.1, 90.9]], 22)
zone('Net-(M8-S)', 'F.Cu', [[60.4, 99.4, 64.2, 104.5]], 22)
zone('Output1_drain', 'B.Cu', [[46.0, 97.3, 50.9, 110.8], [46.0, 97.3, 53.5, 99.8], [46.0, 110.5, 53.2, 115.2]], 20)
zone('Output2_drain', 'B.Cu', [[36.8, 86.0, 43.2, 109.3], [36.8, 109.0, 41.8, 113.8]], 20)
zone('Output3_drain', 'B.Cu', [[58.3, 101.3, 60.2, 110.6], [53.7, 110.9, 60.2, 115.7]], 20)
zone('Output3_drain', 'F.Cu', [[58.5, 101.0, 60.35, 111.4], [56.5, 110.9, 60.35, 113.0]], 20)
for field, (x0, y0, x1, y1) in (('R52.2', (61.06, 94.9, 61.06, 97.1)), ('R53.2', (40.1, 96.05, 42.3, 96.05)),
                                ('R7.2', (61.2, 109.55, 63.4, 109.55))):
    grid('GND', x0, y0, x1, y1, 0.8, name=field + ' pad')

# ---------------------------------------------------------------- GND vias at the bank capacitors
for field, (x0, y0, x1, y1, p) in {
        'C1.2 pad': (73.4, 66.0, 75.1, 66.0, 0.85), 
        'C88.2 pad': (58.5, 64.65, 61.9, 66.25, 0.85), 'C86.2 pad': (69.9, 47.2, 71.4, 47.2, 0.75),
        'C70.2 pad': (80.5, 86.0, 84.0, 87.6, 0.85), 
        'C3.2 pad': (33.85, 67.55, 33.85, 67.55, 1), 'C78.2 pad': (48.8, 67.1, 50.1, 70.6, 0.85),
        'C87.2 pad': (48.6, 92.4, 49.9, 92.4, 0.65), 'C71.2 pad': (31.0, 79.4, 34.5, 80.7, 0.85),
         'C76.2 pad': (88.9, 84.64, 88.9, 84.64, 1),
        'C74.2 pad': (98.4, 95.3, 101.9, 96.35, 0.85), 'C77.2 pad': (75.6, 97.4, 79.0, 98.45, 0.85),
        'C75.2 pad': (95.55, 110.7, 96.8, 114.1, 0.85)}.items():
    grid('GND', x0, y0, x1, y1, p, name=field)
big('GND', 91.25, 83.45, 92.95, 83.45, 0.85, name='C4.2 pad')
pts('GND', [(94.25, 83.45)], name='C4.2 east')
pts('GND', [(75.1, 63.3), (75.1, 63.9)], dia=0.6, drill=0.3, name='C72.2 pad')
pts('GND', [(36.3, 63.85), (37.0, 63.85)], name='C73.2 pad')



def corner(v):
    # field corners facing the incoming current draw several times the average barrel current: leave them empty
    f, x, y = v['field'], v['x'], v['y']
    return ((f == 'L1.2 pad' and x > 61.5 and y < 38.0) or (f == 'R1.4 pad' and x < 69.8 and y > 37.0)
            or (f == 'R1.1 pad' and x > 71.0 and y < 40.8))


V = [v for v in V if not corner(v)]
json.dump(dict(zones=Z, vias=V), open('copper_v8.json', 'w'), indent=1)
print('zones %d, vias %d' % (len(Z), len(V)))
