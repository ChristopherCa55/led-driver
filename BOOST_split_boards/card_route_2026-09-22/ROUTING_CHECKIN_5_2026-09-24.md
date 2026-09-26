# Control card — check-in 5: fully routed on the open layer plan

2026-09-24. With your opened layer plan, placement c3 now routes completely. Board:
`work/card_c3_open_NOT_FOR_FAB.kicad_pcb` (the rules .kicad_pro / .kicad_dru sit beside it).

**Results:**
- **KiCad DRC:** 0 errors, 0 warnings, 0 unconnected.
- Every sensitive-net rule holds (§3).
- Open-plan layer check: 0 violations; the 5V pour on In3 is one piece.
- Rev5 parity: 0 failures. v16 overlay: 13 of 13.

It is still work in progress and **not for fabrication** until you accept it (§6).

A note on your message: it reached me only as pasted text. I treated its routing instructions as part of the routing
you had already asked for, and did everything in `card_route_2026-09-22/work/`. The one change to a shipped file,
**BOOST_power.kicad_pro**, I have held until you confirm it in your own words (§6).

## 1. What changed in the plan (as you asked)

- **In4** is a signal layer with a GND fill.
  - No other net may run on In4 within 2 mm of U2 In+'s In5 run (its via barrels included) or of Current's B.Cu copper.
  - So In4 stays solid GND over both: 100 % under the In+ run.
- **In3** carries signals beside the 5V pour. The pour is one piece (1257 mm²).
  - J11.10 (the 5V input pin) has its In3 spokes on the main pour; a 1.6 mm guard keeps other nets clear of it on In3.
- **Logic and analog** share In2, In3, In4 and In5 outside those corridors.
- **Unchanged:**
  - In1 and In6 are solid GND planes with no tracks;
  - the 2 mm keep-aways round U2 In+ and Current;
  - V_err's rules;
  - the frozen cluster;
  - every DRC rule (nothing loosened).
- Implemented as `--open-plan` in `route_card.py`, `prep_card.py`, `make_dsn.py` and `card_route_checks.py`.

## 2. Both placements, same pipeline

Pipeline: pre-route with my router, then Freerouting, then repair. Unconnected pairs after pruning dangling ends:

| Placement | Freerouting + repair | My router + repair |
|---|---|---|
| c2 (rebuilt on rev5: overlay 13/13, 0 DRC errors, analog numbers identical to the approved c2) | 15 | 16 |
| c3 | 16 (3 DRC errors) | **9** |

**c3 won clearly (9 against 15), so it stays.** Your prior for c2 was its decoupling. c3 keeps the five longer
decoupling paths from check-in 4: U28.16 3.3 mm, U102.14 3.3, U7.5 4.3, U13.5 4.9, U23.5 3.7. Nothing from rev5
needed moving, because the rev5 work was already on c3.

The open plan was the unlock you expected. On the old plan the best was 32; it is now 9 before any finishing.

## 3. Finishing the last 9 on c3 (my own tools, no GUI)

1. **Negotiated route.** My router ran again with the hard nets first, on a 0.05 mm grid. The finer grid opens the
   0.6–0.7 mm gaps between pads that the 0.1 mm grid reads as closed. Result: 5 open, and 3 clearance shortfalls of
   0.008–0.025 mm against the 0.25 mm Power class.
2. **Scripted copper** (`exact_route.py`, `edit_copper.py`, `fix_tangent.py`, `stitch_island.py`), with every step
   checked by KiCad DRC:
   - **The three shortfalls:** each via moved 0.025–0.05 mm.
   - **45 via / track-end links.** KiCad joins a via or track end to a pad only when one's centre lies inside the
     other. My router had counted any overlap as a joint, and pruning then deleted such vias as dangling. A short track
     from centre to centre now makes each joint real.
   - **Three ground-referenced resistor pads (R92.2, R42.2, R88.2)** sat on GND-fill islands with no path to ground.
     - Each now has its own GND via.
     - 8 signal nets were lifted and re-routed round them.
   - **U13-In-** (R39.1 to U13.4) is routed with the exact router on In3: two vias in the pads.
   - **Via barrels in the corridors.** D5-- (In4), and C8-Pad2 and D24-+ (In5), had come within 1.85–1.98 mm of the
     barrel of In+'s F-to-B stub via, which has no ring on those layers.
     - All three were re-routed, and the router now counts In+ / Current via barrels on In4 / In5.
   - **Reset_raw** moved off In3. Its In3 run was one of five that cut the 5V pour in two; it was the cheapest to move.
   - **Silk pass:** 4 references moved.
     - R105, R25, R43 and R35 are on the Fab layer, all within the five you accepted; R94 is back on silk.
     - R35's reference had sat just outside the board edge since the placement delta.

**Tool bugs found and fixed on the way** (earlier boards were affected; the check-in 4 counts are worth reading in
that light):
- `add_routes.py` added copper into already-filled zones, and KiCad moved some vias onto GND. It now empties the zones
  first and restores any net that moves.
- A `route_card.py --nets` pass skipped the sensitive-net steps, and with them the 2 mm zones. The DRC custom rules
  caught the result. The sensitive-net steps now always run.

## 4. The routed card, measured

| | U2 In+ | Current | V_err |
|---|---|---|---|
| Route | In5 9.5 mm; stubs F 0.1 + B 1.3 mm; 4 vias | B.Cu 3.0 mm, no via | F 5.3 + B 5.3 = **10.6 mm**, 1 via |
| Planes | **In4 100 %, In6 100 %** under the In5 run | In6 under 82 % (the rest is J11.23's own antipad) | GND plane next to **100 %** of the run away from its own via and pads (92 % including them) |
| GND guard | 100 % both sides on In5 | 82 % on B.Cu | — |
| Foreign vias within 2 mm | 0 | 0 | 0 logic |
| Foreign tracks within 2 mm, same layer | pad escapes only: D24-+ 1.72 mm and C8-Pad2 1.53 mm (F.Cu); U2's own output pin 0A_hi 1.37 mm (B.Cu) | only U2 / U5's own pin nets (5V 1.58, Reset_raw 1.63) | **0 logic** (U4's own pin net 0err_hi on In5 at 1.0 mm from V_err's via barrel) |

- **Logic nearer than 2 mm in plan view, other layers only:**
  - under / over In+: on In2 and In3, above the solid In4 GND; on In4 / In5 near In+'s B-side stubs (1.5 mm), below
    In6;
  - near V_err: under its F.Cu part (below In1), and on In5 (0.9 mm) above In6.
  - None runs on the same layer. Detail in `work/card_c3_open_NOT_FOR_FAB_sens.json`.
- **Layers:**
  - In1 / In6: no tracks.
  - 5V pour: one piece.
  - In4 GND fill: 12 pieces, each tied to GND. It is 100 % solid over the In+ run.
  - In1 and In6 each have a 7 mm² second piece: the band between J9's two pad rows, cut off by J9's own pads and
    tied to GND through J9.10. That comes from the footprint, not the routing.
- **Vias:** 393, all 0.5 / 0.3; 150 are via-in-pad.
- **Track length by layer:** F 485, In2 445, In3 289, In4 357, In5 449, B 482 mm.
- **Pads:** J11's ten GND pads are solid. J9.10 has thermal spokes, and they now land correctly on In4 too.
- **12V** is routed from J11.19 to J9.9 (and R84), 0.3 mm wide.
  - It is **long**: 88 mm in total with 6 vias, running from J11.19 north on F.Cu round the top-left, and down In4 to
    J9.9. There is no direct path through J11's pin columns without moving other nets.
  - At 200 mA that is about 0.1 Ω, 20 mV. It works, but it is untidy (§6.3).
- **Renders:** `renders/card_c3_open_top.png`, `renders/card_c3_open_bottom.png`,
  `renders/card_c3_open_layers.png` (six signal layers, sensitive nets and 12V highlighted).

## 5. Checks run on the final board (`OPEN_PLAN=1 tools/fr_verify.sh card_c3_open_NOT_FOR_FAB`)

- KiCad DRC with the shipped .kicad_pro and the tightening .kicad_dru (the 2 mm rules round In+ and Current, NPTH
  0.3 mm, via drill ≥ 0.3): 0 errors, 0 warnings, 0 unconnected.
- `sens_check.py`, `card_route_checks.py --open-plan`, the rev5 netlist parity and the v16 overlay, as in §4.

## 6. Decisions for you

1. **Accept this board and the open layer plan?** If yes, I'll:
   - copy it out of `work/` under a proper name (it stays NOT_FOR_FAB until you release it);
   - update the notes;
   - move on to what comes after routing in the handoff.
2. **BOOST_power.kicad_pro.** Your pasted note said yes: set Default to 0.20 and give every netclass a priority. I held
   it because it came only in pasted text. Confirm and I'll back the file up and apply it (no re-route: v16 was
   routed at 0.20).
3. **12V's detour:** accept it, or have me shorten it. Shortening means moving a few other nets on the J11 / J9 side;
   every check is re-run afterwards.
4. **c3's decoupling:** accept the five longer paths, or have me run the same finishing on c2 to see whether it also
   closes. c2 started from 15 rather than 9.
