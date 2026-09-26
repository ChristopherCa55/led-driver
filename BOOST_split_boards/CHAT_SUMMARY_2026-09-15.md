# BOOST LED driver: summary of the design/simulation chat (2026-09-15)

Hand this to a new chat. It covers what was decided, what was simulated, the enclosure
fit work, and what is still open. The routing/placement AI works from
`handoff_2026-09-14/HANDOFF_PROMPT.md`; where this file and that one disagree, this
file is newer (see "Supersedes" at the end).

## 1. The project

- Boost LED driver, Vin about 14 V from a battery, three LED channels.
- Two boards: `BOOST_power.kicad_pcb` (74 x 86 mm, 8 layers, 121 parts) and
  `BOOST_control.kicad_pcb` (a card that stacks on top of the power board).
- Power stage: L1 6.8 uH (CSCF3218, 19 mm tall), M1 low-side switch, back-to-back
  channel pairs M7/M2, M6/M3, M5/M4, linear LED sinks M8/M9/M10 with 50 mOhm shunts
  R7/R52/R53. All FETs are HYG180N10 in TO-220, tab-down against the case floor.
  D19 is a 5KP54A TVS across M1. U25 is an INA241A3 on the 2 mOhm R1 (0.1 V/A).
- Peak inductor current 40.5 A; input bank about 10.4 A RMS at 14 V.
- The board was routed once, audited (`BOOST_AUDIT.md`), revised (`AUDIT_RESPONSE.md`),
  and the conclusion of this chat is to **re-place the parts and re-route**, not to
  patch the existing layout: the parts on each high-current path sit 30-60 mm apart
  because the original placement came from a courtyard-packing fit study, not from
  current paths.

## 2. Decisions made in this chat

| ID | Decision | Status |
|---|---|---|
| D1 | Keep the TO-220s. Slow M1's turn-off: **delete D12, change R15 from 5.1 to 10 Ohm**. | Decided, simulated |
| D1b | Rail gate resistors R13/R23/R47 100 Ohm -> **220 Ohm** (keep D11/D13/D14). | Decided (see 3.4) |
| D2 | **Four-terminal R1**: Bourns CSS4J-4026K-2L00F, Kelvin sense to U25 (ISNS_P -> U25.8, ISNS_N -> U25.1). Backup: CSS4J-4026R-1L00F (LCSC C2076400) with an INA241A4. Net-ties at the sink shunts R7/R52/R53 for the op-amp sense. | Decided |
| D3 | **Copper weight still open.** Route the power copper at 1 oz and at 2 oz outer, then pick B (1 oz all, $106.68) or C (2 oz outer / 1 oz inner, $141.68). Never 0.5 oz inner. | Open until routing |
| D4 | Board-to-board link is a **stacking header + socket**, not a ribbon. | Decided |
| D5 | Control card shrinks to about **42 x 42 mm** with **4x M3 mounting holes** and standoffs. | Decided |
| D6 | New **Arduino header pin -> diode -> M1 inhibit node** (`Net-(D1--)`, to be renamed `M1_INHIBIT`), optional 100k pulldown. The Arduino must be a 5 V board. | Decided |
| D7 | The original input capacitor **EEH-ZU1E681UP is available** (the audit was wrong). Three are used; LCSC C29664285 had 10 in stock, which is enough. | Decided |
| D8 | **FET tab screws:** screw the 4 hottest (M1 about 4.8 W, M8/M9/M10 about 2.8-3.2 W); plus a rule that any FET whose body centre is more than 15 mm from a screw gets its own screw. 3.75 mm washer keep-out, nothing tall over a hole, bodies flat on the board, compliant pad, MLCCs away from the screws. | Decided |
| D9 | **Card stack height 21.21 mm** (Samtec ESQ-115-44-G-D socket on the power board + TSW-115-07-G-D header under the card). The card sits over the 16.5 mm output cans, never over L1. | Decided (see 4) |

## 3. Simulation work (LTspice)

### 3.1 What was changed in the model

`LTspice/BOOST/HYG180N10.lib` was edited to REV 5: the 3-terminal `HYG180N10` now
wraps the die in TO-220 package inductance (LD 4.5 nH, LS 7.5 nH, LG 7.5 nH, plus the
2.38 Ohm internal gate resistor). The original model is kept as `HYG180N10_NOLEADS`.
The file is git-tracked and **uncommitted**; the copy under `Documents/LTspice` was not
touched, and the `.asc` schematics were **not** updated with any of the changes below.

### 3.2 Why it matters

Without lead inductance the switch node peaked at 34.8 V and the TVS absorbed 1.5 mW,
which looked fine. With the leads in, the picture changes completely:

| Run | M1 die Vds | LX at the pins | TVS | Notes |
|---|---|---|---|---|
| No leads | 34.8 V | 34.8 V | 1.5 mW | the old, misleading result |
| Leads | 100.3 V | 64.8 V | 143 mW | avalanche on 124 of 124 turn-offs, di/dt 3.8 A/ns |
| Leads + copper inductance | 100 V | 67 V | 315 mW | M1 loss 4.09 W |

The body diode clamps at the die, not at the pins, so the pin voltage understates what
the silicon sees. Avalanche on every cycle is the thing being fixed.

### 3.3 R15 sweep (M1 turn-off resistor, with leads and copper)

| R15 | M1 die Vds | TVS | M1 loss | |
|---|---|---|---|---|
| 2.2 Ohm | 100 V | 224 mW | - | avalanche |
| 4.7 Ohm | 77.5 V | 57 mW | - | |
| **10 Ohm** | **68 V** | **38 mW** | **4.82 W** | **chosen** |
| 22 Ohm | 66.7 V | 20 mW | 5.18 W | |
| 47 Ohm | 64.3 V | 1.5 mW | 6.60 W | shoot-through, 7-8 A reverse |

With R15 = 10 Ohm, D12 can be deleted: the run with the diode removed is identical, M1's
gate never rises above 0.18 V while held off, and the inductor current at M1 turn-on is
at most 0.30 A, so a slow turn-on costs nothing.

### 3.4 Dead time (M1 off -> rail FET on)

The user believed this was about 100 ns. It is not:

- Driver logic alone: about 5 ns.
- Rail FET die Vgs crosses 1.8 V at 31-34 ns after the M1 off command (present circuit),
  or 39-41 ns with R15 = 10 Ohm.
- Margin from "M1's drain has reached the rail" to "rail FET starts conducting":
  21-25 ns now, 13-18 ns with the 10 Ohm change. No shoot-through in either case.

That margin is why the rail gate resistors go up. The other chat then simulated the
model's threshold corners: **150 Ohm gives about 0 ns margin at the VTO = 1.0 V corner,
220 Ohm gives 18-25 ns**, so 220 Ohm is the value to use (the handoff prompt still says
150 Ohm in section 3.2 - that is superseded).

### 3.5 Method notes for whoever runs LTspice next

- LTspice 26.0.1 batch: `LTspice.exe -netlist BOOST.asc` then `LTspice.exe -b file.net`.
  Run one at a time, or stagger launches by about 15 s; two at once and one silently
  fails to start. Do not run `LTspice.exe -help`, it opens a GUI and hangs.
- `.meas` FROM/TO is broken by the Tstart offset in the raw file, so all measurements
  are computed in Python from uncompressed raw files (`.options plotwinsize=0`).
  See `handoff_2026-09-14/sim/scripts/measure.py` and `deadtime.py`.
- `.save` cannot reach inside a subcircuit, hence a PROBE subckt that exports the die
  nodes Di/Si/Gi.
- Putting lead inductance on the sink FETs M8-M10 breaks convergence ("trouble with node
  m10:di"). Use `HYG180N10_NOLEADS` for the sinks.
- Node names are case-insensitive: a node called `m1_on` collided with the `M1_ON` net
  and quietly wrecked two runs. It was renamed `m1_ton`.
- The servo `.ic` line must be `.ic V(N061)=2.89 V(N062)=3.86 V(N055)=3.90`. The old
  `.ic V(N064)=2.7 V(N065)=3.7 V(N058)=3.7` refers to renumbered nodes and leaves the
  simulation running at a third of full power without any error.
- The netlists are UTF-8 (they contain a micro sign). LTspice 24 on another machine
  misreads them.

## 4. Enclosure fit

Box, as measured by the user: **128 x 90 x 33 mm**, floor 10 mm thick, with two 10 mm
diameter penetrator holes through the **floor**, centres at (9.5, 3.5) and (118.5, 3.5)
mm from the top-left corner of the 128 x 90 face. Each penetrator needs a 15 mm diameter
x 10 mm tall keep-out inside the box. The box is symmetrical, so either end can be the
LED end.

Layout that was checked and works:

- **Power board** in the right 78 x 90 mm end (x 52-126, 2 mm clearance all round). The
  right penetrator carries the battery cable and lands inside this end, so the board
  needs a **notch of about 18 x 12 mm in its top-right corner**: the board plane sits
  5.6-7.2 mm above the floor and the penetrator is 10 mm tall. J1/J2 go beside the notch
  with the input loop next to them; L1, the output cans and the control card stay out of
  that corner so the 10 AWG cable can bend onto the lugs.
- **LED** 50 x 50 mm in the bottom-left. J3-J8 on the power board's left edge, lower
  half, paired per channel.
- **Arduino Nano (5 V) + CAN module** in the top-left, about 50 x 29 mm clear under the
  left penetrator. A Nano (18 x 45 mm) fits flat; a typical MCP2515 + TJA1050 module
  (about 40 x 28 mm) does not fit beside it, so stack them or stand the Nano sideways.
- The Arduino was originally planned for "top middle": **that space does not exist**,
  the power board fills the full 90 mm height of its end.
- **Power the Arduino and CAN module from their own penetrator, not from J9's 5V pin.**
  The power board's 5 V comes from an L78L05 in SOT-89 (about 100 mA) that already feeds
  the control logic. Share GND through J9 and leave J9's 5V unconnected at the Arduino.
- The Arduino must be a 5 V board (Nano classic or Every): the M1-inhibit pin drives a
  74HC14 at 5 V and the current-setpoint PWM divider is scaled for 5 V.

### Vertical stack (heights above the case floor)

| Level | mm |
|---|---|
| Power board bottom (1 mm thermal pad + 4.6 mm TO-220 body) | 5.6 |
| Power board top | 7.2 |
| Output can tops (16.5 mm, Panasonic ZU) | 23.7 |
| L1 top (19 mm) | 26.2 |
| Control card bottom (21.21 mm Samtec stack) | 28.4 |
| Control card top | 30.0 |
| Tallest part on top of the card (about 1.7 mm) | 31.7 |
| Lid | 33.0 |

Conditions that go with the 21.21 mm stack:

1. The card is never over L1 (magnetic field and heat). Parts on the card's underside
   may be over a can only if they keep 2 mm above the can top at maximum can height
   (Panasonic's vent rule).
2. J9 is a right-angle header on the card's **underside**, at the card edge facing the
   Arduino end. With J9 on top, a plugged-in connector reaches about 32.8 mm and leaves
   0.2 mm under the lid. Keep J9 and its mated plug off the cans: the plug hangs about
   2.8 mm below the card.
3. Nothing taller than about 1.7 mm on the card's top side.
4. The socket must not sit above any TO-220 body; its tails stick out about 3 mm under
   the power board, 2.6 mm above the floor. Trim them to about 1 mm after soldering.
5. Standoffs set the card height, not the connector: standoff length = 21.21 mm, e.g.
   an M3 x 20 mm nylon standoff plus about 1.2 mm of nylon washers.

The earlier 16.13 mm stack (ESQ-115-23-G-D) was dropped: once L1 and the nine 16.5 mm
output cans sit next to their FETs there is no 42 x 42 mm area free of tall parts. The
two alternatives were rejected because moving the output caps 18-31 mm from their rail
FETs lengthens M1's turn-off loop (the loop the simulations above are about), and
overhanging the card into the LED/Arduino end blocks the wire exit and the Arduino stack.

## 5. Still open

1. **Are 128 x 90 x 33 mm inside dimensions?** Everything above assumes so. Measure the
   inside height from floor to the underside of the lid at the power-board end, including
   any lip or gasket: the stack needs about 32.5 mm.
2. **Is the 3.5 mm hole centre measured from the inside wall?** A 15 mm diameter
   penetrator body centred 3.5 mm from an inside wall would overlap the wall by 4 mm.
3. **Which end is the LED?** Assumed the left (opposite the power board).
4. **Actual size of the CAN module.**
5. **Copper weight (D3)** - decided after the power copper is routed at both weights.
6. The `.asc` schematics have not been updated with the REV 5 model, the sinks on
   NOLEADS, the corrected servo `.ic`, the gate changes or the Arduino inhibit pin.

## 6. Files

In `BOOST_split_boards/handoff_2026-09-14/`:

- `HANDOFF_PROMPT.md` - the work order for the routing AI (sections 0-9).
- `REPLACE_BRIEF_v2.md` - decisions D1-D6, placement stages 1-6 with targets and the
  current distances, route/check gates.
- `SIMULATION_REPORT.md` - method, result tables, dead time, caveats, how to reproduce.
- `sim/HYG180N10_REV5.lib`, `sim/netlists/*.net`, `sim/scripts/{measure,deadtime}.py`.
- `placement/` - the scripts and distance dumps the placement argument is based on.

Also in `BOOST_split_boards/`: `BOOST_AUDIT.md`, `AUDIT_RESPONSE.md`, `ROUTING_REPORT.md`,
`README.md`, and the newer folders the routing chat has created
(`replace_2026-09-14/`, `placement_review_2026-09-15/`, `handoff_routing_2026-09-15/`).

## 7. Supersedes

- `HANDOFF_PROMPT.md` section 3.2 says the rail gate resistors go to 150 Ohm. Use
  **220 Ohm** (section 3.4 above).
- `REPLACE_BRIEF_v2.md`'s stack budget (13.5 / 17.5 mm header height, "34 mm is too
  tall") is replaced by the 21.21 mm stack in section 4 above.
- The web brief at <https://claude.ai/code/artifact/08a03b10-d9f7-4470-87f0-51cc3f212b3c>
  is older than `REPLACE_BRIEF_v2.md`.
