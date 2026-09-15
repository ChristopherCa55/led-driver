"""Screw plan for a placement result (user rules, check-in 2 and 3).

  python pscrews.py RESULT.json CONFIG.json

Screwed FETs (config 'screwed') keep the TabUp footprint with its hole. Every other FET's body centre
must be within far_mm (config, 25 mm after check-in 3) of a screw point: a screwed FET's tab hole or a
card standoff (H5-H8, which screw through the power board into the case). Prints the distances, the
FETs that would need an extra screw, and the refs that get BOOST:TO-220-3_Horizontal_TabUp_NoHole.
Also flags screws that sit under the control card (reachable only if the board is screwed down before
the card is fitted).
"""
import sys, json, math
import pmodel as M

res = json.load(open(sys.argv[1]))
cfg = json.load(open(sys.argv[2]))
L = {k: tuple(v) for k, v in res['layout'].items()}
far = cfg.get('far_mm', 15.0)
screwed = list(cfg['screwed'])
pts = {m: M.tab_hole(L, m) for m in screwed}
for h in ('H5', 'H6', 'H7', 'H8'):
    if h in L:
        pts[h] = L[h][:2]
cx, cy = res['card']
cs = res.get('card_size', 42)
print('screw points:')
for n, (x, y) in pts.items():
    under = cx <= x <= cx + cs and cy <= y <= cy + cs and n in screwed      # standoffs are always fitted first
    print('   %-4s (%6.2f, %6.2f)%s' % (n, x, y, '  tab screw under the card: fit before the card' if under else ''))
need = []
print('unscrewed FETs, body centre to nearest screw point (limit %g mm):' % far)
for m in M.FETS:
    if m in screwed or m not in L:
        continue
    bx, by = M.body_centre(L, m)
    dn, near = min((math.hypot(bx - x, by - y), n) for n, (x, y) in pts.items())
    flag = 'ok' if dn <= far else 'NEEDS A SCREW'
    print('   %-4s %5.1f mm (nearest %s) %s' % (m, dn, near, flag))
    if dn > far:
        need.append(m)
nohole = [m for m in M.FETS if m in L and m not in screwed and m not in need]
print('extra screws needed: %s' % (need or 'none'))
print('NoHole footprint refs: %s' % ' '.join(nohole))
json.dump(dict(screwed=screwed + need, nohole=nohole), open(sys.argv[1].replace('.json', '.screws.json'), 'w'), indent=1)
