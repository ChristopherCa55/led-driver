"""Step 1, LTspice documentation fixes (user's answers of 2026-10-11, ANSWERS.md), into a NEW file.

    python step01_ltspice.py SRC.asc OUT.asc

- D8: the eight notes of the approved mock-up (tools/mock_notes.py v4 positions).
- D5: the `.ic` keeps only V(Out) and V(Out-): V(C10), V(C5), V(C2) name no node (removing them gives bit-identical
  waveforms, work/sims/base_clean); the commented-out `.ic V(Vout_1)=30 ...` line is deleted.
- D7: each diode valued "D" shows its part name (as in the BOM); a `.model NAME D` alias per name keeps LTspice's
  default diode model, so the simulation is unchanged.
Everything else is written back byte for byte (ascmodel keeps untouched lines). Prints the change list (x, y).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'ltspice_layout_2026-10-05', 'tools')))
import ascmodel as A
from mock_notes import NOTES

IC_OLD = 'TEXT -6376 -4352 Left 2 !.ic V(Out)=0 V(Out-)=1 V(C10)=0 V(C5)=0 V(C2)=0'
IC_NEW = 'TEXT -6376 -4352 Left 2 !.ic V(Out)=0 V(Out-)=1'
IC_COMMENT = 'TEXT -6416 -3488 Left 2 ;.ic V(Vout_1)=30 V(Vout_2)=38 V(Vout_3)=30'
PARTS = {  # from the BOM (SOURCING_TABLE): power D2 D8 D11 D13 D14 D22 B5819W, D9 D10 D21 BAV21W;
           # card D1 D3 D4 D5 D6 D7 D15 D20 D24 D27 1N4148W, D23 D25 D26 BAT54WS
    'B5819W': ['D2', 'D8', 'D11', 'D13', 'D14', 'D22'],
    'BAV21W': ['D9', 'D10', 'D21'],
    '1N4148W': ['D1', 'D3', 'D4', 'D5', 'D6', 'D7', 'D15', 'D20', 'D24', 'D27'],
    'BAT54WS': ['D23', 'D25', 'D26'],
}
MODELS_TEXT = ("TEXT -5520 -4024 Left 2 !* diode part names: LTspice's default diode, as before\\n"
               ".model 1N4148W D\\n.model B5819W D\\n.model BAV21W D\\n.model BAT54WS D")


def main():
    src, out = sys.argv[1], sys.argv[2]
    a = A.Asc(src)
    log = []
    i = a.texts.index(IC_OLD)
    a.texts[i] = IC_NEW
    log.append('directive at (-6376, -4352): .ic now V(Out)=0 V(Out-)=1 (removed V(C10)=0 V(C5)=0 V(C2)=0)')
    a.texts.remove(IC_COMMENT)
    log.append('comment deleted at (-6416, -3488): ;.ic V(Vout_1)=30 V(Vout_2)=38 V(Vout_3)=30')
    a.texts.append(MODELS_TEXT)
    log.append('directive added at (-5520, -4024): .model aliases 1N4148W / B5819W / BAV21W / BAT54WS = D')
    for x, y, just, txt in NOTES:
        a.texts.append('TEXT %d %d %s 2 ;%s' % (x, y, just, txt))
        log.append('note added at (%d, %d): %s' % (x, y, txt.replace('\\n', ' / ')))
    want = {d: p for p, ds in PARTS.items() for d in ds}
    done = set()
    for s in a.syms:
        if s.name in want:
            assert s.sym == 'diode', (s.name, s.sym)
            assert 'Value' not in dict(s.attrs), (s.name, s.attrs)
            s.attrs.append(('Value', want[s.name]))
            done.add(s.name)
            log.append('value set at (%d, %d): %s = %s (was the default D)' % (s.x, s.y, s.name, want[s.name]))
    assert done == set(want), set(want) - done
    a.write(out)
    print('\n'.join(log))
    print('wrote', out)


if __name__ == '__main__':
    main()
