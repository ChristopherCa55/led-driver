# Control card: 8 layers -> 6 layers (2026-09-30)

At the user's request, the card went from 8 to 6 copper layers without re-routing.

**What changed:**
- The old In1 and In6 were solid GND planes with no tracks. `make_card6.py` deletes their zone and renumbers In2-In5
  as In1-In4.
- The stackup is JLCPCB's standard 6-layer 1.6 mm, 1 oz / 1 oz build (JLC061611-7628, 1.609 mm, read from
  jlcpcb.com/impedance).
- The fills were recomputed with `kicad-cli pcb drc --refill-zones --save-board`. The `.kicad_pro` was not changed.

**Checks:**
- DRC: 0 errors, 0 unconnected, the same single warning (J11 library mismatch), from the stored fills and after a
  refill.
- All 168 footprints are identical, and all 5053 tracks and vias match after the renumbering.
- Parity against the cleanup schematic is unchanged (the logos are the only extras).
- In the gerbers, every remaining layer and both drill files are identical to the 8-layer card's. In1-In4 match the
  old In2-In5.

**Trade-off (scratchpad measurement):** the share of signal track with GND copper directly beside it on the
adjacent layer drops:
- top: 88 % -> 58 %;
- bottom: 88 % -> 56 %;
- new In1 (old In2): 92 % -> 34 %;
- new In4 (old In5): 92 % -> 72 %.

**Price (JLC quote page, 2026-09-30):** 5 cards, 45 x 45 mm, ENIG, TG155, 1 oz inner copper, $68.78, against
$123.42 at 8 layers.

The 8-layer card is backed up in `../previous/2026-09-30/before_card_6layer/` (sha 3335e701). This file is the 6-layer
card (sha 320ee4e4), and it was copied into all three folders.
