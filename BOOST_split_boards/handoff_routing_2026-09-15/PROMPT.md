# The prompt

This is the task statement to hand to the AI doing the work. It is reproduced here so the folder is
self-contained; the authoritative detail is in `README.md`, `ROUTING_SPEC.md`, `RUNBOOK.md` and
`OPEN_QUESTIONS.md`.

---

I have a KiCad project for a 3-channel 100 W LED driver at
`C:\Users\bubba\OneDrive\Documents\led-driver`. I need the **power board** placed and fully routed.

**Read this first, before touching anything:**
`BOOST_split_boards\handoff_routing_2026-09-15\README.md`, then `ROUTING_SPEC.md`, then `RUNBOOK.md`,
then `OPEN_QUESTIONS.md`. They tell you what the board is, what the copper has to survive, what tools
already exist, and what the user has already decided. There is a lot of prior work — an independent
copper audit (`BOOST_split_boards\BOOST_AUDIT.md`) that failed 10 of 13 checks on the previous layout,
and a placement pipeline that has already produced a legal placement. Don't start from scratch on any
of it without reading it.

**The job, in order:**

1. **Placement.** A complete, DRC-legal placement exists:
   `BOOST_split_boards\replace_2026-09-14\tools\placement\BOOST_power_p15_WIP_NOT_FOR_FAB.kicad_pcb`
   (124 footprints, 74 nets, 355 pad-net assignments, no copper yet). It scores 38 of 49 agreed goals. Use it as your
   baseline — keep it, polish it, or re-place from scratch with the existing annealer, whichever gives
   the best distance table. Match or beat 38/49 and stay mechanically legal. **Show me the distance
   table and plots of both sides before you draw any copper.**

2. **Routing.** Route every net. Draw the high-current copper deliberately, path by path, then the
   signals. This is an 8-layer board carrying 20.7 A through the input loop and 2.4–2.6 A through each
   LED channel; the previous layout fused its sink tracks and hung 7 A branches on single 0.25 mm vias.
   `ROUTING_SPEC.md` §3–§4 has every current and every thermal/via limit.

3. **Test it with KiCad DRC.** The acceptance test is `kicad-cli pcb drc --severity-all --format json`
   run on the **saved** file, under the shipped rules in `BOOST_power.kicad_pro`:
   **0 errors and 0 unconnected items, with no DRC exclusions and no rule weakened.** Exact commands
   are in `RUNBOOK.md` §2. Save, reload, refill zones, save again, then run DRC on the file on disk —
   don't report DRC on a board that only exists in memory.

4. **Solve the copper at 1 oz and 2 oz outer** (method in `BOOST_split_boards\AUDIT_RESPONSE.md` §1):
   for every high-current branch, the resistance, the minimum cross-section, where the neck is, the
   IPC-2221 temperature rise, and every via barrel's current against its rating. I choose the copper
   weight from that table, so show it to me before you finish.

5. **Write a report** in the style of `AUDIT_RESPONSE.md`: what changed, before/after numbers, and what
   is still open. Then, and only then, re-place and re-route the control card at 45 × 45 mm.

**Ground rules:**

- Never weaken a DRC rule and never add an exclusion. If a check can't pass, tell me — don't change
  the check.
- Verify from saved files, not from what you think you wrote.
- Back up anything shipped to `BOOST_split_boards\previous\<date>\` before replacing it, and keep
  `NOT_FOR_FAB` in the filename of anything that isn't ready to fabricate.
- Don't guess part specs or pinouts — read the datasheet, and say so when you can't verify something.
- The schematic is frozen at `BOOST-github\BOOST\BOOST_9-15_nohole.net`. If routing forces a schematic
  change, stop and ask me.
- Check in with me at the ★ points above (placement, copper weight) rather than running to the end.

**One thing to settle first:** `OPEN_QUESTIONS.md` §2.1 lists a placement question the previous session
left unanswered — whether tall parts may come within 4.0 mm of a tab screw instead of 5.5 mm. The
baseline placement is only legal under the 4.0 mm reading. Ask me about it before you build on that
placement.
