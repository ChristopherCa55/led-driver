"""One-off patch (2026-10-01): teach fab_2026-09-30/tools/fab_drawing.py the card's 0.5 oz inner-copper stackup.
Run from fab_2026-09-30/. The power drawing is not affected (the new branch needs 6 layers and a 1.5468 mm board)."""
p = 'tools/fab_drawing.py'
s = open(p, encoding='utf-8').read()
n = 0


def rep(a, b):
    global s, n
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
    n += 1


rep("NL = F['copper_layers']          # 8, or 6 for the card from 2026-09-30",
    "NL = F['copper_layers']          # 8, or 6 for the card from 2026-09-30\n"
    "HALF = NL == 6 and F['board_thickness_in_file_mm'] < 1.58   # card with 0.5 oz inner copper, from 2026-10-01\n"
    "DATE = '2026-10-01' if HALF else '2026-09-30'")
rep("tx.text(0, 0.965, '%s, 2026-09-30. Files: %s_gerbers.zip. Units: mm.' % (NAME, NAME),",
    "tx.text(0, 0.965, '%s, %s. Files: %s_gerbers.zip. Units: mm.' % (NAME, DATE, NAME),")
# the two notes are computed after HALF is defined, so patch them with a conditional
rep("""    ('Copper 1 oz (35 um) finished on all %s layers: outer 1 oz, inner 1 oz (order option "Inner copper weight '
     '1 oz"; the fab default of 0.5 oz inner is NOT acceptable).' % {6: 'six', 8: 'eight'}[NL], False),
    ('Stackup: the fab\\'s standard %d-layer 1.6 mm build (no stackup specified), as in the table. No impedance '
     'control.' % NL, False),""",
    """    (('Copper: outer layers 1 oz (35 um) finished; the four inner layers 0.5 oz (order option "Inner copper '
      'weight 0.5 oz", the fab default for 6 layers).') if HALF else
     ('Copper 1 oz (35 um) finished on all %s layers: outer 1 oz, inner 1 oz (order option "Inner copper weight '
      '1 oz"; the fab default of 0.5 oz inner is NOT acceptable).' % {6: 'six', 8: 'eight'}[NL]), False),
    ('Stackup: the fab\\'s standard %d-layer 1.6 mm build for %s copper (no stackup specified), as in the table. '
     'No impedance control.' % (NL, '1 oz outer / 0.5 oz inner' if HALF else 'this'), False),""")
rep("""          ('', 'prepreg 7628', '', '0.203'), ('B.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
          ('B.Mask', 'solder mask', '', '0.010')]
for a, b, c, d in ST:""",
    """          ('', 'prepreg 7628', '', '0.203'), ('B.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
          ('B.Mask', 'solder mask', '', '0.010')]
if HALF:         # JLCPCB 6-layer 1.6 mm, 1 oz outer / 0.5 oz inner "no requirement" build (jlcpcb.com/impedance, 2026-10-01)
    ST = [('F.Mask', 'solder mask', '', '0.010'), ('F.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
          ('', 'prepreg 3313, er 4.1', '', '0.0994'), ('In1.Cu', 'copper, 0.5 oz', 'signal / GND fill', '0.0152'),
          ('', 'core, er 4.6', '', '0.550'), ('In2.Cu', 'copper, 0.5 oz', 'signal / 5V pour', '0.0152'),
          ('', 'prepreg 2116, er 4.16', '', '0.1164'), ('In3.Cu', 'copper, 0.5 oz', 'signal / GND fill', '0.0152'),
          ('', 'core, er 4.6', '', '0.550'), ('In4.Cu', 'copper, 0.5 oz', 'signal / GND fill', '0.0152'),
          ('', 'prepreg 3313, er 4.1', '', '0.0994'), ('B.Cu', 'copper, 1 oz', 'signal / parts', '0.035'),
          ('B.Mask', 'solder mask', '', '0.010')]
for a, b, c, d in ST:""")
open(p, 'w', encoding='utf-8').write(s)
print('patched', n)
