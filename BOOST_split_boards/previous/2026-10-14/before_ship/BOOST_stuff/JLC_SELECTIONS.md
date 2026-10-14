# JLCPCB order selections

There are two orders on jlcpcb.com, one per board. Each is 5 bare PCBs, 2 of which are assembled by JLCPCB. The
files to upload are in this folder.

## Power board

| Option | Selection |
|---|---|
| Gerber file | `BOOST_power_RC2_gerbers.zip` |
| Base material, layers | FR-4, 6 |
| Dimensions, quantity | 74 x 86 mm, 5, single PCB |
| Product type | Industrial/Consumer electronics |
| Thickness, material | 1.6 mm, FR4 TG155 |
| Colour, silkscreen | Green, white |
| Surface finish | ENIG |
| Outer / inner copper | 1 oz / 1 oz |
| Specify stackup | Yes: **JLC061611-7628D** (1.583 mm; accept JLC's thickness reminder) |
| Via covering | Epoxy Filled & Capped |
| Min via hole / diameter | 0.3 mm / (0.4 / 0.45 mm) |
| Board outline tolerance | +/-0.2 mm (Regular) |
| Mark on PCB | Remove Mark |
| Electrical test | Flying Probe Fully Test |
| Gold fingers, castellated holes, edge plating | No |
| PCB assembly | Standard PCBA, both sides, quantity 2 |
| BOM / CPL | `BOOST_power_BOM_JLC.csv` / `BOOST_power_CPL_JLC.csv` |
| Not placed by JLC (fitted by hand) | M1-M10 (TO-220 FETs), L1 (inductor), J10 (Samtec socket) |

Price: PCBs $69.57 + assembly about $203.17 = **$272.74**.

Why these choices:
- **The named stackup:** the switching-loop inductance and the current checks were worked out for its layer
  spacing. The fab drawing repeats it.
- **1 oz inner copper:** the inner layers carry the input, switch-node and output currents.
- **Filled and capped vias:** 461 of the 972 vias sit in SMD pads.

## Control card

The same as the power board, except:

| Option | Selection |
|---|---|
| Gerber file | `BOOST_control_RC2_gerbers.zip` |
| Dimensions | 45 x 45 mm |
| Inner copper | 0.5 oz |
| Specify stackup | No (JLC's standard 6-layer 1 / 0.5 oz build, 1.547 mm) |
| Delivery format | Panel by JLCPCB: 1 column, 1 row, 12.5 mm edge rails on all four sides (a 70 x 70 mm panel, because Standard PCBA needs at least 70 x 70 mm) |
| Quantity | 5 panels |
| BOM / CPL | `BOOST_control_BOM_JLC.csv` / `BOOST_control_CPL_JLC.csv` (single-card coordinates) |
| Not placed by JLC | J11 (Samtec header). J9 is wire pads and H1-H4 are mounting holes. |

Price: PCBs $56.83 + assembly about $162.46 = **$219.29**.

## After uploading
- Look at JLC's DFM report for both boards.
- In the placement preview, check:
  - the polarity of the electrolytic caps and the diodes, including D28-D30 on the power board's underside;
  - pin 1 of every IC;
  - that U16's tab (MC7812, which JLC lists as TO-263-2) sits on its large pad;
  - on the card, that the parts land on the panelled card.

## Bought elsewhere
The Samtec J10/J11 pair, a PTC fuse, the thermal pad and the mounting hardware come to $106.96 (see the "Bought
elsewhere" sheet of `BOOST_BOM.xlsx`).

**The total is $598.99** before shipping and tax. That covers two complete sets and three spare bare boards of each
kind.
