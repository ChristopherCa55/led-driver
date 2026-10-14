# Fix report: 2026-10-10 schematic and PCB reviews (BOOST LED driver)

Run from `review_2026-10-10/FIX_PROMPT.md`, with your answers in `ANSWERS.md`. The work copy is
`led-driver/BOOST_review_fixes/` (marked NOT_FOR_FAB). **No shipped folder was written.** Every number below comes from
the tools in `tools/` and the outputs in `work/`.

## Summary

**In the copy now** (every gate passes, nothing worse that you had not accepted):
- LTspice: notes, diode part names, `.ic` clean-up (step 1).
- KiCad: diode part names; J1-J8 named Vin+ / Vin- / Out1+ / Out1- / Out2+ / Out2- / Out3+ / Out3- on the schematics
  and on the power board's front silkscreen; main-page title block; U26D moved (step 2).
- Power board: the 12V route (Option A, step 3), two ch2 loop vias (step 4), three more Vin vias at R1 (step 6).
- Documents: README (D19 sentence, "what changed"), BUILD_NOTES (M8-M10 heat), CHANGES_XY.md.

**Built and checked, waiting for your OK** (not in the copy): the I2C pull-ups and 1k address resistors (step 5),
two card GND stitching vias (step 7), and U101A-Y moved off the card's In1 plane (step 8). Their questions are in
"Decisions for you" at the end.

**Not changed**, with the reasons below: net renames, the overview and directive regrouping, the bypass-cap note,
the master-copy line (no answer to D6 / D8's open items); the other X3 reroutes; the card's other plane-splitting
tracks (no route exists off the GND layers).

**Every change with its x / y and layer:** `CHANGES_XY.md` (also in the copy).

## Final checks (the copy's files, `work/final_copy_check/`)

| Check | Result |
|---|---|
| ERC, main page / power sheet / card sheet | 0 / 0 / 0 |
| DRC power board (refill, parity) | 0 errors, 0 unconnected, 49 warnings (the same 49 items as the baseline), parity 0 |
| DRC control card (refill, parity) | 0 errors, 0 unconnected, 1 warning (the baseline's), parity 0 |
| sync_check (main page against both board sheets) | 324 part units, 0 differences |
| ltspice_equiv (copy's `BOOST.asc` against the frozen original) | E1-E5 PASS |
| LTspice simulation (step 1 file) | LED currents equal to the shipped file's within 1e-9 A; Ptvs 11.72 -> 11.67 mW (solver ordering) |

The pending steps were checked the same way (each `work/stepNN/` has its logs). Step 5's LTspice candidate passes
E1, E2, E4 and E5; E3 fails only on the `.options ... solver=alt` line that waits for your OK.

## Item by item

### Schematic review

| # | Item | Status | What changed / why not |
|---|---|---|---|
| 1 | No I2C pull-ups | **Waiting for your OK** (step 5) | R106 / R107 4.7k to 5V on SCL / SDA in LTspice, both KiCad schematics, the card PCB (0402, B side), BOM / CPL. The MCP4451 has no internal pull-ups (Microchip DS22267A) |
| 2 | U26 HVC/A0 | **Waiting for your OK** (step 5) | R102 and R99 10k -> 1k: A0 and A1 cannot latch high, so the address is 0x2C. R99 / R102 join the card's existing 1k line (C21190), no new part |
| 3 | D19 against the LX peaks | No change (your answer) | README sentence added: D19 modelled at 60.0 V conducts in 101 of 453 cycles, 9.5 mW average |
| 4 | Heat in M8-M10 | Documented (D4, not answered: documentation only) | BUILD_NOTES: 3.9 / 3.4 / 3.4 W, about 7.5 K across the pad at 3.9 W; the FET's R_jc is unverified |
| 5 | `.ic` names missing nodes | **Fixed** (step 1) | `.ic V(Out)=0 V(Out-)=1` at (-6376, -4352); the commented-out `.ic` at (-6416, -3488) deleted. Bit-identical waveforms without the three terms |
| 6 | No overview | Not changed | D8's open question (section tags "(card)" / "(power)") was not answered |
| 7 | Net names | Not changed | D6 not answered (recommendation was notes only, no renames) |
| 8 | One-hot select unexplained | **Fixed** (step 1) | Note at (1921, -6383): "one-hot from U18: picks Verr1/2/3" |
| 9 | Sections without notes | **Fixed, partly** (step 1) | Notes at the latch (3488, -6096), the enable delays (4336, -6600), U15's DT pin (-1974, -8524), U19's channel B (-3584, -6222). The 220 ohm / 5.1 ohm reason is not recorded anywhere, so no note |
| 10 | Directives | **Partly** (step 1) | `.ic` cleaned, commented `.ic` gone, diode `.model` aliases added. The column regrouping, the split POTn note and the LED_ model comment were D8 open questions, not answered |
| 11 | Smaller gaps | **Fixed** (step 1) | U18 note at (1216, -5927) "...5V by net name (SpiceModel)"; "same as channel 1" at (672, -3440) and (4176, -3536) |
| 12 | No title block (main page) | **Fixed** (step 2) | Title, rev RC2, comment line; picture `img/mock/kicad_v4/k2_title_block.png` |
| 13 | 22 diodes valued "D" | **Fixed** (steps 1, 2) | Part names in LTspice (with `.model` aliases, simulation unchanged), on all three KiCad schematics and both PCBs |
| 14 | J1-J8 "Conn_01x01_Pin" | **Fixed** (step 2) | Values Vin+ ... Out3- on the schematics; on the power board the labels replace the references on F.SilkS. Pictures `img/step02/silk_bottom_edge_v3.png`, `silk_J1J2_v3.png` |
| 15 | U26D touching U106D | **Fixed** (step 2) | U26D (129.54, 440.69) -> (142.24, 440.69) with its 3 no-connect flags; `img/mock/kicad_v4/k1_spares_before.png` / `_after.png` |
| 16 | Bypass-cap row note | Not changed | D8 open question not answered |
| 17 | Small visual gaps | Not changed | Re-placing the main page's channel rows and the MOSFET symbol were not asked for in the decisions |
| 18 | `~$BOOST_BOM.xlsx` in the shipped folder | Not changed | The shipped folders are read-only for this run; the copy has no lock file |
| 19 | Which schematic is the master | Not changed | D8 open question not answered |

### Power board

| Item | Status | Numbers (baseline -> copy) | Pictures |
|---|---|---|---|
| P1 Vin funnel / 12V | **Fixed** (steps 3, 6) | Vin J1 -> R1 1.031 -> 1.003 mOhm; worst neck 38.8 -> 29.3 C; worst Vin via 1.59x -> 1.39x; ripple path 0.367 -> 0.344 mOhm | `img/step03/12V_In4_before.png` / `_after.png`, `12V_B_*`, `img/step06/vin_vias_F_*` |
| P2 Output 1 to J3 | Not changed | 8.459 mOhm. The review's pinch at y = 68.7 is not the limit: removing the In3 Vin bar gains only 1.3 % (what-if `work/proto/p2_bar_NOT_FOR_FAB`, which was also DRC-invalid) | - |
| P3 LX to ch3 | Not changed | 1.969 -> 1.967 mOhm. Mostly length; the review's own what-if gained 3 % | - |
| P4 other necks | Not changed | Each <= 7 mV and <= 0.02 W (review). The analog_5V vias have no spot outside the Output2_drain strip without longer detours | `img/x3/a5v_out2drain_*` |
| P5 D28/D29 Vin feed | Not changed | Moving it was not part of the decisions; also, the western trunk feeds U17 / U1 too (review correction 3) | - |
| P6 switching nodes / gate tracks in pours | Not changed | m4_source (In4), D13- (B.Cu), GATE_M7 (In4), GATE_M4 (In3): each move needs a layer that is a power pour or In1, the board's one whole GND plane. Gate-return and loop metrics unchanged | `img/x3/gm4_*.png`, `d13_B.png` |
| P7 M1's GND island | **Partly** (step 3) | The In4 12V loop is gone: In4 GND 16 -> 15 pieces, largest 707 -> 774 mm2 (M1's island joined). In2 / In3 parts unchanged | `img/step03/12V_In4_*` |
| P8 GND fragmentation | **Partly** (step 3) | The B.Cu 12V detour round M1 is gone; the new 0.4 mm B.Cu 12V track adds one B.Cu GND piece (17 -> 18) and one splitting track (35 -> 36), accepted with Option A. GND slices >= 3 mm 60 -> 58 | `img/step03/12V_B_*` |
| P9 Current track, short segments | **Partly** | Short segments 674 -> 667. The Current track was not moved: it runs over In1 (the whole GND plane, 0.42 mm below) and a shorter path crosses the L1 / R1 / LX pours | `img/x3/current_F.png` |

### Control card

| Item | Status | Numbers (baseline -> if approved) |
|---|---|---|
| C1 In1 pieces | **Waiting for your OK** (steps 7, 8) | Two stitching vias in the review's one-via piece at (73.2, 86.9); U101A-Y moved to In2: In1 GND 12 -> 11 pieces, main piece 895 -> 972 mm2 |
| C2 In3 pieces | Not changed | The 21.4 mm2 one-via piece has no legal second via spot |
| C3 In4 cut in two | Not changed | 0err_hi (In4) has several branches; the In1 0err_hi span has no route on In2 / F / B |
| C4 In2 / outer layers | Not changed | (Steps 5 and 8 add two slots to the In2 5V pour) |
| C5 stacked tracks | Not changed | Reset_raw / IREF1 over SDA: SDA has no route off In1 (`work/trySDA`) |
| C6 cleanliness | Not changed | (D13: only on routes already touched) |

### Open 10-02 items

| Item | Baseline | Copy now | Note |
|---|---|---|---|
| Loop vias over IPC | ch2 3.6x, ch3 2.72x, ch1 2.06x, Vout_3 2.8x | ch2 **1.72x**, others unchanged | D10 option (a). ch1 costs Vout_1 +3.7 %, ch3 / Vout_3 cost LX L1 -> M5 +4 %: not applied |
| Unreturned gate drive | M2 42 %, M7 38 % | the same | Not touched |
| Sense nets over GND | 74 % | 74 % | Not touched |
| U16 Tj | 117.8 C | 117.7 C | tab-to-ambient 23.61 -> 23.55 K/W, background 16.04 -> 15.97 K |
| J4-entry stitching vias (your 10-02 edit) | | unchanged | Your call; not touched |

## Metrics

- Every step: `work/METRICS.md` (baseline, step 3, 4, 5d, 6b, 7d, 8b).
- Baseline against final: `work/METRICS_final.md` (baseline / the copy now / if steps 5, 7 and 8 are approved).

**Values worse than the baseline in the copy now, and who accepted them:**

| Metric | Baseline -> copy | Cause | Accepted |
|---|---|---|---|
| Vin J1 -> R1 vias over rating | 4 -> 5 | Option A opened one column of the Vin array | You, with the 12V route (X1) |
| B.Cu GND pieces (power) | 17 -> 18 | The new B.Cu 12V track | You, with X1 |
| Tracks splitting GND (power) | 35 -> 36 | The same track | You, with X1 |
| Short-neck rises | GND ch2 bank 6.1 -> 7.9 C (0.2 mm neck), loop GND ch2 12.1 -> 20.1 C (0.1 mm), loop GND ch1 25.8 -> 26.1 C (3.7 mm), loop LX M1 -> M5 56.7 -> 57.0 C (1.3 mm), GND ch1 bank 5.1 -> 5.7 C (0.5 mm), GND M1 long-neck 4.5 -> 4.9 C | Current redistribution after steps 3 / 4 | Reported, not judged (necks under 5 mm); every one of these paths has lower R than before |
| Loop GND ch2 vias over rating | 3 -> 5 | The two new vias share the current at just over 1x; the worst halved (3.6x -> 1.72x) | You, D10 option (a) |
| Vout_2 bank / LED path R | 0.312 -> 0.315, 3.077 -> 3.082 mOhm | The new vias' antipads in In4 Vout_2 | You, D10 option (a) (stated as +1.2 %) |

**Further values worse if steps 5, 7 and 8 are approved:** card B.Cu GND pieces 18 -> 20 and largest 362 -> 315 mm2
(step 5); card F.Cu GND pieces 27 -> 28 (step 7: a new 8.1 mm2 F.Cu GND patch the vias keep, not a split); tracks over
plane gaps 106 -> 109, 196 -> 204.7 mm, and stacked pairs 83 -> 84 (steps 5 and 8). Details in each `STEP.md`.

## Changed files

**In the copy** (`led-driver/BOOST_review_fixes/`; old files in `BOOST_split_boards/previous/2026-10-11/promote_*`):

| File | Old SHA-256 | New SHA-256 |
|---|---|---|
| `LTspice/BOOST.asc` | 1f008632aebde811314e02d13b4f9aa272b92e4ab0bed6f4e7b61b0172b31756 | cc28c9fa0af7965b4102b6b5b20b279526d136d6f2cd6a0db40d738121d1159f |
| `KiCad/BOOST.kicad_sch` | 899c761cfd6c59d5df1dff41b75d38a0b5369be740f893b18aed820bf8970b18 | f407f44203c306085803da51a8c12a53d02077f71c8352080e2e8ba9e79a7231 |
| `KiCad/BOOST_power_RC2.kicad_sch` | 88faea8208367809d21e56a43dd6f87f4aa748d3cc76cfd39c5343fa80dfcc09 | 3dd5807677a5960b973de1928f5ef752922d7aa73d40c0021acc6da7882c7530 |
| `KiCad/BOOST_control_RC2.kicad_sch` | f57cae741ebdf21c8e912b7a8bbc72d3ec801542b5fff1410aa842f6ad73eb01 | a2a4ea6f2cef4ed4d86b758a8fe9bcba28080bc160a8badb4a2c4373abf7705a |
| `KiCad/BOOST_power_RC2.kicad_pcb` | 01703432b05b05cc09988d1d3dcaa679838453c2b2b8ac8925d82bdcbb92bc05 | 871f3a1d147609075e0742f2f04a4c31ddb622e8dfa77dd6a026f1bdae39af9e |
| `KiCad/BOOST_control_RC2.kicad_pcb` | d34d1202d4cc8b9a8eef1ac13ce93688abc799e4bdc5e477ebf52788773a2504 | 40c9c7f61805059213fff1935a261a02724d14cb84bd768d75daf1dd444b65cb |
| `README.md` | b9a14fbb9eb097c47ad41224eecc78e1e100fbe6ff240372d662894ad6d6f793 | effabd4a9425664dd1140f05e9c38fed441a07b280bfc6ff92e93143a74175f5 |
| `BUILD_NOTES.md` | 64f3a649b450fb651e9ab810be9875c3728f3a455590fd84c376b45364de66d1 | a1d6cf5760b300f4933a1ba8d70dba6111d5e825b10abe02dc816aa9c591dbd9 |
| `CHANGES_XY.md` | (new) | 4a0b166f88b825928979d5e9c25b240b5848a47f6ea3bdd2098f1f877af00e4b |

The copy's gerbers, drill files, fab drawings, STEP and BOM / CPL are **not** regenerated (D14: after your approval).
Your KiCad left `.kicad_prl` files in the copy's KiCad folder; they are yours and were not touched.

**Outside the copy:** `ltspice_layout_handoff_2026-10-05/tools/approved_changes.json` (d6d7ed36 -> 5b594a28 for step 1,
-> d498423d with D1 / D2's additions for step 5; your words quoted in its `_review_fixes_note*` keys) and `ltspice_equiv.py`
(55ac4016 -> f73e5dbd: optional approval keys for directive / value changes and added elements; its self-test passes).
Backups in `previous/2026-10-11/before_equiv_approved_changes/` and `before_step05_approvals/`.

## What I could not verify

- **HYG180N10 junction-to-case resistance:** its data sheet is not on disk (D4 note says so).
- **UCC21520 DT = VCCI behaviour** (no dead time): from my earlier model notes; TI's data sheet was not re-read.
- **I2C bus capacitance and speed:** J9's wire length and the firmware's bus speed are not recorded. With 4.7k, the
  rise-time limit is about 250 pF at 100 kHz and about 75 pF at 400 kHz (0.8473 R C against 1000 / 300 ns).
- **Parts data:** C25900, C21190, C23162, C25804 stock and prices are JLC's parts listing (read 2026-10-11), not
  data sheets.
- **The LTspice stall** with R106 / R107 in the netlist is numerical; I could not find its cause, only that the values
  change alone runs and that solver=alt runs with the same results.

## Where the review was wrong or out of date

1. **Item 2:** A1 (R99, 10k) has the same latch issue as A0, so the address could have been 0x2C-0x2F, not only
   0x2C / 0x2D. The A0 firmware note the review mentions is not in the current README.
2. **Item 9:** U15's inputs are different signals (INA = M2_ON for M2 through R13 220 ohm / D11; INB = ena_out_1 for
   M7 through R60 5.1 ohm / D2), so "both FETs switch together" was wrong. DT = VCCI only disables the driver's interlock.
3. **P5:** the western Vin trunk also feeds U17 and U1, so it carries DC, not only the pre-charge surge.
4. **P2:** the In3 Vin bar at y = 68.7 costs only 1.3 % on Output 1's path; the limit is a 2.4 mm neck at (54.7, 72.3)
   and the path length.
5. **Loop vias:** the "worst" vias are ch2 inside C3.2's pad, ch3 inside C76.2's pad, ch1 at C1.2's edge, and Vout_3 the
   outer of three vias on C4.1. Adding vias there has the costs listed in D10.
6. **P1's what-if** (28.9 C) moved U19's 12V vias and the GND via out; the real Option A keeps U19.16's In4 hop and
   that GND via, so it reaches 29.7 C (29.3 C with step 6).
7. **P3 / D10:** moving GATE_M4's via does not avoid the ch3 loop vias' cost; that cost comes from their antipads in LX
   on In2 and B.Cu.
8. **C1-C3:** the longest plane-splitting tracks (0err_hi on In1, SDA on In1) have no route on In2, F.Cu or B.Cu, so
   "move the single tracks" works only for some of them (U101A-Y did move).
9. **D19 in KiCad:** its Sim.Params model is TVS_5KP54A and its LCSC field C20415356, which do not match LTspice and the
   BOM. Left as is, because you said D19 is fine; please confirm which is meant.
10. **CLEARANCES.md** (source table) still names the G579 thermal pad; BUILD_NOTES, COST_SUMMARY and ORDER_CHECKLIST
    make the McMaster 1272N32 the default. The heights are unchanged, so I left it.

## Decisions for you

1. **Step 2 labels:** are the Vin+ / Vin- / Out labels where you want them? (`img/step02/silk_bottom_edge_v3.png`,
   `silk_J1J2_v3.png`; "Out3+" stands vertical in the J6-J5 gap, next to J5, because no other spot clears the pads.)
2. **Step 5, the pull-ups** (`work/step05d/STEP.md`):
   - R106 / R107 are **0402** (C25900, one new part, about $1.53 more loading), because no 0603 spot near the bus is
     free and routable. Alternative: move C93 (Vref_2's 10 uF, under J9) and use 0603 (C23162, already on the card).
   - Their tracks fence off two small B.Cu GND pieces near U26 (26.9 and 14.2 mm2, both stitched by vias).
   - LTspice needs `solver=alt` on the `.options` line once R106 / R107 are in (runs about 3x longer); or leave them
     out of LTspice and keep them on the KiCad schematics only.
   - Placement pictures: `img/step05/i2c_area_after_preview.png` (LTspice), `main_U26E_final.png`,
     `card_U26E_final.png`, `card_R106_B_final.png`, `card_R107_B_final.png`.
3. **Step 7** (two GND stitching vias) and **step 8** (U101A-Y to In2: In1 main piece +79 mm2, 6.5 mm more track over
   In3 gaps, one more stacked pair): keep or drop?
4. **More loop vias** (ch1 / ch3 / Vout_3) with their stated costs: still no?
5. **D14:** once you approve, regenerate the gerbers, drill, fab drawings, BOM / CPL, cost files and STEP in the copy
   (still marked NOT_FOR_FAB until you say ship).

## Tools added this run (`tools/`)

`make_step.sh` (one copper step: text edit, refill, guards, gates), `step_checks.sh`, `card_checks.sh`,
`solve_only.sh`, `collect.py`, `pcb_text_edit.py`, `pcb_diff.py`, `changes_xy.py`, `route_new.py` (small grid
router: F / B / In2, clearances, rule areas, the card's 2 mm via rules, octilinear paths), `free_spots.py`,
`stitch_vias.py`, `add_footprints.py`, `make_fp_block.py`, `promote.py` (hash-checked promotion with backups),
`sync_check_rf.py`, `step01_ltspice.py`, `step02_kicad.py`, `step05_ltspice.py`, `step05b_ltspice.py`,
`step05_kicad_sch.py`, `step05_card.sh`, `step05_fab.py`, `docs_edit.py`, `pcb_render.py`, `net_map.py`, `sim_case.py`.

Lessons (also in `README.md`): run DC solves alone and with 3-5 workers while other apps are open (two ran out of memory
at 9 and 5 workers); vias with no track or pad need `(free yes)` or KiCad gives them a zone's net; the card's GND is in
the Power netclass (0.25 mm); never edit a bash script while it runs; Git Bash's `grep -c $'\r'` counts every line.
