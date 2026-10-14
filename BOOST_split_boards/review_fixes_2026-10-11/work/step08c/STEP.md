# Steps 7e and 8c: the approved card steps 7 and 8, rebuilt on step 5g's card (2026-10-13)

The user approved steps 7 and 8 on 2026-10-12 ("Everything else looks fine - i approve them"). They were first built on
step 5's 0402 card (step07d, step08b); these rebuild them, unchanged, on step 5g (the 0603 pull-ups, which still wait
for the placement-picture OK). **Not promoted.**

## Commands (from RF)
```
NO_CHECKS=1 bash tools/make_step.sh work/step07e work/step05g/kicad control work/specs/step07d_stitch_vias.json
bash tools/card_checks.sh work/step07e work/step06b
NO_CHECKS=1 bash tools/make_step.sh work/step08c work/step07e/kicad control work/specs/step08_u101ay_to_In2.json
bash tools/card_checks.sh work/step08c work/step06b
```

## What changed
- **Step 7e** (card PCB `7bc4dd9b`): two free GND stitching vias 0.5 / 0.3 at (72.34, 84.823) and (74.34, 85.673) in
  the In1 piece at (73.2, 86.9) that had one via (`remove_unused`: no lone pads).
- **Step 8c** (card PCB `0260b4c8`): Net-(U101A-Y) (U101.3 -> R4.2) leaves In1 (14 segments removed) and runs on In2
  between the same vias (51.675, 75.175) and (55.125, 87.925): (52.25, 75.75) - (52.25, 82.85) - (54.95, 85.55) -
  (54.95, 87.7).

## Gates (each step)
ERC 0 / 0 / 0; card DRC 0 errors, 1 warning (the baseline J11 library mismatch), 0 unconnected, parity 0; sync 0. The
power board is byte-identical to step06b.

## Card metrics, step 5g -> 8c (the same changes as step07d / step08b had)
- F.Cu GND pieces 27 -> 28 (step 7: a new 8.1 mm2 F.Cu GND patch that the vias keep; not a split).
- In1 GND pieces 12 -> 11; the main In1 piece 893.9 -> 972.3 mm2 (U101A-Y's In1 span is gone).
- New: In2 5V cut by U101A-Y 8.6 mm (detour 16.2 mm) plus two short ones; 6.5 mm of U101A-Y over In3 plane gaps; one
  more stacked pair (over VerrGT0 on In3).
- Jogs 2594 -> 2589. The sensitive nets (sens_check6) are unchanged.
