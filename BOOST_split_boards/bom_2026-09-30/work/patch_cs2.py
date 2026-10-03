s = open('tools/cost_summary.py', encoding='utf-8').read()
reps = [
 ("stock = json.load(open(os.path.join(BOM, 'jlc_snapshot_2026-09-30.json'), encoding='utf-8'))['res']",
  "stock = json.load(open(os.path.join(BOM, 'jlc_snapshot_2026-10-01.json'), encoding='utf-8'))['res']"),
 ("""    'card': dict(usd=73.57, layers=6,
                 what='6 layers: 5 panels, one 45 x 45 mm card on a 70 x 70 mm carrier (12.5 mm rails, four sides, V-cut)',
                 detail='$33.00 engineering, $17.20 ENIG, $3.43 TG155, $16.74 1 oz inner, $3.20 board, $0.00 via '
                        'covering (8-9 day build)'),
}
CARD_SINGLE = 68.78        # 5 single 45 x 45 mm 6-layer cards, same options""",
  """    'card': dict(usd=56.83, layers=6,
                 what='6 layers, 0.5 oz inner copper: 5 panels, one 45 x 45 mm card on a 70 x 70 mm carrier (12.5 mm '
                      'rails, four sides, V-cut)',
                 detail='$33.00 engineering, $17.20 ENIG, $3.43 TG155, $3.20 board, $0.00 via covering, 0.5 oz inner '
                        'at no charge (8-9 day build)'),
}
CARD_SINGLE = 52.16        # 5 single 45 x 45 mm 6-layer cards, same options (0.5 oz inner)"""),
 ("""P('- every JLC part price and stock figure was read again on 2026-09-30.')""",
  """P('- every JLC part price and stock figure was read again on 2026-10-01;')
P('- the savings you approved on 2026-10-01 are applied (see "Ways to save").')"""),
 ("""P('The JLC lines and the PTC were read on 2026-09-30 / 2026-10-01.""", """P('The JLC lines and the PTC were read on 2026-09-30 / 2026-10-01."""),
 ("""P('Both boards: 1.6 mm, FR4 TG155, ENIG, 1 oz outer / 1 oz inner, **Epoxy Filled & Capped vias ($0.00 at 6 and '
  '8 layers)**, min via 0.3 mm, Remove Mark, flying-probe full test. The power board is 8 layers, the card 6 '
  '(JLC stackup JLC061611-7628, 1.609 mm).')""",
  """P('Both boards: 1.6 mm, FR4 TG155, ENIG, 1 oz outer copper, **Epoxy Filled & Capped vias ($0.00 at 6 and '
  '8 layers)**, min via 0.3 mm, Remove Mark, flying-probe full test. The power board is 8 layers with 1 oz inner '
  'copper; the card is 6 layers with 0.5 oz inner copper (JLC\'s standard 6-layer 1 / 0.5 oz build, 1.547 mm).')"""),
]
for a, b in reps:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
s = s.replace("CARD_8L_PANEL = 137.04     # the 8-layer card panel, 2026-09-24",
              "CARD_8L_PANEL = 137.04     # the 8-layer card panel, 2026-09-24\nCARD_6L_1OZ = 73.57        # 6 layers, 1 oz inner, 2026-10-01")
s = s.replace("P('- the control card went from 8 to 6 layers: %s -> %s for 5 panels;' % (m(CARD_8L_PANEL), m(PCB['card']['usd'])))",
              "P('- the control card went from 8 to 6 layers, then to 0.5 oz inner copper: %s -> %s -> %s for 5 panels;' % (m(CARD_8L_PANEL), m(CARD_6L_1OZ), m(PCB['card']['usd'])))")
open('tools/cost_summary.py', 'w', encoding='utf-8').write(s)
print('ok')
