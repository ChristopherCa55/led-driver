"""BOOST_BOM.xlsx: the bill of materials as a spreadsheet (system Python, no extra packages), 2026-10-01.

usage: python tools/make_xlsx.py OUT.xlsx        (run from bom_2026-09-30/, after build_bom.py and cost_summary.py)

Sheets: Summary, Power board, Control card, Bought elsewhere, Fees, Ways to save.
Quantities, line costs and totals are Excel formulas, so editing a unit price or a quantity updates the totals.
Links are HYPERLINK() formulas.
"""
import csv, json, sys, zipfile, datetime
from xml.sax.saxutils import escape

rows = list(csv.DictReader(open('bom/SOURCING_TABLE.csv', encoding='utf-8')))
snap = json.load(open('bom/jlc_snapshot_2026-10-01.json', encoding='utf-8'))['res']
cand = snap
cost = json.load(open('cost/cost_summary.json', encoding='utf-8'))
N = 2


# ------------------------------------------------------------------ minimal xlsx writer
def col(n):
    s = ''
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


# style ids (see STYLES below)
S_TXT, S_HEAD, S_USD2, S_USD4, S_WRAP, S_LINK, S_BOLD, S_BUSD, S_TITLE, S_WARN, S_INT, S_NOTE = range(12)
STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="2"><numFmt numFmtId="164" formatCode="&quot;$&quot;#,##0.00"/><numFmt numFmtId="165" formatCode="&quot;$&quot;#,##0.0000"/></numFmts>
<fonts count="6">
<font><sz val="10"/><name val="Calibri"/></font>
<font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
<font><u/><sz val="10"/><color rgb="FF0563C1"/><name val="Calibri"/></font>
<font><b/><sz val="10"/><name val="Calibri"/></font>
<font><b/><sz val="14"/><name val="Calibri"/></font>
<font><b/><sz val="10"/><color rgb="FFC00000"/><name val="Calibri"/></font>
</fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF305496"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="12">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="164" fontId="3" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="0" fontId="5" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="1" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''


class Sheet:
    def __init__(self, name, widths, freeze=1, autofilter=None):
        self.name, self.widths, self.freeze, self.autofilter = name, widths, freeze, autofilter
        self.rows = []      # list of lists of (value, style) or None

    def add(self, *cells):
        self.rows.append(list(cells))
        return len(self.rows)          # 1-based row number

    def xml(self):
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
               'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">']
        if self.freeze:
            out.append('<sheetViews><sheetView workbookViewId="0"><pane ySplit="%d" topLeftCell="A%d" activePane="bottomLeft" '
                       'state="frozen"/></sheetView></sheetViews>' % (self.freeze, self.freeze + 1))
        out.append('<cols>' + ''.join('<col min="%d" max="%d" width="%.1f" customWidth="1"/>' % (i + 1, i + 1, w)
                                      for i, w in enumerate(self.widths)) + '</cols>')
        out.append('<sheetData>')
        for r, cells in enumerate(self.rows, 1):
            out.append('<row r="%d">' % r)
            for c, cell in enumerate(cells):
                if cell is None:
                    continue
                v, st = cell if isinstance(cell, tuple) else (cell, S_TXT)
                ref = '%s%d' % (col(c), r)
                if v is None or v == '':
                    out.append('<c r="%s" s="%d"/>' % (ref, st))
                elif isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.append('<c r="%s" s="%d"><v>%r</v></c>' % (ref, st, v))
                elif isinstance(v, str) and v.startswith('='):
                    out.append('<c r="%s" s="%d"><f>%s</f></c>' % (ref, st, escape(v[1:])))
                else:
                    out.append('<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                               % (ref, st, escape(str(v))))
            out.append('</row>')
        out.append('</sheetData>')
        if self.autofilter:
            out.append('<autoFilter ref="%s"/>' % self.autofilter)
        out.append('<pageSetup orientation="landscape"/></worksheet>')
        return '\n'.join(out)


def write(path, sheets):
    z = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)
    z.writestr('[Content_Types].xml',
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
               '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
               '<Default Extension="xml" ContentType="application/xml"/>'
               '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
               '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
               + ''.join('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-'
                         'officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1) for i in range(len(sheets)))
               + '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
               '</Types>')
    z.writestr('_rels/.rels',
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
               '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
               '</Relationships>')
    z.writestr('docProps/core.xml',
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
               'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>BOOST bill of materials</dc:title>'
               '<dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created></cp:coreProperties>'
               % datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    z.writestr('xl/workbook.xml',
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
               'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
               + ''.join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(s.name), i + 1, i + 1)
                         for i, s in enumerate(sheets))
               + '</sheets>'
               + '<calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')
    z.writestr('xl/_rels/workbook.xml.rels',
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               + ''.join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
                         'worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1) for i in range(len(sheets)))
               + '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                 'Target="styles.xml"/></Relationships>' % (len(sheets) + 1))
    z.writestr('xl/styles.xml', STYLES)
    for i, s in enumerate(sheets):
        z.writestr('xl/worksheets/sheet%d.xml' % (i + 1), s.xml())
    z.close()


def link(url, label):
    if not url:
        return ('', S_TXT)
    return ('=HYPERLINK("%s","%s")' % (url.replace('"', '%22'), label), S_LINK)


# ------------------------------------------------------------------ BOM sheets
HEAD = ['#', 'Designators', 'Qty / board', 'Qty to order (%d boards + attrition)' % N, 'Description',
        'Manufacturer', 'Part number (MPN)', 'LCSC #', 'Basic / Extended', 'Unit price (USD, qty 1)',
        'Line cost (USD)', 'JLC stock 2026-10-01', 'Footprint', 'Side', 'Fitted by', 'JLC page', 'LCSC page',
        'Datasheet', 'Value (schematic)', 'Specs (JLC listing)', 'Notes']
WID = [4, 26, 7, 10, 34, 18, 22, 11, 10, 11, 11, 10, 16, 8, 11, 8, 8, 9, 16, 40, 60]
ELSE_PRICE = {'J10': ('Samtec', 'ESQ-115-44-G-D', 9.13, 'https://www.samtec.com/products/esq-115-44-g-d',
                      'Mouser price as listed on samtec.com (2026-09-25); bought by you, fitted by you'),
              'J11': ('Samtec', 'TSW-115-07-G-D', 3.18, 'https://www.samtec.com/products/tsw-115-07-g-d',
                      'Mouser price as listed on samtec.com (2026-09-25); bought by you, fitted by you'),
              'L1': ('Codaca', 'CSCF3218-6R8MC', None, '', 'you own it; not priced'),
              'M1': ('HUAYI (HYG)', 'HYG180N10LS1P', None, '', 'you own ten; not priced')}


def bom_sheet(board, name):
    sh = Sheet(name, WID, freeze=1)
    sh.add(*[(h, S_HEAD) for h in HEAD])
    lines = {l['refs']: l for l in cost[board]['lines']}   # by refs: a part number can sit on two lines
    first, k = None, 0
    for r in rows:
        if r['board'] != board or r['list'] == 'NONE':
            continue
        k += 1
        s = snap.get(r['lcsc']) if r['lcsc'] else None
        refs = r['refs']
        n = int(r['qty'])
        notes = r['why'] + ((' Alternates: ' + r['alternates']) if r['alternates'] else '')
        rr = len(sh.rows) + 1
        if r['list'] == 'JLC':
            attr = lines[r['refs']]['attr'] if r['refs'] in lines else 0
            short = s['stock'] < n * N if s else False
            row = [(k, S_INT), (refs, S_WRAP), (n, S_INT), ('=C%d*%d+%d' % (rr, N, attr), S_INT),
                   (r['description'], S_WRAP), s['brand'], s['model'], r['lcsc'], r['type'], (s['p1'], S_USD4),
                   ('=D%d*J%d' % (rr, rr), S_USD2), (s['stock'], S_INT), r['footprint'], r['side'], 'JLC',
                   link(s['url'], 'JLC'), link(s.get('lcsc_url'), 'LCSC'), link(s.get('ds'), 'PDF'), r['value'],
                   (s['desc'], S_WRAP),
                   ((('SHORT: %d in stock for %d needed. ' % (s['stock'], n * N)) if short else '') + notes,
                    S_WARN if short else S_NOTE)]
        else:
            key = 'M1' if refs.startswith('M1') else refs.split()[0]
            maker, mpn, price, url, why = ELSE_PRICE.get(key, ('', r['value'], None, '', ''))
            row = [(k, S_INT), (refs, S_WRAP), (n, S_INT), ('=C%d*%d' % (rr, N), S_INT), (r['description'], S_WRAP),
                   maker, mpn, '', '', (price, S_USD4) if price else '', ('=D%d*J%d' % (rr, rr), S_USD2) if price else '',
                   '', r['footprint'], r['side'], 'you (hand)', link(url, 'Maker'), '', '', r['value'], '',
                   (why + '. ' + notes, S_NOTE)]
        sh.add(*row)
        first = first or rr
    last = len(sh.rows)
    sh.add()
    tot = sh.add('', ('Parts total (JLC lines, %d boards + attrition)' % N, S_BOLD), '', '', '', '', '', '', '', '',
                 ('=SUMIFS(K%d:K%d,O%d:O%d,"JLC")' % (first, last, first, last), S_BUSD))
    sh.add('', ('Parts you buy or own (priced lines)', S_BOLD), '', '', '', '', '', '', '', '',
           ('=SUMIFS(K%d:K%d,O%d:O%d,"you (hand)")' % (first, last, first, last), S_BUSD))
    sh.add('', ('Unique JLC part numbers (feeder loading $1.53 each)', S_BOLD), '', '', '', '', '', '', '', '',
           (cost[board]['unique'], S_INT))
    sh.autofilter = 'A1:U%d' % last
    return sh, first, last, tot


pw, pf, pl, ptot = bom_sheet('power', 'Power board')
cd, cf, cl, ctot = bom_sheet('card', 'Control card')

# ------------------------------------------------------------------ bought elsewhere
el = Sheet('Bought elsewhere', [48, 38, 8, 11, 11, 30, 26, 12, 50], freeze=1)
el.add(*[(h, S_HEAD) for h in ('Item', 'Role', 'Qty', 'Unit (USD)', 'Cost (USD)', 'Vendor / source', 'Checked',
                               'Link', 'Notes')])
e_first = len(el.rows) + 1
for it, q, u, src, ok in cost['elsewhere']:
    rr = len(el.rows) + 1
    url = ('https://www.lcsc.com/product-detail/C208476.html' if 'C208476' in it else
           'https://www.samtec.com/products/esq-115-44-g-d' if 'ESQ' in it else
           'https://www.samtec.com/products/tsw-115-07-g-d')
    el.add((it, S_WRAP), ('J10 / J11 board-to-board connector' if 'Samtec' in it else 'J9 pin-9 fuse (inline)', S_WRAP),
           (q, S_INT), (u, S_USD4), ('=C%d*D%d' % (rr, rr), S_USD2), (src, S_WRAP), (ok, S_WRAP), link(url, 'link'), '')
for it, role, q, usd, src, ok, url in cost['hardware']:
    el.add((it, S_WRAP), (role, S_WRAP), q, '', (usd, S_USD2), (src, S_WRAP), (ok, S_WRAP), link(url, 'link'),
           ('GBP price converted at 1.34 USD/GBP' if 'GBP' in src or 'Farnell' in src else '', S_NOTE))
pad = cost['pads'][0]
pr = el.add((pad[0], S_WRAP), ('FET thermal pads (cut 10 x 16 mm, 20 pads)', S_WRAP), '1', '', (pad[1], S_USD2),
            'mcmaster.com', 'read 2026-09-25', link('https://www.mcmaster.com/1272N32/', 'link'),
            ('Default pad. Alternatives: Parker G579 $128.75; t-Global TG-AD30 (price not read). See COST_SUMMARY.md',
             S_NOTE))
e_last = len(el.rows)
el.add()
etot = el.add(('Total bought elsewhere (with the McMaster pad)', S_BOLD), '', '', '',
              ('=SUM(E%d:E%d)' % (e_first, e_last), S_BUSD))
el.add(('Prices are the 2026-09-25 readings except the PTC (read 2026-09-30). Shipping and tax not included.', S_NOTE))

# ------------------------------------------------------------------ fees
fe = Sheet('Fees', [44, 14, 14, 60], freeze=1)
fe.add(*[(h, S_HEAD) for h in ('Item', 'Power board', 'Control card', 'Notes')])
PCBN = {'power': '6 layers, stackup JLC061611-7628D, 74 x 86 mm, 5 single boards, ENIG, 1 oz inner, TG155, filled & '
                 'capped vias',
        'card': '6 layers, 5 panels of one 45 x 45 mm card on a 70 x 70 mm carrier, ENIG, 0.5 oz inner, TG155'}
r_pcb = fe.add('Bare PCBs (5 of each), JLC quote 2026-10-01', (cost['power']['pcb'], S_USD2), (cost['card']['pcb'], S_USD2),
               ('Power: %s. Card: %s.' % (PCBN['power'], PCBN['card']), S_NOTE))
r_setup = fe.add('Assembly set-up (double-sided, Standard PCBA)', (cost['power']['fees']['setup'], S_USD2),
                 (cost['card']['fees']['setup'], S_USD2), ('JLC price page: $25.56 single-side, $51.12 double-side', S_NOTE))
r_sten = fe.add('Stencil (double-sided)', (cost['power']['fees']['stencil'], S_USD2), (cost['card']['fees']['stencil'], S_USD2),
                ('$8.21 single-side, $16.42 double-side', S_NOTE))
r_load = fe.add('Feeder loading ($1.53 per unique part)', ("='Power board'!K%d*1.53" % (ptot + 2), S_USD2),
                ("='Control card'!K%d*1.53" % (ctot + 2), S_USD2), ('Basic or Extended, Standard PCBA', S_NOTE))
r_joint = fe.add('Solder joints ($0.0016 each)', (cost['power']['fees']['joints'], S_USD2),
                 (cost['card']['fees']['joints'], S_USD2),
                 ('%d / %d joints for 2 boards' % (cost['power']['joints'], cost['card']['joints']), S_NOTE))
r_parts = fe.add('JLC parts (2 boards + attrition)', ("='Power board'!K%d" % ptot, S_USD2),
                 ("='Control card'!K%d" % ctot, S_USD2), ('from the board sheets', S_NOTE))
r_ord = fe.add(('Order total (PCBs + assembly)', S_BOLD), ('=SUM(B%d:B%d)' % (r_pcb, r_parts), S_BUSD),
               ('=SUM(C%d:C%d)' % (r_pcb, r_parts), S_BUSD), ('Shipping and tax not included', S_NOTE))

# ------------------------------------------------------------------ summary
su = Sheet('Summary', [52, 16, 70], freeze=0)
su.add(('BOOST LED driver: bill of materials and cost', S_TITLE))
su.add(('Scenario A: 5 bare PCBs of each board, 2 complete sets assembled by JLCPCB. Updated 2026-10-02: schematic rev6 '
        'plus D28-D30, 6-layer control card with 0.5 oz inner copper, the savings approved on 2026-10-01, and the 6-layer '
        'power board (2026-10-02, stackup JLC061611-7628D). JLC prices and stock read 2026-10-01.', S_NOTE))
su.add()
su.add(('Item', S_HEAD), ('Cost (USD)', S_HEAD), ('Notes', S_HEAD))
s1 = su.add('Power board: PCBs + JLC assembly', ("=Fees!B%d" % r_ord, S_USD2), 'JLC order 1')
su.add('Control card: PCBs + JLC assembly', ("=Fees!C%d" % r_ord, S_USD2), 'JLC order 2')
su.add('Bought elsewhere: J10/J11, PTC, hardware, McMaster thermal pad', ("='Bought elsewhere'!E%d" % etot, S_USD2),
       'Mouser, LCSC, McMaster-Carr, Digi-Key, Newark/Farnell')
s4 = su.add(('Total (shipping and tax not included)', S_BOLD), ('=SUM(B%d:B%d)' % (s1, s1 + 2), S_BUSD),
            ('COST_SUMMARY.md gives $%.2f' % [v for k, v in cost['totals'].items() if 'McMaster' in k][0], S_NOTE))
su.add()
_short = [l for b in ('power', 'card') for l in cost[b]['lines'] if snap[l['lcsc']]['stock'] < l['qty']]
su.add((('STOCK PROBLEM: ' + '; '.join('%s (%s): %d in stock, %d needed' % (l['mpn'], l['lcsc'], snap[l['lcsc']]['stock'],
                                                                         l['qty']) for l in _short)) if _short else
        'Stock (2026-10-01): every JLC line is in stock for 2 sets. Re-check on the day you order.',
        S_WARN if _short else S_NOTE))
su.add(('Not included: M1-M10, L1, the buck module and J9 wires (you own them); case, cabling, Arduino, LEDs; '
        'shipping and tax.', S_NOTE))
su.add(('Edit a unit price or a quantity on the board sheets and every total updates.', S_NOTE))

# ------------------------------------------------------------------ ways to save
ws = Sheet('Ways to save', [62, 12, 80, 26], freeze=1)
ws.add(*[(h, S_HEAD) for h in ('Option', 'Saves (USD, this build)', 'What it takes', 'Verdict')])
ns = dict(P_=cost['power'], C_=cost['card'], stock=snap, m=lambda x: '$%.2f' % x, N=N, HERE='.', PCB=None,
          CARD_SINGLE=None)
exec(open('tools/savings.py', encoding='utf-8').read(), ns)
ws.add(('Applied', S_BOLD))
for it, usd, note in ns['APPLIED']:
    ws.add((it.replace('**', ''), S_WRAP), (round(usd, 2), S_USD2), (note, S_WRAP), ('applied', S_WRAP))
ws.add()
ws.add(('Still open (your choice)', S_BOLD))
for it, usd, how, verdict in ns['OPEN']:
    ws.add((it.replace('**', ''), S_WRAP), (round(usd, 2), S_USD2) if usd else ('-' if usd is None else 'shipping'), (how, S_WRAP),
           (verdict.replace('**', ''), S_BOLD if 'Recommended' in verdict else S_WRAP))
ws.add()
ws.add(('Looked at, no good cheaper alternative (kept)', S_BOLD))
for x in ns['SAVINGS_MD']:
    if x.startswith('- '):
        ws.add((x[2:], S_WRAP))

write(sys.argv[1], [su, pw, cd, el, fe, ws])
print('wrote', sys.argv[1], '| power rows %d-%d, card rows %d-%d' % (pf, pl, cf, cl))
