# Loop vias: cost / benefit per location (2026-10-13)

The user (2026-10-12), on the remaining loop vias: "Can you give a cost / benefit for doing this for each of the via
locations?" **Analysis only; nothing applied.**

**Base:** the copy's power board (step06b: ch2's two vias from step 4, the 12V route, the Vin vias).
**Method:** each location is a what-if on that board's copper export (`../../tools/whatif_vias.py`: the vias flash
where their net has copper; elsewhere they cut an antipad), then a full DC solve of all 38 branches (one at a time,
3 workers). Files: `ch1_*`, `ch3_*`, `vout3_*`, the table generator `loopvia_table.py` and its output
`loopvia_table.txt`.

These are plane-connected vias and every neck that moves is shorter than 5 mm. Per the IPC-2221 rule, the
ratings and rises are reported, not judged.

| Location | Vias added (drill / dia 0.4 / 0.8) | Antipads they cut |
|---|---|---|
| ch1, C1.2 | 1 GND via at (73.86, 66.53) | In2 LX, In3 Vout_1, In4 Vout_1 |
| ch3, C76.2 | 2 GND vias at (88.31, 84.94) and (89.61, 84.54) | In2 LX, B.Cu LX, In3 / In4 Vout_3 (the second via) |
| Vout_3, C4.1 | 2 Vout_3 vias at (92.38, 85.80) and (92.38, 87.00) | In1 GND, In2 LX, B.Cu LX |

## Benefit: the loop each location is for

| Location | Loop | Worst via (x its rating) | Loop R (mOhm) |
|---|---|---|---|
| ch1 | loop GND ch1 ceramics -> M1 | **2.06x -> 1.59x** | 1.006 -> 0.981 (-2.5 %) |
| ch3 | loop GND ch3 ceramics -> M1 | **2.73x -> 1.65x** | 0.911 -> 0.865 (-5.0 %) |
| Vout_3 | loop Vout_3 M4 -> ceramics | **2.80x -> 1.82x** | 0.682 -> 0.601 (-11.9 %) |

## Cost: every other branch that changes

| Location | Branch | R (mOhm) | Neck rise (length) | Long-neck rise (length) |
|---|---|---|---|---|
| ch1 | Vout_1 M2 -> bank + J3 | 0.219 -> 0.227 (+3.7 %) | 17.4 -> 19.4 C (0.0-0.1 mm) | 5.2 -> 6.0 C |
| ch1 | Vout_1 M2 -> J3 (LED DC) | 8.459 -> 8.484 (+0.3 %) | 17.7 -> 17.8 C | 17.7 -> 17.8 C |
| ch1 | loop Vout_1 M2 -> ceramics | 0.237 -> 0.244 (+3.0 %) | 18.7 -> 19.6 C (0.0 mm) | 4.9 -> 5.3 C |
| ch1 | GND ch1 bank -> input | 0.369 -> 0.369 | 5.7 -> 6.6 C (0.1 mm) | 4.7 -> 4.7 C |
| ch3 | LX L1 -> M5 | 1.967 -> 2.023 (+2.8 %) | 56.4 -> 57.6 C (1.3 mm) | 25.8 -> 29.4 C (4.1 mm) |
| ch3 | loop LX M1 -> M5 | 1.848 -> 1.905 (+3.1 %) | 57.0 -> 59.3 C (1.3 mm) | 24.9 -> 29.8 C (4.1 mm) |
| ch3 | GND ch3 bank -> input | 0.438 -> 0.434 (-0.9 %) | 4.7 -> 4.7 C | - |
| Vout_3 | Vout_3 M4 -> bank + J5 | 0.121 -> 0.118 (-2.5 %) | 4.8 -> 4.9 C | 1.8 -> 2.0 C |
| Vout_3 | loop Vout_3 M4 -> ceramics (its own loop) | (see above) | 84.9 -> 90.3 C (1.3 -> 1.0 mm, In4 at (95.7, 87.3)) | 55.3 -> 58.7 C (2.3 mm) |
| Vout_3 | LX L1 -> M5 | 1.967 -> 1.981 (+0.7 %) | 56.4 -> 55.4 C | 25.8 -> 30.0 C (2.1 mm) |
| Vout_3 | loop LX M1 -> M5 | 1.848 -> 1.863 (+0.8 %) | 57.0 -> 55.6 C | 24.9 -> 30.2 C (2.1 mm) |
| Vout_3 | loop GND ch3 ceramics -> M1 | 0.911 -> 0.912 | 38.3 -> 39.4 C (2.8 mm) | 38.3 -> 39.4 C |
| Vout_3 | GND ch1 / ch2 / R52 / R53 / R7 returns | +0.1-0.3 % each | - | - |

Every other branch (Vin, rsense_lo, LX to M1 / M6 / M7, the m*_source branches, Vout_2, the drains and the sense
returns) is unchanged in all three.

Vias over their rating, in the loop concerned: ch1 5 -> 6 and ch3 4 -> 6 (the new vias carry just over 1x each while
the worst one halves); Vout_3 3 -> 5.

## Inductance (added 2026-10-13)

The source is the solver's per-branch over-plane inductance, `L_overplane_nH`. It is the same model as `loop_L6.py`:
- a channel's commutation loop = its LX leg + its source leg + its Vout leg;
- the GND return is the image;
- via barrels are not counted.

| Channel loop L (nH) | base | + ch1 | + ch3 | + Vout_3 |
|---|---|---|---|---|
| ch1 | 2.735 | 2.762 (+1.0 %) | 2.735 | 2.735 |
| ch2 | 3.757 | 3.757 | 3.757 | 3.757 |
| ch3 | 4.306 | 4.306 | 4.423 (+2.7 %) | 4.313 (+0.2 %) |

Branch inductances that move:

| Branch | Change |
|---|---|
| LX L1 -> M5 | 2.18 nH: ch3 +5.2 %, Vout_3 +1.3 % |
| loop LX M1 -> M5 | 2.12 nH: ch3 +5.4 %, Vout_3 +1.3 % |
| Vout_1 bank | 0.77 nH: ch1 +3.1 % |
| loop Vout_1 | 0.79 nH: ch1 +3.4 % |
| Vout_1 -> J3 | 8.20 nH: ch1 +1.9 % |
| Vout_3 bank | 0.94 nH: Vout_3 -3.2 % |
| loop Vout_3 | 1.62 nH: Vout_3 -1.3 % |

**Not in the model: the via barrels themselves.** A rough textbook figure (UNVERIFIED for this geometry) is
L ≈ 0.2 h (ln(4h/d) + 1) nH, with h and d in mm. On this stackup F -> In1 is about 0.45 mm and F -> In3 / In4 about
1.0 mm, which gives:
- a 0.4 mm GND via down to In1: about 0.2 nH;
- a Vout_3 via down to In3 / In4: about 0.6 nH.

Each extra via in parallel shaves a part of that; less than half, because neighbouring vias couple. So:
- the Vout_3 vias also lower the ch3 loop by very roughly 0.05-0.1 nH, which makes their net effect slightly
  better than neutral;
- the ch3 vias give back some of their +0.12 nH.

## Summary

| Location | Benefit | Main cost | My view |
|---|---|---|---|
| **Vout_3** | worst via 2.80x -> 1.82x, its loop -12 % R, Vout_3 bank -2.5 % | LX L1 -> M5 +0.7 %; short-neck rises in the Vout_3 loop (1.0 mm) and LX -> M5 long-neck (2.1 mm) | **the best trade** |
| **ch3** | worst via 2.73x -> 1.65x, its loop -5 % R | LX L1 -> M5 and the LX loop to M5 +2.8-3.1 %, already the longest LX path | worth it only if the ch3 via current worries you more than LX -> M5 |
| **ch1** | worst via 2.06x -> 1.59x, its loop -2.5 % R | Vout_1 bank +3.7 % and the Vout_1 ceramics loop +3 %; Vout_1 is already the weakest output path (8.46 mOhm to J3) | smallest gain; I would leave it |

ch3 and Vout_3 both cut LX on In2 and B.Cu in M5's funnel, so together their LX -> M5 costs add up. The 10-11 "all 7"
what-if, with all three plus ch2, had LX L1 -> M5 +4 %. Tell me which, if any, to apply. Each would be one more power
step (board edit, DRC, the full solve and gates).
