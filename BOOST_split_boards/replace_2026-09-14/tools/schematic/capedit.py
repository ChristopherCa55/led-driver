"""2026-09-15 schematic changes: regulator bulk capacitors and the IREF filter capacitors.

  capedit.py SRC.kicad_sch DST.kicad_sch ASSIGN_IN.json ASSIGN_OUT.json

- C30 (LM2940 12 V output): 47 uF solid tantalum Vishay TR3D476K025C0250 (case D 7343-31, ESR <= 0.25 ohm),
  LCSC C4979367. Pin 1 is on 12V, so the tantalum footprint's pad 1 (anode) lands on 12V.
- C7, C55 (L78L05 outputs 5V / analog_5V): 22 uF X7R 25 V 1210 Murata GRM32ER71E226KE15L, LCSC C21397.
- C45, C44, C41: 1 nF C0G 0603 from IREF1_input / IREF2_input / IREF3_input to GND, at the sink op-amp
  inputs (U11 / U12 / U6) on the power board. Clones of C100; each placed on a free spot beside its op-amp,
  pin 1 by a global label of the IREF net, pin 2 by a GND symbol.
Edits are text splices (everything else byte-identical); every new connection point and the area of every
new symbol is checked to be empty first. Connectivity is verified afterwards from a kicad-cli netlist.
"""
import sys, os, re, json, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from schlib import Sheet, kid

SRC, DST, ASSIGN_IN, ASSIGN_OUT = sys.argv[1:5]
s = Sheet(SRC)
T = s.text
MU = 'µ'
edits, new_blocks, log = [], [], []
infos = [s.inst_info(i) for i in s.instances]
by_ref = {}
for inf, node in zip(infos, s.instances):
    by_ref.setdefault(inf['ref'], []).append((inf, str(kid(node, 'uuid')[1])))


def nu():
    return str(uuid.uuid4())


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def one(ref):
    r = by_ref[ref]
    assert len(r) == 1, ref
    return r[0]


def span_uuid(u, headword):
    key = '(uuid "%s")' % u
    assert T.count(key) == 1, (u, T.count(key))
    pos = T.find(key)
    j = T.rfind('\n\t(' + headword, 0, pos)
    a = j + 2
    d, k, ins = 0, a, False
    while True:
        c = T[k]
        if ins:
            if c == '\\':
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


block_mods = {}


def modify(ref, fn):
    inf, u = one(ref)
    a, b = span_uuid(u, 'symbol')
    block_mods[(a, b)] = fn(block_mods.get((a, b), T[a:b]))


def set_prop(ref, name, old, new):
    def fn(blk):
        key = '(property "%s" "%s"' % (name, old)
        assert blk.count(key) == 1, (ref, name, old)
        return blk.replace(key, '(property "%s" "%s"' % (name, new))
    modify(ref, fn)
    log.append('%s %s: %s -> %s' % (ref, name, old, new))


def add_hidden_prop(ref, name, value):
    def fn(blk):
        assert '(property "%s"' % name not in blk, (ref, name)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
        prop = ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
                '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n' % (name, value, at.group(1), at.group(2)))
        i = blk.find('\t\t(pin ')
        assert i > 0
        return blk[:i] + prop + blk[i:]
    modify(ref, fn)
    log.append('%s + %s = %s' % (ref, name, value))


def near(a, b):
    return abs(a[0] - b[0]) < 1e-3 and abs(a[1] - b[1]) < 1e-3


def area_empty(l, t, r, b):
    """No pin, symbol origin, wire (point or crossing), label, junction or no-connect inside the box."""
    def inside(p):
        return l <= p[0] <= r and t <= p[1] <= b
    for inf in infos:
        if inside(inf['at'][:2]) or any(inside(p['pos']) for p in inf['pins']):
            return False
    for pts in s.wires:
        if any(inside(p) for p in pts):
            return False
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        if min(x0, x1) <= r and max(x0, x1) >= l and min(y0, y1) <= b and max(y0, y1) >= t:
            return False
    for kind, name, p in s.labels:
        if inside(p):
            return False
    return not any(inside(p) for p in s.junctions + s.no_connects)


# ---- regulator bulk capacitors
for ref in ('C30', 'C7', 'C55'):
    inf, _ = one(ref)
    assert inf['value'] == '47' + MU and inf['footprint'] == 'Capacitor_SMD:CP_Elec_6.3x5.4', (ref, inf['value'], inf['footprint'])
set_prop('C30', 'Footprint', 'Capacitor_SMD:CP_Elec_6.3x5.4', 'Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D')
add_hidden_prop('C30', 'MPN', 'TR3D476K025C0250')
add_hidden_prop('C30', 'LCSC', 'C4979367')
for ref in ('C7', 'C55'):
    set_prop(ref, 'Value', '47' + MU, '22' + MU)
    set_prop(ref, 'Footprint', 'Capacitor_SMD:CP_Elec_6.3x5.4', 'Capacitor_SMD:C_1210_3225Metric')
    add_hidden_prop(ref, 'MPN', 'GRM32ER71E226KE15L')
    add_hidden_prop(ref, 'LCSC', 'C21397')

# ---- IREF filter capacitors, cloned from C100 (ltspice:cap, pin 1 at (+1.27, 0), pin 2 at (+1.27, +5.08))
assert not any(r in by_ref for r in ('C41', 'C44', 'C45')), 'C41/C44/C45 already exist'
tmpl, tu = one('C100')
ta, tb = span_uuid(tu, 'symbol')
TBLK = T[ta:tb]
X0, Y0, R0 = tmpl['at']
assert R0 == 0 and tmpl['mirror'] is None
tp = {p['number']: p['pos'] for p in tmpl['pins']}
assert sorted(tp) == ['1', '2'] and near(tp['1'], (X0 + 1.27, Y0)) and near(tp['2'], (X0 + 1.27, Y0 + 5.08)), tp
gi, gu = one('#PWR021')
ga, gb = span_uuid(gu, 'symbol')
GBLK = T[ga:gb]
GX, GY, GR = gi['at']
pwr = [max(int(m) for m in re.findall(r'"#PWR(\d+)"', T)) + 1]


def clone_cap(ref, X, Y):
    dx, dy = X - X0, Y - Y0
    blk = re.sub(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)',
                 lambda m: '(at %s %s %s)' % (fmt(float(m.group(1)) + dx), fmt(float(m.group(2)) + dy), m.group(3)), TBLK)
    blk = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % nu(), blk)
    assert blk.count('"C100"') >= 1
    blk = blk.replace('"C100"', '"%s"' % ref)
    blk = re.sub(r'\(property "Description" "[^"]*"', '(property "Description" "1 nF C0G: IREF filter at the sink op-amp input"', blk, count=1)
    new_blocks.append(blk)
    return (X + 1.27, Y), (X + 1.27, Y + 5.08)


def gnd_at(pt):
    ref = '#PWR%03d' % pwr[0]
    pwr[0] += 1
    blk = re.sub(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)',
                 lambda m: '(at %s %s %s)' % (fmt(pt[0] + float(m.group(1)) - GX), fmt(pt[1] + float(m.group(2)) - GY),
                                              '0' if (abs(float(m.group(1)) - GX) < 1e-6 and abs(float(m.group(2)) - GY) < 1e-6) else m.group(3)), GBLK)
    blk = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % nu(), blk)
    blk = blk.replace('"#PWR021"', '"%s"' % ref)
    new_blocks.append(blk)
    return ref


def glabel(name, pt):
    # label runs left from pin 1 (angle 180, text right-justified at the pin)
    return ('\t(global_label "%s"\n\t\t(shape bidirectional)\n\t\t(at %s %s 180)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.0668 1.0668)\n'
            '\t\t\t)\n\t\t\t(justify right)\n\t\t)\n\t\t(uuid "%s")\n\t\t(property "Intersheetrefs" "${INTERSHEET_REFS}"\n'
            '\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n'
            '\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)' % (name, fmt(pt[0]), fmt(pt[1]), nu(), fmt(pt[0]), fmt(pt[1])))


for ref, net, op in (('C45', 'IREF1_input', 'U11'), ('C44', 'IREF2_input', 'U12'), ('C41', 'IREF3_input', 'U6')):
    oi, _ = one(op)
    ox, oy = oi['at'][:2]
    spot = None
    for ring in range(0, 25):                       # grid spots left of the op-amp, nearest first
        for gx in range(-ring, ring + 1):
            for gy in range(-ring, ring + 1):
                if max(abs(gx), abs(gy)) != ring:
                    continue
                X = round((ox - 20.32 + 2.54 * gx) / 1.27) * 1.27
                Y = round((oy + 2.54 * gy) / 1.27) * 1.27
                # label text left of pin 1 (~16 mm), symbol body, and the GND symbol below pin 2
                if area_empty(X - 17.78, Y - 2.54, X + 6.35, Y + 10.16):
                    spot = (X, Y)
                    break
            if spot:
                break
        if spot:
            break
    assert spot, ref
    p1, p2 = clone_cap(ref, *spot)
    new_blocks.append(glabel(net, p1))
    g = gnd_at(p2)
    log.append('%s 1n at (%s, %s): pin 1 label %s, pin 2 %s (GND); beside %s' % (ref, fmt(spot[0]), fmt(spot[1]), net, g, op))

# ---- apply
for (a, b), blk in block_mods.items():
    edits.append((a, b, blk))
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
for r in ('C41', 'C44', 'C45'):
    assign[r] = 'POWER'
json.dump(assign, open(ASSIGN_OUT, 'w'), indent=1, sort_keys=True)
log.append('assignment: %d refs (%s)' % (len(assign), {b: list(assign.values()).count(b) for b in ('POWER', 'CONTROL')}))
print('\n'.join(log))
print('wrote %s (%d -> %d bytes)' % (DST, len(T), len(out)))
