# BOOST LED driver: design files for PCB review

A three-channel boost LED driver on two boards, designed in KiCad 10 and simulated in LTspice 26. The boards are
meant to be made and assembled by JLCPCB.

## Boards

| Board | File | Size | Layers |
|---|---|---|---|
| Power board | `KiCad/BOOST_power_RC2.kicad_pcb` | 74 x 86 mm (18 x 12 mm corner notch) | 6 (stackup JLC061611-7628D, specified at order) |
| Control card | `KiCad/BOOST_control_RC2.kicad_pcb` | 45 x 45 mm | 6 |

The schematic for both boards is `KiCad/BOOST.kicad_sch` (open `KiCad/BOOST.kicad_pro`). The `.pretty` folders,
`ltspice.kicad_sym`, `fp-lib-table` and `sym-lib-table` in `KiCad/` are the project's own footprint and symbol
libraries; KiCad finds them automatically.

## KiCad notes
- Each board has its own `.kicad_pro`, which carries its net classes and design rules. Open a board through (or
  beside) its own `.kicad_pro`; without it, DRC falls back to the defaults.
- 3D models: the parts use KiCad's standard 3D library (`${KICAD10_3DMODEL_DIR}`), which comes with KiCad.

## ERC and DRC
- ERC: 0 errors, 0 warnings.
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

**Parameters** (a `.param` line near the other directives):
- `IREF1_DUTY`, `IREF2_DUTY`, `IREF3_DUTY`: the Arduino's IREF PWM duty in 256ths at 490 Hz. 256 = always on (the
  default), 128 = 50 %, 0 = off.
- `POT1_CODE`, `POT2_CODE`, `POT3_CODE`: the MCP4451 wiper codes of U26A/B/C (0-256). The defaults 86/103/103 give
  2.635/2.371/2.371 A LED peaks. Code 0 is full current and 256 is zero (the pot's A terminal is grounded). At
  power-up the pot sits at mid-scale (128, about 1.98 A) until the firmware writes a code.
- Parts named `SIM_...` exist only in the simulation: the battery, cable, LEDs and the Arduino outputs.

**Results:** a 30 ms run at full duty converges in about 5-7 minutes. Over 25-30 ms the LEDs hold 2.635, 2.371 and
2.371 A, the outputs sit at 23.3, 33.1 and 33.1 V, and LX peaks at about 61 V.

**Start-up:** the two `.ic` lines start the servos and reference filters already settled, so the LEDs reach full
brightness within about 15 ms. Delete both lines for a true cold start (full brightness takes about half a second).
That shortcut start shows one 81 V LX spike at 0.15 ms, which real hardware does not see because it starts with the
references at zero.

**PWM dimming** (`IREFn_DUTY` below 256): each pulse keeps the full current down to about 19 % duty (red) and 25 %
(green, blue); below that the pulses carry less current. Runs can stall while all LEDs are off; adding `solver=alt`
to the `.options` line gets past it.

**File size:** LTspice saves every node, so a 30 ms run writes about 22 GB (`BOOST.raw`). Make sure there is room,
or add a `.save` line that lists only the signals you want.
