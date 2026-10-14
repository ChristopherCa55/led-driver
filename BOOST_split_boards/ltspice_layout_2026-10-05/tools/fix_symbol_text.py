"""Fix the doubled pin text on the five custom symbols (graphics only).

    python fix_symbol_text.py WORKDIR

Each of these symbols drew every pin name twice: once by the PIN line itself (justification LEFT/RIGHT/TOP/BOTTOM 8)
and once by a hand-placed TEXT, and some TEXTs also collided with each other. This hides the automatic pin names
(PIN ... NONE 0) and redraws one small label per pin where nothing overlaps.

What is NOT changed: pin positions, pin names, SpiceOrder, Prefix, Value, SpiceLine, ModelFile and Description, so
every wire still lands on the same pin and the netlist is identical (checked by ltspice_equiv.py's
graphics-only comparison). Originals: ../previous/2026-10-07/asy_before_text_fix/.
"""
import os, sys

TEXTS = {
    # symbol: (lines to drop (startswith), new TEXT lines)
    'INA241A4': (['TEXT ', 'LINE Normal -64 -32 -48 -32', 'LINE Normal -64 32 -48 32', 'LINE Normal -56 -40 -56 -24'],
                 ['TEXT -56 -32 Left 1 IN+', 'TEXT -56 32 Left 1 IN-', 'TEXT -56 0 Left 1 REF1', 'TEXT 0 -52 Center 1 VS',
                  'TEXT 56 0 Right 1 OUT', 'TEXT -2 52 Center 1 GND', 'TEXT 38 52 Center 1 REF2',
                  'TEXT 16 -24 Center 1 x100']),
    'CSS4J_4026': (['TEXT '], ['TEXT 40 -20 Center 0 Kelvin']),
    'CD74HC4066': (['TEXT '], ['TEXT 36 -18 Center 0 VDD', 'TEXT 18 24 Center 0 VSS', 'TEXT 60 24 Center 0 CTRL']),
    'MCP4451_POT': (['TEXT '], ['TEXT -14 -40 Right 1 B', 'TEXT -14 40 Right 1 A', 'TEXT 44 -12 Right 1 W']),
    'MCP4451_CTRL': (['TEXT '], ['TEXT -60 -32 Left 1 SCL', 'TEXT -60 0 Left 1 SDA', 'TEXT 0 -68 Center 1 VDD',
                                 'TEXT 60 0 Right 1 RESET', 'TEXT -44 70 Center 0 HVC/A0', 'TEXT 0 70 Center 0 A1',
                                 'TEXT 48 70 Center 0 VSS', 'TEXT 0 36 Center 1 MCP4451']),
}


def fix(path, drop, new_texts):
    lines = open(path, encoding='latin-1').read().replace('\r', '').split('\n')
    out, inserted = [], False
    for l in lines:
        if any(l.startswith(d) for d in drop):
            continue
        if l.startswith('PIN '):
            t = l.split(' ')
            l = 'PIN %s %s NONE 0' % (t[1], t[2])
        if l.startswith('WINDOW ') and not inserted:
            out += new_texts
            inserted = True
        out.append(l)
    if not inserted:
        raise SystemExit('no WINDOW line in ' + path)
    open(path, 'w', encoding='latin-1', newline='\n').write('\n'.join(out))


if __name__ == '__main__':
    wd = sys.argv[1]
    for sym, (drop, new) in TEXTS.items():
        fix(os.path.join(wd, sym + '.asy'), drop, new)
        print('fixed', sym)
