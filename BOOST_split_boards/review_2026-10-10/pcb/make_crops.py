"""Pictures for PCB_REVIEW.md from pcb_checks.py's saved grid (TAG_grid.npz) and the copper export.

    python make_crops.py COPPER.json GRID.npz OUTDIR SPEC.json

SPEC is a list of items:
  {"name": ..., "layer": "In2.Cu", "box": [x1, y1, x2, y2], "title": ...,
   "heat": "LX" (optional: overlay the solver's sheet current for that net on this layer),
   "pieces": "GND" (optional: colour each separate piece of that net on this layer),
   "tracks": [["12V", "B.Cu"], ...] (optional: outline these nets' tracks in red),
   "marks": [[x, y, "label"], ...] (optional)}
"""
import json, os, sys
import numpy as np
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_layers import colour

PIECE_COLS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#17becf', '#bcbd22',
              '#7f7f7f', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94']


def main():
    js, gz, out, spec = sys.argv[1:5]
    d = json.load(open(js))
    z = np.load(gz, allow_pickle=True)
    names = [str(n) for n in z['names']]
    idx = {n: k for k, n in enumerate(names)}
    x0, y0, h = float(z['x0']), float(z['y0']), float(z['h'])
    os.makedirs(out, exist_ok=True)
    for it in json.load(open(spec)):
        ln = it['layer']
        own = z['own_' + ln]
        x1, y1, x2, y2 = it['box']
        j1, i1 = int((y1 - y0) / h), int((x1 - x0) / h)
        j2, i2 = int((y2 - y0) / h) + 1, int((x2 - x0) / h) + 1
        j1, i1 = max(j1, 0), max(i1, 0)
        j2, i2 = min(j2, own.shape[0]), min(i2, own.shape[1])
        o = own[j1:j2, i1:i2]
        ext = (x0 + i1 * h, x0 + i2 * h, y0 + j2 * h, y0 + j1 * h)
        fig, ax = plt.subplots(figsize=(8, 8 * (y2 - y1) / (x2 - x1) + 0.8), dpi=110)
        if it.get('pieces'):
            q = idx[it['pieces']]
            lab, n = ndimage.label(own == q)
            area = np.bincount(lab.ravel())
            order = np.argsort(-area[1:]) + 1
            rank = np.zeros(n + 1, int)
            rank[order] = np.arange(n)
            img = np.ones(o.shape + (3,))
            img[o >= 0] = to_rgb('#d9d9d9')
            L = lab[j1:j2, i1:i2]
            for v in np.unique(L):
                if v == 0:
                    continue
                img[L == v] = to_rgb(PIECE_COLS[min(rank[v], len(PIECE_COLS) - 1)])
            ax.imshow(img, extent=ext, interpolation='nearest')
            for v in np.unique(L):
                if v == 0 or area[v] * h * h < 3:
                    continue
                jc, ic = ndimage.center_of_mass(L == v)
                ax.text(ext[0] + (ic + 0.5) * h, ext[3] + (jc + 0.5) * h, '%.0f' % (area[v] * h * h), fontsize=7,
                        ha='center', va='center', color='black',
                        bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))
        else:
            pal = np.array([to_rgb(colour(nm)) for nm in names] + [(1, 1, 1)])
            img = pal[np.where(o < 0, len(names), o)]
            ax.imshow(img, extent=ext, interpolation='nearest')
        if it.get('heat'):
            key = 'hot_%s_%s' % (it['heat'], ln)
            if key in z.files:
                hv = z[key][j1:j2, i1:i2]
                hv = np.where(o == idx[it['heat']], hv, np.nan)
                im = ax.imshow(np.where(hv > 0.2, hv, np.nan), extent=ext, cmap='inferno_r', alpha=0.8,
                               interpolation='nearest', vmin=0, vmax=it.get('vmax', 3.5))
                fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label='%s sheet current, A per mm of width' % it['heat'])
        for b in d['barrels']:
            if x1 <= b['x'] <= x2 and y1 <= b['y'] <= y2:
                ax.add_patch(plt.Circle((b['x'], b['y']), b['drill'] / 2, color='black', fill=False, lw=0.4))
        for net, lay in it.get('tracks', []):
            for t in d['tracks']:
                if t['net'] == net and t['layer'] == lay:
                    ax.plot([t['x0'], t['x1']], [t['y0'], t['y1']], color='red', lw=1.2, alpha=0.9)
        for k in d.get('keepouts', []):
            if ln in k['layers']:
                p = np.array(k['pts'] + [k['pts'][0]])
                ax.plot(p[:, 0], p[:, 1], color='black', lw=0.8, ls='--')
        for mk in it.get('marks', []):
            ax.annotate(mk[2], (mk[0], mk[1]), xytext=(mk[0] + mk[3] if len(mk) > 3 else mk[0] + 1.5,
                                                      mk[1] + mk[4] if len(mk) > 4 else mk[1] - 1.5),
                        color='red', fontsize=8, fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color='red', lw=1.2),
                        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='red', alpha=0.85))
        ax.set_xlim(x1, x2)
        ax.set_ylim(y2, y1)
        ax.set_title(it['title'], fontsize=9)
        ax.grid(True, color='#888888', lw=0.25)
        ax.minorticks_on()
        ax.tick_params(labelsize=7)
        fig.tight_layout()
        fig.savefig(os.path.join(out, it['name'] + '.png'))
        plt.close(fig)
        print('wrote', it['name'])


if __name__ == '__main__':
    main()
