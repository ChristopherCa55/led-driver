"""List the symbols of an LTspice .asc: type, position, orientation, InstName.  python asc_list.py FILE.asc"""
import re, sys, collections

L = open(sys.argv[1], encoding='latin-1').read().split('\n')
cur, out = None, []
for ln in L:
    m = re.match(r'SYMBOL (\S+) (-?\d+) (-?\d+) (\S+)', ln)
    if m:
        cur = [m.group(1), int(m.group(2)), int(m.group(3)), m.group(4), None]
        out.append(cur)
        continue
    m = re.match(r'SYMATTR InstName (\S+)', ln)
    if m and cur:
        cur[4] = m.group(1)
print(len(out), 'symbols')
print(collections.Counter(o[0].replace(chr(92), '/').split('/')[-1] for o in out).most_common(45))
odd = [(o[4], o[0]) for o in out if not o[4] or not re.match(r'^[A-Z]+\d+$', o[4])]
print(len(odd), 'non-plain names:')
for n, ty in odd:
    print('  ', n, ty)
