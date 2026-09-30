# Prompt for the agent that adds the pre-charge diodes

Paste everything below the line into a new agent session.

---

I have a KiCad 10 + LTspice project for a 3-channel LED boost driver at
`C:\Users\bubba\OneDrive\Documents\led-driver`. I need three pre-charge diodes, **D28, D29 and D30** (Jingdao S2MW,
LCSC C128729, footprint `Diode_SMD:D_SOD-123F`, anode on `Vin`, cathodes on `Vout_1` / `Vout_2` / `Vout_3`), added to:
- the schematic;
- the power board, placed and routed;
- the LTspice simulation.

Everything must be checked afterwards.

**Read this file completely before you do anything:**
`C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\PRECHARGE_DIODES_HANDOFF.md`

- Sections 1-4 say what changes and why.
- Section 5 is the procedure you must follow: steps 1-9.
- Sections 6-7 say when to stop and how to roll back.
- Section 8 is background for me; it is not a task for you.

The placement, routing, schematic edit and LTspice edit are already designed and tested. They are done by scripts in
`BOOST_schematic_cleanup\tools\precharge\`. Your job is to run the procedure exactly as written, check every output
against its **Expected** text, and report.

**What to do, in order** (details and exact commands are in section 5):
1. Preflight:
   - make sure KiCad and LTspice are closed (no lock files, no processes);
   - check the SHA-256 of the six starting files;
   - check that the tools are present and that `precharge_check\` does not exist yet.
2. Back up the files that will change into `BOOST_split_boards\previous\<today>\before_precharge_diodes\`.
3. Baseline checks: ERC, netlist, DRC and the board parity check, before any edit.
4. Schematic: run `add_precharge_sch.py`, then ERC, a netlist export and `check_netlist.py`.
5. Power board: run `add_precharge_pcb.py`. It places the three diodes on the bottom, moves R47, removes one bottom
   logo, adds the tracks and vias, and refills the zones. Then confirm the `.kicad_pro` / `.kicad_dru` hashes are
   unchanged.
6. Verify the power board:
   - DRC on the saved file with `drc_summary.py`: it must print PASS;
   - parity for both boards with the new assignment file;
   - pour areas with `pour_areas.py`: it must print OK;
   - the collision and mechanical check with `check_mech.py`: it must print ALL PASS;
   - a bottom render, which you compare with `tools\precharge\reference\`.
7. LTspice:
   - run `add_precharge_asc.py`;
   - netlist a copy in `%TEMP%`;
   - `xmatch2.py` against the KiCad netlist: it must say 289 of 289, with no net conflicts;
   - a 3 ms smoke run of a scratch copy;
   - then delete the scratch copy.
8. Edit `BOOST_schematic_cleanup\README.md` with the exact text in step 8. Change nothing else in it.
9. Record the final hashes and report to me in the format of step 9b.

**Rules:**
- Follow the steps in order, one at a time. After each command, compare the output with its **Expected** text. If
  anything differs, stop at once and report the step, the command and the full output. That includes a count, a
  hash, a missing `PASS` / `ALL PASS` / `OK`, an extra warning, a `STOP` line or an exception. Do not work around it,
  and do not "fix" it yourself.
- Never weaken or edit a DRC/ERC rule, never add a DRC exclusion, and never edit `.kicad_pro` or `.kicad_dru` files.
- Change only these files, and only through the scripts and step 8's README text:
  - `KiCad\BOOST.kicad_sch`
  - `KiCad\BOOST_power_RC2.kicad_pcb`
  - `LTspice\BOOST.asc`
  - `README.md`

  Do not open and save the design in the KiCad or LTspice GUI. Do not move, add or delete anything that is not in
  section 4.
- Do not touch `BOOST_package`, `BOOST_package_for_review`, the control card, or anything in `BOOST_split_boards`
  except the new backup folder. Do not regenerate gerbers, BOM or CPL files.
- Use PowerShell and run each command block in section 5 as written: they use full paths and do not rely on
  variables from earlier blocks.
  - Scripts that load a board (`add_precharge_pcb.py`, `pour_areas.py`, `check_mech.py`, `syncboard.py`) run with
    `C:\Program Files\KiCad\10.0\bin\python.exe`.
  - The other scripts run with `python`.
  - Ignore KiCad Python's "Adding duplicate image handler" lines.
- If a step needs something you cannot do, or anything is unclear, stop and ask me instead of guessing.
- Do not create accounts, sign in anywhere, download anything, or buy anything.
