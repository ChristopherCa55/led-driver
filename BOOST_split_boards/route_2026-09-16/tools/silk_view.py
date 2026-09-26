"""Plot a silk_dump.py export, optionally zoomed on a window (system Python, matplotlib).

usage: python silk_view.py DUMP.json OUT.png [x0 y0 x1 y1] [--mirror]
Mask openings (pads) gold, Fab outlines grey, silk white on dark green.
"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

args = [a for a in sys.argv[1:] if not a.startswith('--')]
d = json.load(open(args[0]))
fig, ax = plt.subplots(figsize=(12, 12), dpi=130)
ax.set_facecolor('#1d3b2a')
for p in d['fab']:
    ax.add_patch(Polygon(p, closed=True, fc='none', ec='#8a8a8a', lw=0.5))
for p in d['mask']:
    ax.add_patch(Polygon(p, closed=True, fc='#d4a72c', ec='none'))
for p in d['silk']:
    ax.add_patch(Polygon(p, closed=True, fc='white', ec='none'))
for s in d['edge']:
    ax.plot([s[0][0], s[1][0]], [s[0][1], s[1][1]], color='#e0c000', lw=1)
for r, x, y, own in d['labels']:
    if own:
        ax.text(x, y, r, color='#ff7f7f', fontsize=7, ha='center', va='center', alpha=0.8, clip_on=True)
if len(args) >= 6:
    x0, y0, x1, y1 = map(float, args[2:6])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
else:
    ax.autoscale()
    ax.invert_yaxis()
if '--mirror' in sys.argv:
    ax.invert_xaxis()
ax.set_aspect('equal')
ax.grid(True, color='#3c6', lw=0.3, alpha=0.4)
ax.minorticks_on()
fig.savefig(args[1], bbox_inches='tight', facecolor='#10251a')
print('wrote', args[1])
