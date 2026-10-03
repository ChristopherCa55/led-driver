# JLC quote selections, power board 6-layer trial (2026-10-01)

Read on the public quote page `cart.jlcpcb.com/quote`. There was no sign-in and no Gerber upload, and nothing was
saved to a cart. Each option was set with the page's own buttons and read back from the page (a selected option
carries the `cur` class).

## Selections (the same as the 8-layer order in ORDER_CHECKLIST.md, apart from the layer count)

| Option | Selected | Note |
|---|---|---|
| Base material | FR-4 | default |
| Layers | **6** | and 8 for the comparison |
| Dimensions | **74 x 86 mm** | typed into the X / Y fields |
| PCB qty | 5 | default |
| Product type | Industrial/Consumer electronics | default |
| Different design | 1 | default |
| Delivery format | Single PCB | default |
| PCB thickness | 1.6 mm | default |
| PCB colour / silkscreen | Green / White | defaults |
| Material type | **FR4 TG155** | as the 8-layer order (the page defaults to TG135 at 6 layers) |
| Surface finish | **ENIG** | the page resets this to OSP whenever the layer count changes; set again each time |
| Outer copper weight | 1 oz | default |
| Inner copper weight | **1 oz** | the page defaults to 0.5 oz |
| Specify stackup | No | for the price; set to Yes only to read the stackup list (no price change) |
| Via covering | Epoxy Filled & Capped | the page notes it is free on 6+ layers |
| Min via hole / diameter | 0.3 mm / (0.4 / 0.45 mm) | default |
| Board outline tolerance | +/-0.2 mm (Regular) | default |
| Mark on PCB | Remove Mark | |
| Electrical test | Flying Probe Fully Test | the only option |
| Gold fingers, castellated holes, edge plating, other options | No | defaults |
| Build time | the standard (free) one | 8-9 days at 6 layers, 10-11 days at 8 |

## Prices read (5 boards, PCB only, no assembly)

| Layers | Inner copper | Breakdown | Price |
|---|---|---|---|
| 8 | 1 oz | base $90.00, ENIG $17.30, inner 1 oz $16.80 | **$124.10** (matches ORDER_CHECKLIST) |
| **6** | **1 oz** | base $32.00, ENIG $17.30, TG155 $3.47, inner 1 oz $16.80 | **$69.57** |
| 6 | 0.5 oz | base $32.00, ENIG $17.30, TG155 $3.47 | $52.77 (reference only; too thin for the inner power planes) |

**Saving at 6 layers with 1 oz inner: $54.53 per order** of 5 boards.

## Stackups offered at 6 layers, 1.6 mm, 1 oz / 1 oz
The quote page offers "No requirement" plus 24 named stackups. Each was read from the "View Stackup" dialog, and the
parsed gaps are in `tools/stackups.py`. JLC warned on some of them that the real thickness differs from 1.6 mm (for
example 1.534 mm and 1.655 mm). Those prompts were answered "No", and the page was left on "No requirement" and
"Specify Stackup: No". The price stayed $69.57 throughout.

Gaps between copper layers L1-L2 / L2-L3 / L3-L4 / L4-L5 / L5-L6 (mm):

| Stackup | Gaps | Total |
|---|---|---|
| 1080A | 0.069 / 0.400 / 0.490 / 0.400 / 0.069 | 1.618 |
| 1080B | 0.069 / 0.075 / 1.083 / 0.075 / 0.069 | 1.561 |
| 1080C | 0.069 / 0.600 / 0.109 / 0.600 / 0.069 | 1.637 |
| 1080D | 0.069 / 0.100 / 1.106 / 0.100 / 0.069 | 1.634 |
| 1080E | 0.153 / 0.450 / 0.138 / 0.450 / 0.153 | 1.534 |
| 1080F | 0.069 / 0.400 / 0.406 / 0.400 / 0.069 | 1.534 |
| 1080G | 0.153 / 0.150 / 0.842 / 0.150 / 0.153 | 1.638 |
| 1080M | 0.153 / 0.450 / 0.188 / 0.450 / 0.153 | 1.584 |
| 2116 | 0.109 / 0.500 / 0.218 / 0.500 / 0.109 | 1.626 |
| 2116A | 0.109 / 0.130 / 0.918 / 0.130 / 0.109 | 1.586 |
| 2116B | 0.323 / 0.200 / 0.342 / 0.200 / 0.323 | 1.578 |
| 2116C | 0.239 / 0.250 / 0.402 / 0.250 / 0.239 | 1.570 |
| 2116D | 0.109 / 0.550 / 0.138 / 0.550 / 0.109 | 1.646 |
| 2116E | 0.109 / 0.500 / 0.138 / 0.500 / 0.109 | 1.546 |
| 3313A | 0.092 / 0.130 / 1.003 / 0.130 / 0.092 | 1.637 |
| 3313B | 0.092 / 0.100 / 1.049 / 0.100 / 0.092 | 1.623 |
| 3313C | 0.092 / 0.250 / 0.688 / 0.250 / 0.092 | 1.562 |
| 3313D | 0.092 / 0.300 / 0.624 / 0.300 / 0.092 | 1.598 |
| 3313F | 0.260 / 0.250 / 0.356 / 0.250 / 0.260 | 1.566 |
| 3313G | 0.092 / 0.550 / 0.094 / 0.550 / 0.092 | 1.568 |
| 7628 | 0.203 / 0.250 / 0.513 / 0.250 / 0.203 | 1.609 (the card's stackup) |
| 7628B | 0.287 / 0.300 / 0.291 / 0.300 / 0.287 | 1.655 |
| 7628C | 0.203 / 0.400 / 0.203 / 0.400 / 0.203 | 1.599 |
| 7628D | 0.421 / 0.130 / 0.291 / 0.130 / 0.421 | 1.583 |

Totals are dielectric + copper (0.035 outer, 0.03 inner) as listed. Today's 8-layer board, for comparison (the
board file's stackup, 1.654 mm): 0.109 / 0.25 / 0.218 / 0.25 / 0.218 / 0.25 / 0.109 mm.

Which stackup suits each variant is decided in the trial, by the commutation-loop inductance across all of them.
