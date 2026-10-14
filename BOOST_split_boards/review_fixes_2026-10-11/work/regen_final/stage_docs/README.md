# BOOST LED driver: design files for PCB review

A three-channel boost LED driver on two boards, designed in KiCad 10 and simulated in LTspice 26. The boards are
meant to be made and assembled by JLCPCB.

## Boards

| Board | File | Size | Layers |
|---|---|---|---|
| Power board | `KiCad/BOOST_power_RC2.kicad_pcb` | 74 x 86 mm (18 x 12 mm corner notch) | 6 (stackup JLC061611-7628D, specified at order) |
| Control card | `KiCad/BOOST_control_RC2.kicad_pcb` | 45 x 45 mm | 6 |

The schematic for both boards is `KiCad/BOOST.kicad_sch` (open `KiCad/BOOST.kicad_pro`). Each board also has its
own schematic, linked to its PCB: open `KiCad/BOOST_power_RC2.kicad_pro` or `KiCad/BOOST_control_RC2.kicad_pro`
(Switch to PCB Editor and Update PCB work there). These hold the same parts as the main schematic, so a change goes
into both. The `.pretty` folders,
`ltspice.kicad_sym`, `fp-lib-table` and `sym-lib-table` in `KiCad/` are the project's own footprint and symbol
libraries; KiCad finds them automatically.

## KiCad notes
- Each board has its own `.kicad_pro`, which carries its net classes and design rules. Open a board through (or
  beside) its own `.kicad_pro`; without it, DRC falls back to the defaults.
- 3D models: the parts use KiCad's standard 3D library (`${KICAD10_3DMODEL_DIR}`), which comes with KiCad.

## ERC and DRC
- ERC: 0 errors, 0 warnings for the main schematic and both board projects. The card schematic has PWR_FLAGs on 5V
  and GND (they reach the card only through J11); the main schematic has none there, as U17 drives 5V.
- DRC with schematic parity: 0 on both boards.
- Power board: 0 errors, 0 unconnected. The 49 warnings are expected:
  - 46 silk over copper: a top-side logo under L1 crosses L1's middle (mechanical) pad. It is hidden under L1, and
    the gerbers cut silkscreen away from exposed pads.
  - 2 silk overlaps: the can outlines of C87/C71 and C86/C88 touch.
  - 1 library mismatch: J10's holes are drilled 1.05 mm on purpose (Samtec 0.64 mm square posts).
- Control card: 0 errors, 0 unconnected. The 1 warning is expected: a library mismatch, because J11's holes are
  drilled 1.05 mm on purpose (Samtec 0.64 mm square posts).

## LTspice
`LTspice/BOOST.asc` uses:
- custom symbols: `74HC4051.asy`, `CD4017B.asy`, `CD74HC4066.asy`, `CSS4J_4026.asy`, `INA241A4.asy`, `L78L05.asy`,
  `MC7812.asy`, `MCP4451_CTRL.asy`, `MCP4451_POT.asy`, `UCC21520.asy`;
- model libraries: `74HC4051.lib`, `CD4000_v.lib`, `CD74HC4066.lib`, `CSS4J.lib`, `HYG180N10.lib`, `INA241A4.lib`,
  `L78L05.lib`, `MC7812.lib`, `MCP4451.lib`, `MCP6561.lib`, `TLV9001.lib`, `TVS_5p0SMDJ.lib`, `UCC21520.lib`.
- The INA241A4, CD74HC4066, 74HC4051, MCP4451, L78L05, MC7812, CSS4J shunt and the 5.0SMDJ54A TVS use custom
  behavioural models written for this simulation. U16 (MC7812) uses `MC7812_TYP`, the typical dropout from
  onsemi's curve (about 1.5 V); `MC7812_WC` in the same file is a pessimistic 2 V variant.
- D28-D30 (pre-charge diodes, S2MW) use an inline `.model S2MW` directive: LTspice's 1N4007 scaled to a 2 A die
  (VF 0.91 V at 2 A; data sheet max 1.1 V). Jingdao publishes no SPICE model.
- The `LED_RED`/`LED_GREEN`/`LED_BLUE` models are unused on purpose; the LEDs use the `100W_` models.
- D19 (5.0SMDJ54A) is modelled at its minimum breakdown, 60.0 V. Over 25-30 ms it conducts in 101 of 453 switching
  cycles (22 %), 9.5 mW on average (0.15 % of its 6.5 W rating); most of its current is junction capacitance at the LX
  edges. A typical part (about 63 V) would not conduct at all in steady state.

**Parameters** (a `.param` line near the other directives):
- `IREF1_DUTY`, `IREF2_DUTY`, `IREF3_DUTY`: the Arduino's IREF PWM duty in 256ths at 490 Hz. 256 = always on (the
  default), 128 = 50 %, 0 = off.
- `POT1_CODE`, `POT2_CODE`, `POT3_CODE`: the MCP4451 wiper codes of U26A/B/C (0-256). The defaults 86/103/103 give
  2.635/2.371/2.371 A LED peaks. Code 0 is full current and 256 is zero (the pot's A terminal is grounded). At
  power-up the pot sits at mid-scale (128, about 1.98 A) until the firmware writes a code.
- Parts named `SIM_...` exist only in the simulation: the battery, cable, LEDs and the Arduino outputs.

**Results:** a 30 ms run at full duty converges in about 15-50 minutes; it was 5-7 minutes before the I2C pull-ups.
With R106 / R107 in the netlist the normal solver stops at 0.3216 ms, so the `.options` line now carries
`solver=alt`, which is about 3x slower and gives the same results. Over 25-30 ms the LEDs hold 2.635, 2.371 and
2.371 A, the outputs sit at 23.3, 33.1 and 33.1 V, and LX peaks at about 61 V.

**Start-up:** the two `.ic` lines start the servos and reference filters already settled, so the LEDs reach full
brightness within about 15 ms. Delete both lines for a true cold start (full brightness takes about half a second).
That shortcut start shows one 81 V LX spike at 0.15 ms, which real hardware does not see because it starts with the
references at zero.

**PWM dimming** (`IREFn_DUTY` below 256): each pulse keeps the full current down to about 19 % duty (red) and 25 %
(green, blue); below that the pulses carry less current. Runs can stall while all LEDs are off; the `solver=alt`
on the `.options` line gets past that.

**File size:** LTspice saves every node, so a 30 ms run writes about 22 GB (`BOOST.raw`). Make sure there is room,
or add a `.save` line that lists only the signals you want.

## Review fixes (2026-10-11 to 2026-10-13): what changed

This copy carries the fixes from the 2026-10-10 schematic and PCB reviews that you approved. Every one passes every
check. The gerbers, drill files, fab drawings, BOM / CPL, cost files and the 3D model
(`BOOST_assembly_2026-10-13.step`) were regenerated from these files on 2026-10-13; the older STEP files here are the
shipped ones. The copy stays **not for fabrication** (`NOT_FOR_FAB.txt`) until you say ship.

- **LTspice:** short notes where the review found sections hard to follow (sequencer, latch, enable delays, gate
  drivers, channels 2 and 3); every diode shows its part name (`.model` aliases of the default diode, so the results do
  not change); the `.ic` line no longer names nodes that do not exist, and the commented-out `.ic` line is gone;
  the I2C pull-ups R106 / R107 (4.7k, SCL / SDA to 5V) and R99 / R102 at 1k are in; `.options` has `solver=alt`.
- **KiCad schematics:** the 22 diodes show their part names; J1-J8 show Vin+ / Vin- / Out1+ / Out1- / Out2+ / Out2- /
  Out3+ / Out3-; the main page has a title block; the spare pot unit U26D no longer touches U106D; R106 / R107
  (4.7k, 0603) are drawn with the note "I2C pull-ups (U26 has none)"; R99 / R102 are 1k, so U26's A0 / A1 cannot
  latch high and its I2C address is always 0x2C.
- **Power board:**
  - the silkscreen names J1-J8 Vin+ / Vin- / Out1+ ... instead of J1-J8 (the references are on F.Fab);
  - 12V reaches U19 / C30 / C31 on B.Cu through one opened column of the Vin via array, instead of looping round M1 on
    In4 and through R1's Vin funnel (Vin J1 -> R1 1.031 -> 1.003 mOhm, worst neck 38.8 -> 29.3 C);
  - two more GND vias in C3.2's pad share ch2's switching-loop current (worst via 3.6x -> 1.7x its IPC rating);
  - three more Vin vias in R1's funnel;
  - two more Vout_3 vias at C4.1 share ch3's output-loop current (worst via 2.8x -> 1.8x its IPC rating, that loop
    -12 % resistance).
- **Control card:**
  - R106 (front, in J9's top label row above J9.5 / J9.7; the I2 and SCL labels moved up above it) and R107 (front,
    below J9's I1 label, joined to J9.8 on In2). J9's front courtyard now hugs its pads; H3's label is 0.35 mm lower;
  - two GND stitching vias in an In1 GND piece that had only one;
  - U101A-Y moved from In1 to In2 (the main In1 GND piece 894 -> 972 mm2);
  - D5- re-routed (In4, then In2 along the bottom edge) so it no longer cuts the In4 GND in two (the main In4 piece
    626 -> 952 mm2).
- **Costs:** total $599.01 (was $598.99). R106 / R107 join the card's existing 4.7k line, R99 / R102 the 1k line; no
  new part.
- **Checks:** ERC 0 on all three schematics; DRC 0 errors and 0 unconnected on both boards, with the same warnings as
  before (power 49, card 1); schematic parity 0; the main page and both board schematics still agree; the LTspice
  file is electrically the shipped one plus the approved changes (ltspice_equiv E1-E5).

Every change with its x / y and layer: `CHANGES_XY.md` in this folder. The full report, with before / after numbers and
pictures: `BOOST_split_boards/review_fixes_2026-10-11/FIX_REPORT.md`.
