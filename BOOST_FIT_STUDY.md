# BOOST LED driver — fit study for a 33 × 78 × 90 mm enclosure

Generated 2026-09-08 from the real KiCad courtyards and pad geometry in
`BOOST.kicad_pcb` (273 footprints), not from estimates.

## Inputs and assumptions

| | |
|---|---|
| Enclosure interior | 33 mm H × 78 mm L × 90 mm W = 231.7 cm³ |
| PCB edge → wall clearance | 2 mm → max PCB **74 × 86 mm = 6,364 mm²** |
| PCB thickness | 1.6 mm |
| Underside gap | **4.6 mm**, fixed by the TO-220 body with its tab flat on the case floor |
| Total component courtyard | 8,891 mm² over 273 parts |

Two consequences of the 4.6 mm underside gap:

1. Any part taller than 4.6 mm **must** be on the top side. That is L1 (19 mm) plus
   twelve electrolytic cans (10.5–12.5 mm) plus three 47 µF cans (5.4 mm) —
   **3,126 mm², or 49 % of the whole board, with nowhere else to go.**
2. A through-hole part blocks its full courtyard on the side its body is on, but
   only its pads (plus a clearance ring) on the opposite side. The ten MOSFET
   bodies take 2,229 mm² of the underside; their pin fields cost only 387 mm² up top.

Add a thin insulating pad under each tab (the six distinct tab potentials must be
isolated from the case) and the underside gap becomes ~4.8 mm. It does not change
any conclusion below.

## Option 1 — one board, all ten MOSFETs on the underside

| Forced onto the TOP side | mm² | % of board |
|---|---:|---:|
| parts taller than the 4.6 mm gap (L1 + cans) | 3,126 | 49 % |
| through-hole bodies that live on top (lugs, LED pads) | 421 | 7 % |
| pin fields of the underside MOSFETs | 387 | 6 % |
| **unavoidable top-side load** | **3,934** | **62 %** |

| Forced onto the BOTTOM | mm² | % |
|---|---:|---:|
| ten TO-220 bodies | 2,229 | 35 % |

That leaves 3,114 mm² of low-profile parts to be shared out. Balanced, the result is

> **top 75 %, bottom 75 %.**

**Verdict: it does not fit in any useful sense.** The area arithmetic closes, but 75 %
courtyard occupancy on both sides of a board that also has to carry 40 A peak pours
is past the point where routing succeeds. For comparison, a dense consumer board
runs 50–60 %, and a mixed power/control board wants to stay under ~68 % because the
power nets need large uninterrupted copper, not slivers between parts.

Height is *not* the problem here — the stack is only 25.2 mm of the 33 mm available.
Floor area is the problem: 78 × 90 gives 6,364 mm² of usable PCB against 8,891 mm²
of parts.

## Option 2 — two stacked boards

Split as you proposed. Derived from the netlist, not from refdes guessing:

- **POWER** (120 parts, 7,274 mm²): M1–M10, L1, TVS, all bulk capacitors, the four
  UCC21520 gate drivers, R1 + INA241 current sense, the three linear
  current-regulator channels (U6/U11/U12 + shunts R7/R52/R53 + gate resistors
  R22/R50/R56), the 12 V/5 V/analog 5 V regulators, power lugs and LED pads.
- **CONTROL** (153 parts, 1,617 mm²): 74HC00 NANDs, 74HC14 inverters, CD74HC4066,
  CD4017 counter, 74HC4051 mux, MCP4451 digital pot, error amps, comparators,
  headroom servos, Arduino header.

| Board | Size | Parts | Courtyard | Top | Bottom | |
|---|---|---:|---:|---:|---:|---|
| POWER | 74 × 86 mm | 120 | 7,274 mm² | 62 % | 62 % | workable |
| CONTROL | 42 × 42 mm | 153 | 1,617 mm² | 47 % | 47 % | comfortable |
| CONTROL (full size) | 74 × 86 mm | 153 | 1,617 mm² | 13 % | 13 % | wasteful |

**Verdict: this fits, with margin.** The control board only needs about 42 × 42 mm
at a comfortable 47 % per side; making it full size buys nothing and costs cable space.

### The split lands in exactly the right place

21 conductors cross between the boards:

| Type | Count | Signals |
|---|---:|---|
| gate-driver **inputs** (logic level) | 7 | `M1_ON`, `M2_ON`, `ena_out_1/2/3`, `out_2_on`, `out_3_on` |
| rail feedback (high-Z DC) | 3 | `.1Vout_1/2/3` |
| LED current setpoint (high-Z DC) | 3 | `IREF1/2/3_input` |
| servo drain sense (high-Z DC) | 3 | the three 4066 inputs |
| current-sense output (DC) | 1 | `Current` |
| supply rails | 4 | `GND`, `5V`, `analog_5V`, `12V` |

Every crossing is either logic-level or high-impedance DC. **No gate drive and no
power-stage current crosses the connector** — the four UCC21520s stay on the power
board with their FETs. That is the constraint your handoff document called out
(§10: a board-to-board connector's 5–15 nH in the gate return would cost 40–120 V
at 8 A/ns), and this split satisfies it.

Use a 26-way 2 × 13 ribbon or stacking header: 21 conductors plus ~5 interleaved
ground returns.

## Height stacks

| | Option 1 | Option 2a (both full size) | Option 2b (42 × 42 control) |
|---|---:|---:|---:|
| TO-220 bodies under the board | 4.60 | 4.60 | 4.60 |
| power PCB | 1.60 | 1.60 | 1.60 |
| tallest top-side part | 19.00 (L1) | 19.00 (L1) | 12.50 (680 µF can) |
| clearance to control board | — | 1.00 | 1.00 |
| control PCB | — | 1.60 | 1.60 |
| control parts, facing up | — | 2.65 | 2.65 |
| **total** | **25.20** | **30.45** | **23.95** |
| **spare to lid** | **7.80** | **2.55** | **9.05** |

In 2b the control card is sited over the capacitor field rather than over L1, so it
sits 6.5 mm lower. L1 still peaks at 25.2 mm, well under the lid.

## Space left for cable routing

Box interior 231.7 cm³. Component bodies occupy 59.3 cm³.

| | Option 1 | Option 2a | Option 2b |
|---|---:|---:|---:|
| PCB slabs | 10.2 cm³ | 20.4 cm³ | 13.0 cm³ |
| total free volume | 162.2 cm³ (70 %) | 152.0 cm³ (66 %) | 159.3 cm³ (69 %) |
| **clear headroom above the stack** | **7.80 mm → 54.8 cm³** | **2.55 mm → 17.9 cm³** | **7.80 mm → 54.8 cm³** |
| 2 mm perimeter gutter, full height | 21.6 cm³ | 21.6 cm³ | 21.6 cm³ |
| inter-board cavity beside the control card | — | — | 20.7 cm³ |
| **usable for cable** | **76 cm³** | **40 cm³** | **97 cm³** |

The perimeter gutter is 2 mm × 33 mm = **66 mm² of cross-section per side**, which
takes **3 × 10 AWG** or **9 × 16 AWG** cables lying side by side. That is the number
that matters for getting the battery pair in and the six LED wires out.

Option 2b also leaves 4,600 mm² of the power board's top surface open to the lid —
the control card covers only 28 % of it — so cable can lie flat across the board
rather than being forced round the edges.

## Recommendation

**Option 2b.** Two boards: a 74 × 86 mm power board and a 42 × 42 mm control card
mounted on standoffs over the capacitor bank, joined by a 26-way ribbon.

- Both boards route at sensible density (62 % and 47 %).
- 23.95 mm stack in a 33 mm box, 9 mm spare.
- 97 cm³ of usable cable volume — more than the single-board option, because the
  small control card frees the whole headroom above L1 *and* adds an inter-board cavity.
- The split is at the gate-driver inputs, so nothing fast or high-current crosses
  the connector.

The one-board option is not viable at 78 × 90 mm. If you want to keep it to one
board, the ways out are to grow the floor to about 100 × 90 mm, or to remove the
tall parts — the twelve electrolytic cans and the 19 mm inductor are 49 % of the
board on their own, and they are the whole reason the top side runs out.
