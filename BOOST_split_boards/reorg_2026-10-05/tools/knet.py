"""Parse a KiCad 10 S-expression netlist: comps {ref: value}, pins {ref: [(pin, net)]}, nets {net: [(ref, pin)]}."""
import re, collections


def load(path):
    t = open(path, encoding='utf-8').read()
    comps = {}
    for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)\s+\(value "([^"]*)"\)', t):
        comps[m.group(1)] = m.group(2)
    pins, nets = collections.defaultdict(list), collections.defaultdict(list)
    i = t.find('(nets')
    for m in re.finditer(r'\(net\s+\(code "\d+"\)\s+\(name "([^"]*)"\)(.*?)(?=\(net\s+\(code|\Z)', t[i:], re.S):
        n = m.group(1)
        for r, p in re.findall(r'\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', m.group(2)):
            pins[r].append((p, n))
            nets[n].append((r, p))
    return comps, pins, nets
