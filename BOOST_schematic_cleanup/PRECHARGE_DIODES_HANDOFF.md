# Pre-charge diodes D28, D29, D30: change record and step-by-step instructions

Written 2026-09-29. This file is two things:
- **the record** of what is being added to the BOOST design and why (sections 1-4, 8);
- **the exact procedure** for the AI agent that applies it (sections 5-7). Follow section 5 in order. Do not skip,
  merge or reorder steps, and do not "improve" anything that is not listed.

Everything below applies to the folder `C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup`
(written `BOOST_schematic_cleanup\` from here on). Nothing outside it changes, except the backup copies in step 2 and
a scratch folder in `%TEMP%`.

All the edits were built, applied and checked on scratch copies before this file was written. Every "expected"
output below is what those test runs printed.

---

## 1. What is being added, and why

**Problem.** The earlier simulations showed that on a cold power-up an output that is still below the battery
voltage lets Vin drive current straight through L1. If the controller then switches the channel off mid-current, LX
spikes into the TVS D19. Worst case simulated: LX 93.5 V, L1 73 A, 129 mJ into the TVS. The FETs are rated 100 V.

**Fix chosen by the user (2026-09-29).** Add one diode per output, anode on `Vin`, cathode on `Vout_1`, `Vout_2`
or `Vout_3`. Each output then charges to about Vin - 0.9 V as soon as the battery is connected, so no channel ever
starts from an empty output.
- Simulated with this part: LX 62.3 V, L1 3.9 A, 4.7 mJ into the TVS at 14.8 V, and 62.5 V / 4.0 A / 4.7 mJ at
  16.8 V (the normal ~61 V level).
- In normal running every output is above Vin, so the diodes are reverse-biased and carry no current.
- The Arduino-inhibit diodes that were also discussed are **not** part of this change.

| Ref | Anode | Cathode | Part | Board | Side |
|---|---|---|---|---|---|
| D28 | Vin | Vout_1 | Jingdao S2MW, LCSC C128729 | power board | bottom (B.Cu) |
| D29 | Vin | Vout_2 | same | power board | bottom |
| D30 | Vin | Vout_3 | same | power board | bottom |

Other changes the placement needs on the power board:
- **R47** (220 ohm, M4 gate resistor) moves 10.5 mm down the right edge, with its two gate tracks rerouted.
- The **bottom silkscreen logo at (48.12, 88.66)** is deleted. The user allowed deleting logos.

The control card, the schematic's other parts and every other board item stay as they are.

## 2. The part: Shandong Jingdao Microelectronics S2MW

**Figures from the manufacturer's data sheet** ("S2AW thru S2MW", SOD123FL-A-S2AW~S2MW-2A1KV, 2016.01, 3 pages):
- LCSC copy:
  https://www.lcsc.com/datasheet/lcsc_datasheet_1810121033_Shandong-Jingdao-Microelectronics-S2MW_C128729.pdf
- The same PDF is attached to JLCPCB's part page: https://jlcpcb.com/partdetail/140015-S2MW/C128729

| Item | S2MW value |
|---|---|
| VRRM / VRMS / VDC | 1000 V / 700 V / 1000 V |
| IF(AV) | 2 A at Tc = 115 degC |
| IFSM | **50 A**, 8.3 ms single half sine (JEDEC) |
| VF | 1.1 V max at 2 A |
| IR at rated VDC | 5 uA at 25 degC, 50 uA at 125 degC |
| Cj | 25 pF typical (1 MHz, 4 V) |
| RthJA / RthJC | 75 / 22 degC/W (5 x 5 cm pads) |
| Tj, Tstg | -55 to +150 degC |
| Pins | pin 1 = cathode, pin 2 = anode (matches KiCad's diode footprints: pad 1 = K) |
| Marking | 2A7 |
| Package SOD-123FL | body 2.6-2.9 x 1.7-1.9 mm, 3.5-3.8 mm lead tip to lead tip, **1.1 mm max height** |
| Recommended land | 1.2 x 1.2 mm pads, 2.0 mm apart |

**JLCPCB / LCSC** (read on jlcpcb.com's parts API, 2026-09-29):
- C128729: Extended part, 14,235 in stock, $0.0183 each at 1-499.
- Second source: Foshan Blue Rocket S2MW, C2900725, 1,327 in stock. Its data sheet was not checked.

**Why this part.**
- It is silicon, so its leakage is tiny (5 uA at 1000 V). A 100 V Schottky of the same size is listed at 40-500 uA
  at 25 degC (JLC listings, for example DSK310 at 300 uA), and far more when hot. That would be with the output
  sitting 10-20 V above Vin all the time.
- The outputs can reach about 50 V, and 1000 V is far above that.
- 50 A is the highest surge rating JLC stocks in this small package: no 3 A silicon SOD-123FL part is listed.
- At 1.1 mm tall it fits under the board (the board underside is 5.50 mm above the case floor).
- An SMA part (S1M/M7) does not fit the D30 site, which is 2.6 mm wide.

**Footprint:** KiCad standard library `Diode_SMD:D_SOD-123F`:
- pads 1.1 x 1.1 mm at +/-1.40 mm (outer pad ends at +/-1.95 mm);
- courtyard 4.50 x 2.38 mm.

It covers the S2MW's leads (tips at +/-1.75-1.90 mm). The toe is shorter than on the data sheet's land, whose pads
end at +/-2.2 mm. That is acceptable for reflow; it is recorded here in case the user wants the longer land.

## 3. Is 50 A enough? (battery hot-plug surge)

The case modelled is the battery connected at 16.8 V (full 4S) through the modelled cable (12 mOhm + 0.8 uH), with
all three outputs and the input bank empty and charging at the same time. Each diode was modelled as an S2MW, using
LTspice's 1N4007 model scaled to a 2 A die (VF 0.91 V at 2 A).

The feed-track resistance in front of D28/D29 was left out, which makes this an upper bound.

| Battery internal resistance | Peak per diode | I^2t per diode | Pulse width (>10 % of peak) | Battery peak |
|---|---|---|---|---|
| 0 mOhm (ideal) | 99-101 A | 0.89-0.93 A^2s | ~185 us | 610-620 A |
| 10 mOhm | 74-76 A | 0.55-0.57 A^2s | ~245 us | 458-464 A |
| 40 mOhm | 41 A | 0.25 A^2s | ~550 us | 258 A |

- The per-diode peaks are shares: the input capacitors take about half of the battery current at the same time. So
  the "100 A" is one diode's share when an ideal battery charges all four banks at once, not a total.
- The pulse is short: 0.2-0.5 ms against the 8.3 ms of the IFSM test. By energy, 50 A for 8.3 ms is about
  10.4 A^2s, which is 11-40x the pulses above.
- For pulses shorter than about 1 ms, the permitted I^2t falls. A common derating is I^2t proportional to the square
  root of the pulse length. That gives about 1.6 A^2s at 0.2 ms, still 1.7x the ideal-battery case and 2.9x the
  10 mOhm case.
- **UNVERIFIED:** the short-pulse capability is not in the Jingdao data sheet. The derating above is an engineering
  estimate, not a data-sheet figure.
- D28 and D29 are fed through the regulators' 1 mm Vin feed tracks and single 0.8/0.4 mm vias, about 15-20 mOhm.
  This is an estimate from the track lengths, not measured. It lowers their real surge further.
- D30 sits next to J1's Vin pour and sees the full value.
- The copper carries these pulses easily: 1 A^2s heats a 1 mm x 35 um track by about 4 K and one 0.4 mm via barrel
  by about 8-20 K (adiabatic).

## 4. The exact changes

### 4.1 Schematic `KiCad\BOOST.kicad_sch`

Three new symbols and six new global labels:
- They go in the empty area at the top right of the C-size sheet.
- They are connected only by labels placed on the pin ends, so no wires are drawn.
- Script: `tools\precharge\add_precharge_sch.py`.

| Ref | Symbol | Placed at (mm) | Anode pin (pin 2 "+") | Cathode pin (pin 1 "-") | Symbol UUID |
|---|---|---|---|---|---|
| D28 | `ltspice:diode`, rotation 0 | (506.73, 40.64) | (508.00, 40.64): label `Vin`, 90 deg | (508.00, 45.72): label `Vout_1`, 270 deg | c399746a-53eb-4c48-a735-e8265130f622 |
| D29 | same | (519.43, 40.64) | (520.70, 40.64): `Vin` | (520.70, 45.72): `Vout_2` | ad541492-5975-4a76-baf7-2fb8e76d43fb |
| D30 | same | (532.13, 40.64) | (533.40, 40.64): `Vin` | (533.40, 45.72): `Vout_3` | 68d2cdfe-4062-478b-951b-a3c5578ea96a |

Fields on each symbol:
- Value `S2MW`;
- Footprint `Diode_SMD:D_SOD-123F`;
- Datasheet: the LCSC URL above;
- Description "Pre-charge diode Vin -> Vout_n (Jingdao S2MW, 1000 V 2 A, IFSM 50 A); conducts only while Vout_n is
  below Vin";
- `Sim.Device` SPICE, `Sim.Params` `model="S2MW"`;
- `MPN` S2MW, `LCSC` C128729.

The labels are bidirectional global labels, the same kind as the existing `Vin`/`Vout_n` labels. The file keeps its
CRLF line ends.

### 4.2 Power board `KiCad\BOOST_power_RC2.kicad_pcb`

Script: `tools\precharge\add_precharge_pcb.py`. Coordinates are board millimetres as KiCad shows them. "Rotation"
is what KiCad reports after the script: the script picks the rotation that puts each pad on its target.

**New and moved parts** (all on the bottom side, B.Cu):

| Ref | Footprint | Centre | Rotation | Pad 1 | Pad 2 |
|---|---|---|---|---|---|
| D28 | Diode_SMD:D_SOD-123F, value S2MW | (46.00, 91.50) | 0 | K (44.60, 91.50) = Vout_1 | A (47.40, 91.50) = Vin |
| D29 | same | (52.00, 87.25) | 0 | K (50.60, 87.25) = Vout_2 | A (53.40, 87.25) = Vin |
| D30 | same | (102.85, 89.60) | 90 | K (102.85, 91.00) = Vout_3 | A (102.85, 88.20) = Vin |
| R47 (moved) | Resistor_SMD:R_0603_1608Metric, 220 | from (101.69, 88.99), rot 0 to **(102.85, 99.50)** | 270 (KiCad shows -90) | GATE_M4 (102.85, 98.675) | Net-(D13--) (102.85, 100.325) |

- Each new footprint is linked to its schematic symbol (path `/<symbol UUID>`, sheet name `/`, sheet file
  `BOOST.kicad_sch`), so a later "Update PCB from Schematic" keeps them.
- Reference labels go on B.Fab, not the silkscreen, like every other small part on this board. D30's labels sit at
  its body centre, because the library spot is past the board edge.
  - The first run (2026-09-29) left them on B.Silkscreen, with D30's hanging 1.5 mm off the board edge.
  - `tools\precharge\fix_ref_labels.py` corrected that on the finished board: six lines of text, no copper.
  - `add_precharge_pcb.py` now does it directly.

**Deleted:**
- Four B.Cu segments of `Net-(D13--)` (0.2 mm). This is the old route from R47's pad 2 down the right edge:
  (102.65, 89.35)-(102.65, 89.55)-(102.75, 89.65)-(102.75, 98.55)-(100.45, 100.85).
- The bottom logo footprint `LOGO` "G***" at (48.122601, 88.661485), rotated 90, uuid
  1317deff-735a-4193-978a-f3484107ac56.

**Added tracks and vias.** All vias are through-hole. The widths and drills meet the board's rules: Vin/Vout tracks
at least 1.0 mm, high-current via drill at least 0.4 mm, every via drill at least 0.3 mm.

| Net | Layer / via | Points (mm) | Width / via | Purpose |
|---|---|---|---|---|
| Vin | B.Cu | (47.40, 91.50) -> (47.70, 91.30) | 1.0 | D28 anode onto the existing Vin diagonal (the U1 feed; its centre line is x + y = 139.00) |
| Vout_1 | B.Cu | (44.60, 91.50) -> (45.90, 91.00) | 1.0 | D28 cathode to its via |
| Vout_1 | via | (45.90, 91.00) | 0.8 / 0.4 | into the In3.Cu Vout_1 strip (x 43.0-47.2); sits under D28's body between the pads |
| Vin | B.Cu | (53.40, 87.25) -> (56.45, 87.65) | 1.0 | D29 anode to the existing Vin via at (56.45, 87.65) |
| Vout_2 | B.Cu | (50.60, 87.25) -> (49.90, 84.00) | 1.0 | D29 cathode to the existing Vout_2 via at (49.90, 84.00) |
| Vin | B.Cu | (102.85, 88.20) -> (102.36, 87.00) | 1.0 | D30 anode to the existing Vin via at (102.36, 87.00) in the "Vin J1 bottom" pour |
| Vout_3 | B.Cu | (102.85, 91.00) -> (100.60, 91.60) -> (100.60, 92.50) | 1.0 | D30 cathode to its vias |
| Vout_3 | via x 2 | (100.60, 91.60), (100.60, 92.50) | 0.8 / 0.4 | into the Vout_3 pours on In2/In3/In5 |
| GATE_M4 | B.Cu | (101.05, 88.65) -> (100.55, 88.65) | 0.3 | closes the gap left by R47's old pad 1: keeps via (101.65, 88.05) / R73 joined to M4's gate |
| GATE_M4 | B.Cu | (102.85, 98.675) -> (103.10, 98.425) -> (103.10, 92.90) | 0.3 | R47's new pad 1 up the right edge |
| GATE_M4 | via | (103.10, 92.90) | 0.6 / 0.3 | to F.Cu |
| GATE_M4 | F.Cu | (103.10, 92.90) -> (103.10, 89.60) -> (102.51, 89.00) | 0.3 | to R73 pad 2 |
| Net-(D13--) | B.Cu | (102.85, 100.325) -> (100.45, 100.85) | 0.2 | R47's new pad 2 to the kept end of its old track |

The M4 gate path now runs:
- turn-on: U8 pin 15 -> D13 cathode net -> R47 (220 ohm) -> up the edge -> R73 pad 2 -> via (101.65, 88.05) -> M4's
  gate;
- D13 turn-off: unchanged.

The extra ~12 mm of gate trace sits in series with 220 ohm, so it does not matter.

**Why these spots.** The board has no free space next to a Vin/Vout boundary except these three. A net-aware scan
only allowed spots whose courtyard sits on GND or the diode's own nets, so no high-current pour is cut.
- D28 and D29 sit where the bottom logo was, on GND copper beside the regulator's Vin feed.
- D30 sits on the right edge, where the inner Vin planes end at y 87.2 and the Vout_3 planes start at y 90.5.
- R47 was the only part in that strip, so it moves.

**Expected copper changes** (measured by `pour_areas.py`):
- Only GND pours lose area. The largest loss is B.Cu, -24.6 mm2.
- The GND planes In1/In6 and the 5V plane each lose -4.8 mm2 (via holes).
- "Vout_2 In5 to J8" loses -1.55 mm2 (D28's via).
- The three Vout_3 inner pours lose about -1.25 mm2 each (the GATE_M4 via at the edge).
- Every Vin, Vout_1, Output1/2/3_drain, LX and rsense_lo pour is unchanged.

### 4.3 LTspice `LTspice\BOOST.asc`

Script: `tools\precharge\add_precharge_asc.py`. It adds three built-in `diode` symbols (R0):

| Ref | Symbol origin | Anode flag | Cathode flag |
|---|---|---|---|
| D28 | (3584, -1200) | `FLAG 3600 -1200 Vin` | `FLAG 3600 -1136 Vout_1` |
| D29 | (3712, -1200) | `FLAG 3728 -1200 Vin` | `FLAG 3728 -1136 Vout_2` |
| D30 | (3840, -1200) | `FLAG 3856 -1200 Vin` | `FLAG 3856 -1136 Vout_3` |

- Each symbol gets `SYMATTR Value S2MW`.
- One directive: `.model S2MW D(IS=14n RS=17m N=1.8 CJO=25p M=0.333 TT=3u BV=1000 IBV=5u)`.
- One comment line saying the model is not a vendor model. Jingdao publishes none; this one is LTspice's 1N4007
  scaled to a 2 A die: VF 0.91 V at 2 A against the 1.1 V maximum.
- The file stays latin-1 with LF line ends. Nothing else in it changes.

### 4.4 Files

**Changed:**
- `KiCad\BOOST.kicad_sch`
- `KiCad\BOOST_power_RC2.kicad_pcb`
- `LTspice\BOOST.asc`
- `README.md` (text given in step 8)

KiCad may also rewrite `KiCad\BOOST_power_RC2.kicad_prl`, which is harmless.

**Must not change** (their SHA-256 must be identical before and after):
- `KiCad\BOOST_power_RC2.kicad_pro`
- `KiCad\BOOST_power_RC2.kicad_dru`
- `KiCad\BOOST_control_RC2.kicad_pcb`
- `KiCad\BOOST.kicad_pro`
- every library
- everything in `BOOST_package\`, `BOOST_package_for_review\` and `BOOST_split_boards\` (apart from the new backup
  folder)

**New:**
- `precharge_check\`, the reports from section 5.
- A scratch folder `%TEMP%\boost_precharge_work\`, deleted at the end.

**Starting files** (SHA-256; step 1 checks them):

| File | SHA-256 |
|---|---|
| `KiCad\BOOST.kicad_sch` | 68bcf5d398fc99662dc0b6f0295b607310c00550e694b94469e51d743cc26952 |
| `KiCad\BOOST_power_RC2.kicad_pcb` | 33d2d60c368969c66fe31a6326b3bfec2734177607fdfc8eaf1a4a4c655cadcd |
| `KiCad\BOOST_power_RC2.kicad_pro` | 6977ea5172eb0363197beba1c3dc4132083836333b11be443348626ee6f9ab0f |
| `KiCad\BOOST_power_RC2.kicad_dru` | 0ad32cacdee71c2fd51048714d5df63a91510074a4b3fcb921b84ee2af5f3874 |
| `KiCad\BOOST_control_RC2.kicad_pcb` | 3335e701de1c39ca0d2cceca34f6a9c66d83737b1ead46d33491f22e59b62b1f |
| `LTspice\BOOST.asc` | b137080c3086f1213f0b3a8afbfb4609a602e6ba5172388ccc88e38c988b7c4e |

---

## 5. Procedure (for the agent)

### Ground rules
1. Do the steps in order. After every command, compare the output with the **Expected** text. If anything differs,
   including any count, any extra line or a missing PASS, **stop, do not continue, and report to the user**: the
   step, the command, and the full output. Do not try to work around a difference.
2. Never weaken a DRC or ERC rule, never add a DRC exclusion, and never edit `.kicad_pro` / `.kicad_dru`.
3. Change only the files listed in 4.4, only through the scripts and the README text in step 8. Do not open the
   design in the KiCad or LTspice GUI and save it.
4. Do not move, add or delete anything else. If you think another change is needed, stop and ask the user.
5. The user's files live in OneDrive. Write scratch files only to `%TEMP%\boost_precharge_work\` and reports only to
   `BOOST_schematic_cleanup\precharge_check\`.
6. Every command below is complete on its own (full paths, no variables carried between commands). Run them in
   **PowerShell**, one command block per tool call.
7. Tools:
   - KiCad 10: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`, and KiCad's Python
     `C:\Program Files\KiCad\10.0\bin\python.exe` (it has `pcbnew`).
   - System Python: `python`, 3.13; no `pcbnew`.
   - LTspice 26: `C:\Program Files\ADI\LTspice\LTspice.exe`.
   - Scripts that load boards (`add_precharge_pcb.py`, `pour_areas.py`, `check_mech.py`, `syncboard.py`) must run
     with **KiCad's Python**. All other `.py` scripts run with `python`.
   - KiCad's Python prints several "Adding duplicate image handler" lines. Ignore them.

### Step 1: Preflight (read-only)

1a. KiCad and LTspice must not have these files open.
```powershell
Get-ChildItem "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad" -Force -Filter "~*.lck"
Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(kicad|eeschema|pcbnew|LTspice)\.exe$' } | Select-Object Name, CommandLine
```
**Expected:** no output from either command. If a lock file exists, or any KiCad or LTspice process is running,
stop. Ask the user to close KiCad and LTspice (they often have `BOOST.asc` open), then repeat 1a.

1b. The starting files must be the expected versions.
```powershell
Get-FileHash -Algorithm SHA256 "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST.kicad_sch","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pro","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_dru","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_control_RC2.kicad_pcb","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\LTspice\BOOST.asc" | Format-Table -AutoSize Hash, Path
```
**Expected:** the six hashes in the table in 4.4 (upper case is fine). If any differs, stop: the design changed
after this file was written.

1c. The tools must be present.
```powershell
Get-ChildItem "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge" | Select-Object Name
```
**Expected:** `add_precharge_asc.py`, `add_precharge_pcb.py`, `add_precharge_sch.py`,
`board_assignment_2026-09-29_precharge.json`, `check_mech.py`, `check_netlist.py`, `drc_summary.py`,
`kicad_netcompare.py`, `ltnet_compare.py`, `make_smoke_asc.py`, `pour_areas.py`, `reference` (a folder) and
`xmatch2.py`.

1d. `precharge_check\` must not exist yet.
```powershell
Test-Path "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check"
```
**Expected:** `False`. If `True`, stop and ask the user: the change may have been started before.

### Step 2: Backups
Copies go into `BOOST_split_boards\previous\<today>\before_precharge_diodes\`, where `<today>` is today's date as
yyyy-MM-dd.
```powershell
$d = Get-Date -Format yyyy-MM-dd; $b = "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\previous\$d\before_precharge_diodes"; if (Test-Path $b) { "STOP: $b already exists" } else { New-Item -ItemType Directory -Force "$b\KiCad","$b\LTspice" | Out-Null; $s = "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup"; Copy-Item "$s\KiCad\BOOST.kicad_sch","$s\KiCad\BOOST_power_RC2.kicad_pcb","$s\KiCad\BOOST_power_RC2.kicad_pro","$s\KiCad\BOOST_power_RC2.kicad_dru" "$b\KiCad\"; if (Test-Path "$s\KiCad\BOOST_power_RC2.kicad_prl") { Copy-Item "$s\KiCad\BOOST_power_RC2.kicad_prl" "$b\KiCad\" }; Copy-Item "$s\LTspice\BOOST.asc" "$b\LTspice\"; Copy-Item "$s\README.md" "$b\"; Get-ChildItem -Recurse -File $b | ForEach-Object { "{0}  {1}" -f $_.FullName, $_.Length } }
```
**Expected:** a list of `BOOST.kicad_sch`, `BOOST_power_RC2.kicad_pcb`, `.kicad_pro`, `.kicad_dru` (and `.kicad_prl`
if it existed), `LTspice\BOOST.asc` and `README.md`, with non-zero lengths. If it prints "STOP", ask the user
before going on. Write down the backup folder path: it goes in the report.

### Step 3: Baseline checks (before any edit)
```powershell
New-Item -ItemType Directory -Force "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check" | Out-Null; & "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch erc --severity-all --format json -o "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\erc_before.json" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST.kicad_sch"; & "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch export netlist -o "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\netlist_before.net" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST.kicad_sch"; & "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --severity-all --format json -o "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\drc_before.json" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb"
```
**Expected** (`...` stands for the full path; the netlist export prints nothing):
```
Found 0 violations
Saved ERC Report to ...\precharge_check\erc_before.json
Found 49 violations
Found 0 unconnected items
Saved DRC Report to ...\precharge_check\drc_before.json
```
DRC takes about 1-2 minutes.
```powershell
python "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\drc_summary.py" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\drc_before.json"
```
**Expected:**
```
errors 0, warnings 49, unconnected 0, schematic parity items 0
  warning  lib_footprint_mismatch     1
  warning  silk_over_copper           46
  warning  silk_overlap               2
PASS - matches the accepted baseline
```
```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\replace_2026-09-14\tools\placement\syncboard.py" --check "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\netlist_before.net" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\replace_2026-09-14\board_assignment_2026-09-15.json" POWER
```
**Expected** (the one "failure" is the logos, which are not in the netlist; the same before and after):
```
check BOOST_power_RC2.kicad_pcb: 125 footprints (want 124), 2662 tracks/vias, 57 zones; parity failures 1
   extra footprints ['G***']
```

### Step 4: Schematic
4a. Apply the edit.
```powershell
python "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\add_precharge_sch.py" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST.kicad_sch"
```
**Expected** (`...` is the full path):
```
added D28, D29, D30 and six global labels to C:\...\KiCad\BOOST.kicad_sch
  D28 at (506.73, 40.64): anode pin (508, 40.64) = Vin, cathode pin (508, 45.72) = Vout_1
  D29 at (519.43, 40.64): anode pin (520.7, 40.64) = Vin, cathode pin (520.7, 45.72) = Vout_2
  D30 at (532.13, 40.64): anode pin (533.4, 40.64) = Vin, cathode pin (533.4, 45.72) = Vout_3
```
If it prints a line starting `STOP` or an `AssertionError`, nothing was written; report it.

4b. ERC and netlist.
```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch erc --severity-all --format json -o "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\erc_after.json" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST.kicad_sch"; & "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch export netlist -o "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\BOOST_precharge.net" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST.kicad_sch"; python "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\check_netlist.py" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\BOOST_precharge.net"
```
**Expected:** `Found 0 violations` and `Saved ERC Report to ...\erc_after.json` from ERC, nothing from the netlist
export, then:
```
components 293, nets 186
D28: ('S2MW', 'Diode_SMD:D_SOD-123F'), pin 2 -> Vin, pin 1 -> Vout_1
D29: ('S2MW', 'Diode_SMD:D_SOD-123F'), pin 2 -> Vin, pin 1 -> Vout_2
D30: ('S2MW', 'Diode_SMD:D_SOD-123F'), pin 2 -> Vin, pin 1 -> Vout_3
PASS
```

### Step 5: Power board
5a. Apply the placement and routing. This takes about a minute because it refills every zone.
```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\add_precharge_pcb.py" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb"
```
**Expected:**
```
text pass: deleted 4 segments and the logo
D28: bottom, rotation 0, centre (46.00, 91.50), pad 1 (K) (44.6, 91.5) = Vout_1, pad 2 (A) (47.4, 91.5) = Vin
D29: bottom, rotation 0, centre (52.00, 87.25), pad 1 (K) (50.6, 87.25) = Vout_2, pad 2 (A) (53.4, 87.25) = Vin
D30: bottom, rotation 90, centre (102.85, 89.60), pad 1 (K) (102.85, 91.0) = Vout_3, pad 2 (A) (102.85, 88.2) = Vin
R47 was at (101.689, 88.994) rotation 0
R47 now at (102.85, 99.50) rotation 270, pad 1 (102.85, 98.675), pad 2 (102.85, 100.325)
added 10 track runs and 4 vias
saved C:\...\KiCad\BOOST_power_RC2.kicad_pcb (zones refilled, project file restored)
```
The script:
- refuses to run if a lock file exists, if D28 is already on the board, or if any expected item is missing;
- copies the rules next to its temporary file before loading, so the zone refill uses the project's clearances;
- rebuilds connectivity before the refill;
- writes back the original `.kicad_pro` bytes after `SaveBoard`, which drops the netclasses.

5b. The project and rule files must be unchanged.
```powershell
Get-FileHash -Algorithm SHA256 "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pro","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_dru","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_control_RC2.kicad_pcb" | Format-Table -AutoSize Hash, Path
Get-ChildItem "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad" -Filter "*precharge_tmp*"
```
**Expected:** hashes 6977ea51..., 0ad32cac..., 3335e701... (as in 4.4), and no `*precharge_tmp*` files.

### Step 6: Verify the power board
6a. DRC on the saved file.
```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --severity-all --format json -o "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\drc_after.json" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb"; python "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\drc_summary.py" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\drc_after.json"
```
**Expected:** `Found 49 violations`, `Found 0 unconnected items`, and exactly the same summary as in step 3, ending
in `PASS - matches the accepted baseline`. Any `NOT IN BASELINE` or `UNCONNECTED` line, or `FAIL`, means stop.

6b. Board-vs-schematic parity for both boards, with the new netlist and the new assignment file (the old one plus
D28-D30 -> POWER).
```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\replace_2026-09-14\tools\placement\syncboard.py" --check "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\BOOST_precharge.net" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\board_assignment_2026-09-29_precharge.json" POWER; & "C:\Program Files\KiCad\10.0\bin\python.exe" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\replace_2026-09-14\tools\placement\syncboard.py" --check "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_control_RC2.kicad_pcb" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\BOOST_precharge.net" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\board_assignment_2026-09-29_precharge.json" CONTROL
```
**Expected:**
```
check BOOST_power_RC2.kicad_pcb: 128 footprints (want 127), 2675 tracks/vias, 57 zones; parity failures 1
   extra footprints ['G***']
check BOOST_control_RC2.kicad_pcb: 167 footprints (want 166), 5053 tracks/vias, 7 zones; parity failures 1
   extra footprints ['G***']
```
The only "failure" is the logos (not in the netlist), exactly as in the baseline.

6c. Copper: no high-current pour may lose area. Compare against the backup from step 2.
```powershell
$d = Get-Date -Format yyyy-MM-dd; & "C:\Program Files\KiCad\10.0\bin\python.exe" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\pour_areas.py" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\previous\$d\before_precharge_diodes\KiCad\BOOST_power_RC2.kicad_pcb" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb"
```
If step 2 ran on an earlier date, use that date's folder instead of today's.

**Expected:**
```
5V             5V plane                     In4.Cu     4710.92    4706.13    -4.79
GND            GND fill                     B.Cu       2602.67    2578.08   -24.60
GND            GND fill                     F.Cu       2567.51    2555.69   -11.82
GND            GND fill                     In2.Cu     2366.63    2365.09    -1.55
GND            GND planes                   In1.Cu     4883.40    4878.61    -4.79
GND            GND planes                   In6.Cu     4883.40    4878.61    -4.79
Vout_2         Vout_2 In5 to J8             In5.Cu      919.11     917.57    -1.55
Vout_3         Vout_3 In2 at M4             In2.Cu      196.68     195.44    -1.24
Vout_3         Vout_3 inner to J5           In3.Cu      547.51     546.27    -1.24
Vout_3         Vout_3 inner to J5           In5.Cu      524.40     523.14    -1.27
OK - only the expected pours changed
```
(After the header line. The numbers may differ in the last digit.)

6d. Mechanical and collision check: side, board outline, courtyard overlaps, keep-outs, and distance from J1's
bolt.
```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\check_mech.py" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb"
```
**Expected:** four blocks (D28, D29, D30, R47), each `side B`, with these centres and pad nets:
- D28 at (46.000, 91.500), rotation 0;
- D29 at (52.000, 87.250), rotation 0;
- D30 at (102.850, 89.600), rotation 90, with "nearest courtyard point to J1 centre ... 5.20 mm";
- R47 at (102.850, 99.500), rotation -90.

The last line must be `ALL PASS`. DRC (6a) also checks courtyard overlaps, rule areas and copper clearances. This
script adds the side and J1 checks.

6e. Pictures for the report (bottom view).
```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb render --side bottom --width 1600 --height 1800 --background opaque --quality basic -o "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\power_bottom_after.png" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb"
```
**Expected:** kicad-cli prints progress lines ("Loading...", "Build Tech layer ...", "Rendering: 100") and then
`Successfully created 3D render image`, and `power_bottom_after.png` is created. The view is mirrored (seen from
below), so D30 and R47 show at the left edge. Open it and confirm, then say so in the report:
- the three small diodes and R47 are where the pictures in `tools\precharge\reference\after_*.png` show them;
- the logo at the D28/D29 site is gone.

The reference pictures are copper plots: red Vin, green Vout_1, blue Vout_2, purple Vout_3, grey GND, teal
Output2_drain; black boxes are courtyards.

### Step 7: LTspice
7a. LTspice must not have `BOOST.asc` open (repeat the process check from 1a). Then apply the edit.
```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'LTspice.exe' } | Select-Object CommandLine
python "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\add_precharge_asc.py" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\LTspice\BOOST.asc"
```
**Expected:** no process output, then
`added D28-D30 (S2MW) with Vin / Vout_n flags and the .model S2MW directive to C:\...\LTspice\BOOST.asc`.

7b. Copy the LTspice folder to scratch (outside OneDrive), netlist it there, and compare it with the KiCad netlist.
```powershell
$w = "$env:TEMP\boost_precharge_work"; if (Test-Path $w) { Remove-Item -Recurse -Force $w -Confirm:$false }; New-Item -ItemType Directory -Force $w | Out-Null; Copy-Item "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\LTspice\*" $w; Start-Process -Wait -FilePath "C:\Program Files\ADI\LTspice\LTspice.exe" -ArgumentList '-netlist', "`"$w\BOOST.asc`""; Select-String -Path "$w\BOOST.net" -Pattern '^D2[89] |^D30 |^\.model S2MW' | ForEach-Object { $_.Line }; python "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\xmatch2.py" "$w\BOOST.net" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\BOOST_precharge.net" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\xmatch.json" | Select-Object -Last 14
```
**Expected:**
```
D28 Vin Vout_1 S2MW
D29 Vin Vout_2 S2MW
D30 Vin Vout_3 S2MW
.model S2MW D(IS=14n RS=17m N=1.8 CJO=25p M=0.333 TT=3u BV=1000 IBV=5u)
paired: 289 of KiCad 289 / LTspice 294 simulated parts (after 4 rounds)

KiCad parts with no LTspice match (0):

LTspice parts with no KiCad match (5):
  D§SIM_LED1   LED     0          A=Vout_1 K=Output1_drain
  D§SIM_LED2   LED     0          A=Vout_2 K=Output2_drain
  D§SIM_LED3   LED     0          A=Vout_3 K=Output3_drain
  L§SIM_LCABLE L       8e-07      p=P008 p=Vin
  R§SIM_RCABLE R       0.012      p=P001 p=P008

paired parts whose designators differ:

net conflicts (0):
```
Before the change it was 286 of 286, with the same five simulation-only parts, so the three diodes are the only
difference. There must be no designator differences and no net conflicts.

7c. Smoke test: a 3 ms run of a **scratch copy** (never the real file), to show the LTspice file loads and simulates.
```powershell
$w = "$env:TEMP\boost_precharge_work"; python "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\tools\precharge\make_smoke_asc.py" "$w\BOOST.asc" "$w\BOOST_smoke.asc"; Start-Process -Wait -FilePath "C:\Program Files\ADI\LTspice\LTspice.exe" -ArgumentList '-b', "`"$w\BOOST_smoke.asc`""; Select-String -Path "$w\BOOST_smoke.log" -Pattern 'elapsed|rror|lxmax|id2|id3|vout' | ForEach-Object { $_.Line }
```
**Expected** (the run takes about 15-20 s; the elapsed time varies and the numbers may differ in the last digits):
```
Total elapsed time: 16.376 seconds.
lxmax: MAX(V(lx))=81.24... FROM 0 TO 0.003
id28max: MAX(I(D28))=81.18... FROM 0 TO 0.003
id29max: MAX(I(D29))=81.18... FROM 0 TO 0.003
id30max: MAX(I(D30))=81.18... FROM 0 TO 0.003
vout1end: V(vout_1) =24.32... at 0.00299
vout2end: V(vout_2) =31.17... at 0.00299
vout3end: V(vout_3) =31.70... at 0.00299
```
- The 81 A per diode is the pre-charge pulse at t = 0.
- The 81 V LX peak is expected in this as-drawn start state; section 8 explains it. Report it, and do not try to fix
  it.
- Anything with "error" or "rror", a missing line, or a run that does not finish is a stop.

7d. Record the results, then delete the scratch folder.
```powershell
Copy-Item "$env:TEMP\boost_precharge_work\BOOST_smoke.log" "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\precharge_check\ltspice_smoke.log"; Remove-Item -Recurse -Force "$env:TEMP\boost_precharge_work" -Confirm:$false
```

### Step 8: README
Edit `BOOST_schematic_cleanup\README.md` with exact text replacements, using your file-edit tool. Change nothing
else.

8a. Replace the line
`- the schematic is rev6;`
with
`- the schematic is rev6 plus the pre-charge diodes D28-D30 (added <today's date>, see PRECHARGE_DIODES_HANDOFF.md);`

8b. In the table, replace
`**Power board**: 74 x 86 mm, 8 layers, 9 silkscreen logos`
with
`**Power board**: 74 x 86 mm, 8 layers, 8 silkscreen logos`

8c. Directly under the line `## KiCad notes`, before its first existing bullet, insert these lines:
```
- **<today's date>: pre-charge diodes D28-D30 added.** Jingdao S2MW (LCSC C128729; 1000 V, 2 A, IFSM 50 A;
  SOD-123FL, footprint `Diode_SMD:D_SOD-123F`), anode on `Vin`, cathode on `Vout_1` / `Vout_2` / `Vout_3`.
  On the power board they are on the bottom: D28 (46.00, 91.50), D29 (52.00, 87.25), D30 (102.85, 89.60). R47 moved to
  (102.85, 99.50) to make room for D30, and the bottom logo at (48.1, 88.7) was removed. Checked: ERC 0; DRC 0 errors,
  0 unconnected, the same 49 warnings as before; parity unchanged apart from the three new parts. Full record:
  `PRECHARGE_DIODES_HANDOFF.md`. **The gerbers, fab drawings and 3D model here, and the BOM/CPL files in
  `BOOST_package`, do not include the diodes yet.**
```

8d. Replace the whole "Known issue" paragraph, which starts `**Known issue** (edge-case simulations, 2026-09-28):`
and ends with `- Fixes are being considered; the design is unchanged so far.`, with:
```
**Start-up spikes, fixed <today's date> with pre-charge diodes D28-D30** (Vin -> each output):
- Without them, a cold start could switch a channel off with current in L1 while its output was still below the
  battery: LX 80-93 V into the TVS D19.
- With them, every output sits at about Vin - 0.9 V from the moment the battery is connected. A normal power-up
  (references ramping from zero) then peaks at LX 62-62.5 V with about 4 A in L1, at both 14.8 V and 16.8 V.
- The as-drawn `.ic` start (references and servos already settled while the 12 V gate-drive rail is still coming
  up) still shows an 81 V LX spike at 0.15 ms. Real hardware starts with the references at zero. See section 8 of
  `PRECHARGE_DIODES_HANDOFF.md`.
```

8e. In the LTspice section, directly after the line that begins `- model libraries:` and the line that follows it
(ending `TVS_5p0SMDJ.lib`, `UCC21520.lib`.), insert:
```
- D28-D30 (pre-charge diodes, S2MW) use an inline `.model S2MW` directive: LTspice's 1N4007 scaled to a 2 A die
  (VF 0.91 V at 2 A; data sheet max 1.1 V). Jingdao publishes no SPICE model.
```

### Step 9: Final check and report
9a. Hashes of the changed files, for the report.
```powershell
Get-FileHash -Algorithm SHA256 "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST.kicad_sch","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad\BOOST_power_RC2.kicad_pcb","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\LTspice\BOOST.asc","C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\README.md" | Format-Table -AutoSize Hash, Path
Get-ChildItem "C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_schematic_cleanup\KiCad" -Force -Filter "~*.lck"
```
**Expected:** four hashes (they will differ from the starting ones) and no lock files.

9b. Report to the user, in this order:
1. One line: done or stopped (and at which step).
2. The backup folder path.
3. For each of steps 3, 4b, 5a, 6a-6d and 7b-7c: the command's key output lines, and whether each matched the
   Expected text.
4. The picture from 6e (attach or give its path), and whether it matches the reference.
5. The hashes from 9a.
6. Anything unexpected, even if it looked harmless.

Do not regenerate gerbers, BOM or CPL files. Do not touch `BOOST_package` or `BOOST_package_for_review`. The user
decides those separately.

---

## 6. When to stop and ask the user
- Any output differs from its Expected text. That includes counts, a hash, a missing `PASS`, `ALL PASS` or `OK`
  line, or an extra warning.
- A lock file exists, or KiCad or LTspice is running.
- A script prints `STOP`, or raises an exception.
- Anything would need a change not listed in section 4. That includes moving another part, changing a rule, adding
  an exclusion, or editing a library.
- The backup folder already exists.

## 7. Rollback
To undo everything:
1. Copy the files from `BOOST_split_boards\previous\<date>\before_precharge_diodes\` back over the originals:
   - `KiCad\*` to `BOOST_schematic_cleanup\KiCad\`;
   - `LTspice\BOOST.asc` to `BOOST_schematic_cleanup\LTspice\`;
   - `README.md` to `BOOST_schematic_cleanup\`.
2. Delete `BOOST_schematic_cleanup\precharge_check\`.
3. Check the hashes from 4.4 again.

---

## 8. Notes for the user (not tasks for the agent)

1. **LTspice as-drawn start shows 81 V.**
   - The cause: `BOOST.asc` starts with the references and servos already settled (`.ic` lines) while the battery,
     cable and the 12 V gate-drive rail ramp up from zero. With the diodes, the outputs pre-charge within about
     0.1 ms. At 0.15 ms channel 2 is enabled with 45 A in L1 while its bootstrap is still empty (12 V rail at about
     7-10 V). L1's current then goes into the TVS: LX 81.2 V, about 9 mJ.
   - Without the diodes, the same start gives 60 V but a 118 A inrush in L1, over twice its saturation current.
   - A real power-up starts with Vref/IREF at zero, because the Nano runs from the board's 12 V and the 10k/10 uF
     filters start empty. That case was simulated with the S2MW model:
     - 14.8 V: 62.3 V peak, 3.9 A in L1, 4.7 mJ in the TVS;
     - 16.8 V: 62.5 V, 4.0 A, 4.7 mJ.
   - **Keep the firmware rule:**
     - start or restart with Vref and IREF low and let the filters ramp;
     - never connect the battery while the Nano (on USB, for example) is already commanding a reference.
   - The user wants the LTspice default start changed to a realistic power-up. That is a **separate, later task**
     and is not part of this handoff: the agent must leave the `.ic` lines as they are.
2. **Fuse.** The diodes connect the battery straight to each output, so a short from an output to ground draws
   battery current through D28/D29/D30. **Answered 2026-09-29:** there is a fuse near the batteries, outside the
   driver's housing, protecting the cables and the driver. In that fault the S2MW may still fail, possibly shorted,
   before the fuse opens.
3. **J1 hardware.** D30 sits 5.2 mm (courtyard) and 5.8 mm (nearest pad) from the centre of the J1 battery bolt, on
   the underside where the nut goes. A standard M4 nut plus a DIN 125 washer (9 mm OD) clears it. Do not use a large
   (DIN 9021, 12 mm) washer under J1.
4. **Board edge.** D30's courtyard reaches the board edge (x 104.05). Its pads end 0.65 mm inside and its body
   0.25 mm inside. KiCad does not flag this. If the board is panelised with a V-score on that edge, move D30 in by
   0.1 mm first, which leaves 0.25 mm to the GATE_M4 via.
5. **Via under D28.** D28's cathode via sits under the diode body, between the pads, 0.55 mm from the cathode pad
   and 0.35 mm from the anode pad. The fab notes already specify epoxy-filled, capped vias, so this is fine for
   reflow.
6. **Feed path.** D28 and D29 take their Vin through the regulators' 1 mm feed tracks and single vias, which also
   feed U1/U17. That copper only carries the brief pre-charge pulse; it limits the surge a little, and nothing in
   normal running.
7. **Not verified from a data sheet:** the S2MW's short-pulse (under 1 ms) surge capability (section 3), and the
   Blue Rocket second source (C2900725).
8. **Still to do after this change** (your decision):
   - regenerate the power board's gerbers, drill files, fab drawing, 3D model and JLC BOM/CPL (the three diodes are
     bottom-side parts, like D19);
   - copy the change into `BOOST_package` and `BOOST_package_for_review`. The user will ask for this later; until
     then everything stays in `BOOST_schematic_cleanup`;
   - change the LTspice default start to a realistic power-up (see note 1).
