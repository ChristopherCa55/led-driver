"""JLCPCB parts library lookups (system Python), 2026-09-30. Uses the public search call the jlcpcb.com/parts page
makes; no sign-in.

  python tools/jlc_parts.py snapshot OUT.json CODE [CODE ...]   exact LCSC codes -> stock, price tiers, links
  python tools/jlc_parts.py search OUT.json "KEYWORD" [PAGES]     keyword search -> every hit with its attributes
"""
import json, sys, time, urllib.request

API = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList/v2'


def query(keyword, page=1, size=50):
    body = dict(keyword=keyword, currentPage=page, pageSize=size, searchSource='search', componentAttributes=[],
                stockFlag=False, presaleType='')
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={
        'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0', 'Origin': 'https://jlcpcb.com',
        'Referer': 'https://jlcpcb.com/parts'})
    for attempt in range(3):
        try:
            j = json.loads(urllib.request.urlopen(req, timeout=30).read())
            return ((j.get('data') or {}).get('componentPageInfo') or {}).get('list') or []
        except Exception as e:      # noqa: retry transient errors
            err = e
            time.sleep(2)
    raise err


def row(x):
    attrs = {a['attribute_name_en']: a['attribute_value_name'] for a in (x.get('attributes') or [])}
    prices = [[p['startNumber'], p['productPrice']] for p in (x.get('componentPrices') or [])]
    return dict(code=x['componentCode'], model=x.get('componentModelEn'), brand=x.get('componentBrandEn'),
                stock=x.get('stockCount'), type=x.get('componentLibraryType'), pref=bool(x.get('preferredComponentFlag')),
                pkg=x.get('componentSpecificationEn'), prices=prices, p1=prices[0][1] if prices else None,
                desc=x.get('describe'), cat=x.get('firstSortName'), attrs=attrs, ds=x.get('dataManualUrl'),
                url='https://jlcpcb.com/partdetail/' + (x.get('urlSuffix') or ''), lcsc_url=x.get('lcscGoodsUrl'))


if __name__ == '__main__':
    mode, out = sys.argv[1], sys.argv[2]
    res = {}
    if mode == 'snapshot':
        for code in sys.argv[3:]:
            hit = [x for x in query(code, size=10) if x['componentCode'] == code]
            res[code] = row(hit[0]) if hit else None
            print(code, (res[code]['model'], res[code]['stock'], res[code]['p1']) if hit else 'NOT FOUND')
    else:
        kw = sys.argv[3]
        pages = int(sys.argv[4]) if len(sys.argv) > 4 else 2
        for p in range(1, pages + 1):
            lst = query(kw, page=p)
            for x in lst:
                res[x['componentCode']] = row(x)
            if len(lst) < 50:
                break
        print('%d hits for %r' % (len(res), kw))
    json.dump(dict(_source='JLCPCB parts library search API, read %s' % time.strftime('%Y-%m-%d %H:%M %Z'), res=res),
              open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
