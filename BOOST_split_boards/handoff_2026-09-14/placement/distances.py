import json, math, sys
fps = json.load(open(sys.argv[1]))

def P(ref, num):
    x, y, net = fps[ref]["pads"][num]
    return (x, y, net)

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def row(label, a, b):
    pa, pb = P(*a), P(*b)
    print(f"  {label:44s} {a[0]}.{a[1]} -> {b[0]}.{b[1]}  {dist(pa, pb):5.1f} mm")

print("LED sink: FET source -> its shunt (2.63 A)")
row("M8 source -> R7 (ch3)", ("M8", "3"), ("R7", "1"))
row("M9 source -> R53 (ch2)", ("M9", "3"), ("R53", "1"))
row("M10 source -> R52 (ch1)", ("M10", "3"), ("R52", "1"))
print("LED sink: FET drain -> LED pad (2.63 A)")
row("M10 drain -> J4 (Output1)", ("M10", "2"), ("J4", "1"))
row("M9 drain -> J7 (Output2)", ("M9", "2"), ("J7", "1"))
row("M8 drain -> J6 (Output3)", ("M8", "2"), ("J6", "1"))
print("Rail FET drain -> its output capacitors (7-8 A RMS)")
for fet, caps, rail in (("M2", ("C70", "C86", "C88"), "Vout_1"),
                        ("M3", ("C71", "C78", "C87"), "Vout_2"),
                        ("M4", ("C74", "C75", "C77"), "Vout_3")):
    for c in caps:
        row(f"{fet} drain -> {c} ({rail})", (fet, "2"), (c, "1"))
print("Nearest wrong-rail capacitors to each rail FET")
for fet in ("M2", "M3", "M4"):
    rail = P(fet, "2")[2]
    near = sorted((dist(P(fet, "2"), P(c, "1")), c, P(c, "1")[2])
                  for c in ("C70","C86","C88","C71","C78","C87","C74","C75","C77"))
    print(f"  {fet} ({rail}): " + ", ".join(f"{c} {n} {d:.0f}mm" for d, c, n in near[:4]))
print("LX: L1 -> switch FET drains (15.8 / 7-8 A RMS)")
for m in ("M1", "M7", "M6", "M5"):
    row(f"L1.1 -> {m} drain", ("L1", "1"), (m, "2"))
row("M1 drain -> D19 (TVS)", ("M1", "2"), ("D19", "1"))
print("Back-to-back switch pairs: shared source")
row("M7 source -> M2 source (m2_source)", ("M7", "3"), ("M2", "3"))
row("M6 source -> M3 source (m3_source)", ("M6", "3"), ("M3", "3"))
row("M5 source -> M4 source (m4_source)", ("M5", "3"), ("M4", "3"))
print("Input: caps / shunt / M1 return")
for c in ("C40", "C85", "C69"):
    row(f"{c} GND -> M1 source", (c, "2"), ("M1", "3"))
row("J1 -> R1.2 (Vin)", ("J1", "1"), ("R1", "2"))
row("R1 -> U25 IN- (Kelvin sense)", ("R1", "1"), ("U25", "1"))
print("Gate drivers -> the FETs they drive")
for drv, fets in (("U19", ("M1",)), ("U15", ("M2", "M7")), ("U10", ("M3", "M6")), ("U8", ("M4", "M5"))):
    for m in fets:
        row(f"{drv} centre -> {m} gate", (drv, "9"), (m, "1"))
print("Sink op-amp -> its FET gate / shunt")
for u, m, r in (("U6", "M8", "R7"), ("U12", "M9", "R53"), ("U11", "M10", "R52")):
    row(f"{u} IN- -> {r}.1", (u, "4"), (r, "1"))
    row(f"{u} OUT -> {m} gate (via gate R)", (u, "1"), (m, "1"))

# TO-220 tab pitch
print("TO-220 positions (x, y):")
for m in ("M2","M7","M1","M6","M3","M4","M8","M9","M10","M5"):
    f = fps[m]
    print(f"  {m:4s} {f['x']:6.1f} {f['y']:6.1f}")
