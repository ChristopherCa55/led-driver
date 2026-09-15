# BOOST power board: response to the copper audit

2026-09-14. This responds to `BOOST_AUDIT.md`, which audited the 2026-09-10 files
(SHA-256 5272…07CE power, 61D7…D627 control). Those files are kept in
`previous/2026-09-10/`.

**Board to fabricate:** `BOOST_power.kicad_pcb` (SHA-256 f4807690c5d406ee…). `BOOST_control.kicad_pcb` is
unchanged (61d718272d55d627…). The previous revision of the power board, if needed, is in
`previous/2026-09-10/`. `wip/` holds an unfinished experiment that is **not for fabrication**.

**Where things stand:**
- **Fixed and verified:**
  - 7 of the 8 whole-current single vias the audit named (the solver found 13 in all; 12 are now relieved);
  - LX→5V plane coupling (232 → 20 pF);
  - the M10 shunt's single return via;
  - J4's silkscreen and the project silk rule.
- **Improved, not resolved:** neck temperatures (item 5) and via loading (item 7) on most power branches.
- **Not fixed, needs a design decision (§8):**
  - **the LED sink channels still carry 2.63 A on 0.15 mm tracks and will fuse at full LED current (stop-ship S1)**;
  - the remaining Vout_1 single via;
  - R1 Kelvin sensing;
  - the commutation loop;
  - copper weight;
  - J10/J11;
  - TO-220 mounting;
  - the mechanical stack;
  - the J10/J11 annular ring.

The routing is DRC-clean and electrically unchanged. It is **not** ready for full-power
operation until S1 is resolved.

---

## 1. Final checks (from the saved files)

| Check | Power board | Control board |
|---|---|---|
| DRC, all severities, zones refilled, from the saved file | **0 errors**; 1 warning: `lib_footprint_issues`, L1's footprint library missing from the library table (configuration only, also present on the audited board) | **0** |
| Unconnected items | **0** | **0** |
| DRC exclusions / `.kicad_dru` | 0 / none | 0 / none |
| Silk rule in `.kicad_pro` | 1.0 mm / 0.15 mm (was 0.8 / 0.08) | 1.0 mm / 0.15 mm (was 0.8 / 0.08) |
| Unrouted connections / dangling track ends (own geometry audit) | 0 / 0 | file unchanged since the audit |
| Untied copper islands (own check, zones refilled) | 0 | file unchanged since the audit |
| Non-GND copper on the GND planes (In1, In6) | 0 tracks, 0 zones | — |
| Footprints / pad nets / nets compared with the audited file | identical (121 / 358 / 76) | identical file |

The shipped power file was refilled, saved, reloaded from disk, refilled and saved
again. Both `DRC_*.rpt` files were then regenerated from the saved files in this
folder, and the DRC runs left the boards byte-identical. The solver table was
re-run on the shipped file and matches the verified candidate in all 36 blocks.

Method: I used the same approach as the audit, re-implemented independently.
KiCad 10 Python loads the saved board and refills every zone. It exports each
net's copper per layer: zone fill, tracks, via pads and pads. Plated barrels
(20 µm) join the layers. A conductance mesh is solved on a 0.1 mm grid (0.2 mm
for GND, 0.05 mm for the sink-source nets), with the terminal pads held as
equipotentials. On the audited board my numbers match the audit's within 1–3 %
on most branches (LX within 13 %). Every "before" figure below comes from my
solver on the audited file, so before and after use the same method.

No design rule was weakened, no DRC exclusion was added, and no `.kicad_dru`
exists. The one rule change is a tightening: silk text minimum 0.8/0.08 mm →
1.0/0.15 mm (JLCPCB) in both `.kicad_pro` files.

## 2. What changed

Power board only. The control board's copper is untouched; only its project
silk rule was tightened. No footprint, net, net name, schematic connection or
component position changed.

A board diff against the audited file (`boarddiff.py`) confirms:
- **Unchanged:** all 121 footprints (position, rotation, side, footprint and
  value), all 358 pad-to-net assignments, the 76-net list, and every one of the
  6044 track segments.
- **Changed:** 64 vias added and none removed; 13 zone patches added; 2 LX
  pours removed; one reference designator resized.

### Removed: LX pours on In3 and In5 (item 9)
The two LX zones (priorities 57 and 56) sat directly above and below the In4 5V
plane. Measured LX→5V overlap went from 1085 mm² (232 pF) to 95 mm² (20 pF).
The remainder is LX track on In5. Those pours carried a little of the LX
current, so this costs some LX resistance: LX L1→M1 1.247 → 1.261 mΩ (+1 %), L1→M6 5.126 → 5.143 mΩ (+0.3 %), and L1→M5 7.74 → 8.67 mΩ (+12 %). In the M5 branch, the Ø0.25 via at (84.4, 84.6) in the In4 corridor goes from 3.40 A (4.8×) to 5.14 A (7.3×), the one at (90.1, 84.2) from 1.22 A (1.7×) to 3.50 A (4.9×), and the neck rise from 468 to 951 °C. It fuses either way. No via site exists there (§7). This regression was accepted to remove 212 pF of switch-node coupling into the logic supply. Restoring the pours only partly gave back negligible resistance (§7). The extra LX via at (44.9, 67.8) roughly halves the current in the via at (44.7, 67.3), which feeds all three branches.

### Added: via landings
Each landing is a set of through vias placed where the solved field showed one
via carrying a whole branch, or a barrel far over its rating. Some also get a
priority-95 copper patch of the same net on the layers the current changes
between. Via sizes are the board's existing via types.

| Net | Around | Vias added (pad/drill mm) | Patch layers | Replaces / relieves |
|---|---|---|---|---|
| Vout_1 | (37.3, 76.3) | 8 × 0.80/0.40 | In2, In3 | sole Ø0.25 via at (38.2, 75.6) |
| Vout_2 | (76.9, 95.2) | 4 × 0.80/0.40 | In3, In5 | sole via at (76.0, 96.3) |
| Vout_2 | (65.7, 100.6) | 3 × 0.45/0.25 | In2, In5 | sole via at (65.3, 101.5) |
| Vout_2 | (63.9, 109.7) | 11 × 0.45/0.25 | F.Cu, In2 | sole via at (63.1, 108.4) |
| Vout_3 | (87.8, 103.3) | 6 × 0.80/0.40 | In2, In4 | vias at (88.6, 102.3) / (88.7, 103.5), 6.8× |
| Output1_drain | (58.1, 84.6) | 3 × 0.80/0.40 | In4, B.Cu | sole via at (60.4, 84.6) |
| Output1_drain | (100.1, 75.3) | 3 × 0.80/0.40 | F.Cu, B.Cu | sole via at (100.1, 74.9) |
| Output1_drain | (70.9, 87.9) | 2 × 0.80/0.40 | In4, In5 | sole via at (70.1, 87.4) |
| Output1_drain | (68.7, 79.7) | 2 × 0.60/0.30 | In5, B.Cu | sole via at (68.9, 80.3) |
| Output2_drain | (67.6, 92.4) | 4 × 0.60/0.30 | In5, B.Cu | sole via at (65.2, 92.4) |
| Output2_drain | (95.2, 79.5) | 2 × 0.80/0.40 | In5, B.Cu | sole via at (95.3, 79.5) |
| Output2_drain | (100.9, 74.1) | 2 × 0.45/0.25 | In2, In5 | sole via at (99.7, 72.6) |
| Output3_drain | (53.8, 100.4) | 3 × 0.80/0.40 | In4, In5 | sole via at (55.6, 100.9) |
| Vin | (51.2, 48.5) | 4 × 0.80/0.40 | — | via field feeding R1.2 (1.34 A in one barrel) |
| GND | (96.9, 57.1), at R52.2 | 4 × 0.60/0.30 | — | M10 shunt return: sole Ø0.25 via at (96.9, 58.3) |
| GND | (75.1, 68.7) and (78.8, 65.5), at R53.2 | 2 × 0.45/0.25 | — | M9 shunt return: sole Ø0.25 via at (74.3, 68.8) |
| LX | (44.9, 67.8) | 1 × 0.60/0.30 | — | 6.6 A in the Ø0.25 via at (44.7, 67.3) |

Four patches (Output1 ×2, Output3 and Vout_3; 113 mm² of outline in total) sit
on In4. They cut locally into the 5V plane there. The 5V net stays fully
connected (DRC: 0 unconnected).

### Silkscreen (item 13)
J4's designator went from 0.80/0.12 mm to 1.00/0.15 mm and moved to
(102.80, 75.08), clear of pads, other silk and the board edge. Both projects'
`min_text_height`/`min_text_thickness` rules are now 1.0/0.15 mm, so DRC
enforces the fab limit. All designators pass it.

## 3. Audit items

**Status key:**
- **Fixed:** verified on the final board.
- **Improved:** measurably better, not yet within the audit's threshold.
- **Not changed:** needs a design decision (§8).
- **Pass:** the audit passed it, and it still holds.

### Stop-ship findings

| # | Finding | Status | Evidence on the final board |
|---|---|---|---|
| S1 | LED current through 0.15 mm tracks (Net-(M8/M9/M10-S)) | **Not changed** | Still 161 / 321 / 211 mΩ, fusing. Needs shunts moved near their FETs; the M8 corridor is a WIP in `wip/` (§8). |
| S2 | Power connections hanging on a single Ø0.25 via | **Fixed for 7 of the 8 named vias** | The solver finds 13 such vias on the audited board and **1** on the final one: Vout_1 (66.5, 83.6), 7.05 A (10×), with no via site within 6 mm (§5). |
| S3 | Commutation loop overshoot | **Not changed** | Package inductance alone exceeds the budget. Copper in the ch2 rail path fell (Vout_2 17.3 → 9.8 mΩ). |
| S4 | Current sense reads 32 % high | **Not changed** | Needs sense nets or a Kelvin footprint, and U25 moved (§8). |
| S5 | Stack doesn't fit | **Not changed** | Mechanical (§8). |

### Verdicts

| # | Check | Audit | Status | Evidence on the final board |
|---|---|---|---|---|
| 1 | R1 value | PASS | Pass | 2 mΩ unchanged. The old routing report's "12 mΩ" typo is flagged in its new banner. |
| 2 | Copper weight | FAIL | **Not changed** | Fab decision. Every number here is given at 1 oz and at 1 oz / 0.5 oz. |
| 3 | R1 Kelvin sensing | FAIL | **Not changed** | Schematic and footprint change (§8). |
| 4 | Commutation loop | FAIL | **Not changed** | As S3. |
| 5 | Current density / necks | FAIL | **Improved** | Neck rise: Vin 60 → 40 °C; Output1 198 → 90; Output2 198 → 22; Output3 198 → 58; LX L1→M1 >200 → 103; Vout_2 and Vout_3 >200 → 175 / 196. Unchanged: rsense_lo 76, m2_source 97, GND M1 return 88; Vout_1, LX→M6/M5 and the sink nets still fuse. Resistance got worse on LX L1→M5 (+12 %, LX pour removal) and m4_source (+9 %, neck 93 → 86 °C; solved on the intermediate boards: the three Output1 landings add 0.08 mΩ and the Output2 landing at (95.3, 79.5) adds 0.04 mΩ, where their patches take precedence over m4_source copper. That is about 9 mW more loss at 8.35 A, in exchange for removing four whole-current single vias). |
| 6 | Capacitor current sharing | PASS | Pass | Bank copper unchanged; C74 stays the one to watch. |
| 7 | Vias in the current path | FAIL | **Improved** | Worst barrel, audited → final: Vout_2 10.2× → 4.2×; Vout_3 6.8× → 2.2×; Output1 / 2 / 3 3.7× → 1.5× / 1.8× / 1.7×; LX M1 branch 10.2× → 5.8×; Vin 1.3× → 1.1×; R52.2 return 3.7× → 0.7×; R53.2 return 3.7× → 2.0×. Unchanged: Vout_1 10×, rsense_lo 3.8×, GND M1 return 2.7×, R7.2 return 2.3×. Worse, from the LX pour removal: LX (84.4, 84.6) 4.8× → 7.3× and (90.1, 84.2) 1.7× → 4.9×. |
| 8 | Inter-board connector | FAIL | **Not changed** | Pinout and connector choice (§8). |
| 9 | Ground return and measurement | FAIL | **Partly fixed** | LX→5V coupling fixed: 232 → 20 pF. ch1/ch2 shunt returns improved (§6). The sense taps on the sink tracks are unchanged (tied to S1); DC offsets weren't recomputed. |
| 10 | TO-220 mounting | FAIL | **Not changed** | Washer keep-out needs 17 parts moved; mechanical (§8). |
| 11 | PCB ↔ schematic netlist | PASS | Pass | Board diff: 0 pad-net changes, the same 76 nets, 0 footprint changes. |
| 12 | Mechanical fit | FAIL | **Not changed** | Mechanical (§8). |
| 13 | Fabrication | FAIL | **Silk fixed; annular ring not changed** | J4 is 1.00 / 0.15 mm, and the silk rule now matches JLCPCB, with DRC clean under it. The J10/J11 0.175 mm annular ring needs a footprint change, tied to copper weight (§8). |

## 4. High-current branches, before → after

Solved at the audit's RMS currents. ΔT is IPC-2221 at the minimum cross-section
the full current crosses; >200 °C means the neck fuses. Barrel capacity (IPC-2221
at 10 °C): Ø0.40 0.97 A, Ø0.30 0.80 A, Ø0.25 0.71 A.

### 1 oz on all layers (as filed)
| Branch | I (A) | R before → after (mΩ) | Neck ΔT before → after (°C) | Worst barrel before | Worst barrel after |
|---|---|---|---|---|---|
| Vin J1+caps->R1 | 20.70 | 0.371 → **0.360** ▼ | 60 → 40 | 1.32 A in Ø0.40 at (52.10, 48.30), 1.3× | 1.02 A in Ø0.40 at (52.10, 48.30), 1.1× |
| rsense_lo R1->L1 | 20.70 | 0.522 → **0.522** | 76 → 76 | 3.74 A in Ø0.40 at (53.40, 53.00), 3.8× | 3.74 A in Ø0.40 at (53.40, 53.00), 3.8× |
| LX L1->M1 | 15.80 | 1.247 → **1.261** ▲ | >200 → 103 | 7.19 A in Ø0.25 at (44.70, 67.30), 10.2× | 4.13 A in Ø0.25 at (44.70, 67.30), 5.8× |
| LX L1->M6 | 7.69 | 5.126 → **5.143** | >200 → >200 | 3.50 A in Ø0.25 at (44.70, 67.30), 4.9× | 2.01 A in Ø0.25 at (44.70, 67.30), 2.8× |
| LX L1->M5 | 8.35 | 7.740 → **8.674** ▲ | >200 → >200 | 3.80 A in Ø0.25 at (44.70, 67.30), 5.4× | 5.14 A in Ø0.25 at (84.40, 84.60), 7.3× |
| m2_source | 7.05 | 1.644 → **1.644** | 97 → 97 | 1.07 A in Ø0.40 at (44.00, 73.40), 1.1× | 1.07 A in Ø0.40 at (44.00, 73.40), 1.1× |
| m3_source | 7.69 | 1.301 → **1.301** | 86 → 86 | 0.15 A in Ø0.40 at (83.90, 76.30), 0.2× | 0.15 A in Ø0.40 at (83.90, 76.30), 0.2× |
| m4_source | 8.35 | 1.371 → **1.497** ▲ | 93 → 86 | 0.90 A in Ø0.40 at (96.50, 87.00), 0.9× | 0.94 A in Ø0.40 at (96.50, 87.00), 1.0× |
| Vout_1 M2->bank+J3 | 7.05 | 6.084 → **5.596** ▼ | >200 → >200 | 7.05 A in Ø0.25 at (38.20, 75.60), 10.0× | 7.05 A in Ø0.25 at (66.50, 83.60), 10.0× |
| Vout_2 M3->bank | 7.23 | 17.268 → **9.793** ▼ | >200 → 175 | 7.23 A in Ø0.25 at (65.30, 101.50), 10.2× | 2.97 A in Ø0.25 at (60.80, 106.10), 4.2× |
| Vout_3 M4->bank+J5 | 8.35 | 6.144 → **5.643** ▼ | >200 → 196 | 4.79 A in Ø0.25 at (88.60, 102.30), 6.8× | 2.13 A in Ø0.40 at (87.95, 101.80), 2.2× |
| Output1_drain | 2.63 | 37.191 → **27.522** ▼ | 198 → 90 | 2.63 A in Ø0.25 at (100.10, 74.90), 3.7× | 1.09 A in Ø0.25 at (70.10, 87.40), 1.5× |
| Output2_drain | 2.63 | 28.924 → **24.129** ▼ | 198 → 22 | 2.63 A in Ø0.25 at (99.70, 72.60), 3.7× | 1.43 A in Ø0.30 at (65.00, 92.90), 1.8× |
| Output3_drain | 2.63 | 17.248 → **15.995** ▼ | 198 → 58 | 2.63 A in Ø0.25 at (55.60, 100.90), 3.7× | 1.19 A in Ø0.25 at (77.50, 112.70), 1.7× |
| M8-S | 2.63 | 160.590 → **160.590** | >200 → >200 | 2.63 A in Ø0.25 at (73.50, 110.90), 3.7× | 2.63 A in Ø0.25 at (73.50, 110.90), 3.7× |
| M9-S | 2.63 | 321.327 → **321.327** | >200 → >200 | 2.63 A in Ø0.25 at (94.90, 81.20), 3.7× | 2.63 A in Ø0.25 at (94.90, 81.20), 3.7× |
| M10-S | 2.63 | 211.469 → **211.469** | >200 → >200 | 2.63 A in Ø0.25 at (90.90, 57.00), 3.7× | 2.63 A in Ø0.25 at (90.90, 57.00), 3.7× |
| GND M1->input caps+J2 | 15.80 | 0.487 → **0.487** | 88 → 88 | 2.59 A in Ø0.40 at (78.70, 38.00), 2.7× | 2.59 A in Ø0.40 at (78.70, 38.00), 2.7× |

### 1 oz outer / 0.5 oz inner (JLCPCB default if the order doesn't say otherwise)
Both boards were solved at this weight too.
| Branch | I (A) | R before → after (mΩ) | Neck ΔT before → after (°C) | Worst barrel before | Worst barrel after |
|---|---|---|---|---|---|
| Vin J1+caps->R1 | 20.70 | 0.371 → **0.360** ▼ | 60 → 40 | 1.32 A in Ø0.40 at (52.10, 48.30), 1.3× | 1.00 A in Ø0.40 at (52.10, 48.30), 1.0× |
| rsense_lo R1->L1 | 20.70 | 0.594 → **0.594** | 73 → 73 | 3.51 A in Ø0.40 at (53.40, 53.00), 3.6× | 3.51 A in Ø0.40 at (53.40, 53.00), 3.6× |
| LX L1->M1 | 15.80 | 1.724 → **1.772** ▲ | >200 → >200 | 5.77 A in Ø0.25 at (44.70, 67.30), 8.2× | 3.09 A in Ø0.25 at (44.70, 67.30), 4.4× |
| LX L1->M6 | 7.69 | 9.476 → **9.538** | >200 → >200 | 2.81 A in Ø0.25 at (44.70, 67.30), 4.0× | 1.50 A in Ø0.25 at (44.70, 67.30), 2.1× |
| LX L1->M5 | 8.35 | 14.237 → **15.256** ▲ | >200 → >200 | 3.77 A in Ø0.25 at (84.40, 84.60), 5.3× | 6.01 A in Ø0.25 at (84.40, 84.60), 8.5× |
| m2_source | 7.05 | 3.197 → **3.197** | >200 → >200 | 1.05 A in Ø0.25 at (42.90, 73.90), 1.5× | 1.05 A in Ø0.25 at (42.90, 73.90), 1.5× |
| m3_source | 7.69 | 1.937 → **1.937** | 197 → 197 | 0.21 A in Ø0.40 at (83.90, 76.30), 0.2× | 0.21 A in Ø0.40 at (83.90, 76.30), 0.2× |
| m4_source | 8.35 | 1.751 → **1.974** ▲ | 36 → 35 | 0.95 A in Ø0.40 at (96.50, 87.00), 1.0× | 1.00 A in Ø0.40 at (96.50, 87.00), 1.0× |
| Vout_1 M2->bank+J3 | 7.05 | 10.085 → **9.393** ▼ | >200 → >200 | 7.05 A in Ø0.25 at (38.20, 75.60), 10.0× | 7.05 A in Ø0.25 at (66.50, 83.60), 10.0× |
| Vout_2 M3->bank | 7.23 | 30.462 → **18.135** ▼ | >200 → >200 | 7.23 A in Ø0.25 at (65.30, 101.50), 10.2× | 2.87 A in Ø0.25 at (60.80, 106.10), 4.1× |
| Vout_3 M4->bank+J5 | 8.35 | 11.913 → **11.198** ▼ | >200 → >200 | 5.20 A in Ø0.25 at (88.60, 102.30), 7.3× | 2.63 A in Ø0.40 at (87.95, 101.80), 2.7× |
| Output1_drain | 2.63 | 48.686 → **34.434** ▼ | >200 → >200 | 2.63 A in Ø0.25 at (100.10, 74.90), 3.7× | 1.19 A in Ø0.25 at (70.10, 87.40), 1.7× |
| Output2_drain | 2.63 | 43.097 → **35.677** ▼ | >200 → >200 | 2.63 A in Ø0.25 at (95.30, 79.50), 3.7× | 1.44 A in Ø0.30 at (65.00, 92.90), 1.8× |
| Output3_drain | 2.63 | 33.762 → **31.440** ▼ | 198 → 97 | 2.63 A in Ø0.25 at (55.60, 100.90), 3.7× | 1.21 A in Ø0.25 at (77.50, 112.70), 1.7× |
| M8-S | 2.63 | 319.484 → **319.484** | >200 → >200 | 2.63 A in Ø0.25 at (73.50, 110.90), 3.7× | 2.63 A in Ø0.25 at (73.50, 110.90), 3.7× |
| M9-S | 2.63 | 541.327 → **541.327** | >200 → >200 | 2.63 A in Ø0.25 at (70.90, 68.50), 3.7× | 2.63 A in Ø0.25 at (70.90, 68.50), 3.7× |
| M10-S | 2.63 | 421.544 → **421.544** | >200 → >200 | 2.63 A in Ø0.25 at (90.90, 57.00), 3.7× | 2.63 A in Ø0.25 at (90.90, 57.00), 3.7× |
| GND M1->input caps+J2 | 15.80 | 0.927 → **0.924** | 166 → 166 | 2.70 A in Ø0.40 at (78.70, 38.00), 2.8× | 2.70 A in Ø0.40 at (78.70, 38.00), 2.8× |

## 5. Vias carrying a branch's whole current (item 2)

A via counts here if it carries ≥ 95 % of the branch current in the solved field,
meaning the branch has no other path. The audit named 8 such vias. The solver
finds 13 on the audited board, because Output1 and Output2 each have further
single vias in series.

| Branch | Audited board | Final board |
|---|---|---|
| Vout_1 M2->bank+J3 | 2: Ø0.25 (38.20, 75.60); Ø0.25 (66.50, 83.60) | **1**: Ø0.25 (66.50, 83.60) |
| Vout_2 M3->bank | 3: Ø0.25 (65.30, 101.50); Ø0.25 (76.00, 96.30); Ø0.25 (63.10, 108.40) | **0**: — |
| Vout_3 M4->bank+J5 | 0: — | **0**: — |
| Output1_drain | 4: Ø0.25 (100.10, 74.90); Ø0.25 (60.40, 84.60); Ø0.25 (68.90, 80.30); Ø0.25 (70.10, 87.40) | **0**: — |
| Output2_drain | 3: Ø0.25 (99.70, 72.60); Ø0.25 (65.20, 92.40); Ø0.25 (95.30, 79.50) | **0**: — |
| Output3_drain | 1: Ø0.25 (55.60, 100.90) | **0**: — |
| **Total** | **13** | **1** |

## 6. LED sink ground returns (items 7 and 9)

Each LED sink returns 2.63 A through its shunt's GND pad. The solve runs from that pad to the
input capacitors and J2 (1 oz).

| Shunt return | Audited board | Final board |
|---|---|---|
| R52.2 (M10, ch1) | 0.721 mΩ. Sole Ø0.25 via at (96.9, 58.3), 2.63 A (3.7×); neck rise 198 °C | **0.359 mΩ**. Four Ø0.30 vias share the current, worst 0.60 A (0.7×); neck rise 11 °C |
| R53.2 (M9, ch2) | 2.743 mΩ. Sole Ø0.25 via at (74.3, 68.8), 3.7×; B.Cu neck at (75.8, 68.2), 67 °C | **2.248 mΩ**. Two Ø0.25 vias share the current, worst 1.45 A (2.0×); the B.Cu neck (67 °C) is unchanged |
| R7.2 (M8, ch3) | 4.095 mΩ. Worst via Ø0.40 at (81.9, 107.2), 2.23 A (2.3×); neck rise 24 °C | 4.109 mΩ, **unchanged**. Only one via site exists near R7.2, and a single via made the worst barrel worse (§7) |

The audit's DC ground offsets between J10's GND pins and each shunt (item 9, up to
8.5 mV) were not recomputed. They depend mostly on the path from M1's return field to J10.
Lower shunt-return resistance on ch1 and ch2 reduces them but doesn't remove them.
The dominant sink error (the sense taps on the 0.15 mm sink tracks, −45 to −84 %)
is unchanged (§8).

## 7. What was tried and rejected

Every candidate change had to pass the same gate before it was kept:
- DRC with no new violation and nothing unconnected;
- no untied copper island;
- the GND planes (In1/In6) still GND-only;
- for landings on a measured branch, no rise in that branch's resistance or
  worst-barrel current.

| Attempt | Result | Why it was rejected |
|---|---|---|
| M8 → R7 1 mm corridor (stop-ship 1) | Built: 161 → 23.3 mΩ | Displaced D13--, out_3_on and U8-VDDA; re-routing closed only 1 of 4 opens. With those nets held fixed, no corridor exists. Kept in `wip/` for a placement fix. |
| M9 → R53 corridor | Found with rip-up | 9 opens instead of 5; rejected automatically. |
| LX to M6/M5 on an outer layer | No path | Blocked even with signal tracks movable. |
| Partial restore of LX on In3/In5 (253 mm²) | Negligible resistance gain | Would have put ~54 pF of LX→5V coupling back. |
| rsense_lo, 4 × Ø0.40 vias at (53.4, 53.0) | Committed | Moved the hotspot onto one barrel: 5.23 A, 5.4×. |
| Output3 (77.5, 112.7) and Vout_1 (53.4, 78.8), 4-layer Ø0.40 patches | Committed | Left untied copper slivers. |
| GND zone patch at R52.2, three box sizes | 0.721 → 0.361 mΩ | Every size left GND fill fragments (up to 0.07 mm²) at the patch edge. Replaced by vias only, which gives the same result with no fragments. |
| Vout_2 (65.3, 101.5), 4-layer patch | Committed | Overlapped the (63.1, 108.4) patch on In2 (zones_intersect) and split a B.Cu GND pour. Replaced by a two-layer patch that stops short of it. |
| Vout_1 (66.5, 83.6), 12 mm three-layer patch | 4 vias | 25 untied fragments. |
| Ø0.40 landings at Vout_1 (66.5, 83.6), Vout_2 (65.3, 101.5) and (63.1, 108.4), Output1 (68.9, 80.3), Output2 (65.2, 92.4) and (99.7, 72.6), LX (44.7, 67.3) and (84.4, 84.6), GND R53.2, R7.2 and (78.7, 38.0) | 0–1 via sites | Too congested for Ø0.40 at 1.15 mm pitch. Retried with Ø0.30 and Ø0.25 (results in §2). |
| Vout_1 (66.5, 83.6): Ø0.30 or Ø0.25 vias with a 12 mm three-layer patch, or vias only | 4 or 10 vias with a patch; 0 sites without | 25 and 26 untied fill fragments. **This via still carries all 7.05 A (10×).** |
| Output3 (77.5, 112.7): Ø0.30 or Ø0.25 vias only | 0 sites | Congested. The via carries 1.19 A (1.7×), not the whole branch. |
| LX (84.4, 84.6): Ø0.30 or Ø0.25 vias only | 0 sites | Congested. It is inside the In4 LX corridor; see §8. |
| rsense_lo (53.4, 53.0): 5 × Ø0.30 vias only | R 0.522 → 0.462 mΩ | The new Ø0.30 via would carry 3.12 A (3.9×, against 3.8× before), and the neck rise would go from 76 to 96 °C. A second strategy that also concentrated current, so rejected, and rsense_lo is left as audited. |
| GND at R7.2: Ø0.30 or Ø0.25 vias, 3 mm and 4 mm boxes | 1 site at most | One via cut the R7.2 return from 4.1 to 1.1 mΩ, but it alone carried 2.29 A (2.9×, against 2.3× for the existing via). No second site exists, so rejected. |
| GND M1 return via (78.7, 38.0): Ø0.40 or Ø0.30 vias only | 0 sites | Congested beside the input capacitors. |

## 8. Needs a design decision

These can't be closed by moving copper without changing the schematic,
footprints, placement, fabrication spec or mechanics. Each was investigated
on the board.

### LED sink channels: current path and sense taps (stop-ship 1, items 5 and 9)
Net-(M8-S), Net-(M9-S) and Net-(M10-S) still run as 0.15 mm inner tracks
(161 / 321 / 211 mΩ, fusing at 2.63 A). Each op-amp still senses upstream of
its shunt. **This is the most serious remaining problem, and it isn't fixed.**
- **M8 → R7 (ch3):** a 1.0 mm F.Cu/B.Cu corridor exists and was built. It
  takes the path to 23.3 mΩ with a 12 °C neck rise, and U6's sense connection
  moved to R7.1. It is in `wip/`, not the fabrication board. The corridor
  displaces D13--, out_3_on and U8-VDDA around U8/R47, and none of them can be
  re-routed without a small placement change (for example moving R47).
- **M9 → R53 and M10 → R52 (ch2, ch1):** the corridor search found no
  1 mm path on any layer without pushing many signal nets through power copper.
  The shunts need to move next to their FETs, which is a placement decision.
- The sink sense-tap errors (−45 to −84 % LED current) go away only once each
  op-amp senses at its shunt pad. That comes with the corridors above.

### Copper weight (item 2)
Neither board declares a stackup. The gerber job says 1 oz on all eight layers,
and an unannotated JLCPCB order is 1 oz outer / 0.5 oz inner. Every number here
is given at 1 oz, with 1 oz / 0.5 oz alongside. Specifying 2 oz, or at least
1 oz inner, would lower most remaining neck temperatures. That is a cost and fab
decision, so it isn't written into the files.

### R1 Kelvin sensing (item 3)
U25's inputs are on the `Vin` and `rsense_lo` nets, the same nets as the 20.7 A
pours, and U25 is 46 mm from R1. Without separate sense nets, any sense trace
merges with the pour it touches. A true Kelvin connection needs dedicated sense
nets (net-ties at R1's pads) or a four-terminal shunt footprint, plus U25 moved
near R1. Both are schematic and footprint changes.

### Commutation-loop inductance (item 4)
Every loop passes through three TO-220 packages: M1, the LX-side FET and the
rail-side body diode. Their lead inductance alone exceeds the 4.3 nH budget for
70 V, so no copper arrangement of this part set can meet it. Copper resistance
in the Vout_2 part of the channel-2 loop fell (17.3 → 9.79 mΩ), but the
package term needs a part or topology change.

### LX to M6/M5 and the Vout rails (items 5 and 7)
- LX reaches M6 and M5 through a track inside the In4 5V plane. No outer-layer
  corridor of the needed width exists, even with signal tracks moved. Taking LX
  out of In4 needs a placement change around M1/M6/M3/M4.
- Vout_1/2/3 run 35–57 mm of inner-layer track from each rail FET to its bank.
  At 1 oz an inner track needs about 7.5 mm of width for 7–8 A at a 20 °C rise.
  The fixes are moving each bank next to its FET, or heavier copper.

### Inter-board connector J10/J11 (item 8)
There is no ground pin among analog pins 21–30. Both headers are male and
mirrored, so they can't stack, and the dividers straddle the connector. These
are pin-assignment and connector choices, and J10/J11 aren't in the schematic.

### TO-220 mounting (item 10)
- All ten parts use `TO-220-3_Horizontal_TabDown`. Confirm the tab orientation
  or change to TabUp.
- Washer keep-out: a 7 mm M3 washer (3.75 mm radius including 0.25 mm margin)
  overlaps 17 parts' courtyards, none with a free spot within 14 mm: C6, C71,
  C72, C73, C74, C75, C77, C78, C86, C87, C88, D12, R104, R14, R43, R74 and
  U12. The closest are R14 at 2.46 mm, D12 at 2.59 mm and R104 at 2.76 mm from
  the hole centres. Most are output-bank capacitors, so this is a placement and
  hardware decision (washer size, insulator, screw-head side).
- The tab pitch (1.09 mm gap) and U16's height against the TO-220 body gap are
  mechanical.

### Mechanical stack and control-board fixing (item 12)
The stack height and the control board's lack of mounting holes are enclosure
and mechanical decisions.

### J10/J11 annular ring (item 13)
0.175 mm passes JLCPCB's 1 oz absolute minimum. It is below the recommended
0.20 mm, and fails if 2 oz is ordered. Fixing it means enlarging the footprint's
pads, which ties in with the copper-weight decision.

### Output-bank capacitors (items 6 and 12)
EEH-ZU1H221P is 10 × 16.5 mm per Panasonic, while the footprint is
`CP_Elec_10x10.5`; confirm the footprint and 3D model. C74 carries 90 % of its
rating at 1 oz / 0.5 oz. Item 6 passes, but with little margin.

### Needs data (from the audit, unchanged)
- the BOM (R1 part number, 680 µF part, shunt ratings);
- HYG180N10 lead inductance and capacitor ESL;
- the inter-board cable;
- a thermal model;
- whether `BOOST.kicad_sch` matches its newer `.history` copy.
