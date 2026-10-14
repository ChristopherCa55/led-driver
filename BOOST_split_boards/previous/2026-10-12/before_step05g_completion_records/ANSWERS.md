# The user's answers to DECISIONS.md (2026-10-11)

Verbatim (the user's message), then how each is applied.

> Yes, you can add the pullups to the control card.
> you can change the r99 and r102 to 1k if you think that is better
> d19 looks fine as it is
> you can remove the .ic lines that are not used anymore
> For the part values, I would like to still have the name so that you can refer to each part in the bill of
> materials. I think that it should be changed for example in the ltspice it just says D under the name Dxx, where I
> feel like it should say the actual name of the diode. I also want it to be printed on the silkscreen +/-
> connections for vin, and each of the outputs. For example Vin+, Vin-, Out1+, Out1-... on the front silkscreen
> instead of just putting connector name jxx
> The 12V route looks good.
> You can add the vias
> You can reroute as long as nothing you reroute makes it worse.
> I want to keep both boards at 6 layers.
> You can download datasheets and read jlc's quote page.
> If you think anything could benefit from being placed at a different location on the pcb, you are allowed to move
> it since this is just an extra one for now.
> When you are done changing everything, can you make a document that lists out all of the xy coordinates and layer
> that was changed so that I can review everything more easily.

| Item | Answer | Applied as |
|---|---|---|
| D1 | yes | Two 4.7 k pull-ups, SCL and SDA to 5V, on the card: LTspice, main page, card sheet, card PCB, BOM/CPL |
| D2 | yes | R99 and R102 10k -> 1k everywhere, plus the README address note |
| D3 | keep | No change to D19 |
| D4 | (not answered) | Numbers in the report and a README line only (documentation) |
| D5 | yes | The three `.ic` terms naming no node removed; the commented-out `.ic` line deleted; approved_changes.json updated |
| D6 | (not answered) | No renames (the recommendation) |
| D7 | Values = real part names, refs kept | Diode Values -> part number in LTspice (with `.model` aliases, so the simulation is unchanged) and KiCad (main, board sheets, PCB). J1-J8: Vin+ / Vin- / Out1+ ... on the power board's front silkscreen in place of the J reference text |
| D8 | (not answered) | The mocked-up notes, title block and U26D move go into the copy for review; open items (6, 10, 16, 19 master, the 220 ohm reason) are left as they are |
| X1 | yes | 12V option A (and the extra Vin via, if it tests better) |
| D10 | yes, add vias | Option (a), the recommendation the answer was given to: ch2's vias, with the cost D10 stated (Vout_2 bank about +1 %). ch1 / ch3 / Vout_3 (larger costs, not accepted) are listed, not applied |
| D11 | reroute OK if nothing gets worse | Gates: DRC / parity / ERC clean and no metric worse |
| D9 | 6 layers | Option (c): targeted fixes on the 6-layer card |
| moves | allowed (not the fixed parts of FIX_PROMPT section 3) | Used where it helps |
| downloads | allowed | Data sheets read for D1, D8, D4 |
| final | a review document with every changed x/y and layer | `CHANGES_XY.md` |
