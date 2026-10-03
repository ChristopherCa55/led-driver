import sys, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, 'tools')
from raster import load, rasterize
d = load(sys.argv[1]); out = sys.argv[2]
x0, y0, x1, y1 = 89, 54, 104.05, 72
xs, ys, nets, arr, board = rasterize(d, 0.05, (x0, y0, x1, y1))
col = {'GND': (0.2, 0.6, 0.2), 'Vin': (0.85, 0.2, 0.2), '12V': (0.95, 0.6, 0.1), '5V': (0.2, 0.4, 0.9)}
show = [0, 1, 2, 3, 4, 7]
fig, axs = plt.subplots(2, 3, figsize=(15, 12))
for li, ax in zip(show, axs.ravel()):
    img = np.ones(arr.shape[1:] + (3,)) * 0.92
    img[~board] = 1
    for i, n in enumerate(nets):
        if i: img[arr[li] == i] = col.get(n, (0.55, 0.55, 0.55))
    ax.imshow(img, extent=(xs[0], xs[-1], ys[-1], ys[0]))
    for v in d['vias']:
        if x0 < v['x'] < x1 and y0 < v['y'] < y1:
            ax.add_patch(plt.Circle((v['x'], v['y']), v['dia'] / 2, fc='none', ec='k', lw=0.6))
            ax.add_patch(plt.Circle((v['x'], v['y']), v['drill'] / 2, fc='k' if v['net'] == 'GND' else 'w', ec='k', lw=0.4))
    for f in d['footprints']:
        x_0, y_0, x_1, y_1 = f['bbox']
        if x_1 > x0 and x_0 < x1 and y_1 > y0 and y_0 < y1 and not f['ref'].startswith('G'):
            ax.add_patch(plt.Rectangle((x_0, y_0), x_1 - x_0, y_1 - y_0, fill=False, ec='m' if f['side'] == 'F' else 'c', lw=0.8))
            ax.text(max(x_0, x0) + 0.1, max(y_0, y0) + 0.4, f['ref'] + ('(B)' if f['side'] == 'B' else ''), fontsize=9, color='m' if f['side'] == 'F' else 'c', clip_on=True)
            if f['ref'] == 'U16':
                for p in f['pads']: ax.plot(p['x'], p['y'], 'm+', ms=10)
    ax.set_xticks(np.arange(89, 105, 1)); ax.set_yticks(np.arange(54, 73, 1)); ax.grid(lw=0.3, alpha=0.5)
    ax.tick_params(labelsize=7)
    ax.set_title(d['layers'][li], fontsize=10)
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0)
plt.tight_layout(); plt.savefig(out, dpi=75)
