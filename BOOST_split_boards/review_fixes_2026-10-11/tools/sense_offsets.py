"""LED-sense ground offsets from a gnd_heatmap.py run: each sense resistor's GND end (R52.2 / R53.2 / R7.2) minus the
card's ground, the mean of J10's GND pins (each pin = the mean voltage over its copper on every layer, as
gnd_heatmap.py's pad_potentials does). Rebuilt 2026-10-11 (the 10-02 script is gone); calibrated against the 10-02
U3 figures before use.

    python sense_offsets.py COPPER.json TAG_gndV.npz
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                                                 'power6_2026-10-01', 'tools')))
import solve_copper6 as SC

SENSE = (('R52', '2', 2.63), ('R53', '2', 2.37), ('R7', '2', 2.37))
SET_MV = {'R52': 131.5, 'R53': 118.5, 'R7': 118.5}     # 50 mOhm x 2.63 / 2.37 A


def pad_mean(p, V, g):
    vals = []
    for ln, polys in p['polys'].items():
        if ln in V:
            pm = SC.raster(polys, g['x0'], g['y0'], g['nx'], g['ny'], g['h'])
            v = V[ln][pm]
            vals.extend(v[np.isfinite(v)].tolist())
    return float(np.mean(vals)) if vals else float('nan')


def main():
    cop = json.load(open(sys.argv[1]))
    z = np.load(sys.argv[2])
    g = dict(x0=float(z['x0']), y0=float(z['y0']), h=float(z['h']), nx=int(z['nx']), ny=int(z['ny']))
    V = {str(ln): z['V_' + str(ln).replace('.', '_')] for ln in z['layers']}
    j10 = [pad_mean(p, V, g) for p in cop['pads'] if p['ref'] == 'J10' and p['net'] == 'GND']
    card = float(np.mean(j10))
    print('J10 GND pins: %d, %.2f-%.2f mV, mean %.2f mV' % (len(j10), min(j10), max(j10), card))
    out = {}
    for ref, num, _ in SENSE:
        p = [q for q in cop['pads'] if q['ref'] == ref and q['num'] == num][0]
        v = pad_mean(p, V, g)
        out[ref] = v - card
        print('  %-4s GND end %.2f mV, offset to card GND %.2f mV (%.2f %% of %.1f mV)'
              % (ref, v, v - card, 100 * (v - card) / SET_MV[ref], SET_MV[ref]))
    return out


if __name__ == '__main__':
    main()
