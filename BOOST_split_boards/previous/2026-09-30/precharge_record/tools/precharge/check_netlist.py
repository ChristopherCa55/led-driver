"""Check the KiCad netlist exported after the schematic edit.

    python check_netlist.py BOOST_precharge.net

Expected: 293 components (290 before + D28, D29, D30), 186 nets (unchanged: the diodes join existing nets), and
    D28 value S2MW, footprint Diode_SMD:D_SOD-123F, pin 2 on Vin, pin 1 on Vout_1
    D29 ... pin 1 on Vout_2,   D30 ... pin 1 on Vout_3
Prints PASS or the differences.
"""
import sys, re
t = open(sys.argv[1], encoding='utf-8').read()
comps = {}
for m in re.finditer(r'\(comp\s+\(ref\s+"([^"]+)"\)\s*\(value\s+"([^"]*)"\)\s*\(footprint\s+"([^"]*)"\)', t):
    comps[m.group(1)] = (m.group(2), m.group(3))
nets = {}
i = t.find('(nets')
for blk in re.split(r'\(net\s+\(code', t[i:])[1:]:
    name = re.search(r'\(name\s+"([^"]*)"\)', blk).group(1)
    for r, p in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', blk):
        nets[(r, p)] = name
n_nets = len(re.findall(r'\(net\s+\(code', t))
print('components %d, nets %d' % (len(comps), n_nets))
bad = []
if len(comps) != 293:
    bad.append('expected 293 components')
if n_nets != 186:
    bad.append('expected 186 nets')
for ref, vout in (('D28', 'Vout_1'), ('D29', 'Vout_2'), ('D30', 'Vout_3')):
    c = comps.get(ref)
    print('%s: %s, pin 2 -> %s, pin 1 -> %s' % (ref, c, nets.get((ref, '2')), nets.get((ref, '1'))))
    if c != ('S2MW', 'Diode_SMD:D_SOD-123F'):
        bad.append('%s value/footprint %s' % (ref, c))
    if nets.get((ref, '2')) != 'Vin' or nets.get((ref, '1')) != vout:
        bad.append('%s pins on the wrong nets' % ref)
print('PASS' if not bad else 'FAIL: ' + '; '.join(bad))
