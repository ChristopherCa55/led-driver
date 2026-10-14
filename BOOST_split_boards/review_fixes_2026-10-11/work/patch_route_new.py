"""One-off patch: route_new.py -> configurable routing layers (job 'layers', 'layer_cost'), holes carry their net."""
import sys
p = sys.argv[1]
t = open(p, encoding='utf-8').read()
R = [
    ("    holes = []        # (x, y, r)", "    holes = []        # (x, y, r, net)"),
    ("                holes.append((mm(c.x), mm(c.y), mm(p.GetDrillSizeX()) / 2))",
     "                holes.append((mm(c.x), mm(c.y), mm(p.GetDrillSizeX()) / 2, p.GetNetname()))"),
    ("            holes.append((mm(c.x), mm(c.y), mm(t.GetDrillValue()) / 2))",
     "            holes.append((mm(c.x), mm(c.y), mm(t.GetDrillValue()) / 2, t.GetNetname()))"),
    ("        for hx, hy, hr in holes:\n            g.disc(vblk, hx, hy, hr + 0.25 + vdrill / 2 + MARGIN)",
     "        for hx, hy, hr, hn in holes:\n            g.disc(vblk, hx, hy, hr + 0.25 + vdrill / 2 + MARGIN)"),
    ("            holes.append((x, y, vdrill / 2))", "            holes.append((x, y, vdrill / 2, net))"),
    ("        goal = {ln: g.empty() for ln in OUTER}", "        goal = {ln: g.empty() for ln in RL}"),
    ("                if it['layer'] in OUTER:\n                    m = g.empty()",
     "                if it['layer'] in RL:\n                    m = g.empty()"),
    ("        L = {ln: k for k, ln in enumerate(OUTER)}", "        L = {ln: k for k, ln in enumerate(RL)}"),
    ("        gx = [np.argwhere(goal[ln]) for ln in OUTER] + [np.argwhere(vgoal)]",
     "        gx = [np.argwhere(goal[ln]) for ln in RL] + [np.argwhere(vgoal)]"),
    ("        def h(i, j):\n            d = np.min(np.hypot(allg[:, 0] - i, allg[:, 1] - j))\n            return d * G",
     "        def h(i, j):\n            if len(allg) > 3000:         # a large goal (a pour): plain Dijkstra\n"
     "                return 0.0\n            d = np.min(np.hypot(allg[:, 0] - i, allg[:, 1] - j))\n"
     "            return d * G * min([1.0] + list(lcost.values()))"),
    ("            ln = OUTER[li]", "            ln = RL[li]"),
    ("                    nbrs.append(((li, ii, jj), sc * G))\n            if not vblk[i, j]:\n"
     "                nbrs.append(((1 - li, i, j), job.get('via_cost', 1.5)))",
     "                    nbrs.append(((li, ii, jj), sc * G * lcost.get(ln, 1.0)))\n            if not vblk[i, j]:\n"
     "                for lj in range(len(RL)):\n                    if lj != li:\n"
     "                        nbrs.append(((lj, i, j), job.get('via_cost', 1.5)))"),
    ("            np.savez_compressed(outp.replace('.json', '_fail.npz'), tF=tblk['F.Cu'], tB=tblk['B.Cu'], v=vblk,\n"
     "                                vgoal=vgoal, gF=goal['F.Cu'], gB=goal['B.Cu'], x1=g.x1, y1=g.y1,",
     "            np.savez_compressed(outp.replace('.json', '_fail.npz'), tF=tblk[RL[0]], tB=tblk[RL[1]], v=vblk,\n"
     "                                vgoal=vgoal, gF=goal[RL[0]], gB=goal[RL[1]], x1=g.x1, y1=g.y1,"),
    ("            pts.append((OUTER[li], x, y))", "            pts.append((RL[li], x, y))"),
    ("        key = ('via', i, j) if end[1] == 'via' else (OUTER[li], i, j)",
     "        key = ('via', i, j) if end[1] == 'via' else (RL[li], i, j)"),
    ("    clr = job.get('clearance', 0.2)",
     "    clr = job.get('clearance', 0.2)\n    RL = job.get('layers', list(OUTER))           # routing layers\n"
     "    lcost = job.get('layer_cost', {})              # cost factor per mm on a layer (default 1)"),
]
for a, b in R:
    assert t.count(a) == 1, a[:80]
    t = t.replace(a, b)
t = t.replace("Routes only on F.Cu / B.Cu (no new inner-layer tracks, so no GND plane is cut); a layer change is a through via.",
              "Routes on the job's 'layers' (default F.Cu / B.Cu; never a GND-plane layer, so no GND plane is cut) with\n"
              "an optional cost factor per layer ('layer_cost'); a layer change is a through via.")
open(p, 'w', encoding='utf-8').write(t)
print('patched')
