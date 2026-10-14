"""Redraw the 10 custom LTspice symbols in the KiCad style (the user's request, 2026-10-07).

    python make_symbols.py            reads  ../../previous/2026-10-07/asy_before_kicad_style/*.asy
                                      writes ../work/*.asy

The user asked: no overlapping text, every pin name inside the body, and the look of the KiCad symbols the
schematic uses (Amplifier_Current:INA241A3xD, Device:R_Shunt, Device:R_Potentiometer, Potentiometer_Digital:MCP4451,
Regulator_Linear:L78L05, 74xx:74HC4051, 4xxx:4017, 4xxx:4066, Driver_FET:UCC21520DW).

Kept exactly from the old files: every SYMATTR (model, prefix, value, ...), every pin's PinName and SpiceOrder and the
order of the PIN lines. Pin POSITIONS are kept too, except 74HC4051 and CD4017B (user's OK 2026-10-07: rearranged
like KiCad; their single instances are rewired). Pin labels are hidden (NONE) and drawn as TEXT, so the size and
place of every name is controlled; IC bodies are RECTANGLEs (LTspice fills them, like KiCad's background fill),
resistor bodies are LINEs (unfilled, like KiCad).
"""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', 'previous', '2026-10-07', 'asy_before_kicad_style'))
OUT = os.path.normpath(os.path.join(HERE, '..', 'work'))


def rect_lines(x1, y1, x2, y2):
    return ['LINE Normal %d %d %d %d' % p for p in
            ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1))]


def L(*v):
    return 'LINE Normal %d %d %d %d' % v


def T(x, y, just, size, text):
    return 'TEXT %d %d %s %d %s' % (x, y, just, size, text)


def W(n, x, y, just, size=2):
    return 'WINDOW %d %d %d %s %d' % (n, x, y, just, size)


def arrowhead_left(tip_x, y, length=12, half=8):
    """a filled-looking arrowhead pointing left with its tip at (tip_x, y)"""
    out = [L(tip_x, y, tip_x + length, y - half), L(tip_x, y, tip_x + length, y + half),
           L(tip_x + length, y - half, tip_x + length, y + half)]
    for dx in range(2, length, 2):
        h = round(half * dx / length)
        out.append(L(tip_x + dx, y - h, tip_x + dx, y + h))
    return out


# ------------------------------------------------------------------------------------------------ designs
def pot():
    """KiCad's MCP4451 pot unit: a box with the resistor and its wiper arrow inside (user, 2026-10-09). The box sits
    mostly on the wiper side so the instances' text (placed 32 left of the leads, or right when mirrored) stays out."""
    g = ['RECTANGLE Normal -24 -48 48 48',
         L(0, -48, 0, -28), L(0, 28, 0, 48)] + rect_lines(-8, -28, 8, 28) + [L(48, 0, 20, 0)]
    g += arrowhead_left(8, 0)
    g += [T(14, -36, 'Left', 1, 'B'), T(14, 36, 'Left', 1, 'A'), T(44, -12, 'Right', 1, 'W')]
    w = [W(0, -32, -32, 'Right'), W(3, -32, 0, 'Right', 1), W(39, -32, 24, 'Right', 1)]
    return g, w, None


def shunt():
    g = [L(0, 0, 16, 0), L(64, 0, 80, 0)] + rect_lines(16, -10, 64, 10) + [L(16, -32, 16, -10), L(64, -32, 64, -10)]
    w = [W(0, 40, -40, 'Bottom'), W(3, 40, 24, 'Top'), W(39, 40, 56, 'Top', 1)]
    return g, w, None


def ina():
    g = [L(-64, -96, -64, 96), L(-64, -96, 64, 0), L(-64, 96, 64, 0),
         L(0, -64, 0, -48), L(0, 64, 0, 48), L(32, 64, 32, 24),
         T(-56, -32, 'Left', 2, '+'), T(-56, 32, 'Left', 2, '-'), T(-56, 0, 'Left', 1, 'REF1'),
         T(0, -36, 'Center', 1, 'VS'), T(0, 36, 'Center', 1, 'GND'), T(32, 4, 'VCenter', 0, 'REF2')]
    w = [W(0, 32, -40, 'Left'), W(3, 40, 32, 'Left')]
    return g, w, None


def regulator():
    g = ['RECTANGLE Normal -64 -40 64 32', T(-58, 0, 'Left', 1, 'IN'), T(58, 0, 'Right', 1, 'OUT'),
         T(0, 16, 'VCenter', 1, 'GND')]
    w = [W(0, 0, -72, 'Bottom'), W(3, 0, -44, 'Bottom')]
    return g, w, None


def pot_ctrl():
    g = ['RECTANGLE Normal -80 -96 80 96',
         L(-96, -32, -80, -32), L(-96, 0, -80, 0), L(96, 0, 80, 0), L(0, -112, 0, -96),
         L(-48, 112, -48, 96), L(0, 112, 0, 96), L(48, 112, 48, 96),
         T(-74, -32, 'Left', 1, 'SCL'), T(-74, 0, 'Left', 1, 'SDA'), T(74, 0, 'Right', 1, 'RESET'),
         L(26, -11, 74, -11),                                            # RESET is active low
         T(0, -76, 'VCenter', 1, 'VDD'),
         T(-48, 76, 'VCenter', 0, 'HVC/A0'), T(0, 84, 'VCenter', 0, 'A1'), T(48, 82, 'VCenter', 0, 'VSS'),
         T(0, 36, 'Center', 0, 'digital potentiometer')]
    w = [W(0, 88, -104, 'Left'), W(3, 88, 104, 'Left', 1)]
    return g, w, None


def switch4066():
    """an analog switch the way KiCad draws the ADG417/DG417: two contacts, an open lever, and a dashed actuator line
    from the control pin (user, 2026-10-09: "make it look more like a switch")"""
    g = ['RECTANGLE Normal 0 -32 80 48',
         L(0, 0, 17, 0), L(63, 0, 80, 0),                                              # A, B leads
         'CIRCLE Normal 17 -5 27 5', 'CIRCLE Normal 53 -5 63 5',                         # contacts
         L(26, -5, 62, -15),                                                            # lever (open)
         L(40, -9, 40, 24) + ' 2', L(40, 24, 64, 24) + ' 2', L(64, 24, 64, 48),         # control
         T(32, -24, 'Center', 0, 'VDD'), T(16, 38, 'Center', 0, 'VSS'), T(60, 38, 'Right', 0, 'CTRL')]
    w = [W(0, 40, -40, 'Bottom'), W(3, 40, 64, 'Top', 1)]
    return g, w, None


def ucc21520():
    g = ['RECTANGLE Normal -96 -96 96 96',
         L(-6, -96, -6, 64) + ' 2', L(6, -96, 6, 64) + ' 2']                          # isolation barrier
    g += rect_lines(-40, -76, -28, 76) + [T(-34, 0, 'VCenter', 0, 'Logic Input')]
    for y in (-48, 48):                                                                # the two output drivers
        g += [L(16, y - 12, 16, y + 12), L(16, y - 12, 40, y), L(16, y + 12, 40, y)]
    for n, y in (('INA', -64), ('INB', -32), ('VCCI', 0), ('GND', 32), ('DIS', 64)):
        g.append(T(-90, y, 'Left', 1, n))
    for n, y in (('VDDA', -80), ('OUTA', -48), ('VSSA', -16), ('VDDB', 16), ('OUTB', 48), ('VSSB', 80)):
        g.append(T(90, y, 'Right', 1, n))
    g.append(T(0, 84, 'Center', 1, 'DT'))
    w = [W(0, -96, -112, 'Left'), W(3, -96, 108, 'Left', 1)]                    # value small: clear of the DT wire
    return g, w, None


def mux4051():
    pins = {'IOC': (0, 32), 'A': (0, 96), 'B': (0, 128), 'C': (0, 160), 'INH': (0, 224),
            'VDD': (64, 0), 'VSS': (48, 288), 'VEE': (80, 288)}
    for k in range(8):
        pins['IO%d' % k] = (128, 32 + 32 * k)
    g = ['RECTANGLE Normal 0 0 128 288',
         T(6, 32, 'Left', 1, 'A'), T(6, 96, 'Left', 1, 'S0'), T(6, 128, 'Left', 1, 'S1'), T(6, 160, 'Left', 1, 'S2'),
         T(6, 224, 'Left', 1, 'E'), L(6, 214, 16, 214),                                  # E is active low
         T(64, 22, 'VCenter', 1, 'VCC'), T(48, 266, 'VCenter', 1, 'GND'), T(80, 266, 'VCenter', 1, 'VEE')]
    g += [T(122, 32 + 32 * k, 'Right', 1, 'A%d' % k) for k in range(8)]
    w = [W(0, 0, -16, 'Left'), W(3, -8, 304, 'Right')]
    return g, w, pins


def counter4017():
    pins = {'CP': (0, 32), 'CPN': (-16, 64), 'MR': (0, 128), 'Q59': (128, 384)}
    for k in range(10):
        pins['Q%d' % k] = (128, 32 + 32 * k)
    g = ['RECTANGLE Normal 0 0 128 416',
         L(0, 24, 10, 32), L(10, 32, 0, 40), 'CIRCLE Normal -16 56 0 72',           # clock input, active-low enable
         T(14, 32, 'Left', 1, 'CLK'), T(6, 64, 'Left', 1, 'CKEN'), T(6, 128, 'Left', 1, 'Reset'),
         T(122, 384, 'Right', 1, 'Cout')]
    g += [T(122, 32 + 32 * k, 'Right', 1, 'Q%d' % k) for k in range(10)]
    w = [W(0, 0, -16, 'Left'), W(3, 0, 432, 'Left')]
    return g, w, pins


DESIGNS = {'MCP4451_POT': pot, 'CSS4J_4026': shunt, 'INA241A4': ina, 'L78L05': regulator, 'MC7812': regulator,
           'MCP4451_CTRL': pot_ctrl, 'CD74HC4066': switch4066, 'UCC21520': ucc21520, '74HC4051': mux4051,
           'CD4017B': counter4017}


def rebuild(name):
    old = open(os.path.join(SRC, name + '.asy'), encoding='latin-1').read().replace('\r', '').split('\n')
    head = [l for l in old if l.startswith(('Version', 'SymbolType'))]
    attrs = [l for l in old if l.startswith('SYMATTR ')]
    pins, cur = [], None
    for l in old:
        if l.startswith('PIN '):
            t = l.split()
            cur = [int(t[1]), int(t[2]), []]
            pins.append(cur)
        elif l.startswith('PINATTR ') and cur is not None:
            cur[2].append(l)
    graphics, windows, moved = DESIGNS[name]()
    out = head + graphics + windows + attrs
    for x, y, pa in pins:
        pname = next(l.split(' ', 2)[2] for l in pa if l.startswith('PINATTR PinName'))
        if moved:
            x, y = moved.pop(pname)
        out.append('PIN %d %d NONE 0' % (x, y))
        out += pa
    if moved:
        raise SystemExit('%s: pins %s not in the old symbol' % (name, sorted(moved)))
    open(os.path.join(OUT, name + '.asy'), 'w', encoding='latin-1', newline='\n').write('\n'.join(out) + '\n')
    return len(pins)


if __name__ == '__main__':
    for n in sorted(DESIGNS):
        print('%-13s %2d pins' % (n, rebuild(n)))
