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
| 3 Schematic | Done and verified; three capacitor changes and the unscrewed-FET footprints still to apply |
| §8 item 1 simulation | Done (220 Ω chosen) |
| 4 Power-board placement | In progress: several placement passes, best so far meets 33 of 43 agreed goals; one of five J10-position runs finished (not reviewed), four failed to start |
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

Still to apply:
- C30, C7, C55 part swaps (§6).
- NoHole footprint on the unscrewed FETs once the screw set is final.
- Then re-export the netlist, ERC, netcheck, and re-sync both boards.

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

## 11. Next steps

1. **Pick the J10 position.** Rerun candidates R, C, T, B (numeric seeds), then review all five with `sa_view.py` and `ptable.py --goals`; pick the best and clear its remaining conflicts: M7 pins vs L1, standoffs vs sinks, M1/M8 screwdriver paths, M3 at 25 mm.
2. **Capacitor parts.** Confirm LCSC stock for TPSC226K025R0275 (or another low-ESR tantalum inside 0.1–1 Ω). Then set C30 (tantalum, 6032 case-C footprint) and C7/C55 (GRM32ER71E226KE15L, 1210) in the schematic.
3. **Footprints.** Run `pscrews.py` on the chosen layout; assign `BOOST:TO-220-3_Horizontal_TabUp_NoHole` to the unscrewed FETs (`setfp.py`).
4. **Rebuild the netlist and boards.** Re-export the netlist, ERC, netcheck, re-sync the boards (`syncboard.py`), refresh `inv_power2.json`.
5. **Build the WIP board.** Run `run_place.sh`; review the KiCad plots, distance table and DRC. ★ Placement check-in with the user.
6. **Continue with handoff steps 5–7:** power copper solve at 1 oz / 2 oz, copper-weight decision, routing and checks, report, then the control card at 45 mm.
7. **Open with the user:** C41/C44/C45 removal; screw spacer and bushing hardware; LTspice `BOOST.asc` updates (not modified); who runs the remaining sims.
