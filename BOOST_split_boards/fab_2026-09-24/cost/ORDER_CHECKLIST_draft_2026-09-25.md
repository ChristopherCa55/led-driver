# BOOST order checklist, scenario A (2026-09-25)

**Two JLCPCB orders** (power: 5 PCBs, 2 assembled; card: 5 panels, 2 assembled), plus the parts below from
elsewhere. **Grand total $803.86** (shipping and tax not included; four hardware prices still to read).

## Before you order

- [ ] **Rev6 is in your schematic.** It is prepared and checked, but not yet written into
      `BOOST-github/BOOST/BOOST.kicad_sch`, which carries KiCad lock files. It waits for your OK.
- [ ] **Stock**, on JLC's BOM page after upload (2026-09-25 values in brackets). **If the 220 uF line is short, stop
      and tell me before ordering.**
  - EEH-ZU1H221P C6843593: need 18 (19)
  - LM2940S-12/NOPB C2877347: need 2 (2). If short, use **LM2940CS-12/NOPB C2865267** (7).
  - INA241A4IDR C22427873: need 2 (116)
  - CSS4J-4026R-1L00F C2076400: need 2 (385)
  - MCP6241T-E/OT C49889: need 18 (38)
  - EEH-ZU1E681UP C29664285: need 6 (10)
- [ ] The four prices in COST_SUMMARY.md's URL list, read and sent back.

## JLC order 1: power board (files in `BOOST_power_RC2/` and `bom/`)

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
| Everything else | defaults (colour green, outline tolerance +/-0.2, no gold fingers, castellations, edge plating) |
| PCB Assembly | on: **Standard**, **both sides**, quantity **2** |
| BOM / CPL | `bom/BOOST_power_BOM_JLC.csv` / `bom/BOOST_power_CPL_JLC.csv` |
| Not placed (you fit) | M1-M10, L1, J10 (and R1 only if you stay on rev5) |
| Check | the placement preview: polarity of the cans and diodes, pin 1 of every IC |

Bare PCBs $124.10 + assembly about $225.42 = **$349.52**.

## JLC order 2: control card (files in `BOOST_control_RC2/` and `bom/`)

Same settings as order 1, except:

| Page | Set |
|---|---|
| Gerber | upload `BOOST_control_RC2_gerbers.zip` |
| Dimensions | 45 x 45 mm |
| Delivery format | **Panel by JLCPCB**: column 1, row 1, edge rails **on four sides, 12.5 mm** (70 x 70 mm panel). JLC's Standard assembly needs at least 70 x 70 mm |
| Quantity | **5** panels (5 cards) |
| PCB Assembly | Standard, both sides, quantity **2** |
| BOM / CPL | `bom/BOOST_control_BOM_JLC.csv` / `bom/BOOST_control_CPL_JLC.csv` (single-card coordinates; check that the preview puts them on the panelled card) |
| Not placed (you fit) | J11; J9 is wire pads; H1-H4 are holes |

Bare PCBs $137.04 + assembly about $167.31 = **$304.35**.

## Buy elsewhere (2 sets)

| Part | Qty | Where | About |
|---|---|---|---|
| Samtec ESQ-115-44-G-D (J10 socket) | 2 | Mouser or Samtec | $18.26 |
| Samtec TSW-115-07-G-D (J11 header) | 2 | Mouser or Samtec | $6.36 |
| Bourns MF-R020 PTC (J9 pin-9 fuse) | 2 | LCSC (its own order) | $0.28 |
| Parker 61-05-0909-G579, 9 x 9 in sheet (FET pads) | 1 | Digi-Key / Mouser | **read the price** (est. $85) |
| McMaster 92000A107 M2.5 x 12 pan head (pack of 100) | 1 | McMaster-Carr | $5.65 |
| McMaster 93657A200 nylon spacer 2.0 mm | 8 | McMaster-Carr | $7.36 |
| Boyd 7721-7PPSG shoulder washer | 8 | Digi-Key | **read the price** (est. $2.08) |
| Essentra HTSN-M3-5-3 nylon stud | 8 | Digi-Key | **read the price** (est. $4.80) |
| Essentra HNSM3-20-5.5-1 nylon standoff 20 mm | 8 | Digi-Key | **read the price** (est. $6.40) |
| TR Fastenings TR NWE-34815-M3 washers (pack of 100) | 1 | Newark / Farnell | about $11.67 |
| Wurth 97790803211 M3 x 8 nylon screw | 8 | Newark / Farnell / Digi-Key | about $2.13 |

**You already own:** M1-M10 (HYG180N10), L1 (CSCF3218-6R8MC), the J9 wires and plug, and a buck converter. The buck
must regulate 5.0 V +/-5 % at 200 mA or more from 11-13 V, and survive at least 20 V. The proposed input filter is
awaiting your OK; see COST_SUMMARY.md.

## Total, scenario A

| PCBs | JLC assembly | Parts elsewhere | Hardware | **Total** |
|---|---|---|---|---|
| $261.14 | $392.73 | $24.90 | $125.09 | **$803.86** + shipping + tax |
