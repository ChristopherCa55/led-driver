# 3D assembly rebuilt 2026-10-02: 6-layer power board

- **The thickness.** The power board is 1.583 mm (JLC061611-7628D) instead of 1.654. `build_assembly.py` now uses
  `T_NOM = T_MODEL = 1.583`, so the stack and the parts both sit on the real nominal top. JLC's +/-10 % tolerance
  still applies.
- **The inputs.**
  - `work/power.step` is exported from `../fab_2026-10-02/BOOST_power_RC2/.src/`.
  - `work/card.step` is re-exported from the current card (5df474e9).
  - `geometry.json` was rebuilt. Only R70 moved (-0.31 mm in x); the other differences are value texts from the
    earlier part swaps.
- **The output** is `BOOST_assembly_2026-10-02.step` (3967b9b5), copied to the three folders; the 09-30 STEP went to
  the Recycle Bin, and backups are in `previous/2026-10-02/before_power6_release/`. CLEARANCES.md went to
  BOOST_package.
- **The clearances.** All 67 rows are present, and every change is a few hundredths:
  - the card to tall power parts +0.01 to +0.05 mm;
  - the lid to the card screws 0.77 mm and to U18/U28 1.11 mm;
  - D30 to R73 1.68 mm.
  The under-1 mm rows are the same items as before.
- The previous inputs and outputs are in `work/before_power_6layer/`.

# 3D assembly rebuilt 2026-09-30 (BOOST_schematic_cleanup boards)

**Rebuilt again later on 2026-09-30 with the 6-layer card**, which is 1.609 mm thick instead of 1.654.
- `build_assembly.py` has `T_CARD_MODEL = 1.609` for the card top.
- `write_clearances.py` states both thicknesses.
- 6 of the 67 clearance rows changed, all by the thinner card:
  - lid to the four card screw heads, 0.65 -> 0.69 mm;
  - lid to U18 and U28, 0.98 -> 1.03 mm.
- The 8-layer-card build's `clearances.json`, `card.step`, `geometry.json` and CLEARANCES.md are in
  `work/before_card_6layer/`.

This is the same build as `../assembly_3d_2026-09-24/` (see its README), from the boards plotted in
`../fab_2026-09-30/*/.src/`. `BOOST_assembly_2026-09-30.step` was copied into `BOOST_schematic_cleanup/`.

What changed from the 2026-09-24 build:
- `tools/board_geometry.py` is new. It writes `work/geometry.json`, whose original generator was not kept. Run on
  the RC1 plotted boards, it reproduces the old `geometry.json` exactly (290 footprints and both outlines).
- `tools/build_assembly.py`:
  - writes `*_2026-09-30` output names;
  - has check 9, which measures D28-D30 and R47 (added or moved on the power board's underside) against the nearest
    part, fixing or case wall.
- `tools/write_clearances.py` has a new title date.

Run from this folder:
1. `kicad-cli pcb export step --subst-models` on each plotted board, into `work/power.step` and `work/card.step`.
2. `"<KiCad python>" tools/board_geometry.py POWER.kicad_pcb CARD.kicad_pcb work/geometry.json`
3. The boost3d venv's python on `tools/build_assembly.py`, then `tools/write_clearances.py`.

Result:
- All 63 clearance rows of the 2026-09-25 build are identical.
- The new rows:
  - D28 to M10, 1.13 mm;
  - D29 to M8, 1.02 mm;
  - D30 to R73, 1.75 mm;
  - R47 to M4, 1.18 mm.
  None is under 1 mm.
- The builder's own GLB is here without the unit and axis fix: `step_to_glb.py` was not run. No STL or 3D PDF was
  made this time.
