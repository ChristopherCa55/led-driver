"""Grid router for the BOOST power board signals (system Python: numpy, scipy, matplotlib).

usage: python route_signals.py COPPER.json OUT_ROUTES.json [--nets a,b,...] [--skip a,b] [--no-via-in-pad] [--no-rip]
                              [--routes EARLIER_ROUTES.json] [--zones ROUTED_BOARD_COPPER.json] [--jmap SHEET.npz]
With --routes the earlier routes are committed first (and may be ripped up); the output then holds all routes.
With --zones every zone shape comes from that export (the refilled routed board) instead of COPPER.json.

Reads the copper export of a board whose power copper is fixed (export_copper.py), finds each net's copper
islands (layers joined through its own barrels), joins them with a minimum spanning tree, and routes every tree
edge on a 0.1 mm grid over F.Cu, In2, In3, In5 and B.Cu (In1/In6 are GND only, In4 is the 5 V plane) with
Dijkstra. Obstacles are other nets' pads, vias, tracks and non-yielding zone fills grown by
track half-width + clearance + margin, other nets' holes grown by the 0.2 mm hole clearance, keep-outs and the
board edge (0.3 mm). GND fill (zone priority <= 1) yields and is refilled afterwards. Vias must clear copper on
all eight layers and every hole by 0.25 mm. The 5 V net may land on the In4 plane, GND on In1/In6.
Output: tracks and vias, added to the board by add_routes.py.
"""
import json, math, sys, time
import numpy as np
from scipy import ndimage
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
from matplotlib.path import Path
from PIL import Image, ImageDraw

H = 0.1
X0, Y0 = 29.0, 29.0
NX, NY = 770, 890
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu', 'B.Cu']
LI = {n: i for i, n in enumerate(LAYERS)}
ROUTE = [0, 2, 3, 5, 7]
MARGIN = 0.06
HOLE_CLR = 0.20
HOLE_HOLE = 0.25
EDGE_CLR = 0.30
PAD_VIA_GAP = 0.10        # with --no-via-in-pad: via copper to the edge of an SMD pad of the same net
NO_VIA_IN_PAD = False     # default allows via-in-pad, as the step-5 power copper already does (415 vias in pads), so the
                          # board needs filled and capped vias either way; routing this placement without it fails 29 edges
OWN_GAP = 0.10            # new copper keeps this gap from the net's other islands unless it lands inside them (KiCad
                          # joins items only when an anchor lies inside the other shape, not when edges merely touch)
EXT = 20                  # cells: distance fields see obstacles this far outside the routing window (2 mm)
VIA_COST = 1.6            # mm-equivalent per via
VIA_POUR = 3.0            # added per power pour the via's hole passes near (keeps signal vias out of the pours)
VIA_POUR_PAIR = 0.3       # the same for a Kelvin sense pair: a via pair that lets the pair cross beats a loop round R1
LAYER_COST = {0: 1.0, 2: 1.25, 3: 1.25, 5: 1.1, 7: 1.0}

CLASS = {  # clearance from the project netclasses; w = the netclass track width where it fits (Power: the DRU
           # minimum, 2.0 mm stubs into small pads make no sense), wmin = the fallback when an edge does not fit at w
    'Default': dict(clr=0.15, w=0.20, wmin=0.20, via=(0.6, 0.3)),
    'Sense': dict(clr=0.20, w=0.20, wmin=0.20, via=(0.6, 0.3)),
    'Gate': dict(clr=0.20, w=0.50, wmin=0.30, via=(0.6, 0.3)),
    'Rail': dict(clr=0.20, w=0.80, wmin=0.40, via=(0.6, 0.3)),
    'Power': dict(clr=0.25, w=0.50, wmin=0.50, via=(0.8, 0.4)),
}
HIGH_CURRENT = {'Vin', 'rsense_lo', 'LX', 'm2_source', 'm3_source', 'm4_source', 'Vout_1', 'Vout_2', 'Vout_3',
                'Output1_drain', 'Output2_drain', 'Output3_drain', 'Net-(M8-S)', 'Net-(M9-S)', 'Net-(M10-S)'}
QUIET = {'ISNS_P', 'ISNS_N', 'SNS_CH1', 'SNS_CH2', 'SNS_CH3', 'IREF1_input', 'IREF2_input', 'IREF3_input',
         'Current', 'analog_5V'}
# Power-current protection (--jmap, from solve_copper.py on the unrouted power copper). S is the solved sheet current
# (A/mm), spread by JCUT_R (tracks) or JVIA_R (vias) so the whole cut, not just its centre line, is judged.
# A track cuts a strip of pour: not allowed across another net's pour or fill where S > J_FORBID, and each crossing
# cell costs (1 + S / J_REF). A via only cuts a ~1.3 mm disc: not allowed where S > J_FORBID_VIA on any layer it
# cuts, and it costs S / J_REF_VIA per layer below that.
J_FORBID = 0.25          # calibrated on v11: the pour spots that the unprotected routing damaged carry 0.41-1.5 A/mm
J_REF = 0.08
J_FORBID_VIA = 2.0       # a via hole in a wide pour doubles the current density at its rim but barely changes the
J_REF_VIA = 0.5          # branch resistance; at 1.0 A/mm no via could leave U19 or U25 (every inner layer is Vin/rsense)
JCUT_R = 0.6
JVIA_R = 0.8
RIPUP = True              # on a failed edge, rip up nearby routes of other nets and try again (see ripup_edge)
RIP_RADIUS = 2.0          # mm round the smaller island in which other nets' routes count as blockers
RIP_MAX = 4               # at most this many nets are ripped for one edge
RIP_PROTECT = {'GND', 'ISNS_P', 'ISNS_N'}   # never ripped: plane stitching, the Kelvin pair (gate loops added below)
FP_COPPER = '<footprint copper>'   # pseudo net of footprint copper graphics
PAD_CLR_MIN = 0.20        # DRC applies 0.2 mm to pads ("local override": J10's THT pads, U10's SMD pads); all pads
SRC_WIDTH_TEST = None     # what-if: source-net track width override (--src-width MM); None in real runs
LOOP_MODE = 'legs'        # gate loops: 'corridor' (return first, room kept beside it) or 'legs' (see LOOP_DRIVE_FIRST)
LOOP_CORRIDOR = 1.2       # mm of extra width kept free while routing a gate-loop return
LOOP_VIA_MULT = 4.0       # gate-loop drive legs: via cost multiplier
LOOP_DRIVE_FIRST = True   # gate loops: drive track first, return beside it (False: return first, drive beside)
LOOP_RETURN_FIRST = {'M6', 'M3'}   # U10's loops: return first, drive beside it (plan-view loop area 17-21 % smaller)
PAIR_ATTRACT = 0.15       # cost factor in the band beside a gate loop's return track
# Gate loops (user, 2026-09-17): FET -> (driver, OUT pin, VSS pin, gate net, drive net, source net); routed in this
# order: LX-side 5 ohm FETs first, then the rail FETs whose turn-off diodes put the drive track in the hold-off path
# The last field is the drive leg paired with the return: the 5 ohm series resistor on the LX side, the turn-off
# diode's cathode on the rail side (the diode bypasses the 220 ohm, so that leg is the hold-off path).
GATE_LOOPS = {
    'M7': ('U15', '10', '9', 'GATE_M7', 'Net-(D2--)', 'm2_source', ('R60', '1')),
    'M5': ('U8', '10', '9', 'GATE_M5', 'Net-(D22--)', 'm4_source', ('R59', '2')),
    'M6': ('U10', '10', '9', 'GATE_M6', 'Net-(D8--)', 'm3_source', ('R70', '1')),
    'M2': ('U15', '15', '14', 'GATE_M2', 'Net-(D11--)', 'm2_source', ('D11', '1')),
    'M3': ('U10', '15', '14', 'GATE_M3', 'Net-(D14--)', 'm3_source', ('D14', '1')),
    'M4': ('U8', '15', '14', 'GATE_M4', 'Net-(D13--)', 'm4_source', ('D13', '1')),
}
DIRECT_NETS = {'GATE_M1', 'Net-(M8-G)', 'Net-(M9-G)', 'Net-(M10-G)'}   # other gate-pin links, routed direct
# Bypass links (user, 2026-09-17), routed direct right after the sense nets: (net, capacitor pad, IC pin, partner)
BYPASS_EDGES = [
    ('12V', ('C31', '1'), ('U19', '16'), None),
    ('GND', ('C31', '2'), ('U19', '14'), '12V'),
    # C51 sits beside pins 14-16: the C86 pad above it rules out a via, the Vout_1 via row blocks the 1.0 mm source
    # track along the pin row, so it ties to the same nets' pins 14 and 16; pins 9 and 11 reach it through the source
    # return and the VDDA net (decision reported, 2026-09-17)
    ('m2_source', ('C51', '2'), ('U15', '14'), None),
    ('Net-(U15-VDDA)', ('C51', '1'), ('U15', '16'), 'm2_source'),
    ('m3_source', ('C50', '2'), ('U10', '9'), None),
    ('Net-(U10-VDDA)', ('C50', '1'), ('U10', '11'), 'm3_source'),
    ('m4_source', ('C61', '2'), ('U8', '9'), None),
    ('Net-(U8-VDDA)', ('C61', '1'), ('U8', '11'), 'm4_source'),
    # U19.3/U19.4 sit under L1's F.Cu pad, which rules out vias beside them. U19.3 gets its own 5 V via east of the pad
    # first, then U19.4 runs east under U19's body to GND, before the 5 V links can ring it in (r33 did). C48.1 ties to
    # VCCI pin 8, which the UCC21520 pin table says is internally shorted to pin 3, by way of pin 6 (DT, tied to 5 V):
    # a direct C48.1 -> U19.8 track has to pass pin 6 and cannot keep clear of it.
    ('5V', ('U19', '3'), 'largest', None),
    ('GND', ('U19', '4'), 'largest', None),
    ('5V', ('C48', '1'), ('U19', '6'), None),
    ('5V', ('U19', '6'), ('U19', '8'), None),
    ('GND', ('C48', '2'), ('U19', '4'), '5V'),
    ('5V', ('C90', '1'), ('U10', '3'), None),
    ('GND', ('C90', '2'), ('U10', '4'), '5V'),
    ('5V', ('C89', '2'), ('U8', '3'), None),
    ('GND', ('C89', '1'), ('U8', '4'), '5V'),
    ('5V', ('C62', '2'), ('U15', '3'), None),
    ('GND', ('C62', '1'), ('U15', '4'), '5V'),
]
RIP_PROTECT |= {v[i] for v in GATE_LOOPS.values() for i in (3, 4, 5)} | \
    {'Net-(U15-VDDA)', 'Net-(U10-VDDA)', 'Net-(U8-VDDA)'} | DIRECT_NETS
SMALL_VIA = (0.6, 0.3)    # fallback via for nets outside HIGH_CURRENT (DRU minimum drill 0.30 mm) when the class via fails
PLANE_TARGET = {'5V': [4], 'GND': [1, 6]}
PAIRS = {'ISNS_N': 'ISNS_P'}
# nets whose power path is a pour between the FET source pins: every other island (driver VSS pins, decoupling and
# pull-down pads) joins the pour island (largest) directly, so returns run pin-to-source instead of pin-to-pin loops
STAR = {'m2_source', 'm3_source', 'm4_source'}
# pads given their own plane via before signal routing: the rest reach GND through the refilled fill, and a late GND
# pass stitches any fill fragment the routes cut off. Listed here are the pads that the finished routes fence in so
# tightly that no via fits afterwards (found by the GND pass on the routed board, 2026-09-16).
FANOUT_PADS = {'GND': {'U11.2', 'U15.4', 'U15.5', 'U19.9', 'R62.2',
                        'C48.2', 'C90.2', 'C89.1', 'C62.1'},      # VCCI caps: own GND via (user, 2026-09-17)
               '5V': {'C48.1', 'C90.1', 'C89.2', 'C62.2',         # VCCI caps: own 5 V plane via
                      'U19.8'}}      # C48.1 has none (L1's F.Cu pad above it): its plane via is at the VCCI pin
POUR_MULT_DRIVE = 3.0     # gate-drive nets may cut through a non-LX power pour at this cost multiplier
POUR_MULT_OTHER = 6.0


def pour_mult(net):
    if net.startswith(('GATE_', 'Net-(D', 'Net-(U19-OUT', 'Net-(U11-OUT', 'Net-(U12-OUT', 'Net-(U6-OUT'))             or net.endswith(('-VDDA)', '-G)')) or net in ('m2_source', 'm3_source', 'm4_source'):
        return POUR_MULT_DRIVE
    return POUR_MULT_OTHER


def small_via_ok(net):
    # the DRU's 0.40 mm via-drill rule covers the high-current nets except the FET source nets, whose tracks outside
    # the pours carry only gate-drive current, so those may use the 0.6/0.3 via
    return net not in HIGH_CURRENT or net in ('m2_source', 'm3_source', 'm4_source')


def cls_of(net, classes):
    c = classes.get(net, 'Default').split(',')[0]
    return c if c in CLASS else 'Default'


def rules_for(net, classes):
    c = dict(CLASS[cls_of(net, classes)])
    if net in HIGH_CURRENT:
        c['w'] = c['wmin'] = 1.0
        c['via'] = (0.8, 0.4)
        if SRC_WIDTH_TEST and net in ('m2_source', 'm3_source', 'm4_source'):
            c['w'] = c['wmin'] = SRC_WIDTH_TEST       # what-if only (--src-width): not legal under the current DRU
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
                        raster_poly(poly, tmp, True)
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
        raster_poly(pts, inside, True)
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
        layers = ROUTE + [l for l in planes if l not in ROUTE]
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
            blk |= edge < w / 2 + EDGE_CLR + MARGIN
            if l in other_d:
                blk |= other_d[l] < w / 2 + OWN_GAP + MARGIN
            passable[l] = ~blk & ~ring
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
            flash = set(ls) | self.fill_layers.get(nn, set()) | {
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
            for l in ROUTE:
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

    def gate_loop(self, fet, log):
        """One FET's gate loop: gate-net links (series R, pulldown, diode) direct; the driver's VSS pin to the source
        pour; the drive track (driver OUT -> R and diode) beside that return."""
        drv, out_pin, vss_pin, gate_net, drive_net, src_net, leg = GATE_LOOPS[fet]
        self.direct = True
        try:
            f = self.route_net(gate_net, log, allow_rip=False)
        finally:
            self.direct = False
        self.lx_ok = True
        try:
            if LOOP_MODE == 'corridor':
                # the return goes first in a corridor wide enough for the drive beside it; the drive leg then follows it
                self.route_pad_edge(src_net, (drv, vss_pin), (fet, '3'), log, hot_ok=True, tag='loop',
                                    own_routes_off=not self.loaded, corridor=LOOP_CORRIDOR)
                self.via_mult = LOOP_VIA_MULT
                try:
                    self.route_pad_edge(drive_net, (drv, out_pin), leg, log, partner_net=src_net, hot_ok=True, tag='loop')
                finally:
                    self.via_mult = 1.0
                self.hot_ok = True
                f += self.route_net(drive_net, log, allow_rip=False)
            elif LOOP_DRIVE_FIRST and fet not in LOOP_RETURN_FIRST:
                # the paired drive leg takes its natural path (on one layer where it can), the return runs beside it to
                # this FET's own source pin (not into the other channel's return), then the rest of the drive net
                self.via_mult = LOOP_VIA_MULT
                try:
                    self.route_pad_edge(drive_net, (drv, out_pin), leg, log, hot_ok=True, tag='loop')
                finally:
                    self.via_mult = 1.0
                # beside the whole forward path: the drive leg and the gate-net link from that part to the gate pin
                self.route_pad_edge(src_net, (drv, vss_pin), (fet, '3'), log, partner_net=[drive_net, gate_net],
                                    hot_ok=True, tag='loop', own_routes_off=not self.loaded)
                self.hot_ok = True
                f += self.route_net(drive_net, log, allow_rip=False)
            else:
                self.route_pad_edge(src_net, (drv, vss_pin), 'largest', log, hot_ok=True, tag='loop')
                self.hot_ok = True
                self.pair_tracks = True
                f += self.route_net(drive_net, log, allow_rip=False, partner_override=src_net)
        finally:
            self.hot_ok = False
            self.pair_tracks = False
            self.lx_ok = False
        return f

    def fanout(self, net, planes, log, max_len=2.0, near=0.6, only=None):
        """Give every SMD pad of NET on F/B its own via to the planes, unless a barrel of the net already lies
        within NEAR mm of the pad. The net's fills on the routing layers are hidden while doing it (they yield and are
        refilled), so a pad counts as its own island; a stub longer than MAX_LEN mm is not committed."""
        n = self.nid[net]
        self.hidden_yld = [y.copy() for y in self.yld]
        for l in ROUTE:
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
            if res is None and allow_rip and RIPUP:
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


ORDER = ['SNS_CH1', 'SNS_CH2', 'SNS_CH3', 'ISNS_P', 'ISNS_N',
         'Net-(U19-OUTA)', 'GATE_M1',               # M1 hard-switches every cycle: its drive goes first
         'BYPASS',                                  # driver bypass links, direct and paired (user, 2026-09-17)
         'GATELOOP:M7', 'GATELOOP:M5', 'GATELOOP:M6', 'GATELOOP:M2', 'GATELOOP:M3', 'GATELOOP:M4',
         'm2_source', 'm3_source', 'm4_source',     # the rest of the driver returns (caps, pulldowns)
         'FANOUT:GND', 'FANOUT:5V',                 # a via per listed pad before signal tracks fence the pads in
         'Net-(U19-OUTB)',
         'Net-(U11-OUT)', 'Net-(M10-G)', 'Net-(U12-OUT)', 'Net-(M9-G)', 'Net-(U6-OUT)', 'Net-(M8-G)',
         'Net-(D10--)', 'Net-(D21--)', 'Net-(D9--)', 'Net-(U15-VDDA)', 'Net-(U10-VDDA)', 'Net-(U8-VDDA)',
         # J10's Vout/drain pins (1.0 mm by rule) can only leave the header's middle column one way: route them
         # before the logic and analog nets take that corridor
         'Vout_1', 'Vout_2', 'Vout_3', 'Output1_drain', 'Output2_drain', 'Output3_drain',
         'IREF1_input', 'IREF2_input', 'IREF3_input', 'Current',
         'M1_ON', 'M2_ON', 'ena_out_1', 'out_2_on', 'ena_out_2', 'out_3_on', 'ena_out_3',
         'analog_5V', '12V', '5V', 'LX', 'Vin', 'GND']


def main():
    a = sys.argv[1:]
    cop = json.load(open(a[0]))
    out = a[1]
    only = a[a.index('--nets') + 1].split(',') if '--nets' in a else None
    global NO_VIA_IN_PAD
    NO_VIA_IN_PAD = '--no-via-in-pad' in a
    skip = set(a[a.index('--skip') + 1].split(',')) if '--skip' in a else set()
    global RIPUP, LOOP_DRIVE_FIRST
    RIPUP = '--no-rip' not in a
    global LOOP_MODE
    if '--return-first' in a:
        LOOP_DRIVE_FIRST = False
    if '--loop-mode' in a:
        LOOP_MODE = a[a.index('--loop-mode') + 1]
    global SRC_WIDTH_TEST
    if '--src-width' in a:
        SRC_WIDTH_TEST = float(a[a.index('--src-width') + 1])
    t0 = time.time()
    if '--zones' in a:
        # zone shapes (pours and fills) from another export of the same board, e.g. the routed board after KiCad
        # refilled it: pour necks and fill fragments cut by routes then show up as islands to be joined again
        cop['zones'] = json.load(open(a[a.index('--zones') + 1]))['zones']
    bd = Board(cop)
    if '--jmap' in a:
        bd.load_jmap(a[a.index('--jmap') + 1])
    log = ['board rasterised in %.1f s' % (time.time() - t0)]
    if '--fills' in a:
        bd.replace_fills(json.load(open(a[a.index('--fills') + 1])))
    if '--routes' in a:
        bd.load_routes(json.load(open(a[a.index('--routes') + 1])))
        log.append('loaded %d committed route items' % len(bd.routes))
    order = [n for n in ORDER if (n in bd.nid or n.startswith(('FANOUT:', 'GATELOOP:')) or n == 'BYPASS')
             and (only is None or n in only) and n not in skip]
    total_fail = 0
    for net in order:
        t1 = time.time()
        if net == 'BYPASS':
            pxy = {(p['ref'], p['num']): (p['x'], p['y']) for p in bd.cop['pads']}
            bd.protect = True
            for bnet, pad, pin, partner in BYPASS_EDGES:
                if pin == 'largest':
                    bd.route_pad_edge(bnet, pad, pin, log, hot_ok=True, hide_fill=True, tag='byp ')
                    continue
                straight = math.hypot(pxy[pad][0] - pxy[pin][0], pxy[pad][1] - pxy[pin][1])
                bd.route_pad_edge(bnet, pad, pin, log, partner_net=partner, direct=True, hide_fill=(bnet in PLANE_TARGET),
                                  tag='byp ', max_len=max(4.0, 2.5 * straight))
            bd.protect = False
            log.append('     %-16s %.1f s' % (net, time.time() - t1))
            print('\n'.join(log[-3:]), flush=True)
            continue
        if net.startswith('GATELOOP:'):
            f = bd.gate_loop(net[9:], log)
            total_fail += f
            log.append('     %-16s done in %.1f s%s' % (net, time.time() - t1, (' (%d failed)' % f) if f else ''))
            print('\n'.join(log[-3:]), flush=True)
            continue
        if net in DIRECT_NETS:
            bd.direct = True
            try:
                f = bd.route_net(net, log)
            finally:
                bd.direct = False
            total_fail += f
            log.append('     %-16s done in %.1f s%s (direct)' % (net, time.time() - t1, (' (%d failed)' % f) if f else ''))
            print('\n'.join(log[-3:]), flush=True)
            continue
        if net.startswith('FANOUT:'):
            bd.direct = net == 'FANOUT:5V'        # VCCI caps' own 5 V vias: next to the pad, current map ignored
            bd.protect = True
            try:
                done, skipped = bd.fanout(net[7:], PLANE_TARGET[net[7:]], log, only=FANOUT_PADS.get(net[7:]))
            finally:
                bd.direct = bd.protect = False
            log.append('     %-16s %d vias, %d pads skipped, %.1f s' % (net, done, skipped, time.time() - t1))
            print('\n'.join(log[-3:]), flush=True)
            continue
        f = bd.route_net(net, log)
        total_fail += f
        log.append('     %-16s done in %.1f s%s' % (net, time.time() - t1, (' (%d failed)' % f) if f else ''))
        print('\n'.join(log[-3:]), flush=True)
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
