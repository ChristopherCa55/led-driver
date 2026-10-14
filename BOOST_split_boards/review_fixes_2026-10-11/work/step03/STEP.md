# Step 3: 12V route, Option A (X1 / P1, P7, P8)

User's answer: "The 12V route looks good." (DECISIONS.md X1, Option A as prototyped in work/proto/p12v_A_NOT_FOR_FAB.)

Made with `bash tools/make_step.sh work/step03 work/step02d/kicad power work/proto/p12v_A.json` (spec copied to
`specs/step03_12V_optionA.json` and `step03/spec_1.json`): text edit of the power board, then kicad-cli refill + save.
`.kicad_pro` / `.kicad_dru` unchanged; all 225 428 lines CRLF.

What changed (full list with x/y and layer: `changes.md`, from tools/pcb_diff.py):
- removed 22 12V track segments: the In4 loop round M1 (In4.Cu, x 71.95-82, y 46.15-55.25), the F.Cu jog at
  (74.75-75.35, 43.85-45.95) and the B.Cu stub at (74.55-74.75, 43.35-43.85);
- removed 3 12V vias (74.75, 43.85), (75.35, 45.95), (82.0, 48.25) and 4 Vin vias in the column x = 80.85
  (y 42.7 / 43.7 / 44.7 / 45.7);
- added one 0.4 mm B.Cu 12V track (82.0, 48.25) -> (82.0, 46.6) -> (80.85, 46.6) -> (80.85, 42.0) -> (81.45, 41.4)
  -> (81.45, 39.75) (C30's via).

Gates: ERC 0 / 0 / 0; DRC power 0 errors, the same 49 warnings, 0 unconnected, parity 0; card unchanged (1 warning);
sync 0. The DC solve first ran out of memory (9 workers while the user's KiCad and other apps held ~20 GB); it was
re-run alone with 5 workers (tools/solve_only.sh; the failed outputs are kept in solve_failed_1/).

Results (METRICS.md column step03; identical to the prototype's): Vin J1->R1 1.031 -> 1.013 mOhm, worst neck
38.8 -> 29.7 C; GND branches 1-3 % lower R; In4 GND 16 -> 15 pieces. Costs, as listed in X1 and accepted with the
route: Vin vias over their rating 4 -> 5 ((79.8, 42.7) 1.13 -> 1.28x); B.Cu GND pieces 17 -> 18 and tracks splitting
GND 35 -> 36 (the new B.Cu track); short-neck rises (GND ch2 bank 6.1 -> 7.9 C, loop GND ch2 12.1 -> 19.5 C at
0.1 mm, loop LX M1->M5 56.7 -> 57.0 C, GND ch1 bank 5.1 -> 5.7 C, GND M1 long-neck 4.5 -> 4.9 C). The short-neck
values are reported, not judged (necks under ~5 mm). Loop L unchanged 1.49 / 2.00 / 2.77 nH.

Pictures: img/step03/vin_funnel_F_after.png, vin_funnel_B_after.png, vin_map_after.png.
