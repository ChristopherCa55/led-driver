# Step 9: Net-(D5--) re-routed so it no longer cuts the card's In4 GND in two (2026-10-13)

The user (2026-10-12): "For the card's longest ground splitting tracks, just place them in the location that would
affect other stuff the least (keep other things as intact as possible)."

**Status: built and gated on step 8c, NOT promoted.** Needs the user's OK on the pictures (a re-route of an existing
track).

## What changed (card only; `specs/step09_D5m_reroute.json`, built with `tools/make_step.sh`)
- Removed: Net-(D5--)'s 27.2 mm In4.Cu run (62 segments) from the via (82.125, 95.575) down x 82 and diagonally along
  the card's bottom edge (y 113.8) to the via (69.575, 114.375). With 0err_hi's In4 run at x 79.7 it sealed off the
  right-hand In4 GND piece (318 mm2) from the main one (626 mm2).
- Added (found by `tools/route_new.py` with `fill_cost` and the sensitive-net keepout, `trySplit_D5d`):
  - In4.Cu from the same via (82.125, 95.575): (81.8, 95.95) - (80.95, 96.8) - (80.95, 97.95) - (80.35, 98.55) -
    (80.35, 99.5) - (80.2, 99.65) - (80.2, 103.25) - ... - (81.95, 106.1) - (81.95, 108) - ... - (82.3, 111.6),
    beside 0err_hi's run and round H4's washer keep-out;
  - a via 0.5 / 0.3 at (82.3, 111.6);
  - In2.Cu (the 5V layer) west along the bottom beside the existing In2 track: (81, 111.6) - (80.55, 112.05) -
    (80.05, 112.05) - (79.45, 111.45) - (74.5, 111.45) - ... - (72.4, 112.25) - (70.85, 113.8) - (70.2, 113.8) -
    (69.575, 114.375), into the same via as before.
  - D5- total 41.0 -> 46.1 mm (In4 27.2 -> 18.0, In2 0 -> 14.4).

## Gates
ERC 0 / 0 / 0; card DRC 0 errors, 1 warning (the baseline J11 library mismatch), 0 unconnected, parity 0; sync 0.
Power board byte-identical to step06b. Card PCB `cdd5f629`.

## Card metrics, step 8c -> 9
- **In4 GND: 9 -> 8 pieces; the main piece 626.3 -> 951.8 mm2** (the 318.3 mm2 right-hand piece joins it, with the
  30.1 and 1.1 mm2 ones). 0err_hi's In4 run (15.4 mm) no longer separates anything. New small pieces: 16.1 mm2 and
  18.1 mm2 next to the new In4 run (each still has its vias to the other layers).
- In3 GND unchanged (1066.9 -> 1066.6 mm2). In1, F, B unchanged.
- In2 5V: two new cuts by D5- along the bottom (3.6 mm, detour 29.8 mm; 2.4 mm, detour 22.7 mm); no new 5V piece.
- Sensitive nets (sens_check6): U2 In+ foreign tracks within 2 mm unchanged (2); logic tracks within 2 mm in plan
  154 -> 132 (better); Current and V_err identical.
- Tracks over plane gaps 108 / 202.5 mm -> 106 / 198.9 mm; jogs 2589 -> 2551.

## Pictures
`img/card_splitters/D5_In4_before.png` / `D5_In4_after.png`, `D5_In2_before.png` / `D5_In2_after.png`
(KiCad's own render, x 66-92, y 88-116).
