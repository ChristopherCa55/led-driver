"""Place the sink-sense net-ties on their shunts' top pads (after psat).

  python pnettie.py FULL_LAYOUT.json OUT.json

NT1/NT2/NT3 (NetTie-2_SMD_Pad0.5mm: pad 1 sense net at (-0.5, 0), pad 2 shunt-top net at (+0.5, 0), 0.5 mm
circles, no courtyard) go on R52/R53/R7 pad 1 (Net-(M10/M9/M8-S), 1.225 x 3.35 mm at (-2.9625, 0)).
Along the pad's long axis the tie's pad 2 is centred 1.5 mm from the pad centre (overlapping the pad end,
same net) and pad 1 (SNS_CHn) 2.5 mm from it, 0.575 mm clear of the pad copper, so the sense trace leaves
from the shunt pad itself. Of the two pad ends, the one farther from the sink FET's source pin is used.
psat places net-ties anywhere (no courtyard); this step overrides those positions.
"""
import sys, json, math
import pmodel as M

res = json.load(open(sys.argv[1]))
L = {k: tuple(v) for k, v in res['layout'].items()}
for nt, shunt, fet in (('NT1', 'R52', 'M10'), ('NT2', 'R53', 'M9'), ('NT3', 'R7', 'M8')):
    X, Y, rot, side = L[shunt]
    assert side == 'F', (shunt, side)
    src = M.pad(L, fet, '3')
    best = None
    for sgn in (-1, 1):
        # shunt-local centre of the tie and the tie's rotation relative to the shunt (pads along local y)
        lx, ly = -2.9625, sgn * 2.0
        rel = 270 if sgn < 0 else 90          # 270: pad 1 toward -y; 90: pad 1 toward +y
        wx, wy = M.tf(L[shunt], lx, ly)
        pl = (wx, wy, int(round(rot + rel)) % 360, 'F')
        L[nt] = pl
        p1, p2 = M.pad(L, nt, '1'), M.pad(L, nt, '2')
        sp = M.pad(L, shunt, '1')
        assert p2[5] == sp[5] and p1[5].startswith('SNS_CH'), (nt, p1[5], p2[5], sp[5])
        d2 = math.hypot(p2[1] - sp[1], p2[2] - sp[2])
        d1 = math.hypot(p1[1] - sp[1], p1[2] - sp[2])
        assert abs(d2 - 1.5) < 1e-6 and abs(d1 - 2.5) < 1e-6, (nt, d1, d2)
        far = math.hypot(p1[1] - src[1], p1[2] - src[2])
        if best is None or far > best[0]:
            best = (far, pl)
    L[nt] = best[1]
    print('%s on %s pad 1 end, sense pad %.1f mm from %s source: (%.2f, %.2f) rot %d' % (nt, shunt, best[0], fet, *best[1][:3]))
res['layout'] = {k: list(v) for k, v in L.items()}
json.dump(res, open(sys.argv[2], 'w'), indent=1)
