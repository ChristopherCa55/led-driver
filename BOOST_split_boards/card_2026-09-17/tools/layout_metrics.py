"""One-line comparison of placer layouts (system Python).

usage: python layout_metrics.py CONFIG.json LAYOUT.json [LAYOUT.json ...]

Per layout: unweighted HPWL of the signal nets (power nets GND, 5V, analog_5V, 12V excluded, as in the placer),
the HPWL of the comparator input nets (Current, V_err, Net-(U2-In+)), the nearest logic-edge pin (gate / counter
signals, switch controls, mux selects, I2C) to any of those nets, the decoupling worst case and the number of IC supply pins whose nearest capacitor is on the other side.
"""
import json, math, sys

cfg = json.load(open(sys.argv[1]))
inv = json.load(open(cfg['inventory']))
MATS = [((1, 0), (0, 1)), ((0, -1), (1, 0)), ((-1, 0), (0, -1)), ((0, 1), (-1, 0))]
POWER = ('GND', '5V', 'analog_5V', '12V')
SENS = ('Current', 'V_err', 'Net-(U2-In+)')
# logic edges: every signal pin of the gates and the counter; only the control / select / I2C pins of the analog
# switch (CD74HC4066: 1E 13, 2E 5, 3E 6, 4E 12), the mux (74HC4051: S0-S2 11, 10, 9) and the digipot
LOGIC_ALL = ('U101', 'U102', 'U103', 'U104', 'U105', 'U18')
LOGIC_PINS = {'U106': ('5', '6', '12', '13'), 'U28': ('9', '10', '11'), 'U26': ('5', '6')}
for f in sys.argv[2:]:
    lay = json.load(open(f))['layout']
    pin, net, pn = {}, {}, {}
    for r, v in inv.items():
        x, y, rot, sd = lay[r]
        m = MATS[int(round(rot / 90)) % 4]
        for p in v['pads']:
            if not p.get('num'):
                continue
            px, py = p['x'], (-p['y'] if sd == 'B' else p['y'])
            k = '%s.%s' % (r, p['num'])
            pin[k] = (x + px * m[0][0] + py * m[1][0], y + px * m[0][1] + py * m[1][1])
            net[k] = p.get('net', '')
            pn.setdefault(net[k], []).append(k)

    def hpwl(n):
        ps = [pin[k] for k in pn[n]]
        return max(p[0] for p in ps) - min(p[0] for p in ps) + max(p[1] for p in ps) - min(p[1] for p in ps)

    tot = sum(hpwl(n) for n in pn if n and n not in POWER and not n.startswith('unconnected') and len(pn[n]) > 1)
    sens = [k for n in SENS for k in pn[n]]
    # logic pins that carry a signal (not supply, not unconnected, not the sensitive nets themselves)
    lg = [k for k in pin if (k.split('.')[0] in LOGIC_ALL or k.split('.')[1] in LOGIC_PINS.get(k.split('.')[0], ()))
          and net[k] not in POWER and net[k] not in SENS and not net[k].startswith('unconnected')]
    d = lambda a, b: math.hypot(pin[a][0] - pin[b][0], pin[a][1] - pin[b][1])
    near = min((d(a, b), a, b) for a in sens for b in lg)
    dec, opp = [], 0
    for rail in ('5V', 'analog_5V'):
        caps = [k for k in pn[rail] if k.startswith('C')]
        for k in pn[rail]:
            if k[0] in 'UQ':
                dd, c = min((d(k, c), c) for c in caps)
                dec.append(dd)
                opp += lay[k.split('.')[0]][3] != lay[c.split('.')[0]][3]
    print('%-22s HPWL %5.0f | Current %4.1f V_err %4.1f U2-In+ %4.1f | nearest logic pin %4.1f (%s-%s) | decap max %.1f, '
          'other side %d' % (f.split('/')[-1], tot, hpwl('Current'), hpwl('V_err'), hpwl('Net-(U2-In+)'), near[0],
                             near[1], near[2], max(dec), opp))
