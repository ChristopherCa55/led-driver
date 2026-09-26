# Control card — check-in 4: B and A done, routing still open (32 unconnected), decision needed

2026-09-23. Everything in your message of today is done except closing the routing: B (placement delta), A
(Freerouting over DSN/SES), C (Default 0.20 in the file), rev5 (J9.9 → 12V), BUILD_NOTES, and your V_err condition,
all measured below.

The best board has **32 unconnected pairs and 0 DRC errors**:
- every sensitive-net rule holds, and the three sensitive nets are identical, item by item, to their pre-route;
- the layer plan has 0 violations, rev5 parity is 0, and the v16 overlay passes 13 of 13.

Neither router closes the rest, whatever I tried (§4), so this is again a check-in with a decision, not the routing
report. Nothing is ready for fabrication. Every board is `NOT_FOR_FAB` work in `card_route_2026-09-22/work/`.

## 1. B — placement delta c3

Files: `card_2026-09-17/work/place_c3.json`, board `BOOST_control_place_c3_NOT_FOR_FAB.kicad_pcb`.

Only underside passives moved. The frozen cluster is untouched: U2, U5, U4, U28, R11/R16/R17, D27, R105,
R101/R100/R77, J9, J11.

- **Underside passives under the top-side SOICs** (U101, U102, U103, U105, U18): 35 → 9. Their overlap with those
  courtyards fell from 158 to 15 mm².
- **37 parts moved:**
  - 12 of them went to the top side: C54, C99, D25, R31, R32, R34, R4, R41, R63, R64, R81, R92.
  - R87 and R88 moved 0.1 mm or less, in legalisation.
  - R18/R19/R20 (U4's In+ divider) moved about 3 mm east of U4, out of V_err's path. The first delta moved R20
    alone, and V_err then cut U4 In+ in two.
- **Checks:**
  - v16 overlay: 13 of 13 pass.
  - card_check: legal.
  - DRC: 0 errors (17 silk warnings, which the silk pass clears).
  - Every analog number is identical to c2: Current, D27 → U104.1 2.5 mm, the J9 RC resistors, the apart distances.
    The existing U4.4 – U28.11 3.8 mm (minimum 4.0) is unchanged.
- **Cost:**
  - Five decoupling distances grew:

    | Supply pin | c2 | c3 |
    |---|---|---|
    | U28.16 | 1.5 mm | 3.3 mm |
    | U102.14 | 0.4 mm | 3.3 mm |
    | U7.5 | 2.0 mm | 4.3 mm |
    | U13.5 | 1.9 mm | 4.9 mm |
    | U23.5 | 1.9 mm | 3.7 mm |

  - Wire length (half-perimeter) 1791 → 2102 mm.
  - Underside parts over an output can: 46 → 32.
- **It did not measurably help routing.** My router alone on c3 stalls at 38 after its repair rounds; on c2 it
  reached 24. The comparison isn't exact: c2's 24 took more negotiation rounds.

## 2. A — Freerouting 2.4.1

### Setup

- Nothing was installed; it runs as installed.
  - The bundled runtime has no `java.exe`, but `freerouting.exe` launches Java itself.
  - Headless: `freerouting.exe -de X.dsn -do X.ses -mp N -da --gui.enabled=false`.
  - `-da` switches off Freerouting 2.x's usage analytics, so nothing is sent from your PC.
- **DSN** (`tools/make_dsn.py`, from the pre-routed board):
  - My router's pre-routes are fixed wiring: Current, U2 In+, V_err, the other comparator inputs, stitching,
    decoupling links, plane fan-outs.
  - Layer plan as net classes (`use_layer`):
    - logic: F / In2 / B;
    - analog: F / In5 / B;
    - the J11 sense lines: F / In5 / B, 0.25 mm clearance;
    - rails: F / In3 / In5 / B;
    - GND and 5V reach their planes through vias.
  - Keep-outs, since Freerouting doesn't read the .kicad_dru; each measured from the copper edge:
    - vias of any other net: 2 mm round U2 In+ and Current on every layer, 0.3 mm round V_err;
    - wires: 2 mm round Current on B.Cu and In5, and round U2 In+ on In5;
    - J9's tie slots: 0.3 mm;
    - board edge: 0.3 mm.
  - Class rules:
    - logic keeps 2 mm from U2 In+ and V_err on F.Cu and B.Cu, where those nets have copper. It is per layer: my
      first DSN applied it on every layer, and that walled In2 off under them;
    - 0.25 mm between the Power-class nets and everything else.
  - One via for every net, 0.5 / 0.3, via-in-pad allowed.
- **Import** (`tools/import_ses.py`):
  - puts every pre-route back;
  - drops anything the session added to Current / In+ / V_err, or to the nets the pre-route had already completed;
  - checks the three sensitive nets item by item against the pre-route.
- **Checks** (`tools/fr_verify.sh`): DRC, `sens_check.py`, the layer plan, rev5 parity, the v16 overlay.

### What Freerouting 2.4.1 does that the pipeline works around

1. **`-inc` is ignored.** It accepts the option to ignore net classes, then routes GND and the finished nets anyway.
2. **The session file leaves out all fixed wiring**, and KiCad's SES import deletes every track first. The import
   step puts the pre-routes back.
3. **It counts a track as connected only where it reaches a pad's centre.**
   - My router ends tracks on its 0.1 mm grid inside the pad, so Freerouting drew stubs to the centres. Those
     included 8 stubs on U2 In+ and 4 on V_err; the import removed them.
   - The DSN now carries fixed pad-centre stubs, which exist in the DSN only. That cut its "unrouted" count at the
     start from 389 to 290.
4. **Rails on In3 cut an island out of the 5V plane.** J11.10's thermal spokes then landed on that island, which
   KiCad flags as a starved thermal (an error).
   - My repair rounds reconnected it.
   - On the best board, the 5V plane is one piece of 1429 mm² (1577 before routing, −9 %).
5. **It drew two 0.12 mm tracks** on Vref_3, in the same spot in two runs, under the 0.13 mm board minimum. That
   looks like its automatic neck-down, but `--router.automatic_neckdown=false` did not stop it. Neither board is a
   candidate.
6. **Used as a finisher on my router's board** (pre-routes fixed, everything else movable), it made no progress in
   three passes.

### Results

Unconnected pairs are counted by KiCad DRC after import, and every sensitive net is identical to the pre-route in
all runs.

| Run | Unconnected | DRC errors |
|---|---|---|
| Pre-route only (sensitive nets, comparator inputs, stitching, decoupling, fan-outs) | 186 | 0 |
| Freerouting, 20 passes, fanout stage on (c3b) | **54** | 0 |
| Freerouting, fanout stage off (c3c) | 66 | 0 |
| Freerouting, rails kept off In3 (c3d) | 59 | 2 (0.12 mm tracks) |
| Freerouting with pad-centre stubs, 6 passes (c3f) | 73 | 0 |
| Freerouting with stubs + the per-layer logic rule, 12 passes (c3g) | 65 | 3 (the 0.12 mm tracks; a starved thermal on the B.Cu GND fill) |
| c3b, then my router's repair rounds | 38 → 32 → 32 → 32 (stalled) | **0** |
| Freerouting finishing that board | no progress in 3 passes | — |
| My router alone on c3, from scratch | 46 → 38 → 38 (stalled) | 0 |
| **What-if, not your plan:** logic and analog both allowed on In2 and In5 | 32 → 28 → 26 → 26 | 0 |

## 3. The best board

`work/card_c3_fr_best_NOT_FOR_FAB.kicad_pcb`: c3b plus my repair rounds, then dangling ends pruned.

- **DRC:** 0 errors; 32 unconnected; 17 silk warnings, which the silk pass will clear once routing is final.
- **Layer plan:** 0 violations.
  - No logic on In5, no analog on In2, nothing on In1 / In4 / In6.
  - Only 12V / analog_5V / 5V on In3 (95 mm of rail track).
- **Vias:** 309, all 0.5 / 0.3; 78 are via-in-pad.
- **Pads and stackup:** J11's ten GND pads are solid and J9.10 has thermal spokes; the stackup has 8 copper layers.
- **Parity** against the rev5 netlist: 0 failures. **v16 overlay:** 13 of 13.
- **Sensitive nets** (`sens_check.py`), identical to the pre-route and to check-in 3:

  | | U2 In+ | Current | V_err |
  |---|---|---|---|
  | Route | In5 9.6 mm; stubs F 0.1, B 1.2; 4 vias | B.Cu 2.9 mm, no via | F.Cu 5.6 + B.Cu 7.7 = **13.3 mm** (17 mm on c2; the moved divider shortened it), 1 via |
  | Planes | In4 and In6 under 100 % of the In5 run | In6 under 87 % (the rest is J11.23's own antipad) | GND plane next to 100 % of the run away from its own via / pads |
  | GND guard | 100 % both sides on In5 | 80 % on B.Cu | — |
  | Foreign vias within 2 mm | 0 | 0 | 0 logic; the nearest via of any other net is 0.375 mm away (5V) |
  | Foreign tracks within 2 mm, same layer | pad escapes only: D24-+ 1.77 mm and C8-Pad2 1.56 mm (F.Cu); 0A_hi, U2's own output pin, 1.40 mm (B.Cu) | only U2 / U5's own pin nets leaving their pads | **0 logic** |

- **12V:** J11.19 → J9.9 is routed, 0.4 mm on In3. R84's 12 V pad is still among the 32.
- **Maps:**
  - `renders/unrouted_c3_fr_best.png`: the 32 open pairs.
  - `renders/j9_labels_top_rev5.png`, `renders/j9_labels_bottom_rev5.png`.

## 4. What blocks

- **The 32:** 16 analog, 14 logic, one 5V (U4.5) and one 12V (R84.1).
  - 13 span more than 15 mm. Mostly they are logic nets crossing the card, 20–35 mm:
    - U103.6 → U104.9;
    - D5 → U105;
    - IREF1 / IREF3 to J9;
    - U102D / U102C;
    - Output1_drain from J11 to R94.
  - 10 are short, under 5 mm: pads that can't get out. They sit mostly in the central analog block, round U13 / U23
    / U24 / U106 / R39 / R40 / C64 / C68.
- **The limit is the same as at check-in 3: getting pads onto a via.**
  - The inner layers are not full: In2 carries 719 mm of track, In5 475 mm.
  - With parts on both sides, a through via needs a free spot on F.Cu and B.Cu at once.
  - The 2 mm via zones round In+ / Current, and V_err's 0.3 mm band, take out most of the centre-south.
  - Several 5V / GND pads round U4, U5, U13, U21, U23 and U26 have no reachable via site at all.
- **Evidence for that:**
  - Two different routers stall at about the same count.
  - Freerouting's push-and-shove makes no progress on the finished board.
  - Opening In2 and In5 to both classes gains only 6.

## 5. Your other items

**C: the Default netclass.**
- `BOOST_control.kicad_pro` now states Default 0.20 / 0.20, and every netclass has a priority: Default last, then
  Power, Gate, Rail.
- KiCad resolves exactly what it enforced before: Default 0.20, GND (Power) 0.25, 5V (Rail) 0.20.
- Backup: `previous/2026-09-23/control_pro_before_default_0p20/`. The routing rules copy is updated to match.
- **`BOOST_power.kicad_pro` has the same problem** (as does v16's rules copy):
  - no netclass has a priority, and the file says Default 0.15;
  - KiCad 10 resolves Default to 0.20 / 0.20 on v16 (checked today).
  - v16 was routed and checked at 0.20, so nothing needs redoing. I have **not** changed that file; the same fix is
    ready if you want the file to say what KiCad enforces.

**Rev5: J9.9 is 12V.**
- The schematic's global label at J9.9 changed from 5V to 12V. The old file is in
  `previous/2026-09-23/schematic_before_j9_12v/`.
- ERC: 0 violations, the same 4 ignored checks as rev4.
- netdiff rev4 → rev5 (`tools/netdiff.py`): 290 components and 859 pins; the only change is **J9.9: 5V → 12V**.
- Parity against rev5: 0 failures on power v16, 0 on the card.
- **J9 footprint:** the label reads "12V" on both sides.
  - Strokes keep 0.30 mm or more from each other. The SCL / 12V / INH row is tight but readable; see the renders.
  - Backup: `previous/2026-09-23/j9_footprint_before_12v_label/`.
- **BUILD_NOTES.md:**
  - pin 9 is 12 V (red wire), feeding a 12 V → 5 V buck at the Arduino, **not** the Nano's VIN;
  - an inline 200 mA PTC at the card end;
  - the 12 V and GND wires twisted together;
  - your colours in the J9 table.

**V_err: your condition** (measured on the best board).
- **GND plane under its whole length:** In1 under the F.Cu part and In6 over the B.Cu part cover **100 %** of the
  run, with no gap points.
  - Counting the 0.8 mm round its own via and pads, coverage is 91.2 %. The shortfall is the via's own antipad and the
    pad lands.
  - No via of another net sits within 0.3 mm of V_err, so no foreign antipad cuts the plane under it.
- **Logic running parallel within 2 mm on its layers:** none.
- In plan view, some logic comes within 2 mm on other layers, each with a GND plane in between:
  - 0A_hi, 0err_hi and Reset_raw on In2 cross under the F.Cu part, below In1.
  - Reset_raw on B.Cu comes within 1.36 mm of V_err's F.Cu pad at U28, with the whole board thickness between them.

**Fab-layer references and the J9 colours:** recorded as accepted.

## 6. Decisions for you

1. **How to close the last 32.** My recommendation is **a**.
   - **a. Finish them by hand in KiCad's interactive router** (push-and-shove) on `card_c3_fr_best_NOT_FOR_FAB`.
     - It enforces the tightening .kicad_dru, so the 2 mm via rules round In+ / Current stay checked while you drag.
     - Most of the 32 need a nearby track moved to open a via site. That is what push-and-shove does and what neither
       batch router managed.
     - I then re-run everything: sens_check, the layer plan, DRC, parity, the overlay and the silk pass.
   - **b. Placement round 2.** Move the logic parts behind the long nets (U103, U104, U105, U102, D5) closer to their
     partners, and give the central analog block (U13 / U23 / U24 / U106) more via room. The apart constraints stay.
     This reopens your approved placement beyond today's delta, and I can't promise it closes.
   - **c. Open In2 and In5 to both logic and analog** outside the sensitive zones. Measured: 32 → 26. Not enough on
     its own.
2. **Keep delta B, or return to c2?** B didn't measurably help routing, and it lengthened five decoupling paths (up to
   4.9 mm at U13.5). I'd keep it, because the best board and the rev5 work are built on it. Returning to c2 means
   redoing the pre-route and routing there.
3. **`BOOST_power.kicad_pro`:** apply the same netclass-priority fix (no change in what KiCad enforces), or leave it.
