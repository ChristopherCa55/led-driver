# BOM and JLCPCB sourcing, 2026-09-24

Stock and prices read from the JLCPCB parts library on 2026-09-24 (snapshot: `jlc_snapshot_2026-09-24.json`). "Max sets" is how many power board + control card pairs the stock covers at the quantities used on both boards. Unit prices are JLC's quantity-1 prices; JLC also buys a few spares of each small part (attrition), not included here.

## JLC fits (bought and fitted by JLCPCB)

| Board | Refs | Qty | Value | Footprint | Side | LCSC | MPN (maker) | Basic/Ext | Stock | $/unit | Max sets | Orderable | Why / notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| power | C1 C4 C73 | 3 | 4.7uF | 1210 | top | C381466 | FS32X475K101EGG (PSA (Prosperity Dielectrics)) | Extended | 195752 | 0.2421 | 65250 | yes | on Vout (23-33 V running; TVS stand-off 54 V, clamp 87 V): 100 V rated; commutation-loop ceramic per rail; 50 V part C170099 is cheaper but keeps less capacitance at 33 V Alternates: C170099 (50 V) |
| power | C3 C72 C76 | 3 | 100nF | 0805 | top | C28233 | CL21B104KCFNNNE (Samsung) | Basic | 1749919 | 0.0356 | 583306 | yes | on Vout (23-33 V running; TVS stand-off 54 V, clamp 87 V): 100 V rated |
| power | C6 C21 C25 C31 C62 C89 | 6 | 1uF | 0805 | bottom/top | C28323 | CL21B105KBFNNNE (Samsung) | Basic | 2568377 | 0.0398 | 321047 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V) |
| power | C7 C55 | 2 | 22uF | 1210 | top | C21397 | GRM32ER71E226KE15L (Murata) | Extended | 73199 | 0.4597 | 36599 | yes | part chosen earlier (HANDOFF_SUMMARY / replace_notes / ANSWERS) |
| power | C16 C18 C60 | 3 | 2.2uF | 1206 | bottom | C50254 | CL31B225KBHNNNE (Samsung) | Basic | 417173 | 0.0857 | 139057 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V); bootstrap caps, 12 V across |
| power | C20 C33 C34 C35 C48 C50 C51 C61 C82 C83 C84 C90 | 12 | 100nF | 0603 | bottom/top | C14663 | CC0603KRX7R9BB104 (YAGEO) | Basic | 51360098 | 0.0122 | 1194420 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V); C82-C84 on Vin (<= 17 V), 50 V part |
| power | C30 | 1 | 47uF tantalum | EIA-7343 (D) | top | C4979367 | TR3D476K025C0250 (Vishay) | Extended | 107 | 1.1566 | 107 | yes | part chosen earlier (HANDOFF_SUMMARY / replace_notes / ANSWERS); LM2940 output, ESR 250 mOhm |
| power | C39 C56 C79 C80 C81 | 5 | 10uF | 1210 | top | C138687 | CL32B106KBJNNNE (Samsung) | Extended | 36383 | 0.325 | 7276 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V); C79-C81 on Vin: 50 V X7R |
| power | C40 C69 C85 | 3 | 680uF EEH-ZU1E681UP | CP_Elec_10x12.5 | top | C29664285 | EEH-ZU1E681UP (Panasonic) | Extended | 10 | 2.5389 | 3 | LIMITS BUILD | part chosen earlier (HANDOFF_SUMMARY / replace_notes / ANSWERS); STOCK 10: enough for 3 boards (3 each) |
| power | C41 C44 C45 | 3 | 1nF | 0603 | top | C1588 | CL10B102KB8NNNC (Samsung) | Basic | 8270810 | 0.0089 | 1378468 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V); IREF wiper filter Alternates: C163508 (C0G) |
| power | C70 C71 C74 C75 C77 C78 C86 C87 C88 | 9 | 220uF EEH-ZU1H221P | CP_Elec_10x16.5 | top | C6843593 | EEH-ZU1H221P (Panasonic) | Extended | 19 | 2.8329 | 2 | LIMITS BUILD | part chosen earlier (HANDOFF_SUMMARY / replace_notes / ANSWERS); STOCK 19: enough for 2 boards (9 each) |
| power | D2 D8 D11 D13 D14 D22 | 6 | B5819W (gate turn-off) | SOD-123 | bottom | C8598 | B5819W SL (JSCJ (Changjing)) | Basic | 500510 | 0.028 | 83418 | yes | your choice of 2026-09-24; no diode type in the schematic (LTspice default diode). Anode on the FET gate, cathode to the driver side of the gate resistor: the turn-off path. Proposal B5819W (40 V 1 A Schottky, Basic) Alternates: C81598 1N4148W |
| power | D9 D10 D21 | 3 | BAV21W (bootstrap) | SOD-123 | bottom | C21565 | BAV21W (JSCJ (Changjing)) | Extended | 90626 | 0.0191 | 30208 | yes | your choice of 2026-09-24; no diode type in the schematic. 12 V to the high-side VDDA: blocks the rail FET source voltage (up to Vout, 54-87 V under a clamp event). Proposal BAV21W (200 V, trr 50 ns) Alternates: C81598 1N4148W (75 V: too low) |
| power | D19 | 1 | TVS 5.0SMDJ54A | D_SMC | bottom | C42394451 | 5.0SMDJ54A (R+O (listed as hongjiacheng)) | Extended | 9930 | 0.3948 | 9930 | yes | part chosen earlier (HANDOFF_SUMMARY / replace_notes / ANSWERS); Littelfuse has 1 in stock; R+O alternate (as decided 2026-09-15). Its listing gives the ratings but links no datasheet Alternates: C20415356 Littelfuse (stock 1); C5279851 SETsafe (published specs) |
| power | R1 | 1 | 1m CSS4J-4026R-1L00F | 4026 4-terminal | top | C2076400 | CSS4J-4026R-1L00F (Bourns) | Extended | 385 | 1.7072 | 385 | yes | your choice of 2026-09-24; rev6: 1 mOhm with U25 = INA241A4 (100 V/V): Current stays 0.1 V/A. Same Bourns land pattern (series drawing), H 2.70 max against 2.93 Alternates: C2076167 CSS4J-4026K-2L00F 2 mOhm (0 stock) |
| power | R7 R52 R53 | 3 | 50 mOhm WSL2512 | 2512 | top | C413486 | WSL2512R0500FEA (Vishay) | Extended | 41066 | 0.2346 | 13688 | yes | your choice of 2026-09-24; LED current sinks: 2.63 A, 0.35 W each. The value sets the LED current, so the TCR matters: WSL2512 metal strip +/-75 ppm/C ($0.23) against thick film +/-800 ppm/C ($0.04) Alternates: C127698 thick film +/-800 ppm/C |
| power | R13 R23 R47 | 3 | 220 | 0603 | bottom/top | C22962 | 0603WAF2200T5E (UNI-ROYAL) | Basic | 2009900 | 0.0034 | 287128 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| power | R14 | 1 | 1M | 0805 | top | C17514 | 0805W8F1004T5E (UNI-ROYAL) | Basic | 2496169 | 0.0043 | 1248084 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists; on LX (65 V peak): 150 V rated |
| power | R15 | 1 | 10 | 0805 | bottom | C17415 | 0805W8F100JT5E (UNI-ROYAL) | Basic | 7059587 | 0.004 | 7059587 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| power | R21 R48 R60 R72 | 4 | 5.1 | 0805 | bottom | C17724 | 0805W8F510KT5E (UNI-ROYAL) | Basic | 534124 | 0.0041 | 89020 | yes | your choice of 2026-09-24; rev6: 5 -> 5.1 Ohm (5.0 Ohm 0805 is not stocked), the value R59/R70 already use Alternates: C25273 4.99 Ohm |
| power | R22 R50 R56 | 3 | 100 | 0603 | top | C22775 | 0603WAF1000T5E (UNI-ROYAL) | Basic | 12437521 | 0.0031 | 4145840 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| power | R49 R61 R62 R73 R74 R75 R76 R104 | 8 | 10k | 0603 | bottom/top | C25804 | 0603WAF1002T5E (UNI-ROYAL) | Basic | 22979578 | 0.0018 | 999112 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| power | R59 R70 | 2 | 5.1 | 0805 | bottom/top | C17724 | 0805W8F510KT5E (UNI-ROYAL) | Basic | 534124 | 0.0041 | 89020 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| power | U1 U17 | 2 | L78L05 | SOT-89 | top | C43116 | L78L05ACUTR (STMicroelectronics) | Extended | 27095 | 0.1019 | 13547 | yes | the device named in the schematic or the notes; ST L78L05ACUTR (pinout OUT-GND-IN as the symbol) |
| power | U6 U11 U12 | 3 | MCP6241 | SOT-23-5 | top | C49889 | MCP6241T-E/OT (Microchip) | Extended | 38 | 0.6936 | 4 | LIMITS BUILD | the device named in the schematic or the notes; STOCK 38, shared with the card (9 per set) |
| power | U8 U10 U15 U19 | 4 | UCC21520DW | SOIC-16W | bottom | C601651 | UCC21520DWR (Texas Instruments) | Extended | 18240 | 0.8886 | 4560 | yes | the device named in the schematic or the notes |
| power | U16 | 1 | LM2940-12 | TO-263-3 | top | C2877347 | LM2940S-12/NOPB (Texas Instruments) | Extended | 2 | 4.5758 | 2 | LIMITS BUILD | the device named in the schematic or the notes; STOCK 2 (LM2940S-12): enough for 2 boards; the CS grade (7) covers 5 Alternates: C2865267 LM2940CS-12 (stock 7): same regulator, rated 0-125 C and 45 V / 1 ms transients (TI SNVS769J) |
| power | U25 | 1 | INA241A4 | SOIC-8 | top | C22427873 | INA241A4IDR (Texas Instruments) | Extended | 116 | 3.524 | 116 | yes | your choice of 2026-09-24; rev6: gain 100 V/V with the 1 mOhm R1; TI SBOSA30D: same SOIC-8 pinout for every gain, 1.1 MHz for all gains Alternates: C22427652 INA241A3IDR (rev5) |
| card | C8 C9 C17 C19 | 4 | 330pF | 0603 | bottom/top | C1664 | CL10C331JB8NNNC (Samsung) | Basic | 914234 | 0.0179 | 228558 | yes | timing / compensation / sample-and-hold: C0G |
| card | C10 C11 C13 | 3 | 4.7nF | 0603 | bottom/top | C85980 | GRM1885C1H472JA01D (Murata) | Extended | 103491 | 0.0278 | 34497 | yes | timing / compensation / sample-and-hold: C0G; on Verr1-3 Alternates: C53987 X7R Basic |
| card | C12 C22 C23 C24 C26 C28 C29 C32 C36 C37 C38 C42 C43 C46 C52 C53 C54 C58 C59 C63 C65 C66 C68 C92 C94 C95 C96 C97 C98 C99 C104 | 31 | 100nF | 0603 | bottom/top | C14663 | CC0603KRX7R9BB104 (YAGEO) | Basic | 51360098 | 0.0122 | 1194420 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V) |
| card | C14 | 1 | 220pF | 0603 | top | C27675 | CL10C221JB8NNNC (Samsung) | Extended | 74938 | 0.0095 | 74938 | yes | timing / compensation / sample-and-hold: C0G; Q1 emitter Alternates: C1603 X7R Basic |
| card | C15 | 1 | 100pF | 0603 | top | C14858 | CL10C101JB8NNNC (Samsung) | Basic | 4203127 | 0.0086 | 4203127 | yes | timing / compensation / sample-and-hold: C0G |
| card | C47 C93 C103 | 3 | 10uF | 0603 | bottom | C96446 | CL10A106MA8NRNC (Samsung) | Basic | 3577918 | 0.0541 | 1192639 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V); Vref_1-3 (5 V): 25 V X5R |
| card | C49 C64 C67 | 3 | 100nF | 1206 | bottom | C97946 | GRM31C5C1H104JA01L (Murata) | Extended | 97593 | 0.1847 | 32531 | yes | timing / compensation / sample-and-hold: C0G; sample-and-hold into the 4066 switches Alternates: C14663-class X7R |
| card | C57 C91 | 2 | 1uF | 0805 | bottom/top | C28323 | CL21B105KBFNNNE (Samsung) | Basic | 2568377 | 0.0398 | 321047 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V) |
| card | C100 C101 C102 | 3 | 1nF | 0603 | bottom/top | C1588 | CL10B102KB8NNNC (Samsung) | Basic | 8270810 | 0.0089 | 1378468 | yes | value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V); pot B-terminal filter |
| card | D1 D3 D4 D5 D6 D7 D15 D20 D24 D27 | 10 | 1N4148W (logic) | SOD-123 | bottom/top | C81598 | 1N4148W (ST (Semtech)) | Basic | 5264473 | 0.0123 | 526447 | yes | your choice of 2026-09-24; no diode type in the schematic (LTspice default silicon diode). Proposal 1N4148W (Basic), the closest real part to what was simulated |
| card | D23 D25 D26 | 3 | BAT54WS (Vref) | SOD-323 | bottom/top | C22629 | BAT54WS L9 (JSCJ (Changjing)) | Extended | 5522 | 0.0238 | 1840 | yes | your choice of 2026-09-24; no type in the schematic; the design notes show BAT54 on this path (Output -> .1Vref_n). Proposal BAT54WS Alternates: C124205 BAT54WS-7-F |
| card | Q1 | 1 | MMBT3906 | SOT-23 | bottom | C53444 | MMBT3906LT1G (onsemi) | Extended | 1010094 | 0.0189 | 1010094 | yes | your choice of 2026-09-24; no transistor type in the schematic (LTspice generic PNP). Proposal MMBT3906 Alternates: C2143 JSCJ MMBT3906 |
| card | R2 R6 R31 R33 R39 R41 R67 R77 R83 R85 R99 R100 R101 R102 R103 | 15 | 10k | 0603 | bottom/top | C25804 | 0603WAF1002T5E (UNI-ROYAL) | Basic | 22979578 | 0.0018 | 999112 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R3 R32 R40 | 3 | 620k | 0603 | bottom/top | C23219 | 0603WAF6203T5E (UNI-ROYAL) | Extended | 97659 | 0.002 | 32553 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R4 R54 R55 R58 R71 | 5 | 1k | 0603 | bottom/top | C21190 | 0603WAF1001T5E (UNI-ROYAL) | Basic | 23926464 | 0.0026 | 4785292 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R8 R34 R42 R51 R63 R78 R80 | 7 | 2k | 0603 | bottom/top | C22975 | 0603WAF2001T5E (UNI-ROYAL) | Basic | 14129032 | 0.0024 | 2018433 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R9 R35 R43 | 3 | 18k | 0805 | bottom/top | C17506 | 0805W8F1802T5E (UNI-ROYAL) | Extended (preferred) | 203916 | 0.0043 | 67972 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R11 R17 | 2 | 510k | 0603 | bottom | C23192 | 0603WAF5103T5E (UNI-ROYAL) | Basic | 940892 | 0.0024 | 470446 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R16 R19 | 2 | 5.1k | 0603 | bottom/top | C23186 | 0603WAF5101T5E (UNI-ROYAL) | Basic | 26217412 | 0.0015 | 13108706 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R18 R20 | 2 | 200k | 0603 | bottom | C25811 | 0603WAF2003T5E (UNI-ROYAL) | Basic | 2604608 | 0.0023 | 1302304 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R25 R87 R94 | 3 | 910k | 0805 | bottom/top | C17864 | 0805W8F9103T5E (UNI-ROYAL) | Extended | 16104 | 0.0034 | 5368 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists; Vout dividers: 150 V rated |
| card | R26 R64 R79 R81 | 4 | 220 | 0603 | bottom/top | C22962 | 0603WAF2200T5E (UNI-ROYAL) | Basic | 2009900 | 0.0034 | 287128 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R27 R37 R45 | 3 | 4.7k | 0603 | bottom/top | C23162 | 0603WAF4701T5E (UNI-ROYAL) | Basic | 23361029 | 0.0028 | 7787009 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R28 R36 R38 R44 R46 R88 R91 R95 R96 R105 | 10 | 100k | 0603 | bottom/top | C25803 | 0603WAF1003T5E (UNI-ROYAL) | Basic | 22875369 | 0.0031 | 2287536 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R29 R30 R57 | 3 | 22k | 0805 | top | C17560 | 0805W8F2202T5E (UNI-ROYAL) | Basic | 1810782 | 0.0048 | 603594 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R65 | 1 | 22k | 0603 | top | C31850 | 0603WAF2202T5E (UNI-ROYAL) | Basic | 3686199 | 0.0041 | 3686199 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R66 R89 R92 R97 | 4 | 3.3k | 0603 | bottom/top | C22978 | 0603WAF3301T5E (UNI-ROYAL) | Basic | 5489100 | 0.0026 | 1372275 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R68 | 1 | 62k | 0603 | top | C23221 | 0603WAF6202T5E (UNI-ROYAL) | Extended (preferred) | 440315 | 0.0028 | 440315 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R69 | 1 | 20k | 0603 | top | C4184 | 0603WAF2002T5E (UNI-ROYAL) | Basic | 8367518 | 0.0023 | 8367518 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R82 | 1 | 56k | 0603 | top | C23206 | 0603WAF5602T5E (UNI-ROYAL) | Basic | 1040364 | 0.0027 | 1040364 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R84 | 1 | 120k | 0603 | bottom | C25808 | 0603WAF1203T5E (UNI-ROYAL) | Basic | 1048781 | 0.0015 | 1048781 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R86 | 1 | 1M | 0805 | top | C17514 | 0805W8F1004T5E (UNI-ROYAL) | Basic | 2496169 | 0.0043 | 1248084 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | R90 R93 R98 | 3 | 10M | 0603 | bottom/top | C7250 | 0603WAF1005T5E (UNI-ROYAL) | Basic | 332804 | 0.0037 | 110934 | yes | value and package from the schematic; 1% thick film, JLC Basic where one exists |
| card | U2 U4 U5 U14 U21 | 5 | MCP6561 | SOT-23-5 | bottom/top | C117501 | MCP6561T-E/OT (Microchip) | Extended | 4522 | 0.7424 | 904 | yes | the device named in the schematic or the notes |
| card | U3 U7 U13 U22 U23 U24 | 6 | MCP6241 | SOT-23-5 | bottom/top | C49889 | MCP6241T-E/OT (Microchip) | Extended | 38 | 0.6936 | 4 | LIMITS BUILD | the device named in the schematic or the notes; STOCK 38, shared with the power board |
| card | U18 | 1 | CD4017B | SOIC-16 | top | C11349 | CD4017BM96 (Texas Instruments) | Extended | 18886 | 0.7424 | 18886 | yes | the device named in the schematic or the notes |
| card | U26 | 1 | MCP4451-103E/ST | TSSOP-20 | bottom | C145613 | MCP4451-103E/ST (Microchip) | Extended | 52 | 2.9173 | 52 | yes | part chosen earlier (HANDOFF_SUMMARY / replace_notes / ANSWERS); STOCK 52 |
| card | U28 | 1 | 74HC4051 | SOIC-16 | top | C9386 | 74HC4051D,653 (Nexperia) | Extended | 2364 | 0.2195 | 2364 | yes | the device named in the schematic or the notes |
| card | U101 U102 U103 | 3 | 74HC00 | SOIC-14 | top | C5586 | 74HC00D,653 (Nexperia) | Extended | 9058 | 0.1548 | 3019 | yes | the device named in the schematic or the notes |
| card | U104 U105 | 2 | 74HC14 | SOIC-14 | bottom/top | C5605 | 74HC14D,653 (Nexperia) | Basic | 214020 | 0.1022 | 107010 | yes | the device named in the schematic or the notes |
| card | U106 | 1 | CD74HC4066 | SOIC-14 | bottom | C179842 | CD74HC4066M96 (Texas Instruments) | Extended | 73 | 0.6092 | 73 | yes | the device named in the schematic or the notes; STOCK 73 |

## I fit (DNP in the JLC files; pads, holes and silk stay)

| Board | Refs | Qty | Value | Footprint | Side | LCSC | MPN (maker) | Basic/Ext | Stock | $/unit | Max sets | Orderable | Why / notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| power | J10 | 1 | ESQ-115-44-G-D | PinSocket 2x15 | top |  |  |  |  |  |  |  | the device named in the schematic or the notes; not stocked at LCSC (only the -LL variant is listed, 0 in stock, $23.28); buy from Samtec / Digi-Key / Mouser Alternates: C5689183 ESQ-115-44-G-D-LL (stock 0) |
| power | L1 | 1 | CSCF3218-6R8MC | 32 x 22.5 mm SMD | top |  |  |  |  |  |  |  | the device named in the schematic or the notes; the user owns it Alternates: C5629897 (stock 0) |
| power | M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 | 10 | HYG180N10 | TO-220 | bottom |  |  |  |  |  |  |  | the device named in the schematic or the notes; the user owns ten Alternates: C2841917 HYG180N10LS1P |
| card | J11 | 1 | TSW-115-07-G-D | PinHeader 2x15 | bottom |  |  |  |  |  |  |  | the device named in the schematic or the notes; LCSC lists it with 0 in stock; buy from Samtec / Digi-Key / Mouser Alternates: C5994596 (stock 0) |

## Unresolved (a decision is needed; the proposal is in the *_with_proposals files)

| Board | Refs | Qty | Value | Footprint | Side | LCSC | MPN (maker) | Basic/Ext | Stock | $/unit | Max sets | Orderable | Why / notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## No part to buy

| Board | Refs | Qty | Value | Footprint | Side | LCSC | MPN (maker) | Basic/Ext | Stock | $/unit | Max sets | Orderable | Why / notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| power | H5 H6 H7 H8 | 4 | mounting hole | M3 | top |  |  |  |  |  |  |  |  |
| power | J1 J2 | 2 | battery lug | M4 hole | top |  |  |  |  |  |  |  | cable lugs bolted through; no part on the BOM |
| power | J3 J4 J5 J6 J7 J8 | 6 | LED wire pad | THT pad 4 mm | top |  |  |  |  |  |  |  | wires soldered in |
| power | NT1 NT2 NT3 | 3 | net tie | - | top |  |  |  |  |  |  |  |  |
| card | H1 H2 H3 H4 | 4 | mounting hole | M3 | top |  |  |  |  |  |  |  |  |
| card | J9 | 1 | Arduino wire pads | 11 wire pads | top |  |  |  |  |  |  |  | wires soldered in (BUILD_NOTES J9 table) |

## Assembly quantities

| Board | Files | Unique parts | Basic | Extended | Placements | SMT pads | Components $/board (qty-1 prices) | Sides |
|---|---|---|---|---|---|---|---|---|
| power | JLC only | 27 | 12 | 15 | 97 | 279 | 55.35 | bottom + top |
| power | _with_proposals | 27 | 12 | 15 | 97 | 279 | 55.35 | bottom + top |
| card | JLC only | 41 | 25 | 16 | 160 | 472 | 14.82 | bottom + top |
| card | _with_proposals | 41 | 25 | 16 | 160 | 472 | 14.82 | bottom + top |
