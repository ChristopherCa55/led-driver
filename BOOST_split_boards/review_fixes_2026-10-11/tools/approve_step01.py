"""Add the user-approved step-1 changes (2026-10-11) to ltspice_layout_handoff_2026-10-05/tools/approved_changes.json.
Backed up first to previous/2026-10-11/before_equiv_approved_changes/. Idempotent: refuses if the keys exist.

    python approve_step01.py
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.normpath(os.path.join(HERE, '..', '..', 'ltspice_layout_handoff_2026-10-05', 'tools', 'approved_changes.json'))
from step01_ltspice import PARTS

a = json.load(open(P))
for k in ('directive_changes', 'removed_comments', 'added_directives', 'value_changes'):
    if k in a:
        raise SystemExit('%s already present: not changed' % k)
a['directive_changes'] = {'.ic V(Out)=0 V(Out-)=1 V(C10)=0 V(C5)=0 V(C2)=0': '.ic V(Out)=0 V(Out-)=1'}
a['removed_comments'] = ['.ic V(Vout_1)=30 V(Vout_2)=38 V(Vout_3)=30']
a['added_directives'] = ["* diode part names: LTspice's default diode, as before\\n.model 1N4148W D\\n.model B5819W D\\n"
                         ".model BAV21W D\\n.model BAT54WS D"]
a['value_changes'] = {d: ['D', p] for p, ds in PARTS.items() for d in ds}
a['_review_fixes_note'] = (
    "2026-10-11, user's own words: 'you can remove the .ic lines that are not used anymore' (V(C10), V(C5), V(C2) "
    "name no node; the run without them is bit-identical) and, for the diode values, 'in the ltspice it just says D "
    "under the name Dxx, where I feel like it should say the actual name of the diode' (each name is a .model alias "
    "of LTspice's default diode, so the simulation is unchanged).")
json.dump(a, open(P, 'w'), indent=1)
print('approved_changes.json updated:', len(a['value_changes']), 'value changes, 1 directive change, 1 added directive,'
      ' 1 removed comment')
