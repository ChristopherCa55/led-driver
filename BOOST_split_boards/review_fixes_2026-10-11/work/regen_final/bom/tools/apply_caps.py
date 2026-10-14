"""Apply the approved 220 uF output-cap change (2026-10-01) to one BOOST folder.

    python apply_caps.py FOLDER          (FOLDER holds KiCad/BOOST.kicad_sch and LTspice/BOOST.asc)

C70, C71, C75, C77, C78, C88 -> Panasonic EEH-ZS1H221P (LCSC C385885); C74, C86, C87 stay EEH-ZU1H221P.
- KiCad: the MPN field of those six symbols changes. Nothing else.
- LTspice: their SpiceLine changes from the ZU figures (Irms 4.5 A, Rser 10 mOhm) to the ZS ones: Rser 13 mOhm
  (Panasonic ZS data sheet, 100 kHz / 20 C) and Irms 3.2 A (the ZU's 4.5 A working figure scaled by the data-sheet
  ratings, 3.7 / 5.2). Irms is informational in LTspice; Rser changes the simulation.
Line endings and encodings are kept (the .kicad_sch is UTF-8, the .asc latin-1).
"""
import re, sys, os

ZS = ['C70', 'C71', 'C75', 'C77', 'C78', 'C88']
folder = sys.argv[1]

# ---- KiCad ----
p = os.path.join(folder, 'KiCad', 'BOOST.kicad_sch')
raw = open(p, 'rb').read()
s = raw.decode('utf-8')
n = 0
for ref in ZS:
    i = s.find('(property "Reference" "%s"' % ref)
    assert i > 0, ref
    a = s.rfind('\t(symbol', 0, i)
    b = s.find('(property "MPN" "EEH-ZU1H221P"', a)
    assert a < b < s.find('(property "Reference"', i + 10), ('MPN not in the symbol block', ref)
    s = s[:b] + '(property "MPN" "EEH-ZS1H221P"' + s[b + len('(property "MPN" "EEH-ZU1H221P"'):]
    n += 1
open(p, 'wb').write(s.encode('utf-8'))
print('KiCad: %d MPN fields changed' % n)

# ---- LTspice ----
p = os.path.join(folder, 'LTspice', 'BOOST.asc')
t = open(p, 'rb').read().decode('latin-1')
OLD = 'SYMATTR SpiceLine V=50 Irms=4.5 Rser=0.01 Lser=4n Rpar=455k'
NEW = 'SYMATTR SpiceLine V=50 Irms=3.2 Rser=0.013 Lser=4n Rpar=455k'
m = 0
for ref in ZS:
    k = t.find('SYMATTR InstName %s\n' % ref)
    assert k > 0, ref
    nxt = t.find('SYMBOL', k)
    j = t.find(OLD, k)
    assert k < j < nxt, ('ZU SpiceLine not found for', ref)
    t = t[:j] + NEW + t[j + len(OLD):]
    m += 1
open(p, 'wb').write(t.encode('latin-1'))
print('LTspice: %d SpiceLines changed; ZU lines left: %d' % (m, t.count(OLD)))
