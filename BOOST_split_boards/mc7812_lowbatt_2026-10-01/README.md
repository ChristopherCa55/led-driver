# U16 = MC7812: low-battery simulations (2026-10-01)

The user is leaning towards the onsemi MC7812BD2TR4G (C231294) for U16 instead of the LM2940S-12, and asked for a
simulation of the low-battery case. Nothing in the shipped folders was changed.

## Set-up
- `sim/` is a copy of `BOOST_package/LTspice/` (BOOST.asc sha 99d0b375, the current design with TLV9001), netlisted with
  `LTspice -netlist`. `tools/make_cases.py` builds each case from `sim/BOOST.net`:
  - U16 model: `LM2940_12` (unchanged) or `MC7812_TYP` / `MC7812_WC` from `sim/MC7812.lib`;
  - battery: `SIM_VBATT` (open-circuit voltage, constant or PWL) + `SIM_RPACK` (pack resistance) + the existing
    12 mOhm `SIM_RCABLE`;
  - `SIM_ARDLOAD` 120 ohm on 12V: the Arduino buck, 0.1 A at 12 V (not in BOOST.asc);
  - a `.save` list (12 V rail, U21 output N013, M1_INHIBIT, the high-side driver supplies, battery nodes) and new
    `.meas` lines. Full brightness (IREF duty 256), the `.ic` settled start.
- `sim/MC7812.lib` (behavioural, NOT an onsemi model), from the onsemi MC7800/D data sheet:
  - 12.00 V; bias 3.4 mA (TYP) / 8 mA (WC); load current drawn from IN.
  - Dropout: TYP 1.45 V + 0.55 ohm x Iout (figure 14: about 1.5 V at 20 mA, 1.6 V at 200 mA, 2.0 V at 1 A, 25 C).
    WC 1.95 V + 0.55 ohm x Iout is an ASSUMPTION; the data sheet gives no maximum.
  - Bench check (`sim/bench_mc7812.net`): 12 V in, 0.1 A out -> TYP 10.51 V, WC 10.02 V, LM2940 model 11.91 V.
- U21 (from the netlist): + input = 5V x R85 / (R82 + R85), with R86 1 M hysteresis from the output; - input =
  12V x R83 / (R83 + R84). M1 stops when the 12 V rail falls to 9.77 V and restarts at 10.32 V. Worst case
  (5 V rail +5 %, 1 % resistors, 10 mV offset) the stop point is about 10.8 V.
- `tools/analyze.py` tabulates each run in 2 ms windows; `tools/plot_runs.py` and `tools/brightness_chart.py` plot.

## Runs (`sim/runs.txt`; all exit 0)
| Case | U16 | Battery | Result |
|---|---|---|---|
| A | MC7812 TYP | 12.0 V stiff | full brightness (2.635/2.371/2.371 A); 12 V rail 10.21 V; high-side driver supplies >= 8.93 V; LX 60.7 V |
| B | MC7812 WC | 12.0 V stiff | never starts: the rail sits at 10.00 V, under the 10.32 V restart point |
| C | MC7812 TYP | 13.0 -> 11.8 V, 50 mOhm | full to 12.7 V, then fades: ~50 % at 12.1 V, ~15 % at 11.8 V |
| D | LM2940 | 13.0 -> 11.8 V, 50 mOhm | full brightness throughout |
| E | MC7812 TYP | 12.3 -> 11.1 V, 10 mOhm | full to 11.9 V, a short chop at 11.8 V, then cleanly off from 11.7 V |
| F | MC7812 WC | 13.5 -> 12.3 V, 50 mOhm | as C, about 0.45 V higher: fades from 13.1 V |
| G | MC7812 TYP | 12.3 V hold, 50 mOhm | steady: LEDs 85/52/52 %, U21 holds M1 off ~51 %, ~4 kHz, supplies >= 8.53 V, LX 60.8 V |
| H | LM2940 | 11.8 -> 10.6 V, 50 mOhm | the same fade, from 11.3 V |
| I | MC7812 TYP | 11.85 V hold, 50 mOhm | steady: LEDs 32/14/19 %, M1 off 84 %, ~2.5 kHz, supplies 7.93 V, LX 60.9 V |

Voltages are the battery's open-circuit voltage. The ramps fall at about 50 V/s, far faster than a real discharge;
the hold runs G and I confirm the steady behaviour.

## Findings
- With a 4S battery above its last few percent the MC7812 behaves like the LM2940: full brightness, no new
  stresses. The 12 V rail sits about 1.5 V lower once the battery is under about 13.5 V.
- End of discharge with a pack that sags (50 mOhm): no visible blinking. U21 stops and restarts M1 at 2-4 kHz, so
  the LEDs fade smoothly as the battery falls. The LM2940 does the same about 1.4 V lower. Red holds up better than
  green and blue during the fade, so mixed colours drift towards red.
- With a stiff pack (10 mOhm, LiPo-like) there is no fade: full brightness, then a clean, latched off.
- Re-start needs the 12 V rail above 10.32 V: about 11.8 V open-circuit (TYP), 12.3 V (WC).
- Deep in the fade (M1 off over 80 % of the time) the high-side driver supplies sag to 7.4-7.9 V, at the model's
  simple 8 V UVLO. LX never exceeded 61.2 V and nothing ran away. The real UCC21520 thresholds have tolerance;
  the same region exists with the LM2940, lower down.
- The user's Arduino buck sees about 9.7-10.2 V near the end (BUILD_NOTES asks for 11-13 V regulation).

Not modelled: the MC7812's transient response and current limit; a battery whose voltage recovers with time
constants; temperature effects on the dropout (hot parts drop about 0.2-0.3 V less).

## Applied (2026-10-01, the user's OK)
`tools/apply_u16_mc7812.py` with `release/` (MC7812.asy, MC7812.lib) was tried on `work/trial/` first: ERC clean, DRC
with parity unchanged (49 expected warnings), every power-board gerber identical, and a 30 ms LTspice run at 14 V gave
2.6348 / 2.3713 / 2.3713 A, 23.30 / 33.13 / 33.11 V, LX 60.4 V (25-30 ms), 12 V rail 12.000 V. It was then applied to
BOOST_schematic_cleanup, BOOST_package and BOOST_stuff (identical results). The BOM side is recorded in
`../bom_2026-09-30/README.md`.
