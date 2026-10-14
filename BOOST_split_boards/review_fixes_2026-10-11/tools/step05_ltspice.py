"""Step 5 (LTspice part), the user's D1 / D2 answers of 2026-10-11, into a NEW file.

    python step05_ltspice.py SRC.asc OUT.asc

- D2: R99 (U26 A1 to GND) and R102 (U26 HVC/A0 to GND) 10k -> 1k ("you can change the r99 and r102 to 1k").
- D1: R106 (SCL) and R107 (SDA), 4.7k pull-ups to 5V ("Yes, you can add the pullups to the control card"). The
  MCP4451 has no internal SCL/SDA pull-ups (DS22267A). Each is drawn on its own, left of U26E, with a 5V flag above and
  its SCL / SDA flag below, so no existing wire, flag or part moves.
- a short note under them.
In the simulation the MCP4451_CTRL model ties SCL / SDA / A0 / A1 to VSS through 1 Gohm only, so these change ~5 nA.
Everything else is written back byte for byte (ascmodel keeps untouched lines). Prints the change list (x, y).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'ltspice_layout_2026-10-05', 'tools')))
import ascmodel as A

VALUES = {'R99': ('10k', '1k'), 'R102': ('10k', '1k')}
# res.asy pins are at (16, 16) and (16, 96) of the symbol origin (R0)
PULLUPS = [('R106', -6448, -6672, 'SCL'), ('R107', -6320, -6672, 'SDA')]
NOTE = (-6480, -6480, 'Left', 'I2C pull-ups (U26 has none)')


def main():
    src, out = sys.argv[1], sys.argv[2]
    a = A.Asc(src)
    log = []
    names = {s.name for s in a.syms}
    for s in a.syms:
        if s.name in VALUES:
            old, new = VALUES[s.name]
            i = [k for k, _ in s.attrs].index('Value')
            assert s.attrs[i][1] == old, (s.name, s.attrs[i])
            s.attrs[i] = ('Value', new)
            log.append('value changed at (%d, %d): %s %s -> %s' % (s.x, s.y, s.name, old, new))
    for ref, x, y, net in PULLUPS:
        assert ref not in names, ref
        px = x + 16
        a.syms.append(A.Sym('res', x, y, 'R0', [('InstName', ref), ('Value', '4.7k')],
                            {0: (-16, 40, 'Right', 2), 3: (-16, 72, 'Right', 2)}))
        a.wires.append((px, y - 16, px, y + 16))
        a.wires.append((px, y + 96, px, y + 128))
        a.flags.append([px, y - 16, '5V', None])
        a.flags.append([px, y + 128, net, None])
        log.append('part added at (%d, %d): %s 4.7k, pins (%d, %d) to 5V and (%d, %d) to %s; wires (%d, %d)-(%d, %d) '
                   'and (%d, %d)-(%d, %d); flags 5V at (%d, %d), %s at (%d, %d)' % (
                       x, y, ref, px, y + 16, px, y + 96, net, px, y - 16, px, y + 16, px, y + 96, px, y + 128,
                       px, y - 16, net, px, y + 128))
    x, y, just, txt = NOTE
    a.texts.append('TEXT %d %d %s 2 ;%s' % (x, y, just, txt))
    log.append('note added at (%d, %d): %s' % (x, y, txt))
    a.write(out)
    print('\n'.join(log))
    print('wrote', out)


if __name__ == '__main__':
    main()
