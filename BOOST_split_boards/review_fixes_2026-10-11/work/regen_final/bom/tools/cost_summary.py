"""Cost summary for the chosen build, scenario A (updated 2026-10-01).

Copied from fab_2026-09-24/tools/cost_summary.py. Changes: the 6-layer control card (quote 2026-10-01), D28-D30,
stock and JLC prices from bom/jlc_snapshot_2026-09-30.json, the 220 uF shortage, and a "Ways to save" section.

Scenario A: 5 bare PCBs of each board, 2 complete sets assembled by JLCPCB, 3 spare bare boards of each.
Scenario B was dropped on 2026-09-25; its version of this script and document are kept as
tools/cost_summary_AB_2026-09-24.py and cost/COST_SUMMARY_AB_2026-09-24.md, and its BOM/CPL files stay in cost/.

Reads bom/SOURCING_TABLE.csv (JLC lines), bom/parts_from_boards.json (pad counts) and
bom/jlc_snapshot_2026-09-30.json (stock and quantity-1 prices read 2026-09-30, 23:55 PDT), and writes
COST_SUMMARY.md and cost/cost_summary.json.

  python tools/cost_summary.py
"""
import csv, json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # bom_2026-09-30/
BOM = os.path.join(HERE, 'bom')
OUT = os.path.join(HERE, 'cost')
os.makedirs(OUT, exist_ok=True)

rows = list(csv.DictReader(open(os.path.join(BOM, 'SOURCING_TABLE.csv'), encoding='utf-8')))
parts = json.load(open(os.path.join(BOM, 'parts_from_boards.json'), encoding='utf-8'))
stock = json.load(open(os.path.join(BOM, 'jlc_snapshot_2026-10-01.json'), encoding='utf-8'))['res']
npads = {b: {p['ref']: p['npads'] for p in parts[b]} for b in parts}

N = 2                      # boards of each assembled
PCB = {  # 5 boards, 1.6 mm, ENIG, 1 oz / 1 oz, epoxy filled & capped vias (JLC quote page, 2026-10-01)
    'power': dict(usd=69.57, what='6 layers, stackup JLC061611-7628D: 5 single boards, 74 x 86 mm', layers=6,
                  detail='$32.00 base, $17.30 ENIG, $3.47 TG155, $16.80 1 oz inner, $0.00 via covering, specified '
                         'stackup at no charge (8-9 day build)'),
    'card': dict(usd=56.83, layers=6,
                 what='6 layers, 0.5 oz inner copper: 5 panels, one 45 x 45 mm card on a 70 x 70 mm carrier (12.5 mm '
                      'rails, four sides, V-cut)',
                 detail='$33.00 engineering, $17.20 ENIG, $3.43 TG155, $3.20 board, $0.00 via covering, 0.5 oz inner '
                        'at no charge (8-9 day build)'),
}
CARD_SINGLE = 52.16        # 5 single 45 x 45 mm 6-layer cards, same options (0.5 oz inner)
CARD_8L_PANEL = 137.04     # the 8-layer card panel, 2026-09-24
CARD_6L_1OZ = 73.57        # 6 layers, 1 oz inner, 2026-10-01
SETUP, STENCIL, LOAD, JOINT = 51.12, 16.42, 1.53, 0.0016
ATTR_SMALL = 20
LIMITED = {'C6843593', 'C29664285', 'C49889', 'C4979367'}
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

# ---- bought elsewhere (2 sets) -------------------------------------------------------------------------------------
ELSEWHERE = [  # item, qty, unit, source, checked
    ('Samtec ESQ-115-44-G-D, J10 socket (power board)', N, 9.13, 'Mouser, as listed on samtec.com', 'read on samtec.com'),
    ('Samtec TSW-115-07-G-D, J11 header (card)', N, 3.18, 'Mouser, as listed on samtec.com', 'read on samtec.com'),
    ('Bourns MF-R050 PTC, 0.50 A hold (inline on the J9 pin-9 wire), LCSC C208476', N, 0.1433,
     'LCSC (its own order; JLC does not ship loose parts)', 'read 2026-09-30 (7,030 in stock); derating from the Bourns MF-R datasheet'),
]
# ---- hardware (2 sets) without the thermal pad -----------------------------------------------------------------------
HARDWARE = [  # item, role, qty text, cost, source, checked, link
    ('McMaster-Carr 92000A107, M2.5 x 12 pan head Phillips, 18-8 stainless, pack of 100', 'FET tab screws (4 per set)',
     '1 pack', 5.65, 'mcmaster.com', 'read', 'https://www.mcmaster.com/92000A107/'),
    ('McMaster-Carr 93657A200, nylon 6/6 spacer, M2.5, 2.0 mm long, 4.5 mm OD', 'FET tab-screw gap spacer (4 per set)',
     '8', 8 * 0.92, 'mcmaster.com ($0.92 each under 10)', 'read', 'https://www.mcmaster.com/93657A200/'),
    ('Boyd (Aavid) 7721-7PPSG shoulder washer, glass-filled PPS', 'insulates each tab screw in the FET tab hole (4 per set)',
     '8', 8 * 0.164, 'Digi-Key $0.164 at 5+ (10 for $1.51)', 'read by you 2026-09-25',
     'https://www.digikey.com/en/products/result?keywords=7721-7PPSG'),
    ('McMaster-Carr 92605A109, M3 x 20 mm set screw, 18-8 stainless, flat tip, pack of 25',
     'floor stud, part 1: threaded 6 mm into the floor (4 per set)', '1 pack', 10.69, 'mcmaster.com', 'read',
     'https://www.mcmaster.com/92605A109/'),
    ('McMaster-Carr 94669A099, aluminium unthreaded spacer, M3, 5.00 +/-0.13 mm long, 4.5 mm OD',
     'floor stud, part 2: sets the board height with the washer (4 per set; buy 10 to select 8)', '10', 10 * 0.50,
     'mcmaster.com ($0.50 each)', 'read', 'https://www.mcmaster.com/94669A099/'),
    ('Essentra HNSM3-20-5.5-1, nylon hex standoff M3 female-female, 20 mm', 'board-to-card standoff (4 per set)',
     '8', 8 * 1.416, 'Digi-Key $1.416 at 5+ (10 for $13.22)', 'read by you 2026-09-25',
     'https://www.digikey.com/en/products/detail/essentra-components/HNSM3-20-5-5-1/3813076'),
    ('TR Fastenings TR NWE-34815-M3, nylon 6/6 washer 3.2 x 7.0 x 0.5 mm, pack of 100', 'standoff shims (16 per set)',
     '1 pack', 8.71 * GBP, 'Farnell UK 8.71 GBP, converted at %.2f USD/GBP' % GBP, 'price via search; conversion assumed',
     'https://www.newark.com/tr-fastenings/tr-nwe-34815-m3/washer-nylon-6-6-3-2mm-pk100/dp/43Y4267'),
    ('Wurth Elektronik 97790803211, WA-SCRW M3 x 8 nylon 66 pan head', 'card screws (4 per set)', '8',
     8 * 0.199 * GBP, 'Farnell UK 0.199 GBP each, converted at %.2f USD/GBP' % GBP, 'price via search; conversion assumed',
     'https://www.we-online.com/en/components/products/WA-SCRW'),
]
PADS = [  # name, cost, note
    ('McMaster-Carr 1272N32, 3 W/m-K silicone, 0.060 in (1.52 mm), 4 x 4 in', 26.91, 'the default: read on mcmaster.com'),
    ('Parker 61-06-0909-G579, THERM-A-GAP 579, 0.060 in (1.524 mm), 9 x 9 in', 128.75, 'read by you at Digi-Key'),
    ('t-Global TG-AD30, 3.0 W/m-K, 1.5 mm, smallest sheet', None, 'price not read: URL for you'),
]
e_usd = sum(q * u for _, q, u, _, _ in ELSEWHERE)
h_usd = sum(h[3] for h in HARDWARE)
base = P_['total'] + C_['total'] + e_usd + h_usd
totals = {p[0]: (base + p[1] if p[1] is not None else None) for p in PADS}
PREV_TOTAL = 760.83   # 2026-09-25 total with the McMaster pad

json.dump(dict(power=P_, card=C_, elsewhere=ELSEWHERE, hardware=HARDWARE, pads=PADS, base_without_pad=round(base, 2),
               totals={k: (round(v, 2) if v else None) for k, v in totals.items()}),
          open(os.path.join(OUT, 'cost_summary.json'), 'w'), indent=1)


def m(x):
    return '$%s' % format(x, ',.2f')
exec(open(os.path.join(HERE, 'tools', 'savings.py'), encoding='utf-8').read())


cheap, g579 = totals[PADS[0][0]], totals[PADS[1][0]]
L = []
P = L.append
P('# BOOST: cost summary, scenario A (updated 2026-10-01)')
P('')
P('**Scenario A:** 5 bare PCBs of each board, 2 complete sets assembled by JLCPCB, 3 spare bare boards of each. '
  '**Shipping and tax are not included anywhere below.** Excluded because you own them: M1-M10, L1, the 12 V -> 5 V '
  'buck module and the J9 wires. Also excluded: case, battery cabling and lugs, Arduino Nano and CAN parts, LEDs.')
P('')
P('The BOM is schematic **rev6** (R1 = Bourns CSS4J-4026R-1L00F, U25 = INA241A4) **plus the pre-charge diodes '
  'D28-D30 (S2MW)**, with the **6-layer control card**.')
P('')
for x in SHORT_NOTE:
    P(x)
P('')
P('## Grand total')
P('')
P('| | Power board | Control card | Total |')
P('|---|---|---|---|')
P('| Bare PCBs (5 each) | %s | %s | %s |' % (m(P_['pcb']), m(C_['pcb']), m(P_['pcb'] + C_['pcb'])))
P('| JLC assembly of 2 each (fees + parts) | %s | %s | %s |' % (m(P_['assembly']), m(C_['assembly']),
                                                               m(P_['assembly'] + C_['assembly'])))
P('| Parts bought elsewhere (J10, J11, PTC) | | | %s |' % m(e_usd))
P('| Hardware for 2 sets, without the thermal pad | | | %s |' % m(h_usd))
P('| **Subtotal without the pad** | | | **%s** |' % m(base))
P('| + McMaster 1272N32 pad (default) | | | **%s** |' % m(cheap))
P('| + Parker G579 0.060 in pad instead | | | %s |' % m(g579))
P('| + t-Global TG-AD30 1.5 mm instead | | | %s + its price (not read) |' % m(base))
P('| Shipping, tax | | | not included |')
P('')
P('Against the 2026-09-25 total (%s with the McMaster pad):' % m(PREV_TOTAL))
P('- the control card went from 8 to 6 layers, then to 0.5 oz inner copper: %s -> %s -> %s for 5 panels;' % (m(CARD_8L_PANEL), m(CARD_6L_1OZ), m(PCB['card']['usd'])))
P('- D28-D30 (S2MW, LCSC C128729) were added to the power board: 3 parts, one more unique part to load;')
P('- every JLC part price and stock figure was read again on 2026-10-01;')
P('- the savings you approved on 2026-10-01 are applied (see "Ways to save").')
P('')
P('The JLC lines and the PTC were read on 2026-09-30 / 2026-10-01. The Samtec, McMaster, Digi-Key and Farnell '
  'prices are the 2026-09-25 readings, not read again. The TR washers and the Wurth screws are Farnell UK prices '
  'converted from GBP.')
P('')
for x in SAVINGS_MD:
    P(x)
P('')
P('## Bare PCBs (JLCPCB quote page, 2026-10-01)')
P('')
P('Both boards: 1.6 mm, FR4 TG155, ENIG, 1 oz outer copper, **Epoxy Filled & Capped vias ($0.00 at 6 and '
  '8 layers)**, min via 0.3 mm, Remove Mark, flying-probe full test. The power board is 6 layers with 1 oz inner '
  'copper on the specified stackup **JLC061611-7628D** (1.583 mm; order option "Specify Stackup: Yes"); the card is '
  '6 layers with 0.5 oz inner copper (the standard JLC 6-layer 1 / 0.5 oz build, 1.547 mm).')
P('')
P('| Board | Order | Price for 5 | Breakdown |')
P('|---|---|---|---|')
for b in ('power', 'card'):
    P('| %s | %s | %s | %s |' % ('Power' if b == 'power' else 'Card', PCB[b]['what'], m(PCB[b]['usd']), PCB[b]['detail']))
P('')
P('The card has to go on a carrier panel: JLC\'s Standard PCBA takes nothing under 70 x 70 mm, and Economic PCBA '
  'handles single-sided boards only (the card has parts on both sides). The panel costs %s more than 5 single '
  'cards (%s).'
  % (m(PCB['card']['usd'] - CARD_SINGLE), m(CARD_SINGLE)))
P('')
P('## Assembly (JLC Standard PCBA, 2 of each)')
P('')
P('Set-up %s and stencil %s per order (both boards are double-sided); feeder loading %s per unique part; $0.0016 per '
  'solder joint (JLC price page, read 2026-10-01). Parts: JLC quantity-1 prices read 2026-09-30, plus about %d '
  'attrition spares per '
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
for x in STOCK_MD:
    P(x)
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
    P('| %s | %d | $%.4f | %s | %s | %s |' % (it, q, u, m(q * u), src, ok))
P('| **Total** | | | **%s** | | |' % m(e_usd))
P('')
P('**PTC changed to MF-R050** (you asked, 2026-09-25). Bourns MF-R datasheet, thermal derating table:')
P('')
P('| | 23 C | 60 C | 70 C | 75 C (interpolated) | 85 C |')
P('|---|---|---|---|---|---|')
P('| MF-R020 hold / trip (A) | 0.20 / 0.40 | 0.13 / 0.26 | 0.11 / 0.22 | about 0.10 / 0.20 | 0.08 / 0.16 |')
P('| **MF-R050 hold / trip (A)** | **0.50 / 1.00** | 0.32 / 0.64 | 0.27 / 0.54 | **about 0.25 / 0.49** | 0.20 / 0.40 |')
P('')
P('The load is about 0.1 A. MF-R050 still holds about 2.5x that at 75 C. It trips at 1.0 A at room temperature, which '
  'protects the 26-28 AWG wire and the card\'s 0.3 mm track; the MC7812 limits its output at about 2.2 A (onsemi, typical peak). Its '
  'resistance is 0.41-0.77 ohm new and 1.17 ohm at most an hour after a trip, so the drop at 0.1 A is at most 0.12 V. '
  'Rated 60 V, -40 to +85 C.')
P('')
P('## Hardware for 2 sets')
P('')
P('| Part | Role | Qty | $ | Source | Checked | Page |')
P('|---|---|---|---|---|---|---|')
for it, role, q, usd, src, ok, link in HARDWARE:
    P('| %s | %s | %s | %s | %s | %s | [link](%s) |' % (it, role, q, m(usd), src, ok, link))
P('| **Total without the pad** | | | **%s** | | | |' % m(h_usd))
P('')
P('**Floor stud (replaces Essentra HTSN-M3-5-3, which Digi-Key sells only as 6,500 pieces).**')
P('- Preferred option: an M3 x 5 mm male-male hex standoff in small quantities.')
P('  - LCSC and McMaster have none. McMaster sells male-female and female-female only.')
P('  - LCSC\'s brass M3*5+6 pillars (C87703) come with no drawing: no hex size, length tolerance or thread depth.')
P('  - I could not read Keystone or Wurth parts through Digi-Key.')
P('- So it is your option 2, built from McMaster parts that publish their tolerances:')
P('  1. **92605A109**: M3 x 20 mm, 18-8 stainless, flat tip. Threaded 6 mm into the floor\'s 7 mm tapped hole with '
  'low-strength threadlocker, so 14 mm stands proud.')
P('  2. **94669A099**: aluminium spacer, 5.00 +/-0.13 mm long, 4.5 mm OD, 3.2 mm ID, dropped over it.')
P('  3. The TR washer (0.5 mm), then the power board. Underside at 5.50 mm, as before.')
P('  4. The HNSM3-20-5.5-1 screws onto the set screw with **6.9 mm of thread engaged** (3.9 mm with the old stud).')
P('     The card screw uses 4.9 mm of the other end, so 6.9 + 4.9 = 11.8 mm of the 20 mm standoff is used and the '
  'two cannot meet.')
P('- It is metal and does not creep. The clamp load sits in the steel screw (tension) and the aluminium spacer '
  '(compression); the only nylon in that path is the 0.5 mm washer.')
P('- Buy 10 spacers and fit the 8 whose spacer + washer measures closest to 5.50 mm; the target stays 5.50 +/-0.10 mm.')
P('- Low-strength threadlocker (Loctite 222 or similar) is not priced: most workshops have it.')
P('')
P('**Is a metal stud safe?** Yes. Measured on the plotted boards, 2026-09-25 (`tools/hole_isolation.py`):')
P('- H5-H8 are unplated 3.2 mm holes with no copper ring. The nearest copper on any layer is 3.10-3.49 mm from the '
  'hole centre, 1.5-1.9 mm from the hole wall.')
P('- The steel screw (1.5 mm radius) stays in the hole. The aluminium spacer (2.25 mm radius) sits under the 7.0 mm '
  'nylon washer, 0.5 mm below the board, so no metal reaches any copper.')
P('- The card (H1-H4) has only nylon at its holes: the standoff top and the card screw. Its nearest copper is '
  '3.36 mm from the centre.')
P('- Finding: each hole has a 3.5 mm-radius copper keep-out, but on the power board some track edges come to 3.10 mm '
  '(H6) and 3.21 mm (H5), inside that circle. KiCad\'s DRC does not flag them, so it appears to check these keep-outs '
  'less strictly than drawn.')
P('  - It does not matter for this hardware: that copper is under soldermask, below the nylon washer and the nylon '
  'standoff hex, never under metal.')
P('')
P('## Thermal pad: the ones you can buy')
P('')
P('Full numbers in `cost/pad_options.txt` (`tools/pad_options.py`). The stack puts every pad at **0.93 mm**. '
  'The approved G579 was 1.27 mm (27 %), but that sheet is not sold at Digi-Key; every pad below is about 1.5 mm, '
  'so about 39 %.')
P('')
P('| Pad | Published | At 0.93 mm (per FET, nominal / worst case) | M1 Tj, 25 C water | Price |')
P('|---|---|---|---|---|')
P('| Approved: G579 0.050 in, 1.27 mm | curve, 3.0 W/m-K, 7.9 kV/mm | 27 %: 7.7 N / 22 N (77 N for 10) | about 78 C | not '
  'sold |')
P('| **McMaster 1272N32**, 1.52 mm, 40 Shore 00 | 3 W/m-K only: **no curve, no dielectric strength** | 39 %: **about '
  '25 N / 49 N** (about 250 N for 10), estimated from 40 Shore 00 against G579\'s 30 (x1.6, +/-50 %) | about 78 C '
  '(contact assumed as G579) | **$26.91**, 4 x 4 in |')
P('| Parker 61-06-0909-G579, 1.524 mm, 30 Shore 00 | curve, 3.0 W/m-K, 7.9 kV/mm | 39 %: **15 N / 30 N** (151 N) from '
  'Parker\'s curve; 39 % is the top of Parker\'s "typical 5-40 %", and the worst case reaches 56 % | about 78 C | '
  '**$128.75**, 9 x 9 in |')
P('| **t-Global TG-AD30**, 1.5 mm, 20 Shore 00 | curve, 3.0 W/m-K, **>= 5 kV/mm** | 38 %: **12 N / 24 N** (116 N) | '
  '**about 71 C** | not read (URL below) |')
P('')
P('**What 39 % means for the stack.** The stack height does not change: 0.93 mm is fixed by the 5.50 mm board height. '
  'What changes is the force.')
P('- **Force.** About twice the approved design with G579, and an estimated three times with the McMaster pad '
  '(roughly 150 N and 250 N over ten FETs, against 77 N).')
P('- **Where it goes.** It pushes the power board up. The board is held down by the four standoffs, and near '
  'M1/M8/M9/M10 by the tab-screw heads once the board has lifted their 0.25 mm of free play.')
P('- **The standoffs.** With the metal stud above, the load sits in steel and aluminium. The nylon standoff\'s 6.9 mm '
  'of thread takes about 60 N each, roughly 2 MPa, which is small. So it **does not change the standoff choice**; it '
  'is one more reason to prefer the metal stud to a nylon one.')
P('- **Board bow.** The extra force will bow the board up a little between supports, which unloads the middle pads '
  'somewhat. I have not modelled the board (no FEA).')
P('- **Not recommended:** shimming the board up 0.25 mm to get back to about 22 %. That also lifts the card, and the '
  'card screw heads would come to 0.40 mm under the lid, against 0.65 mm now.')
P('')
P('**Recommendation.**')
P('- If TG-AD30 comes in a 1.5 mm sheet of 150 x 150 mm or less for about $40 or less, buy it. It is the only '
  'candidate that is soft, publishes both a curve and a dielectric strength, and it lowers M1 by about 7 C.')
P('- Otherwise buy the McMaster 1272N32 (the default). Its risk is the missing dielectric rating, covered by the '
  'tab-to-case test now in BUILD_NOTES.')
P('- The G579 at $128.75 works, but costs about five times as much for nothing extra.')
P('')
P('## Your buck converter')
P('')
P('Fed from J9 pin 9 (the 12 V MC7812 rail) through the MF-R050. It has to:')
P('- regulate from about 9.5 V to 13 V in (the MC7812 rail sags to about 9.7-10.2 V near the end of a 4S '
  'discharge), and survive at least 20 V;')
P('- give 5.0 V +/-5 % at 200 mA or more;')
P('- draw about 0.1 A.')
P('')
P('**No extra input filter** (your decision, 2026-09-25): the converter has its own input capacitors, and the draw '
  'is about 0.1 A. This is noted in BUILD_NOTES.')
P('')
P('## URLs for you to read')
P('')
P('One line is left:')
P('')
P('1. **t-Global TG-AD30** (FET thermal pads; you need about 10 x 16 mm x 20 pads, a 100 x 100 mm sheet is plenty). '
  'Look for 1.5 mm thickness and the smallest sheet: https://www.digikey.com/en/products/result?keywords=TG-AD30')
P('')
P('## Still flagged')
P('')
P('1. TR washers and Wurth screws: Farnell UK prices in GBP, converted at an assumed %.2f USD/GBP.' % GBP)
P('2. The McMaster pad\'s force is an estimate from its hardness (+/-50 %), and it publishes no dielectric strength.')
P('3. Samtec ESQ/TSW: Mouser\'s prices as listed on Samtec\'s pages, not read on Mouser.')
P('4. JLC: quantity-1 prices, attrition about 20 per small-passive line, fees from JLC\'s price page. The upload '
  'itself may add charges.')
P('5. The Wurth WA-SCRW page link was not opened.')
P('6. The Samtec, McMaster, Digi-Key and Farnell prices were not read again after 2026-09-25.')
P('')
P('Scenario B was dropped on 2026-09-25. Its files are kept, not developed further: '
  '`cost/BOOST_power_BOM_JLC_limitedDNP.csv`, `cost/BOOST_power_CPL_JLC_limitedDNP.csv`, '
  '`cost/COST_SUMMARY_AB_2026-09-24.md`.')
P('')
P('Generated by `BOOST_split_boards/bom_2026-09-30/tools/cost_summary.py`; every number is also in '
  '`cost/cost_summary.json` there.')
open(os.path.join(HERE, 'COST_SUMMARY.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('power %.2f  card %.2f  elsewhere %.2f  hardware %.2f  base %.2f  +McMaster %.2f  +G579 %.2f'
      % (P_['total'], C_['total'], e_usd, h_usd, base, cheap, g579))
