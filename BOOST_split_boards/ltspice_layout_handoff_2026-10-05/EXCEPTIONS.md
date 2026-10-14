# Exceptions

A rule in LAYOUT_RULES.md that makes a genuinely better layout impossible can be waived, but **only with the user's
OK at a check-in**. Add one row per exception before asking. The checker is not changed; the exception is reported
next to its failing line.

| # | Rule | Where (block, parts, coordinates) | Why the rule hurts here | What you drew instead | Capture | User's answer |
|---|---|---|---|---|---|---|
| 1 | H10 matching copies: the `flip_ok` list (only R23, R49, R59, R74) | REF2: C38; EA2: C36; EA3: C37; channel-2 driver: C90. Not drawn yet; channels 2 and 3 come after check-in 1 | Each of these caps is netlisted with its pin 1 on the opposite net to its channel-1 twin: `C38 0 analog_5V` vs `C32 analog_5V 0`; `C36 0 analog_5V`, `C37 0 analog_5V` vs `C66 analog_5V 0`; `C90 5V 0` vs `C62 0 5V`. E1 compares pins by position, so these caps must be drawn turned 180° to stay electrically identical. H10 then reports a different rotation, origin and text window for each one, exactly as it would for R23/R49/R59/R74 without the `flip_ok` list. | Each one drawn R180, with its body on exactly the same box as its twin and its name and value in the same place on screen, so the copies look identical. Request: judge them like the `flip_ok` resistors (body centres compared) | To follow once channels 2 and 3 are drawn (the pilot holds channel 1 only) | |
