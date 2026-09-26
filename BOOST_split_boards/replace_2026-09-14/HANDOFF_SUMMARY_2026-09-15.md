# BOOST re-place: handoff summary (2026-09-15)

Status of the work started from `led-driver/BOOST_split_boards/handoff_2026-09-14/HANDOFF_PROMPT.md`, written so another
session or account can pick it up. Paths are relative to `led-driver/` unless noted.

## 1. The job and the ground rules

The task, from `HANDOFF_PROMPT.md`, with a ★ user check-in at each stage:

1. Read the handoff files.
2. ★ Confirm open items.
3. Schematic changes (§4). ERC 0 errors / 0 warnings, netlist diff.
4. ★ Re-place the power board (`REPLACE_BRIEF_v2.md`, stages 1–6). Show a placement plot and distance table before any copper.
5. ★ Draw the power copper, solve it at 1 oz and 2 oz outer; the user picks copper weight B (1/1 oz) or C (2/1 oz).
6. Route signals, run the §6 checks, write a report in the `AUDIT_RESPONSE.md` style.
7. Re-place and re-route the control card.

Ground rules (from the handoff and the user):
- Never weaken a DRC rule or add an exclusion; keep the 1.0 / 0.15 mm silk rule.
- Back up shipped files to `previous/<date>/` before replacing them; mark work-in-progress boards "not for fabrication".
- Don't guess part specs or pinouts: read datasheets, and say when something can't be verified.
- Verify from saved files. In1/In6 stay GND-only. No LX copper on In3/In5.
- Don't run `sed -i` on the CRLF `.kicad_pro` files.

## 2. Where it stands

| Step | State |
|---|---|
| 1–2 Read, confirm open items | Done (four check-ins, decisions below) |
| 3 Schematic | Done and verified, including (2026-09-15 afternoon) C30/C7/C55, C41/C44/C45 restored, NoHole on M2–M7 |
| §8 item 1 simulation | Done (220 Ω chosen) |
| 4 Power-board placement | Accepted by the user (2026-09-15 evening) as the base for copper, with changes applied (§11a). One item open: the 4.0 mm tab-screw clearance. |
| 5–7 Copper, routing, control card | Not started |

Nothing in `BOOST_split_boards/BOOST_power.kicad_pcb` or `BOOST_control.kicad_pcb` has been replaced yet. KiCad lock
files (`~BOOST_power.kicad_pcb.lck`, `~BOOST_control.kicad_pcb.lck`) were present: close KiCad before replacing those files.

## 3. User decisions

### Check-in 1
- Divider resistors: both resistors of every divider on the control card.
- All ten TO-220 FETs lie tab-down against the aluminium case (TabUp footprint on B.Cu, body flat against the board underside), insulated. About 1 mm compliant thermal pad under every tab.
- Standoffs nylon; mounting holes isolated.
- Input caps: 3 × Panasonic EEH-ZU1E681UP (ZU(U), 680 µF 25 V, 10 × 12.5 mm, LCSC C29664285). LCSC had 10 in stock: plan JLCPCB assembly for at most 3 boards; the user fits caps by hand on any others. (This part does exist; an early claim that it didn't was wrong.)
- Output caps: EEH-ZU1H221P, 10 × 16.5 mm tall.
- Arduino is 5 V logic; 100 kΩ pull-down on the new inhibit pin; MCP6241 op-amps kept.

### Check-in 2
- R13/R23/R47 = 220 Ω (150 Ω had no dead-time margin at the 1.0 V threshold corner).
- Tab screws on M1, M8, M9, M10. They get tab holes, a 3.75 mm washer keep-out and a clear screwdriver path. Other FETs must be near a screw (rule relaxed at check-in 3). Keep MLCCs away from screw points.
- Card gap first set to 16.13 mm; changed to 21.21 mm (below).
- Case layout (example, "tell me if another way works better"):
  - Box inside 128 × 90 × 33 mm, 10 mm floor, origin top-left. Power board in the right end, x 52–126 (board coordinates = box − (22, −28)).
  - Floor penetrators Ø10 at (9.5, 3.5) and (118.5, 3.5), each with a Ø15 × 10 mm keep-out. Notch the board's top-right corner (~18 × 12 mm) for the battery cable.
  - LED 50 × 50 at the bottom-left; Arduino Nano (5 V, own supply) plus CAN module top-left.
  - J9 right-angle on the card edge facing the Arduino; J9's 5V pin stays unconnected at the Arduino end, GND shared.

### Stacking height (after placement showed 16.13 mm had no room)
- 21.21 mm gap: Samtec ESQ-115-44-G-D elevated socket on the power board (J10), TSW-115-07-G-D header under the card (J11).
- The card may sit over the output cans (4.4 mm clear) but never over L1.

### Check-in 3 (placement over-constrained)
- M2–M7 may be up to ~25 mm from the nearest screw (tab screw or card standoff).
- The brief's distance limits become goals with priorities:
  - Hard: rail FET → its own caps; M1 with D19 and its return; sink → shunt.
  - Loose: input caps ~20 mm; farthest switch-node drains ~22–30 mm.
- The card may sit anywhere not over L1 and not in the lug corner.
- LED pads J3–J8 may move to the bottom edge (left half); lugs J1/J2 may move lower on the right edge.

### Check-in 4
- J10 is placed first, with a FET-free strip on the underside beneath it. The card grows to 45 mm (a 39.2 mm J10 cannot fit a 42 mm card with 2 mm margins).
- Regulator bulk caps shrink (the top side had no room for them):
  - C30 (LM2940 12 V output) → solid tantalum ≥ 22 µF with ESR 100 mΩ–1 Ω.
  - C7 and C55 (L78L05 outputs) → 22 µF ceramic.
  - LCSC-stocked parts.
- Open, not yet answered: C41/C44/C45 (1 nF IREF wiper caps) are missing from the netlist compared with `BOOST_9-2_1013.net`. They were already absent before this work; `BOOST_CONTEXT_TRANSFER.md` §13 item 6 recommended removing them. Confirm with the user.

## 4. Schematic (`BOOST-github/BOOST/BOOST.kicad_sch`)

Backup of the pre-edit schematic, project, sym-lib-table and `BOOST_9-2_1013.net`: `BOOST_split_boards/previous/2026-09-14/schematic/`.
Latest verified state: ERC 0 violations (same four ignored checks as the shipped project), netcheck 0 failures, SHA-256
starting `295fd915…`.

Changes made:
- **R1:** 4-terminal Bourns CSS4J-4026K-2L00F (2 mΩ, 4 W, LCSC C2076167, out of stock on 2026-09-14), footprint `BOOST:R_Bourns_CSS4J-4026`.
  - Pins 1 = Vin, 4 = rsense_lo; sense pins 2 = ISNS_P → U25.8, 3 = ISNS_N → U25.1.
  - Backup part: CSS4J-4026R-1L00F (1 mΩ, LCSC C2076400) with U25 changed to INA241A4.
- **Sink sense net-ties:** NT1 (SNS_CH1 ↔ Net-(M10-S), U11.4), NT2 (SNS_CH2 ↔ Net-(M9-S), U12.4), NT3 (SNS_CH3 ↔ Net-(M8-S), U6.4).
- **Gate drive:** D12 deleted; R15 = 10 Ω; R13/R23/R47 = 220 Ω.
- **M1 inhibit:** Net-(D1--) renamed M1_INHIBIT. J9 → 1 × 11 right-angle, pin 11 = ARD_M1_INHIBIT. New D27 (SOD-123, anode ARD_M1_INHIBIT, cathode M1_INHIBIT) and R105 100 kΩ to GND.
- **J10/J11:** Conn_02x15.
  - J10 = `PinSocket_2x15_P2.54mm_Vertical`, MPN ESQ-115-44-G-D.
  - J11 = `PinHeader_2x15_P2.54mm_Vertical`, MPN TSW-115-07-G-D.
  - Pinout: 1 GND, 2 GND, 3 M1_ON, 4 M2_ON, 5 ena_out_1, 6 out_2_on, 7 ena_out_2, 8 out_3_on, 9 ena_out_3, 10 5V, 11 GND, 12 GND, 13 Vout_1, 14 Output1_drain, 15 Vout_2, 16 Output2_drain, 17 Vout_3, 18 Output3_drain, 19 12V, 20 GND, 21 GND, 22 analog_5V, 23 Current, 24 GND, 25 GND, 26 IREF1_input, 27 IREF2_input, 28 GND, 29 GND, 30 IREF3_input.
  - Mating checked: socket pin 2 at −2.54 mm on F.Cu; the header flipped to the card's B.Cu also lands pin 2 at −2.54 mm seen from the top, so pin n meets pin n.
- **Mounting holes:** H1–H4 (card), H5–H8 (power-board standoffs), `MountingHole_3.2mm_M3`.
- **FETs:** M1–M10 footprint → `TO-220-3_Horizontal_TabUp`. New library footprint `BOOST:TO-220-3_Horizontal_TabUp_NoHole` for unscrewed FETs, not yet assigned.
- **Output caps:** C70/C86/C88/C71/C78/C87/C74/C75/C77 → `BOOST:CP_Elec_10x16.5`, MPN EEH-ZU1H221P.
- **Input caps:** C40/C69/C85 MPN EEH-ZU1E681UP.
- **U21520DW:** VSSA pin type → passive.

Project library files: `BOOST-github/BOOST/fp-lib-table` (BOOST, CSCF3218-6R8MC); `BOOST.pretty/`; `CSCF3218-6R8MC.pretty/`.

Records in `BOOST_split_boards/replace_2026-09-14/`:
- `board_assignment_2026-09-14.json` (POWER 121 parts, CONTROL 166)
- `netlist_diff_vs_BOOST_9-2_1013.txt`
- `schematic_edit_log.txt`, `schematic_netcheck.txt`
- `deadtime_check_2026-09-14.txt`

All applied on 2026-09-15 (§11): C30 → TR3D476K025C0250, C7/C55 → GRM32ER71E226KE15L, C41/C44/C45 restored at
the sink op-amp inputs, NoHole footprint on M2–M7. Netlist `BOOST_9-15_nohole.net`, ERC 0/0, netcheck 0 failures,
schematic SHA-256 `a1c93a19…`. The control card has not been re-synced yet (step 7).

## 5. Simulation (SIMULATION_REPORT §8 item 1, done)

Conditions: R15 = 10 Ω, no D12, 35–39 ms window. LTspice 24.0.12. Handoff netlists re-encoded to cp1252 (UTF-8 "µ" breaks LTspice 24).

| Run | R13/R23/R47 | Rail FET Vth | Dead-time margin min / median | M1 die peak | TVS avg | M1 loss |
|---|---|---|---|---|---|---|
| s150 | 150 Ω | nominal | 24.6 / 28.8 ns | 68.0 V | 38.2 mW | 4.83 W |
| s150lv | 150 Ω | 1.0 V | −0.4 / 2.6 ns (fail) | 66.0 V | 14.2 mW | 5.00 W |
| s220 | 220 Ω | nominal | 40.8 / 46.3 ns | 68.0 V | 38.3 mW | 4.85 W |
| s220lv | 220 Ω | 1.0 V | 18.3 / 24.4 ns | 66.0 V | 13.1 mW | 4.98 W |

All runs: no avalanche; LED currents 2.631 / 2.368 / 2.368 A; reverse current into rail drains ≤ 1.34 A; IL peak ≈ 37.3 A.
Input-cap check: bank ripple 10.36 A RMS at 14 V (8.61 A at 17 V). 3 × EEH-ZU1E681UP ≈ 13.4 A usable after frequency derating.

## 6. Part facts checked against datasheets or distributor listings

- **Samtec TSW (F-219):** lead style −07 = tail 2.54 / overall 10.92 / post 5.84 mm; recommended hole 1.02 ± 0.03 mm. KiCad's 1.0 mm drill is at the low end; consider 1.05 mm.
- **Samtec ESQ (F-218):** −44 = tail 4.57 / body 18.67 mm; insertion depth 3.68–6.35 mm; 5.7 A per pin with TSW. Mated gap = ESQ body + 2.54 = 21.21 mm.
- **TI LM2940** (SNVS769J): output capacitor ≥ 22 µF with ESR 100 mΩ–1 Ω across the operating temperature range; input 0.47 µF.
- **ST L78L** (Rev 19): characterized with 0.33 µF in and 0.1 µF out; no ESR or stability requirement found in the text.
- **C30 candidates:**
  - KEMET T491C226K025AT (LCSC C116749) and AVX TAJC226K025RNJ (LCSC C7214) list ESR 1.4 Ω, above the LM2940 limit: rejected.
  - Proposed: AVX TPSC226K025R0275 (22 µF 25 V, case C 6032, 0.275 Ω). LCSC stock not yet confirmed.
- **C7/C55 candidate:** Murata GRM32ER71E226KE15L (22 µF 25 V X7R 1210, JLCPCB C21397, Extended part, listed in stock). Chosen over Samsung CL31A226KOHNNNE (X5R, 85 °C max) because the case runs warm.
- **HYG180N10 TO-220:** overall thickness A 4.57 mm, tab A1 1.30 mm, hole 3.6 mm. The board underside to the tab at the hole is 3.27 mm, so each screwed FET needs a ~3.3 mm insulating spacer between board and tab, plus an insulating shoulder bushing (the tab is the drain). To confirm with the user.
- **Codaca CSCF3218 (L1):** 32 × 22.5 × 19 mm; both pads on one edge, 12 mm apart (LX and rsense_lo).

Links:
- [TI LM2940](https://www.ti.com/lit/ds/symlink/lm2940-n.pdf)
- [ST L78L](https://www.st.com/resource/en/datasheet/l78l.pdf)
- [Samtec ESQ](https://www.samtec.com/products/esq)
- [Samtec TSW](https://www.samtec.com/products/tsw-115-07-g-d)
- [TPSC226K025R0275](https://octopart.com/part/kyocera-avx/TPSC226K025R0275)
- [TAJC226K025RNJ (Farnell, 1.4 Ω)](https://uk.farnell.com/avx/tajc226k025rnj/cap-22-f-25v-10-2312-smd/dp/1135060)
- [GRM32ER71E226KE15L (JLCPCB)](https://jlcpcb.com/partdetail/MurataElectronics-GRM32ER71E226KE15L/C21397)

## 7. Stack budget at the 21.21 mm gap

Superseded 2026-09-16 by §11c (board underside 5.50, card gap 21.50).

| Item | Top of item above case floor (mm) |
|---|---|
| Thermal pad 1.0 + TO-220 4.57 | 5.57 (power board underside) |
| Power PCB 1.6 | 7.17 |
| Gap 21.21 | 28.38 (card underside) |
| Card PCB 1.6 | 29.98 |
| Tallest card part (SOIC 1.75) | 31.73; lid at 33 |

- Output cans (16.8 mm maximum) top out at 23.97 mm, leaving 4.4 mm under the card (Panasonic needs 2 mm above the vent).
- L1 tops out at 26.17 mm; it stays out from under the card by decision.
- ESQ −44 tails stick out 2.97 mm below the power board, 2.6 mm above the floor.
- J9 right-angle mounts on the card underside at the card edge.

## 8. Power-board placement: what was learned

- **Density:** parts that can only go on the top side take 4,086 of 6,148 mm² (66 %). Eight screw points, each needing an 11 mm circle free of tall parts, bring that to 79 %, before ~72 small parts.
- **L1 geometry:** L1's two pads are 12 mm apart on one edge, so no input cap can be within 10 mm of both R1 (at rsense_lo) and M1 (at LX).
- **J10:** a 39.2 mm through-hole part. It needs a strip with no FET body underneath, and must sit inside the card (hence 45 mm).
- **No room for the bulk caps:** in the best layout a scan found no free top-side spot for C30/C55 (6.3 mm cans), hence the smaller-capacitor decision.
- **Screws under the card** (e.g. M9, M10 tabs) are reachable if the power board is screwed down before the card is fitted.
- **Placement model:** each switch pair shares its source pins 2.54 mm apart (LX FET on B.Cu rot 180 at the origin, rail FET rot 0 at −12.7 mm, bodies on opposite sides of one pin row). Each sink FET has its shunt pad 1 about 3 mm from the source pin. LED pads come in pairs 6.5 mm apart.
- **Best layout so far:** `p6l_1` (card 42 mm at (35.8, 67.6), LED pads on the bottom edge, lugs on the right edge). It meets 33 of 43 agreed goals and 26 of 43 of the brief's original targets. Remaining conflicts:
  - M7's pins under L1;
  - standoff H5 on sink M9 and its shunt R53;
  - M1's and M8's screwdriver paths blocked (L1, C74/C75/C77);
  - M3 25.5 mm from a screw;
  - J10 over FET bodies;
  - C30/C55 unplaced.
- **Latest runs:** five J10-position candidates with a 45 mm card and J10 fixed (L left, R right, C centre vertical; T top, B bottom horizontal). Configs `p7L/R/C/T/B_cfg.json` all pass the fit check.
  - Only L ran: `p7L.json`, final cost 1366.5, not reviewed.
  - R, C, T and B crashed at start: the launch command passed seeds "80R", "80C" and so on instead of numbers. Rerun them with numeric seeds, for example `python psa4.py p7R_cfg.json p7R 802`.

## 9. Tooling and gotchas

- **KiCad 10.0.6 Python:** `C:/Program Files/KiCad/10.0/bin/python.exe` (no matplotlib; use Anaconda Python for plots).
  - `BOARD.Remove` breaks later SWIG proxies, so strip items in the file text before loading.
  - `FootprintLibCreate` fails; use `PCB_IO_KICAD_SEXPR`.
  - A B.Cu footprint is `Flip(LEFT_RIGHT)` then `SetOrientationDegrees`; its local point maps as (x, −y) then rotated.
- **Rules lost on save:** `pcbnew.SaveBoard` rewrites the `.kicad_pro` without the shipped board's netclasses, netclass patterns and rules. Copy the shipped `BOOST_power.kicad_pro` / `BOOST_control.kicad_pro` next to any new board after saving, then add the new netclass members. Shipped power rules: min clearance 0.13, copper-edge 0.3, min track 0.13, via 0.45, text 1.0 / 0.15; netclasses Default, Power, Gate, Rail.
- **LTspice** 24.0.12 at `AppData/Local/Programs/ADI/LTspice/LTspice.exe`; a 40 ms run takes about 25–35 min.
- **Bash tool:** inline heredocs mangle `\\`; put regex-heavy code in files. Long inline command chains can fail to parse.
- **PDF datasheets:** no poppler/pypdf installed; a zlib-based text extractor (`pdftext.py`) worked on TI/National/ST PDFs.
- **Rate limits:** Samtec and some mirrors rate-limit or block; Octopart-hosted PDFs usually load.

## 10. Files

The scripts, configs and key results were copied into the project at
`BOOST_split_boards/replace_2026-09-14/tools/`, with the same file names. See `tools/README.md`:
- `placement/`; its unplaced synced boards are in `placement/wip_NOT_FOR_FAB/`;
- `schematic/`;
- `sim/` (LTspice `.raw` files not copied);
- `replace_notes.md` and `pdftext.py` at the top level.

They came from this session's temporary scratchpad (listed below for reference):
`C:\Users\Dominick Junior\AppData\Local\Temp\claude\C--Users-Dominick-Junior-Downloads-UCSD-Stuff-2025-2026-robotx-boat-code-stuff-rx26-asv\f9992ea6-ae1d-40d1-8331-d525af1a19f1\scratchpad\`

- `replace_notes.md`: running verified-facts log.
- `pdftext.py`: PDF text extractor.
- `sch/`:
  - `netcheck.py` (checks every §4 change on an exported netlist);
  - `netdiff.py`;
  - `setfp.py` (sets Footprint fields by reference, verified);
  - `schedit.py`, `schlib.py`.
- `sim_dt/`: `s150`, `s150lv`, `s220`, `s220lv` netlists and raw files; `deadtime2.py`.
- `place/`:
  - `syncboard.py` (builds a split board from the netlist; `--check` for parity);
  - `fpinventory.py`;
  - `power_sync2.kicad_pcb` and `control_sync2.kicad_pcb` (parity 0, unplaced);
  - `inv_power2.json`;
  - `pmodel.py` (geometry model), `pcheck.py` (targets and mechanical checks), `pplot.py`, `sa_view.py`;
  - `psa4.py` (simulated-annealing placer with rigid groups, goals, movable card, `only_move`);
  - `mk6.py`, `mk7.py` (configs);
  - `psat.py` + `psat_cfg.json` (small-part placer);
  - `pstand.py`, `pscrews.py` (screw plan and NoHole list);
  - `papply.py` (writes a WIP board: notched outline, keep-outs, "not for fabrication" note; refuses unplaced parts);
  - `ptable.py` (distance table with a goals column), `pdrc.py`;
  - `run_place.sh` (pipeline: small parts → KiCad board with the shipped `.kicad_pro` → plots → table → DRC);
  - results `p6l_1.json/.png/.distances.md` and `p7?.json`;
  - `checkin_notes.md`, `fp-lib-table`.

## 11. Session 2 (2026-09-15 afternoon, account bubba)

Project now at `C:\Users\bubba\OneDrive\Documents\led-driver`. Details and every number: `tools/replace_notes.md`.

- **J10 candidates:** R, C, T, B rerun (seeds 802–805). None of the five legal; all kept L1 over M2/M7 pins and tall caps in sink screw circles; p7L's standoffs were in a line (no support rule).
- **C30:** TPSC226K025R0275 (C313069) had 2 in stock. User chose **Vishay TR3D476K025C0250** (47 µF, case D, ESR ≤ 0.25 Ω, C4979367, 107 in stock). C7/C55 GRM32ER71E226KE15L (C21397, 77,742 in stock). KEMET T491C226K025AT is 1.0 Ω max (not 1.4).
- **C41/C44/C45 (user: "decide"):** restored as 1 nF at the sink op-amp inputs on the power board (the IREF nets now cross the header beside the power stage; nothing filters them there). DNP-able.
- **Schematic:** `capedit.py` + `setfp.py` (NoHole on M2–M7). ERC 0/0, netcheck 0, netdiff shows only the intended changes. Backups in `previous/2026-09-15/`.
- **Shipped `BOOST_power.kicad_pro`:** KiCad (GUI) opened and closed the power project at 14:26 and rewrote the file without the Power/Gate/Rail netclasses. Restored from git with the user's OK; the rewritten copy is in `previous/2026-09-15/`.
- **L1 land pattern** matches Codaca's reference numbers (§13 item 4 of the context doc); its large courtyard is real.
- **Placement:** ~250 annealing runs (psa5: exact local costing, card and J10 free, standoffs spread across the card). Under the agreed rules no layout was both legal and close on the hard goals. Legal layouts appear once tall parts may come within **4.0 mm** of a tab-screw centre (was 5.5 mm, an interpretation of "clear screwdriver path") with standoffs anywhere in their card quadrant; screw distance stays 25 mm. Chosen: `p15_b10_k1`.
- **WIP board** `tools/placement/BOOST_power_p15_WIP_NOT_FOR_FAB.kicad_pcb` (+ shipped `.kicad_pro`): 124 parts placed, mechanical checks clean, DRC 0 errors (39 silk warnings, 270 unconnected), brief targets 31/49, agreed goals 38/49. Distances verified against KiCad's saved pads (0.0000 mm).
- **The check-in itself** (decisions, plots, distance table, DRC): `BOOST_split_boards/placement_review_2026-09-15/BOOST_power_placement_review.html`, also at <https://claude.ai/artifact/RizZaqBSKCshiew2Vd4GhR>.

## 11a. User review of the check-in (2026-09-15 evening)

Accepted: `p15_b10_k1` as the base for copper; standoffs anywhere in their card quadrant; no global re-place.
The cap-to-rail assignment is confirmed optimal (the user checked all 1,680 permutations). Changes made:

- **Gate loops.** New stage 6 in `pcheck.py`: series gate resistor, pulldown and turn-off diode within 5 mm of
  the gate pin. `psat.py` gained `place_first` (ordered) and `either_side`; the order that won interleaves per
  channel — rail ceramic (100 nF), LX FET's gate parts, rail FET's gate parts, 4.7 µF bulk. R60 21.1 → 5.2 mm,
  R70 22.8 → 4.2 mm, R76 16.4 → 9.8 mm. Still over 5 mm: R75 5.3, R23 5.3, R60 5.2, D13 9.7 (M4, slowest edge).
- **Standoffs are board-to-case fixings** (male-female nylon standoff into a tapped boss, ~5.6 mm insulating
  spacer under the board). The rules already counted them as screws, so the 25 mm result is unchanged (worst
  22.6 mm). H8 moved to (85.1, 109.5), the farthest legal point toward the bottom-right corner: 29.7 → 20.0 mm.
  No fifth fixing fits at the top-left (L1 covers it); M3's body under L1 carries that corner.
- **Commutation loop** reported per channel (new stage 7): 38.0 / 89.4 / 90.6 mm, with M1 drain → LX drain
  10.9 / 33.1 / 41.9 mm and the loop ceramic 3.2 / 5.3 / 4.4 mm from its rail FET drain. Routing rules and the
  post-routing inductance check are in `tools/replace_notes.md`.
- **M2→C70 (20.1 mm) and M3→C87 (18.8 mm) cannot be improved**: an exhaustive scan found no legal position
  closer than 20.0 / 18.6 mm with the rest of the board fixed (C70 is boxed by M5's pins and H6, C87 by C71/C78).
- **Tab-screw hardware:** Aavid/Boyd 7721-7PPSG shoulder washer (shoulder 3.43, flange 5.46, bore 2.95 → #4-40
  or M2.5 screw) and the gap spacer both sit under the board, so the top-side radius is set by the screw head
  (2.5–3.0 mm). 5.5 mm remains unsolvable (p16b and ~180 global runs).
- **Battery cable:** runs over U16 from the notch to the lugs (21 mm headroom). Open: J1/J2 are 9.2 mm apart and
  10 AWG ring terminals are 10–12 mm across.

Board state: brief targets 50/72, agreed goals 57/72, mechanical checks 0, DRC 0 errors (45 silk warnings,
270 unconnected).

## 11b. Third review round (2026-09-15 late)

Applied: loop ceramic redefined as the 4.7 uF (both rail ceramics targeted at 6 mm); tab-screw board hole
3.5 -> 2.9 mm via `BOOST:TO-220-3_Horizontal_TabUp_M2.5` on M1/M8/M9/M10; D19 -> 5.0SMDJ54A (D_SMC land checked
against the Bourns drawing and kept); U26 -> MCP4451-103E/ST (10 k, the 5 k is out of stock). Standoffs are
board-to-case fixings: nylon M/F 6 mm below the board, 22 mm above it, M3 screw at the card.
Delivered: case-floor drilling drawing, `BOOST_split_boards/case_drilling_2026-09-15/`.
Open for the user: whether U16 moves to the bottom side, which is what a 12 mm lug pitch needs (0.74 mm to the
floor); otherwise the lugs stay at 9.2 mm. Strain relief should go on the case, not the board.
Full detail and every number: `tools/replace_notes.md`.

## 11c. Fourth review round (2026-09-16)

Applied: J1/J2 pads 8.6 -> 7.0 mm at the 9.2 mm pitch (`BOOST:MountingHole_4.3mm_M4_Pad7.0_TopBottom`, 2.21 mm
copper gap; ERC 0/0, netlist rev3, DRC 0 errors). Drilling drawing rev B: same eight positions, corrected tap
depths (M3 7.0 / M2.5 6.0 mm full thread in the 10 mm floor) and fixed clipping.
Approved by the user 2026-09-16: THERM-A-GAP G579 0.050 in pads (published curve and 5-40 % range; Gap Pad 1500
publishes neither) at 26.8 % nominal; board underside 5.50 on an Essentra HTSN-M3-5-3 nylon M/M stud plus one
TR NWE-34815-M3 0.5 mm washer; Essentra HNSM3-20-5.5-1 nylon F/F above plus three washers (card gap 21.50);
all hand-tight. §7 is superseded: card-top parts now top out at 31.95 mm, 1.05 mm under the lid.
M1 dissipates about 6 W when warm (the LTspice model has no temperature dependence), about 21-22 K across the
pad; the user's budget puts M1 at about 78 C at 25 C water and 118-125 C with every conservative assumption.
Full detail and every number: `tools/replace_notes.md`.

## 11d. Step 5: power copper (2026-09-16)

Copper v9 drawn on p15_b10_k2 and solved at 1 oz and 2 oz outer: `BOOST_split_boards/route_2026-09-16/`, check-in
page `BOOST_split_boards/copper_review_2026-09-16/`. DRC 0 errors, no exclusions, no rule weakened (tightening
`.kicad_dru` and a Sense netclass in the WIP project copy only). At 1 oz four branches have necks over 20 C (LX at
M5/M1/M6 pins 58/52/36 C, Vin 24 C) and four have vias over rating, so the rule gives C. At 2 oz three 1-2 mm
FET-pin throats (22-27 C), one 10 mm Vin neck (23.7 C) and 11 vias (up to 1.39x, at R1 and L1.2) remain.
Copper-only loop inductance ch1/ch2/ch3 about 0.7/1.2/1.7 nH against the 4.85/12.74/7.91 nH simulated.
**User decisions (2026-09-16):** copper weight B (1 oz / 1 oz), stackup written into the board; IPC-2221 figures
stay in reports but are not pass/fail for necks under ~5 mm or vias in plane-connected fields; FET-pin throats and
R1/L1.2 via crowding accepted; U19 stays; In4 stays one 5 V plane; solid pad connections kept, soldering and
hardware instructions in `BOOST_split_boards/BUILD_NOTES.md`; the M1 turn-off re-sim is confirmation only (LX
copper about 600 pF to GND if it is run). Full numbers: `tools/replace_notes.md`.

## 11e. Step 6: signal routing (2026-09-16), handed back

Every signal routed on the v11 power copper: `route_2026-09-16/BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb`,
report `route_2026-09-16/ROUTING_REPORT_2026-09-16.md`. The saved file passes DRC (0 errors, 0 unconnected,
0 exclusions, only the 43 placement silk warnings), the layer-plan, plane, island and rev3 parity checks, and has
the stackup. The first routed board (v12) was rejected: it cut the power pours (Vout_1 LED path neck 177 C).
v13 was routed with the solved sheet-current map and fixes that, but the routes to U19/U25 still narrow the R1
rsense_lo and Vin necks (59 / 38.5 C at IPC, necks 2.5 / 3.6 mm long), a 0.93 mm throat appears in the Vout_3 LED
path at U6, gate returns are not routed beside the gate tracks, and some Rail/Gate tracks use the fallback width.
These are the report's section-6 decisions for the user.

## 11f. Step 6 second pass: driver bypass, gate links, gate loops (2026-09-17), handed back

The user decided section 6 on 2026-09-17 (6.1, 6.2, 6.4 accept; 6.3 pair-route the gate loops M7, M5, M6 then
M2-M4; 6.5 no action) and asked for two fixes first: the driver bypass capacitors at the driver pins (placement
only) and direct gate-resistor -> gate links. Result:
`route_2026-09-16/BOOST_power_route_v15_NOT_FOR_FAB.kicad_pcb`, report
`route_2026-09-16/ROUTING_REPORT_2026-09-17.md`.

- Ten capacitors moved (C31, C48, C51, C18, C50, C16, C90, C61, C60, C89) and three Vout_1 vias shifted 0.6 mm;
  no other footprint moved, schematic unchanged. C31 is 2.8 / 2.5 mm from U19 pins 16 / 14.
- Everything routed again from v11's copper (the moves change the space round all four drivers).
- Saved file: DRC 0 errors / 0 unconnected / 0 exclusions, parity 0, layer, plane and island checks pass, and
  every router item is on the board with its routed net (new `tools/net_flips.py`).
- Series R -> gate links are all <= 5.1 mm; M7's went 14.5 -> 5.1 mm. M7 and M5 returns run beside their drive
  paths (73 %, 82 %); M6 34 %, M2-M4 <= 18 %.
- Solve vs the unrouted base: rsense_lo 20.1 -> 27.4 C (v13 was 59 C), Vout_3 LED throat fixed (13.7 -> 4.6 C),
  but LX L1->M5 57.8 -> 84.0 C because the D13 -> M4 gate link crosses the In2 LX pour.
- Open decisions in the new report's section 8: the D13 link (recommend routing it with the current map), C51's
  pair link to U15 pins 11/9 (not routable, tied to pins 16/14), the unpaired gate loops, C48's missing 5 V via.

## 11g. Step 6 frozen at v16 (2026-09-17)

The user accepted v15 in principle and asked for one final pass: `route_2026-09-16/ROUTING_FINAL_2026-09-17.md`,
board `BOOST_power_route_v16_NOT_FOR_FAB.kicad_pcb` (SHA-256 7aaf6f5752ca794b81ea...). Placement identical to v15.
- D13 -> M4 gate link routed with the current map (31.0 mm, no hot crossing): LX L1->M5 back to 57.3 C / 2.017 mOhm
  (v15 84.0 C / 2.271), ch3 commutation loop 2.08 -> 2.04 nH.
- Gate loops hand-routed through chosen corridors (GATE_GUIDES in route_signals.py): M2 147 -> 36 mm2,
  M3 187 -> 38 mm2, M6 47.7 unchanged, M7 49.1, M5 24.2, M4 59.7 - all <= the user's 60 mm2 target.
- New: the U15 VDDA pin-row link cuts the F.Cu LX pour for 4.1 mm at 1.28 A/mm (LX L1->M1 +0.028 mOhm, via
  0.83 -> 0.90x); flagged in the report as the one new crossing.
- Checks on the saved file: DRC 0/0/0, parity 0, layer/plane/island checks pass, net_flips 0.
- Placement mechanical checks re-run after the ten moves: washer keep-outs, screwdriver paths, 25 mm rule, card and
  corner zones all pass (C89 courtyard 4.03 mm from H8 against the 3.75 mm keep-out). Eleven pairs of courtyards
  now touch (0.011-0.089 mm) without overlapping; KiCad's courtyard check is clean.
- The user's decisions 8.2(a) (C51 stays tied to U15 pins 16/14) and 8.4 (C48.1's 5 V via at U19.8) are accepted
  as documented. The power board is frozen; the file keeps NOT_FOR_FAB until there is a fab package.

## 11h. Step 7 control card: J9 wire pads and placement (2026-09-17/18), awaiting the user

Folder `card_2026-09-17/`.
- **Check-in 1** (`CARD_CHECKIN_1_2026-09-17.md`), both decisions made by the user:
  - J9 became soldered wire pads. Schematic rev4 (J9 footprint only); ERC 0; netdiff shows only J9; parity 0 for
    the card and for v16.
  - Card screw: Würth 97790803211, lid margin 0.70 mm nominal.
- **Check-in 2** (`CARD_CHECKIN_2_2026-09-18.md`): placement c2, `work/BOOST_control_place_c2_NOT_FOR_FAB.kicad_pcb`.
  - v16 overlay 13/13; DRC 0 errors (27 silk warnings, 380 unconnected).
  - 68 SMD parts on top, 92 underneath: double-sided, forced by area.
  - Current stubs 2.8 / 3.0 mm; every route-proxy separation to I2C, M1_ON and the 74HC14 outputs is ≥ 10.2 mm.
  - D27 is 2.5 mm from U104.1.
  - The 1206 caps are underside only.
  - Open with the user: approve the placement, double-sided assembly, 1206 MPNs, whether Vref_n_arduino is PWM,
    the U2 In+ spread (11.2 mm), and the routing plan (layers, J11 solid GND pads, via drill ≥ 0.3 mm, stackup).
- Tools: `tools/card_place.py`, `apply_layout.py`, `card_overlay.py`, `drc_place.py`, `card_check.py`,
  `layout_metrics.py`, and `check_card.sh` (runs the full check).

## 12. Next steps

Steps 1-5 of the first list are done (§11). The rounds in §11a-§11c settled the 4.0 mm tab-screw clearance,
the lugs, D19, the MCP4451 variant, the tab-screw and standoff hardware, the thermal pad and the drilling drawing.
Now:

1. ✔ **Handoff step 6 is done and frozen at v16 (§11g).** Open only if the user wants the one new LX-pour
   crossing (U15 VDDA link) re-routed or the touching courtyards nudged apart.
2. **Step 7 (control card):** placed (c2, §11h). The placement check-in is with the user; route only after they
   approve it.
3. **Open with the user:** LTspice `BOOST.asc` updates; who runs the remaining sims.
