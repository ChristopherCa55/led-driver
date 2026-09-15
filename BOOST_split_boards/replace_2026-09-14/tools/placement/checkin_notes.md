# Placement check-in notes (draft, layout-independent parts)

## Stack at the 21.21 mm card gap (user decision 2026-09-15)

| Item | mm | Top of item above case floor |
|---|---|---|
| Thermal pad under tabs (user: ~1 mm compliant) | 1.00 | 1.00 |
| TO-220 overall thickness A (HYG180N10 drawing) | 4.57 | 5.57 = power board underside |
| Power PCB | 1.60 | 7.17 |
| Card gap: ESQ-115-44 body 18.67 + TSW insulator 2.54 | 21.21 | 28.38 = card underside |
| Control PCB | 1.60 | 29.98 |
| Tallest top-side card part (SOIC 1.75) | 1.75 | 31.73 |
| Lid (33 mm inside) | | 33.00, margin 1.27 |

- Over the 220 µF cans: can top 7.17 + 16.8 (V-code max) = 23.97; card underside 28.38; 4.4 mm clear (Panasonic
  needs 2 mm above the vent). Any part on the card's underside over a can must be <= 2.4 mm.
- L1 (Codaca CSCF3218, 19.0 mm) top at 26.17: kept out from under the card as decided.
- ESQ-44 tail 4.57 mm through 1.6 mm board: 2.97 mm below the power board, 2.6 mm above the aluminium floor. These
  pins carry 5V/12V/signals; trim tails or keep a clear area on the floor (no standoff/screw heads under J10).
- TSW-07 tail 2.54 through the card: 0.94 mm above the card top.
- J9 right-angle on the card's underside at the board's left edge (2.54 mm body hangs to 25.8 mm; only low THT LED
  pads under it).

Samtec sources (drawings read 2026-09-15): TSW F-219 lead style -07 A 2.54 tail / B 10.92 overall / C 5.84 post, 0.64 sq,
recommended hole 1.02 ± 0.03 mm. ESQ F-218 -44: A 4.57 tail / B 18.67 body, insertion depth 3.68-6.35 mm (5.84 post
seats), 5.7 A per pin with TSW. KiCad 2x15 footprints drill 1.0 mm: at the low end of 1.02 ± 0.03; consider 1.05 mm.
Mating check: J10 = PinSocket footprint on F.Cu (pin 2 at -2.54 mm), J11 = PinHeader footprint flipped to the card's
B.Cu (pin 2 mirrors to -2.54 mm seen from the top): same rotation -> pin n meets pin n. Verify in 3D at the card step.

## Tab screws (user rules)
- Screwed: M1, M8, M9, M10 (TabUp footprint with 3.5 mm NPTH; 3.75 mm washer keep-out, all copper layers; nothing
  taller than 3 mm within 5.5 mm so a screwdriver reaches the head).
- Mechanics to confirm: at the hole the tab is bare metal (A1 1.30 mm), so board underside to tab top = 4.57 - 1.30
  = 3.27 mm. Tightening a screw through the board and tab bends the board unless a ~3.3 mm insulating spacer sits
  between the board and the tab. The tab is the drain (M1: LX), so the screw needs an insulating shoulder bushing in
  the tab hole; the board hole is non-plated with a copper keep-out, so the screw can be at case potential.
- Unscrewed FETs: new footprint BOOST:TO-220-3_Horizontal_TabUp_NoHole (KiCad TabUp without the NPTH and its fab
  circle). The schematic footprint field changes for those refs after the user approves placement.

## R1 Kelvin footprint (for review)
BOOST:R_Bourns_CSS4J-4026 vs Bourns recommended land pattern (css4j datasheet): force pads 5.0 x 5.6 at ±4.7 plus the
outer 1.2 x 1.8 step (7.30 overall height), sense pads 0.80 wide. Open choices: sense stub length (2.1 mm, the drawing
does not dimension it) and the force-pad outer extent. Render: fpsvg/R1_CSS4J-4026_footprint.png.

## Simulation (SIMULATION_REPORT §8 item 1, done)
| Run | R13/R23/R47 | Rail FET Vth | Margin min / median | M1 die | TVS | M1 loss |
|---|---|---|---|---|---|---|
| s150 | 150 | 1.8 V | 24.6 / 28.8 ns | 68.0 V | 38.2 mW | 4.83 W |
| s150lv | 150 | 1.0 V | -0.4 / 2.6 ns (fail) | 66.0 V | 14.2 mW | 5.00 W |
| s220 | 220 | 1.8 V | 40.8 / 46.3 ns | 68.0 V | 38.3 mW | 4.85 W |
| s220lv | 220 | 1.0 V | 18.3 / 24.4 ns | 66.0 V | 13.1 mW | 4.98 W |
No avalanche in any run; LEDs 2.631 / 2.368 / 2.368 A; reverse current into rail drains <= 1.34 A.
Record: BOOST_split_boards/replace_2026-09-14/deadtime_check_2026-09-14.txt.

## Schematic since check-in 2
- R13/R23/R47 = 220 (value was already 220 in the saved file when I re-ran; ERC 0, netcheck 0).
- J10 -> PinSocket_2x15 + MPN ESQ-115-44-G-D; J11 -> PinHeader_2x15 + MPN TSW-115-07-G-D. ERC 0, netcheck 0.
- Netlist diff vs BOOST_9-2_1013 also lists C41/C44/C45 (1 nF IREF wiper caps) as removed: not my edit; they were
  already absent from the pre-edit backup (context doc §13 item 6 recommended deleting them). Confirm with the user.

## Delivery cautions
- KiCad lock files exist next to BOOST_power/BOOST_control in BOOST_split_boards: close KiCad before files are replaced.
