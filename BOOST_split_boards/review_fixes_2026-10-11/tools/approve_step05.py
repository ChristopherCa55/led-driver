"""Add the user-approved step-5 circuit changes (2026-10-11, D1 / D2) to
ltspice_layout_handoff_2026-10-05/tools/approved_changes.json. Backs it up first to
previous/2026-10-11/before_step05_approvals/. Refuses if any of these entries is already there.

    python approve_step05.py
"""
import json, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
BSB = os.path.normpath(os.path.join(HERE, '..', '..'))
P = os.path.join(BSB, 'ltspice_layout_handoff_2026-10-05', 'tools', 'approved_changes.json')
BK = os.path.join(BSB, 'previous', '2026-10-11', 'before_step05_approvals')

a = json.load(open(P))
for k in ('R99', 'R102'):
    if k in a.get('value_changes', {}):
        raise SystemExit('%s already in value_changes: not changed' % k)
if set(a.get('added_elements', [])) & {'R106', 'R107'}:
    raise SystemExit('R106/R107 already in added_elements: not changed')
os.makedirs(BK, exist_ok=False)
shutil.copy2(P, BK)
a.setdefault('value_changes', {}).update({'R99': ['10k', '1k'], 'R102': ['10k', '1k']})
a['added_elements'] = a.get('added_elements', []) + ['R106', 'R107']
a['_review_fixes_note_step05'] = (
    "2026-10-11, user's own words: 'Yes, you can add the pullups to the control card.' (R106 SCL, R107 SDA, 4.7k to "
    "5V; the MCP4451 has no internal pull-ups) and 'you can change the r99 and r102 to 1k if you think that is better' "
    "(U26 A1 / A0 to GND, so the address cannot latch high: 0x2C).")
json.dump(a, open(P, 'w'), indent=1)
print('approved_changes.json updated (backup in %s): R99/R102 10k->1k, added R106/R107' % BK)
