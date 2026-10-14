"""Set one footprint field on a board to the text a schematic symbol unit has (what KiCad's Update PCB writes).

    python pcb_set_field.py BOARD.kicad_pcb SHEET.kicad_sch REF UNIT FIELD

Used for U104 Sim.Params: U104's units disagree in the schematic (A-D vs E/F, KiCad simulation fields only), and
KiCad's parity check compares the footprint with unit E/F. Text edit, CRLF kept, nothing else changes.
"""
import re, sys

FIELD_TXT = r'\(property "%s" "((?:[^"\\]|\\.)*)"'


def main():
    pcb, sch, ref, unit, field = sys.argv[1:6]
    s = open(sch, encoding='utf-8').read()
    val = None
    for b in re.findall(r'\n\t\(symbol\n(.*?)\n\t\)', s, re.S):
        if ('"Reference" "%s"' % ref) in b and re.search(r'\n\t\t\(unit %s\)' % unit, b):
            val = re.search(FIELD_TXT % re.escape(field), b).group(1)
    assert val is not None, (ref, unit, field)
    t = open(pcb, encoding='utf-8', newline='').read()
    i = t.find('(property "Reference" "%s"' % ref)
    j = t.rfind('\n\t(footprint ', 0, i)
    k = t.find('\n\t)', i)
    blk = t[j:k]
    m = re.search(FIELD_TXT % re.escape(field), blk)
    assert m, 'footprint %s has no %s' % (ref, field)
    old = m.group(1)
    blk = blk[:m.start(1)] + val + blk[m.end(1):]
    open(pcb, 'w', encoding='utf-8', newline='').write(t[:j] + blk + t[k:])
    print('%s %s: %s -> %s' % (ref, field, old, val))


if __name__ == '__main__':
    main()
