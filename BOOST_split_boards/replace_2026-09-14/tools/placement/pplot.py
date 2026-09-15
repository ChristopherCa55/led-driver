"""Plot a pmodel layout: top side and bottom side (both seen from the top), plus checks."""
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
import pmodel as M
import pcheck as C

NETC = {'LX': '#e41a1c', 'Vin': '#ff7f00', 'rsense_lo': '#ffb000', 'GND': '#777777', 'Vout_1': '#377eb8',
        'Vout_2': '#4daf4a', 'Vout_3': '#984ea3', 'm2_source': '#9ecae1', 'm3_source': '#a1d99b',
        'm4_source': '#cbb4d4', 'Output1_drain': '#1f5f9f', 'Output2_drain': '#2d7f2a', 'Output3_drain': '#6a2f73',
        'Net-(M10-S)': '#08306b', 'Net-(M9-S)': '#00441b', 'Net-(M8-S)': '#3f007d', 'ISNS_P': '#000000', 'ISNS_N': '#000000'}


def run(L, meta, png, title):
    tg = C.distances(L)
    msgs, screws = C.mechanical(L, meta)
    fig, axs = plt.subplots(1, 2, figsize=(17, 10.5))
    for ax, side in zip(axs, 'FB'):
        ax.add_patch(Polygon(M.BOARD, closed=True, fill=False, lw=1.5))
        px, py, pr = M.PENETRATOR
        ax.add_patch(Circle((px, py), pr, fill=False, ls=':', color='k'))
        co = meta['corner']
        ax.add_patch(Rectangle(co[:2], co[2] - co[0], co[3] - co[1], fill=False, ls='--', color='orange'))
        cl = meta['card']
        ax.add_patch(Rectangle(cl[:2], cl[2] - cl[0], cl[3] - cl[1], fill=True, alpha=0.07, color='g', ls='--'))
        for ref in L:
            for s, r, kind in M.areas(L, ref):
                if s != side:
                    continue
                h = M.HEIGHT.get(ref, 2)
                fc = '#fdd0a2' if h > 14 else ('#fee6ce' if h > 5 else ('#deebf7' if kind == 'body' else '#f0f0f0'))
                if ref in M.FETS and kind == 'body':
                    fc = '#c6dbef' if ref not in meta['screwed'] else '#9ecae1'
                ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fc=fc, ec='k', lw=0.4, alpha=0.9))
                if kind == 'body':
                    fs = 7 if (r[2] - r[0]) * (r[3] - r[1]) > 60 else 4.5
                    ax.text((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, ref, ha='center', va='center', fontsize=fs)
            if side == L[ref][3] or M.is_tht(ref):
                for num, x, y, w, h, net, drill in M.pads(L, ref):
                    col = NETC.get(net, '#bbbbbb')
                    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=col, ec='none', alpha=0.8))
        for s, (x, y) in screws.items():
            ax.add_patch(Circle((x, y), 3.75, fill=False, color='r', lw=1))
            ax.plot([x], [y], 'r+')
        ax.set_xlim(26, 108)
        ax.set_ylim(119, 27)
        ax.set_aspect('equal')
        ax.grid(True, lw=0.2)
        ax.set_title('%s  %s side (seen from top)' % (title, 'TOP' if side == 'F' else 'BOTTOM'))
    fig.tight_layout()
    fig.savefig(png, dpi=100)
    plt.close(fig)
    lines = []
    for st, label, val, lim, kind, ok in tg:
        lines.append('S%d %-40s %6.1f  %s %-5s %s' % (st, label, val, kind, lim, 'ok' if ok else 'MISS'))
    return lines, msgs
