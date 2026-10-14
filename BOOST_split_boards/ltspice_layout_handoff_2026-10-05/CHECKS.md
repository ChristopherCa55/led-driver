# Checks

There are two kinds of check, reported separately:

- **Electrical (E):** is it the same circuit?
- **Visual (V, H, T):** can a person read it?

Every line of the report says whether the check was **performed** (with the command and its result), **not
performed**, or **unavailable** (and why). Run everything on the **saved** file in your work folder.

## 1. Electrical: `tools/ltspice_equiv.py`

```bash
python tools/ltspice_equiv.py WORK/BOOST.asc --json WORK/checks/equiv.json
```

LTspice netlists both the frozen original and your file (`LTspice.exe -netlist`, each in a fresh temp copy); then the
two netlists are compared. It takes about 5 seconds. Exit code 0 means every check passed.

| Check | What must hold |
|---|---|
| **E1 Netlist identity** | Same 302 elements, apart from the 3 approved battery/cable renames. Each element keeps its exact value, model and parameter text. Every net holds the same pins **by pin position**, so pin order is kept: a resistor turned end-for-end fails. Auto node names (N001, P001) are ignored. A named net keeps its exact name. A new name is allowed only on a net that was auto-named before, and is listed |
| **E2 Name-based connections** | U18's `SpiceModel` stays `5V 0`, and the net named `5V` holds the same pins. U18 has no supply pin: it is powered by that **name**. Its output labels `4`…`10` stay |
| **E3 Directives and comments** | The 18 directive texts are an identical multiset; they may move but not change. All 6 original comments are present verbatim, unless `approved_changes.json` lists the user-approved new wording |
| **E4 Referenced identifiers** | Everything `.ic`, `.meas` and `.param` expressions use still resolves to the same thing: V(Out), V(Out-), V(0A_hi), V(SRV1-3), V(Vref_1-3), V(LX), I(L1), I(D19), IREFn_DUTY, POTn_CODE. `V(C10) V(C5) V(C2)` name no node even in the original; leave them as they are |
| **E5 Support files** | Every .asy/.lib beside your .asc is byte-identical to the original's |

**Self-test** (`python tools/selftest_equiv.py`):

- It confirms the checker catches a reversed resistor, a renamed label, a deleted comment, a changed value and a
  renamed 5V rail.
- It also confirms the checker accepts the approved renames.

Its output on 2026-10-05 is in `calibration/selftest_equiv.txt`: all 6 cases correct.

**A simulation run is not required:** identical netlists simulate identically. If you run one anyway, do it on a
copy, never in the user's folders.

## 2. Layout: `tools/asc_layout_check.py`

```bash
python tools/asc_layout_check.py WORK/BOOST.asc --out WORK/checks/layout                # full sheet
python tools/asc_layout_check.py WORK/BOOST.asc --blocks PWR,ISNS,CREG1,REF1,EA1         # the pilot
python tools/asc_layout_check.py WORK/BOOST.asc --split                                  # if CONTROL is split
```

- It checks H2–H12 (LAYOUT_RULES.md §2) and the tracing tasks. It prints review flags and per-block statistics:
  parts, crossings, labels, area and density.
- The file must have block frames: `RECTANGLE` plus a `;[ID] title` comment inside it. `--no-frames` exists only for
  measuring the original and the failed attempt.
- **H9 (text) is an estimate.** The font metrics were calibrated on LTspice screenshots on 2026-10-05
  (`calibration/README.md`), so every H9 finding, and the absence of findings, must be confirmed in the captures.

## 3. Tracing tasks (T1–T10)

The checker walks each path part by part and counts **label jumps**: steps where the next part is reached only
through a same-name label, not a wire. Steps that share a signal net are judged on that net. A step whose only
shared net is a supply or ground counts as well; that is how T1 checks the drawn ground return.

| Task | Path | Budget |
|---|---|---|
| T1 Power path | SIM_BATTERY → cable R → cable L → C69 → R1 → L1 → M1; L1 → M7 → M2 → C86 (and ch2, ch3); cable L → D28/D29/D30 → output caps; M1 → battery (ground return) | 0 |
| T2 Error amp | M2 (Vout_1) → R9 → R2 → U3 → R27 → U28; D26 (.1Vref_1) → U3 | 1 (Vout_1 into EA1) |
| T3 LED current loop | M2 → SIM_LED1 → M10 → R52 → U11; SIM_IREF1 → R29 → U26A → U11 → R56 → M10 | 1 (Vout_1 into CREG1) |
| T4 Headroom servo | M10 → R94 → U106C → U24 → D26 → U3; SIM_IREF1 → U106C | 0 |
| T5 Low-error timeout | U4 → R66 → Q1 → U14 → U18; U14 → D6 | 0 |
| T6 Fault latch | U25 → U5 → U101B → U101D → U102A; U101D → D15 | 1 (Current) |
| T7 Channel enable | U18 → U102B → R80 → R81 → U105A → U15 → R60 → M7 | 1 (CONTROL → GATEDRV) |
| T8 M1 inhibit | R84 → U21 → D24 → U104A → U19 → R15 → M1; D1 → U104A; D27 → U104A | 1 |
| T9 Gate drive | U104B → U15 → R13 → M2; D10 → R21 → U15 → C18 | 1 |
| T10 Kelvin sense | R1 → U25 | 0 |

**A human also does T1–T4 at each check-in.** The user follows each path on the LTspice captures. If they have to
search across the sheet for a matching label, that counts against the layout even if the budget is met.

## 4. Visual: `tools/ltspice_capture.py`

```bash
python tools/ltspice_capture.py WORK/BOOST.asc WORK/captures                 # overview + every block (tiled)
python tools/ltspice_capture.py WORK/BOOST.asc WORK/captures --blocks PWR,CREG1
```

**How it works:**

- Each view is a temporary cropped copy, opened maximized in LTspice. LTspice fits it to the window and draws it
  itself; the tool captures the window and closes it.
- Blocks larger than 1400 × 900 units are tiled.
- It opens LTspice windows on the user's desktop, so ask first.
- Your own renderer (e.g. `render_asc.py`) is fine for quick iteration. **It does not count as the visual check.**

**For every capture, check and record:**

- [ ] no text touches or overlaps other text, a wire, or a symbol;
- [ ] every junction dot is where a connection is meant, and no crossing sits next to a dot or pin;
- [ ] no cramped area: each part's name and value read at a glance;
- [ ] no hidden connection: no wire runs through a pin, and no part sits on a wire;
- [ ] exit labels sit at the block edge, are port-shaped, and point at the block they go to;
- [ ] supplies point up and ground points down; the dashed SIM frames carry a "simulation only" note;
- [ ] notes sit beside what they describe;
- [ ] channel copies, side by side, look the same; every real difference has a note.

## 5. Report template (for each check-in)

```
ELECTRICAL (tools/ltspice_equiv.py on <path>, sha256 <...>)        performed / not performed
  E1..E5  PASS/FAIL  <one line each; list new net names and approved renames>
VISUAL - automatic (tools/asc_layout_check.py <args>)               performed / not performed
  H2..H12 PASS/FAIL  <counts; every FAIL line, or the exception it falls under>
  Traces  T1..T10    <jumps / budget>
  Review flags       <crossings per block, long wires, label counts>
VISUAL - LTspice captures (tools/ltspice_capture.py)                performed / unavailable (why)
  <one line per capture: file, what you checked, what you found>
HUMAN tracing T1-T4                                                 to be done by the user at this check-in
TEMPORARY LABELS (pilot only)  <net, block, why>
EXCEPTIONS requested            <EXCEPTIONS.md rows>
QUESTIONS for the user          <ambiguous bypass owners with a proposal; note wording; anything else>
```
