"""Hand layouts around the parts that keep KiCad's own library symbols (their pins are not where the LTspice symbols
have them). Coordinates are LTspice units relative to the LTspice part's origin, like the rest of build_kicad.py."""
import re
import kgeo
from build_kicad import kpin_off, pin_out_dir, ORIENTS, S


# ------------------------------------------------------------------------------------------------ helpers
def clear_box(b, x1, y1, x2, y2, keep_flags=()):
    """remove LTspice wires lying inside the box and the flags/texts there (the hand layout replaces them)"""
    ins = lambda p: x1 <= p[0] <= x2 and y1 <= p[1] <= y2
    b.wires = [w for w in b.wires if not (ins(w[:2]) and ins(w[2:]))]
    b.labels = [l for l in b.labels if not ins(l[:2]) or l[2] in keep_flags]
    b.gnds = [g for g in b.gnds if not ins(g[:2])]


def move_text(b, startswith, x, y):
    for i, t in enumerate(b.texts):
        if t[4].startswith(startswith):
            b.texts[i] = (x, y) + t[2:]
            return True
    return False


def place_unit(b, key, origin, ang=0, mir=None):
    """put a KiCad unit (any library) with its origin at `origin`; returns {pin number: (point, outward dir)}"""
    lib = b.libs[b.lib_of(key)]
    b.placed[key] = (ang, mir, origin[0], origin[1])
    out = {}
    for k in kgeo.lib_pins(lib, key[1]):
        o = kpin_off(k[2], k[3], ang, mir)
        p = (origin[0] + o[0], origin[1] + o[1])
        b.kpins[(key[0], k[0])] = p
        out[k[0]] = (p, pin_out_dir(k, ang, mir))
    return out


def place_two(b, name, pa, pb, texts='auto'):
    """2-pin converted part (res/cap/diode) with LTspice pin A/+ at pa and B/- at pb"""
    s = b.lt_by[name]
    key = b.kunit(name)
    pm = b.pin_map(s, key)
    first = 'A' if 'A' in pm else '+'
    second = 'B' if 'B' in pm else '-'
    lib = b.libs[b.lib_of(key)]
    kp = {k[0]: k for k in kgeo.lib_pins(lib, 1)}
    k1, k2 = kp[pm[first]], kp[pm[second]]
    for ang, mir in [(a, None) for a in (0, 90, 180, 270)]:
        o1 = kpin_off(k1[2], k1[3], ang, mir)
        o2 = kpin_off(k2[2], k2[3], ang, mir)
        if (o2[0] - o1[0], o2[1] - o1[1]) == (pb[0] - pa[0], pb[1] - pa[1]):
            origin = (pa[0] - o1[0], pa[1] - o1[1])
            place_unit(b, key, origin, ang, mir)
            mx, my = (pa[0] + pb[0]) // 2, (pa[1] + pb[1]) // 2
            if pa[1] == pb[1]:
                b.prop_pos[key] = {'Reference': (mx, my - 24, 'Bottom', 2), 'Value': (mx, my + 24, 'Top', 2)}
            else:
                b.prop_pos[key] = {'Reference': (mx + 24, my - 16, 'Left', 2), 'Value': (mx + 24, my + 16, 'Left', 2)}
            return
    raise SystemExit('cannot place %s between %s and %s' % (name, pa, pb))


def W(b, *pts):
    for p, q in zip(pts, pts[1:]):
        assert p[0] == q[0] or p[1] == q[1], ('diagonal', p, q)
        b.wires.append((p[0], p[1], q[0], q[1]))


def label(b, p, name, d, shape='passive'):
    b.labels.append((p[0], p[1], name, shape, d))


def gnd(b, p, d=(0, 1)):
    b.gnds.append((p[0], p[1], d))


def rel(c):
    return lambda dx, dy: (c[0] + dx, c[1] + dy)


def orient_for(b, key, want):
    """KiCad (angle, mirror) that puts the given pins at the given offsets from the origin"""
    lib = b.libs[b.lib_of(key)]
    kp = {k[0]: k for k in kgeo.lib_pins(lib, key[1])}
    for ang in (0, 90, 180, 270):
        for mir in (None, 'x', 'y'):
            if all(kpin_off(kp[n][2], kp[n][3], ang, mir) == tuple(o) for n, o in want.items()):
                return ang, mir
    raise SystemExit('no orientation of %s gives %s' % (key, want))


def texts_at(b, key, ref, val, size=2):
    """Reference / Value positions: (x, y, justify) or 'hide'"""
    f = lambda t: t if t == 'hide' else (t[0], t[1], t[2], size)
    b.prop_pos[key] = {'Reference': f(ref), 'Value': f(val)}


def move_texts_in(b, x1, y1, x2, y2, dx, dy):
    """move the comment texts anchored inside the box"""
    for i, t in enumerate(b.texts):
        if x1 <= t[0] <= x2 and y1 <= t[1] <= y2:
            b.texts[i] = (t[0] + dx, t[1] + dy) + tuple(t[2:])


def drop_labels(b, name, x1, y1, x2, y2):
    b.labels = [l for l in b.labels if not (l[2] == name and x1 <= l[0] <= x2 and y1 <= l[1] <= y2)]


# ------------------------------------------------------------------------------------------------ gate drivers
OUTPUT_DRIVERS = {  # driver: (input labels INA, INB, VCCI cap)
    'U15': ('M2_ON', 'ena_out_1', 'C62'),
    'U10': ('out_2_on', 'ena_out_2', 'C90'),
    'U8': ('out_3_on', 'ena_out_3', 'C89'),
}


def output_driver(b, name):
    ina, inb, cap = OUTPUT_DRIVERS[name]
    s = b.lt_by[name]
    c = (s.x, s.y)
    r = rel(c)
    clear_box(b, c[0] - 300, c[1] - 260, c[0] + 95, c[1] + 160)
    pins = place_unit(b, (name, 1), r(-64, 0))
    b.custom_done.add(name)
    # right side: join your bootstrap bus (x 160), source bus (x 208) and gate networks
    W(b, r(96, -128), r(160, -128), r(160, -80))           # VDDA
    W(b, r(96, -96), r(240, -96))                          # OUTA -> R/D network
    W(b, r(96, -64), r(208, -64), r(208, -16))             # VSSA
    W(b, r(96, 64), r(160, 64))                            # VDDB
    W(b, r(96, 96), r(304, 96), r(304, 64))                # OUTB -> R/D network
    W(b, r(96, 128), r(208, 128))                          # VSSB
    # left side in KiCad's pin order
    W(b, r(-224, -128), r(-288, -128), r(-288, -176))      # VCCI, 5V
    label(b, r(-288, -176), '5V', (0, -1))
    place_two(b, cap, r(-288, -128), r(-352, -128)) if b.lt_net_name.get((cap, 'A')) == '5V' else \
        place_two(b, cap, r(-352, -128), r(-288, -128))
    W(b, r(-352, -128), r(-352, -128))
    gnd(b, r(-352, -128), (-1, 0))
    W(b, r(-224, -32), r(-272, -32))
    label(b, r(-272, -32), ina, (-1, 0), 'input')
    W(b, r(-224, 0), r(-272, 0))
    label(b, r(-272, 0), inb, (-1, 0), 'input')
    gnd(b, r(-224, 32), (-1, 0))                           # DIS
    W(b, r(-224, 96), r(-272, 96))
    label(b, r(-272, 96), '5V', (-1, 0))                   # DT tied to VCCI
    gnd(b, r(-224, 128), (-1, 0))
    b.prop_pos[(name, 1)] = {'Reference': (c[0] - 64, c[1] - 200, 'Center', 2),
                             'Value': (c[0] - 64, c[1] - 176, 'Center', 2)}
    for i, t in enumerate(b.texts):
        if t[4] == 'gate driver' and abs(t[0] - c[0]) < 200 and abs(t[1] - c[1]) < 200:
            b.texts[i] = (c[0] - 300, c[1] - 236) + t[2:]


def m1_driver(b):
    s = b.lt_by['U19']
    c = (s.x, s.y)
    r = rel(c)
    clear_box(b, c[0] - 300, c[1] - 160, c[0] + 95, c[1] + 160)
    place_unit(b, ('U19', 1), r(-64, 0))
    b.custom_done.add('U19')
    W(b, r(96, -128), r(128, -128), r(128, -80))           # VDDA -> bootstrap/12V bus
    W(b, r(96, 64), r(128, 64), r(128, 16))                # VDDB
    W(b, r(96, -96), r(192, -96), r(192, -48))             # OUTA -> R15
    gnd(b, r(96, -64), (1, 0))                             # VSSA
    gnd(b, r(96, 128), (1, 0))                             # VSSB
    place_two(b, 'R62', r(176, 96), r(96, 96))             # OUTB -> R62 -> GND (R62 moves down with the pin)
    gnd(b, r(176, 96), (1, 0))
    W(b, r(-224, -128), r(-288, -128), r(-288, -176))
    label(b, r(-288, -176), '5V', (0, -1))
    cap = 'C48'
    if b.lt_net_name.get((cap, 'A')) == '5V':
        place_two(b, cap, r(-288, -128), r(-352, -128))
    else:
        place_two(b, cap, r(-352, -128), r(-288, -128))
    gnd(b, r(-352, -128), (-1, 0))
    W(b, r(-224, -32), r(-272, -32))
    label(b, r(-272, -32), 'M1_ON', (-1, 0), 'input')
    gnd(b, r(-224, 0), (-1, 0))                            # INB unused
    gnd(b, r(-224, 32), (-1, 0))                           # DIS
    W(b, r(-224, 96), r(-272, 96))
    label(b, r(-272, 96), '5V', (-1, 0))
    gnd(b, r(-224, 128), (-1, 0))
    b.prop_pos[('U19', 1)] = {'Reference': (c[0] - 64, c[1] + 184, 'Center', 2),
                              'Value': (c[0] - 64, c[1] + 208, 'Center', 2)}


# ------------------------------------------------------------------------------------------------ current sense
def current_sense(b):
    """U25 (INA241) and the shunt R1: KiCad pins land on your LTspice wires; GND, REF1, REF2 share one ground"""
    s = b.lt_by['U25']
    c = (s.x, s.y)
    r = rel(c)
    pins = place_unit(b, ('U25', 1), r(32, 0))        # +/- inputs exactly on your input wires
    b.custom_done.add('U25')
    assert pins['8'][0] == b.a.pin(s, 'IN+') and pins['1'][0] == b.a.pin(s, 'IN-')
    W(b, pins['7'][0], pins['3'][0])                   # REF1 -> REF2/GND bar (your GND symbol stays)
    texts_at(b, ('U25', 1), (r(144, 32)) + ('Left',), r(144, 56) + ('Left',))
    move_texts_in(b, c[0] + 60, c[1] + 100, c[0] + 100, c[1] + 120, 64, -8)     # "current sense ..." note
    # R1: pins 2/3 (Kelvin) up, force pins on your power wire
    s1 = b.lt_by['R1']
    key = ('R1', 1)
    pm = b.pin_map(s1, key)
    want = {pm['F1']: (-64, 0), pm['F2']: (64, 0), pm['S1']: (-32, -32), pm['S2']: (32, -32)}
    o = (s1.x + 32, s1.y)
    pins = place_unit(b, key, o, *orient_for(b, key, want))
    b.custom_done.add('R1')
    s1p = pins[pm['S1']][0]
    W(b, s1p, (s1p[0], s1p[1] - 32))                   # up onto the ISNS_P wire
    assert pins[pm['S2']][0] == b.a.pin(s1, 'S2')


# ------------------------------------------------------------------------------------------------ regulators
def l78l05(b, name):
    s = b.lt_by[name]
    u = (s.x, s.y)
    r = rel(u)
    pins = place_unit(b, (name, 1), u)                 # IN/OUT land on your input/output wires
    b.custom_done.add(name)
    gnd(b, pins['2'][0], (0, 1))
    texts_at(b, (name, 1), r(0, -64) + ('Center',), r(0, -40) + ('Center',))


# ------------------------------------------------------------------------------------------------ digital pots
def pot(b, name):
    """MCP4451 pot unit: its 3 pins on the left, on your B/A column; the box to the right of the column"""
    s = b.lt_by[name]
    p = (s.x, s.y)
    r = rel(p)
    key = b.kunit(name)
    pins = place_unit(b, key, r(96, 0))
    b.custom_done.add(key[0])
    pm = b.pin_map(s, key)
    bp, wp, ap = (pins[pm[n]][0] for n in ('B', 'W', 'A'))
    assert bp == r(0, -32) and wp == r(0, 0) and ap == r(0, 32), (name, bp, wp, ap)
    lt = {n: b.a.pin(s, n) for n in ('A', 'W', 'B')}
    W(b, bp, lt['B'])
    W(b, wp, lt['W'])
    W(b, ap, lt['A'])
    texts_at(b, key, r(176, -24) + ('Left',), r(32, 80) + ('Left',))
    move_texts_in(b, p[0] + 30, p[1] + 60, p[0] + 60, p[1] + 160, 0, 48)


def pot_control(b):
    """U26E (MCP4451 supply / I2C / address pins): drawn again around KiCad's wider unit, same parts and nets"""
    s = b.lt_by['U26E']
    e = (s.x, s.y)
    clear_box(b, e[0] - 216, e[1] - 192, e[0] + 184, e[1] + 256)
    o = (e[0] + 64, e[1])
    r = rel(o)
    pins = {n: v[0] for n, v in place_unit(b, ('U26', 5), o).items()}
    b.custom_done.add('U26')
    rail = o[1] - 192
    W(b, pins['17'], (o[0], rail))                     # VDD up to the 5V rail
    W(b, r(-256, -192), (o[0], rail))
    label(b, r(-96, -192), '5V', (0, -1))
    place_two(b, 'C26', r(-256, -192), r(-256, -128))  # VDD bypass
    gnd(b, r(-256, -128))
    b.prop_pos[b.kunit('C26')] = {'Reference': r(-280, -176) + ('Right', 2), 'Value': r(-280, -144) + ('Right', 2)}
    place_two(b, 'R103', r(-192, -192), r(-192, -112))  # RESET pull-up
    b.prop_pos[b.kunit('R103')] = {'Reference': r(-168, -176) + ('Left', 2), 'Value': r(-168, -144) + ('Left', 2)}
    W(b, r(-192, -112), r(-192, -96), pins['15'])
    W(b, pins['5'], r(-192, -32))
    label(b, r(-192, -32), 'SCL', (-1, 0))
    W(b, pins['6'], r(-256, 0))
    label(b, r(-256, 0), 'SDA', (-1, 0))
    W(b, pins['4'], r(-256, 64), r(-256, 112))         # HVC/A0 pull-down
    place_two(b, 'R102', r(-256, 112), r(-256, 192))
    gnd(b, r(-256, 192))
    b.prop_pos[b.kunit('R102')] = {'Reference': r(-280, 136) + ('Right', 2), 'Value': r(-280, 168) + ('Right', 2)}
    W(b, pins['16'], r(-208, 96), r(-208, 112))        # A1 pull-down
    place_two(b, 'R99', r(-208, 112), r(-208, 192))
    gnd(b, r(-208, 192))
    gnd(b, pins['7'])                                  # VSS
    texts_at(b, ('U26', 5), r(32, -144) + ('Left',), r(32, 144) + ('Left',))
    for i, t in enumerate(b.texts):
        if t[4].startswith('U26E: MCP4451 control unit'):
            b.texts[i] = r(-272, 256) + tuple(t[2:])


# ------------------------------------------------------------------------------------------------ counter / mux
def counter_mux(b):
    """U18 (4017) and U28 (4051) sit on your pin rows (the LTspice drawing was opened to KiCad's widths);
    here: the mux supply pins, and the OUT_n_ENA names taken off the three select wires so they do not stack"""
    s = b.lt_by['U28']
    a_pt = b.a.pin(s, 'IOC')
    o = (a_pt[0] + 96, a_pt[1] + 96)                   # KiCad A pin = your IOC point
    r = rel(o)
    pins = {n: v[0] for n, v in place_unit(b, ('U28', 1), o).items()}
    b.custom_done.add('U28')
    vdd = b.a.pin(s, 'VDD')
    W(b, pins['16'], (o[0], vdd[1] - 96), (vdd[0], vdd[1] - 96))      # VCC -> your C96 / 5V wire
    W(b, pins['8'], r(0, 224), r(32, 224), pins['7'])                  # GND + VEE
    gnd(b, r(16, 224))
    texts_at(b, ('U28', 1), r(-24, -184) + ('Right',), r(64, 208) + ('Left',))
    # OUT_n_ENA: names on short branches beside the select wires
    q = {n: b.a.pin(b.lt_by['U18'], n) for n in ('Q0', 'Q1', 'Q2')}
    for n, nm in (('Q0', 'OUT_1_ENA'), ('Q1', 'OUT_2_ENA'), ('Q2', 'OUT_3_ENA')):
        drop_labels(b, nm, q[n][0], q[n][1], o[0], q[n][1])
    x1 = q['Q0'][0] + 96
    label(b, (x1, q['Q0'][1]), 'OUT_1_ENA', (0, -1))
    label(b, (x1, q['Q2'][1]), 'OUT_3_ENA', (0, 1))
    x2 = q['Q1'][0] + 176
    W(b, (x2, q['Q1'][1]), (x2, q['Q1'][1] + 80))       # crosses the Q2 wire (no dot: not connected)
    label(b, (x2, q['Q1'][1] + 80), 'OUT_2_ENA', (0, 1))


def apply(b):
    b.custom_done = set()
    for n in OUTPUT_DRIVERS:
        output_driver(b, n)
    m1_driver(b)
    current_sense(b)
    l78l05(b, 'U1')
    l78l05(b, 'U17')
    for n in ('U26A', 'U26B', 'U26C'):
        pot(b, n)
    pot_control(b)
    counter_mux(b)
    # the generic stage must not route these parts' pins: their LTspice pin points are gone
    keep = []
    for m in b.moved:
        if m[0][0] in b.custom_done:
            b.dead.add(m[3])
        else:
            keep.append(m)
    b.moved = keep
    b.unmapped = [u for u in b.unmapped if u[0][0] not in b.custom_done]
