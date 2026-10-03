# Fab outputs regenerated 2026-09-30 (BOOST_schematic_cleanup boards)

**Later on 2026-09-30, the control card went to 6 layers** (see `../card6_2026-09-30/`).
- `BOOST_control_RC2/` and `work/card_facts.json` are now the 6-layer card: 18 gerber/drill files, 1.609 mm stackup.
  Every layer and both drill files are identical to the 8-layer versions; In1-In4 are the old In2-In5.
- `fab_drawing.py` takes the layer count from the facts. At 6 layers it writes JLC's 6-layer stackup table and says
  "6 copper layers" / "all six layers". The power drawing is byte-identical to before the edit (PNG compared).
- The superseded 8-layer card outputs are in `superseded_8layer_card/`.

Gerbers, drills and fab drawings for the boards in `../../BOOST_schematic_cleanup/KiCad/`: RC2 plus the silkscreen
logos, the pre-charge diodes D28-D30, and their reference labels on B.Fab. The zips and PDFs were copied into
`BOOST_schematic_cleanup/`. The RC2 release record in `../fab_2026-09-24/` is untouched.

Tools are copies of `fab_2026-09-24/tools/`:
- `make_fab.sh` rewrites `fp-lib-table` to point at the cleanup folder's libraries.
- `fab_drawing.py` has a new title date and footer.
- `fab_facts.py` is unchanged.

Run from this folder:
```
sh tools/make_fab.sh ../../BOOST_schematic_cleanup/KiCad/<NAME>.kicad_pcb <NAME> <NAME>
"<KiCad python>" tools/fab_facts.py <NAME>/.src/<NAME>.kicad_pcb work/<power|card>_facts.json
python tools/fab_drawing.py power|card
```

Checks on 2026-09-30:
- DRC of the plotted copies:
  - power: 0 errors, 0 unconnected, 49 warnings (46 logo silk over L1's pad, 2 can silk overlaps, J10 library
    mismatch);
  - card: 0 errors, 0 unconnected, 1 warning (J11 library mismatch).
  - A refill changes no zone.
- Fab facts against `fab_2026-09-24/work/`:
  - card: identical;
  - power: 4 more vias (872: 123 x 0.30, 631 x 0.40, 118 x 0.50). Every minimum is unchanged, and the filled via
    closest to a pad hole is still 0.481 mm away (JLC needs > 0.45).
- Drill hits: only those 4 vias are new.
- Gerbers:
  - card: copper, mask and paste are identical; only the silkscreen differs (logos);
  - power: the copper, bottom mask/paste and silkscreen differ (D28-D30, R47, GATE_M4 route, logos); F.Mask, F.Paste
    and Edge.Cuts are identical.
