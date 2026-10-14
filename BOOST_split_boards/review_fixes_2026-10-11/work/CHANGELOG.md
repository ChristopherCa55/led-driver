# Changelog (review fixes, 2026-10-11)

Each step was made on a scratch copy, gated (ERC, DRC with refill and parity, sync, and the metrics that apply), and
only then promoted into `BOOST_review_fixes/` (hashes in `promotions.log`, old files in
`previous/2026-10-11/promote_*`). Numbers are baseline -> after; the full table is `METRICS.md`.

## 2026-10-14: step 11 (in the copy)

- The user re-arranged R106 / R107 on the main page and asked for the same on the card sheet: `step11/`
  (`tools/sync_group_to_card.py`, shift +125.73 / +113.03); ERC 0, sync 0, card parity 0; promoted.

## 2026-10-13: the user's answers applied (in the copy)

- **Step 5g** (0603 pull-ups near J9; `step05g/STEP.md`): after step05e (3 silk_overlap warnings; route_new put a via in
  R107's pad, so it now forbids vias in own-net pads) and step05f (via position, a 0.07 mm jog). Built on the copy's
  files including the user's own card-sheet save (U26D). LTspice 5b (`solver=alt`) and the card BOM / CPL
  (`step05g_completion/`, made by the session that continued from the handoff; re-made identically by the BOM
  pipeline).
- **Step 7e / 8c**: steps 7 and 8 rebuilt unchanged on step 5g (`step08c/STEP.md`).
- **Step 9** (D5- re-route; `step09/STEP.md`, `CARD_SPLITTERS.md`): tries trySplit_D5 (too slow), D5b (In3 over U2
  In+, rejected), D5c (no route), D5d (kept), 0errIn4 / 0errIn1 / 0errIn1b / SDA / SDAb / SDAc (worse or no route).
- **Loop vias**: per-location what-ifs (`whatif_1013/LOOP_VIAS.md`); the user chose Vout_3 only -> **step 10**.
- **Promoted** steps 5g-10 and LTspice 5b; final gates on the copy (`final_copy_check_1013/`).
- **Regenerated** every output (`regen_final/`, dry run `REGEN_DRYRUN.md`) and promoted them; total $599.01.

## Promoted (in the copy)

**Step 1, LTspice documentation** (D5, D7, D8; `step01/`). `LTspice/BOOST.asc` 1f008632 -> cc28c9fa.
- Eight short notes from the approved mock-ups; diode Values = part names, with `.model 1N4148W D` (etc.) aliases so
  the simulation is unchanged; `.ic` without the three non-existent nodes; the commented-out `.ic` line deleted.
- Equivalence E1-E5 PASS (approved_changes.json extended with the user's words). Simulation: LED currents equal to 1e-9;
  waveforms not bit-identical (solver ordering), Ptvs 11.72 -> 11.67 mW.

**Step 2, KiCad documentation** (D7, D8; `step02d/`). Main page, both board sheets, both PCBs.
- 22 diode Values -> part names (schematics and PCBs); J1-J8 Values -> Vin+ / Vin- / Out1+ / Out1- / Out2+ / Out2- /
  Out3+ / Out3-, shown on the power board's F.SilkS in place of the references (references moved to F.Fab; J1, J4,
  J5 and J6 labels placed clear of pads); main-page title block; U26D moved one slot right with its 3 no-connect flags.
- ERC 0 / 0 / 0, DRC warnings identical to the baseline (49 / 1), parity 0, sync 0; copper unchanged.
- Earlier tries kept: step02 (3 new silk warnings, ERC 6), step02b / 02c (positions rounded).

**Step 3, 12V route Option A** (X1, P1 / P7 / P8; `step03/`). Power PCB.
- 22 12V segments and 3 12V vias removed (the In4 loop round M1, R1's funnel), 4 Vin vias removed (column x 80.85), one
  0.4 mm B.Cu 12V track added through that column.
- Vin J1 -> R1 1.031 -> 1.013 mOhm, worst neck 38.8 -> 29.7 C; GND branches 1-3 % lower R; In4 GND 16 -> 15 pieces.
  Costs (listed in X1, accepted with the route): Vin vias over rating 4 -> 5; B.Cu GND 17 -> 18 pieces; short-neck
  rises (reported, not judged).

**Step 4, ch2 loop vias** (D10 option (a); `step04/`). Power PCB.
- Two GND vias 0.8 / 0.4 in C3.2's pad: (33.24, 67.25), (34.44, 67.85).
- ch2 loop worst via 3.59x -> 1.72x, loop R 1.087 -> 0.993 mOhm; cost (stated in D10): Vout_2 bank +1 %.

**Step 6, three more Vin vias** (X1 follow-up; `step06b/`). Power PCB.
- Vin vias 0.8 / 0.4 at (72.08, 41.55), (72.08, 42.4), (72.08, 43.25), next to R1's funnel.
- Vin J1 -> R1 1.013 -> 1.003 mOhm, worst via 1.61x -> 1.39x, neck 29.7 -> 29.3 C; ripple path 0.355 -> 0.344 mOhm.
  Nothing worse. First try (0.9 / 0.5 at x 72.25, `step06/`) broke clearance to U19 pins 15 / 16 and was dropped.

**Documentation** (`docs/`): README.md (D19 sentence, "what changed" section), BUILD_NOTES.md (M8-M10 heat, D4),
CHANGES_XY.md (new).

## Built and gated, waiting for the user's OK (not in the copy)

**Step 5, I2C pull-ups and 1k address resistors** (D1, D2; `step05_lt/`, `step05b_lt/`, `step05d/`).
- LTspice, both KiCad schematics, card PCB, card BOM / CPL. R106 / R107 4.7k 0402 on the card's B side, routed by
  tools/route_new.py. Open points: 0402 size, two small B.Cu GND pieces fenced off near U26, LTspice needs
  `solver=alt` (see `step05d/STEP.md`).
- Earlier tries kept: step05 (silk warning), step05b (courtyard error), step05c (7 short segments); try05a-c, tryC*.

**Step 7, card GND stitching** (C1; `step07d/`): two free GND vias (0.5 / 0.3) in the In1 piece at (73.2, 86.9) that had
one via: (72.34, 84.823), (74.34, 85.673). F.Cu GND pieces 27 -> 28: the vias keep an 8.1 mm2 F.Cu GND patch that the
filler used to drop (new copper, not a split). Earlier tries: step07 (vias took the net 5V: no "free" flag), step07b
(0.2 mm clearance; GND is in the Power class, 0.25 mm).

**Step 8, Net-(U101A-Y) from In1 to In2** (C1; `step08b/`): In1 GND 12 -> 11 pieces, main piece 893 -> 972 mm2, tracks
splitting GND 79 -> 78; costs: 6.5 mm more track over plane gaps (In2 over In3 gaps), one more stacked pair (over
VerrGT0 on In3, 3 mm). step08 (built on step07c) is superseded.

## Tried and dropped
- 0err_hi (In1, 13.4 mm) and SDA (In1, around J9) off In1: no route exists on In2 / F / B (`tryC1`, `trySDA`).
- R106 / R107 as 0603: no free 0603 spot near the bus outside the H1-H4 washer areas that routes (`img/step05/card_free_*`).
- `Cpar` on the pull-ups to get past the LTspice stall: LTspice resistors have no Cpar parameter.
