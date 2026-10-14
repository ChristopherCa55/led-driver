"""One image per copper layer, coloured by net group (from export_copper6.py's JSON).

    python render_layers.py power.json power OUTDIR [x1 y1 x2 y2 TAG]     (optional crop in board mm)
"""
import json, os, sys, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Patch
from matplotlib.collections import PatchCollection

FIXED = {
    'GND': '#a9b6c6', 'Vin': '#d62728', 'rsense_lo': '#7f1d1d', 'LX': '#ff7f0e',
    'Vout_1': '#1f5fb4', 'Vout_2': '#17becf', 'Vout_3': '#2ca02c',
    'm2_source': '#9467bd', 'm3_source': '#b39ddb', 'm4_source': '#5e3c99',
    'Output1_drain': '#8c564b', 'Output2_drain': '#b07a5a', 'Output3_drain': '#d6a77a',
    '12V': '#bcbd22', '5V': '#e7ba52', 'analog_5V': '#f2d59b',
}
SENSE = ('Current', 'ISNS_P', 'ISNS_N', 'SNS_CH1', 'SNS_CH2', 'SNS_CH3', 'IREF1_input', 'IREF2_input',
         'IREF3_input', 'V_err', 'Verr1', 'Verr2', 'Verr3')


def colour(net):
    if net in FIXED:
        return FIXED[net]
    if re.match(r'Net-\(M\d+-S\)', net):
        return '#c49c94'
    if net.startswith('GATE_') or re.match(r'Net-\(D\d+--\)', net) or 'VDDA' in net or 'U19-OUT' in net:
        return '#f19cbb'
    if net in SENSE or net.startswith('.1V'):
        return '#2a9d8f'
    return '#6e6e6e'


def main():
    js, tag, out = sys.argv[1:4]
    crop = list(map(float, sys.argv[4:8])) if len(sys.argv) >= 9 else None
    ctag = sys.argv[8] if crop else ''
    d = json.load(open(js))
    os.makedirs(out, exist_ok=True)
    edge = d.get('edge') or []
    order = sorted(d['nets'], key=lambda n: (n != 'GND', n in FIXED, n))   # GND first, power nets last (on top)
    for ln in d['layers']:
        fig, ax = plt.subplots(figsize=(13, 13 if not crop else 9), dpi=140)
        ax.set_facecolor('#ffffff')
        for net in order:
            polys = [p for p in d['nets'][net].get(ln, []) if isinstance(p, list) and len(p) >= 3]
            if not polys:
                continue
            pc = PatchCollection([Polygon(p, closed=True) for p in polys], facecolor=colour(net),
                                 edgecolor='none', alpha=0.95 if net != 'GND' else 0.85)
            ax.add_collection(pc)
        for b in d['barrels']:
            if ln in b.get('layers', []) or b.get('kind') == 'tht':
                ax.add_patch(plt.Circle((b['x'], b['y']), b['drill'] / 2, color='white', zorder=5))
        for seg in edge:
            ax.plot([seg[0], seg[2]], [seg[1], seg[3]], color='black', lw=1)
        ax.set_aspect('equal')
        allx = [v for seg in edge for v in (seg[0], seg[2])] or [0, 100]
        ally = [v for seg in edge for v in (seg[1], seg[3])] or [0, 100]
        if crop:
            ax.set_xlim(crop[0], crop[2])
            ax.set_ylim(crop[3], crop[1])
        else:
            ax.set_xlim(min(allx) - 1, max(allx) + 1)
            ax.set_ylim(max(ally) + 1, min(ally) - 1)
        ax.grid(True, color='#dddddd', lw=0.4)
        ax.minorticks_on()
        ax.set_title('%s  %s%s' % (tag, ln, ('  ' + ctag) if ctag else ''))
        present = {n for n in d['nets'] if d['nets'][n].get(ln)}
        handles = [Patch(color=c, label=n) for n, c in FIXED.items() if n in present]
        handles += [Patch(color='#f19cbb', label='gate drive'), Patch(color='#2a9d8f', label='sense / reference'),
                    Patch(color='#c49c94', label='LED sink source (M8-M10 S)'), Patch(color='#6e6e6e', label='other')]
        ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=8)
        fig.tight_layout()
        name = '%s_%s%s.png' % (tag, ln.replace('.', ''), ('_' + ctag) if ctag else '')
        fig.savefig(os.path.join(out, name))
        plt.close(fig)
        print('wrote', name)


if __name__ == '__main__':
    main()
