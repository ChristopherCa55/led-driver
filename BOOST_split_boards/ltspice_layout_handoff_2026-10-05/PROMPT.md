# The prompt

This is the task statement to hand to the AI doing the work. It is kept here so the folder is self-contained.

---

I have an LTspice schematic of a 3-channel 100 W LED driver, `C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_stuff\LTspice\BOOST.asc`, that I need **redrawn so a person can read and trace it**. The circuit must stay electrically identical.

**Read this folder first, before touching anything:**
`C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\ltspice_layout_handoff_2026-10-05\`.
Start with `README.md`, then read `LAYOUT_RULES.md`, `BLOCKS.md` and `CHECKS.md`. They give:

- the blocks I want, with every part assigned;
- the floorplan;
- the rules;
- the checking tools, already calibrated.

**An earlier AI already tried this and failed.** It removed wire crossings by cutting the circuit into islands
joined by net labels:

- the power path became 16 separate pieces;
- 30 parts were attached only by labels;
- tracing battery → R1 → L1 → FETs took 13 label jumps.

It was electrically identical and it passed its own checks, and it was still harder to read than my original. Its
file is in `reference/` as an example of what not to do. **An electrically identical schematic that is harder to
follow is a failed result, even if every check passes.**

**What I want:**

- **A few large blocks of related parts.** The high-current power path must be one continuous wired drawing:
  - the simulated battery, cable resistance and cable inductance, wired in series;
  - `Vin` labeled right after the cable;
  - then the input caps → R1 → L1 → M1 and the three FET pairs → output caps, with the pre-charge diodes.
- **The current-sense amp** in its own small block directly above R1.
- **One block per channel each** for: the LED current regulator; the digipot + sample-and-hold + integrator; and the
  output-voltage error amp.
- **All the control logic in one block**, organized in groups of three. A two-block fallback is pre-approved.
- **Wiring inside blocks.** Connections between blocks leave at the block edge through a short wire and a clear
  port-style label, never from the middle of dense circuitry.
- **The three channels drawn identically.**
- **Each bypass cap at the supply pin of the IC it serves.**
- **Much more space than my original.** No text may overlap anything.

**How to work:**

1. Work in a new folder, `BOOST_split_boards\ltspice_layout_<date>\work\`. Never write to `BOOST_stuff`,
   `BOOST_reorg_2026-10-05`, `BOOST_package` or `BOOST_schematic_cleanup`. I have some of them open in LTspice.
2. Do the **pilot** first: the power path, the sense amp, and channel 1's three blocks. Leave the rest of the sheet
   where it is.
3. Run the three tools on the saved file:
   - `tools\ltspice_equiv.py` (electrical identity);
   - `tools\asc_layout_check.py --blocks PWR,ISNS,CREG1,REF1,EA1` (layout rules and tracing tasks);
   - `tools\ltspice_capture.py` (screenshots drawn by LTspice itself). Ask me before you run it, because it opens
     LTspice windows.
4. Look at the captures yourself, then **stop and show me** (★ check-in 1). Include:
   - the captures;
   - the checker output;
   - the six ambiguous bypass-cap owners, each with a proposal;
   - a proposed new wording for my capacitor note.

   Revise until I'm happy.
5. Only then copy channel 1's drawing to channels 2 and 3, and do the supplies, gate drivers and control block.
6. **Clean up inside every block** until the captures read cleanly.
7. Report back (★ check-in 2) using the template in `CHECKS.md` §5:
   - electrical and visual results kept separate;
   - each check marked performed, not performed or unavailable.

**Ground rules:**

- **Don't edit the tools, `blocks.json`, `bypass_map.json` or `tools\approved_changes.json`.** If a rule blocks a
  genuinely better layout, write it in `EXCEPTIONS.md` with a screenshot and ask me.
- **Don't rename any existing net.** `.ic`, `.meas` and U18's supply depend on the names. The only approved renames
  are the three battery/cable parts listed in the README.
- **Don't change any value, model, directive, `.asy` or `.lib`.**
- **Don't use hierarchical sub-sheets.**
- **Keep every one of my notes verbatim** unless I approve new wording.
- **Report only what you verified on the saved file.**
