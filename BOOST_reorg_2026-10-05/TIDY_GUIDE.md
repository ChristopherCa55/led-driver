# Tidy guide for the reorganized schematics (for you - delete this file before sending the folder)

## What has been done
- **KiCad: one schematic per board.** `BOOST_power_RC2.kicad_sch` and `BOOST_control_RC2.kicad_sch` are each their
  board project's own schematic. `BOOST.kicad_sch` is the system page that includes both.
- **Blocks:** the parts are grouped into dashed, titled blocks, one per circuit.
  - Wires that ran between blocks, and very long wire runs, were replaced by global labels with the same name at
    each end.
  - Nets that had no name got one from KiCad's own name for them: `Net-(U102B-A)` became `U102B_A`.
- **LTspice:** `BOOST.asc` has the same blocks in the same places, power board left and control card right, and the
  same label names. The simulation-only parts and all the directives are in the test-bench area at the bottom.
- **What was not tidied:** the placement *inside* each block is still yours. That covers overlapping text, GND symbols
  printed over values, and parts squeezed together.
- **Checks:** both schematics connect exactly the same pins as before. Both PCBs pass KiCad's own schematic-parity
  check, and their gerbers are unchanged.

## Rules that keep the PCB link intact
- **Move parts; never cut/paste or delete and re-add them.**
  - In KiCad, use M (move) or G (drag, wires follow). A pasted part is a new part with a new ID, and its footprint
    loses its link.
  - In LTspice, use F7 (move) and F8 (drag).
- **Keep every part on its own board's sheet.** The connectors J10 (power) and J11 (card) are the only links between
  the boards.
- **Don't rename a label unless you mean to.** Two labels with the same name are one net, and a new name renames the
  net on the PCB.
- **After a session in KiCad:**
  1. Run ERC on `BOOST.kicad_pro`. It should report 0.
  2. Open each board project and run Tools -> Update PCB from Schematic. It should list no changes; if it offers to
     replace or delete footprints, cancel and ask.
  3. Run DRC with "Test for parity between PCB and schematic". It should report 0 parity issues.

## Tidy tips
- **Flow:** inputs on the left, outputs on the right; supplies at the top, GND at the bottom.
- **Labels instead of wires between blocks:** if a wire has to cross another block, put a label at each end instead.
- **Power symbols at the pin:** a GND symbol right below each pin that needs it, and rail labels right at the pin. No
  long wires to a shared GND.
- **Text:**
  - In KiCad, hover a part and press E to move its reference and value off the wires.
  - Keep text horizontal and keep it off symbols.
  - Field text can be moved on its own: hover it and press M.
- **The three channels:** make channels 1, 2 and 3 look the same and line them up, so the reader learns one and
  knows all three. This applies to the LED regulators, gate drivers, error amplifiers and sample-and-holds.
- **Logic gates:** upright, inputs left and output right. Their power units are collected in "Logic supplies and
  spare gates".
- **Decoupling caps:** next to the IC they serve, with that IC's rail label and GND symbol.
- **Crossings and junctions:** avoid 4-way junctions. Where two wires cross without a dot they are not connected;
  keep such crossings rare.
- **Block boxes:** if a block grows, drag its dashed box (or redraw it); the boxes are only graphics.
