# Board temperature rise at U16's tab from the battery current alone (U16 itself off), 2026-10-01.
# Vin: J1 lug -> R1 (input shunt). GND: M1 source + the three LED shunt returns -> J2 lug.
# Full power at 18 V in: outputs 2.635 A x 23.3 V + 2 x 2.371 A x 33.1 V = 218 W; 95 % efficiency assumed
#   -> 12.75 A from the battery; M1 carries 12.75 - 7.38 = 5.37 A on average.
# Plus an assumed 0.1 W contact loss at each battery lug (not known; about 0.6 mOhm at 12.75 A).
# Usage: python tools/run_background.py COPPER.json CONFIG h [--save NAME]
import sys
import numpy as np
sys.path.insert(0, 'tools')
from raster import load
from run_board import setup
from vias import TABS, CONFIGS
from joule import solve_net, pad_cells

fn, cfg, h = sys.argv[1], sys.argv[2], float(sys.argv[3])
d = load(fn)
m, cells, added, (xs, ys) = setup(d, cfg)
A = m.a * 1e3
x0, y0 = xs[0] - A / 2, ys[0] - A / 2
nets = {}
for li, ln in enumerate(d['layers']):
    pass
# rebuild the net-id map the same way raster.rasterize does
from raster import rasterize
_, _, netnames, arr, _ = rasterize(d, A)
netid = {n: i for i, n in enumerate(netnames)}
ALL = list(range(m.nl))


def barrels_for(net):
    out = []
    for v in d['vias']:
        if v['net'] == net:
            iy, ix = m.cell(v['x'], v['y'], x0, y0)
            out.append((iy, ix, [li for li, ln in enumerate(d['layers']) if ln in v['flash']], v['drill']))
    for p in d['pth']:
        if p['net'] == net:
            iy, ix = m.cell(p['x'], p['y'], x0, y0)
            out.append((iy, ix, ALL, p['drill']))
    if net == 'GND':
        for x, y in CONFIGS[cfg][1]:
            iy, ix = m.cell(x, y, x0, y0)
            out.append((iy, ix, ALL, 0.4))
    return out


fp = {f['ref']: f for f in d['footprints']}
I_IN, I_M1 = 12.75, 5.37
I_OUT = {'R7': 2.635, 'R52': 2.371, 'R53': 2.371}
J1 = fp['J1']; J2 = fp['J2']
r1_pads = [(p['x'], p['y']) for p in fp['R1']['pads'] if p['net'] == 'Vin']
q_vin, p_vin, dv_vin = solve_net(
    m, netid['Vin'], barrels_for('Vin'),
    [(pad_cells(m, x0, y0, J1['x'], J1['y'], 3.5, ALL), I_IN)],
    [c for (x, y) in r1_pads for c in pad_cells(m, x0, y0, x, y, 1.0, [0])])
inj = [(pad_cells(m, x0, y0, fp['M1']['pads'][2]['x'] if fp['M1']['pads'][2]['net'] == 'GND' else
                  [p for p in fp['M1']['pads'] if p['net'] == 'GND'][0]['x'],
                  [p for p in fp['M1']['pads'] if p['net'] == 'GND'][0]['y'], 1.0, ALL), I_M1)]
for ref, cur in I_OUT.items():
    p = [p for p in fp[ref]['pads'] if p['net'] == 'GND'][0]
    inj.append((pad_cells(m, x0, y0, p['x'], p['y'], 1.5, [0]), cur))
q_gnd, p_gnd, dv_gnd = solve_net(m, netid['GND'], barrels_for('GND'), inj,
                                 pad_cells(m, x0, y0, J2['x'], J2['y'], 3.5, ALL))
print('Vin plane loss %.3f W (drop %.1f mV), GND plane loss %.3f W (drop %.1f mV)'
      % (p_vin, dv_vin * 1e3, p_gnd, dv_gnd * 1e3))
# heat of other parts on this board whose losses follow from BOM values (18 V in, full power):
#   R7/R52/R53 50 mOhm at 2.635/2.371/2.371 A; R1 1 mOhm at 12.75 A;
#   U17 and U1 (L78L05 from Vin, 18 -> 5 V): 8 mA + 6 mA max quiescent, and 3 mA + 6 mA;
#   gate drivers U8/U10/U15/U19: the 12 V rail's 16 mA (simulated) x 12 V.
# Not included: L1 (winding resistance not in the files) and the FETs (their tabs sit on the case).
PARTS = {'R7': 2.635 ** 2 * 0.05, 'R52': 2.371 ** 2 * 0.05, 'R53': 2.371 ** 2 * 0.05, 'R1': 12.75 ** 2 * 0.001,
         'U17': 13 * 0.014, 'U1': 13 * 0.009, 'U8': 0.048, 'U10': 0.048, 'U15': 0.048, 'U19': 0.048}
q_lug = np.zeros(m.nl * m.nc)
for J in (J1, J2):
    cs = [c for c in pad_cells(m, x0, y0, J['x'], J['y'], 3.5, [0]) if m.idx[c[1], c[2]] >= 0]
    for l, iy, ix in cs:
        q_lug[m.node(l, iy, ix)] += 0.1 / len(cs)
q_parts = np.zeros(m.nl * m.nc)
for ref, pw in PARTS.items():
    f = fp[ref]
    lay = [m.nl - 1] if f['side'] == 'B' else [0]
    cs = [c for p in f['pads'] for c in pad_cells(m, x0, y0, p['x'], p['y'], 0.6, lay) if m.idx[c[1], c[2]] >= 0]
    for l, iy, ix in cs:
        q_parts[m.node(l, iy, ix)] += pw / len(cs)
print('parts heat %.2f W: %s' % (sum(PARTS.values()), ', '.join('%s %.2f' % kv for kv in PARTS.items())))
import scipy.sparse.linalg as spla
m.build(h, h)
lu = spla.splu(m.K, permc_spec='MMD_AT_PLUS_A')
res = {}
for name, qq in (('planes', q_vin + q_gnd), ('lugs', q_lug), ('parts', q_parts)):
    full = np.zeros(m.N); full[:len(qq)] = qq
    T = lu.solve(full)
    res[name] = (np.mean([T[m.node(0, iy, ix)] for iy, ix in cells]), T)
tot = sum(v[0] for v in res.values())
print('%s h=%.0f: rise at the U16 tab: battery current in copper %.2f K, lug contacts %.2f K, other parts %.2f K, '
      'total %.2f K' % (cfg, h, res['planes'][0], res['lugs'][0], res['parts'][0], tot))
if '--save' in sys.argv:
    name = sys.argv[sys.argv.index('--save') + 1]
    T = res['planes'][1] + res['lugs'][1] + res['parts'][1]
    np.savez_compressed('work/bg_%s.npz' % name, F=m.layer_map(T, 0), xs=xs, ys=ys, tab=tot,
                        split=np.array([res['planes'][0], res['lugs'][0], res['parts'][0]]))
