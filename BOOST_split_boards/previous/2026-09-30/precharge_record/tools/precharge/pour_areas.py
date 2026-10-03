"""Compare the filled copper area of every zone, per layer, between two boards (KiCad 10 Python).

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" pour_areas.py BEFORE.kicad_pcb AFTER.kicad_pcb

Prints every zone/layer whose area changed by more than 0.02 mm2. For the pre-charge change the expected result is:
only GND pours, the GND planes (In1/In6), the 5V plane (In4), "Vout_2 In5 to J8" (In5, about -1.5 mm2) and the three
Vout_3 inner pours (about -1.2 mm2 each) change; every Vin, Vout_1, Output*_drain, LX and rsense_lo pour is unchanged.
"""
import sys
import pcbnew


def areas(path):
    b = pcbnew.LoadBoard(path)
    out = {}
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for l in z.GetLayerSet().Seq():
            key = (z.GetNetname(), z.GetZoneName(), b.GetLayerName(l))
            out[key] = out.get(key, 0.0) + abs(z.GetFilledPolysList(l).Area()) / 1e12
    return out


A, B = areas(sys.argv[1]), areas(sys.argv[2])
print('%-14s %-28s %-7s %10s %10s %8s' % ('net', 'zone', 'layer', 'before', 'after', 'delta'))
for k in sorted(set(A) | set(B)):
    a, b = A.get(k, 0.0), B.get(k, 0.0)
    if abs(a - b) > 0.02:
        print('%-14s %-28s %-7s %10.2f %10.2f %+8.2f' % (k[0], k[1], k[2], a, b, b - a))
bad = [k for k in set(A) | set(B) if abs(A.get(k, 0) - B.get(k, 0)) > 0.02
       and k[0] not in ('GND', '5V', 'Vout_2', 'Vout_3')]
print('OK - only the expected pours changed' if not bad else 'CHECK - unexpected pour changes: %s' % sorted(bad))
