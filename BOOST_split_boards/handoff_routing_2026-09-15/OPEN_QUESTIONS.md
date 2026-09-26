# Decisions already made, and what is still open

Source of truth: `BOOST_split_boards/replace_2026-09-14/HANDOFF_SUMMARY_2026-09-15.md` §3 and §12, and
the verified-facts log `replace_2026-09-14/tools/replace_notes.md`. If this file and the summary
disagree, the summary is newer — check it.

---

## 1. Locked — do not revisit without asking

| Topic | Decision |
|---|---|
| FET mounting | All ten TO-220s tab-down against the aluminium case: `TO-220-3_Horizontal_TabUp` footprint on **B.Cu**, body flat against the board underside, insulated, ~1 mm compliant thermal pad under every tab |
| Screwed FETs | M1, M8, M9, M10 get tab holes, a 3.75 mm washer keep-out and a clear screwdriver path. M2–M7 use `BOOST:TO-220-3_Horizontal_TabUp_NoHole` and may be up to 25 mm from the nearest screw |
| Standoffs | Nylon; mounting holes isolated (non-plated, copper keep-out) |
| Card gap | **21.21 mm**: Samtec **ESQ-115-44-G-D** socket at J10 (power board), **TSW-115-07-G-D** header at J11 (card underside) |
| Card position | May sit over the output cans (4.4 mm clear), **never over L1**, and not in the lug corner |
| Card size | **45 × 45 mm** (a 39.2 mm J10 will not fit a 42 mm card with 2 mm margins) |
| Divider resistors | Both resistors of every divider on the control card |
| Input caps | 3 × Panasonic **EEH-ZU1E681UP** (680 µF 25 V, 10 × 12.5 mm, LCSC C29664285). LCSC had 10 in stock: JLCPCB assembly for at most 3 boards; the user hand-fits the rest |
| Output caps | **EEH-ZU1H221P**, 10 × 16.5 mm (16.8 mm max with the V-code) |
| Gate drive | D12 deleted; R15 = 10 Ω; R13/R23/R47 = **220 Ω** (simulated: 40.8 ns minimum dead-time margin nominal, 18.3 ns at the 1.0 V threshold corner) |
| R1 | 4-terminal Bourns **CSS4J-4026K-2L00F** (2 mΩ, 4 W), Kelvin nets `ISNS_P`/`ISNS_N` to U25 |
| Sink sense | Net-ties NT1/NT2/NT3 at the R52/R53/R7 top pads → `SNS_CH1/2/3` → U11.4 / U12.4 / U6.4 |
| M1 inhibit | J9 → 1 × 11, pin 11 = `ARD_M1_INHIBIT`; D27 SOD-123; R105 100 kΩ to GND; Arduino is 5 V logic |
| Regulator bulk caps | C30 → Vishay **TR3D476K025C0250** (47 µF, case D, ESR ≤ 0.25 Ω, LCSC C4979367); C7 and C55 → Murata **GRM32ER71E226KE15L** (22 µF 25 V X7R 1210, JLCPCB C21397) |
| C41/C44/C45 | Restored as 1 nF at the sink op-amp inputs on the power board; DNP-able |
| Case | 128 × 90 × 33 mm inside, 10 mm floor. Power board in the right end. Floor penetrators Ø10 at box (9.5, 3.5) and (118.5, 3.5), each with a Ø15 × 10 mm keep-out. Board notch already cut for the battery cable |

The schematic reflecting all of this is frozen at netlist **`BOOST_9-15_nohole.net`** (ERC 0 errors /
0 warnings, netcheck 0 failures).

---

## 2. Open — ask the user

### 2.1 Blocking the placement sign-off

The previous session ended with a ★ check-in the user has not answered. It is the first thing to
settle, because it decides whether you can keep the baseline placement:

1. **Does the 4.0 mm tab-screw tall-part clearance stand?** The brief's original reading of "clear
   screwdriver path" was 5.5 mm. No legal layout was found at 5.5 mm in ~250 annealing runs; at 4.0 mm
   legal layouts appear. Under 5.5 mm the baseline is illegal (U16 4.05 mm and C69 4.15 mm from M1's
   screw, C87 5.02 from M8's, C71 4.01 and C78 5.21 from M9's).
2. **Standoffs anywhere in their card quadrant** (rather than in 17 mm corner squares)?
3. **Accept `p15_b10_k1`** with its hard-goal misses — M2 → C70 20.1 mm, M3 → C87 18.8 mm,
   L1 LX → M1 16.5 mm?

If the user rejects it, the levers named in the summary are: fewer screw points (e.g. a standoff
doubling as a sink-FET tab screw), a larger LED-pad zone, or looser input-loop goals.

### 2.2 Blocking fabrication, not your routing

| Item | Status |
|---|---|
| **Copper weight B vs C** | Open by design — the user decides from your 1 oz / 2 oz solver table |
| **D19** | Value is `TVS_5KP54A` but the footprint is `Diode_SMD:D_SMC`. The 5KP series is an axial P600 part; which part is actually intended is unverified. Raise it |
| **Screw hardware** | Board underside to tab at the hole is 3.27 mm, so each screwed FET needs a ~3.3 mm insulating spacer plus an insulating shoulder bushing (the tab is the drain). Not confirmed with the user |
| **R1 stock** | CSS4J-4026K-2L00F was out of stock at LCSC on 2026-09-14. Backup: CSS4J-4026R-1L00F (1 mΩ, C2076400) with U25 changed to INA241A4 — that halves the sense signal, so layout error counts double |
| **R1 land pattern** | `BOOST:R_Bourns_CSS4J-4026` — the sense stub length (2.1 mm) and force-pad outer extent are not dimensioned in Bourns' drawing |
| **J10/J11 drill** | Samtec's recommended hole is 1.02 ± 0.03 mm; KiCad's 2×15 footprints drill 1.00 mm, at the low end. Consider 1.05 mm |
| **Sink op-amp accuracy** | MCP6241 offset ±5 mV ≈ ±4 % per channel. A zero-drift op-amp was raised and never decided |
| **MCP4451 resistance variant** | Sets the IREF filter time constant with the restored C41/C44/C45 |
| **LTspice** | `BOOST.asc` has not been updated for the schematic changes, and its servo `.ic` points at renumbered nodes. Who runs the remaining sims is undecided |

---

## 3. How to check in

The previous sessions used a written check-in with: the specific decisions being asked for, plots of
both sides, the distance table against targets, and the DRC summary — see
`BOOST_split_boards/placement_review_2026-09-15/BOOST_power_placement_review.html` for the format.

Ask narrow questions with the numbers attached. "Do you accept 4.0 mm instead of 5.5 mm, given that no
legal layout exists at 5.5 mm?" is answerable; "is the placement OK?" is not.
