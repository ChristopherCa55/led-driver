"""Documentation edits for the copy (review fixes 2026-10-11), into NEW files in OUT_DIR (OUT_DIR must not exist).

    python docs_edit.py COPY_DIR OUT_DIR

- README.md: one sentence on D19 (D3, numbers from DECISIONS.md), and a "Review fixes (2026-10-11): what changed"
  section at the end.
- BUILD_NOTES.md: the M8-M10 heat numbers (D4) under the thermal-pad item.
Line endings are kept as in the source files.
"""
import os, sys, textwrap

D3 = ("- D19 (5.0SMDJ54A) is modelled at its minimum breakdown, 60.0 V. Over 25-30 ms it conducts in 101 of 453 "
      "switching cycles (22 %), 9.5 mW on average (0.15 % of its 6.5 W rating); most of its current is junction "
      "capacitance at the LX edges. A typical part (about 63 V) would not conduct at all in steady state.")

WHAT = """
## Review fixes (2026-10-11): what changed

This copy carries the fixes from the 2026-10-10 schematic and PCB reviews that are approved and pass every check. It is
**not for fabrication**: the gerbers, drill files, fab drawings and STEP in this folder are still the shipped ones and
do not show these changes.

- **LTspice:** short notes where the review found sections hard to follow (sequencer, latch, enable delays, gate
  drivers, channels 2 and 3); every diode shows its part name (`.model` aliases of the default diode, so the results do
  not change); the `.ic` line no longer names nodes that do not exist, and the commented-out `.ic` line is gone.
- **KiCad schematics:** the 22 diodes show their part names; J1-J8 show Vin+ / Vin- / Out1+ / Out1- / Out2+ / Out2- /
  Out3+ / Out3-; the main page has a title block; the spare pot unit U26D no longer touches U106D.
- **Power board:**
  - the silkscreen names J1-J8 Vin+ / Vin- / Out1+ ... instead of J1-J8 (the references are on F.Fab);
  - 12V reaches U19 / C30 / C31 on B.Cu through one opened column of the Vin via array, instead of looping round M1 on
    In4 and through R1's Vin funnel (Vin J1 -> R1 1.031 -> 1.003 mOhm, worst neck 38.8 -> 29.3 C);
  - two more GND vias in C3.2's pad share ch2's switching-loop current (worst via 3.6x -> 1.7x its IPC rating);
  - three more Vin vias in R1's funnel.
- **Checks:** ERC 0 on all three schematics; DRC 0 errors and 0 unconnected on both boards, with the same warnings as
  before (power 49, card 1); schematic parity 0; the main page and both board schematics still agree.

**Waiting for your OK** (built and checked, not yet in this copy): the I2C pull-ups R106 / R107 and R99 / R102 at 1k
(control card, LTspice, BOM / CPL), two GND stitching vias and one re-routed track on the card.

Every change with its x / y and layer: `CHANGES_XY.md` in this folder. The full report, with before / after numbers and
pictures: `BOOST_split_boards/review_fixes_2026-10-11/FIX_REPORT.md`.
"""

D4 = ("   - **Heat in M8-M10 (2026-10-11):** in the simulation the sink FETs hold their drains at 1.49 / 1.45 / 1.45 V at "
      "full current, so M10 / M9 / M8 dissipate about 3.9 / 3.4 / 3.4 W each. Across a 10 x 16 mm, 3 W/m-K pad "
      "compressed to 0.93 mm (about 1.9 K/W) that is about 7.5 K at 3.9 W. The HYG180N10's junction-to-case resistance "
      "is not verified (its data sheet is not on file).")


def edit(path, out, fn):
    raw = open(path, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    t = fn(t)
    open(out, 'wb').write(t.replace('\n', nl).encode('utf-8'))


def readme(t):
    anchor = '- The `LED_RED`/`LED_GREEN`/`LED_BLUE` models are unused on purpose; the LEDs use the `100W_` models.\n'
    assert t.count(anchor) == 1
    t = t.replace(anchor, anchor + '\n'.join(textwrap.wrap(D3, 118, subsequent_indent='  ')) + '\n')
    return t.rstrip('\n') + '\n' + WHAT


def build_notes(t):
    anchor = ('   - Do not cut the pads larger. In the 3D model, 10 x 16 pads centred on the bodies leave 0.54 mm between '
              "M6's and\n     M8's, 0.56 mm to M9's, and 0.86 mm between M1's and M7's.\n")
    assert t.count(anchor) == 1, 'anchor'
    return t.replace(anchor, anchor + '\n'.join(textwrap.wrap(D4, 118, subsequent_indent='     ')) + '\n')


def main():
    copy, out = sys.argv[1:3]
    os.makedirs(out)
    edit(os.path.join(copy, 'README.md'), os.path.join(out, 'README.md'), readme)
    edit(os.path.join(copy, 'BUILD_NOTES.md'), os.path.join(out, 'BUILD_NOTES.md'), build_notes)
    print('wrote', out)


if __name__ == '__main__':
    main()
