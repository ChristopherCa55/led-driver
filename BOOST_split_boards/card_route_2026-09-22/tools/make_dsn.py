"""Write a Specctra DSN of a pre-routed control-card board for Freerouting (KiCad Python).

usage: python.exe make_dsn.py BOARD.kicad_pcb OUT.dsn REPORT.json [DRC.json] [--lock-only=PRE_ROUTES.json] [--rails-in3]
                          [--open-plan]

--lock-only: a finishing run on a routed board; only the pre-routes are fixed, the rest is movable wiring.
--open-plan: the layer plan of 2026-09-24 (see below, at CLASSES).

With DRC.json, the signal nets the pre-route already completed go in class 'done' (Freerouting 2.4.1 ignores -inc, so
import_ses.py drops whatever the session adds to them).

Freerouting routes only what is still open; everything already on BOARD (the sensitive nets, the other comparator
inputs, stitching, decoupling links and plane fan-outs from route_card.py --pre) is exported locked, as (type fix).
Freerouting does not read the .kicad_dru, so the card's rules go into the DSN (user, 2026-09-23):
- layer plan (approved at check-in 2) as net classes with use_layer: logic F / In2 / B; analog F / In5 / B; the J11
  sense lines likewise with the Power class's 0.25 mm clearance; 12V and analog_5V F / In5 / B; GND and 5V
  reach their planes (In1 / In4 / In6, In3) through vias only;
- U2 In+ and Current: no via of another net within 2 mm of their copper (via keep-outs, every layer, 2 mm from the
  copper edge); Current: no other copper within 2 mm on B.Cu and In5 (wire keep-outs); U2 In+: its In5 run keeps
  2 mm of free band on In5 for the GND guard (wire keep-out); no logic net within 2 mm of U2 In+ or V_err on the
  layers where they have copper (class_class clearance 2 mm per layer; a logic via has pads there too);
- V_err: no via of another net within 0.3 mm of its copper, so the GND plane under it keeps no antipad (via keep-out);
- J9's tie slots: copper 0.3 mm from the slot (keep-outs); board edge 0.3 mm (keep-out strips inside the outline);
- one via for every net, 0.5 / 0.3 (drill >= 0.3 DRU rule), via-in-pad allowed (ROUTING_SPEC 2).
Every keep-out is the rule distance measured from the copper edge; Freerouting may add its own clearance on top,
which only tightens. GND fills on F / In2 / In5 / B are dropped from the DSN (KiCad refills them after the import);
the GND planes In1 / In4 / In6 and the 5 V plane In3 stay as DSN planes.
REPORT.json lists the keep-outs and every pad of an open net (DRC.json unconnected items) inside one.
"""
import json, re, sys
import pcbnew

sys.path.insert(0, 'tools')
from card_nets import ANALOG, RAILS, is_logic

RAILS_IN3 = '--rails-in3' in sys.argv
args = [x for x in sys.argv[1:] if not x.startswith('--lock-only=') and x not in ('--rails-in3', '--open-plan')]
LOCK_ONLY = [x.split('=', 1)[1] for x in sys.argv[1:] if x.startswith('--lock-only=')]
SRC, OUT, REP = args[0:3]
DRC = args[3] if len(args) > 3 else None
MM = pcbnew.FromMM
ERR = MM(0.005)
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu', 'B.Cu']
SENS = ['Current', 'Net-(U2-In+)', 'V_err']
VIA_ZONE = {'Current': 2.0, 'Net-(U2-In+)': 2.0, 'V_err': 0.3}
# (net, source layers, keep-out layers, distance): no wire of another net
WIRE_ZONE = [('Current', ['B.Cu', 'In5.Cu'], ['B.Cu', 'In5.Cu'], 2.0),
             ('Net-(U2-In+)', ['In5.Cu'], ['In5.Cu'], 2.0)]
LOGIC_CLR = {'Net-(U2-In+)': 2.0, 'V_err': 2.0}
NPTH_CLR = 0.3
EDGE_CLR = 0.3
SENSE = {'Vout_1', 'Vout_2', 'Vout_3', 'Output1_drain', 'Output2_drain', 'Output3_drain'}
VIA = 'Via[0-7]_500:300_um'
# class: (layers, width um, clearance um)
CLASSES = {
    'logic': (['F.Cu', 'In2.Cu', 'B.Cu'], 200, 200),
    'analog': (['F.Cu', 'In5.Cu', 'B.Cu'], 200, 200),
    'sense': (['F.Cu', 'In5.Cu', 'B.Cu'], 250, 250),
    # rails off In3 unless --rails-in3 (the approved plan allows In3, but a run with it cut the 5 V plane into islands)
    'rail12': (['F.Cu'] + (['In3.Cu'] if RAILS_IN3 else []) + ['In5.Cu', 'B.Cu'], 400, 200),
    'railA': (['F.Cu'] + (['In3.Cu'] if RAILS_IN3 else []) + ['In5.Cu', 'B.Cu'], 300, 200),
    'gnd': (['F.Cu', 'In2.Cu', 'In5.Cu', 'B.Cu'], 300, 250),
    'p5v': (['F.Cu', 'In3.Cu', 'B.Cu'], 300, 200),
    'sens_cur': (['B.Cu'], 250, 200),
    'sens_inp': (['F.Cu', 'In5.Cu', 'B.Cu'], 200, 200),
    'sens_verr': (['F.Cu', 'In5.Cu', 'B.Cu'], 200, 200),
    'nc': (['F.Cu', 'B.Cu'], 200, 200),
    'done': (['F.Cu', 'B.Cu'], 200, 200),     # nets the pre-route completed (with DRC.json): run with -inc done
}
# --open-plan (user, 2026-09-24): logic, analog, the sense lines and the rails share In2, In3, In4 and In5; GND stays
# off In3 (the 5 V pour); 5V is routed as tracks on In3 (its pour is left out of the DSN and fills round them after
# the import, so the pour stays one piece along them); In4 keeps other nets 2 mm off the U2 In+ run and the Current
# stub, so its GND fill stays solid over them
OPEN_PLAN = '--open-plan' in sys.argv
if OPEN_PLAN:
    ALL = ['F.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'B.Cu']
    for c in ('logic', 'analog', 'sense', 'rail12', 'railA'):
        CLASSES[c] = (ALL,) + CLASSES[c][1:]
    CLASSES['gnd'] = (['F.Cu', 'In2.Cu', 'In4.Cu', 'In5.Cu', 'B.Cu'],) + CLASSES['gnd'][1:]
    WIRE_ZONE = [('Current', ['B.Cu', 'In5.Cu'], ['B.Cu', 'In4.Cu', 'In5.Cu'], 2.0),
                 ('Net-(U2-In+)', ['In5.Cu'], ['In4.Cu', 'In5.Cu'], 2.0)]


def cls_of(net):
    if net.startswith('unconnected-'):
        return 'nc'
    if net == 'Current':
        return 'sens_cur'
    if net == 'Net-(U2-In+)':
        return 'sens_inp'
    if net == 'V_err':
        return 'sens_verr'
    if net == 'GND':
        return 'gnd'
    if net == '5V':
        return 'p5v'
    if net == '12V':
        return 'rail12'
    if net == 'analog_5V':
        return 'railA'
    if net in SENSE:
        return 'sense'
    if net in ANALOG:
        return 'analog'
    return 'logic'


b = pcbnew.LoadBoard(SRC)
LID = {n: b.GetLayerID(n) for n in CU}
TRACKS = list(b.GetTracks())
FPS = list(b.GetFootprints())
if LOCK_ONLY:
    # finishing run: only the pre-routes (route_card.py --pre output) are fixed; every other track and via goes in as
    # ordinary wiring that Freerouting may push, shove or rip up
    pre = json.load(open(LOCK_ONLY[0]))
    q = lambda v: round(v, 3)
    pk = set()
    for t in pre['tracks']:
        e = sorted([(q(t['x0']), q(t['y0'])), (q(t['x1']), q(t['y1']))])
        pk.add((t['net'], t['layer'], e[0], e[1]))
    pv = {(v['net'], q(v['x']), q(v['y'])) for v in pre['vias']}
    for t in TRACKS:
        n = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            k = (n, q(pcbnew.ToMM(t.GetPosition().x)), q(pcbnew.ToMM(t.GetPosition().y)))
            t.SetLocked(k in pv)
        else:
            e = sorted([(q(pcbnew.ToMM(t.GetStart().x)), q(pcbnew.ToMM(t.GetStart().y))),
                        (q(pcbnew.ToMM(t.GetEnd().x)), q(pcbnew.ToMM(t.GetEnd().y)))])
            t.SetLocked((n, b.GetLayerName(t.GetLayer()), e[0], e[1]) in pk)
    print('locked %d of %d items (the pre-routes)' % (sum(t.IsLocked() for t in TRACKS), len(TRACKS)))
else:
    for t in TRACKS:
        t.SetLocked(True)


def simplify(ps):
    try:
        ps.Simplify()
    except TypeError:
        ps.Simplify(pcbnew.SHAPE_POLY_SET.PM_FAST)


def copper(net, layers, clr):
    """Union of the net's copper on the given layers, grown by clr mm (outer approximation)."""
    ps = pcbnew.SHAPE_POLY_SET()
    for t in TRACKS:
        if t.GetNetname() != net:
            continue
        for ln in layers:
            if t.IsOnLayer(LID[ln]):
                t.TransformShapeToPolygon(ps, LID[ln], MM(clr), ERR, pcbnew.ERROR_OUTSIDE)
    for f in FPS:
        for p in f.Pads():
            if p.GetNetname() != net:
                continue
            for ln in layers:
                if p.IsOnLayer(LID[ln]) and p.FlashLayer(LID[ln]):
                    p.TransformShapeToPolygon(ps, LID[ln], MM(clr), ERR, pcbnew.ERROR_OUTSIDE)
    simplify(ps)
    return ps


def outlines(ps):
    """Outer outlines of a polygon set as point lists in mm; holes are filled (tighter than the rule)."""
    out, holes = [], 0
    for i in range(ps.OutlineCount()):
        ch = ps.Outline(i)
        out.append([(pcbnew.ToMM(ch.CPoint(k).x), pcbnew.ToMM(ch.CPoint(k).y)) for k in range(ch.PointCount())])
        holes += ps.HoleCount(i)
    return out, holes


def dsn_poly(kind, layer, pts):
    pts = list(pts) + [pts[0]]
    s = ' '.join('%.1f %.1f' % (x * 1000, -y * 1000) for x, y in pts)
    return '    (%s "" (polygon %s 0 %s))\n' % (kind, layer, s)


keepouts = []           # (kind, layer, points)
report = dict(board=SRC, keepouts=[], pads_inside=[])
for net in SENS:
    ps = copper(net, CU, VIA_ZONE[net])
    polys, holes = outlines(ps)
    for pts in polys:
        for ln in CU:
            keepouts.append(('via_keepout', ln, pts))
    report['keepouts'].append(dict(kind='via', net=net, dist=VIA_ZONE[net], polygons=len(polys), holes_filled=holes,
                                   poly=ps))
for net, src, dst, d in WIRE_ZONE:
    ps = copper(net, src, d)
    polys, holes = outlines(ps)
    for pts in polys:
        for ln in dst:
            keepouts.append(('keepout', ln, pts))
    report['keepouts'].append(dict(kind='wire', net=net, layers=dst, dist=d, polygons=len(polys), holes_filled=holes,
                                   poly=ps))
# J9 tie slots (non-plated holes)
nslot = 0
for f in FPS:
    for p in f.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, LID['F.Cu'], MM(NPTH_CLR), ERR, pcbnew.ERROR_OUTSIDE)
            simplify(ps)
            for pts in outlines(ps)[0]:
                for ln in CU:
                    keepouts.append(('keepout', ln, pts))
            nslot += 1
report['keepouts'].append(dict(kind='npth', count=nslot, dist=NPTH_CLR))
# board edge strips (the outline is a rectangle)
bb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = [pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]
e = EDGE_CLR
for r in ((x0, y0, x1, y0 + e), (x0, y1 - e, x1, y1), (x0, y0, x0 + e, y1), (x1 - e, y0, x1, y1)):
    for ln in CU:
        keepouts.append(('keepout', ln, [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]))
report['keepouts'].append(dict(kind='edge', box=[x0, y0, x1, y1], dist=EDGE_CLR))

# pads of open nets inside a keep-out
open_nets = None
if DRC:
    open_nets = set()
    for u in json.load(open(DRC))['unconnected_items']:
        for it in u['items']:
            m = re.search(r'\[([^\]]+)\]', it['description'])
            if m:
                open_nets.add(m.group(1))
# (GND is not routed by Freerouting: -inc gnd; its pads reach the planes through the fills and stitching)
checks = [k for k in report['keepouts'] if 'poly' in k]
for net, d in LOGIC_CLR.items():
    checks.append(dict(kind='logic clearance', net=net, dist=d, poly=copper(net, CU, d), logic_only=True))
for k in checks:
    ps = k.pop('poly')
    for f in FPS:
        for p in f.Pads():
            n = p.GetNetname()
            if not n or n in (k['net'], 'GND') or (open_nets is not None and n not in open_nets):
                continue
            if k.get('logic_only') and cls_of(n) != 'logic':
                continue
            lays = k.get('layers', CU)
            if not any(p.IsOnLayer(LID[ln]) and p.FlashLayer(LID[ln]) for ln in lays):
                continue
            pp = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(pp, LID['B.Cu' if f.IsFlipped() else 'F.Cu'], 0, ERR, pcbnew.ERROR_INSIDE)
            pts = [pp.Outline(0).CPoint(i) for i in range(pp.Outline(0).PointCount())] + [p.GetPosition()]
            inside = sum(ps.Contains(pcbnew.VECTOR2I(v.x, v.y)) for v in pts)
            if inside:
                report['pads_inside'].append(dict(keepout='%s %s' % (k['kind'], k['net']), pad='%s.%s' % (
                    f.GetReference(), p.GetNumber()), net=n, cls=cls_of(n), side='B' if f.IsFlipped() else 'F',
                    points_inside='%d/%d' % (inside, len(pts))))

# the layers where logic keeps 2 mm from U2 In+ / V_err: those of logic's routing layers where they have copper
LOGIC_LAYERS = {}
for s_ in LOGIC_CLR:
    ls = set()
    for t in TRACKS:
        if t.GetNetname() == s_ and t.GetClass() != 'PCB_VIA':
            ls.add(b.GetLayerName(t.GetLayer()))
    for f in FPS:
        for p in f.Pads():
            if p.GetNetname() == s_ and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                ls.add('B.Cu' if f.IsFlipped() else 'F.Cu')
    LOGIC_LAYERS[s_] = [l for l in CLASSES['logic'][0] if l in ls]
report['logic_clearance_layers'] = LOGIC_LAYERS

# Pad-centre stubs, DSN only: Freerouting does not count a track that ends inside a pad away from its centre as
# connected (route_card.py ends tracks on its 0.1 mm grid), and draws a stub to the centre. So every track end that
# lies in a pad of its net gets a fixed wire from there to the pad centre, on the track's layer at the track's width.
# The stub lies within the pad and the track's own end, adds no copper, and never comes back: Freerouting leaves fixed
# wiring out of the session.
stubs = []
PADS = [(p, f) for f in FPS for p in f.Pads() if p.GetNetname()]
for t in TRACKS:
    if t.GetClass() == 'PCB_VIA':
        continue
    lid = t.GetLayer()
    for e in (t.GetStart(), t.GetEnd()):
        for p, f in PADS:
            if p.GetNetname() != t.GetNetname() or not p.IsOnLayer(lid) or not p.FlashLayer(lid) or not p.HitTest(e):
                continue
            c = p.GetPosition()
            if (c - e).EuclideanNorm() > 1000:
                stubs.append((b.GetLayerName(lid), t.GetWidth(), (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)),
                              (pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)), t.GetNetname()))
            break
report['pad_centre_stubs'] = len(stubs)

# the GND fills go last: after BOARD.Remove() the SWIG item lists stop iterating (KiCad 10)
for z in list(b.Zones()):
    if not z.GetIsRuleArea() and z.GetZoneName() in ('GND fill', '5V pour'):
        b.Remove(z)
tmp = OUT + '.kicad.dsn'
if not pcbnew.ExportSpecctraDSN(b, tmp):
    sys.exit('ExportSpecctraDSN failed')
txt = open(tmp, encoding='utf8').read()

# structure: one via, the added keep-outs, via-in-pad allowed
m = re.search(r'\n    \(via "[^\n]*\)\n', txt)
ko = ''.join(dsn_poly(kind, ln, pts) for kind, ln, pts in keepouts)
txt = txt[:m.start()] + '\n' + ko.rstrip('\n') + '\n    (via "%s")\n' % VIA + txt[m.end():]
pad = re.search(r'\(padstack "%s"\n(.*?)\(attach off\)' % re.escape(VIA), txt, re.S)
txt = txt[:pad.end() - len('(attach off)')] + '(attach on)' + txt[pad.end():]

# network: rewrite the classes
net_sec = re.search(r'\n  \(network\n(.*?)\n  \)\n  \(wiring', txt, re.S)
body = net_sec.group(1)
c0 = body.index('\n    (class ')
tok = re.findall(r'"[^"]*"|[^\s()]+', body[:c0])
names = []
i = 0
while i < len(tok):
    if tok[i] == 'net':
        names.append(tok[i + 1])
    i += 1
members = {c: [] for c in CLASSES}
for t in names:
    n = t.strip('"').replace('{slash}', '/')
    c = cls_of(n)
    if open_nets is not None and n not in open_nets and c in ('logic', 'analog', 'sense', 'rail12', 'railA') and \
            (not LOCK_ONLY or all(x.IsLocked() for x in TRACKS if x.GetNetname() == n)):
        c = 'done'
    members[c].append(t)
cls_txt = ''
for c, (lays, w, clr) in CLASSES.items():
    if not members[c]:
        continue
    cls_txt += '    (class %s %s\n      (circuit\n        (use_via "%s")\n        (use_layer %s)\n      )\n' \
               '      (rule\n        (width %d)\n        (clearance %d)\n      )\n    )\n' % (
                   c, ' '.join(members[c]), VIA, ' '.join(lays), w, clr)
pairs = []
for s, d in LOGIC_CLR.items():
    pairs.append(('logic', cls_of(s), int(d * 1000), LOGIC_LAYERS[s]))
# the Power-class nets (J11 sense lines, GND) keep 0.25 mm from everything, as KiCad takes the larger clearance
for a in ('sense', 'gnd'):
    for c in CLASSES:
        if c != a and not any({a, c} == {p[0], p[1]} for p in pairs):
            pairs.append((a, c, 250, None))
pairs = [p for p in pairs if members[p[0]] and members[p[1]]]
for a, c, v, lays in pairs:
    if lays:
        # the 2 mm applies on the layers where the sensitive net has copper (the user's rule: no logic net running
        # parallel to it); elsewhere a GND plane lies between them and the ordinary clearance holds
        cls_txt += '    (class_class\n      (classes %s %s)\n      (rule\n        (clearance 200)\n      )\n' % (a, c)
        for ln in lays:
            cls_txt += '      (layer_rule %s\n        (rule\n          (clearance %d)\n        )\n      )\n' % (ln, v)
        cls_txt += '    )\n'
    else:
        cls_txt += '    (class_class\n      (classes %s %s)\n      (rule\n        (clearance %d)\n      )\n    )\n' % (a, c, v)
body = body[:c0 + 1] + cls_txt.rstrip('\n')
txt = txt[:net_sec.start(1)] + body + txt[net_sec.end(1):]
w0 = txt.index('\n  (wiring\n') + len('\n  (wiring\n')
txt = txt[:w0] + ''.join('    (wire (path %s %d  %.1f %.1f  %.1f %.1f)(net "%s")(type fix))\n' % (
    ln, round(w / 1000), a[0] * 1000, -a[1] * 1000, c[0] * 1000, -c[1] * 1000, n.replace('/', '{slash}'))
    for ln, w, a, c, n in stubs) + txt[w0:]
open(OUT, 'w', encoding='utf8', newline='\n').write(txt)

report['classes'] = {c: len(v) for c, v in members.items()}
report['class_class'] = pairs
report['keepout_polygons'] = len(keepouts)
json.dump(report, open(REP, 'w'), indent=1)
print('wrote %s: %d keep-out polygons, classes %s' % (OUT, len(keepouts), report['classes']))
for k in report['keepouts']:
    print('  keep-out', {a: v for a, v in k.items()})
print('pads of open nets inside a keep-out: %d' % len(report['pads_inside']))
for p in report['pads_inside']:
    print('  ', p)
