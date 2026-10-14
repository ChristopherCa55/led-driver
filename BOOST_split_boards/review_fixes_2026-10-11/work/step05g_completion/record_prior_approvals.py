"""Record the October 12 decisions already quoted in HANDOFF_2026-10-12.md.
Back up both existing records first; refuse if the approval record changed.
This does not approve step 5g's picture or promote any design files.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RF = HERE.parent.parent
BSB = RF.parent
approval = BSB / 'ltspice_layout_handoff_2026-10-05/tools/approved_changes.json'
answers = RF / 'ANSWERS.md'
raw = approval.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'd498423d24e16f23152ac96e1a043528282d745090f2e51c74d9383c0d125ca7'
answers_raw = answers.read_bytes()
backup = BSB / 'previous/2026-10-12/before_step05g_completion_records'
backup.mkdir(parents=True, exist_ok=False)
(backup / approval.name).write_bytes(raw)
(backup / answers.name).write_bytes(answers_raw)
data = json.loads(raw)
old = '.options gmin=100f reltol=0.001'
assert old not in data['directive_changes']
data['directive_changes'][old] = old + ' solver=alt'
data['_review_fixes_note_solver_alt'] = (
    "2026-10-12, user's words recorded in HANDOFF_2026-10-12.md section 5.2: "
    "'Everything else looks fine - i approve them.' The handoff explicitly lists "
    "LTspice solver=alt among those approvals. This records that existing approval; "
    "the step05g physical placement still needs picture approval.")
newline = '\r\n' if b'\r\n' in raw else '\n'
encoded = (json.dumps(data, indent=1, ensure_ascii=False) + '\n').replace('\n', newline).encode('utf-8')
assert approval.read_bytes() == raw
approval.write_bytes(encoded)
addition = '''

## 2026-10-12 decisions carried forward from the handoff

Source: `HANDOFF_2026-10-12.md`, section 5.2. Recorded during the pull-up continuation.

> Ok, the vin/out labels are good. Can you retry placing the i2c pullups using the same resistor size as all the other
> resistors. To me it seems like there is plenty of space near the input pins. There are 5V vias which you should be
> able to connect to at around 58.5, 92.5, and 55.8, 94.3. You can also just add a via, and connect it to the in2 plane
> instead of using the different resistor size. Everything else looks fine - i approve them. You do not need to rename
> the nets in ltspice. For now, do not do the other power board reroutes. For the card's longest ground splitting
> tracks, just place them in the location that would affect other stuff the least (keep other things as intact as
> possible). Yes, I would like you to regenerate all the files like the gerbers, drill, fab, bom etc...

The handoff also records the choices "Shrink J9's courtyard (Recommended)" and, for the remaining loop vias,
"Can you give a cost / benefit for doing this for each of the via locations?"

- Approved: Vin/output labels, 0603 pull-up retry near J9, shrinking J9's front courtyard (back unchanged),
  R99/R102 = 1k, LTspice `solver=alt`, card steps 7 and 8, and full output regeneration after the design is settled.
- Card long GND-splitting tracks: minimise disruption to other routing.
- Remaining power loop vias: analysis per location only, not permission to apply them.
- No LTspice net renames and no other power-board reroutes for now.
- Step 5g's precise placement and associated text/via moves still await picture approval.
- The user's saved U26D move is present in step05g; the promotion log has not yet been reconciled.

The `solver=alt` approval is now recorded in `approved_changes.json`; backup:
`previous/2026-10-12/before_step05g_completion_records/`.
'''
ans_newline = '\r\n' if b'\r\n' in answers_raw else '\n'
assert answers.read_bytes() == answers_raw
answers.write_bytes(answers_raw + addition.replace('\n', ans_newline).encode('utf-8'))
print('Recorded prior October 12 decisions and solver=alt; placement approval remains pending.')
print('approved_changes.json SHA256', hashlib.sha256(encoded).hexdigest())
print('Backup:', backup)
