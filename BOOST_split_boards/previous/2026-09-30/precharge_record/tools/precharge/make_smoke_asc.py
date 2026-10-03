"""Make a short smoke-test copy of BOOST.asc: 3 ms, a few saved signals, and .meas lines that print the results
into the LTspice log.

    python make_smoke_asc.py WORKCOPY\\BOOST.asc WORKCOPY\\BOOST_smoke.asc

Only for a scratch copy of the LTspice folder - never point it at the real BOOST.asc.
Expected log lines after "LTspice.exe -b BOOST_smoke.asc" (LTspice 26.0.1, 2026-09-29):
    lxmax:  MAX(v(lx))   about 81 V   at about 0.15 ms  (see the handoff, section 8: a start-state artefact)
    id28max / id29max / id30max: MAX(i(d2x))  about 81 A each (the pre-charge pulse at t = 0)
    vout1end / vout2end / vout3end: about 24.3 / 31.1 / 31.7 V
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
t = open(src, 'rb').read().decode('latin-1')
old = 'TEXT -2224 1120 Left 2 !.tran 30m startup uic'
assert t.count(old) == 1, 'the .tran line is not the expected one'
meas = '\\n'.join(['.meas TRAN LXmax MAX V(lx)', '.meas TRAN ID28max MAX I(D28)', '.meas TRAN ID29max MAX I(D29)',
                   '.meas TRAN ID30max MAX I(D30)', '.meas TRAN Vout1end FIND V(vout_1) AT 2.99m',
                   '.meas TRAN Vout2end FIND V(vout_2) AT 2.99m', '.meas TRAN Vout3end FIND V(vout_3) AT 2.99m'])
t = t.replace(old, 'TEXT -2224 1120 Left 2 !.tran 3m startup uic\n'
                   'TEXT -2224 1160 Left 2 !.save V(vin) V(lx) I(D19) V(vout_1) V(vout_2) V(vout_3) I(D28) I(D29) I(D30)\n'
                   'TEXT -2224 1200 Left 2 !' + meas)
open(dst, 'wb').write(t.encode('latin-1'))
print('wrote', dst)
