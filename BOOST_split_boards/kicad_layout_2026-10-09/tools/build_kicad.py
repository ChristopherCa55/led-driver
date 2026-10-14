"""KiCad schematic laid out like the LTspice v7 schematic (the user's request, 2026-10-09).

    python build_kicad.py [--draft]     ref/BOOST.kicad_sch + LTspice v7  ->  work/BOOST.kicad_sch

The KiCad schematic was made by KiCad's LTspice importer: 1 LTspice unit = 0.079375 mm and the converted `ltspice:`
symbols have the LTspice pin geometry. So every part is placed where its LTspice twin is, every LTspice wire is copied,
LTspice net flags become global labels / GND symbols, comments become text. Then the KiCad-only differences:
  - symbols kept from KiCad's libraries (INA241, R_Shunt, MCP4451, UCC21520, L78L05, 4017, 74HC4051) have other pin
    positions: their pins are joined to the LTspice wiring (supply pins get their own GND symbol / supply label),
  - remade symbols (user's choice): NAND gates (output moved to the middle: a 1.27 mm jog is added), Schmitt
    inverters, the 4066 switch, U16's regulator box, op-amp marks, GND text hidden (remade_symbols.py),
  - simulation sources: each LED becomes its two wire pads (J3..J8), the battery J1 (Vin) / J2 (GND), the Arduino
    sources become labels to header J9; board-to-board connectors J10/J11, mounting holes, spare gate units and the
    gate supply units get their own areas; the net ties NT1..NT3 go between each sense resistor and its op-amp,
  - nets KiCad leaves unnamed keep no name, except OUT_1_ENA, OUT_2_ENA, OUT_3_ENA and "4" (user's choice).
The netlist is then compared with the original KiCad netlist (components, every net's pins, net names).
"""
import os, re, sys, copy, uuid, json
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'ltspice_layout_2026-10-05', 'tools')))
from sexpr import parse, dump, find, findall, unq, q, prop
import kgeo, knet, remade_symbols as RS
from ascmodel import Asc, connectivity as lt_connectivity, on_interior
from layout_lib import window as lt_window

BASE = os.path.normpath(os.path.join(HERE, '..'))
REF = os.path.join(BASE, 'ref', 'BOOST.kicad_sch')
REFNET = os.path.join(BASE, 'work', 'ref.xml')
LT = os.path.normpath(os.path.join(BASE, '..', 'ltspice_layout_2026-10-05', 'work', 'BOOST_revised_v7.asc'))
OUT = os.path.join(BASE, 'work', 'BOOST.kicad_sch')
S = 0.079375                      # mm per LTspice unit (KiCad's importer)
OX, OY = 629.92, 805.18           # sheet position of LTspice (0, 0); the drawing lands inside an A0 sheet
PROJECT_PATH = None
POWER = {'GND', '5V', 'analog_5V', '12V'}
NEW_NAMES = {'OUT_1_ENA', 'OUT_2_ENA', 'OUT_3_ENA', '4'}

ROTMAP = {'R0': (0, None), 'R90': (270, None), 'R180': (180, None), 'R270': (90, None),
          'M0': (0, 'y'), 'M90': (270, 'y'), 'M180': (180, 'y'), 'M270': (90, 'y')}
ORIENTS = [(a, m) for a in (0, 90, 180, 270) for m in (None, 'x')]

STD_MAP = {
    'INA241A4': {'IN+': '8', 'IN-': '1', 'VS': '6', 'GND': '2', 'REF1': '7', 'REF2': '3', 'OUT': '5'},
    'MCP4451_CTRL': {'VDD': '17', 'VSS': '7', 'SCL': '5', 'SDA': '6', 'HVC/A0': '4', 'A1': '16', 'RESET': '15'},
    'UCC21520': {'INA': '1', 'INB': '2', 'VCCI': '3', 'GND': '4', 'DIS': '5', 'DT': '6', 'VSSB': '9', 'VOUTB': '10',
                 'VDDB': '11', 'VSSA': '14', 'VOUTA': '15', 'VDDA': '16'},
    'L78L05': {'IN': '3', 'OUT': '1', 'GND': '2'},
    'CD4017B': {'MR': '15', 'CPN': '13', 'CP': '14', 'Q0': '3', 'Q1': '2', 'Q2': '4', 'Q3': '7', 'Q4': '10', 'Q5': '1',
                'Q6': '5', 'Q7': '6', 'Q8': '9', 'Q9': '11', 'Q59': '12'},
    '74HC4051': {'IOC': '3', 'A': '11', 'B': '10', 'C': '9', 'INH': '6', 'VDD': '16', 'VSS': '8', 'VEE': '7',
                 'IO0': '13', 'IO1': '14', 'IO2': '15', 'IO3': '12', 'IO4': '1', 'IO5': '5', 'IO6': '2', 'IO7': '4'},
    'MC7812': {'IN': '1', 'GND': '2', 'OUT': '3'},
    'CD74HC4066': None,              # by pin name
    'MCP4451_POT': None,             # by pin name (P0A etc. end in A/W/B)
    'CSS4J_4026': None,              # by net (filled in below)
}
SIM_TEXT_DROP = ('simulation only - not on the PCB',)


def nid():
    return q(str(uuid.uuid4()))


# ------------------------------------------------------------------------------------------------ helpers
def kpin_off(px, py, ang, mirror):
    dx, dy = kgeo.xform(px, py, ang, mirror)
    return (round(dx / S), round(dy / S))


def to_mm(x, y):
    return (round(S * x + OX, 4), round(S * y + OY, 4))


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


# KiCad's gate-driver symbol is wider than the LTspice one: the power section right of the LX bus is moved right
# (horizontal wires crossing the line get longer; nothing straddles it, no wire crosses the band's lower edge)
STRETCH = (-2296, -4900, 160)     # x line, band = y above this, shift
OFFGRID_ROW = (-6440, -4800, -5700, -4680, 8)   # bypass-cap row drawn on LTspice's 8-unit half grid -> KiCad 1.27 mm
# KiCad's 4017 / 74HC4051 are wider than the LTspice symbols (same pin rows): split them open, in this order
SPLITS = [('U18', 1440, 192),     # left pins 1376 .. right pins 1504 -> KiCad 320 wide
          ('U28', 2008, 96)]      # (after the U18 split) left 1952 .. right 2080 -> KiCad 224 wide; VSS left, VEE/VDD right


def _split_pins(a):
    """parts widened by a split stretch keep their own pin points (a.pin_over); everything else uses the .asy"""
    if not hasattr(a, 'pin_over'):
        a.pin_over = {}
        base = a.pins
        a.pins = lambda s: [(n,) + a.pin_over.get((s.name, n), (x, y)) for n, x, y in base(s)]


def stretch(a, x0, ylim, dx, mv=None, split=()):
    """move everything where mv(x, y) (default: right of x0 and above ylim) right by dx; parts move whole, and a wire
    with only one end moving must be horizontal (it gets longer); checked: the LTspice nets stay the same.
    `split` parts are widened instead: the stretch line runs through them and their pins on the right side move
    (their KiCad symbol is wider than the LTspice one; the KiCad part is placed on these pin points)"""
    _split_pins(a)
    before = lt_connectivity(a)
    mv = mv or (lambda x, y: x > x0 and y < ylim)
    for s in a.syms:
        if s.name in split:
            continue
        x1, y1, x2, y2 = a.body(s)
        corners = {mv(x, y) for n, x, y in a.pins(s)}
        if not any(k[0] == s.name for k in a.pin_over):
            corners |= {mv(x, y) for x in (x1, x2) for y in (y1, y2)}
        assert len(corners) == 1, ('part straddles the stretch edge', s.name)
    for w in a.wires:
        assert mv(w[0], w[1]) == mv(w[2], w[3]) or w[1] == w[3], ('wire crosses the stretch edge', w)
    a.wires = [(w[0] + dx * mv(w[0], w[1]), w[1], w[2] + dx * mv(w[2], w[3]), w[3]) for w in a.wires]
    for f in a.flags:
        f[0] += dx * mv(f[0], f[1])
    for s in a.syms:
        pts = a.pins(s)
        if s.name in split:
            for n, x, y in pts:
                a.pin_over[(s.name, n)] = (x + dx * mv(x, y), y)
            continue
        if mv(*pts[0][1:]) if pts else mv(s.x, s.y):
            s.x += dx
            for n, x, y in pts:
                if (s.name, n) in a.pin_over:
                    a.pin_over[(s.name, n)] = (x + dx, y)
    for i, t in enumerate(a.texts):
        u = t.split(' ', 3)
        x, y = int(u[1]), int(u[2])
        a.texts[i] = ' '.join([u[0], str(x + dx * mv(x, y)), u[2], u[3]])
    after = lt_connectivity(a)
    part = lambda c: sorted(sorted(k for k, g in c[0].items() if c[2][g] == n) for n in set(c[2][g] for g in c[0].values()))
    assert part(before) == part(after), 'stretch changed the LTspice connectivity'
    nm = lambda c: sorted((sorted(k for k, g in c[0].items() if c[2][g] == n), sorted(c[3].get(n, ())))
                          for n in set(c[2][g] for g in c[0].values()))
    assert nm(before) == nm(after), 'stretch changed the LTspice net names'


class Builder:
    def __init__(self):
        self.root = parse(open(REF, encoding='utf-8').read())
        global PROJECT_PATH
        self.comps, self.knets = knet.read(REFNET)
        self.kpin_net = {(r, p): n for n, nodes in self.knets.items() for r, p, f, t in nodes}
        self.libs = {unq(s[1]): s for s in findall(find(self.root, 'lib_symbols'), 'symbol')}
        self.libs['ltspice:74HC00_conv'] = RS.sym_74hc00()
        self.libs['ltspice:74HC14_conv'] = RS.sym_74hc14()
        self.libs['ltspice:CD4066_conv'] = RS.sym_4066()
        self.libs['ltspice:LM2940_12'] = RS.sym_regulator()
        RS.fix_opamp(self.libs['ltspice:OpAmps/opamp2'])
        RS.fix_gnd(self.libs['ltspice:GND'])
        self.inst = {}
        self.power_templates = {}
        for s in findall(self.root, 'symbol'):
            i = kgeo.inst_info(s)
            if i['ref'].startswith('#'):
                self.power_templates.setdefault(i['lib'], s)
                if i['lib'] == 'power:PWR_FLAG':
                    self.inst[(i['ref'], 1)] = s
                continue
            self.inst[(i['ref'], i['unit'])] = s
        path = find(find(find(next(iter(self.inst.values())), 'instances'), 'project'), 'path')
        PROJECT_PATH = path[1]
        self.a = Asc(LT)
        stretch(self.a, *STRETCH)
        x1, y1, x2, y2, d = OFFGRID_ROW
        stretch(self.a, x1, y1, d, lambda x, y: x1 <= x <= x2 and y1 <= y <= y2)   # whole row, no wire leaves it
        for name, x0, d in SPLITS:
            stretch(self.a, x0, STRETCH[1], d, split=(name,))
        self.lt_by = self.a.by()
        pg, group, nog, names, pins_at = lt_connectivity(self.a)
        self.lt_net_id = {k: nog[g] for k, g in pg.items()}
        self.swap2 = set()
        self.lt_net_name = {}
        for k, g in pg.items():
            ns = names.get(nog[g])
            self.lt_net_name[k] = ('GND' if '0' in ns else sorted(ns)[0]) if ns else None
        # outputs
        self.wires = [tuple(w) for w in self.a.wires]
        self.labels = []          # (x, y, name, shape)
        self.gnds = []            # (x, y)
        self.nocon = []
        self.texts = []           # (x, y, just, size, text)
        self.kpins = {}           # (ref, num) -> (x, y)  LTspice units
        self.placed = {}          # (ref, unit) -> (ang, mirror, x, y)  (x, y LTspice units)
        self.prop_pos = {}        # (ref, unit) -> {'Reference': (x, y, just, size, hide), 'Value': ...}
        self.dead = set()         # LTspice pin points with no KiCad pin (trimmed later)
        self.extra_syms = []      # new symbol nodes (GND power symbols)
        self.report = []
        self.unmapped = []        # KiCad pins with no LTspice twin: (key, num, point, outward dir)

    # ------------------------------------------------------------------ placing parts
    def kunit(self, ltname):
        m = re.match(r'^(U\d+)([A-G])$', ltname)
        if m and (m.group(1), ord(m.group(2)) - 64) in self.inst:
            return (m.group(1), ord(m.group(2)) - 64)
        return (ltname, 1) if (ltname, 1) in self.inst else None

    def lib_of(self, key):
        return kgeo.inst_info(self.inst[key])['lib']

    def pin_map(self, s, key):
        """LTspice pin name -> KiCad pin number for this instance"""
        lib = self.libs[self.lib_of(key)]
        kp = [p for p in kgeo.lib_pins(lib, key[1]) if not p[5]]
        ltp = self.a.asy(s.sym)['pins']
        if s.sym in STD_MAP and STD_MAP[s.sym]:
            return dict(STD_MAP[s.sym])
        if s.sym == 'CD74HC4066':
            return {n: next(k[0] for k in kp if k[1] == n) for n in ('A', 'B', 'CTRL')}
        if s.sym == 'MCP4451_POT':
            return {n: next(k[0] for k in kp if k[1].endswith(n)) for n in ('A', 'W', 'B')}
        if s.sym == 'Digital\\\\and':
            byname = {k[1]: k[0] for k in kp}
            m = {'b': byname['A'], 'd': byname['B'], '_Q': byname['Y']}
            nb, nd = self.lt_net_name.get((s.name, 'b')), self.lt_net_name.get((s.name, 'd'))
            ka, kb = self.kpin_net.get((key[0], m['b'])), self.kpin_net.get((key[0], m['d']))
            if nb and nd and (nb != ka or nd != kb) and (nb == kb and nd == ka):
                m['b'], m['d'] = m['d'], m['b']
                self.report.append('%s: inputs drawn the other way round (KiCad pin order kept)' % s.name)
            return m
        if s.sym == 'Digital\\\\schmtinv':
            byname = {k[1]: k[0] for k in kp}
            return {'in': byname['A'], '_Q': byname['Y']}
        if s.sym == 'CSS4J_4026':
            out = {}
            for n in ('F1', 'S1', 'S2', 'F2'):
                ln = self.lt_net_name.get((s.name, n))
                cand = [k[0] for k in kp if self.kpin_net.get((key[0], k[0])) == ln]
                if len(cand) == 1:
                    out[n] = cand[0]
            if len(out) < 4:
                out = {'F1': '1', 'S1': '2', 'S2': '3', 'F2': '4'}
            return out
        # converted symbols: same geometry (KiCad lib = LTspice local * S, y flipped)
        out = {}
        for p in ltp:
            for k in kp:
                if round(k[2] / S) == p['x'] and round(-k[3] / S) == p['y']:
                    out[p['name']] = k[0]
        if s.name in self.swap2 and len(out) == 2:
            a, b = list(out)
            out[a], out[b] = out[b], out[a]
        return out

    def place(self, s, key, orient=None, anchor=None):
        lib = self.libs[self.lib_of(key)]
        kp = {k[0]: k for k in kgeo.lib_pins(lib, key[1])}
        pmap = self.pin_map(s, key)
        ltpts = {n: (x, y) for n, x, y in self.a.pins(s)}
        pairs = [(ltpts[n], kp[k]) for n, k in pmap.items() if n in ltpts and k in kp]
        best = None
        cands = [orient] if orient else [ROTMAP[s.rot]] + ORIENTS
        for ang, mir in cands:
            offs = [(lt, kpin_off(k[2], k[3], ang, mir)) for lt, k in pairs]
            if anchor:
                lt, k = next((lt, k) for lt, k in pairs if k[0] == anchor)
                o = kpin_off(k[2], k[3], ang, mir)
                t = (lt[0] - o[0], lt[1] - o[1])
            else:
                votes = defaultdict(int)
                for lt, o in offs:
                    votes[(lt[0] - o[0], lt[1] - o[1])] += 1
                t = max(votes, key=votes.get)
            score = sum(abs(lt[0] - t[0] - o[0]) + abs(lt[1] - t[1] - o[1]) for lt, o in offs)
            if best is None or score < best[0]:
                best = (score, ang, mir, t)
            if score == 0 and not orient:
                break
        score, ang, mir, t = best
        self.placed[key] = (ang, mir, t[0], t[1])
        moved = []
        for num, k in kp.items():
            o = kpin_off(k[2], k[3], ang, mir)
            self.kpins[(key[0], num)] = (t[0] + o[0], t[1] + o[1])
        used = set(pmap.values())
        for num, k in kp.items():
            if num not in used and not k[5]:
                o = kpin_off(k[2], k[3], ang, mir)
                self.unmapped.append((key, num, self.kpins[(key[0], num)], pin_out_dir(k, ang, mir)))
        for n, (x, y) in ltpts.items():
            kn = pmap.get(n)
            if kn is None or kn not in kp:
                self.dead.add((x, y))
                continue
            kx, ky = self.kpins[(key[0], kn)]
            if (kx, ky) != (x, y):
                moved.append((key, kn, (kx, ky), (x, y), kp[kn]))
        return moved

    # ------------------------------------------------------------------ texts of placed parts
    def lt_window_world(self, s, num):
        asy = self.a.asy(s.sym)
        w = s.windows.get(num) or asy['windows'].get(num)
        if not w:
            return None
        lx, ly, just, size = w
        if just == 'Invisible':
            return 'hide'
        wx, wy = self.a.xf(lx, ly, s.rot)
        world = 'Center' if just in ('Center', 'VCenter') else None
        for h in ('Left', 'Right', 'Top', 'Bottom'):
            if world is None and lt_window(s.rot, h, wx, wy, size)[2] == just:
                world = h
        return (s.x + wx, s.y + wy, world or 'Left', size)

    # ------------------------------------------------------------------ build
    def compute_swaps(self):
        """2-pin parts whose KiCad pin 1/2 sit the other way round from LTspice: decided by the nets on each side"""
        for it in range(4):
            corr = defaultdict(lambda: defaultdict(int))
            for s in self.a.syms:
                key = self.kunit(s.name) if not s.name.startswith('SIM_') else None
                if key is None:
                    continue
                pm = self.pin_map(s, key)
                if len(pm) == 2 and s.sym in ('res', 'cap') and it == 0:
                    continue
                for ln, kn in pm.items():
                    lid = self.lt_net_id.get((s.name, ln))
                    knet = self.kpin_net.get((key[0], kn))
                    if lid is not None and knet:
                        corr[lid][knet] += 1
            best = {lid: max(c, key=c.get) for lid, c in corr.items()}
            changed = False
            for s in self.a.syms:
                if s.sym not in ('res', 'cap') or s.name.startswith('SIM_'):
                    continue
                key = self.kunit(s.name)
                pm = self.pin_map(s, key)
                ok = all(best.get(self.lt_net_id.get((s.name, ln))) in (None, self.kpin_net.get((key[0], kn)))
                         for ln, kn in pm.items())
                if not ok:
                    self.swap2 ^= {s.name}
                    changed = True
            if not changed and it > 0:
                break

    def build(self):
        self.compute_swaps()
        moved_all = []
        std_keys = []
        for s in self.a.syms:
            if s.name.startswith('SIM_'):
                for n, x, y in self.a.pins(s):
                    self.dead.add((x, y))
                continue
            key = self.kunit(s.name)
            if key is None:
                raise SystemExit('no KiCad part for %s' % s.name)
            moved = self.place(s, key)
            lib = self.lib_of(key)
            if lib.startswith('ltspice:') or lib == 'Device:R_Shunt':
                pp = {}
                for kname, num in (('Reference', 0), ('Value', 3)):
                    w = self.lt_window_world(s, num)
                    pp[kname] = w
                self.prop_pos[key] = pp
            else:
                std_keys.append(key)
            moved_all += moved
        self.moved = moved_all
        self.std_keys = std_keys
        return self


# ================================================================================================= wiring stage
def seg_dir(w, p):
    """direction (dx, dy) of wire w leaving point p (p is an end of w)"""
    o = (w[2], w[3]) if (w[0], w[1]) == p else (w[0], w[1])
    return ((o[0] > p[0]) - (o[0] < p[0]), (o[1] > p[1]) - (o[1] < p[1]))


def pin_out_dir(kp, ang, mir):
    """outward direction of a KiCad pin (from the body towards its connection point)"""
    a = kp[4]                                    # pin angle: direction from connection point into the body
    vx, vy = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[a]
    bx, by = kgeo.xform(vx, vy, ang, mir)        # into the body, sheet coordinates
    return (-int(round(bx)), -int(round(by)))


def add_methods():
    def flags_to_items(self):
        """LTspice flags -> GND symbols / global labels / no-connects (SIM-only nets dropped)"""
        knames = set(self.knets)
        for x, y, name, io in self.a.flags:
            if name == '0':
                self.gnds.append((x, y))
            elif name in knames or name in NEW_NAMES:
                shape = {'In': 'input', 'Out': 'output'}.get(io, 'passive')
                self.labels.append((x, y, name, shape))
            elif re.fullmatch(r'\d+', name):
                pass                                   # U18 Q4..Q9: no-connect flags, added with the part
            else:
                self.report.append('LTspice label %s not used in KiCad (simulation net)' % name)

    def connect_moved(self):
        for key, num, kpt, ltpt, kp in self.moved:
            net = self.kpin_net.get((key[0], num), '')
            ang, mir = self.placed[key][:2]
            if self.lib_of(key) == 'ltspice:74HC00_conv':  # NAND output in the middle: 1.27 mm jog to the old point
                self.wires.append((kpt[0], kpt[1], ltpt[0], ltpt[1]))
                continue
            d = pin_out_dir(kp, ang, mir)
            if net in POWER:
                self.dead.add(ltpt)
                self.power_at(kpt, net, d)
            else:
                self.route(kpt, ltpt, d)
        for key, num, p, d in self.unmapped:
            net = self.kpin_net.get((key[0], num), '')
            if net in POWER:
                end = (p[0] + 32 * d[0], p[1] + 32 * d[1])
                self.wires.append((p[0], p[1], end[0], end[1]))
                self.power_at(end, net, d)
            elif not net.startswith('unconnected-'):
                self.report.append('%s pin %s (net %s) has no LTspice twin and is left open' % (key[0], num, net))

    def power_at(self, p, net, d):
        if net == 'GND':
            self.gnds.append((p[0], p[1], d))
        else:
            self.labels.append((p[0], p[1], net, 'passive', d))

    def route(self, k, l, d):
        """orthogonal route from KiCad pin point k (pin leaving in direction d) to the LTspice point l"""
        if k == l:
            return
        if k[0] == l[0] or k[1] == l[1]:
            self.wires.append((k[0], k[1], l[0], l[1]))
            return
        c = (l[0], k[1]) if d[1] == 0 else (k[0], l[1])
        self.wires.append((k[0], k[1], c[0], c[1]))
        self.wires.append((c[0], c[1], l[0], l[1]))

    for f in (flags_to_items, connect_moved, power_at, route):
        setattr(Builder, f.__name__, f)


add_methods()


# ================================================================================================= KiCad-only parts
CONN_BODY_ANGLE = {(1, 0): 180, (-1, 0): 0, (0, 1): 90, (0, -1): 270}   # body direction from the pin -> Conn angle


def add_methods2():
    def place_extra(self, key, x, y, ang=0, mir=None):
        """place a KiCad part that has no LTspice twin; (x, y) = symbol origin in LTspice units"""
        lib = self.libs[self.lib_of(key)]
        self.placed[key] = (ang, mir, x, y)
        pts = {}
        for k in kgeo.lib_pins(lib, key[1]):
            o = kpin_off(k[2], k[3], ang, mir)
            self.kpins[(key[0], k[0])] = (x + o[0], y + o[1])
            pts[k[0]] = ((x + o[0], y + o[1]), pin_out_dir(k, ang, mir))
        return pts

    def connector_at(self, ref, p, body_dir):
        """single-pin wire pad with its pin end at p and its body in direction body_dir"""
        ang = CONN_BODY_ANGLE[body_dir]
        o = kpin_off(5.08, 0, ang, None)
        bx, by = p[0] - o[0], p[1] - o[1]                  # the pad body
        self.place_extra((ref, 1), bx, by, ang)
        dx, dy = body_dir
        if dy:                                             # texts beyond the body, in line with the wire
            y0 = by + dy * 24 + (min(dy, 0) * 24)
            self.prop_pos[(ref, 1)] = {'Reference': (bx, y0, 'Center', 2), 'Value': (bx, y0 + 24, 'Center', 2)}
        else:
            j = 'Left' if dx > 0 else 'Right'
            self.prop_pos[(ref, 1)] = {'Reference': (bx + dx * 16, by - 12, j, 2), 'Value': (bx + dx * 16, by + 12, j, 2)}

    def sim_parts(self):
        pads = {}
        for r in ('J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8'):
            pads[self.kpin_net[(r, '1')]] = r
        labels = {'IREF1', 'IREF2', 'IREF3', 'Vref_1_arduino', 'Vref_2_arduino', 'Vref_3_arduino', 'ARD_M1_INHIBIT'}
        for s in self.a.syms:
            if not s.name.startswith('SIM_'):
                continue
            pins = {n: (x, y) for n, x, y in self.a.pins(s)}
            if s.name.startswith('SIM_LED'):
                for n in ('+', '-'):
                    p = pins[n]
                    net = self.lt_net_name.get((s.name, n))
                    stub = (p[0] + 48, p[1])
                    self.wires.append((p[0], p[1], stub[0], stub[1]))
                    self.connector_at(pads[net], stub, (1, 0))
                    self.dead.discard(p)
            elif s.name == 'SIM_CABLE_INDUCTANCE':
                vin = next(n for n in pins if self.lt_net_name.get((s.name, n)) == 'Vin')
                other = next(n for n in pins if n != vin)
                p, o = pins[vin], pins[other]
                d = ((o[0] > p[0]) - (o[0] < p[0]), (o[1] > p[1]) - (o[1] < p[1]))
                self.connector_at(pads['Vin'], p, d)
                self.dead.discard(p)
            elif s.name == 'SIM_BATTERY':
                p, o = pins['-'], pins['+']
                d = ((o[0] > p[0]) - (o[0] < p[0]), (o[1] > p[1]) - (o[1] < p[1]))
                self.connector_at(pads['GND'], p, d)
                self.dead.discard(p)
            else:
                net = self.lt_net_name.get((s.name, '+'))
                if net in labels and self.named_on_wires(pins['+'], net):
                    pass                               # your flag already names this wire: the source stub goes
                elif net in labels:
                    self.labels.append((pins['+'][0], pins['+'][1], net, 'input'))
                    self.dead.discard(pins['+'])
                else:
                    self.report.append('%s: + pin net %s has no KiCad counterpart' % (s.name, net))

    def named_on_wires(self, p, name):
        """is a label `name` on the wires connected to point p?"""
        seen, todo = {p}, [p]
        while todo:
            q = todo.pop()
            for w in self.wires:
                a, b = (w[0], w[1]), (w[2], w[3])
                if q in (a, b) or on_interior(q, w):
                    for r in (a, b):
                        if r not in seen:
                            seen.add(r)
                            todo.append(r)
        return any(l[2] == name and ((l[0], l[1]) in seen or any(on_interior((l[0], l[1]), w) and
                   ((w[0], w[1]) in seen) for w in self.wires)) for l in self.labels)

    def split_all(self):
        pts = set()
        for w in self.wires:
            pts |= {(w[0], w[1]), (w[2], w[3])}
        pts |= set(self.kpins.values()) | {(l[0], l[1]) for l in self.labels} | {(g[0], g[1]) for g in self.gnds}
        out = []
        for w in self.wires:
            a, b = (w[0], w[1]), (w[2], w[3])
            inner = sorted([p for p in pts if on_interior(p, w)] + [a, b])
            out += [(p[0], p[1], q[0], q[1]) for p, q in zip(inner, inner[1:]) if p != q]
        self.wires = out

    def trim(self):
        self.split_all()
        anchors = set(self.kpins.values())
        while True:
            ends = defaultdict(int)
            for w in self.wires:
                ends[(w[0], w[1])] += 1
                ends[(w[2], w[3])] += 1
            item_pts = {(l[0], l[1]) for l in self.labels} | {(g[0], g[1]) for g in self.gnds}

            def interior(p):
                return any(on_interior(p, w) for w in self.wires)
            removed = False
            keep = []
            for w in self.wires:
                bad = False
                for p in ((w[0], w[1]), (w[2], w[3])):
                    if ends[p] == 1 and p not in anchors and p not in item_pts and not interior(p):
                        bad = True
                if bad or (w[0], w[1]) == (w[2], w[3]):
                    removed = True
                else:
                    keep.append(w)
            self.wires = keep
            ends2 = set()
            for w in self.wires:
                ends2 |= {(w[0], w[1]), (w[2], w[3])}

            def attached(p):
                return p in anchors or p in ends2 or interior(p)
            nl = [l for l in self.labels if attached((l[0], l[1]))]
            ng = [g for g in self.gnds if attached((g[0], g[1]))]
            if len(nl) != len(self.labels) or len(ng) != len(self.gnds):
                removed = True
            self.labels, self.gnds = nl, ng
            if not removed:
                return

    for f in (place_extra, connector_at, sim_parts, named_on_wires, split_all, trim):
        setattr(Builder, f.__name__, f)


add_methods2()


def add_methods3():
    def nettie(self):
        """NT1..NT3 between each sense resistor/MOSFET source node and the op-amp input, on a straight wire"""
        for nt, m, r, u in (('NT1', 'M10', 'R52', 'U11'), ('NT2', 'M9', 'R53', 'U12'), ('NT3', 'M8', 'R7', 'U6')):
            side_a = {self.kpins[(m, '3')], self.kpins[(r, '1')]}
            target = self.kpins[(u, '4')]
            adj = defaultdict(list)
            pts = set()
            for i, w in enumerate(self.wires):
                pts |= {(w[0], w[1]), (w[2], w[3])}
            for i, w in enumerate(self.wires):
                a, b = (w[0], w[1]), (w[2], w[3])
                inner = sorted([p for p in pts if on_interior(p, w)] + [a, b])
                for p, q in zip(inner, inner[1:]):
                    adj[p].append((q, i))
                    adj[q].append((p, i))
            # path from side A to the op-amp pin
            prev, seen, todo = {}, set(side_a), list(side_a)
            while todo:
                p = todo.pop(0)
                if p == target:
                    break
                for q, i in adj[p]:
                    if q not in seen:
                        seen.add(q)
                        prev[q] = p
                        todo.append(q)
            path = [target]
            while path[-1] not in side_a:
                path.append(prev[path[-1]])
            path.reverse()
            # longest straight piece that is a bridge (no other wire touches its inside)
            best = None
            for p, q in zip(path, path[1:]):
                length = abs(p[0] - q[0]) + abs(p[1] - q[1])
                if length >= 96 and (best is None or length > best[0]):
                    best = (length, p, q)
            if best is None:
                self.report.append('%s: no straight wire long enough on the %s sense path' % (nt, u))
                continue
            _, p, q = best
            d = ((q[0] > p[0]) - (q[0] < p[0]), (q[1] > p[1]) - (q[1] < p[1]))
            mid = ((p[0] + q[0]) // 2 // 16 * 16, (p[1] + q[1]) // 2 // 16 * 16)
            c1 = (mid[0] - 32 * d[0], mid[1] - 32 * d[1])        # towards side A: pin 2
            c2 = (mid[0] + 32 * d[0], mid[1] + 32 * d[1])        # towards the op-amp: pin 1
            # cut the wire that holds p..q
            far = c2
            for i, w in enumerate(self.wires):
                if (on_interior(c1, w) or c1 in ((w[0], w[1]), (w[2], w[3]))) and \
                        (on_interior(c2, w) or c2 in ((w[0], w[1]), (w[2], w[3]))):
                    a, b = (w[0], w[1]), (w[2], w[3])
                    da = abs(a[0] - c1[0]) + abs(a[1] - c1[1])
                    db = abs(b[0] - c1[0]) + abs(b[1] - c1[1])
                    near, far = (a, b) if da <= db else (b, a)
                    del self.wires[i]
                    if near != c1:
                        self.wires.append((near[0], near[1], c1[0], c1[1]))
                    if far != c2:
                        self.wires.append((c2[0], c2[1], far[0], far[1]))
                    break
            # NetTie_2: pin 1 at (-2.54, 0), pin 2 at (2.54, 0); pin 2 must face side A
            ang = {(1, 0): 180, (-1, 0): 0, (0, 1): 270, (0, -1): 90}[d]
            o2 = kpin_off(2.54, 0, ang, None)
            self.place_extra((nt, 1), c1[0] - o2[0], c1[1] - o2[1], ang)
            assert self.kpins[(nt, '1')] == c2, (nt, self.kpins[(nt, '1')], c2)
            mx, my = c1[0] - o2[0], c1[1] - o2[1]
            if d[1] == 0:                                  # texts above / below the tie, off the wire
                self.prop_pos[(nt, 1)] = {'Reference': (mx, my - 12, 'Bottom', 2), 'Value': (mx, my + 12, 'Top', 2)}
            else:
                self.prop_pos[(nt, 1)] = {'Reference': (mx + 16, my - 12, 'Left', 2), 'Value': (mx + 16, my + 12, 'Left', 2)}
            # label spot: on the op-amp side wire, clear of the tie
            run = abs(far[0] - c2[0]) + abs(far[1] - c2[1])
            spot = (c2[0] + 64 * d[0], c2[1] + 64 * d[1]) if run >= 96 else c2
            # the net's label belongs to the op-amp side (KiCad: SNS_CHn = NT pin 1 + op-amp input)
            name = 'SNS_CH%s' % nt[-1]
            reach, todo = set(side_a), list(side_a)
            while todo:
                p0 = todo.pop()
                for w in self.wires:
                    for a0, b0 in (((w[0], w[1]), (w[2], w[3])), ((w[2], w[3]), (w[0], w[1]))):
                        if (a0 == p0 or on_interior(p0, w)) and b0 not in reach:
                            reach.add(b0)
                            todo.append(b0)
                        if on_interior(a0, (p0[0], p0[1], p0[0], p0[1])):
                            pass
            for i, l in enumerate(self.labels):
                if l[2] == name and ((l[0], l[1]) in reach or any(on_interior((l[0], l[1]), w) and
                                                                   ((w[0], w[1]) in reach) for w in self.wires)):
                    self.labels[i] = (spot[0], spot[1], name, l[3])
                    self.report.append('%s label moved next to %s pin 1 (op-amp side of the net tie)' % (name, nt))

    def noconnects(self):
        hidden = set()                                 # hidden NC pins need no marker (the original has none)
        for key in self.placed:
            if key in self.inst:
                for k in kgeo.lib_pins(self.libs[self.lib_of(key)], key[1]):
                    if k[5]:
                        hidden.add((key[0], k[0]))
        for (ref, num), p in self.kpins.items():
            if self.kpin_net.get((ref, num), '').startswith('unconnected-') and (ref, num) not in hidden:
                self.nocon.append(p)

    def junctions_and_split(self):
        pts = set()
        for w in self.wires:
            pts |= {(w[0], w[1]), (w[2], w[3])}
        pts |= set(self.kpins.values()) | {(l[0], l[1]) for l in self.labels} | {(g[0], g[1]) for g in self.gnds}
        out = []
        for w in set(self.wires):
            a, b = (w[0], w[1]), (w[2], w[3])
            inner = sorted([p for p in pts if on_interior(p, w)] + [a, b])
            for p, q in zip(inner, inner[1:]):
                if p != q:
                    out.append((p[0], p[1], q[0], q[1]))
        # drop duplicates (same segment either way round)
        seen, ws = set(), []
        for w in out:
            k = tuple(sorted([(w[0], w[1]), (w[2], w[3])]))
            if k not in seen:
                seen.add(k)
                ws.append(w)
        self.wires = ws
        deg = defaultdict(int)
        for w in ws:
            deg[(w[0], w[1])] += 1
            deg[(w[2], w[3])] += 1
        pinpts = set(self.kpins.values())
        self.junctions = sorted(p for p, n in deg.items() if n + (1 if p in pinpts else 0) >= 3)

    for f in (nettie, noconnects, junctions_and_split):
        setattr(Builder, f.__name__, f)


add_methods3()


def add_methods4():
    def extras(self):
        """gate supply units, spare units, connectors J9..J11, mounting holes, PWR_FLAGs"""
        # supply units of the logic chips, under the logic bypass-cap row: 5V label on top, GND below
        x = -6304
        self.texts.append((-6320, -4560, 'Left', 2, 'logic chip supply pins'))
        for key in (('U101', 5), ('U102', 5), ('U103', 5), ('U104', 7), ('U105', 7), ('U106', 5)):
            pts = self.place_extra(key, x, -4464)
            top, bot = sorted(pts.values(), key=lambda v: v[0][1])
            (tx, ty), (bx, by) = top[0], bot[0]
            self.wires.append((tx, ty, tx, ty - 32))
            self.labels.append((tx, ty - 32, '5V', 'passive'))
            self.wires.append((bx, by, bx, by + 16))
            self.gnds.append((bx, by + 16))
            # texts beside the box (body 96 wide): the library puts them on its top / bottom edge
            self.prop_pos[key] = {'Reference': (x + 64, -4464 + 48, 'Left', 2), 'Value': (x + 64, -4464 + 80, 'Left', 2)}
            x += 224
        # spare units: every pin gets a no-connect
        x = -6304
        self.texts.append((-6320, -4176, 'Left', 2, 'spare units (not used)'))
        for key in (('U103', 3), ('U103', 4), ('U105', 3), ('U105', 4), ('U105', 5), ('U105', 6), ('U106', 4),
                    ('U26', 4)):
            self.place_extra(key, x, -4096 if key[0] != 'U26' else -4064)
            x += 160 if key[0] != 'U106' else 192
        # connectors: each pin gets a short stub and the label of its net
        self.texts.append((-6320, -2400, 'Left', 3, 'CONNECTORS'))
        for ref, x0 in (('J9', -6000), ('J10', -5440), ('J11', -4800)):
            pts = self.place_extra((ref, 1), x0, -2112)
            top = min(p[1] for p, d in pts.values())
            xs = sorted({p[0] for p, d in pts.values()})
            xc = (xs[0] + xs[-1]) // 2 if len(xs) > 1 else x0     # 2 columns: between them; 1: the body
            bot = max(p[1] for p, d in pts.values())
            self.prop_pos[(ref, 1)] = {'Reference': (xc, top - 56, 'Center', 2),
                                       'Value': (xc, top - 32, 'Center', 2) if len(xs) > 1 else (xc, bot + 40, 'Center', 2)}
            for num, (p, d) in pts.items():
                end = (p[0] + 48 * d[0], p[1] + 48 * d[1])
                self.wires.append((p[0], p[1], end[0], end[1]))
                net = self.kpin_net[(ref, num)]
                if net == 'GND':
                    self.gnds.append((end[0], end[1]))
                else:
                    self.labels.append((end[0], end[1], net, 'passive'))
        x = -6000
        for i in range(1, 9):
            self.place_extra(('H%d' % i, 1), x, -1664)
            x += 256                                        # "MountingHole_M3" is about 180 units wide
        # PWR_FLAGs on the nets the original had them on
        for flg, (ref, num) in (('#FLG01', ('J1', '1')), ('#FLG02', ('J2', '1')), ('#FLG05', ('U16', '3')),
                                ('#FLG03', ('U15', '11')), ('#FLG04', ('U15', '14')), ('#FLG06', ('U10', '11')),
                                ('#FLG07', ('U10', '14')), ('#FLG08', ('U8', '11')), ('#FLG09', ('U8', '14'))):
            p = self.kpins[(ref, num)]
            # 32 units out along the pin's wire (clear of the part), standing off the wire; text hidden
            ang = 0
            for w in self.wires:
                if p in ((w[0], w[1]), (w[2], w[3])):
                    d = seg_dir(w, p)
                    if abs(w[0] - w[2]) + abs(w[1] - w[3]) >= 48:
                        p = (p[0] + 32 * d[0], p[1] + 32 * d[1])
                        ang = 0 if d[1] == 0 else 90
                    break
            self.place_extra((flg, 1), p[0], p[1], ang)
            self.prop_pos[(flg, 1)] = {'Reference': 'hide', 'Value': 'hide'}

    def lt_texts(self):
        for t in self.a.texts:
            parts = t.split(' ', 5)
            body = parts[5]
            if not body.startswith(';'):
                continue                                   # SPICE directives stay in LTspice
            txt = body[1:]
            nl = chr(92) + 'n'                             # LTspice and KiCad both store a line break as \n
            lines = txt.split(nl)
            lines = [l for l in lines if l.strip() not in SIM_TEXT_DROP and not l.startswith('PWM duty =')]
            if not lines:
                continue
            self.texts.append((int(parts[1]), int(parts[2]), parts[3], int(parts[4]), nl.join(lines)))

    for f in (extras, lt_texts):
        setattr(Builder, f.__name__, f)


add_methods4()
