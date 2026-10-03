# Power board, 8 -> 6 layers: trial of two variants (2026-10-01)

The user asked whether the power board could go to 6 layers like the card. Both variants were built and checked on
copies; **nothing in the shipped folders was changed**. The quote selections are in `JLC_QUOTE_SELECTIONS.md`.

## The starting point
- In1 and In6 are solid GND planes with no tracks.
- In4 is a solid 5 V plane (about 10 mA), also with no tracks.
- All tracks are on F, In2, In3, In5 and B.

The two variants:
- **A: drop In4 and In6.** The layers become F, In1 (GND plane), In2, In3, In5 -> In4, B. The 5 V net is routed as
  tracks.
- **B: drop In1 and In6** (the user's idea). The layers become F, In2 -> In1, In3 -> In2, In4 (5 V plane) -> In3,
  In5 -> In4, B.

## How each was built (`work/`, tools in `tools/`)
1. **`prep8.py`** works on an 8-layer copy:
   - A: deletes the "5V plane" zone.
   - B: deletes the "GND planes" zone and the 40 vias that then connect nothing.
2. **`route6.py`** runs route_2026-09-16's router with plane landing switched off, kept out of power copper by the
   8-layer current map (`L8_jmap.npz`).
   - A: the 5 V net, 13 links. 218 track segments (186 mm, 0.4 / 0.8 mm) and 25 vias, 0 failures.
   - B: 4 GND links. 33 segments (28 mm, 0.5 mm) and 2 vias, 0 failures.
   - `add_routes.py` adds them.
3. **`make_power6.py`** (from the card's `make_card6.py`):
   - deletes the dropped planes;
   - renumbers the layers, including the vias' zone_layer_connections;
   - rewrites the layer table and the stackup.
4. **`drop_dangling.py`** removes what the DRC then reports as dangling:
   - A: 13 old 5 V plane vias, 16 In1-In6 stitching vias near J2, and one 0.85 mm 5 V stub at U19.
5. **`set_stack6.py`** sets the chosen JLC stackup (step 3 below).

**The final boards:** `work/A6/` (JLC061611-7628D, 1.583 mm) and `work/B6/` (JLC061611-1080B, 1.561 mm).
- DRC: 0 errors, 0 unconnected. The same 49 warnings as the 8-layer board.
- Parity: kicad-cli's `--schematic-parity` cannot fetch this split project's netlist (it reports an empty list), so
  parity was checked with `replace_2026-09-14/tools/placement/syncboard.py --check` against a fresh netlist of the
  current schematic and the 2026-09-29 precharge assignment. A6 and B6 each give 1 failure, the G*** logo, exactly as
  the 8-layer board does.
- All 135 footprints are unchanged.
- The tracks and vias are exactly the 8-layer ones, plus the routes, minus the removed dangling items:
  - A: 2020 tracks, 868 vias;
  - B: 1836 tracks, 834 vias;
  - the 8-layer board: 1803 tracks, 872 vias.

## Checks (the same tools on the 8-layer board, so each comparison is like for like)

| Check | 8-layer (now) | A: drop In4 + In6 | B: drop In1 + In6 |
|---|---|---|---|
| Bare PCB, 5 pcs (ENIG, TG155, 1 oz inner) | $124.10 | **$69.57** | $69.57 |
| Stackup | JLC 8L, 1.654 mm | JLC061611-7628D, 1.583 mm | JLC061611-1080B, 1.561 mm |
| Extra layout | - | 5 V as tracks: 186 mm, 25 vias | 4 GND links: 28 mm, 2 vias |
| Power paths (Vin, rsense_lo, LX, Vout, drains): IPC long-neck rises | baseline | within about 1 C | within 1 C, except rsense_lo 25 -> 34 C |
| GND paths: resistance | 0.13-0.59 mOhm | 1.3-1.8x | 2-20x (about 5 mOhm) |
| GND bank -> input returns (7-8 A of switching current): long-neck rise | 1.8-2.1 C | 7.6-10.2 C | 123-144 C |
| GND M1 -> input caps + J2 (15.8 A): long-neck rise | 9.4 C | 13.8 C | 21.8 C |
| Commutation loop copper inductance, ch1 / ch2 / ch3 | 0.86 / 1.38 / 2.26 nH | 1.40 / 2.04 / 2.70 nH | 3.32 / 3.36 / 6.80 nH |
| M1 turn-off, nominal: die Vds / LX / TVS average / dead-time minimum | 67.6 V / 60.8 V / 10.0 mW / 41.0 ns | 67.6 V / 60.9 V / 11.5 mW / 41.1 ns | 67.7 V / 61.4 V / 19.7 mW / 40.7 ns |
| M1 turn-off, 1.0 V corner | 64.7 V / 59.4 V / 1.7 mW / 18.6 ns | 65.0 V / 59.7 V / 1.7 mW / 18.6 ns | 66.0 V / 60.5 V / 3.7 mW / 18.7 ns |
| Signal track over GND on an adjacent layer: all (gate) | 82 % (72 %) | 47 % (34 %) | 29 % (11 %) |
| Sense nets (SNS_CH, ISNS, Current, IREF) over GND | 94 % | 71 % | 38 % (ISNS pair 0 %) |
| M1 gate loop: drive-to-GND vertical distance | 0.05 mm | 0.38 mm | 0.53 mm |
| U16 (MC7812): Tj at 120 mA, 18 V, 75 C air, h = 10 | 115 C | 119 C | 122 C |

### Method notes
- **The stackup choice.** `loop_L6.py` computed the loop inductance for all 24 JLC 6-layer 1 oz builds, and the
  lowest sum was taken:
  - A: 7628D (6.15 nH; 1080B 6.72, 2116B 6.92);
  - B: 1080B (13.48 nH; all 24 lie between 13.5 and 15.3).
- **The inductance method.** It is the over-plane method of `route_2026-09-16/tools/loop_inductance.py`, with a
  per-cell height to the nearest GND copper. GND copper within 1 mm counts, so the return flows round the antipads.
  - On the 8-layer board this gives 0.86 / 1.38 / 2.26 nH, against 0.72 / 1.17 / 2.04 by the fixed-plane method.
  - Sensitivity on the 8-layer board: 0 mm gives 2.23 / 3.33 / 3.86 nH; 0.5 mm gives 1.04 / 1.69 / 2.39 nH.
- **The M1 runs.** They are `sim_m1_2026-09-24/m1_routed_*.net` with only Lcu_ch1-3 changed (`sim_m1/`). The value is
  the routed copper times the variant / 8-layer ratio, plus 1.0 nH for barrels:
  - A: 2.19 / 2.73 / 3.44 nH;
  - B: 3.82 / 3.85 / 7.14 nH;
  - the 8-layer board: 1.73 / 2.17 / 3.04 nH.
  - These are rev5 netlists, as on 2026-09-24, and the gate-loop change is not in them.
- **The IPC rises.** `tools/solve_copper6.py` is a copy of solve_copper.py with the layer list read from the export.
  The "GND bank -> input" branches carry the inductor's switching current, so their DC rise is an upper bound.
- **U16.** It uses `tools/thermal6.py` with the u16 study's model and inputs: MC7812 R_jc 5 K/W, 8 mA bias, 11.4 V
  minimum out. The u16 study had used 0.109 mm for the 8-layer board's two 0.218 mm gaps; the corrected 8-layer
  figure is 20.97 K/W tab-to-air (20.76 before), so its conclusions stand.

## Reading it
- **B is not viable as built.** With no solid GND plane, the GND network becomes about 5 mOhm, the commutation loops
  are 2.4-3.9x today's, the R1 Kelvin pair loses all GND underneath, and U16 runs hotter. It would need GND re-planned
  (in effect a re-layout).
- **A is workable on the power stage.**
  - The extra loop inductance moves M1's turn-off by 0-0.3 V, with the TVS at 1.7-11.5 mW.
  - The DC paths are unchanged, and the GND paths are about 1.5x.
  - U16 is about 3.5 C warmer.
- **What A gives up:**
  - **The bottom side loses its GND reference.** Signal track over GND falls from 82 % to 47 % (B.Cu 93 % -> 22 %,
    where the gate drivers sit), and the sense nets fall from 94 % to 71 %. This is noise and EMI margin that none
    of these checks quantify.
  - **The 5 V rail becomes 186 mm of track** instead of a plane.
- **The saving:** $54.53 per order of 5 boards (bare PCB). Assembly is unchanged.

## Applied: variant A moved into the three folders (2026-10-01, 22:40)
The user chose A, and asked to move it in first so they can hand-improve the pours before any further work.
- **Backups.** The 8-layer boards (a63e8a0e) and BOOST_package's `.kicad_prl` are in
  `previous/2026-10-01/before_power_6layer/<folder>/KiCad/`.
- **The move.** `work/A6/BOOST_power_RC2.kicad_pcb` (e43c56c1) was copied to BOOST_package, BOOST_schematic_cleanup
  and BOOST_stuff. The `.kicad_pro`, `.kicad_dru` and schematic are byte-identical to A6's, so they were left alone.
- **Checks in place.**
  - DRC: 0 errors, 0 unconnected, and the same 49 warnings.
  - Parity (syncboard): only the logo.
  - No files were added beside the boards.
- **Not yet done:** the gerbers, fab drawing, STEP, cost files, xlsx, ORDER_CHECKLIST and BUILD_NOTES. Those in
  BOOST_package are still the 8-layer ones. They get regenerated once the pours and vias are final.

### GND vias on the 6-layer board (read only; `gnd_via_layers.py` in the session scratchpad)
- There are 157 GND vias. Every via reaches In1, and the number of copper layers each connects to is:

  | Layers | 1 | 2 | 3 | 4 | 5 | 6 |
  |---|---|---|---|---|---|---|
  | Vias | 5 | 20 | 49 | 22 | 31 | 30 |

- **Missed layers:** In2 102, In4 95, In3 62, B 62, F 6.
  - 314 of the 327 missed connections are where a higher-priority Vin / LX / Vout pour owns that layer at the via.
  - 13 are where a GND pour exists but its fill is blocked locally:
    - In3: (58.50-61.90, 66.25), five vias;
    - In2 and In3: (36.30, 63.85) and (37.00, 63.85);
    - B: (94.20, 70.30), (94.20, 71.42), (100.15, 95.30) and (100.15, 96.35).
- KiCad already connects a GND via to every GND fill that reaches it. `remove_unused_layers` only hides the rings on
  the other layers.

## 2026-10-02: the user's GND pour edits (BOOST_stuff, board d62b79f5), checked on the copy `work/U1`
`tools/check_variant.sh` ran the checks; the results are in `work/U1_*` and `heatmap/U1_edited_*`. BOOST_package and
BOOST_schematic_cleanup still hold e43c56c1 (not synced).

**What changed** (`work/U1_detail.txt`, from `tools/edit_detail.py`):
- **New pours.** Four zones of their own nets around the via arrays: Vin x2, rsense_lo and Vout_2. They span all 6
  layers, or In1 only, and use the default thermal-relief pad connection. Those arrays now flash on every layer.
- **Vias removed:** 4 LX at x = 75.7, 4 Vin, 3 Vout_3, 3 GND near (50, 67). The rsense_lo array was re-spaced from 7
  vias to 6.
- **Vias added:** 5 GND at x = 93.4, y = 53.5-61.1, and 3 GND near y = 113.6.
- **B.Cu:**
  - The GND M1.3 zones merged (88 -> 93 mm2), and the Vout_1 zone under M2 shrank (160 -> 63 mm2).
  - Signal track was rerouted, about 530 mm removed and 550 mm added on all layers (mostly on B.Cu), and R70 moved
    0.3 mm.
  - B.Cu GND grew by 62 mm2; In1 GND fell by 30 mm2.

**Electrical checks:**
- DRC 0/0, with the same 49 warnings.
- Parity is logo only.
- None of the new pours has a piece without a via or pad.

**Copper solve:** U1 against A6 and L8; R in mOhm / long-neck C.

| Branch | L8 | A6 | U1 |
|---|---|---|---|
| Vin J1->R1 | 1.038 / 38.5 | 1.020 / 39.6 | 1.028 / 39.0 |
| rsense_lo R1->L1 | 0.216 / 25.0 | 0.227 / 26.2 | 0.228 / 24.1 |
| LX L1->M1 | 0.495 / 38.0 | 0.496 / 38.8 | 0.462 / 30.0 |
| LX L1->M6 | 0.745 / 28.3 | 0.758 / 26.6 | 0.729 / 21.4 |
| GND M1->input caps+J2 | 0.128 / 9.4 | 0.168 / 13.8 | 0.150 / 5.9 (vias over rating 2 -> 0) |
| GND ch1 / ch2 / ch3 bank->input | 2.0 / 2.1 / 1.8 C | 8.0 / 10.2 / 7.6 C | 4.9 / 6.0 / 5.1 C |
| GND R52 / R53 / R7 return | 0.454 / 0.592 / 0.544 | 0.769 / 0.955 / 0.883 | 0.746 / 0.937 / 0.865 |
| Loop GND ch1 / ch2 / ch3 ceramics->M1, R | 0.688 / 0.792 / 0.572 | 1.204 / 1.278 / 0.949 | 1.087 / 1.167 / 0.927 |
| Commutation loop L, ch1 / ch2 / ch3 (nH) | 0.86 / 1.38 / 2.26 | 1.40 / 2.04 / 2.70 | 1.38 / 2.00 / 2.71 |

- All other branches are within about 1 %.
- The known Vout_3 ceramics-loop via overload at (92.8, 86.4) is unchanged (2.8x; it was 2.9x on the 8-layer board).
- **The power-via pours did not lower the Vin or rsense_lo resistance.** A via gains from a layer only where that
  layer's copper continues somewhere, and the In1 patches only join the vias to each other.
- **The GND gains come from the B.Cu GND around M1 and the x = 93.4 vias.**

**Signal over GND:** 47 % -> 48 % (gate 34 % -> 31 %, as the gate track grew from 85 to 92 mm). GND vias missing B.Cu:
62 -> 28.

## GND heatmap (`tools/gnd_heatmap.py`, `heatmap/`)
- **The model:** full-load DC. The currents enter at M1.3 (11.03 A) and at the GND ends of R52 / R53 / R7 (2.63 /
  2.37 / 2.37 A), and leave at J2.1 (0 V). The solve is solve_copper6's grid and barrel model.
- **The result:** the highest GND voltage is 8.25 mV on A6 and 8.15 mV on U1.
  - The drop is spread over the right side of the board: 1.3 mV within 5 mm of J2, 3.3 within 10 mm, 6.1 within 20.
  - Near J2, In2-In4 are Vin/LX pours, so only F, In1 and B carry GND there, and they are already stitched together.
  - Adding the 10 best via spots that cut no power pour lowers the maximum by only 0.05 mV. The stronger spots
    (1.1-2.2 mV across their layers) all cut the Vin/LX pours near J2.
- **What it means for the circuit.** The LED current loops compare the top of each 50 mOhm sense resistor with IREF
  from the control card (via J10). The error is therefore the sense resistor's GND end minus the card's GND (the mean
  of J10's GND pins).

  | | R52 | R53 | R7 |
  |---|---|---|---|
  | Offset (mV) | 0.67 | 1.15 | 0.78 |
  | Share of the 118-132 mV sense signal | 0.5 % | 1.0 % | 0.65 % |

  The LEDs run that much below their set current at full load. This is the same on A6 and U1.
- J10's own GND pins span 6.5-7.3 mV, so a little power-board return current shares the card's GND through the
  connector.
- **The 8-layer board for comparison** (`heatmap/L8_reference_*`, the same model):
  - The highest GND voltage is 4.87 mV, against 8.15-8.25 mV on 6 layers.
  - The drop within 5 / 10 / 20 mm of J2 is 0.8 / 1.8 / 3.5 mV, against 1.3 / 3.3 / 6.1 mV.
  - The LED sense offsets to the card's GND are 0.46 / 0.82 / 0.56 mV (0.35-0.7 %), against 0.67 / 1.15 / 0.78 mV
    (0.5-1.0 %).
  - So the 6-layer board costs about 0.3 percentage points of LED current accuracy at full load.

## 2026-10-02 (afternoon): the user's second edit (BOOST_stuff, board 256a68d5), checked on `work/U2`
**Electrical checks:**
- DRC 0/0, with the same 49 warnings.
- Parity is logo only.

**What changed** against U1 (`work/U2_detail_vs_U1.txt`, `work/U2_area_vs_U1.txt`):
- **122 GND vias added:** 100 small (0.3 / 0.5) and 22 standard, mostly at x = 30-50, y = 30-50. There are now 279
  GND vias, 139 of them on all 6 layers.
- **4 GND vias removed** at x = 79.65, y = 52.8-55.2 (by M1), with new ones near x = 79.0-79.6.
- **A new GND patch on In2** at M1 (75.7-79.9, 49.6-53.8; priority 32, above LX In2's 28). It takes 12 mm2 out of the
  LX plane.
- **Zone priorities were renumbered** (by KiCad's zone manager), but no fill changed beyond these areas.
- A 12 V track on In4 was rerouted.

**Copper solve** (R mOhm / long-neck C):

| Branch | L8 | U1 | U2 |
|---|---|---|---|
| LX L1->M1 | 0.495 / 38.0 | 0.462 / 30.0 | **0.501 / 40.9** (worst neck on In2 at (77.7, 48.4), beside the new patch) |
| LX L1->M5 | 2.017 / 26.9 | 1.990 / 24.9 | 2.010 / 28.2 |
| Output1_drain J4->M10 | 1.787 / 3.9 | 1.752 / 3.8 | 1.968 / 3.8 (new small vias in its B pour) |
| Output2_drain J7->M9 | 2.733 / 3.3 | 2.733 / 3.3 | 2.868 / 3.5 |
| GND M1->input caps+J2 | 0.128 / 9.4 | 0.150 / 5.9 | 0.142 / 4.9 |
| GND ch1 / ch2 / ch3 bank->input | 0.249 / 0.433 / 0.251 | 0.389 / 0.711 / 0.450 | 0.378 / 0.686 / 0.443 |
| GND R52 / R53 / R7 return | 0.454 / 0.592 / 0.544 | 0.746 / 0.937 / 0.865 | 0.726 / 0.905 / 0.847 |
| Loop L ch1 / ch2 / ch3 (nH) | 0.86 / 1.38 / 2.26 | 1.38 / 2.00 / 2.71 | 1.49 / 2.07 / 2.80 |

**GND heatmap** (`heatmap/U2_*`):
- The maximum is 8.06 mV (U1 8.15, A6 8.25, L8 4.87).
- The drop within 5 / 10 / 20 mm of J2 is 1.27 / 3.26 / 6.09 mV.
- The LED sense offsets to the card's GND are 0.65 / 1.10 / 0.76 mV (0.50 / 0.93 / 0.64 %).
- The 122 new vias lowered the maximum by 0.09 mV, as the U1 map predicted.
- The remaining gap to the 8-layer board is set by the layer count near J2, where In2-In4 are Vin/LX on 6 layers
  but there were GND layers on 8. No via placement closes it.

## 2026-10-02 (evening): the third edit (BOOST_stuff, board 4ee5c427), checked on `work/U3`
**Electrical checks:**
- DRC 0/0, with the same 49 warnings.
- Parity is logo only.

**What changed** against U2 (`work/U3_detail_vs_U2.txt`):
- The In2 GND patch at M1 shrank from 13.0 to 8.5 mm2 (now 76.2-79.8, 50.3-53.4).
- 2 LX vias were added at (80.0, 48.2) and (80.0, 49.2), and the LX B D19-M1 zone was extended to x = 80.2.
- A 12 V via moved from x = 80.95 to 82.0, with its track rerouted.
- GND vias: three removed, at (48.8, 67.1), (76.8, 50.0) and (79.6, 50.8), and one added at (79.6, 51.0).

**Copper solve:**
- **LX L1->M1** is 0.474 mOhm with a 29.2 C long-neck rise. It was 40.9 C on U2, 30.0 on U1 and 38.0 on L8.
- **GND M1->input caps+J2** is 0.147 mOhm / 4.6 C, with no vias over rating.
- **The other GND branches** are within 1 % of U2.
- **Output1/2_drain** are unchanged from U2 (+12 / +5 % against U1; under 4 C).
- **Loop L** is 1.42 / 2.00 / 2.75 nH.

**GND heatmap:**
- The maximum is 8.08 mV.
- The LED sense offsets are 0.65 / 1.11 / 0.76 mV (0.50 / 0.93 / 0.64 %).

**Verdict:** U3 is the best 6-layer version so far.

### Readiness review of U3 (2026-10-02)
**U16 (MC7812)** (`work/U3_th.json`, refilled copy `work/U3th`):
- Tab-to-air is 23.65 K/W, against 24.61 on A6 and 20.97 on L8.
- The background rise is 16.05 K.
- Tj at 120 mA, 18 V and 75 C air is about 118 C (A6 119, L8 115; limit 125).

**The M2 gate drive** (Net-(D11-) and GATE_M2, with m2_source as its return):
- 63 % of its 42 mm has no m2_source copper within 1 mm, against 38 % on L8 and A6.
- The user's B.Cu reroute of Net-(D11-) at (68.5, 61.8) -> (80.2, 71.2), and of GATE_M2 near (73-80, 68-72), took
  it away from its return.
- The other gate loops are as on A6.

**Sense nets over GND:**
- 74 % overall (A6 71 %, L8 94 %).
- SNS_CH3 is 83 % (it was 45 %), Current 63 %, ISNS_N 64 % (its pair ISNS_P is 100 %) and IREF3_input 44 %.

**Switching-loop vias over IPC rating:**
- Loop GND ch2 at (33.9, 67.5) is 3.6x, ch3 at (88.9, 84.6) 2.7x and ch1 at (73.4, 66.0) 2.1x.
- Loop Vout_3 at (92.8, 86.4) is 2.8x.
- All of these were the same on L8 (3.6x / 2.6x / 2.1x / 2.9x). They are plane-connected, so they are reported,
  not judged. They are the best spots for extra vias.

**Before ordering:**
- Regenerate the fab package for 6 layers: gerbers, drill, fab drawing with the stackup, STEP and CPL. R70 moved
  0.3 mm, so the CPL changes; the BOM does not.
- Sync the board to the other two folders.
- Update the cost files and ORDER_CHECKLIST: 6 layers, JLC061611-7628D, $69.57.

## 2026-10-02 (night): the fourth save and the M2 gate reroute
**The user's 20:29 save** (2bdf491b, `work/U4`; diff against U3 in `work/U4_detail_vs_U3.txt`):
- DRC 0/0 with the 49 warnings; parity is logo only.
- Changes:
  - GATE_M2 rerouted on F.Cu, and the M7 drive (GATE_M7, Net-(D2-)) and the m2_source return track reworked.
  - A new LX zone on In3 + In4 at (72.2-79.1, 55.2-62.0), priority 51, with 3 LX vias moved to x = 73.7. This cut
    the Vout_1 In3 outline from 579 to 509 mm2.
- **The M2 drive was still 64 % unreturned**, because the B.Cu diagonal of Net-(D11-) was unchanged.

**The reroute** (`tools/patch_m2_drive.py`, applied at the user's request with KiCad closed):
- The diagonal was replaced by a 0.4 mm route: y = 62.1, a step to y = 62.525 (0.275 mm to both the m2_source
  track and the GND via at (75.1, 63.3); the rule is 0.25), then down x = 76.0 beside M2.
- It was refilled with kicad-cli; `.kicad_pro` was unchanged.
- DRC 0/0 with the 49 warnings; parity is logo only.
- `edit_detail` shows only Net-(D11-) changed: 9 segments out, 5 in.
- The M2 drive is now 42 % unreturned (A6 and L8: 38 %).
- **BOOST_stuff now holds b6d7bb9a** (= `work/U5`). The 20:29 file is in
  `previous/2026-10-02/before_m2_reroute/BOOST_stuff/KiCad/`.

**The final-board solve, `work/U5`** (BOOST_stuff b6d7bb9a = U4 + the M2 reroute):
- **The new LX In3/In4 pour helps.**
  - LX L1->M7 goes from 0.514 to 0.462 mOhm and its long-neck rise from 12.2 to 5.5 C.
  - Loop LX M1->M7 goes from 0.504 to 0.462 mOhm and its neck from 15.3 to 7.5 C.
  - Vout_1 is unchanged (0.219 mOhm; LED DC 8.459 mOhm).
- Everything else is within 1 % of U3.
- Loop L is 1.50 / 2.00 / 2.77 nH (ch1 is +0.08 against U3).
- The GND heatmap maximum is 8.09 mV.
- Signal over GND is 47 %; gate track over GND is 27 %.
- **M7 gate drive** (Net-(D2-) and GATE_M7, return m2_source): 52 % unreturned, against 34 % on L8, A6 and U3.
  - The 20:29 save straightened the R60.1 -> D2.1 link to y = 58.3, on B.Cu and In4. U3 had it on In4, dipping to
    y = 60.3 beside the m2_source track at y = 60.85.
  - The LX vias moved to (73.7, 57.5 / 59.1) and (73.78, 59.85) now block that corridor. Restoring the return needs
    the via at (73.78, 59.85) moved or removed; then a 0.3 mm B.Cu route along y = 59.925 fits (0.275 mm each side).

**The M7 reroute** (`tools/patch_m7_drive.py`, at the user's request; copy `work/U6`):
- **What was removed:** the LX via at (73.78, 59.85) (no tracks; flashed F/In2/In3/In4), the straight R60.1 -> D2.1
  link along y = 58.3 on B.Cu and In4, and its two Net-(D2-) vias.
- **What was added:** a 0.3 mm B.Cu route along y = 59.8, continuing the user's y = 59.85 track, then up into D2.1.
  It has 0.35 mm to the LX via hole at (73.7, 59.1) and 0.40 mm to the m2_source track.
- **Checks:**
  - Refilled with kicad-cli; `.kicad_pro` unchanged.
  - DRC 0/0 with the 49 warnings; parity is logo only.
  - `edit_detail` shows only these items changed.
- **Results:**
  - The M7 drive is now 38 % unreturned (L8 / A6 / U3: 34 %; U5: 52 %); M2 is still 42 %.
  - **LX did not suffer; it improved slightly**, because the In4 link no longer splits the new LX In4 pour.
    - LX L1->M7: 0.462 -> 0.449 mOhm, long-neck 5.5 C.
    - Loop LX M1->M7: 0.462 -> 0.451 mOhm, neck 7.0 C.
    - LX L1->M1: 0.471 mOhm / 29.3 C.
  - Loop L is 1.49 / 2.00 / 2.77 nH.
  - The GND branches are unchanged.
- **BOOST_stuff now holds e3e92c26** (= `work/U6`). The previous file (b6d7bb9a) is in
  `previous/2026-10-02/before_m7_reroute/`.

## Released 2026-10-02
- **The board:** e3e92c26 (= `work/U6`) is in BOOST_package, BOOST_schematic_cleanup and BOOST_stuff. The previous
  boards are in `previous/2026-10-02/`.
- **The fab package:** `../fab_2026-10-02/`, with the gerbers and the fab drawing (stackup JLC061611-7628D).
- **The 3D model:** `../assembly_3d_2026-09-30/` (BOOST_assembly_2026-10-02.step).
- **The costs:** `../bom_2026-09-30/` (total $600.61).
- **ORDER_CHECKLIST:** 6 layers, "Specify Stackup: Yes -> JLC061611-7628D", TG155 and ENIG reminders, $274.36 for
  the power order, and a JLC DFM check before paying.
