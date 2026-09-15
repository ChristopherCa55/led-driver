"""Patch schedit.py: the only rsense_lo global label sat on U25.1's deleted wire run.
Delete it, re-label the power net at R1 pin 4, and refuse any other label that would dangle."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, 'schedit.py')
t = open(p, encoding='utf8').read()

if 'moved_labels' in t:
    print('already patched')
    raise SystemExit(0)

old_imp = "from schlib import Sheet, kids, kid\n"
assert t.count(old_imp) == 1
t = t.replace(old_imp, "from schlib import Sheet, kids, kid, head as head_of\n")

old = "delete_symbol('D12')\ndelete_symbol('R1')\n"
new = old + '''
# labels that sat only on deleted wiring would dangle: move rsense_lo, refuse anything else
moved_labels = []
for gl in kids(s.root, 'global_label') + kids(s.root, 'label'):
    at = kid(gl, 'at')
    pt = (float(at[1]), float(at[2]))
    items = s.touching(pt)
    wires_here = [it for it in items if it[0] in ('wire', 'wire_mid')]
    kept = [it for it in items
            if not (it[0] in ('wire', 'wire_mid') and it[1] in deleted_wires) and it[0] not in ('global_label', 'label')]
    pins_here = [inf['ref'] for inf in infos if inf['ref'] not in ('R1', 'D12') for q in inf['pins'] if near(q['pos'], pt)]
    if wires_here and not kept and not pins_here:
        name = str(gl[1])
        assert name == 'rsense_lo', ('label would dangle', name, pt)
        la, lb = span_uuid(str(kid(gl, 'uuid')[1]), head_of(gl))
        edits.append((la - 1, lb, ''))
        moved_labels.append((name, pt))
log.append('labels on deleted wiring (removed): %s' % moved_labels)
'''
assert t.count(old) == 1
t = t.replace(old, new)

old2 = "label('ISNS_P', p2, 90)\n"
new2 = "label('rsense_lo', p4, 90, must_attach=True)   # net name; the original label was on the deleted U25.1 run\n" + old2
assert t.count(old2) == 1
t = t.replace(old2, new2)

open(p, 'w', encoding='utf8').write(t)
print('schedit.py patched')
