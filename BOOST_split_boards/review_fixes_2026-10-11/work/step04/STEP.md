# Step 4: ch2 loop vias (D10 option (a))

User's answer to D10: "You can add the vias". D10 recommended option (a), ch2 only, and stated its cost (Vout_2 bank
path +1.2 %). ch1 (+3.7 % on Vout_1) and ch3 (LX L1->M5 +4 %) were not applied: their costs were not accepted.

Made with `WORKERS=5 bash tools/make_step.sh work/step04 work/step03/kicad power work/specs/step04_ch2_loop_vias.json`.

What changed (`changes.md`): two GND vias, 0.8 / 0.4 mm, through F.Cu-B.Cu, in C3.2's pad beside the existing loop
via (33.85, 67.55): (33.24, 67.25) and (34.44, 67.85). Same via type as the board's other loop vias; via-in-pad is
already used here and the order specifies Epoxy Filled & Capped vias (free at 6 layers).

Gates: ERC 0 / 0 / 0; DRC power the same 49 warnings, 0 errors, 0 unconnected, parity 0; card unchanged; sync 0.

Results (METRICS.md column step04 against step03):
- loop GND ch2 ceramics->M1: worst via 3.59x -> 1.72x its IPC rating; R 1.087 -> 0.993 mOhm; long-neck 7.3 -> 6.0 C;
  vias over their rating 3 -> 5 (the two new vias share the current and sit just over 1x; the worst one halved);
  short-neck 19.5 -> 20.1 C (0.1 mm neck: reported, not judged).
- cost (as stated in D10): Vout_2 bank path 0.312 -> 0.315 mOhm (+1 %), Vout_2 LED DC path 3.077 -> 3.082 mOhm
  (+0.2 %), loop Vout_2 0.457 -> 0.460 mOhm; the In4 Vout_2 pour gets two antipads.
- Loop inductance (loop_L6.py): 1.49 / 2.00 / 2.77 nH, unchanged at the precision it reports.

Pictures: img/step04/c3_vias_before.png, c3_vias_after.png.
