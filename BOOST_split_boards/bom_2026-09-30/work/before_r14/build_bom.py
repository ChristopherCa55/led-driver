"""BOM, JLCPCB sourcing table and pick-and-place files for both boards (system Python), 2026-10-01.

Copied from fab_2026-09-24/tools/build_bom.py. Changes: D28-D30 (S2MW pre-charge diodes) added; stock and prices
from bom/jlc_snapshot_2026-09-30.json (tools/jlc_parts.py); the logo footprints (no pads) are skipped; the sourcing
table carries maker and links.

usage: python tools/build_bom.py            (run from bom_2026-09-30/)

Inputs: bom/parts_from_boards.json (every footprint on the two candidate boards), bom/power_pos_all.csv and
bom/card_pos_all.csv (kicad-cli pos), bom/jlc_snapshot_2026-09-30.json (JLC stock and prices).
The decision for every line is in LINES below, with the reason. Lists:
  JLC   bought and fitted by JLCPCB (in the JLC BOM and CPL)
  ME    fitted by the user (DNP: not in the JLC BOM or CPL; pads, holes and silk stay on the board)
  OPEN  not decided: the part has no type in the schematic, or the drawn part cannot be bought; a proposal is given,
        and the *_with_proposals files include it
  NONE  no part to buy (mounting holes, net ties, wire pads)
Outputs in bom/: SOURCING_TABLE.md and .csv, and per board BOM_JLC.csv / CPL_JLC.csv (JLC list only) and
BOM_JLC_with_proposals.csv / CPL_JLC_with_proposals.csv (JLC list plus the OPEN proposals).
"""
import csv, json, math, re, collections

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from descriptions import short as short_desc
SNAPFILE = os.environ.get('SNAP', 'bom/jlc_snapshot_2026-10-01.json')
SNAP = {k: v for k, v in json.load(open(SNAPFILE, encoding='utf-8'))['res'].items() if v}
PARTS = {b: [p for p in v if not (p['ref'].startswith('G') and p['npads'] == 0)]   # logos: silk only
         for b, v in json.load(open('bom/parts_from_boards.json', encoding='utf-8')).items()}

# rule notes, referenced by key in LINES
RULES = {
    'decoup': 'value and package from the schematic; X7R, voltage rating at least 2x the net (rails 5/12 V, Vin 14-17 V)',
    'vout': 'on Vout (23-33 V running; TVS stand-off 54 V, clamp 87 V): 100 V rated',
    'c0g': 'timing / compensation / sample-and-hold: C0G',
    'res': 'value and package from the schematic; 1% thick film, JLC Basic where one exists',
    'decided': 'part chosen earlier (HANDOFF_SUMMARY / replace_notes / ANSWERS)',
    'mpn': 'the device named in the schematic or the notes',
    'approved': 'your choice of 2026-09-24',
}

L = []


def line(board, refs, value, fp, lst, lcsc=None, alts=(), rule=None, note=''):
    L.append(dict(board=board, refs=refs.split(','), value=value, fp=fp, list=lst, lcsc=lcsc, alts=list(alts),
                  rule=rule, note=note))


P, C = 'power', 'card'
# ---------------- power board ----------------
line(P, 'C1,C4,C73', '4.7uF', '1210', 'JLC', 'C381466', ['C170099 (50 V)'], 'vout',
     'commutation-loop ceramic per rail; 50 V part C170099 is cheaper but keeps less capacitance at 33 V')
line(P, 'C3,C72,C76', '100nF', '0805', 'JLC', 'C28233', [], 'vout')
line(P, 'C6,C21,C25,C31,C62,C89', '1uF', '0805', 'JLC', 'C28323', [], 'decoup')
line(P, 'C7,C55', '22uF', '1210', 'JLC', 'C21397', [], 'decided')
line(P, 'C16,C18,C60', '2.2uF', '1206', 'JLC', 'C50254', [], 'decoup', 'bootstrap caps, 12 V across')
line(P, 'C20,C33,C34,C35,C48,C50,C51,C61,C82,C83,C84,C90', '100nF', '0603', 'JLC', 'C14663', [], 'decoup',
     'C82-C84 on Vin (<= 17 V), 50 V part')
line(P, 'C30', '47uF tantalum', 'EIA-7343 (D)', 'JLC', 'C4979367', [], 'decided', 'U16 (12 V regulator) output, ESR 250 mOhm')
line(P, 'C39,C56,C79,C80,C81', '10uF', '1210', 'JLC', 'C138687', [], 'decoup', 'C79-C81 on Vin: 50 V X7R')
line(P, 'C40,C69,C85', '680uF EEH-ZU1E681UP', 'CP_Elec_10x12.5', 'JLC', 'C29664285', [], 'decided',
     'STOCK 10: enough for 3 boards (3 each)')
line(P, 'C41,C44,C45', '1nF', '0603', 'JLC', 'C1588', ['C163508 (C0G)'], 'decoup', 'IREF wiper filter')
line(P, 'C74,C86,C87', '220uF EEH-ZU1H221P', 'CP_Elec_10x16.5', 'JLC', 'C6843593', [],
     'decided', 'the three most loaded output caps (BOOST_AUDIT section 6: up to 3.46 A); since 2026-10-01 the other six '
     'are EEH-ZS1H221P')
line(P, 'C70,C71,C75,C77,C78,C88', '220uF EEH-ZS1H221P', 'CP_Elec_10x16.5', 'JLC', 'C385885', ['C6843593 EEH-ZU1H221P'],
     None, 'approved 2026-10-01: same Panasonic hybrid family, size and footprint; 13 mOhm, 3.7 A (ZU: 10 mOhm, 5.2 A). '
     'These positions carry 1.90-2.37 A, 51-64 % of the ZS rating; cheaper, and the ZU had too little stock')
line(P, 'D2,D8,D11,D13,D14,D22', 'B5819W (gate turn-off)', 'SOD-123', 'JLC', 'C8598', ['C81598 1N4148W'], 'approved',
     'no diode type in the schematic (LTspice default diode). Anode on the FET gate, cathode to the driver side of '
     'the gate resistor: the turn-off path. Proposal B5819W (40 V 1 A Schottky, Basic)')
line(P, 'D9,D10,D21', 'BAV21W (bootstrap)', 'SOD-123', 'JLC', 'C21565', ['C81598 1N4148W (75 V: too low)'], 'approved',
     'no diode type in the schematic. 12 V to the high-side VDDA: blocks the rail FET source voltage (up to Vout, '
     '54-87 V under a clamp event). Proposal BAV21W (200 V, trr 50 ns)')
line(P, 'D28,D29,D30', 'S2MW (pre-charge)', 'SOD-123F', 'JLC', 'C128729', ['C2900725 Foshan Blue Rocket S2MW'],
     None, 'pre-charge diodes Vin -> Vout_1/2/3 (chosen 2026-09-29): 1000 V 2 A, IFSM 50 A; surge headroom '
     '2.5x at an ideal battery (precharge_surge_2026-09-30), kept 2026-09-30')
line(P, 'D19', 'TVS 5.0SMDJ54A', 'D_SMC', 'JLC', 'C42394451', ['C20415356 Littelfuse (stock 1)',
                                                                 'C5279851 SETsafe (published specs)'], 'decided',
     'Littelfuse has 1 in stock; R+O alternate (as decided 2026-09-15). Its listing gives the ratings but links no '
     'datasheet')
line(P, 'H5,H6,H7,H8', 'mounting hole', 'M3', 'NONE')
line(P, 'J1,J2', 'battery lug', 'M4 hole', 'NONE', note='cable lugs bolted through; no part on the BOM')
line(P, 'J3,J4,J5,J6,J7,J8', 'LED wire pad', 'THT pad 4 mm', 'NONE', note='wires soldered in')
line(P, 'J10', 'ESQ-115-44-G-D', 'PinSocket 2x15', 'ME', None, ['C5689183 ESQ-115-44-G-D-LL (stock 0)'], 'mpn',
     'not stocked at LCSC (only the -LL variant is listed, 0 in stock, $23.28); buy from Samtec / Digi-Key / Mouser')
line(P, 'L1', 'CSCF3218-6R8MC', '32 x 22.5 mm SMD', 'ME', None, ['C5629897 (stock 0)'], 'mpn', 'the user owns it')
line(P, 'M1,M2,M3,M4,M5,M6,M7,M8,M9,M10', 'HYG180N10', 'TO-220', 'ME', None, ['C2841917 HYG180N10LS1P'], 'mpn',
     'the user owns ten')
line(P, 'NT1,NT2,NT3', 'net tie', '-', 'NONE')
line(P, 'R1', '1m CSS4J-4026R-1L00F', '4026 4-terminal', 'JLC', 'C2076400', ['C2076167 CSS4J-4026K-2L00F 2 mOhm (0 stock)'],
     'approved', 'rev6: 1 mOhm with U25 = INA241A4 (100 V/V): Current stays 0.1 V/A. Same Bourns land pattern '
     '(series drawing), H 2.70 max against 2.93')
line(P, 'R7,R52,R53', '50 mOhm WSL2512', '2512', 'JLC', 'C413486', ['C127698 thick film +/-800 ppm/C'], 'approved',
     'LED current sinks: 2.63 A, 0.35 W each. The value sets the LED current, so the TCR matters: WSL2512 metal strip '
     '+/-75 ppm/C ($0.23) against thick film +/-800 ppm/C ($0.04)')
line(P, 'R13,R23,R47', '220', '0603', 'JLC', 'C22962', [], 'res')
line(P, 'R14', '1M', '0805', 'JLC', 'C17514', [], 'res', 'on LX (65 V peak): 150 V rated')
line(P, 'R15', '10', '0805', 'JLC', 'C17415', [], 'res')
line(P, 'R21,R48,R60,R72', '5.1', '0805', 'JLC', 'C17724', ['C25273 4.99 Ohm'], 'approved',
     'rev6: 5 -> 5.1 Ohm (5.0 Ohm 0805 is not stocked), the value R59/R70 already use')
line(P, 'R22,R50,R56', '100', '0603', 'JLC', 'C22775', [], 'res')
line(P, 'R49,R61,R62,R73,R74,R75,R76,R104', '10k', '0603', 'JLC', 'C25804', [], 'res')
line(P, 'R59,R70', '5.1', '0805', 'JLC', 'C17724', [], 'res')
line(P, 'U1,U17', 'L78L05', 'SOT-89', 'JLC', 'C43116', [], 'mpn', 'ST L78L05ACUTR (pinout OUT-GND-IN as the symbol)')
line(P, 'U6,U11,U12', 'TLV9001', 'SOT-23-5', 'JLC', 'C398363', ['C49889 MCP6241T-E/OT (before 2026-10-01)'], None,
     'approved 2026-10-01: TI TLV9001IDBVR (the DBV part: pins 1 OUT, 2 V-, 3 IN+, 4 IN-, 5 V+, as the MCP6241; NOT the TLV9001U). 1 MHz, 2 V/us, 1.6 mV max offset. LTspice re-runs (30 ms, 25 % PWM, cold start) match the MCP6241 within 0.05 %')
line(P, 'U8,U10,U15,U19', 'UCC21520DW', 'SOIC-16W', 'JLC', 'C601651', [], 'mpn')
line(P, 'U16', 'MC7812', 'TO-263-3', 'JLC', 'C231294', ['C38744 MC7812CD2TR4G (0 to +125 C)',
     'C2877347 LM2940S-12/NOPB (before 2026-10-01)'], None,
     'approved 2026-10-01: onsemi MC7812BD2TR4G. Its D2PAK (case 936) fits the TO-263-3 footprint: pins 1 IN and '
     '3 OUT at 2.54 mm pitch, tab = pin 2 GND, the centre lead is cut (pad 2 stays empty, it is GND). 35 V in, '
     '-40 to +125 C. About 1.5 V dropout, so at the end of a 4S discharge the LEDs fade from about 12.7 V '
     'open-circuit (simulated: BOOST_split_boards/mc7812_lowbatt_2026-10-01)')
line(P, 'U25', 'INA241A4', 'SOIC-8', 'JLC', 'C22427873', ['C22427652 INA241A3IDR (rev5)'], 'approved',
     'rev6: gain 100 V/V with the 1 mOhm R1; TI SBOSA30D: same SOIC-8 pinout for every gain, 1.1 MHz for all gains')
# ---------------- control card ----------------
line(C, 'C8,C9,C17,C19', '330pF', '0603', 'JLC', 'C1664', [], 'c0g')
line(C, 'C10,C11,C13', '4.7nF', '0603', 'JLC', 'C85980', ['C53987 X7R Basic'], 'c0g', 'on Verr1-3')
line(C, 'C12,C22,C23,C24,C26,C28,C29,C32,C36,C37,C38,C42,C43,C46,C52,C53,C54,C58,C59,C63,C65,C66,C68,C92,C94,'
        'C95,C96,C97,C98,C99,C104', '100nF', '0603', 'JLC', 'C14663', [], 'decoup')
line(C, 'C14', '220pF', '0603', 'JLC', 'C27675', ['C1603 X7R Basic'], 'c0g', 'Q1 emitter')
line(C, 'C15', '100pF', '0603', 'JLC', 'C14858', [], 'c0g')
line(C, 'C47,C93,C103', '10uF', '0603', 'JLC', 'C96446', [], 'decoup', 'Vref_1-3 (5 V): 25 V X5R')
line(C, 'C49,C64,C67', '100nF', '1206', 'JLC', 'C97946', ['C14663-class X7R'], 'c0g',
     'sample-and-hold into the 4066 switches')
line(C, 'C57,C91', '1uF', '0805', 'JLC', 'C28323', [], 'decoup')
line(C, 'C100,C101,C102', '1nF', '0603', 'JLC', 'C1588', [], 'decoup', 'pot B-terminal filter')
line(C, 'D1,D3,D4,D5,D6,D7,D15,D20,D24,D27', '1N4148W (logic)', 'SOD-123', 'JLC', 'C81598', [], 'approved',
     'no diode type in the schematic (LTspice default silicon diode). Proposal 1N4148W (Basic), the closest real '
     'part to what was simulated')
line(C, 'D23,D25,D26', 'BAT54WS (Vref)', 'SOD-323', 'JLC', 'C22629', ['C124205 BAT54WS-7-F'], 'approved',
     'no type in the schematic; the design notes show BAT54 on this path (Output -> .1Vref_n). Proposal BAT54WS')
line(C, 'H1,H2,H3,H4', 'mounting hole', 'M3', 'NONE')
line(C, 'J9', 'Arduino wire pads', '11 wire pads', 'NONE', note='wires soldered in (BUILD_NOTES J9 table)')
line(C, 'J11', 'TSW-115-07-G-D', 'PinHeader 2x15', 'ME', None, ['C5994596 (stock 0)'], 'mpn',
     'LCSC lists it with 0 in stock; buy from Samtec / Digi-Key / Mouser')
line(C, 'Q1', 'MMBT3906', 'SOT-23', 'JLC', 'C53444', ['C2143 JSCJ MMBT3906'], 'approved',
     'no transistor type in the schematic (LTspice generic PNP). Proposal MMBT3906')
line(C, 'R2,R6,R31,R33,R39,R41,R67,R77,R83,R85,R99,R100,R101,R102,R103', '10k', '0603', 'JLC', 'C25804', [], 'res')
line(C, 'R3,R32,R40', '620k', '0603', 'JLC', 'C23219', [], 'res')
line(C, 'R4,R54,R55,R58,R71', '1k', '0603', 'JLC', 'C21190', [], 'res')
line(C, 'R8,R34,R42,R51,R63,R78,R80', '2k', '0603', 'JLC', 'C22975', [], 'res')
line(C, 'R9,R35,R43', '18k', '0805', 'JLC', 'C17506', [], 'res')
line(C, 'R11,R17', '510k', '0603', 'JLC', 'C23192', [], 'res')
line(C, 'R16,R19', '5.1k', '0603', 'JLC', 'C23186', [], 'res')
line(C, 'R18,R20', '200k', '0603', 'JLC', 'C25811', [], 'res')
line(C, 'R25,R87,R94', '910k', '0805', 'JLC', 'C17864', [], 'res', 'Vout dividers: 150 V rated')
line(C, 'R26,R64,R79,R81', '220', '0603', 'JLC', 'C22962', [], 'res')
line(C, 'R27,R37,R45', '4.7k', '0603', 'JLC', 'C23162', [], 'res')
line(C, 'R28,R36,R38,R44,R46,R88,R91,R95,R96,R105', '100k', '0603', 'JLC', 'C25803', [], 'res')
line(C, 'R29,R30,R57', '22k', '0805', 'JLC', 'C17560', [], 'res')
line(C, 'R65', '22k', '0603', 'JLC', 'C31850', [], 'res')
line(C, 'R66,R89,R92,R97', '3.3k', '0603', 'JLC', 'C22978', [], 'res')
line(C, 'R68', '62k', '0603', 'JLC', 'C23221', [], 'res')
line(C, 'R69', '20k', '0603', 'JLC', 'C4184', [], 'res')
line(C, 'R82', '56k', '0603', 'JLC', 'C23206', [], 'res')
line(C, 'R84', '120k', '0603', 'JLC', 'C25808', [], 'res')
line(C, 'R86', '1M', '0805', 'JLC', 'C17514', [], 'res')
line(C, 'R90,R93,R98', '10M', '0603', 'JLC', 'C7250', [], 'res')
line(C, 'U2,U4,U5,U14,U21', 'MCP6561', 'SOT-23-5', 'JLC', 'C117501', [], 'mpn')
line(C, 'U3,U7,U13,U22,U23,U24', 'TLV9001', 'SOT-23-5', 'JLC', 'C398363', ['C49889 MCP6241T-E/OT (before 2026-10-01)'],
     None, 'approved 2026-10-01: TI TLV9001IDBVR (the DBV part: pins 1 OUT, 2 V-, 3 IN+, 4 IN-, 5 V+, as the MCP6241; NOT the TLV9001U). 1 MHz, 2 V/us, 1.6 mV max offset. LTspice re-runs (30 ms, 25 % PWM, cold start) match the MCP6241 within 0.05 %')
line(C, 'U18', 'CD4017B', 'SOIC-16', 'JLC', 'C11349', [], 'mpn')
line(C, 'U26', 'MCP4451-103E/ST', 'TSSOP-20', 'JLC', 'C145613', [], 'decided', 'STOCK 52')
line(C, 'U28', '74HC4051', 'SOIC-16', 'JLC', 'C9386', [], 'mpn')
line(C, 'U101,U102,U103', '74HC00', 'SOIC-14', 'JLC', 'C5586', [], 'mpn')
line(C, 'U104,U105', '74HC14', 'SOIC-14', 'JLC', 'C5605', [], 'mpn')
line(C, 'U106', 'CD74HC4066', 'SOIC-14', 'JLC', 'C179842', [], 'mpn', 'STOCK 73')

# ---- every footprint on each board must be in exactly one line ----
for board in (P, C):
    on_board = {p['ref']: p for p in PARTS[board]}
    listed = [r for l in L if l['board'] == board for r in l['refs']]
    dup = [r for r, n in collections.Counter(listed).items() if n > 1]
    missing = sorted(set(on_board) - set(listed))
    extra = sorted(set(listed) - set(on_board))
    assert not dup and not missing and not extra, (board, dup, missing, extra)
    for l in L:
        if l['board'] == board:
            l['sides'] = sorted(set(on_board[r]['side'] for r in l['refs']))
            l['pads'] = sum(on_board[r]['npads'] for r in l['refs'])

# ---- build limits and costs ----
per_set = collections.Counter()
for l in L:
    if l['lcsc'] and l['list'] in ('JLC', 'OPEN'):
        per_set[l['lcsc']] += len(l['refs'])
for l in L:
    s = SNAP.get(l['lcsc']) if l['lcsc'] else None
    l['snap'] = s
    l['max_sets'] = (s['stock'] // per_set[l['lcsc']]) if s and per_set[l['lcsc']] else None


def natkey(r):
    m = re.match(r'([A-Z]+)(\d+)', r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


# ---- sourcing table ----
TYPE = {'base': 'Basic', 'expand': 'Extended'}
rows = []
for l in L:
    s = l['snap']
    rows.append({
        'board': l['board'], 'list': l['list'], 'refs': ' '.join(sorted(l['refs'], key=natkey)), 'qty': len(l['refs']),
        'value': l['value'], 'description': short_desc(l['lcsc'], s, l['value']), 'footprint': l['fp'],
        'side': '/'.join(l['sides']),
        'lcsc': l['lcsc'] or '', 'mpn': s['model'] if s else '', 'maker': s['brand'] if s else '',
        'type': (TYPE[s['type']] + (' (preferred)' if s['pref'] else '')) if s else '',
        'stock': s['stock'] if s else '', 'unit_usd': s['p1'] if s else '',
        'board_usd': round(s['p1'] * len(l['refs']), 4) if s else '',
        'max_sets': l['max_sets'] if l['max_sets'] is not None else '',
        'orderable': ('' if not s else ('NO (0 in stock)' if s['stock'] == 0 else
                                         ('LIMITS BUILD' if l['max_sets'] is not None and l['max_sets'] < 5 else 'yes'))),
        'why': (RULES.get(l['rule'], '') + ('; ' if l['rule'] and l['note'] else '') + l['note']).strip(),
        'alternates': '; '.join(l['alts']),
        'jlc_url': s['url'] if s else '', 'lcsc_url': (s.get('lcsc_url') or '') if s else '',
        'datasheet': (s.get('ds') or '') if s else '',
    })
with open('bom/SOURCING_TABLE.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# ---- JLC BOM and CPL ----
pos = {}
for board in (P, C):
    with open('bom/%s_pos_all.csv' % board, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            pos[(board, r['Ref'])] = r
NAME = {P: 'BOOST_power', C: 'BOOST_control'}
summary = {}
for board in (P, C):
    for tag, lists in (('', ('JLC',)), ('_with_proposals', ('JLC', 'OPEN'))):
        bl = [l for l in L if l['board'] == board and l['list'] in lists and l['lcsc']]
        with open('bom/%s_BOM_JLC%s.csv' % (NAME[board], tag), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
            for l in bl:
                w.writerow([SNAP[l['lcsc']]['model'], ','.join(sorted(l['refs'], key=natkey)), l['fp'], l['lcsc']])
        refs = sorted((r for l in bl for r in l['refs']), key=natkey)
        with open('bom/%s_CPL_JLC%s.csv' % (NAME[board], tag), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
            for r in refs:
                p = pos[(board, r)]
                w.writerow([r, '%.4fmm' % float(p['PosX']), '%.4fmm' % float(p['PosY']),
                            'Top' if p['Side'] == 'top' else 'Bottom', '%g' % float(p['Rot'])])
        uniq = len(set(l['lcsc'] for l in bl))
        ext = len(set(l['lcsc'] for l in bl if SNAP[l['lcsc']]['type'] == 'expand'))
        parts = sum(len(l['refs']) for l in bl)
        joints = sum(l['pads'] for l in bl)
        comp = sum(SNAP[l['lcsc']]['p1'] * len(l['refs']) for l in bl)
        sides = sorted(set(s for l in bl for s in l['sides']))
        summary[(board, tag or 'JLC only')] = dict(unique=uniq, extended=ext, basic=uniq - ext, placements=parts,
                                                   joints=joints, components_usd=round(comp, 2), sides=sides)

# ---- markdown ----
out = ['# BOM and JLCPCB sourcing, 2026-10-01', '',
       ('Stock and prices read from the JLCPCB parts library on 2026-10-01 (snapshot: `%s`). ' % os.path.basename(SNAPFILE)) +
       '"Max sets" is how many power board + control card pairs the stock covers at the quantities used on both '
       'boards. Unit prices are JLC\'s quantity-1 prices; JLC also buys a few spares of each small part (attrition), '
       'not included here.', '']
for lst, title in (('JLC', 'JLC fits (bought and fitted by JLCPCB)'),
                   ('ME', 'I fit (DNP in the JLC files; pads, holes and silk stay)'),
                   ('OPEN', 'Unresolved (a decision is needed; the proposal is in the *_with_proposals files)'),
                   ('NONE', 'No part to buy')):
    out += ['## ' + title, '']
    out += ['| Board | Refs | Qty | Description | Footprint | Side | LCSC | MPN (maker) | Basic/Ext | Stock | $/unit | '
            'Max sets | Orderable | Why / notes |', '|' + '---|' * 14]
    for r in rows:
        if r['list'] != lst:
            continue
        out.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            r['board'], r['refs'], r['qty'], r['description'], r['footprint'], r['side'], r['lcsc'],
            ('%s (%s)' % (r['mpn'], r['maker'])) if r['mpn'] else '', r['type'], r['stock'], r['unit_usd'],
            r['max_sets'], r['orderable'], (r['why'] + ((' Alternates: ' + r['alternates']) if r['alternates'] else ''))))
    out.append('')
out += ['## Assembly quantities', '', '| Board | Files | Unique parts | Basic | Extended | Placements | SMT pads | '
        'Components $/board (qty-1 prices) | Sides |', '|---|---|---|---|---|---|---|---|---|']
for (board, tag), s in summary.items():
    out.append('| %s | %s | %d | %d | %d | %d | %d | %.2f | %s |' % (board, tag, s['unique'], s['basic'], s['extended'],
                                                                     s['placements'], s['joints'],
                                                                     s['components_usd'], ' + '.join(s['sides'])))
open('bom/SOURCING_TABLE.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
json.dump({'%s|%s' % k: v for k, v in summary.items()}, open('bom/assembly_summary.json', 'w'), indent=1)
for k, v in summary.items():
    print(k, v)
lim = sorted((l['max_sets'], l['lcsc'], SNAP[l['lcsc']]['model']) for l in L
             if l['max_sets'] is not None and l['list'] in ('JLC', 'OPEN'))
print('tightest stock (sets):', lim[:10])
