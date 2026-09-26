"""Cost summary for the chosen build, scenario A (2026-09-25).

Scenario A: 5 bare PCBs of each board, 2 complete sets assembled by JLCPCB, 3 spare bare boards of each.
Scenario B was dropped on 2026-09-25; its version of this script and document are kept as
tools/cost_summary_AB_2026-09-24.py and cost/COST_SUMMARY_AB_2026-09-24.md, and its BOM/CPL files stay in cost/.

Reads bom/SOURCING_TABLE.csv (JLC lines), bom/parts_from_boards.json (pad counts) and
bom/jlc_stock_2026-09-25.json (stock and quantity-1 prices read 2026-09-25), and writes
COST_SUMMARY.md and cost/cost_summary.json.

  python tools/cost_summary.py
"""
import csv, json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = os.path.join(HERE, 'bom')
OUT = os.path.join(HERE, 'cost')
os.makedirs(OUT, exist_ok=True)

rows = list(csv.DictReader(open(os.path.join(BOM, 'SOURCING_TABLE.csv'), encoding='utf-8')))
parts = json.load(open(os.path.join(BOM, 'parts_from_boards.json'), encoding='utf-8'))
stock = json.load(open(os.path.join(BOM, 'jlc_stock_2026-09-25.json'), encoding='utf-8'))['res']
npads = {b: {p['ref']: p['npads'] for p in parts[b]} for b in parts}

N = 2                      # boards of each assembled
PCB = {  # 5 boards, 8 layers, 1.6 mm, ENIG, 1 oz / 1 oz, epoxy filled & capped vias, 10-11 day build (2026-09-24)
    'power': dict(usd=124.10, what='5 single boards, 74 x 86 mm',
                  detail='$90.00 base, $17.30 ENIG, $16.80 1 oz inner, $0.00 via covering'),
    'card': dict(usd=137.04, what='5 panels: one 45 x 45 mm card on a 70 x 70 mm carrier (12.5 mm rails, four sides, V-cut)',
                 detail='$99.00 engineering, $17.20 ENIG, $16.74 1 oz inner, $4.10 board, $0.00 via covering'),
}
CARD_SINGLE = 123.42
SETUP, STENCIL, LOAD, JOINT = 51.12, 16.42, 1.53, 0.0016
ATTR_SMALL = 20
LIMITED = {'C6843593', 'C29664285', 'C49889', 'C2877347'}
GBP = 1.34                 # assumed USD per GBP for the two Farnell UK prices

jlc = [r for r in rows if r['list'] == 'JLC']


def order(board):
    lines, seen, parts_usd, attr_usd, joints = [], set(), 0.0, 0.0, 0
    for r in jlc:
        if r['board'] != board:
            continue
        code, n = r['lcsc'], len(r['refs'].split())
        unit = stock[code]['p1']
        attr = ATTR_SMALL if (unit < 0.10 and code not in LIMITED and code not in seen) else 0
        seen.add(code)
        lines.append(dict(refs=r['refs'], lcsc=code, mpn=stock[code]['model'], per_board=n, qty=n * N, attr=attr,
                          unit=unit, usd=round(unit * (n * N + attr), 2), stock=stock[code]['stock']))
        parts_usd += unit * n * N
        attr_usd += unit * attr
        joints += sum(npads[board][x] for x in r['refs'].split()) * N
    fees = dict(setup=SETUP, stencil=STENCIL, loading=round(LOAD * len(seen), 2), joints=round(JOINT * joints, 2))
    asm = sum(fees.values()) + parts_usd + attr_usd
    return dict(board=board, unique=len(seen), joints=joints, pcb=PCB[board]['usd'], fees=fees,
                parts=round(parts_usd, 2), attrition=round(attr_usd, 2), assembly=round(asm, 2),
                total=round(PCB[board]['usd'] + asm, 2), lines=lines)


P_, C_ = order('power'), order('card')

ELSEWHERE = [  # item, qty, unit, source, checked
    ('Samtec ESQ-115-44-G-D, J10 socket (power board)', N, 9.13, 'Mouser, as listed on samtec.com', 'read on samtec.com'),
    ('Samtec TSW-115-07-G-D, J11 header (card)', N, 3.18, 'Mouser, as listed on samtec.com', 'read on samtec.com'),
    ('Bourns MF-R020 PTC, 0.20 A hold (inline on the J9 pin-9 wire)', N, 0.14, 'LCSC (its own order; JLC does not ship '
     'loose parts)', 'read on lcsc.com; ratings read in the Bourns MF-R datasheet'),
]
HARDWARE = [  # item, role, qty text, qty-cost, source, checked, link
    ('Parker Chomerics 61-05-0909-G579, THERM-A-GAP 579, 0.050 in, 9 x 9 in sheet (smallest listed)',
     'FET thermal pads, cut 10 x 16 mm (10 per board)', '1 sheet', 85.00,
     'price not readable: Parker quotes via distributors, and Digi-Key/Mouser/Newark/Arrow/RS block this browser',
     'ESTIMATE: you read it (URL list)', 'https://ph.parker.com/us/en/product/therm-a-gap-579-thermally-conductive-gap-filler-pads/61-05-0909-g579'),
    ('McMaster-Carr 92000A107, M2.5 x 12 pan head Phillips, 18-8 stainless, pack of 100', 'FET tab screws (4 per set)',
     '1 pack', 5.65, 'mcmaster.com', 'read on mcmaster.com', 'https://www.mcmaster.com/92000A107/'),
    ('McMaster-Carr 93657A200, nylon 6/6 spacer, M2.5, 2.0 mm long, 4.5 mm OD', 'FET tab-screw gap spacer (4 per set)',
     '8', 8 * 0.92, 'mcmaster.com ($0.92 each under 10)', 'read on mcmaster.com', 'https://www.mcmaster.com/93657A200/'),
    ('Boyd (Aavid) 7721-7PPSG shoulder washer, glass-filled PPS', 'insulates each tab screw in the FET tab hole (4 per set)',
     '8', 8 * 0.26, 'search-engine summary of Digi-Key ($0.26)', 'UNVERIFIED: you read it (URL list)',
     'https://www.digikey.com/en/products/result?keywords=7721-7PPSG'),
    ('Essentra HTSN-M3-5-3, nylon hex stud M3 male-male, 5 mm body', 'floor-to-power-board standoff (4 per set)',
     '8', 8 * 0.60, 'estimate (Digi-Key shows $0.48 at 500)', 'ESTIMATE: you read it (URL list)',
     'https://www.digikey.com/en/products/result?keywords=HTSN-M3-5-3'),
    ('Essentra HNSM3-20-5.5-1, nylon hex standoff M3 female-female, 20 mm', 'power-board-to-card standoff (4 per set)',
     '8', 8 * 0.80, 'estimate (no public price found)', 'ESTIMATE: you read it (URL list)',
     'https://www.digikey.com/en/products/detail/essentra-components/HNSM3-20-5-5-1/3813076'),
    ('TR Fastenings TR NWE-34815-M3, nylon 6/6 washer 3.2 x 7.0 x 0.5 mm, pack of 100', 'standoff shims (16 per set)',
     '1 pack', 8.71 * GBP, 'Farnell UK 8.71 GBP, converted at %.2f USD/GBP' % GBP,
     'price read via search; conversion assumed',
     'https://www.newark.com/tr-fastenings/tr-nwe-34815-m3/washer-nylon-6-6-3-2mm-pk100/dp/43Y4267'),
    ('Wurth Elektronik 97790803211, WA-SCRW M3 x 8 nylon 66 pan head', 'card screws (4 per set)', '8',
     8 * 0.199 * GBP, 'Farnell UK 0.199 GBP each, converted at %.2f USD/GBP' % GBP,
     'price read via search; conversion assumed', 'https://www.we-online.com/en/components/products/WA-SCRW'),
]
e_usd = sum(q * u for _, q, u, _, _ in ELSEWHERE)
h_usd = sum(h[3] for h in HARDWARE)
total = P_['total'] + C_['total'] + e_usd + h_usd
removed = 2 * 8.95 + 7.95   # Pololu D24V5F5 x2 and Adafruit 793, dropped 2026-09-25 (you own a buck and wires)

json.dump(dict(power=P_, card=C_, elsewhere=ELSEWHERE, hardware=HARDWARE, total=round(total, 2)),
          open(os.path.join(OUT, 'cost_summary.json'), 'w'), indent=1)


def m(x):
    return '$%s' % format(x, ',.2f')


L = []
P = L.append
P('# BOOST: cost summary, scenario A (updated 2026-09-25)')
P('')
P('**Scenario A:** 5 bare PCBs of each board, 2 complete sets assembled by JLCPCB, 3 spare bare boards of each. '
  '**Shipping and tax are not included anywhere below.** Excluded because you own them: M1-M10, L1, the 12 V -> 5 V '
  'buck module and the J9 wires. Also excluded: case, battery cabling and lugs, Arduino Nano and CAN parts, LEDs.')
P('')
P('The BOM is schematic **rev6**: R1 = Bourns CSS4J-4026R-1L00F (1 mOhm), U25 = INA241A4. The rev6 copy is checked. '
  'It still has to be written into your schematic `BOOST-github/BOOST/BOOST.kicad_sch`, which carries KiCad lock '
  'files; see `ORDER_CHECKLIST.md`.')
P('')
P('## Grand total')
P('')
P('| | Power board | Control card | Total |')
P('|---|---|---|---|')
P('| Bare PCBs (5 each) | %s | %s | %s |' % (m(P_['pcb']), m(C_['pcb']), m(P_['pcb'] + C_['pcb'])))
P('| JLC assembly of 2 each (fees + parts) | %s | %s | %s |' % (m(P_['assembly']), m(C_['assembly']),
                                                               m(P_['assembly'] + C_['assembly'])))
P('| Parts bought elsewhere (J10, J11, PTC) | | | %s |' % m(e_usd))
P('| Hardware for 2 sets | | | %s |' % m(h_usd))
P('| **Grand total, scenario A** | | | **%s** |' % m(total))
P('| Shipping, tax | | | not included |')
P('')
P('That is %s less than the 2026-09-24 figure ($829.75): the Pololu D24V5F5 buck modules and the Adafruit 793 wires '
  'are removed (%s), and JLC\'s prices moved by a few cents. Four hardware lines ($%.2f of the total) are still estimates '
  'or unverified; see "URLs for you to read".' % (m(829.75 - total), m(removed),
                                                    HARDWARE[0][3] + HARDWARE[3][3] + HARDWARE[4][3] + HARDWARE[5][3]))
P('')
P('## Bare PCBs (JLCPCB quote page, 2026-09-24)')
P('')
P('Both boards: 8 layers, 1.6 mm, FR4 TG155, ENIG, 1 oz outer / 1 oz inner, **Epoxy Filled & Capped vias ($0.00 at '
  '8 layers)**, min via 0.3 mm, Remove Mark, flying-probe full test, 10-11 day build.')
P('')
P('| Board | Order | Price for 5 | Breakdown |')
P('|---|---|---|---|')
for b in ('power', 'card'):
    P('| %s | %s | %s | %s |' % ('Power' if b == 'power' else 'Card', PCB[b]['what'], m(PCB[b]['usd']), PCB[b]['detail']))
P('')
P('The card has to go on a carrier panel: JLC\'s Standard PCBA takes nothing under 70 x 70 mm, and Economic PCBA '
  'handles 2/4/6 layers, single-sided boards only. The panel costs %s more than 5 single cards (%s).'
  % (m(PCB['card']['usd'] - CARD_SINGLE), m(CARD_SINGLE)))
P('')
P('## Assembly (JLC Standard PCBA, 2 of each)')
P('')
P('Set-up %s and stencil %s per order (both boards are double-sided); feeder loading %s per unique part; $0.0016 per '
  'solder joint (JLC price page). Parts: JLC quantity-1 prices read 2026-09-25, plus about %d attrition spares per '
  'small-passive line.' % (m(SETUP), m(STENCIL), m(LOAD), ATTR_SMALL))
P('')
P('| Board | Unique parts | Set-up | Stencil | Loading | Joints | Parts | Attrition | **Assembly** | PCB | **Order** |')
P('|---|---|---|---|---|---|---|---|---|---|---|')
for o in (P_, C_):
    f = o['fees']
    P('| %s | %d | %s | %s | %s | %s (%d) | %s | %s | **%s** | %s | **%s** |'
      % ('Power' if o['board'] == 'power' else 'Card', o['unique'], m(f['setup']), m(f['stencil']), m(f['loading']),
         m(f['joints']), o['joints'], m(o['parts']), m(o['attrition']), m(o['assembly']), m(o['pcb']), m(o['total'])))
P('')
P('## Stock on 2026-09-25 (JLC parts library, 00:15 PDT)')
P('')
P('Every one of the 61 JLC lines is in stock for 2 sets. The tight ones (JLC buys no attrition spares on these):')
P('')
P('| Part | LCSC | Stock | Needed for 2 sets | Note |')
P('|---|---|---|---|---|')
for code, note in (('C6843593', '**1 spare.** If it drops below 18 before you order, stop: tell me before placing it'),
                   ('C2877347', '**exactly 2.** Fallback: LM2940CS-12/NOPB C2865267 (stock 7): same TO-263 part, '
                                'rated 0 to 125 C and 45 V / 1 ms transients (TI SNVS769J)'),
                   ('C22427873', 'rev6 U25: in stock'), ('C2076400', 'rev6 R1: in stock'),
                   ('C29664285', ''), ('C49889', 'shared: 6 per card, 3 per power board'),
                   ('C145613', ''), ('C179842', '')):
    need = sum(l['qty'] for o in (P_, C_) for l in o['lines'] if l['lcsc'] == code)
    P('| %s | %s | %d | %d | %s |' % (stock[code]['model'], code, stock[code]['stock'], need, note))
P('')
P('Re-check on the day you order: JLC\'s BOM page shows any shortage when you upload the BOM. Or ask me to re-run the '
  'check (`bom/jlc_stock_2026-09-25.json` is today\'s).')
P('')
P('## Itemised JLC parts (everything JLC buys; excludes M1-M10 and L1)')
P('')
for o in (P_, C_):
    P('### %s' % ('Power board' if o['board'] == 'power' else 'Control card'))
    P('')
    P('| Refs | LCSC | MPN | Per board | Unit | Qty for 2 (+attrition) | $ |')
    P('|---|---|---|---|---|---|---|')
    for x in o['lines']:
        P('| %s | %s | %s | %d | $%.4f | %d (+%d) | %s |'
          % (x['refs'], x['lcsc'], x['mpn'], x['per_board'], x['unit'], x['qty'], x['attr'], m(x['usd'])))
    P('| **Total** | | | | | | **%s** |' % m(o['parts'] + o['attrition']))
    P('')
P('## Parts bought elsewhere')
P('')
P('| Item | Qty | Unit | $ | Source | Checked |')
P('|---|---|---|---|---|---|')
for it, q, u, src, ok in ELSEWHERE:
    P('| %s | %d | %s | %s | %s | %s |' % (it, q, m(u), m(q * u), src, ok))
P('| **Total** | | | **%s** | | |' % m(e_usd))
P('')
P('## Hardware for 2 sets')
P('')
P('| Part | Role | Qty | $ | Source | Checked | Page |')
P('|---|---|---|---|---|---|---|')
for it, role, q, usd, src, ok, link in HARDWARE:
    P('| %s | %s | %s | %s | %s | %s | [link](%s) |' % (it, role, q, m(usd), src, ok, link))
P('| **Total** | | | **%s** | | | |' % m(h_usd))
P('')
P('## Your buck converter: what it has to meet')
P('')
P('It is fed from J9 pin 9: the power board\'s 12 V LM2940 rail, through 88 mm of 0.3 mm track on the card (about '
  '0.1 ohm) and the MF-R020 PTC (1.50-2.84 ohm new, up to 4.40 ohm an hour after a trip; Bourns MF-R datasheet).')
P('')
P('1. **Input:** regulates from **11 to 13 V**. That is the 12 V rail less up to about 0.5 V across the track and PTC '
  'at 0.1 A. It should also **survive at least 20 V**: if U16 failed short, the battery rail (14-17 V) would reach it.')
P('2. **Output: 5.0 V, within +/-5 % (4.75-5.25 V), at least 200 mA continuous**, stable from no load. The Arduino '
  'plus CAN load is about 50 mA average and 120 mA peak (BUILD_NOTES).')
P('3. **Input current: at most about 0.1 A** at 200 mA out (85 % efficiency assumed). The PTC holds 0.20 A and trips at '
  '0.40 A (2.2 s maximum at 1.0 A). A module with soft-start keeps its switch-on inrush from tripping it; the '
  'LM2940\'s budget (about 120 mA extra, accepted 2026-09-23) also covers this.')
P('4. **Input filter: BUILD_NOTES does not contain one.** The idea ("filter at the buck end so the harness carries '
  'near-DC") was never written into BUILD_NOTES. **My proposal, for your OK:** a bulk capacitor across the buck\'s '
  'input terminals, **at least 22 uF, rated 25 V or more, aluminium electrolytic or polymer**, in addition to the '
  'module\'s own ceramic input capacitors. It supplies the switching current locally, so the 12 V wire carries near-DC. '
  'The PTC\'s 1.5-4.4 ohm in series already damps the wire\'s inductance against the module\'s ceramics. If you '
  'agree, I will add it to BUILD_NOTES.')
P('')
P('## Thermal pad: cheaper options checked, and the recommendation')
P('')
P('Full numbers in `cost/pad_options.txt` (from `tools/pad_options.py`). The board sits at 5.50 mm, so every pad is '
  'squeezed to **0.93 mm**. What changes between pads is how hard it presses and how much heat it passes.')
P('')
P('| Pad | Published data | At 0.93 mm | M1 Tj at 25 C water | Price | Verdict |')
P('|---|---|---|---|---|---|')
P('| **Parker THERM-A-GAP G579, 1.27 mm** (current) | 3.0 W/m-K; 30 Shore 00; deflection curve 22/33/55/68 % at '
  '5/10/25/50 psi; 4.5 C-cm2/W | 27 %, about 7 psi, 8 N per FET; worst case 1-48 % (always touching) | **about 78 C** '
  '(20.5 K across the pad at 6 W) | 9 x 9 in sheet only; price to read (URL list) | **Keep it.** No stack change |')
P('| t-Global TG-A3500F, 1.0 mm | 3.0 W/m-K; 35 Shore 00; curve 5/14/27 % at 10/30/50 psi; 1.35/1.02/0.90 C-in2/W | '
  '7 %, 14 psi, 15 N per FET; worst case -26 % (**loses contact**) to 34 % | about 89 C (31.7 K) | quote only '
  '(t-Global sells through distributors) | No: about 7x stiffer; a 1.5 mm pad would need over 54 N per FET |')
P('| Wurth WE-TGF, 3 W/m-K | one point: >= 20 % at 35.5 N/cm2 (51 psi); 4.9 K-cm2/W (2 mm) | force unknown (no '
  'curve); 20 % alone needs 55 N per FET | not computable | not readable | No: too stiff, and no curve |')
P('| McMaster-Carr 1272N32, 1.52 mm | 3 W/m-K, 40 Shore 00; **no compression data**, no dielectric strength, maker '
  'not named | 39 %, force unknown | not computable | **$26.91, 4 x 4 in** | No: fails your "publishes a compression '
  'curve" condition |')
P('')
P('**Result: the only cheap option publishes no compression data, and the options that do are far stiffer than '
  'G579.** At our fixed 0.93 mm, a stiffer pad either loses contact at the tolerance extremes or pushes the board '
  'up with several times the force. Keeping G579 means the standoff and washer stack stays as it is (5.0 mm stud + '
  '0.5 mm washer, 0.93 mm compressed, 27 %). Its junction-temperature figure is unchanged at about 78 C: 3.10 '
  'C-cm2/W of bulk at 0.93 mm, plus at most 2.23 of contact, over the 1.56 cm2 tab. Parker lists the 9 x 9 in sheet '
  'as the smallest (18 x 18 in is the other). One sheet cuts about 300 pads, 30 boards\' worth. Its price is the '
  'first line of the URL list.')
P('')
P('## URLs for you to read (the four unverified scenario-A lines)')
P('')
P('Digi-Key, Mouser, Newark, Arrow and RS all block this browser, and Essentra and Parker quote only on request. Open '
  'these and paste the prices back:')
P('')
P('1. Thermal pad sheet, **Parker 61-05-0909-G579** (FET pads; 1 sheet): '
  'https://www.digikey.com/en/products/result?keywords=61-05-0909-G579')
P('2. **Essentra HTSN-M3-5-3** (floor-to-board nylon stud; 8): '
  'https://www.digikey.com/en/products/result?keywords=HTSN-M3-5-3')
P('3. **Essentra HNSM3-20-5.5-1** (board-to-card nylon standoff; 8): '
  'https://www.digikey.com/en/products/detail/essentra-components/HNSM3-20-5-5-1/3813076')
P('4. **Boyd 7721-7PPSG** (shoulder washer in each FET tab hole; 8): '
  'https://www.digikey.com/en/products/result?keywords=7721-7PPSG')
P('')
P('## Still flagged')
P('')
P('1. The four lines above: estimates until you read them.')
P('2. Samtec ESQ/TSW: Mouser\'s prices as listed on Samtec\'s pages, not read on Mouser.')
P('3. TR washers and Wurth screws: Farnell UK prices in GBP, converted at an assumed %.2f USD/GBP.' % GBP)
P('4. JLC: quantity-1 prices. Price breaks or minimum buys may change a line by cents. Attrition follows the "about '
  '20 per small-passive line" read on 2026-09-24. Fees are from JLC\'s price page, not from a quote with the files '
  'uploaded; the upload can add charges.')
P('5. The Wurth WA-SCRW page link was not opened.')
P('')
P('Scenario B was dropped on 2026-09-25. Its files are kept, not developed further: '
  '`cost/BOOST_power_BOM_JLC_limitedDNP.csv`, `cost/BOOST_power_CPL_JLC_limitedDNP.csv`, '
  '`cost/COST_SUMMARY_AB_2026-09-24.md`.')
P('')
P('Generated by `tools/cost_summary.py`; every number is also in `cost/cost_summary.json`.')
open(os.path.join(HERE, 'COST_SUMMARY.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('power %.2f (pcb %.2f asm %.2f, %d unique)  card %.2f (pcb %.2f asm %.2f, %d unique)  elsewhere %.2f  hw %.2f  '
      'TOTAL %.2f' % (P_['total'], P_['pcb'], P_['assembly'], P_['unique'], C_['total'], C_['pcb'], C_['assembly'],
                      C_['unique'], e_usd, h_usd, total))
