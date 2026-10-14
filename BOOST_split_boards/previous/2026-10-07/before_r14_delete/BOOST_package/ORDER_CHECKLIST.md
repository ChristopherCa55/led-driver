# BOOST order checklist, scenario A (updated 2026-10-02)

Two JLCPCB orders (power: 5 PCBs, 2 assembled; card: 5 panels, 2 assembled), plus four small orders elsewhere.
**Total $600.61 with the McMaster pad** (shipping and tax not included). Every price is read, except the two Farnell
UK prices converted from GBP (marked "GBP").

**Since 2026-09-25 ($760.83):**
- the control card is 6 layers with 0.5 oz inner copper ($56.83 instead of $137.04);
- the power board is 6 layers on the stackup JLC061611-7628D ($69.57 instead of $124.10), with your GND and
  gate-drive rework of 2026-10-02 (`BOOST_split_boards/power6_2026-10-01/README.md`);
- the pre-charge diodes D28-D30 (S2MW) are on the power board;
- the savings you approved on 2026-10-01 are in the design files and the BOM:
  - EEH-ZS1H221P on six of the 220 uF positions;
  - the card's 0.5 oz inner copper;
  - TLV9001 op-amps;
  - the onsemi MC7812BD2TR4G as the 12 V regulator U16 (same footprint, gerbers unchanged).
- JLC stock and prices were read again on 2026-10-01.

## Before you order

- [x] **12 V regulator U16:** onsemi MC7812BD2TR4G (C231294), your choice of 2026-10-01. Same TO-263 footprint, so
      the gerbers, CPL, fab drawing and 3D model are unchanged; the BOM line is updated. At the end of a 4S
      discharge the LEDs fade from about 12.7 V open-circuit (`BOOST_split_boards/mc7812_lowbatt_2026-10-01/`).
- [x] **The design files:** schematic rev6 plus D28-D30 and the 2026-10-01 changes, the 6-layer power board (2026-10-02) and
      the 6-layer card, all in `BOOST_package/KiCad/`. The gerbers, BOM and CPL in this folder match them.
- [ ] **Stock**, on JLC's BOM page after upload (2026-10-01 values in brackets).
  - EEH-ZU1E681UP C29664285: need 6 (10)
  - EEH-ZU1H221P C6843593: need 6 (14)
  - EEH-ZS1H221P C385885: need 12 (1263)
  - TLV9001IDBVR C398363: need 18 (48438)
  - MCP4451-103E/ST C145613: need 2 (40)
  - TR3D476K025C0250 C4979367: need 2 (63)
  - CD74HC4066M96 C179842: need 2 (73)
- [ ] **Power board stackup:** on the quote page set "Specify Stackup: Yes" and pick **JLC061611-7628D**. If JLC
      reminds you that its real thickness is 1.583 mm rather than 1.6 mm, accept it (Yes). The loop-inductance,
      current and U16 temperature checks all assume this stackup; the fab drawing says the same.
- [ ] After the Gerber upload, look at JLC's free DFM check for both boards before paying.
- [ ] Optional: read the TG-AD30 price (URL at the bottom). If a 1.5 mm sheet of 150 x 150 mm or less costs about
      $40 or less, buy it instead of the McMaster pad.

## JLC order 1: power board

| Page | Set |
|---|---|
| Gerber | upload `BOOST_power_RC2_gerbers.zip` |
| Base material, layers | FR-4, **6** |
| Dimensions, quantity | 74 x 86 mm, **5**, Single PCB |
| Thickness, material | 1.6 mm, **FR4 TG155** (6 layers default to TG135: change it) |
| Surface finish | **ENIG** (6 layers default to OSP: change it) |
| Outer / inner copper | 1 oz / **1 oz** (inner defaults to 0.5 oz: change it) |
| **Specify stackup** | **Yes: JLC061611-7628D** (1.583 mm; accept the thickness reminder) |
| **Via covering** | **Epoxy Filled & Capped** (free at 6 layers, $0.00) |
| Min via hole / diameter | 0.3 mm / (0.4 / 0.45 mm) |
| Mark on PCB | **Remove Mark** |
| Electrical test | **Flying Probe Fully Test** |
| Everything else | defaults (green, +/-0.2 outline, no gold fingers, castellations, edge plating) |
| PCB Assembly | on: **Standard**, **both sides**, quantity **2** |
| BOM / CPL | `BOOST_power_BOM_JLC.csv` / `BOOST_power_CPL_JLC.csv` |
| Not placed (you fit) | M1-M10, L1, J10 |
| Check | the placement preview: polarity of the cans and diodes (including **D28-D30 on the bottom**), pin 1 of every IC, and U16's tab over the large pad (JLC lists the MC7812 as TO-263-2) |

PCBs $69.57 + assembly about $204.79 = **$274.36**. The standard build time is 8-9 days.

## JLC order 2: control card

Same settings as order 1, except:

| Page | Set |
|---|---|
| Gerber | upload `BOOST_control_RC2_gerbers.zip` |
| Layers | **6** (the stackup in the fab drawing is JLC's standard 6-layer 1.6 mm build for 1 oz outer / 0.5 oz inner, 1.547 mm) |
| Specify stackup | **No** (the card uses JLC's standard build; only the power board names one) |
| Dimensions | 45 x 45 mm |
| Surface finish, inner copper | **ENIG** (6 layers default to OSP: change it); inner copper **0.5 oz** (the default) |
| Delivery format | **Panel by JLCPCB**: column 1, row 1, edge rails **on four sides, 12.5 mm** (70 x 70 mm panel) |
| Quantity | **5** panels (5 cards) |
| PCB Assembly | Standard, both sides, quantity **2** |
| BOM / CPL | `BOOST_control_BOM_JLC.csv` / `BOOST_control_CPL_JLC.csv` (single-card coordinates; check the preview places them on the panelled card) |
| Not placed (you fit) | J11; J9 is wire pads; H1-H4 are holes |

PCBs $56.83 + assembly about $162.46 = **$219.29**.

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
more from about 9.5-13 V (the MC7812 rail sags to 9.7-10.2 V near the end of a 4S discharge), and survive
at least 20 V. No extra input filter is needed (your decision).

**Before first power-up:** the tab-to-case check in BUILD_NOTES (order of work, step 7a). All ten FETs must read open
to the case. It is mandatory with the McMaster pad, which publishes no dielectric strength.

## Total, scenario A

| JLC (both orders) | Mouser | LCSC | McMaster | Digi-Key | Newark/Farnell | **Total** |
|---|---|---|---|---|---|---|
| $493.65 | $24.62 | $0.29 | $55.61 | $12.64 | $13.80 | **$600.61** + shipping + tax |

Pad alternatives:
- Parker 61-06-0909-G579 (0.060 in) instead of the McMaster pad: **$702.45**.
- t-Global TG-AD30 1.5 mm instead: $573.70 plus its price.

Pay both JLC orders together so they ship as one parcel.

TG-AD30 URL: https://www.digikey.com/en/products/result?keywords=TG-AD30
