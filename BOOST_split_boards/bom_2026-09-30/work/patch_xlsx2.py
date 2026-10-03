"""One-off patch (2026-10-01): make_xlsx.py gets the short Description column, the 2026-10-01 snapshot, prices from
cost_summary.json, and the new Ways-to-save structure. Run from bom_2026-09-30/."""
p = 'tools/make_xlsx.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)


rep("snap = json.load(open('bom/jlc_snapshot_2026-09-30.json', encoding='utf-8'))['res']\n"
    "cand = json.load(open('bom/jlc_candidates_2026-10-01.json', encoding='utf-8'))['res']",
    "snap = json.load(open('bom/jlc_snapshot_2026-10-01.json', encoding='utf-8'))['res']\ncand = snap")
rep("""HEAD = ['#', 'Designators', 'Qty / board', 'Qty to order (%d boards + attrition)' % N, 'Value', 'Description',
        'Manufacturer', 'Part number (MPN)', 'LCSC #', 'Basic / Extended', 'Unit price (USD, qty 1)',
        'Line cost (USD)', 'JLC stock 2026-09-30', 'Footprint', 'Side', 'Fitted by', 'JLC page', 'LCSC page',
        'Datasheet', 'Notes']
WID = [4, 26, 7, 10, 18, 40, 18, 22, 11, 10, 11, 11, 10, 16, 8, 14, 10, 10, 10, 60]""",
    """HEAD = ['#', 'Designators', 'Qty / board', 'Qty to order (%d boards + attrition)' % N, 'Description',
        'Manufacturer', 'Part number (MPN)', 'LCSC #', 'Basic / Extended', 'Unit price (USD, qty 1)',
        'Line cost (USD)', 'JLC stock 2026-10-01', 'Footprint', 'Side', 'Fitted by', 'JLC page', 'LCSC page',
        'Datasheet', 'Value (schematic)', 'Specs (JLC listing)', 'Notes']
WID = [4, 26, 7, 10, 34, 18, 22, 11, 10, 11, 11, 10, 16, 8, 11, 8, 8, 9, 16, 40, 60]""")
rep("""            row = [(k, S_INT), (refs, S_WRAP), (n, S_INT), ('=C%d*%d+%d' % (rr, N, attr), S_INT), r['value'],
                   (s['desc'], S_WRAP), s['brand'], s['model'], r['lcsc'], r['type'], (s['p1'], S_USD4),
                   ('=D%d*K%d' % (rr, rr), S_USD2), (s['stock'], S_INT), r['footprint'], r['side'], 'JLC',
                   link(s['url'], 'JLC'), link(s.get('lcsc_url'), 'LCSC'), link(s.get('ds'), 'PDF'),
                   ((('SHORT: %d in stock for %d needed. ' % (s['stock'], n * N)) if short else '') + notes,
                    S_WARN if short else S_NOTE)]""",
    """            row = [(k, S_INT), (refs, S_WRAP), (n, S_INT), ('=C%d*%d+%d' % (rr, N, attr), S_INT),
                   (r['description'], S_WRAP), s['brand'], s['model'], r['lcsc'], r['type'], (s['p1'], S_USD4),
                   ('=D%d*J%d' % (rr, rr), S_USD2), (s['stock'], S_INT), r['footprint'], r['side'], 'JLC',
                   link(s['url'], 'JLC'), link(s.get('lcsc_url'), 'LCSC'), link(s.get('ds'), 'PDF'), r['value'],
                   (s['desc'], S_WRAP),
                   ((('SHORT: %d in stock for %d needed. ' % (s['stock'], n * N)) if short else '') + notes,
                    S_WARN if short else S_NOTE)]""")
rep("""            row = [(k, S_INT), (refs, S_WRAP), (n, S_INT), ('=C%d*%d' % (rr, N), S_INT), r['value'], '', maker, mpn,
                   '', '', (price, S_USD4) if price else '', ('=D%d*K%d' % (rr, rr), S_USD2) if price else '',
                   '', r['footprint'], r['side'], 'you (hand)', link(url, 'Maker'), '', '', (why + '. ' + notes, S_NOTE)]""",
    """            row = [(k, S_INT), (refs, S_WRAP), (n, S_INT), ('=C%d*%d' % (rr, N), S_INT), (r['description'], S_WRAP),
                   maker, mpn, '', '', (price, S_USD4) if price else '', ('=D%d*J%d' % (rr, rr), S_USD2) if price else '',
                   '', r['footprint'], r['side'], 'you (hand)', link(url, 'Maker'), '', '', r['value'], '',
                   (why + '. ' + notes, S_NOTE)]""")
rep("""    tot = sh.add('', ('Parts total (JLC lines, %d boards + attrition)' % N, S_BOLD), '', '', '', '', '', '', '', '', '',
                 ('=SUMIFS(L%d:L%d,P%d:P%d,"JLC")' % (first, last, first, last), S_BUSD))
    sh.add('', ('Parts you buy or own (priced lines)', S_BOLD), '', '', '', '', '', '', '', '', '',
           ('=SUMIFS(L%d:L%d,P%d:P%d,"you (hand)")' % (first, last, first, last), S_BUSD))
    sh.add('', ('Unique JLC part numbers (feeder loading $1.53 each)', S_BOLD), '', '', '', '', '', '', '', '', '',
           (cost[board]['unique'], S_INT))
    sh.autofilter = 'A1:T%d' % last""",
    """    tot = sh.add('', ('Parts total (JLC lines, %d boards + attrition)' % N, S_BOLD), '', '', '', '', '', '', '', '',
                 ('=SUMIFS(K%d:K%d,O%d:O%d,"JLC")' % (first, last, first, last), S_BUSD))
    sh.add('', ('Parts you buy or own (priced lines)', S_BOLD), '', '', '', '', '', '', '', '',
           ('=SUMIFS(K%d:K%d,O%d:O%d,"you (hand)")' % (first, last, first, last), S_BUSD))
    sh.add('', ('Unique JLC part numbers (feeder loading $1.53 each)', S_BOLD), '', '', '', '', '', '', '', '',
           (cost[board]['unique'], S_INT))
    sh.autofilter = 'A1:U%d' % last""")
rep("""PCBN = {'power': '8 layers, 74 x 86 mm, 5 single boards, ENIG, 1 oz inner, TG155, filled & capped vias',
        'card': '6 layers, 5 panels of one 45 x 45 mm card on a 70 x 70 mm carrier, ENIG, 1 oz inner, TG155'}
r_pcb = fe.add('Bare PCBs (5 of each), JLC quote 2026-10-01', (124.10, S_USD2), (73.57, S_USD2),""",
    """PCBN = {'power': '8 layers, 74 x 86 mm, 5 single boards, ENIG, 1 oz inner, TG155, filled & capped vias',
        'card': '6 layers, 5 panels of one 45 x 45 mm card on a 70 x 70 mm carrier, ENIG, 0.5 oz inner, TG155'}
r_pcb = fe.add('Bare PCBs (5 of each), JLC quote 2026-10-01', (cost['power']['pcb'], S_USD2), (cost['card']['pcb'], S_USD2),""")
rep("""r_load = fe.add('Feeder loading ($1.53 per unique part)', ("='Power board'!L%d*1.53" % (ptot + 2), S_USD2),
                ("='Control card'!L%d*1.53" % (ctot + 2), S_USD2), ('Basic or Extended, Standard PCBA', S_NOTE))""",
    """r_load = fe.add('Feeder loading ($1.53 per unique part)', ("='Power board'!K%d*1.53" % (ptot + 2), S_USD2),
                ("='Control card'!K%d*1.53" % (ctot + 2), S_USD2), ('Basic or Extended, Standard PCBA', S_NOTE))""")
rep("""r_parts = fe.add('JLC parts (2 boards + attrition)', ("='Power board'!L%d" % ptot, S_USD2),
                 ("='Control card'!L%d" % ctot, S_USD2), ('from the board sheets', S_NOTE))""",
    """r_parts = fe.add('JLC parts (2 boards + attrition)', ("='Power board'!K%d" % ptot, S_USD2),
                 ("='Control card'!K%d" % ctot, S_USD2), ('from the board sheets', S_NOTE))""")
rep("""        'plus D28-D30, 6-layer control card. JLC prices and stock read 2026-09-30.', S_NOTE))""",
    """        'plus D28-D30, 6-layer control card with 0.5 oz inner copper, and the savings approved on 2026-10-01. JLC '
        'prices and stock read 2026-10-01.', S_NOTE))""")
rep("""            ('COST_SUMMARY.md gives $699.68', S_NOTE))
su.add()
su.add(('STOCK PROBLEM: EEH-ZU1H221P (C6843593), the 220 uF output cap, has 14 in stock; two power boards need 18. '
        'See the "Ways to save" sheet, item 1, or ORDER_CHECKLIST.md.', S_WARN))""",
    """            ('COST_SUMMARY.md gives $%.2f' % [v for k, v in cost['totals'].items() if 'McMaster' in k][0], S_NOTE))
su.add()
_short = [l for b in ('power', 'card') for l in cost[b]['lines'] if snap[l['lcsc']]['stock'] < l['qty']]
su.add((('STOCK PROBLEM: ' + '; '.join('%s (%s): %d in stock, %d needed' % (l['mpn'], l['lcsc'], snap[l['lcsc']]['stock'],
                                                                         l['qty']) for l in _short)) if _short else
        'Stock (2026-10-01): every JLC line is in stock for 2 sets. Re-check on the day you order.',
        S_WARN if _short else S_NOTE))""")
a = s.index("exec(open('tools/savings.py', encoding='utf-8').read().split('SAVINGS_MD = [')[0]")
b = s.index("write(sys.argv[1], [su, pw, cd, el, fe, ws])")
s = s[:a] + """ns = dict(P_=cost['power'], C_=cost['card'], stock=snap, m=lambda x: '$%.2f' % x, N=N, HERE='.', PCB=None,
          CARD_SINGLE=None)
exec(open('tools/savings.py', encoding='utf-8').read(), ns)
ws.add(('Applied', S_BOLD))
for it, usd, note in ns['APPLIED']:
    ws.add((it.replace('**', ''), S_WRAP), (round(usd, 2), S_USD2), (note, S_WRAP), ('applied', S_WRAP))
ws.add()
ws.add(('Still open (your choice)', S_BOLD))
for it, usd, how, verdict in ns['OPEN']:
    ws.add((it.replace('**', ''), S_WRAP), (round(usd, 2), S_USD2) if usd else 'shipping', (how, S_WRAP),
           (verdict.replace('**', ''), S_BOLD if 'Recommended' in verdict else S_WRAP))
ws.add()
ws.add(('Looked at, no good cheaper alternative (kept)', S_BOLD))
for x in ns['SAVINGS_MD']:
    if x.startswith('- '):
        ws.add((x[2:], S_WRAP))

""" + s[b:]
open(p, 'w', encoding='utf-8').write(s)
print('patched')
