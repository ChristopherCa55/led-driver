"""Move the D28-D30 reference labels from B.SilkS to B.Fab, like every other small part on the power board.

    python fix_ref_labels.py BOOST_power_RC2.kicad_pcb

Text edit only (no KiCad save, so nothing else in the file changes):
  - D28, D29: the Reference field moves to B.Fab, at the same local spot as the footprint's ${REFERENCE} fab text
    (the D13 convention).
  - D30: the Reference field and its ${REFERENCE} fab text both go to B.Fab at the footprint centre (0, 0), because the
    library spot (-0.127, 1.905) lies 0.7 mm past the board edge at x 104.05.
Refuses to run unless each block is exactly in the expected state.
"""
import sys, re

PATH = sys.argv[1]
raw = open(PATH, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in raw else '\n'
t = raw.replace('\r\n', '\n')
WANT = {  # ref: (current Reference at, current ${REFERENCE} at, new Reference at, new ${REFERENCE} at)
    'D28': ('0 -1.9 180', '-0.127 1.905 180', '-0.127 1.905 180', '-0.127 1.905 180'),
    'D29': (None, '-0.127 1.905 180', '-0.127 1.905 180', '-0.127 1.905 180'),
    'D30': ('-0.127 1.905 270', '-0.127 1.905 270', '0 0 270', '0 0 270'),
}
for ref, (cur_at, cur_fab, new_at, new_fab) in WANT.items():
    i = t.index('(property "Reference" "%s"' % ref)
    a = t.rindex('\n\t(footprint ', 0, i) + 1
    b = t.index('\n\t(footprint ', i) + 1
    blk = t[a:b]
    assert blk.count('(property "Reference" "%s"' % ref) == 1
    m = re.search(r'(\t\t\(property "Reference" "%s"\n\t\t\t\(at )([^)]*)(\)\n\t\t\t\(layer ")([^"]*)(")' % ref, blk)
    assert m, ref
    if m.group(4) != 'B.SilkS':
        sys.exit('STOP: %s reference is on %s, not B.SilkS - already fixed? Nothing changed.' % (ref, m.group(4)))
    if cur_at is not None and m.group(2) != cur_at:
        sys.exit('STOP: %s reference at (%s), expected (%s). Nothing changed.' % (ref, m.group(2), cur_at))
    blk = blk[:m.start()] + m.group(1) + new_at + m.group(3) + 'B.Fab' + m.group(5) + blk[m.end():]
    f = re.search(r'(\t\t\(fp_text user "\$\{REFERENCE\}"\n\t\t\t\(at )([^)]*)(\)\n\t\t\t\(layer "B\.Fab"\))', blk)
    assert f and f.group(2) == cur_fab, (ref, f and f.group(2))
    blk = blk[:f.start()] + f.group(1) + new_fab + f.group(3) + blk[f.end():]
    t = t[:a] + blk + t[b:]
    print('%s: Reference -> B.Fab at (%s); ${REFERENCE} fab text at (%s)' % (ref, new_at, new_fab))
open(PATH, 'w', encoding='utf-8', newline='').write(t.replace('\n', nl) if nl == '\r\n' else t)
print('saved', PATH)
