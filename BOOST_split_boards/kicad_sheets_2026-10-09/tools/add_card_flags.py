"""PWR_FLAGs on the control card's 5V and GND (user's OK, 2026-10-10): the card gets both only through J11, so its
project alone reported U18 VDD/VSS "power pin not driven". Card schematic only: on the main page a flag on 5V would
clash with U17's output.

    python add_card_flags.py CARD.kicad_sch POWER.kicad_sch      (edits CARD; POWER only supplies the PWR_FLAG symbol)

A small group right of J11: a note, "5V" label -> wire -> PWR_FLAG, GND symbol -> wire -> PWR_FLAG.
"""
import sys, copy, uuid
sys.path.insert(0, r'C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\kicad_layout_2026-10-09\tools')
from sexpr import parse, dump, find, findall, unq, q
import kgeo

NS = uuid.UUID('5b0a1f2e-6c1d-4e8a-9a51-2f3d0c9b7a10')
X0, X1 = 396.24, 401.32             # label / GND point, flag point (mm, on the 1.27 mm grid)
Y5, YG, YN = 386.08, 393.7, 379.73  # 5V row, GND row, note
NOTE = 'power enters the card through J11'


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def uid(name):
    return q(str(uuid.uuid5(NS, name)))


def place(tmpl, ref, x, y, ang, project, path, hide_value):
    s = copy.deepcopy(tmpl)
    find(s, 'at')[1:4] = [fmt(x), fmt(y), str(ang)]
    s[:] = [c for c in s if not (isinstance(c, list) and c[0] == 'mirror')]
    find(s, 'uuid')[1] = uid('card flag symbol ' + ref)
    for p in findall(s, 'property'):
        find(p, 'at')[1:3] = [fmt(x), fmt(y)]
        if unq(p[1]) == 'Reference':
            p[2] = q(ref)
        if unq(p[1]) in ('Reference', 'Value') and (unq(p[1]) == 'Reference' or hide_value):
            if ['hide', 'yes'] not in p:
                p.insert(4, ['hide', 'yes'])
    for k, pn in enumerate(findall(s, 'pin')):
        find(pn, 'uuid')[1] = uid('card flag pin %s %d' % (ref, k))
    inst = find(s, 'instances')
    inst[:] = ['instances', ['project', q(project), ['path', q(path), ['reference', q(ref)], ['unit', '1']]]]
    return s


def main(card, power):
    root = parse(open(card, encoding='utf-8').read())
    pw = parse(open(power, encoding='utf-8').read())
    if any(unq(t[1]) == NOTE for t in findall(root, 'text')):
        raise SystemExit('flags already added')
    libs = find(root, 'lib_symbols')
    if not any(unq(s[1]) == 'power:PWR_FLAG' for s in findall(libs, 'symbol')):
        libs.append(copy.deepcopy(next(s for s in findall(find(pw, 'lib_symbols'), 'symbol')
                                       if unq(s[1]) == 'power:PWR_FLAG')))
    flag = next(s for s in findall(pw, 'symbol') if unq(find(s, 'lib_id')[1]) == 'power:PWR_FLAG')
    syms = findall(root, 'symbol')
    gnd = next(s for s in syms if unq(find(s, 'lib_id')[1]) == 'ltspice:GND')
    proj = find(find(syms[0], 'instances'), 'project')
    project, path = unq(proj[1]), unq(find(proj, 'path')[1])
    refs = [kgeo.inst_info(s)['ref'] for s in syms]
    nflg = 1 + max([int(r[4:]) for r in refs if r.startswith('#FLG')] + [9])
    ngnd = 1 + max(int(r[4:]) for r in refs if r.startswith('#GND'))
    new = [
        ['text', q(NOTE), ['exclude_from_sim', 'no'], ['at', fmt(X0 - 3.81), fmt(YN), '0'],
         ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left']], ['uuid', uid('card flag note')]],
        ['global_label', '"5V"', ['shape', 'passive'], ['at', fmt(X0), fmt(Y5), '180'], ['fields_autoplaced', 'yes'],
         ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'right']], ['uuid', uid('card flag 5V label')],
         ['property', '"Intersheetrefs"', '"${INTERSHEET_REFS}"', ['at', fmt(X0), fmt(Y5), '0'], ['hide', 'yes'],
          ['show_name', 'no'], ['do_not_autoplace', 'no'], ['effects', ['font', ['size', '1.27', '1.27']]]]],
    ]
    for y, tag in ((Y5, '5V'), (YG, 'GND')):
        new.append(['wire', ['pts', ['xy', fmt(X0), fmt(y)], ['xy', fmt(X1), fmt(y)]],
                    ['stroke', ['width', '0'], ['type', 'default']], ['uuid', uid('card flag wire ' + tag)]])
    new.append(place(gnd, '#GND%03d' % ngnd, X0, YG, 0, project, path, hide_value=True))
    new.append(place(flag, '#FLG%02d' % nflg, X1, Y5, 0, project, path, hide_value=True))
    new.append(place(flag, '#FLG%02d' % (nflg + 1), X1, YG, 0, project, path, hide_value=True))
    k = max(i for i, c in enumerate(root) if isinstance(c, list) and c[0] == 'symbol')
    root[k + 1:k + 1] = new
    open(card, 'w', encoding='utf-8', newline='\n').write(dump(root) + '\n')
    print('added #FLG%02d (5V), #FLG%02d (GND), #GND%03d, a 5V label and a note to %s' % (nflg, nflg + 1, ngnd, card))


if __name__ == '__main__':
    main(*sys.argv[1:3])
