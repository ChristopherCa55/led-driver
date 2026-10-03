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
    'C2877347': '**exactly 2.** Fallbacks, same TI part in TO-263: LM2940SX-12/NOPB C131916 (%d in stock, $%.2f) and '
                'LM2940CS-12/NOPB C2865267 (%d, $%.2f). Or the SOT-223 swap under "Ways to save"'
                % (CAND['C131916']['stock'], CAND['C131916']['p1'], CAND['C2865267']['stock'], CAND['C2865267']['p1']),
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
reg_ti = N * (_p('C2877347') - _p('C2866640'))
reg_utc = N * (_p('C2877347') - _p('C127023'))
APPLIED = [
    ('Control card 8 -> 6 layers (2026-09-30)', 137.04 - 73.57, 'card panel $137.04 -> $73.57'),
    ('220 uF output caps: EEH-ZS1H221P (C385885) on C70, C71, C75, C77, C78, C88; EEH-ZU1H221P stays on C74, C86, '
     'C87', cap_save, 'also cleared the ZU stock shortage (14 in stock, now 6 needed)'),
    ('Card inner copper 0.5 oz', 16.74, 'card panel $73.57 -> $56.83; stackup now 1.547 mm (JLC 6-layer 1/0.5 oz '
     'build); Gerber layers unchanged'),
]
if OPAMP == 'C398363':
    APPLIED.append(('Op-amps: TI TLV9001IDBVR for the 18 MCP6241 (same SOT-23-5 pinout)', op_save,
                    'LTspice re-runs against the MCP6241 (30 ms full power, 25 % PWM, cold start to 140 ms): LED '
                    'currents, LX, TVS energy and servo levels match within 0.05 %'))
OPEN = [
    ('**12 V regulator U16 in SOT-223: UTC LM2940G-12-AA3-R** (C127023, $%.2f, %d in stock), a second-source LM2940'
     % (_p('C127023'), CAND['C127023']['stock']), reg_utc,
     'UTC data sheet: 1 A, 26 V, 60 V for 100 ms, 0.11-0.15 V dropout at 100 mA, pins 1 IN / 2 GND / 3 OUT, '
     'Cout >= 22 uF, -40 to +85 C ambient in SOT-223. Load: 16 mA simulated plus about 0.1 A for the Arduino buck. '
     'At 18 V in it dissipates 0.9-1.2 W (including its 10-15 mA ground current): junction about 87-123 C at 50 C '
     'air with 40-60 C/W on this board\'s copper (assumed air temperature). The swap is tested: footprint at U16\'s '
     'spot, the existing Vin and 12 V vias land in pads 1 and 3, DRC unchanged. If it ever overheats it shuts down '
     'cleanly: U21 stops M1 below 9.8 V, the drivers\' 8 V UVLO stops the rest, the Arduino resets with the rail, '
     'and the LEDs come back like a cold start (simulated).',
     'Your pick, pending'),
    ('12 V regulator U16 in SOT-223: TI LM2940IMPX-12/NOPB (C2866640, $%.2f, %d in stock), the same chip as now'
     % (_p('C2866640'), CAND['C2866640']['stock']), reg_ti,
     'TI data sheet (SNVS769J): the SOT-223 (DCY) is rated -40 to +85 C, the same as the UTC part (the +125 C '
     'rating belongs to the TO-263); 150 C absolute maximum junction for both makers. Same heat and the same swap '
     'as above, so it adds no thermal margin over the UTC part.',
     'Alternative'),
    ('Arduino buck fed from Vin instead of the 12 V rail (on top of either regulator)', None,
     'Cuts the regulator\'s loss to 0.3-0.5 W (junction about 61-78 C). Needs a 1206 PTC (about 0.2-0.35 A hold, '
     '>= 30 V) at the tap point and a new low-current net to J10 pin 19 (the board rule wants 1.0 mm tracks on Vin); '
     'the existing 26 mm branch to J10.19 runs past Vin copper. The buck must take up to 18 V. Simulated drawback: '
     'after a 12 V dropout the Arduino keeps its references up, so the restart gives LX 62 V at 16.8 V and 82 V at '
     '18 V (with the Arduino on 12 V the restart is a gentle cold start).',
     'Optional; cooler but a harsher restart'),
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
               '- 12 V regulator in a 78xx-style DPAK or TO-263 ($0.08-0.26): 2 V dropout would pull the 12 V rail down '
               'to the M1 cut-off (9.85 V) and the gate-driver UVLO at low battery.',
               '- Card FR4 TG135 (-$3.43): you chose to keep TG155.',
               '- OSP finish (-$34.50): shelf life and hand soldering after two reflows.',
               '- A 6-layer power board ($69.57): complete re-route. One-sided assembly: parts on both sides of both boards.',
               '- INA240A3 for INA241A4: slower and an 80 V limit.',
               '']
