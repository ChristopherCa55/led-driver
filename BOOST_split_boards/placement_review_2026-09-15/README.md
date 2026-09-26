# Power-board placement review, 2026-09-15

`BOOST_power_placement_review.html` — open it in a browser (the three PNGs must stay beside it).
Same content as the private page at <https://claude.ai/artifact/RizZaqBSKCshiew2Vd4GhR>.

It was the ★ check-in for step 4 of `handoff_2026-09-14/HANDOFF_PROMPT.md`: the three decisions asked of the
user, both sides of the board, the distance table against the brief's targets and the check-in 3 goals, and
the DRC summary.

Updated 2026-09-15 evening after the user's review (accepted with changes: gate parts at their gate pins,
standoffs as board-to-case fixings with H8 moved toward the bottom-right corner, commutation loop reported).
Snapshot of layout `p15_b10_k2`, built as
`replace_2026-09-14/tools/placement/BOOST_power_p15_WIP_NOT_FOR_FAB.kicad_pcb` (placement only, no copper,
marked NOT FOR FABRICATION). Numbers come from that board's own outputs:

| In this folder | From |
|---|---|
| `render_top.png`, `render_bottom.png` | `kicad-cli pcb render` of the WIP board (bottom seen from below) |
| `model.png` | `tools/placement/sa_view.py` (both sides seen from the top, screw circles, card outline) |
| distance table, DRC counts | `BOOST_power_p15_WIP_NOT_FOR_FAB.distances.md` and `.drc.json` |

The page is a snapshot: it is not regenerated when the layout changes. Live records are
`replace_2026-09-14/HANDOFF_SUMMARY_2026-09-15.md` (§11 session, §12 next steps) and
`replace_2026-09-14/tools/replace_notes.md`.
