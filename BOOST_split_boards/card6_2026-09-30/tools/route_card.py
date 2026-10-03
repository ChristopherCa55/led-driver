"""Grid router for the BOOST control card (system Python: numpy, scipy, matplotlib, PIL).

usage: python route_card.py COPPER.json OUT_ROUTES.json [--nets a,b,...] [--skip a,b] [--no-rip]
                            [--routes EARLIER_ROUTES.json] [--zones ROUTED_BOARD_COPPER.json]
With --routes the earlier routes are committed first (and may be ripped up); the output then holds all routes.
With --zones every zone shape comes from that export (the refilled routed board) instead of COPPER.json.

Derived from the power board's route_signals.py (route_2026-09-16): same grid (0.1 mm), islands, minimum spanning
tree of each net's copper islands, Dijkstra over the routing layers, rip-up and repair rounds. What is card-specific:

Layers (user-approved plan, check-in 2): In1, In4, In6 GND planes; In3 the 5 V plane; F.Cu, In2, In5, B.Cu carry
GND fill that yields to routes. Logic nets route on F, In2, B; analog nets on F, In5, B; analog_5V and 12V on
F, In3, In5, B. No logic net ever runs on In5 and no analog net on In2.

Sensitive nets (user, 2026-09-22), routed first:
- Current (J11.23 -> U2.4, U5.3): B.Cu only, no via (J11 is through-hole, U2 and U5 sit on the underside), over the
  In6 GND plane.
- Net-(U2-In+) (U2.3, R11, R16, R17: 49 mV threshold at about 5 kohm, the most pickup-sensitive net) and V_err
  (U28.3, U4.4, U5.4): the run on In5 between the In4 and In6 GND planes; F / B only as pad stubs within STUB_R mm of
  their own pads.
After them, PROTECT builds keep-out distance fields round their copper:
- Current and U2 In+: no track of another non-GND net within ZONE mm on the same layer (for Current also on In5,
  the approved plan), and no via of another non-GND net within ZONE mm in plan view on any layer. Nets with a pad on
  the sensitive net's own parts (U2, U5, R11, R16, R17, J11) may run inside the track zone at a cost (their pins sit
  there), but their vias may not.
- V_err: the same distances against logic nets only.
STITCH then drops GND vias beside the U2 In+ run on In5 and beside the Current stubs, so the In5 / B.Cu GND fill on
both sides is a guard tied to the planes. The track zone keeps every other net out of that band, so the fill takes it.
"""
import json, math, sys, time
import numpy as np
from scipy import ndimage
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
from matplotlib.path import Path
from PIL import Image, ImageDraw

H = 0.1
X0, Y0 = 45.0, 69.0
NX, NY = 470, 470
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu', 'B.Cu']
LI = {n: i for i, n in enumerate(LAYERS)}
ROUTE = [0, 2, 3, 5, 7]
MARGIN = 0.06
HOLE_CLR = 0.20
HOLE_HOLE = 0.25
EDGE_CLR = 0.30
PAD_VIA_GAP = 0.10
NO_VIA_IN_PAD = False     # ROUTING_SPEC 2: epoxy-filled, capped vias are free on 6+ layer boards (as on the power board)
OWN_GAP = 0.10            # new copper keeps this gap from the net's other islands unless it lands inside them
EXT = 20                  # cells: distance fields see obstacles this far outside the routing window (2 mm)
# ROUTE_GRID=0.05 (finishing passes, 2026-09-24): half the cell size, so tight gaps between pads (0.6-0.7 mm) that the
# 0.1 mm raster reads as closed open up; the rasterisation allowance shrinks with the cell (raster error ~ H / 2 * 1.4)
import os as _os
if _os.environ.get('ROUTE_GRID') == '0.05':
    H = 0.05
    NX, NY = 940, 940
    EXT = 40
    MARGIN = 0.04
VIA_COST = 1.6            # mm-equivalent per via
VIA_POUR = 0.0
VIA_POUR_PAIR = 0.0
LAYER_COST = {0: 1.0, 2: 1.1, 3: 1.5, 5: 1.1, 7: 1.0}

CLASS = {  # the card's netclasses (shipped BOOST_control.kicad_pro): clearance enforced by DRC; w is the width used where
           # it fits, wmin the fallback (DRC minimum 0.13)
    'Default': dict(clr=0.20, w=0.20, wmin=0.15, via=(0.5, 0.3)),   # KiCad 10 applies its built-in 0.20 (see NOTE)
    'Power': dict(clr=0.25, w=0.30, wmin=0.25, via=(0.5, 0.3)),     # GND and the J11 sense lines (Vout_n, drains)
    'Rail': dict(clr=0.20, w=0.40, wmin=0.30, via=(0.5, 0.3)),      # 12V, 5V, analog_5V
    'Gate': dict(clr=0.20, w=0.50, wmin=0.30, via=(0.6, 0.3)),
}
WIDTH = {'Current': (0.25, 0.20)}
# J11 sense lines (Power class for their 0.25 mm clearance; they carry microamps into dividers): 0.15 mm fallback so
# they fit between J11's pins, 0.84 mm apart, with that clearance
WIDTH.update({n: (0.30, 0.15) for n in ('Vout_1', 'Vout_2', 'Vout_3', 'Output1_drain', 'Output2_drain', 'Output3_drain')})
RIP_BUDGET_S = 60.0       # rip-up attempts stop once a net has spent this long
FANOUT_SIGNALS = True     # escape vias for signal pads before any signal track (--no-fanout-signals: off)
HIGH_CURRENT = set()
QUIET = set()
J_FORBID = J_REF = J_FORBID_VIA = J_REF_VIA = 1e9
JCUT_R = JVIA_R = 0.6
RIPUP = True
RIP_RADIUS = 2.0
RIP_MAX = 4
SENS = ['Current', 'Net-(U2-In+)', 'V_err']   # V_err last: its vias keep 2 mm from U2 In+ (the user's rule)
RIP_PROTECT = {'GND'} | set(SENS)
FP_COPPER = '<footprint copper>'
PAD_CLR_MIN = 0.20
# NOTE: the shipped BOOST_control.kicad_pro lists Default at 0.15 / 0.15, but KiCad 10 loads the Default class as its
# built-in 0.20 / 0.20 (pcbnew and kicad-cli DRC alike, 2026-09-22). Routing uses the 0.20 KiCad enforces.
NPTH_CLR = 0.30           # copper to a non-plated hole: DRC treats the J9 tie slots as board edge (0.3 mm)
EARLY = ['Net-(U4-In+)', 'Net-(U14-In+)', 'Net-(U21-In+)', 'Net-(U21-In-)', 'Net-(Q1-E)']   # other comparator inputs
SPOKE_KEEP = [('J9', '10', 1.8)]    # thermal-relief pad (hand-soldered wire): no track this close, so its spokes land
# per layer, other nets only (--open-plan): J11.10 brings the card's 5 V in; on In3 no other net's track this close,
# so its thermal spokes land on the main 5 V pour (a pour island there starved them, 2026-09-24)
SPOKE_KEEP_LAYER = [('J11', '10', 1.6, 3)]
SRC_WIDTH_TEST = None
PAIR_ATTRACT = 0.15
DIRECT_NETS = set()
SMALL_VIA = (0.5, 0.3)    # every via: 0.5 / 0.3 (0.1 mm annulus = board minimum, drill 0.3 = DRU minimum)
PLANE_TARGET = {'5V': [3], 'GND': [1, 4, 6]}
PAIRS = {}
STAR = set()
FANOUT_PADS = {}
POUR_MULT_DRIVE = POUR_MULT_OTHER = 1.0

# ---- layer assignment (net classes in card_nets.py)
from card_nets import ANALOG, RAILS, is_logic
STUB_R = 0.6              # U2 In+ / V_err: F and B only this close to their own pads (pad, then its via)
ZONE = 2.0                # sensitive keep-out distance (copper edge to copper edge): Current and U2 In+ (user)
ZONES = {'Current': 2.0, 'Net-(U2-In+)': 2.0, 'V_err': 2.0}   # V_err: logic nets 2 mm (user, 2026-09-23)
VERR_LATE = False         # route V_err after the other comparator inputs (--verr-late)
# V_err keeps out of U4's In+ divider (R18, R19, R20 on B.Cu): its short route through there cut the divider in two
VERR_BLOCK_B = (78.4, 99.0, 81.6, 103.4)      # x0, y0, x1, y1: U4's In+ divider (R18-R20, placement c3); B.Cu and vias
VERR_PLANE_BAND = 0.3     # V_err: no via of another net this close (plus its radius) -> no antipad in the plane under it
ZONE_EXEMPT_COST = 20.0   # cost factor for an exempt net's track inside a track zone
ESCAPE_R = 0.8            # an exempt net (a pin inside the zone) may use the zone only this close to its own pads
ZONE_MARGIN = 0.15        # added to track-zone distances: grid rounding let an In5 track in at 1.875 mm (run 15)
ZONE_MARGIN_VIA = 0.02    # vias sit exactly on cell centres; MARGIN already covers the raster (U2.3's via needs it)
STITCH_PITCH = 1.5        # GND stitching vias beside the sensitive runs


LOGIC_IN3 = False         # --logic-in3: what-if, logic nets may also use In3 (the 5 V plane becomes a fill round them)
MIXED_INNER = False       # --mixed-inner: what-if (not the approved plan), logic and analog both on In2 and In5; the
                          # sensitive nets keep their layers and every keep-out round them still applies
# --open-plan (user, 2026-09-24): In4 becomes a signal layer with a GND fill, solid GND kept over the U2 In+ corridor
# (its In5 run) and the Current stub by an In4 keep-out for every other net; In3 carries signals beside the 5 V pour;
# logic and analog share In2, In3, In4 and In5; In1 and In6 stay solid GND planes; all sensitive-net rules unchanged
OPEN_PLAN = False
NO_IN3 = set()            # --no-in3 NETS: these nets keep off In3 (their In3 run was cutting the 5 V pour in two)


def set_open_plan():
    global OPEN_PLAN, ROUTE
    OPEN_PLAN = True
    ROUTE[:] = [0, 2, 3, 4, 5, 7]
    LAYER_COST.update({2: 1.1, 3: 1.3, 4: 1.1, 5: 1.1})     # In3 a little dearer: its tracks cut the 5 V pour
    PLANE_TARGET['GND'] = [1, 6]                             # In4's GND is a fill now, like In2 / In5


def route_layers(net):
    if net in NO_IN3:
        return [l for l in _route_layers(net) if l != 3]
    return _route_layers(net)


def _route_layers(net):
    if net == 'Current':
        return [7]
    if net in ('Net-(U2-In+)', 'V_err'):
        return [0, 5, 7]
    if OPEN_PLAN:
        if net == '5V':
            return [0, 3, 7]
        if net == 'GND':
            return [0, 2, 4, 5, 7]
        return [0, 2, 3, 4, 5, 7]
    if MIXED_INNER and net not in RAILS and net not in ('GND', '5V'):
        return [0, 2, 5, 7]
    if net in ANALOG:
        return [0, 5, 7]
    if net in RAILS:
        return [0, 3, 5, 7]
    if net == '5V':
        return [0, 3, 7]
    if net == 'GND':
        return [0, 2, 5, 7]
    return [0, 2, 3, 7] if LOGIC_IN3 else [0, 2, 7]


def pour_mult(net):
    return 1.0


def small_via_ok(net):
    return True


def cls_of(net, classes):
    c = classes.get(net, 'Default').split(',')[0]
    return c if c in CLASS else 'Default'


def rules_for(net, classes):
    c = dict(CLASS[cls_of(net, classes)])
    if net in WIDTH:
        c['w'], c['wmin'] = WIDTH[net]
    return c


def gkey(g):
    return tuple(tuple(x) if isinstance(x, list) else x for x in g)


def cell(x, y):
    return int(round((x - X0) / H - 0.5)), int(round((y - Y0) / H - 0.5))


def raster_poly(pts, into, val):
    # PIL polygon fill in cell units (cell k spans [k, k+1)); fills cells the outline passes through
    pts = np.asarray(pts, float)
    if len(pts) < 3:
        return
    i0 = max(int((pts[:, 0].min() - X0) / H) - 1, 0)
    i1 = min(int((pts[:, 0].max() - X0) / H) + 2, NX)
    j0 = max(int((pts[:, 1].min() - Y0) / H) - 1, 0)
    j1 = min(int((pts[:, 1].max() - Y0) / H) + 2, NY)
    if i1 <= i0 or j1 <= j0:
        return
    img = Image.new('1', (i1 - i0, j1 - j0), 0)
    xy = [((x - X0) / H - i0 - 0.5, (y - Y0) / H - j0 - 0.5) for x, y in pts]
    ImageDraw.Draw(img).polygon(xy, fill=1, outline=None)
    m = np.array(img, dtype=bool)
    into[j0:j1, i0:i1][m] = val


def raster_poly_c(pts, into, val):
    # cells whose centre lies inside the polygon (pads): the outline-inclusive raster_poly grows a pad by up to a cell
    # per side, which closed the 0.84 mm gaps between J11's pins to the router. With cell centres the raster errs by
    # at most H / sqrt(2) either way, and MARGIN (0.06) plus the H / 2 in every distance test keep DRC clearance.
    pts = np.asarray(pts, float)
    if len(pts) < 3:
        return
    i0 = max(int((pts[:, 0].min() - X0) / H) - 1, 0)
    i1 = min(int((pts[:, 0].max() - X0) / H) + 2, NX)
    j0 = max(int((pts[:, 1].min() - Y0) / H) - 1, 0)
    j1 = min(int((pts[:, 1].max() - Y0) / H) + 2, NY)
    if i1 <= i0 or j1 <= j0:
        return
    xs = X0 + (np.arange(i0, i1) + 0.5) * H
    ys = Y0 + (np.arange(j0, j1) + 0.5) * H
    Xg, Yg = np.meshgrid(xs, ys)
    m = Path(pts).contains_points(np.column_stack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)
    into[j0:j1, i0:i1][m] = val


def raster_disc(x, y, r, into, val):
    i0 = max(int((x - r - X0) / H) - 1, 0)
    i1 = min(int((x + r - X0) / H) + 2, NX)
    j0 = max(int((y - r - Y0) / H) - 1, 0)
    j1 = min(int((y + r - Y0) / H) + 2, NY)
    xs = X0 + (np.arange(i0, i1) + 0.5) * H
    ys = Y0 + (np.arange(j0, j1) + 0.5) * H
    Xg, Yg = np.meshgrid(xs, ys)
    m = (Xg - x) ** 2 + (Yg - y) ** 2 <= r * r
    into[j0:j1, i0:i1][m] = val


def raster_seg(x0, y0, x1, y1, r, into, val):
    i0 = max(int((min(x0, x1) - r - X0) / H) - 1, 0)
    i1 = min(int((max(x0, x1) + r - X0) / H) + 2, NX)
    j0 = max(int((min(y0, y1) - r - Y0) / H) - 1, 0)
    j1 = min(int((max(y0, y1) + r - Y0) / H) + 2, NY)
    xs = X0 + (np.arange(i0, i1) + 0.5) * H
    ys = Y0 + (np.arange(j0, j1) + 0.5) * H
    Xg, Yg = np.meshgrid(xs, ys)
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = np.zeros_like(Xg) if L2 == 0 else np.clip(((Xg - x0) * dx + (Yg - y0) * dy) / L2, 0, 1)
    d2 = (Xg - (x0 + t * dx)) ** 2 + (Yg - (y0 + t * dy)) ** 2
    into[j0:j1, i0:i1][d2 <= r * r] = val


class Board:
    def __init__(self, cop):
        self.cop = cop
        self.classes = cop.get('classes', {})
        names = set(cop['nets']) | {p['net'] for p in cop['pads']} | {FP_COPPER}
        self.nid = {n: i for i, n in enumerate(sorted(names))}
        self.nname = {i: n for n, i in self.nid.items()}
        self.hard = [np.full((NY, NX), -1, np.int32) for _ in LAYERS]
        self.clr = [np.zeros((NY, NX), np.float32) for _ in LAYERS]
        self.yld = [np.full((NY, NX), -1, np.int32) for _ in LAYERS]
        self.zonehard = [np.zeros((NY, NX), bool) for _ in LAYERS]
        self.smd = {0: np.full((NY, NX), -1, np.int32), 7: np.full((NY, NX), -1, np.int32)}   # SMD pad copper by net
        self.holes = np.full((NY, NX), -1, np.int32)
        self.keep_tracks = np.zeros((NY, NX), bool)
        self.keep_vias = np.zeros((NY, NX), bool)
        self.barrels = []           # (x, y, net id, [layers])
        self.fill_layers = {}       # net id -> layers carrying one of its yielding fills (GND fill, planes)
        # where a new track may end on a net's copper so that KiCad joins it: inside a pad, via or zone ("solid"), or
        # on a track's centre line ("tline"); a track end inside another track's width but off its centre line dangles
        self.solid = [np.full((NY, NX), -1, np.int32) for _ in LAYERS]
        self.tline = [np.full((NY, NX), -1, np.int32) for _ in LAYERS]
        tmp = np.zeros((NY, NX), bool)
        for z in cop['zones']:
            l = LI[z['layer']]
            n = self.nid[z['net']]
            if z['prio'] <= 1:
                self.fill_layers.setdefault(n, set()).add(l)
                for poly in z['polys']:
                    if not isinstance(poly, dict):
                        raster_poly(poly, self.yld[l], n)
                        raster_poly(poly, self.solid[l], n)
            else:
                c = max(z['clearance'], rules_for(z['net'], self.classes)['clr'])
                for poly in z['polys']:
                    if not isinstance(poly, dict):
                        tmp[:] = False
                        raster_poly(poly, tmp, True)
                        self.hard[l][tmp] = n
                        self.clr[l][tmp] = c
                        self.zonehard[l][tmp] = True
                        self.solid[l][tmp] = n
        for g in cop.get('fp_copper', []):
            # footprint copper graphics (the net-tie shapes of NT1-NT3): netless copper, cleared like a pad; the
            # tied pads are rasterised after them and take the overlapping cells back
            n = self.nid[FP_COPPER]
            for poly in g['polys']:
                if not isinstance(poly, dict):
                    tmp[:] = False
                    raster_poly(poly, tmp, True)
                    l = LI[g['layer']]
                    self.hard[l][tmp] = n
                    self.clr[l][tmp] = HOLE_CLR
                    self.zonehard[l][tmp] = False
        for p in cop['pads']:
            n = self.nid[p['net']]
            c = rules_for(p['net'], self.classes)['clr']
            c = max(c, PAD_CLR_MIN)
            for ln, polys in p['polys'].items():
                l = LI[ln]
                for poly in polys:
                    if not isinstance(poly, dict):
                        tmp[:] = False
                        raster_poly_c(poly, tmp, True)
                        self.hard[l][tmp] = n
                        self.clr[l][tmp] = c
                        self.zonehard[l][tmp] = False
                        self.solid[l][tmp] = n
                        if p['drill'] == 0 and l in (0, 7):
                            self.smd[l][tmp] = n
        for v in cop['vias']:
            n = self.nid[v['net']]
            c = rules_for(v['net'], self.classes)['clr']
            for ln in v['layers']:
                tmp[:] = False
                raster_disc(v['x'], v['y'], v['dia'] / 2, tmp, True)
                self.hard[LI[ln]][tmp] = n
                self.clr[LI[ln]][tmp] = c
                self.zonehard[LI[ln]][tmp] = False
                self.solid[LI[ln]][tmp] = n
            raster_disc(v['x'], v['y'], v['drill'] / 2, self.holes, n)
        for b in cop['barrels']:
            n = self.nid[b['net']]
            if b['kind'] == 'tht':
                raster_disc(b['x'], b['y'], b['drill'] / 2, self.holes, n)
            self.barrels.append((b['x'], b['y'], n, [LI[l] for l in b['layers']]))
        for t in cop.get('tracks', []):
            n = self.nid[t['net']]
            c = rules_for(t['net'], self.classes)['clr']
            tmp[:] = False
            raster_seg(t['x0'], t['y0'], t['x1'], t['y1'], t['w'] / 2, tmp, True)
            self.hard[LI[t['layer']]][tmp] = n
            self.clr[LI[t['layer']]][tmp] = c
            self.zonehard[LI[t['layer']]][tmp] = False
            raster_seg(t['x0'], t['y0'], t['x1'], t['y1'], 0.02, self.tline[LI[t['layer']]], n)
        for h in cop.get('npth', []):
            tmp[:] = False
            for poly in h['polys']:
                if not isinstance(poly, dict):
                    raster_poly_c(poly, tmp, True)
            if tmp.any():
                dh = ndimage.distance_transform_edt(~tmp) * H - H / 2
                self.keep_tracks |= dh < NPTH_CLR + 0.20 + MARGIN      # widest track half-width 0.2 (Rail)
                self.keep_vias |= dh < NPTH_CLR + 0.30 + MARGIN
        for p in cop['pads']:
            for ref, num, r in SPOKE_KEEP:
                if p['ref'] == ref and p['num'] == num:
                    tmp[:] = False
                    raster_disc(p['x'], p['y'], r, tmp, True)
                    self.keep_tracks |= tmp
        self.keep_tracks_l = {}     # layer -> (mask, net id allowed inside)
        if OPEN_PLAN:
            for ref, num, r, l in SPOKE_KEEP_LAYER:
                for p in cop['pads']:
                    if p['ref'] == ref and p['num'] == num:
                        tmp[:] = False
                        raster_disc(p['x'], p['y'], r, tmp, True)
                        self.keep_tracks_l[l] = (tmp.copy(), self.nid[p['net']])
        for k in cop['keepouts']:
            tmp[:] = False
            raster_poly(k['pts'], tmp, True)
            if k['no_tracks']:
                self.keep_tracks |= tmp
            if k['no_vias']:
                self.keep_vias |= tmp
        # board outline: polygon from the edge segments (simple closed outline)
        segs = [tuple(map(tuple, (e[:2], e[2:]))) for e in cop['edge']]
        pts = [segs[0][0], segs[0][1]]
        used = {0}
        while len(used) < len(segs):
            for k, (a, b) in enumerate(segs):
                if k in used:
                    continue
                if np.hypot(a[0] - pts[-1][0], a[1] - pts[-1][1]) < 1e-3:
                    pts.append(b); used.add(k); break
                if np.hypot(b[0] - pts[-1][0], b[1] - pts[-1][1]) < 1e-3:
                    pts.append(a); used.add(k); break
            else:
                break
        inside = np.zeros((NY, NX), bool)
        raster_poly_c(pts, inside, True)       # cell centres: the outline-inclusive raster let a track 0.285 mm off the edge
        self.edge_dist = ndimage.distance_transform_edt(inside) * H - H / 2
        self.lx_proj = ndimage.binary_dilation(self.hard[2] == self.nid.get('LX', -99), iterations=10)
        self.routes = []            # committed geometry
        self.keep = set()           # gkey of committed geometry that rip-up leaves alone (bypass links, fan-out vias)
        self.protect = False        # while True, commit() adds its geometry to keep
        self.loaded = False         # a repair round: earlier routes were loaded (finished gate loops are left alone)
        self.snapshot_base()
        self.hidden_yld = None      # fills hidden during a fan-out; vias landing in them still get full clearance
        self.jcut, self.jvia = {}, {}   # sheet-current maps (A/mm) spread for track and via cuts, per layer
        self.hot_ok = False         # last resort for an edge nothing else routes: cross copper above J_FORBID at cost
        self.direct = False         # gate-pin links and bypass links: shortest path, no power-copper limits or costs
        self.pair_tracks = False    # partner attraction to the partner's tracks only (gate-loop pairs), not its pours
        self.lx_ok = False          # gate loops: the LX pour may be crossed (at pour cost) where needed
        self.via_mult = 1.0         # via cost multiplier (gate-loop drive legs stay on one layer the return can follow)
        self.corridor = 0.0         # extra clearance width while routing (a gate-loop return keeps room for its drive)
        self.free_own = None        # {layer: mask}: own copper that is not an obstacle although outside A and B
        self.guide = None           # {layer: mask}: the only cells a route may use (sensitive-net pad stubs)
        self.via_forbid = None      # bool mask: no via of the net being routed here (sensitive-net planning)
        self.prot = []              # sensitive keep-outs: dict(nid, track={layer: dist}, via=dist, logic_only, exempt)

    # ------------------------------------------------------------------ islands
    def own_mask(self, n, l):
        return (self.hard[l] == n) | (self.yld[l] == n)

    def islands(self, n):
        labels, offs, total = {}, {}, 0
        for l in range(len(LAYERS)):
            m = self.own_mask(n, l)
            if not m.any():
                continue
            lab, k = ndimage.label(m, structure=np.ones((3, 3)))
            labels[l] = lab
            offs[l] = total
            total += k
        parent = list(range(total))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for x, y, bn, bl in self.barrels + [(r[1], r[2], r[3], r[4]) for r in self.routes if r[0] == 'via']:
            if bn != n:
                continue
            i, j = cell(x, y)
            ids = [offs[l] + labels[l][j, i] - 1 for l in bl if l in labels and labels[l][j, i] > 0]
            for a in ids[1:]:
                union(ids[0], a)
        groups = {}
        for l, lab in labels.items():
            for k in range(1, lab.max() + 1):
                groups.setdefault(find(offs[l] + k - 1), []).append((l, k))
        pads_cells = []
        for p in self.cop['pads']:
            if self.nid[p['net']] == n:
                i, j = cell(p['x'], p['y'])
                for ln in p['polys']:
                    l = LI[ln]
                    if l in labels and labels[l][j, i] > 0:
                        pads_cells.append(find(offs[l] + labels[l][j, i] - 1))
        keep = set(pads_cells)
        out = []
        for g, members in groups.items():
            if g in keep:
                out.append(members)
        return out, labels

    def island_pads(self, n, members, labels, most=4):
        found = []
        for p in self.cop['pads']:
            if self.nid[p['net']] != n:
                continue
            i, j = cell(p['x'], p['y'])
            for ln in p['polys']:
                l = LI[ln]
                if l in labels and (l, labels[l][j, i]) in members:
                    found.append('%s.%s' % (p['ref'], p['num']))
                    break
        return ' '.join(found[:most]) + (' +%d' % (len(found) - most) if len(found) > most else '') if found else 'no pads'

    # ------------------------------------------------------------------ routing
    def blocked_layer(self, n, l, bb, r_extra, cN, items_only=False):
        j0, j1, i0, i1 = bb
        sub = self.hard[l][j0:j1, i0:i1]
        cl = self.clr[l][j0:j1, i0:i1]
        foreign = (sub >= 0) & (sub != n)
        if items_only:
            foreign &= ~self.zonehard[l][j0:j1, i0:i1]
        blk = np.zeros(sub.shape, bool)
        for cv in np.unique(cl[foreign]):
            d = ndimage.distance_transform_edt(~(foreign & (cl == cv))) * H - H / 2
            blk |= d < r_extra + max(cN, float(cv)) + MARGIN
        return blk

    def try_edge(self, n, A, B, labels, partner=None):
        """Route an edge at the class width and via first, then with the small via, then at the fallback width, in
        the edge's window and then over the whole board."""
        net = self.nname[n]
        ru = rules_for(net, self.classes)
        small_ok = small_via_ok(net) and ru['via'] != SMALL_VIA
        narrow_ok = ru['wmin'] < ru['w']
        for full in (False, True):
            # a crossing of power copper (hot_ok) cuts less copper with the narrow track, so it goes first there
            for narrow in (((True, False) if (self.hot_ok or self.direct) else (False, True)) if narrow_ok else (False,)):
                for small in ((False, True) if small_ok else (False,)):
                    res = self.route_edge(n, A, B, labels, partner, full=full, small_via=small, narrow=narrow)
                    if res is not None:
                        return res
        return None

    def route_edge(self, n, A, B, labels, partner=None, full=False, small_via=False, window=None, narrow=False):
        """Route one edge; a path whose layer changes fall closer together than a via pitch cannot be built (two holes
        on top of each other, and one merged via would sit where it was never checked), so the second via cell is
        banned and the edge routed again."""
        ban = set()
        for _ in range(8):
            res = self._route_edge(n, A, B, labels, partner, full, small_via, window, narrow, ban)
            if res is None:
                return None
            path, ru = res
            pitch = ru['via'][1] + HOLE_HOLE + MARGIN
            changes = [(path[k][1], path[k][2]) for k in range(len(path) - 1) if path[k][0] != path[k + 1][0]]
            clash = [c2 for c1, c2 in zip(changes, changes[1:]) if H * math.hypot(c2[0] - c1[0], c2[1] - c1[1]) < pitch]
            if not clash:
                return res
            ban.update(clash)
        return None

    def _route_edge(self, n, A, B, labels, partner, full, small_via, window, narrow, ban):
        net = self.nname[n]
        ru = rules_for(net, self.classes)
        if small_via:
            ru['via'] = SMALL_VIA
        if narrow:
            ru['w'] = ru['wmin']
        w, cN = ru['w'], ru['clr']
        vdia, vdrill = ru['via']
        planes = PLANE_TARGET.get(net, [])
        layers = [l for l in ROUTE if l in route_layers(net)] + [l for l in planes if l not in ROUTE]
        # sensitive keep-outs that apply to this net (not GND, not the sensitive net itself)
        prots = [pr for pr in self.prot if pr['nid'] != n and net != 'GND' and (not pr['logic_only'] or is_logic(net))]
        amask = {}
        bmask = {}
        for l in layers:
            if l in labels:
                la = np.isin(labels[l], [k for (ll, k) in A if ll == l])
                lb = np.isin(labels[l], [k for (ll, k) in B if ll == l])
                if la.any():
                    amask[l] = la
                if lb.any():
                    bmask[l] = lb
        if not amask or not bmask:
            return None
        if full:
            core = (0, NY, 0, NX)
        elif window is not None:
            core = window
        else:
            ys, xs = [], []
            for mm in list(amask.values()) + list(bmask.values()):
                jj, ii = np.nonzero(mm)
                ys += [jj.min(), jj.max()]
                xs += [ii.min(), ii.max()]
            pad = 80
            core = (max(min(ys) - pad, 0), min(max(ys) + pad, NY), max(min(xs) - pad, 0), min(max(xs) + pad, NX))
        # every distance field is computed over the core window grown by EXT cells, so obstacles just outside the
        # core still count; the graph is limited to the core by making the added ring impassable
        bb = (max(core[0] - EXT, 0), min(core[1] + EXT, NY), max(core[2] - EXT, 0), min(core[3] + EXT, NX))
        j0, j1, i0, i1 = bb
        ring = np.ones((j1 - j0, i1 - i0), bool)
        ring[core[0] - j0:core[1] - j0, core[2] - i0:core[3] - i0] = False
        ny, nx = j1 - j0, i1 - i0
        holes = self.holes[j0:j1, i0:i1]
        hole_foreign_d = ndimage.distance_transform_edt(~((holes >= 0) & (holes != n))) * H - H / 2
        hole_any_d = ndimage.distance_transform_edt(~(holes >= 0)) * H - H / 2
        edge = self.edge_dist[j0:j1, i0:i1]
        other_d, other_in = {}, {}
        for l in range(len(LAYERS)):
            oth = self.own_mask(n, l)[j0:j1, i0:i1]
            if l in labels:
                oth = oth & ~np.isin(labels[l][j0:j1, i0:i1], [k for (ll, k) in list(A) + list(B) if ll == l])
            if self.free_own is not None and l in self.free_own:
                oth = oth & ~self.free_own[l][j0:j1, i0:i1]
            if oth.any():
                other_d[l] = ndimage.distance_transform_edt(~oth) * H - H / 2
                other_in[l] = ndimage.distance_transform_edt(oth) * H
        passable, cost = {}, {}
        term, via_term_ok, depth = {}, {}, {}
        hot = {}
        for l in layers:
            own = self.own_mask(n, l)[j0:j1, i0:i1]
            depth[l] = ndimage.distance_transform_edt(own) * H
            term[l] = np.zeros((ny, nx), bool)
            for mm in (amask.get(l), bmask.get(l)):
                if mm is not None:
                    term[l] |= mm[j0:j1, i0:i1]
            if l in planes and l not in ROUTE:
                passable[l] = own & (hole_foreign_d >= vdrill / 2 + HOLE_CLR) & ~ring
                cost[l] = np.ones((ny, nx))
                continue
            blk_all = self.blocked_layer(n, l, bb, w / 2 + self.corridor / 2, cN)
            blk = self.blocked_layer(n, l, bb, w / 2 + self.corridor / 2, cN, items_only=True)
            lxz = self.zonehard[l][j0:j1, i0:i1] & (self.hard[l][j0:j1, i0:i1] == self.nid.get('LX', -99)) & (n != self.nid.get('LX', -99))
            if lxz.any() and not (self.direct or self.lx_ok):   # direct links and gate loops may cross the LX pour
                blk |= ndimage.distance_transform_edt(~lxz) * H - H / 2 < w / 2 + 0.3 + MARGIN
            pour_only = blk_all & ~blk
            cut = None
            if l in self.jcut:
                yl = self.yld[l][j0:j1, i0:i1]
                cut = pour_only | ((yl >= 0) & (yl != n))
                S = self.jcut[l][j0:j1, i0:i1]
                hot[l] = np.where(cut & (S > J_FORBID), S, 0.0)
                if not (self.hot_ok or self.direct):
                    blk |= cut & (S > J_FORBID)
            blk |= hole_foreign_d < w / 2 + HOLE_CLR + MARGIN
            blk |= self.keep_tracks[j0:j1, i0:i1]
            if l in self.keep_tracks_l and self.keep_tracks_l[l][1] != n:
                blk |= self.keep_tracks_l[l][0][j0:j1, i0:i1]
            zone_cost = None
            for pr in prots:
                if l in pr['track'] and (not pr['track'][l][1] or is_logic(net)):
                    inz = pr['track'][l][0][j0:j1, i0:i1] < pr['zone'] + w / 2 + MARGIN + ZONE_MARGIN
                    if n in pr['exempt']:
                        # a pin sits inside the zone: its track may leave the pad (ESCAPE_R), not run along the zone
                        esc = self.escape_mask(n, l)[j0:j1, i0:i1]
                        blk |= inz & ~esc
                        zone_cost = (inz & esc) if zone_cost is None else (zone_cost | (inz & esc))
                    else:
                        blk |= inz
            blk |= edge < w / 2 + EDGE_CLR + MARGIN
            if l in other_d:
                blk |= other_d[l] < w / 2 + OWN_GAP + MARGIN
            passable[l] = ~blk & ~ring
            if self.guide is not None:
                g = self.guide[l][j0:j1, i0:i1] if l in self.guide else np.zeros((ny, nx), bool)
                passable[l] &= g | term[l]
            c = np.full((ny, nx), LAYER_COST[l])
            if not self.direct:
                c[pour_only] *= pour_mult(net)
                if cut is not None:
                    c[cut] *= 1.0 + S[cut] / J_REF
            if net in QUIET:
                lx = self.lx_proj[j0:j1, i0:i1]
                if l == 3:
                    c[lx] *= 5.0
                if l == 2:
                    c[lx] *= 5.0
            if partner is not None:
                pm = np.isin(self.hard[l][j0:j1, i0:i1], partner if isinstance(partner, (list, tuple)) else [partner])
                if self.pair_tracks:
                    pm &= ~self.zonehard[l][j0:j1, i0:i1]
                if pm.any():
                    d = ndimage.distance_transform_edt(~pm) * H
                    band = (d > w / 2 + cN) & (d < w / 2 + cN + 0.45)
                    c[band] *= PAIR_ATTRACT if self.pair_tracks else 0.45
                else:
                    c *= 1.3
            if zone_cost is not None:
                c[zone_cost] *= ZONE_EXEMPT_COST
            cost[l] = c
            # own terminal cells are enterable where the part of the track (or via) disc lying outside the net's own
            # copper still clears every foreign item, hole, keep-out and the edge
            if term[l].any():
                # only the net's own pads, vias and tracks excuse a nearby foreign item: zones and fills stop at their
                # own clearance, so new copper over them still needs the full gap
                own_items = (self.hard[l][j0:j1, i0:i1] == n) & ~self.zonehard[l][j0:j1, i0:i1]
                near = self.blocked_layer(n, l, bb, 0.0, cN, items_only=True) & ~own_items
                if lxz.any() and not (self.direct or self.lx_ok):
                    near |= (ndimage.distance_transform_edt(~lxz) * H - H / 2 < 0.3 + MARGIN) & ~own_items
                viol = near | (hole_foreign_d < HOLE_CLR + MARGIN) | (edge < EDGE_CLR + MARGIN) | self.keep_tracks[j0:j1, i0:i1]
                if l in other_d:
                    viol |= other_d[l] < OWN_GAP + MARGIN
                free_r = ndimage.distance_transform_edt(~viol) * H - H / 2
                passable[l] |= term[l] & (free_r >= w / 2) & ~ring
                via_term_ok[l] = term[l] & (free_r >= vdia / 2)
                # a via joining a fill (not a pad, via, track or pour) must sit a via radius inside it, or the refill
                # round the new copper nearby can leave the via outside the fill
                fill_only = (self.yld[l][j0:j1, i0:i1] == n) & (self.hard[l][j0:j1, i0:i1] != n)
                via_term_ok[l] &= ~fill_only | (depth[l] >= vdia / 2 + H)
            else:
                via_term_ok[l] = term[l]
        # via feasibility: annulus layers (the two ends) need full clearance, set per pair below; every other
        # layer only needs its pads, vias and tracks cleared by the hole (a power pour clears round the hole)
        vbase = hole_any_d >= vdrill / 2 + HOLE_HOLE + MARGIN
        vbase &= ~self.keep_vias[j0:j1, i0:i1]
        vbase &= edge >= vdia / 2 + EDGE_CLR + MARGIN
        items_block = np.zeros((ny, nx), bool)
        pour_count = np.zeros((ny, nx))
        via_j = np.zeros((ny, nx))
        full_block = {}
        for l in range(len(LAYERS)):
            items_block |= self.blocked_layer(n, l, bb, vdrill / 2 + HOLE_CLR - cN, cN, items_only=True)
            if NO_VIA_IN_PAD and l in self.smd:   # no via in or touching an SMD pad of its own net (solder wicks)
                spad = self.smd[l][j0:j1, i0:i1] == n
                if spad.any():
                    items_block |= ndimage.distance_transform_edt(~spad) * H - H / 2 < vdia / 2 + PAD_VIA_GAP + MARGIN
            if l in other_d:    # a via either clears the net's other islands or sits wholly inside one (a real joint)
                items_block |= (other_d[l] < vdia / 2 + OWN_GAP + MARGIN) & (other_in[l] < vdia / 2 + H)
            zh = self.zonehard[l][j0:j1, i0:i1] & (self.hard[l][j0:j1, i0:i1] != n)
            if l not in (1, 4, 6):
                pour_count += ndimage.binary_dilation(zh, iterations=4)
            if l in self.jvia and not self.direct:
                yl = self.yld[l][j0:j1, i0:i1]
                foreign = ndimage.binary_dilation(zh | ((yl >= 0) & (yl != n)), iterations=int(round(JVIA_R / H)))
                Sv = self.jvia[l][j0:j1, i0:i1]
                items_block |= foreign & (Sv > J_FORBID_VIA)
                via_j += np.where(foreign, Sv / J_REF_VIA, 0.0)
            ownl = self.own_mask(n, l)[j0:j1, i0:i1]
            if self.hidden_yld is not None:
                ownl = ownl | (self.hidden_yld[l][j0:j1, i0:i1] == n)
            if l in self.fill_layers.get(n, ()):
                # the fill may be absent at the via today only because KiCad removed an isolated island there; the via
                # can reconnect that island, which then refills and flashes the via, so assume the annulus is present
                ownl = np.ones_like(ownl)
            if l in layers or ownl.any():
                fb = self.blocked_layer(n, l, bb, vdia / 2, cN, items_only=True)
                # KiCad flashes a via on every layer where its annulus touches its own net's copper (fills included),
                # so there it needs full clearance even when the layer is not one of the path's two ends
                touch = ndimage.binary_dilation(ownl, iterations=int(math.ceil(vdia / 2 / H))) if not ownl.all() else ownl
                items_block |= touch & fb
            if l in layers:
                lxz = self.zonehard[l][j0:j1, i0:i1] & (self.hard[l][j0:j1, i0:i1] == self.nid.get('LX', -99)) & (n != self.nid.get('LX', -99))
                if lxz.any() and not (self.direct or self.lx_ok):
                    fb |= ndimage.distance_transform_edt(~lxz) * H - H / 2 < vdia / 2 + 0.3 + MARGIN
                full_block[l] = fb
        vbase &= ~items_block & ~ring
        for pr in prots:
            vbase &= ~(pr['via'][j0:j1, i0:i1] < pr['zone'] + vdia / 2 + MARGIN + ZONE_MARGIN_VIA)
        if self.via_forbid is not None:
            vbase &= ~self.via_forbid[j0:j1, i0:i1]
        for (bj, bi) in ban:
            if j0 <= bj < j1 and i0 <= bi < i1:
                vbase[bj - j0, bi - i0] = False
        # graph
        L = len(layers)
        N = L * ny * nx
        rows, cols, wts = [], [], []
        idx = np.arange(ny * nx).reshape(ny, nx)
        for k, l in enumerate(layers):
            P = passable[l]
            C = cost[l]
            base = k * ny * nx
            for (dj, di, s) in ((0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))):
                if di >= 0:
                    a = (slice(0, ny - dj), slice(0, nx - di))
                    b = (slice(dj, ny), slice(di, nx))
                else:
                    a = (slice(0, ny - dj), slice(1, nx))
                    b = (slice(dj, ny), slice(0, nx - 1))
                ok = P[a] & P[b]
                if s > 1:   # no diagonal squeeze past a blocked corner
                    if di > 0:
                        ok &= P[a[0], b[1]] & P[b[0], a[1]]
                    else:
                        ok &= P[slice(0, ny - 1), slice(0, nx - 1)] & P[slice(1, ny), slice(1, nx)]
                rows.append(base + idx[a][ok])
                cols.append(base + idx[b][ok])
                wts.append((H * s * 0.5 * (C[a] + C[b]))[ok])
        for ka in range(L):
            for kb in range(ka + 1, L):
                la, lb = layers[ka], layers[kb]
                ok = vbase & passable[la] & passable[lb]
                if la in ROUTE:
                    ok &= ~full_block[la] | via_term_ok[la]
                if lb in ROUTE:
                    ok &= ~full_block[lb] | via_term_ok[lb]
                ii = idx[ok]
                rows.append(ka * ny * nx + ii)
                cols.append(kb * ny * nx + ii)
                pour_w = 0.0 if self.direct else (VIA_POUR_PAIR if (net in PAIRS or net in PAIRS.values()) else VIA_POUR)
                wts.append(VIA_COST * self.via_mult + pour_w * pour_count[ok] + via_j[ok])
        r_ = np.concatenate(rows)
        c_ = np.concatenate(cols)
        w_ = np.concatenate(wts)
        G = sp.coo_matrix((w_, (r_, c_)), shape=(N, N)).tocsr()
        def ends(masks):
            # path ends sit at least two cells inside the net's rasterised copper, so the track end point lies inside
            # the real pad or via (the raster over-covers outlines by up to a cell), and on a pad, via or zone or on
            # a track centre line; weaker ends only as fallbacks
            for dmin, anchor in ((0.2 - 1e-6, True), (0.0, True), (0.2 - 1e-6, False), (0.0, False)):
                out = []
                for k, l in enumerate(layers):
                    if l in masks:
                        m = masks[l][j0:j1, i0:i1] & passable[l] & (depth[l] >= dmin)
                        if anchor:
                            m &= (self.solid[l][j0:j1, i0:i1] == n) | (self.tline[l][j0:j1, i0:i1] == n)
                        out.append(k * ny * nx + idx[m])
                out = np.concatenate(out) if out else np.array([], int)
                if out.size:
                    return out
            return out

        src, dst = ends(amask), ends(bmask)
        if src.size == 0 or dst.size == 0:
            return None
        if src.size > 4000:
            src = src[:: max(1, src.size // 4000)]
        dist, pred, sources = dijkstra(G, directed=False, indices=src, min_only=True, return_predecessors=True)
        dd = dist[dst]
        if not np.isfinite(dd).any():
            return None
        t = int(dst[np.argmin(dd)])
        path = []
        while t >= 0:
            path.append(t)
            if t == sources[t]:
                break
            t = pred[t]
        path.reverse()
        out = []
        for node in path:
            k, rem = divmod(node, ny * nx)
            j, i = divmod(rem, nx)
            out.append((layers[k], j + j0, i + i0))
        crossed = [(float(hot[l][j - j0, i - i0]), l, j, i) for (l, j, i) in out if l in hot and hot[l][j - j0, i - i0] > 0]
        if crossed:
            smax = max(crossed)
            ru['hot'] = dict(cells=len(crossed), max_A_per_mm=round(smax[0], 2), layer=LAYERS[smax[1]],
                             x=round(X0 + (smax[3] + 0.5) * H, 2), y=round(Y0 + (smax[2] + 0.5) * H, 2))
        return out, ru

    def commit(self, n, path, ru):
        w, cN = ru['w'], ru['clr']
        vdia, vdrill = ru['via']
        pts = [(l, X0 + (i + 0.5) * H, Y0 + (j + 0.5) * H) for (l, j, i) in path]
        runs = []
        k = 0
        while k < len(pts):
            run = [pts[k]]
            k += 1
            while k < len(pts) and pts[k][0] == run[0][0]:
                run.append(pts[k])
                k += 1
            runs.append(run)
        # route_edge never returns layer changes closer than a via pitch (see there), so each run ends in its own via
        geoms = []
        for r_i, run in enumerate(runs):
            l = run[0][0]
            if r_i + 1 < len(runs):
                geoms.append(('via', run[-1][1], run[-1][2], n, [l, runs[r_i + 1][0][0]], vdia, vdrill))
            # simplify collinear points
            simp = [run[0]]
            for p in run[1:]:
                if len(simp) >= 2:
                    a, b = simp[-2], simp[-1]
                    if abs((b[1] - a[1]) * (p[2] - b[2]) - (b[2] - a[2]) * (p[1] - b[1])) < 1e-9:
                        simp[-1] = p
                        continue
                simp.append(p)
            if l in ROUTE:
                for a, b in zip(simp, simp[1:]):
                    geoms.append(('track', a[1], a[2], b[1], b[2], n, l, w))
        self.restore(geoms)
        if self.protect:
            self.keep |= {gkey(g) for g in geoms}
        return geoms

    def load_jmap(self, path):
        d = np.load(path)

        def disk(r):
            k = int(round(r / H))
            yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
            return xx * xx + yy * yy <= k * k

        for key in d.files:
            l = LI[key.replace('_', '.')]
            S = d[key].astype(np.float32)
            self.jcut[l] = ndimage.maximum_filter(S, footprint=disk(JCUT_R))
            self.jvia[l] = ndimage.maximum_filter(S, footprint=disk(JVIA_R))

    def raster_geom(self, g):
        if g[0] == 'track':
            _, x0, y0, x1, y1, nn, l, ww = g
            cN = rules_for(self.nname[nn], self.classes)['clr']
            tmp = np.zeros((NY, NX), bool)
            raster_seg(x0, y0, x1, y1, ww / 2, tmp, True)
            self.hard[l][tmp] = nn
            self.clr[l][tmp] = cN
            self.zonehard[l][tmp] = False
            raster_seg(x0, y0, x1, y1, 0.02, self.tline[l], nn)
        else:
            _, x, y, nn, ls, dia, drill = g
            cN = rules_for(self.nname[nn], self.classes)['clr']
            raster_disc(x, y, drill / 2, self.holes, nn)
            ci, cj = cell(x, y)
            # the annulus exists on the two end layers and wherever KiCad will flash it: the net's fill layers and
            # any layer where the via sits in the net's own copper
            k = int(math.ceil(dia / 2 / H))
            flash = set(ls) | self.fill_layers.get(nn, set()) | (set(ROUTE) if self.nname[nn] == 'GND' else set()) | {
                l for l in ROUTE if self.own_mask(nn, l)[max(cj - k, 0):cj + k + 1, max(ci - k, 0):ci + k + 1].any()}
            for l in sorted(flash):
                if l in ROUTE:
                    tmp = np.zeros((NY, NX), bool)
                    raster_disc(x, y, dia / 2, tmp, True)
                    self.hard[l][tmp] = nn
                    self.clr[l][tmp] = cN
                    self.zonehard[l][tmp] = False
                    self.solid[l][tmp] = nn

    def restore(self, geoms):
        for g in geoms:
            self.raster_geom(g)
            self.routes.append(g)

    def snapshot_base(self):
        # rasters with no routes committed: rip() returns cells to these values
        self.base_hard = [a.copy() for a in self.hard]
        self.base_clr = [a.copy() for a in self.clr]
        self.base_zonehard = [a.copy() for a in self.zonehard]
        self.base_solid = [a.copy() for a in self.solid]
        self.base_tline = [a.copy() for a in self.tline]
        self.base_holes = self.holes.copy()

    def rip(self, nids):
        """Remove every committed route of the nets NIDS; returns the removed geometry."""
        nids = list(nids)
        gone = [g for g in self.routes if g[5 if g[0] == 'track' else 3] in nids and gkey(g) not in self.keep]
        self.routes = [g for g in self.routes if g[5 if g[0] == 'track' else 3] not in nids or gkey(g) in self.keep]
        for l in range(len(LAYERS)):
            m = np.isin(self.hard[l], nids) & ((self.hard[l] != self.base_hard[l]) |
                                               (self.zonehard[l] != self.base_zonehard[l]) |
                                               (self.clr[l] != self.base_clr[l]))
            self.hard[l][m] = self.base_hard[l][m]
            self.clr[l][m] = self.base_clr[l][m]
            self.zonehard[l][m] = self.base_zonehard[l][m]
            for arr, base in ((self.solid[l], self.base_solid[l]), (self.tline[l], self.base_tline[l])):
                m = np.isin(arr, nids) & (arr != base)
                arr[m] = base[m]
        m = np.isin(self.holes, nids) & (self.holes != self.base_holes)
        self.holes[m] = self.base_holes[m]
        for g in self.routes:           # kept geometry of these nets: put its cells back
            if g[5 if g[0] == 'track' else 3] in nids:
                self.raster_geom(g)
        return gone

    def replace_fills(self, cop2):
        """Take the yielding fills (priority <= 1) from another export of the same board, such as the routed board
        after KiCad refilled it, so fill fragments cut off by routes show up as islands."""
        for l in range(len(LAYERS)):
            m = self.yld[l] >= 0
            self.solid[l][m & (self.solid[l] == self.yld[l])] = -1
            self.yld[l][:] = -1
        for z in cop2['zones']:
            if z['prio'] > 1:
                continue
            l, n = LI[z['layer']], self.nid[z['net']]
            for poly in z['polys']:
                if not isinstance(poly, dict):
                    raster_poly(poly, self.yld[l], n)
                    raster_poly(poly, self.solid[l], n)
        self.snapshot_base()

    def load_routes(self, rt):
        geoms = [('track', t['x0'], t['y0'], t['x1'], t['y1'], self.nid[t['net']], LI[t['layer']], t['w'])
                 for t in rt['tracks']]
        geoms += [('via', v['x'], v['y'], self.nid[v['net']], [LI[x] for x in v['layers']], v['dia'], v['drill'])
                  for v in rt['vias']]
        self.keep |= {gkey(g) for g, item in zip(geoms, rt['tracks'] + rt['vias']) if item.get('keep')}
        self.restore(geoms)
        self.loaded = True

    def ghost_blockers(self, n, A, B, labels, partner, max_nets=12):
        """Route the edge with every other net's routes lifted (the ghost path), put them back, and return the nets
        whose tracks or vias lie in the ghost path's corridor, most crossings first."""
        others = sorted({g[5] if g[0] == 'track' else g[3] for g in self.routes} - {n} -
                        {self.nid[x] for x in RIP_PROTECT if x in self.nid})
        lifted = self.rip(others)
        try:
            res = self.try_edge(n, A, B, labels, partner)
        finally:
            self.restore(lifted)
        if res is None:
            return []
        path, ru = res
        reach = int(math.ceil((max(ru['w'], ru['via'][0]) / 2 + 0.3 + MARGIN) / H))
        corridor = {l: np.zeros((NY, NX), bool) for l in range(len(LAYERS))}
        for k, (l, j, i) in enumerate(path):
            corridor[l][j, i] = True
            if k + 1 < len(path) and path[k + 1][0] != l:      # ghost via: all layers
                for ll in corridor:
                    corridor[ll][j, i] = True
        foot = np.ones((2 * reach + 1, 2 * reach + 1), bool)
        for l in corridor:
            if corridor[l].any():
                corridor[l] = ndimage.binary_dilation(corridor[l], structure=foot)
        count = {}
        for g in self.routes:
            gn = g[5] if g[0] == 'track' else g[3]
            if gn == n or self.nname[gn] in RIP_PROTECT:
                continue
            if g[0] == 'track':
                steps = max(1, int(math.hypot(g[3] - g[1], g[4] - g[2]) / H))
                pts = [(g[6], g[1] + (g[3] - g[1]) * t / steps, g[2] + (g[4] - g[2]) * t / steps) for t in range(steps + 1)]
            else:
                pts = [(ll, g[1], g[2]) for ll in range(len(LAYERS))]
            hit = 0
            for l, x, y in pts:
                i, j = cell(x, y)
                if 0 <= i < NX and 0 <= j < NY and corridor[l][j, i]:
                    hit += 1
            if hit:
                count[gn] = count.get(gn, 0) + hit
        return sorted(count, key=lambda k: -count[k])[:max_nets]

    def ripup_edge(self, n, A, B, labels, partner, near_mask, log, radius=None, max_nets=None, blockers=None):
        """The edge A-B failed: rip up the routes of other nets that are in the way (by default the nearest ones
        round the smaller island; or the given BLOCKERS), route the edge, then re-route the ripped nets; undo
        everything if any of them fails."""
        net = self.nname[n]
        if blockers is None:
            radius = RIP_RADIUS if radius is None else radius
            max_nets = RIP_MAX if max_nets is None else max_nets
            zone = ndimage.binary_dilation(near_mask, iterations=int(round(radius / H)))
            count = {}
            for g in self.routes:
                gn = g[5] if g[0] == 'track' else g[3]
                if gn == n or self.nname[gn] in RIP_PROTECT:
                    continue
                if g[0] == 'track':
                    pts = [(g[1], g[2]), (g[3], g[4]), ((g[1] + g[3]) / 2, (g[2] + g[4]) / 2)]
                else:
                    pts = [(g[1], g[2])]
                for x, y in pts:
                    i, j = cell(x, y)
                    if 0 <= i < NX and 0 <= j < NY and zone[j, i]:
                        count[gn] = count.get(gn, 0) + 1
                        break
            blockers = sorted(count, key=lambda k: -count[k])[:max_nets]
        if not blockers:
            return False
        saved_self = [g for g in self.routes if (g[5] if g[0] == 'track' else g[3]) == n and gkey(g) not in self.keep]
        saved = self.rip(blockers)
        res = self.try_edge(n, A, B, labels, partner)
        names = ', '.join(self.nname[b] for b in blockers)
        if res is None:
            self.restore(saved)
            log.append('rip  %-16s ripping %s did not free a path' % (net, names))
            return False
        self.commit(n, *res)
        sub = []
        order = sorted(blockers, key=lambda b: ORDER.index(self.nname[b]) if self.nname[b] in ORDER else 999)
        for b in order:
            if self.route_net(self.nname[b], sub, allow_rip=False):
                self.rip(list(blockers) + [n])
                self.restore(saved_self + saved)
                log.append('rip  %-16s ripped %s, but %s then failed; undone' % (net, names, self.nname[b]))
                return False
        log.append('rip  %-16s ripped and re-routed %s' % (net, names))
        log.extend('     ' + x for x in sub)
        return True

    def island_of_pad(self, n, isl, labels, ref, num):
        for p in self.cop['pads']:
            if p['ref'] == ref and p['num'] == num:
                i, j = cell(p['x'], p['y'])
                for ln in p['polys']:
                    l = LI[ln]
                    if l in labels and labels[l][j, i] > 0:
                        for k, members in enumerate(isl):
                            if (l, labels[l][j, i]) in members:
                                return k
        return None

    def guide_mask(self, legs, r):
        """Cells within R mm of the hand-chosen corridor: [(layer, [(x, y), ...]), ...]."""
        g = {}
        for ln, pts in legs:
            l = LI[ln]
            if l not in g:
                g[l] = np.zeros((NY, NX), bool)
            for a, b in zip(pts, pts[1:]):
                raster_seg(a[0], a[1], b[0], b[1], r, g[l], True)
        return g

    def route_pad_edge(self, net, pad_a, target, log, partner_net=None, direct=False, hot_ok=False, hide_fill=False,
                       tag='edge', max_len=None, own_routes_off=False, corridor=0.0):
        """Route one connection of NET from pad PAD_A (ref, num) to the island holding pad TARGET, or to the net's
        largest island when TARGET is 'largest'. DIRECT: shortest path, no power-copper limits or costs. HOT_OK:
        power copper may be crossed at its current-weighted cost. PARTNER_NET: run beside that net's tracks.
        HIDE_FILL: the net's own fills on the routing layers are ignored, so pads that only touch through a fill
        get a real track (used for GND bypass links)."""
        n = self.nid[net]
        if hide_fill:
            self.hidden_yld = [y.copy() for y in self.yld]
            for l in [x for x in ROUTE if x not in PLANE_TARGET.get(net, [])]:     # a plane stays a plane
                self.yld[l][self.yld[l] == n] = -1
        lifted = []
        if own_routes_off:        # route as if the net's earlier tracks were not there; its vias stay (they may flash)
            gone = self.rip([n])
            keep = [g for g in gone if g[0] == 'via']
            lifted = [g for g in gone if g[0] != 'via']
            self.restore(keep)
        try:
            isl, labels = self.islands(n)
            ia = self.island_of_pad(n, isl, labels, *pad_a)
            if target == 'largest':
                ib = int(np.argmax([sum(int((labels[l] == k).sum()) for l, k in m) for m in isl])) if isl else None
                tname = 'largest island'
            else:
                ib = self.island_of_pad(n, isl, labels, *target)
                tname = '%s.%s' % target
            if ia is None or ib is None:
                log.append('%s %-16s %s.%s -> %s: pad not found in the net\'s copper' % (tag, net, pad_a[0], pad_a[1], tname))
                return False
            if ia == ib:
                log.append('%s %-16s %s.%s -> %s: already joined' % (tag, net, pad_a[0], pad_a[1], tname))
                return True
            self.direct, self.hot_ok, self.pair_tracks = direct, hot_ok, partner_net is not None
            try:
                pn = None
                if partner_net:
                    pn = [self.nid[x] for x in partner_net] if isinstance(partner_net, (list, tuple)) else self.nid[partner_net]
                self.corridor = corridor
                try:
                    res = self.try_edge(n, isl[ia], isl[ib], labels, pn)
                finally:
                    self.corridor = 0.0
                if res is None and corridor > 0:
                    res = self.try_edge(n, isl[ia], isl[ib], labels, pn)
                    if res is not None:
                        log.append('%s %-16s %s.%s: no room for the paired corridor, routed without it' % (tag, net, pad_a[0], pad_a[1]))
            finally:
                self.direct = self.hot_ok = self.pair_tracks = False
            if res is None:
                log.append('FAIL %s %-16s %s.%s -> %s' % (tag, net, pad_a[0], pad_a[1], tname))
                return False
            path_mm = sum(H * math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(res[0], res[0][1:]) if a[0] == b[0])
            if max_len is not None and path_mm > max_len:
                log.append('%s %-16s %s.%s -> %s: shortest path %.1f mm > %.1f mm, not drawn' % (
                    tag, net, pad_a[0], pad_a[1], tname, path_mm, max_len))
                return False
            g = self.commit(n, *res)
            ln = sum(math.hypot(x[3] - x[1], x[4] - x[2]) for x in g if x[0] == 'track')
            nv = sum(1 for x in g if x[0] == 'via')
            log.append('%s %-16s %s.%s -> %s: %.1f mm, %d via(s), w %.2f%s' % (
                tag, net, pad_a[0], pad_a[1], tname, ln, nv, res[1]['w'],
                (' beside %s' % (' + '.join(partner_net) if isinstance(partner_net, (list, tuple)) else partner_net)) if partner_net else ''))
            return True
        finally:
            if lifted:
                self.restore(lifted)
            if hide_fill:
                for l in ROUTE:
                    self.yld[l][self.hidden_yld[l] == n] = n
                self.hidden_yld = None

    # ------------------------------------------------------------------ card stages
    def pad_list(self, net):
        return [p for p in self.cop['pads'] if p['net'] == net]

    def stub_guide(self, net):
        """F / B only within STUB_R of the net's own pads; In5 anywhere (U2 In+, V_err)."""
        g = {5: np.ones((NY, NX), bool)}
        for l in (0, 7):
            m = np.zeros((NY, NX), bool)
            for p in self.pad_list(net):
                if LAYERS[l] in p['polys']:
                    for poly in p['polys'][LAYERS[l]]:
                        if not isinstance(poly, dict):
                            raster_poly(poly, m, True)
            if m.any():
                m = ndimage.distance_transform_edt(~m) * H - H / 2 <= STUB_R
            g[l] = m
        return g

    def reserved_escapes(self, net):
        """Cells within 1 mm of other nets' pads that sit inside an earlier sensitive zone: those pins' only way out,
        which a later sensitive net must not take (V_err once sealed U5.1 between Current and U2 In+)."""
        res = {}
        for l in ROUTE:
            m = np.zeros((NY, NX), bool)
            for p in self.cop['pads']:
                if p['net'] in (net, 'GND') or LAYERS[l] not in p['polys']:
                    continue
                i, j = cell(p['x'], p['y'])
                if not (0 <= i < NX and 0 <= j < NY):
                    continue
                if any(l in pr['track'] and pr['track'][l][0][j, i] < pr['zone'] + 0.5 and
                       (not (pr['logic_only'] or pr['track'][l][1]) or is_logic(p['net'])) for pr in self.prot):
                    for poly in p['polys'][LAYERS[l]]:
                        if not isinstance(poly, dict):
                            raster_poly_c(poly, m, True)
            res[l] = (ndimage.distance_transform_edt(~m) * H - H / 2 <= 1.0) if m.any() else m
        return res

    def route_sensitive(self, net, log):
        n = self.nid[net]
        if net == 'Net-(U2-In+)':
            self.guide = self.stub_guide(net)
        if self.prot:
            rsv = self.reserved_escapes(net)
            g = self.guide or {l: np.ones((NY, NX), bool) for l in ROUTE}
            self.guide = {l: g.get(l, np.ones((NY, NX), bool)) & ~rsv.get(l, np.zeros((NY, NX), bool)) for l in ROUTE}
        if net == 'V_err':
            # U2 In+ comes next and allows no via of another net within 2 mm of its copper: keep V_err's vias that far
            # from In+'s pads now (its tracks are free to pass: V_err is not a logic net)
            m = np.zeros((NY, NX), bool)
            for p in self.pad_list('Net-(U2-In+)'):
                for ln, polys in p['polys'].items():
                    for poly in polys:
                        if not isinstance(poly, dict):
                            raster_poly_c(poly, m, True)
            self.via_forbid = ndimage.distance_transform_edt(~m) * H - H / 2 < ZONES['Net-(U2-In+)'] + 0.3 + 0.08 + MARGIN
        if net == 'V_err':
            if self.guide is None:
                self.guide = {l: np.ones((NY, NX), bool) for l in ROUTE}
            if VERR_BLOCK_B:
                x0, y0, x1, y1 = VERR_BLOCK_B
                i0, j0 = cell(x0, y0)
                i1, j1 = cell(x1, y1)
                self.guide[7][j0:j1 + 1, i0:i1 + 1] = False
                vf = np.zeros((NY, NX), bool)
                vf[j0:j1 + 1, i0:i1 + 1] = True
                self.via_forbid = vf if self.via_forbid is None else (self.via_forbid | vf)
            # a GND plane under its whole length (user, 2026-09-23): keep clear of vias already placed (their antipads)
            fv = np.zeros((NY, NX), bool)
            for x in self.routes:
                if x[0] == 'via' and x[3] != n and self.nname[x[3]] != 'GND':
                    raster_disc(x[1], x[2], x[5] / 2, fv, True)
            if fv.any():
                far = ndimage.distance_transform_edt(~fv) * H - H / 2 >= 0.25 + 0.08 + MARGIN + VERR_PLANE_BAND
                self.guide = {l: (self.guide[l] if self.guide else np.ones((NY, NX), bool)) & far for l in ROUTE}
        if net == 'Net-(U2-In+)':
            # the user's rule read both ways: no via of another net within ZONE of its copper, so it keeps clear of
            # vias already placed (V_err's), not only the reverse
            fv = np.zeros((NY, NX), bool)
            for x in self.routes:
                if x[0] == 'via' and x[3] != n and self.nname[x[3]] != 'GND':
                    raster_disc(x[1], x[2], x[5] / 2, fv, True)
            if fv.any():
                far = ndimage.distance_transform_edt(~fv) * H - H / 2 >= ZONES[net] + 0.3 + 0.08 + MARGIN
                self.guide = {l: self.guide[l] & far for l in self.guide}
        self.direct = True
        try:
            f = self.route_net(net, log, allow_rip=False)
        finally:
            self.guide = None
            self.via_forbid = None
            self.direct = False
        # everything this net drew is kept through rip-ups
        self.keep |= {gkey(g) for g in self.routes if (g[5] if g[0] == 'track' else g[3]) == n}
        return f

    def build_protect(self, nets, log):
        """Distance fields round the sensitive nets' copper (pads, tracks, vias) for the keep-out rules. Built right
        after each sensitive net is routed, so the next sensitive net keeps the earlier ones' rules too."""
        parts = {}
        for p in self.cop['pads']:
            parts.setdefault(p['net'], set()).add(p['ref'])
        for net in nets:
            n = self.nid[net]
            own = {l: (self.hard[l] == n) for l in range(len(LAYERS))}
            track = {}
            for l in ROUTE:
                if net == 'Current' and l not in (4, 5, 7):
                    continue            # approved plan: B.Cu and In5 only (In4 too with --open-plan)
                m = own[l].copy()
                if net == 'Current' and l in (4, 5):
                    m |= own[7]         # approved plan: no other copper on B.Cu or In5 within 2 mm of the stubs
                if net == 'Net-(U2-In+)' and l == 4:
                    m |= own[5]         # --open-plan: In4 stays solid GND over the In5 run (user, 2026-09-24)
                if l in (4, 5) and net in ('Net-(U2-In+)', 'Current'):
                    # the net's via barrels pass through In4 / In5 even where their ring is removed: they count as
                    # its copper there (a track came to 1.85 mm of an In+ stub via's barrel, 2026-09-24)
                    for x in self.routes:
                        if x[0] == 'via' and x[3] == n:
                            raster_disc(x[1], x[2], x[5] / 2, m, True)
                if m.any():
                    # U2 In+ pad stubs on F / B: no logic net within ZONE (user: no logic net parallel to it); its In5
                    # run: no other net at all (the GND guard fills the band). Current: no other net (approved plan).
                    # V_err: logic nets only, every layer.
                    lo = net == 'V_err' or (net == 'Net-(U2-In+)' and l in (0, 7))
                    track[l] = ((ndimage.distance_transform_edt(~m) * H - H / 2).astype(np.float32), lo)
            plan = np.zeros((NY, NX), bool)
            for l in range(len(LAYERS)):
                plan |= own[l]
            via = (ndimage.distance_transform_edt(~plan) * H - H / 2).astype(np.float32)
            refs = parts.get(net, set())
            exempt = set()
            # nets whose own pads already sit inside the zone cannot keep out of it: they may escape from those pads
            for p in self.cop['pads']:
                if p['net'] not in self.nid:
                    continue
                for ln in p['polys']:
                    l = LI[ln]
                    if l in track:
                        i, j = cell(p['x'], p['y'])
                        if 0 <= i < NX and 0 <= j < NY and track[l][0][j, i] < ZONES[net] + 0.5:
                            exempt.add(self.nid[p['net']])
            exempt -= {n}
            self.prot.append(dict(nid=n, name=net, track=track, via=via, logic_only=(net == 'V_err'), exempt=exempt,
                                  zone=ZONES[net]))
            if net == 'V_err':
                # user, 2026-09-23: a GND plane under V_err's whole length, so no via of any other net under it
                # (each would leave an antipad in In1 / In6 below the track)
                self.prot.append(dict(nid=n, name='V_err plane', track={}, via=via, logic_only=False, exempt=set(),
                                      zone=VERR_PLANE_BAND))
            log.append('prot %-16s track zone on %s, via zone all layers; %d nets exempt in the track zone%s' % (
                net, '/'.join(LAYERS[l] for l in sorted(track)), len(exempt),
                ' (logic nets only)' if net == 'V_err' else ''))

    def escape_mask(self, n, l):
        key = (n, l)
        if not hasattr(self, '_esc'):
            self._esc = {}
        if key not in self._esc:
            m = np.zeros((NY, NX), bool)
            for p in self.cop['pads']:
                if self.nid.get(p['net']) == n and LAYERS[l] in p['polys']:
                    for poly in p['polys'][LAYERS[l]]:
                        if not isinstance(poly, dict):
                            raster_poly_c(poly, m, True)
            self._esc[key] = (ndimage.distance_transform_edt(~m) * H - H / 2 <= ESCAPE_R) if m.any() else m
        return self._esc[key]

    def via_ok(self, n, vdia, vdrill):
        """Where a through via of net N (all layers flashed) is legal, over the whole board."""
        net = self.nname[n]
        cN = rules_for(net, self.classes)['clr']
        bb = (0, NY, 0, NX)
        ok = ndimage.distance_transform_edt(~(self.holes >= 0)) * H - H / 2 >= vdrill / 2 + HOLE_HOLE + MARGIN
        ok &= ~self.keep_vias
        ok &= self.edge_dist >= vdia / 2 + EDGE_CLR + MARGIN
        for l in range(len(LAYERS)):
            ok &= ~self.blocked_layer(n, l, bb, vdia / 2, cN, items_only=True)
        return ok

    def stitch(self, log):
        """GND vias beside the U2 In+ run on In5 and beside the Current stubs on B.Cu, both sides, every STITCH_PITCH
        mm where a via fits; the GND fill between them and the sensitive track is the guard."""
        g = self.nid['GND']
        vdia, vdrill = CLASS['Power']['via']
        ok = self.via_ok(g, vdia, vdrill)
        placed = []
        for net, layer in (('Net-(U2-In+)', 5), ('Current', 7), ('V_err', 5)):
            n = self.nid[net]
            segs = [x for x in self.routes if x[0] == 'track' and x[5] == n and x[6] == layer]
            cnt = 0
            for (_, x0, y0, x1, y1, _, _, w) in segs:
                L = math.hypot(x1 - x0, y1 - y0)
                if L < 1e-6:
                    continue
                ux, uy = (x1 - x0) / L, (y1 - y0) / L
                nxv, nyv = -uy, ux
                k = max(1, int(L / STITCH_PITCH))
                for t in np.linspace(0, L, k + 1):
                    px, py = x0 + ux * t, y0 + uy * t
                    for side in (1, -1):
                        for off in [w / 2 + 0.25 + vdia / 2 + 0.05 + 0.15 * k for k in range(9)]:     # 0.7 .. 1.9 mm
                            vx, vy = px + side * off * nxv, py + side * off * nyv
                            i, j = cell(vx, vy)
                            if not (0 <= i < NX and 0 <= j < NY) or not ok[j, i]:
                                continue
                            if any(math.hypot(vx - a, vy - b) < STITCH_PITCH * 0.8 for a, b in placed):
                                break
                            # the via must not touch the sensitive track itself on any layer (checked by ok) and must
                            # keep GND clearance from it: ok already includes that
                            vx, vy = X0 + (i + 0.5) * H, Y0 + (j + 0.5) * H
                            geom = ('via', vx, vy, g, [0, 7], vdia, vdrill)
                            self.restore([geom])
                            self.keep.add(gkey(geom))
                            placed.append((vx, vy))
                            cnt += 1
                            ok = self.via_ok(g, vdia, vdrill) if cnt % 8 == 0 else ok & ~self._disc(vx, vy, vdia + HOLE_HOLE + 0.1)
                            break
            log.append('stch %-16s %d GND vias beside its %s run' % (net, cnt, LAYERS[layer]))
        # a thermal-relief pad (J9.10): GND vias just outside its spokes, so the fill its spokes reach on every layer is
        # tied to the planes by a via of its own, not only through the pad (DRC: starved thermal / isolated island)
        ok = self.via_ok(g, vdia, vdrill)
        for ref, num, r in SPOKE_KEEP:
            pad = [p for p in self.cop['pads'] if p['ref'] == ref and p['num'] == num][0]
            got = []
            for dx, dy in ((0, 1), (-0.707, 0.707), (0.707, 0.707), (-1, 0), (1, 0), (0, -1)):
                for rr in (r, r + 0.3, r + 0.6):
                    vx, vy = pad['x'] + dx * rr, pad['y'] + dy * rr
                    i, j = cell(vx, vy)
                    if not ok[j, i] or any(math.hypot(vx - a, vy - b) < 1.5 for a, b in got):
                        continue
                    vx, vy = X0 + (i + 0.5) * H, Y0 + (j + 0.5) * H
                    geom = ('via', vx, vy, g, [0, 7], vdia, vdrill)
                    self.restore([geom])
                    self.keep.add(gkey(geom))
                    got.append((vx, vy))
                    ok = ok & ~self._disc(vx, vy, vdia + HOLE_HOLE + 0.1)
                    break
                if len(got) >= 2:
                    break
            log.append('stch %s.%-13s %d GND vias beside the thermal-relief pad' % (ref, num, len(got)))

    def _disc(self, x, y, r):
        m = np.zeros((NY, NX), bool)
        raster_disc(x, y, r, m, True)
        return m

    def decap_links(self, match, log):
        """Direct link from each IC supply pin to its placement-matched capacitor when both sit on the same side."""
        side = {}
        for p in self.cop['pads']:
            if p['drill'] == 0:
                side[p['ref']] = 'F' if 'F.Cu' in p['polys'] else 'B'
        pxy = {(p['ref'], p['num']): (p['x'], p['y']) for p in self.cop['pads']}
        net_of = {(p['ref'], p['num']): p['net'] for p in self.cop['pads']}
        done = 0
        self.protect_flag_old = self.protect
        self.protect = True
        try:
            for ic_pin, cap_pin in match.items():
                ic, ipn = ic_pin.split('.')
                cap, cpn = cap_pin.split('.')
                if side.get(ic) != side.get(cap) or (ic, ipn) not in net_of:
                    continue
                net = net_of[(ic, ipn)]
                straight = math.hypot(pxy[(ic, ipn)][0] - pxy[(cap, cpn)][0], pxy[(ic, ipn)][1] - pxy[(cap, cpn)][1])
                if self.route_pad_edge(net, (cap, cpn), (ic, ipn), log, direct=True, hide_fill=(net in PLANE_TARGET),
                                       tag='dcap', max_len=max(3.0, 2.0 * straight)):
                    done += 1
        finally:
            self.protect = self.protect_flag_old
        return done

    def fanout_signals(self, log, max_len=1.2, local=3.0):
        """Escape vias first (dense double-sided card): every SMD pad of a signal net that has no pad of its own net on
        the same side within LOCAL mm gets a via to its inner layer (In2 logic, In5 analog), in the pad where legal,
        else within MAX_LEN mm, before any signal track is laid. Pads in the most crowded spots go first. The via's
        inner end is left for route_net to join; one that stays unused is pruned as dangling afterwards."""
        pads = [p for p in self.cop['pads'] if p['drill'] == 0 and p['net'] in self.nid and
                p['net'] not in ('GND', '5V') and p['net'] not in SENS and p['net'] not in RAILS and
                not p['net'].startswith('unconnected')]
        bynet = {}
        for p in pads:
            bynet.setdefault(p['net'], []).append(p)
        side = lambda p: 0 if 'F.Cu' in p['polys'] else 7
        todo = []
        for net, ps in bynet.items():
            allp = [q for q in self.cop['pads'] if q['net'] == net]
            if len(allp) < 2:
                continue
            for p in ps:
                near = [q for q in allp if q is not p and q['drill'] == 0 and side(q) == side(p) and
                        math.hypot(q['x'] - p['x'], q['y'] - p['y']) <= local]
                if near:
                    continue
                crowd = sum(1 for q in self.cop['pads'] if q['net'] != net and
                            math.hypot(q['x'] - p['x'], q['y'] - p['y']) < 2.0)
                todo.append((-crowd, net, p))
        todo.sort(key=lambda t: (t[0], t[1]))
        done = skipped = 0
        for _, net, p in todo:
            n = self.nid[net]
            l = side(p)
            inner = 2 if is_logic(net) else 5
            # this pad must not already have a via of its net within reach (an earlier route or decap link)
            have = [g for g in self.routes if g[0] == 'via' and g[3] == n and
                    math.hypot(g[1] - p['x'], g[2] - p['y']) < max_len + 0.5]
            if have:
                continue
            padm = np.zeros((NY, NX), bool)
            for poly in p['polys'][LAYERS[l]]:
                if not isinstance(poly, dict):
                    raster_poly_c(poly, padm, True)
            if not padm.any():
                continue
            ci, cj = cell(p['x'], p['y'])
            ext = int(round((max_len + 1.0) / H))
            win = (max(cj - ext, 0), min(cj + ext, NY), max(ci - ext, 0), min(ci + ext, NX))
            target = np.zeros((NY, NX), bool)
            target[win[0]:win[1], win[2]:win[3]] = True
            lab_own, _ = ndimage.label(self.own_mask(n, l), structure=np.ones((3, 3)))
            island = lab_own == lab_own[cj, ci] if lab_own[cj, ci] > 0 else padm
            labels = {l: (padm & island).astype(np.int32), inner: target.astype(np.int32)}
            self.free_own = {l: island}
            try:
                res = self.route_edge(n, [(inner, 1)], [(l, 1)], labels, window=win)
            finally:
                self.free_own = None
            if res is None:
                skipped += 1
                continue
            path, ru = res
            ln_mm = sum(H * math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(path, path[1:]) if a[0] == b[0])
            if ln_mm > max_len or not any(a[0] != b[0] for a, b in zip(path, path[1:])):
                skipped += 1
                continue
            # keep only the pad-side part and the via: drop any inner-layer run beyond the via cell
            k = next(i for i in range(len(path) - 1) if path[i][0] != path[i + 1][0])
            self.commit(n, path[:k + 2], ru)
            done += 1
        log.append('fan  signals          %d escape vias, %d pads without a via site within %.1f mm' % (
            done, skipped, max_len))
        return done, skipped

    def fanout(self, net, planes, log, max_len=2.0, near=0.6, only=None):
        """Give every SMD pad of NET on F/B its own via to the planes, unless a barrel of the net already lies
        within NEAR mm of the pad. The net's fills on the routing layers are hidden while doing it (they yield and are
        refilled), so a pad counts as its own island; a stub longer than MAX_LEN mm is not committed."""
        n = self.nid[net]
        self.hidden_yld = [y.copy() for y in self.yld]
        for l in [x for x in ROUTE if x not in planes]:      # the planes themselves stay
            self.yld[l][self.yld[l] == n] = -1
        done = skipped = 0
        try:
            plane_labels, A = {}, []
            for pl in planes:
                lab, k = ndimage.label(self.own_mask(n, pl), structure=np.ones((3, 3)))
                if k:
                    plane_labels[pl] = lab
                    A.append((pl, int(np.argmax(np.bincount(lab.ravel())[1:])) + 1))
            for p in self.cop['pads']:
                if self.nid[p['net']] != n or p['drill'] > 0:
                    continue
                if only is not None and '%s.%s' % (p['ref'], p['num']) not in only:
                    continue
                for ln, polys in p['polys'].items():
                    l = LI[ln]
                    if l not in (0, 7):
                        continue
                    pts = [q for poly in polys if not isinstance(poly, dict) for q in poly]
                    xa, xb = min(q[0] for q in pts) - near, max(q[0] for q in pts) + near
                    ya, yb = min(q[1] for q in pts) - near, max(q[1] for q in pts) + near
                    have = [b for b in self.barrels if b[2] == n and xa <= b[0] <= xb and ya <= b[1] <= yb]
                    have += [g for g in self.routes if g[0] == 'via' and g[3] == n and xa <= g[1] <= xb and ya <= g[2] <= yb]
                    if have:
                        continue
                    lab, _ = ndimage.label(self.own_mask(n, l), structure=np.ones((3, 3)))
                    i, j = cell(p['x'], p['y'])
                    if lab[j, i] == 0:
                        continue
                    island = lab == lab[j, i]
                    padm = np.zeros((NY, NX), bool)
                    for poly in polys:
                        if not isinstance(poly, dict):
                            raster_poly(poly, padm, True)
                    labels = dict(plane_labels)
                    labels[l] = (padm & island).astype(np.int32)
                    B = [(l, 1)]
                    self.free_own = {l: island}
                    ci, cj = cell(xa, ya), cell(xb, yb)
                    ext = int(round(max_len / H)) + 10
                    win = (max(ci[1] - ext, 0), min(cj[1] + ext, NY), max(ci[0] - ext, 0), min(cj[0] + ext, NX))
                    try:
                        res = self.route_edge(n, A, B, labels, window=win)
                        if res is None and small_via_ok(net):
                            res = self.route_edge(n, A, B, labels, small_via=True, window=win)
                    finally:
                        self.free_own = None
                    if res is None:
                        log.append('fan  %-16s %s.%s: no via reachable' % (net, p['ref'], p['num']))
                        skipped += 1
                        continue
                    path, ru = res
                    ln_mm = sum(H * math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(path, path[1:])
                                if a[0] == b[0] and a[0] in ROUTE)
                    px0, px1 = xa + near, xb - near
                    py0, py1 = ya + near, yb - near
                    for a, b in zip(path, path[1:]):
                        if a[0] != b[0]:
                            vx, vy = X0 + (a[2] + 0.5) * H, Y0 + (a[1] + 0.5) * H
                            ln_mm = max(ln_mm, math.hypot(max(px0 - vx, 0, vx - px1), max(py0 - vy, 0, vy - py1)))
                    if ln_mm > max_len:
                        log.append('fan  %-16s %s.%s: nearest via needs %.1f mm, not fanned out' % (net, p['ref'], p['num'], ln_mm))
                        skipped += 1
                        continue
                    self.commit(n, path, ru)
                    done += 1
                    log.append('fan  %-16s %s.%s: %.1f mm stub, via %.1f/%.1f' % (net, p['ref'], p['num'], ln_mm, *ru['via']))
        finally:
            for l in ROUTE:
                keep = self.hidden_yld[l] == n
                self.yld[l][keep] = n
            self.hidden_yld = None
        return done, skipped

    def route_net(self, net, log, allow_rip=True, partner_override=None):
        n = self.nid[net]
        partner = self.nid[PAIRS[net]] if net in PAIRS else None
        if partner_override is not None:
            partner = self.nid[partner_override]
        failed = set()
        t_net = time.time()
        fails = 0
        for attempt in range(80):
            isl, labels = self.islands(n)
            if len(isl) <= 1:
                return fails
            proj, keys = [], []
            for members in isl:
                m = np.zeros((NY, NX), bool)
                for (l, k) in members:
                    m |= labels[l] == k
                proj.append(m)
                keys.append(int(np.flatnonzero(m)[0]))
            cands = []
            if net in STAR:
                big = int(np.argmax([m.sum() for m in proj]))
                db = ndimage.distance_transform_edt(~proj[big]) * H
                for b in range(len(proj)):
                    key = (min(keys[big], keys[b]), max(keys[big], keys[b]))
                    if b != big and key not in failed and (keys[big], keys[b]) not in failed and (keys[b], keys[big]) not in failed:
                        cands.append((float(db[proj[b]].min()), min(big, b), max(big, b)))
            for a in (range(len(proj)) if not cands else []):
                da = ndimage.distance_transform_edt(~proj[a]) * H
                for b in range(a + 1, len(proj)):
                    if (keys[a], keys[b]) in failed:
                        continue
                    cands.append((float(da[proj[b]].min()), a, b))
                if a == 0 and len(proj) > 12:
                    break           # large nets (plane fan-outs): pair everything with island 0 only
            if not cands:
                return fails
            cands.sort()
            dist, a, b = cands[0]
            res = self.try_edge(n, isl[a], isl[b], labels, partner)
            if res is None and allow_rip and RIPUP and time.time() - t_net < RIP_BUDGET_S:
                small = proj[a] if proj[a].sum() <= proj[b].sum() else proj[b]
                if self.ripup_edge(n, isl[a], isl[b], labels, partner, small, log) or self.ripup_edge(
                        n, isl[a], isl[b], labels, partner, small, log, radius=2 * RIP_RADIUS, max_nets=2 * RIP_MAX):
                    continue
                ghost = self.ghost_blockers(n, isl[a], isl[b], labels, partner)
                if ghost and self.ripup_edge(n, isl[a], isl[b], labels, partner, small, log, blockers=ghost):
                    continue
            if res is None and allow_rip and self.jcut:
                self.hot_ok = True
                try:
                    res = self.try_edge(n, isl[a], isl[b], labels, partner)
                finally:
                    self.hot_ok = False
                if res is not None and 'hot' in res[1]:
                    hs = res[1]['hot']
                    log.append('HOT  %-16s crosses power copper over %.1f mm, up to %.2f A/mm on %s at (%.2f, %.2f)' % (
                        net, hs['cells'] * H, hs['max_A_per_mm'], hs['layer'], hs['x'], hs['y']))
            if res is None:
                log.append('FAIL %s: island %d (%d cells; %s) to island %d (%s), gap %.1f mm' % (
                    net, a, int(proj[a].sum()), self.island_pads(n, isl[a], labels), b, self.island_pads(n, isl[b], labels), dist))
                failed.add((keys[a], keys[b]))
                fails += 1
                continue
            path, ru = res
            g = self.commit(n, path, ru)
            nv = sum(1 for x in g if x[0] == 'via')
            ln = sum(math.hypot(x[3] - x[1], x[4] - x[2]) for x in g if x[0] == 'track')
            log.append('ok   %-16s %5.1f mm, %d via(s)%s, w %.2f, gap %.1f' % (
                net, ln, nv, ' %.1f/%.1f' % ru['via'] if nv else '', ru['w'], dist))
        return fails



def hpwl(cop, net):
    ps = [(p['x'], p['y']) for p in cop['pads'] if p['net'] == net]
    if len(ps) < 2:
        return 0.0
    xs, ys = [p[0] for p in ps], [p[1] for p in ps]
    return max(xs) - min(xs) + max(ys) - min(ys)


def build_order(cop, first=()):
    nets = sorted({p['net'] for p in cop['pads'] if p['net'] and not p['net'].startswith('unconnected')})
    rest = [n for n in nets if n not in SENS and n not in RAILS and n not in ('GND', '5V')]
    # longest first: long nets need the inner layers, short local links fit on F / B afterwards
    analog = sorted([n for n in rest if n in ANALOG], key=lambda n: -hpwl(cop, n))
    logic = sorted([n for n in rest if n not in ANALOG], key=lambda n: -hpwl(cop, n))
    analog = [n for n in analog if n not in EARLY]
    # negotiation by priority (--first): nets that failed in earlier passes go right after the stitching and the
    # decoupling links, ahead of the plane fan-outs and everything else
    first = [n for n in first if n in rest and n not in EARLY]
    analog = [n for n in analog if n not in first]
    logic = [n for n in logic if n not in first]
    # V_err after the other comparator inputs: its long route (forced round U2 In+) otherwise splits their dividers
    sens = ['SENS:Current', 'SENS:Net-(U2-In+)'] + (['SENS:V_err'] + [n for n in EARLY if n in nets] if not VERR_LATE else
                                                     [n for n in EARLY if n in nets] + ['SENS:V_err'])
    return (sens + ['STITCH', 'DECAP'] + first +
            ['FANOUT:GND', 'FANOUT:5V', 'FANOUT:signals', 'analog_5V', '12V'] + analog + logic + ['5V', 'GND'])


ORDER = []


def main():
    a = sys.argv[1:]
    cop = json.load(open(a[0]))
    out = a[1]
    only = a[a.index('--nets') + 1].split(',') if '--nets' in a else None
    skip = set(a[a.index('--skip') + 1].split(',')) if '--skip' in a else set()
    global RIPUP, ORDER, LOGIC_IN3, FANOUT_SIGNALS, VERR_LATE, MIXED_INNER
    VERR_LATE = '--verr-late' in a
    RIPUP = '--no-rip' not in a
    FANOUT_SIGNALS = '--no-fanout-signals' not in a
    LOGIC_IN3 = '--logic-in3' in a
    MIXED_INNER = '--mixed-inner' in a
    if '--open-plan' in a:
        set_open_plan()
    if '--no-in3' in a:
        NO_IN3.update(a[a.index('--no-in3') + 1].split(','))
    global VERR_BLOCK_B
    if '--no-verr-block' in a:        # the U4 In+ divider block is placement c3's; placement c2 has no such crossing
        VERR_BLOCK_B = None
    global RIP_BUDGET_S, PAD_CLR_MIN
    if '--default-clr' in a:          # what-if only: the shipped file's 0.15 (KiCad 10 enforces 0.20, see NOTE)
        CLASS['Default']['clr'] = float(a[a.index('--default-clr') + 1])
        PAD_CLR_MIN = min(PAD_CLR_MIN, CLASS['Default']['clr'])
    if '--rip-budget' in a:
        RIP_BUDGET_S = float(a[a.index('--rip-budget') + 1])
    global RIP_RADIUS, RIP_MAX
    if '--rip-radius' in a:           # finishing passes: rip up farther and more nets than the repair rounds do
        RIP_RADIUS = float(a[a.index('--rip-radius') + 1])
    if '--rip-max' in a:
        RIP_MAX = int(a[a.index('--rip-max') + 1])
    if LOGIC_IN3:
        LAYER_COST[3] = 1.25
    match = json.load(open(a[a.index('--match') + 1]))['match'] if '--match' in a else {}
    t0 = time.time()
    if '--zones' in a:
        cop['zones'] = json.load(open(a[a.index('--zones') + 1]))['zones']
    bd = Board(cop)
    log = ['board rasterised in %.1f s' % (time.time() - t0)]
    loaded = '--routes' in a
    if loaded:
        rt = json.load(open(a[a.index('--routes') + 1]))
        if '--unkeep' in a:
            # finishing passes: these pre-routed nets (zone nets, other comparator inputs) may be ripped and re-routed;
            # the sensitive nets and GND always stay fixed, and every keep-out still applies to the re-route
            free = set(a[a.index('--unkeep') + 1].split(',')) - set(SENS) - {'GND'}
            for item in rt['tracks'] + rt['vias']:
                if item['net'] in free:
                    item['keep'] = False
        bd.load_routes(rt)
        log.append('loaded %d committed route items' % len(bd.routes))
    first = [x for x in open(a[a.index('--first') + 1]).read().split() if x] if '--first' in a else []
    ORDER = [x[5:] if x.startswith('SENS:') else x for x in build_order(cop, first)]
    # the sensitive nets always run (loaded, they only rebuild their keep-out zones): a --nets pass without them
    # routed with no zones at all (2026-09-24, finishing pass c: vias inside the U2 In+ / Current 2 mm zones)
    order = [x for x in build_order(cop, first) if (only is None or x in only or x[5:] in only or
                                                   x.startswith('SENS:')) and x not in skip]
    if first:
        log.append('first: %d nets from earlier passes routed ahead of the plane fan-outs' % len(first))
    if '--pre' in a:
        # pre-route for Freerouting (user, 2026-09-23): what Freerouting must not touch, locked afterwards
        keep = ('SENS:', 'STITCH', 'DECAP', 'FANOUT:GND', 'FANOUT:5V')
        order = [x for x in order if x.startswith(keep) or x in EARLY] + ['ZONENETS']
        log.append('pre-route mode: sensitive nets, other comparator inputs, stitching, decoupling links, plane '
                   'fan-outs, then every net with a pin inside a sensitive zone')
    total_fail = 0
    shown = 0
    for step in order:
        t1 = time.time()
        if step.startswith('SENS:'):
            f = bd.route_sensitive(step[5:], log)
            bd.build_protect([step[5:]], log)
            total_fail += f
            log.append('     %-16s sensitive, %.1f s%s' % (step[5:], time.time() - t1, (' (%d failed)' % f) if f else ''))
        elif step == 'STITCH':
            if not loaded:
                bd.stitch(log)
        elif step == 'DECAP':
            if not loaded:
                k = bd.decap_links(match, log)
                log.append('     DECAP            %d direct links, %.1f s' % (k, time.time() - t1))
        elif step == 'ZONENETS':
            names = sorted({bd.nname[x] for pr in bd.prot for x in pr['exempt']} - {'GND', '5V'} - set(SENS) - set(EARLY))
            names = [x for x in names if not x.startswith('unconnected')]
            log.append('zone nets (%d): %s' % (len(names), ' '.join(names)))
            for net in names:
                total_fail += bd.route_net(net, log)
        elif step == 'FANOUT:signals':
            if not loaded and FANOUT_SIGNALS:
                bd.fanout_signals(log)
        elif step.startswith('FANOUT:'):
            net = step[7:]
            bd.direct = True
            bd.protect_flag = bd.protect
            bd.protect = True
            try:
                # own plane vias for capacitor and IC pins only (the decoupling loops); resistor and diode pads join
                # the plane later through the fill or a short route, which keeps ~30 through vias out of In2 / In5
                only = {'%s.%s' % (p['ref'], p['num']) for p in cop['pads'] if p['net'] == net and p['ref'][0] in 'CUQ'}
                done, skipped = bd.fanout(net, PLANE_TARGET[net], log, max_len=1.5, only=only)
            finally:
                bd.direct = False
                bd.protect = bd.protect_flag
            log.append('     %-16s %d vias, %d pads skipped, %.1f s' % (step, done, skipped, time.time() - t1))
        else:
            f = bd.route_net(step, log)
            total_fail += f
            log.append('     %-16s done in %.1f s%s' % (step, time.time() - t1, (' (%d failed)' % f) if f else ''))
        print('\n'.join(log[shown:]), flush=True)
        shown = len(log)
    tracks, vias = [], []
    seen = set()
    for g in bd.routes:
        key = tuple(round(x, 3) if isinstance(x, float) else (tuple(x) if isinstance(x, list) else x) for x in g)
        if key in seen:
            continue
        seen.add(key)
        if g[0] == 'track':
            _, x0, y0, x1, y1, n, l, w = g
            tracks.append(dict(net=bd.nname[n], layer=LAYERS[l], w=w, x0=round(x0, 3), y0=round(y0, 3),
                               x1=round(x1, 3), y1=round(y1, 3)))
            if gkey(g) in bd.keep:
                tracks[-1]['keep'] = True
        else:
            _, x, y, n, ls, dia, drill = g
            vias.append(dict(net=bd.nname[n], x=round(x, 3), y=round(y, 3), dia=dia, drill=drill,
                             layers=[LAYERS[l] for l in ls]))
            if gkey(g) in bd.keep:
                vias[-1]['keep'] = True
    json.dump(dict(tracks=tracks, vias=vias, log=log, failures=total_fail), open(out, 'w'), indent=1)
    print('tracks %d, vias %d, failures %d, %.0f s' % (len(tracks), len(vias), total_fail, time.time() - t0))


if __name__ == '__main__':
    main()
