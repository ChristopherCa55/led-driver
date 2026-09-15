# Re-place tools (copied from the 2026-09-14/15 session scratchpad)

See `../HANDOFF_SUMMARY_2026-09-15.md` for the decisions, results and next steps.

Two Pythons are used:
- **KiCad Python** `C:/Program Files/KiCad/10.0/bin/python.exe` for anything that imports `pcbnew`: `syncboard.py`, `fpinventory.py`, `papply.py`, `tftest.py`.
- **Anaconda Python** (has numpy and matplotlib) for everything else.

## placement/

| File | Purpose |
|---|---|
| `pmodel.py` | Geometry model: courtyards, pads, tab holes, board outline with notch. Loads `inv_power2.json` from this folder. B.Cu transform verified against pcbnew by `tftest.py`. |
| `pcheck.py`, `pplot.py`, `sa_view.py` | Brief distance targets, mechanical checks (washer keep-outs, screwdriver paths, screw-distance rule, overlaps), two-side plot |
| `psa4.py` | Simulated-annealing placer: rigid groups (switch pairs, sink + shunt, LED pad pairs), per-target goals, movable or fixed card, `only_move`. Saves a checkpoint 20 times per run. |
| `mk6.py`, `mk7.py` | Config builders. `mk6` holds the check-in 3 rules; `mk7` fixes J10 and a 45 mm card at candidate L/R/C/T/B. |
| `psat.py`, `psat_cfg.json` | Greedy small-part placer (net anchors, bottom-side preferences). Exits 3 if any part cannot be placed. |
| `pstand.py`, `pscrews.py` | Standoff positions; screw plan and the list of FETs that get the no-hole footprint |
| `papply.py` | Writes a WIP board from a layout: notched outline, washer and standoff keep-outs, card outline on Eco1, "NOT FOR FABRICATION" note. Refuses footprints without a position. |
| `ptable.py`, `pdrc.py` | Distance table (brief targets plus agreed goals with `--goals=CONFIG`); DRC summary |
| `run_place.sh` | Pipeline: `sh run_place.sh RESULT_WITH_STANDOFFS.json NAME [GOALS_CONFIG]`. Copies the shipped `BOOST_power.kicad_pro` next to the output so DRC uses the real rules. |
| `syncboard.py`, `fpinventory.py` | Build a split board from the netlist (`--check` verifies parity); footprint inventory |
| `p6l_1.*` | Best layout so far (33 of 43 agreed goals) |
| `p7?_cfg.json`, `p7L.json`, `p7?.log` | Five J10-position candidate configs (L, R, C, T, B). Only L ran (`p7L.json`, not reviewed); the R/C/T/B logs show a start-up crash from non-numeric seeds. Rerun, e.g. `python psa4.py p7R_cfg.json p7R 802`. |
| `wip_NOT_FOR_FAB/` | Synced but unplaced boards used as the pipeline's source. Not for fabrication. Their `.kicad_pro` files lack the shipped rules. |

Typical sequence:

```
python psa4.py p7C_cfg.json p7C 803
python sa_view.py p7C.json p7C_cfg.json p7C.png
python ptable.py p7C.json p7C.distances.md --goals=p7C_cfg.json
python pscrews.py p7C.json p7C_cfg.json
python pstand.py p7C.json p7C_st.json
sh run_place.sh p7C_st.json p_p7C p7C_cfg.json
```

## schematic/

- `netcheck.py`: checks every §4 change and the J10/J11 pinout on an exported netlist, plus the ERC json.
- `netdiff.py`: netlist diff by content.
- `setfp.py`: sets the Footprint field for given refs (verified, `--dry-run`).
- `schedit.py`, `schlib.py`, `patch_rsense.py`: the edit scripts used for the §4 changes (record only; paths inside point at the old scratchpad).

## sim/

- `deadtime2.py`: dead-time margin with a threshold parameter. It imports `measure.py` from `handoff_2026-09-14/sim/scripts/`.
- `s150`, `s150lv`, `s220`, `s220lv`: netlists (cp1252) and logs. The `.raw` files (~140 MB each) were not copied; rerun LTspice 24 in batch mode (`-b`) to regenerate them.
- `input_caps/`: the input-capacitor ripple runs.

## Other

- `replace_notes.md`: running log of verified facts and decisions.
- `pdftext.py`: dependency-free PDF text extraction (zlib); used to read the LM2940 and L78L datasheets.
