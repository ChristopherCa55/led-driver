Companion files: `BOOST_AUDIT.html` (full page with figures) · `BOOST_AUDIT_density_maps.png`. Published page: https://claude.ai/code/artifact/aaf5f06d-ba80-4751-b12e-b6402e8ecbb9

Board files re-checked 2026-09-13: SHA-256 still 527284DF10FB07CE… (power) and 61D718272D55D627… (control), so these results are current.

Independent copper audit · 3-channel 100 W LED driver

# BOOST split-board audit

BOOST_power.kicad_pcb · BOOST_control.kicad_pcb saved 2026-09-10 13:37:50 · SHA-256 5272…07CE / 61D7…D627 KiCad 10.0.6 · zones refilled on fresh load checked 2026-09-11

The routing report is right that both boards pass DRC. It is not right that they are clean. Computed from the copper itself, 10 of the 13 checks fail. Several of those failures would destroy parts at first power-up. DRC could not see any of them, because the rules the report relied on don't describe them.

## Stop-ship findings

1. **LED current runs through 0.15 mm tracks.** `Net-(M8-S)`, `Net-(M9-S)` and `Net-(M10-S)` carry the full 2.63 A from each sink FET to its shunt. They use 50–101 mm of 0.15 mm track on inner layers: 501 A/mm² at 1 oz, 165–334 mΩ, 1.1–2.3 W each. They will fuse. The sink op-amps sense the shunt at a point 42–270 mΩ upstream, so the loop can only reach 1.43 / 0.84 / 0.41 A instead of 2.63 A. These nets aren't in the Power netclass, so no rule looked at them.

2. **Eight power connections hang on a single 0.25 mm via.** Vout_1 (2 vias), Vout_2 (3) and all three Output drains depend on one Ø0.25 mm barrel each. Those barrels carry 2.6–7.2 A RMS, against about 0.7 A capacity. KiCad's own connectivity engine confirms each one is the only connection: remove it and the net opens.

3. **The commutation loop overshoots with copper alone.** At 8 A/ns the PCB copper by itself gives 74 / 137 / 99 V on LX for channels 1/2/3. Three TO-220 packages sit in every loop, which pushes it past 350 V. The 70 V target needs ≤ 4.3 nH total.

4. **The current sense reads 32% high.** The INA241 is 46 mm from R1 and taps the Vin and rsense_lo pours, not R1's terminals. RESET trips at 30.6 A instead of 40.5 A.

5. **The stack doesn't fit.** Any 60 × 60 mm control card inside the 78 × 90 mm case sits over L1 (19 mm). The minimum stack is 36.5 mm against 33 mm, and the control board has no mounting holes.

## Verdicts

| # | Check | Verdict | Deciding number | Against |
|---|---|---|---|---|
| 1 | R1 value | **PASS** | 2 mΩ in PCB and schematic (the report's "12 mΩ" is a typo in the report only) | 2 mΩ |
| 2 | Copper weight | **FAIL** | No stackup in either file; gerber job = 35 µm on all 8 layers; no fab notes | 2 oz assumed everywhere |
| 3 | R1 Kelvin sensing | **FAIL** | +26.1 mV at 40.5 A → 13 A phantom output-referred; loop ≈ 1 770 mm² | 10 mV → 100 mA |
| 4 | Commutation loop | **FAIL** | 74 / 137 / 99 V copper-only; > 350 V with packages | ≤ 70 V |
| 5 | Current density / necks | **FAIL** | Necks of 0.017–0.13 mm² carrying 2.6–20.7 A (155–501 A/mm²) | IPC-2221 ≤ 20 °C rise |
| 6 | Capacitor current sharing | **PASS** | Worst part C74 at 3.46 A (77%); up to 1.47× spread within a bank. At 1 oz / 0.5 oz: 4.07 A (90%) | 4.5 A / 5.4 A per part |
| 7 | Vias in the current path | **FAIL** | Worst barrel 7.2 A (Ø0.25); rsense_lo 3.8 A (Ø0.40) | 0.71 / 0.97 A per barrel |
| 8 | Inter-board connector | **FAIL** | No GND pin among the 10 analog pins; J10/J11 both male and mirrored | Adjacent ground returns; mateable |
| 9 | Ground return & measurement | **FAIL** | Sink sense taps 42–270 mΩ off the shunts (LED current −45 to −84%); GND offsets up to 8.5 mV DC (−6.5% on ch3) | ≪ 1% LED current error |
| 10 | Component thermal / TO-220 mounting | **FAIL** | Live copper 0.2 mm from every tab hole; 1.09 mm tab gaps; TabDown model | Washer/insulator keep-out |
| 11 | PCB ↔ schematic netlist | **PASS** | 0 splits, 0 merges, 0 value/footprint mismatches; J10/J11 exist only in the PCBs | Exact match |
| 12 | Mechanical fit | **FAIL** | Outlines fit; stack ≥ 36.5 mm | 33 mm internal |
| 13 | Fabrication | **FAIL** | J4 silk 0.80 mm × 0.12 mm; J10/J11 annular 0.175 mm | JLCPCB 1.0 mm × 0.15 mm; 0.20 mm rec. |

Rules: both `.kicad_pro` files have `drc_exclusions: []` and no `rule_severities` block, so every check runs at KiCad's default severity. No `.kicad_dru` exists anywhere under the project. I weakened, excluded and added nothing. DRC on the refilled saved files reproduces the report: power 1 warning (the `lib_footprint_issues` library-table warning for L1), control 0. Both boards are open in pcbnew at the time of this audit (power opened 2026-09-11 11:51), so every figure here comes from hashed copies of the saved files, not from the editor.

## 1 · R1 value — **PASS**

**Measured** PCB: R1 value `2m`, `R_2512_6332Metric`, B.Cu at (50.88, 51.25) rot 90. Schematic (`BOOST.kicad_sch`, exported netlist): R1 `2m`, same footprint. R99 in the schematic is now an unrelated 10 kΩ part. The 0.012 Ω cable model was deleted, as your notes say.

**Threshold** 2 mΩ, 0.1 V/A with the INA241A3 (gain 50)

**Depends on** The BOM ordering the part the value field names. `BOOST_BOM.xlsx` is not in this folder, so I couldn't check it.

The "12 mΩ shunt" appears only in ROUTING_REPORT.md §4, the components-moved table. It is a documentation error, so the 6× scale error, 8 A RESET and 5.1 W dissipation do not apply. The shunt's *effective* value as the INA241 sees it is 2.65 mΩ, not 2 mΩ, because of where the sense lines tap in (item 3).

## 2 · Copper weight and the recomputed high-current table — **FAIL**

**Measured** Neither board has a `(stackup …)` block in `(setup)`. The gerber job KiCad writes from the saved files declares **0.035 mm (1 oz) on all eight copper layers**, with seven 0.1857 mm dielectrics, 1.6 mm total and finish "None". No fab note exists on any layer: the only board-level drawings are four Edge.Cuts lines. The "2 oz" appears only in README prose.

**Threshold** Report assumption: 2 oz (70 µm) on all 8 layers

**Depends on** What gets typed into the fab order. JLCPCB's page lists inner copper as 0.5 / 1 / 2 oz with **0.5 oz as the default**, and outer as 1 or 2 oz. So an unannotated order is 1 oz / 0.5 oz, which is config C below.

I recomputed every branch in the report on my own conductance mesh, built from the refilled geometry. The grid is 0.1 mm (0.05 mm for the smaller nets), with real via barrels (20 µm plating, the board setting) and terminal pads as equipotentials. At the report's own 2 oz assumption my numbers land within about 10% of the report wherever the path runs through wide pours. That is the Vin rows, m*_source, Vout_3→J5 and Output3, and it validates both methods. They diverge 2–8× where the path is forced through a 2 mm In4 track or a 0.25 mm via. A 0.4 mm mesh like the report's cannot resolve those features.

| Net | Branch | Report 2 oz | Mine 2 oz | Mine 1 oz (as filed) | Mine 1 oz / 0.5 oz | As filed ÷ report |
|---|---|---|---|---|---|---|
| Vin | J1.1→R1.2 | 0.47 | 0.44 | 0.86 | 0.86 | 1.8× |
| Vin | C85.1→R1.2 | 0.26 | 0.27 | 0.51 | 0.51 | 2.0× |
| Vin | C40.1→R1.2 | 0.23 | 0.23 | 0.44 | 0.44 | 1.9× |
| rsense_lo | R1.1→L1.2 | 0.37 | 0.30 | 0.53 | 0.60 | 1.4× |
| LX | L1.1→M1.2 | 0.36 | 0.59 | 1.10 | 1.50 | 3.0× |
| LX | L1.1→M7.2 | 0.22 | 0.27 | 0.49 | 0.57 | 2.2× |
| LX | L1.1→M6.2 | 0.49 | 2.47 | 4.85 | 9.00 | 9.9× |
| LX | L1.1→M5.2 | 0.50 | 3.81 | 7.40 | 13.66 | 14.8× |
| GND | M1.3→C85.2 | 0.16 | 0.98 | 1.85 | 2.30 | 11.6× |
| GND | M1.3→J2.1 | 0.16 | 0.25 | 0.51 | 1.00 | 3.2× |
| GND | M1.3→C40.2 | 0.16 | 0.38 | 0.67 | 1.22 | 4.2× |
| Vout_1 | M2.2→C86.1 | 3.37 | 3.56 | 6.18 | 10.27 | 1.8× |
| Vout_1 | M2.2→J3.1 | 4.87 | 9.99 | 18.92 | 35.60 | 3.9× |
| Vout_2 | M3.2→C78.1 | 5.46 | 12.56 | 22.50 | 38.85 | 4.1× |
| Vout_2 | M3.2→J8.1 | 2.39 | 2.63 | 5.26 | 10.52 | 2.2× |
| Vout_3 | M4.2→C77.1 | 5.67 | 7.56 | 13.87 | 26.28 | 2.4× |
| Vout_3 | M4.2→J5.1 | 3.38 | 3.40 | 6.57 | 12.89 | 1.9× |
| m2_source | M7.3→M2.3 | 0.80 | 0.86 | 1.69 | 3.27 | 2.1× |
| m3_source | M6.3→M3.3 | 0.58 | 0.65 | 1.30 | 1.93 | 2.2× |
| m4_source | M5.3→M4.3 | 0.67 | 0.70 | 1.38 | 1.75 | 2.1× |
| Output1_drain | M10.2→J4.1 | 18.21 | 20.20 | 37.49 | 49.25 | 2.1× |
| Output2_drain | M9.2→J7.1 | 13.67 | 15.33 | 29.09 | 43.37 | 2.1× |
| Output3_drain | M8.2→J6.1 | 8.82 | 9.00 | 17.48 | 34.10 | 2.0× |

All values in mΩ at 20 °C, two-terminal between the named pads with every other terminal open (GND solved on a 0.2 mm grid). The report gives 0.16 mΩ for all three GND branches; mine differ by 4× between them, because M1's source pin connects to no F.Cu copper and leaves through a narrow ring on In1/In6/B.Cu (item 5). The report's "rsense_lo at 1.10× its requirement" becomes **0.76×** at 1 oz, using the report's own equivalent-width method: 9.85 mm equivalent against 12.9 mm required for 20.7 A at a 20 °C rise. Item 5 shows why that metric understates the problem.

## 3 · R1 Kelvin sensing — **FAIL**

**Measured** U25 (INA241A3, F.Cu, (84.5, 82.3)) IN+ pin 8 is on net `Vin` and IN− pin 1 is on `rsense_lo`. There are no separate sense nets in the schematic or PCB. R1 sits on B.Cu at (50.9, 51.3), **46 mm away**. At 40.5 A the copper between R1's pads and the points where the sense conductors leave the current path adds **15.2 mV (IN+) + 11.0 mV (IN−) = 26.1 mV** to the 81.0 mV shunt signal.

**Threshold** 10 mV of offset = 100 mA phantom current (output-referred, 0.1 V/A)

**Depends on** 1 oz copper. At 2 oz it's still +14.5 mV (+18%, RESET at 34.3 A); at 1 oz / 0.5 oz it's +26.5 mV (+33%). The 2512 part's own termination resistance isn't included, and neither is magnetic pickup in the loop. Both would add error.

- Effective shunt 2.645 mΩ (+32%). Output-referred error 1.31 V, which is 13 A of phantom current at the peak.

- RESET trips at **30.6 A instead of 40.5 A**. To reach the simulated 40.5 A the error amp would need V_err = 5.36 V. That's above the 4.76 V full scale and the INA's 4.98 V clip, so the converter cannot deliver its designed peak.

- Sense conductors through copper: IN+ 168 mm, IN− 165 mm (grid path, an upper bound). The enclosed sense-loop plan area is about **1 770 mm²**. It surrounds L1 and the LX corridor. All of it is high-current copper; nothing in the loop is a dedicated trace.

- The footprint is the stock two-terminal `R_2512_6332Metric`. A four-terminal Kelvin land was specified in your placement notes, and it isn't present.

## 4 · Commutation loop, M1 → M7/6/5 → M2/3/4 body diode → bank → GND — **FAIL**

**Measured** Copper-only loop inductance **4.85 / 12.74 / 7.91 nH** (channels 1/2/3), giving LX peaks of **74 / 137 / 99 V** at 8 A/ns.

**Threshold** 70 V flag; 100 V BVDSS. Budget: L ≤ 4.31 nH for 70 V, ≤ 8.06 nH for 100 V.

**Depends on** The same over-plane model the report used for D19, L = µ₀·h·(squares), with h = 0.221 mm to the adjacent GND plane. It is geometry-only, so the result doesn't change with copper weight. The package term uses typical TO-220 LD + LS = 4.5 + 7.5 nH; HYG180N10's datasheet doesn't state it.

| Channel | LX M1→M7/6/5 | m*_source | Vout→bank | GND return | Plan-view area | L copper | V_LX copper | + caps ESL/3 | + 3 × TO-220 |
|---|---|---|---|---|---|---|---|---|---|
| 1 (M7, M2) | 0.717 mΩ | 1.694 | 6.177 | 0.515 | 44 mm² | 4.85 nH | 74.3 V | 82.3 V | 370 V |
| 2 (M6, M3) | 3.828 | 1.297 | 17.452 | 0.344 | 89 mm² | 12.74 nH | 137.4 V | 145.4 V | 433 V |
| 3 (M5, M4) | 6.383 | 1.379 | 6.262 | 0.357 | 83 mm² | 7.91 nH | 98.8 V | 106.8 V | 395 V |

The failure is structural as well as a layout problem. Every commutation loop passes through three TO-220 packages: M1, the LX-side FET and the rail-side FET's body diode. Their leads alone are several times the 4.3 nH budget, so no copper arrangement of this part set can meet 70 V at 8 A/ns. As built, the TVS (about 82 V at 45 A) or M1's avalanche would absorb the overshoot on every cycle. Channel 2 is worst because its rail current reaches the capacitors through a chain of three 0.25 mm vias and 1.25 mm tracks (item 7).

The report's D19 loop, recomputed with the report's own method (both legs, over-plane): LX M1.2→D19.1 1.51 mΩ plus GND D19.2→M1.3 0.86 mΩ gives **1.34 nH** of copper (1.55 nH at 2 oz, against the report's 1.43 nH). So the report's copper figure holds, and that agreement cross-checks both methods. What it leaves out is M1's own drain and source leads, which sit in series with the die D19 protects. Adding a typical 12 nH for them gives 16.3 nH, or 166 V at 8 A/ns. And D19 is the wrong loop to judge by: it doesn't conduct in normal operation, while the commutation loop above sets the overshoot on every cycle.

## 5 · Current density and the minimum cross-section on each path — **FAIL**

**Measured** Minimum copper cross-section crossed by the full current of each path. It comes from the solved potential field: the co-area integral of |∇φ| over every equipotential band, with via barrels included.

**Threshold** IPC-2221 ≤ 20 °C rise (the report's criterion), applied to the neck cross-section

**Depends on** 1 oz as filed. RMS currents: M1 branch 15.8 A (from 20.7² − Σ channel²); channel switches 7.05 / 7.69 / 8.35 A; bank AC 6.54 / 7.22 / 7.92 A; LED 2.63 A. The IPC-2221 formula treats the neck as an infinitely long conductor, so it is conservative for short necks. Values above 200 °C only mean "fuses".

| Path (RMS) | R mΩ | Min section | Where / what | Avg J at neck | IPC ΔT | at 1 oz / 0.5 oz |
|---|---|---|---|---|---|---|
| Vin J1→R1 18.4 A | 0.86 | 0.363 mm² | (51.2, 47.0) B.Cu + via field at R1.2 | 51 A/mm² | 22 °C | same |
| Vin J1+caps→R1 20.7 A | 0.40 | 0.116 mm² | (49.6, 47.4) 68% via barrels feeding R1.2 | 179 | via-limited | same |
| rsense_lo R1→L1 20.7 A | 0.53 | 0.130 mm² | (51.6, 53.1) B.Cu leaving R1.1 (≈ 3.7 mm at 1 oz) | 160 | 156 °C | 0.210 mm², 71 °C |
| LX L1→M1 15.8 A | 1.10 | 0.069 mm² | (46.9, 68.1) F.Cu 76% + vias | 228 | >200 | 0.043 mm², 370 A/mm² |
| LX L1→M6 7.69 A | 4.85 | 0.033 mm² | (70.5, 80.8) single In4 track inside the 5V plane | 231 | >200 | 0.016 mm², 483 A/mm² |
| LX L1→M5 8.35 A | 7.40 | 0.022 mm² | (74.0, 82.0) same In4 corridor | 378 | >200 | 0.007 mm², 1 170 A/mm² |
| m2_source M7→M2 7.05 A | 1.69 | 0.032 mm² | (46.8, 76.8) In2 | 222 | >200 | 0.013 mm², 538 A/mm² |
| m3_source M6→M3 7.69 A | 1.30 | 0.049 mm² | (80.3, 75.1) F.Cu | 156 | 81 °C | same |
| m4_source M5→M4 8.35 A | 1.38 | 0.042 mm² | (96.9, 79.5) F.Cu | 199 | 127 °C | 0.039 mm² |
| Vout_1 M2→bank+J3 7.05 A | 6.18 | 0.017 mm² | one Ø0.25 via at (38.2, 75.6), in series with a second at (66.5, 83.6) | 416 | >200 | 0.010 mm² (In2) |
| Vout_2 M3→bank 7.23 A | 17.45 | 0.017 mm² | three Ø0.25 vias in series: (76.0, 96.3), (65.3, 101.5), (63.1, 108.4) | 426 | >200 | 0.011 mm² |
| Vout_3 M4→bank+J5 8.35 A | 6.20 | 0.034 mm² | two Ø0.25 vias at (88.6, 102.3) / (88.7, 103.5) + In4 | 244 | >200 | 0.029 mm² |
| Output1/2/3_drain 2.63 A | 37.5 / 29.1 / 17.5 | 0.017 mm² | one Ø0.25 via each: (60.4, 84.6), (65.2, 92.4), (55.6, 100.9) | 155 | 198 °C | 0.008–0.017 mm² |
| Net-(M8/9/10-S) 2.63 A | 165 / 334 / 216 | 0.0053 mm² | 0.15 mm × 35 µm tracks on In2/In3/In5/B.Cu for 50 / 101 / 66 mm | 501 | fuses | 1 002 A/mm² |
| GND M1.3→input caps+J2 20.7 A (M1's own 15.8 A) | 0.43 | 0.284 mm² | (62.3, 72.6), the ring round M1's source pin: In1 37%, In6 46%, B.Cu 17%, no F.Cu at all | 73 (56) | >200 (112 °C) | 0.186 mm², 226 °C at 15.8 A |
| GND Vout_1 bank return 6.54 A | 0.59 | 0.037 mm² | (89.1, 86.8) F.Cu strip | 175 | 89 °C | 0.067 mm² |

> *[Figure: Fourteen current-density maps of the power board, one per high-current path, showing the maximum over all layers of RMS current density on a log scale from 1 to 1000 amps per square millimetre. — image in BOOST_AUDIT_density_maps.png or the HTML version.]*

Current-density maps (config A, 1 oz), maximum over the 8 layers, log colour 1–1000 A/mm². Left to right, top to bottom: Vin combined, rsense_lo, LX combined, m2/m3/m4_source, Vout_1/2/3 combined, Output1/2/3_drain, GND M1 return, GND combined. Green rings mark each path's neck or peak. The dark pours are copper carrying almost nothing. Much of the LX and Vout copper counted in the report's pour areas is not in any current path.

## 6 · Capacitor current sharing — **PASS**

**Measured** For each part: impedance from the switch terminal (M2/M3/M4 drain, or R1.2 for the input) to the capacitor, then through GND back to the return. The split comes from the full port-reduced copper network, summed over the harmonics of the simulated current pulse.

**Threshold** 4.5 A per EEH-ZU1H221P (your figure; Panasonic lists 5.2 A at 125 °C, 3.6 A at 135 °C) · 5.4 A per input part

**Depends on** ESR 10 mΩ each (Panasonic, 100 kHz; tolerance not modelled). ESL 3 nH assumed, since it isn't specified. Copper inductance uses the over-plane model. Waveforms are triangular pulses fitted to the simulated RMS (ch1 28.3 A over 19.6 µs every 105.6 µs). Switching-edge content beyond that model isn't included.

| Bank | Part | Path R | Path L | RMS (1 oz) | of equal share | of rating | RMS at 1 oz / 0.5 oz |
|---|---|---|---|---|---|---|---|
| Vout_1 | C70 | 21.7 mΩ | 10.7 nH | 1.90 A | 87% | 42% | 1.73 A |
|  | C86 | 7.1 | 3.5 | 2.70 | 124% | 60% | 3.12 |
|  | C88 | 13.3 | 6.8 | 2.14 | 98% | 48% | 2.09 |
| Vout_2 | C71 | 24.0 | 13.0 | 2.24 | 93% | 50% | 2.16 |
|  | C78 | 23.4 | 12.7 | 2.26 | 94% | 50% | 2.19 |
|  | C87 | 18.2 | 9.9 | 2.85 | 118% | 63% | 3.12 |
| Vout_3 | C74 | 6.9 | 3.5 | 3.46 | 131% | 77% | 4.07 (90%) |
|  | C75 | 15.2 | 8.0 | 2.35 | 89% | 52% | 2.17 |
|  | C77 | 14.6 | 7.8 | 2.37 | 90% | 53% | 2.20 |
| Vin | C40 | 1.11 | 0.25 | 3.27 | 104% | 61% | 3.26 |
|  | C69 | 1.76 | 0.49 | 3.16 | 100% | 59% | 3.15 |
|  | C85 | 2.36 | 0.29 | 3.05 | 97% | 57% | 3.07 |

No part exceeds its rating, but the margin is thin and it depends on copper weight. Path resistance spreads up to 3.1× within a bank, but each part's 10 mΩ ESR and its reactance at the 9.5 kHz channel rate absorb much of that, so currents spread 1.2–1.5× at 1 oz and 1.4–1.9× at 1 oz / 0.5 oz. C74 is the one to watch: at 1 oz / 0.5 oz it carries 4.07 A, 90% of your 4.5 A figure and above Panasonic's 3.6 A rating at 135 °C. The report checked one capacitor per bank, which cannot reveal this.

Two facts don't depend on the split. First, the simulation's "≈ 3.7 A per capacitor" came from the two-capacitor run. With three caps per rail the bank ripple is √(I_sw² − I_LED²) = 6.54 / 7.22 / 7.92 A, so the equal share is 2.18 / 2.41 / 2.64 A. Second, Panasonic lists EEH-ZU1H221P as 10 × **16.5** mm, 10 mΩ, 5.2 A at 125 °C and 3.6 A at 135 °C. The footprint name `CP_Elec_10x10.5` implies a 10.5 mm can.

## 7 · Via barrels actually in the current path — **FAIL**

**Measured** Current in every barrel segment, taken from the solved field, not from barrel counts.

**Threshold** IPC-2221 internal-conductor rating of the barrel wall at 10 °C: Ø0.40 → 0.97 A, Ø0.25 → 0.71 A

**Depends on** 20 µm plating (the board's hole-plating setting) and 1 oz copper

| Net / path | Barrels on net | Carrying ≥ 1% of I | Worst barrel | vs capacity |
|---|---|---|---|---|
| Vin J1→R1 18.4 A | 263 | 43 | 1.18 A, Ø0.40 at (52.1, 48.3) | 1.2× |
| Vin J1+caps→R1 20.7 A | 263 | 36 | 1.34 A, same barrel | 1.4× |
| rsense_lo R1→L1 20.7 A | 25 | 20 | 3.80 A, Ø0.40 at (53.4, 53.0) | 3.9× |
| LX L1→M1 15.8 A | 74 | 8 | 6.36 A, Ø0.25 at (44.7, 67.3) | 9.0× |
| LX L1→M5 8.35 A | 74 | 17 | 3.46 A, Ø0.25 at (84.4, 84.6) | 4.9× |
| Vout_1 M2→bank 6.54 A | 20 | 7 | 6.54 A, Ø0.25 at (38.2, 75.6), sole path | 9.2× |
| Vout_2 M3→bank 7.23 A | 71 | 5 | 7.23 A, Ø0.25 at (76.0, 96.3), sole path | 10.2× |
| Vout_3 M4→bank 7.92 A | 45 | 5 | 4.69 A, Ø0.25 at (88.6, 102.3) | 6.6× |
| m2_source 7.05 A | 21 | 11 | 1.07 A, Ø0.40 at (44.0, 73.4) | 1.1× |
| m3 / m4_source | 29 / 24 | 1 / 9 | 0.09 / 0.91 A | ok |
| Output1/2/3_drain 2.63 A | 11 / 12 / 10 | 4 / 3 / 8 | 2.63 A in one Ø0.25 each, sole path | 3.7× |
| GND M1 return 20.7 A | 285 | 21 | 2.97 A, Ø0.40 at (78.7, 38.0) beside the input caps | 3.0× |
| GND sink returns 2.63 A each | 285 | 20 | 2.63 A in one Ø0.25 each: R52.2 at (96.9, 58.3), R53.2 at (74.3, 68.8) | 3.7× |
| GND Vout_2 bank return 7.23 A | 285 | 35 | 2.05 A, Ø0.25 at (54.0, 81.4) | 2.9× |

- **Why Vin has 246 Ø0.40 barrels on only two copper layers:** they are stitching arrays between the F.Cu and B.Cu Vin pours. Current only needs to change layers where it goes from J1 and the F.Cu capacitors to R1, which is on B.Cu. That transfer happens in the cluster next to R1.2. At 18.4 A, 43 of 263 barrels carry ≥ 1% of the current, so about 84% are decorative. Even so, the cluster next to R1 is over its rating.

- **The router used Default-class 0.45/0.25 mm vias in Power nets.** The Power netclass's 0.8/0.4 via is only a default, not a rule, and DRC only enforces the 0.45 mm minimum. KiCad's own connectivity engine confirms that removing any one of these eight vias opens its net: Vout_1 (38.2, 75.6) and (66.5, 83.6); Vout_2 (76.0, 96.3), (65.3, 101.5) and (63.1, 108.4); Output1 (60.4, 84.6); Output2 (65.2, 92.4); Output3 (55.6, 100.9).

## 8 · Inter-board connector J10 (power) ↔ J11 (control) — **FAIL**

- **PASS** — **Gate drivers stay on the power board.** U8, U10, U15 and U19 (UCC21520DW) are all there, with their FETs. The 21 crossing nets are logic-level driver inputs, feedback and sense signals, and three rails. No high-current net crosses. J10 pin n and J11 pin n carry the same net for all 30 pins.

- **FAIL** — **No ground return among the analog pins.** All ten GND pins sit in pins 1–20. The block of pins 21–30 carries every analog signal (Current, the three .1Vout_n, the three IREF_n_input, and the three servo drain senses) with no ground pin among them. `Current` (21) sits beside `12V` (19).

- **FAIL** — **The dividers straddle the connector.** The top resistors are on power (18 k R9/R35/R43; 910 k R25/R87/R94) and the bottom resistors (2 k, 100 k) are on control. The pins see 0–4.5 V only while the cable is mated; unplugged they float up to the rail through 18 k. The ratio is referenced to the control ground. The IREF divider (R10/R54/R57) is on control, so the 25–131 mV sink setpoints cross the connector as bare low-level analog.

- **FAIL** — **J10 and J11 cannot stack.** Both are male `PinHeader_2x15_P1.27mm_Vertical`. J11 on the control board's B.Cu is the mirror image of J10 (pin-grid handedness −1.61 vs +1.61), so no stacking position mates pin n to pin n. The link must be a 30-way 1.27 mm IDC ribbon, and no such cable or sockets exist in the files. J10 and J11 are also absent from the schematic.

J10 / J11 pinout (odd pins in the first row, even pins in the second):

| **1**GND | **3**GND | **5**GND | **7**GND | **9**GND | **11**GND | **13**GND | **15**5V | **17**a5V | **19**12V | **21**Current | **23**.1Vo2 | **25**IREF1 | **27**IREF3 | **29**srvB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **2**M1_ON | **4**M2_ON | **6**ena1 | **8**ena2 | **10**ena3 | **12**o2_on | **14**o3_on | **16**GND | **18**GND | **20**GND | **22**.1Vo1 | **24**.1Vo3 | **26**IREF2 | **28**srvA | **30**srvC |

Legend: ground (pins 1–13 odd, 16, 18, 20) · supply rail (15, 17, 19) · analog with no adjacent ground (21–30) · logic (2–14 even)

## 9 · Ground return and measurement integrity — **FAIL**

**Measured** Each sink op-amp senses its shunt through the same 0.15 mm track that carries the LED current, joining it upstream of the shunt pad. Track between the tap and the shunt: ch1 (U11/R52) 107 mΩ, ch2 (U12/R53) 270 mΩ, ch3 (U6/R7) 42 mΩ. The loop therefore regulates across shunt plus track. At the 131.5 mV setpoint the sinks deliver **0.84 / 0.41 / 1.43 A instead of 2.63 A** (−68 / −84 / −45%).

**Threshold** Your ±4% per-channel budget (MCP6241 offset) — this is 10–20× that

**Depends on** 1 oz. At 2 oz the three channels give 1.26 / 0.70 / 1.85 A. If IREF is raised to force 2.63 A, the tracks fuse (item 5).

**Ground offsets.** The control board's reference is J10's ten GND pins, at (69–81, 72–74), 7–19 mm from M1's source pin and inside its return-current field. The sink setpoints (IREF_n_input) are referenced to it. Each sink regulates against its own shunt return: R52.2 and R53.2 each reach GND through one Ø0.25 mm via, and R7.2 joins the B.Cu pour with no via within 4 mm.

| Channel | DC: J10 GND − shunt GND | LED error | At M1 = 40.5 A (instant) | Bank ripple (RMS) | DC at 1 oz / 0.5 oz | DC at 2 oz |
|---|---|---|---|---|---|---|
| ch1 (U11 / R52 / M10) | +2.45 mV | +49 mA (+1.9%) | +8.43 mV → +169 mA | 1.0–1.5 mV | +4.3% | +0.7% |
| ch2 (U12 / R53 / M9) | −5.61 mV | −112 mA (−4.3%) | +0.64 mV → +13 mA | 0.2 mV | −4.6% | −2.4% |
| ch3 (U6 / R7 / M8) | −8.50 mV | −170 mA (−6.5%) | −0.04 mV | 0.6–1.4 mV | −7.1% | −3.4% |
| INA241 REF (U25.3/.7) − J10 GND | +0.27 mV | 3 mA phantom | +0.27 mV → 3 mA at RESET | 0.6–2.1 mV | 6 mA | 1 mA |

DC case: M1's average 10.5 A (18.4 − 3 × 2.63) plus the three 2.63 A sink returns, all to J2. Control-board current returning over the ribbon is ignored because no cable is defined, and it would add to these offsets. The INA241 ground itself is fine; its error comes from the sense taps (item 3). The ground offsets alone put ch2 and ch3 beyond the ±4% budget before the MCP6241's own ±5 mV offset is added.

**LX is capacitively coupled into the 5V plane.** The router added LX pours on In3 and In5, directly above and below the In4 5V plane. The overlap is 504 + 618 mm², or **241 pF LX→5V**, plus 596 pF LX→GND (εr 4.5, 0.186 mm). At an LX edge of 5–25 V/ns that injects 1.2–6 A of displacement current into the plane that feeds the logic and, through J10 pin 15, the control board. It also adds 0.84 nF to a switch node the simulation modelled at 1.6 nF.

## 10 · Component thermal and TO-220 mounting — **FAIL**

- **Orientation.** All ten are `TO-220-3_Horizontal_TabDown` on B.Cu, rotation 0, and the 3D model is the TabDown STEP. By KiCad's library convention TabDown puts the metal tab *against the board*. On the underside that is the opposite of tab-to-case. Confirm in the 3D viewer, and use the TabUp variant or document the lead bend.

- **Screw keep-out: none.** At every one of the ten 3.5 mm tab holes, pour copper comes to 0.20 mm from the hole edge on F.Cu, B.Cu and inner layers. Nets under a 7 mm M3 washer include GND, Vout_2, Vout_3 and m4_source. A screw isolated from the tab by a shoulder washer sits at case potential on solder mask over live copper. Top-side parts intrude too: R14 is 2.53 mm, D12 2.64 mm and R104 2.82 mm from hole centres, so even a 5.5 mm M3 head collides.

- **Spacing.** Tab pitch is 11.25 mm, leaving a 1.09 mm tab-to-tab gap (courtyards 0.76 mm). Adjacent tabs at different potentials: M2 (Vout_1) / M7 (LX), M6 (LX) / M3 (Vout_2), and M8 / M9 / M10 (three LED cathodes). A standard ~13 mm TO-220 insulator can't be fitted per device at this pitch, so it has to be one sheet per row. A 3.3 mm insulating spacer between tab and PCB is implied and isn't in the design.

- **Copper on the hot parts** (same net, pad layer, within 10 mm): M1 drain 173 mm² outer; R1 100 + 129 mm²; L1 168 + 190 mm². R7 / R52 / R53 (0.346 W each) have **4–5 mm²** on pad 1, the 0.15–0.3 mm sink-source track, and 49–72 mm² of GND on pad 2. Nearest courtyards: R1–D19 0.93 mm, R7–R47 0.70 mm, R52–R61 0.60 mm, R53–U11 0.63 mm, L1–C51 0.66 mm.

- **Underside height.** U16 (LM2940, TO-263) is up to 4.83 mm tall against the 4.6 mm TO-220 body gap plus about 0.23 mm of insulator. It would touch the case.

## 11 · PCB ↔ schematic netlist equivalence — **PASS**

**Measured** Schematic `BOOST-github/BOOST/BOOST.kicad_sch` (exported with kicad-cli) has 273 components; the power board has 121 and control 154. The only extras are J10 and J11. There are 0 value or footprint mismatches, and every schematic net maps to exactly one PCB net on each board: 0 splits, 0 merges, 0 opens. All 21 cross-board nets keep their names on both sides.

**Threshold** Exact match

**Depends on** The schematic file named above. KiCad's `.history` copy is two minutes newer (22:26 vs 22:24), which suggests an edit that may not be in the main file. Physical connectivity: refilled DRC shows 0 unconnected, and my meshes connect every power terminal. But 8 of those connections rest on a single 0.25 mm via (item 7).

## 12 · Mechanical fit, 33 × 78 × 90 mm — **FAIL**

| Element | mm | Source |
|---|---|---|
| Power outline | 74.0 × 86.0 | Edge.Cuts: fits 78 × 90 with 2 mm per side |
| Control outline | 60.0 × 60.0 | Edge.Cuts: fits |
| TO-220 body under power board + insulator | 4.60 + 0.23 | fit study; pad assumed |
| Power PCB | 1.60 | gerber job |
| L1 (unavoidably under the control card) | 19.00 | Codaca datasheet; every 60 × 60 placement inside 78 × 90 overlaps L1's courtyard x 32–65, y 33–67 |
| Clearance | 1.00 | assumed |
| Control PCB | 1.60 | gerber job |
| J9 1 × 10 2.54 mm header, unmated | 8.50 | typical part height |
| **Total** | **36.53** | vs 33 mm internal: 3.5 mm over before any mated cable |

- The fit study's 23.95 mm stack assumed a 42 × 42 control card placed clear of L1. The delivered card is 60 × 60, which cannot avoid L1.

- The control board has **no mounting holes** of any kind (its NPTH drill file is empty), so no standoff can be placed. The power board is held only by the ten TO-220 screws and the M4 lugs J1/J2.

- Other tall parts: EEH-ZU1H221P is 16.5 mm per Panasonic, not the 10.5 mm the footprint name suggests; the 680 µF cans are 12.5 mm; U16 on the underside is 4.83 mm (item 10).

## 13 · Fabrication against JLCPCB's published limits — **FAIL**

| Check | Board | JLCPCB | Result |
|---|---|---|---|
| Silkscreen text height / stroke | Power: 20 visible designators, **J4 0.80 / 0.12 mm**; the other 19 are 1.00 / 0.15. Control: J9, J11 at 1.00 / 0.15. | ≥ 1.0 mm / ≥ 0.15 mm | J4 fails both |
| Project silk rule | `min_text_height 0.8`, `min_text_thickness 0.08` | 1.0 / 0.15 | Rule set below the fab; that's why DRC passed J4 (the report named J3) |
| Track / clearance | 0.15 mm minimum track, ≥ 0.15 mm netclass clearance | 0.09 / 0.09 (1 oz); 0.15 / 0.15 (2 oz) | Pass; at the limit if 2 oz |
| Via hole / diameter | 0.25/0.45, 0.30/0.60, 0.40/0.80 (diameter − hole ≥ 0.20) | ≥ 0.15 hole; diameter ≥ hole + 0.10 | **PASS** |
| Via hole to copper | 0.333 mm minimum | 0.20 mm | **PASS** |
| PTH hole to copper | 0.329 mm minimum (J10.30) | 0.28 min, 0.35 recommended | Pass (1 below recommended) |
| PTH annular ring | 0.175 mm on 29 pads of J10 and 29 of J11; J1/J2 0.20 | ≥ 0.15 abs, 0.20 rec (1 oz); ≥ 0.254 (2 oz) | Below recommended; fails if 2 oz is ordered |
| Copper to edge | 0.30 mm rule | ≥ 0.20 mm | **PASS** |

## What the files could not settle — **NEEDS DATA**

- The copper weight that will actually be ordered. Nothing in the files states it.

- The BOM: `BOOST_BOM.xlsx` isn't in this folder, so the R1 part number, the 680 µF part (EEH-ZU1E681UP isn't on Panasonic's EEH-ZU series page) and the 2512 shunt ratings are unverified.

- HYG180N10 lead inductance (not in its datasheet), capacitor ESL (not specified by Panasonic), and whether the 8 A/ns figure survives the loop inductances found in item 4.

- TO-220 variant: if your parts are TO-220FB full-pack (isolated plastic tab), the isolation requirement changes and so does the thermal resistance.

- The inter-board cable (length, wire gauge, connectors) and the control board's position and fixing. Neither is defined, so ribbon ground resistance and inductance are unknown.

- Component temperatures: there is no enclosure-interior thermal model. I report copper areas and spacing only.

- Heights of soldered LED and battery wires on J3–J8 and the M4 lugs; L1 has no 3D model.

Method: KiCad 10.0.6 Python loads each saved board fresh, refills all zones and exports the copper geometry. A resistive mesh is solved per net (0.05–0.1 mm grid; GND 0.2 mm) with plated barrels, port reduction and field back-substitution. The three sink-source nets use an exact track-graph solve. Single-via bridges were confirmed with KiCad's own connectivity engine. Nothing in the design files was modified.

Sources: [JLCPCB PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) · [Panasonic EEH-ZU series](https://na.industrial.panasonic.com/products/capacitors/polymer-capacitors/lineup/polymer-hybrid-aluminum-electrolytic-capacitor/series/142648)
