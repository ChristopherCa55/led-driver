# Plot the low-battery runs from their LTspice .raw files (binary: double time + float32 variables).
# Usage (from the sim folder): python ../tools/plot_runs.py OUT.png CASE [CASE ...]
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read_raw(fn):
    data = open(fn, 'rb').read()
    marker = 'Binary:\n'.encode('utf-16-le')
    i = data.index(marker)
    head = data[:i].decode('utf-16-le')
    lines = head.splitlines()
    nvar = int([l for l in lines if l.startswith('No. Variables:')][0].split(':')[1])
    npts = int([l for l in lines if l.startswith('No. Points:')][0].split(':')[1])
    k = lines.index('Variables:')
    names = [lines[k + 1 + j].split('\t')[2] for j in range(nvar)]
    dt = np.dtype([('t', '<f8')] + [('v%d' % j, '<f4') for j in range(1, nvar)])
    arr = np.frombuffer(data, dtype=dt, count=npts, offset=i + len(marker))
    out = {'time': np.abs(arr['t'])}
    for j in range(1, nvar):
        out[names[j].lower()] = arr['v%d' % j].astype(float)
    return out


def envelope(t, y, n=4000):
    """max and min of y in n time bins (for switching waveforms)."""
    edges = np.linspace(t[0], t[-1], n + 1)
    idx = np.searchsorted(t, edges)
    tc, lo, hi = [], [], []
    for a, b in zip(idx[:-1], idx[1:]):
        if b > a:
            tc.append(t[a]); lo.append(y[a:b].min()); hi.append(y[a:b].max())
    return np.array(tc), np.array(lo), np.array(hi)


if __name__ == '__main__':
    out = sys.argv[1]
    cases = sys.argv[2:]
    fig, axs = plt.subplots(5, len(cases), figsize=(7 * len(cases), 16), sharex='col', squeeze=False)
    for c, name in enumerate(cases):
        r = read_raw(name + '.raw')
        t = r['time'] * 1e3
        ax = axs[0, c]
        ax.plot(t, r['v(pbat)'], label='battery open-circuit (PBAT)')
        ax.plot(t, r['v(vin)'], label='board Vin')
        ax.set_ylabel('V'); ax.legend(fontsize=8); ax.set_title(name, fontsize=10); ax.grid(alpha=0.3)
        ax = axs[1, c]
        ax.plot(t, r['v(12v)'], label='12 V rail')
        ax.axhline(9.77, color='r', ls='--', lw=0.8, label='U21 stop (9.77 V, falling)')
        ax.axhline(10.32, color='g', ls='--', lw=0.8, label='U21 restart (10.32 V)')
        for nd, src, lab in (('v(n019)', 'v(m2_source)', 'VDDA U15'), ('v(n032)', 'v(m3_source)', 'VDDA U10'),
                             ('v(n040)', 'v(m4_source)', 'VDDA U8')):
            tc, lo, hi = envelope(r['time'], r[nd] - r[src])
            ax.plot(tc * 1e3, lo, lw=0.8, label=lab + ' (min)')
        ax.axhline(8.0, color='k', ls=':', lw=0.8, label='driver UVLO (model, 8 V)')
        ax.set_ylabel('V'); ax.legend(fontsize=7, ncol=2); ax.grid(alpha=0.3); ax.set_ylim(6, 13)
        ax = axs[2, c]
        ax.plot(t, r['v(m1_inhibit)'], label='M1_INHIBIT')
        ax.plot(t, r['v(n013)'], label='U21 out', lw=0.8)
        ax.set_ylabel('V'); ax.legend(fontsize=8); ax.grid(alpha=0.3)
        ax = axs[3, c]
        for k in (1, 2, 3):
            tc, lo, hi = envelope(r['time'], r['i(sim_led%d)' % k], 2000)
            ax.plot(tc * 1e3, (lo + hi) / 2, label='LED%d' % k)
        ax.set_ylabel('A'); ax.legend(fontsize=8); ax.grid(alpha=0.3)
        ax = axs[4, c]
        tc, lo, hi = envelope(r['time'], r['v(lx)'], 4000)
        ax.plot(tc * 1e3, hi, lw=0.6, label='LX peak')
        ax.set_ylabel('V'); ax.set_xlabel('ms'); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=75)
    print('saved', out)
