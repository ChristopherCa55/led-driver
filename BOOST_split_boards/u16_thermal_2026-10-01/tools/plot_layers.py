# Plot each copper layer around a point, coloured by net (GND, Vin, 12V, 5V, other).
import sys, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, 'tools')
from raster import load, rasterize
d = load(sys.argv[1]); out = sys.argv[2]
cx, cy, half = 97.6, 63.75, float(sys.argv[3]) if len(sys.argv) > 3 else 22
xs, ys, nets, arr, board = rasterize(d, 0.1, (cx - half, cy - half, min(cx + half, 104.05), cy + half))
col = {'GND': (0.2, 0.6, 0.2), 'Vin': (0.85, 0.2, 0.2), '12V': (0.95, 0.6, 0.1), '5V': (0.2, 0.4, 0.9)}
fig, axs = plt.subplots(2, 4, figsize=(20, 11))
for li, ax in enumerate(axs.ravel()):
    img = np.ones(arr.shape[1:] + (3,)) * 0.92
    img[~board] = 1
    for i, n in enumerate(nets):
        if i == 0: continue
        img[arr[li] == i] = col.get(n, (0.55, 0.55, 0.55))
    ax.imshow(img, extent=(xs[0], xs[-1], ys[-1], ys[0]))
    for v in d['vias']:
        if abs(v['x'] - cx) < half and abs(v['y'] - cy) < half:
            ax.plot(v['x'], v['y'], 'o', ms=2.2, mfc='k' if v['net'] == 'GND' else 'w', mec='k', mew=0.4)
    for f in d['footprints']:
        if f['ref'] in ('U16', 'J1', 'J2', 'D21', 'D10', 'C85', 'C40', 'C25', 'C6', 'C69', 'C81'):
            x0, y0, x1, y1 = f['bbox']
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec='m' if f['side'] == 'F' else 'c', lw=0.8))
            ax.text(x0, y0, f['ref'], fontsize=7, color='m' if f['side'] == 'F' else 'c')
    ax.set_title(d['layers'][li] + '  (green GND, red Vin, orange 12V, blue 5V, grey other)', fontsize=9)
    ax.set_xlim(cx - half, min(cx + half, 104.05)); ax.set_ylim(cy + half, cy - half)
plt.tight_layout(); plt.savefig(out, dpi=80)
