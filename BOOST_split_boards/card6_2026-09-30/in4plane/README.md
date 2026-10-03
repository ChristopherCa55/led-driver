# In4 solid-plane attempt on the 6-layer card (2026-09-30) - not adopted

The user asked whether one of the 6-layer card's GND layers could become a full plane, by moving its tracks to the
other layers. Tried with In4 (the old 8-layer In5) as the plane; abandoned. **The user chose to keep the 6-layer card
without a plane**, the one in the three folders (sha 320ee4e4).

**Method:** the work ran in the 8-layer frame, so the original tools keep their layer names; `make_card6.py` would
convert the result. Tools are in `../tools/`:
- `prep_in4plane.py`, `prune_chains.py`, `rip_region.py`, `restore_net_copper.py`, `add_inp_shield.py`;
- `route_card_in4.py` (`--in4plane`, `--inp-on-plane`), `exact_route_in4.py` (`--escape`), `sens_check6.py`,
  `plot_region.py`.

**Variant A:** U2 In+ moved from old In5 to old In4, with a GND shield band on old In3. The 33 nets on old In5 and 4
nets on old In3 were re-routed.
- Best result `sig5.kicad_pcb`, after grid and fine-grid passes plus an exact route for SCL:
  - 2 logic nets unroutable (0A_hi, Reset_raw);
  - a 5V pour split and a cut-off GND sliver on B.Cu between J9's rows, both fixable;
  - one 0.005 mm clearance error.
- A regional rip-up round U2/U5 (`reg0` / `q1` / `q2`) ended with 12 open.

**Variant B:** In+ left as the only track on the plane layer. 10 open after fine-grid repair (`vb1` / `w1` / `w2`).

**Why it fails:**
- No foreign via may sit within 2 mm of In+ copper on any layer, and logic must stay 2 mm from In+ / V_err on F / B.
  Together they leave too few layers to cross the corridor between U101 and U2 / U5.
- With In+ shielded, only old In2 is left to cross it.
- The two nets cannot even leave their end pads, between U101's pins, J9's rows and J11's columns; that held even
  with the plane layer allowed for them.
- The original card needed all six signal layers to close (32 open with 4-5 routing layers, 9 open with 6). A 6-layer
  stack with one solid plane leaves 5.
- A solid plane would need parts moved to open that corridor (offered; not chosen).

**Sensitive nets on the 6-layer card as kept** (`../sens_6now.json`, `../tools/sens_check6.py ... 6now`):

| Net | 8-layer card | 6-layer card |
|---|---|---|
| U2 In+, GND both sides of its run | 100 % | 65.6 % |
| V_err, plane beside its length (off its own vias / pads) | 100 % | 90.4 % |
| Current | 82.4 % | 82.4 % |

All the user's other rules still hold: no foreign vias within 2 mm, the same tracks, DRC clean.
