"""Show a part's pins in an .asc and every wire end, wire interior, flag and other pin at those points.
python asc_probe.py FILE.asc INST [INST ...]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ascgeo import Asc

a = Asc(sys.argv[1])
for inst in sys.argv[2:]:
    s = a.byname[inst]
    print(inst, s['sym'], s['x'], s['y'], s['rot'])
    for name, x, y in a.pins(s):
        hits = []
        for (ln, x1, y1, x2, y2) in a.wires:
            if (x, y) in ((x1, y1), (x2, y2)):
                hits.append('wire end %s' % ((x1, y1, x2, y2),))
            elif (x1 == x2 == x and min(y1, y2) < y < max(y1, y2)) or (y1 == y2 == y and min(x1, x2) < x < max(x1, x2)):
                hits.append('wire interior %s' % ((x1, y1, x2, y2),))
        for (ln, fx, fy, n) in a.flags:
            if (fx, fy) == (x, y):
                hits.append('flag %s' % n)
        for o in a.syms:
            if o is s:
                continue
            for n2, x2, y2 in a.pins(o):
                if (x2, y2) == (x, y):
                    hits.append('pin %s.%s' % (o['attr'].get('InstName'), n2))
        print('   pin %-4s (%d, %d): %s' % (name, x, y, '; '.join(hits) or 'NOTHING'))
