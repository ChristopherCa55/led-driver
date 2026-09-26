"""Signal-routing statistics from two copper exports (system Python): the routed board and the board before routing.

usage: python route_stats.py ROUTED_CU.json UNROUTED_CU.json OUT.json [OUT.png]

Reports per net: track length by layer, widths used, vias added (barrels in ROUTED that are not in UNROUTED);
the ISNS_P/ISNS_N spacing along ISNS_N; and, with OUT.png, a per-layer plot of the routes coloured by netclass.
"""
import json, math, sys, collections
import numpy as np

routed = json.load(open(sys.argv[1]))
before = json.load(open(sys.argv[2]))
classes = routed.get('classes', {})
key = lambda v: (round(v['x'], 3), round(v['y'], 3))
old = {key(v) for v in before['vias']}
new_vias = [v for v in routed['vias'] if key(v) not in old]

nets = collections.defaultdict(lambda: dict(length=0.0, layers=collections.Counter(), widths=collections.Counter(),
                                            vias=collections.Counter()))
for t in routed['tracks']:
    d = math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0'])
    r = nets[t['net']]
    r['length'] += d
    r['layers'][t['layer']] += d
    r['widths'][round(t['w'], 2)] += d
for v in new_vias:
    nets[v['net']]['vias']['%.1f/%.1f' % (v['dia'], v['drill'])] += 1

out = {}
for n, r in sorted(nets.items(), key=lambda kv: -kv[1]['length']):
    out[n] = dict(netclass=classes.get(n, 'Default'), length_mm=round(r['length'], 1),
                  layers={k: round(x, 1) for k, x in r['layers'].most_common()},
                  widths={str(k): round(x, 1) for k, x in sorted(r['widths'].items())},
                  vias=dict(r['vias']))


def samples(net, step=0.1):
    pts = []
    for t in routed['tracks']:
        if t['net'] != net:
            continue
        d = math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0'])
        k = max(1, int(d / step))
        for i in range(k + 1):
            pts.append((t['x0'] + (t['x1'] - t['x0']) * i / k, t['y0'] + (t['y1'] - t['y0']) * i / k, t['layer']))
    return pts


pn, pp = samples('ISNS_N'), samples('ISNS_P')
if pn and pp:
    P = np.array([(x, y) for x, y, _ in pp])
    gaps = [float(np.min(np.hypot(P[:, 0] - x, P[:, 1] - y))) for x, y, _ in pn]
    out['_isns_pair'] = dict(n_samples=len(gaps), centre_spacing_median_mm=round(float(np.median(gaps)), 2),
                             centre_spacing_p90_mm=round(float(np.percentile(gaps, 90)), 2),
                             centre_spacing_max_mm=round(max(gaps), 2))
out['_totals'] = dict(tracks=len(routed['tracks']), track_mm=round(sum(r['length'] for r in nets.values()), 1),
                      vias_added=len(new_vias))
json.dump(out, open(sys.argv[3], 'w'), indent=1)
print('%-18s %-8s %7s %-34s %-22s %s' % ('net', 'class', 'mm', 'layers (mm)', 'widths (mm: mm)', 'vias'))
for n, r in out.items():
    if n.startswith('_'):
        continue
    print('%-18s %-8s %7.1f %-34s %-22s %s' % (n, r['netclass'][:8], r['length_mm'],
          ', '.join('%s %.0f' % (k.replace('.Cu', ''), x) for k, x in r['layers'].items()),
          ', '.join('%s: %.0f' % (k, x) for k, x in r['widths'].items()),
          ', '.join('%s x%d' % (k, c) for k, c in r['vias'].items())))
for k in ('_isns_pair', '_totals'):
    print(k, out.get(k))

if len(sys.argv) > 4:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Circle
    COL = {'Sense': '#d62728', 'Gate': '#ff7f0e', 'Rail': '#9467bd', 'Power': '#1f77b4', 'Default': '#2ca02c'}
    LAY = ['F.Cu', 'In2.Cu', 'In3.Cu', 'In5.Cu', 'B.Cu']
    fig, axs = plt.subplots(1, 5, figsize=(30, 7.6))
    for ax, ln in zip(axs, LAY):
        for z in routed['zones']:
            if z['layer'] != ln:
                continue
            fc = '#e8e8e8' if z['net'] == 'GND' else '#cfd8e3'
            for poly in z['polys']:
                if not isinstance(poly, dict):
                    ax.add_patch(Polygon(poly, closed=True, fc=fc, ec='none'))
        for p in routed['pads']:
            for poly in p['polys'].get(ln, []):
                if not isinstance(poly, dict):
                    ax.add_patch(Polygon(poly, closed=True, fc='#555555', ec='none'))
        for t in routed['tracks']:
            if t['layer'] != ln:
                continue
            c = COL.get(classes.get(t['net'], 'Default').split(',')[0], COL['Default'])
            ax.plot([t['x0'], t['x1']], [t['y0'], t['y1']], color=c, lw=max(0.6, t['w'] * 2.2), solid_capstyle='round')
        for v in new_vias:
            ax.add_patch(Circle((v['x'], v['y']), v['dia'] / 2, fc='none', ec='k', lw=0.5))
        ax.set_xlim(29, 105)
        ax.set_ylim(117, 29)
        ax.set_aspect('equal')
        ax.set_title(ln + ' (grey: GND fill; blue-grey: power pours; rings: vias added in routing)', fontsize=8)
        ax.tick_params(labelsize=6)
    handles = [plt.Line2D([], [], color=c, lw=3, label=k) for k, c in COL.items()]
    fig.legend(handles=handles, loc='lower center', ncol=5, fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(sys.argv[4], dpi=130)
    print('wrote', sys.argv[4])
