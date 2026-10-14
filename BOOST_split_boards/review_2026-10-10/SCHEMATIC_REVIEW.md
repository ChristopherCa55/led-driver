# Schematic review, as a first-time reviewer (2026-10-10)

Files reviewed: `BOOST_stuff` (README, `LTspice/BOOST.asc`, `KiCad/BOOST.kicad_sch` and the two board schematics).
Method: by eye only, no netlists. LTspice screenshots are LTspice's own drawing of cropped copies (`lt/`); KiCad
screenshots are KiCad's own SVG export (`kicad/`).

## Possible problems (worth checking)

1. **No I2C pull-ups.** SCL and SDA run between U26E (MCP4451) and J9 only. No pull-up resistor appears on either
   schematic, so the bus relies on the Arduino's weak internal pull-ups. (`kicad/regulators_conn.png`, U26E in
   `lt/regulators.png`)
2. **U26 address pin HVC/A0.** R102 (10k) pulls it down against the chip's internal pull-up, so the address bit
   latched at power-up may be uncertain. An earlier datasheet check (DS22267A) gave the same warning: the firmware
   should probe both 0x2C and 0x2D, or the pull-down should be stronger.
3. **D19 against the LX peak.** The README gives about 61 V LX peaks. A 54 V-standoff TVS (5.0SMDJ54A) starts to
   break down near 60 V (from memory of the datasheet, not re-read today). The `.meas Ptvs` line shows this is
   watched, but a reviewer will ask whether D19 conducts every cycle. (`lt/power_input.png`)
4. **Heat in M8-M10.** R94/R95 (910k/100k) against R96/R97 (100k/3.3k from analog_5V) make each headroom servo hold
   its sink MOSFET's drain near 1.6 V. At 2.6 A that is about 4 W per FET. A reviewer will ask about cooling.
   (`lt/ch1.png`)
5. **`.ic` names nodes that do not exist.** `.ic V(Out)=0 V(Out-)=1 V(C10)=0 V(C5)=0 V(C2)=0`: there is no node
   C10, C5 or C2. (`lt/directives_full.png`)

## Where a reviewer gets lost: LTspice

6. **No overview.** Nothing on the sheet says how the blocks connect (power path -> outputs, error amps -> mux ->
   latch -> drivers), or which board each circuit is on. The channel rows mix both boards: M8-M10, R52/R53/R7 and
   U11/U12/U6 are on the power board; U3/U7/U13, U24/U23/U22 and U26 are on the card. (`lt/overview.png`)
7. **Net names:**
   - Output 1's switch command is `M2_ON`; outputs 2 and 3 use `out_2_on` / `out_3_on`. Next to `M1_ON` it reads
     like another kind of signal. (`lt/output1.png`, `lt/latch_enable.png`)
   - U18's reset net is named `4`, and its Q4-Q9 outputs carry labels `5`-`10`; they look like pin numbers.
     (`lt/seq_timeout.png`)
   - The latch outputs `Out` / `Out-` read like the LED outputs (Vout_n, OUTPUT 1-3).
   - `IREF1` (the Arduino PWM) and `IREF1_input` (the pot wiper into U11) look alike but are different signals.
   - `0err_hi`, `0A_hi`, `VerrGT0`, `set-`, `RESET-` are terse.
8. **The one-hot select is not explained.** U18's Q0/Q1/Q2 (one at a time) drive U28's S0/S1/S2, which selects mux
   inputs 1, 2 and 4 = Verr1/2/3. It looks like a bug until worked out. (`lt/seq_timeout.png`)
9. **Sections without notes:**
   - M1 ON/OFF LATCH (U101A-D, D6, R4): what sets it, what resets it, what Out/Out- mean.
   - Channel enable: the R80/C17/D20 (and R78/C9/D7, R63/C8/D5) slow-on / fast-off delays. M1 INHIBIT explains the
     same circuit; the enable rows do not.
   - Gate drivers: DT tied to 5V (no dead time, both FETs of the pair switch together), 220 ohm turn-on on one FET
     against 5.1 ohm on the other, and U19's unused channel B (INB to GND, OUTB to GND through R62).
10. **Directives:**
   - Libraries, `.ic`, `.meas`, `.param`, `.model` and `.options` sit in one ragged column; `.tran` is off to the
     side.
   - A commented-out `.ic V(Vout_1)=30 V(Vout_2)=38 V(Vout_3)=30` sits among the active `.ic` lines.
   - The POTn_CODE note breaks after "= 0 A;" and continues far below ("confirmed in Microchip's data sheet..."), so
     it reads as two notes.
   - LED_RED/GREEN/BLUE are defined but unused; only the README says why.
11. **Smaller gaps:**
   - U18 gets 5V by net name inside its model: no wire shows where it is powered.
   - Channels 2 and 3 say "same as channel 1" under LED CURRENT LIMIT only, not under HEADROOM SERVO or the error
     amp.

## Where a reviewer gets lost: KiCad

12. **No title block** on the main schematic (project, revision, date); both board schematics have one.
13. **22 diodes show the value "D"** (D1-D27 apart from D19). A reviewer cannot tell what D11 or D24 is without the
    BOM. Only D19 (5.0SMDJ54A) and D28-D30 (S2MW) show part numbers.
14. **J1-J8 show only "Conn_01x01_Pin"**: J1/J2 are the battery input, J3-J8 the LED pads. Values such as BAT+/BAT-
    or LED1+/LED1-, or a short note, would say what connects where. (`kicad/power_input.png`)
15. **Spare units on top of each other:** the spare 4066 switch U106D touches the spare pot unit U26D, and U26D's
    value "MCP4451-103E/ST" floats well below. (`kicad/regulators_conn.png`)
16. **The bypass-cap row** (C104, C91, C92, ...) does not say which cap serves which chip, and its note ("I added a
    lot of capacitors for individual components in the kicad, which are all put here") is informal. C54 sits alone
    between two 5V labels.
17. **Small visual gaps:**
    - The main KiCad page places the channel rows differently from LTspice, so a reviewer has to find everything
      again.
    - Each output cap bank reaches ground through one small GND symbol on its bottom wire (under C88/C78/C77); it
      is easy to miss.
    - The MOSFET symbol has no pin names or body diode, so the back-to-back orientation of M7/M2 (M6/M3, M5/M4)
      cannot be checked by eye.

## Package

18. **`~$BOOST_BOM.xlsx`** (an Excel lock file, 10-07) is in the reviewer folder.
19. The README explains that the main schematic and the board schematics hold the same parts. A reviewer may still
    ask which one is the master copy.
