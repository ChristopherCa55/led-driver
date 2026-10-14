## Update 2026-10-13: read this first

Your answers of 2026-10-12 and 2026-10-13 are in `ANSWERS.md`. With them, everything still open on 2026-10-11 is
now in the copy, and the copy's outputs were regenerated. It stays NOT_FOR_FAB until you say ship.

**Now in the copy** (on top of steps 1-4 and 6b):
- **Step 5g** (`work/step05g/STEP.md`): the I2C pull-ups R106 / R107 (4.7k) as **0603**, both on the card's front,
  and R99 / R102 at 1k.
  - R106 is at (57.15, 94.0), in J9's top label row above J9.5 / J9.7; the I2 / SCL labels moved up above it.
  - R107 is at (55.15, 101.45), below J9's I1 label, and joins J9.8 on In2.
  - J9's front courtyard hugs its pads (board and library); H3's label is 0.35 mm lower.
  - LTspice: the pull-ups, and `solver=alt` on `.options`.
  - Your own 10-11 save of the card sheet (U26D moved) is kept and recorded in `work/promotions.log`.
- **Step 7e:** the two card GND stitching vias.
- **Step 8c:** U101A-Y from In1 to In2.
- **Step 9** (`work/step09/STEP.md`): D5- re-routed so it no longer cuts the card's In4 GND in two. In4 GND goes from
  9 to 8 pieces, and the main piece from 626 to 952 mm2.
  - 0err_hi and SDA were tried too and stay where they are: every alternative split more plane, or broke a
    sensitive-net rule or a thermal relief (`work/CARD_SPLITTERS.md`).
- **Step 10:** two Vout_3 loop vias at C4.1, your choice from `work/whatif_1013/LOOP_VIAS.md`, which also has ch3 and
  ch1 (not added).
  - Vout_3 loop: worst via 2.80x -> 1.82x, loop R 0.682 -> 0.601 mOhm.
  - LX L1 -> M5: 1.967 -> 1.978 mOhm.
- **Regenerated** (`work/regen_final/`; dry run `work/REGEN_DRYRUN.md`):
  - gerbers, drill, IPC-356 and fab drawings for both boards (power 972 vias, card 398);
  - the 4 JLC BOM / CPL CSVs, SOURCING_TABLE.md, COST_SUMMARY.md and BOOST_BOM.xlsx (Excel: 0 formula errors);
  - CLEARANCES.md (all 67 rows unchanged) and `BOOST_assembly_2026-10-13.step`;
  - ORDER_CHECKLIST.md totals.
  - **Total $599.01 (was $598.99):** R106 / R107 join the existing 4.7k line and R99 / R102 the 1k line, so there is
    no new part.
  - The older STEP files in the copy are the shipped ones, left in place.

**Final checks on the copy** (`work/final_copy_check_1013/`; the copy's 20 KiCad design files are byte-identical to
step 10's, whose full gates ran, including the DC solve, loop L, gate returns, GND heatmap and sens_check6):
- ERC 0 / 0 / 0.
- DRC power: 0 errors, 49 warnings (the baseline's 46 silk over copper, 2 silk overlap, 1 library mismatch),
  0 unconnected, parity 0.
- DRC card: 0 errors, 1 warning (J11), 0 unconnected, parity 0.
- sync_check: 326 units, 0 differences.
- ltspice_equiv: E1-E5 PASS.
- Fab note: on the power board KiCad Python's refill differs from the stored fill by about 0.0002 mm2 on one or
  three zone-layers (it varies between runs: polygon vertices only). DRC with a fresh refill is clean.

**Worse than the baseline, new since 10-11** (all in what you approved):
- **Step 10 (Vout_3 vias):**
  - LX L1 -> M5 R 1.969 -> 1.978 mOhm, long-neck 25.8 -> 30.3 C (2.1 mm);
  - loop LX M1 -> M5 1.854 -> 1.860 mOhm, long-neck 25.4 -> 27.4 C;
  - the Vout_3 loop's 1.0 mm neck 84.9 -> 90.3 C, long-neck 55.3 -> 58.7 C, vias over rating 3 -> 5 (the new vias
    just over 1x each, while the worst drops to 1.82x);
  - GND ch1 / ch2 bank necks +0.2 / +0.1 C.
  - All are short necks, so they are reported, not judged.
- **Step 5g:** the card's largest F.Cu GND piece 348 -> 343 mm2 (R107 and its vias in the front pour).
- **Step 8c (U101A-Y), net of step 9:** card track over plane gaps 196 -> 198.9 mm.
- Baseline-to-copy table: `work/METRICS_final_2026-10-13.md`; per step: `work/METRICS.md`.

**Changed files in the copy since 10-11** (old -> new SHA-256 prefix; backups in
`previous/2026-10-11/promote_steps05g-10`, `promote_step05b_lt`, `promote_regen-1013`, `promote_docs-1013`,
`promote_readme-1013`):
- `KiCad/BOOST.kicad_sch` f407f442 -> b6d660f8.
- `KiCad/BOOST_control_RC2.kicad_sch` 13af0cd6 (your save) -> d687838b.
- `KiCad/BOOST_control_RC2.kicad_pcb` 40c9c7f6 -> cdd5f629.
- `KiCad/BOOST_power_RC2.kicad_pcb` 871f3a1d -> fafb44b3.
- `KiCad/BOOST.pretty/WirePads_11_Staggered_P1.27mm_Drill1.0mm_TieSlots.kicad_mod` 6a787584 -> 8e5ab0ab.
- `LTspice/BOOST.asc` cc28c9fa -> bfd51e7c.
- Gerber zips: power ff3c1290 -> f6fdf259, card 72cb46ac -> 67e2283a.
- Fab PDFs: power 396fdc86 -> 51766cc8, card 55a22771 -> 64af6eea.
- Card BOM c66c63fc -> 9b2132ff, card CPL 5b7a2d14 -> 97e29ddf. The power BOM / CPL are unchanged.
- SOURCING_TABLE.md d04ae259 -> d4092ac4; COST_SUMMARY.md 930307a1 -> 1a5ecd2f; BOOST_BOM.xlsx 09dbefa8 -> d322f952.
- CLEARANCES.md 8e07cc62 -> bbcb4a2e; ORDER_CHECKLIST.md 5bd1bf9f -> eb7bd90b.
- `BOOST_assembly_2026-10-13.step` (new) 7bf83adc.
- CHANGES_XY.md 4a0b166f -> 7e423343; README.md effabd4a -> 229586fa.

**Outside the copy:** `ltspice_layout_handoff_2026-10-05/tools/approved_changes.json` gained the solver=alt
approval on 2026-10-12 (by the session that continued from the handoff). `tools/route_new.py` gained:
- `fill_cost` (prefer existing plane gaps);
- `foreign_track_keepout` (2 mm from U2 In+ / Current / V_err on the layers sens_check6 checks);
- `net_clearance` (per-net clearance);
- `h_weight`;
- no via in or touching a pad of its own net.

New tools: `fp_text_edit.py`, `try_reroute.sh`, `make_fab_copy.sh`, `fab_drawing_copy.py`, `docs_edit_1013.py`,
`step05e_kicad_sch.py`, `step05g_card.sh`.

**Still open:** nothing from the review list that you have asked for. Not done, as before: the D6 renames (your "no"),
the other power reroutes ("not now"), the D8 open items, ch3 / ch1 loop vias (your "no"), and the D19 KiCad Sim-field
question. Shipping into the three shipped folders waits for your words.

The 2026-10-11 report follows unchanged. Its "Decisions for you" section is answered above.

