"""Point the board projects at their new schematics and list the sub-sheets in the system project (text edits).

    python fix_projects.py DIR SPLIT_INFO.json
"""
import sys, os, json

d, info = sys.argv[1], json.load(open(sys.argv[2]))
for bd, name in (('POWER', 'BOOST_power_RC2'), ('CONTROL', 'BOOST_control_RC2')):
    p = os.path.join(d, name + '.kicad_pro')
    t = open(p, encoding='utf-8', newline='').read()
    old = '"uuid": "00000000-0000-0000-0000-000000000000"'
    assert t.count(old) == 1, p
    t = t.replace(old, '"uuid": "%s"' % info['sheets'][bd]['uuid'])
    open(p, 'w', encoding='utf-8', newline='').write(t)
    print(p, 'top-level sheet ->', info['sheets'][bd]['uuid'])
p = os.path.join(d, 'BOOST.kicad_pro')
t = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in t else '\n'
old = ('  "sheets": [' + nl + '    [' + nl + '      "%s",' % info['root'] + nl + '      ""' + nl + '    ]')
assert t.count(old) == 1
new = old
for bd, title in (('POWER', 'Power board'), ('CONTROL', 'Control card')):
    new += ',' + nl + '    [' + nl + '      "%s",' % info['sheets'][bd]['sheet_uuid'] + nl + '      "%s"' % title + nl + '    ]'
t = t.replace(old, new)
open(p, 'w', encoding='utf-8', newline='').write(t)
json.loads(t)
print(p, 'sheets list updated')
