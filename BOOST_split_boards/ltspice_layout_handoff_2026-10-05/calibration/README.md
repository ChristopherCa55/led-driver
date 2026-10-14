# Calibration (2026-10-05)

Both checkers were run on the frozen original and on the failed 2026-10-05 attempt. A layout that passes them must
look nothing like that attempt. **If a future checker run passes the attempt's layout, the checker is broken.**

## Electrical (`ltspice_equiv.py`)

| File | Result |
|---|---|
| `equiv_original.txt` (original vs itself) | **PASS**: 302 elements, 152 nets, 18 directive texts, 6 comments |
| `equiv_reorg_attempt.txt` | E1 PASS (the same circuit); **E3 FAIL**: the user's note "I added a lot of capacitors…" was deleted |
| `selftest_equiv.txt` | 6/6: approved renames pass; a reversed resistor, a renamed label, a deleted comment, a changed value and a renamed 5V rail each fail on the right check |

## Layout (`asc_layout_check.py --no-frames`)

| Measure | Original | 10-05 attempt |
|---|---|---|
| H3 separate drawings inside PWR | 1 (wired) | **16** |
| H3b orphan parts | 1 (C54) | **30** (L1, M1, D19, the 220 µF caps, U18, U28 …) |
| H4 signal nets split by labels inside a block | 7 | **29** |
| H5 power-path nets in pieces | ground only (19 pieces) | Vin 6, rsense_lo 2, LX 7, Vout_2 7, ground 20 |
| H9 estimated text problems | 926 | 948 |
| Traces within budget | 8 / 10 (T1 needs a wired ground return; T4 uses 3 labels) | **1 / 10** (T1 needs 13 label jumps) |
| Label instances, signal nets | 139 | 243 |

The original fails mostly on crowding (H9, H8), its bypass caps placed away from their ICs (H12), and its missing
frames. That is exactly what the user wants fixed. The attempt additionally fails everything that measures "drawn as
one connected circuit".

## Text-size calibration (H9)

`ltspice_capture.py` was tested with the user's permission. LTspice opened temporary cropped copies, drew them, and
the window was captured:

- `ltspice_captures/orig_battery_R1.png`: the battery, R1, L1 and M1 area of the original. Overlapping text is
  visible: "S1 rsense_lo", "SIM_LCABLE / CSS4J_4026", "C69 680µ680µ680µ".
- `ltspice_captures/orig_EA1.png`: the channel-1 error amplifier of the original.
- `ltspice_captures/orig_frame_mode_test.png`: the block-frame mode on a temporary copy with a `[TEST]` frame. The
  dashed frame and its title are drawn.

**Measured on `orig_EA1.png`** (2.12 px per schematic unit, from R2's pins at x = 944 and 1024):

- **Size-2 text:** cap height ≈ 19 units, about 13–14 units per character (e.g. "Voltage_err_1" ≈ 170 units).
- **The checker's model:** height 16 × 1.5 = 24 units, 0.6 × height = 14.4 units per character.
- **R2's InstName box:** predicted centred at x = 984, y = 312…336. The capture shows the glyphs at x ≈ 984,
  y ≈ 313…332.

So the H9 estimate is close enough to use, but every H9 finding must still be confirmed in a capture.
