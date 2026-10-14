"""Do the main schematic and the two board schematics still agree? (Every part is drawn twice since 2026-10-10.)

    python sync_check.py DIR        (a KiCad folder: BOOST.kicad_sch + BOOST_power_RC2 / BOOST_control_RC2.kicad_sch)

For every part unit on the main page: it is on exactly one board sheet (the right one for its board), with the same
library symbol, the same field values and the same BOM / board / DNP flags. Positions may differ. Electrical
agreement is checked by check.py (netlists).
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'kicad_layout_2026-10-09', 'tools')))
from sexpr import parse, find, findall, unq
import kgeo
import split_sheets as SS

FLAGS = ('exclude_from_sim', 'in_bom', 'on_board', 'dnp')


def units(path):
    out = {}
    for s in findall(parse(open(path, encoding='utf-8').read()), 'symbol'):
        i = kgeo.inst_info(s)
        if i['ref'].startswith('#'):
            continue
        props = {unq(p[1]): unq(p[2]) for p in findall(s, 'property')}
        flags = {f: find(s, f)[1] for f in FLAGS if find(s, f)}
        out[(i['ref'], i['unit'])] = (i['lib'], props, flags)
    return out


def main(d):
    A = json.load(open(SS.ASSIGN))
    main_u = units(os.path.join(d, 'BOOST.kicad_sch'))
    sheets = {'POWER': units(os.path.join(d, 'BOOST_power_RC2.kicad_sch')),
              'CONTROL': units(os.path.join(d, 'BOOST_control_RC2.kicad_sch'))}
    probs = []
    for key, (lib, props, flags) in sorted(main_u.items()):
        where = [b for b, u in sheets.items() if key in u]
        if where != [A[key[0]]]:
            probs.append('%s%s: on board sheet(s) %s, assigned to %s' % (key[0], key[1], where, A[key[0]]))
            continue
        lib2, props2, flags2 = sheets[where[0]][key]
        if lib2 != lib:
            probs.append('%s unit %d: symbol %s on the main page, %s on the board sheet' % (key[0], key[1], lib, lib2))
        for f in sorted(set(props) | set(props2)):
            if props.get(f) != props2.get(f):
                probs.append('%s unit %d: field %s differs (main %r, board %r)' % (key[0], key[1], f, props.get(f),
                                                                                   props2.get(f)))
        if flags != flags2:
            probs.append('%s unit %d: flags differ %s / %s' % (key[0], key[1], flags, flags2))
    extra = [(b, k) for b, u in sheets.items() for k in u if k not in main_u]
    for b, k in extra:
        probs.append('%s%s is on the %s sheet but not on the main page' % (k[0], k[1], b))
    print('%d part units on the main page; board sheets %d + %d; %d differences'
          % (len(main_u), len(sheets['POWER']), len(sheets['CONTROL']), len(probs)))
    for p in probs[:40]:
        print('  ', p)
    return probs


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), 'work_flat'))
