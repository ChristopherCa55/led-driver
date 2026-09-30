"""Add the three pre-charge diodes D28-D30 (S2MW, Vin -> Vout_1/2/3) to BOOST.kicad_sch, in place.

    python add_precharge_sch.py PATH\\TO\\BOOST.kicad_sch

Plain text edit (no KiCad needed). Refuses to run if D28, D29 or D30 already exist or if the file is not the
expected KiCad 10 schematic. Each diode uses the project's own "ltspice:diode" symbol (pin 2 = "+" = anode at the
symbol origin + (1.27, 0); pin 1 = "-" = cathode at + (1.27, 5.08)) and connects through global labels placed exactly on
the pin ends: "Vin" on the anode, "Vout_n" on the cathode. They sit in the empty area at the top right of the C-size
sheet (x 505-535 mm, y 35-52 mm). The UUIDs are fixed so the board script can link the footprints to these symbols.
"""
import sys, re

SCH = sys.argv[1]
ROOT = 'dc4aa17e-0995-4bac-889e-471ae16ef44e'          # the schematic's own uuid (instances path)
DATASHEET = 'https://www.lcsc.com/datasheet/lcsc_datasheet_1810121033_Shandong-Jingdao-Microelectronics-S2MW_C128729.pdf'
Y = 40.64
DIODES = [  # ref, cathode net, symbol x, symbol uuid, pin1 uuid, pin2 uuid, Vin label uuid, Vout label uuid
    ('D28', 'Vout_1', 506.73, 'c399746a-53eb-4c48-a735-e8265130f622', '7e41245f-cb10-42f5-9da4-a2cc122f95ec',
     '2613c396-abe2-40fa-92ba-246524ba92f1', '6d2b29fb-e94d-4bd1-8429-ee72f5efd2e1', '8073aea7-1c95-4a52-b357-e162af37e8a2'),
    ('D29', 'Vout_2', 519.43, 'ad541492-5975-4a76-baf7-2fb8e76d43fb', '2a56e77a-9556-469c-a881-5db038cdc167',
     'edf6ad36-dda8-4332-9bc9-86eb16ab1dc6', '150084de-8ea1-45f4-ab93-5577ef15846d', '83f2955c-01dc-4a74-9047-8557bd8333be'),
    ('D30', 'Vout_3', 532.13, '68d2cdfe-4062-478b-951b-a3c5578ea96a', '865cc67f-c457-4daa-9124-925347a3c1dc',
     '89468a8b-b695-42c3-804b-7fe782d027a0', 'dbd267d7-d807-42af-9911-b01a0c853805', '584f0d72-0ac6-46c8-8ed9-0adbfe85e884'),
]


def f(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def prop(name, value, x, y, hide, size='1.27', justify=None):
    j = '\n\t\t\t\t(justify %s)' % justify if justify else ''
    h = '\n\t\t\t(hide yes)' if hide else ''
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)%s\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
            '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size %s %s)\n\t\t\t\t)%s\n\t\t\t)\n\t\t)\n'
            % (name, value, f(x), f(y), h, size, size, j))


def symbol(ref, vout, x, su, p1, p2):
    desc = 'Pre-charge diode Vin -> %s (Jingdao S2MW, 1000 V 2 A, IFSM 50 A); conducts only while %s is below Vin' % (vout, vout)
    s = ('\t(symbol\n\t\t(lib_id "ltspice:diode")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 0)\n'
         '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n'
         '\t\t(uuid "%s")\n' % (f(x), f(Y), su))
    s += prop('Reference', ref, x + 1.905, Y + 1.27, False, '1.0668', 'left')
    s += prop('Value', 'S2MW', x + 1.905, Y + 3.81, False, '1.0668', 'left')
    s += prop('Footprint', 'Diode_SMD:D_SOD-123F', x, Y, True)
    s += prop('Datasheet', DATASHEET, x, Y, True)
    s += prop('Description', desc, x, Y, True)
    s += prop('Sim.Device', 'SPICE', x, Y, True)
    s += prop('Sim.Params', 'model=\\"S2MW\\"', x, Y, True)
    s += prop('MPN', 'S2MW', x, Y, True)
    s += prop('LCSC', 'C128729', x, Y, True)
    s += ('\t\t(pin "2"\n\t\t\t(uuid "%s")\n\t\t)\n\t\t(pin "1"\n\t\t\t(uuid "%s")\n\t\t)\n' % (p2, p1))
    s += ('\t\t(instances\n\t\t\t(project "BOOST"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n'
          '\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n' % (ROOT, ref))
    return s


def label(net, x, y, rot, justify, u):
    return ('\t(global_label "%s"\n\t\t(shape bidirectional)\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n'
            '\t\t\t\t(size 1.0668 1.0668)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n'
            '\t\t(property "Intersheetrefs" "${INTERSHEET_REFS}"\n\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n'
            '\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n'
            '\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n'
            % (net, f(x), f(y), rot, justify, u, f(x), f(y)))


raw = open(SCH, encoding='utf-8', newline='').read()
CRLF = '\r\n' in raw                        # the shipped file uses CRLF line ends; keep whatever it has
txt = raw.replace('\r\n', '\n')
assert txt.startswith('(kicad_sch') and '(uuid "%s")' % ROOT in txt[:400], 'not the expected BOOST schematic'
assert '\t\t(symbol "ltspice:diode"\n' in txt, 'lib symbol ltspice:diode missing'
for ref, *_ in DIODES:
    assert '(reference "%s")' % ref not in txt, '%s already exists - nothing changed' % ref
for *_, su, p1, p2, lv, lo in DIODES:
    for u in (su, p1, p2, lv, lo):
        assert u not in txt, 'uuid %s already in the file - nothing changed' % u
new = ''
for ref, vout, x, su, p1, p2, lv, lo in DIODES:
    px = x + 1.27
    new += label('Vin', px, Y, 90, 'left', lv)
    new += label(vout, px, Y + 5.08, 270, 'right', lo)
for ref, vout, x, su, p1, p2, lv, lo in DIODES:
    new += symbol(ref, vout, x, su, p1, p2)
anchor = '\t(sheet_instances\n'
assert txt.count(anchor) == 1
txt = txt.replace(anchor, new + anchor)
open(SCH, 'w', encoding='utf-8', newline='').write(txt.replace('\n', '\r\n') if CRLF else txt)
print('added D28, D29, D30 and six global labels to', SCH)
for ref, vout, x, *_ in DIODES:
    print('  %s at (%s, %s): anode pin (%s, %s) = Vin, cathode pin (%s, %s) = %s'
          % (ref, f(x), f(Y), f(x + 1.27), f(Y), f(x + 1.27), f(Y + 5.08), vout))
