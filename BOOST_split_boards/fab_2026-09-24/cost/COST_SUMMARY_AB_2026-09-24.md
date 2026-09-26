# BOOST: cost summary (2026-09-24)

Both boards are still **NOT_FOR_FAB**: pick a scenario first. The numbers come from JLCPCB's quote page and parts library on 2026-09-24, and from distributor pages where noted. **Shipping and tax: not included** anywhere below. Items marked **ESTIMATE** or **UNVERIFIED** are listed at the end.

Excluded, because you own them: M1-M10 (HYG180N10) and L1 (CSCF3218-6R8MC). Also excluded: the case, battery cabling and lugs, the Arduino Nano and its CAN parts, and the LEDs and their wiring.

The BOM is schematic **rev6** (R1 = Bourns CSS4J-4026R-1L00F 1 mOhm, U25 = INA241A4). Rev6 is prepared but not yet written into your schematic; see "If you stay on rev5" below.

## The scenarios at a glance

| | **A**: 5 bare PCBs of each board, 2 complete sets | **B**: A plus 3 more boards of each assembled without the stock-limited parts | B alternative: one power order |
|---|---|---|---|
| PCB orders | power x1, card x1 | power x2, card x1 | power x1, card x1 |
| Assembled by JLC | 2 power + 2 card, complete | 2 power complete + 3 power without the limited lines; 5 cards complete | 5 power without the limited lines; 5 cards complete |
| Bare spare PCBs | 3 power, 3 card | 5 power, 0 card | 0 power, 0 card |
| You hand-fit (beyond J10/J11) | nothing | on 3 power boards: 9 x 220 uF, 3 x 680 uF, 3 x MCP6241 each | the same on all 5 power boards |
| Bare PCBs | $261.14 | $385.24 | $261.14 |
| JLC assembly (fees + parts) | $392.77 | $610.78 | $426.68 |
| Parts bought elsewhere | $24.62 | $185.99 | $264.35 |
| Hardware | $151.22 | $213.60 | $213.60 |
| **Grand total** | **$829.75** | **$1,395.61** | **$1,165.77** |
| Shipping, tax | not included | not included | not included |

Why B needs a second power order: JLC applies one BOM to every board in an order, so one order cannot give 2 complete power boards and 3 without the limited lines. The card has no limited line once the shared MCP6241 stock goes to the cards (below), so one card order covers all 5. "B alternative" saves the second power PCB order and set-up, but then **none** of the five power boards comes complete: you hand-fit the limited parts on all five.

For scale, DHL was quoted at $29.45 for one bare-PCB order (0.17-0.22 kg). Assembled orders weigh more and ship separately per order. **Not included.**

## Stock-limited lines at 5 sets (JLC stock on 2026-09-24; JLC buys no attrition spares on these)

| Line | Per power board | Per card | Need for 5 sets | JLC stock | Covers | Alternate at JLC | Does it remove the limit? |
|---|---|---|---|---|---|---|---|
| EEH-ZU1H221P 220 uF 50 V (C70 C71 C74 C75 C77 C78 C86 C87 C88) | 9 | 0 | 45 | 19 | 2 power boards | EEH-ZU1H221V (C7182696), stock 12, 17.1 mm tall | **No**: 31 together, and the V part's land pattern is not checked against the footprint |
| EEH-ZU1E681UP 680 uF 25 V (C40 C69 C85) | 3 | 0 | 15 | 10 | 3 power boards | EEH-ZU1E681UV (C23810697), stock 10 | **Possibly**: 20 together is enough if one ref per board used the V part, but its datasheet and land pattern are **not checked**. I have not used it |
| MCP6241T-E/OT (power U6 U11 U12; card U3 U7 U13 U22 U23 U24) | 3 | 6 | 45 | 38 | 4 sets | MCP6241RT-E/OT (29), MCP6241UT-E/OT (6) | **No**: Microchip DS21882D draws different SOT-23-5 pinouts for them (the R version has VDD and VSS swapped: pin 5 is VSS). The SOIC-8 versions need a different footprint |
| LM2940S-12/NOPB (U16) | 1 | 0 | 5 | 2 | 2 power boards | **LM2940CS-12/NOPB (C2865267), stock 7** | **Yes**, used for the scenario-B boards. TI SNVS769J: same TO-263 part in the C grade, rated 0 to 125 C (the S grade is -40 to 125 C) and 45 V / 1 ms input transients |

Allocation used for B: the cards get 30 MCP6241 and the 2 complete power boards get 6, 36 of the 38. The 3 extra power boards have U6/U11/U12 left off for you to fit. Scenario A uses exactly the 2 LM2940S-12 in stock. If one goes before you order, use the CS grade on A as well: it is the same file change as the B BOM.

## Bare PCBs (JLCPCB quote page, 2026-09-24)

Both boards: 8 layers, 1.6 mm, FR4 TG155, ENIG, 1 oz outer / 1 oz inner, **epoxy filled and capped vias ($0.00 at 8 layers)**, 0.3 mm minimum via, Remove Mark, full flying-probe test, 10-11 day build.

| Board | What you order | Price for 5 | Breakdown |
|---|---|---|---|
| Power | 74 x 86 mm single boards, 5 pcs | $124.10 | $90.00 base, $17.30 ENIG, $16.80 1 oz inner, $0.00 via fill |
| Card | 5 panels, each one card on a 70 x 70 mm carrier (12.5 mm rails on four sides, V-cut) | $137.04 | $99.00 engineering, $17.20 ENIG, $16.74 1 oz inner, $4.10 board, $0.00 via fill |

**Panelising the card costs $13.62** ($137.04 as a carrier panel against $123.42 as 5 single 45 x 45 mm boards). It is needed because JLC's Standard PCBA takes nothing under 70 x 70 mm. Economic PCBA would take the small board but handles 2/4/6 layers, single-sided only. The carrier is one card per panel with V-cut 12.5 mm rails, so "5 PCBs" is still 5 cards. A 2-up panel (90 x 70 mm) would give 10 cards per order.

## Assembly per order (JLC Standard PCBA)

Fees from JLC's PCBA price page: set-up $51.12 and stencil $16.42 per order (both boards are double-sided); feeder loading $1.53 per unique part (Basic or Extended alike in Standard PCBA); $0.0016 per solder joint. Parts are JLC's quantity-1 prices, plus attrition of about 20 spares per small-passive line (lines under $0.10).

| Order | Boards assembled | Unique parts | Set-up | Stencil | Loading | Joints | Parts | Attrition | **Assembly total** | PCB | **Order total** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A: power, 5 PCBs, 2 assembled complete | 2 | 27 | $51.12 | $16.42 | $41.31 | $0.89 (558) | $110.71 | $5.00 | **$225.45** | $124.10 | **$349.55** |
| A: card, 5 PCBs, 2 assembled complete | 2 | 41 | $51.12 | $16.42 | $62.73 | $1.51 (944) | $29.65 | $5.89 | **$167.32** | $137.04 | **$304.36** |
| B: power order 2, 5 PCBs, 3 assembled without the limited lines | 3 | 24 | $51.12 | $16.42 | $36.72 | $1.15 (720) | $60.86 | $5.00 | **$171.27** | $124.10 | **$295.37** |
| B: card, 5 PCBs, 5 assembled complete | 5 | 41 | $51.12 | $16.42 | $62.73 | $3.78 (2360) | $74.12 | $5.89 | **$214.06** | $137.04 | **$351.10** |
| B alternative: power, 5 PCBs, all 5 assembled without the limited lines | 5 | 24 | $51.12 | $16.42 | $36.72 | $1.92 (1200) | $101.44 | $5.00 | **$212.62** | $124.10 | **$336.72** |

The scenario-B power order uses `cost/BOOST_power_BOM_JLC_limitedDNP.csv` and `cost/BOOST_power_CPL_JLC_limitedDNP.csv`. They are the approved files with the 220 uF, 680 uF and MCP6241 lines left off and U16 set to LM2940CS-12/NOPB (C2865267).

## Itemised JLC parts (everything JLC buys; excludes M1-M10 and L1)

Unit prices are JLC's at quantity 1. "A" is 2 boards; "B" is the extra boards in B, each with its own order.

### Power board

| Refs | LCSC | MPN | Per board | Unit | A: qty (+attrition) | A: $ | B order: qty (+attrition) | B order: $ |
|---|---|---|---|---|---|---|---|---|
| C1 C4 C73 | C381466 | FS32X475K101EGG | 3 | $0.2421 | 6 (+0) | $1.45 | 9 (+0) | $2.18 |
| C3 C72 C76 | C28233 | CL21B104KCFNNNE | 3 | $0.0356 | 6 (+20) | $0.93 | 9 (+20) | $1.03 |
| C6 C21 C25 C31 C62 C89 | C28323 | CL21B105KBFNNNE | 6 | $0.0398 | 12 (+20) | $1.27 | 18 (+20) | $1.51 |
| C7 C55 | C21397 | GRM32ER71E226KE15L | 2 | $0.4597 | 4 (+0) | $1.84 | 6 (+0) | $2.76 |
| C16 C18 C60 | C50254 | CL31B225KBHNNNE | 3 | $0.0857 | 6 (+20) | $2.23 | 9 (+20) | $2.49 |
| C20 C33 C34 C35 C48 C50 C51 C61 C82 C83 C84 C90 | C14663 | CC0603KRX7R9BB104 | 12 | $0.0122 | 24 (+20) | $0.54 | 36 (+20) | $0.68 |
| C30 | C4979367 | TR3D476K025C0250 | 1 | $1.1566 | 2 (+0) | $2.31 | 3 (+0) | $3.47 |
| C39 C56 C79 C80 C81 | C138687 | CL32B106KBJNNNE | 5 | $0.3250 | 10 (+0) | $3.25 | 15 (+0) | $4.88 |
| C40 C69 C85 | C29664285 | EEH-ZU1E681UP | 3 | $2.5389 | 6 (+0) | $15.23 | **you fit** | - |
| C41 C44 C45 | C1588 | CL10B102KB8NNNC | 3 | $0.0089 | 6 (+20) | $0.23 | 9 (+20) | $0.26 |
| C70 C71 C74 C75 C77 C78 C86 C87 C88 | C6843593 | EEH-ZU1H221P | 9 | $2.8329 | 18 (+0) | $50.99 | **you fit** | - |
| D2 D8 D11 D13 D14 D22 | C8598 | B5819W SL | 6 | $0.0280 | 12 (+20) | $0.90 | 18 (+20) | $1.06 |
| D9 D10 D21 | C21565 | BAV21W | 3 | $0.0191 | 6 (+20) | $0.50 | 9 (+20) | $0.55 |
| D19 | C42394451 | 5.0SMDJ54A | 1 | $0.3948 | 2 (+0) | $0.79 | 3 (+0) | $1.18 |
| R1 | C2076400 | CSS4J-4026R-1L00F | 1 | $1.7072 | 2 (+0) | $3.41 | 3 (+0) | $5.12 |
| R7 R52 R53 | C413486 | WSL2512R0500FEA | 3 | $0.2346 | 6 (+0) | $1.41 | 9 (+0) | $2.11 |
| R13 R23 R47 | C22962 | 0603WAF2200T5E | 3 | $0.0034 | 6 (+20) | $0.09 | 9 (+20) | $0.10 |
| R14 | C17514 | 0805W8F1004T5E | 1 | $0.0043 | 2 (+20) | $0.09 | 3 (+20) | $0.10 |
| R15 | C17415 | 0805W8F100JT5E | 1 | $0.0040 | 2 (+20) | $0.09 | 3 (+20) | $0.09 |
| R21 R48 R60 R72 | C17724 | 0805W8F510KT5E | 4 | $0.0041 | 8 (+20) | $0.11 | 12 (+20) | $0.13 |
| R22 R50 R56 | C22775 | 0603WAF1000T5E | 3 | $0.0031 | 6 (+20) | $0.08 | 9 (+20) | $0.09 |
| R49 R61 R62 R73 R74 R75 R76 R104 | C25804 | 0603WAF1002T5E | 8 | $0.0018 | 16 (+20) | $0.06 | 24 (+20) | $0.08 |
| R59 R70 | C17724 | 0805W8F510KT5E | 2 | $0.0041 | 4 (+0) | $0.02 | 6 (+0) | $0.02 |
| U1 U17 | C43116 | L78L05ACUTR | 2 | $0.1019 | 4 (+0) | $0.41 | 6 (+0) | $0.61 |
| U6 U11 U12 | C49889 | MCP6241T-E/OT | 3 | $0.6936 | 6 (+0) | $4.16 | **you fit** | - |
| U8 U10 U15 U19 | C601651 | UCC21520DWR | 4 | $0.8886 | 8 (+0) | $7.11 | 12 (+0) | $10.66 |
| U16 | C2877347 | LM2940S-12/NOPB | 1 | $4.5758 | 2 (+0) | $9.15 | 3 (+0) as C2865267 LM2940CS-12/NOPB | $14.11 |
| U25 | C22427873 | INA241A4IDR | 1 | $3.5240 | 2 (+0) | $7.05 | 3 (+0) | $10.57 |
| **Total** | | | | | | **$115.71** | | **$65.86** |

### Control card

| Refs | LCSC | MPN | Per board | Unit | A: qty (+attrition) | A: $ | B order: qty (+attrition) | B order: $ |
|---|---|---|---|---|---|---|---|---|
| C8 C9 C17 C19 | C1664 | CL10C331JB8NNNC | 4 | $0.0179 | 8 (+20) | $0.50 | 20 (+20) | $0.72 |
| C10 C11 C13 | C85980 | GRM1885C1H472JA01D | 3 | $0.0278 | 6 (+20) | $0.72 | 15 (+20) | $0.97 |
| C12 C22 C23 C24 C26 C28 C29 C32 C36 C37 C38 C42 C43 C46 C52 C53 C54 C58 C59 C63 C65 C66 C68 C92 C94 C95 C96 C97 C98 C99 C104 | C14663 | CC0603KRX7R9BB104 | 31 | $0.0122 | 62 (+20) | $1.00 | 155 (+20) | $2.14 |
| C14 | C27675 | CL10C221JB8NNNC | 1 | $0.0095 | 2 (+20) | $0.21 | 5 (+20) | $0.24 |
| C15 | C14858 | CL10C101JB8NNNC | 1 | $0.0086 | 2 (+20) | $0.19 | 5 (+20) | $0.21 |
| C47 C93 C103 | C96446 | CL10A106MA8NRNC | 3 | $0.0541 | 6 (+20) | $1.41 | 15 (+20) | $1.89 |
| C49 C64 C67 | C97946 | GRM31C5C1H104JA01L | 3 | $0.1847 | 6 (+0) | $1.11 | 15 (+0) | $2.77 |
| C57 C91 | C28323 | CL21B105KBFNNNE | 2 | $0.0398 | 4 (+20) | $0.96 | 10 (+20) | $1.19 |
| C100 C101 C102 | C1588 | CL10B102KB8NNNC | 3 | $0.0089 | 6 (+20) | $0.23 | 15 (+20) | $0.31 |
| D1 D3 D4 D5 D6 D7 D15 D20 D24 D27 | C81598 | 1N4148W | 10 | $0.0123 | 20 (+20) | $0.49 | 50 (+20) | $0.86 |
| D23 D25 D26 | C22629 | BAT54WS L9 | 3 | $0.0238 | 6 (+20) | $0.62 | 15 (+20) | $0.83 |
| Q1 | C53444 | MMBT3906LT1G | 1 | $0.0189 | 2 (+20) | $0.42 | 5 (+20) | $0.47 |
| R2 R6 R31 R33 R39 R41 R67 R77 R83 R85 R99 R100 R101 R102 R103 | C25804 | 0603WAF1002T5E | 15 | $0.0018 | 30 (+20) | $0.09 | 75 (+20) | $0.17 |
| R3 R32 R40 | C23219 | 0603WAF6203T5E | 3 | $0.0020 | 6 (+20) | $0.05 | 15 (+20) | $0.07 |
| R4 R54 R55 R58 R71 | C21190 | 0603WAF1001T5E | 5 | $0.0026 | 10 (+20) | $0.08 | 25 (+20) | $0.12 |
| R8 R34 R42 R51 R63 R78 R80 | C22975 | 0603WAF2001T5E | 7 | $0.0024 | 14 (+20) | $0.08 | 35 (+20) | $0.13 |
| R9 R35 R43 | C17506 | 0805W8F1802T5E | 3 | $0.0043 | 6 (+20) | $0.11 | 15 (+20) | $0.15 |
| R11 R17 | C23192 | 0603WAF5103T5E | 2 | $0.0024 | 4 (+20) | $0.06 | 10 (+20) | $0.07 |
| R16 R19 | C23186 | 0603WAF5101T5E | 2 | $0.0015 | 4 (+20) | $0.04 | 10 (+20) | $0.04 |
| R18 R20 | C25811 | 0603WAF2003T5E | 2 | $0.0023 | 4 (+20) | $0.06 | 10 (+20) | $0.07 |
| R25 R87 R94 | C17864 | 0805W8F9103T5E | 3 | $0.0034 | 6 (+20) | $0.09 | 15 (+20) | $0.12 |
| R26 R64 R79 R81 | C22962 | 0603WAF2200T5E | 4 | $0.0034 | 8 (+20) | $0.10 | 20 (+20) | $0.14 |
| R27 R37 R45 | C23162 | 0603WAF4701T5E | 3 | $0.0028 | 6 (+20) | $0.07 | 15 (+20) | $0.10 |
| R28 R36 R38 R44 R46 R88 R91 R95 R96 R105 | C25803 | 0603WAF1003T5E | 10 | $0.0031 | 20 (+20) | $0.12 | 50 (+20) | $0.22 |
| R29 R30 R57 | C17560 | 0805W8F2202T5E | 3 | $0.0048 | 6 (+20) | $0.12 | 15 (+20) | $0.17 |
| R65 | C31850 | 0603WAF2202T5E | 1 | $0.0041 | 2 (+20) | $0.09 | 5 (+20) | $0.10 |
| R66 R89 R92 R97 | C22978 | 0603WAF3301T5E | 4 | $0.0026 | 8 (+20) | $0.07 | 20 (+20) | $0.10 |
| R68 | C23221 | 0603WAF6202T5E | 1 | $0.0028 | 2 (+20) | $0.06 | 5 (+20) | $0.07 |
| R69 | C4184 | 0603WAF2002T5E | 1 | $0.0023 | 2 (+20) | $0.05 | 5 (+20) | $0.06 |
| R82 | C23206 | 0603WAF5602T5E | 1 | $0.0027 | 2 (+20) | $0.06 | 5 (+20) | $0.07 |
| R84 | C25808 | 0603WAF1203T5E | 1 | $0.0015 | 2 (+20) | $0.03 | 5 (+20) | $0.04 |
| R86 | C17514 | 0805W8F1004T5E | 1 | $0.0043 | 2 (+20) | $0.09 | 5 (+20) | $0.11 |
| R90 R93 R98 | C7250 | 0603WAF1005T5E | 3 | $0.0037 | 6 (+20) | $0.10 | 15 (+20) | $0.13 |
| U2 U4 U5 U14 U21 | C117501 | MCP6561T-E/OT | 5 | $0.7424 | 10 (+0) | $7.42 | 25 (+0) | $18.56 |
| U3 U7 U13 U22 U23 U24 | C49889 | MCP6241T-E/OT | 6 | $0.6936 | 12 (+0) | $8.32 | 30 (+0) | $20.81 |
| U18 | C11349 | CD4017BM96 | 1 | $0.7424 | 2 (+0) | $1.48 | 5 (+0) | $3.71 |
| U26 | C145613 | MCP4451-103E/ST | 1 | $2.9173 | 2 (+0) | $5.83 | 5 (+0) | $14.59 |
| U28 | C9386 | 74HC4051D,653 | 1 | $0.2195 | 2 (+0) | $0.44 | 5 (+0) | $1.10 |
| U101 U102 U103 | C5586 | 74HC00D,653 | 3 | $0.1548 | 6 (+0) | $0.93 | 15 (+0) | $2.32 |
| U104 U105 | C5605 | 74HC14D,653 | 2 | $0.1022 | 4 (+0) | $0.41 | 10 (+0) | $1.02 |
| U106 | C179842 | CD74HC4066M96 | 1 | $0.6092 | 2 (+0) | $1.22 | 5 (+0) | $3.05 |
| **Total** | | | | | | **$35.54** | | **$80.01** |

The card's B order assembles all 5 boards, so its "B order" column is the whole 5-board order, not an addition to A.

## Parts bought elsewhere

| Item | A: qty | A: $ | B: qty | B: $ | Unit | Source | Checked |
|---|---|---|---|---|---|---|---|
| Samtec ESQ-115-44-G-D (J10 socket) | 2 | $18.26 | 5 | $45.65 | $9.13 | Mouser, as listed on Samtec's product page | read on samtec.com |
| Samtec TSW-115-07-G-D (J11 header) | 2 | $6.36 | 5 | $15.90 | $3.18 | Mouser, as listed on Samtec's product page | read on samtec.com |
| Panasonic EEH-ZU1H221P 220 uF 50 V (hand-fit, 1 spare) | - | - | 28 | $86.24 | $3.08 | Digi-Key (search-engine summary) | UNVERIFIED |
| Panasonic EEH-ZU1E681UP 680 uF 25 V (hand-fit, 1 spare) | - | - | 10 | $31.30 | $3.13 | Digi-Key (search-engine summary) | UNVERIFIED |
| Microchip MCP6241T-E/OT (hand-fit, 1 spare) | - | - | 10 | $6.90 | $0.69 | placeholder: JLC's price; distributor price not read | UNVERIFIED |
| **Total** | | **$24.62** | | **$185.99** | | | |

Digi-Key, Mouser and Octopart show bot-check pages to my browser, and I did not get past them. So the Samtec prices are Mouser's as Samtec's own product pages list them, and the can prices are what a search engine reported from Digi-Key. B alternative (all five power boards hand-fitted) needs 46 x 220 uF, 16 x 680 uF and 16 x MCP6241: $264.35 elsewhere in total.

## Hardware (per assembled set: 4 tab screws, 4 standoff stacks, 4 card screws, the Arduino-end parts)

| Part | Role | A: qty | A: $ | B: qty | B: $ | Unit price | Source | Checked | Datasheet / page |
|---|---|---|---|---|---|---|---|---|---|
| Parker Chomerics 61-05-0909-G579 THERM-A-GAP 579, 1.27 mm, 9 x 9 in sheet | FET thermal pads (cut 10 x 16 mm) | 1 sheet | $85.00 | 1 sheet | $85.00 | about $85 | no price found for -05; Digi-Key lists -04 at $66.10 and -06 at $110.83 | ESTIMATE | [link](https://ph.parker.com/us/en/product/therm-a-gap-579-thermally-conductive-gap-filler-pads/61-05-0909-g579) |
| McMaster-Carr 92000A107, M2.5 x 12 pan head Phillips, 18-8 stainless | FET tab screws (4 per set) | 1 pack of 100 | $5.65 | 1 pack of 100 | $5.65 | $5.65 / 100 | mcmaster.com | read on mcmaster.com | [link](https://www.mcmaster.com/92000A107/) |
| McMaster-Carr 93657A200, nylon 6/6 spacer, M2.5, 2.0 mm long, 4.5 mm OD | FET tab-screw gap spacer (4 per set) | 8 | $7.36 | 20 | $15.00 | $0.92 (1-9), $0.75 (10+) | mcmaster.com | read on mcmaster.com | [link](https://www.mcmaster.com/93657A200/) |
| Boyd (Aavid) 7721-7PPSG shoulder washer, glass-filled PPS | insulates the tab screw in the tab hole (4 per set) | 8 | $2.08 | 20 | $5.20 | $0.26 | Digi-Key / Allied (search-engine summary) | UNVERIFIED | [link](https://eu.mouser.com/ProductDetail/Aavid/7721-7PPSG?qs=NqprlHOmxN1c1LnnOZYpOw%3D%3D) |
| Essentra HTSN-M3-5-3, nylon hex stud M3 male-male, 5 mm | board standoff, floor side (4 per set) | 8 | $4.80 | 20 | $12.00 | about $0.60 | Digi-Key lists $0.48 at 500; small-quantity price not read | ESTIMATE | [link](https://www.essentracomponents.com/en-us/p/pcb-standoffs-hexagonal-metric-imperial-threaded-plastic) |
| Essentra HNSM3-20-5.5-1, nylon hex standoff M3 female-female, 20 mm | card standoff (4 per set) | 8 | $6.40 | 20 | $16.00 | about $0.80 | no public price found (Essentra quotes on request) | ESTIMATE | [link](https://www.essentracomponents.com/en-us/p/pcb-standoffs-hexagonal-metric-imperial-threaded-plastic/hnsm3-20-5-5-1) |
| TR Fastenings TR NWE-34815-M3, nylon 6/6 washer 3.2 x 7.0 x 0.5 mm, pack of 100 | standoff shims (16 per set) | 1 pack | $11.67 | 1 pack | $11.67 | 8.71 GBP / 100 | Farnell UK, converted at 1.34 USD/GBP | price read via search; USD conversion assumed | [link](https://www.newark.com/tr-fastenings/tr-nwe-34815-m3/washer-nylon-6-6-3-2mm-pk100/dp/43Y4267) |
| Wurth Elektronik 97790803211, WA-SCRW M3 x 8 nylon 66 pan head | card screws (4 per set) | 8 | $2.13 | 20 | $5.33 | 0.199 GBP | Farnell UK, converted at 1.34 USD/GBP | price read via search; USD conversion assumed; link not opened | [link](https://www.we-online.com/en/components/products/WA-SCRW) |
| Pololu D24V5F5, 5 V 500 mA step-down module (5.1-36 V in) | 12 V -> 5 V at the Arduino end (1 per set) | 2 | $17.90 | 5 | $41.15 | $8.95 (1), $8.23 (5+) | pololu.com | read on pololu.com | [link](https://www.pololu.com/product/2843) |
| Adafruit 793, 40 female-female jumper wires, 300 mm, 28 AWG | J9 wires and Nano plug (11 per set) | 1 pack | $7.95 | 2 pack | $15.90 | $7.95 | adafruit.com | read on adafruit.com | [link](https://www.adafruit.com/product/793) |
| Bourns MF-R020, 0.20 A hold radial PTC | inline fuse on the J9 pin-9 (12 V) wire (1 per set) | 2 | $0.28 | 5 | $0.70 | $0.14 | LCSC (a separate LCSC order; JLC does not ship loose parts) | read on lcsc.com; datasheet link not opened | [link](https://www.bourns.com/docs/Product-Datasheets/mfr.pdf) |
| **Total** | | | **$151.22** | | **$213.60** | | | | |

Choices made for the parts that had none:
- **Tab-screw spacer: McMaster 93657A200 (2.0 mm)** in place of the 2.25 mm spacer. No stocked 0.25 mm shim was found. The thermal-pad compression comes from the standoff height, not the tab screw, which only retains the FET.
- **Tab screw: McMaster 92000A107.** Its head is 2.1 mm tall; the 3D model used 1.75 mm.
- **Standoff washers: TR Fastenings TR NWE-34815-M3.** Essentra's NWE-34815-M3 is obsolete at Digi-Key; this is the same washer, stocked at Farnell/Newark.
- **Arduino-end 5 V: Pololu D24V5F5.** **J9 wires and plug: Adafruit 793**: cut each jumper and solder the cut end into J9. The female housing then plugs onto the Nano's pins. I have not checked the pack's colour mix against the J9 table: where a colour is missing, use white with a coloured marker (BUILD_NOTES already allows that for pin 11). **PTC: Bourns MF-R020.**

## If you stay on rev5 (2 mOhm R1, INA241A3)

The fallback you set: keep 2 mOhm with the INA241A3 and hand-fit R1. Per power board, JLC then fits INA241A3IDR (C22427652, $4.63, **stock 16**: enough for all scenarios) instead of INA241A4 ($3.52); R1 (Bourns CSS4J-4026K-2L00F) is 0 at JLC and gets bought elsewhere at about $1.08 (JLC's listed price; distributor price **UNVERIFIED**). That is about +$0.48 per power board, and one fewer JLC line (-$1.53 loading).

## Unverified or estimated (flagged)

1. **Distributor prices for the hand-fit cans** (EEH-ZU1H221P $3.08, EEH-ZU1E681UP $3.13): a search engine's summary of Digi-Key, not read on Digi-Key. **MCP6241T-E/OT** elsewhere: no distributor price read; JLC's $0.69 is used as a placeholder.
2. **Samtec ESQ/TSW**: Mouser's prices as listed on Samtec's pages, not read on Mouser.
3. **Parker 61-05-0909-G579 sheet: about $85, an estimate** between the -04 and -06 sheets' Digi-Key prices. One sheet covers far more than 5 sets.
4. **Essentra HTSN-M3-5-3 (about $0.60) and HNSM3-20-5.5-1 (about $0.80): estimates.** Essentra quotes on request, and Digi-Key's small-quantity prices were not readable.
5. **Boyd 7721-7PPSG $0.26**: search-engine summary of Digi-Key/Allied.
6. **TR washers and Wurth screws**: Farnell UK prices in GBP, converted at an assumed 1.34 USD/GBP.
7. **JLC parts**: quantity-1 prices. JLC may apply a price break or a minimum purchase on some lines; attrition follows the "about 20 per small-passive line" read on 2026-09-24, and 0 on the other lines.
8. **Stock moves daily.** The 2 LM2940S-12 and the 19 x 220 uF are exact or near-exact for A. Re-check stock the day you order.
9. **The V-suffix Panasonic alternates** (EEH-ZU1H221V, EEH-ZU1E681UV): not used. Their land patterns are not checked.
10. **Two links not opened**: the Wurth WA-SCRW page and the Bourns MF-R datasheet URL. The Adafruit 793 colour mix is not checked against the J9 wire colours.
11. **JLC fees** (set-up, stencil, loading, joints) are from JLC's price page, not from a quote with the files uploaded. The PCB prices are from the quote page with dimensions entered, not with the gerbers uploaded. An upload can add engineering charges (for example for the via-in-pad count).

Generated by `tools/cost_summary.py` from `bom/SOURCING_TABLE.csv` and `bom/jlc_snapshot_2026-09-24.json`; every number is also in `cost/cost_summary.json`.
