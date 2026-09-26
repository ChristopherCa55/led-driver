"""Before / after silk plots of a silk-only delta (system Python, matplotlib), from silk_dump.py exports.

usage: python silk_compare.py BEFORE_F.json BEFORE_B.json AFTER_F.json AFTER_B.json FET_SILK.json OUT_PREFIX
Writes OUT_PREFIX_board.png (both sides, before and after, B mirrored as seen from below) and OUT_PREFIX_fets.png
(each TO-220's pins on both sides after the change, letters readable).
"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

bF, bB, aF, aB, rep_path, out = sys.argv[1:7]
D = {k: json.load(open(p)) for k, p in (('bF', bF), ('bB', bB), ('aF', aF), ('aB', aB))}
rep = json.load(open(rep_path))


def draw(ax, d, mirror, win=None, labels=False, lw=0.5):
    ax.set_facecolor('#1d3b2a')
    for p in d['fab']:
        ax.add_patch(Polygon(p, closed=True, fc='none', ec='#7d8a80', lw=0.3))
    for p in d['mask']:
        ax.add_patch(Polygon(p, closed=True, fc='#d4a72c', ec='none'))
    for p in d['silk']:
        ax.add_patch(Polygon(p, closed=True, fc='white', ec='none'))
    for s in d['edge']:
        ax.plot([s[0][0], s[1][0]], [s[0][1], s[1][1]], color='#e0c000', lw=1)
    if win:
        ax.set_xlim(win[0], win[2])
        ax.set_ylim(win[3], win[1])
    else:
        ax.set_xlim(29, 105)
        ax.set_ylim(117, 29)
    if mirror:
        ax.invert_xaxis()
    ax.set_aspect('equal')
    ax.tick_params(labelsize=6)


fig, axs = plt.subplots(2, 2, figsize=(20, 23), dpi=110)
for (i, j), (k, title) in zip(((0, 0), (0, 1), (1, 0), (1, 1)),
                              (('bF', 'BEFORE (v16), top side F.SilkS'), ('aF', 'AFTER (v17), top side F.SilkS'),
                               ('bB', 'BEFORE (v16), bottom side B.SilkS, seen from below'),
                               ('aB', 'AFTER (v17), bottom side B.SilkS, seen from below'))):
    draw(axs[i][j], D[k], k.endswith('B'))
    axs[i][j].set_title(title, fontsize=13)
fig.tight_layout()
fig.savefig(out + '_board.png', facecolor='white')

fig, axs = plt.subplots(4, 5, figsize=(26, 22), dpi=100)
for n, ref in enumerate(['M%d' % k for k in range(1, 11)]):
    pads = rep[ref]['pads']
    xs = [pads[q]['xy'][0] for q in '123']
    ys = [pads[q]['xy'][1] for q in '123']
    cx, cy = sum(xs) / 3, sum(ys) / 3
    for s, (k, side) in enumerate((('aF', 'top, F.SilkS'), ('aB', 'bottom, B.SilkS, seen from below'))):
        ax = axs[(n // 5) * 2 + s][n % 5]
        draw(ax, D[k], k.endswith('B'), (cx - 7.5, cy - 7.5, cx + 7.5, cy + 7.5))
        ax.set_title('%s %s\nF: %s' % (ref, side, rep[ref]['F_mode']), fontsize=10)
fig.tight_layout()
fig.savefig(out + '_fets.png', facecolor='white')
print('wrote', out + '_board.png', out + '_fets.png')
