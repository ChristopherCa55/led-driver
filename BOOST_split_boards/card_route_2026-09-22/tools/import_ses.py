"""Import a Freerouting session into a pre-routed board, keep the pre-routes exact, refill, save (KiCad Python).

usage: python.exe import_ses.py PRE.kicad_pcb IN.ses OUT.kicad_pcb REPORT.json [IN.dsn] [--fixed=PRE_ROUTES.json]

--fixed: a finishing run (make_dsn.py --lock-only): only PRE's items listed in PRE_ROUTES.json were fixed in the DSN,
so only they (and the sensitive nets) are put back; the rest of PRE's wiring comes back through the session.

KiCad's SES import replaces every track and via on the board with the session's wiring, and Freerouting 2.4.1
leaves the fixed (pre-routed) wiring out of the session. So the pre-routes are recorded first and put back after the
import (1 um tolerance):
- the sensitive nets (Current, U2 In+, V_err): whatever the session holds for them is removed and their copper is
  put back exactly as it was on PRE (user, 2026-09-23: "If Freerouting moved any of them, restore them"); the report
  says how many session items that removed, and the final check compares the nets item by item with PRE;
- every other pre-routed item (other comparator inputs, stitching, decoupling links, fan-outs) is added back unless
  the session already holds it;
- with IN.dsn, the nets of its class 'done' (complete before Freerouting) lose whatever the session added to them too:
  Freerouting 2.4.1 ignores -inc and draws pad-centre stubs to pre-routed track ends it does not count as connected.
Vias: GND vias keep every layer's annulus (stitching), the others drop unused inner annuli, as add_routes.py does.
"""
import json, re, sys, collections
import pcbnew


args = [x for x in sys.argv[1:] if not x.startswith('--fixed=')]
FIXED = [x.split('=', 1)[1] for x in sys.argv[1:] if x.startswith('--fixed=')]
PRE, SES, OUT, REP = args[0:4]
SENS = ['Current', 'Net-(U2-In+)', 'V_err']
DONE = set()
if len(args) > 4:
    m = re.search(r'\n    \(class done (.*?)\n      \(circuit', open(args[4], encoding='utf8').read(), re.S)
    if m:
        DONE = {n.strip('"').replace('{slash}', '/') for n in re.findall(r'"[^"]*"|[^\s()]+', m.group(1))}
DROP = set(SENS) | DONE
TOL = 1000          # nm
KEEP = []


def rec(t, b):
    if t.GetClass() == 'PCB_VIA':
        return dict(kind='via', net=t.GetNetname(), x=t.GetPosition().x, y=t.GetPosition().y, w=t.GetWidth(pcbnew.F_Cu),
                    drill=t.GetDrillValue())
    p = sorted([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)])
    return dict(kind='track', net=t.GetNetname(), layer=b.GetLayerName(t.GetLayer()), x0=p[0][0], y0=p[0][1],
                x1=p[1][0], y1=p[1][1], w=t.GetWidth())


def key(r):
    q = lambda v: int(round(v / TOL))
    if r['kind'] == 'via':
        return ('via', r['net'], q(r['x']), q(r['y']), q(r['w']), q(r['drill']))
    return ('track', r['net'], r['layer'], q(r['x0']), q(r['y0']), q(r['x1']), q(r['y1']), q(r['w']))


b = pcbnew.LoadBoard(PRE)
before = [rec(t, b) for t in b.GetTracks()]
bkeys = collections.Counter(key(r) for r in before)
if FIXED:
    # finishing run (make_dsn.py --lock-only): only the pre-routes were fixed, so only they are missing from the
    # session; the rest of PRE's wiring went in as movable wiring and comes back through the session
    fx = json.load(open(FIXED[0]))
    FM = pcbnew.FromMM
    fk = collections.Counter()
    for t in fx['tracks']:
        e = sorted([(FM(t['x0']), FM(t['y0'])), (FM(t['x1']), FM(t['y1']))])
        fk[key(dict(kind='track', net=t['net'], layer=t['layer'], x0=e[0][0], y0=e[0][1], x1=e[1][0], y1=e[1][1],
                    w=FM(t['w'])))] += 1
    for v in fx['vias']:
        fk[key(dict(kind='via', net=v['net'], x=FM(v['x']), y=FM(v['y']), w=FM(v['dia']), drill=FM(v['drill'])))] += 1
    readd_set = [r for r in before if fk[key(r)] > 0 or r['net'] in SENS]
else:
    readd_set = before
# the pre-route fills would touch the new wiring and pull it onto their net: empty every zone first
for z in b.Zones():
    z.UnFill()
if not pcbnew.ImportSpecctraSES(b, SES):
    sys.exit('ImportSpecctraSES failed')
nets = {t.m_Uuid.AsString(): t.GetNetname() for t in b.GetTracks()}      # the session's nets
# Freerouting 2.4.1 necks tracks down at some pins to 0.12 mm even with automatic neck-down off: raise any session
# track under the board minimum (0.13 mm) to it; DRC then checks the clearance as for any other track
MINW = pcbnew.FromMM(0.13)
narrow = 0
for t in b.GetTracks():
    if t.GetClass() != 'PCB_VIA' and t.GetWidth() < MINW:
        t.SetWidth(MINW)
        narrow += 1
after = [rec(t, b) for t in b.GetTracks()]
akeys = collections.Counter(key(r) for r in after)
report = dict(pre=PRE, ses=SES, out=OUT, pre_items=len(before), session_items=len(after),
              session_tracks_widened_to_0p13=narrow)
# 1. anything the session put on a sensitive net goes (Freerouting must not touch them)
sens_ses = collections.Counter()
for t in list(b.GetTracks()):
    if t.GetNetname() in DROP:
        sens_ses[t.GetNetname()] += 1
        b.Remove(t)
        KEEP.append(t)      # KiCad 10: a removed item's proxy must not be collected before the script ends
report['session_items_on_sensitive_nets_removed'] = {k: v for k, v in sens_ses.items() if k in SENS}
report['session_items_on_done_nets_removed'] = {k: v for k, v in sens_ses.items() if k in DONE}
# 2. put back every pre-routed item the import dropped (Freerouting leaves fixed wiring out of the session)
readd = collections.Counter()
dup = 0
for r in readd_set:
    if r['net'] not in DROP and akeys[key(r)] > 0:
        akeys[key(r)] -= 1
        dup += 1
        continue
    if r['kind'] == 'via':
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(r['x'], r['y']))
        v.SetWidth(r['w'])
        v.SetDrill(r['drill'])
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    else:
        v = pcbnew.PCB_TRACK(b)
        v.SetStart(pcbnew.VECTOR2I(r['x0'], r['y0']))
        v.SetEnd(pcbnew.VECTOR2I(r['x1'], r['y1']))
        v.SetWidth(r['w'])
        v.SetLayer(b.GetLayerID(r['layer']))
    v.SetNet(b.FindNet(r['net']))
    b.Add(v)
    KEEP.append(v)
    nets[v.m_Uuid.AsString()] = r['net']
    readd[r['net']] += 1
report['pre_items_readded'] = sum(readd.values())
report['pre_items_already_in_session'] = dup
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        n = nets.get(t.m_Uuid.AsString(), t.GetNetname())
        t.Padstack().SetUnconnectedLayerMode(pcbnew.UNCONNECTED_LAYER_MODE_KEEP_ALL if n == 'GND'
                                             else pcbnew.UNCONNECTED_LAYER_MODE_REMOVE_ALL)
# KiCad can move an item it sees joined only to other copper onto that copper's net: put every item back on the
# net the session (or the pre-route) gave it, refill, and repeat while anything moves; what still moves is reported
flips = []
for rnd in range(3):
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    moved = []
    for t in b.GetTracks():
        n0 = nets.get(t.m_Uuid.AsString())
        if n0 is not None and t.GetNetname() != n0:
            moved.append('round %d: %s at (%.3f, %.3f) %s -> %s' % (rnd, t.GetClass(), pcbnew.ToMM(t.GetPosition().x),
                                                                 pcbnew.ToMM(t.GetPosition().y), n0, t.GetNetname()))
            t.SetNet(b.FindNet(n0))
    flips += moved
    if not moved:
        break
report['net_flips'] = flips
report['net_flips_unsettled'] = bool(flips) and bool(moved)
# final check: every sensitive item of PRE is on OUT unchanged, and nothing else of those nets
fin = collections.Counter(key(rec(t, b)) for t in b.GetTracks() if t.GetNetname() in SENS)
pre_s = collections.Counter(key(r) for r in before if r['net'] in SENS)
report['sensitive_identical_to_pre'] = fin == pre_s
report['sensitive_items'] = sum(pre_s.values())
pcbnew.SaveBoard(OUT, b)
json.dump(report, open(REP, 'w'), indent=1)
print(json.dumps(report, indent=1))
