# Control card, step 7 — check-in 2: placement (before routing)

2026-09-18. The card is placed but not routed. The v16 power board is untouched. The schematic is untouched since
rev4 (J9 footprint only), and no DRC rule was changed.

**Board:** `card_2026-09-17/work/BOOST_control_place_c2_NOT_FOR_FAB.kicad_pcb`
- The shipped `BOOST_control.kicad_pro` sits beside it, byte-identical (SHA c602fc94…).
- An `fp-lib-table` there points KiCad at `BOOST-github/BOOST/BOOST.pretty`, for J9's footprint.
- Layout file: `work/place_c2.json`. Config: `work/place_c2_cfg.json`.
- Plots: `work/BOOST_control_place_c2_NOT_FOR_FAB_check.png` (both sides, nets drawn as spanning trees, cans
  and keep-outs).
- Renders: `work/c2_render_top.png`, `work/c2_render_bottom.png`.
- One command re-checks it: `tools/check_card.sh work/place_c2_cfg.json work/place_c2.json BOOST_control_place_c2_NOT_FOR_FAB`.

## 1. Result

| Check | Result |
|---|---|
| **Overlay against v16** (`card_overlay.py`, reads both saved boards) | **13 of 13 pass**: J11 pad n on J10 pad n for all 30 (worst 0.0000 mm), J11 on B, J10 on F, H1–H4 on H5–H8 (0.0000 mm), all five locked, outline = the v16 card rectangle |
| **DRC** (kicad-cli, shipped rules) | **0 errors.** 27 silkscreen warnings (§6) and 380 unconnected items, as expected before routing |
| Placement model | 0 courtyard overlaps, nothing outside the card, nothing in the four r 3.5 mm washer/screw-head keep-outs |
| Pads vs model | Every pad in KiCad within 0.05 µm of the placer's model |
| Parts | 160 SMD: **68 top, 92 underside**; plus J9, J11 and H1–H4. ICs on top: U3, U14, U18, U22, U24, U28, U101, U102, U103, U105. ICs underneath: Q1, U2, U4, U5, U7, U13, U21, U23, U26, U104, U106 |
| Heights | Top ≤ 1.75 mm; underside tallest 1.80 mm (1206 worst case), 2.90 mm above the cans (§4) |

`check_card.sh` runs every stage in order and stops at the first failure:
1. apply the layout;
2. the v16 overlay (non-zero exit on any failure);
3. DRC through `drc_place.py`, which fails on any error-severity violation and only counts unconnected items;
4. the distance and height report `card_check.py`.

## 2. Your analog constraints

The Current net is J11.23 → U2.4 and U5.3. U2 and U5 sit on the underside, stacked right beside J11.23. U4, the
other V_err comparator, sits next to them, with U28 (the 4051 that drives V_err) above them on the top side.

| Constraint | Result |
|---|---|
| Current short | J11.23 → U2.4 **2.8 mm**, → U5.3 **3.0 mm**, both on the underside; half-perimeter 4.4 mm |
| Over continuous GND | Both stubs leave J11.23 eastward, away from J11's pin column, on B.Cu over In6 GND (routing plan §7). No via is needed on the Current net: J11 is through-hole |
| Away from the 74HC14s | Nearest U104 pin 23.8 mm, nearest U105 pin 17.5 mm (both from any pin, supply pins included) |
| Away from M1_ON | Nearest M1_ON pin 18.9 mm (U101.5) |
| Away from I2C | SCL 12.4 mm, SDA 10.2 mm (J9.7 / J9.8). U26 sits on the underside just north of J9, so the I2C runs are 10–13 mm long and stay on the west side |
| Routes, not just pins (proxy below) | Current vs SCL 12.4, SDA 10.2, M1_ON 18.9, M2_ON 25.4, out_2_on 22.9, out_3_on 20.5, VerrGT0 15.1, ena_out_1 21.2, ena_out_2 20.1, ena_out_3 12.7 mm (minimum 8) |
| J11 GND straight into the plane | J11's ten GND pins (1, 2, 11, 12, 20, 21, 24, 25, 28, 29) are through-hole. They join every GND plane directly, with no via or trace. J11.23 is flanked by GND pins 21, 24 and 25. I propose solid (no-spoke) plane connections on those ten pads (§7) |
| D27/R105 at M1_INHIBIT | D27.1 → U104.1 **2.5 mm** (limit I set: 2.5); R105.1 → D27.2 **1.7 mm** (limit 2.0). The M1_INHIBIT node (D1, D15, D24, D27, R26, U104.1) spans 6.2 mm half-perimeter |

**Route proxy.** A pin-to-pin distance can hide a crossing trace, so the check draws each net as the minimum spanning
tree of its pins and measures segment to segment.

This caught a real problem in an intermediate layout (gv_92). Every pin was 10 mm or more from Current, but U26 sat
south-east, so the SCL/SDA spans crossed J11 1.9 mm from the Current stub. The placer now carries the same term: the
Current segments against SCL, SDA, M1_ON and every 74HC14 output net, 8 mm minimum.

## 3. What else I checked (decisions in §8)

The Current net is not the only input of those comparators:
- U5 compares Current against **V_err**, the 4051 COM output (U28.3), which also feeds U4.4.
- U2 compares Current against its **In+** node: the R16/R17 divider plus the R11 hysteresis resistor from its
  output (0A_hi).

Noise on either one eats the same 22 mV margin, so I weighted both and measured them.

| Item | Result |
|---|---|
| V_err (U28.3, U4.4, U5.4) | half-perimeter **4.0 mm** |
| U2 In+ (U2.3, R11, R16, R17) | half-perimeter **11.2 mm**. The divider and R11 sit 7–11 mm south of U2: U5, U4 and U28 fill the space beside it. Weighting it 15 and two re-runs did not pull it closer |
| Comparator inputs vs logic-edge pins (gates, 4017, 4051 selects S0–S2, 4066 controls) | nearest **3.8 mm**: U4.4 (V_err) to U28.11 (S0). My target was 4.0. U4 sits under U28, and on the 4051 itself COM (pin 3) and S0 are only about 6 mm apart, so this cannot go far |
| Route proxy: 4017 → 4051 select lines (Net-(U102C-A), Net-(U102B-A)) | cross the V_err span U5–U4 at 1.1–1.4 mm, and U2 In+ at 2.4–2.9 mm. They only switch when the 4017 steps channel. Routing answer (§7): V_err and U2 In+ on an inner layer between two GND planes, the selects on the other side of the stack |
| Route proxy: IREF3 (Arduino → R57 → U106.13, the 4066 control 1E) | 2.0 mm from the J11.23–U2.4 stub. IREF1 8.2, IREF2 12.8, ARD_M1_INHIBIT 8.4 mm. The IREF lines switch only when the Arduino enables a channel. Same routing answer: IREF3 on the far side of the stack |
| Vref_n_arduino → series R of each RC (R101, R100, R77) | 4.3 / 4.4 / 5.9 mm from J9.1–3. An early layout had R77 26.9 mm away, so the unfiltered line would have crossed the card past the Current node. The config now keeps each within 6 mm of J9. **I assumed these are Arduino PWM outputs; I have not verified that** |

The 4051/4066/74HC14/74HC00 pin functions above (select, control, output pins) are standard pinouts; I did not
re-read the datasheets this session.

## 4. Heights (package maxima: only J11 and U26 have part numbers)

| Side | Tallest | Limit | Stack |
|---|---|---|---|
| Top | 1.75 mm, SOIC-14/16 (U18, U28, U101, U102, U103, U105) at the JEDEC maximum | ≤ 1.75 | Card top 30.20 → 31.95 mm, **1.05 mm under the lid** (33.00). Screw heads 32.30 |
| Top, through-hole | J9 fillets trimmed flush (≈ 1.0); J11 TSW-07 tails 0.94 | ≤ 1.75 | |
| Underside | 1.80 mm: C49, C64, C67 (C_1206, 1.6 + 0.2 worst case). **The placer keeps these three on the underside only**; on top they would break 1.75. Next: SOIC U104/U106 1.75 | ≤ 2.7 over a can | Card underside 28.60 → 26.80 mm, **2.90 mm above the can tops** (23.90) |
| Underside parts over an output can | 46, tallest 1.80 mm | ≤ 2.7 | |

Nothing else under the card reaches the card, from v16's courtyards in the card area:
- J10's socket outline equals J11's courtyard (65.11–71.29 × 72.33–111.54), and no card part sits inside it on
  either side.
- C40 (680 µF, top 19.9) is 8.7 mm below the card underside.
- The rest under the card is:
  - SMD parts;
  - the J3–J6 test-point pads (4 × 4 mm through-hole; anything soldered to them is not modelled);
  - the standoffs;
  - the FET tab screw heads (M2.5 pan head).
- The J9 tie head is over no can (from check-in 1; J9 has not moved).

## 5. Decoupling

| IC supply pin | Nearest cap | mm | Sides (IC / cap) |
|---|---|---|---|
| U2.5, U4.5, U5.5, U21.5, U104.14, U106.14 | C28, C98, C24, C53, C58, C23 | 1.6–1.9 | B / B |
| U14.5, U18.16, U103.14 | C12, C52, C104 | 1.6–2.1 | F / F |
| **U101.14** | C22 | **4.4** | F / F |
| U26.17, U28.16, U102.14, U105.14 | C26, C99, C94, C57 | 0.4–2.0 | **other side** |
| U7.5, U13.5, U23.5 (analog_5V) | C36, C32, C38 | 1.9–2.0 | B / B |
| U22.5, U24.5 (analog_5V) | C63, C37 | 1.6–2.0 | F / F |
| U3.5 (analog_5V) | C66 | 1.9 | **other side** |

- 5V: 14 IC pins, 21 capacitors. analog_5V: 6 pins, 6 capacitors.
- Five caps sit on the other side, under their IC (0.4–2.0 mm). Their loop is a via pair through 1.6 mm, next to
  the In1/In6 planes.
- U101's cap is the one outlier, at 4.4 mm.

## 6. DRC detail (27 warnings, all silkscreen, none waived)

- **silk_over_copper (14):** reference text of J9, R9, R25, R35, R43, R94, R105 and D27 over nearby pads.
- **silk_overlap (13):**
  - reference texts against outlines: R105/U101, D27/D1, R25/R96, R94/C42, R35/R91;
  - R9 and R94's texts against each other;
  - the outlines of three touching SOD-123s (D1, D24, D27).

These are for the silk pass after routing: move reference text (kept at or above the 1.0/0.15 minimum), and nudge
the three diodes if their outlines still touch. No rule change and no exclusion. The 1.0/0.15 silk text rule stays.

## 7. Routing plan (for your approval with this placement)

1. **Stackup.** Write the same JLCPCB 8-layer stackup into the card file as the power board (1 oz outer and inner,
   1.6 mm). The card file currently has none.
2. **Layers.**

   | Layer | Use |
   |---|---|
   | F.Cu | Parts, short fan-outs |
   | In1 | GND, solid |
   | In2 | Logic and I2C |
   | In3 | 5V / analog_5V pours |
   | In4 | GND |
   | In5 | Analog: V_err, U2 In+, Verr1–3, Vref_1–3 after their RC |
   | In6 | GND, solid |
   | B.Cu | Parts, short fan-outs |

   - The Current stubs go on B.Cu over In6.
   - V_err and U2 In+ run as stripline on In5, between In4 and In6.
   - The 4017 → 4051 selects and IREF3 stay on F / In2, above In1.
3. **J11 GND pins.** Solid plane connection on all ten GND pads (a per-pad zone setting; stricter than the default,
   not a rule change).
4. **Via drill ≥ 0.3 mm.** A custom rule that tightens the card's 0.25 mm minimum; the handoff notes Ø0.25 drills
   cost extra at JLCPCB. Tightening only.
5. **Current.** No other copper on B.Cu or In5 within 2 mm of the stubs; no via of another net inside that band.

## 8. Decisions for you

1. **Approve this placement for routing**, or tell me what to move.
2. **Double-sided assembly.** The SMD courtyards total 1578 mm² against 1440 mm² free per side, so one side cannot
   hold them. The layout puts 92 parts (11 ICs) underneath. That means two-sided SMT at the assembler.
3. **1206 caps C49, C64, C67:** underside only (as placed), or choose MPNs no taller than 1.75 mm so they could go
   on top. I have not looked any up.
4. **Vref_1–3_arduino:** confirm they are PWM. If they are DC, the RC-at-J9 rule is harmless and stays.
5. **U2 In+ spread (11.2 mm):**
   - **(a) (my recommendation)** accept it and route it on In5 between GND planes;
   - (b) ask me for a focused re-placement of the comparator cluster (U2, U5, U4, U28, R11, R16, R17). That
     probably costs some V_err or Current length.
6. **Routing plan (§7):** the layers, the J11 solid GND pads, via drill ≥ 0.3 mm, and writing the stackup.
7. **Silk warnings (§6):** fix them in the silk pass after routing.

## 9. How the placement was made (so it can be repeated)

- **Placer** `tools/card_place.py`: simulated annealing over x, y, rotation and side. It includes:
  - courtyard, edge (0.25 mm inset) and keep-out legality;
  - signal-net half-perimeter; power nets are planes;
  - greedy decap matching per supply pin, with a penalty for the other side;
  - "near" rules: D27 at U104.1, R105 at D27, the Vref RC resistors at J9;
  - "apart" rules, pins: comparator inputs ≥ 10 mm from the 74HC14s and I2C, ≥ 8 mm from M1_ON, ≥ 4 mm from
    logic-edge pins;
  - the route-proxy rule (Current ≥ 8 mm from the I2C, M1_ON and 74HC14-output spanning trees);
  - side-only for the 1206s.
- **Legalizer:** a random local search, then a whole-card "shove" for any IC still illegal (it may cover passives,
  which are then re-legalized).
- **Sequence:**
  1. The first fully legal layout (c1) met your Current rules, but V_err spanned the card (61 mm; U28, U4 and U5 in
     three corners).
  2. Fresh runs with V_err weighted fixed that. One of them (gv_92) exposed the I2C crossing.
  3. With the route-proxy term, then polishing and warm restarts, the result is pw_134 = **c2**. Total signal
     half-perimeter is 1790 mm (c1: 1869).
  4. D3 was then moved 0.05 mm west: its courtyard touched H3's keep-out by 0.3 µm.
- **Scripts:**
  - `apply_layout.py`: places the parts in KiCad and asserts every pad against the model;
  - `card_overlay.py`: the v16 overlay;
  - `drc_place.py`: the DRC verdict;
  - `card_check.py`: the report and plot;
  - `layout_metrics.py`: a one-line comparison of layouts;
  - `check_card.sh`: runs all of them.

rev4 recap (done after check-in 1, per your J9 decision):
- J9 → `BOOST:WirePads_11_Staggered_P1.27mm_Drill1.0mm_TieSlots`. 11 PTH (drill 1.0, pad 2.0) in two staggered rows,
  2.54 mm apart on a 1.27 mm step, plus two 2.8 × 1.4 mm NPTH tie slots at the west end.
- ERC 0 (the same four ignored checks). The netdiff against rev3 shows only J9's footprint. Parity 0 for the card
  (control_sync4) and for the frozen v16.
- The schematic was backed up to `previous/2026-09-17/schematic_before_j9_wirepads/`. Its lock file dates from 2
  September and was stale.
