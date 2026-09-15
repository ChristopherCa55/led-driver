"""The nine output caps are identical 220 uF parts. How much shorter do the
rail-FET -> cap distances get if the same nine positions are reassigned to
the right rails (positions only, no new placement)?"""
import json, math, sys, itertools
fps = json.load(open(sys.argv[1]))
caps = ["C70", "C86", "C88", "C71", "C78", "C87", "C74", "C75", "C77"]
rails = {"M2": "Vout_1", "M3": "Vout_2", "M4": "Vout_3"}
pos = {c: fps[c]["pads"]["1"][:2] for c in caps}
drain = {m: fps[m]["pads"]["2"][:2] for m in rails}

def d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

now = {m: [c for c in caps if fps[c]["pads"]["1"][2] == r] for m, r in rails.items()}
tot_now = sum(d(drain[m], pos[c]) for m in now for c in now[m])
best = None
slots = list(pos.values())
for perm in itertools.permutations(range(9)):
    groups = {"M2": perm[0:3], "M3": perm[3:6], "M4": perm[6:9]}
    if any(list(g) != sorted(g) for g in groups.values()):
        continue
    t = sum(d(drain[m], slots[i]) for m, g in groups.items() for i in g)
    if best is None or t < best[0]:
        best = (t, groups)
print(f"sum of FET->cap distances now: {tot_now:.0f} mm")
for m in now:
    print(f"  {m}: " + ", ".join(f"{c} {d(drain[m], pos[c]):.0f}" for c in now[m]))
print(f"best reassignment of the same 9 spots: {best[0]:.0f} mm")
for m, g in best[1].items():
    print(f"  {m}: " + ", ".join(f"{caps[i]}'s spot {d(drain[m], slots[i]):.0f}" for i in g))
