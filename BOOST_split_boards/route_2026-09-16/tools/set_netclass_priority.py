"""Make a .kicad_pro state what KiCad 10 enforces (2026-09-24, the user's confirmation of that day).

usage: python set_netclass_priority.py FILE.kicad_pro [...]

KiCad 10 expects a `priority` on every netclass. Without one it ignores the file's Default class and applies its
built-in 0.20 / 0.20, so the shipped "Default 0.15 / 0.15" was never what DRC checked. This sets Default to
0.20 / 0.20 and gives every class a priority: the named classes in file order from 0, Default last (2147483647),
the same fix as BOOST_control.kicad_pro on 2026-09-23. Nothing else in the file changes. Back the file up first.
"""
import json, sys

for path in sys.argv[1:]:
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    rank = 0
    for c in d['net_settings']['classes']:
        if c['name'] == 'Default':
            c['clearance'] = 0.2
            c['track_width'] = 0.2
            c['priority'] = 2147483647
        else:
            c['priority'] = rank
            rank += 1
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(d, indent=2) + '\n')
    print(path, [(c['name'], c['clearance'], c['priority']) for c in d['net_settings']['classes']])
