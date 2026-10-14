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


## 2026-10-12 decisions carried forward from the handoff

Source: `HANDOFF_2026-10-12.md`, section 5.2. Recorded during the pull-up continuation.

> Ok, the vin/out labels are good. Can you retry placing the i2c pullups using the same resistor size as all the other
> resistors. To me it seems like there is plenty of space near the input pins. There are 5V vias which you should be
> able to connect to at around 58.5, 92.5, and 55.8, 94.3. You can also just add a via, and connect it to the in2 plane
> instead of using the different resistor size. Everything else looks fine - i approve them. You do not need to rename
> the nets in ltspice. For now, do not do the other power board reroutes. For the card's longest ground splitting
> tracks, just place them in the location that would affect other stuff the least (keep other things as intact as
> possible). Yes, I would like you to regenerate all the files like the gerbers, drill, fab, bom etc...

The handoff also records the choices "Shrink J9's courtyard (Recommended)" and, for the remaining loop vias,
"Can you give a cost / benefit for doing this for each of the via locations?"

- Approved: Vin/output labels, 0603 pull-up retry near J9, shrinking J9's front courtyard (back unchanged),
  R99/R102 = 1k, LTspice `solver=alt`, card steps 7 and 8, and full output regeneration after the design is settled.
- Card long GND-splitting tracks: minimise disruption to other routing.
- Remaining power loop vias: analysis per location only, not permission to apply them.
- No LTspice net renames and no other power-board reroutes for now.
- Step 5g's precise placement and associated text/via moves still await picture approval.
- The user's saved U26D move is present in step05g; the promotion log has not yet been reconciled.

The `solver=alt` approval is now recorded in `approved_changes.json`; backup:
`previous/2026-10-12/before_step05g_completion_records/`.

## 2026-10-13 answers (picture and choice questions)

- **Step 5g, the 0603 pull-ups near J9** (`work/step05g/STEP.md`, picture `img/step05e/j9_F_after_5g.png`):
  "Approve as shown". R106 in J9's row-1 label row with I2 / SCL raised, R107 below I1 with the In2 link to J9.8, the
  5V via moved about 0.3 mm, H3's text 0.35 mm lower, J9's front courtyard 0.15 mm from the pads.
- **Step 9, the D5- re-route** (`work/step09/STEP.md`, pictures `img/card_splitters/D5_*`): "Approve step 9".
  0err_hi and SDA stay where they are (every alternative was worse, `work/CARD_SPLITTERS.md`).
- **Loop vias** (`work/whatif_1013/LOOP_VIAS.md`), the user's words:
  > Add without hesitation: Vout_3, two vias on C4.1. They help their own loop a lot and barely touch anything else.
  > May do more harm than good: ch3, two GND vias at C76.2. They make LX -> M5 worse, and that is already the board's
  > longest, highest-resistance LX path. They also add inductance to the channel that already has the most.
  > Probably not worth it: ch1, one GND via at C1.2. The gain is small, and the cost lands on Vout_1, already the
  > weakest output path at 8.46 mOhm to J3.

  Applied as step 10 (Vout_3 only).
- The user's own save of the card sheet (2026-10-11 23:14, U26D moved) is kept; `work/promotions.log` records it.

