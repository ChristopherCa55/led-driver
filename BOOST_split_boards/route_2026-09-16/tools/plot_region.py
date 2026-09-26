"""Plot a board region per routing layer from a copper export plus router output (system Python).

usage: python plot_region.py COPPER.json ROUTES.json OUT.png X0 Y0 X1 Y1 NET[,NET...]
Highlighted nets in colour (one per net), other copper grey, zones lighter, holes black, vias as rings.
"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle

cop = json.load(open(sys.argv[1]))
rt = json.load(open(sys.argv[2])) if sys.argv[2] != '-' else dict(tracks=[], vias=[])
out = sys.argv[3]
x0, y0, x1, y1 = map(float, sys.argv[4:8])
hl = sys.argv[8].split(',') if len(sys.argv) > 8 else []
COL = ['tab:red', 'tab:blue', 'tab:green', 'tab:orange', 'tab:purple', 'tab:cyan', 'tab:olive', 'tab:pink']
col = {n: COL[i % len(COL)] for i, n in enumerate(hl)}
import os
LAYERS = os.environ.get('PLOT_LAYERS', 'F.Cu,In2.Cu,In3.Cu,In5.Cu,B.Cu').split(',')


def inwin(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return max(xs) >= x0 and min(xs) <= x1 and max(ys) >= y0 and min(ys) <= y1


PW = float(os.environ.get('PLOT_W', '5.2'))
fig, axs = plt.subplots(1, len(LAYERS), figsize=(PW * len(LAYERS), PW * (y1 - y0) / (x1 - x0) + 0.6), squeeze=False)
axs = axs[0]
for ax, ln in zip(axs, LAYERS):
    for z in cop['zones']:
        if z['layer'] != ln:
            continue
        for poly in z['polys']:
            if isinstance(poly, dict) or not inwin(poly):
                continue
            c = col.get(z['net'], '0.82' if z['prio'] > 1 else '0.93')
            ax.add_patch(Polygon(poly, closed=True, fc=c, ec='none', alpha=0.35 if z['net'] in col else 1))
    for p in cop['pads']:
        for poly in p['polys'].get(ln, []):
            if isinstance(poly, dict) or not inwin(poly):
                continue
            ax.add_patch(Polygon(poly, closed=True, fc=col.get(p['net'], '0.45'), ec='k', lw=0.3))
        if ln in p['polys'] and x0 <= p['x'] <= x1 and y0 <= p['y'] <= y1:
            ax.text(p['x'], p['y'], '%s.%s' % (p['ref'], p['num']), fontsize=float(os.environ.get('PLOT_FS', '4')), ha='center', va='center', color='w')
    for t in cop.get('tracks', []) + rt['tracks']:
        if t['layer'] != ln or not inwin([[t['x0'], t['y0']], [t['x1'], t['y1']]]):
            continue
        ax.plot([t['x0'], t['x1']], [t['y0'], t['y1']], color=col.get(t['net'], '0.35'), lw=t['w'] * PW * 72 / (x1 - x0) * 0.8,
                solid_capstyle='round', alpha=0.8)
    for v in cop['vias'] + rt['vias']:
        if not (x0 <= v['x'] <= x1 and y0 <= v['y'] <= y1):
            continue
        ax.add_patch(Circle((v['x'], v['y']), v['dia'] / 2, fc=col.get(v['net'], '0.55') if ln in v['layers'] else 'none',
                            ec=col.get(v['net'], '0.3'), lw=0.4))
        ax.add_patch(Circle((v['x'], v['y']), v['drill'] / 2, fc='k', ec='none'))
    for b in cop['barrels']:
        if b['kind'] == 'tht' and x0 <= b['x'] <= x1 and y0 <= b['y'] <= y1:
            ax.add_patch(Circle((b['x'], b['y']), b['drill'] / 2, fc='k', ec='none'))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_aspect('equal')
    ax.set_title(ln, fontsize=9)
    ax.tick_params(labelsize=6)
handles = [plt.Line2D([], [], color=c, lw=4, label=n) for n, c in col.items()]
fig.legend(handles=handles, loc='lower center', ncol=len(handles), fontsize=8)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(out, dpi=170)
print('wrote', out)
