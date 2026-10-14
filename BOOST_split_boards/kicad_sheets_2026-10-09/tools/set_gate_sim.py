"""KiCad simulation fields of the logic gates = the LTspice v7 gate settings (user's OK, 2026-10-10).

    python set_gate_sim.py SHEET.kicad_sch

Every gate unit of the 74HC00 (U101-U103, units 1-4) and 74HC14 (U104-U105, units 1-6), spares included, gets
Sim.Device "SPICE" and Sim.Params model="<LTspice value>". The old KiCad values were the pre-retune LTspice ones;
LTspice's 74HC14 numbers match Nexperia 74HC_HCT14 Rev. 10 typicals at 5 V (checked 2026-10-10). Supply units
(74HC00 unit 5, 74HC14 unit 7) have no simulation fields and are left alone.
"""
import sys, copy
sys.path.insert(0, r'C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\kicad_layout_2026-10-09\tools')
from sexpr import parse, dump, find, findall, unq, q

VALUES = {  # lib_id: (gate units, LTspice v7 value)
    'ltspice:74HC00_conv': ((1, 2, 3, 4), 'Vhigh=5 Vlow=0 Vt=2.5 Td=2.6n Trise=8.75n Tfall=8.75n Rhigh=45 Rlow=38'),
    'ltspice:74HC14_conv': ((1, 2, 3, 4, 5, 6),
                            'Vhigh=5 Vlow=0 Vt=2.098 Vh=0.535 Td=7.6n Trise=8.75n Tfall=8.75n Rout=41'),
}


def hidden_prop(name, value, at):
    return ['property', q(name), q(value), ['at', at[1], at[2], '0'], ['hide', 'yes'], ['show_name', 'no'],
            ['do_not_autoplace', 'no'], ['effects', ['font', ['size', '1.27', '1.27']]]]


def main(path):
    root = parse(open(path, encoding='utf-8').read())
    n_set = n_added = 0
    for s in findall(root, 'symbol'):
        lid = unq(find(s, 'lib_id')[1])
        if lid not in VALUES:
            continue
        units, val = VALUES[lid]
        if int(find(s, 'unit')[1]) not in units:
            continue
        want = {'Sim.Device': 'SPICE', 'Sim.Params': 'model="%s"' % val}
        props = {unq(p[1]): p for p in findall(s, 'property')}
        for name, v in want.items():
            if name in props:
                if unq(props[name][2]) != v:
                    props[name][2] = q(v)
                    n_set += 1
            else:
                last = max(i for i, c in enumerate(s) if isinstance(c, list) and c[0] == 'property')
                s.insert(last + 1, hidden_prop(name, v, find(s, 'at')))
                n_added += 1
    open(path, 'w', encoding='utf-8', newline='\n').write(dump(root) + '\n')
    print('%s: %d fields changed, %d added' % (path, n_set, n_added))


if __name__ == '__main__':
    main(sys.argv[1])
