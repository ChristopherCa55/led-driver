# Step 5g: I2C pull-ups R106 / R107 as 0603 near J9 (the user's 2026-10-12 retry), plus R99 / R102 = 1k

The user's words (2026-10-12): "Can you retry placing the i2c pullups using the same resistor size as all the other
resistors. To me it seems like there is plenty of space near the input pins. There are 5V vias which you should be
able to connect to at around 58.5, 92.5, and 55.8, 94.3. You can also just add a via, and connect it to the in2 plane
instead of using the different resistor size." Their choice when asked: "Shrink J9's courtyard". R99 / R102 1k and
LTspice `solver=alt` were approved in the same message ("Everything else looks fine - i approve them").

**Status: built and gated, NOT promoted. The placement picture still needs the user's OK** (new parts, moved labels,
moved H3 text, J9 courtyard). Built by `tools/step05g_card.sh work/step05g work/step06b`.

## Base
The review copy's KiCad files as they were on 2026-10-12 (`BASE.txt`): steps 1-4 and 6b, **plus the user's own edit
of the card sheet** (saved in KiCad 2026-10-11 23:14: U26D moved 3.81 mm right with its three NC flags and its
Ref / Value fields; card sheet 13af0cd6, while promotions.log still expects a2a4ea6f).

## What changed (card + schematics only; the power board is byte-identical to step06b, 871f3a1d)
- **Schematics** (`tools/step05e_kicad_sch.py`, = step05_kicad_sch.py with the footprint `Resistor_SMD:R_0603_1608Metric`):
  R99 / R102 10k -> 1k; R106 (SCL) and R107 (SDA) 4.7k with 5V / SCL / SDA global labels left of U26E and the note
  "I2C pull-ups (U26 has none)", on the main page and the card sheet (shared uuids).
- **J9** (`tools/fp_text_edit.py`, `specs/step05f_fp_text.json`; board AND `BOOST.pretty/WirePads_11_...kicad_mod`, so no
  library-mismatch warning): the **F.CrtYd** outline now hugs the pad rows (0.15 mm from the pads: local y -1.15 .. 3.69,
  the tie-slot block x -4.5 .. -1.2 kept full height); **B.CrtYd unchanged** (the wires run underneath). The F.SilkS labels
  **I2** and **SCL** moved from local y -1.825 to -3.1 (board y 94.075 -> 92.80), i.e. above R106. B.SilkS labels unchanged.
- **H3**'s Reference text (F.SilkS) moved from local (0, -4.15) to (0, -3.8) (0.35 mm down), clear of R107's pad / silk.
- **5V** (`specs/step05g_5v.json`): the 12-segment F.Cu 5V stretch between the vias (58.425, 92.625) and (55.825, 94.225)
  removed (both vias land on the In2 5V pour); the (55.825, 94.225) via removed and a new 5V via at (55.5, 94.4) with a
  0.3 mm stub to R106.1; a new 5V via at (53.35, 101.45) with a 0.3 mm stub to R107.1.
- **R106** 0603 F.Cu at (57.15, 94.0) rot 0 (pad 1 = 5V at 56.325, pad 2 = SCL at 57.975), in J9's row-1 label row above
  J9.5 / J9.7. **R107** 0603 F.Cu at (55.15, 101.45) rot 0 (pad 1 = 5V at 54.325, pad 2 = SDA at 55.975), below J9's
  I1 label. Both from KiCad's library footprint (`tools/make_fp_block.py`, `specs/step05f_fp0603.json`); refs on F.Fab.
- **SCL**: route_new.py (F.Cu only): (57.975, 94) -> (58, 94.45) -> (58, 95.25) into J9.7.
- **SDA** (`specs/step05g_sda.json`): F.Cu (55.975, 101.45) -> (55.6, 101.075) -> (55.6, 100.7); via (55.6, 100.7);
  In2.Cu (55.6, 100.7) -> (57.25, 100.7) -> (59.1, 98.85) into J9.8's In2 pad. (The same kind of In2 link as the approved
  0402 version, but shorter: 2.8 mm slot, detour 3.4 mm, against 3.0 / 8.8 mm.)

## Gates (`card_checks.log`; power results carried over from step06b)
ERC 0 / 0 / 0; card DRC 0 errors, 1 warning (the baseline J11 library mismatch), 0 unconnected, parity 0; sync 0
(326 units; board sheets 126 + 200).

## Card metrics against step 4 (the copy's card)
- New: In2 5V cut by SDA 2.8 mm, detour 3.4 mm (the SDA link).
- F.Cu|5V pieces 14 -> 16 (the C26.1, R106.1 and R107.1 pieces are each joined to In2 by their via; not a split).
- In1 RESET cut 2.6 -> 3.0 mm (detour 4.4 -> 4.6): In1 GND now fills about 0.5 mm further under the RESET track because
  the old (55.825, 94.225) via's antipad is gone (pictures `img/step05e/in1_reset_before.png` / `_after.png`) - more
  plane, not less.
- Largest GND pieces lose 0.8-4.6 mm2 each (the two new resistors in the F.Cu pour; the new vias' antipads); short jogs
  2600 -> 2594. Narrow-neck lists gain entries near (54.5, 100.0) and (53.5, 102.6) on In1 / In3 / In4 / F (the new vias).

## Pictures
`img/step05e/j9_F_before.png`, `j9_F_after_5g.png`, `j9_In2_before.png`, `j9_In2_after_5g.png`
(`j9_F_after.png` / `j9_In2_after.png` are step 5f's).

## Still to do for step 5
1. The user's OK on the picture (R106 / R107 spots, I2 / SCL labels raised, H3 text, J9 courtyard).
2. LTspice: the candidate is `work/step05b_lt/LTspice/BOOST.asc` (bfd51e7c, solver=alt). Add the user's approval of the
   `.options ... solver=alt` change to `ltspice_layout_handoff_2026-10-05/tools/approved_changes.json` (with their words),
   re-run ltspice_equiv (E3 must then pass).
3. BOM / CPL: R106 / R107 join the card's existing 4.7k 0603 line (0603WAF4701T5E, C23162: R27, R37, R45); R99 / R102
   join the 1k line (C21190); CPL rows Top side. `tools/step05_fab.py` is the 0402 version: write a new
   `step05g_fab.py` (new output folder).
4. Rebuild steps 7 and 8 on this card; then promote (promote.py will refuse the card sheet until the user's U26D edit
   hash is recorded with their OK).
