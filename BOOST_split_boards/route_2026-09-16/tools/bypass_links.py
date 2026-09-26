"""Driver bypass links on a routed board, from its copper export (system Python).

usage: python bypass_links.py ROUTED_CU.json [OUT.json]

For each driver supply pin and its bypass capacitor: pad-centre distance, and the routed copper from the capacitor
pad to the pin on that net alone (track centre lines and vias, as gate_paths.py measures; the planes and the
priority <= 1 fills are not part of the path, so a link that only exists through a plane shows as n/a).
For the VCCI capacitors: the capacitor pad's nearest via of its net along its own copper, and whether that path
passes another part's pad on the way (then the via is not the capacitor's own).
"""
import collections, json, math, sys
import gate_paths as gp

LINKS = [  # cap pad, driver pin, what the pin is
    (('C31', '1'), ('U19', '16'), 'VDDA 12V'), (('C31', '2'), ('U19', '14'), 'VSSA GND'),
    (('C51', '1'), ('U15', '11'), 'VDDB'), (('C51', '2'), ('U15', '9'), 'VSSB'),
    (('C51', '1'), ('U15', '16'), 'VDDA'), (('C51', '2'), ('U15', '14'), 'VSSA'),
    (('C18', '1'), ('U15', '11'), 'VDDB'), (('C18', '2'), ('U15', '9'), 'VSSB'),
    (('C50', '1'), ('U10', '11'), 'VDDB'), (('C50', '2'), ('U10', '9'), 'VSSB'),
    (('C16', '1'), ('U10', '11'), 'VDDB'), (('C16', '2'), ('U10', '9'), 'VSSB'),
    (('C61', '1'), ('U8', '11'), 'VDDB'), (('C61', '2'), ('U8', '9'), 'VSSB'),
    (('C60', '1'), ('U8', '11'), 'VDDB'), (('C60', '2'), ('U8', '9'), 'VSSB'),
    (('C48', '1'), ('U19', '3'), 'VCCI'), (('C48', '1'), ('U19', '8'), 'VCCI (pin 8, shorted to 3 inside)'),
    (('C48', '2'), ('U19', '4'), 'GND'),
    (('C90', '1'), ('U10', '3'), 'VCCI'), (('C90', '2'), ('U10', '4'), 'GND'),
    (('C89', '2'), ('U8', '3'), 'VCCI'), (('C89', '1'), ('U8', '4'), 'GND'),
    (('C62', '2'), ('U15', '3'), 'VCCI'), (('C62', '1'), ('U15', '4'), 'GND'),
]
VCCI_PADS = [('C48', '1'), ('C48', '2'), ('C90', '1'), ('C90', '2'), ('C89', '2'), ('C89', '1'), ('C62', '2'),
             ('C62', '1')]


def main():
    pads = gp.pads
    graphs = {}

    def g(net):
        if net not in graphs:
            graphs[net] = gp.graph(net)
        return graphs[net]

    out = dict(links=[], vcci_vias=[])
    print('link                       net                 centre mm  routed mm  vias')
    for cap, pin, what in LINKS:
        if cap not in pads or pin not in pads:
            continue
        a, b = pads[cap], pads[pin]
        if a['net'] != b['net']:
            print('%s.%s -> %s.%s: different nets (%s, %s)' % (*cap, *pin, a['net'], b['net']))
            continue
        d, nodes = gp.dist(g(a['net']), 'P:%s.%s' % cap, {'P:%s.%s' % pin}, want_path=True)
        row = dict(cap='%s.%s' % cap, pin='%s.%s' % pin, what=what, net=a['net'],
                   centre_mm=math.hypot(a['x'] - b['x'], a['y'] - b['y']), routed_mm=d,
                   vias=gp.vias_on(nodes) if d is not None else None)
        out['links'].append(row)
        print('%-26s %-19s %6.1f     %s     %s' % ('%s -> %s %s' % (row['cap'], row['pin'], what), row['net'],
                                                   row['centre_mm'], '%5.1f' % d if d is not None else '  n/a',
                                                   row['vias'] if d is not None else '-'))
    print('\nVCCI capacitor pad -> nearest via of its net along its copper')
    for cap in VCCI_PADS:
        p = pads[cap]
        adj = g(p['net'])
        vias = {x for x in adj if isinstance(x, tuple) and x[0] == 'V'}
        src = 'P:%s.%s' % cap
        # the nearest via reached without passing another part's pad; failing that, any nearest via
        own = {k: [(u, w) for u, w in nb if not (isinstance(u, str) and u.startswith('P:') and u != src)]
               for k, nb in adj.items()}
        own = collections.defaultdict(list, own)
        d, nodes = gp.dist(own, src, vias, want_path=True)
        if d is None:
            d, nodes = gp.dist(adj, src, vias, want_path=True)
        if d is None:
            print('%s.%s %s: no via reached' % (*cap, p['net']))
            out['vcci_vias'].append(dict(pad='%s.%s' % cap, net=p['net'], via=None))
            continue
        v = nodes[-1]
        through = [x[2:] for x in nodes[1:-1] if isinstance(x, str) and x.startswith('P:')]
        row = dict(pad='%s.%s' % cap, net=p['net'], via=[v[1], v[2]], track_mm=d,
                   centre_mm=math.hypot(v[1] - p['x'], v[2] - p['y']), through_pads=through)
        out['vcci_vias'].append(row)
        print('%s.%s %-4s via (%.2f, %.2f): %.1f mm from the pad centre, %.1f mm of track%s' % (
            *cap, p['net'], v[1], v[2], row['centre_mm'], d,
            (', through %s (not its own)' % ', '.join(through)) if through else ', own via'))
    if len(sys.argv) > 2:
        json.dump(out, open(sys.argv[2], 'w'), indent=1)


if __name__ == '__main__':
    main()
