"""Plot the board from a dump: courtyards, pads coloured by power net, keep-outs, optional copper polygons.

usage: python plot_nets.py DUMP.json OUT.png [--side F|B|both] [--zoom x0,y0,x1,y1] [--copper COPPER.json]
"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

args = sys.argv[1:]
dump = json.load(open(args[0]))
out = args[1]
side = 'both'
zoom = None
copper = None
for i, a in enumerate(args):
    if a == '--side':
        side = args[i + 1]
    if a == '--zoom':
        zoom = [float(v) for v in args[i + 1].split(',')]
    if a == '--copper':
        copper = json.load(open(args[i + 1]))

COL = {'Vin': '#d62728', 'rsense_lo': '#ff7f0e', 'LX': '#9467bd', 'GND': '#555555',
       'm2_source': '#1f77b4', 'm3_source': '#17becf', 'm4_source': '#2ca02c',
       'Vout_1': '#1f77b4', 'Vout_2': '#17becf', 'Vout_3': '#2ca02c',
       'Output1_drain': '#8c564b', 'Output2_drain': '#e377c2', 'Output3_drain': '#bcbd22',
       'Net-(M8-S)': '#bcbd22', 'Net-(M9-S)': '#e377c2', 'Net-(M10-S)': '#8c564b'}

sides = ['F', 'B'] if side == 'both' else [side]
fs = (11 * len(sides), 13) if not zoom else (16 * len(sides), 16 * (zoom[3] - zoom[1]) / (zoom[2] - zoom[0]))
fig, axes = plt.subplots(1, len(sides), figsize=fs)
if len(sides) == 1:
    axes = [axes]
for ax, s in zip(axes, sides):
    for e in dump['edge']:
        ax.plot([e[0], e[2]], [e[1], e[3]], 'k-', lw=1.5)
    for z in dump['zones']:
        if z['keepout']:
            ax.add_patch(Polygon(z['outline'], closed=True, fc='#ffdddd', ec='r', lw=0.6))
    if copper:
        for c in copper:
            if c['layer'] == ('F.Cu' if s == 'F' else 'B.Cu'):
                ax.add_patch(Polygon(c['pts'], closed=True, fc=COL.get(c['net'], '#999999'), alpha=0.25,
                                     ec=COL.get(c['net'], '#999999'), lw=0.8))
    for f in dump['footprints']:
        if 'crtyd' in f and f['side'] == s:
            x0, y0, x1, y1 = f['crtyd']
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec='#999999', lw=0.5))
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, f['ref'], fontsize=6, ha='center', va='center', color='#444444')
        for p in f['pads']:
            smd_here = p['drill'] == 0 and f['side'] == s
            if not (smd_here or p['drill'] > 0):
                continue
            x0, y0, x1, y1 = p['bbox']
            col = COL.get(p['net'], '#dddddd')
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=col, ec='k' if p['drill'] > 0 else col,
                                   lw=0.3, alpha=0.85))
            if zoom and (x1 - x0) > 0.5:
                short = p['net'].replace('Net-(', '').replace(')', '')[:9]
                ax.text((x0 + x1) / 2, (y0 + y1) / 2, '%s.%s/%s' % (f['ref'], p['num'], short), fontsize=4.5,
                        rotation=0 if (x1 - x0) >= (y1 - y0) else 90,
                        ha='center', va='center', color='k', clip_on=True)
            elif p['net'] in COL and (x1 - x0) > 1.5:
                ax.text((x0 + x1) / 2, (y0 + y1) / 2, '%s.%s' % (f['ref'], p['num']), fontsize=5, ha='center',
                        va='center', color='w')
    ax.set_aspect('equal')
    ax.set_title('%s side (seen from top)' % s)
    ax.grid(True, lw=0.3, alpha=0.4)
    ax.set_xticks(range(30, 106, 1 if zoom else 5), minor=False)
    ax.set_yticks(range(30, 117, 1 if zoom else 5), minor=False)
    ax.tick_params(labelsize=7)
    if zoom:
        ax.set_xlim(zoom[0], zoom[2])
        ax.set_ylim(zoom[3], zoom[1])
    else:
        ax.set_xlim(29, 105)
        ax.set_ylim(117, 29)
fig.tight_layout()
fig.savefig(out, dpi=110)
print('wrote', out)
