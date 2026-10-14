# The card's longest GND-splitting tracks (2026-10-13)

The user (2026-10-12): "For the card's longest ground splitting tracks, just place them in the location that would
affect other stuff the least (keep other things as intact as possible)."

Method (`tools/try_reroute.sh`, one scratch folder per try, all on step 8c): remove the span, refill so the planes
heal, re-route with `tools/route_new.py` using its new `fill_cost` (a cell costs more the more existing GND fill a
track there would remove; vias pay for the fill they cut on every layer; In2 counts its 5V pour), then every card
gate. Two more router options were added on the way:
- `foreign_track_keepout`: no new track within 2 mm (plan) of U2 In+ (on F / In3 / In4 / B), Current (B / In3 / In4)
  or V_err (F / In4 / B), i.e. exactly what sens_check6 counts;
- `net_clearance`: per-net clearance (signals 0.2 mm, GND 0.25 mm), instead of one value for all nets.

The longest tracks that separate GND pieces on step 8c: 0err_hi In4 15.4 mm, 0err_hi In1 13.4 mm, D5- In4 11.8 mm,
SDA In1 7.6 + 5.8 mm (U101A-Y, also on the list before, moved in step 8).

| Try | Result | Kept? |
|---|---|---|
| `trySplit_D5` | whole-card search, stopped after 14 min | - |
| `trySplit_D5b` | In4 9 -> 6 pieces (main 626 -> 993 mm2), but D5- ran on In3 right over U2 In+'s In4 run (0.99 mm away; sens_check6 foreign tracks 2 -> 5) | no |
| `trySplit_D5c` | 2 mm keepout on every layer: no route | - |
| **`trySplit_D5d` -> step 9** | **In4 9 -> 8 pieces, main 626 -> 952 mm2**; sensitive nets unchanged or better; two short In2 5V cuts | **yes, pending OK** |
| `trySplit_0errIn4` | the R18 -> U4 span moved to In1: In4 9 -> 7 but In1 11 -> 12 and a foreign via near V_err. Not needed once D5- moves (the span no longer separates anything) | no |
| `trySplit_0errIn1` / `0errIn1b` | B start boxed in; In1 start: main In1 piece 972 -> 918 mm2 and a 58 mm2 piece cut off (today's route separates only 2.5 mm2) | no: the existing route is already the least-harm place |
| `trySplit_SDA` / `SDAb` / `SDAc` | SDA must pass round J9's east end (J9's pads close every other way, on every layer); the best re-route gains 1.6 mm2 and starves J9.10's GND thermal spokes on In1 (DRC error) | no: the existing route is already the least-harm place |
