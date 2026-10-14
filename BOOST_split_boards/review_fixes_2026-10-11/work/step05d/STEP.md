# Step 5: I2C pull-ups (D1) and U26 address pull-downs 1k (D2)

User's answers: "Yes, you can add the pullups to the control card." and "you can change the r99 and r102 to 1k if
you think that is better".

**Status: built and gated, NOT promoted.** It waits for the user's OK on four points (below).

## What changed
- **LTspice** (`work/step05_lt`, then `work/step05b_lt` = the candidate): R99 / R102 10k -> 1k; R106 / R107 4.7k from
  5V to SCL / SDA, drawn left of U26E (each with a 5V flag above and its SCL / SDA flag below); the note "I2C pull-ups
  (U26 has none)" at (-6480, -6480). 5b adds `solver=alt` to the `.options` line (see below).
- **KiCad schematics** (main page and card sheet, `sch_changes.json`): the same values; R106 / R107 with 5V / SCL / SDA
  global labels left of U26E; the note "I2C pull-ups / (U26 has none)". Footprint field R_0402_1005Metric.
- **Card PCB** (`changes.md`): R99 / R102 Value and Sim.Params 1k; R106 0402 on B.Cu at (53.2, 84.5) between U104 and
  U26 (courtyard margins 0.03 / 0.04 / 0.23 mm); R107 0402 on B.Cu at (60.0, 106.6) under J9; 13 track segments and
  4 vias routed by tools/route_new.py (SCL on B.Cu into U26.5; SDA via In2 onto the end of its In1 track at
  (59.975, 100.075); each 5V pad to a via into the In2 5V pour).
- **Fab files** (`fab/`, not in the copy yet): R99 / R102 join the card's existing 1k line (C21190); new line
  0402WGF4701TCE, R106 / R107, C25900 (JLC basic, 14.6 M in stock, $0.0027, read 2026-10-11); CPL rows for R106 / R107.

## Gates
- ERC 0 / 0 / 0; sync 0 differences (326 units on the main page, card sheet 200; sync via tools/sync_check_rf.py,
  which adds R106 / R107 to the 2026-09-30 part -> board assignment in memory only).
- DRC: card 0 errors, the 1 baseline warning, 0 unconnected, parity 0; power unchanged (byte-identical to step 4).
- LTspice equivalence (`work/step05b_lt/ltspice_equiv.txt`): E1 netlist PASS (R106 / R107 additions and R99 / R102
  values approved in approved_changes.json from the user's D1 / D2 words), E2 / E4 / E5 PASS, **E3 FAIL only on the
  `.options` line** (solver=alt is not approved yet).
- Simulation (`work/sims/*.out`): every .meas value equals the shipped file's within solver noise (LED currents equal to
  1e-8 A; Ptvs 25-30 ms 9.48 -> 9.50 mW).

## Waiting for the user's OK
1. **0402 instead of 0603 for R106 / R107.** No 0603 spot near SCL / SDA is free, outside the H1-H4 washer keepouts and
   routable without new tracks on a GND layer (`img/step05/card_free_*.png`). 0402 adds one unique part to the card
   order (about $1.53 loading). An 0603 pair would need C93 (Vref_2's 10 uF, under J9) moved and re-wired.
2. **B.Cu GND fill near U26:** R106's SCL and 5V tracks fence off two small B.Cu GND pieces (26.9 mm2 under U26 with
   R99.2 / U26.20 and 3 vias; 14.2 mm2 at U104.7 / U26.7 with 2 vias). Both stay stitched to the inner GND planes by
   their vias. Largest B.Cu GND piece 362 -> 315 mm2; B.Cu GND pieces 18 -> 20.
3. **Smaller costs:** the SCL B.Cu track crosses an In4 plane gap for 2.2 mm at (54.1, 84.15); SDA's In2 track slots
   the 5V pour (3.0 mm, detour 8.8 mm); one more short segment (2600 -> 2601).
4. **LTspice: `.options ... solver=alt`.** With R106 / R107 in the netlist the normal solver stops at 0.3216 ms ("Time
   step too small" at m7:di; listing them first gives m1:di at the same time). The values-only change runs normally.
   solver=alt runs it to 30 ms with the same results, but about 3x slower (990-2811 s here against 341 s). The file's
   own note already gives solver=alt for dimming-run stalls. Alternative: leave R106 / R107 out of the LTspice file
   (the MCP4451 model does not model the bus) and keep them on the KiCad schematics only.

Pictures: img/step05/i2c_area_after_preview.png (LTspice), main_U26E_final.png, card_U26E_final.png,
card_R106_B_final.png, card_R107_B_final.png, card_SDA_In2_final.png.
Earlier attempts kept for the record: step05 (silk warning), step05b (courtyard error), step05c (7 short segments).
