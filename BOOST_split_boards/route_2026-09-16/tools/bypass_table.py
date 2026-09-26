"""Bypass capacitor distances: capacitor pad centre -> IC pin centre, per supply pin pair (system Python).

usage: python bypass_table.py FOOTPRINTS.json [BEFORE_FOOTPRINTS.json]
"""
import json, math, sys

ROWS = [  # (IC, supply pin, return pin(s), capacitor, role, target mm)
    ('U19', '16', ['14'], 'C31', 'VDDA/VSSA 1 uF (M1 driver)', 3.0),
    ('U19', '3', ['2', '4'], 'C48', 'VCCI 100 nF', 5.0),
    ('U15', '11', ['9'], 'C51', 'VDDB/VSSB 100 nF (paired links)', 5.0),
    ('U15', '11', ['9'], 'C18', 'VDDB/VSSB 2.2 uF', 10.0),
    ('U15', '3', ['4'], 'C62', 'VCCI 1 uF', 3.0),
    ('U10', '11', ['9'], 'C50', 'VDDB/VSSB 100 nF', 3.0),
    ('U10', '11', ['9'], 'C16', 'VDDB/VSSB 2.2 uF (next closest)', 99),
    ('U10', '3', ['4', '5'], 'C90', 'VCCI 100 nF', 3.0),
    ('U8', '11', ['9'], 'C61', 'VDDB/VSSB 100 nF', 3.0),
    ('U8', '11', ['9'], 'C60', 'VDDB/VSSB 2.2 uF (next closest)', 99),
    ('U8', '3', ['4'], 'C89', 'VCCI 1 uF', 5.0),
]


def load(p):
    return {f['ref']: f for f in json.load(open(p))}


def dist(fps, ic, sup, rets, cap):
    pads = {p['num']: p for p in fps[ic]['pads']}
    s = pads[sup]
    cp = fps[cap]['pads']
    ds = [p for p in cp if p['net'] == s['net']]
    rs = [p for p in cp if p['net'] != s['net']]
    d1 = min(math.hypot(p['x'] - s['x'], p['y'] - s['y']) for p in ds)
    d2 = min(math.hypot(p['x'] - pads[r]['x'], p['y'] - pads[r]['y']) for p in rs for r in rets)
    return d1, d2


now = load(sys.argv[1])
before = load(sys.argv[2]) if len(sys.argv) > 2 else None
print('| IC | Supply pin / return pin | Capacitor | %sNow: supply pad, return pad (mm) | Target |' % ('Before (mm) | ' if before else ''))
print('|---|---|---|%s---|---|' % ('---|' if before else ''))
for ic, sup, rets, cap, role, lim in ROWS:
    d1, d2 = dist(now, ic, sup, rets, cap)
    b = ''
    if before:
        b1, b2 = dist(before, ic, sup, rets, cap)
        b = '%.1f, %.1f | ' % (b1, b2)
    print('| %s | %s / %s | %s %s | %s%.1f, %.1f | %s |' % (ic, sup, '/'.join(rets), cap, role, b, d1, d2,
          ('<= %.0f' % lim) if lim < 99 else 'next closest'))
