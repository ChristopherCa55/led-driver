# 100 W Common-Anode RGB LED Driver — Design Notes

12–16 V in · 3 × 900 mA constant current · Arduino true-PWM dimming
Target LED: Chanzon 100 W RGB, common anode, Vf R 22–26 V / G,B 33–37 V

---

## 1. Why the circuit looks like this

Three facts about your parts decide the whole architecture, and none of them are negotiable:

**Your input is below your LED.** Red needs 22–26 V, green and blue need 33–37 V, and you have 12–16 V. Every volt has to go *up*, so there is a boost stage no matter what. There is no version of this that is a simple buck.

**The die is common anode.** All three anodes are one pin, so all three colours are forced to sit at the same positive voltage. That kills the obvious approach of three independent boost converters — their outputs would be shorted together and you'd lose per-colour control.

**900 mA on all three is 85 W of light.** At 12 V that is roughly 7.5–8.5 A of input current in a well-built board. This is a real power supply, not a hobby trinket.

Put together, exactly one clean topology survives:

```
12–16 V ──▶ [ BOOST ] ──▶ 44 V rail ──┬──▶ LED anode (common)
                                       │
                       ┌───────────────┴────────────────┐
                    R cathode      G cathode      B cathode
                       │                │               │
                  [CC buck R]     [CC buck G]     [CC buck B]
                       │                │               │
                      GND              GND             GND
```

Stage 1 lifts 12–16 V to a single 44 V rail. The LED's common anode sits on that rail. Stage 2 is three independent step-down constant-current channels that pull each cathode down to ground through an inductor.

The important trick in stage 2 is that **the LED sits in the high side, in series with the inductor**, and the freewheel diode returns to the 44 V rail rather than to ground. That puts the switching MOSFET on the low side with its source at ground, so every gate drive and every current sense in the design is ground-referenced. No bootstrap, no high-side drivers, no level shifting. It also means the LED carries the smooth inductor current continuously rather than chopped switch current, which is why the LED wiring radiates so little.

---

## 2. What was verified in simulation

Everything below is measured from the SPICE model, not estimated. The controller subcircuits used are the same `LEDCOT.sub` / `BOOSTPCM.sub` files the schematic references.

### LED current vs. the LED's full Vf tolerance band

| Corner | Red | Green | Blue |
|---|---|---|---|
| Min Vf (R 22 V, G/B 33 V) | 0.912 A | 0.904 A | 0.904 A |
| Typ Vf (R 24 V, G/B 35 V) | 0.899 A | 0.896 A | 0.896 A |
| Max Vf (R 26 V, G/B 37 V) | 0.885 A | 0.886 A | 0.886 A |

**−1.7 % to +1.3 % across the entire datasheet spread.** That is the payoff from constant-off-time control: ripple is set by `(Vf + Vd) × t_off / L`, which does not care what the rail is doing, so the average current barely moves.

### Input voltage corners, all three channels at 100 %

| Vin | Iin | Pin | Rail | Rail ripple | Boost L peak |
|---|---|---|---|---|---|
| 10.5 V | 8.50 A | 89 W | 43.86 V | 60 mV | 9.9 A |
| 12 V | 7.40 A | 89 W | 43.86 V | 59 mV | 8.9 A |
| 14 V | 6.32 A | 89 W | 43.86 V | 53 mV | 8.0 A |
| 16 V | 5.52 A | 88 W | 43.86 V | 55 mV | 7.3 A |
| 18 V | 4.89 A | 88 W | 43.86 V | 49 mV | 6.7 A |

Those input currents come from an idealised-switch model. **Budget 7.5–8.5 A at 12 V in the real build** once switching and conduction losses are counted, and more like 9 A if your supply sags to 11 V.

### PWM dimming linearity (green channel, worst case)

| PWM duty | measured light | error |
|---|---|---|
| 100 % | 100 % | — |
| 75 % | 74.3 % | −0.7 % |
| 50 % | 48.7 % | −1.3 % |
| 25 % | 23.2 % | −1.8 % |
| 10 % | 10.0 % | 0.0 % |
| 5 % | 4.9 % | −0.1 % |
| 2 % | 1.8 % | −0.2 % |
| 1 % | 0.8 % | −0.2 % |

Usable down to 1 % duty at Arduino's default 490 Hz — about a 200:1 range on plain 8-bit `analogWrite()`. The small shortfall is the inductor current ramping up and down at each PWM edge, and it is why true-PWM keeps colour consistent: all three channels always run at their full 900 mA setpoint when they are on, so hue does not drift as you dim.

### Cross-channel behaviour

R 30 % / G 10 % / B 90 % simultaneously → measured 0.270 A / 0.085 A / 0.801 A, with the 44 V rail moving only 0.28 V. The channels do not fight each other.

---

## 3. Three real problems the simulation caught

These are worth knowing because they are the things that would have made a first PCB spin fail.

**The current comparator trips on its own turn-on spike.** Every time the switching FET closes, the freewheel diode's junction capacitance dumps into the sense resistor and produces a spike far bigger than the 0.34 V trip threshold. Without filtering, the converter simply refuses to start. Fixed with a 220 Ω / 470 pF leading-edge filter (`Rf`/`Cf`) ahead of the comparator on every channel. This is also the single most valuable noise-immunity part in the design — do not delete it to save two components.

**The boost goes subharmonic below about 11.5 V in.** At 10.5 V the duty cycle reaches 0.76, and a peak-current-mode boost above 50 % duty needs slope compensation or it oscillates at half the switching frequency. With too little slope comp the peak inductor current doubled to 26 A. Fixed by setting the compensating ramp roughly equal to the inductor down-slope (`Ksl = 0.13`).

**The boost voltage loop must cross well below its right-half-plane zero.** The RHP zero here lands near 18 kHz. An initially reasonable-looking compensator crossed too close to it and the rail rang at 7 kHz with the inductor current swinging 0–27 A. `R4 = 2.2 k`, `C11 = 220 nF`, `C12 = 4.7 nF` pull the crossover down to roughly 1.5 kHz. Verified stable with ±50 % on R4 and ±2× on C11, so it is not a knife edge.

A useful consequence: because the buck channels regulate current independently, the rail voltage does not need to be accurate. ±2 V of rail movement changes LED current by under 1.5 %. So a slow, heavily damped, rock-stable voltage loop is exactly the right call.

---

## 4. Noise immunity

You asked for this specifically, so it is designed in rather than bolted on.

**On the PWM inputs** — each of the three lines gets a 1 kΩ series resistor into 1 nF to ground (1 µs time constant: transparent to 1 kHz PWM, opaque to switching pickup), a 5.1 V zener to clamp overshoot, a **10 kΩ pull-down so a disconnected wire means LED off** rather than LED randomly on, and then a **74HCT14 Schmitt-trigger buffer**. The 74HCT14 is the key part: TTL thresholds (0.8 V / 2.0 V) with about 0.9 V of hysteresis, so the Arduino ground can bounce around and the driver still sees clean, unambiguous edges. Two inverters per channel restore the polarity.

**On the current sense** — the 220 Ω / 470 pF leading-edge filter described above, on all three channels plus the boost.

**On the switch nodes** — a 100 Ω / 470 pF RC snubber on the boost switch node, and 10 Ω gate resistors everywhere to slow the edges deliberately. Fast edges buy you nothing here and cost you EMI.

**On the input** — a 3 kW TVS, a 15 A fuse, a reverse-polarity P-FET, and 940 µF of low-ESR bulk close to the boost FET.

**Architecturally** — the high-side-LED topology means the LED cables carry smooth inductor current, not chopped switch current. Your four LED wires are not an antenna. That is a structural advantage over a conventional low-side buck here.

**If your Arduino is more than about 30 cm away or shares a noisy ground**, add three optocouplers (6N137 or TLP2361) on the PWM inputs. Leave the footprints on the PCB even if you don't populate them — they cost nothing in layout and save a respin.

---

## 5. Things you must not skip

**The supply.** Spec a **12 V, 10 A (120 W) supply minimum.** At 12 V you will draw 7.5–8.5 A continuously. Use at least 16 AWG for the input wiring and don't run it through a breadboard.

**The heatsink.** 85 W into a die that wants a junction under about 120 °C means the heatsink needs to be roughly **0.5 °C/W or better, which in practice means forced air.** A 100 W LED heatsink-plus-fan assembly is $12–25 and is not optional. Running a 100 W COB LED on a passive sink at full current will kill it.

**Board dissipation.** The PCB itself burns roughly 8 W — mostly the boost FET (~1.5 W), the boost diode (~1.3 W), and the sense resistors (~1.5 W total). Give the boost FET and diode generous copper pours, and consider small clip-on heatsinks.

---

## 6. PCB layout notes

The three things that decide whether this board is quiet or a mess:

1. **Keep the boost hot loop tiny.** The loop formed by the boost FET, the Schottky, and the output ceramics carries 9 A with nanosecond edges. That loop's area is the single largest EMI contributor on the board. Same rule, smaller scale, for each of the three channel loops (FET, freewheel diode, and the local rail decoupling cap).

2. **Split the grounds and join them at one point.** Run a power ground (boost return, all three sense resistors, LED return) and a signal ground (comparators, logic, reference divider). Tie them together at exactly one place — the negative terminal of the input bulk capacitor. Do not let sense-resistor return current share copper with the comparator's reference.

3. **Route each sense resistor as a Kelvin connection.** Take the sense line from the resistor pad itself, not from the ground pour. A few milliohms of shared copper at 8 A is tens of millivolts of error on a 340 mV threshold.

Also: 2 oz copper, 2 layers is fine, keep the reference divider and its 100 nF filter cap right at the comparator pins, and give the LED connector a dedicated ground pin adjacent to the three cathodes.

Realistic board size: about **70 × 90 mm**. Not tiny — the 15 µH/14 A boost inductor alone is a substantial part, and the thermal requirements set a floor on copper area.

---

## 7. Arduino side

```cpp
const int PIN_R = 9, PIN_G = 10, PIN_B = 11;

void setup() {
  pinMode(PIN_R, OUTPUT); pinMode(PIN_G, OUTPUT); pinMode(PIN_B, OUTPUT);
  analogWrite(PIN_R, 0);  analogWrite(PIN_G, 0);  analogWrite(PIN_B, 0);
}

void setColour(uint8_t r, uint8_t g, uint8_t b) {
  analogWrite(PIN_R, r);
  analogWrite(PIN_G, g);
  analogWrite(PIN_B, b);
}
```

Notes:

- Default `analogWrite()` frequency (490 Hz or 980 Hz) is ideal here. Don't raise it — above about 5 kHz the inductor ramp times start to eat the low end of the dimming range.
- **Always start with all three at 0** and ramp up. The board has pull-downs so it fails safe, but don't rely on that during boot.
- The channels are linear in *current*, not in perceived brightness. Apply a gamma of about 2.2 in software if you want smooth-looking fades.
- Green and blue produce far more lumens per amp than red on this die (2000–2400 lm and 300–400 lm vs 1000–1200 lm). White will need heavy per-channel scaling — expect roughly R 100 % / G 35 % / B 90 % as a starting point, then trim by eye.

---

## 8. Bill of materials

Prices are approximate single-unit from a low-cost distributor (LCSC-class). DigiKey/Mouser will run roughly 1.6× these numbers.

### Stage 1 — boost

| Ref | Part | Spec | Qty | ~$ |
|---|---|---|---|---|
| F1 | Fuse + holder | 15 A | 1 | 0.60 |
| Q5 | P-MOSFET | −55 V, ≤25 mΩ (IRF4905) | 1 | 0.70 |
| D6 | Zener | BZX84C12 | 1 | 0.05 |
| D7 | TVS | SMDJ18A, 3 kW | 1 | 0.45 |
| C1, C2 | Electrolytic | 470 µF 25 V low-ESR | 2 | 0.70 |
| C3, C4 | Ceramic | 10 µF 25 V, 100 nF | 2 | 0.13 |
| **L1** | **Inductor** | **15 µH, ≥14 A sat, ≤10 mΩ** | 1 | 3.20 |
| **Q1** | **N-MOSFET** | **100 V, ≤6 mΩ (IRFB4110)** | 1 | 1.60 |
| D1 | Schottky | 100 V 20 A (MBR20100CT) | 1 | 0.70 |
| R1 | Sense | 12 mΩ 3 W 2512 | 1 | 0.35 |
| C5, C6 | Electrolytic | 220 µF 63 V low-ESR, ≥1.4 A ripple | 2 | 1.70 |
| C7–C10 | Ceramic | 4.7 µF 100 V X7R 1210 | 4 | 1.20 |
| **U1** | **Boost controller** | **LM5155DSSR** | 1 | 2.60 |
| — | Passives | feedback, comp, snubber, gate | ~14 | 0.35 |
| | | | | **$14.33** |

### Stage 2 — per channel (×3)

| Ref | Part | Spec | ~$ |
|---|---|---|---|
| Q | N-MOSFET | FQD13N10L, 100 V 135 mΩ logic-level DPAK | 0.55 |
| Dfw | Schottky | SS3H10 / STPS3150, 100–150 V 3 A | 0.18 |
| L | Inductor | 150 µH, ≥1.6 A sat, ≤0.2 Ω | 1.10 |
| Rs | Sense | 0.33 Ω 1 W 2512 1 % | 0.12 |
| U | Comparator | MCP6561R, 47 ns SOT-23-5 | 0.38 |
| — | Gate driver | UCC27517ADBVT | 0.55 |
| — | Logic | 74HC132 (¾ package per channel) | 0.20 |
| — | Passives | LEB filter, off-timer, gate | 0.07 |
| | | **per channel** | **$3.15** |
| | | **× 3** | **$9.45** |

### Shared

| Part | Spec | ~$ |
|---|---|---|
| U5 5 V regulator | MCP1703T-5002 | 0.35 |
| U6 reference | LM4040DIZ-2.5 + divider | 0.45 |
| U7 | 74HCT14 | 0.28 |
| PWM input passives | 3× (1 k, 1 nF, 10 k, 5.1 V zener) | 0.20 |
| Connectors | 2× screw terminal + 4-pin header | 1.40 |
| Misc | decoupling, test points | 0.80 |
| | | **$3.48** |

**Board:** 2-layer, 2 oz, ~70 × 90 mm — about $2/board in a batch of five.

### Total

| | |
|---|---|
| **Driver board BOM** | **≈ $29** |
| Heatsink + fan for the LED | $12–25 |
| 12 V / 10 A supply | $20–30 |

So the **board itself lands right about at your $30 target** if you buy from a low-cost distributor. From DigiKey it's closer to $45. The heatsink and the supply are on top of that and there is no way around either of them.

---

## 9. If you want it smaller or cheaper

Ranked by how much they buy you:

**Drop to 500 mA per colour.** ~65 % of the light for 55 % of the current. Boost inductor drops from 15 µH/14 A to 10 µH/8 A (much smaller and about $1.50 cheaper), the boost FET and diode get cheaper, input current falls to ~4.5 A, board dissipation halves, and the heatsink requirement becomes something a passive sink can actually meet. This is the single biggest win available and I'd push you toward it unless you specifically need maximum output.

**Feed the board 36–48 V instead of 12 V.** This deletes the entire boost stage — about $14 of BOM, the largest and hottest parts, and roughly half the board area. A 48 V/2 A brick is $15. If the 12 V requirement is convenience rather than a hard constraint (a vehicle, a battery), this is by far the cleanest simplification.

**Swap the discrete channel controllers for an integrated part.** A MAX16833 or TPS92515HV-class driver replaces the comparator + latch + one-shot + gate driver with one chip. Costs about $6 more across three channels but removes roughly 30 components and makes assembly much easier. Worth it if this is your first board of this complexity.

**Time-multiplex the colours through one converter.** Tempting — it would collapse four converters into one — but each colour then gets at most ⅓ duty, so peak brightness drops to a third, and the converter has to slew its output between 24 V and 35 V every slot. Mentioned for completeness; not recommended here.

---

## 10. Files

| File | What it is |
|---|---|
| `RGB100W_Driver.asc` | The schematic. Open in LTspice. |
| `LEDCOT.asy` / `LEDCOT.sub` | Channel controller symbol + model. Keep in the same folder. |
| `BOOSTPCM.asy` / `BOOSTPCM.sub` | Boost controller symbol + model. Keep in the same folder. |
| `RGB100W_Driver_sim.net` | Plain-SPICE twin, verified in ngspice. Fast to sweep. |

**All five files must sit in one folder** — LTspice looks for `.asy` symbols next to the schematic.

To run: open `RGB100W_Driver.asc`, hit run, and probe `I(D_R)`, `I(D_G)`, `I(D_B)` — each should settle at 900 mA — and `V(rail)`, which should sit at about 44 V.

The two controller blocks are behavioural models of circuits you build from real parts. `LEDCOT.sub` documents the mapping in its header: MCP6561 comparator, 74HC132 cross-coupled NAND latch, third 74HC132 gate as the one-shot Schmitt, 2N7002 discharge FET, UCC27517 gate driver. `BOOSTPCM.sub` stands in for an LM5155. Both are written as plain SPICE so you can read exactly what they do, and both simulate without downloading any vendor models. When you want to check a specific vendor part, drop its model in and replace the block.

### To sweep the design

In `RGB100W_Driver_sim.net`, edit the `.param` line:

- `VIN` — input voltage (10.5 to 18 tested)
- `DR`, `DG`, `DB` — PWM duty per channel, 0 to 1
- `TP` — PWM period (1m = 1 kHz)
- `RTGB`, `RTR` — off-time resistors; these set ripple and switching frequency
- `VREF` — the 0.340 V current setpoint. LED current scales directly with it: `I ≈ VREF/0.33 − ripple/2`

Then `ngspice -b RGB100W_Driver_sim.net`.
