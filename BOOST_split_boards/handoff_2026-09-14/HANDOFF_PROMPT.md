# Handoff: re-place and re-route the BOOST power board (and shrink the control card)

2026-09-14. From a review session to the AI that routed `BOOST_split_boards/` and wrote
`AUDIT_RESPONSE.md`. Read this whole prompt before changing anything.

## 0. What you're being asked to do

The 2026-09-14 power board (via landings, LX pours removed, J4 silk) is DRC-clean but still fails the
audit, and further patching has stopped paying off. The problems are placement problems. The user has
decided to **re-place the power board around its current loops and re-route it**, after a set of
schematic changes, and to **shrink the control card and give it mounting holes and a stacking
header**.

Work in this order and check in with the user at each ★:

1. Read the files in §1.
2. ★ Confirm the open items in §8 that block your step (at least divider placement, TO-220 variant/orientation, 220 µF can height, header part).
3. Make the schematic changes in §4. ERC 0 errors / 0 warnings. Export the netlist and check every change landed.
4. Re-place the power board using `REPLACE_BRIEF_v2.md` (stages 1–6). ★ Show the user a placement plot and the distance table against the targets before any copper.
5. Draw the power copper deliberately, then solve it (your `AUDIT_RESPONSE.md` §1 method) at 1 oz and at 2 oz outer. ★ The user chooses the copper weight from that result (§3.7).
6. Route signals, run the checks in §6, and write a report in the `AUDIT_RESPONSE.md` style.
7. Re-place and re-route the control card (§3.5, §3.6).

Ground rules (same as before): never weaken a DRC rule or add an exclusion; keep the 1.0 / 0.15 mm
silk rule; back up shipped files to `previous/<date>/` before replacing them; keep work-in-progress
boards clearly marked not for fabrication; don't guess part specs or pinouts: read datasheets, and say
when something can't be verified.

## 1. Files

### In this handoff folder (`BOOST_split_boards/handoff_2026-09-14/`)

| File | What it is |
|---|---|
| `HANDOFF_PROMPT.md` | This prompt |
| `REPLACE_BRIEF_v2.md` | **Placement plan**: decisions table, placement rules by stage with targets and today's distances, keep-outs, stack budget, route-and-check gates |
| `SIMULATION_REPORT.md` | LTspice lead-inductance, M1 turn-off resistor sweep and dead-time analysis, method, caveats, pending sims |
| `replace_brief_page_saved_2026-09-14.html` | Saved copy of the web brief with the user's original choices and notes (superseded by v2) |
| `placement/distances_power_board_2026-09-14.txt` | Pad-to-pad distances on the shipped power board for every power path |
| `placement/output_cap_reassignment_2026-09-14.txt` | Shows that reshuffling the nine 220 µF caps between existing spots isn't enough |
| `placement/fps_power.json`, `fps_control.json` | Every footprint's position, side, value and pad nets from the shipped boards |
| `placement/placement.py`, `distances.py`, `capswap.py` | Scripts that produced the above (plain Python, read the `.kicad_pcb` text) |
| `sim/HYG180N10_REV5.lib` | FET model with lead inductance (copy of the edited library) |
| `sim/netlists/*.net` | Every simulation netlist (see `SIMULATION_REPORT.md` §9) |
| `sim/scripts/measure.py`, `deadtime.py`, `sweep2.sh` | Post-processing and run scripts |

### Already in the project

| Path (from `led-driver/`) | What it is |
|---|---|
| `BOOST_split_boards/BOOST_AUDIT.md` (+ `.html`, `_density_maps.png`) | The independent copper audit (13 checks, 5 stop-ship findings) |
| `BOOST_split_boards/AUDIT_RESPONSE.md` | Your response: what was fixed, solver method, tried-and-rejected list |
| `BOOST_split_boards/BOOST_power.kicad_pcb` / `.kicad_pro` | Shipped power board (SHA-256 `f4807690…`), the starting point |
| `BOOST_split_boards/BOOST_control.kicad_pcb` / `.kicad_pro` | Control board (60 × 60 mm, 8 layers, 154 parts, DRC clean) |
| `BOOST_split_boards/wip/BOOST_power_M8_WIP_NOT_FOR_FAB.kicad_pcb` | The M8 sink corridor experiment |
| `BOOST_split_boards/README.md`, `ROUTING_REPORT.md` | Routing notes; README explains you were asked not to move parts |
| `BOOST-github/BOOST/BOOST.kicad_sch` (+ `.kicad_pro`, `BOOST_9-2_1013.net`) | The single schematic both boards come from. J10/J11 exist only in the PCBs today. |
| `BOOST-github/BOOST_CONTEXT_TRANSFER.md` | Design decisions, thresholds, simulation results and cautions (§5, §6, §13 matter) |
| `BOOST-github/LTspice/BOOST/BOOST.asc` + libraries | LTspice design. `HYG180N10.lib` here is REV 5 (uncommitted git change). An identical older copy lives in `Documents/LTspice/BOOST-github/LTspice/BOOST/` (the user's LTspice session uses that one). |
| `BOOST_FIT_STUDY.md`, `BOOST_option2b_placement.png` | Enclosure fit study (78 × 90 × 33 mm case, stack heights); the current placement came from option 2b |

## 2. Why re-place (evidence)

- Audit status after your last pass: of the 10 failed checks none passes; stop-ship items 1 (LED sink
  current on 0.15 mm tracks), 3 (commutation loop), 4 (current sense 32 % high) and 5 (stack height)
  are open; item 2 (single vias) is 12 of 13 fixed.
- Every remaining item traces to placement. Straight-line pad-to-pad distances on the shipped board:

| Path | Current | Now | Target |
|---|---|---|---|
| Sink FET source → its shunt (M10→R52, M9→R53, M8→R7) | 2.63 A | 48 / 33 / 39 mm | ≤ 5 mm |
| Sink FET drain → its LED pad (M10→J4, M9→J7, M8→J6) | 2.63 A | 49 / 61 / 51 mm | ≤ 15 mm |
| Rail FET → its own three caps (M2, M3, M4) | 7–8 A RMS | 30–67 mm | ≤ 15 mm |
| L1 LX pad → M5 drain | 8.35 A | 59 mm | ≤ 15 mm |
| M5 ↔ M4 shared source | 8.35 A | 22 mm | adjacent |
| U8 gate driver → M4 gate | edges | 28 mm | ≤ 15 mm |
| R1 → U25 (INA241) | sense | 41 mm | ≤ 10 mm |
| M1 → D19 (TVS) | clamp | 29 mm | ≤ 5 mm |

- Each rail FET's nearest caps belong to other rails. Reassigning the nine identical 220 µF caps to the
  existing spots only halves the total distance (401 → 199 mm).

## 3. Decisions

### 3.1 FETs stay TO-220; slow M1's turn-off (delete D12, R15 = 10 Ω)

Keep all ten HYG180N10 in TO-220, tab-down on the case floor (the user hand-solders them).

LTspice with typical TO-220 lead inductance showed the "clean" 35 V switch node was an artifact of zero
parasitic inductance. With leads plus the audit's copper loop inductance and today's gate drive, M1's
die hits its 100 V avalanche clamp on every turn-off and the TVS absorbs 315 mW. A 10 Ω turn-off path
gives M1 die 68 V, TVS 38 mW, no avalanche, +0.73 W in M1 (4.09 → 4.82 W), no shoot-through. Deleting
D12 and making R15 10 Ω simulates identically to a split network; M1 turns on at ≤ 0.3 A so slow
turn-on is harmless, and M1's gate stays ≤ 0.18 V while held off. Full data: `SIMULATION_REPORT.md` §4–§5.

| Ref | Today (KiCad, power board) | Change |
|---|---|---|
| R15 | 5.1 Ω 0805, B.Cu, `Net-(D12--)` (U19 pin 15 OUTA) ↔ `GATE_M1` | **10 Ω** (0805 is fine: ~9 mW, ~1 A peak) |
| D12 | SOD-123 across R15 (pad 2 `GATE_M1`, pad 1 `Net-(D12--)`) | **Delete** (it was also inside a TO-220 washer keep-out) |

Put the R15 footprint where it can take 4.7–22 Ω for bench tuning (the model has half the real
Miller charge, so the real edge will be slower).

### 3.2 Longer rail-side dead time (R13/R23/R47 = 150 Ω)

The dead time is ~30 ns, not ~100 ns: the logic only delays the rail FET's driver by ~5 ns after
M1's driver; the 100 Ω rail-side gate resistors set the rest. With M1 at 10 Ω, the margin from M1's
drain starting to rise to the rail FET reaching threshold falls from 21–25 ns to 13–18 ns, and a rail
FET at the 1.0 V threshold corner would reach threshold ~14 ns sooner. Raising these resistors
restores the margin (RC estimate: 1.8 V reached at ~45 ns instead of ~30 ns). **Not yet simulated**
(`SIMULATION_REPORT.md` §8 item 1).

| Ref | Today | Change |
|---|---|---|
| R13 | 100 Ω 0603, `GATE_M2` ↔ `Net-(D11--)` (U15 OUTA) | **150 Ω**; keep D11 |
| R23 | 100 Ω 0603, `Net-(D14--)` (U10 OUTA) ↔ `GATE_M3` | **150 Ω**; keep D14 |
| R47 | 100 Ω 0603, `GATE_M4` ↔ `Net-(D13--)` (U8 OUTA) | **150 Ω**; keep D13 |

Unchanged: LX-side gate resistors R60 (5 Ω, `GATE_M7`), R70 (5.1 Ω, `GATE_M6`), R59 (5.1 Ω, `GATE_M5`)
with D2/D8/D22; sink gate resistors R22/R50/R56 (100 Ω). Note: the context document says "never reduce
R13/R23/R47"; this change *raises* them, which is the safe direction.

### 3.3 R1: four-terminal 2 mΩ shunt

**Part: Bourns CSS4J-4026K-2L00F**: CSS4J-4026 series metal-strip current sense resistor,
**2 mΩ ±1 %, 4 W, ±75 ppm/°C, four-terminal (Kelvin)**, 4026 package (10.1 × 6.6 mm; RS lists
10.06 × 6.6 × 2.4 mm for the -2L00FE variant), −55 to +170 °C.

Where to buy (checked 2026-09-14):
- LCSC / JLCPCB assembly: **C2076167**, <https://www.lcsc.com/product-detail/C2076167.html>. $1.0882 each (1+), 1500/reel. **Out of stock** on 2026-09-14.
- LCSC variant CSS4J-4026K-2L00FE (400/reel): **C1848567**, $1.7614 each. Also out of stock.
- Digi-Key: <https://www.digikey.com/en/products/detail/bourns-inc/CSS4J-4026K-2L00F/6023759>. Listed at $2.19 (stock not confirmed; the product page is behind a bot check).
- Newark: <https://www.newark.com/bourns/css4j-4026k-2l00f/current-sense-res-0r002-1-4-w/dp/98Y2134>
- Farnell UK: <https://uk.farnell.com/bourns/css4j-4026k-2l00f/res-current-sense-0r002-4026/dp/2576352RL>
- Datasheet: <https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf>
- Symbol/footprint (verify against the datasheet): <https://www.snapeda.com/parts/CSS4J-4026K-2L00F/Bourns/view-part/>

Why it fits: R1 dissipates 0.853 W (LTspice) = 21 % of rating; 4 W at 2 mΩ ≈ 44.7 A, above 20.7 A
RMS and the 40.5 A peak; ±75 ppm/°C is ~0.4 % over 50 °C of self-heating. It keeps 2 mΩ, so the
INA241A3's 0.1 V/A scale, V_err full scale (4.76 V) and RESET behaviour are unchanged.

Implementation:
- New 4-pin symbol and the **land pattern from Bourns' datasheet** (the review session could not open
  it; confirm which terminals are force and which are sense).
- Current pads carry the `Vin` and `rsense_lo` pours. Sense pads get new nets: **`ISNS_P`** (Vin side →
  U25 pin 8 IN+) and **`ISNS_N`** (rsense_lo side → U25 pin 1 IN−). Today U25's inputs sit directly on
  the Vin/rsense_lo pours 41 mm away (audit item 3: reads 32 % high).
- Route the sense pair together, away from L1 and LX, touching no pour.
- JLCPCB assembly needs LCSC stock: check JLCPCB's parts pre-order at order time, or the user
  hand-solders it.

Backup if stock doesn't come back: **CSS4J-4026R-1L00F** (LCSC **C2076400**, 1 mΩ, 4 W, ±75 ppm/°C,
422 in stock on 2026-09-14, $1.7049) with U25 changed from INA241A3 to **INA241A4** (gain 100 V/V, same
1.1 MHz bandwidth, ±10 µV max offset; <https://www.ti.com/product/INA241A>). That keeps 0.1 V/A and
halves R1's loss (~0.43 W) but halves the sense signal, so leftover layout error counts double. Check
INA241A4 stock.

Rejected: Vishay WSK25122L000FEA (LCSC C3997408, four-terminal 2 mΩ, in stock) is rated only 1 W and
±250 ppm/°C.

### 3.4 LED sink sense: net-ties at the shunts

Keep R7, R52, R53 (50 mΩ, 2512). Add a net-tie footprint at each shunt's top pad so each sink op-amp
senses the shunt directly (audit items 1/9: today they sense 42–270 mΩ upstream, LEDs get 45–84 % less
current):

| Channel | Sink FET | Shunt | Op-amp IN− (pin 4) | Suggested sense net |
|---|---|---|---|---|
| ch1 | M10 (`Net-(M10-S)`) | R52 | U11 | `SNS_CH1` |
| ch2 | M9 (`Net-(M9-S)`) | R53 | U12 | `SNS_CH2` |
| ch3 | M8 (`Net-(M8-S)`) | R7 | U6 | `SNS_CH3` |

Put `Net-(M8-S)`, `Net-(M9-S)` and `Net-(M10-S)` in the Power netclass (they carry 2.63 A).

### 3.5 Board-to-board link: stacking header, not a ribbon

- **Type:** 2 × 15, **2.54 mm pitch**, male pin header on the power board (J10, top side) and female
  socket on the control card's underside (J11), placed so pin n meets pin n. (Today both are male
  1.27 mm and mirrored, so they can't mate.)
- **Mated height = standoff height** = gap from power-board top to card bottom: ~13.5 mm if the card
  sits over the 680 µF cans (12.5 mm), ~17.5 mm over 16.5 mm-tall 220 µF cans. Tall pairs are routine at
  2.54 mm and rare at 1.27 mm. Pick parts (LCSC where possible) and confirm the mated height from their
  datasheets.
- **Why a header:** the link carries 25–131 mV current setpoints, drain-sense lines from 90 kΩ
  dividers, rail feedback and the INA241 output; a header keeps them ~15–18 mm long instead of a ribbon
  folded past L1 and the switch node in a sealed underwater case, and it's mechanically solid on
  standoffs. For bring-up, a 2 × 15 2.54 mm jumper cable lets the boards run side by side.
- **Pinout rules:** a GND pin beside every analog signal (`Current`, `.1Vout_1/2/3`, `IREF1/2/3_input`,
  `Net-(U106A-A)`, `Net-(U106B-A)`, `Net-(U106C-A)`); `Current` not beside `12V`; logic (`M1_ON`, `M2_ON`,
  `ena_out_1/2/3`, `out_2_on`, `out_3_on`) grouped away from analog. Today's mapping is in
  `BOOST_AUDIT.md` item 8.
- **Add J10 and J11 to the schematic** (they exist only in the PCBs).
- **Dividers straddle the connector** (audit item 8): tops on the power board (18 k R9/R35/R43; 910 k
  R25/R87/R94), bottoms (2 k, 100 k) on the control card. Keep both resistors of each divider on one
  board. ★ Ask the user which board. Suggestion: both on the control card, so the connector carries the
  rail/drain voltages from low impedance and an unplugged card reads 0 V.
- A 2 × 15 2.54 mm header is 38.1 mm long, tight on a 42 mm card: plan the holes around it or grow the card to ~45 mm.

### 3.6 Control card: smaller, with mounting holes

- **Shrink** from 60 × 60 mm to ~42 × 42 mm (the user notes there's plenty of empty space), up to ~45 mm
  if the header and holes need it. Site it over the capacitor field, clear of L1 (19 mm tall). No
  60 × 60 card can avoid L1 in the 78 × 90 mm case.
- **Mounting holes:** 4 × M3 (3.2 mm) near the corners, non-plated by default with a ~7 mm diameter
  copper keep-out on all layers (ask the user if the standoffs should be grounded). Matching standoff
  holes on the power board inside the card outline, with the same keep-outs, clear of power pours.
  Standoff length = header mated height.
- **Stack budget** (33 mm internal): 4.83 (TO-220 + insulator) + 1.6 (power PCB) + tallest part under
  the card + 1.0 + 1.6 (card) + J9. Over 12.5 mm cans with a vertical J9 (8.5 mm): 30.0 mm, fits. Over
  16.5 mm cans: 34.0 mm, too tall; use a right-angle or low-profile J9 (~28 mm). Mated Arduino jumper
  housings on a vertical J9 would exceed the lid either way; prefer a right-angle J9 at the card edge.
- The card will need a full re-place and re-route; keep its current quality bar (DRC 0/0).

### 3.7 Copper weight: undecided (decide from the routed power copper)

The user wants to see how wide the power copper can be made before choosing.

JLCPCB quote, 2026-09-14, 5 boards, 74 × 86 mm, 8 layers, 1.6 mm, default options, 10–11 day build,
before ~$28 shipping:

| Option (outer / inner) | Price | Adders |
|---|---|---|
| A: 1 oz / 0.5 oz (fab default) | $90.00 | not acceptable: inner layers can't carry rail currents |
| **B: 1 oz / 1 oz** | **$106.68** | inner +$16.68 |
| **C: 2 oz / 1 oz** | **$141.68** | outer +$35.00, inner +$16.68 |
| D: 2 oz / 2 oz | $242.80 | outer +$35.00, inner +$35.19, stackup fee +$82.61 |

- Epoxy-filled, capped vias are free on 6+ layer boards (so via-in-pad costs nothing extra).
- Ø0.25 mm drills add $16.94 plus a $16.84 4-wire Kelvin test: **keep every via ≥ 0.3 mm drill**.
- JLCPCB 2 oz outer rules: 0.15 / 0.15 mm minimum track/space, **≥ 0.254 mm annular ring** on
  through-hole pads. Design to these regardless, so C stays possible.

Track width for a 20 °C rise (IPC-2221, long conductor):

| Current and layer | 0.5 oz | 1 oz | 2 oz |
|---|---|---|---|
| 20.7 A, outer (Vin, rsense_lo) | — | 12.9 mm | 6.4 mm |
| 8.35 A, inner (Vout_3, m4_source) | 19.2 mm | 9.6 mm | 4.8 mm |
| 8.35 A, outer | — | 3.7 mm | 1.8 mm |
| 2.63 A, inner (LED sink) | 3.9 mm | 1.9 mm | 1.0 mm |
| 2.63 A, outer (LED sink) | — | 0.75 mm | 0.37 mm |

Where B and C really differ: surface-mount pads carrying > 10 A, where all current enters on the outer
layer.
- R1's current pads: IPC estimate for a 3.35 mm 2512 pad at 20.7 A is ~184 °C rise at 1 oz vs ~59 °C at
  2 oz. The CSS4J-4026 is only 6.6 mm wide, so its current pads are ≤ ~6 mm: roughly ~70 °C at 1 oz vs
  ~23 °C at 2 oz. R1 also dissipates 0.85 W there.
- L1's pads (8 mm): ~44 °C vs ~14 °C.
- Filled vias in R1's pad don't rescue 1 oz: one row of ~3 Ø0.3 vias carries ~2.4 A of the 20.7 A.
- Through-hole parts (TO-220s, J1/J2 lugs) spread current over all layers, so B and C are about equal there.

**Decision rule:** solve the drawn power copper at B and C. Choose B only if every neck is ≤ 20 °C
rise and every via is within rating at 1 oz; otherwise C. Then write the stackup into both board
files so the gerber job matches the order.

### 3.8 New: Arduino pin that holds M1 off

The user wants an Arduino header pin that can hold M1 off, the same way the "0 error" signal and the
supply-good comparator already do. On the control card that node is **`Net-(D1--)`** (LTspice `N017`):

| Member of `Net-(D1--)` | Role |
|---|---|
| D1 cathode (anode `0err_hi`) | "0 error": no demand → M1 off |
| D15 cathode (anode `Out-`) | SR latch says M1 off |
| D24 cathode (anode `Net-(D24-+)` = U21 MCP6561 output) | supply-good comparator (the user's 12 V check) |
| R26 220 Ω pin 1 → `Net-(C19-Pad1)` (R51 2 k from `Out-`, C19 330 pF to GND) | pull-down path and the ~505 ns M1 turn-on delay |
| U104 (74HC14) pin 1 → pin 2 = `M1_ON` | M1_ON = NOT(node): node high → M1 off |

Add:
- A new pin on **J9** (today 1 × 10, 2.54 mm: 1 Vref_1_arduino, 2 Vref_2_arduino, 3 Vref_3_arduino,
  4 IREF1, 5 IREF2, 6 IREF3, 7 SCL, 8 SDA, 9 5V, 10 GND) → make it 1 × 11 with **pin 11 =
  `ARD_M1_INHIBIT`**.
- A new diode, the same part/footprint as D1/D15/D24 (SOD-123): **anode on `ARD_M1_INHIBIT`, cathode on
  `Net-(D1--)`**. Rename `Net-(D1--)` to `M1_INHIBIT` for clarity.
- Optional: 100 kΩ from `ARD_M1_INHIBIT` to GND so a disconnected or booting Arduino pin can't float.

Behaviour: Arduino pin HIGH → node high → `M1_ON` low → M1 off immediately. LOW or unconnected → no
effect. Releasing it lets M1 turn back on after the normal R26/C19/R51 delay. It draws ~2 mA from the
Arduino pin (through R26 + R51 into `Out-`), like D1/D24 do today. **The Arduino must be 5 V logic**:
after the diode drop the 74HC14 (5 V) needs up to ~3.5 V at its input, which a 3.3 V board can't
guarantee. Everything is on the control card, so J10/J11 don't change for this.

## 4. Schematic change list (`BOOST-github/BOOST/BOOST.kicad_sch`)

1. R1 → Bourns CSS4J-4026K-2L00F, 4-pin symbol + datasheet land pattern; new nets `ISNS_P` (→ U25.8) and `ISNS_N` (→ U25.1).
2. Net-tie footprints at R52, R53, R7 top pads; U11.4 → `SNS_CH1`, U12.4 → `SNS_CH2`, U6.4 → `SNS_CH3`.
3. R15 5.1 → **10 Ω**; delete **D12**.
4. R13, R23, R47 100 → **150 Ω** (D11, D14, D13 stay).
5. Add **J10** (2 × 15 2.54 mm male, power board) and **J11** (2 × 15 2.54 mm female, control card) with the new pinout (§3.5).
6. Divider resistors on one board each (★ user choice, §3.5).
7. J9 → 1 × 11 (right-angle if the stack needs it), new diode + optional 100 kΩ, nets `ARD_M1_INHIBIT` and `M1_INHIBIT` (§3.8).
8. Mounting holes: 4 × M3 on the control card, 4 × standoff holes on the power board.

Then ERC 0/0, export the netlist, diff it against `BOOST_9-2_1013.net`, and carry the changes into both
split boards the same way you built them.

Cautions from `BOOST_CONTEXT_TRANSFER.md` §13–§14 for schematic work:
- KiCad wires attach by pin **position**, not pin number: don't swap symbols for stock ones without re-checking every connection.
- Verify connectivity from an exported netlist, not by parsing the raw `.kicad_sch`.
- Preserve: the 22 mV SET/RESET mutual-exclusion margin (R18/R19/R20, R11/R16/R17); V_err full scale 4.76 V below the INA241 clip 4.98 V (R27/R37/R45 = 4.7 k); the split gate drive's body-diode orientation (M2/M3/M4 body diodes point with the discharge current).

## 5. Placement (power board)

Follow `REPLACE_BRIEF_v2.md` stages 1–6. In short:
1. **Input loop:** C40/C69/C85, R1, L1, M1 tight on one outer layer; J1/J2 on the nearest edge; **D19 at M1's pins**; U19 + R15 beside M1; U25 beside R1.
2. **LX node:** L1's LX pad central to M1/M7/M6/M5 on outer copper; **M5 leaves the sink row**; no LX on In3/In5.
3. **Channel pairs:** M7 beside M2, M6 beside M3, M5 beside M4; U15/U10/U8 beside their pairs.
4. **Banks and LED pads:** each rail's three caps at its own rail FET; LED pads J3+J4, J8+J7, J5+J6 side by side at the edge.
5. **Sinks:** R52/R53/R7 at M10/M9/M8 source pins; J4/J7/J6 at their drains; U11/U12/U6 between shunt and FET; ≥ 2 GND vias per shunt return.
6. **Keep-outs:** TO-220 washer keep-outs (3.75 mm radius from each tab hole centre, all layers); U16 (TO-263, 4.83 mm) to F.Cu; control-card outline, header and standoff holes; J10's GND pins outside M1's return-current field.

Remember the TO-220s mount horizontally on B.Cu with tabs toward the case floor, so their pin rows and
tab holes constrain everything else. ★ Get the user's OK on the placement before any copper.

## 6. Routing and checks

- Netclasses: sink current nets in Power; sense nets (`ISNS_P/N`, `SNS_CH1–3`) in their own narrow class, routed as pairs, never touching a pour.
- `.kicad_dru` custom rules: minimum via drill (≥ 0.3 mm; prefer 0.4 mm arrays) and minimum track width on Power nets, so the router can't use Ø0.25 mm vias.
- Draw power copper by hand/script path by path; solve every branch (neck ≤ 20 °C IPC rise; vias Ø0.40 ≤ 0.97 A, Ø0.30 ≤ 0.80 A, Ø0.25 ≤ 0.71 A) at 1 oz and 2 oz outer; report both for the copper decision.
- Lock power copper, then route signals.
- Final checks on the saved files: DRC 0 errors / 0 unconnected with no exclusions and the 1.0 / 0.15 mm silk rule; no untied copper islands; In1/In6 GND only; no LX on In3/In5; the solver table; stackup written in once D3 is chosen.
- Re-check the audit's items: commutation loop area, R1 Kelvin, sink sense points, capacitor current sharing (C74 was at 90 %), via loading, J10/J11 annular ring (≥ 0.254 mm), silk, mechanical fit.

## 7. Simulation status (for context)

- `HYG180N10.lib` REV 5 (lead inductance) is only in `led-driver/BOOST-github/LTspice/BOOST/`.
- With REV 5 on M8–M10 the full schematic stalls; use `HYG180N10_NOLEADS` on the sinks for now.
- `BOOST.asc`'s servo `.ic` points at renumbered nodes (N064/N065/N058 → now N061/N062/N055); fix with net labels.
- **Not yet simulated:** R13/R23/R47 = 150 Ω together with R15 = 10 Ω / no D12, nominal and at the VTO = 1.0 V corner; the re-placed board's own loop inductance; the sink FET convergence issue.

If you have LTspice access, run `SIMULATION_REPORT.md` §8 item 1 before fabrication; otherwise flag it
in your report.

## 8. Open items for the user (★ ask; don't decide silently)

1. Copper weight B vs C (after the power-copper solve, §3.7).
2. Divider resistor board (§3.5).
3. TO-220 variant (FB full-pack plastic tab vs AB bare tab) and footprint orientation (`TO-220-3_Horizontal_TabDown` puts the tab against the board; confirm in 3D), insulator per row, tab pitch (1.09 mm gaps today).
4. The real height of the 220 µF cans (Panasonic EEH-ZU1H221P lists 16.5 mm; the footprint says 10.5 mm), which decides where the card can sit and whether J9 must be right-angle.
5. Header/socket part numbers and mated height; standoff type (nylon/metal) and whether mounting holes are grounded.
6. Sink op-amp accuracy: MCP6241 offset ±5 mV ≈ ±4 % per channel; zero-drift op-amp? (context document open item 7)
7. BOM gaps from the audit: 680 µF part number (EEH-ZU1E681UP not on Panasonic's series page), shunt ratings, LCSC stock for R1.
8. Who updates `BOOST.asc` and runs the pending simulations (§7).

## 9. What to hand back

- Schematic changes (ERC report, netlist diff).
- Power-board placement plot + distance table vs `REPLACE_BRIEF_v2.md` targets (★ before copper).
- Power-copper solver tables at 1 oz and 2 oz outer (★ copper decision).
- Routed power board and re-placed/re-routed control card with DRC reports, geometry checks and a
  report in the `AUDIT_RESPONSE.md` style: what changed, before/after numbers, what's still open.
- Old files backed up in `previous/<date>/`; WIP clearly marked.
