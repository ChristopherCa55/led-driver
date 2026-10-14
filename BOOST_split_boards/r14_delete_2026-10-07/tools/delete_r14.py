"""Delete R14 (1 Meg, LX to GND) from the KiCad schematic and the power PCB of one KiCad folder.

    python delete_r14.py KICAD_DIR

Approved by the user on 2026-10-07 ("delete it on ltspice, kicad schematic, and kicad pcb").

Schematic (BOOST.kicad_sch):
  - the R14 symbol;
  - the GND power symbol sitting on R14's pin 2 (it connected to nothing else);
  - the junction dot at R14's pin 1 on the LX wire (only two collinear wires meet there now).
PCB (BOOST_power_RC2.kicad_pcb):
  - footprint R14;
  - the copper that existed only to reach it: the 1 mm F.Cu stub from its LX pad, the via under it, the seven 1 mm
    B.Cu segments and the via where they joined the In2.Cu LX pour.
Zones are NOT refilled here: run kicad-cli pcb drc --refill-zones --save-board afterwards.
Each removal must match exactly once, or nothing is written.
"""
import os, re, sys

NL, TAB = '\n', '\t'


def top_blocks(text, kind):
    pat = NL + TAB + '(' + kind
    i = 0
    while True:
        i = text.find(pat, i)
        if i < 0:
            return
        if text[i + len(pat)] not in (NL, ' '):
            i += 1
            continue
        k = text.find(NL + TAB + ')', i + 1)
        yield i + 1, k + 3, text[i + 1:k + 3]
        i = k


def cut(text, spans):
    for s, e in sorted(spans, reverse=True):
        text = text[:s] + text[e:]
    return text


def fix_sch(path):
    t = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in t
    t = t.replace('\r\n', NL)
    spans = []
    r14 = [(s, e) for s, e, b in top_blocks(t, 'symbol') if '(property "Reference" "R14"' in b]
    gnd = [(s, e) for s, e, b in top_blocks(t, 'symbol')
           if '(uuid "6b451c86-47f4-43e0-b3f0-83d4a368d4ca")' in b and '(lib_id "ltspice:GND")' in b
           and '(at 222.25 140.97 ' in b]
    jun = [(s, e) for s, e, b in top_blocks(t, 'junction') if re.search(r'\(at 222\.25 134\.62\)', b)]
    for name, found in (('R14 symbol', r14), ('GND symbol on R14 pin 2', gnd), ('junction at R14 pin 1', jun)):
        if len(found) != 1:
            raise SystemExit('schematic: %s found %d times; nothing written' % (name, len(found)))
        spans += found
    t = cut(t, spans)
    open(path, 'w', encoding='utf-8', newline='').write(t.replace(NL, '\r\n') if crlf else t)
    print('schematic: removed R14, its GND symbol and the junction at its LX pin')


SEGS = [((91.75, 44.15), (91.75, 45.85), 'F.Cu'),
        ((91.75, 45.85), (91.65, 45.85), 'B.Cu'), ((91.65, 45.85), (91.35, 46.15), 'B.Cu'),
        ((91.35, 46.15), (91.35, 46.25), 'B.Cu'), ((91.35, 46.25), (91.15, 46.45), 'B.Cu'),
        ((91.15, 46.45), (91.15, 46.55), 'B.Cu'), ((91.15, 46.55), (91.05, 46.65), 'B.Cu'),
        ((91.05, 46.65), (91.05, 46.75), 'B.Cu')]
VIAS = [(91.75, 45.85), (91.05, 46.75)]


def fix_pcb(path):
    t = open(path, encoding='utf-8', newline='').read()
    crlf = '\r\n' in t
    t = t.replace('\r\n', NL)
    spans = []
    fp = [(s, e) for s, e, b in top_blocks(t, 'footprint') if '(property "Reference" "R14"' in b]
    if len(fp) != 1:
        raise SystemExit('pcb: footprint R14 found %d times' % len(fp))
    spans += fp
    segs = list(top_blocks(t, 'segment'))
    for a, b2, lay in SEGS:
        hits = []
        for s, e, blk in segs:
            m1 = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', blk)
            m2 = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', blk)
            p1 = (float(m1.group(1)), float(m1.group(2)))
            p2 = (float(m2.group(1)), float(m2.group(2)))
            if {p1, p2} == {a, b2} and '(layer "%s")' % lay in blk and '(net "LX")' in blk:
                hits.append((s, e))
        if len(hits) != 1:
            raise SystemExit('pcb: segment %s-%s %s found %d times' % (a, b2, lay, len(hits)))
        spans += hits
    vias = list(top_blocks(t, 'via'))
    for v in VIAS:
        hits = [(s, e) for s, e, blk in vias if re.search(r'\(at %s %s\)' % (re.escape(repr(v[0]).rstrip('0')),
                                                                     re.escape(repr(v[1]).rstrip('0'))), blk)
                and '(net "LX")' in blk]
        if len(hits) != 1:
            raise SystemExit('pcb: via at %s found %d times' % (v, len(hits)))
        spans += hits
    t = cut(t, spans)
    open(path, 'w', encoding='utf-8', newline='').write(t.replace(NL, '\r\n') if crlf else t)
    print('pcb: removed footprint R14, %d LX segments and %d LX vias' % (len(SEGS), len(VIAS)))


if __name__ == '__main__':
    d = sys.argv[1]
    fix_sch(os.path.join(d, 'BOOST.kicad_sch'))
    fix_pcb(os.path.join(d, 'BOOST_power_RC2.kicad_pcb'))
