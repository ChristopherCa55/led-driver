# BOOST order checklist, scenario A: final (2026-09-25)

Two JLCPCB orders (power: 5 PCBs, 2 assembled; card: 5 panels, 2 assembled), plus four small orders elsewhere.
**Total $760.83 with the McMaster pad** (shipping and tax not included). Every price is read, except the two
Farnell UK prices converted from GBP (marked "GBP").

## Before you order

- [x] **Rev6 is in your schematic** (`BOOST-github/BOOST/BOOST.kicad_sch`, written 2026-09-25). The boards, gerbers and BOM below
      use it: R1 = CSS4J-4026R-1L00F, U25 = INA241A4.
- [ ] **Stock**, on JLC's BOM page after upload (2026-09-25 values in brackets). **If the 220 uF line is short, stop
      and tell me before ordering.**
  - EEH-ZU1H221P C6843593: need 18 (19)
  - LM2940S-12/NOPB C2877347: need 2 (2). If short, use **LM2940CS-12/NOPB C2865267** (7).
  - INA241A4IDR C22427873: need 2 (116)
  - CSS4J-4026R-1L00F C2076400: need 2 (385)
  - MCP6241T-E/OT C49889: need 18 (38)
  - EEH-ZU1E681UP C29664285: need 6 (10)
- [ ] Optional: read the TG-AD30 price (URL at the bottom). If a 1.5 mm sheet of 150 x 150 mm or less costs about
      $40 or less, buy it instead of the McMaster pad.

## JLC order 1: power board (`BOOST_power_RC2/`, `bom/`)

| Page | Set |
|---|---|
| Gerber | upload `BOOST_power_RC2_gerbers.zip` |
| Base material, layers | FR-4, **8** |
| Dimensions, quantity | 74 x 86 mm, **5**, Single PCB |
| Thickness, material | 1.6 mm, FR4 TG155 |
| Surface finish | **ENIG** (1 U") |
| Outer / inner copper | 1 oz / **1 oz** (inner defaults to 0.5 oz: change it) |
| Specify stackup | No |
| **Via covering** | **Epoxy Filled & Capped** (the 8-layer default, $0.00) |
| Min via hole / diameter | 0.3 mm / (0.4 / 0.45 mm) |
| Mark on PCB | **Remove Mark** |
| Electrical test | **Flying Probe Fully Test** |
| Everything else | defaults (green, +/-0.2 outline, no gold fingers, castellations, edge plating) |
| PCB Assembly | on: **Standard**, **both sides**, quantity **2** |
| BOM / CPL | `bom/BOOST_power_BOM_JLC.csv` / `bom/BOOST_power_CPL_JLC.csv` |
| Not placed (you fit) | M1-M10, L1, J10 |
| Check | the placement preview: polarity of the cans and diodes, pin 1 of every IC |

PCBs $124.10 + assembly about $225.42 = **$349.52**.

## JLC order 2: control card (`BOOST_control_RC2/`, `bom/`)

Same settings as order 1, except:

| Page | Set |
|---|---|
| Gerber | upload `BOOST_control_RC2_gerbers.zip` |
| Dimensions | 45 x 45 mm |
| Delivery format | **Panel by JLCPCB**: column 1, row 1, edge rails **on four sides, 12.5 mm** (70 x 70 mm panel) |
| Quantity | **5** panels (5 cards) |
| PCB Assembly | Standard, both sides, quantity **2** |
| BOM / CPL | `bom/BOOST_control_BOM_JLC.csv` / `bom/BOOST_control_CPL_JLC.csv` (single-card coordinates; check the preview places them on the panelled card) |
| Not placed (you fit) | J11; J9 is wire pads; H1-H4 are holes |

PCBs $137.04 + assembly about $167.31 = **$304.35**.

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

Buying 10 of the HNSM3 ($13.22) and 10 of the Boyd washers ($1.51) instead of 8 adds $2.09 for spares.

**You already own:** M1-M10, L1, the J9 wires and plug, and the buck. The buck must regulate 5.0 V +/-5 % at 200 mA or
more from 11-13 V, and survive at least 20 V. No extra input filter is needed (your decision).

**Before first power-up:** the tab-to-case check in BUILD_NOTES (order of work, step 7a). All ten FETs must read open
to the case. It is mandatory with the McMaster pad, which publishes no dielectric strength.

## Total, scenario A

| JLC (both orders) | Mouser | LCSC | McMaster | Digi-Key | Newark/Farnell | **Total** |
|---|---|---|---|---|---|---|
| $653.87 | $24.62 | $0.29 | $55.61 | $12.64 | $13.80 | **$760.83** + shipping + tax |

Pad alternatives:
- Parker 61-06-0909-G579 (0.060 in) instead of the McMaster pad: **$862.67**.
- t-Global TG-AD30 1.5 mm instead: $733.92 plus its price.

TG-AD30 URL: https://www.digikey.com/en/products/result?keywords=TG-AD30
