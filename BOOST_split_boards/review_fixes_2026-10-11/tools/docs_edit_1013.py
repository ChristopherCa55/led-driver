"""2026-10-13 README update for the review copy (steps 5g-10 and the regenerated outputs), on a STAGED copy:

    python docs_edit_1013.py README.md        (edits that file in place; each replacement must match exactly once)
"""
import sys

p = sys.argv[1]
b = open(p, 'rb').read()
nl = '\r\n' if b'\r\n' in b else '\n'
s = b.decode('utf-8').replace('\r\n', '\n')

REPS = [
    ("**Results:** a 30 ms run at full duty converges in about 5-7 minutes. Over 25-30 ms the LEDs hold 2.635, 2.371 and\n",
     "**Results:** a 30 ms run at full duty converges in about 15-50 minutes; it was 5-7 minutes before the I2C pull-ups.\n"
     "With R106 / R107 in the netlist the normal solver stops at 0.3216 ms, so the `.options` line now carries\n"
     "`solver=alt`, which is about 3x slower and gives the same results. Over 25-30 ms the LEDs hold 2.635, 2.371 and\n"),
    ("(green, blue); below that the pulses carry less current. Runs can stall while all LEDs are off; adding `solver=alt`\n"
     "to the `.options` line gets past it.\n",
     "(green, blue); below that the pulses carry less current. Runs can stall while all LEDs are off; the `solver=alt`\n"
     "on the `.options` line gets past that.\n"),
    ("## Review fixes (2026-10-11): what changed\n\n"
     "This copy carries the fixes from the 2026-10-10 schematic and PCB reviews that are approved and pass every check. It is\n"
     "**not for fabrication**: the gerbers, drill files, fab drawings and STEP in this folder are still the shipped ones and\n"
     "do not show these changes.\n",
     "## Review fixes (2026-10-11 to 2026-10-13): what changed\n\n"
     "This copy carries the fixes from the 2026-10-10 schematic and PCB reviews that you approved. Every one passes every\n"
     "check. The gerbers, drill files, fab drawings, BOM / CPL, cost files and the 3D model\n"
     "(`BOOST_assembly_2026-10-13.step`) were regenerated from these files on 2026-10-13; the older STEP files here are the\n"
     "shipped ones. The copy stays **not for fabrication** (`NOT_FOR_FAB.txt`) until you say ship.\n"),
    ("  not change); the `.ic` line no longer names nodes that do not exist, and the commented-out `.ic` line is gone.\n",
     "  not change); the `.ic` line no longer names nodes that do not exist, and the commented-out `.ic` line is gone;\n"
     "  the I2C pull-ups R106 / R107 (4.7k, SCL / SDA to 5V) and R99 / R102 at 1k are in; `.options` has `solver=alt`.\n"),
    ("  Out3+ / Out3-; the main page has a title block; the spare pot unit U26D no longer touches U106D.\n",
     "  Out3+ / Out3-; the main page has a title block; the spare pot unit U26D no longer touches U106D; R106 / R107\n"
     "  (4.7k, 0603) are drawn with the note \"I2C pull-ups (U26 has none)\"; R99 / R102 are 1k, so U26's A0 / A1 cannot\n"
     "  latch high and its I2C address is always 0x2C.\n"),
    ("  - three more Vin vias in R1's funnel.\n",
     "  - three more Vin vias in R1's funnel;\n"
     "  - two more Vout_3 vias at C4.1 share ch3's output-loop current (worst via 2.8x -> 1.8x its IPC rating, that loop\n"
     "    -12 % resistance).\n"
     "- **Control card:**\n"
     "  - R106 (front, in J9's top label row above J9.5 / J9.7; the I2 and SCL labels moved up above it) and R107 (front,\n"
     "    below J9's I1 label, joined to J9.8 on In2). J9's front courtyard now hugs its pads; H3's label is 0.35 mm lower;\n"
     "  - two GND stitching vias in an In1 GND piece that had only one;\n"
     "  - U101A-Y moved from In1 to In2 (the main In1 GND piece 894 -> 972 mm2);\n"
     "  - D5- re-routed (In4, then In2 along the bottom edge) so it no longer cuts the In4 GND in two (the main In4 piece\n"
     "    626 -> 952 mm2).\n"
     "- **Costs:** total $599.01 (was $598.99). R106 / R107 join the card's existing 4.7k line, R99 / R102 the 1k line; no\n"
     "  new part.\n"),
    ("  before (power 49, card 1); schematic parity 0; the main page and both board schematics still agree.\n\n"
     "**Waiting for your OK** (built and checked, not yet in this copy): the I2C pull-ups R106 / R107 and R99 / R102 at 1k\n"
     "(control card, LTspice, BOM / CPL), two GND stitching vias and one re-routed track on the card.\n",
     "  before (power 49, card 1); schematic parity 0; the main page and both board schematics still agree; the LTspice\n"
     "  file is electrically the shipped one plus the approved changes (ltspice_equiv E1-E5).\n"),
]
for a, c in REPS:
    n = s.count(a)
    assert n == 1, (n, a[:80])
    s = s.replace(a, c)
open(p, 'wb').write(s.replace('\n', nl).encode('utf-8'))
print('edited', p, len(REPS), 'replacements')
