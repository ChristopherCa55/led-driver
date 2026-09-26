# BOOST power board: driver bypass, gate links and gate loops (step 6, second pass)

2026-09-17. This answers your 2026-09-17 message (items A and B, decisions 6.1–6.5) and your follow-up on U15,
U10, VCCI and C31. Every change is placement or routing; the schematic (netlist rev3) is unchanged.

**Board:** `route_2026-09-16/BOOST_power_route_v15_NOT_FOR_FAB.kicad_pcb` (SHA-256 10f453b951f3f95d…), with
`BOOST_power_route_v15_NOT_FOR_FAB.kicad_pro` and `.kicad_dru` beside it (copies of `rules/`).
- **Starting point:** v11's power copper, plus the ten capacitor moves and three moved Vout_1 vias in §2.
- **Routing:** every signal was routed again. The moves change the space round all four drivers, so v13's routes
  could not be reused.
- **Other files:** v13 stays in the folder as handed back, and the shipped `BOOST_power.kicad_pcb` / `.kicad_pro`
  are untouched.
- **Name:** stays `NOT_FOR_FAB` until you have decided §8.

**Where things stand:**
- **Done and verified on the saved file:**
  - DRC: 0 errors, 0 unconnected, 0 exclusions, and no rule changed.
  - Netlist parity against rev3: 0 failures. In1/In6 carry GND only, In4 is one 5 V outline, and there are no untied
    islands.
  - New check: every router track and via is on the board with the net it was routed with (§7 says why).
  - **A.** All ten capacitor moves are done. **C31 is 2.8 mm from U19 pin 16 and 2.5 mm from pin 14** (your item 4).
    C90 and C89 now sit at U10's and U8's VCCI pins, with their own 5 V and GND vias.
  - **B.** Every series resistor is ≤ 5.1 mm of routed copper from its gate pin. The pull-downs and turn-off
    diodes are ≤ 6.3 mm, except D13 → M4 (26.6 mm, placement: 9.7 mm apart).
  - **6.3.** M7's and M5's returns run beside their drive paths (73 %, 82 %). M6 is at 34 %, and M2–M4 at 18 % or
    less (§4).
  - **6.4.** The datasheets confirm that 12V and analog_5V draw milliamps (§5).
- **Needs your decision (§8):**
  1. The D13 → M4 gate link crosses the In2 LX pour. It raises the LX L1→M5 resistance by 22 % (neck 57.8 →
     84.0 °C, 0.9 mm long). My recommendation is to route that one link with the current map instead: 31.0 mm, no
     hot crossing.
  2. C51 cannot be pair-linked to U15 pins 11/9, so it is tied to pins 16/14.
  3. The M6 and M2–M4 gate loops are not paired, because the router pairs by cost only.
  4. C48's 5 V side cannot have a via of its own (L1's pad is above it).

---

## 1. Final checks (from the saved file)

| Check | Result |
|---|---|
| `kicad-cli pcb drc --severity-all`, file refilled, saved, reloaded, refilled, saved | **0 errors**, **0 unconnected**; 43 warnings, the same silk warnings as v13 (20 silk overlap, 22 silk over copper, 1 J8 reference clipped by the edge) |
| DRC exclusions / rules | 0 exclusions. Board rules and `.kicad_dru` identical to v13's; silk rule 1.0 / 0.15 mm |
| Untied copper islands (`tools/plane_checks.py`) | 0; all 49 zones remove islands; every fill outline touches a pad, via, track or zone of its net |
| In1 / In6, In4, LX on In3 / In5 (`tools/layer_checks.py`) | GND only; one 5 V outline, 0 tracks; no LX: **PASS** |
| Netlist parity, `syncboard.py --check` against `BOOST_9-15_rev3.net` | 124 footprints, every library ID, value and pad net: **0 failures** |
| Router items on their routed nets (`tools/net_flips.py`, new) | 2100 of 2100 (v13 and v14 also 0 changed) |
| Stackup | JLCPCB 8 layers, 1 oz / 1 oz, 1.654 mm, in the file |
| Solver on the saved file | §6 (`work/v15_B.json`) |
| Renders | `renders_v15/v15_render_top.png`, `v15_render_bottom.png`, `v15_routes_by_layer.png` |

Routing added: 1922 track segments, 1858 mm (F 476, In2 93, In3 248, In5 375, B 666). There are 178 new vias
(124 × 0.6/0.3, 54 × 0.8/0.4), 875 on the board; 45 of the new vias sit in an SMD pad of their own net.

## 2. A: driver bypass capacitors

### 2.1 Moves (placement only; `work/bypass_moves_final.json`, applied with `tools/move_parts.py`)

| Part | Role | Was | Now |
|---|---|---|---|
| C31 1 µF | U19 VDDA/VSSA (M1's driver) | (80.81, 31.67) F | (76.03, 40.60) B, 90° |
| C48 100 nF | U19 VCCI | (56.50, 61.83) B | (62.38, 36.73) B |
| C51 100 nF | U15 VDD/VSS | (71.61, 60.38) B | (70.52, 56.90) B, 90°, beside pins 14–16 |
| C18 2.2 µF | U15 VDD/VSS | (84.17, 66.50) B | (63.70, 47.45) B, 180° |
| C50 100 nF | U10 VDDB/VSSB | (48.81, 57.25) B | (53.83, 56.48) B, the pocket below pins 9–11 |
| C16 2.2 µF | U10 VDDB/VSSB | (49.61, 59.50) B | (53.05, 58.40) B, next closest |
| C90 100 nF | U10 VCCI | (54.23, 59.08) B | (51.03, 42.98) B |
| C61 100 nF | U8 VDDB/VSSB | (81.16, 87.61) B | (78.08, 90.88) B, 180° |
| C60 2.2 µF | U8 VDDB/VSSB | (88.42, 98.41) B | (75.05, 91.35) B |
| C89 1 µF | U8 VCCI | (56.41, 68.43) B | (82.45, 104.63) B |

- **Unmoved:** D19, C86, C62 and C30. No other footprint moved (checked against v11's footprint export).
- **Vout_1 vias:** C51's pads needed room, so three Vout_1 vias at y 55.60 (x 69.90, 70.65, 71.40, the top row under
  C86.1) moved to y 55.00. The unrouted solve with the moves (`work/v14base_B.json`) shows no branch more than 2 °C or
  0.05× worse than v11.

### 2.2 Distances (pad centre to pin centre; `tools/bypass_table.py`, `work/v15_bypass_table.md`)

| IC | Supply / return pin | Capacitor | Before (mm) | Now (mm) | Target |
|---|---|---|---|---|---|
| U19 | 16 / 14 | C31 1 µF | 13.0, 12.0 | **2.8, 2.5** | ≤ 3 (item 4: as close as the board allows) |
| U19 | 3 / 4 | C48 100 nF | 23.3, 20.7 | 3.8, 4.0 | ≤ 5 (accepted) |
| U15 | 11 / 9 | C51 100 nF | 8.2, 11.1 | 5.5, 6.4 | beside pins 12–16, paired links ≤ ~5 mm (§8.2) |
| U15 | 11 / 9 | C18 2.2 µF | 19.9, 23.8 | 6.1, 6.7 | ≤ ~10 |
| U15 | 3 / 4 | C62 1 µF | 2.9, 4.8 | 2.9, 4.8 | stays |
| U10 | 11 / 9 | C50 100 nF | 6.8, 7.7 | 2.4, 3.0 | the pocket |
| U10 | 11 / 9 | C16 2.2 µF | 8.0, 7.6 | 4.8, 4.6 | next closest |
| U10 | 3 / 4 | C90 100 nF | 15.3, 13.3 | 2.1, 2.1 | 2.1 (yes) |
| U8 | 11 / 9 | C61 100 nF | 5.5, 7.5 | 2.2, 2.2 | |
| U8 | 11 / 9 | C60 2.2 µF | 11.4, 12.3 | 4.3, 3.6 | |
| U8 | 3 / 4 | C89 1 µF | 43.9, 41.6 | 2.3, 2.4 | ≤ ~5 |

These rows are now in the placement check as stage 8 "Driver bypass" (`replace_2026-09-14/tools/placement/pcheck.py`,
the old file backed up to `previous/2026-09-16/pcheck_before_bypass_rows.py`; table in `v14_distances.md`, same
placement as v15). It marks four MISSes:
- C51 to pins 11/9 (5.5 / 6.4 against 5);
- C62 to pin 4 (4.8 against 3; C62 stays, as you said);
- C50 to pin 9 (3.01 against 3, before you relaxed the 3 mm target).

### 2.3 Routed links (`tools/bypass_links.py`, `work/v15_bypass_links.json`)

The links were drawn before any other signal. They go straight to the pins and are kept out of rip-up. "Routed"
is track outside the pads; "–" means the two pads join only through their plane vias.

| Link | Net | Pad centres (mm) | Routed (mm) | Vias |
|---|---|---|---|---|
| C31.1 → U19.16 VDDA | 12V | 2.8 | 2.9 | 2 |
| C31.2 → U19.14 VSSA | GND | 2.5 | 0.9 | 0 |
| C51.1 → U15.16 VDDA | U15-VDDA | 2.4 | 1.2 | 0 |
| C51.2 → U15.14 VSSA | m2_source | 2.1 | 0.7 | 0 |
| C51.1 → U15.11 VDDB | U15-VDDA | 5.5 | 7.3 | 2 |
| C51.2 → U15.9 VSSB | m2_source | 6.4 | 36.0 (through the M7 source pour) | 4 |
| C18.1 → U15.11 VDDB | U15-VDDA | 6.1 | 7.8 | 0 |
| C18.2 → U15.9 VSSB | m2_source | 6.7 | 5.4 | 2 |
| C50.1 → U10.11 VDDB | U10-VDDA | 2.4 | 1.0 | 0 |
| C50.2 → U10.9 VSSB | m3_source | 3.0 | 1.9 | 2 |
| C16.1 → U10.11 / C16.2 → U10.9 | | 4.8 / 4.6 | 2.2 / 2.6 | 0 / 2 |
| C61.1 → U8.11 VDDB | U8-VDDA | 2.2 | 0.9 | 0 |
| C61.2 → U8.9 VSSB | m4_source | 2.2 | 1.0 | 0 |
| C60.1 → U8.11 / C60.2 → U8.9 | | 4.3 / 3.6 | 4.6 / 2.2 | 0 / 0 |
| C48.1 → U19.8 VCCI (pin 8 is shorted to pin 3 inside) | 5V | 3.8 | 3.8, via pin 6 (DT, tied to 5 V) | 0 |
| C48.2 → U19.4 GND | GND | 4.0 | – | – |
| C90.1 → U10.3 VCCI / C90.2 → U10.4 | 5V / GND | 2.1 / 2.1 | 0.8 / 0.9 | 0 / 0 |
| C89.2 → U8.3 VCCI / C89.1 → U8.4 | 5V / GND | 2.3 / 2.4 | 0.8 / 1.0 | 0 / 0 |
| C62.2 → U15.3 VCCI / C62.1 → U15.4 | 5V / GND | 2.9 / 4.8 | 1.4 / – | 0 / – |

The C31.1 link uses two vias because C31.2's GND link and U19's OUTA track occupy B.Cu between the pads.

### 2.4 VCCI capacitors' own plane vias

| Pad | Via | From the pad centre (mm) | Track (mm) | Own via |
|---|---|---|---|---|
| C48.1 5V | (65.05, 34.05), at U19.8 | 4.4 | 3.8 | **no**, through U19.6 and U19.8 |
| C48.2 GND | (62.25, 35.55) | 0.4 | 0 | yes |
| C90.1 5V / C90.2 GND | (49.95, 42.55) / (51.45, 43.35) | 0.5 / 0.5 | 0 / 0 | yes / yes |
| C89.2 5V / C89.1 GND | (83.05, 103.85) / (82.15, 106.85) | 0.8 / 2.3 | 0 / 1.5 | yes / yes |
| C62.2 5V / C62.1 GND | (56.65, 56.75) / (57.35, 58.25) | 0.5 / 1.3 | 0 / 0.8 | yes / yes |

**C48.1 (5 V) can't have a via of its own.**
- L1's F.Cu pad (rsense_lo, x 58.8–64.8, y 36.4–41.5) covers C48.1 and U19 pins 1–6, so no through via fits there.
- On B.Cu, the rsense_lo pour, C48.2 with its GND via, and U19's pad column box C48.1 in. No via is reachable
  within 4 mm.
- C48.1 therefore ties to VCCI pin 8 by way of pin 6 (DT, tied to 5 V), and U19.8 has its own 5 V via.
  - TI's pin table (SLUSCJ9F) says pin 8 "is internally shorted to pin 3".
  - Pin 3 has its own 5 V via 0.9 mm away.
- The same cramped corner forced two more orders:
  - U19.2 (GND) and U19.3 (5 V) take their plane vias first.
  - U19.4 (GND) joins GND before the 5 V links are drawn. In run r33, the 5 V link ringed U19.4 and U19.5 in, so
    they had no way to GND.
- C48.2 reaches U19.4 only through the planes: C48.2's via, then U19.4's track to the via at U19.2. The C48.1 link
  runs between them on B.Cu.
- C48's loop to pins 8/4 is therefore about 4 mm of track plus a plane hop. It carries VCCI's 1.4 mA quiescent
  current and the input-side edges, not M1's gate current (that is C31's loop).

## 3. B: gate-net links to the gate pin (`tools/gate_paths.py`, `work/v15_gate_paths.json`)

The gate nets are routed first in each gate loop, on the shortest path, with the current map ignored (your
instruction). "Routed" is track outside the pads, so it can be shorter than the pad-centre distance. Bold: over
5 mm.

| FET | Part → gate pin | Role | Routed (mm) | Pad centres (mm) | Vias |
|---|---|---|---|---|---|
| M1 | R15.2 / R104.1 | series R / pull-down to GND | 1.2 / 1.3 | 2.6 / 3.0 | 0 / 0 |
| M7 | R60.2 | series R | **5.1** | 5.2 | 0 |
| M7 | R76.2 / D2.2 | pull-down / turn-off diode | 3.5 / 1.4 | 4.8 / 2.9 | 1 / 0 |
| M5 | R59.1 / R74.2 / D22.2 | series R / pull-down / diode | 1.3 / 1.3 / 1.0 | 2.6 / 2.9 / 2.4 | 0 |
| M6 | R70.2 / R49.1 / D8.2 | series R / pull-down / diode | 3.4 / 1.1 / 1.5 | 4.2 / 2.2 / 3.1 | 0 |
| M2 | R13.1 / D11.2 | series R / diode | 4.5 / 1.5 | 4.8 / 3.2 | 0 |
| M2 | R75.2 | pull-down to m2_source | **6.3** | 5.3 | 0 |
| M3 | R23.2 / D14.2 | series R / diode | 4.0 / 1.1 | 5.3 / 2.4 | 0 |
| M3 | R61.2 | pull-down to m3_source | **5.2** | 6.9 | 0 |
| M4 | R47.1 / R73.2 | series R / pull-down | 1.1 / 2.5 | 2.2 / 3.8 | 0 / 1 |
| M4 | D13.2 | turn-off diode | **26.6** | 9.7 | 2 |
| M8 / M9 / M10 | R22.1 / R50.1 / R56.1 | series R | 1.0 / 1.1 / 1.4 | 2.4 / 2.3 / 2.9 | 0 |

- **M7's R60 (was 14.5 mm, now 5.1 mm):** now on B.Cu. The pads are 5.2 mm apart, so this is as short as
  placement allows.
- **M3's R23 (was 7.7 mm):** now 4.0 mm.
- **R75 → M2 and R61 → M3:** these are placement-limited. R61 is 6.9 mm from the gate. R75's link bends round M2's
  source pad.
- **D13 → M4 (26.6 mm):** D13 sits south-west of M4, and the straight line to the gate crosses M4's own Vout_3 via
  field and source pads. The link goes round the north side, 7.6 mm on In2 and 5.9 mm on B, through the LX and
  Vout_3 pours at up to 1.1 A/mm. That is what costs LX L1→M5 22 % (§6, §8.1).

## 4. 6.3: gate loops paired with their returns

Order as you set it: M7, M5, M6, then M2, M3, M4. For each loop, the paired leg is drawn first (driver OUT → series
R on the 5 Ω side; driver OUT → turn-off diode on the 220 Ω side, the hold-off path). The return (driver VSS pin →
that FET's own source pin) is then drawn beside the leg and the gate-net link, and may cross power copper at its
current-weighted cost. M6 and M3 are routed the other way round (return first), which gave the smaller loop in tests
(below).

"Beside" is the share of the forward path (driver → R → gate, or driver → diode → gate) whose track lies within
1.5 mm of the return on the same layer, or within 0.5 mm on the In2/In3 pair. "Yes" means at least 70 %. Loop area
is the plan-view area enclosed by forward path, gate pin → source pin and return. It ignores layer spacing, so use it
to compare loops, not to calculate inductance.

| FET | Driver → R | R → gate | Driver → diode | Diode → gate | Driver VSS → source | Paired path | Return beside | Loop area (mm²) |
|---|---|---|---|---|---|---|---|---|
| M1 (boost) | 1.5 | 1.2 | – | – | GND planes | – | – | – |
| **M7** (5 Ω) | 13.6 | 5.1 | 18.5 | 1.4 | 21.3 | driver → R → gate | **73 % (yes)** | 47.5 |
| **M5** (5 Ω) | 13.5 | 1.3 | 2.1 | 1.0 | 22.2 | driver → R → gate | **82 % (yes)** | 24.5 |
| **M6** (5 Ω) | 28.9 | 3.4 | 16.0 | 1.5 | 14.8 | driver → R → gate | 34 % (no) | 47.7 |
| M2 (220 Ω) | 25.9 | 4.5 | 30.5 | 1.5 | 19.5 | driver → diode → gate | 18 % (no) | 147.4 |
| M3 (220 Ω) | 30.3 | 4.0 | 30.1 | 1.1 | 9.9 | driver → diode → gate | 0 % (no) | 186.5 |
| M4 (220 Ω) | 32.9 | 1.1 | 4.9 | 26.6 | 16.2 | driver → diode → gate | 4 % (no) | 57.0 |
| M8 / M9 / M10 (sinks) | 17.5 / 12.5 / 2.1 | 1.0 / 1.1 / 1.4 | – | – | GND planes | – | – | – |

v13 for comparison: M7 driver → R 10.0 + R → gate 14.5 mm, M6 10.3 + 3.9, M5 13.7 + 1.3. No return ran beside a gate
track.

What was tried for the loops that do not pair, with M7 and M5 fixed (local runs to the first six loops, measured the
same way):

| M6 variant | M6 beside | M6 loop (mm²) | Side effects |
|---|---|---|---|
| Drive first (as M7/M5) | 0 % | 57.6 | the drive drops to In5 at U10.10; the return stays on B with the In6 GND plane between them |
| Drive first, via cost × 12 | 48 % | 59.8 | drive 29.2 mm, return 24.8 mm: longer, no smaller |
| Stronger attraction to the drive | 0 % | 57.6 | no effect: the drive is on another layer |
| Return first, with room kept beside it ("corridor") | 0 % | – | M7 falls to 32 %, M5 to 0 % |
| **Return first (used)** | **34 %** | **47.7** | M3 (also return first) 236 → 187 mm²; M7, M5, M2, M4 unchanged |
| Return first for M2 and M4 too | – | – | M4 57 → 112 mm², M2's return not joined: not used |

The router finds the pairing through a cost bonus beside the partner's track. Once one track changes layer, the
bonus is gone. A true pair would need both tracks routed as one object (a coupled two-track router), or hand
routing in KiCad (§8.3).

## 5. 6.4: 12V and analog_5V currents (datasheets)

| Part | Datasheet | Figure |
|---|---|---|
| UCC21520 (U19, U15, U10, U8) | TI SLUSCJ9F, §6.8 Electrical Characteristics, p. 8 | VDDA / VDDB quiescent **1.0 mA typ, 2.5 mA max** per channel; operating 2.5 / 4.2 mA per channel at 500 kHz, 100 pF load. VCCI quiescent 1.4 / 2.0 mA |
| INA241A (U25) | TI SBOSA30D, §6.5 Electrical Characteristics, p. 7 | IQ **2.5 mA typ, 3.0 mA max** at VSENSE = 0; 3.2 mA max over –40 to 125 °C |
| MCP6241 (×3) | Microchip DS21882D, DC characteristics, p. 3 | IQ **50 µA typ, 70 µA max** per amplifier |

- **12V** feeds the eight driver channels: 8 × 1.0 mA typ, 2.5 mA max. Add M1's gate charge, 24.6 nC × about
  31 kHz ≈ 0.8 mA; the channel FETs switch only at hand-over. The average is about **9 mA typ, 21 mA max**.
- **analog_5V on this board:** 2.5 + 3 × 0.05 ≈ **2.7 mA typ, 3.2 mA max** (3.4 mA over temperature).
- **Not verifiable here:** J10.19 / J10.22 take these rails to the control card, and its load is not on this board.

Both rails are in the milliamp range, so the 0.4 mm fallback widths (12V 106 of 179 mm, analog_5V 89 of 154 mm)
carry no meaningful current.

## 6. Copper solve: unrouted v14 base → v15 (1 oz, `solve_copper.py`)

The base is v11 plus the moves in §2, unrouted (`work/v14base_B.json`); v15 is `work/v15_B.json`. Rows in bold got
worse by more than 2 °C at the neck or 0.05× on the worst via. Per your step-5 rule, IPC-2221 rises are reported but
are not pass/fail for necks under about 5 mm, or for vias in plane-connected fields.

| Branch | I (A) | R (mΩ) | Neck rise °C (width mm, length mm, layer) | Worst via × rating (vias over) |
|---|---|---|---|---|
| **Vin J1->R1 (DC)** | 18.40 | 0.993 → 1.038 | 23.6 (10.04, 11.2, In3) → 38.4 (5.33, 4.5, In2) | 1.50 (4) → 1.64 (4) |
| **Vin caps->R1 (ripple)** | 9.50 | 0.310 → 0.351 | 5.0 (8.46, 5.0, In2) → 9.2 (5.63, 3.4, In2) | 0.81 (0) → 0.85 (0) |
| **rsense_lo R1->L1** | 20.70 | 0.205 → 0.220 | 20.1 (8.91, 7.0, In2) → 27.4 (6.97, 6.9, In2) | 1.33 (9) → 1.40 (9) |
| LX L1->M1 | 15.80 | 0.442 → 0.467 | 51.5 (5.87, 1.3, In2) → 52.3 (6.06, 1.2, In2) | 0.82 (0) → 0.83 (0) |
| LX L1->M7 | 7.05 | 0.457 → 0.505 | 19.6 (4.72, 0.9, In2) → 19.9 (5.50, 1.1, In2) | 0.44 (0) → 0.43 (0) |
| LX L1->M6 | 7.69 | 0.667 → 0.727 | 35.7 (5.29, 0.3, In2) → 32.8 (3.86, 0.7, In2) | 0.78 (0) → 0.79 (0) |
| **LX L1->M5** | 8.35 | 1.864 → **2.271** | 57.8 (2.48, 1.2, In2) → **84.0** (2.42, 0.9, In2) | 0.58 (0) → 0.74 (0) |
| m2/m3/m4_source | 7.05–8.35 | 0.038–0.042, unchanged | 4.0–8.6 | no vias |
| **Vout_1 M2->bank+J3** | 7.05 | 0.199 → 0.208 | 13.5 (1.76, 0.0, F) → 15.7 (3.59, 0.1, In3) | 0.85 (0) → 0.92 (0) |
| Vout_2 M3->bank+J8 | 7.69 | 0.299 → 0.307 | 7.9 → 8.3 | 0.41 → 0.40 |
| Vout_3 M4->bank+J5 | 8.35 | 0.118 → 0.119 | 4.9 → 4.9 | 0.53 → 0.54 |
| Vout_1 M2->J3 (LED DC) | 2.63 | 7.924 → 8.567 | 17.7 → 17.7 | 0.26 → 0.30 |
| Vout_2 M3->J8 (LED DC) | 2.37 | 2.968 → 3.029 | 5.5 → 5.4 | 0.11 → 0.11 |
| **Vout_3 M4->J5 (LED DC)** | 2.37 | 1.447 → 1.726 | 1.1 (5.26, 9.6, In5) → 4.6 (1.82, 1.1, In5) | 0.10 → 0.10 |
| Output1/2/3_drain, M8/M9/M10-S | 2.37–2.63 | +0.00 to +0.17 | within 1.2 °C of the base | no vias |
| **GND M1->input caps+J2** | 15.80 | 0.120 → 0.123 | 18.8 (7.48, 0.2, In1) → 20.3 (6.45, 0.1, In1) | 1.13 (1) → 1.19 (1) |
| **GND ch1 / ch2 / ch3 bank->input** | 7.05–8.35 | +22 to +37 % | 1.4–1.5 → 2.0–2.3 °C | ch1 0.65 → 0.81, ch2 0.85 → 1.04 (1), ch3 1.01 → 1.24 (1) |
| **GND R52 / R53 / R7 returns** | 2.37–2.63 | +33 to +50 % | ≤ 0.5 °C | ≤ 0.66 |

Against v13 (`work/v15_vs_v13.md`), v15 is better or equal on most branches:
- **Better:**
  - rsense_lo neck 59.0 → 27.4 °C (your 6.1);
  - the Vout_3 LED throat at U6 13.7 → 4.6 °C, 0.93 → 1.82 mm wide (your 6.2: the corridor did free up);
  - GND M1 21.9 → 20.3 °C.
- **Worse:**
  - LX L1→M5 57.5 → 84.0 °C (§8.1);
  - Vout_1 bank worst via 0.85 → 0.92×;
  - GND ch3 via 1.19 → 1.24×.

**What moved the bold rows:**
- **LX L1→M5:** the neck sits at (88.5, 87.6) on In2, where the D13 → M4 gate link crosses the LX pour that feeds M5
  (§3). The rise is 26 °C over 0.9 mm, and the resistance rises by 0.41 mΩ, about 28 mW at 8.35 A RMS.
- **rsense_lo and Vin:** the neck moved next to U19's VCCI corner, at (65.8, 35.2) on In2. Nearby are a GND
  stitching via that ties an F.Cu GND fill piece at C79/C83 to the planes, and U19.8's 5 V via. v13 had 59 °C here.
- **GND bank returns:** the plane copper loses area to the new via holes. Routing adds 178 vias in all, 17 of them
  GND (v13 added 168, 15 of them GND); the board now has 177 GND vias against v13's 175. All are in
  plane-connected fields, so per your step-5 rule the via ratios are reported but not pass/fail.

**Necks at least 5 mm long** (`--long 5`, the worst neck on each branch that stays above half its rise for at least
5 mm; `work/v14base_B_long5.json` → `work/v15_B_long5.json`):

| Branch | I (A) | base: rise °C (length mm) | v15: rise °C (length mm) |
|---|---|---|---|
| **Vin J1->R1 (DC)** | 18.40 | 23.6 (11.2) | **30.8 (5.0)** |
| **LX L1->M1** | 15.80 | 22.3 (6.1) | **29.8 (5.0)** |
| **rsense_lo R1->L1** | 20.70 | 20.1 (7.0) | **27.4 (6.9)** |
| **LX L1->M5** | 8.35 | 21.6 (15.1) | **27.0 (5.1)** |
| **LX L1->M6** | 7.69 | 16.3 (5.0) | **18.8 (5.2)** |
| Vout_1 M2->J3 (LED DC) | 2.63 | 10.2 (15.4) | 11.0 (18.8) |
| Vin caps->R1 (ripple) | 9.50 | 5.0 (5.0) | 6.7 (5.1) |
| Vout_2 M3->J8 (LED DC) | 2.37 | 5.0 (5.0) | 5.4 (5.7) |
| Output3_drain J6->M8 | 2.37 | 4.6 (10.0) | 4.6 (10.0) |
| Vout_2 M3->bank+J8 | 7.69 | 3.8 (6.3) | 3.9 (6.2) |
| LX L1->M7 | 7.05 | 2.7 (5.8) | 3.3 (7.7) |
| Vout_3 M4->J5 (LED DC) | 2.37 | 1.1 (9.6) | 2.7 (5.9) |
| GND M1->input caps+J2 | 15.80 | 1.8 (5.1) | 2.3 (5.1) |
| Output2_drain J7->M9 | 2.37 | 1.7 (6.1) | 2.2 (5.4) |
| GND ch2 bank->input | 7.69 | 1.1 (8.5) | 1.8 (5.1) |
| GND ch3 bank->input | 8.35 | 1.4 (5.0) | 1.7 (5.2) |
| GND ch1 bank->input | 7.05 | 0.9 (8.6) | 1.5 (8.8) |
| Output1_drain J4->M10 | 2.63 | 1.4 (14.4) | 1.4 (14.5) |
| Vout_3 M4->bank+J5 | 8.35 | 0.9 (5.2) | 1.0 (5.1) |
| GND R7 return | 2.37 | 0.1 (5.7) | 0.2 (5.6) |
| GND R52 return | 2.63 | 0.1 (6.7) | 0.2 (7.2) |
| GND R53 return | 2.37 | 0.1 (7.9) | 0.1 (8.0) |

Branches with no neck that long: m2_source M7->M2, m3_source M6->M3, m4_source M5->M4, Vout_1 M2->bank+J3,
M10-S M10->R52, M9-S M9->R53, M8-S M8->R7.

Five branches gain more than 2 °C on a neck this long. All five are the LX / Vin / rsense_lo copper round R1, L1 and
the FET rows, where the routes that reach U19, U10 and the gate loops have to cross. The worst single figure stays
the short LX L1→M5 neck in the table above (84.0 °C over 0.9 mm), which §8.1 addresses.

**Copper loss** over all 29 non-loop branches: base 1.006 → v15 1.097 W (v11 1.004, v13 1.089 on the same basis;
the 2026-09-16 report's 0.896 → 0.975 W used a smaller set).

**Commutation-loop copper inductance** (`tools/loop_inductance.py`):

| Channel | v11 | v13 | v14 base | v15 | Audit method v13 → v15 | Simulated |
|---|---|---|---|---|---|---|
| ch1 (M7/M2) | 0.70 | 0.73 | 0.70 | 0.73 nH | 0.82 → 0.81 | 4.85 |
| ch2 (M6/M3) | 1.13 | 1.20 | 1.13 | 1.18 nH | 1.37 → 1.36 | 12.74 |
| ch3 (M5/M4) | 1.98 | 2.04 | 1.98 | **2.08 nH** | 1.78 → **1.92** | 7.91 |

- **ch3:** the rise is the LX L1→M5 leg (1.78 → 2.14 mΩ in the loop solve), again from the D13 link.
- **Model limits:** neither method includes via barrels, pads, FET leads or the die, which the simulations'
  package models cover.

Track crossings of power copper above 0.25 A/mm (`tools/crossings.py` against the base current map):
- **Totals:** 14 runs, 47.7 mm (v13: 18 runs, 30.8 mm), plus 96 new vias in such copper (v13: 95).
- **Longest runs:**
  - GATE_M4: In2 7.6 mm and B 5.9 mm, up to 1.12 A/mm;
  - 12V: In5 7.2 mm, up to 0.84 A/mm at (77.0, 42.1), U19's VDD feed;
  - ena_out_1: In5 5.6 mm, 0.47 A/mm;
  - GATE_M2: F 3.8 mm, 0.54 A/mm.

## 7. How it was routed, and what went wrong on the way

Same pipeline as v13 (`tools/route_pipeline.sh`, current map from the unrouted base), with these changes:

- **Order:** sense nets; U19 OUTA and M1's gate; **bypass links** (§2.3); **gate loops** M7, M5, M6, M2, M3, M4 (§4);
  source nets; VCCI fan-out vias; then everything else as before.
- **Kept copper:** bypass links and fan-out vias are kept out of rip-up. In run r34, a later net ripped the C90.1 →
  U10.3 5 V link, and the pads then joined only through the plane.
- **Pad clearance:** the router now keeps 0.2 mm from every pad. DRC applies 0.2 mm to U10's NC pads, as it does to
  J10's through-hole pads.

Bugs found and fixed before v15, run by run:

| Run | Problem | Fix |
|---|---|---|
| r32 | Repair rounds re-drew the gate-loop returns on top of themselves (614 duplicate segments by round 5), which caused 3 clearance errors; plus 1 error from a via 0.19 mm from a U10 NC pad | Finished loops are left alone in repair rounds; duplicates are dropped on output; 0.2 mm pad clearance |
| r32–r33 | A "fan-out" via could land anywhere on the pad's copper island: C48.1's was 4 mm away beside U19, C90.2's 2.5 mm away | The via must reach the pad itself; the pad's own link track is not an obstacle |
| r33 | The C48 5 V link ringed U19.4/U19.5 in: 1 unconnected | U19.2, U19.3 and U19.4 get their plane connections first; C48.1 ties to pin 8 through pin 6 |
| r34 | Clean, but M6 unpaired (loop 57.6 mm²) and the C90 5 V link ripped | Return-first for M6/M3; bypass links kept (candidate kept in `work/v15_r34/`) |
| r35 | U19.3's kept 5 V route cut U19.2 off; and **KiCad silently changed the nets of router items when building the board**: a GND stub and via inside the Vout_1 bank came back as Vout_1 (DRC then saw 2 Vout_1 tracks under 1.0 mm), and a GND via became rsense_lo | U19.2 first. `add_routes.py` now checks every added item after the fills and puts back the routed net, so DRC judges the copper as routed. `tools/net_flips.py` checks a saved board against the router output: v13, v14 and v15 have no changed items |
| r36 | Clean in 3 repair rounds, no net changes | **v15** |

## 8. Needs a decision

### 8.1 D13 → M4 gate link across the LX pour
Under your "direct path even across power copper" rule, the D13 → M4.1 link is 26.6 mm round the north side of M4
(D13 is 9.7 mm from the gate, with M4's Vout_3 via field in between). It cuts the In2 LX pour that feeds M5:
- **LX L1→M5:** R 1.86 → 2.27 mΩ, neck 57.8 → 84.0 °C (2.42 mm wide, 0.9 mm long), about +28 mW;
- **ch3 loop:** 1.98 → 2.08 nH.

Options:
- **(a) Accept.** The neck is 0.9 mm long.
- **(b) Route this one link with the current map (recommended).** In a local run it is 31.0 mm with 2 vias, no track
  in copper above 0.25 A/mm, and the M4 loop is 59.7 instead of 57.0 mm². I have not solved that board yet; it
  needs another full run and solve (about 40 minutes).
- **(c) Move D13 beside R47**, east of M4 (placement). Diode → gate becomes about 2 mm, but driver → diode grows
  from 4.9 to about 33 mm, like M2 and M3, whose loops are 147–187 mm².

### 8.2 C51 cannot be pair-linked to U15 pins 11/9
C51 sits beside pins 14–16, which is the nearest legal spot (D19 and C86 not moved). A paired VDDB/VSSB link along
the pin row to pins 11/9 does not fit:
- **Tracks:** the VSSB half is m2_source, which the `.kicad_dru` requires to be ≥ 1.0 mm. The pair needs about a
  1.8 mm strip, and the strip beside pins 12–13 is limited by the Vout_1 via row of C86.1 (y 55.0).
- **Vias:** C86.1's F.Cu pad (Vout_1) covers C51, so it cannot drop to an inner layer.

C51 is linked to pins 16 (VDDA) and 14 (VSSA) instead, at 1.2 / 0.7 mm. VDDA/VDDB share Net-(U15-VDDA), and
VSSA/VSSB share m2_source. C51 reaches pin 11 over 7.3 mm, but reaches pin 9 only through the M7 source pour
(36 mm). Channel B's local cap is therefore C18 (2.2 µF): 6.1 / 6.7 mm, routed 7.8 / 5.4 mm.

Options:
- **(a) Accept.** You noted that channel B switches only at hand-over near zero current; its protection is the
  OUTB → VSSB → source loop (§4: M7 is paired at 73 %).
- **(b) Remove the top three Vout_1 vias of C86.1** (keep the bottom row) and route the pair along the pin row.
  This changes power copper you accepted, needs a Vout_1 bank solve, and I have not checked that the 1.8 mm strip
  then fits.

Relaxing the 1.0 mm source-net rule is not an option under your no-weakening rule.

### 8.3 Gate loops that do not pair (M6, M2, M3, M4)
M7 and M5 meet the 70 % mark; M6 reaches 34 %, and the 220 Ω side 0–18 % (§4).

Options:
- **(a) Accept** as routed.
- **(b) Hand-route** the four loops in KiCad: drive and return as a pair on one layer, about 25–33 mm each, crossing
  power copper where needed. Then I re-run the checks and the solve.
- **(c) A coupled pair router:** I extend `route_signals.py` to route drive and return as one two-track object. This
  is a tool build, probably most of a day, with no guarantee the pairs fit where the single tracks only just did.

### 8.4 C48's 5 V side (information; say if you want it changed)
C48.1 has no via of its own (§2.4). The alternative is placement: move C48 off L1's pad footprint, farther from
U19 than the accepted 3.8 / 4.0 mm.

## 9. Files

- **Board:** `BOOST_power_route_v15_NOT_FOR_FAB.kicad_pcb` / `.kicad_pro` / `.kicad_dru`; base
  `work/base_v14.kicad_pcb` (v11 + `work/bypass_moves_final.json` + `work/via_moves_v14.json`).
- **Checks:**
  - DRC `work/v15.drc.json`;
  - copper export `work/v15_cu.json`, footprints `work/v15_fp.json`.
- **Measurements:**
  - bypass `work/v15_bypass_table.md`, `work/v15_bypass_links.json`;
  - gate paths `work/v15_gate_paths.json`;
  - crossings `work/v15_crossings.json`;
  - route statistics `work/v15_route_stats.json`;
  - report tables `work/v15_report_tables.md`.
- **Solver:**
  - results `work/v14base_B.json` → `work/v15_B.json` (and `_long5` versions);
  - comparisons `work/v15_vs_v14base.md`, `work/v15_vs_v13.md`, `work/v14base_vs_v11.md`;
  - current map `work/v14base_jmap.npz`.
- **Router runs:** `work/r_36.json`, `g_36_1.json`, `g_36_2.json` with logs, router snapshot
  `work/route_signals_r36.py`; the board was built from `work/sig_36_3.kicad_pcb`. Earlier runs r32–r35 are in
  `work/` too.
- **Superseded:** `work/superseded_v14/` (the first board on the new base, never handed back) and `work/v15_r34/`
  (clean earlier candidate), each with a README.
- **Renders:** `renders_v15/`.
- **Tools, new or changed:**
  - new: `bypass_links.py`, `net_flips.py`, `place_bypass.py`, `move_parts.py`, `move_vias.py`,
    `export_courtyards.py`, `bypass_table.py`, `merge_routes.py`;
  - `gate_paths.py`: every gate-net pad, diode paths, forward-path pairing, loop area;
  - `add_routes.py`: net check;
  - `solve_copper.py`: `--long`;
  - `route_signals.py`: bypass links, gate loops, kept copper, fan-out and pad-clearance fixes.

Not started: step 7, the control card.
