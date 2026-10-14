"""Plan view of one or more nets' tracks, vias and pads on every layer (colour per layer), over a faint picture of a
chosen background layer's copper, with keepouts and part labels. For planning reroutes.

    python net_map.py CU.json OUT.png BG_LAYER NET[,NET...] [x1 y1 x2 y2] [--refs R1,U19,...]
"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

LC = {'F.Cu': '#d62728', 'In1.Cu': '#8c564b', 'In2.Cu': '#ff7f0e', 'In3.Cu': '#2ca02c', 'In4.Cu': '#1f77b4',
      'B.Cu': '#9467bd'}
BGC = {'GND': '#c8d0da', 'Vin': '#f4b6b6', 'LX': '#ffd9b0', 'rsense_lo': '#e0a0a0', 'Vout_1': '#b9cbe8',
       'Vout_2': '#bfe9ef', 'Vout_3': '#c5e8c5'}


def main():
    a = sys.argv[1:]
    refs = []
    if '--refs' in a:
        i = a.index('--refs')
        refs = a[i + 1].split(',')
        a = a[:i] + a[i + 2:]
    cu, out, bg, nets = a[0], a[1], a[2], a[3].split(',')
    box = list(map(float, a[4:8])) if len(a) >= 8 else None
    d = json.load(open(cu))
    fig, ax = plt.subplots(figsize=(13, 13), dpi=110)
    for net, layers in d['nets'].items():
        polys = [p for p in layers.get(bg, []) if isinstance(p, list) and len(p) > 2]
        if polys:
            ax.add_collection(PatchCollection([Polygon(p) for p in polys], facecolor=BGC.get(net, '#e6e6e6'),
                                              edgecolor='none', zorder=0))
    for k in d.get('keepouts', []):
        xs = [p[0] for p in k['pts']] + [k['pts'][0][0]]
        ys = [p[1] for p in k['pts']] + [k['pts'][0][1]]
        ax.plot(xs, ys, 'k--', lw=0.8, zorder=1)
    for t in d['tracks']:
        if t['net'] in nets:
            ax.plot([t['x0'], t['x1']], [t['y0'], t['y1']], color=LC[t['layer']], lw=max(1.0, t['w'] * 6),
                    solid_capstyle='round', zorder=3, alpha=0.85)
    for v in d['vias']:
        if v['net'] in nets:
            ax.add_patch(plt.Circle((v['x'], v['y']), v['dia'] / 2, color='black', zorder=4))
            ax.text(v['x'] + 0.4, v['y'] - 0.3, '/'.join(l[:3] for l in v['layers']), fontsize=6, zorder=5, clip_on=True)
    for p in d['pads']:
        if p['net'] in nets:
            ax.plot(p['x'], p['y'], 's', color='gold', mec='black', ms=6, zorder=5)
            ax.text(p['x'] + 0.4, p['y'] + 0.6, '%s.%s' % (p['ref'], p['num']), fontsize=7, zorder=6, weight='bold', clip_on=True)
    for r in refs:
        ps = [p for p in d['pads'] if p['ref'] == r]
        if ps:
            x = sum(p['x'] for p in ps) / len(ps)
            y = sum(p['y'] for p in ps) / len(ps)
            ax.text(x, y, r, fontsize=9, color='black', ha='center', zorder=6, clip_on=True,
                    bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='grey', alpha=0.7))
    for s in d['edge']:
        ax.plot([s[0], s[2]], [s[1], s[3]], 'k-', lw=1)
    for ln, c in LC.items():
        ax.plot([], [], color=c, lw=3, label=ln)
    ax.legend(loc='upper left', fontsize=8)
    ax.set_aspect('equal')
    if box:
        ax.set_xlim(box[0], box[2]); ax.set_ylim(box[3], box[1])
    else:
        ax.invert_yaxis()
    ax.grid(True, lw=0.3)
    ax.set_title('%s on all layers (background: %s copper)' % (','.join(nets), bg))
    fig.tight_layout()
    fig.savefig(out)
    print('wrote', out)


if __name__ == '__main__':
    main()
