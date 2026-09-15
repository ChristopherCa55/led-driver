"""Apply the HANDOFF_PROMPT.md section 4 schematic changes to a copy of BOOST.kicad_sch.

  schedit.py SRC.kicad_sch DST.kicad_sch ASSIGN_IN.json ASSIGN_OUT.json

Every deletion is checked against the wire geometry traced beforehand, every new
connection point is checked to be free before anything is placed there, and all
edits are applied as text splices so the rest of the file stays byte-identical.
Connectivity is then verified from a kicad-cli netlist export, not from here.
"""
import sys, os, re, json, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from schlib import Sheet, kids, kid, head as head_of

Sheet.ORDER = 'rotate_first'
SRC, DST, ASSIGN_IN, ASSIGN_OUT = sys.argv[1:5]
KSYM = r'C:\Program Files\KiCad\10.0\share\kicad\symbols'

s = Sheet(SRC)
T = s.text
ROOT_UUID = str(kid(s.root, 'uuid')[1])
edits = []          # (start, end, replacement)
log = []


def nu():
    return str(uuid.uuid4())


def span_from(pos, headword):
    j = T.rfind('\n\t(' + headword, 0, pos)
    assert j >= 0, headword
    a = j + 2
    d, k, ins = 0, a, False
    while True:
        c = T[k]
        if ins:
            if c == chr(92):
                k += 1
            elif c == '"':
                ins = False
        elif c == '"':
            ins = True
        elif c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                return a, k + 1
        k += 1


def span_uuid(u, headword):
    key = '(uuid "%s")' % u
    assert T.count(key) == 1, (u, T.count(key))
    a, b = span_from(T.find(key), headword)
    assert T.startswith('(' + headword, a), (headword, T[a:a + 20])
    return a, b


# ---------------------------------------------------------------- indexes
wire_nodes = kids(s.root, 'wire')
wire_uuid = [str(kid(w, 'uuid')[1]) for w in wire_nodes]
infos = [s.inst_info(i) for i in s.instances]
by_ref = {}
for inf, node in zip(infos, s.instances):
    by_ref.setdefault(inf['ref'], []).append((inf, str(kid(node, 'uuid')[1])))


def one(ref):
    r = by_ref[ref]
    assert len(r) == 1, ref
    return r[0]


def pin_pos(ref, num):
    inf, _ = one(ref)
    return [p['pos'] for p in inf['pins'] if p['number'] == num][0]


def near(a, b):
    return abs(a[0] - b[0]) < 1e-3 and abs(a[1] - b[1]) < 1e-3


# ---------------------------------------------------------------- deletions
def delete_wire(idx, p0, p1):
    pts = s.wires[idx]
    assert (near(pts[0], p0) and near(pts[1], p1)) or (near(pts[0], p1) and near(pts[1], p0)), (idx, pts, p0, p1)
    a, b = span_uuid(wire_uuid[idx], 'wire')
    edits.append((a - 1, b, ''))


def delete_symbol(ref):
    inf, u = one(ref)
    a, b = span_uuid(u, 'symbol')
    edits.append((a - 1, b, ''))
    log.append('deleted %s (%s)' % (ref, inf['lib_id']))


WIRES = {
    'R1 stub pin2': (283, (199.39, 134.62), (198.12, 134.62)),
    'R1 stub pin1': (348, (205.74, 134.62), (207.01, 134.62)),
    'U25.1 a': (127, (237.49, 102.87), (232.41, 102.87)), 'U25.1 b': (583, (232.41, 102.87), (232.41, 104.14)),
    'U25.1 c': (692, (232.41, 104.14), (232.41, 118.11)), 'U25.1 d': (495, (232.41, 118.11), (207.01, 118.11)),
    'U25.1 e': (325, (207.01, 118.11), (207.01, 134.62)),
    'U25.8 a': (515, (237.49, 97.79), (228.6, 97.79)), 'U25.8 b': (294, (228.6, 97.79), (228.6, 99.06)),
    'U25.8 c': (151, (228.6, 99.06), (228.6, 115.57)), 'U25.8 d': (497, (228.6, 115.57), (196.85, 115.57)),
    'U25.8 e': (189, (196.85, 115.57), (196.85, 134.62)),
    'D12 1a': (322, (411.48, 147.32), (411.48, 146.05)), 'D12 1b': (387, (411.48, 146.05), (403.86, 146.05)),
    'D12 2a': (150, (411.48, 152.4), (411.48, 153.67)), 'D12 2b': (754, (411.48, 153.67), (408.94, 153.67)),
    'U6.4 a': (527, (267.97, 209.55), (265.43, 209.55)), 'U6.4 b': (555, (265.43, 209.55), (265.43, 214.63)),
    'U6.4 c': (49, (265.43, 214.63), (283.21, 214.63)), 'U6.4 d': (803, (283.21, 214.63), (283.21, 213.36)),
    'U6.4 e': (856, (283.21, 213.36), (285.75, 213.36)),
    'U11.4 a': (21, (269.24, 139.7), (265.43, 139.7)), 'U11.4 b': (143, (265.43, 139.7), (265.43, 144.78)),
    'U11.4 c': (139, (265.43, 144.78), (283.21, 144.78)), 'U11.4 d': (561, (283.21, 144.78), (283.21, 143.51)),
    'U11.4 e': (513, (283.21, 143.51), (285.75, 143.51)),
    'U12.4 a': (320, (273.05, 175.26), (270.51, 175.26)), 'U12.4 b': (103, (270.51, 175.26), (270.51, 180.34)),
    'U12.4 c': (735, (270.51, 180.34), (280.67, 180.34)), 'U12.4 d': (744, (280.67, 180.34), (280.67, 179.07)),
    'U12.4 e': (41, (280.67, 179.07), (289.56, 179.07)),
}
deleted_wires = set()
for name, (idx, p0, p1) in WIRES.items():
    delete_wire(idx, p0, p1)
    deleted_wires.add(idx)
log.append('deleted %d wires' % len(WIRES))

# confirm the pins we re-use sit where the trace said
assert near(pin_pos('U25', '1'), (237.49, 102.87)) and near(pin_pos('U25', '8'), (237.49, 97.79))
assert near(pin_pos('U6', '4'), (267.97, 209.55)) and near(pin_pos('U11', '4'), (269.24, 139.7)) and near(pin_pos('U12', '4'), (273.05, 175.26))
assert near(pin_pos('D1', '1'), (463.55, 123.19)) and near(pin_pos('J9', '1'), (298.45, 331.47)) and near(pin_pos('J9', '10'), (298.45, 354.33))
delete_symbol('D12')
delete_symbol('R1')

# labels that sat only on deleted wiring would dangle: move rsense_lo, refuse anything else
moved_labels = []
for gl in kids(s.root, 'global_label') + kids(s.root, 'label'):
    at = kid(gl, 'at')
    pt = (float(at[1]), float(at[2]))
    items = s.touching(pt)
    wires_here = [it for it in items if it[0] in ('wire', 'wire_mid')]
    kept = [it for it in items
            if not (it[0] in ('wire', 'wire_mid') and it[1] in deleted_wires) and it[0] not in ('global_label', 'label')]
    pins_here = [inf['ref'] for inf in infos if inf['ref'] not in ('R1', 'D12') for q in inf['pins'] if near(q['pos'], pt)]
    if wires_here and not kept and not pins_here:
        name = str(gl[1])
        assert name == 'rsense_lo', ('label would dangle', name, pt)
        la, lb = span_uuid(str(kid(gl, 'uuid')[1]), head_of(gl))
        edits.append((la - 1, lb, ''))
        moved_labels.append((name, pt))
log.append('labels on deleted wiring (removed): %s' % moved_labels)


def free(pt, allow_deleted_wire=True):
    """Nothing survives at pt: no pin of a kept symbol, no kept wire or label."""
    for it in s.touching(pt):
        if it[0] in ('wire', 'wire_mid') and it[1] in deleted_wires:
            continue
        return False
    for inf in infos:
        if inf['ref'] in ('R1', 'D12'):
            continue
        for p in inf['pins']:
            if near(p['pos'], pt):
                return False
    return True


def only_pin(ref, num):
    """The pin ref.num is the only thing left at its position (its old wiring is being deleted)."""
    pt = pin_pos(ref, num)
    for it in s.touching(pt):
        if it[0] in ('wire', 'wire_mid') and it[1] in deleted_wires:
            continue
        return False
    others = [inf['ref'] + '.' + p['number'] for inf in infos for p in inf['pins'] if near(p['pos'], pt)]
    return others == [ref + '.' + num]


def attach_ok(pt):
    """pt is an existing connection point (kept wire end / junction)."""
    return any(it[0] in ('wire', 'junction') and (it[0] == 'junction' or it[1] not in deleted_wires) for it in s.touching(pt))


# ---------------------------------------------------------------- property edits
block_mods = {}


def modify(ref, fn):
    inf, u = one(ref)
    a, b = span_uuid(u, 'symbol')
    cur = block_mods.get((a, b), T[a:b])
    block_mods[(a, b)] = fn(cur)


def set_prop(ref, name, old, new):
    def fn(blk):
        key = '(property "%s" "%s"' % (name, old)
        assert blk.count(key) == 1, (ref, name, old)
        return blk.replace(key, '(property "%s" "%s"' % (name, new))
    modify(ref, fn)
    log.append('%s %s: %s -> %s' % (ref, name, old, new))


def add_hidden_prop(ref, name, value):
    def fn(blk):
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
        x, y = at.group(1), at.group(2)
        prop = ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
                '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n' % (name, value, x, y))
        i = blk.find('\t\t(pin ')
        assert i > 0
        return blk[:i] + prop + blk[i:]
    modify(ref, fn)
    log.append('%s + %s = %s' % (ref, name, value))


set_prop('R15', 'Value', '5.1', '10')
for r in ('R13', 'R23', 'R47'):
    set_prop(r, 'Value', '100', '150')
for m in ['M%d' % i for i in range(1, 11)]:
    set_prop(m, 'Footprint', 'Package_TO_SOT_THT:TO-220-3_Horizontal_TabDown', 'Package_TO_SOT_THT:TO-220-3_Horizontal_TabUp')
for c in ('C70', 'C86', 'C88', 'C71', 'C78', 'C87', 'C74', 'C75', 'C77'):
    inf, _ = one(c)
    assert inf['value'] in ('220µ', '220\u00b5'), (c, inf['value'])
    set_prop(c, 'Footprint', 'Capacitor_SMD:CP_Elec_10x10.5', 'BOOST:CP_Elec_10x16.5')
    add_hidden_prop(c, 'MPN', 'EEH-ZU1H221P')
for c in ('C40', 'C69', 'C85'):
    inf, _ = one(c)
    assert inf['footprint'] == 'Capacitor_SMD:CP_Elec_10x12.5', (c, inf['footprint'])
    add_hidden_prop(c, 'MPN', 'EEH-ZU1E681UP')
    add_hidden_prop(c, 'LCSC', 'C29664285')


# J9: 1x10 -> 1x11 right-angle, pins 1-10 kept in place
def j9(blk):
    reps = [('(lib_id "Connector_Generic:Conn_01x10")', '(lib_id "Connector_Generic:Conn_01x11")'),
            ('(at 303.53 341.63 0)', '(at 303.53 344.17 0)'),
            ('(at 306.07 341.6299 0)', '(at 306.07 344.1699 0)'),
            ('(property "Value" "Conn_01x10"\n\t\t\t(at 306.07 344.1699 0)', '(property "Value" "Conn_01x11"\n\t\t\t(at 306.07 346.7099 0)'),
            ('"Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical"', '"Connector_PinHeader_2.54mm:PinHeader_1x11_P2.54mm_Horizontal"'),
            ('single row, 01x10,', 'single row, 01x11,')]
    for old, new in reps:
        n = blk.count(old)
        assert n >= 1, old
        blk = blk.replace(old, new)
    i = blk.find('\t\t(instances')
    return blk[:i] + '\t\t(pin "11"\n\t\t\t(uuid "%s")\n\t\t)\n' % nu() + blk[i:]


modify('J9', j9)
log.append('J9 -> Conn_01x11, PinHeader_1x11_P2.54mm_Horizontal, pin 11 added')


# UCC21520DW VSSA: power_in -> passive (floating high-side reference, not ground)
def lib_span(name):
    key = '\n\t\t(symbol "%s"' % name
    i = T.find(key)
    assert i > 0, name
    a = i + 1
    d, k = 0, a
    while True:
        c = T[k]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                return a, k + 1
        k += 1


a, b = lib_span('Driver_FET:UCC21520DW')
blk = T[a:b]
k = blk.find('(name "VSSA"')
p = blk.rfind('(pin power_in', 0, k)
assert p > 0
blk = blk[:p] + '(pin passive' + blk[p + len('(pin power_in'):]
block_mods[(a, b)] = blk
log.append('UCC21520DW pin 14 VSSA type power_in -> passive')

for (a, b), txt in block_mods.items():
    edits.append((a, b, txt))


# ---------------------------------------------------------------- library symbols to add
def kicad_lib_symbol(lib, name):
    t = open(os.path.join(KSYM, lib + '.kicad_sym'), encoding='utf8').read()
    i = t.find('\n\t(symbol "%s"' % name)
    assert i >= 0, name
    a = i + 1
    d, k = 0, a
    while True:
        c = t[k]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                break
        k += 1
    blk = t[a:k + 1]
    blk = blk.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (lib, name), 1)
    return '\t' + blk.replace('\n', '\n\t')


new_libs = []
for lib, name in (('Device', 'R_Shunt'), ('Device', 'NetTie_2'), ('Connector_Generic', 'Conn_01x11'),
                  ('Connector_Generic', 'Conn_02x15_Odd_Even'), ('Mechanical', 'MountingHole')):
    if '(symbol "%s:%s"' % (lib, name) not in T:
        new_libs.append(kicad_lib_symbol(lib, name))
la, lb = lib_span('Connector_Generic:Conn_01x10')  # any lib symbol: insert after it
edits.append((lb, lb, '\n' + '\n'.join(new_libs)))
log.append('lib symbols added: %d' % len(new_libs))

# load pin tables for placement of new-lib instances
s_libpins = {}
for lib, name in (('Device', 'R_Shunt'), ('Device', 'NetTie_2'), ('Connector_Generic', 'Conn_02x15_Odd_Even')):
    blk = kicad_lib_symbol(lib, name)
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)(?:.|\n)*?\(number "([^"]*)"', blk):
        pins[m.group(4)] = (float(m.group(1)), float(m.group(2)))
    s_libpins['%s:%s' % (lib, name)] = pins


def place(lib_id, X, Y, rot, num):
    px, py = s_libpins[lib_id][num]
    return Sheet.xform(px, py, X, Y, rot, None)


# ---------------------------------------------------------------- new blocks
new_blocks = []


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def prop_text(name, value, x, y, hide=False, justify=None, size='1.27 1.27'):
    j = '\t\t\t\t(justify %s)\n' % justify if justify else ''
    h = '\t\t\t(hide yes)\n' if hide else ''
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n%s\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
            '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size %s)\n\t\t\t\t)\n%s\t\t\t)\n\t\t)\n' % (name, value, fmt(x), fmt(y), h, size, j))


def instance(lib_id, ref, value, footprint, X, Y, rot, pins, extra=(), desc='', sim_exclude='no', ref_hidden=False):
    out = ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s %s)\n\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim %s)\n'
           '\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n\t\t(uuid "%s")\n'
           % (lib_id, fmt(X), fmt(Y), fmt(rot), sim_exclude, nu()))
    out += prop_text('Reference', ref, X + 2.54, Y - 1.27, hide=ref_hidden, justify='left')
    out += prop_text('Value', value, X + 2.54, Y + 1.27, justify='left')
    out += prop_text('Footprint', footprint, X, Y, hide=True)
    out += prop_text('Datasheet', '', X, Y, hide=True)
    out += prop_text('Description', desc, X, Y, hide=True)
    for n, v in extra:
        out += prop_text(n, v, X, Y, hide=True)
    for pnum in pins:
        out += '\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)\n' % (pnum, nu())
    out += ('\t\t(instances\n\t\t\t(project "BOOST"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n'
            '\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)' % (ROOT_UUID, ref))
    return out


def glabel(name, pt, angle):
    just = 'right' if angle in (180, 270) else 'left'
    return ('\t(global_label "%s"\n\t\t(shape bidirectional)\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.0668 1.0668)\n'
            '\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t\t(property "Intersheetrefs" "${INTERSHEET_REFS}"\n'
            '\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n'
            '\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)' % (name, fmt(pt[0]), fmt(pt[1]), angle, just, nu(), fmt(pt[0]), fmt(pt[1])))


used_points = []


def label(name, pt, angle, must_attach=False):
    if must_attach:
        assert attach_ok(pt) or any(near(pt, p) for p in used_points), ('label must attach', name, pt)
    new_blocks.append(glabel(name, pt, angle))
    log.append('label %s at %s' % (name, pt))


def clone(template_ref, new_ref, X, Y, value=None, footprint=None):
    """Copy an existing ltspice:res / ltspice:diode / power:GND instance to a new place and reference."""
    inf, u = one(template_ref)
    a, b = span_uuid(u, 'symbol')
    blk = T[a:b]
    X0, Y0, rot = inf['at']
    dx, dy = X - X0, Y - Y0

    def shift(m):
        return '(at %s %s %s)' % (fmt(float(m.group(1)) + dx), fmt(float(m.group(2)) + dy), m.group(3))
    blk = re.sub(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', shift, blk)
    blk = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % nu(), blk)
    blk = blk.replace('"%s"' % template_ref, '"%s"' % new_ref)
    if value is not None:
        blk = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "%s"' % value, blk, count=1)
    if footprint is not None:
        blk = re.sub(r'\(property "Footprint" "[^"]*"', '(property "Footprint" "%s"' % footprint, blk, count=1)
    new_blocks.append(blk)
    lib_pins = s.lib_pins(inf['lib_id'], 1)
    return {p['number']: Sheet.xform(p['x'], p['y'], X, Y, rot, inf['mirror']) for p in lib_pins}


pwr = [42]


def gnd_at(pt, rot):
    ref = '#PWR%03d' % pwr[0]
    pwr[0] += 1
    inf, u = one('#PWR021')
    a, b = span_uuid(u, 'symbol')
    blk = T[a:b]
    X0, Y0, r0 = inf['at']
    blk = blk.replace('(at %s %s %s)' % (fmt(X0), fmt(Y0), fmt(r0)), '(at %s %s %d)' % (fmt(pt[0]), fmt(pt[1]), rot), 1)
    blk = re.sub(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', lambda m: '(at %s %s %s)' % (fmt(pt[0]), fmt(pt[1]), m.group(3)), blk)
    blk = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % nu(), blk)
    blk = blk.replace('"#PWR021"', '"%s"' % ref)
    new_blocks.append(blk)
    return ref


# ---- R1: four-terminal shunt on the two existing junctions (force pins 10.16 mm apart)
X, Y, ROT = 201.93, 134.62, 90
p1, p2, p3, p4 = (place('Device:R_Shunt', X, Y, ROT, n) for n in '1234')
assert near(p1, (196.85, 134.62)) and near(p4, (207.01, 134.62)), (p1, p4)
assert attach_ok(p1) and attach_ok(p4)
assert free(p2) and free(p3), (p2, p3)
new_blocks.append(instance('Device:R_Shunt', 'R1', '2m', 'BOOST:R_Bourns_CSS4J-4026', X, Y, ROT, '1234',
                           extra=(('MPN', 'CSS4J-4026K-2L00F'), ('LCSC', 'C2076167')),
                           desc='2 mOhm 4-terminal current sense shunt, Bourns CSS4J-4026 (pins 1,4 current; 2,3 sense)'))
log.append('R1 -> Device:R_Shunt at (%s, %s) rot %d; force pins on Vin/rsense_lo junctions' % (X, Y, ROT))
label('rsense_lo', p4, 90, must_attach=True)   # net name; the original label was on the deleted U25.1 run
label('ISNS_P', p2, 90)
label('ISNS_N', p3, 90)
assert only_pin('U25', '8') and only_pin('U25', '1')
label('ISNS_P', pin_pos('U25', '8'), 180)
label('ISNS_N', pin_pos('U25', '1'), 180)

# ---- sink sense net-ties at the shunt top junctions
for nt, junction, op, sns in (('NT1', (285.75, 143.51), 'U11', 'SNS_CH1'),
                              ('NT2', (289.56, 179.07), 'U12', 'SNS_CH2'),
                              ('NT3', (285.75, 213.36), 'U6', 'SNS_CH3')):
    X, Y = junction[0] - 2.54, junction[1]
    q1, q2 = place('Device:NetTie_2', X, Y, 0, '1'), place('Device:NetTie_2', X, Y, 0, '2')
    assert near(q2, junction) and attach_ok(q2), (nt, q2)
    assert free(q1), (nt, q1)
    new_blocks.append(instance('Device:NetTie_2', nt, 'NetTie_2', 'NetTie:NetTie-2_SMD_Pad0.5mm', X, Y, 0, '12',
                               desc='Net tie: %s senses the shunt pad directly' % op, sim_exclude='yes'))
    label(sns, q1, 180)
    assert only_pin(op, '4')
    label(sns, pin_pos(op, '4'), 180)
    log.append('%s pin 2 on shunt junction %s, pin 1 = %s; %s.4 -> %s' % (nt, junction, sns, op, sns))

# ---- M1 inhibit: name the D1/D15/D24 node, add Arduino pin 11, diode, pull-down
label('M1_INHIBIT', pin_pos('D1', '1'), 180, must_attach=True)
j9p11 = (298.45, 356.87)
assert free(j9p11)
label('ARD_M1_INHIBIT', j9p11, 180)
dp = clone('D22', 'D27', 330.2, 364.49, value='D', footprint='Diode_SMD:D_SOD-123')
rp = clone('R41', 'R105', 345.44, 363.22, value='100k', footprint='Resistor_SMD:R_0603_1608Metric')
for pt in list(dp.values()) + list(rp.values()):
    assert free(pt), pt
label('ARD_M1_INHIBIT', dp['2'], 90)    # anode (+)
label('M1_INHIBIT', dp['1'], 270)       # cathode (-)
label('ARD_M1_INHIBIT', rp['1'], 90)
gnd_at(rp['2'], 0)
log.append('D27 anode ARD_M1_INHIBIT cathode M1_INHIBIT; R105 100k ARD_M1_INHIBIT-GND')

# ---- J10 / J11 stacking header and socket
PINOUT = {1: 'GND', 2: 'GND', 3: 'M1_ON', 4: 'M2_ON', 5: 'ena_out_1', 6: 'out_2_on', 7: 'ena_out_2', 8: 'out_3_on',
          9: 'ena_out_3', 10: '5V', 11: 'GND', 12: 'GND', 13: 'Vout_1', 14: 'Output1_drain', 15: 'Vout_2', 16: 'Output2_drain',
          17: 'Vout_3', 18: 'Output3_drain', 19: '12V', 20: 'GND', 21: 'GND', 22: 'analog_5V', 23: 'Current', 24: 'GND',
          25: 'GND', 26: 'IREF1_input', 27: 'IREF2_input', 28: 'GND', 29: 'GND', 30: 'IREF3_input'}
assert len(PINOUT) == 30 and list(PINOUT.values()).count('GND') == 10
for ref, X, fp, desc in (('J10', 203.2, 'Connector_PinHeader_2.54mm:PinHeader_2x15_P2.54mm_Vertical',
                          'Board-to-board stacking header, power board top side (mates with J11 pin for pin)'),
                         ('J11', 254.0, 'Connector_PinSocket_2.54mm:PinSocket_2x15_P2.54mm_Vertical',
                          'Board-to-board socket, control card underside (mates with J10 pin for pin)')):
    Y = 375.92
    pts = {n: place('Connector_Generic:Conn_02x15_Odd_Even', X, Y, 0, str(n)) for n in range(1, 31)}
    for n, pt in pts.items():
        assert free(pt), (ref, n, pt)
    new_blocks.append(instance('Connector_Generic:Conn_02x15_Odd_Even', ref, 'Conn_02x15_2.54mm', fp, X, Y, 0,
                               [str(n) for n in range(1, 31)], desc=desc, sim_exclude='yes'))
    for n, net in PINOUT.items():
        odd = n % 2 == 1
        if net == 'GND':
            gnd_at(pts[n], 270 if odd else 90)
        else:
            label(net, pts[n], 180 if odd else 0)
    log.append('%s placed with the 30-pin pinout' % ref)

# ---- mounting holes: H1-H4 control card, H5-H8 power-board standoffs
for i in range(8):
    ref = 'H%d' % (i + 1)
    board = 'control card M3 mounting hole' if i < 4 else 'power board M3 standoff hole'
    new_blocks.append(instance('Mechanical:MountingHole', ref, 'MountingHole_M3', 'MountingHole:MountingHole_3.2mm_M3',
                               295.64 + 10.16 * i, 381.0, 0, [], desc=board + ' (nylon standoff, not plated, isolated)',
                               sim_exclude='yes'))
log.append('H1-H8 mounting holes added')

# ---------------------------------------------------------------- apply
ins = T.find('\n\t(sheet_instances')
assert ins > 0
edits.append((ins, ins, '\n' + '\n'.join(new_blocks)))
edits.sort(key=lambda e: (e[0], e[1]))
for (a1, b1, _), (a2, b2, _) in zip(edits, edits[1:]):
    assert b1 <= a2, ('overlapping edits', a1, b1, a2, b2)
out = T
for a, b, txt in sorted(edits, key=lambda e: -e[0]):
    out = out[:a] + txt + out[b:]
open(DST, 'w', encoding='utf8', newline='').write(out)

assign = json.load(open(ASSIGN_IN))
assign.pop('D12', None)
for r in ('R9', 'R35', 'R43', 'R25', 'R87', 'R94'):
    assign[r] = 'CONTROL'
for r in ('NT1', 'NT2', 'NT3', 'J10'):
    assign[r] = 'POWER'
for r in ('J11', 'D27', 'R105', 'H1', 'H2', 'H3', 'H4'):
    assign[r] = 'CONTROL'
for r in ('H5', 'H6', 'H7', 'H8'):
    assign[r] = 'POWER'
json.dump(assign, open(ASSIGN_OUT, 'w'), indent=1, sort_keys=True)
log.append('assignment: %d refs (%s)' % (len(assign), {b: list(assign.values()).count(b) for b in ('POWER', 'CONTROL')}))
print('\n'.join(log))
print('wrote %s (%d -> %d bytes)' % (DST, len(T), len(out)))
