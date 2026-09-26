"""Where can J9 (right-angle connector, card underside, pins out over a card edge) go? (system Python)

usage: python j9_fit.py POWER_FP.json ANCHOR.json OUT.json [OUT.png]

For each candidate connector and each card edge, the connector is slid along the edge in 0.1 mm steps. At each
position its plan-view keep-out is a rectangle:
- along the edge: the footprint's courtyard length (KiCad library, the board-side header), or the plug's length if
  that is given and longer;
- across the edge: from INBOARD mm inside the card (the header body and pin rows) to EXT mm outside it (the mated
  plug, measured from the card edge);
- vertically: from the card underside down HANG mm (header plus mated plug).
A position is legal when that box
- stays inside the case (inside walls, power-board coordinates below),
- does not cover a mounting-hole keep-out on the card (H1-H4, r 3.5) or J11's courtyard,
- is not over anything on the power board that reaches into it: a part whose top is above the box bottom is a
  collision; a 220 uF can also needs VENT mm clear above its top (Panasonic, 2 mm above the pressure valve), so a
  can counts when box bottom - can top < VENT. Cans are their top circle (diameter 10.0 mm, ZU series).
Heights: card underside 28.60 (round-4 stack), power-board top 7.10, part tops from pmodel's height table.
"""
import json, math, os, sys

POWER_FP, ANCHOR, OUT = sys.argv[1:4]
PNG = sys.argv[4] if len(sys.argv) > 4 else None
CARD_UNDER = 28.60
if '--card-under' in sys.argv:          # what-if: another stack height
    CARD_UNDER = float(sys.argv[sys.argv.index('--card-under') + 1])
    sys.argv = [x for i, x in enumerate(sys.argv) if x != '--card-under' and sys.argv[i - 1] != '--card-under']
    PNG = sys.argv[4] if len(sys.argv) > 4 else None
HANG_OVERRIDE = None
if '--hang' in sys.argv:                # what-if: header + mated plug hang below the card, all candidates
    HANG_OVERRIDE = float(sys.argv[sys.argv.index('--hang') + 1])
    sys.argv = [x for i, x in enumerate(sys.argv) if x != '--hang' and sys.argv[i - 1] != '--hang']
    PNG = sys.argv[4] if len(sys.argv) > 4 else None
BOARD_TOP = 7.10
VENT = 2.0
CAN_D = 10.0
HOLE_KO = 3.5
# case inside, power-board coordinates (box = pcb + (22, -28), box inside 128 x 90)
CASE = (-22.0, 28.0, 106.0, 118.0)

# candidates: courtyard along the edge (mm, KiCad library), inboard depth (card edge to the back of the courtyard),
# plug extension past the edge and hang below the card. The 2.54 mm single-row figures are the user's; the others
# are marked in 'source' and must be confirmed on the manufacturer's drawings.
CANDS = [
    dict(name='1x11 2.54 mm RA header (rev3 J9)', along=28.94, inboard=5.81, ext=15.0, hang=2.75,
         source='courtyard: PinHeader_1x11_P2.54mm_Horizontal; plug 15 / 2.75 mm: user'),
    dict(name='JST PH 1x11 2.0 mm, locking (S11B-PH-K)', along=24.90, inboard=6.75, ext=15.0, hang=None,
         source='courtyard: JST_PH_S11B-PH-K; hang and plug not verified'),
    dict(name='JST GH 1x11 1.25 mm, locking, SMD (SM11B-GHS-TB)', along=18.20, inboard=6.40, ext=15.0, hang=None,
         source='courtyard: JST_GH_SM11B-GHS-TB; hang and plug not verified'),
    dict(name='2x6 2.54 mm RA header', along=16.24, inboard=8.35, ext=15.0, hang=5.35,
         source='courtyard: PinHeader_2x06_P2.54mm_Horizontal; hang = two 2.54 rows + 0.27 plug wall, not verified'),
    dict(name='JST PHD 2x6 2.0 mm, locking (S12B-PHDSS)', along=14.90, inboard=10.60, ext=15.0, hang=None,
         source='courtyard: JST_PHD_S12B-PHDSS; hang and plug not verified'),
]

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'replace_2026-09-14', 'tools',
                                'placement'))
os.environ.setdefault('PMODEL_INV', 'inv_power5.json')
here = os.getcwd()
os.chdir(sys.path[0])
import pmodel as M
os.chdir(here)

fp = {f['ref']: f for f in json.load(open(POWER_FP))}
anchor = json.load(open(ANCHOR))
x0, y0, s = anchor['card']['x0'], anchor['card']['y0'], anchor['card']['size']
X1, Y1 = x0 + s, y0 + s

# power-board obstacles: (kind, geometry, top)
obst = []
for ref, h in M.HEIGHT.items():
    if ref not in fp or fp[ref]['side'] != 'F' or h < 5:
        continue
    f = fp[ref]
    top = BOARD_TOP + h
    if str(f.get('value', '')).startswith('220'):
        obst.append(('can', ref, (f['x'], f['y'], CAN_D / 2), top))
    else:
        pts = [q for poly in (f['courtyard'] or []) for q in poly]
        obst.append(('box', ref, (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts),
                                  max(p[1] for p in pts)), top))
holes = [tuple(v) for v in anchor['standoffs'].values()]
jp = list(anchor['J10']['pads'].values())
j11 = (min(p[0] for p in jp) - 1.33, min(p[1] for p in jp) - 1.33, max(p[0] for p in jp) + 1.33,
       max(p[1] for p in jp) + 1.33)       # 2x15 header courtyard (pads +/- 1.33 mm)


def rect_circle(r, cx, cy):
    dx = max(r[0] - cx, 0, cx - r[2])
    dy = max(r[1] - cy, 0, cy - r[3])
    return math.hypot(dx, dy)


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def box_at(edge, t, c):
    """Keep-out rectangle for a connector whose along-edge span starts at t."""
    a, i, e = c['along'], c['inboard'], c['ext']
    if edge == 'west':
        return (x0 - e, t, x0 + i, t + a)
    if edge == 'east':
        return (X1 - i, t, X1 + e, t + a)
    if edge == 'north':
        return (t, y0 - e, t + a, y0 + i)
    return (t, Y1 - i, t + a, Y1 + e)


def blockers(box, hang):
    bottom = CARD_UNDER - hang
    out = []
    if not (box[0] >= CASE[0] and box[1] >= CASE[1] and box[2] <= CASE[2] and box[3] <= CASE[3]):
        out.append('case wall')
    for hx, hy in holes:
        if rect_circle(box, hx, hy) < HOLE_KO:
            out.append('mounting-hole keep-out')
    if overlap(box, j11):
        out.append('J11')
    for kind, ref, g, top in obst:
        if kind == 'can':
            hit = rect_circle(box, g[0], g[1]) < g[2] and bottom - top < VENT
        else:
            hit = overlap(box, g) and bottom < top
        if hit:
            out.append(ref)
    return out


res = []
for c in CANDS:
    hang = HANG_OVERRIDE if HANG_OVERRIDE is not None else (c['hang'] if c['hang'] is not None else 2.75)
    row = dict(c, hang_used=hang, edges={})
    for edge, (lo, hi) in (('west', (y0, Y1)), ('east', (y0, Y1)), ('north', (x0, X1)), ('south', (x0, X1))):
        spans, cur, why = [], None, {}
        t = lo
        while t + c['along'] <= hi + 1e-9:
            b = blockers(box_at(edge, t, c), hang)
            if not b:
                cur = [t, t] if cur is None else [cur[0], t]
            else:
                for x in b:
                    why[x] = why.get(x, 0) + 1
                if cur:
                    spans.append(cur)
                    cur = None
            t = round(t + 0.1, 6)
        if cur:
            spans.append(cur)
        row['edges'][edge] = dict(legal_starts=[[round(a, 1), round(b, 1)] for a, b in spans],
                                  blocked_by=sorted(why, key=lambda k: -why[k]))
    res.append(row)
    print(c['name'])
    for edge, v in row['edges'].items():
        print('   %-5s %s   blocked by: %s' % (edge, ('LEGAL, start %s' % v['legal_starts']) if v['legal_starts']
                                              else 'no legal position', ', '.join(v['blocked_by'][:6]) or '-'))
json.dump(dict(card=[x0, y0, X1, Y1], card_under=CARD_UNDER, vent=VENT, candidates=res,
               obstacles=[dict(kind=k, ref=r, geom=g, top=t) for k, r, g, t in obst]), open(OUT, 'w'), indent=1)

if PNG:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, ax = plt.subplots(figsize=(10, 8.5))
    ax.add_patch(Rectangle((30, 30), 74, 86, fill=False, lw=1, ls=':', color='0.5'))
    ax.add_patch(Rectangle((CASE[0], CASE[1]), CASE[2] - CASE[0], CASE[3] - CASE[1], fill=False, lw=1.5, color='k'))
    ax.add_patch(Rectangle((x0, y0), s, s, fill=True, alpha=0.08, color='g', lw=1.5))
    for kind, ref, g, top in obst:
        if kind == 'can':
            ax.add_patch(Circle((g[0], g[1]), g[2], color='tab:red', alpha=0.35))
            ax.text(g[0], g[1], '%s\n%.2f' % (ref, top), ha='center', va='center', fontsize=7)
        else:
            ax.add_patch(Rectangle((g[0], g[1]), g[2] - g[0], g[3] - g[1], color='tab:orange', alpha=0.3))
            ax.text((g[0] + g[2]) / 2, (g[1] + g[3]) / 2, '%s\n%.2f' % (ref, top), ha='center', fontsize=7)
    for hx, hy in holes:
        ax.add_patch(Circle((hx, hy), HOLE_KO, fill=False, color='b'))
    ax.add_patch(Rectangle((j11[0], j11[1]), j11[2] - j11[0], j11[3] - j11[1], color='tab:blue', alpha=0.3))
    ax.text((j11[0] + j11[2]) / 2, (j11[1] + j11[3]) / 2, 'J11', ha='center', fontsize=8)
    colors = ['k', 'tab:purple', 'tab:green', 'tab:brown', 'tab:cyan']
    for c, col in zip(res, colors):
        for edge, v in c['edges'].items():
            for a, b in v['legal_starts']:
                bx = box_at(edge, a, c)
                ax.add_patch(Rectangle((bx[0], bx[1]), bx[2] - bx[0], bx[3] - bx[1], fill=False, ls='--', color=col,
                                       lw=1.2))
    ax.set_xlim(CASE[0] + 20, CASE[2] + 2)
    ax.set_ylim(CASE[3] + 2, 26)
    ax.set_aspect('equal')
    ax.set_title('J9 fit: cans (top height), L1, keep-outs; dashed = legal positions of the options that fit')
    ax.grid(True, lw=0.3)
    fig.savefig(PNG, dpi=110, bbox_inches='tight')
    print('wrote', PNG)
