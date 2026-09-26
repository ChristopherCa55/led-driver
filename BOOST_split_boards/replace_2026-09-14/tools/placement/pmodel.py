"""Fast placement model for the power board (plain Python + matplotlib).

A layout is a dict ref -> (x, y, rot_deg, side) in board mm. Geometry comes from
inv_power.json (fpinventory.py). Transform (to verify against pcbnew before use):
  F: world = P + R(rot) (x, y);  B: world = P + R(rot) (x, -y)
  R(a)(x, y) = (x cos a + y sin a, -x sin a + y cos a)   (KiCad, y down)
"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
# inv_power2.json: netlist after J10 -> ESQ socket, R13/R23/R47 220 (all runs up to p12).
# inv_power3.json: + C30 tantalum, C7/C55 1210, C41/C44/C45, NoHole FETs (2026-09-15). Select with PMODEL_INV.
INV = json.load(open(os.path.join(HERE, os.environ.get('PMODEL_INV', 'inv_power2.json'))))

BOARD = [(30, 30), (86, 30), (86, 42), (104, 42), (104, 116), (30, 116)]   # notch top-right
PENETRATOR = (96.5, 31.5, 7.5)
HEIGHT = {'L1': 19.0, 'U16': 4.83, 'J1': 4.0, 'J2': 4.0}
for r in ('C70', 'C86', 'C88', 'C71', 'C78', 'C87', 'C74', 'C75', 'C77'):
    HEIGHT[r] = 16.8
for r in ('C40', 'C69', 'C85'):
    HEIGHT[r] = 12.8
if 'Tantalum' in INV.get('C30', {}).get('fp', ''):
    HEIGHT['C30'] = 3.1       # Vishay TR3 case D: 2.8 +/- 0.3 mm (datasheet 40080)
    HEIGHT['C7'] = HEIGHT['C55'] = 2.7   # GRM32ER 1210: T code E, 2.5 +/- 0.2 mm (Murata code; not re-read this session)
else:
    for r in ('C7', 'C30', 'C55'):
        HEIGHT[r] = 5.7       # 6.3 x 5.4 electrolytic cans (inv_power2)
FETS = ['M%d' % i for i in range(1, 11)]
CAN_VENT_CLEAR = 2.0
CARD_GAP = 21.21          # ESQ-115-44 + TSW-115-07 (user decision 2026-09-15); L1 never under the card


def tf(pl, x, y):
    X, Y, a, side = pl
    if side == 'B':          # pcbnew: Flip(LEFT_RIGHT) then SetOrientationDegrees(a) (verified tftest.py)
        y = -y
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return X + x * c + y * s, Y - x * s + y * c


def rect(pl, l, t, r, b):
    pts = [tf(pl, x, y) for x in (l, r) for y in (t, b)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def pads(L, ref):
    """[(num, x, y, w, h, net)] in board mm (w, h as bbox after rotation)."""
    out = []
    for p in INV[ref]['pads']:
        x, y = tf(L[ref], p['x'], p['y'])
        a = L[ref][2] % 180
        w, h = (p['h'], p['w']) if a == 90 else (p['w'], p['h'])
        out.append((p['num'], x, y, w, h, p['net'], p['drill']))
    return out


def pad(L, ref, num):
    ps = [p for p in pads(L, ref) if p[0] == num]
    return max(ps, key=lambda p: p[3] * p[4])


def is_tht(ref):
    return INV[ref]['tht']


def areas(L, ref):
    """List of (side, rect, kind): kind 'body' or 'pins' (THT: pins on both sides)."""
    pl = L[ref]
    if ref in FETS:
        body = rect(pl, -2.71, 1.25, 7.79, 19.71)      # courtyard includes the lead bends between pins and body
        pins = rect(pl, -1.21, -1.25, 6.29, 1.25)      # KiCad pin-region courtyard (TO-220-3_Horizontal_TabUp)
        return [(pl[3], body, 'body'), ('F', pins, 'pins'), ('B', pins, 'pins')]
    if ref == 'L1':
        return [('F', rect(pl, -16.25, -14.25, 16.25, 11.5), 'body'), ('F', rect(pl, -10.25, 11.5, 10.25, 20.5), 'pads')]
    c = INV[ref]['courtyard']
    if c is None:
        return []
    r = rect(pl, *c)
    if ref in ('H5', 'H6', 'H7', 'H8'):          # standoff holes: spacer below, standoff above
        return [('F', r, 'body'), ('B', r, 'pins')]
    if is_tht(ref):
        return [('F', r, 'body'), ('B', r, 'pins')] if pl[3] == 'F' else [('B', r, 'body'), ('F', r, 'pins')]
    return [(pl[3], r, 'body')]


def tab_hole(L, ref):
    return tf(L[ref], 2.54, 16.66)


def body_centre(L, ref):
    return tf(L[ref], 2.54, 11.64)


def overlap(a, b, gap=0.0):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def rect_circle_dist(r, cx, cy):
    dx = max(r[0] - cx, 0, cx - r[2])
    dy = max(r[1] - cy, 0, cy - r[3])
    return math.hypot(dx, dy)


EDGE = 0.25      # courtyard inside the edge by 0.25 mm keeps pads >= 0.5 mm (min_copper_edge_clearance)


def in_board(r):
    if r[0] < 30 + EDGE or r[2] > 104 - EDGE or r[1] < 30 + EDGE or r[3] > 116 - EDGE:
        return False
    return not overlap(r, (86 - EDGE, 30, 104, 42 + EDGE))


def d(L, a, pa, b, pb):
    if a not in L or b not in L:
        return float('nan')
    A, B = pad(L, a, pa), pad(L, b, pb)
    return math.hypot(A[1] - B[1], A[2] - B[2])
