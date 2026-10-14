"""Proposed schematic notes (FIX_PROMPT D8), drawn into a NEW copy of BOOST.asc for pictures only.

    python mock_notes.py SRC.asc OUT.asc

Adds comment TEXT lines (size 2, the user's note size) next to their parts. Nothing else changes; Asc.write refuses
to overwrite. The wording is a PROPOSAL for the user to approve, change or reject.
"""
import os, sys
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                                                 'ltspice_layout_2026-10-05', 'tools')))
import ascmodel as A

NOTES = [
    # item 8: the one-hot select (right of U28's Verr1/2/3 labels)
    (1921, -6383, 'Left', r'one-hot from U18: picks Verr1/2/3'),
    # items 8 + 11: U18 (under its value): the Q3 reset and the hidden supply
    (1216, -5927, 'Left', r'Q3 resets it: counts Q0-Q2 only\n5V by net name (SpiceModel)'),
    # item 9: latch (under U101D)
    (3488, -6096, 'Left', r'latch: set- low turns M1 on\nRESET- low turns it off'),
    # item 9: channel enable delay (right of C17, the user's M1 INHIBIT wording, shortened)
    (4336, -6600, 'Left', r'rc: slow turn on\ndiode: fast off'),
    # item 9: gate drivers (U15's DT pin; U19's unused B side)
    (-1974, -8524, 'Left', r'DT = VCCI:\nno dead time'),
    (-3584, -6222, 'Left', r'ch B unused'),
    # item 11: "same as channel 1" under the ch2 / ch3 headroom-servo titles
    (672, -3440, 'Left', r'same as channel 1'),
    (4176, -3536, 'Left', r'same as channel 1'),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    a = A.Asc(src)
    for x, y, just, txt in NOTES:
        a.texts.append('TEXT %d %d %s 2 ;%s' % (x, y, just, txt))
    a.write(out)
    print('wrote %s with %d proposed notes' % (out, len(NOTES)))


if __name__ == '__main__':
    main()
