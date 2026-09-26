"""Placement check for the control card (system Python): legality, distances, heights, and a plot.

usage: python card_check.py CONFIG.json LAYOUT.json OUT.md [OUT.png]

Reads the placer config and a layout. Reports:
- legality in the placer's model: courtyard overlaps per side (through-hole parts on both), parts outside the card,
  mounting-hole keep-out intrusions (KiCad DRC on the saved board is the final word);
- the analog constraints: the Current net (J11.23 -> U2.4, U5.3), its distance to the 74HC14s, M1_ON and I2C,
  D27 / R105 at the M1_INHIBIT node;
- decoupling: each IC supply pin to its nearest capacitor on the rail;
- J9's pins to their first load;
- heights per side from package maxima (no part numbers in the netlist except J11 and U26), and which underside
  parts sit over an output can of the frozen power board.
"""
import json, math, sys
import numpy as np

cfg = json.load(open(sys.argv[1]))
lay = json.load(open(sys.argv[2]))['layout']
OUT = sys.argv[3]
PNG = sys.argv[4] if len(sys.argv) > 4 else None
inv = json.load(open(cfg['inventory']))
X0, Y0, X1, Y1 = cfg['card']
MATS = [((1, 0), (0, 1)), ((0, -1), (1, 0)), ((-1, 0), (0, -1)), ((0, 1), (-1, 0))]
# package maxima (JEDEC / typical manufacturer outlines); not part-number heights
PKG_H = [('SOIC', 1.75, 'JEDEC MS-012 max'), ('TSSOP', 1.20, 'JEDEC MO-153 max'), ('SOT-23-5', 1.45, 'MO-178 max'),
         ('SOT-23', 1.45, 'MO-178 / TO-236 up to 1.45'), ('SOD-123', 1.35, 'typical max, varies by maker'),
         ('SOD-323', 1.10, 'typical max'), ('R_0603', 0.55, 'thick film'), ('C_0603', 0.95, '0.8 + 0.15'),
         ('R_0805', 0.65, 'thick film'), ('C_0805', 1.45, '1.25 + 0.2'), ('C_1206', 1.80, '1.6 + 0.2 worst case'),
         ('WirePads', 1.0, 'trimmed solder fillet'), ('PinHeader_2x15', 0.94, 'TSW tail above the card top'),
         ('MountingHole', 0.0, '')]


def pkg_h(fp):
    for k, h, why in PKG_H:
        if k in fp:
            return h, why
    return None, 'unknown'


def tf(ref, lx, ly):
    x, y, rot, side = lay[ref]
    m = MATS[int(round(rot / 90)) % 4]
    ly = -ly if side == 'B' else ly
    return x + lx * m[0][0] + ly * m[1][0], y + lx * m[0][1] + ly * m[1][1]


pin = {}
netpins = {}
for r, v in inv.items():
    for p in v['pads']:
        if p.get('num'):
            pin['%s.%s' % (r, p['num'])] = tf(r, p['x'], p['y'])
            netpins.setdefault(p.get('net', ''), []).append('%s.%s' % (r, p['num']))


def box(r):
    c = inv[r]['courtyard']
    pts = [tf(r, c[0], c[1]), tf(r, c[2], c[1]), tf(r, c[2], c[3]), tf(r, c[0], c[3])]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def d(a, b):
    return math.hypot(pin[a][0] - pin[b][0], pin[a][1] - pin[b][1])


def mst(net):
    """Minimum spanning tree of the net's pins: [(pin_a, pin_b)], a proxy for its route."""
    ps = [p for p in netpins.get(net, []) if p in pin]
    if len(ps) < 2:
        return []
    inn, out = [ps[0]], ps[1:]
    segs = []
    while out:
        dd, a, b = min((d(a, b), a, b) for a in inn for b in out)
        segs.append((a, b))
        inn.append(b)
        out.remove(b)
    return segs


def pt_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / max(dx * dx + dy * dy, 1e-12)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def seg_seg(a1, a2, b1, b2):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if o(a1, a2, b1) * o(a1, a2, b2) < 0 and o(b1, b2, a1) * o(b1, b2, a2) < 0:
        return 0.0
    return min(pt_seg(a1, b1, b2), pt_seg(a2, b1, b2), pt_seg(b1, a1, a2), pt_seg(b2, a1, a2))


L = []
# legality
boxes = {r: box(r) for r in lay if inv[r]['courtyard']}
ov = []
rs = sorted(boxes)
for i in range(len(rs)):
    for j in range(i + 1, len(rs)):
        a, b = rs[i], rs[j]
        if lay[a][3] != lay[b][3] and not inv[a]['tht'] and not inv[b]['tht']:
            continue
        A, B = boxes[a], boxes[b]
        w = min(A[2], B[2]) - max(A[0], B[0])
        h = min(A[3], B[3]) - max(A[1], B[1])
        if w > 1e-6 and h > 1e-6:
            ov.append((a, b, w * h))
outside = [r for r, b in boxes.items() if b[0] < X0 or b[1] < Y0 or b[2] > X1 or b[3] > Y1]
ko = []
for kx, ky, kr in cfg.get('keepouts', []):
    for r, b in boxes.items():
        if r.startswith('H'):
            continue
        dd = math.hypot(max(b[0] - kx, 0, kx - b[2]), max(b[1] - ky, 0, ky - b[3]))
        if dd < kr - 1e-6:
            ko.append((r, (kx, ky), round(kr - dd, 3)))
nF = sum(1 for r in lay if lay[r][3] == 'F' and not inv[r]['tht'])
nB = sum(1 for r in lay if lay[r][3] == 'B' and not inv[r]['tht'])
L.append('## Legality (placer model; DRC on the saved board is separate)\n')
L.append('- Courtyard overlaps: %d%s' % (len(ov), ''.join('\n  - %s x %s: %.3f mm2' % o for o in ov[:20])))
L.append('- Outside the card: %s' % (', '.join(outside) or 'none'))
L.append('- Inside a mounting-hole keep-out: %s' % (', '.join('%s (%.2f mm)' % (r, p) for r, c, p in ko) or 'none'))
L.append('- SMD parts: %d on the top (F), %d on the underside (B)\n' % (nF, nB))

# analog
L.append('## Analog constraints\n')
L.append('| Item | Value |\n|---|---|')
cur = [p for p in netpins.get('Current', []) if p in pin]
for p in cur:
    if p != 'J11.23':
        L.append('| Current: J11.23 -> %s | %.1f mm straight, %s side |' % (p, d('J11.23', p), lay[p.split('.')[0]][3]))
xs = [pin[p][0] for p in cur]
ys = [pin[p][1] for p in cur]
L.append('| Current net half-perimeter | %.1f mm |' % ((max(xs) - min(xs)) + (max(ys) - min(ys))))
for grp, members in (('74HC14 U104', [p for p in pin if p.startswith('U104.')]),
                     ('74HC14 U105', [p for p in pin if p.startswith('U105.')]),
                     ('M1_ON', [p for p in netpins.get('M1_ON', []) if p in pin]),
                     ('SCL', [p for p in netpins.get('SCL', []) if p in pin]),
                     ('SDA', [p for p in netpins.get('SDA', []) if p in pin])):
    best = min((d(a, b), a, b) for a in cur for b in members)
    L.append('| Current pins to %s | %.1f mm (%s - %s) |' % (grp, best[0], best[1], best[2]))
for a, b, m, w in cfg.get('near', []):
    L.append('| %s -> %s | %.1f mm (limit %.1f) |' % (a, b, d(a, b), m))


def expand(items):
    out = []
    for it in items:
        if it.startswith('net:'):
            out += [q for q in netpins.get(it[4:], []) if q in pin]
        elif it in pin:
            out.append(it)
        else:
            out += [q for q in pin if q.split('.')[0] == it]
    return sorted(set(out))


for a, b, m, w in cfg.get('apart', []):
    best = min((d(p, q), p, q) for p in expand(a) for q in expand(b))
    L.append('| apart: {%s} vs {%s} | %.1f mm (%s - %s), minimum %.1f |' % (
        ', '.join(a), ', '.join(b), best[0], best[1], best[2], m))
for vic, agg, m, w in cfg.get('apart_seg', []):
    for g in agg:
        best = min((seg_seg(pin[a], pin[b], pin[c], pin[e]), '%s-%s' % (a, b), '%s-%s' % (c, e))
                   for v in vic for a, b in mst(v) for c, e in mst(g))
        L.append('| route proxy: %s vs %s | %.1f mm (%s / %s), minimum %.1f%s |' % (
            '+'.join(vic), g, best[0], best[1], best[2], m, '' if best[0] >= m - 1e-6 else ' **short**'))
for r, sd in cfg.get('side_only', {}).items():
    L.append('| %s restricted to %s | on %s |' % (r, sd, lay[r][3]))
mi = [p for p in netpins.get('M1_INHIBIT', []) if p in pin]
L.append('| M1_INHIBIT node spread (%s) | %.1f mm half-perimeter |' % (
    ', '.join(mi), (max(pin[p][0] for p in mi) - min(pin[p][0] for p in mi)) +
    (max(pin[p][1] for p in mi) - min(pin[p][1] for p in mi))))
L.append('')

# decoupling
L.append('## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)\n')
L.append('| Pin | Rail | Nearest cap | mm | Side (IC / cap) |\n|---|---|---|---|---|')
for rail in cfg.get('decap_rails', ['5V', 'analog_5V']):
    ics = [p for p in netpins.get(rail, []) if p in pin and p[0] in 'UQ']
    caps = [p for p in netpins.get(rail, []) if p in pin and p.startswith('C')
            and any(q in netpins.get('GND', []) for q in ('%s.1' % p.split('.')[0], '%s.2' % p.split('.')[0]))]
    for p in sorted(ics, key=lambda s: (len(s.split('.')[0]), s)):
        dd, c = min((d(p, c), c) for c in caps)
        L.append('| %s | %s | %s | %.1f | %s / %s |' % (p, rail, c.split('.')[0], dd, lay[p.split('.')[0]][3],
                                                       lay[c.split('.')[0]][3]))
L.append('')

# J9
L.append('## J9 (wire pads) to first load\n')
L.append('| J9 pin | Net | Nearest other pin | mm |\n|---|---|---|---|')
for k in range(1, 12):
    p = 'J9.%d' % k
    net = [nn for nn, ps in netpins.items() if p in ps][0]
    others = [q for q in netpins[net] if q in pin and not q.startswith('J9.')]
    if net in ('GND', '5V') or not others:
        L.append('| %d | %s | (plane) | - |' % (k, net))
        continue
    dd, q = min((d(p, q), q) for q in others)
    L.append('| %d | %s | %s | %.1f |' % (k, net, q, dd))
L.append('')

# heights
L.append('## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)\n')
cans = cfg.get('cans', [])
over = []
top_max = (0, '')
bot_max = (0, '')
flag = []
for r in lay:
    h, why = pkg_h(inv[r]['fp'])
    if h is None:
        flag.append(r)
        continue
    if inv[r]['tht']:
        continue
    b = boxes.get(r)
    if lay[r][3] == 'F':
        if h > top_max[0]:
            top_max = (h, r)
        if h > 1.75:
            flag.append('%s (%s, %.2f mm on top)' % (r, inv[r]['fp'].split(':')[-1], h))
    else:
        if h > bot_max[0]:
            bot_max = (h, r)
        for cx, cy, cr, ref in cans:
            if b and math.hypot(max(b[0] - cx, 0, cx - b[2]), max(b[1] - cy, 0, cy - b[3])) < cr:
                over.append((r, ref, h))
L.append('- Tallest on the top: %.2f mm (%s); tallest on the underside: %.2f mm (%s)' % (top_max[0], top_max[1],
                                                                                   bot_max[0], bot_max[1]))
L.append('- Over the top limit: %s' % (', '.join(flag) or 'none'))
L.append('- Underside parts over an output can: %d, tallest %.2f mm (limit 2.7)' % (
    len(over), max([o[2] for o in over], default=0)))
open(OUT, 'w', encoding='utf8').write('\n'.join(L) + '\n')
print('\n'.join(L))

if PNG:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, axs = plt.subplots(1, 2, figsize=(17, 8.8))
    hl = {'Current': 'red', 'V_err': 'magenta', 'Net-(U2-In+)': 'red', 'SCL': 'tab:purple', 'SDA': 'tab:purple',
          'M1_ON': 'tab:orange', 'M1_INHIBIT': 'tab:brown', 'ARD_M1_INHIBIT': 'tab:brown'}
    for g in ('M2_ON', 'out_2_on', 'out_3_on', 'VerrGT0', 'ena_out_1', 'ena_out_2', 'ena_out_3'):
        hl[g] = 'tab:olive'
    for ax, sd in zip(axs, 'FB'):
        ax.add_patch(Rectangle((X0, Y0), X1 - X0, Y1 - Y0, fill=False, lw=1.5))
        for cx, cy, cr, ref in cans:
            ax.add_patch(Circle((cx, cy), cr, color='tab:red', alpha=0.08 if sd == 'F' else 0.18))
            ax.text(cx, cy, ref, fontsize=6, color='tab:red', alpha=0.6, ha='center')
        for kx, ky, kr in cfg.get('keepouts', []):
            ax.add_patch(Circle((kx, ky), kr, fill=False, color='b', lw=0.8))
        for r, b in boxes.items():
            if lay[r][3] != sd and not inv[r]['tht']:
                continue
            ic = r[0] in 'UQJ'
            ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fc='#c6dbef' if ic else '#f0f0f0', ec='k',
                                   lw=0.4))
            ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, r, fontsize=6 if ic else 3.5, ha='center', va='center')
        for net, col in hl.items():
            for a, b in mst(net):
                ax.plot([pin[a][0], pin[b][0]], [pin[a][1], pin[b][1]], color=col, lw=0.9)
        ax.set_xlim(X0 - 1, X1 + 1)
        ax.set_ylim(Y1 + 1, Y0 - 1)
        ax.set_aspect('equal')
        ax.set_title('%s side (%s)%s' % ('top' if sd == 'F' else 'underside', sd,
                                        ' - seen from the top' if sd == 'B' else ''))
    fig.suptitle('Control card placement (nets as minimum spanning trees of their pins): red Current and U2 In+, '
                 'magenta V_err, purple I2C,' + chr(10) + 'orange M1_ON, olive other 74HC14 outputs, brown M1_INHIBIT; '
                 'red circles = output cans below; blue = H1-H4 keep-outs')
    fig.savefig(PNG, dpi=120, bbox_inches='tight')
    print('wrote', PNG)
