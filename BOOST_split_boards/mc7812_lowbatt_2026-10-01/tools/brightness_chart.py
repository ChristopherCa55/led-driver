# Chart: average LED brightness against the battery's open-circuit voltage, for the low-battery runs.
# Usage (from the sim folder): python ../tools/brightness_chart.py OUT.png
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, '../tools')
from plot_runs import read_raw

FULL = np.array([2.635, 2.371, 2.371])
SURFACE, INK, INK2, GRID = '#fcfcfb', '#1f1f1e', '#5f5e5a', '#e6e5e0'
SERIES = [  # (label, runs, colour, marker): fixed categorical order
    ('LM2940 (now), 50 mOhm pack', ['D_lm2940_ramp_R50m', 'H_lm2940_ramp_low_R50m'], '#2a78d6', 'o'),
    ('MC7812 typical, 50 mOhm pack', ['C_7812typ_ramp_R50m', 'G_7812typ_hold12p3_R50m', 'I_7812typ_hold11p85_R50m'],
     '#eb6834', 's'),
    ('MC7812 pessimistic, 50 mOhm pack', ['F_7812wc_ramp_R50m'], '#1baf7a', '^'),
    ('MC7812 typical, stiff 10 mOhm pack', ['E_7812typ_ramp_R10m'], '#eda100', 'D'),
]


def windows(name, w=0.002):
    r = read_raw(name + '.raw')
    t = r['time']
    pts = []
    for w0 in np.arange(0.008, t[-1] - 1e-6, w):
        m = (t >= w0) & (t < w0 + w)
        if m.sum() < 10:
            continue
        tt = t[m]; dt = np.diff(tt)
        avg = lambda y: np.sum(0.5 * (y[1:] + y[:-1]) * dt) / (tt[-1] - tt[0])
        led = np.mean([avg(r['i(sim_led%d)' % k][m]) / FULL[k - 1] for k in (1, 2, 3)]) * 100
        pts.append((avg(r['v(pbat)'][m]), led))
    return pts


fig, ax = plt.subplots(figsize=(10, 5.6), facecolor=SURFACE)
ax.set_facecolor(SURFACE)
for label, runs, col, mk in SERIES:
    pts = sorted(p for run in runs for p in windows(run))
    v, b = np.array(pts).T
    # several windows share one voltage in the hold runs: average them
    uv = np.unique(np.round(v, 2))
    bb = np.array([b[np.round(v, 2) == x].mean() for x in uv])
    ax.plot(uv, bb, color=col, lw=2, marker=mk, ms=6, mec=SURFACE, mew=1.5, label=label, zorder=3)
    i = np.argmin(np.abs(bb - 50)) if bb.min() < 60 else len(uv) - 1
    ax.annotate(label.split(',')[0] + ('\n' + label.split(', ')[1]), (uv[i], bb[i]), xytext=(8, -4),
                textcoords='offset points', fontsize=8.5, color=INK, va='top')
ax.set_xlim(13.6, 10.5)  # discharge reads left to right
ax.set_ylim(-3, 108)
ticks = np.arange(13.5, 10.4, -0.5)
ax.set_xticks(ticks)
ax.set_xticklabels(['%.1f V\n%.2f V/cell' % (x, x / 4) for x in ticks], fontsize=8.5, color=INK2)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels(['0 %', '25 %', '50 %', '75 %', '100 %'], fontsize=8.5, color=INK2)
ax.set_xlabel('Battery open-circuit voltage (4S), falling as it discharges', fontsize=9.5, color=INK2)
ax.set_ylabel('Average LED current, % of full', fontsize=9.5, color=INK2)
ax.grid(axis='y', color=GRID, lw=0.8)
for s in ('top', 'right', 'left'):
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(GRID)
ax.tick_params(length=0)
ax.legend(loc='lower left', fontsize=8.5, frameon=False, labelcolor=INK)
fig.suptitle('LED brightness as the battery runs down (simulated, full brightness setting)', fontsize=12,
             color=INK, x=0.07, ha='left')
ax.set_title('Battery = open-circuit voltage + pack resistance + 12 mOhm cable; 218 W of LEDs; mean of the three '
             'channels', fontsize=8.5, color=INK2, loc='left')
plt.tight_layout()
plt.savefig(sys.argv[1], dpi=110, facecolor=SURFACE)
print('saved', sys.argv[1])
