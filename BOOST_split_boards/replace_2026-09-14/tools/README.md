# Re-place tools (copied from the 2026-09-14/15 session scratchpad)

See `../HANDOFF_SUMMARY_2026-09-15.md` for the decisions, results and next steps.

Two Pythons are used:
- **KiCad Python** `C:/Program Files/KiCad/10.0/bin/python.exe` for anything that imports `pcbnew`: `syncboard.py`, `fpinventory.py`, `papply.py`, `tftest.py`.
- **Anaconda Python** (has numpy and matplotlib) for everything else. On the 2026-09-15 machine plain `python` (C:\Python313) has both.

## placement/

| File | Purpose |
|---|---|
| `pmodel.py` | Geometry model: courtyards, pads, tab holes, board outline with notch. Loads `inv_power2.json` from this folder. B.Cu transform verified against pcbnew by `tftest.py`. |
| `pplot.py`, `sa_view.py` | Two-side plot with screw circles and the card outline; mechanical checks (washer keep-outs, tool paths, screw-distance rule, overlaps, card and corner rules) |
| `psa4.py` | Simulated-annealing placer: rigid groups (switch pairs, sink + shunt, LED pad pairs), per-target goals, movable or fixed card, `only_move`. Saves a checkpoint 20 times per run. 2026-09-15: optional weight `ramp`; checkpoint moved to the top of the loop. |
| `psa5.py` | Supersedes psa4 (same config keys). Screw-owning moves costed locally (~9x faster, exact: `tdelta.py`), `card_zones` that move with the card, `random_init`, `p_teleport`, `tall_tab_mm` / `tall_standoff_mm`. Importable as a model (no annealing unless run as a script). |
| `mk6.py`, `mk7.py` | Config builders. `mk6` holds the check-in 3 rules; `mk7` fixes J10 and a 45 mm card at candidate L/R/C/T/B. |
| `mk8.py` | Refinement config from a p7 result: standoffs in 17 mm card-corner squares, legality ramp. |
| `mk9.py` | Global search config: random start, card and J10 free, standoff corner zones move with the card, ramp. |
| `mk10.py` | Legality weights from the start (no ramp), teleport moves, optional start layout for polish passes. |
| `mk11.py` | Rigid INPUT (L1+M1+D19+R1) and LED-channel (sink+shunt+pads) groups. Tried in p12; worse, kept as a record. |
| `pcost.py` | Cost breakdown of a result under its config: weighted terms and the worst parts per term. |
| `prank.py` | Ranks results: legal first (unweighted overlap, keep-out, card/zone, screw distance), then goals met, then weighted miss. |
| `pcheck.py` | Brief targets, agreed goals, plus (2026-09-15) stage 6 gate-loop targets (series R, pulldown, turn-off diode within 5 mm of the gate pin) and stage 7 commutation-loop report rows. |
| `psat.py`, `psat_cfg.json` | Greedy small-part placer (net anchors, side preferences); exits 3 if a part cannot be placed. `place_first` (ordered) and `either_side` decide who gets the space at a pin: rail ceramic, then LX gate parts, then rail gate parts, per channel. |
| `pnettie.py` | Puts NT1-NT3 on their shunts' top pads after psat (net-ties have no courtyard). Called by `run_place.sh`. |
| `tdelta.py` | Checks psa5's local move costing against full re-evaluation; prints typical move deltas (for T0). |
| `pstand.py`, `pscrews.py` | Standoff positions; screw plan and the list of FETs that get the no-hole footprint |
| `papply.py` | Writes a WIP board from a layout: notched outline, washer and standoff keep-outs, card outline on Eco1, "NOT FOR FABRICATION" note. Refuses footprints without a position. |
| `ptable.py`, `pdrc.py` | Distance table (brief targets plus agreed goals with `--goals=CONFIG`); DRC summary |
| `run_place.sh` | Pipeline: `sh run_place.sh RESULT_WITH_STANDOFFS.json NAME [GOALS_CONFIG] [SRC_BOARD]`. Copies the shipped `BOOST_power.kicad_pro` (repo-relative) next to the output so DRC uses the real rules; PNG views via `kicad-cli pcb render` (Inkscape optional). |
| `syncboard.py`, `fpinventory.py` | Build a split board from the netlist (`--check` verifies parity); footprint inventory |
| `p6l_1.*` | Best layout so far (33 of 43 agreed goals) |
| `p7?_cfg.json`, `p7?.json`, `p7?.log`, `p7?.png`, `p7?.distances.md` | Five J10-position candidates (L, R, C, T, B), all run 2026-09-15 (seeds R 802, C 803, T 804, B 805). None legal. |
| `p8/` ... `p15/` | 2026-09-15 search rounds (configs, logs, results): p8 = mk8 refinement of p7; p9 = mk9 global; p10 = mk10 legality-first; p11 = relaxation variants (A tab-screw tall clearance 4 mm; B + standoffs in card quadrants; C + screw distance 30 mm); p12 = mk11 groups; p13 = cool polish; p14 = ramp polish under D (4 mm, quadrants, 25 mm); p15 = keep-out polish, `p15_b10_k1` chosen. See `replace_notes.md`. |
| `BOOST_power_p15_WIP_NOT_FOR_FAB.*` | WIP power board from `p15_b10_k1` (placement only, no copper): `.kicad_pcb` + shipped `.kicad_pro`, `.full.json`, `.distances.md`, `.drc.json`, `.top/.bottom.svg`, `.render_top/_bottom.png`, `.model.png`, `.kicad_pcb.pads.json`. |
| `inv_power3.json` | Inventory after the 2026-09-15 schematic changes; use with `PMODEL_INV=inv_power3.json`. |
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
- `capedit.py`: the 2026-09-15 edit (C30 tantalum, C7/C55 1210 MLCC, C41/C44/C45 restored at the sink op-amp inputs); checks every new connection point and symbol area is empty.
- `schedit.py`, `schlib.py`, `patch_rsense.py`: the edit scripts used for the §4 changes (record only; paths inside point at the old scratchpad).

## sim/

- `deadtime2.py`: dead-time margin with a threshold parameter. It imports `measure.py` from `handoff_2026-09-14/sim/scripts/`.
- `s150`, `s150lv`, `s220`, `s220lv`: netlists (cp1252) and logs. The `.raw` files (~140 MB each) were not copied; rerun LTspice 24 in batch mode (`-b`) to regenerate them.
- `input_caps/`: the input-capacitor ripple runs.

## Other

- `replace_notes.md`: running log of verified facts and decisions.
- `pdftext.py`: dependency-free PDF text extraction (zlib); used to read the LM2940 and L78L datasheets.
