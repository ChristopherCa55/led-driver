"""Step 5e (KiCad schematics; = step05_kicad_sch.py with the 0603 footprint the user asked for on 2026-10-12), the user's D1 / D2 answers, in place on a SCRATCH KiCad folder (text edits only; each
file keeps its own line endings).

    python step05_kicad_sch.py KICAD_DIR LOG.json

- D2: R99 and R102 Value 10k -> 1k (main page and card sheet).
- D1: R106 (SCL) and R107 (SDA), 4.7k 0603 pull-ups to 5V (JLC C23162, the card's existing 4.7k line), drawn like the LTspice page: left of U26E's SCL / SDA
  labels, each vertical with a 5V global label above and its SCL / SDA global label below, plus the note
  "I2C pull-ups (U26 has none)". The parts drawn twice share their symbol and pin uuids (as every other part does),
  so the main page and the card sheet stay in sync and the card PCB footprints link to the card sheet symbols.
Positions are relative to U26E (main page (59.69, 254), card sheet (185.42, 367.03)).
"""
import json, os, re, sys, uuid

U26E = {'BOOST.kicad_sch': (59.69, 254.0, 'BOOST', '/dc4aa17e-0995-4bac-889e-471ae16ef44e'),
        'BOOST_control_RC2.kicad_sch': (185.42, 367.03, 'BOOST_control_RC2', '/e787d626-5fd8-58e4-8fae-f7770db0d081')}
VALUES = {'R99': ('10k', '1k'), 'R102': ('10k', '1k')}
# symbol origin relative to U26E; ltspice:res pins are at (+1.27, +1.27) and (+1.27, +7.62)
NEW = [('R106', -44.45, -13.97, 'SCL'), ('R107', -35.56, -13.97, 'SDA')]   # R107's text clear of C26's (v1 overlap)
NOTE = (-44.45, 3.81, 'I2C pull-ups\\n(U26 has none)')                     # two lines, clear of the labels and R102
# fixed uuids (same in both files): symbol, pin 1, pin 2
UU = {'R106': ('6c1f7a52-3d0e-4b8a-9a61-5e2b4f0c1061', '0b7e2f61-8a43-4c1d-b6f0-2a9d1e7c1061',
               'd5a9c3e0-71f4-4e2b-8c6d-3f0a2b9e1061'),
      'R107': ('6c1f7a52-3d0e-4b8a-9a61-5e2b4f0c1071', '0b7e2f61-8a43-4c1d-b6f0-2a9d1e7c1071',
               'd5a9c3e0-71f4-4e2b-8c6d-3f0a2b9e1071')}


def f(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def prop(name, val, x, y, hide):
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n%s\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
            '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n') % (
        name, val, f(x), f(y), '\t\t\t(hide yes)\n' if hide else '')


def symbol(ref, x, y, project, path):
    su, p1, p2 = UU[ref]
    s = ('\t(symbol\n\t\t(lib_id "ltspice:res")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
         '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n'
         '\t\t(uuid "%s")\n') % (f(x), f(y), su)
    s += prop('Reference', ref, x + 5.1562, y + 2.54, False)
    s += prop('Value', '4.7k', x + 4.6609, y + 5.08, False)
    s += prop('Footprint', 'Resistor_SMD:R_0603_1608Metric', x, y, True)   # 0603 like the card's other resistors (user, 2026-10-12)
    s += prop('Datasheet', '', x, y, True)
    s += prop('Description', '', x, y, True)
    s += prop('Sim.Device', 'R', x, y, True)
    s += prop('Sim.Params', 'R=${VALUE}', x, y, True)
    s += '\t\t(pin "1"\n\t\t\t(uuid "%s")\n\t\t)\n\t\t(pin "2"\n\t\t\t(uuid "%s")\n\t\t)\n' % (p1, p2)
    s += ('\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "%s"\n\t\t\t\t\t(reference "%s")\n'
          '\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n') % (project, path, ref)
    return s


def wire(x0, y0, x1, y1):
    return ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s)\n\t\t\t(xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
            '\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n') % (f(x0), f(y0), f(x1), f(y1), uuid.uuid4())


def glabel(name, x, y, rot, just):
    return ('\t(global_label "%s"\n\t\t(shape passive)\n\t\t(at %s %s %s)\n\t\t(fields_autoplaced yes)\n'
            '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n'
            '\t\t(uuid "%s")\n\t\t(property "Intersheetrefs" "${INTERSHEET_REFS}"\n\t\t\t(at %s %s 0)\n'
            '\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n'
            '\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n') % (
        name, f(x), f(y), rot, just, uuid.uuid4(), f(x), f(y))


def text(s, x, y):
    return ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n'
            '\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n\t\t(uuid "%s")\n\t)\n') % (
        s, f(x), f(y), uuid.uuid4())


def insert_after_last(t, kind, add):
    """add (LF text) after the last top-level item of this kind ('\\n\\t(wire\\n' ...)."""
    i = t.rfind('\n\t(%s' % kind)
    assert i >= 0, kind
    j = t.find('\n\t)\n', i) + 4
    return t[:j] + add + t[j:]


def edit(path, log):
    name = os.path.basename(path)
    raw = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in raw
    t = raw.replace('\r\n', '\n')
    assert '"Reference" "R106"' not in t and '"Reference" "R107"' not in t
    bx, by, project, spath = U26E[name]
    for ref, (old, new) in VALUES.items():
        i = t.find('(property "Reference" "%s"' % ref)
        m = re.compile(r'\(property "Value" "%s"' % re.escape(old)).search(t, i)
        assert m and m.start() - i < 400, ref
        t = t[:m.start()] + '(property "Value" "%s"' % new + t[m.end():]
        log.append(dict(file=name, what='Value', ref=ref, old=old, new=new))
    wires, labels, syms = '', '', ''
    for ref, dx, dy, net in NEW:
        x, y = bx + dx, by + dy
        px, t1, t2 = x + 1.27, y + 1.27, y + 7.62
        syms += symbol(ref, x, y, project, spath)
        wires += wire(px, t1 - 2.54, px, t1) + wire(px, t2, px, t2 + 2.54)
        labels += glabel('5V', px, t1 - 2.54, 90, 'left') + glabel(net, px, t2 + 2.54, 270, 'right')
        log.append(dict(file=name, what='part added', ref=ref, value='4.7k', at=[round(x, 4), round(y, 4)],
                        pins=[[round(px, 4), round(t1, 4)], [round(px, 4), round(t2, 4)]],
                        wires=[[round(px, 4), round(t1 - 2.54, 4), round(px, 4), round(t1, 4)],
                               [round(px, 4), round(t2, 4), round(px, 4), round(t2 + 2.54, 4)]],
                        labels=[['5V', round(px, 4), round(t1 - 2.54, 4)], [net, round(px, 4), round(t2 + 2.54, 4)]]))
    nx, ny, ns = NOTE
    t = insert_after_last(t, 'wire\n', wires)
    t = insert_after_last(t, 'global_label ', labels)
    t = insert_after_last(t, 'text ', text(ns, bx + nx, by + ny))
    t = insert_after_last(t, 'symbol\n', syms)
    log.append(dict(file=name, what='note added', at=[round(bx + nx, 4), round(by + ny, 4)], text=ns))
    if crlf:
        t = t.replace('\n', '\r\n')
    open(path, 'w', encoding='utf-8', newline='').write(t)


def main():
    d, logp = sys.argv[1], sys.argv[2]
    log = []
    for n in U26E:
        edit(os.path.join(d, n), log)
    json.dump(log, open(logp, 'w'), indent=1)
    for r in log:
        print(r)


if __name__ == '__main__':
    main()
