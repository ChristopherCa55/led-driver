# BOOST order checklist, scenario A (updated 2026-10-01)

Two JLCPCB orders (power: 5 PCBs, 2 assembled; card: 5 panels, 2 assembled), plus four small orders elsewhere.
**Total $699.68 with the McMaster pad** (shipping and tax not included). Every price is read, except the two Farnell
UK prices converted from GBP (marked "GBP").

**Since 2026-09-25 ($760.83):**
- the control card is 6 layers ($73.57 instead of $137.04);
- the pre-charge diodes D28-D30 (S2MW) are on the power board;
- JLC stock and prices were read again on 2026-09-30.

## Before you order

- [ ] **The 220 uF output capacitor is short.** EEH-ZU1H221P (C6843593): 14 in stock on 2026-09-30, and two power
      boards need 18. Decide one of these first:
  - **Recommended:** the cheaper Panasonic EEH-ZS1H221P (C385885) on C70, C71, C75, C77, C78 and C88; keep the ZU on
    C74, C86 and C87. This is item 1 in COST_SUMMARY "Ways to save"; it needs a schematic field change, which I make
    when you say so.
  - or buy 4 EEH-ZU1H221P elsewhere, have JLC leave 4 positions empty on one board, and solder them yourself.
- [x] **The design files:** schematic rev6 plus D28-D30, the 8-layer power board and the 6-layer card, all in
      `BOOST_package/KiCad/`. The gerbers, BOM and CPL in this folder match them.
- [ ] **Stock**, on JLC's BOM page after upload (2026-09-30 values in brackets).
  - EEH-ZU1H221P C6843593: need 18 (14): **see above**
  - LM2940S-12/NOPB C2877347: need 2 (2). If short, use **LM2940SX-12/NOPB C131916** (4) or **LM2940CS-12/NOPB
    C2865267** (7).
  - EEH-ZU1E681UP C29664285: need 6 (10)
  - MCP6241T-E/OT C49889: need 18 (38)
  - MCP4451-103E/ST C145613: need 2 (40)
  - TR3D476K025C0250 C4979367: need 2 (63)
  - CD74HC4066M96 C179842: need 2 (73)
- [ ] Optional: read the TG-AD30 price (URL at the bottom). If a 1.5 mm sheet of 150 x 150 mm or less costs about
      $40 or less, buy it instead of the McMaster pad.

## JLC order 1: power board

| Page | Set |
|---|---|
| Gerber | upload `BOOST_power_RC2_gerbers.zip` |
| Base material, layers | FR-4, **8** |
| Dimensions, quantity | 74 x 86 mm, **5**, Single PCB |
| Thickness, material | 1.6 mm, FR4 TG155 |
| Surface finish | **ENIG** (8 layers default to OSP: change it) |
| Outer / inner copper | 1 oz / **1 oz** (inner defaults to 0.5 oz: change it) |
| Specify stackup | No |
| **Via covering** | **Epoxy Filled & Capped** (the 8-layer default, $0.00) |
| Min via hole / diameter | 0.3 mm / (0.4 / 0.45 mm) |
| Mark on PCB | **Remove Mark** |
| Electrical test | **Flying Probe Fully Test** |
| Everything else | defaults (green, +/-0.2 outline, no gold fingers, castellations, edge plating) |
| PCB Assembly | on: **Standard**, **both sides**, quantity **2** |
| BOM / CPL | `BOOST_power_BOM_JLC.csv` / `BOOST_power_CPL_JLC.csv` |
| Not placed (you fit) | M1-M10, L1, J10 |
| Check | the placement preview: polarity of the cans and diodes (including **D28-D30 on the bottom**), pin 1 of every IC |

PCBs $124.10 + assembly about $227.39 = **$351.49**.

## JLC order 2: control card

Same settings as order 1, except:

| Page | Set |
|---|---|
| Gerber | upload `BOOST_control_RC2_gerbers.zip` |
| Layers | **6** (the stackup in the fab drawing is JLC's standard 6-layer 1.6 mm build, JLC061611-7628) |
| Dimensions | 45 x 45 mm |
| Surface finish, inner copper | **ENIG**, **1 oz** (6 layers also default to OSP and 0.5 oz: change both) |
| Delivery format | **Panel by JLCPCB**: column 1, row 1, edge rails **on four sides, 12.5 mm** (70 x 70 mm panel) |
| Quantity | **5** panels (5 cards) |
| PCB Assembly | Standard, both sides, quantity **2** |
| BOM / CPL | `BOOST_control_BOM_JLC.csv` / `BOOST_control_CPL_JLC.csv` (single-card coordinates; check the preview places them on the panelled card) |
| Not placed (you fit) | J11; J9 is wire pads; H1-H4 are holes |

PCBs $73.57 + assembly about $167.66 = **$241.23**.

If you take "Ways to save" item 2 (0.5 oz inner copper on the card, -$16.74), leave the inner copper at 0.5 oz. Tell me
first, so I can re-make the fab drawing's stackup table.

## Buy elsewhere (2 sets)

| Vendor | Part | Qty | $ |
|---|---|---|---|
| Mouser (or Samtec) | Samtec ESQ-115-44-G-D, J10 socket | 2 | 18.26 |
| Mouser (or Samtec) | Samtec TSW-115-07-G-D, J11 header | 2 | 6.36 |
| **LCSC** | Bourns **MF-R050** PTC, C208476 (J9 pin-9 fuse; 0.5 A hold, 0.25 A at 75 C) | 2 | 0.29 |
| **McMaster-Carr** | **1272N32** thermal pad, 3 W/m-K, 0.060 in, 4 x 4 in (cut 10 x 16 mm, 20 pads) | 1 | 26.91 |
| McMaster-Carr | 92000A107 M2.5 x 12 pan head, 18-8 (pack of 100): FET tab screws | 1 pack | 5.65 |
| McMaster-Carr | 93657A200 nylon spacer M2.5 x 2.0 mm: tab-screw spacer | 8 | 7.36 |
| McMaster-Carr | **92605A109** M3 x 20 set screw, 18-8, flat tip (pack of 25): floor stud | 1 pack | 10.69 |
| McMaster-Carr | **94669A099** aluminium spacer M3, 5.00 +/-0.13 mm, 4.5 mm OD: floor stud | 10 | 5.00 |
| Digi-Key | Boyd 7721-7PPSG shoulder washer: tab-screw insulator | 8 | 1.31 |
| Digi-Key | Essentra HNSM3-20-5.5-1 nylon F/F standoff, 20 mm: power board to card | 8 | 11.33 |
| Newark / Farnell | TR Fastenings TR NWE-34815-M3 nylon washer (pack of 100) | 1 pack | 11.67 (GBP) |
| Newark / Farnell | Wurth 97790803211 M3 x 8 nylon pan head: card screws | 8 | 2.13 (GBP) |
| (your stock) | low-strength threadlocker (Loctite 222 or similar) for the set screws | - | not priced |

Subtotals:
- Mouser $24.62
- LCSC $0.29
- McMaster $55.61
- Digi-Key $12.64
- Newark/Farnell $13.80

These prices (except the PTC) are the 2026-09-25 readings. Buying 10 of the HNSM3 ($13.22) and 10 of the Boyd washers
($1.51) instead of 8 adds $2.09 for spares.

**You already own:** M1-M10, L1, the J9 wires and plug, and the buck. The buck must regulate 5.0 V +/-5 % at 200 mA or
more from 11-13 V, and survive at least 20 V. No extra input filter is needed (your decision).

**Before first power-up:** the tab-to-case check in BUILD_NOTES (order of work, step 7a). All ten FETs must read open
to the case. It is mandatory with the McMaster pad, which publishes no dielectric strength.

## Total, scenario A

| JLC (both orders) | Mouser | LCSC | McMaster | Digi-Key | Newark/Farnell | **Total** |
|---|---|---|---|---|---|---|
| $592.72 | $24.62 | $0.29 | $55.61 | $12.64 | $13.80 | **$699.68** + shipping + tax |

Pad alternatives:
- Parker 61-06-0909-G579 (0.060 in) instead of the McMaster pad: **$801.52**.
- t-Global TG-AD30 1.5 mm instead: $672.77 plus its price.

Pay both JLC orders together so they ship as one parcel.

TG-AD30 URL: https://www.digikey.com/en/products/result?keywords=TG-AD30
