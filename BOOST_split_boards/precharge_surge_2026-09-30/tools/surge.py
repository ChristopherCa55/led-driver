"""Pre-charge diode surge summary: python surge.py CASE ..."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, r'C:/Users/bubba/AppData/Local/Temp/claude/C--Users-bubba-OneDrive-Documents-led-driver/14c8a43e-d3bb-4a1c-bb90-a19d4b04633d/scratchpad/tools')
from analyze_edges import read_raw, Sig
for case in sys.argv[1:]:
    mm, idx = read_raw(os.path.join(HERE, case + '.raw'))
    s = Sig(mm, idx)
    t = s.t
    ok = np.flatnonzero(np.diff(t) > 0); n = ok[-1] + 1; t = t[:n]
    line = [case]
    tot = None
    for c in (1, 2, 3):
        i = s('i(dpre%d)' % c)[:n].astype(np.float64)
        pk = i.max()
        above = i > 0.1 * pk
        w = float(np.sum(np.diff(t)[above[:-1]]))
        vf = (s('v(vin)')[:n].astype(np.float64) - s('v(vout_%d)' % c)[:n].astype(np.float64))[np.argmax(i)]
        line.append('D%d pk %.1f A  I2t %.3f A2s  >10%%pk %.0f us  VF@pk %.2f V' % (27 + c, pk, np.trapezoid(i ** 2, t), w * 1e6, vf))
        tot = i if tot is None else tot + i
    if s.has('i(rbatt)'):
        ib = np.abs(s('i(rbatt)')[:n].astype(np.float64))
        line.append('battery pk %.0f A' % ib.max())
    print('\n   '.join(line))
