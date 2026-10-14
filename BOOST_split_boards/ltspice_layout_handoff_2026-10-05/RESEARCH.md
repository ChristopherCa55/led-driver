# Where the rules come from

These are the published guidance and manufacturer examples behind LAYOUT_RULES.md. For each practice the table says
where it applies in BOOST and which readability problem it solves. All sources were read on 2026-10-05.

**What I could not read:** ANSI Y14.15 and IEEE 315 are cited by others but were not read directly, so nothing here
relies on them. For IPC-2612, only its scope (the ANSI preview) was read.

| # | Source | Practice | Where in BOOST | Problem it solves |
|---|---|---|---|---|
| 1 | P. Horowitz & W. Hill, *The Art of Electronics*, 2nd ed., Cambridge University Press 1989, App. E "How to Draw Schematic Diagrams" (App. B in the 3rd ed.). Read via the reproduction at xcircuit.sourceforge.net/goodschem/goodschem.html | Keep functional areas distinct and don't fill the page. Signals flow left to right; positive supplies at the top. Keep each symbol's label and value together with it. Leave room around parts for labels. No four wires meeting at a point. Draw the same device the same way every time | Large framed blocks; left-to-right channel rows; the spacing rule (H9); identical channel copies (H10); no 4-way junctions (H8) | The original is crammed, with overlapping text. The last attempt drew the same kind of circuit differently in each place |
| 2 | Linear Technology, *LTspice IV User Guide*, pp. 18–21, 35, 186 (Columbia University mirror); **and the LTspice 26 help shipped with the program** (`C:\Program Files\ADI\LTspice\LTspiceHelp`: *Label a Node Name*, *Basic Schematic Editing*, *Drafting Options*) | A wire drawn through a component is cut so the part is in series. Each node has one name. **Port types (input, output, bidirectional) "will be drawn differently but have no significance to the netlister"; indicating them "can make circuit more readable."** Rectangles and lines are graphics only. "Mark unconnected pins". Hierarchy exists for repeated circuits | Port-typed exit labels vs plain supply labels (H6, H7); dashed frames for blocks; the hidden-connection rule (H8); no hierarchy, because it would rename the `.ic`/`.meas` nodes | Every label looked the same, so a reader could not tell a supply from a signal they must follow. Wires laid across pins create connections nobody sees |
| 3 | Analog Devices, LT3797 triple-output LED driver: application circuit on the product page (analog.com/en/products/lt3797.html, image `lt3797-acl.png`) | Three identical boost channels side by side under one VIN rail. Each controller pin sits directly under the channel it drives. The LED string is drawn in series inside its channel. Bypass caps are drawn at the pins they serve | Power spine across the top with each gate driver directly under its FETs (short gate wires, H6); the LED load drawn inline in CREG; bypass caps at their IC's pin (H12) | Gate and sense signals jumped across the sheet through labels; the LED current path was broken into label pieces |
| 4 | Analog Devices example schematics shipped with LTspice (`examples.zip`, scanned 2026-10-05): `LTC3884-1.asc` marks SW1/SW2 as `IOPIN Out`, ISNS1/2 as `BiDir` and OUT1/2 as `In`. 192 `RECTANGLE` drawings appear across the examples (e.g. `AD4080.asc`), mostly with line style 2 | A manufacturer uses port-typed labels and drawn rectangles in LTspice itself. I checked the syntax, not each example's purpose | The `.asc` syntax in LAYOUT_RULES.md §5 | Shows these are native LTspice features, not inventions |
| 5 | I. McNally, "Drawing Circuit Schematics", University of Southampton (2003), southampton.ac.uk/~bim/notes/cad/guides/schematics.html | Left-to-right flow, with arrows where it must reverse. Same-name labels connect, so use them to avoid spaghetti, but readability is the goal. Don't rely only on the CAD tool's checks | The label budget (H4, H6) and tracing tasks (T1–T10). The rule that passing the checker is necessary, not sufficient | The last attempt satisfied its own checks and produced something harder to read |
| 6 | Microchip, hardware design guidelines, "Decoupling Capacitors" (onlinedocs.microchip.com) | Place decoupling capacitors as close to the supply pins as possible, first in the power path to the pin | Each bypass cap drawn at its owner's supply pin (H12); ownership taken from the real PCB pad positions | It was invisible which of 39 caps served which IC |
| 7 | IPC-2612 (2010), *Sectional Requirements for Electronic Diagramming Documentation*: scope only (ANSI webstore preview) | Schematics document circuit flow and use consistent naming | Block titles naming the function and the board; channel names kept consistent | — (cited for scope only) |

**How the guidance was adapted to LTspice:**

- **No hierarchy.** LTspice's hierarchical blocks would handle the three channels neatly, but they rename internal
  nodes. That breaks `.ic V(SRV1)`, `V(Vref_1)` and the `.meas` lines. So the channels are drawn flat as three
  identical copies, and H10 enforces sameness.
- **Port labels instead of off-sheet connectors.** Everything is on one sheet, so the "off-page connector"
  convention becomes port-typed flags at block edges, and adjacent blocks are joined by real wires.
- **The bypass group for logic gates.** LTspice draws the 74HC00/74HC14 gates (U101–U105) without supply pins, and
  U18 gets 5 V by net name. Their caps cannot sit at a pin, so they form one labeled bank in the control block. This
  mirrors the separate power units in the KiCad symbols.
- **Simulation-only parts are inline, framed and noted**, at the user's request. It is like a manufacturer's test
  circuit drawing its load in place. The dashed frame keeps it obvious that they are not on the PCB.
