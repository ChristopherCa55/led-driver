# Exec'd by cost_summary.py after the totals are computed (uses P_, C_, stock, m, PCB, CARD_SINGLE, N, HERE).
# Builds SHORT_NOTE (stock warnings), STOCK_MD (stock section) and SAVINGS_MD ("Ways to save"), 2026-10-01.
# Candidate prices: bom/jlc_snapshot_2026-10-01.json (tools/jlc_parts.py snapshot).
import json as _json, os as _os

CAND = _json.load(open(_os.path.join(HERE, 'bom', 'jlc_snapshot_2026-10-01.json'), encoding='utf-8'))['res']


def _need(code):
    return sum(l['qty'] for o in (P_, C_) for l in o['lines'] if l['lcsc'] == code)


def _p(code):
    return (stock.get(code) or CAND.get(code))['p1']


ZU, ZS = 'C6843593', 'C385885'
OPAMP = 'C398363' if any(l['lcsc'] == 'C398363' for o in (P_, C_) for l in o['lines']) else 'C49889'
SHORT_NOTE = []

# ---- stock section ----
codes = []
for o in (P_, C_):
    for l in o['lines']:
        if l['lcsc'] not in codes:
            codes.append(l['lcsc'])
short = [c for c in codes if stock[c]['stock'] < _need(c)]
tight = [c for c in codes if c not in short and (stock[c]['stock'] < 3 * _need(c) or stock[c]['stock'] < 100)]
NOTES = {
    'C49889': 'shared: 6 per card, 3 per power board',
    ZU: 'now only C74, C86 and C87 (6 for two boards)',
}
for c in short:
    SHORT_NOTE.append('> **Stock problem:** %s (%s) has %d in stock; the build needs %d.'
                      % (stock[c]['model'], c, stock[c]['stock'], _need(c)))
STOCK_MD = ['## Stock on 2026-10-01 (JLC parts library)', '',
            '%d LCSC part numbers across both boards. %s.' % (len(codes), ('**%d short**: %s' % (len(short), ', '.join(
                '%s (%s)' % (stock[c]['model'], c) for c in short))) if short else 'None is short'),
            'The tight ones (stock under 3x the need, or under 100; JLC buys no attrition spares on these):', '',
            '| Part | LCSC | Stock | Needed for %d sets | Note |' % N, '|---|---|---|---|---|']
for c in short + tight:
    STOCK_MD.append('| %s | %s | %d | %d | %s |' % (stock[c]['model'], c, stock[c]['stock'], _need(c), NOTES.get(c, '')))
STOCK_MD += ['', 'Re-check on the day you order: JLC\'s BOM page shows any shortage when you upload the BOM. The '
             'snapshot is `bom/jlc_snapshot_2026-10-01.json` in `BOOST_split_boards/bom_2026-09-30/`.', '']

# ---- ways to save ----
cap_save = 6 * N * (_p(ZU) - _p(ZS)) - 1.53
op_save = 18 * (_p('C49889') - _p('C398363')) - 20 * _p('C398363')
reg_7812 = N * (_p('C2877347') - _p('C231294'))
APPLIED = [
    ('Control card 8 -> 6 layers (2026-09-30)', 137.04 - 73.57, 'card panel $137.04 -> $73.57'),
    ('220 uF output caps: EEH-ZS1H221P (C385885) on C70, C71, C75, C77, C78, C88; EEH-ZU1H221P stays on C74, C86, '
     'C87', cap_save, 'also cleared the ZU stock shortage (14 in stock, now 6 needed)'),
    ('Card inner copper 0.5 oz', 16.74, 'card panel $73.57 -> $56.83; stackup now 1.547 mm (JLC 6-layer 1/0.5 oz '
     'build); Gerber layers unchanged'),
]
APPLIED.append(('12 V regulator U16: onsemi MC7812BD2TR4G (C231294) for the TI LM2940S-12/NOPB', reg_7812,
                'your choice, 2026-10-01. Same TO-263 footprint; the gerbers do not change. About 1.5 V dropout: at the '
                'end of a 4S discharge the LEDs fade from about 12.7 V open-circuit instead of 11.3 V (simulated, '
                '`mc7812_lowbatt_2026-10-01`). Its lower bias current makes it run about 2 C cooler than the LM2940 '
                'at 18 V; it also cleared the LM2940 stock problem (2 in stock)'))
_POWER_8L = 124.10          # the 8-layer power board, JLC quote 2026-10-01
APPLIED.append(('Power board: 6 layers instead of 8', _POWER_8L - P_['pcb'],
                'your choice, 2026-10-01/02: $%.2f -> $%.2f. The 5 V plane (In4) and the second GND plane (In6) are '
                'gone, 5 V is routed as tracks, and the GND pours, vias and two gate-drive routes were reworked. '
                'Stackup JLC061611-7628D (must be specified at order). Copper solve, loop inductance, M1 turn-off and '
                'U16 thermal re-checked (`power6_2026-10-01/README.md`)' % (_POWER_8L, P_['pcb'])))
if OPAMP == 'C398363':
    APPLIED.append(('Op-amps: TI TLV9001IDBVR for the 18 MCP6241 (same SOT-23-5 pinout)', op_save,
                    'LTspice re-runs against the MCP6241 (30 ms full power, 25 % PWM, cold start to 140 ms): LED '
                    'currents, LX, TVS energy and servo levels match within 0.05 %'))
OPEN = [
    ('Samtec J10/J11 through Samtec\'s free-sample program', 24.62,
     'Needs a Samtec account (your choice). A generic header pair would need the exact stack height re-checked.',
     'Worth asking Samtec'),
    ('Ordering', 0.0,
     'Pay both JLC orders together so they ship as one parcel; JLC\'s JLCONE desktop app advertises $1-20 off per '
     'order; check the coupons in your JLC account.', 'Do it'),
]
SAVINGS_MD = ['## Ways to save', '',
              'Savings are for this build: 5 bare boards of each, %d of each assembled.' % N, '',
              '**Applied:**', '', '| Change | Saved | Note |', '|---|---|---|']
for it, usd, note in APPLIED:
    SAVINGS_MD.append('| %s | %s | %s |' % (it, m(usd), note))
SAVINGS_MD += ['', '**Still open (your choice):**', '', '| Option | Saves | What it takes | Verdict |', '|---|---|---|---|']
for it, usd, how, verdict in OPEN:
    SAVINGS_MD.append('| %s | %s | %s | %s |' % (it, '-' if usd is None else (m(usd) if usd else 'shipping'), how, verdict))
SAVINGS_MD += ['',
               '**Looked at, no good cheaper alternative (kept):**',
               '- Comparators MCP6561 ($%.2f x 10): the cheaper parts are slower (Linearin LTC8721: 66-155 ns, 85 C), '
               'run hotter on supply current (Tokmas CSGM8743: 1.3 mA, 85 C) or save only $1.74 in all (3PEAK TP1961). '
               'TI TLV3201 costs more.' % _p('C117501'),
               '- Digital pot MCP4451-103 ($%.2f): already the cheapest 10 kOhm quad of its family; the 50 kOhm versions '
               'would change the current-setting network, the 7-bit MCP4441 is QFN and dearer.' % _p('C145613'),
               '- L78L05 5 V regulators ($%.3f x 4): the clones cost $0.03-0.05, but under $0.10 JLC adds about 20 '
               'attrition spares per line, so the line costs more. Loads 8 mA and 3 mA (simulated).' % _p('C43116'),
               '- 12 V regulator, other options: the SOT-223 LM2940s (UTC $0.24, TI $1.68) run too hot at 75 C case air '
               '(`u16_thermal_2026-10-01`); Microchip MIC2940A-12WU-TR ($2.60, a true LDO in the same TO-263 '
               'footprint) is the fall-back if the low-battery fade ever matters; ST L4940 is rated for only 17 V in.',
               '- Card FR4 TG135 (-$3.43): you chose to keep TG155.',
               '- OSP finish (-$34.50): shelf life and hand soldering after two reflows.',
               '- One-sided assembly: parts on both sides of both boards.',
               '- INA240A3 for INA241A4: slower and an 80 V limit.',
               '']
