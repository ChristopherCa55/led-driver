"""Plot exported copper (export_copper.py JSON) per layer, coloured by net.

usage: python plot_copper.py COPPER.json OUT.png [--layers F.Cu,In2.Cu,...] [--nets a,b] [--zoom x0,y0,x1,y1]
"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

a = sys.argv[1:]
cop = json.load(open(a[0]))
out = a[1]
layers = a[a.index('--layers') + 1].split(',') if '--layers' in a else cop['layers']
nets = set(a[a.index('--nets') + 1].split(',')) if '--nets' in a else None
zoom = [float(v) for v in a[a.index('--zoom') + 1].split(',')] if '--zoom' in a else [29, 29, 105, 117]
COL = {'Vin': '#d62728', 'rsense_lo': '#ff7f0e', 'LX': '#9467bd', 'GND': '#bbbbbb',
       'm2_source': '#000080', 'm3_source': '#000080', 'm4_source': '#000080',
       'Vout_1': '#1f77b4', 'Vout_2': '#17becf', 'Vout_3': '#2ca02c',
       'Output1_drain': '#8c564b', 'Output2_drain': '#e377c2', 'Output3_drain': '#bcbd22',
       'Net-(M8-S)': '#6b6b00', 'Net-(M9-S)': '#8a2d6b', 'Net-(M10-S)': '#4d2f28'}
cols = 4 if len(layers) > 4 else len(layers)
rows = (len(layers) + cols - 1) // cols
w = zoom[2] - zoom[0]
h = zoom[3] - zoom[1]
fig, axs = plt.subplots(rows, cols, figsize=(cols * 6.0, rows * 6.0 * h / w + 0.4))
axs = [axs] if rows * cols == 1 else list(getattr(axs, 'flat', axs))
for ax, ln in zip(axs, layers):
    for net, per in cop['nets'].items():
        if nets and net not in nets:
            continue
        if ln not in per:
            continue
        c = COL.get(net, '#eeeeee')
        for poly in per[ln]:
            if isinstance(poly, dict):
                continue
            ax.add_patch(Polygon(poly, closed=True, fc=c, ec='none', alpha=0.9 if net in COL else 0.5))
    for b in cop['barrels']:
        if nets and b['net'] not in nets:
            continue
        if b['kind'] == 'via':
            ax.plot(b['x'], b['y'], '.', ms=1.2, color='k')
    ax.plot([30, 86, 86, 104, 104, 30, 30], [30, 30, 42, 42, 116, 116, 30], 'k-', lw=0.6)
    ax.set_xlim(zoom[0], zoom[2])
    ax.set_ylim(zoom[3], zoom[1])
    ax.set_aspect('equal')
    ax.set_title(ln, fontsize=9)
    ax.tick_params(labelsize=6)
    ax.grid(True, lw=0.2, alpha=0.5)
for ax in axs[len(layers):]:
    ax.axis('off')
fig.tight_layout()
fig.savefig(out, dpi=100)
print('wrote', out)
