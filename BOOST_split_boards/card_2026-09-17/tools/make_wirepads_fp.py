"""Write the J9 wire-pad footprint into the project library (system Python).

usage: python make_wirepads_fp.py OUT.kicad_mod

11 plated holes for 26-28 AWG stranded wire (user, 2026-09-17), in two staggered rows so the block is short:
pin k at x = (k - 1) * STEP, y = 0 (odd k) or ROW_Y (even k). Pin 1 (square pad) is at the west end.
Wires come in from the card's underside, are soldered on the top side and trimmed flush, and leave toward local -x:
place the footprint at rotation 0 with its west end at the card's west edge, and the bundle runs straight off the
edge along the block.
Strain relief: two NPTH slots for a cable tie at the west end, one on each side of the bundle. The tie goes down
through one slot, under the wires, up through the other and back across the top side (flat strap only, about 1 mm);
its head closes on the underside, below the wires, so the footprint belongs where the power board has no can under
it. Slots are sized for a 2.5 mm tie.
The courtyard (both sides) covers the pads, the slots and the strap path, so nothing is placed in the way on either
side; its west side is where the card edge should be.
Labels (user, 2026-09-22): a short name beside every pad on both F.SilkS and B.SilkS (mirrored there), 1.0 x 1.0 mm
text, 0.15 mm stroke: odd pins in a row above the pad field, even pins in a row below it, each centred on its pad
except the wide ones, shifted a few tenths apart so their strokes keep 0.3 mm (SCL, 12V, INH; SDA, GND). Pin 9 is
12 V from schematic rev5 (2026-09-23; it was 5 V). Pin 1 has a square pad and a
0.6 mm silk dot at its south-west (both sides). The reference sits between the tie slots on F.SilkS.
Pads keep their rings on every layer. (Dropping the unused inner rings freed no routing room: KiCad then treats a
foreign track crossing the ring area as a short, so tracks must clear the full ring anyway; tried 2026-09-22.)
"""
import sys

OUT = sys.argv[1]
NAME = 'WirePads_11_Staggered_P1.27mm_Drill1.0mm_TieSlots'
N = 11
STEP = 1.27           # along the block, pin to pin (same-row pins 2.54 apart)
ROW_Y = 2.54          # between the two rows
PAD = 2.0             # pad diameter: 0.5 mm annular ring on a 1.0 mm drill, for hand soldering
DRILL = 1.0
SLOT_X = -2.9         # slot centres, west of pin 1 (slot edge 0.5 mm from pin 1's pad)
SLOT_W, SLOT_H = 2.8, 1.4      # along x (tie width 2.5 + 0.3) x along y (tie thickness about 1.0 + 0.4)
SLOT_OFF = 3.7        # slot centre to the bundle centre line (y = ROW_Y / 2): 6.0 mm clear between the slots
CY = 0.2              # courtyard margin
LABELS = {1: 'V1', 2: 'V2', 3: 'V3', 4: 'I1', 5: 'I2', 6: 'I3', 7: 'SCL', 8: 'SDA', 9: '12V', 10: 'GND', 11: 'INH'}   # pin 9: 12V (rev5)
LABEL_DX = {7: -0.3, 8: -0.3, 9: 0.1, 10: 0.4, 11: 0.35}   # wide labels on a 2.54 pitch: SCL/12V/INH and SDA/GND shifted apart
TXT = 1.0             # label height = width (the card's 1.0 / 0.15 silk text minimum)
TXT_T = 0.15
INK_H = 1.15          # stroke-font ink height at 1.0 mm (KiCad effective shape)
LABEL_GAP = 0.25      # pad copper edge to label ink
DOT = (-1.3, 1.6, 0.3)     # pin-1 dot: centre and radius, off pad 1's south-west corner (0.3 mm), clear of pad 2

x_last = (N - 1) * STEP
yc = ROW_Y / 2
slots = [(SLOT_X, yc - SLOT_OFF), (SLOT_X, yc + SLOT_OFF)]
cx0 = SLOT_X - SLOT_W / 2 - CY
cx1 = x_last + PAD / 2 + CY
cy0 = yc - SLOT_OFF - SLOT_H / 2 - CY
cy1 = yc + SLOT_OFF + SLOT_H / 2 + CY


def line(x0, y0, x1, y1, layer, w):
    return ('\t(fp_line\n\t\t(start %.3f %.3f)\n\t\t(end %.3f %.3f)\n\t\t(stroke\n\t\t\t(width %.2f)\n'
            '\t\t\t(type solid)\n\t\t)\n\t\t(layer "%s")\n\t)\n' % (x0, y0, x1, y1, w, layer))


def rect(x0, y0, x1, y1, layer, w):
    return (line(x0, y0, x1, y0, layer, w) + line(x1, y0, x1, y1, layer, w) + line(x1, y1, x0, y1, layer, w) +
            line(x0, y1, x0, y0, layer, w))


def label(val, x, y, layer):
    mirror = '\t\t\t(justify mirror)\n' if layer.startswith('B.') else ''
    return ('\t(fp_text user "%s"\n\t\t(at %.3f %.3f 0)\n\t\t(layer "%s")\n\t\t(effects\n\t\t\t(font\n'
            '\t\t\t\t(size %.2f %.2f)\n\t\t\t\t(thickness %.2f)\n\t\t\t)\n%s\t\t)\n\t)\n' % (
                val, x, y, layer, TXT, TXT, TXT_T, mirror))


def dot(x, y, r, layer):
    return ('\t(fp_circle\n\t\t(center %.3f %.3f)\n\t\t(end %.3f %.3f)\n\t\t(stroke\n\t\t\t(width 0.1)\n'
            '\t\t\t(type solid)\n\t\t)\n\t\t(fill yes)\n\t\t(layer "%s")\n\t)\n' % (x, y, x + r - 0.05, y, layer))


def text(kind, val, x, y, layer, hide=False):
    return ('\t(property "%s" "%s"\n\t\t(at %.3f %.3f 0)\n\t\t(layer "%s")\n%s\t\t(effects\n\t\t\t(font\n'
            '\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n' % (
                kind, val, x, y, layer, '\t\t(hide yes)\n' if hide else ''))


s = '(footprint "%s"\n\t(version 20260206)\n\t(generator "make_wirepads_fp.py")\n\t(layer "F.Cu")\n' % NAME
s += ('\t(descr "J9 Arduino wires: 11 plated holes (drill %.1f, pad %.1f) for 26-28 AWG stranded wire in two staggered '
      'rows %.2f mm apart, %.2f mm step; wires enter from the underside, are soldered on the top and leave toward -x; '
      'two NPTH cable-tie slots %.1fx%.1f mm at the -x end (BOOST control card, 2026-09-17)")\n' % (
          DRILL, PAD, ROW_Y, STEP, SLOT_W, SLOT_H))
s += '\t(tags "wire solder pad cable tie")\n'
s += text('Reference', 'REF**', SLOT_X, yc, 'F.SilkS')     # between the tie slots
s += text('Value', NAME, x_last / 2, cy1 + 1.0, 'F.Fab', hide=True)
s += '\t(attr through_hole)\n\t(duplicate_pad_numbers_are_jumpers no)\n'
for layer in ('F.CrtYd', 'B.CrtYd'):
    s += rect(cx0, cy0, cx1, cy1, layer, 0.05)
s += rect(-PAD / 2 - 0.2, -PAD / 2 - 0.2, x_last + PAD / 2 + 0.2, ROW_Y + PAD / 2 + 0.2, 'F.Fab', 0.1)
# pad names and the pin-1 dot on both silk layers (the wires enter from the underside, solder on the top)
y_odd = -(PAD / 2 + LABEL_GAP + INK_H / 2)
y_even = ROW_Y + PAD / 2 + LABEL_GAP + INK_H / 2
for layer in ('F.SilkS', 'B.SilkS'):
    for k, name in LABELS.items():
        s += label(name, (k - 1) * STEP + LABEL_DX.get(k, 0.0), y_odd if k % 2 else y_even, layer)
    s += dot(DOT[0], DOT[1], DOT[2], layer)
for k in range(1, N + 1):
    x = (k - 1) * STEP
    y = 0.0 if k % 2 else ROW_Y
    shape = 'rect' if k == 1 else 'circle'
    s += ('\t(pad "%d" thru_hole %s\n\t\t(at %.3f %.3f)\n\t\t(size %.2f %.2f)\n\t\t(drill %.2f)\n'
          '\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t)\n' % (
              k, shape, x, y, PAD, PAD, DRILL))
for (x, y) in slots:
    s += ('\t(pad "" np_thru_hole oval\n\t\t(at %.3f %.3f)\n\t\t(size %.2f %.2f)\n\t\t(drill oval %.2f %.2f)\n'
          '\t\t(layers "*.Cu" "*.Mask")\n\t)\n' % (x, y, SLOT_W, SLOT_H, SLOT_W, SLOT_H))
s += '\t(embedded_fonts no)\n)\n'
open(OUT, 'w', encoding='utf8', newline='\n').write(s)
print('wrote %s: %d pads, block %.2f x %.2f mm, courtyard %.2f x %.2f mm (x %.2f..%.2f, y %.2f..%.2f)' % (
    OUT, N, x_last + PAD, ROW_Y + PAD, cx1 - cx0, cy1 - cy0, cx0, cx1, cy0, cy1))
