"""One-off patch: route_new.py A* becomes direction-aware with a turn penalty (job 'turn_cost', default 0.15 mm per
45 degrees), so paths come out as long straight / 45-degree runs instead of grid staircases; and the free first segment
from the pad centre is limited to 0.15 mm so the first leg is octilinear too."""
import sys
p = sys.argv[1]
t = open(p, encoding='utf-8').read()
old_loop = t[t.index("        hc = {}\n        start_state = (L[slayer], si, sj)"):t.index("        if end is None:\n            print('NO ROUTE for'")]
new_loop = '''        hc = {}
        DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]   # 45-degree steps, in order
        tpen = job.get('turn_cost', 0.15)
        start_state = (L[slayer], si, sj, 8)       # direction 8 = none yet (start, or just after a via)
        openq = [(0.0, 0.0, start_state)]
        came, cost = {start_state: None}, {start_state: 0.0}
        own = g.empty()
        block(start[0], own, 0.0)
        end = None
        n = 0
        while openq:
            f, c0, s = heapq.heappop(openq)
            if c0 > cost.get(s, 1e18) + 1e-9:
                continue
            n += 1
            li, i, j, dprev = s
            ln = RL[li]
            if goal[ln][i, j] and s != start_state:
                end = (s, 'track')
                break
            if vgoal[i, j] and not vblk[i, j]:
                end = (s, 'via')
                break
            nbrs = []
            for dk, (di, dj) in enumerate(DIRS):
                ii, jj = i + di, j + dj
                if 0 <= ii < g.ny and 0 <= jj < g.nx and (not tblk[ln][ii, jj] or own[ii, jj] and li == L[slayer]):
                    turn = 0 if dprev == 8 else min((dk - dprev) % 8, (dprev - dk) % 8)
                    if turn > 2:                    # no turns sharper than 90 degrees
                        continue
                    sc = (1.4142 if di and dj else 1.0) * G * lcost.get(ln, 1.0) + turn * tpen
                    nbrs.append(((li, ii, jj, dk), sc))
            if not vblk[i, j]:
                for lj in range(len(RL)):
                    if lj != li:
                        nbrs.append(((lj, i, j, 8), job.get('via_cost', 1.5)))
            for ns, sc in nbrs:
                nc = c0 + sc
                if nc < cost.get(ns, 1e18):
                    cost[ns] = nc
                    came[ns] = s
                    key = ns[1:3]
                    if key not in hc:
                        hc[key] = h(*key)
                    heapq.heappush(openq, (nc + hc[key], nc, ns))
'''
t = t.replace(old_loop, new_loop)
a = "                                seen=np.array([k for k in cost]))"
assert t.count(a) == 1
t = t.replace(a, "                                seen=np.array([k[:3] for k in cost]))")
a = "        path.reverse()\n"
assert t.count(a) == 1
t = t.replace(a, "        path.reverse()\n        path = [q[:3] for q in path]\n")
a = "        li, i, j = end[0]\n"
assert t.count(a) == 1
t = t.replace(a, "        li, i, j = end[0][:3]\n")
a = "            return dx_ == 0 or dy_ == 0 or abs(abs(dx_) - abs(dy_)) < 1e-6 or (p is pts[0])"
assert t.count(a) == 1
t = t.replace(a, "            return (dx_ == 0 or dy_ == 0 or abs(abs(dx_) - abs(dy_)) < 1e-6 or\n"
                 "                    (p is pts[0] and math.hypot(dx_, dy_) <= 0.15))")
open(p, 'w', encoding='utf-8').write(t)
print('patched')
