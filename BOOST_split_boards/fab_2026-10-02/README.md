# Fab outputs for the 6-layer power board (2026-10-02)

The power board is `BOOST_schematic_cleanup/KiCad/BOOST_power_RC2.kicad_pcb`, e3e92c26. It is the same in all three
folders: the 6-layer variant A from `../power6_2026-10-01/`, plus the user's GND, LX and gate-drive rework and the
M2/M7 reroutes. The card outputs are not regenerated; they stay as in `../fab_2026-09-30/`.

**Tools** are copies of `fab_2026-09-30/tools/`:
- **`fab_drawing.py`** has a `POWER6` branch:
  - the JLC061611-7628D table (prepreg 2 x 7628 0.421 / core 0.130 / prepreg 3 x 3313 0.291 / core 0.130 / 2 x 7628
    0.421);
  - a bold note to order it with "Specify Stackup: Yes".
  - The card-only 0.5 oz test (`HALF`) is now limited to the card, because the power board's 1.583 mm sat next to its
    1.58 threshold.
- **`update_docs.py`** made the ORDER_CHECKLIST, BUILD_NOTES and README edits.

**Run** (from this folder):
```
sh tools/make_fab.sh ../../BOOST_schematic_cleanup/KiCad/BOOST_power_RC2.kicad_pcb BOOST_power_RC2 BOOST_power_RC2
"<KiCad python>" tools/fab_facts.py BOOST_power_RC2/.src/BOOST_power_RC2.kicad_pcb work/power_facts.json
python tools/fab_drawing.py power
```

**Checks:**
- **DRC on the saved file:** 0 errors, 0 unconnected, and the 49 expected warnings.
- **A test refill:** one zone-layer (Vin, In2) differs by 0.0002 mm2 and 5 vertices. That is filler noise; a second run
  showed 2.
- **The outputs:** 18 files (In1-In4 copper). The plotted copy is identical to the board, and no work-in-progress name
  appears in the outputs.
- **Facts against 2026-09-30:**
  - 974 vias (it was 872): 102 x 0.30/0.50, 132 x 0.30/0.60, 626 x 0.40/0.80, 114 x 0.50/0.90.
  - The smallest via annular ring is 0.10 mm (it was 0.15); the quote's "min via 0.3 / 0.4-0.45 mm" option covers it.
  - The filled via closest to a pad hole is still 0.481 mm away (JLC needs > 0.45).

**Copied to** BOOST_package, BOOST_schematic_cleanup and BOOST_stuff: `BOOST_power_RC2_gerbers.zip` (9a030214) and
`BOOST_power_RC2_fab_drawing.pdf` (742a0285). The old files are in `../previous/2026-10-02/before_power6_release/`.
