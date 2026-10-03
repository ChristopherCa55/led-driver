# BOOST: cost summary, scenario A (updated 2026-10-01)

**Scenario A:** 5 bare PCBs of each board, 2 complete sets assembled by JLCPCB, 3 spare bare boards of each. **Shipping and tax are not included anywhere below.** Excluded because you own them: M1-M10, L1, the 12 V -> 5 V buck module and the J9 wires. Also excluded: case, battery cabling and lugs, Arduino Nano and CAN parts, LEDs.

The BOM is schematic **rev6** (R1 = Bourns CSS4J-4026R-1L00F, U25 = INA241A4) **plus the pre-charge diodes D28-D30 (S2MW)**, with the **6-layer control card**.


## Grand total

| | Power board | Control card | Total |
|---|---|---|---|
| Bare PCBs (5 each) | $124.10 | $56.83 | $180.93 |
| JLC assembly of 2 each (fees + parts) | $212.89 | $162.46 | $375.35 |
| Parts bought elsewhere (J10, J11, PTC) | | | $24.91 |
| Hardware for 2 sets, without the thermal pad | | | $55.14 |
| **Subtotal without the pad** | | | **$636.33** |
| + McMaster 1272N32 pad (default) | | | **$663.24** |
| + Parker G579 0.060 in pad instead | | | $765.08 |
| + t-Global TG-AD30 1.5 mm instead | | | $636.33 + its price (not read) |
| Shipping, tax | | | not included |

Against the 2026-09-25 total ($760.83 with the McMaster pad):
- the control card went from 8 to 6 layers, then to 0.5 oz inner copper: $137.04 -> $73.57 -> $56.83 for 5 panels;
- D28-D30 (S2MW, LCSC C128729) were added to the power board: 3 parts, one more unique part to load;
- every JLC part price and stock figure was read again on 2026-10-01;
- the savings you approved on 2026-10-01 are applied (see "Ways to save").

The JLC lines and the PTC were read on 2026-09-30 / 2026-10-01. The Samtec, McMaster, Digi-Key and Farnell prices are the 2026-09-25 readings, not read again. The TR washers and the Wurth screws are Farnell UK prices converted from GBP.

## Ways to save

Savings are for this build: 5 bare boards of each, 2 of each assembled.

**Applied:**

| Change | Saved | Note |
|---|---|---|
| Control card 8 -> 6 layers (2026-09-30) | $63.47 | card panel $137.04 -> $73.57 |
| 220 uF output caps: EEH-ZS1H221P (C385885) on C70, C71, C75, C77, C78, C88; EEH-ZU1H221P stays on C74, C86, C87 | $12.89 | also cleared the ZU stock shortage (14 in stock, now 6 needed) |
| Card inner copper 0.5 oz | $16.74 | card panel $73.57 -> $56.83; stackup now 1.547 mm (JLC 6-layer 1/0.5 oz build); Gerber layers unchanged |
| Op-amps: TI TLV9001IDBVR for the 18 MCP6241 (same SOT-23-5 pinout) | $8.78 | LTspice re-runs against the MCP6241 (30 ms full power, 25 % PWM, cold start to 140 ms): LED currents, LX, TVS energy and servo levels match within 0.05 % |

**Still open (your choice):**

| Option | Saves | What it takes | Verdict |
|---|---|---|---|
| **12 V regulator U16 in SOT-223: UTC LM2940G-12-AA3-R** (C127023, $0.24, 119 in stock), a second-source LM2940 | $8.68 | UTC data sheet: 1 A, 26 V, 60 V for 100 ms, 0.11-0.15 V dropout at 100 mA, pins 1 IN / 2 GND / 3 OUT, Cout >= 22 uF, -40 to +85 C ambient in SOT-223. Load: 16 mA simulated plus about 0.1 A for the Arduino buck. At 18 V in it dissipates 0.9-1.2 W (including its 10-15 mA ground current): junction about 87-123 C at 50 C air with 40-60 C/W on this board's copper (assumed air temperature). The swap is tested: footprint at U16's spot, the existing Vin and 12 V vias land in pads 1 and 3, DRC unchanged. If it ever overheats it shuts down cleanly: U21 stops M1 below 9.8 V, the drivers' 8 V UVLO stops the rest, the Arduino resets with the rail, and the LEDs come back like a cold start (simulated). | Your pick, pending |
| 12 V regulator U16 in SOT-223: TI LM2940IMPX-12/NOPB (C2866640, $1.68, 1293 in stock), the same chip as now | $5.80 | Same chip and ratings as the LM2940S-12, operating junction up to 125 C; same heat and the same swap as above. | Alternative |
| Arduino buck fed from Vin instead of the 12 V rail (on top of either regulator) | - | Cuts the regulator's loss to 0.3-0.5 W (junction about 61-78 C). Needs a 1206 PTC (about 0.2-0.35 A hold, >= 30 V) at the tap point and a new low-current net to J10 pin 19 (the board rule wants 1.0 mm tracks on Vin); the existing 26 mm branch to J10.19 runs past Vin copper. The buck must take up to 18 V. Simulated drawback: after a 12 V dropout the Arduino keeps its references up, so the restart gives LX 62 V at 16.8 V and 82 V at 18 V (with the Arduino on 12 V the restart is a gentle cold start). | Optional; cooler but a harsher restart |
| Samtec J10/J11 through Samtec's free-sample program | $24.62 | Needs a Samtec account (your choice). A generic header pair would need the exact stack height re-checked. | Worth asking Samtec |
| Ordering | shipping | Pay both JLC orders together so they ship as one parcel; JLC's JLCONE desktop app advertises $1-20 off per order; check the coupons in your JLC account. | Do it |

**Looked at, no good cheaper alternative (kept):**
- Comparators MCP6561 ($0.74 x 10): the cheaper parts are slower (Linearin LTC8721: 66-155 ns, 85 C), run hotter on supply current (Tokmas CSGM8743: 1.3 mA, 85 C) or save only $1.74 in all (3PEAK TP1961). TI TLV3201 costs more.
- Digital pot MCP4451-103 ($2.91): already the cheapest 10 kOhm quad of its family; the 50 kOhm versions would change the current-setting network, the 7-bit MCP4441 is QFN and dearer.
- L78L05 5 V regulators ($0.102 x 4): the clones cost $0.03-0.05, but under $0.10 JLC adds about 20 attrition spares per line, so the line costs more. Loads 8 mA and 3 mA (simulated).
- 12 V regulator in a 78xx-style DPAK or TO-263 ($0.08-0.26): 2 V dropout would pull the 12 V rail down to the M1 cut-off (9.85 V) and the gate-driver UVLO at low battery.
- Card FR4 TG135 (-$3.43): you chose to keep TG155.
- OSP finish (-$34.50): shelf life and hand soldering after two reflows.
- A 6-layer power board ($69.57): complete re-route. One-sided assembly: parts on both sides of both boards.
- INA240A3 for INA241A4: slower and an 80 V limit.


## Bare PCBs (JLCPCB quote page, 2026-10-01)

Both boards: 1.6 mm, FR4 TG155, ENIG, 1 oz outer copper, **Epoxy Filled & Capped vias ($0.00 at 6 and 8 layers)**, min via 0.3 mm, Remove Mark, flying-probe full test. The power board is 8 layers with 1 oz inner copper; the card is 6 layers with 0.5 oz inner copper (the standard JLC 6-layer 1 / 0.5 oz build, 1.547 mm).

| Board | Order | Price for 5 | Breakdown |
|---|---|---|---|
| Power | 8 layers: 5 single boards, 74 x 86 mm | $124.10 | $90.00 special offer, $17.30 ENIG, $16.80 1 oz inner, $0.00 via covering (10-11 day build) |
| Card | 6 layers, 0.5 oz inner copper: 5 panels, one 45 x 45 mm card on a 70 x 70 mm carrier (12.5 mm rails, four sides, V-cut) | $56.83 | $33.00 engineering, $17.20 ENIG, $3.43 TG155, $3.20 board, $0.00 via covering, 0.5 oz inner at no charge (8-9 day build) |

The card has to go on a carrier panel: JLC's Standard PCBA takes nothing under 70 x 70 mm, and Economic PCBA handles single-sided boards only (the card has parts on both sides). The panel costs $4.67 more than 5 single cards ($52.16).

## Assembly (JLC Standard PCBA, 2 of each)

Set-up $51.12 and stencil $16.42 per order (both boards are double-sided); feeder loading $1.53 per unique part; $0.0016 per solder joint (JLC price page, read 2026-10-01). Parts: JLC quantity-1 prices read 2026-09-30, plus about 20 attrition spares per small-passive line.

| Board | Unique parts | Set-up | Stencil | Loading | Joints | Parts | Attrition | **Assembly** | PCB | **Order** |
|---|---|---|---|---|---|---|---|---|---|---|
| Power | 29 | $51.12 | $16.42 | $44.37 | $0.91 (570) | $92.73 | $7.33 | **$212.89** | $124.10 | **$336.99** |
| Card | 41 | $51.12 | $16.42 | $62.73 | $1.51 (944) | $22.53 | $8.15 | **$162.46** | $56.83 | **$219.29** |

## Stock on 2026-10-01 (JLC parts library)

63 LCSC part numbers across both boards. None is short.
The tight ones (stock under 3x the need, or under 100; JLC buys no attrition spares on these):

| Part | LCSC | Stock | Needed for 2 sets | Note |
|---|---|---|---|---|
| TR3D476K025C0250 | C4979367 | 63 | 2 |  |
| EEH-ZU1E681UP | C29664285 | 10 | 6 |  |
| EEH-ZU1H221P | C6843593 | 14 | 6 | now only C74, C86 and C87 (6 for two boards) |
| LM2940S-12/NOPB | C2877347 | 2 | 2 | **exactly 2.** Fallbacks, same TI part in TO-263: LM2940SX-12/NOPB C131916 (4 in stock, $4.25) and LM2940CS-12/NOPB C2865267 (7, $4.71). Or the SOT-223 swap under "Ways to save" |
| MCP4451-103E/ST | C145613 | 40 | 2 |  |
| CD74HC4066M96 | C179842 | 73 | 2 |  |

Re-check on the day you order: JLC's BOM page shows any shortage when you upload the BOM. The snapshot is `bom/jlc_snapshot_2026-10-01.json` in `BOOST_split_boards/bom_2026-09-30/`.

## Itemised JLC parts (everything JLC buys; excludes M1-M10 and L1)

### Power board

| Refs | LCSC | MPN | Per board | Unit | Qty for 2 (+attrition) | $ |
|---|---|---|---|---|---|---|
| C1 C4 C73 | C381466 | FS32X475K101EGG | 3 | $0.2328 | 6 (+0) | $1.40 |
| C3 C72 C76 | C28233 | CL21B104KCFNNNE | 3 | $0.0357 | 6 (+20) | $0.93 |
| C6 C21 C25 C31 C62 C89 | C28323 | CL21B105KBFNNNE | 6 | $0.0399 | 12 (+20) | $1.28 |
| C7 C55 | C21397 | GRM32ER71E226KE15L | 2 | $0.4585 | 4 (+0) | $1.83 |
| C16 C18 C60 | C50254 | CL31B225KBHNNNE | 3 | $0.0857 | 6 (+20) | $2.23 |
| C20 C33 C34 C35 C48 C50 C51 C61 C82 C83 C84 C90 | C14663 | CC0603KRX7R9BB104 | 12 | $0.0123 | 24 (+20) | $0.54 |
| C30 | C4979367 | TR3D476K025C0250 | 1 | $1.0990 | 2 (+0) | $2.20 |
| C39 C56 C79 C80 C81 | C138687 | CL32B106KBJNNNE | 5 | $0.3252 | 10 (+0) | $3.25 |
| C40 C69 C85 | C29664285 | EEH-ZU1E681UP | 3 | $2.5409 | 6 (+0) | $15.25 |
| C41 C44 C45 | C1588 | CL10B102KB8NNNC | 3 | $0.0089 | 6 (+20) | $0.23 |
| C74 C86 C87 | C6843593 | EEH-ZU1H221P | 3 | $2.8352 | 6 (+0) | $17.01 |
| C70 C71 C75 C77 C78 C88 | C385885 | EEHZS1H221P | 6 | $1.6338 | 12 (+0) | $19.61 |
| D2 D8 D11 D13 D14 D22 | C8598 | B5819W SL | 6 | $0.0280 | 12 (+20) | $0.90 |
| D9 D10 D21 | C21565 | BAV21W | 3 | $0.0191 | 6 (+20) | $0.50 |
| D28 D29 D30 | C128729 | S2MW | 3 | $0.0183 | 6 (+20) | $0.48 |
| D19 | C42394451 | 5.0SMDJ54A | 1 | $0.3951 | 2 (+0) | $0.79 |
| R1 | C2076400 | CSS4J-4026R-1L00F | 1 | $1.7086 | 2 (+0) | $3.42 |
| R7 R52 R53 | C413486 | WSL2512R0500FEA | 3 | $0.2348 | 6 (+0) | $1.41 |
| R13 R23 R47 | C22962 | 0603WAF2200T5E | 3 | $0.0035 | 6 (+20) | $0.09 |
| R14 | C17514 | 0805W8F1004T5E | 1 | $0.0043 | 2 (+20) | $0.09 |
| R15 | C17415 | 0805W8F100JT5E | 1 | $0.0040 | 2 (+20) | $0.09 |
| R21 R48 R60 R72 | C17724 | 0805W8F510KT5E | 4 | $0.0041 | 8 (+20) | $0.11 |
| R22 R50 R56 | C22775 | 0603WAF1000T5E | 3 | $0.0031 | 6 (+20) | $0.08 |
| R49 R61 R62 R73 R74 R75 R76 R104 | C25804 | 0603WAF1002T5E | 8 | $0.0018 | 16 (+20) | $0.06 |
| R59 R70 | C17724 | 0805W8F510KT5E | 2 | $0.0041 | 4 (+0) | $0.02 |
| U1 U17 | C43116 | L78L05ACUTR | 2 | $0.1020 | 4 (+0) | $0.41 |
| U6 U11 U12 | C398363 | TLV9001IDBVR | 3 | $0.0979 | 6 (+20) | $2.55 |
| U8 U10 U15 U19 | C601651 | UCC21520DWR | 4 | $0.8893 | 8 (+0) | $7.11 |
| U16 | C2877347 | LM2940S-12/NOPB | 1 | $4.5795 | 2 (+0) | $9.16 |
| U25 | C22427873 | INA241A4IDR | 1 | $3.5277 | 2 (+0) | $7.06 |
| **Total** | | | | | | **$100.06** |

### Control card

| Refs | LCSC | MPN | Per board | Unit | Qty for 2 (+attrition) | $ |
|---|---|---|---|---|---|---|
| C8 C9 C17 C19 | C1664 | CL10C331JB8NNNC | 4 | $0.0179 | 8 (+20) | $0.50 |
| C10 C11 C13 | C85980 | GRM1885C1H472JA01D | 3 | $0.0212 | 6 (+20) | $0.55 |
| C12 C22 C23 C24 C26 C28 C29 C32 C36 C37 C38 C42 C43 C46 C52 C53 C54 C58 C59 C63 C65 C66 C68 C92 C94 C95 C96 C97 C98 C99 C104 | C14663 | CC0603KRX7R9BB104 | 31 | $0.0123 | 62 (+20) | $1.01 |
| C14 | C27675 | CL10C221JB8NNNC | 1 | $0.0095 | 2 (+20) | $0.21 |
| C15 | C14858 | CL10C101JB8NNNC | 1 | $0.0086 | 2 (+20) | $0.19 |
| C47 C93 C103 | C96446 | CL10A106MA8NRNC | 3 | $0.0752 | 6 (+20) | $1.96 |
| C49 C64 C67 | C97946 | GRM31C5C1H104JA01L | 3 | $0.1849 | 6 (+0) | $1.11 |
| C57 C91 | C28323 | CL21B105KBFNNNE | 2 | $0.0399 | 4 (+20) | $0.96 |
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
| R26 R64 R79 R81 | C22962 | 0603WAF2200T5E | 4 | $0.0035 | 8 (+20) | $0.10 |
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
| U2 U4 U5 U14 U21 | C117501 | MCP6561T-E/OT | 5 | $0.7430 | 10 (+0) | $7.43 |
| U3 U7 U13 U22 U23 U24 | C398363 | TLV9001IDBVR | 6 | $0.0979 | 12 (+20) | $3.13 |
| U18 | C11349 | CD4017BM96 | 1 | $0.7267 | 2 (+0) | $1.45 |
| U26 | C145613 | MCP4451-103E/ST | 1 | $2.9051 | 2 (+0) | $5.81 |
| U28 | C9386 | 74HC4051D,653 | 1 | $0.2146 | 2 (+0) | $0.43 |
| U101 U102 U103 | C5586 | 74HC00D,653 | 3 | $0.1546 | 6 (+0) | $0.93 |
| U104 U105 | C5605 | 74HC14D,653 | 2 | $0.1023 | 4 (+0) | $0.41 |
| U106 | C179842 | CD74HC4066M96 | 1 | $0.6097 | 2 (+0) | $1.22 |
| **Total** | | | | | | **$30.68** |

## Parts bought elsewhere

| Item | Qty | Unit | $ | Source | Checked |
|---|---|---|---|---|---|
| Samtec ESQ-115-44-G-D, J10 socket (power board) | 2 | $9.1300 | $18.26 | Mouser, as listed on samtec.com | read on samtec.com |
| Samtec TSW-115-07-G-D, J11 header (card) | 2 | $3.1800 | $6.36 | Mouser, as listed on samtec.com | read on samtec.com |
| Bourns MF-R050 PTC, 0.50 A hold (inline on the J9 pin-9 wire), LCSC C208476 | 2 | $0.1433 | $0.29 | LCSC (its own order; JLC does not ship loose parts) | read 2026-09-30 (7,030 in stock); derating from the Bourns MF-R datasheet |
| **Total** | | | **$24.91** | | |

**PTC changed to MF-R050** (you asked, 2026-09-25). Bourns MF-R datasheet, thermal derating table:

| | 23 C | 60 C | 70 C | 75 C (interpolated) | 85 C |
|---|---|---|---|---|---|
| MF-R020 hold / trip (A) | 0.20 / 0.40 | 0.13 / 0.26 | 0.11 / 0.22 | about 0.10 / 0.20 | 0.08 / 0.16 |
| **MF-R050 hold / trip (A)** | **0.50 / 1.00** | 0.32 / 0.64 | 0.27 / 0.54 | **about 0.25 / 0.49** | 0.20 / 0.40 |

The load is about 0.1 A. MF-R050 still holds about 2.5x that at 75 C. It trips at 1.0 A at room temperature, which protects the 26-28 AWG wire and the card's 0.3 mm track; the LM2940 current-limits above its 1 A rating. Its resistance is 0.41-0.77 ohm new and 1.17 ohm at most an hour after a trip, so the drop at 0.1 A is at most 0.12 V. Rated 60 V, -40 to +85 C.

## Hardware for 2 sets

| Part | Role | Qty | $ | Source | Checked | Page |
|---|---|---|---|---|---|---|
| McMaster-Carr 92000A107, M2.5 x 12 pan head Phillips, 18-8 stainless, pack of 100 | FET tab screws (4 per set) | 1 pack | $5.65 | mcmaster.com | read | [link](https://www.mcmaster.com/92000A107/) |
| McMaster-Carr 93657A200, nylon 6/6 spacer, M2.5, 2.0 mm long, 4.5 mm OD | FET tab-screw gap spacer (4 per set) | 8 | $7.36 | mcmaster.com ($0.92 each under 10) | read | [link](https://www.mcmaster.com/93657A200/) |
| Boyd (Aavid) 7721-7PPSG shoulder washer, glass-filled PPS | insulates each tab screw in the FET tab hole (4 per set) | 8 | $1.31 | Digi-Key $0.164 at 5+ (10 for $1.51) | read by you 2026-09-25 | [link](https://www.digikey.com/en/products/result?keywords=7721-7PPSG) |
| McMaster-Carr 92605A109, M3 x 20 mm set screw, 18-8 stainless, flat tip, pack of 25 | floor stud, part 1: threaded 6 mm into the floor (4 per set) | 1 pack | $10.69 | mcmaster.com | read | [link](https://www.mcmaster.com/92605A109/) |
| McMaster-Carr 94669A099, aluminium unthreaded spacer, M3, 5.00 +/-0.13 mm long, 4.5 mm OD | floor stud, part 2: sets the board height with the washer (4 per set; buy 10 to select 8) | 10 | $5.00 | mcmaster.com ($0.50 each) | read | [link](https://www.mcmaster.com/94669A099/) |
| Essentra HNSM3-20-5.5-1, nylon hex standoff M3 female-female, 20 mm | board-to-card standoff (4 per set) | 8 | $11.33 | Digi-Key $1.416 at 5+ (10 for $13.22) | read by you 2026-09-25 | [link](https://www.digikey.com/en/products/detail/essentra-components/HNSM3-20-5-5-1/3813076) |
| TR Fastenings TR NWE-34815-M3, nylon 6/6 washer 3.2 x 7.0 x 0.5 mm, pack of 100 | standoff shims (16 per set) | 1 pack | $11.67 | Farnell UK 8.71 GBP, converted at 1.34 USD/GBP | price via search; conversion assumed | [link](https://www.newark.com/tr-fastenings/tr-nwe-34815-m3/washer-nylon-6-6-3-2mm-pk100/dp/43Y4267) |
| Wurth Elektronik 97790803211, WA-SCRW M3 x 8 nylon 66 pan head | card screws (4 per set) | 8 | $2.13 | Farnell UK 0.199 GBP each, converted at 1.34 USD/GBP | price via search; conversion assumed | [link](https://www.we-online.com/en/components/products/WA-SCRW) |
| **Total without the pad** | | | **$55.14** | | | |

**Floor stud (replaces Essentra HTSN-M3-5-3, which Digi-Key sells only as 6,500 pieces).**
- Preferred option: an M3 x 5 mm male-male hex standoff in small quantities.
  - LCSC and McMaster have none. McMaster sells male-female and female-female only.
  - LCSC's brass M3*5+6 pillars (C87703) come with no drawing: no hex size, length tolerance or thread depth.
  - I could not read Keystone or Wurth parts through Digi-Key.
- So it is your option 2, built from McMaster parts that publish their tolerances:
  1. **92605A109**: M3 x 20 mm, 18-8 stainless, flat tip. Threaded 6 mm into the floor's 7 mm tapped hole with low-strength threadlocker, so 14 mm stands proud.
  2. **94669A099**: aluminium spacer, 5.00 +/-0.13 mm long, 4.5 mm OD, 3.2 mm ID, dropped over it.
  3. The TR washer (0.5 mm), then the power board. Underside at 5.50 mm, as before.
  4. The HNSM3-20-5.5-1 screws onto the set screw with **6.9 mm of thread engaged** (3.9 mm with the old stud).
     The card screw uses 4.9 mm of the other end, so 6.9 + 4.9 = 11.8 mm of the 20 mm standoff is used and the two cannot meet.
- It is metal and does not creep. The clamp load sits in the steel screw (tension) and the aluminium spacer (compression); the only nylon in that path is the 0.5 mm washer.
- Buy 10 spacers and fit the 8 whose spacer + washer measures closest to 5.50 mm; the target stays 5.50 +/-0.10 mm.
- Low-strength threadlocker (Loctite 222 or similar) is not priced: most workshops have it.

**Is a metal stud safe?** Yes. Measured on the plotted boards, 2026-09-25 (`tools/hole_isolation.py`):
- H5-H8 are unplated 3.2 mm holes with no copper ring. The nearest copper on any layer is 3.10-3.49 mm from the hole centre, 1.5-1.9 mm from the hole wall.
- The steel screw (1.5 mm radius) stays in the hole. The aluminium spacer (2.25 mm radius) sits under the 7.0 mm nylon washer, 0.5 mm below the board, so no metal reaches any copper.
- The card (H1-H4) has only nylon at its holes: the standoff top and the card screw. Its nearest copper is 3.36 mm from the centre.
- Finding: each hole has a 3.5 mm-radius copper keep-out, but on the power board some track edges come to 3.10 mm (H6) and 3.21 mm (H5), inside that circle. KiCad's DRC does not flag them, so it appears to check these keep-outs less strictly than drawn.
  - It does not matter for this hardware: that copper is under soldermask, below the nylon washer and the nylon standoff hex, never under metal.

## Thermal pad: the ones you can buy

Full numbers in `cost/pad_options.txt` (`tools/pad_options.py`). The stack puts every pad at **0.93 mm**. The approved G579 was 1.27 mm (27 %), but that sheet is not sold at Digi-Key; every pad below is about 1.5 mm, so about 39 %.

| Pad | Published | At 0.93 mm (per FET, nominal / worst case) | M1 Tj, 25 C water | Price |
|---|---|---|---|---|
| Approved: G579 0.050 in, 1.27 mm | curve, 3.0 W/m-K, 7.9 kV/mm | 27 %: 7.7 N / 22 N (77 N for 10) | about 78 C | not sold |
| **McMaster 1272N32**, 1.52 mm, 40 Shore 00 | 3 W/m-K only: **no curve, no dielectric strength** | 39 %: **about 25 N / 49 N** (about 250 N for 10), estimated from 40 Shore 00 against G579's 30 (x1.6, +/-50 %) | about 78 C (contact assumed as G579) | **$26.91**, 4 x 4 in |
| Parker 61-06-0909-G579, 1.524 mm, 30 Shore 00 | curve, 3.0 W/m-K, 7.9 kV/mm | 39 %: **15 N / 30 N** (151 N) from Parker's curve; 39 % is the top of Parker's "typical 5-40 %", and the worst case reaches 56 % | about 78 C | **$128.75**, 9 x 9 in |
| **t-Global TG-AD30**, 1.5 mm, 20 Shore 00 | curve, 3.0 W/m-K, **>= 5 kV/mm** | 38 %: **12 N / 24 N** (116 N) | **about 71 C** | not read (URL below) |

**What 39 % means for the stack.** The stack height does not change: 0.93 mm is fixed by the 5.50 mm board height. What changes is the force.
- **Force.** About twice the approved design with G579, and an estimated three times with the McMaster pad (roughly 150 N and 250 N over ten FETs, against 77 N).
- **Where it goes.** It pushes the power board up. The board is held down by the four standoffs, and near M1/M8/M9/M10 by the tab-screw heads once the board has lifted their 0.25 mm of free play.
- **The standoffs.** With the metal stud above, the load sits in steel and aluminium. The nylon standoff's 6.9 mm of thread takes about 60 N each, roughly 2 MPa, which is small. So it **does not change the standoff choice**; it is one more reason to prefer the metal stud to a nylon one.
- **Board bow.** The extra force will bow the board up a little between supports, which unloads the middle pads somewhat. I have not modelled the board (no FEA).
- **Not recommended:** shimming the board up 0.25 mm to get back to about 22 %. That also lifts the card, and the card screw heads would come to 0.40 mm under the lid, against 0.65 mm now.

**Recommendation.**
- If TG-AD30 comes in a 1.5 mm sheet of 150 x 150 mm or less for about $40 or less, buy it. It is the only candidate that is soft, publishes both a curve and a dielectric strength, and it lowers M1 by about 7 C.
- Otherwise buy the McMaster 1272N32 (the default). Its risk is the missing dielectric rating, covered by the tab-to-case test now in BUILD_NOTES.
- The G579 at $128.75 works, but costs about five times as much for nothing extra.

## Your buck converter

Fed from J9 pin 9 (the 12 V LM2940 rail) through the MF-R050. It has to:
- regulate from 11-13 V in, and survive at least 20 V;
- give 5.0 V +/-5 % at 200 mA or more;
- draw about 0.1 A.

**No extra input filter** (your decision, 2026-09-25): the converter has its own input capacitors, and the draw is about 0.1 A. This is noted in BUILD_NOTES.

## URLs for you to read

One line is left:

1. **t-Global TG-AD30** (FET thermal pads; you need about 10 x 16 mm x 20 pads, a 100 x 100 mm sheet is plenty). Look for 1.5 mm thickness and the smallest sheet: https://www.digikey.com/en/products/result?keywords=TG-AD30

## Still flagged

1. TR washers and Wurth screws: Farnell UK prices in GBP, converted at an assumed 1.34 USD/GBP.
2. The McMaster pad's force is an estimate from its hardness (+/-50 %), and it publishes no dielectric strength.
3. Samtec ESQ/TSW: Mouser's prices as listed on Samtec's pages, not read on Mouser.
4. JLC: quantity-1 prices, attrition about 20 per small-passive line, fees from JLC's price page. The upload itself may add charges.
5. The Wurth WA-SCRW page link was not opened.
6. The Samtec, McMaster, Digi-Key and Farnell prices were not read again after 2026-09-25.

Scenario B was dropped on 2026-09-25. Its files are kept, not developed further: `cost/BOOST_power_BOM_JLC_limitedDNP.csv`, `cost/BOOST_power_CPL_JLC_limitedDNP.csv`, `cost/COST_SUMMARY_AB_2026-09-24.md`.

Generated by `BOOST_split_boards/bom_2026-09-30/tools/cost_summary.py`; every number is also in `cost/cost_summary.json` there.
