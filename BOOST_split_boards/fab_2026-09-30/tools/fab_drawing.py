"""Fabrication drawing, one A3 landscape PDF page per board (system Python, matplotlib). 2026-09-24, re-used 2026-09-30.

usage: python fab_drawing.py power|card        (run from fab_2026-09-30/)

Draws the outline (dimensioned from the lower-left corner of the outline), every drilled hole with one symbol per
drill size (from the Excellon files that go to the fab), the stackup read from the board file, the drill table and
the fabrication notes. Facts come from work/<board>_facts.json (tools/fab_facts.py on the plotted copy).
"""
import json, re, sys, collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D

which = sys.argv[1]
NAME = {'power': 'BOOST_power_RC2', 'card': 'BOOST_control_RC2'}[which]
TITLE = {'power': 'BOOST power board', 'card': 'BOOST control card'}[which]
F = json.load(open('work/%s_facts.json' % which))


def read_drill(path):
    tools, hits, slots, cur = {}, [], [], None
    for ln in open(path):
        ln = ln.strip()
        m = re.match(r'T(\d+)C([\d.]+)', ln)
        if m:
            tools[m.group(1)] = float(m.group(2))
            continue
        m = re.match(r'T(\d+)$', ln)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r'X([-\d.]+)Y([-\d.]+)G85X([-\d.]+)Y([-\d.]+)', ln)
        if m:
            slots.append((tools[cur], float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))))
            continue
        m = re.match(r'X([-\d.]+)Y([-\d.]+)$', ln)
        if m:
            hits.append((tools[cur], float(m.group(1)), float(m.group(2))))
    return hits, slots


pth, pslots = read_drill('%s/gerbers/%s-PTH.drl' % (NAME, NAME))
npth, nslots = read_drill('%s/gerbers/%s-NPTH.drl' % (NAME, NAME))
x0, y0k, x1, y1k = F['outline_bbox_mm']       # KiCad coordinates (y down), outline line centres +/- 0.05
x0 += 0.05; y0k += 0.05; x1 -= 0.05; y1k -= 0.05
W, H = x1 - x0, y1k - y0k


def to_draw_k(x, y):          # KiCad (y down) -> drawing (datum lower-left, y up)
    return x - x0, y1k - y


def to_draw_d(x, y):          # Excellon (y = -KiCad y) -> drawing
    return x - x0, y1k + y


fig = plt.figure(figsize=(16.54, 11.69), dpi=100)          # A3 landscape
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.03, 0.08, 0.50, 0.84])
ax.set_aspect('equal')
ax.axis('off')
# outline
for poly in F['outline_vertices']:
    pts = [to_draw_k(x, y) for x, y in poly] + [to_draw_k(*poly[0])]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color='black', lw=1.4)
# holes: one marker per tool
SYM = ['o', 's', '^', 'D', 'v', 'P', 'X', '*', 'h', '<', '>', 'p']
sizes = sorted(set([('PTH', d) for d, _, _ in pth] + [('NPTH', d) for d, _, _ in npth] +
                   [('NPTH slot', s[0]) for s in nslots] + [('PTH slot', s[0]) for s in pslots]),
               key=lambda k: (k[1], k[0]))
sym = {k: SYM[i % len(SYM)] for i, k in enumerate(sizes)}
col = {'PTH': '#1f4e9c', 'NPTH': '#b3261e', 'NPTH slot': '#b3261e', 'PTH slot': '#1f4e9c'}
count = collections.Counter()
for kind, lst in (('PTH', pth), ('NPTH', npth)):
    for d, x, y in lst:
        X, Y = to_draw_d(x, y)
        count[(kind, d)] += 1
        if d >= 2.0:
            ax.add_patch(Circle((X, Y), d / 2, fill=False, ec=col[kind], lw=0.8))
        ax.plot(X, Y, marker=sym[(kind, d)], ms=2.2 if d < 1 else 3.2, mfc='none', mec=col[kind], mew=0.5)
for kind, lst in (('NPTH slot', nslots), ('PTH slot', pslots)):
    for d, xa, ya, xb, yb in lst:
        A, B = to_draw_d(xa, ya), to_draw_d(xb, yb)
        count[(kind, d)] += 1
        ax.add_patch(FancyBboxPatch((min(A[0], B[0]) - d / 2, A[1] - d / 2), abs(B[0] - A[0]) + d, d,
                                    boxstyle='round,pad=0,rounding_size=%g' % (d / 2 - 0.01), fill=False,
                                    ec=col[kind], lw=0.9))
        ax.plot((A[0] + B[0]) / 2, A[1], marker=sym[(kind, d)], ms=3.2, mfc='none', mec=col[kind], mew=0.6)


def dim_h(xa, xb, y, text, off):
    ax.annotate('', xy=(xa, y + off), xytext=(xb, y + off), arrowprops=dict(arrowstyle='<->', lw=0.7))
    ax.plot([xa, xa], [y, y + off * 1.1], color='0.4', lw=0.4)
    ax.plot([xb, xb], [y, y + off * 1.1], color='0.4', lw=0.4)
    ax.text((xa + xb) / 2, y + off + (1.2 if off > 0 else -2.6), text, ha='center', fontsize=8)


def dim_v(ya, yb, x, text, off):
    ax.annotate('', xy=(x + off, ya), xytext=(x + off, yb), arrowprops=dict(arrowstyle='<->', lw=0.7))
    ax.plot([x, x + off * 1.1], [ya, ya], color='0.4', lw=0.4)
    ax.plot([x, x + off * 1.1], [yb, yb], color='0.4', lw=0.4)
    ax.text(x + off + (1.0 if off > 0 else -1.0), (ya + yb) / 2, text, va='center', rotation=90, fontsize=8,
            ha='left' if off > 0 else 'right')


dim_h(0, W, 0, '%.2f' % W, -6)
dim_v(0, H, 0, '%.2f' % H, -6)
if which == 'power':
    # notch at the top-right corner: find the outline's inner corner
    xs = sorted(set(round(to_draw_k(x, y)[0], 3) for x, y in F['outline_vertices'][0]))
    ys = sorted(set(round(to_draw_k(x, y)[1], 3) for x, y in F['outline_vertices'][0]))
    xn = [v for v in xs if 0.5 < v < W - 0.5]
    yn = [v for v in ys if 0.5 < v < H - 0.5]
    if xn and yn:
        dim_h(xn[0], W, H, '%.2f' % (W - xn[0]), 6)
        dim_v(yn[-1], H, W, '%.2f' % (H - yn[-1]), 6)
        dim_h(0, xn[0], H, '%.2f' % xn[0], 6)
ax.text(0, -12.5, 'Datum: lower-left corner of the outline (0, 0). Dimensions in mm, outline tolerance +/-0.2 mm.\n'
        'Drawn from the Excellon files: every drilled hole is shown with its symbol; holes >= 2 mm also to scale.',
        fontsize=8, va='top')
# NPTH coordinates next to them
for d, x, y in npth:
    X, Y = to_draw_d(x, y)
    ax.text(X + d / 2 + 0.6, Y + 0.6, '%.2f, %.2f' % (X, Y), fontsize=6, color=col['NPTH'])
for d, xa, ya, xb, yb in nslots:
    A, B = to_draw_d(xa, ya), to_draw_d(xb, yb)
    ax.text(max(A[0], B[0]) + d, A[1] - 0.3, 'slot %.2f x %.2f @ %.2f, %.2f' % (abs(B[0] - A[0]) + d, d,
                                                                            (A[0] + B[0]) / 2, A[1]),
            fontsize=6, color=col['NPTH slot'])
ax.set_xlim(-16, W + 14)
ax.set_ylim(-16, H + 12)

# ---- right side: title, notes, tables ----
tx = fig.add_axes([0.55, 0.03, 0.43, 0.94])
tx.axis('off')
tx.set_xlim(0, 1)
tx.set_ylim(0, 1)
tx.text(0, 0.995, '%s  -  FABRICATION DRAWING' % TITLE.upper(), fontsize=15, weight='bold', va='top')
NL = F['copper_layers']
HALF = NL == 6 and F['board_thickness_in_file_mm'] < 1.58   # card with 0.5 oz inner copper, from 2026-10-01
DATE = '2026-10-01' if HALF else '2026-09-30'
tx.text(0, 0.965, '%s, %s. Files: %s_gerbers.zip. Units: mm.' % (NAME, DATE, NAME),
        fontsize=9, va='top')
vib = F['via_in_pad_count']
nvia = F['via_count']
vd = ', '.join(sorted(set(k.split('/')[0] for k in F['vias_by_drill_dia'])))
card = which == 'card'
NL = F['copper_layers']          # 8, or 6 for the card from 2026-09-30
notes = [
    ('ALL VIAS EPOXY FILLED AND COPPER CAPPED (resin plugged, plated over; IPC-4761 Type VII). %d of the %d vias sit '
     'in SMD pads. Via drills %s mm (JLCPCB filled-via range 0.2-0.5 mm). Order option "Via Covering: Epoxy Filled '
     '& Capped".' % (vib, nvia, vd), True),
    ('Material FR-4, Tg 155 C or better (JLCPCB "FR4 TG155"%s). %d copper layers. Finished thickness '
     '1.6 mm +/-10 %%.' % (', Nan Ya NP-155F' if NL == 8 else '', NL), False),
    (('Copper: outer layers 1 oz (35 um) finished; the four inner layers 0.5 oz (order option "Inner copper '
      'weight 0.5 oz", the fab default for 6 layers).') if HALF else
     ('Copper 1 oz (35 um) finished on all %s layers: outer 1 oz, inner 1 oz (order option "Inner copper weight '
      '1 oz"; the fab default of 0.5 oz inner is NOT acceptable).' % {6: 'six', 8: 'eight'}[NL]), False),
    (('Stackup: the fab\'s standard %d-layer 1.6 mm build for 1 oz outer / 0.5 oz inner copper (no stackup '
      'specified), as in the table. No impedance control.' % NL) if HALF else
     ('Stackup: the fab\'s standard %d-layer 1.6 mm build (no stackup specified), as in the table. No impedance '
      'control.' % NL), False),
    ('Surface finish ENIG. Solder mask green LPI both sides. Silkscreen white both sides.', False),
    ('Minimum track / space: %.2f / 0.20 mm on every layer. Minimum drill %.2f mm (vias); smallest plated pad hole '
     '%.2f mm.' % (min(F['min_track_outer_mm'], F['min_track_inner_mm']), F['min_drill_mm'],
                  min(float(k) for k in F['pth_by_drill'])), False),
    ('Minimum via annular ring %.2f mm; minimum plated pad annular ring %.2f mm. Via-to-via hole gap >= %.2f mm; '
     'filled via to any pad hole >= %.2f mm.' % (F['via_min_annular_mm'], F['pth_min_annular_mm'],
                                                  F['min_via_to_via_hole_gap_mm'],
                                                  F['min_via_to_pad_hole_gap_mm']), False),
    ('Plated hole tolerance +0.13 / -0.08 mm. %s 2x15 header holes are drilled 1.05 mm for Samtec 0.64 mm square '
     'posts.' % ('J11' if card else 'J10'), False),
    (('Non-plated holes: 4 x 3.20 mm (standoffs) and 2 slots 2.80 x 1.40 mm (J9 cable tie), routed; the slots are '
      'G85 routes in the NPTH drill file.') if card else
     'Non-plated holes: 4 x 3.20 mm (standoffs), 4 x 2.90 mm (FET tab screws).', False),
    ('Outline on the Edge.Cuts (GM1) layer, tolerance +/-0.2 mm.%s' % (
        '' if card else ' Notched top-right corner.'), False),
    ('Electrical test: 100 %% flying probe; IPC-D-356 netlist %s.ipc356 supplied.' % NAME, False),
    ('No order number or other marking to be added ("Remove Mark").', False),
]
if card:
    notes.append(('Assembly panel: standard PCBA needs at least 70 x 70 mm; order "Panel by JLCPCB" (edge rails) for '
                  'this 45 x 45 mm card.', False))
y = 0.935
tx.text(0, y, 'FABRICATION NOTES', fontsize=11, weight='bold', va='top')
y -= 0.025
import textwrap
for i, (t, bold) in enumerate(notes, 1):
    lines = textwrap.wrap(t, 105)
    tx.text(0, y, '%d.' % i, fontsize=8.2, va='top', weight='bold' if bold else 'normal',
            color='#b3261e' if bold else 'black')
    tx.text(0.03, y, '\n'.join(lines), fontsize=8.2, va='top', weight='bold' if bold else 'normal',
            color='#b3261e' if bold else 'black')
    y -= 0.0145 * len(lines) + 0.006
# stackup table
y -= 0.01
tx.text(0, y, 'STACKUP (from the board file; copper + dielectric %.3f mm, + mask)' % F['board_thickness_in_file_mm'],
        fontsize=10, weight='bold', va='top')
y -= 0.022
ST = [('F.Mask', 'solder mask', '', '0.010'), ('F.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
      ('', 'prepreg 2116 NP-155F, er 4.16', '', '0.109'), ('In1.Cu', 'copper, 1 oz', 'GND plane', '0.030'),
      ('', 'core NP-155F, er 4.23', '', '0.250'), ('In2.Cu', 'copper, 1 oz', 'signal', '0.030'),
      ('', 'prepreg 2 x 2116', '', '0.218'), ('In3.Cu', 'copper, 1 oz', 'signal%s' % (' / 5V pour' if card else ''),
                                              '0.030'),
      ('', 'core NP-155F', '', '0.250'), ('In4.Cu', 'copper, 1 oz', 'signal / GND fill' if card else '5 V plane',
                                          '0.030'),
      ('', 'prepreg 2 x 2116', '', '0.218'), ('In5.Cu', 'copper, 1 oz', 'signal', '0.030'),
      ('', 'core NP-155F', '', '0.250'), ('In6.Cu', 'copper, 1 oz', 'GND plane', '0.030'),
      ('', 'prepreg 2116', '', '0.109'), ('B.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
      ('B.Mask', 'solder mask', '', '0.010')]
if NL == 6:      # JLCPCB JLC061611-7628, the 6-layer 1.6 mm 1/1 oz "no requirement" build (jlcpcb.com/impedance)
    ST = [('F.Mask', 'solder mask', '', '0.010'), ('F.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
          ('', 'prepreg 7628, er 4.4', '', '0.203'), ('In1.Cu', 'copper, 1 oz', 'signal / GND fill', '0.030'),
          ('', 'core, er 4.6', '', '0.250'), ('In2.Cu', 'copper, 1 oz', 'signal / 5V pour', '0.030'),
          ('', 'prepreg 7628 + 3313 + 7628', '', '0.513'), ('In3.Cu', 'copper, 1 oz', 'signal / GND fill', '0.030'),
          ('', 'core, er 4.6', '', '0.250'), ('In4.Cu', 'copper, 1 oz', 'signal / GND fill', '0.030'),
          ('', 'prepreg 7628', '', '0.203'), ('B.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
          ('B.Mask', 'solder mask', '', '0.010')]
if HALF:         # JLCPCB 6-layer 1.6 mm, 1 oz outer / 0.5 oz inner "no requirement" build (jlcpcb.com/impedance, 2026-10-01)
    ST = [('F.Mask', 'solder mask', '', '0.010'), ('F.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
          ('', 'prepreg 3313, er 4.1', '', '0.0994'), ('In1.Cu', 'copper, 0.5 oz', 'signal / GND fill', '0.0152'),
          ('', 'core, er 4.6', '', '0.550'), ('In2.Cu', 'copper, 0.5 oz', 'signal / 5V pour', '0.0152'),
          ('', 'prepreg 2116, er 4.16', '', '0.1164'), ('In3.Cu', 'copper, 0.5 oz', 'signal / GND fill', '0.0152'),
          ('', 'core, er 4.6', '', '0.550'), ('In4.Cu', 'copper, 0.5 oz', 'signal / GND fill', '0.0152'),
          ('', 'prepreg 3313, er 4.1', '', '0.0994'), ('B.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
          ('B.Mask', 'solder mask', '', '0.010')]
for a, b, c, d in ST:
    is_cu = a.endswith('Cu')
    if is_cu:
        tx.add_patch(Rectangle((0, y - 0.0125), 0.62, 0.0145, color='#f3d9a4', lw=0))
    tx.text(0.005, y, a, fontsize=7.8, va='top', weight='bold' if is_cu else 'normal')
    tx.text(0.10, y, b, fontsize=7.8, va='top')
    tx.text(0.38, y, c, fontsize=7.8, va='top')
    tx.text(0.57, y, d, fontsize=7.8, va='top', ha='left')
    y -= 0.0148
# drill table
y -= 0.012
tx.text(0, y, 'DRILL TABLE', fontsize=10, weight='bold', va='top')
y -= 0.022
tx.text(0.005, y, 'sym', fontsize=7.8, va='top', weight='bold')
tx.text(0.06, y, 'drill mm', fontsize=7.8, va='top', weight='bold')
tx.text(0.17, y, 'type', fontsize=7.8, va='top', weight='bold')
tx.text(0.30, y, 'count', fontsize=7.8, va='top', weight='bold')
tx.text(0.38, y, 'used for', fontsize=7.8, va='top', weight='bold')
y -= 0.016
USE = {('PTH', 0.3): 'vias (filled, capped)', ('PTH', 0.4): 'vias (filled, capped)', ('PTH', 0.5): 'vias (filled, capped)',
       ('PTH', 1.0): 'J9 wire pads' if card else '', ('PTH', 1.05): '2x15 header (J11)' if card else '2x15 socket (J10)',
       ('PTH', 1.1): 'TO-220 pins M1-M10', ('PTH', 2.0): 'LED wire pads J3-J8', ('PTH', 4.3): 'battery lugs J1/J2',
       ('NPTH', 2.9): 'FET tab screws', ('NPTH', 3.2): 'standoffs', ('NPTH slot', 1.4): 'J9 tie slots 2.8 x 1.4'}
for k in sizes:
    tx.add_line(Line2D([0.02], [y - 0.006], marker=sym[k], ms=5, mfc='none', mec=col[k[0]], mew=0.8,
                       transform=tx.transData))
    tx.text(0.06, y, '%.2f' % k[1], fontsize=7.8, va='top')
    tx.text(0.17, y, k[0], fontsize=7.8, va='top')
    tx.text(0.30, y, '%d' % count[k], fontsize=7.8, va='top')
    tx.text(0.38, y, USE.get((k[0], round(k[1], 2)), ''), fontsize=7.8, va='top')
    y -= 0.0145
tx.text(0, 0.0, 'Generated by fab_2026-09-30/tools/fab_drawing.py from BOOST_schematic_cleanup/KiCad/%s.kicad_pcb'
        % NAME, fontsize=6.5, va='bottom', color='0.35')
out = '%s/%s_fab_drawing.pdf' % (NAME, NAME)
fig.savefig(out)
fig.savefig(out.replace('.pdf', '.png'), dpi=110)
print('wrote', out)
