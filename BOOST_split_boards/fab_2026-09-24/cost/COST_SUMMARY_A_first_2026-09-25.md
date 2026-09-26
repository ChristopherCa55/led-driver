# BOOST: cost summary, scenario A (updated 2026-09-25)

**Scenario A:** 5 bare PCBs of each board, 2 complete sets assembled by JLCPCB, 3 spare bare boards of each. **Shipping and tax are not included anywhere below.** Excluded because you own them: M1-M10, L1, the 12 V -> 5 V buck module and the J9 wires. Also excluded: case, battery cabling and lugs, Arduino Nano and CAN parts, LEDs.

The BOM is schematic **rev6**: R1 = Bourns CSS4J-4026R-1L00F (1 mOhm), U25 = INA241A4. The rev6 copy is checked. It still has to be written into your schematic `BOOST-github/BOOST/BOOST.kicad_sch`, which carries KiCad lock files; see `ORDER_CHECKLIST.md`.

## Grand total

| | Power board | Control card | Total |
|---|---|---|---|
| Bare PCBs (5 each) | $124.10 | $137.04 | $261.14 |
| JLC assembly of 2 each (fees + parts) | $225.42 | $167.31 | $392.73 |
| Parts bought elsewhere (J10, J11, PTC) | | | $24.90 |
| Hardware for 2 sets | | | $125.09 |
| **Grand total, scenario A** | | | **$803.86** |
| Shipping, tax | | | not included |

That is $25.89 less than the 2026-09-24 figure ($829.75): the Pololu D24V5F5 buck modules and the Adafruit 793 wires are removed ($25.85), and JLC's prices moved by a few cents. Four hardware lines ($98.28 of the total) are still estimates or unverified; see "URLs for you to read".

## Bare PCBs (JLCPCB quote page, 2026-09-24)

Both boards: 8 layers, 1.6 mm, FR4 TG155, ENIG, 1 oz outer / 1 oz inner, **Epoxy Filled & Capped vias ($0.00 at 8 layers)**, min via 0.3 mm, Remove Mark, flying-probe full test, 10-11 day build.

| Board | Order | Price for 5 | Breakdown |
|---|---|---|---|
| Power | 5 single boards, 74 x 86 mm | $124.10 | $90.00 base, $17.30 ENIG, $16.80 1 oz inner, $0.00 via covering |
| Card | 5 panels: one 45 x 45 mm card on a 70 x 70 mm carrier (12.5 mm rails, four sides, V-cut) | $137.04 | $99.00 engineering, $17.20 ENIG, $16.74 1 oz inner, $4.10 board, $0.00 via covering |

The card has to go on a carrier panel: JLC's Standard PCBA takes nothing under 70 x 70 mm, and Economic PCBA handles 2/4/6 layers, single-sided boards only. The panel costs $13.62 more than 5 single cards ($123.42).

## Assembly (JLC Standard PCBA, 2 of each)

Set-up $51.12 and stencil $16.42 per order (both boards are double-sided); feeder loading $1.53 per unique part; $0.0016 per solder joint (JLC price page). Parts: JLC quantity-1 prices read 2026-09-25, plus about 20 attrition spares per small-passive line.

| Board | Unique parts | Set-up | Stencil | Loading | Joints | Parts | Attrition | **Assembly** | PCB | **Order** |
|---|---|---|---|---|---|---|---|---|---|---|
| Power | 27 | $51.12 | $16.42 | $41.31 | $0.89 (558) | $110.68 | $5.00 | **$225.42** | $124.10 | **$349.52** |
| Card | 41 | $51.12 | $16.42 | $62.73 | $1.51 (944) | $29.64 | $5.89 | **$167.31** | $137.04 | **$304.35** |

## Stock on 2026-09-25 (JLC parts library, 00:15 PDT)

Every one of the 61 JLC lines is in stock for 2 sets. The tight ones (JLC buys no attrition spares on these):

| Part | LCSC | Stock | Needed for 2 sets | Note |
|---|---|---|---|---|
| EEH-ZU1H221P | C6843593 | 19 | 18 | **1 spare.** If it drops below 18 before you order, stop: tell me before placing it |
| LM2940S-12/NOPB | C2877347 | 2 | 2 | **exactly 2.** Fallback: LM2940CS-12/NOPB C2865267 (stock 7): same TO-263 part, rated 0 to 125 C and 45 V / 1 ms transients (TI SNVS769J) |
| INA241A4IDR | C22427873 | 116 | 2 | rev6 U25: in stock |
| CSS4J-4026R-1L00F | C2076400 | 385 | 2 | rev6 R1: in stock |
| EEH-ZU1E681UP | C29664285 | 10 | 6 |  |
| MCP6241T-E/OT | C49889 | 38 | 18 | shared: 6 per card, 3 per power board |
| MCP4451-103E/ST | C145613 | 52 | 2 |  |
| CD74HC4066M96 | C179842 | 73 | 2 |  |

Re-check on the day you order: JLC's BOM page shows any shortage when you upload the BOM. Or ask me to re-run the check (`bom/jlc_stock_2026-09-25.json` is today's).

## Itemised JLC parts (everything JLC buys; excludes M1-M10 and L1)

### Power board

| Refs | LCSC | MPN | Per board | Unit | Qty for 2 (+attrition) | $ |
|---|---|---|---|---|---|---|
| C1 C4 C73 | C381466 | FS32X475K101EGG | 3 | $0.2420 | 6 (+0) | $1.45 |
| C3 C72 C76 | C28233 | CL21B104KCFNNNE | 3 | $0.0356 | 6 (+20) | $0.93 |
| C6 C21 C25 C31 C62 C89 | C28323 | CL21B105KBFNNNE | 6 | $0.0398 | 12 (+20) | $1.27 |
| C7 C55 | C21397 | GRM32ER71E226KE15L | 2 | $0.4596 | 4 (+0) | $1.84 |
| C16 C18 C60 | C50254 | CL31B225KBHNNNE | 3 | $0.0856 | 6 (+20) | $2.23 |
| C20 C33 C34 C35 C48 C50 C51 C61 C82 C83 C84 C90 | C14663 | CC0603KRX7R9BB104 | 12 | $0.0122 | 24 (+20) | $0.54 |
| C30 | C4979367 | TR3D476K025C0250 | 1 | $1.1563 | 2 (+0) | $2.31 |
| C39 C56 C79 C80 C81 | C138687 | CL32B106KBJNNNE | 5 | $0.3249 | 10 (+0) | $3.25 |
| C40 C69 C85 | C29664285 | EEH-ZU1E681UP | 3 | $2.5383 | 6 (+0) | $15.23 |
| C41 C44 C45 | C1588 | CL10B102KB8NNNC | 3 | $0.0089 | 6 (+20) | $0.23 |
| C70 C71 C74 C75 C77 C78 C86 C87 C88 | C6843593 | EEH-ZU1H221P | 9 | $2.8322 | 18 (+0) | $50.98 |
| D2 D8 D11 D13 D14 D22 | C8598 | B5819W SL | 6 | $0.0280 | 12 (+20) | $0.90 |
| D9 D10 D21 | C21565 | BAV21W | 3 | $0.0191 | 6 (+20) | $0.50 |
| D19 | C42394451 | 5.0SMDJ54A | 1 | $0.3947 | 2 (+0) | $0.79 |
| R1 | C2076400 | CSS4J-4026R-1L00F | 1 | $1.7068 | 2 (+0) | $3.41 |
| R7 R52 R53 | C413486 | WSL2512R0500FEA | 3 | $0.2345 | 6 (+0) | $1.41 |
| R13 R23 R47 | C22962 | 0603WAF2200T5E | 3 | $0.0034 | 6 (+20) | $0.09 |
| R14 | C17514 | 0805W8F1004T5E | 1 | $0.0043 | 2 (+20) | $0.09 |
| R15 | C17415 | 0805W8F100JT5E | 1 | $0.0040 | 2 (+20) | $0.09 |
| R21 R48 R60 R72 | C17724 | 0805W8F510KT5E | 4 | $0.0041 | 8 (+20) | $0.11 |
| R22 R50 R56 | C22775 | 0603WAF1000T5E | 3 | $0.0031 | 6 (+20) | $0.08 |
| R49 R61 R62 R73 R74 R75 R76 R104 | C25804 | 0603WAF1002T5E | 8 | $0.0018 | 16 (+20) | $0.06 |
| R59 R70 | C17724 | 0805W8F510KT5E | 2 | $0.0041 | 4 (+0) | $0.02 |
| U1 U17 | C43116 | L78L05ACUTR | 2 | $0.1019 | 4 (+0) | $0.41 |
| U6 U11 U12 | C49889 | MCP6241T-E/OT | 3 | $0.6935 | 6 (+0) | $4.16 |
| U8 U10 U15 U19 | C601651 | UCC21520DWR | 4 | $0.8883 | 8 (+0) | $7.11 |
| U16 | C2877347 | LM2940S-12/NOPB | 1 | $4.5747 | 2 (+0) | $9.15 |
| U25 | C22427873 | INA241A4IDR | 1 | $3.5240 | 2 (+0) | $7.05 |
| **Total** | | | | | | **$115.68** |

### Control card

| Refs | LCSC | MPN | Per board | Unit | Qty for 2 (+attrition) | $ |
|---|---|---|---|---|---|---|
| C8 C9 C17 C19 | C1664 | CL10C331JB8NNNC | 4 | $0.0179 | 8 (+20) | $0.50 |
| C10 C11 C13 | C85980 | GRM1885C1H472JA01D | 3 | $0.0278 | 6 (+20) | $0.72 |
| C12 C22 C23 C24 C26 C28 C29 C32 C36 C37 C38 C42 C43 C46 C52 C53 C54 C58 C59 C63 C65 C66 C68 C92 C94 C95 C96 C97 C98 C99 C104 | C14663 | CC0603KRX7R9BB104 | 31 | $0.0122 | 62 (+20) | $1.00 |
| C14 | C27675 | CL10C221JB8NNNC | 1 | $0.0095 | 2 (+20) | $0.21 |
| C15 | C14858 | CL10C101JB8NNNC | 1 | $0.0086 | 2 (+20) | $0.19 |
| C47 C93 C103 | C96446 | CL10A106MA8NRNC | 3 | $0.0541 | 6 (+20) | $1.41 |
| C49 C64 C67 | C97946 | GRM31C5C1H104JA01L | 3 | $0.1847 | 6 (+0) | $1.11 |
| C57 C91 | C28323 | CL21B105KBFNNNE | 2 | $0.0398 | 4 (+20) | $0.96 |
| C100 C101 C102 | C1588 | CL10B102KB8NNNC | 3 | $0.0089 | 6 (+20) | $0.23 |
| D1 D3 D4 D5 D6 D7 D15 D20 D24 D27 | C81598 | 1N4148W | 10 | $0.0123 | 20 (+20) | $0.49 |
| D23 D25 D26 | C22629 | BAT54WS L9 | 3 | $0.0238 | 6 (+20) | $0.62 |
| Q1 | C53444 | MMBT3906LT1G | 1 | $0.0189 | 2 (+20) | $0.42 |
| R2 R6 R31 R33 R39 R41 R67 R77 R83 R85 R99 R100 R101 R102 R103 | C25804 | 0603WAF1002T5E | 15 | $0.0018 | 30 (+20) | $0.09 |
| R3 R32 R40 | C23219 | 0603WAF6203T5E | 3 | $0.0020 | 6 (+20) | $0.05 |
| R4 R54 R55 R58 R71 | C21190 | 0603WAF1001T5E | 5 | $0.0026 | 10 (+20) | $0.08 |
| R8 R34 R42 R51 R63 R78 R80 | C22975 | 0603WAF2001T5E | 7 | $0.0024 | 14 (+20) | $0.08 |
| R9 R35 R43 | C17506 | 0805W8F1802T5E | 3 | $0.0043 | 6 (+20) | $0.11 |
| R11 R17 | C23192 | 0603WAF5103T5E | 2 | $0.0024 | 4 (+20) | $0.06 |
| R16 R19 | C23186 | 0603WAF5101T5E | 2 | $0.0015 | 4 (+20) | $0.04 |
| R18 R20 | C25811 | 0603WAF2003T5E | 2 | $0.0023 | 4 (+20) | $0.06 |
| R25 R87 R94 | C17864 | 0805W8F9103T5E | 3 | $0.0034 | 6 (+20) | $0.09 |
| R26 R64 R79 R81 | C22962 | 0603WAF2200T5E | 4 | $0.0034 | 8 (+20) | $0.10 |
| R27 R37 R45 | C23162 | 0603WAF4701T5E | 3 | $0.0028 | 6 (+20) | $0.07 |
| R28 R36 R38 R44 R46 R88 R91 R95 R96 R105 | C25803 | 0603WAF1003T5E | 10 | $0.0031 | 20 (+20) | $0.12 |
| R29 R30 R57 | C17560 | 0805W8F2202T5E | 3 | $0.0048 | 6 (+20) | $0.12 |
| R65 | C31850 | 0603WAF2202T5E | 1 | $0.0041 | 2 (+20) | $0.09 |
| R66 R89 R92 R97 | C22978 | 0603WAF3301T5E | 4 | $0.0026 | 8 (+20) | $0.07 |
| R68 | C23221 | 0603WAF6202T5E | 1 | $0.0028 | 2 (+20) | $0.06 |
| R69 | C4184 | 0603WAF2002T5E | 1 | $0.0023 | 2 (+20) | $0.05 |
| R82 | C23206 | 0603WAF5602T5E | 1 | $0.0027 | 2 (+20) | $0.06 |
| R84 | C25808 | 0603WAF1203T5E | 1 | $0.0015 | 2 (+20) | $0.03 |
| R86 | C17514 | 0805W8F1004T5E | 1 | $0.0043 | 2 (+20) | $0.09 |
| R90 R93 R98 | C7250 | 0603WAF1005T5E | 3 | $0.0037 | 6 (+20) | $0.10 |
| U2 U4 U5 U14 U21 | C117501 | MCP6561T-E/OT | 5 | $0.7422 | 10 (+0) | $7.42 |
| U3 U7 U13 U22 U23 U24 | C49889 | MCP6241T-E/OT | 6 | $0.6935 | 12 (+0) | $8.32 |
| U18 | C11349 | CD4017BM96 | 1 | $0.7422 | 2 (+0) | $1.48 |
| U26 | C145613 | MCP4451-103E/ST | 1 | $2.9166 | 2 (+0) | $5.83 |
| U28 | C9386 | 74HC4051D,653 | 1 | $0.2194 | 2 (+0) | $0.44 |
| U101 U102 U103 | C5586 | 74HC00D,653 | 3 | $0.1548 | 6 (+0) | $0.93 |
| U104 U105 | C5605 | 74HC14D,653 | 2 | $0.1022 | 4 (+0) | $0.41 |
| U106 | C179842 | CD74HC4066M96 | 1 | $0.6090 | 2 (+0) | $1.22 |
| **Total** | | | | | | **$35.53** |

## Parts bought elsewhere

| Item | Qty | Unit | $ | Source | Checked |
|---|---|---|---|---|---|
| Samtec ESQ-115-44-G-D, J10 socket (power board) | 2 | $9.13 | $18.26 | Mouser, as listed on samtec.com | read on samtec.com |
| Samtec TSW-115-07-G-D, J11 header (card) | 2 | $3.18 | $6.36 | Mouser, as listed on samtec.com | read on samtec.com |
| Bourns MF-R020 PTC, 0.20 A hold (inline on the J9 pin-9 wire) | 2 | $0.14 | $0.28 | LCSC (its own order; JLC does not ship loose parts) | read on lcsc.com; ratings read in the Bourns MF-R datasheet |
| **Total** | | | **$24.90** | | |

## Hardware for 2 sets

| Part | Role | Qty | $ | Source | Checked | Page |
|---|---|---|---|---|---|---|
| Parker Chomerics 61-05-0909-G579, THERM-A-GAP 579, 0.050 in, 9 x 9 in sheet (smallest listed) | FET thermal pads, cut 10 x 16 mm (10 per board) | 1 sheet | $85.00 | price not readable: Parker quotes via distributors, and Digi-Key/Mouser/Newark/Arrow/RS block this browser | ESTIMATE: you read it (URL list) | [link](https://ph.parker.com/us/en/product/therm-a-gap-579-thermally-conductive-gap-filler-pads/61-05-0909-g579) |
| McMaster-Carr 92000A107, M2.5 x 12 pan head Phillips, 18-8 stainless, pack of 100 | FET tab screws (4 per set) | 1 pack | $5.65 | mcmaster.com | read on mcmaster.com | [link](https://www.mcmaster.com/92000A107/) |
| McMaster-Carr 93657A200, nylon 6/6 spacer, M2.5, 2.0 mm long, 4.5 mm OD | FET tab-screw gap spacer (4 per set) | 8 | $7.36 | mcmaster.com ($0.92 each under 10) | read on mcmaster.com | [link](https://www.mcmaster.com/93657A200/) |
| Boyd (Aavid) 7721-7PPSG shoulder washer, glass-filled PPS | insulates each tab screw in the FET tab hole (4 per set) | 8 | $2.08 | search-engine summary of Digi-Key ($0.26) | UNVERIFIED: you read it (URL list) | [link](https://www.digikey.com/en/products/result?keywords=7721-7PPSG) |
| Essentra HTSN-M3-5-3, nylon hex stud M3 male-male, 5 mm body | floor-to-power-board standoff (4 per set) | 8 | $4.80 | estimate (Digi-Key shows $0.48 at 500) | ESTIMATE: you read it (URL list) | [link](https://www.digikey.com/en/products/result?keywords=HTSN-M3-5-3) |
| Essentra HNSM3-20-5.5-1, nylon hex standoff M3 female-female, 20 mm | power-board-to-card standoff (4 per set) | 8 | $6.40 | estimate (no public price found) | ESTIMATE: you read it (URL list) | [link](https://www.digikey.com/en/products/detail/essentra-components/HNSM3-20-5-5-1/3813076) |
| TR Fastenings TR NWE-34815-M3, nylon 6/6 washer 3.2 x 7.0 x 0.5 mm, pack of 100 | standoff shims (16 per set) | 1 pack | $11.67 | Farnell UK 8.71 GBP, converted at 1.34 USD/GBP | price read via search; conversion assumed | [link](https://www.newark.com/tr-fastenings/tr-nwe-34815-m3/washer-nylon-6-6-3-2mm-pk100/dp/43Y4267) |
| Wurth Elektronik 97790803211, WA-SCRW M3 x 8 nylon 66 pan head | card screws (4 per set) | 8 | $2.13 | Farnell UK 0.199 GBP each, converted at 1.34 USD/GBP | price read via search; conversion assumed | [link](https://www.we-online.com/en/components/products/WA-SCRW) |
| **Total** | | | **$125.09** | | | |

## Your buck converter: what it has to meet

It is fed from J9 pin 9: the power board's 12 V LM2940 rail, through 88 mm of 0.3 mm track on the card (about 0.1 ohm) and the MF-R020 PTC (1.50-2.84 ohm new, up to 4.40 ohm an hour after a trip; Bourns MF-R datasheet).

1. **Input:** regulates from **11 to 13 V**. That is the 12 V rail less up to about 0.5 V across the track and PTC at 0.1 A. It should also **survive at least 20 V**: if U16 failed short, the battery rail (14-17 V) would reach it.
2. **Output: 5.0 V, within +/-5 % (4.75-5.25 V), at least 200 mA continuous**, stable from no load. The Arduino plus CAN load is about 50 mA average and 120 mA peak (BUILD_NOTES).
3. **Input current: at most about 0.1 A** at 200 mA out (85 % efficiency assumed). The PTC holds 0.20 A and trips at 0.40 A (2.2 s maximum at 1.0 A). A module with soft-start keeps its switch-on inrush from tripping it; the LM2940's budget (about 120 mA extra, accepted 2026-09-23) also covers this.
4. **Input filter: BUILD_NOTES does not contain one.** The idea ("filter at the buck end so the harness carries near-DC") was never written into BUILD_NOTES. **My proposal, for your OK:** a bulk capacitor across the buck's input terminals, **at least 22 uF, rated 25 V or more, aluminium electrolytic or polymer**, in addition to the module's own ceramic input capacitors. It supplies the switching current locally, so the 12 V wire carries near-DC. The PTC's 1.5-4.4 ohm in series already damps the wire's inductance against the module's ceramics. If you agree, I will add it to BUILD_NOTES.

## Thermal pad: cheaper options checked, and the recommendation

Full numbers in `cost/pad_options.txt` (from `tools/pad_options.py`). The board sits at 5.50 mm, so every pad is squeezed to **0.93 mm**. What changes between pads is how hard it presses and how much heat it passes.

| Pad | Published data | At 0.93 mm | M1 Tj at 25 C water | Price | Verdict |
|---|---|---|---|---|---|
| **Parker THERM-A-GAP G579, 1.27 mm** (current) | 3.0 W/m-K; 30 Shore 00; deflection curve 22/33/55/68 % at 5/10/25/50 psi; 4.5 C-cm2/W | 27 %, about 7 psi, 8 N per FET; worst case 1-48 % (always touching) | **about 78 C** (20.5 K across the pad at 6 W) | 9 x 9 in sheet only; price to read (URL list) | **Keep it.** No stack change |
| t-Global TG-A3500F, 1.0 mm | 3.0 W/m-K; 35 Shore 00; curve 5/14/27 % at 10/30/50 psi; 1.35/1.02/0.90 C-in2/W | 7 %, 14 psi, 15 N per FET; worst case -26 % (**loses contact**) to 34 % | about 89 C (31.7 K) | quote only (t-Global sells through distributors) | No: about 7x stiffer; a 1.5 mm pad would need over 54 N per FET |
| Wurth WE-TGF, 3 W/m-K | one point: >= 20 % at 35.5 N/cm2 (51 psi); 4.9 K-cm2/W (2 mm) | force unknown (no curve); 20 % alone needs 55 N per FET | not computable | not readable | No: too stiff, and no curve |
| McMaster-Carr 1272N32, 1.52 mm | 3 W/m-K, 40 Shore 00; **no compression data**, no dielectric strength, maker not named | 39 %, force unknown | not computable | **$26.91, 4 x 4 in** | No: fails your "publishes a compression curve" condition |

**Result: the only cheap option publishes no compression data, and the options that do are far stiffer than G579.** At our fixed 0.93 mm, a stiffer pad either loses contact at the tolerance extremes or pushes the board up with several times the force. Keeping G579 means the standoff and washer stack stays as it is (5.0 mm stud + 0.5 mm washer, 0.93 mm compressed, 27 %). Its junction-temperature figure is unchanged at about 78 C: 3.10 C-cm2/W of bulk at 0.93 mm, plus at most 2.23 of contact, over the 1.56 cm2 tab. Parker lists the 9 x 9 in sheet as the smallest (18 x 18 in is the other). One sheet cuts about 300 pads, 30 boards' worth. Its price is the first line of the URL list.

## URLs for you to read (the four unverified scenario-A lines)

Digi-Key, Mouser, Newark, Arrow and RS all block this browser, and Essentra and Parker quote only on request. Open these and paste the prices back:

1. Thermal pad sheet, **Parker 61-05-0909-G579** (FET pads; 1 sheet): https://www.digikey.com/en/products/result?keywords=61-05-0909-G579
2. **Essentra HTSN-M3-5-3** (floor-to-board nylon stud; 8): https://www.digikey.com/en/products/result?keywords=HTSN-M3-5-3
3. **Essentra HNSM3-20-5.5-1** (board-to-card nylon standoff; 8): https://www.digikey.com/en/products/detail/essentra-components/HNSM3-20-5-5-1/3813076
4. **Boyd 7721-7PPSG** (shoulder washer in each FET tab hole; 8): https://www.digikey.com/en/products/result?keywords=7721-7PPSG

## Still flagged

1. The four lines above: estimates until you read them.
2. Samtec ESQ/TSW: Mouser's prices as listed on Samtec's pages, not read on Mouser.
3. TR washers and Wurth screws: Farnell UK prices in GBP, converted at an assumed 1.34 USD/GBP.
4. JLC: quantity-1 prices. Price breaks or minimum buys may change a line by cents. Attrition follows the "about 20 per small-passive line" read on 2026-09-24. Fees are from JLC's price page, not from a quote with the files uploaded; the upload can add charges.
5. The Wurth WA-SCRW page link was not opened.

Scenario B was dropped on 2026-09-25. Its files are kept, not developed further: `cost/BOOST_power_BOM_JLC_limitedDNP.csv`, `cost/BOOST_power_CPL_JLC_limitedDNP.csv`, `cost/COST_SUMMARY_AB_2026-09-24.md`.

Generated by `tools/cost_summary.py`; every number is also in `cost/cost_summary.json`.
