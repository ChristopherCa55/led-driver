"""KiCad library symbols remade at the user's request (2026-10-09). Pin numbers, pin types and units are those of the
existing `ltspice:` symbols; only the drawing changes, plus:
  - 74HC00 gate output Y moves to the middle of the body (a standard NAND); the wiring adds a 1.27 mm jog there,
  - CD4066 switch units get the pin positions of the LTspice CD74HC4066 symbol (A, B, CTRL; supply stays in unit E).
Everything here is written in the same S-expression form KiCad uses, then parsed."""
from sexpr import parse


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def stroke(w=0.254, t='default'):
    return '(stroke (width %s) (type %s))' % (fmt(w), t)


def poly(pts, w=0.254, fill='none', t='default'):
    return '(polyline (pts %s) %s (fill (type %s)))' % (
        ' '.join('(xy %s %s)' % (fmt(x), fmt(y)) for x, y in pts), stroke(w, t), fill)


def rect(x1, y1, x2, y2, fill='background', w=0.254):
    return '(rectangle (start %s %s) (end %s %s) %s (fill (type %s)))' % (
        fmt(x1), fmt(y1), fmt(x2), fmt(y2), stroke(w), fill)


def circle(cx, cy, r, fill='none', w=0.254):
    return '(circle (center %s %s) (radius %s) %s (fill (type %s)))' % (fmt(cx), fmt(cy), fmt(r), stroke(w), fill)


def arc(sx, sy, mx, my, ex, ey, w=0.254):
    return '(arc (start %s %s) (mid %s %s) (end %s %s) %s (fill (type none)))' % (
        fmt(sx), fmt(sy), fmt(mx), fmt(my), fmt(ex), fmt(ey), stroke(w))


def text(s, x, y, size=1.0, angle=0, just=''):
    j = ' (justify %s)' % just if just else ''
    return '(text "%s" (at %s %s %d) (effects (font (size %s %s))%s))' % (
        s, fmt(x), fmt(y), angle, fmt(size), fmt(size), j)


def pin(typ, x, y, ang, length, name, num, hide=False):
    h = ' (hide yes)' if hide else ''
    return ('(pin %s line (at %s %s %d) (length %s)%s (name "%s" (effects (font (size 1.27 1.27)))) '
            '(number "%s" (effects (font (size 1.27 1.27)))))' % (typ, fmt(x), fmt(y), ang, fmt(length), h, name, num))


def header(name, ref, value, fp, desc, ref_at=(0, 2.54), val_at=(0, -10.16), extra=''):
    return ('(symbol "%s" %s(pin_names (offset 1.016) (hide yes)) (pin_numbers (hide yes)) (exclude_from_sim yes) '
            '(in_bom yes) (on_board yes) (in_pos_files yes) (duplicate_pin_numbers_are_jumpers no) '
            '(property "Reference" "%s" (at %s %s 0) (show_name no) (do_not_autoplace no) (effects (font (size 1.27 1.27)))) '
            '(property "Value" "%s" (at %s %s 0) (show_name no) (do_not_autoplace no) (effects (font (size 1.27 1.27)))) '
            '(property "Footprint" "%s" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 1.27 1.27)))) '
            '(property "Datasheet" "" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 1.27 1.27)))) '
            '(property "Description" "%s" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 1.27 1.27)))) '
            % (name, extra, ref, fmt(ref_at[0]), fmt(ref_at[1]), value, fmt(val_at[0]), fmt(val_at[1]), fp, desc))


def nand_body():
    """inputs at (-2.54,-3.81) and (-2.54,-6.35), output at (2.54,-5.08)"""
    return ' '.join([
        poly([(-2.54, -3.81), (-1.905, -3.81)]), poly([(-2.54, -6.35), (-1.905, -6.35)]),
        poly([(-0.635, -2.54), (-1.905, -2.54), (-1.905, -7.62), (-0.635, -7.62)], fill='background'),
        arc(-0.635, -2.54, 1.905, -5.08, -0.635, -7.62),
        circle(2.2225, -5.08, 0.3175)])


def inverter_body():
    """input (0,-5.08), output (5.08,-5.08)"""
    return ' '.join([
        poly([(0, -5.08), (0.635, -5.08)]),
        poly([(0.635, -3.175), (3.81, -5.08), (0.635, -6.985), (0.635, -3.175)], fill='background'),
        circle(4.1275, -5.08, 0.3175), poly([(4.445, -5.08), (5.08, -5.08)])])


def supply_body(top, bot, numtop, numbot):
    """power unit: pins at (0,0) top and (0,-10.16) bottom, names written inside, horizontally"""
    return ' '.join([rect(-3.81, -1.27, 3.81, -8.89), text(top, 0, -2.54), text(bot, 0, -7.62),
                     pin('power_in', 0, 0, 270, 1.27, top, numtop), pin('power_in', 0, -10.16, 90, 1.27, bot, numbot)])


def sym_74hc00():
    units = {1: ('1', '2', '3'), 2: ('4', '5', '6'), 3: ('10', '9', '8'), 4: ('13', '12', '11')}
    out = [header('ltspice:74HC00_conv', 'U', '74HC00', 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
                  'Quad 2-input NAND (converted from LTspice A-device)', ref_at=(0, -1.27), val_at=(0, -8.89))]
    for u, (a, b, y) in units.items():
        out.append('(symbol "74HC00_conv_%d_1" %s %s %s %s)' % (
            u, nand_body(), pin('input', -2.54, -3.81, 0, 0.0005, 'A', a), pin('input', -2.54, -6.35, 0, 0.0005, 'B', b),
            pin('output', 2.54, -5.08, 180, 0.0005, 'Y', y)))
    out.append('(symbol "74HC00_conv_5_1" %s)' % supply_body('VCC', 'GND', '14', '7'))
    return parse(' '.join(out) + ' (embedded_fonts no))')


def sym_74hc14():
    units = {1: ('1', '2'), 2: ('3', '4'), 3: ('5', '6'), 4: ('9', '8'), 5: ('11', '10'), 6: ('13', '12')}
    out = [header('ltspice:74HC14_conv', 'U', '74HC14', 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
                  'Hex Schmitt-trigger inverter (converted from LTspice A-device)', ref_at=(0, -2.54), val_at=(0, -8.89))]
    for u, (a, y) in units.items():
        out.append('(symbol "74HC14_conv_%d_1" %s %s %s)' % (
            u, inverter_body(), pin('input', 0, -5.08, 0, 0.0005, 'A', a), pin('output', 5.08, -5.08, 180, 0.0005, 'Y', y)))
    out.append('(symbol "74HC14_conv_7_1" %s)' % supply_body('VCC', 'GND', '14', '7'))
    return parse(' '.join(out) + ' (embedded_fonts no))')


def switch_body():
    """LTspice CD74HC4066 geometry without its supply pins: A (0,0), B (6.35,0), CTRL (5.08,-3.81)"""
    return ' '.join([
        rect(0, 2.54, 6.35, -3.81),
        poly([(0, 0), (1.35, 0)]), poly([(5.0, 0), (6.35, 0)]),
        circle(1.746, 0, 0.397), circle(4.604, 0, 0.397),
        poly([(2.064, 0.397), (4.921, 1.191)]),
        poly([(3.175, 0.714), (3.175, -1.905), (5.08, -1.905)], t='dash'), poly([(5.08, -1.905), (5.08, -3.81)]),
        text('CTRL', 4.76, -3.0, 0.8, 0, 'right')])


def sym_4066():
    units = {1: ('1', '2', '13'), 2: ('3', '4', '5'), 3: ('8', '9', '6'), 4: ('11', '10', '12')}
    out = [header('ltspice:CD4066_conv', 'U', 'CD74HC4066', 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
                  'Quad bilateral switch (converted from LTspice)', ref_at=(0, 5.08), val_at=(0, 3.81))]
    for u, (a, b, c) in units.items():
        out.append('(symbol "CD4066_conv_%d_1" %s %s %s %s)' % (
            u, switch_body(), pin('passive', 0, 0, 0, 0.0005, 'A', a), pin('passive', 6.35, 0, 180, 0.0005, 'B', b),
            pin('input', 5.08, -3.81, 90, 0.0005, 'CTRL', c)))
    out.append('(symbol "CD4066_conv_5_1" %s)' % supply_body('VDD', 'VSS', '14', '7'))
    return parse(' '.join(out) + ' (embedded_fonts no))')


def sym_regulator():
    body = ' '.join([rect(-5.08, 3.175, 5.08, -2.54), text('IN', -4.6, 0, 1.0, 0, 'left'),
                     text('OUT', 4.6, 0, 1.0, 0, 'right'), text('GND', 0, -1.016, 1.0, 90),
                     pin('passive', -5.08, 0, 0, 0.0005, 'IN', '1'), pin('passive', 0, -2.54, 90, 0.0005, 'GND', '2'),
                     pin('passive', 5.08, 0, 180, 0.0005, 'OUT', '3')])        # same pin types as before (ERC)
    return parse(header('ltspice:LM2940_12', 'U', 'LM2940_12', '', '12 V linear regulator', ref_at=(0, 6.35),
                        val_at=(0, 4.445)) + '(symbol "LM2940_12_0_0" %s) (embedded_fonts no))' % body)


def fix_opamp(sym):
    """move the V+/V- marks off the input marks: they go beside the supply leads, outside the triangle"""
    from sexpr import find, findall
    unit = next(s for s in findall(sym, 'symbol') if s[1].endswith('_0_0"'))
    keep = []
    for g in unit[2:]:
        if isinstance(g, list) and g[0] == 'polyline':
            pts = [(float(p[1]), float(p[2])) for p in find(g, 'pts')[1:]]
            xs = [p[0] for p in pts]
            if min(xs) >= 0.3 and max(xs) <= 1.0:          # the old + at V+ and - at V-
                continue
        keep.append(g)
    unit[2:] = keep
    unit[2:2] = parse('(x %s %s %s)' % (poly([(0.635, -1.27), (1.27, -1.27)], 0.1524),
                                        poly([(0.9525, -0.9525), (0.9525, -1.5875)], 0.1524),
                                        poly([(0.635, -8.89), (1.27, -8.89)], 0.1524)))[1:]
    return sym


def fix_gnd(sym):
    """hide the pin name 'GND' that was drawn on the ground symbol"""
    sym.insert(2, ['pin_names', ['hide', 'yes']])
    return sym
