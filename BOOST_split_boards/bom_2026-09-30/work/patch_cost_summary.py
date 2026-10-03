"""One-off patch: turn the 2026-09-25 cost_summary.py into the 2026-10-01 version (run from bom_2026-09-30/)."""
s = open('tools/cost_summary.py', encoding='utf-8').read()
n_ok = 0


def rep(a, b):
    global s, n_ok
    assert s.count(a) == 1, ('count', s.count(a), a[:90])
    s = s.replace(a, b)
    n_ok += 1


rep('"""Cost summary for the chosen build, scenario A (final, 2026-09-25).',
    '"""Cost summary for the chosen build, scenario A (updated 2026-10-01).\n\nCopied from fab_2026-09-24/tools/'
    'cost_summary.py. Changes: the 6-layer control card (quote 2026-10-01), D28-D30,\nstock and JLC prices from '
    'bom/jlc_snapshot_2026-09-30.json, the 220 uF shortage, and a "Ways to save" section.')
rep("bom/jlc_stock_2026-09-25.json (stock and quantity-1 prices read 2026-09-25), and writes",
    "bom/jlc_snapshot_2026-09-30.json (stock and quantity-1 prices read 2026-09-30, 23:55 PDT), and writes")
rep("stock = json.load(open(os.path.join(BOM, 'jlc_stock_2026-09-25.json'), encoding='utf-8'))['res']",
    "stock = json.load(open(os.path.join(BOM, 'jlc_snapshot_2026-09-30.json'), encoding='utf-8'))['res']")
rep("""PCB = {  # 5 boards, 8 layers, 1.6 mm, ENIG, 1 oz / 1 oz, epoxy filled & capped vias, 10-11 day build (2026-09-24)
    'power': dict(usd=124.10, what='5 single boards, 74 x 86 mm',
                  detail='$90.00 base, $17.30 ENIG, $16.80 1 oz inner, $0.00 via covering'),
    'card': dict(usd=137.04, what='5 panels: one 45 x 45 mm card on a 70 x 70 mm carrier (12.5 mm rails, four sides, V-cut)',
                 detail='$99.00 engineering, $17.20 ENIG, $16.74 1 oz inner, $4.10 board, $0.00 via covering'),
}
CARD_SINGLE = 123.42""",
    """PCB = {  # 5 boards, 1.6 mm, ENIG, 1 oz / 1 oz, epoxy filled & capped vias (JLC quote page, 2026-10-01)
    'power': dict(usd=124.10, what='8 layers: 5 single boards, 74 x 86 mm', layers=8,
                  detail='$90.00 special offer, $17.30 ENIG, $16.80 1 oz inner, $0.00 via covering (10-11 day build)'),
    'card': dict(usd=73.57, layers=6,
                 what='6 layers: 5 panels, one 45 x 45 mm card on a 70 x 70 mm carrier (12.5 mm rails, four sides, V-cut)',
                 detail='$33.00 engineering, $17.20 ENIG, $3.43 TG155, $16.74 1 oz inner, $3.20 board, $0.00 via '
                        'covering (8-9 day build)'),
}
CARD_SINGLE = 68.78        # 5 single 45 x 45 mm 6-layer cards, same options
CARD_8L_PANEL = 137.04     # the 8-layer card panel, 2026-09-24""")
rep("LIMITED = {'C6843593', 'C29664285', 'C49889', 'C2877347'}",
    "LIMITED = {'C6843593', 'C29664285', 'C49889', 'C2877347', 'C4979367'}")
rep("""    ('Bourns MF-R050 PTC, 0.50 A hold (inline on the J9 pin-9 wire), LCSC C208476', N, 0.1431,
     'LCSC (its own order; JLC does not ship loose parts)', 'read 2026-09-25 (7,362 in stock); derating from the Bourns MF-R datasheet'),""",
    """    ('Bourns MF-R050 PTC, 0.50 A hold (inline on the J9 pin-9 wire), LCSC C208476', N, 0.1433,
     'LCSC (its own order; JLC does not ship loose parts)', 'read 2026-09-30 (7,030 in stock); derating from the Bourns MF-R datasheet'),""")
rep("FIRST_A = 803.86   # 2026-09-25 first scenario-A figure",
    "PREV_TOTAL = 760.83   # 2026-09-25 total with the McMaster pad\nexec(open(os.path.join(HERE, 'tools', 'savings.py'), encoding='utf-8').read())")
rep("P('# BOOST: cost summary, scenario A (final, 2026-09-25)')", "P('# BOOST: cost summary, scenario A (updated 2026-10-01)')")
rep("P('The BOM is schematic **rev6**: R1 = Bourns CSS4J-4026R-1L00F (1 mOhm), U25 = INA241A4.')",
    "P('The BOM is schematic **rev6** (R1 = Bourns CSS4J-4026R-1L00F, U25 = INA241A4) **plus the pre-charge diodes '\n"
    "  'D28-D30 (S2MW)**, with the **6-layer control card**.')\nP('')\nfor x in SHORT_NOTE:\n    P(x)")
rep("""P('Against the first scenario-A figure (%s, which carried an estimated $85 pad):' % m(FIRST_A))
P('- your Digi-Key prices for the HNSM3 standoff and the Boyd washer;')
P('- the Essentra HTSN stud (bulk only) replaced by a McMaster set screw and aluminium spacer;')
P('- the PTC changed to MF-R050.')
P('')
P('Every line is now a read price, except two: the TR washers and the Wurth screws, which are Farnell UK prices '
  'converted from GBP.')""",
    """P('Against the 2026-09-25 total (%s with the McMaster pad):' % m(PREV_TOTAL))
P('- the control card went from 8 to 6 layers: %s -> %s for 5 panels;' % (m(CARD_8L_PANEL), m(PCB['card']['usd'])))
P('- D28-D30 (S2MW, LCSC C128729) were added to the power board: 3 parts, one more unique part to load;')
P('- every JLC part price and stock figure was read again on 2026-09-30.')
P('')
P('The JLC lines and the PTC were read on 2026-09-30 / 2026-10-01. The Samtec, McMaster, Digi-Key and Farnell '
  'prices are the 2026-09-25 readings, not read again. The TR washers and the Wurth screws are Farnell UK prices '
  'converted from GBP.')
P('')
for x in SAVINGS_MD:
    P(x)""")
rep("P('## Bare PCBs (JLCPCB quote page, 2026-09-24)')", "P('## Bare PCBs (JLCPCB quote page, 2026-10-01)')")
rep("""P('Both boards: 8 layers, 1.6 mm, FR4 TG155, ENIG, 1 oz outer / 1 oz inner, **Epoxy Filled & Capped vias ($0.00 at '
  '8 layers)**, min via 0.3 mm, Remove Mark, flying-probe full test, 10-11 day build.')""",
    """P('Both boards: 1.6 mm, FR4 TG155, ENIG, 1 oz outer / 1 oz inner, **Epoxy Filled & Capped vias ($0.00 at 6 and '
  '8 layers)**, min via 0.3 mm, Remove Mark, flying-probe full test. The power board is 8 layers, the card 6 '
  '(JLC stackup JLC061611-7628, 1.609 mm).')""")
rep("""  'handles 2/4/6 layers, single-sided boards only. The panel costs %s more than 5 single cards (%s).'""",
    """  'handles single-sided boards only (the card has parts on both sides). The panel costs %s more than 5 single '
  'cards (%s).'""")
rep("""  'solder joint (JLC price page). Parts: JLC quantity-1 prices read 2026-09-25, plus about %d attrition spares per '""",
    """  'solder joint (JLC price page, read 2026-10-01). Parts: JLC quantity-1 prices read 2026-09-30, plus about %d '
  'attrition spares per '""")
# stock section
a = s.index("P('## Stock on 2026-09-25 (JLC parts library, 00:15 PDT)')")
b = s.index("P('## Itemised JLC parts")
s = s[:a] + "for x in STOCK_MD:\n    P(x)\n" + s[b:]
n_ok += 1
rep("P('5. The Wurth WA-SCRW page link was not opened.')",
    "P('5. The Wurth WA-SCRW page link was not opened.')\n"
    "P('6. The Samtec, McMaster, Digi-Key and Farnell prices were not read again after 2026-09-25.')")
rep("P('Generated by `tools/cost_summary.py`; every number is also in `cost/cost_summary.json`.')",
    "P('Generated by `BOOST_split_boards/bom_2026-09-30/tools/cost_summary.py`; every number is also in '\n"
    "  '`cost/cost_summary.json` there.')")
open('tools/cost_summary.py', 'w', encoding='utf-8').write(s)
print('replacements', n_ok)
