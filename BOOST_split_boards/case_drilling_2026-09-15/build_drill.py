"""Dimensioned drilling drawing for the case floor, from the placed board's own hole coordinates."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\replace_2026-09-14\tools\placement\case_floor_holes.json'
holes = json.load(open(SRC))

BOX_W, BOX_H = 128.0, 90.0
S = 6.0                      # px per mm
ML, MT, MR, MB = 150, 104, 56, 320   # margins: ordinate labels, title block, 90.00 dimension, table and notes
W, H = int(BOX_W * S) + ML + MR, int(BOX_H * S) + MT + MB


def X(mm):
    return ML + mm * S


def Y(mm):
    return MT + mm * S


p = []
a = p.append
a('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="IBM Plex Mono, Consolas, monospace">' % (W, H, W, H))
a('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))
a('<g stroke="#1a2320" fill="none" stroke-width="1.6">')
a('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (X(0), Y(0), BOX_W * S, BOX_H * S))   # case interior
a('</g>')

# board outline (reference only), with the notched top-right corner
bx0, by0, bx1, by1 = 52.0, 2.0, 126.0, 88.0
nx0, ny1 = 108.0, 14.0
pts = [(bx0, by0), (nx0, by0), (nx0, ny1), (bx1, ny1), (bx1, by1), (bx0, by1)]
a('<polygon points="%s" fill="#f3f5f1" stroke="#9aa5a0" stroke-width="1" stroke-dasharray="6 4"/>'
  % ' '.join('%.1f,%.1f' % (X(x), Y(y)) for x, y in pts))
a('<text x="%.1f" y="%.1f" font-size="11" fill="#75807a">power board outline (reference)</text>' % (X(54), Y(86)))

# penetrators, given by the case design
for px, py in ((9.5, 3.5), (118.5, 3.5)):
    a('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#9aa5a0" stroke-width="1" stroke-dasharray="4 3"/>'
      % (X(px), Y(py), 7.5 * S))
    a('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#1a2320" stroke-width="1.2"/>' % (X(px), Y(py), 5 * S))
    a('<text x="%.1f" y="%.1f" font-size="10" fill="#75807a" text-anchor="middle">penetrator &#216;10</text>'
      % (X(px), Y(py) + 7.5 * S + 12))

ACC = {'M2.5 tab screw': '#a95f24', 'M3 standoff': '#1f4a38'}
for h in holes:
    cx, cy = X(h['box_x']), Y(h['box_y'])
    col = ACC[h['kind']]
    r = 3.6 * S / 2 if h['kind'].startswith('M3') else 2.9 * S / 2
    a('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="1.8"/>' % (cx, cy, r, col))
    a('<path d="M%.1f %.1f H%.1f M%.1f %.1f V%.1f" stroke="%s" stroke-width="0.8"/>'
      % (cx - r - 6, cy, cx + r + 6, cx, cy - r - 6, cy + r + 6, col))
    a('<text x="%.1f" y="%.1f" font-size="11" font-weight="600" fill="%s">%s</text>' % (cx + r + 8, cy - 4, col, h['ref']))

# ordinate dimensions from the top-left datum
a('<g stroke="#4a5550" stroke-width="0.7" fill="#1a2320" font-size="10">')
a('<circle cx="%.1f" cy="%.1f" r="3" fill="none"/>' % (X(0), Y(0)))
a('<text x="%.1f" y="%.1f" font-size="10" fill="#4a5550" text-anchor="end">0,0 datum</text>' % (X(0) - 8, Y(0) - 8))


def levels(vals, spacing):
    # lowest label row whose previous label is at least `spacing` px away
    last, out = [], []
    for v in vals:
        k = next((k for k, x in enumerate(last) if v - x >= spacing), len(last))
        if k == len(last):
            last.append(v)
        last[k] = v
        out.append(k)
    return out


xs = sorted(holes, key=lambda h: h['box_x'])
for h, k in zip(xs, levels([X(h['box_x']) for h in xs], 40)):
    cx = X(h['box_x'])
    top = MT - 14 - k * 12
    a('<path d="M%.1f %.1f V%.1f" stroke-dasharray="3 3"/>' % (cx, top, Y(h['box_y'])))
    a('<text x="%.1f" y="%.1f" text-anchor="middle">%.2f</text>' % (cx, top - 3, h['box_x']))
ys = sorted(holes, key=lambda h: h['box_y'])
for h, k in zip(ys, levels([Y(h['box_y']) for h in ys], 13)):
    cy = Y(h['box_y'])
    left = ML - 12 - k * 44
    a('<path d="M%.1f %.1f H%.1f" stroke-dasharray="3 3"/>' % (left, cy, X(h['box_x'])))
    a('<text x="%.1f" y="%.1f" text-anchor="end">%.2f</text>' % (left - 2, cy + 3, h['box_y']))
a('</g>')

# overall dimensions
a('<g stroke="#1a2320" stroke-width="1" fill="#1a2320" font-size="11">')
yb = Y(BOX_H) + 22
a('<path d="M%.1f %.1f H%.1f M%.1f %.1f v-6 m0 12 v-6 M%.1f %.1f v-6 m0 12 v-6"/>' % (X(0), yb, X(BOX_W), X(0), yb, X(BOX_W), yb))
a('<text x="%.1f" y="%.1f" text-anchor="middle">128.00 case interior</text>' % ((X(0) + X(BOX_W)) / 2, yb - 6))
xr = X(BOX_W) + 18
a('<path d="M%.1f %.1f V%.1f M%.1f %.1f h-6 m12 0 h-6 M%.1f %.1f h-6 m12 0 h-6"/>' % (xr, Y(0), Y(BOX_H), xr, Y(0), xr, Y(BOX_H)))
a('<text x="%.1f" y="%.1f" text-anchor="middle" transform="rotate(90 %.1f %.1f)">90.00</text>' % (xr + 12, (Y(0) + Y(BOX_H)) / 2, xr + 12, (Y(0) + Y(BOX_H)) / 2))
a('</g>')

# hole table
ty = Y(BOX_H) + 40
a('<g font-size="11" fill="#1a2320">')
a('<text x="%.1f" y="%.1f" font-weight="700">HOLE TABLE &#8212; case floor, tapped from inside</text>' % (X(0), ty))
cols = [0, 58, 170, 250, 330, 440]
hdr = ['REF', 'TYPE', 'X', 'Y', 'TAP', 'FULL THREAD']
for c, t in zip(cols, hdr):
    a('<text x="%.1f" y="%.1f" font-weight="600" fill="#4a5550">%s</text>' % (X(0) + c, ty + 16, t))
for i, h in enumerate(holes):
    yy = ty + 32 + i * 13
    tap = 'M3 x 0.5' if h['kind'].startswith('M3') else 'M2.5 x 0.45'
    depth = '7.0 min' if h['kind'].startswith('M3') else '6.0 min'
    vals = [h['ref'], h['kind'], '%.2f' % h['box_x'], '%.2f' % h['box_y'], tap, depth]
    for c, t in zip(cols, vals):
        a('<text x="%.1f" y="%.1f" fill="%s">%s</text>' % (X(0) + c, yy, ACC[h['kind']] if c == 0 else '#1a2320', t))
a('</g>')

notes = [
    'NOTES',
    '1. Datum: inside top-left corner of the case floor, as in the case layout (box = board + 22, -28). All dimensions in mm.',
    '2. The floor is 10 mm thick and the case is sealed: blind holes only, drill depth 8.5 mm maximum, bottoming tap.',
    '3. M3: 7.0 mm of full thread minimum, for the 6 mm nylon stud of the H5-H8 standoffs (the stud must not bottom).',
    '4. M2.5: 6.0 mm of full thread minimum, for the FET tab screws (M2.5 x 12 pan head, 4.9 mm engaged).',
    '5. Light 90&#176; countersink to thread diameter so the standoff hex and the thermal pads seat flat. Deburr.',
    '6. Nylon threads in aluminium: assemble hand-tight only.',
    '7. Rev B changes notes and layout only: all eight positions are unchanged from rev A (placement p15_b10_k2).',
]
a('<g font-size="10.5" fill="#4a5550">')
for i, n in enumerate(notes):
    a('<text x="%.1f" y="%.1f"%s>%s</text>' % (X(0), ty + 150 + i * 14, ' font-weight="700" fill="#1a2320"' if i == 0 else '', n))
a('</g>')

a('<g font-size="11" fill="#1a2320">')
a('<text x="%.1f" y="%.1f" font-weight="700">BOOST power board &#8212; case floor drilling</text>' % (X(0), 26))
a('<text x="%.1f" y="%.1f" fill="#4a5550" font-size="10.5">rev B 2026-09-16 &#183; placement p15_b10_k2 &#183; 8 holes &#183; not to scale: work from the hole table</text>' % (X(0), 44))
a('</g>')
a('</svg>')

svg = '\n'.join(p)
open(os.path.join(HERE, 'case_floor_drilling.svg'), 'w', encoding='utf8').write(svg)
html = ('<title>Case Floor Drilling</title>\n'
        '<style>:root{color-scheme:light}body{background:#e8ece6;margin:0;padding:24px;font-family:"IBM Plex Sans",system-ui,sans-serif}'
        '.wrap{max-width:1100px;margin:0 auto;display:grid;gap:14px}'
        'svg{width:100%;height:auto;background:#fff;border:1px solid #c9d1cb;border-radius:4px}'
        'p{margin:0;color:#4a5550;font-size:14px;max-width:70ch}</style>\n'
        '<div class="wrap">\n' + svg + '\n<p>Drawn from the placed board: hole centres are the NPTH tab holes of M1, M8, M9, M10 '
        'and the H5&#8211;H8 standoff holes, converted to case coordinates. Not to scale: work from the hole table.</p>\n</div>\n')
open(os.path.join(HERE, 'case_floor_drilling.html'), 'w', encoding='utf8').write(html)
print('wrote case_floor_drilling.svg and .html (%d holes)' % len(holes))
