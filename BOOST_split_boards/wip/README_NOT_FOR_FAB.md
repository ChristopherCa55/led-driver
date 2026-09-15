# NOT FOR FABRICATION: work in progress

`BOOST_power_M8_WIP_NOT_FOR_FAB.kicad_pcb` is an experiment toward audit stop-ship
item 1 (LED current through 0.15 mm tracks) on channel 3 only. **It has three
open connections and must not be sent to a fab.** The board to fabricate is
`../BOOST_power.kicad_pcb`.

## What it adds
- A 1.0 mm F.Cu/B.Cu conductor from M8's source (M8.3) to the shunt R7.1. It
  replaces the 0.15 mm inner-layer track: Net-(M8-S) goes from 161 mΩ to 23.3 mΩ,
  and the IPC-2221 neck rise at 2.63 A from about 1500 °C to 12 °C (1 oz copper).
- U6's sense connection moved to R7.1 itself, so the op-amp no longer senses
  through the current-carrying track (audit item 9, channel 3).

## Why it isn't finished
The corridor passes round U8 and R47, and taking that route displaced three
signal nets. The router could not put them back, even with the corridor
treated as fixed:

| Net | Open between |
|---|---|
| Net-(D13--) | In5.Cu stub at (73.2, 109.4) and R47 pad 2 (B.Cu) at (72.33, 110.0) |
| out_3_on | In5.Cu stub at (66.9, 80.3) and B.Cu track at (70.8, 107.7) |
| Net-(U8-VDDA) | In5.Cu track at (72.1, 111.1) and F.Cu track at (74.0, 109.2) |

Routing the corridor round those nets' existing copper finds no path at all.
Closing these three opens needs a small placement change near U8/R47, such as
moving R47, to free a channel. Then re-route the three nets and re-run DRC. That
placement change is a design decision, so it was not made automatically.

The file also carries two GND fill fragments smaller than 0.01 mm² on B.Cu near
R52 from an older via-landing box. The fabrication board uses a corrected box.
