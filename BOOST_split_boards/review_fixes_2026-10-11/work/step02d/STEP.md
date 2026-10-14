# Step 2: KiCad documentation fixes (final attempt "d")

Made with `python tools/step02_kicad.py work/step02d/kicad work/step02d/kicad_changes.json` on a fresh copy of
BOOST_review_fixes/KiCad (lock files and .kicad_prl left out). Text edits only; each file keeps its own line endings (main page LF; board sheets and PCBs CRLF; checked byte-wise).

What changed (full list with x/y in kicad_changes.json):
- 22 diode Values "D" -> part name (1N4148W / B5819W / BAV21W / BAT54WS) on the main page (30 units incl. repeats),
  power sheet 17, card sheet 13, power PCB 17, card PCB 13. Sim.Params model="D" kept.
- J1-J8 Values -> Vin+ / Vin- / Out1+ / Out1- / Out2+ / Out2- / Out3+ / Out3- (main page, power sheet, power PCB).
  On the power PCB the Value is shown on F.SilkS and the reference text moved to F.Fab:

  | Ref | Label | board x, y (mm) | angle | spot |
  |---|---|---|---|---|
  | J1 | Vin+  | 93.206, 80.600  | 90 | moved up clear of C4 pad 2, in line with Vin- |
  | J2 | Vin-  | 93.206, 73.933  | 90 | where "J2" was |
  | J3 | Out1+ | 44.416, 109.690 | 0  | where "J3" was |
  | J4 | Out1- | 50.916, 109.690 | 0  | above its own pad ("J4" sat above J6) |
  | J5 | Out3+ | 59.600, 113.185 | 90 | J6-J5 gap, against J5 |
  | J6 | Out3- | 56.074, 109.940 | 0  | above its own pad |
  | J7 | Out2- | 39.305, 108.323 | 0  | where "J7" was |
  | J8 | Out2+ | 32.805, 108.323 | 0  | where "J8" was |

- Main page: title block added; U26 unit 4 moved (129.54, 440.69) -> (142.24, 440.69), value under it at
  (142.24, 448.31); its three no-connect flags (121.92 -> 134.62, y 438.15 / 440.69 / 443.23).

Gates (step_checks.log): ERC 0 / 0 / 0; DRC power 49 warnings, card 1 (the same items as the baseline, none new or
gone), 0 errors, 0 unconnected, parity 0 on both; sync 0 differences. Copper export identical to the baseline
(the only change is 0.0002 mm2 of Vin In2.Cu fill, which is refill noise); card sensitive nets identical.

Earlier attempts, kept for the record: step02 (labels on the old reference spots: 3 new silk warnings, ERC 6 from
the NC flags), step02b/step02c (right spots but positions rounded to 0.01 mm, which moved J2/J3/J7/J8 by microns).

Pictures: img/step02/silk_bottom_edge_v1.png / silk_J1J2_v1.png (first try), _v3.png (these spots).
Needs the user's OK on the label pictures before it is final (FIX_PROMPT rule for new labels).
