# Runbook — environment, commands, gotchas

Verified on this machine on 2026-09-15. Paths use the Git-Bash style (`/c/...`); in PowerShell use
`C:\...`. Repository root: `C:\Users\bubba\OneDrive\Documents\led-driver`.

---

## 1. Environment

| Tool | Path on this machine | Notes |
|---|---|---|
| `kicad-cli` | `C:/Program Files/KiCad/10.0/bin/kicad-cli.exe` | reports version **10.0.0** |
| KiCad Python (has `pcbnew`) | `C:/Program Files/KiCad/10.0/bin/python.exe` | `pcbnew.GetBuildVersion()` → 10.0.0. **No numpy/matplotlib.** |
| System Python | `C:/Python313/python.exe` (on PATH as `python`) | numpy 2.3.1, matplotlib 3.10.3. **No `pcbnew`.** |
| LTspice | `AppData/Local/Programs/ADI/LTspice/LTspice.exe` | 24.0.12; netlists must be cp1252, UTF-8 "µ" breaks it. A 40 ms run takes 25–35 min. |
| Inkscape | `C:/Program Files/Inkscape/bin/inkscape.exe` | optional, only for SVG → PNG in `run_place.sh` |

**The split matters.** Anything importing `pcbnew` runs under KiCad's Python; anything needing numpy or
matplotlib runs under system Python. The existing scripts follow this split:
`syncboard.py`, `fpinventory.py`, `papply.py`, `tftest.py` → KiCad Python; everything else → system
Python. (The older notes say "Anaconda Python"; on this machine it is `C:/Python313`.)

---

## 2. The three commands you will use most

Run these from `BOOST_split_boards/replace_2026-09-14/tools/placement/`.

### DRC on a saved board — this is the acceptance test

```bash
"/c/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc --severity-all --format json \
  -o OUT.drc.json BOARD.kicad_pcb
python pdrc.py OUT.drc.json
```

`pdrc.py` prints violations by type and lists the placement-relevant ones item by item. For routing
work also read `unconnected_items` — it must reach **0**. The baseline board (no copper) reports 270.

DRC reads the rules from the `.kicad_pro` sitting next to the `.kicad_pcb`, so **make sure the shipped
project file is there** or you are testing against KiCad defaults, not the real rules.

### Renders and plots

```bash
K="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
"$K" pcb export svg --layers "F.Cu,F.CrtYd,F.Fab,Edge.Cuts,User.Eco1,User.Comments" \
  --mode-single --page-size-mode 2 --exclude-drawing-sheet -o NAME.top.svg NAME.kicad_pcb
"$K" pcb export svg --layers "B.Cu,B.CrtYd,B.Fab,Edge.Cuts,User.Eco1" \
  --mode-single --page-size-mode 2 --exclude-drawing-sheet -o NAME.bottom.svg NAME.kicad_pcb
"$K" pcb render --side top    --width 1600 --height 1800 --background opaque --quality basic \
  -o NAME.render_top.png NAME.kicad_pcb
"$K" pcb render --side bottom --width 1600 --height 1800 --background opaque --quality basic \
  -o NAME.render_bottom.png NAME.kicad_pcb
```

`sa_view.py` draws both sides from the layout JSON (screw circles, card outline, courtyards) without
needing KiCad:

```bash
python sa_view.py LAYOUT.json CONFIG.json OUT.png
```

### Distance table against the targets

```bash
python ptable.py LAYOUT.full.json OUT.distances.md --goals=CONFIG.json
```

The last line prints `Brief targets met: N of 49. Agreed goals met: M of 49.`

---

## 3. The placement pipeline (if you re-place)

From `replace_2026-09-14/tools/placement/`:

```bash
# 1. anneal (system Python).  ARGS: config, output stem, numeric seed
python psa5.py p16_cfg.json p16_s1 801

# 2. inspect and rank results   (note: prank takes the CONFIG first, then the results)
python prank.py p16_cfg.json p16_s1.json p16_s2.json
python pcost.py p16_s1.json p16_cfg.json

# 3. screw plan and standoffs
python pscrews.py p16_s1.json p16_cfg.json
python pstand.py  p16_s1.json p16_s1_st.json

# 4. whole pipeline: small parts -> net-ties -> KiCad board -> table, plots, DRC
sh run_place.sh p16_s1_st.json BOOST_power_p16_WIP_NOT_FOR_FAB p16_cfg.json \
   wip_NOT_FOR_FAB/power_sync3.kicad_pcb
```

`run_place.sh` copies the shipped `BOOST_power.kicad_pro` next to the output **twice** (once before
`papply.py`, once after, because `SaveBoard` rewrites it), then runs the table, SVG/PNG export and DRC.

Config builders: `mk10.py` (legality weights from the start, teleport moves, optional start layout for
polish) and `mk9.py` (global random-start search) are the ones that produced the baseline lineage.
`mk11.py` (rigid groups) was tried and was worse — kept as a record.

**Seeds must be numeric.** An earlier run lost four candidates by passing `"80R"`, `"80C"` etc.

### Rebuilding a board from the netlist

```bash
KP="/c/Program Files/KiCad/10.0/bin/python.exe"
"$KP" syncboard.py SRC.kicad_pcb ../../../../BOOST-github/BOOST/BOOST_9-15_nohole.net \
      ../../board_assignment_2026-09-15.json POWER OUT.kicad_pcb
"$KP" syncboard.py --check OUT.kicad_pcb NETLIST.net ASSIGN.json POWER   # parity check
```

`--check` verifies every footprint, library ID, value and pad net in a fresh process. It must report
parity 0. Note `wip_NOT_FOR_FAB/` has `power_sync3` (current) but only `control_sync2` — **the control
card has not been re-synced since the 2026-09-15 schematic changes.** Build `control_sync3` before
working on the card.

---

## 4. Gotchas that have already cost time

| Gotcha | What to do |
|---|---|
| `pcbnew.SaveBoard` rewrites the `.kicad_pro` and drops the netclasses, netclass patterns and rules | Copy the shipped `BOOST_power.kicad_pro` next to the board **after every save**, then add any new netclass members |
| `BOARD.Remove` breaks later SWIG proxies in KiCad 10 Python | Strip items in the file *text* before loading the board (this is what `syncboard.py` does) |
| `FootprintLibCreate` fails | Use `PCB_IO_KICAD_SEXPR` |
| A B.Cu footprint's transform | `Flip(LEFT_RIGHT)` then `SetOrientationDegrees`; a local point maps as (x, −y) then rotated. `tftest.py` checks the model against pcbnew |
| `lib_footprint_issues` DRC warnings on L1, R1 and the 16.5 mm cans | The board needs a project `fp-lib-table` with the `BOOST` and `CSCF3218-6R8MC` libraries, `${KIPRJMOD}`-relative. There is a good one at `replace_2026-09-14/tools/placement/fp-lib-table` |
| Net-ties have no courtyard | The small-part placer once put NT1 on M10's source pin (`shorting_items`). `pnettie.py` puts each tie on its shunt's top pad end |
| `sed -i` on `.kicad_pro` | Don't — they are CRLF and it corrupts them. Use a JSON round-trip |
| Heredocs in the Bash tool mangle backslashes, and long inline chains fail to parse | Put regex-heavy code in a file and run the file |
| KiCad lock files (`~BOOST_power.kicad_pcb.lck`) | The user may have the project open. Ask them to close KiCad before you replace shipped files |
| KiCad's GUI rewrote the shipped `.kicad_pro` once, dropping the Power/Gate/Rail netclasses | It was restored from git. If the rules look wrong, check git before assuming |
| PDF datasheets | No poppler or pypdf installed. `replace_2026-09-14/tools/pdftext.py` is a zlib-based extractor that worked on TI, National and ST PDFs |
| Samtec and some mirrors rate-limit | Octopart-hosted PDF copies usually load |

---

## 5. Where to put your output

- Work in progress: a new folder, e.g. `BOOST_split_boards/route_2026-09-16/`, with `NOT_FOR_FAB` in
  every board filename and a "NOT FOR FABRICATION" note on the board itself.
- Before replacing `BOOST_split_boards/BOOST_power.kicad_pcb` or `BOOST_control.kicad_pcb`: copy the
  current ones to `BOOST_split_boards/previous/<date>/` first, and check no `.lck` file is present.
- Keep a running verified-facts log the way `replace_2026-09-14/tools/replace_notes.md` does: every
  number you rely on, where it came from, and what you could not verify.
