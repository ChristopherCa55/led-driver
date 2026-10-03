# Brightness and protection behaviour versus battery open-circuit voltage for the low-battery runs.
# Usage (from the sim folder): python ../tools/analyze.py CASE [CASE ...]
# For each 1 ms window after 8 ms: battery open-circuit voltage, the LEDs' average current as a share of the
# full-power values (2.635 / 2.371 / 2.371 A), the share of time U21 holds M1 off, how many times it trips,
# the lowest 12 V rail, the lowest high-side driver supply and the highest LX.
import sys
import numpy as np
sys.path.insert(0, '../tools')
from plot_runs import read_raw

FULL = np.array([2.635, 2.371, 2.371])

for name in sys.argv[1:]:
    r = read_raw(name + '.raw')
    t = r['time']
    u21 = r['v(n013)'] > 2.5
    vdda = np.minimum.reduce([r['v(n019)'] - r['v(m2_source)'], r['v(n032)'] - r['v(m3_source)'],
                              r['v(n040)'] - r['v(m4_source)']])
    print('==', name)
    print(' window   Voc    Vin_avg  12V_min  LED avg %% (1/2/3)   U21 off %%  trips  VDDA_min  LX_max')
    for w0 in np.arange(0.008, t[-1] - 1e-6, 0.002):
        m = (t >= w0) & (t < w0 + 0.002)
        if m.sum() < 10:
            continue
        tt = t[m]
        dt = np.diff(tt)

        def avg(y):
            return np.sum(0.5 * (y[1:] + y[:-1]) * dt) / (tt[-1] - tt[0])
        leds = [avg(r['i(sim_led%d)' % k][m]) for k in (1, 2, 3)]
        off = avg(u21[m].astype(float))
        trips = int(np.sum(np.diff(u21[m].astype(int)) == 1))
        print(' %4.0f ms  %5.2f  %6.2f   %6.2f   %3.0f / %3.0f / %3.0f      %5.1f   %4d    %5.2f   %5.1f' % (
            w0 * 1e3, avg(r['v(pbat)'][m]), avg(r['v(vin)'][m]), r['v(12v)'][m].min(),
            *(100 * np.array(leds) / FULL), 100 * off, trips, vdda[m].min(), r['v(lx)'][m].max()))
