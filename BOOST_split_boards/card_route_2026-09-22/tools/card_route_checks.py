"""Layer-plan and routing checks on a saved control-card board (KiCad Python).

usage: python.exe card_route_checks.py BOARD.kicad_pcb OUT.json [--open-plan]

- layer plan (approved, check-in 2): no track on In1 / In4 / In6 (GND planes); on In3 only 5V, analog_5V, 12V;
  no logic net on In5; no analog net on In2 (classes from card_nets.py);
  with --open-plan (user, 2026-09-24): no track on In1 / In6; no GND track on In3; on In4 no other net within 2 mm
  of the U2 In+ run or the Current stub; the In3 5 V pour in one piece;
- vias: count, smallest drill (rule >= 0.3 mm), vias whose centre lies inside an SMD pad of their own net
  (via-in-pad, filled and capped per ROUTING_SPEC 2);
- track length per layer and per class (logic / analog / rail / GND / 5V);
- pad-to-zone connections: J11's ten GND pads solid, J9.10 thermal (user decisions);
- the board file carries a stackup (8 copper layers).
"""
import json, sys, collections, re
import pcbnew

sys.path.insert(0, 'tools')
from card_nets import ANALOG, RAILS, is_logic

MM = pcbnew.ToMM
OPEN = '--open-plan' in sys.argv
sys.argv = [x for x in sys.argv if x != '--open-plan']
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
b.BuildConnectivity()
LID = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
# --open-plan (user, 2026-09-24): In1 / In6 GND planes only; In2-In5 open to logic, analog and rails; GND off In3;
# on In4 no other net within 2 mm of the U2 In+ run (In5) or the Current stub (B.Cu); the In3 5 V pour in one piece
CORRIDOR = []           # (net, shape) sources of the In4 corridor
if OPEN:
    for t in b.GetTracks():
        n = t.GetNetname()
        if (n == 'Net-(U2-In+)' and t.IsOnLayer(LID['In5.Cu'])) or (n == 'Current' and t.IsOnLayer(LID['B.Cu'])):
            CORRIDOR.append((n, t.GetEffectiveShape(LID['In5.Cu'] if n != 'Current' else LID['B.Cu'])))
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == 'Current' and p.IsOnLayer(LID['B.Cu']):
                CORRIDOR.append(('Current', p.GetEffectiveShape(LID['B.Cu'])))


def cls(n):
    if n in ('GND', '5V'):
        return n
    if n in RAILS:
        return 'rail'
    if n in ANALOG:
        return 'analog'
    return 'logic'


viol = []
length = collections.defaultdict(float)
per_class = collections.defaultdict(float)
vias, drills = [], []
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == 'PCB_VIA':
        vias.append(t)
        drills.append(MM(t.GetDrillValue()))
        continue
    ln = b.GetLayerName(t.GetLayer())
    L = MM(t.GetLength())
    length[ln] += L
    per_class[(ln, cls(n))] += L
    if OPEN:
        if ln in ('In1.Cu', 'In6.Cu'):
            viol.append('track on GND plane layer %s: %s' % (ln, n))
        if ln == 'In3.Cu' and n == 'GND':
            viol.append('GND track on In3 (the 5 V pour layer)')
        if ln == 'In4.Cu' and n != 'GND':
            sh = t.GetEffectiveShape(LID['In4.Cu'])
            for src, s2 in CORRIDOR:
                if src != n and sh.Collide(s2, pcbnew.FromMM(2.0)):
                    viol.append('%s track on In4 within 2 mm of the %s corridor' % (n, src))
                    break
        continue
    if ln in ('In1.Cu', 'In4.Cu', 'In6.Cu'):
        viol.append('track on GND plane layer %s: %s' % (ln, n))
    if ln == 'In3.Cu' and n not in ('5V', 'analog_5V', '12V'):
        viol.append('track on In3 (5 V plane layer): %s' % n)
    if ln == 'In5.Cu' and is_logic(n):
        viol.append('logic net on In5: %s' % n)
    if ln == 'In2.Cu' and n in ANALOG:
        viol.append('analog net on In2: %s' % n)
pieces = {}
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    for ln in ('In1.Cu', 'In3.Cu', 'In4.Cu', 'In6.Cu'):
        if z.IsOnLayer(LID[ln]) and z.HasFilledPolysForLayer(LID[ln]):
            ps = z.GetFilledPolysList(LID[ln])
            pieces['%s %s' % (ln, z.GetNetname())] = dict(pieces=ps.OutlineCount(), mm2=round(ps.Area() * 1e-12, 1))
if OPEN and pieces.get('In3.Cu 5V', {}).get('pieces', 1) != 1:
    viol.append('5V pour on In3 in %d pieces (must be one)' % pieces['In3.Cu 5V']['pieces'])
vip = 0
for v in vias:
    pos = v.GetPosition()
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetNetname() == v.GetNetname() and \
                    p.HitTest(pos) if hasattr(p, 'HitTest') else False:
                vip += 1
                break
        else:
            continue
        break
fps = {f.GetReference(): f for f in b.GetFootprints()}
conn = {}
for p in fps['J11'].Pads():
    if p.GetNetname() == 'GND':
        conn['J11.' + p.GetNumber()] = int(p.GetLocalZoneConnection())
for p in fps['J9'].Pads():
    if p.GetNetname() == 'GND':
        conn['J9.' + p.GetNumber()] = int(p.GetLocalZoneConnection())
FULL, THERMAL = int(pcbnew.ZONE_CONNECTION_FULL), int(pcbnew.ZONE_CONNECTION_THERMAL)
conn_ok = all(v == FULL for k, v in conn.items() if k.startswith('J11.')) and conn.get('J9.10') == THERMAL
txt = open(path, encoding='utf8').read()
stack = re.search(r'\(stackup', txt) is not None and len(re.findall(r'\(type "copper"\)', txt)) == 8
out = dict(board=path, layer_violations=viol, vias=len(vias), min_via_drill=min(drills) if drills else None,
           via_in_pad=vip, track_mm_by_layer={k: round(v, 1) for k, v in sorted(length.items())},
           track_mm_by_layer_class={'%s %s' % k: round(v, 1) for k, v in sorted(per_class.items())},
           gnd_pad_connections=conn, gnd_pad_connections_ok=conn_ok, stackup_8_copper=stack,
           plan='open (2026-09-24)' if OPEN else 'check-in 2', plane_pieces=pieces)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print('layer-plan (%s) violations: %d%s' % (out['plan'], len(viol), ''.join('\n  ' + x for x in viol[:20])))
print('inner planes / pours:', pieces)
print('vias %d, smallest drill %.2f mm, via-in-pad %d' % (len(vias), out['min_via_drill'] or 0, vip))
print('track mm by layer:', out['track_mm_by_layer'])
print('J11 GND pads solid and J9.10 thermal: %s; stackup with 8 copper layers: %s' % (conn_ok, stack))
