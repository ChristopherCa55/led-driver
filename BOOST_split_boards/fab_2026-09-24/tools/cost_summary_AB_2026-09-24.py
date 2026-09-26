"""Cost summary for the two build scenarios (2026-09-24).

Reads bom/SOURCING_TABLE.csv (JLC lines, unit prices), bom/parts_from_boards.json (pad counts) and
bom/jlc_snapshot_2026-09-24.json, and writes:
  COST_SUMMARY.md                               the document
  cost/cost_summary.json                        every number in it
  cost/BOOST_power_BOM_JLC_limitedDNP.csv       power BOM with the stock-limited lines left off (scenario B)
  cost/BOOST_power_CPL_JLC_limitedDNP.csv       its pick-and-place

  python tools/cost_summary.py
"""
import csv, json, math, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = os.path.join(HERE, 'bom')
OUT = os.path.join(HERE, 'cost')
os.makedirs(OUT, exist_ok=True)

rows = list(csv.DictReader(open(os.path.join(BOM, 'SOURCING_TABLE.csv'), encoding='utf-8')))
parts = json.load(open(os.path.join(BOM, 'parts_from_boards.json'), encoding='utf-8'))
snap = json.load(open(os.path.join(BOM, 'jlc_snapshot_2026-09-24.json'), encoding='utf-8'))
npads = {b: {p['ref']: p['npads'] for p in parts[b]} for b in parts}

# ---- JLCPCB prices read on 2026-09-24 ------------------------------------------------------------------------
PCB = {  # 5 boards, 8 layers, 1.6 mm, ENIG, 1 oz / 1 oz, epoxy filled & capped vias, 10-11 day build
    'power': dict(usd=124.10, what='74 x 86 mm single boards, 5 pcs',
                  detail='$90.00 base, $17.30 ENIG, $16.80 1 oz inner, $0.00 via fill'),
    'card': dict(usd=137.04, what='5 panels, each one card on a 70 x 70 mm carrier (12.5 mm rails on four sides, V-cut)',
                 detail='$99.00 engineering, $17.20 ENIG, $16.74 1 oz inner, $4.10 board, $0.00 via fill'),
}
CARD_SINGLE = 123.42  # the same card as 5 single boards (cannot be assembled: under 70 x 70 mm)
SETUP, STENCIL, LOAD, JOINT = 51.12, 16.42, 1.53, 0.0016
ATTR_SMALL = 20        # JLC attrition on small passives: about 20 extra per line (read 2026-09-24)
SHIP_DHL = 29.45       # quoted DHL for the bare-PCB order, NOT included in the totals

LIMITED = {'C6843593', 'C29664285', 'C49889', 'C2877347'}   # 220 uF, 680 uF, MCP6241, LM2940S-12
CS_GRADE = 'C2865267'                                        # LM2940CS-12/NOPB, stock 7

jlc = [r for r in rows if r['list'] == 'JLC']
for r in jlc:
    r['refs_l'] = r['refs'].split()
    r['n'] = len(r['refs_l'])
    r['unit'] = float(r['unit_usd'])
    r['pads'] = sum(npads[r['board']][x] for x in r['refs_l'])


def order(board, n, drop=(), swap=None, label=''):
    """One JLC order of `board`, `n` boards assembled. drop: LCSC codes left off; swap: {old: new LCSC}."""
    swap = swap or {}
    lines, parts_usd, attr_usd, joints, seen = [], 0.0, 0.0, 0, set()
    for r in jlc:
        if r['board'] != board or r['lcsc'] in drop:
            continue
        code = swap.get(r['lcsc'], r['lcsc'])
        unit = snap[code]['p1'] if code != r['lcsc'] else r['unit']
        # attrition and feeder loading are per unique part: two table lines can share one LCSC part (the 5.1 ohms)
        attr = ATTR_SMALL if (unit < 0.10 and code not in LIMITED and code not in seen) else 0
        seen.add(code)
        cost = unit * (r['n'] * n + attr)
        lines.append(dict(refs=r['refs'], lcsc=code, mpn=snap[code]['model'] if code != r['lcsc'] else r['mpn'],
                          per_board=r['n'], qty=r['n'] * n, attr=attr, unit=unit, usd=round(cost, 2)))
        parts_usd += unit * r['n'] * n
        attr_usd += unit * attr
        joints += r['pads'] * n
    fees = dict(setup=SETUP, stencil=STENCIL, loading=round(LOAD * len(seen), 2),
                joints=round(JOINT * joints, 2))
    asm = sum(fees.values())
    tot = PCB[board]['usd'] + asm + parts_usd + attr_usd
    return dict(board=board, label=label, n=n, unique=len(seen), joints=joints, pcb=PCB[board]['usd'], fees=fees,
                fees_usd=round(asm, 2), parts=round(parts_usd, 2), attrition=round(attr_usd, 2),
                assembly_total=round(asm + parts_usd + attr_usd, 2), total=round(tot, 2), lines=lines)


# ---- orders per scenario --------------------------------------------------------------------------------------
A_power = order('power', 2, label='A: power, 5 PCBs, 2 assembled complete')
A_card = order('card', 2, label='A: card, 5 PCBs, 2 assembled complete')
DROP = ('C6843593', 'C29664285', 'C49889')
B2_power = order('power', 3, drop=DROP, swap={'C2877347': CS_GRADE},
                 label='B: power order 2, 5 PCBs, 3 assembled without the limited lines')
B_card = order('card', 5, label='B: card, 5 PCBs, 5 assembled complete')
B1_power = order('power', 5, drop=DROP, swap={'C2877347': CS_GRADE},
                 label='B alternative: power, 5 PCBs, all 5 assembled without the limited lines')

# ---- bought elsewhere ------------------------------------------------------------------------------------------
# (item, unit USD, source, verified?)
J10 = ('Samtec ESQ-115-44-G-D (J10 socket)', 9.13, 'Mouser, as listed on Samtec\'s product page', 'read on samtec.com')
J11 = ('Samtec TSW-115-07-G-D (J11 header)', 3.18, 'Mouser, as listed on Samtec\'s product page', 'read on samtec.com')
HF = {  # hand-fit stock-limited parts, per power board
    'C6843593': ('Panasonic EEH-ZU1H221P 220 uF 50 V', 9, 3.08, 'Digi-Key (search-engine summary)', 'UNVERIFIED'),
    'C29664285': ('Panasonic EEH-ZU1E681UP 680 uF 25 V', 3, 3.13, 'Digi-Key (search-engine summary)', 'UNVERIFIED'),
    'C49889': ('Microchip MCP6241T-E/OT', 3, 0.69, 'placeholder: JLC\'s price; distributor price not read', 'UNVERIFIED'),
}


def elsewhere(n_sets, n_handfit):
    items = [dict(item=J10[0], qty=n_sets, unit=J10[1], usd=round(J10[1] * n_sets, 2), src=J10[2], ok=J10[3]),
             dict(item=J11[0], qty=n_sets, unit=J11[1], usd=round(J11[1] * n_sets, 2), src=J11[2], ok=J11[3])]
    if n_handfit:
        for code, (name, per, unit, src, ok) in HF.items():
            q = per * n_handfit + 1
            items.append(dict(item=name + ' (hand-fit, 1 spare)', qty=q, unit=unit, usd=round(unit * q, 2), src=src,
                              ok=ok))
    return items


# ---- hardware ---------------------------------------------------------------------------------------------------
GBP = 1.34  # USD per GBP used to convert the Farnell UK prices: an assumption, not a quoted rate


def hardware(n):
    H = []

    def add(item, role, qty, unit, usd, src, ok, link):
        H.append(dict(item=item, role=role, qty=qty, unit=unit, usd=round(usd, 2), src=src, ok=ok, link=link))
    add('Parker Chomerics 61-05-0909-G579 THERM-A-GAP 579, 1.27 mm, 9 x 9 in sheet', 'FET thermal pads (cut 10 x 16 mm)',
        '1 sheet', 'about $85', 85.0, 'no price found for -05; Digi-Key lists -04 at $66.10 and -06 at $110.83',
        'ESTIMATE', 'https://ph.parker.com/us/en/product/therm-a-gap-579-thermally-conductive-gap-filler-pads/61-05-0909-g579')
    add('McMaster-Carr 92000A107, M2.5 x 12 pan head Phillips, 18-8 stainless', 'FET tab screws (4 per set)',
        '1 pack of 100', '$5.65 / 100', 5.65, 'mcmaster.com', 'read on mcmaster.com', 'https://www.mcmaster.com/92000A107/')
    q = 4 * n
    add('McMaster-Carr 93657A200, nylon 6/6 spacer, M2.5, 2.0 mm long, 4.5 mm OD', 'FET tab-screw gap spacer (4 per set)',
        q, '$0.92 (1-9), $0.75 (10+)', q * (0.75 if q >= 10 else 0.92), 'mcmaster.com', 'read on mcmaster.com',
        'https://www.mcmaster.com/93657A200/')
    add('Boyd (Aavid) 7721-7PPSG shoulder washer, glass-filled PPS', 'insulates the tab screw in the tab hole (4 per set)',
        q, '$0.26', q * 0.26, 'Digi-Key / Allied (search-engine summary)', 'UNVERIFIED',
        'https://eu.mouser.com/ProductDetail/Aavid/7721-7PPSG?qs=NqprlHOmxN1c1LnnOZYpOw%3D%3D')
    add('Essentra HTSN-M3-5-3, nylon hex stud M3 male-male, 5 mm', 'board standoff, floor side (4 per set)',
        q, 'about $0.60', q * 0.60, 'Digi-Key lists $0.48 at 500; small-quantity price not read', 'ESTIMATE',
        'https://www.essentracomponents.com/en-us/p/pcb-standoffs-hexagonal-metric-imperial-threaded-plastic')
    add('Essentra HNSM3-20-5.5-1, nylon hex standoff M3 female-female, 20 mm', 'card standoff (4 per set)',
        q, 'about $0.80', q * 0.80, 'no public price found (Essentra quotes on request)', 'ESTIMATE',
        'https://www.essentracomponents.com/en-us/p/pcb-standoffs-hexagonal-metric-imperial-threaded-plastic/hnsm3-20-5-5-1')
    packs = math.ceil(16 * n / 100)
    add('TR Fastenings TR NWE-34815-M3, nylon 6/6 washer 3.2 x 7.0 x 0.5 mm, pack of 100', 'standoff shims (16 per set)',
        '%d pack' % packs, '8.71 GBP / 100', packs * 8.71 * GBP, 'Farnell UK, converted at %.2f USD/GBP' % GBP,
        'price read via search; USD conversion assumed',
        'https://www.newark.com/tr-fastenings/tr-nwe-34815-m3/washer-nylon-6-6-3-2mm-pk100/dp/43Y4267')
    add('Wurth Elektronik 97790803211, WA-SCRW M3 x 8 nylon 66 pan head', 'card screws (4 per set)',
        q, '0.199 GBP', q * 0.199 * GBP, 'Farnell UK, converted at %.2f USD/GBP' % GBP,
        'price read via search; USD conversion assumed; link not opened',
        'https://www.we-online.com/en/components/products/WA-SCRW')
    add('Pololu D24V5F5, 5 V 500 mA step-down module (5.1-36 V in)', '12 V -> 5 V at the Arduino end (1 per set)',
        n, '$8.95 (1), $8.23 (5+)', n * (8.23 if n >= 5 else 8.95), 'pololu.com', 'read on pololu.com',
        'https://www.pololu.com/product/2843')
    packs = 1 if n <= 2 else 2
    add('Adafruit 793, 40 female-female jumper wires, 300 mm, 28 AWG', 'J9 wires and Nano plug (11 per set)',
        '%d pack' % packs, '$7.95', packs * 7.95, 'adafruit.com', 'read on adafruit.com',
        'https://www.adafruit.com/product/793')
    add('Bourns MF-R020, 0.20 A hold radial PTC', 'inline fuse on the J9 pin-9 (12 V) wire (1 per set)',
        n, '$0.14', n * 0.14, 'LCSC (a separate LCSC order; JLC does not ship loose parts)',
        'read on lcsc.com; datasheet link not opened',
        'https://www.bourns.com/docs/Product-Datasheets/mfr.pdf')
    return H


def scen(orders, n_sets, n_handfit, name):
    e = elsewhere(n_sets, n_handfit)
    h = hardware(n_sets)
    pcb = sum(o['pcb'] for o in orders)
    asm = sum(o['assembly_total'] for o in orders)
    out = dict(name=name, orders=[o['label'] for o in orders], pcb=round(pcb, 2), assembly=round(asm, 2),
               elsewhere=round(sum(x['usd'] for x in e), 2), hardware=round(sum(x['usd'] for x in h), 2),
               elsewhere_items=e, hardware_items=h)
    out['total'] = round(out['pcb'] + out['assembly'] + out['elsewhere'] + out['hardware'], 2)
    return out


SA = scen([A_power, A_card], 2, 0, 'A')
SB = scen([A_power, B2_power, B_card], 5, 3, 'B')
SB1 = scen([B1_power, B_card], 5, 5, 'B, one power order')

json.dump(dict(orders=dict(A_power=A_power, A_card=A_card, B2_power=B2_power, B_card=B_card, B1_power=B1_power),
               scenarios=[SA, SB, SB1]), open(os.path.join(OUT, 'cost_summary.json'), 'w'), indent=1)

# ---- scenario-B power BOM / CPL without the limited lines ------------------------------------------------------
src_bom = list(csv.reader(open(os.path.join(BOM, 'BOOST_power_BOM_JLC.csv'), encoding='utf-8')))
drop_refs = set()
with open(os.path.join(OUT, 'BOOST_power_BOM_JLC_limitedDNP.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(src_bom[0])
    for r in src_bom[1:]:
        if r[3] in DROP:
            drop_refs.update(r[1].split(','))
            continue
        if r[3] == 'C2877347':
            r = ['LM2940CS-12/NOPB', r[1], r[2], CS_GRADE]
        w.writerow(r)
src_cpl = list(csv.reader(open(os.path.join(BOM, 'BOOST_power_CPL_JLC.csv'), encoding='utf-8')))
with open(os.path.join(OUT, 'BOOST_power_CPL_JLC_limitedDNP.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    for r in src_cpl:
        if r[0] not in drop_refs:
            w.writerow(r)


# ---- the document -----------------------------------------------------------------------------------------------
def m(x):
    return '$%s' % format(x, ',.2f')


L = []
P = L.append
P('# BOOST: cost summary (2026-09-24)')
P('')
P('Both boards are still **NOT_FOR_FAB**: pick a scenario first. The numbers come from JLCPCB\'s quote page and parts '
  'library on 2026-09-24, and from distributor pages where noted. **Shipping and tax: not included** anywhere below. '
  'Items marked **ESTIMATE** or **UNVERIFIED** are listed at the end.')
P('')
P('Excluded, because you own them: M1-M10 (HYG180N10) and L1 (CSCF3218-6R8MC). Also excluded: the case, battery '
  'cabling and lugs, the Arduino Nano and its CAN parts, and the LEDs and their wiring.')
P('')
P('The BOM is schematic **rev6** (R1 = Bourns CSS4J-4026R-1L00F 1 mOhm, U25 = INA241A4). Rev6 is prepared but not yet '
  'written into your schematic; see "If you stay on rev5" below.')
P('')
P('## The scenarios at a glance')
P('')
P('| | **A**: 5 bare PCBs of each board, 2 complete sets | **B**: A plus 3 more boards of each assembled without the '
  'stock-limited parts | B alternative: one power order |')
P('|---|---|---|---|')
P('| PCB orders | power x1, card x1 | power x2, card x1 | power x1, card x1 |')
P('| Assembled by JLC | 2 power + 2 card, complete | 2 power complete + 3 power without the limited lines; 5 cards '
  'complete | 5 power without the limited lines; 5 cards complete |')
P('| Bare spare PCBs | 3 power, 3 card | 5 power, 0 card | 0 power, 0 card |')
P('| You hand-fit (beyond J10/J11) | nothing | on 3 power boards: 9 x 220 uF, 3 x 680 uF, 3 x MCP6241 each | the same '
  'on all 5 power boards |')
for key, lab in (('pcb', 'Bare PCBs'), ('assembly', 'JLC assembly (fees + parts)'),
                 ('elsewhere', 'Parts bought elsewhere'), ('hardware', 'Hardware')):
    P('| %s | %s | %s | %s |' % (lab, m(SA[key]), m(SB[key]), m(SB1[key])))
P('| **Grand total** | **%s** | **%s** | **%s** |' % (m(SA['total']), m(SB['total']), m(SB1['total'])))
P('| Shipping, tax | not included | not included | not included |')
P('')
P('Why B needs a second power order: JLC applies one BOM to every board in an order, so one order cannot give 2 '
  'complete power boards and 3 without the limited lines. The card has no limited line once the shared MCP6241 stock '
  'goes to the cards (below), so one card order covers all 5. "B alternative" saves the second power PCB order and '
  'set-up, but then **none** of the five power boards comes complete: you hand-fit the limited parts on all five.')
P('')
P('For scale, DHL was quoted at %s for one bare-PCB order (0.17-0.22 kg). Assembled orders weigh more and ship '
  'separately per order. **Not included.**' % m(SHIP_DHL))
P('')
P('## Stock-limited lines at 5 sets (JLC stock on 2026-09-24; JLC buys no attrition spares on these)')
P('')
P('| Line | Per power board | Per card | Need for 5 sets | JLC stock | Covers | Alternate at JLC | Does it remove the limit? |')
P('|---|---|---|---|---|---|---|---|')
P('| EEH-ZU1H221P 220 uF 50 V (C70 C71 C74 C75 C77 C78 C86 C87 C88) | 9 | 0 | 45 | 19 | 2 power boards | '
  'EEH-ZU1H221V (C7182696), stock 12, 17.1 mm tall | **No**: 31 together, and the V part\'s land pattern is not checked '
  'against the footprint |')
P('| EEH-ZU1E681UP 680 uF 25 V (C40 C69 C85) | 3 | 0 | 15 | 10 | 3 power boards | EEH-ZU1E681UV (C23810697), stock 10 '
  '| **Possibly**: 20 together is enough if one ref per board used the V part, but its datasheet and land pattern are '
  '**not checked**. I have not used it |')
P('| MCP6241T-E/OT (power U6 U11 U12; card U3 U7 U13 U22 U23 U24) | 3 | 6 | 45 | 38 | 4 sets | MCP6241RT-E/OT (29), '
  'MCP6241UT-E/OT (6) | **No**: Microchip DS21882D draws different SOT-23-5 pinouts for them (the R version has VDD '
  'and VSS swapped: pin 5 is VSS). The SOIC-8 versions need a different footprint |')
P('| LM2940S-12/NOPB (U16) | 1 | 0 | 5 | 2 | 2 power boards | **LM2940CS-12/NOPB (C2865267), stock 7** | **Yes**, '
  'used for the scenario-B boards. TI SNVS769J: same TO-263 part in the C grade, rated 0 to 125 C (the S grade is '
  '-40 to 125 C) and 45 V / 1 ms input transients |')
P('')
P('Allocation used for B: the cards get 30 MCP6241 and the 2 complete power boards get 6, 36 of the 38. The 3 extra '
  'power boards have U6/U11/U12 left off for you to fit. Scenario A uses exactly the 2 LM2940S-12 in stock. If one '
  'goes before you order, use the CS grade on A as well: it is the same file change as the B BOM.')
P('')
P('## Bare PCBs (JLCPCB quote page, 2026-09-24)')
P('')
P('Both boards: 8 layers, 1.6 mm, FR4 TG155, ENIG, 1 oz outer / 1 oz inner, **epoxy filled and capped vias ($0.00 at '
  '8 layers)**, 0.3 mm minimum via, Remove Mark, full flying-probe test, 10-11 day build.')
P('')
P('| Board | What you order | Price for 5 | Breakdown |')
P('|---|---|---|---|')
P('| Power | %s | %s | %s |' % (PCB['power']['what'], m(PCB['power']['usd']), PCB['power']['detail']))
P('| Card | %s | %s | %s |' % (PCB['card']['what'], m(PCB['card']['usd']), PCB['card']['detail']))
P('')
P('**Panelising the card costs %s** (%s as a carrier panel against %s as 5 single 45 x 45 mm boards). It is needed '
  'because JLC\'s Standard PCBA takes nothing under 70 x 70 mm. Economic PCBA would take the small board but '
  'handles 2/4/6 layers, single-sided only. The carrier is one card per panel with V-cut 12.5 mm rails, so "5 PCBs" is '
  'still 5 cards. A 2-up panel (90 x 70 mm) would give 10 cards per order.'
  % (m(PCB['card']['usd'] - CARD_SINGLE), m(PCB['card']['usd']), m(CARD_SINGLE)))
P('')
P('## Assembly per order (JLC Standard PCBA)')
P('')
P('Fees from JLC\'s PCBA price page: set-up %s and stencil %s per order (both boards are double-sided); feeder '
  'loading %s per unique part (Basic or Extended alike in Standard PCBA); %s per solder joint. Parts are JLC\'s '
  'quantity-1 prices, plus attrition of about %d spares per small-passive line (lines under $0.10).'
  % (m(SETUP), m(STENCIL), m(LOAD), '$0.0016', ATTR_SMALL))
P('')
P('| Order | Boards assembled | Unique parts | Set-up | Stencil | Loading | Joints | Parts | Attrition | **Assembly '
  'total** | PCB | **Order total** |')
P('|---|---|---|---|---|---|---|---|---|---|---|---|')
for o in (A_power, A_card, B2_power, B_card, B1_power):
    f = o['fees']
    P('| %s | %d | %d | %s | %s | %s | %s (%d) | %s | %s | **%s** | %s | **%s** |'
      % (o['label'], o['n'], o['unique'], m(f['setup']), m(f['stencil']), m(f['loading']), m(f['joints']), o['joints'],
         m(o['parts']), m(o['attrition']), m(o['assembly_total']), m(o['pcb']), m(o['total'])))
P('')
P('The scenario-B power order uses `cost/BOOST_power_BOM_JLC_limitedDNP.csv` and '
  '`cost/BOOST_power_CPL_JLC_limitedDNP.csv`. They are the approved files with the 220 uF, 680 uF and MCP6241 lines '
  'left off and U16 set to LM2940CS-12/NOPB (C2865267).')
P('')
P('## Itemised JLC parts (everything JLC buys; excludes M1-M10 and L1)')
P('')
P('Unit prices are JLC\'s at quantity 1. "A" is 2 boards; "B" is the extra boards in B, each with its own order.')
P('')
for board, oa, ob in (('power', A_power, B2_power), ('card', A_card, B_card)):
    P('### %s' % ('Power board' if board == 'power' else 'Control card'))
    P('')
    P('| Refs | LCSC | MPN | Per board | Unit | A: qty (+attrition) | A: $ | B order: qty (+attrition) | B order: $ |')
    P('|---|---|---|---|---|---|---|---|---|')
    bl = {x['refs']: x for x in ob['lines']}
    for x in oa['lines']:
        y = bl.get(x['refs'])
        yb = ('%d (+%d)' % (y['qty'], y['attr']), m(y['usd'])) if y else ('**you fit**', '-')
        if y and y['lcsc'] != x['lcsc']:
            yb = ('%d (+%d) as %s %s' % (y['qty'], y['attr'], y['lcsc'], y['mpn']), m(y['usd']))
        P('| %s | %s | %s | %d | %s | %d (+%d) | %s | %s | %s |'
          % (x['refs'], x['lcsc'], x['mpn'], x['per_board'], '$%.4f' % x['unit'], x['qty'], x['attr'], m(x['usd']),
             yb[0], yb[1]))
    P('| **Total** | | | | | | **%s** | | **%s** |'
      % (m(oa['parts'] + oa['attrition']), m(ob['parts'] + ob['attrition'])))
    P('')
    if board == 'card':
        P('The card\'s B order assembles all 5 boards, so its "B order" column is the whole 5-board order, not an '
          'addition to A.')
        P('')
P('## Parts bought elsewhere')
P('')
P('| Item | A: qty | A: $ | B: qty | B: $ | Unit | Source | Checked |')
P('|---|---|---|---|---|---|---|---|')
ea = {x['item']: x for x in SA['elsewhere_items']}
for x in SB['elsewhere_items']:
    a = ea.get(x['item'])
    P('| %s | %s | %s | %d | %s | %s | %s | %s |'
      % (x['item'], a['qty'] if a else '-', m(a['usd']) if a else '-', x['qty'], m(x['usd']), m(x['unit']), x['src'],
         x['ok']))
P('| **Total** | | **%s** | | **%s** | | | |' % (m(SA['elsewhere']), m(SB['elsewhere'])))
P('')
P('Digi-Key, Mouser and Octopart show bot-check pages to my browser, and I did not get past them. So the Samtec prices '
  'are Mouser\'s as Samtec\'s own product pages list them, and the can prices are what a search engine reported from '
  'Digi-Key. B alternative (all five power boards hand-fitted) needs 46 x 220 uF, 16 x 680 uF and 16 x MCP6241: %s '
  'elsewhere in total.' % m(SB1['elsewhere']))
P('')
P('## Hardware (per assembled set: 4 tab screws, 4 standoff stacks, 4 card screws, the Arduino-end parts)')
P('')
P('| Part | Role | A: qty | A: $ | B: qty | B: $ | Unit price | Source | Checked | Datasheet / page |')
P('|---|---|---|---|---|---|---|---|---|---|')
ha = SA['hardware_items']
for a, b in zip(ha, SB['hardware_items']):
    P('| %s | %s | %s | %s | %s | %s | %s | %s | %s | [link](%s) |'
      % (b['item'], b['role'], a['qty'], m(a['usd']), b['qty'], m(b['usd']), b['unit'], b['src'], b['ok'], b['link']))
P('| **Total** | | | **%s** | | **%s** | | | | |' % (m(SA['hardware']), m(SB['hardware'])))
P('')
P('Choices made for the parts that had none:')
P('- **Tab-screw spacer: McMaster 93657A200 (2.0 mm)** in place of the 2.25 mm spacer. No stocked 0.25 mm shim was '
  'found. The thermal-pad compression comes from the standoff height, not the tab screw, which only retains the FET.')
P('- **Tab screw: McMaster 92000A107.** Its head is 2.1 mm tall; the 3D model used 1.75 mm.')
P('- **Standoff washers: TR Fastenings TR NWE-34815-M3.** Essentra\'s NWE-34815-M3 is obsolete at Digi-Key; this is '
  'the same washer, stocked at Farnell/Newark.')
P('- **Arduino-end 5 V: Pololu D24V5F5.** **J9 wires and plug: Adafruit 793**: cut each jumper and solder the cut end '
  'into J9. The female housing then plugs onto the Nano\'s pins. I have not checked the pack\'s colour mix against '
  'the J9 table: where a colour is missing, use white with a coloured marker (BUILD_NOTES already allows that for pin '
  '11). **PTC: Bourns MF-R020.**')
P('')
P('## If you stay on rev5 (2 mOhm R1, INA241A3)')
P('')
P('The fallback you set: keep 2 mOhm with the INA241A3 and hand-fit R1. Per power board, JLC then fits INA241A3IDR '
  '(C22427652, %s, **stock 16**: enough for all scenarios) instead of INA241A4 (%s); R1 (Bourns CSS4J-4026K-2L00F) is '
  '0 at JLC and gets bought elsewhere at about %s (JLC\'s listed price; distributor price **UNVERIFIED**). That is '
  'about +%s per power board, and one fewer JLC line (-%s loading).'
  % (m(snap['C22427652']['p1']), m(snap['C22427873']['p1']), m(snap['C2076167']['p1']),
     m(snap['C22427652']['p1'] - snap['C22427873']['p1'] + snap['C2076167']['p1'] - snap['C2076400']['p1']), m(LOAD)))
P('')
P('## Unverified or estimated (flagged)')
P('')
P('1. **Distributor prices for the hand-fit cans** (EEH-ZU1H221P $3.08, EEH-ZU1E681UP $3.13): a search engine\'s '
  'summary of Digi-Key, not read on Digi-Key. **MCP6241T-E/OT** elsewhere: no distributor price read; JLC\'s $0.69 '
  'is used as a placeholder.')
P('2. **Samtec ESQ/TSW**: Mouser\'s prices as listed on Samtec\'s pages, not read on Mouser.')
P('3. **Parker 61-05-0909-G579 sheet: about $85, an estimate** between the -04 and -06 sheets\' Digi-Key prices. '
  'One sheet covers far more than 5 sets.')
P('4. **Essentra HTSN-M3-5-3 (about $0.60) and HNSM3-20-5.5-1 (about $0.80): estimates.** Essentra quotes on request, '
  'and Digi-Key\'s small-quantity prices were not readable.')
P('5. **Boyd 7721-7PPSG $0.26**: search-engine summary of Digi-Key/Allied.')
P('6. **TR washers and Wurth screws**: Farnell UK prices in GBP, converted at an assumed %.2f USD/GBP.' % GBP)
P('7. **JLC parts**: quantity-1 prices. JLC may apply a price break or a minimum purchase on some lines; attrition '
  'follows the "about 20 per small-passive line" read on 2026-09-24, and 0 on the other lines.')
P('8. **Stock moves daily.** The 2 LM2940S-12 and the 19 x 220 uF are exact or near-exact for A. Re-check stock '
  'the day you order.')
P('9. **The V-suffix Panasonic alternates** (EEH-ZU1H221V, EEH-ZU1E681UV): not used. Their land patterns are not '
  'checked.')
P('10. **Two links not opened**: the Wurth WA-SCRW page and the Bourns MF-R datasheet URL. The Adafruit 793 '
  'colour mix is not checked against the J9 wire colours.')
P('11. **JLC fees** (set-up, stencil, loading, joints) are from JLC\'s price page, not from a quote with the files '
  'uploaded. The PCB prices are from the quote page with dimensions entered, not with the gerbers uploaded. An upload '
  'can add engineering charges (for example for the via-in-pad count).')
P('')
P('Generated by `tools/cost_summary.py` from `bom/SOURCING_TABLE.csv` and `bom/jlc_snapshot_2026-09-24.json`; every '
  'number is also in `cost/cost_summary.json`.')

open(os.path.join(HERE, 'COST_SUMMARY.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
for s in (SA, SB, SB1):
    print('%-22s pcb %8.2f  asm %8.2f  elsewhere %7.2f  hw %7.2f  TOTAL %8.2f'
          % (s['name'], s['pcb'], s['assembly'], s['elsewhere'], s['hardware'], s['total']))
for o in (A_power, A_card, B2_power, B_card, B1_power):
    print('%-70s unique %2d joints %5d fees %7.2f parts %7.2f attr %5.2f asm %7.2f total %7.2f'
          % (o['label'], o['unique'], o['joints'], o['fees_usd'], o['parts'], o['attrition'], o['assembly_total'],
             o['total']))
