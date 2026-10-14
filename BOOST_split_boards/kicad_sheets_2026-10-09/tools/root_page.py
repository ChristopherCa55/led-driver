"""Make the root page say what the two sheet boxes are: a light fill, a short contents list inside each box, and
"double-click a box to open it". KiCad never previews a sheet's contents inside its box.

    python root_page.py ROOT.kicad_sch      (edits that file; only the root page)
"""
import sys, uuid
sys.path.insert(0, r'C:\Users\bubba\OneDrive\Documents\led-driver\BOOST_split_boards\kicad_layout_2026-10-09\tools')
from sexpr import parse, dump, find, findall, unq, q

NS = uuid.UUID('5b0a1f2e-6c1d-4e8a-9a51-2f3d0c9b7a10')
CONTENTS = {
    'Power board': ['Battery input, current sense, boost switch M1',
                    'Outputs 1-3 with their gate drivers',
                    'LED current limit, channels 1-3',
                    'Regulators: 12V, 5V, analog 5V',
                    'J10: to the control card'],
    'Control card': ['Error amplifiers and headroom servos, 1-3',
                     'Digital pots (U26)',
                     'Sequencer, M1 latch, channel enable, M1 inhibit',
                     'Logic chip supplies, spare units',
                     'J9: Arduino, J11: to the power board'],
}
NOTE = 'Double-click a box to open that board\'s schematic (Alt+Backspace goes back up).'


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def main(path):
    root = parse(open(path, encoding='utf-8').read())
    have = {t[1][1:-1] for t in findall(root, 'text')}            # raw text: run twice, add once
    for sh in findall(root, 'sheet'):
        name = next(unq(p[2]) for p in findall(sh, 'property') if unq(p[1]) == 'Sheetname')
        fill = find(sh, 'fill')
        fill[:] = ['fill', ['color', '255', '255', '225', '1.0000']]
        x, y = float(find(sh, 'at')[1]), float(find(sh, 'at')[2])
        txt =(chr(92) + 'n').join(CONTENTS[name] + ['', '(double-click to open)'])
        if txt in have:
            continue
        root.insert(root.index(sh) + 1,
                    ['text', '"%s"' % txt, ['exclude_from_sim', 'no'], ['at', fmt(x + 3.81), fmt(y + 5.08), '0'],
                     ['effects', ['font', ['size', '1.524', '1.524']], ['justify', 'left', 'top']],
                     ['uuid', q(str(uuid.uuid5(NS, 'root contents ' + name)))]])
    if NOTE not in have:
        last = max((t for t in findall(root, 'text') if float(find(t, 'at')[2]) < 50),
                   key=lambda t: float(find(t, 'at')[2]))
        y = float(find(last, 'at')[2]) + 6.35
        root.insert(root.index(last) + 1,
                    ['text', '"%s"' % NOTE, ['exclude_from_sim', 'no'], ['at', '30.48', fmt(y), '0'],
                     ['effects', ['font', ['size', '1.905', '1.905'], ['bold', 'yes']], ['justify', 'left', 'bottom']],
                     ['uuid', q(str(uuid.uuid5(NS, 'root note open')))]])
    open(path, 'w', encoding='utf-8', newline='\n').write(dump(root) + '\n')
    print('root page updated:', path)


if __name__ == '__main__':
    main(sys.argv[1])
