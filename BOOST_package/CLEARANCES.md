# BOOST assembly: clearances and substitutions (2026-09-25)

From `tools/build_assembly.py`: the two release-candidate boards (KiCad STEP export) in the case, with every part that has no 3D model replaced by a dimensioned solid. Distances are exact solid-to-solid minimums (OpenCASCADE BRepExtrema), in mm. **Under 1 mm is flagged.**

## Stack used (height above the case floor, mm)

| Item | Z |
|---|---|
| Thermal pad top = FET tab | 0.93 |
| Power board underside (5.0 stud + 0.5 washer) | 5.50 |
| Power board top as modelled (board files: 1.654 thick) | 7.154 |
| Female-female standoff, on the nominal 1.6 mm board | 7.10 - 27.10 |
| J10 ESQ body top | 25.824 |
| J11 TSW insulator underside | 26.06 |
| Control card underside (+1.5 mm of washers) | 28.60 |
| Control card top as modelled | 30.254 |
| Lid underside | 33.00 |

The boards are modelled 1.654 mm thick (copper + dielectric from the board files); the stack uses the nominal 1.6. So everything on the power board sits 0.054 mm higher than nominal and the card top 0.054 mm higher: the clearances to the card and the lid are pessimistic by that much.

## Clearance table

### Card to tall power part

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| C77 | card U106 | 3.10 |  | part top 23.67 |
| C78 | card U104 | 3.10 |  | part top 23.67 |
| C87 | card U104 | 3.10 |  | part top 23.67 |
| C70 | card C64 | 3.25 |  | part top 23.67 |
| C88 | card J11 post | 3.67 |  | part top 23.67 |
| C74 | card C67 | 4.07 |  | part top 23.67 |
| C75 | card C67 | 4.73 |  | part top 23.67 |
| C71 | card BOOST_control_RC2_PCB | 6.59 |  | part top 23.67 |
| C40 | card D7 | 7.59 |  | part top 19.67 |
| L1 CSCF3218-6R8MC body 22.5 x 32.0 x 19.0 | card BOOST_control_RC2_PCB | 7.82 |  | part top 26.15 |
| M8 | card J11 post | 7.96 |  | part top 13.55 |
| C85 | card D7 | 9.18 |  | part top 19.67 |
| M2 | card J11 post | 10.86 |  | part top 13.55 |
| M10 | card J9 cable-tie head (5.0 x 4.5 x 3.5 ASSUMED) | 11.62 |  | part top 13.55 |
| C86 | card BOOST_control_RC2_PCB | 13.09 |  | part top 23.67 |
| M5 | card U106 | 13.22 |  | part top 13.55 |
| M9 | card J9 cable-tie head (5.0 x 4.5 x 3.5 ASSUMED) | 14.48 |  | part top 13.55 |
| M4 | card U106 | 14.49 |  | part top 13.55 |
| M6 | card C97 | 15.18 |  | part top 13.55 |
| M7 | card J11 post | 15.54 |  | part top 13.55 |
| M3 | card BOOST_control_RC2_PCB | 15.86 |  | part top 13.55 |
| C69 | card BOOST_control_RC2_PCB | 18.62 |  | part top 19.67 |
| M1 | card BOOST_control_RC2_PCB | 24.21 |  | part top 13.55 |

### Vent clearance above can (max height)

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| C77 EEH-ZU1H221P 16.8 max | card U106 | 2.80 |  |  |
| C78 EEH-ZU1H221P 16.8 max | card U104 | 2.80 |  |  |
| C87 EEH-ZU1H221P 16.8 max | card U104 | 2.80 |  |  |
| C70 EEH-ZU1H221P 16.8 max | card C64 | 2.95 |  |  |
| C75 EEH-ZU1H221P 16.8 max | hardware H8 female-female HNSM3-20-5.5-1 (hex 5.5 AF x 20) | 2.99 |  |  |
| C40 EEH-ZU1E681UP 12.8 max | hardware H6 female-female HNSM3-20-5.5-1 (hex 5.5 AF x 20) | 3.20 |  |  |
| C88 EEH-ZU1H221P 16.8 max | card J11 Samtec TSW-115-07-G-D insulator (2.54) | 3.29 |  |  |
| C74 EEH-ZU1H221P 16.8 max | card C67 | 3.55 |  |  |
| C71 EEH-ZU1H221P 16.8 max | card BOOST_control_RC2_PCB | 6.07 |  |  |
| C85 EEH-ZU1E681UP 12.8 max | card D7 | 8.68 |  |  |
| C69 EEH-ZU1E681UP 12.8 max | hardware M1 tab screw McMaster 92000A107 M2.5 x 12 pan head (5.0 x 2.1) | 10.92 |  |  |
| C86 EEH-ZU1H221P 16.8 max | card BOOST_control_RC2_PCB | 12.74 |  |  |

### Card outline to L1 body, in plan

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| card board | L1 | 7.42 |  | positive = not overlapping |

### Card to L1, 3D

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| L1 body | card BOOST_control_RC2_PCB | 7.82 |  |  |

### J9 wire exit

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| J9 wires (11 x 26-28 AWG, bundle 1.5 mm deep ASSUMED) | hardware H7 washers 3 x TR NWE-34815-M3 | 1.39 |  |  |
| J9 cable-tie head (5.0 x 4.5 x 3.5 ASSUMED) | C87 EEH-ZU1H221P 16.8 max | 3.68 |  |  |

### Lid (33.0) to

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| H8 card screw 97790803211 head (5.5 x 2.1) | lid underside | 0.65 | **UNDER 1 mm** |  |
| H7 card screw 97790803211 head (5.5 x 2.1) | lid underside | 0.65 | **UNDER 1 mm** |  |
| H6 card screw 97790803211 head (5.5 x 2.1) | lid underside | 0.65 | **UNDER 1 mm** |  |
| H5 card screw 97790803211 head (5.5 x 2.1) | lid underside | 0.65 | **UNDER 1 mm** |  |
| U28 | lid underside | 0.98 | **UNDER 1 mm** |  |
| U18 | lid underside | 0.98 | **UNDER 1 mm** |  |

### Standoff stack to nearest part

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| H5 (with H1 on the card) | card D6 | 0.40 | **UNDER 1 mm** |  |
| H6 (with H2 on the card) | card R94 | 0.43 | **UNDER 1 mm** |  |
| H7 (with H3 on the card) | card D3 | 0.61 | **UNDER 1 mm** |  |
| H8 (with H4 on the card) | card R84 | 0.73 | **UNDER 1 mm** |  |

### Screwdriver access (r 4.0 above the head, to the lid)

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M1 | C69 EEH-ZU1E681UP 12.8 max | 0.70 | **UNDER 1 mm** | touching = 0.00 |

### Screwdriver access, power-board parts only

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M1 | C69 EEH-ZU1E681UP 12.8 max | 0.70 | **UNDER 1 mm** | the 4.0 mm / 3 mm rule |

### Screwdriver access blocked by the card?

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M1 | card board | 17.81 |  | card clear of the access cylinder |

### Screwdriver access (r 4.0 above the head, to the lid)

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M8 | card U101 | 0.00 | **UNDER 1 mm** | touching = 0.00 |

### Screwdriver access, power-board parts only

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M8 | power C87 | 1.80 |  | the 4.0 mm / 3 mm rule |

### Screwdriver access blocked by the card?

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M8 | card board | 0.00 | **UNDER 1 mm** | card over the screw: fit this screw before the card |

### Screwdriver access (r 4.0 above the head, to the lid)

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M9 | power C71 | 0.70 | **UNDER 1 mm** | touching = 0.00 |

### Screwdriver access, power-board parts only

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M9 | power C71 | 0.70 | **UNDER 1 mm** | the 4.0 mm / 3 mm rule |

### Screwdriver access blocked by the card?

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M9 | card board | 3.22 |  | card clear of the access cylinder |

### Screwdriver access (r 4.0 above the head, to the lid)

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M10 | card J9 wires (11 x 26-28 AWG, bundle 1.5 mm deep ASSUMED) | 0.39 | **UNDER 1 mm** | touching = 0.00 |

### Screwdriver access, power-board parts only

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M10 | power M9 | 7.15 |  | the 4.0 mm / 3 mm rule |

### Screwdriver access blocked by the card?

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| M10 | card board | 6.39 |  | card clear of the access cylinder |

### Penetrator keep-out

| Item | Nearest | mm | Flag | Note |
|---|---|---|---|---|
| penetrator keep-out box (118.5, 3.5), 15 x 10 | power BOOST_power_RC2_PCB | 3.00 |  |  |
| penetrator keep-out box (9.5, 3.5), 15 x 10 | nothing within 25 mm (the Arduino, CAN module and LED are not modelled) | 25.00 |  |  |

## What was substituted, and from which source

| Item | Source |
|---|---|
| Standoff stack H5-H8 / H1-H4 | BUILD_NOTES: Essentra HTSN-M3-5-3 (5 mm body, 6 mm hex), TR NWE-34815-M3 washers 0.50 mm, Essentra HNSM3-20-5.5-1 (20 mm, 5.5 mm hex), Wurth 97790803211 (head 2.1 x 5.5). Washer OD 7.0 / ID 3.2 from the Farnell / Newark listing (which gives 0.51 mm thick; the stack uses the notes 0.50). Stud thread length ASSUMED 5 mm |
| Thermal pads | BUILD_NOTES: Parker Chomerics THERM-A-GAP G579 0.050 in, cut ~10 x 16 mm, 3.0 mm hole at the screwed FETs, 0.93 mm compressed. Centred on the FET body (Fab outline), long side along the body |
| FET tab screws M1/M8/M9/M10 | BUILD_NOTES 2026-09-25: McMaster 92000A107 M2.5 x 12 pan head, head 5.0 x 2.1 (mcmaster.com); McMaster 93657A200 nylon spacer 2.0 mm long, 4.5 mm OD (mcmaster.com), 0.25 mm short of the tab-washer stack by design; Aavid 7721-7PPSG flange 1.02 mm (OD ASSUMED 6.35) |
| L1 CSCF3218-6R8MC | notes (Codaca): body 32.0 x 22.5 x 19.0 mm, placed on its footprint's Fab outline; the two J-lead terminals drawn as 3 mm blocks over their pads (terminal height ASSUMED) |
| R1 CSS4J-4026R-1L00F (rev6) | Bourns CSS4J-4026 datasheet: the 1 mOhm R version is 2.70 mm max (the 2 mOhm K version of rev5 was 2.93); plan from the footprint's Fab outline |
| J10 / J11 mated pair | notes (Samtec F-218 / F-219): ESQ -44 body 18.67 mm, TSW -07 insulator 2.54, post 5.84, tail 2.54; plan envelope 5.08 x 38.10 ASSUMED from the 2.54 mm pitch (2 x 15), not from the Samtec drawing |
| J9 wire exit | BUILD_NOTES: 11 wires 26-28 AWG in from the card underside, along the underside to the west edge, one cable tie through the two slots, head on the underside. Bundle depth 1.5 mm and tie head 5.0 x 4.5 x 3.5 ASSUMED |
| Case and lid | notes: inside 128 x 90 x 33 mm, 10 mm floor, lid underside at 33.0; wall and lid thickness 3 mm ASSUMED (not in the notes); penetrators at box (9.5, 3.5) and (118.5, 3.5) with 15 mm x 10 mm keep-outs |
| Can heights for the clearance checks | JLC/LCSC listings of 2026-09-24: EEH-ZU1H221P seated height 16.8 mm max (the KiCad model is 16.45); EEH-ZU1E681UP 12.5 max listed, package D10 x 12.8, 12.8 used. Diameter 10.0 |

Also substituted: the KiCad generic 2x15 socket/header models on J10 and J11 were removed (they are 8.5 mm parts, not the Samtec pair). Everything else is the KiCad library model on its footprint. R1 and L1 had no model. J1-J8 and J9 are wire pads (no part), and H1-H8 are holes.

