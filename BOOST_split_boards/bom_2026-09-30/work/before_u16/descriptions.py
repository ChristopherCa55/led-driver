"""Short plain-English part descriptions for the BOM (2026-10-01), e.g. "220 uF 50 V hybrid polymer electrolytic".

short(lcsc, snap_row, value) -> str. Passive values come from the JLC listing; everything else from the table below.
"""
import re

FIXED = {
    'C4979367': '47 uF 25 V tantalum capacitor (low ESR, case D)',
    'C29664285': '680 uF 25 V hybrid polymer electrolytic capacitor',
    'C6843593': '220 uF 50 V hybrid polymer electrolytic capacitor (Panasonic ZU)',
    'C385885': '220 uF 50 V hybrid polymer electrolytic capacitor (Panasonic ZS)',
    'C8598': 'Schottky diode 40 V 1 A',
    'C21565': 'switching diode 200 V 0.2 A',
    'C128729': 'rectifier diode 1000 V 2 A',
    'C42394451': 'TVS diode 54 V stand-off, 5 kW',
    'C2076400': 'current-sense resistor 1 mOhm 4 W, 4-terminal',
    'C413486': 'current-sense resistor 50 mOhm 1 W, metal strip',
    'C43116': 'linear regulator 5 V 100 mA',
    'C49889': 'op-amp, rail-to-rail, 550 kHz',
    'C398363': 'op-amp, rail-to-rail, 1 MHz',
    'C601651': 'isolated dual gate driver',
    'C2877347': 'low-dropout regulator 12 V 1 A',
    'C2866640': 'low-dropout regulator 12 V 1 A',
    'C127023': 'low-dropout regulator 12 V 1 A',
    'C22427873': 'current-sense amplifier, gain 100',
    'C81598': 'small-signal diode 75 V',
    'C22629': 'Schottky diode 30 V 0.2 A',
    'C53444': 'PNP transistor 40 V',
    'C117501': 'comparator, push-pull, 56 ns',
    'C11349': 'decade counter (CMOS 4017)',
    'C145613': 'quad digital potentiometer 10 kOhm, I2C',
    'C9386': '8-channel analog multiplexer',
    'C5586': 'quad 2-input NAND gate',
    'C5605': 'hex Schmitt-trigger inverter',
    'C179842': 'quad analog switch',
}
MANUAL = {   # parts with no LCSC line (fitted or owned by you)
    'ESQ-115-44-G-D': '2x15 socket strip, 2.54 mm, elevated (Samtec)',
    'TSW-115-07-G-D': '2x15 pin header, 2.54 mm (Samtec)',
    'CSCF3218-6R8MC': '6.8 uH power inductor, 32 x 22.5 mm',
    'HYG180N10': '100 V N-channel MOSFET (TO-220)',
}


def short(lcsc, s, value):
    if lcsc in FIXED:
        return FIXED[lcsc]
    if not s:
        for k, v in MANUAL.items():
            if k in value:
                return v
        return value
    d = s.get('desc') or ''
    cat = s.get('cat') or ''
    pkg = s.get('pkg') or ''
    if 'Resistor' in cat:
        m = re.search(r'(\d+(?:\.\d+)?[kKM]?)\s*(?:Ω|ohm)', d)
        v = m.group(1).replace('K', 'k') if m else value
        return 'resistor %s ohm 1 %% (%s)' % (v, pkg)
    if 'Capacitor' in cat and 'MLCC' in cat:
        c = re.search(r'(\d+(?:\.\d+)?\s*[pnu]F)', d)
        v = re.search(r'(\d+(?:\.\d+)?)V', d)
        di = re.search(r'\b(C0G|NP0|X7R|X5R|X7S|X6S)\b', d)
        return 'ceramic capacitor %s %s V %s (%s)' % (c.group(1) if c else value, v.group(1) if v else '?',
                                                    di.group(1) if di else '', pkg)
    return value
