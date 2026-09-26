"""Check the sensitive-net rules on a saved, filled board (KiCad Python).

usage: python.exe sens_check.py BOARD.kicad_pcb OUT.json

Rules (user, 2026-09-22, and the approved routing plan of check-in 2):
- Net-(U2-In+): the run on In5 between the In4 and In6 GND planes (outer layers only as pad-to-via stubs), a GND guard
  either side on In5, no logic net parallel to it, no via of another net within 2 mm.
- Current: B.Cu over continuous In6 GND; no other copper on B.Cu or In5 within 2 mm of it; no via of another net
  within 2 mm.
- V_err: logic nets kept 2 mm away; its 17 mm route (F.Cu, a via, B.Cu) accepted by the user on 2026-09-23 provided
  a GND plane runs under its whole length and no logic net runs parallel to it within 2 mm ("whole length" below).
Distances are copper edge to copper edge; "plan" means measured in plan view whatever the layers. GND is exempt
(guard and stitching). Tracks of nets that have a pad on the sensitive net's own parts are listed separately: those
pins sit beside the sensitive pad by placement.
Coverage: points every 0.1 mm along the sensitive tracks, except within 0.8 mm of the net's own vias and pads (their
plane antipads and pad lands); "guard" = GND fill on the same layer found on both sides
within track edge + 0.25 mm clearance + 0.15 mm; "plane" = the GND plane above / below contains the point.
"""
import json, math, sys
import pcbnew

MM, FM = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
sys.path.insert(0, 'tools')
from card_nets import ANALOG, RAILS, is_logic      # the router's net classes

ZONE = 2.0
LID = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}


def dist(sa, sb):
    if sa.Collide(sb, 0):
        return 0.0
    lo, hi = 0.0, 6.0
    if not sa.Collide(sb, FM(hi)):
        return 99.0
    for _ in range(18):
        mid = (lo + hi) / 2
        if sa.Collide(sb, FM(mid)):
            hi = mid
        else:
            lo = mid
    return round(hi, 3)


fps = {f.GetReference(): f for f in b.GetFootprints()}
items = []          # (kind, net, layers, shape per layer, object)
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        items.append(('via', t.GetNetname(), None, t))
    else:
        items.append(('track', t.GetNetname(), b.GetLayerName(t.GetLayer()), t))
for f in b.GetFootprints():
    for p in f.Pads():
        items.append(('pad', p.GetNetname(), f.GetReference(), p))


def copper_of(net):
    out = []
    for k, n, l, o in items:
        if n != net:
            continue
        if k == 'track':
            out.append((l, o.GetEffectiveShape(LID[l]), o))
        elif k == 'via':
            for ln, lid in LID.items():
                out.append((ln, o.GetEffectiveShape(lid), o))
        else:
            for ln, lid in LID.items():
                if o.IsOnLayer(lid):
                    out.append((ln, o.GetEffectiveShape(lid), o))
    return out


def plan_shape(o):
    if isinstance(o, pcbnew.PCB_VIA):
        return pcbnew.SHAPE_SEGMENT(o.GetPosition(), o.GetPosition(), int(o.GetWidth(pcbnew.F_Cu)))
    if isinstance(o, pcbnew.PAD):
        return o.GetEffectiveShape(LID['F.Cu'] if o.IsOnLayer(LID['F.Cu']) else LID['B.Cu'])
    return o.GetEffectiveShape(o.GetLayer())


zones = {}
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    for ln, lid in LID.items():
        if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
            zones.setdefault((z.GetNetname(), ln), []).append(z.GetFilledPolysList(lid))


def in_fill(net, ln, x, y):
    return any(ps.Contains(pcbnew.VECTOR2I(FM(x), FM(y))) for ps in zones.get((net, ln), []))


def along(t, step=0.1):
    x0, y0, x1, y1 = MM(t.GetStart().x), MM(t.GetStart().y), MM(t.GetEnd().x), MM(t.GetEnd().y)
    L = math.hypot(x1 - x0, y1 - y0)
    k = max(1, int(L / step))
    ux, uy = ((x1 - x0) / L, (y1 - y0) / L) if L > 0 else (1.0, 0.0)
    for i in range(k + 1):
        yield x0 + ux * L * i / k, y0 + uy * L * i / k, -uy, ux


def check(net, run_layer, track_layers, logic_only_layers, planes, logic_only_vias=False):
    own = copper_of(net)
    parts = {o.GetParentFootprint().GetReference() for (_, _, o) in own if isinstance(o, pcbnew.PAD)}
    part_nets = {p.GetNetname() for r in parts for p in fps[r].Pads()} - {net, 'GND'}
    res = dict(net=net, parts=sorted(parts))
    tr = [o for (k, n, l, o) in items if k == 'track' and n == net]
    res['track_mm_by_layer'] = {}
    for t in tr:
        ln = b.GetLayerName(t.GetLayer())
        res['track_mm_by_layer'][ln] = round(res['track_mm_by_layer'].get(ln, 0) + MM(t.GetLength()), 2)
    res['vias'] = sum(1 for (k, n, l, o) in items if k == 'via' and n == net)
    # foreign vias, plan view, any layer
    bad_vias = []
    for k, n, l, o in items:
        if k != 'via' or n in (net, 'GND') or (logic_only_vias and not is_logic(n)):
            continue
        sv = pcbnew.SHAPE_SEGMENT(o.GetPosition(), o.GetPosition(), int(o.GetWidth(pcbnew.F_Cu)))    # full annulus, any layer
        d = min(dist(sv, s) for (_, s, _) in own)
        if d < ZONE:
            bad_vias.append(dict(net=n, x=round(MM(o.GetPosition().x), 2), y=round(MM(o.GetPosition().y), 2), mm=d))
    res['foreign_vias_within_2mm'] = bad_vias
    # foreign tracks on the listed layers
    near, near_pins = [], []
    for k, n, l, o in items:
        if k != 'track' or n in (net, 'GND') or l not in track_layers:
            continue
        if l in logic_only_layers and not is_logic(n):
            continue
        so = o.GetEffectiveShape(LID[l])
        # In5 / In4 round Current count from its B.Cu copper; In4 round U2 In+ from its In5 run (open plan, 2026-09-24)
        src = {('Current', 'In5.Cu'): 'B.Cu', ('Current', 'In4.Cu'): 'B.Cu', ('Net-(U2-In+)', 'In4.Cu'): 'In5.Cu'}
        cands = [s for (ln, s, _) in own if ln == l or ln == src.get((net, l))]
        if not cands:
            continue
        d = min(dist(so, s) for s in cands)
        if d < ZONE:
            rec = dict(net=n, layer=l, mm=d, logic=is_logic(n), length=round(MM(o.GetLength()), 2))
            (near_pins if n in part_nets else near).append(rec)
    res['foreign_tracks_within_2mm'] = near
    res['foreign_tracks_within_2mm_pin_nets'] = near_pins
    # logic tracks anywhere within 2 mm in plan (shielded layers included), for the "no logic parallel" rule
    logic_plan = []
    for k, n, l, o in items:
        if k != 'track' or n in (net, 'GND') or not is_logic(n):
            continue
        so = o.GetEffectiveShape(o.GetLayer())
        d = min(dist(so, plan_shape(x[2])) for x in own)
        if d < ZONE:
            logic_plan.append(dict(net=n, layer=l, mm=d, length=round(MM(o.GetLength()), 2)))
    res['logic_tracks_within_2mm_plan_any_layer'] = logic_plan
    # guard and plane coverage along the run
    pts = guard = plane = 0
    plane_detail = {p: 0 for p in planes}
    ends = [(MM(o.GetPosition().x), MM(o.GetPosition().y)) for (_, _, o) in own
            if isinstance(o, (pcbnew.PCB_VIA, pcbnew.PAD))]
    for t in tr:
        if b.GetLayerName(t.GetLayer()) != run_layer:
            continue
        w = MM(t.GetWidth())
        for x, y, nx, ny in along(t):
            if any(math.hypot(x - a, y - c) < 0.8 for a, c in ends):
                continue            # the net's own via or pad: its plane antipad and pad land, not the run
            pts += 1
            off = w / 2 + 0.25 + 0.15
            if in_fill('GND', run_layer, x + nx * off, y + ny * off) and in_fill('GND', run_layer, x - nx * off, y - ny * off):
                guard += 1
            ok = True
            for p in planes:
                if in_fill('GND', p, x, y):
                    plane_detail[p] += 1
                else:
                    ok = False
            plane += ok
    res['run_points'] = pts
    res['guard_both_sides_pct'] = round(100.0 * guard / pts, 1) if pts else None
    res['planes_pct'] = round(100.0 * plane / pts, 1) if pts else None
    res['plane_detail_pct'] = {p: round(100.0 * v / pts, 1) for p, v in plane_detail.items()} if pts else {}
    # whole length, every layer (user, 2026-09-23, V_err): the GND plane next to each track -- In1 under F.Cu, In6
    # over B.Cu, In4 and In6 round In5 -- contains every point; reported with and without the 0.8 mm round the net's
    # own vias and pads, where the via's own antipad and the pad land sit
    adj = {'F.Cu': ['In1.Cu'], 'B.Cu': ['In6.Cu'], 'In5.Cu': ['In4.Cu', 'In6.Cu'], 'In2.Cu': ['In1.Cu']}
    n_all = ok_all = n_run = ok_run = 0
    gaps = []
    for t in tr:
        ln = b.GetLayerName(t.GetLayer())
        for x, y, nx, ny in along(t):
            ok = all(in_fill('GND', p, x, y) for p in adj.get(ln, ['?']))
            n_all += 1
            ok_all += ok
            if not any(math.hypot(x - a, y - c) < 0.8 for a, c in ends):
                n_run += 1
                ok_run += ok
                if not ok:
                    gaps.append((ln, round(x, 2), round(y, 2)))
    res['whole_length_points'] = n_all
    res['whole_length_plane_pct'] = round(100.0 * ok_all / n_all, 1) if n_all else None
    res['whole_length_plane_pct_off_own_vias_pads'] = round(100.0 * ok_run / n_run, 1) if n_run else None
    res['whole_length_plane_gaps_off_own_vias_pads'] = gaps[:40]
    res['gnd_vias_within_2mm'] = sum(1 for k, n, l, o in items if k == 'via' and n == 'GND' and
                                     min(dist(pcbnew.SHAPE_SEGMENT(o.GetPosition(), o.GetPosition(), int(o.GetWidth(pcbnew.F_Cu))), s)
                                         for (_, s, _) in own) < ZONE)
    return res


out = [check('Net-(U2-In+)', 'In5.Cu', ['F.Cu', 'In4.Cu', 'In5.Cu', 'B.Cu'], ['F.Cu', 'B.Cu'], ['In4.Cu', 'In6.Cu']),
       check('Current', 'B.Cu', ['B.Cu', 'In4.Cu', 'In5.Cu'], [], ['In6.Cu']),
       check('V_err', 'In5.Cu', ['F.Cu', 'In5.Cu', 'B.Cu'], ['F.Cu', 'In5.Cu', 'B.Cu'], ['In4.Cu', 'In6.Cu'],
             logic_only_vias=True)]
json.dump(out, open(sys.argv[2], 'w'), indent=1)
for r in out:
    print('%-14s tracks %s, vias %d | foreign vias <2mm: %d | foreign tracks <2mm: %d (+%d of its parts\' pin nets) | '
          'logic <2mm plan: %d | guard %s%% planes %s%% | GND vias <2mm %d' % (
              r['net'], r['track_mm_by_layer'], r['vias'], len(r['foreign_vias_within_2mm']),
              len(r['foreign_tracks_within_2mm']), len(r['foreign_tracks_within_2mm_pin_nets']),
              len(r['logic_tracks_within_2mm_plan_any_layer']), r['guard_both_sides_pct'], r['planes_pct'],
              r['gnd_vias_within_2mm']))
    print('%-14s GND plane next to the whole length: %s%% (%s%% off its own vias / pads, %d gap points)' % (
        '', r['whole_length_plane_pct'], r['whole_length_plane_pct_off_own_vias_pads'],
        len(r['whole_length_plane_gaps_off_own_vias_pads'])))
