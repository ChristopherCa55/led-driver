# Shipping the review fixes to the three folders (2026-10-14)

**The user's words:** "Can you update the 3 folders boost package, schematic cleanup, and boost stuff to be like they
used to be, but with the updated ltspice schematic, updated kicad main schematic, subschematics, and pcbs. I want all
files to be updated to the new layout, regenerate gerbers."

**Backups:** full copies of the three folders as they were (the 2026-10-10 shipped state, every file hash in
`checks/before_<folder>.sha256`) in `../previous/2026-10-14/before_ship/`.

## What went into each folder (`ship.log`: every file, old -> new SHA-256 prefix)
- **All three:**
  - KiCad: `BOOST.kicad_sch` b53b5baf (the user's main page), `BOOST_power_RC2.kicad_sch` 3dd58076,
    `BOOST_control_RC2.kicad_sch` d2daaed3, `BOOST_power_RC2.kicad_pcb` fafb44b3, `BOOST_control_RC2.kicad_pcb` cdd5f629,
    `BOOST.pretty/WirePads_11_Staggered_P1.27mm_Drill1.0mm_TieSlots.kicad_mod` 8e5ab0ab (J9's front courtyard).
    Every other KiCad file was already identical.
  - LTspice: `BOOST.asc` c0703433 (the user's re-placed pull-ups, saved 2026-10-14 00:07). ltspice_equiv E1-E5 PASS
    against the shipped original with the approved changes (`checks/ltspice_equiv.txt`). The .asy / .lib files were
    already identical.
  - README.md 064444f5: the review copy's README without its "what changed" section (no history, as before).
  - Gerbers and fab drawings, re-plotted today from BOOST_package's boards (`fab/`): power zip e78c99bc, drawing
    63a9a7fd; card zip 7a513e76, drawing 158da47b. Their content equals the 2026-10-13 regeneration line for line,
    apart from the date stamps.
  - `BOOST_assembly_2026-10-13.step` 7bf83adc replaces `BOOST_assembly_2026-10-07.step` (sent to the Recycle Bin;
    copies in the backup). No document named the old file.
- **BOOST_package** also:
  - BOOST_BOM.xlsx d322f952 (full workbook) and the card BOM / CPL CSVs;
  - COST_SUMMARY.md, SOURCING_TABLE.md, CLEARANCES.md and ORDER_CHECKLIST.md;
  - BUILD_NOTES.md (the M8-M10 heat note).
  - The power BOM / CPL were already identical. The 09-25 STEP / STL / 3D PDF and the old `~$BOOST_BOM.xlsx` are
    untouched.
- **BOOST_stuff** also: BOOST_BOM.xlsx 57268b91 (the reviewer workbook, `make_xlsx.py --review`; Excel check 0
  formula errors, $599.01), and JLC_SELECTIONS.md (card assembly $162.48 / $219.31, 468 of 972 vias in pads, total
  $599.01).
- **BOOST_schematic_cleanup:** only the "all three" files.

## Checks on the shipped files (`checks/<folder>/`, run on scratch copies; `tools/gates.sh`)
Each folder:
- ERC 0 / 0 / 0.
- DRC power: 0 errors, 49 warnings (46 silk over copper, 2 silk overlap, 1 library mismatch: the long-standing
  ones), 0 unconnected, parity 0.
- DRC card: 0 errors, 1 warning (J11), 0 unconnected, parity 0.
- sync_check 0 differences (326 units).

Before / after file lists (`checks/before_*.sha256`, `after_*.sha256`) show only the files above changed. KiCad's
`.history`, `-backups` and `.kicad_prl` files are untouched.

The design and its checks are recorded in `../review_fixes_2026-10-11/` (FIX_REPORT.md, CHANGES_XY.md).
