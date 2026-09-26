# Control card, step 7 — check-in 1: frame, J9 and the card screw

2026-09-17. Nothing is placed yet beyond the five locked parts: J9's position decides the west edge of the card,
and your J9 rule sends it to a check-in, so this comes first. The frozen power board (v16) is untouched.

## 1. Done

| Item | Result |
|---|---|
| `control_sync3` | Built from `control_sync2` with `syncboard.py` against `BOOST_9-15_rev3.net` + `board_assignment_2026-09-15.json` (CONTROL): 166 footprints, **parity 0**. `replace_2026-09-14/tools/placement/wip_NOT_FOR_FAB/control_sync3.kicad_pcb`, with the shipped `BOOST_control.kicad_pro` beside it (the notes say control_sync2's project file had the wrong rules). |
| Frame | `card_2026-09-17/work/card_frame.kicad_pcb`: outline x 45.8905–90.8905, y 70.0226–115.0226 (the card rectangle of the power layout), NOT FOR FABRICATION note. |
| H1–H4 | On H5 (60.6753, 76.5137), H6 (75.0708, 75.7507), H7 (54.4567, 106.4637), H8 (85.1212, 109.5071); **locked**. |
| J11 | B.Cu, rotation 180°, pad n on J10 pad n for all 30 pads (worst 0.0000 mm); **locked**. |
| Keep-outs | One rule area per mounting hole, r 3.5 mm, every copper layer: no copper, no footprints. Covers the 7.0 mm washer (TR NWE-34815-M3, OD 7.0 +0/−0.36) under the card and the screw head on top (§3: Ø 5.5 ± 0.3). |
| Overlay check | `tools/card_overlay.py CARD.kicad_pcb POWER.kicad_pcb`: reads both saved files; J11 pads vs J10, H1–H4 vs H5–H8, locks, outline. **13 of 13 pass** against `BOOST_power_route_v16_NOT_FOR_FAB.kicad_pcb`. It exits non-zero on any failure, so the card's placement check will call it. |
| Heights | All 162 parts other than J9, J11 and H1–H4 are SMD: SOIC-14/16 (8), TSSOP-20 (1), SOT-23-5 (11), SOT-23 (1), SOD-123 (10), SOD-323 (3), 0603/0805/1206 R and C. Package outlines put the tallest at 1.75 mm (SOIC), so everything meets the 1.75 mm top limit and the 2.7 mm over-can limit. **Only J11 and U26 have part numbers** in the netlist, so these are package limits, not verified part heights; the three 1206 caps (C49, C64, C67, 100 nF) and the SOD-123 diodes are the ones to check when MPNs are chosen. |

The shipped `BOOST_control.kicad_pcb` has lock files dated 10 and 14 September (probably stale); I only read it.

## 2. J9 — a 0.05 mm question

`tools/j9_fit.py` slides each candidate along all four card edges in 0.1 mm steps. Its plan-view box runs from the
back of the footprint courtyard (inside the card) to 15 mm past the edge (the mated plug), and down from the card
underside by the header-plus-plug hang. A position is illegal if that box:
- leaves the case (inside walls x −22…106, y 28…118 in power-board coordinates);
- covers an H1–H4 keep-out or J11;
- sits over a 220 µF can with less than 2.0 mm above the can top (23.90 mm);
- sits over anything whose top is above the box bottom (L1 tops out at 26.10 mm).

Along-edge lengths are the courtyards of KiCad's installed footprints.

| Connector (along-edge courtyard) | Round-4 stack, hang 2.75 (your figure) | Same stack, hang ≤ 2.70 | One more 0.5 mm washer (card underside 29.10), hang 2.75 |
|---|---|---|---|
| **1×11 2.54 mm RA (rev3), 28.94 mm** | **nowhere** | **west edge, start y 70.0–75.3** (spans up to y 104); east edge | west edge (start y 70.0–75.3), east edge |
| JST PH 1×11 2.0 mm locking, 24.90 | nowhere | west, east | west, east |
| JST GH 1×11 1.25 mm locking SMD, 18.20 | east edge only (plug toward the east wall, 0.1 mm spare) | west, east | west, east |
| 2×6 2.54 mm RA, 16.24 (hang ≈ 5.35) | nowhere | does not apply (hangs ≈ 5.35) | nowhere |
| JST PHD 2×6 2.0 mm locking, 14.90 | nowhere | west, east | west, east |

Plots: `work/j9_fit.png` (as specified), `work/j9_fit_hang2p70.png`, `work/j9_fit_29p10.png`; data in the matching
`.json` files.

Why each edge fails at your 2.75 mm:
- **West** (faces the Arduino): the cans C78, C87 and C71 leave y 91.4–115.0 can-free (23.6 mm). H3's washer
  keep-out (54.46, 106.46) then cuts that span, because the header body reaches 5.8 mm in from the edge.
- **North:** L1, C86, C88 and C78 below the plug; H1, J11 and H2 along the inside of the edge.
- **East:** C74, C75 and C77, and a plug 15 mm past x 90.89 ends 0.1 mm from the case wall.
- **South:** 3 mm to the case wall.
- **2×6 dual row:** it hangs about 5.35 mm, which is below the can tops, so no can can be anywhere under it at any
  stack height.

The whole question sits on 0.05 mm. A 2.54 mm right-angle header puts its pins mid-body (about 1.27 mm), so a
2.5 mm crimp housing would hang about 2.5 mm, not 2.75. That is plausible, but it depends on the exact header and
housing, and on which way a latch or polarising rib faces. I have not verified any header/plug pair.

## 3. Card screw: head height from a real drawing

No screw part number had been chosen ("M3 × 8 nylon pan head" in the notes and BUILD_NOTES). I found a published
drawing for **Würth Elektronik WA-SCRW 97790803211**: M3 × 8, cross-recessed pan head, nylon 66, UL94 V-0.
- **Head height 2.1 ± 0.2 mm, head Ø 5.5 ± 0.3 mm**, L 8 ± 0.4 mm.
- Operating temperature −30 to +85 °C.
- Source: Würth datasheet rev 001.002, 2022-04-28. WebFetch saved a 212 KB copy in this session's tool-results
  folder, outside the project; I did not add it to the repo.

| Card top | Head top (nominal / max head) | Margin to the lid (33.00) |
|---|---|---|
| 30.20 (round-4 stack) | 32.30 / 32.50 | **0.70 / 0.50 mm** |
| 30.70 (one more washer, §2 option) | 32.80 / 33.00 | 0.20 / **0.00 mm** |

These figures exclude the stack's own tolerances: three washers ±0.05 each, card thickness (fab tolerance), and the
Essentra F/F standoff length, which Essentra does not publish. At the round-4 stack the margin is about 0.5 mm only
at nominal stack height. With all three washers at +0.05 and a card 10 % thick (+0.16 mm, an assumed fab tolerance,
not checked), it drops to about 0.2 mm. Also unverified: whether the card area stays under this screw's +85 °C
rating.

## 4. Decisions for you

1. **J9** (my recommendation first):
   - **(a) Keep the rev3 1×11** with a header and plug whose combined hang is ≤ 2.70 mm below the card. It goes on
     the west edge (toward the Arduino), y ≈ 70–104, with no schematic or stack change. I would pick a header and
     crimp housing and confirm the hang on their drawings; say if I may fetch those drawings.
   - (b) Keep the 1×11 and add a fourth 0.5 mm washer per standoff. J9 then clears at the 2.75 mm figure. But the
     Würth screw's worst-case lid margin goes to 0, so this also needs a lower-head nylon screw (not found yet),
     and the card-top parts lose 0.5 mm (lid margin 1.05 → 0.55 mm for 1.75 mm SOICs).
   - (c) A schematic change to a smaller connector. At the round-4 stack only a JST GH 1×11 fits, on the east edge
     facing the case wall, away from the Arduino. I don't recommend it.
2. **Card screw:** accept Würth 97790803211 (0.70 mm nominal margin, 0.50 at maximum head height; the stack
   tolerances not included), or ask me for a lower-head alternative. Its +85 °C rating needs your view of the
   in-case temperature.

Next, once J9 is settled: placement, with the analog constraints you listed. That means the Current node
(J11.23) and the hysteretic comparators short and over continuous GND, away from the 74HC14s (U104, U105), M1_ON
and I2C; J11's GND pins straight into the GND plane; D27/R105 at M1_INHIBIT. Then the placement check-in:
distances, heights, and the overlay against v16.
