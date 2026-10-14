"""Update the hand-written docs for the 6-layer power board (2026-10-02). Run from led-driver/ with system Python.

    python BOOST_split_boards/fab_2026-10-02/tools/update_docs.py

Edits BOOST_package/ORDER_CHECKLIST.md, BOOST_package/BUILD_NOTES.md and the README.md of the three folders in place
(each replacement must match exactly once).
"""
import io


def edit(path, reps):
    s = io.open(path, encoding='utf-8', newline='').read()
    if '\r\n' in s:                       # the docs are CRLF: match and write in the file's own line endings
        reps = [(a.replace('\n', '\r\n'), b.replace('\n', '\r\n')) for a, b in reps]
    for a, b in reps:
        n = s.count(a)
        assert n == 1, '%s: %d matches for %r' % (path, n, a[:70])
        s = s.replace(a, b)
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    print('edited', path, len(reps))


OC = 'BOOST_package/ORDER_CHECKLIST.md'
edit(OC, [
    ('# BOOST order checklist, scenario A (updated 2026-10-01)',
     '# BOOST order checklist, scenario A (updated 2026-10-02)'),
    ('**Total $655.14 with the McMaster pad**', '**Total $600.61 with the McMaster pad**'),
    ('- the control card is 6 layers with 0.5 oz inner copper ($56.83 instead of $137.04);\n',
     '- the control card is 6 layers with 0.5 oz inner copper ($56.83 instead of $137.04);\n'
     '- the power board is 6 layers on the stackup JLC061611-7628D ($69.57 instead of $124.10), with your GND and\n'
     '  gate-drive rework of 2026-10-02 (`BOOST_split_boards/power6_2026-10-01/README.md`);\n'),
    ('the 8-layer power board and the\n      6-layer card, all in `BOOST_package/KiCad/`.',
     'the 6-layer power board (2026-10-02) and\n      the 6-layer card, all in `BOOST_package/KiCad/`.'),
    ('- [ ] Optional: read the TG-AD30 price',
     '- [ ] **Power board stackup:** on the quote page set "Specify Stackup: Yes" and pick **JLC061611-7628D**. If JLC\n'
     '      reminds you that its real thickness is 1.583 mm rather than 1.6 mm, accept it (Yes). The loop-inductance,\n'
     '      current and U16 temperature checks all assume this stackup; the fab drawing says the same.\n'
     '- [ ] After the Gerber upload, look at JLC\'s free DFM check for both boards before paying.\n'
     '- [ ] Optional: read the TG-AD30 price'),
    ('| Base material, layers | FR-4, **8** |', '| Base material, layers | FR-4, **6** |'),
    ('| Thickness, material | 1.6 mm, FR4 TG155 |',
     '| Thickness, material | 1.6 mm, **FR4 TG155** (6 layers default to TG135: change it) |'),
    ('| Surface finish | **ENIG** (8 layers default to OSP: change it) |',
     '| Surface finish | **ENIG** (6 layers default to OSP: change it) |'),
    ('| Specify stackup | No |',
     '| **Specify stackup** | **Yes: JLC061611-7628D** (1.583 mm; accept the thickness reminder) |'),
    ('| **Via covering** | **Epoxy Filled & Capped** (the 8-layer default, $0.00) |',
     '| **Via covering** | **Epoxy Filled & Capped** (free at 6 layers, $0.00) |'),
    ('PCBs $124.10 + assembly about $204.79 = **$328.89**.',
     'PCBs $69.57 + assembly about $204.79 = **$274.36**. The standard build time is 8-9 days.'),
    ('| Layers | **6** (the stackup in the fab drawing is JLC\'s standard 6-layer 1.6 mm build for 1 oz outer / 0.5 oz inner, 1.547 mm) |',
     '| Layers | **6** (the stackup in the fab drawing is JLC\'s standard 6-layer 1.6 mm build for 1 oz outer / 0.5 oz inner, 1.547 mm) |\n'
     '| Specify stackup | **No** (the card uses JLC\'s standard build; only the power board names one) |'),
    ('| $548.18 | $24.62 | $0.29 | $55.61 | $12.64 | $13.80 | **$655.14** + shipping + tax |',
     '| $493.65 | $24.62 | $0.29 | $55.61 | $12.64 | $13.80 | **$600.61** + shipping + tax |'),
    ('instead of the McMaster pad: **$756.98**.', 'instead of the McMaster pad: **$702.45**.'),
    ('- t-Global TG-AD30 1.5 mm instead: $628.23 plus its price.',
     '- t-Global TG-AD30 1.5 mm instead: $573.70 plus its price.'),
])

BN = 'BOOST_package/BUILD_NOTES.md'
edit(BN, [
    ('- Power board: 8 layers, 1.6 mm nominal (JLCPCB stackup 1 oz outer / 1 oz inner, 1.654 mm copper + dielectric),\n'
     '  written into the board file.',
     '- Power board: 6 layers since 2026-10-02, on JLCPCB\'s stackup **JLC061611-7628D** (1 oz outer / 1 oz inner,\n'
     '  1.583 mm copper + dielectric; it must be specified at order), written into the board file. In1 is the GND plane;\n'
     '  5 V runs as tracks (`BOOST_split_boards/power6_2026-10-01/README.md`).'),
    ('## Clearances measured in the 3D model (2026-09-24)\n\n'
     'Full table in `assembly_3d_2026-09-24/CLEARANCES.md`.',
     '## Clearances measured in the 3D model (2026-10-02)\n\n'
     'Full table in `CLEARANCES.md` (this folder; built in `BOOST_split_boards/assembly_3d_2026-09-30/`).'),
    ('- Lid to the card screw heads 0.65 mm, and to the SOIC-16 packages on the card top (U18, U28) 0.98 mm. The model uses\n'
     '  the board files\' 1.654 mm thickness, 0.054 mm more than the nominal 1.6; nominal gives 0.70 and 1.03.',
     '- Lid to the card screw heads 0.77 mm, and to the SOIC-16 packages on the card top (U18, U28) 1.11 mm. The model uses\n'
     '  the board files\' thicknesses (power 1.583 mm, card 1.547 mm); the fab tolerance is +/-10 %.'),
    ('(closest: 2.80 mm under U104 / U106 on the card)', '(closest: 2.85 mm under U104 / U106 on the card)'),
])

for f in ('BOOST_package', 'BOOST_schematic_cleanup', 'BOOST_stuff'):
    edit(f + '/README.md', [
        ('| Power board | `KiCad/BOOST_power_RC2.kicad_pcb` | 74 x 86 mm (18 x 12 mm corner notch) | 8 |',
         '| Power board | `KiCad/BOOST_power_RC2.kicad_pcb` | 74 x 86 mm (18 x 12 mm corner notch) | 6 (stackup '
         'JLC061611-7628D, specified at order) |'),
    ])
