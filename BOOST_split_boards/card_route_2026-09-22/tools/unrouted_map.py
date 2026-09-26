"""Map of a board's unconnected pairs from its kicad-cli DRC report, over the pads of a copper export (system Python).

usage: python unrouted_map.py COPPER.json DRC.json OUT.png "TITLE"
Pads grey (top side darker), each unconnected pair a line coloured by net class (card_nets.py).
"""
import json, re, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

sys.path.insert(0, 'tools')
from card_nets import ANALOG, RAILS

cop = json.load(open(sys.argv[1]))
drc = json.load(open(sys.argv[2]))
fig, ax = plt.subplots(figsize=(9, 9), dpi=130)
for p in cop['pads']:
    for ln, polys in p['polys'].items():
        if ln not in ('F.Cu', 'B.Cu'):
            continue
        for poly in polys:
            pts = poly['outline'] if isinstance(poly, dict) else poly
            ax.add_patch(Polygon(pts, closed=True, fc='#555555' if ln == 'F.Cu' else '#bbbbbb', ec='none', alpha=0.8))
col = {'logic': '#1f77b4', 'analog': '#d62728', 'rail': '#ff7f0e', 'GND': '#2ca02c', '5V': '#9467bd'}
seen = set()
n = 0
for u in drc['unconnected_items']:
    a, b = u['items'][0], u['items'][1]
    m = re.search(r'\[([^\]]+)\]', a['description'])
    net = m.group(1) if m else '?'
    c = 'rail' if net in RAILS else 'analog' if net in ANALOG else net if net in ('GND', '5V') else 'logic'
    ax.plot([a['pos']['x'], b['pos']['x']], [a['pos']['y'], b['pos']['y']], '-', color=col[c], lw=1.6,
            label=c if c not in seen else None)
    ax.plot([a['pos']['x'], b['pos']['x']], [a['pos']['y'], b['pos']['y']], 'o', color=col[c], ms=3)
    seen.add(c)
    n += 1
ax.set_xlim(45.5, 91.3)
ax.set_ylim(115.4, 69.6)
ax.set_aspect('equal')
ax.set_xlabel('x (mm)')
ax.set_ylabel('y (mm)')
ax.set_title('%s: %d unconnected pairs (pads: top dark, underside light)' % (sys.argv[4], n))
ax.legend(loc='lower right')
fig.tight_layout()
fig.savefig(sys.argv[3])
print('wrote', sys.argv[3])
