# BOOST power board: re-place brief, v2

2026-09-14. Supersedes the web version of the brief
(<https://claude.ai/code/artifact/08a03b10-d9f7-4470-87f0-51cc3f212b3c>, private to the user; saved copy
with the user's choices and notes: `replace_brief_page_saved_2026-09-14.html`).

- **Board:** `BOOST_split_boards/BOOST_power.kicad_pcb`, 74 × 86 mm, 8 copper layers, 121 parts.
- **Replaces:** the layout shipped 2026-09-14 (SHA-256 `f4807690…`).
- **Based on:** `BOOST_AUDIT.md`, `AUDIT_RESPONSE.md`, pad positions from the shipped board, and `SIMULATION_REPORT.md`.

## Why re-place

The 2026-09-14 layout added 64 vias and 13 copper patches, and none of the audit's 10 failed checks
passes yet. The cause is placement: the parts on each high-current path sit 30–60 mm apart. The
placement appears to carry over from the 2026-09-08 fit study (option 2b), which packed courtyards to
prove the parts fit; it did not follow current paths. The routing AI was told not to move parts and
flagged this in `README.md`.

- Every rail FET's nearest output caps belong to other rails. The nine 220 µF caps are identical, but
  even the best reshuffle of the existing nine spots only halves the total FET-to-cap distance
  (401 → 199 mm) and still leaves one cap per rail 30–43 mm away (`placement/output_cap_reassignment_2026-09-14.txt`).
- M5 sits in the LED-sink row, 59 mm from L1 and 22 mm from M4 (its source-sharing partner).

## Decisions

| ID | Topic | Decision | Status |
|---|---|---|---|
| D1 | Switching edges / FET package | Keep the TO-220s (tab-down to the case). Slow **M1's turn-off**: delete D12, R15 5.1 Ω → **10 Ω**. | Decided (simulated) |
| D1b | Dead-time margin | R13, R23, R47 100 Ω → **150 Ω** (keep D11, D14, D13). | Decided; **150 Ω not yet simulated** |
| D2 | Current sense | **Four-terminal R1** (Bourns CSS4J-4026K-2L00F) with Kelvin sense nets to U25; **net-ties** at the sink shunts R7/R52/R53 for the op-amp sense. U25 beside R1; each sink op-amp beside its shunt. | Decided |
| D3 | Copper weight | **Open.** Route the power copper first, solve it at 1 oz and at 2 oz outer, then choose B (1 oz all, $106.68) or C (2 oz outer / 1 oz inner, $141.68). Never 0.5 oz inner. | Open |
| D4 | Board-to-board link | **Stacking header + socket** (not a ribbon), header on the power board, socket on the control card, pin n meets pin n, with standoffs carrying the card. GND beside every analog pin. J10/J11 into the schematic. | Decided |
| D5 | Control card | **Shrink** (target ~42 × 42 mm; ~45 mm if the header needs it), sited over the capacitor field clear of L1. **Add mounting holes** (M3) and matching standoff holes on the power board. | Decided |
| D6 | Arduino M1 inhibit | New Arduino header pin → diode → M1 inhibit node (`Net-(D1--)`) on the control card. | Decided (new) |

Details and part links are in `HANDOFF_PROMPT.md` §3.

## Placement, in this order

Distances under "Now" are straight-line pad-to-pad on the shipped board (copper paths are longer).
Targets are layout goals for this re-place, not audit thresholds. Full numbers:
`placement/distances_power_board_2026-09-14.txt`.

Lay each channel out as one strip: rail FET → its three caps → LED anode/cathode pads → sink FET → shunt.

### Stage 1: input loop and M1

The 20.7 A RMS loop from the input caps through R1, L1 and M1 and back. Place it first.

| Rule | Parts | Target | Now |
|---|---|---|---|
| Input caps hug R1 and M1: Vin pads to R1's Vin current pad, GND pads to M1's source, short outer-layer pours | C40, C69, C85 | ≤ 10 mm | Vin→R1.2: C85 17, C40 21, C69 31 mm. GND→M1 source: C85 28, C69 37, C40 39 mm |
| R1 between the caps and L1 on one outer layer; J1/J2 lugs on the edge nearest this cluster | R1, L1, J1, J2 | R1 → L1.2 ≤ 10 mm | 10.6 mm (J1 → R1.2 49 mm) |
| D19 (TVS 5KP54A) right across M1's drain and source pins | D19, M1 | ≤ 5 mm | LX pad → M1 drain 29 mm; GND pad → M1 source 27 mm |
| U19 beside M1's gate; R15 (now 10 Ω) between them; no D12 | U19, R15, M1 | ≤ 10 mm | U19 → M1 gate 15 mm |
| U25 (INA241A3) beside R1, inputs only on R1's two sense pads | U25, R1 | ≤ 10 mm | 41 mm |

### Stage 2: LX node

| Rule | Target | Now |
|---|---|---|
| L1's LX pad in the middle of the four LX drains (M1, M7, M6, M5) on one outer-layer pour. **M5 leaves the LED-sink row.** | ≤ 15 mm | M7 10, M1 19, M6 31, M5 59 mm |
| No LX copper on In3 or In5 (they face the In4 5V plane; the old pours coupled 232 pF) | none | removed in the 09-14 layout |

### Stage 3: channel switch pairs

| Rule | Target | Now |
|---|---|---|
| Each LX FET directly beside its rail FET, shared source joined by short, wide copper: M7–M2 (m2_source), M6–M3 (m3_source), M5–M4 (m4_source) | adjacent (11.25 mm tab pitch) | 11, 11, 22 mm |
| Gate driver beside its pair: U15 → M2/M7, U10 → M3/M6, U8 → M4/M5 (KiCad refdes; U8 is U20 in LTspice). Gate resistors R13/R23/R47 (150 Ω) and R60/R70/R59 next to the FETs | ≤ 15 mm | U15 13/18, U10 20/27, U8 11/28 mm |

### Stage 4: output banks and LED pads

| Rule | Target | Now |
|---|---|---|
| Each rail's three caps at its own rail FET: Vout_1 C70/C86/C88 at M2; Vout_2 C71/C78/C87 at M3; Vout_3 C74/C75/C77 at M4 | ≤ 15 mm | M2: 34/45/55; M3: 32/34/48; M4: 30/55/67 mm |
| Bank GND pads return to M1's source and the input caps through outer-layer pour plus In1/In6, never through a single via | multiple vias | M1 return via (78.7, 38.0) at 2.7× rating |
| Each channel's LED pads side by side at the edge: J3+J4 (ch1), J8+J7 (ch2), J5+J6 (ch3) | ≤ 8 mm | 6, 41, 6 mm |

### Stage 5: LED sinks (clears audit stop-ship item 1)

| Rule | Target | Now |
|---|---|---|
| Shunt at the sink FET's source pin: R52 at M10 (ch1), R53 at M9 (ch2), R7 at M8 (ch3) | ≤ 5 mm | 48, 33, 39 mm (2.63 A runs 50–101 mm of 0.15 mm track today) |
| LED cathode pad at the sink FET's drain: J4 at M10, J7 at M9, J6 at M8 | ≤ 15 mm | 49, 61, 51 mm |
| Sink op-amp between its shunt and its FET, IN− on the new sense net at the shunt pad (net-tie): U11 (R52/M10), U12 (R53/M9), U6 (R7/M8); gate resistors R56/R50/R22 at the FET | ≤ 10 mm | IN−→shunt 25/24/13; OUT→gate 27/29/42 mm |
| Shunt GND pads straight into the planes, ≥ 2 vias each | ≥ 2 vias | R53 two Ø0.25 (2.0×), R7 worst via 2.3× |

### Stage 6: keep-outs and mechanical (draw before any copper)

| Rule | Detail |
|---|---|
| Washer keep-out at every TO-220 tab hole | No copper or parts within 3.75 mm of each hole centre (7 mm M3 washer + 0.25 mm) on every layer, as rule areas. Today copper reaches 0.2 mm from the hole edge and 17 parts intrude (closest R14 2.46, D12 2.59, R104 2.76 mm). D12 is being deleted. |
| Nothing on B.Cu taller than the TO-220 body gap | U16 (LM2940, TO-263) is 4.83 mm vs a 4.6 mm gap: move it to F.Cu. |
| Control-card outline, stacking header and standoff holes as keep-outs on the power board | Tall parts stay out from under the card except the ones the stack budget allows (see below). |
| J10 (power-side header) outside M1's return-current field | Its GND pins are the control card's ground reference; today they are 7–19 mm from M1's source (up to 8.5 mV setpoint offset). |

**Stack budget** (33 mm internal height):

| Item | mm |
|---|---|
| TO-220 body under the power board + insulator | 4.60 + 0.23 |
| Power PCB | 1.60 |
| Tallest part under the card | 12.5 (680 µF cans) **or** 16.5 (EEH-ZU1H221P 220 µF per Panasonic; the footprint name says 10.5, verify) |
| Clearance | 1.0 |
| Control PCB | 1.60 |
| J9 Arduino header, vertical, unmated | 8.5 |
| **Total** | **30.0** over 12.5 mm cans; **34.0 over 16.5 mm cans (too tall)** |

Over 16.5 mm cans the card only fits with a right-angle or low-profile J9 (about 28 mm total). The
header/socket mated height equals the gap: about 13.5 mm (over 680 µF) or 17.5 mm (over 220 µF).

## Route and check, in order

1. **Placement review before any copper.** Plot both sides; re-measure every distance above; get the user's OK.
2. **Netclasses and rules.** Put `Net-(M8-S)`, `Net-(M9-S)` and `Net-(M10-S)` (the 2.63 A sink current nets) in the **Power** class. Give the new R1 and sink sense nets their own class: narrow, routed as pairs, never joining a pour. Add a `.kicad_dru` custom rule for minimum via drill and track width on Power nets so the router cannot use Ø0.25 mm vias. Keep every via ≥ 0.3 mm drill (0.25 mm costs +$16.94 and a $16.84 test at JLCPCB). Design through-hole pads with ≥ 0.254 mm annular ring and 0.15 mm minimum track/space so 2 oz outer stays possible.
3. **Draw and solve the power copper** path by path (same solver method as `AUDIT_RESPONSE.md`): every neck ≤ 20 °C rise (IPC-2221) and every via within rating (Ø0.40 ≤ 0.97 A, Ø0.30 ≤ 0.80 A, Ø0.25 ≤ 0.71 A at 10 °C), at 1 oz and at 2 oz outer. That result decides D3.
4. **Lock the power copper, then route signals.**
5. **Final checks on the saved file:** DRC 0 errors / 0 unconnected under the 1.0 / 0.15 mm silk rule, no exclusions; no untied copper islands; In1 and In6 GND only; no LX on In3/In5; solver table re-run; stackup written into the board file once D3 is chosen.
