"""D19 (TVS, LX to GND) conduction per switching cycle, from a sim_case.py run (LTspice raw: double time + float32).

    python d19_cycles.py RUN_DIR [T0_ms T1_ms]

Switching cycles are counted from LX rising through 30 V. A cycle "conducts" when D19 carries more than 10 mA
(reverse, i.e. I(D19) < -10 mA, LX -> GND). Prints the share of cycles that conduct, the peak current, the charge and
energy per conducting cycle, and the LX peak distribution.
"""
import os, sys
import numpy as np


def read_raw(fn, want):
    data = open(fn, 'rb').read()
    marker = 'Binary:\n'.encode('utf-16-le')
    i = data.index(marker)
    lines = data[:i].decode('utf-16-le').splitlines()
    nvar = int([l for l in lines if l.startswith('No. Variables:')][0].split(':')[1])
    npts = int([l for l in lines if l.startswith('No. Points:')][0].split(':')[1])
    k = lines.index('Variables:')
    names = [lines[k + 1 + j].split('\t')[2].lower() for j in range(nvar)]
    dt = np.dtype([('t', '<f8')] + [('v%d' % j, '<f4') for j in range(1, nvar)])
    arr = np.frombuffer(data, dtype=dt, count=npts, offset=i + len(marker))
    out = {'time': np.abs(arr['t'])}
    for w in want:
        out[w] = arr['v%d' % names.index(w)].astype(float)
    return out


def main():
    run = sys.argv[1]
    t0 = float(sys.argv[2]) * 1e-3 if len(sys.argv) > 2 else 25e-3
    t1 = float(sys.argv[3]) * 1e-3 if len(sys.argv) > 3 else 30e-3
    r = read_raw(os.path.join(run, 'BOOST.raw'), ['v(lx)', 'i(d19)'])
    t, lx, i = r['time'], r['v(lx)'], r['i(d19)']
    m = (t >= t0) & (t <= t1)
    t, lx, i = t[m], lx[m], i[m]
    up = np.where((lx[:-1] < 30) & (lx[1:] >= 30))[0]
    cyc = len(up) - 1
    n_cond, peaks, qs, es, lxp = 0, [], [], [], []
    for a, b in zip(up[:-1], up[1:]):
        seg = slice(a, b + 1)
        tt, ii, vv = t[seg], -i[seg], lx[seg]
        lxp.append(vv.max())
        if ii.max() > 0.010:
            n_cond += 1
            peaks.append(ii.max())
            qs.append(np.trapezoid(np.clip(ii, 0, None), tt))
            es.append(np.trapezoid(np.clip(ii, 0, None) * vv, tt))
    lxp = np.array(lxp)
    f = cyc / (t[up[-1]] - t[up[0]])
    print('%s, %.1f-%.1f ms: %d switching cycles (%.1f kHz)' % (run, t0 * 1e3, t1 * 1e3, cyc, f / 1e3))
    print('  D19 > 10 mA in %d of %d cycles (%.0f %%)' % (n_cond, cyc, 100.0 * n_cond / max(cyc, 1)))
    if peaks:
        print('  peak current per conducting cycle: median %.2f A, max %.2f A' % (np.median(peaks), max(peaks)))
        print('  charge per cycle: median %.1f nC; energy per cycle: median %.2f uJ, max %.2f uJ'
              % (1e9 * np.median(qs), 1e6 * np.median(es), 1e6 * max(es)))
        print('  average TVS power over the window: %.1f mW' % (1e3 * sum(es) / (t[-1] - t[0])))
    print('  LX peak per cycle: min %.2f V, median %.2f V, max %.2f V' % (lxp.min(), np.median(lxp), lxp.max()))
    for v in (58, 59, 60, 61, 62, 63):
        print('    cycles with LX peak above %d V: %d' % (v, int((lxp > v).sum())))


if __name__ == '__main__':
    main()
