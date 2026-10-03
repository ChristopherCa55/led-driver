"""Commutation-loop copper inductance (DILATE_MM env, default 1.0: GND copper within that distance counts) per channel for any stackup, from solve_copper6.py --dump files.

    python loop_L6.py COPPER.json DUMP_DIR STACK [STACK ...]      (STACK 'all6' = every JLC 6-layer stackup)

Method (the over-plane model of route_2026-09-16/tools/loop_inductance.py, with a per-cell height):
for each forward leg, L = mu0 * sum(h_eff * |J_tot|^2) * cell^2, J_tot = vector sum over layers of the sheet current
at 1 A, h_eff = current-weighted mean over layers of the vertical distance from that layer to the nearest other layer
carrying GND copper at that cell (H_NONE where the column has none). The GND return is the image and is not added.
Channel = LX leg + source leg + Vout leg, as loop_inductance.py. No via barrels, pads, FET leads or die.
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve_copper6 as S

MU0 = 4e-7 * math.pi * 1e-3
DILATE = float(os.environ.get('DILATE_MM', '1.0'))
CH = {'ch1': ['loop LX M1->M7', 'm2_source M7->M2', 'loop Vout_1 M2->ceramics'],
      'ch2': ['loop LX M1->M6', 'm3_source M6->M3', 'loop Vout_2 M3->ceramics'],
      'ch3': ['loop LX M1->M5', 'm4_source M5->M4', 'loop Vout_3 M4->ceramics']}


def safe(n):
    return ''.join(ch if ch.isalnum() or ch in '_-' else '_' for ch in n)


def zpos(layers, stack):
    st = S.STACKS[stack]
    z, acc = {}, 0.0
    for i, ln in enumerate(layers):
        z[ln] = acc + st['cu'][i] / 2
        acc += st['cu'][i] + (st['gaps'][i] if i < len(st['gaps']) else 0)
    return z


def leg_L(d, gmask, z):
    lays = [str(x) for x in d['layers']]
    jx = sum(d['sx_' + l].astype(float) for l in lays)
    jy = sum(d['sy_' + l].astype(float) for l in lays)
    jabs = np.zeros_like(jx)
    jh = np.zeros_like(jx)
    for l in lays:
        hm = np.full(jx.shape, np.inf)
        for k, m in gmask.items():
            if k != l:
                hm = np.where(m, np.minimum(hm, abs(z[k] - z[l])), hm)
        hm = np.where(np.isfinite(hm), hm, S.H_NONE)
        mag = np.hypot(d['sx_' + l].astype(float), d['sy_' + l].astype(float))
        jabs += mag
        jh += mag * hm
    heff = np.where(jabs > 0, jh / np.maximum(jabs, 1e-30), 0.0)
    h = float(d['h'])
    return float(MU0 * (heff * (jx ** 2 + jy ** 2)).sum() * h * h * 1e9)


def main():
    cop = json.load(open(sys.argv[1]))
    layers = cop['layers']
    stacks = sys.argv[3:]
    if stacks == ['all6']:
        stacks = [k for k in S.STACKS if k.startswith('JLC0616')]
    gcu = cop['nets'].get('GND', {})
    legs = {}
    for ch, names in CH.items():
        for n in names:
            d = dict(np.load(os.path.join(sys.argv[2], safe(n) + '.npz')))
            x0, y0, h, nx, ny = float(d['x0']), float(d['y0']), float(d['h']), int(d['nx']), int(d['ny'])
            gmask = {ln: S.raster(gcu[ln], x0, y0, nx, ny, h) if ln in gcu else np.zeros((ny, nx), bool) for ln in layers}
            if DILATE > 0:     # return current flows round small antipads: GND copper within DILATE mm counts
                r = int(round(DILATE / h))
                yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
                disk = xx * xx + yy * yy <= r * r
                gmask = {ln: ndimage.binary_dilation(m, structure=disk) for ln, m in gmask.items()}
            legs[n] = (d, gmask)
    out = {}
    for st in stacks:
        z = zpos(layers, st)
        row = {}
        for ch, names in CH.items():
            row[ch] = sum(leg_L(legs[n][0], legs[n][1], z) for n in names)
        out[st] = row
        print('%-18s ch1 %.2f  ch2 %.2f  ch3 %.2f nH   sum %.2f' % (st, row['ch1'], row['ch2'], row['ch3'], sum(row.values())),
              flush=True)
    json.dump(out, open(os.path.join(sys.argv[2], 'loop_L_dil%.1f.json' % DILATE), 'w'), indent=1)


if __name__ == '__main__':
    main()
