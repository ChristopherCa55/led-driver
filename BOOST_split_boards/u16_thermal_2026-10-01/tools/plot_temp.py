# Top-layer temperature around U16 for a given load (2026-10-01).
# Usage: python tools/plot_temp.py T_NAME BG_NAME I_mA VIN OUT.png "title"
#   T_NAME: work/T_<name>.npz (rise per watt), BG_NAME: work/bg_<name>.npz (battery-current rise) or "-"
import sys, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, 'tools')
from limits import P, T_AIR, R_JT
from vias import CONFIGS

tn, bn, I, vin, out, title = sys.argv[1], sys.argv[2], float(sys.argv[3]) / 1e3, float(sys.argv[4]), sys.argv[5], sys.argv[6]
t = np.load('work/T_%s.npz' % tn)
p = P(I, vin)
F = t['F'] * p + T_AIR
if bn != '-':
    F = F + np.load('work/bg_%s.npz' % bn)['F']
xs, ys = t['xs'], t['ys']
tj = T_AIR + (np.load('work/bg_%s.npz' % bn)['tab'] if bn != '-' else 0) + p * (float(t['tab']) + R_JT['SOT-223'])
fig, axs = plt.subplots(1, 2, figsize=(14, 6.5), gridspec_kw={'width_ratios': [1.25, 1]})
ax = axs[0]
im = ax.imshow(F, extent=(xs[0], xs[-1], ys[-1], ys[0]), cmap='inferno')
plt.colorbar(im, ax=ax, label='top-layer copper temperature (C)')
ax.set_title('Whole power board, top layer', fontsize=10)
ax.add_patch(plt.Rectangle((95.7, 59.6), 3.8, 2.0, fill=False, ec='c', lw=1))
ax = axs[1]
x0, x1, y0, y1 = 84, 104.05, 50, 76
ix = (xs >= x0) & (xs <= x1); iy = (ys >= y0) & (ys <= y1)
sub = F[np.ix_(iy, ix)]
im = ax.imshow(sub, extent=(xs[ix][0], xs[ix][-1], ys[iy][-1], ys[iy][0]), cmap='inferno')
cs = ax.contour(xs[ix], ys[iy], sub, levels=np.arange(np.floor(np.nanmin(sub)), np.nanmax(sub), 2), colors='w', linewidths=0.4)
ax.clabel(cs, fontsize=6, fmt='%.0f')
plt.colorbar(im, ax=ax, label='C')
ax.add_patch(plt.Rectangle((95.7, 59.6), 3.8, 2.0, fill=False, ec='c', lw=1.2))
ax.text(95.8, 59.4, 'U16 tab', color='c', fontsize=8)
for x, y in CONFIGS['sot223_vias_around'][1]:
    ax.plot(x, y, 'o', ms=3, mfc='none', mec='c', mew=0.8)
ax.set_title('Around U16 (cyan circles: the 27 added GND vias)', fontsize=10)
fig.suptitle('%s\nload %.0f mA at %.1f V in: U16 dissipates %.2f W; junction about %.0f C' % (title, I * 1e3, vin, p, tj),
             fontsize=11)
plt.tight_layout()
plt.savefig(out, dpi=90)
print('P %.3f W, Tj %.1f C, tab copper max %.1f C' % (p, tj, np.nanmax(sub)))
