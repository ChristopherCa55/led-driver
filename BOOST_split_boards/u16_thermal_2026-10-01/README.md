# U16 (12 V regulator) worst-case temperature, SOT-223 with ground vias (2026-10-01)

The user asked: how hot would the SOT-223 LM2940 get in the worst case with ground vias added, and what is the
largest safe continuous current? Nothing here touches the shipped boards. The SOT-223 board is the tested swap copy
from `../bom_2026-09-30/work/u16/u16test.kicad_pcb`.

## Method
- `tools/export_copper.py` (KiCad Python): every copper layer as polygons per net, plus vias and plated holes.
- `tools/raster.py`: those polygons on a 0.25 mm grid, one net id per cell per layer.
- `tools/thermal.py`: a steady-state finite-difference model with one node per cell per copper layer.
  - In-plane: copper (385 W/m-K) between cells of the same net, plus FR-4 (0.8 W/m-K) in the half dielectrics on
    each side.
  - Vertical: FR-4 at 0.3 W/m-K through the stackup in the board file (35/30 um copper, 0.109 mm prepreg, 0.25 mm
    cores).
  - Vias and plated holes: a plated barrel of 18 um copper between the layers it is flashed on.
  - Top and bottom surfaces: a heat-transfer coefficient h to the in-case air.
  - Device: a junction node joined to the cells under the tab by R_jt.
- `tools/joule.py` + `tools/run_background.py`: the DC battery current through the Vin copper (J1 lug to R1) and
  the GND copper (M1 source and the three LED shunts to J2), and the resulting heat, solved on the same grid.
- `tools/vias.py`: the via sets. `tools/add_vias.py` puts a set on a board copy and refills the zones.
- `tools/limits.py`: junction temperature and current limits from the modelled resistances.

## Checks
- Energy balance: the heat leaving both surfaces equals the heat put in (1.0000 W for 1 W).
- Grid: 0.5 mm instead of 0.25 mm changes the SOT-223 tab-to-air figure by 1 % (29.91 vs 29.58 K/W).
- Against TI's published RthetaJA (SNVS769J table 6.4, JEDEC high-K board), using my own approximation of that
  board (`tools/jedec_check.py`; its geometry is not read from JESD51-7):
  - TO-263: the model gives 29.8 K/W at h = 10 against TI's 40.9. Matching TI takes h of about 3.6 W/m2-K, so
    **h = 4 is used as the pessimistic case** and h = 10 as the nominal one.
  - SOT-223: the model gives 130-137 K/W against TI's 59.3. With so small a tab, the result depends on the test
    board's trace layout, which my approximation does not reproduce. This case is not used for calibration.
- The 27-via layout: DRC on the copy (`work/vias_around/`) has the same 71 warnings as the swap copy, 0 new and 0
  unconnected.

## Inputs (worst case unless stated)
- In-case air 75 C: the top of your own "55-75 C in-case air" (replace_notes, 2026-09-17). 55 C is shown too.
- Vin 18 V (your margin case) and 16.8 V (4S full). Vout 11.64 V (UTC minimum, so the largest drop).
- Ground current: TI's LM2940-N maximum over temperature (20 mA at light load, 60 mA at 1 A, straight line
  between). UTC gives only 15 mA max at 5 mA and 25 C.
- R_jt: SOT-223 15 K/W (UTC theta_JC); TO-263 0.8 K/W (TI RthetaJC(bot), the TI part now on the board).
- Background heat at full LED power, 18 V in (`tools/run_background.py`):
  - battery current in the copper: Vin 0.25 W, GND 0.06 W;
  - an assumed 0.1 W contact loss at each battery lug;
  - other parts from BOM values, 1.56 W in all: R7/R52/R53 0.35/0.28/0.28 W, R1 0.16 W, U17/U1 0.18/0.12 W, gate
    drivers 0.19 W.
  - Not included: L1 (winding resistance not in the files), the FETs (their tabs sit on the case), the control card.
- Loads: 50 mA (16 mA simulated board load plus the Arduino's own ~50 mA-at-5 V average through its buck) and
  120 mA (16 mA plus your 0.1 A buck-input figure).

## Thermal resistances (tab to air, K/W)
| Case | h = 10 | h = 6 | h = 4 |
|---|---|---|---|
| SOT-223, no extra vias | 29.6 | 35.5 | 42.6 |
| SOT-223 + 4 vias in the tab (virtual) | 26.3 | - | - |
| SOT-223 + 27 vias (virtual) | 25.3 | 31.2 | - |
| SOT-223 + 27 vias (real copy, DRC clean) | 25.5 | 31.5 | 38.5 |
| SOT-223 + 31 vias (needs the B.Cu 12 V track moved; virtual) | 24.0 | - | - |
| TO-263 (now) | 20.8 | 26.7 | 33.8 |

Background rise at the U16 tab (K), copper current / lug contacts / other parts: h = 10: 3.7 / 2.6 / 9.9 = 16.2;
h = 6: 5.5 / 3.7 / 18.1 = 27.3; h = 4: 7.6 / 5.1 / 28.6 = 41.3. With 75 C air and h = 10 the whole board sits at
about 97-110 C (`work/temp_sot223_vias_120mA_18V_h10.png`).

## Results, 75 C in-case air
| Case | h (W/m2K) | theta_JA (K/W) | background (K) | Tj at 50 mA, 18 V | Tj at 120 mA, 18 V | max I for Tj 125 C (18 V / 16.8 V) | max I for Tj 150 C (18 V / 16.8 V) |
|---|---|---|---|---|---|---|---|
| SOT-223, no extra vias | 10 | 44.6 | 16.2 | 123 C | 145 C | 56 mA / 73 mA | 136 mA / 169 mA |
| SOT-223 + 27 GND vias | 10 | 40.5 | 16.2 | 120 C | 140 C | 67 mA / 85 mA | 154 mA / 191 mA |
| TO-263 (now) | 10 | 21.6 | 15.9 | 106 C | 117 C | 172 mA / 213 mA | 336 mA / 412 mA |
| SOT-223, no extra vias | 6 | 50.5 | 27.3 | 138 C | 163 C | 13 mA / 19 mA | 83 mA / 104 mA |
| SOT-223 + 27 GND vias | 6 | 46.5 | 27.3 | 135 C | 158 C | 18 mA / 26 mA | 94 mA / 118 mA |
| TO-263 (now) | 6 | 27.5 | 27.0 | 122 C | 135 C | 67 mA / 86 mA | 196 mA / 242 mA |
| SOT-223, no extra vias | 4 | 57.6 | 41.3 | 157 C | 186 C | 0 mA / 0 mA | 32 mA / 43 mA |
| SOT-223 + 27 GND vias | 4 | 53.5 | 41.3 | 154 C | 181 C | 0 mA / 0 mA | 38 mA / 50 mA |
| TO-263 (now) | 4 | 34.5 | 40.9 | 141 C | 158 C | 0 mA / 0 mA | 89 mA / 112 mA |

With TI's typical ground current instead of the maximum, the SOT-223 + 27 vias at h = 10 gives 112 C at 50 mA and
131 C at 120 mA.

## Results, 55 C in-case air
| Case | h (W/m2K) | theta_JA (K/W) | background (K) | Tj at 50 mA, 18 V | Tj at 120 mA, 18 V | max I for Tj 125 C (18 V / 16.8 V) | max I for Tj 150 C (18 V / 16.8 V) |
|---|---|---|---|---|---|---|---|
| SOT-223, no extra vias | 10 | 44.6 | 16.2 | 103 C | 125 C | 120 mA / 149 mA | 199 mA / 246 mA |
| SOT-223 + 27 GND vias | 10 | 40.5 | 16.2 | 100 C | 120 C | 137 mA / 170 mA | 224 mA / 276 mA |
| TO-263 (now) | 10 | 21.6 | 15.9 | 86 C | 97 C | 303 mA / 372 mA | 467 mA / 571 mA |
| SOT-223, no extra vias | 6 | 50.5 | 27.3 | 118 C | 143 C | 69 mA / 87 mA | 138 mA / 172 mA |
| SOT-223 + 27 GND vias | 6 | 46.5 | 27.3 | 115 C | 138 C | 79 mA / 100 mA | 155 mA / 192 mA |
| TO-263 (now) | 6 | 27.5 | 27.0 | 102 C | 115 C | 170 mA / 211 mA | 299 mA / 367 mA |
| SOT-223, no extra vias | 4 | 57.6 | 41.3 | 137 C | 166 C | 20 mA / 28 mA | 81 mA / 102 mA |
| SOT-223 + 27 GND vias | 4 | 53.5 | 41.3 | 134 C | 161 C | 25 mA / 34 mA | 91 mA / 115 mA |
| TO-263 (now) | 4 | 34.5 | 40.9 | 121 C | 138 C | 68 mA / 87 mA | 170 mA / 211 mA |

## Conclusions
- The vias help little: 44.6 -> 40.5 K/W junction to air at h = 10, about 5 C at 120 mA. The large F.Cu GND pour and
  the thin 0.109 mm prepreg to In1 already spread the tab's heat; the limit is the board surface to the air.
- The SOT-223 with vias holds Tj <= 125 C up to 67 mA (18 V) / 85 mA (16.8 V) at 75 C air and h = 10; it reaches
  150 C at 154 / 191 mA. The TO-263 holds 125 C to 172 / 213 mA.
- At h = 4 nothing stays under 125 C, because the board around U16 is already at about 116 C from the other parts.
- The 27-via layout is in `work/vias_around/` (DRC: 71 warnings as before, 0 new, 0 unconnected). It is not applied
  to any shipped board.

## Correction (2026-10-01, later)
`tools/run_board.py` used 0.109 mm for the 8-layer board's two 0.218 mm (two-ply) gaps; the board file has
0.109 / 0.25 / 0.218 / 0.25 / 0.218 / 0.25 / 0.109 mm. Re-run with the real stackup
(`../power6_2026-10-01/tools/thermal6.py`): TO-263 tab-to-air 20.97 K/W (was 20.76), background 15.93 K (was 15.92).
The conclusions above stand.
