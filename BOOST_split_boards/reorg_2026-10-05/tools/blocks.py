"""Functional blocks shared by the LTspice and KiCad schematics (2026-10-05).

    python blocks.py SCH NETLIST ASSIGNMENT.json OUT.json

Every placed KiCad symbol instance (key: reference, plus the unit letter for multi-unit parts, e.g. U101A) goes into
one block. LTspice uses the same keys (its gate units are named U101A, ...), plus the SIM_* test-bench parts.
Seeds below fix the main parts; every other part joins the block it is wired to most (rails excluded, each net
weighted 1/(pins-1)), iterating; anything left joins the nearest seeded part on its own board.
"""
import sys, os, json, re, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ksch, knet

BLOCKS = [  # id, board, title
    ('P1', 'POWER', 'Battery input and input-current sense'),
    ('P2', 'POWER', 'Boost power stage and output banks'),
    ('P3a', 'POWER', 'LED channel 1 current regulator'),
    ('P3b', 'POWER', 'LED channel 2 current regulator'),
    ('P3c', 'POWER', 'LED channel 3 current regulator'),
    ('P4a', 'POWER', 'Gate driver: M1 (boost switch)'),
    ('P4b', 'POWER', 'Gate driver: channel 1 switches M2/M7'),
    ('P4c', 'POWER', 'Gate driver: channel 2 switches M3/M6'),
    ('P4d', 'POWER', 'Gate driver: channel 3 switches M4/M5'),
    ('P5', 'POWER', 'Supplies: 12 V and two 5 V regulators'),
    ('PJ', 'POWER', 'Card connector and mounting holes'),
    ('C1', 'CONTROL', 'Arduino interface and LED-current references'),
    ('C2a', 'CONTROL', 'Channel 1 output-voltage error amplifier'),
    ('C2b', 'CONTROL', 'Channel 2 output-voltage error amplifier'),
    ('C2c', 'CONTROL', 'Channel 3 output-voltage error amplifier'),
    ('C3', 'CONTROL', 'Error select and comparators'),
    ('C4', 'CONTROL', 'Channel sequencer and low-error timeout'),
    ('C5a', 'CONTROL', 'Channel 1 reference sample-and-hold'),
    ('C5b', 'CONTROL', 'Channel 2 reference sample-and-hold'),
    ('C5c', 'CONTROL', 'Channel 3 reference sample-and-hold'),
    ('C6', 'CONTROL', 'Gate-enable logic and M1 inhibit'),
    ('C7', 'CONTROL', 'Logic supplies and spare gates'),
    ('CJ', 'CONTROL', 'Power-board connector and mounting holes'),
]
SEEDS = {
    'P1': 'J1 J2 R1 C40 C69 C85 U25',
    'P2': 'L1 R14 M1 D19 M2 M3 M4 M5 M6 M7 D28 D29 D30 C1 C72 C70 C86 C88 C3 C73 C71 C78 C87 C4 C76 C74 C75 C77',
    'P3a': 'J3 J4 M10 R52 NT1 U11 C45',
    'P3b': 'J8 J7 M9 R53 NT2 U12 C44',
    'P3c': 'J5 J6 M8 R7 NT3 U6 C41',
    'P4a': 'U19', 'P4b': 'U15', 'P4c': 'U10', 'P4d': 'U8',
    'P5': 'U16 U1 U17',
    'PJ': 'J10 H5 H6 H7 H8',
    'C1': 'J9 U26A U26B U26C U26D U26E',
    'C2a': 'U3', 'C2b': 'U7', 'C2c': 'U13',
    'C3': 'U28 U4 U5 U2',
    'C4': 'U18 U14 Q1',
    'C5a': 'U24', 'C5b': 'U23', 'C5c': 'U22',
    'C6': 'U101A U101B U101C U101D U102A U102B U102C U102D U103A U103B U104A U104B U104C U104D U104E U104F '
          'U105A U105B U21',
    'C7': 'U101E U102E U103E U104G U105G U106D U106E U103C U103D U105C U105D U105E U105F C94 C95 C96 C97 C98 C99',
    'CJ': 'J11 H1 H2 H3 H4',
}
OVERRIDE = {  # checked by hand against the nets (2026-10-05)
    'D11': 'P4b', 'R13': 'P4b', 'R75': 'P4b', 'R76': 'P4b',          # M2/M7 gate network and pulldowns
    'R104': 'P4a', 'C89': 'P4a', 'C90': 'P4a', 'C31': 'P4a',          # M1 pulldown; U19 decoupling
    'C48': 'P4c', 'C62': 'P4c',                                       # U10 decoupling
    'R27': 'C2a', 'R28': 'C2a', 'C13': 'C2a',                         # error-amp output filters, per channel
    'R37': 'C2b', 'R38': 'C2b', 'C11': 'C2b',
    'R45': 'C2c', 'R46': 'C2c', 'C10': 'C2c',
    'D26': 'C5a', 'D25': 'C5b', 'D23': 'C5c',                         # sample-and-hold output diodes
    'R25': 'C5b', 'R36': 'C5b',                                       # channel 2 drain divider
    'C47': 'C1',                                                      # Vref_3 filter, like C93 / C103
}
RAILS = {'GND', '5V', '12V', 'analog_5V', 'Vin', 'Vout_1', 'Vout_2', 'Vout_3', 'LX', 'm2_source', 'm3_source',
         'm4_source'}


def main():
    sch = ksch.Sch(sys.argv[1])
    comps, kpins, knets = knet.load(sys.argv[2])
    asg = json.load(open(sys.argv[3]))
    inst = {}                                     # key -> symbol
    for s in sch.syms:
        if not s['power']:
            inst[sch.key(s)] = s
    # (ref, pin) -> instance key (common unit-0 pins go to the lowest unit)
    pin_key = {}
    for k in sorted(inst, key=lambda k: inst[k]['unit']):
        s = inst[k]
        for n, name, x, y, et, hid in sch.pins(s):
            pin_key.setdefault((s['ref'], n), k)
    blk = {}
    for b, refs in SEEDS.items():
        for k in refs.split():
            if k not in inst:
                print('seed not in schematic:', k)
                continue
            blk[k] = b
    board_of = {b: bd for b, bd, _ in BLOCKS}
    # neighbours through non-rail nets
    nb = collections.defaultdict(collections.Counter)
    for net, members in knets.items():
        if net in RAILS:
            continue
        keys = [pin_key.get((r, p)) for r, p in members if not r.startswith('#')]
        keys = [k for k in keys if k]
        if len(keys) < 2:
            continue
        w = 1.0 / (len(keys) - 1)
        for a in keys:
            for b in keys:
                if a != b:
                    nb[a][b] += w
    changed = True
    while changed:
        changed = False
        for k in inst:
            if k in blk:
                continue
            sc = collections.Counter()
            for o, w in nb[k].items():
                if o in blk and board_of[blk[o]] == asg.get(inst[k]['ref']):
                    sc[blk[o]] += w
            if sc:
                blk[k] = sc.most_common(1)[0][0]
                changed = True
    for k in inst:
        if k in blk:
            continue
        s = inst[k]
        cands = [(math.hypot(s['x'] - inst[o]['x'], s['y'] - inst[o]['y']), b) for o, b in blk.items()
                 if board_of[b] == asg.get(s['ref']) and o in inst]
        blk[k] = min(cands)[1]
        print('nearest:', k, '->', blk[k])
    for k, b in OVERRIDE.items():
        assert k in inst, k
        blk[k] = b
    bad = [k for k in inst if board_of[blk[k]] != asg.get(inst[k]['ref'])]
    if bad:
        print('BOARD MISMATCH', bad)
    out = {'blocks': [dict(id=b, board=bd, title=t) for b, bd, t in BLOCKS], 'member': blk}
    json.dump(out, open(sys.argv[4], 'w'), indent=1)
    by = collections.defaultdict(list)
    for k, b in blk.items():
        by[b].append(k)
    for b, bd, t in BLOCKS:
        ks = sorted(by[b], key=lambda k: (re.sub(r'\d.*', '', k), int(re.sub(r'\D', '', k) or 0), k))
        print('%-4s %-7s %3d  %s' % (b, bd, len(ks), ' '.join(ks)))


if __name__ == '__main__':
    main()
