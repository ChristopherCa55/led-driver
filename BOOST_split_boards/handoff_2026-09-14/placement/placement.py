"""Extract footprint placement and pad nets from a .kicad_pcb and report
power-path distances. Read-only."""
import math, re, sys, json

path = sys.argv[1]
src = open(path, encoding="utf-8").read()

def sexpr_blocks(text, head):
    """Yield top-level-ish '(head ...)' blocks by paren matching."""
    i = 0
    key = "(" + head + " "
    key2 = "(" + head + "\n"
    while True:
        a = text.find(key, i)
        b = text.find(key2, i)
        cands = [x for x in (a, b) if x >= 0]
        if not cands:
            return
        s = min(cands)
        depth = 0
        j = s
        in_str = False
        while j < len(text):
            c = text[j]
            if in_str:
                if c == "\\":
                    j += 1
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield text[s:j + 1]
        i = j + 1

fps = {}
for blk in sexpr_blocks(src, "footprint"):
    name = re.match(r'\(footprint\s+"([^"]+)"', blk).group(1)
    layer = re.search(r'\(layer\s+"([^"]+)"\)', blk).group(1)
    at = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', blk)
    x, y = float(at.group(1)), float(at.group(2))
    rot = float(at.group(3) or 0)
    ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', blk).group(1)
    val = re.search(r'\(property\s+"Value"\s+"([^"]+)"', blk)
    val = val.group(1) if val else ""
    pads = {}
    for p in sexpr_blocks(blk, "pad"):
        pm = re.match(r'\(pad\s+"([^"]*)"', p)
        pat = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)', p)
        net = re.search(r'\(net\s+(?:\d+\s+)?"([^"]*)"\)', p)
        if not pm or not pat:
            continue
        px, py = float(pat.group(1)), float(pat.group(2))
        th = math.radians(-rot)
        gx = x + px * math.cos(th) - py * math.sin(th)
        gy = y + px * math.sin(th) + py * math.cos(th)
        pads[pm.group(1)] = (round(gx, 2), round(gy, 2), net.group(1) if net else "")
    fps[ref] = dict(fp=name, layer=layer, x=x, y=y, rot=rot, val=val, pads=pads)

json.dump(fps, open(sys.argv[2], "w"), indent=1)
print(len(fps), "footprints")

def d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def pad(ref, num):
    return fps[ref]["pads"][num]

refs = ["J1","J2","R1","U25","L1","D19","M1","M5","M6","M7","M2","M3","M4",
        "M8","M9","M10","R7","R52","R53","U6","U11","U12",
        "C40","C69","C85","C70","C86","C88","C71","C78","C87","C74","C75","C77",
        "J3","J4","J5","J6","J7","J8","J10","U8","U10","U15","U19","R47"]
print("\nref   side   x      y     rot  value / footprint")
for r in refs:
    if r in fps:
        f = fps[r]
        print(f"{r:5s} {f['layer'][:4]:5s} {f['x']:6.1f} {f['y']:6.1f} {f['rot']:5.0f}  {f['val']} / {f['fp'].split(':')[-1]}")
        print("      pads:", {k: v[2] for k, v in f["pads"].items()})
