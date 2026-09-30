"""Add the pre-charge diodes D28-D30 (S2MW, Vin -> Vout_1/2/3) to the LTspice schematic BOOST.asc, in place.

    python add_precharge_asc.py PATH\\TO\\BOOST.asc

Plain text edit, latin-1 and LF line ends kept. Refuses to run if D28-D30 already exist. Each diode is LTspice's
built-in "diode" symbol, R0 (anode "+" pin at symbol origin + (16, 0), cathode "-" pin at + (16, 64)), placed in the
empty area right of the drawing (x 3584-3856, y -1200). They connect by net-name flags on the pin ends: "Vin" on the
anode, "Vout_n" on the cathode (the same flag names the schematic already uses). The S2MW model goes in one TEXT
directive under them; it is NOT a vendor model (Jingdao publishes none): it is LTspice's 1N4007 model scaled to a
2 A die (IS x2, RS /2), giving VF = 0.91 V at 2 A against the datasheet's 1.1 V maximum.
"""
import sys

ASC = sys.argv[1]
DIODES = [('D28', 'Vout_1', 3584), ('D29', 'Vout_2', 3712), ('D30', 'Vout_3', 3840)]
Y = -1200
MODEL = '.model S2MW D(IS=14n RS=17m N=1.8 CJO=25p M=0.333 TT=3u BV=1000 IBV=5u)'
NOTE = (';D28-D30: pre-charge diodes Vin -> Vout_1/2/3 (Jingdao S2MW, 1000 V 2 A, IFSM 50 A).\\n'
        'Model scaled from LTspice\'s 1N4007 to a 2 A die - VF 0.91 V at 2 A (datasheet max 1.1 V). Not a vendor model.')

raw = open(ASC, 'rb').read()
if b'\r\n' in raw:
    sys.exit('STOP: BOOST.asc has CRLF line ends - not the expected file. Nothing changed.')
txt = raw.decode('latin-1')
lines = txt.split('\n')
for ref, *_ in DIODES:
    if 'SYMATTR InstName %s' % ref in lines:
        sys.exit('STOP: %s already in BOOST.asc - this script has run before. Nothing changed.' % ref)
if '.model S2MW' in txt:
    sys.exit('STOP: a .model S2MW line already exists. Nothing changed.')
for ref, net, x in DIODES:
    for yy in (Y, Y + 64):
        for l in lines:
            p = l.split()
            if p[:1] == ['FLAG'] and int(p[1]) == x + 16 and int(p[2]) == yy:
                sys.exit('STOP: something already sits at (%d, %d). Nothing changed.' % (x + 16, yy))
last_flag = max(i for i, l in enumerate(lines) if l.startswith('FLAG '))
first_text = min(i for i, l in enumerate(lines) if l.startswith('TEXT '))
flags = []
for ref, net, x in DIODES:
    flags += ['FLAG %d %d Vin' % (x + 16, Y), 'FLAG %d %d %s' % (x + 16, Y + 64, net)]
syms = []
for ref, net, x in DIODES:
    syms += ['SYMBOL diode %d %d R0' % (x, Y), 'SYMATTR InstName %s' % ref, 'SYMATTR Value S2MW']
texts = ['TEXT 3576 -1072 Left 2 !%s' % MODEL, 'TEXT 3576 -1024 Left 2 %s' % NOTE]
# symbols go just before the first TEXT line (end of the SYMBOL section); flags after the last FLAG; texts at the end
end = len(lines) - 1 if lines[-1] == '' else len(lines)
new = lines[:last_flag + 1] + flags + lines[last_flag + 1:first_text] + syms + lines[first_text:end] + texts
if lines[-1] == '':
    new.append('')
open(ASC, 'wb').write('\n'.join(new).encode('latin-1'))
print('added D28-D30 (S2MW) with Vin / Vout_n flags and the .model S2MW directive to', ASC)
