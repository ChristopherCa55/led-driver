"""Explicit checks of the section 4 changes on an exported netlist, plus ERC summary.

  netcheck.py ERC.json NETLIST.net ASSIGN.json
"""
import json, sys, re, collections

erc = json.load(open(sys.argv[1], encoding='utf8'))
vs = [v for s in erc.get('sheets', []) for v in s.get('violations', [])]
print('ERC:', dict(collections.Counter((v['severity'], v['type']) for v in vs)), 'total', len(vs))
for v in vs:
    print('  ', v['severity'], v['type'], '|', v.get('description', '')[:70], '|',
          [i.get('description', '')[:60] for i in v.get('items', [])][:3])

t = open(sys.argv[2], encoding='utf8').read()
nets = {}
i = t.find('(nets')
for blk in re.split(r'\(net\s+\(code', t[i:])[1:]:
    name = re.search(r'\(name\s+"([^"]*)"\)', blk).group(1)
    nets[name] = {'%s.%s' % m for m in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', blk)}
comps = dict(re.findall(r'\(comp\s+\(ref\s+"([^"]+)"\)\s*\(value\s+"([^"]*)"\)', t))
where = {x: n for n, nodes in nets.items() for x in nodes}
fails = []


def check(cond, msg):
    print('   %s %s' % ('ok  ' if cond else 'FAIL', msg))
    if not cond:
        fails.append(msg)


check(nets.get('ISNS_P') == {'R1.2', 'U25.8'}, 'ISNS_P = %s' % sorted(nets.get('ISNS_P', [])))
check(nets.get('ISNS_N') == {'R1.3', 'U25.1'}, 'ISNS_N = %s' % sorted(nets.get('ISNS_N', [])))
check(where.get('R1.1') == 'Vin' and where.get('J1.1') == 'Vin' and where.get('U25.8') != 'Vin', 'R1.1 and J1.1 on Vin, U25.8 off Vin')
check(where.get('R1.4') == 'rsense_lo' and where.get('L1.2') == 'rsense_lo' and where.get('U25.1') != 'rsense_lo',
      'R1.4 and L1.2 on rsense_lo, U25.1 off it (rsense_lo = %s)' % sorted(nets.get('rsense_lo', [])))
for nt, op, fet, sh, sns in (('NT1', 'U11', 'M10', 'R52', 'SNS_CH1'), ('NT2', 'U12', 'M9', 'R53', 'SNS_CH2'),
                             ('NT3', 'U6', 'M8', 'R7', 'SNS_CH3')):
    check(nets.get(sns) == {nt + '.1', op + '.4'}, '%s = %s' % (sns, sorted(nets.get(sns, []))))
    src = where.get(fet + '.3')
    check(where.get(sh + '.1') == src and where.get(nt + '.2') == src and where.get(op + '.4') != src,
          '%s.3, %s.1, %s.2 on %s; %s.4 not' % (fet, sh, nt, src, op))
check({'D1.1', 'D15.1', 'D24.1', 'D27.1'} <= nets.get('M1_INHIBIT', set()),
      'M1_INHIBIT = %s' % sorted(nets.get('M1_INHIBIT', [])))
check(nets.get('ARD_M1_INHIBIT') == {'J9.11', 'D27.2', 'R105.1'} and where.get('R105.2') == 'GND',
      'ARD_M1_INHIBIT = %s; R105.2 on %s' % (sorted(nets.get('ARD_M1_INHIBIT', [])), where.get('R105.2')))
check('D12' not in comps and where.get('R15.2') == 'GATE_M1' and where.get('M1.1') == 'GATE_M1',
      'D12 gone; R15.2 and M1.1 on GATE_M1; R15.1 on %s' % where.get('R15.1'))
check(comps.get('R15') == '10' and all(comps.get(r) == '220' for r in ('R13', 'R23', 'R47')),
      'R15 = %s; R13/R23/R47 = %s' % (comps.get('R15'), [comps.get(r) for r in ('R13', 'R23', 'R47')]))

PINOUT = {1: 'GND', 2: 'GND', 3: 'M1_ON', 4: 'M2_ON', 5: 'ena_out_1', 6: 'out_2_on', 7: 'ena_out_2', 8: 'out_3_on',
          9: 'ena_out_3', 10: '5V', 11: 'GND', 12: 'GND', 13: 'Vout_1', 14: 'Output1_drain', 15: 'Vout_2',
          16: 'Output2_drain', 17: 'Vout_3', 18: 'Output3_drain', 19: '12V', 20: 'GND', 21: 'GND', 22: 'analog_5V',
          23: 'Current', 24: 'GND', 25: 'GND', 26: 'IREF1_input', 27: 'IREF2_input', 28: 'GND', 29: 'GND', 30: 'IREF3_input'}
bad = [(j, n, where.get('%s.%d' % (j, n))) for j in ('J10', 'J11') for n, net in PINOUT.items() if where.get('%s.%d' % (j, n)) != net]
check(not bad, 'J10/J11 pin n on its pinout net (mismatches %s)' % bad)

assign = json.load(open(sys.argv[3]))
refs = {x.split('.')[0] for x in where}
check(refs <= set(assign), 'every netlist ref has a board (missing %s)' % sorted(refs - set(assign)))
check(all(assign.get(r) == 'CONTROL' for r in ('R9', 'R35', 'R43', 'R25', 'R87', 'R94', 'R8', 'R34', 'R42')),
      'both resistors of every divider on CONTROL')
cross = {}
for n, nodes in nets.items():
    boards = {assign[x.split('.')[0]] for x in nodes if x.split('.')[0] in assign}
    if len(boards) > 1:
        cross[n] = nodes
hdr = set(PINOUT.values())
check(set(cross) == hdr, 'board-crossing nets == header nets (extra %s, missing %s)' % (sorted(set(cross) - hdr), sorted(hdr - set(cross))))
print('RESULT: %d failures' % len(fails))
