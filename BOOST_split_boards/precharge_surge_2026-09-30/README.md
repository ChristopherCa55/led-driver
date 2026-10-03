# Pre-charge diode surge headroom and the bigger-diode fit check (2026-09-30)

The user asked whether D28-D30 (Jingdao S2MW, SOD-123FL, IFSM 50 A for 8.3 ms) should become 100 A surge parts.
Nothing in the design was changed. The study is recorded here. **Decision (2026-09-30): the user kept the S2MW.**

## Surge headroom of the S2MW as fitted (`headroom_results.txt`)

The simulated battery hot-plug is 16.8 V through a 12 mOhm, 0.8 uH cable, with every bank empty
(`sim_nets/S2MW_*`, the 2026-09-29 runs). These are the D30 currents; D28 and D29 are lower in reality, because
their feed tracks were not modelled:

| Battery resistance | Peak | Width above 50 % | I^2t | Temperature-rise headroom | Current headroom |
|---|---|---|---|---|---|
| 0 mOhm (ideal) | 98.5 A | 122 us | 0.89 A^2s | 2.5x | 1.75x (172 A) |
| 10 mOhm | 73.9 A | 133 us | 0.55 A^2s | 4.0x | 2.3x |
| 40 mOhm | 41.0 A | 195 us | 0.25 A^2s | 8.9x | 4.1x |

**Method (`tools/headroom.py`).**
- The junction temperature rise is computed by superposition, with a power-law thermal impedance Z = k t^n. Power is
  VF(I) x I, using the simulation's diode model.
- The headroom is the peak temperature rise of the rated pulse (a 50 A, 8.33 ms half sine) divided by that of the
  simulated pulse. The current factor is how far the simulated waveform could be scaled up before it matches the
  rated pulse.
- n is calibrated on Wild Goose S2MF, a 2 A, 1000 V SMAF part with the same 50 A / 8.3 ms rating, whose data sheet
  also gives 100 A for a 1 ms half sine (and I^2t 10.4 A^2s). The fit gives n = 0.499, which is pure 1-D diffusion.
  With n = 0.25 the ideal-battery headroom would fall to 1.0x; that exponent contradicts the S2MF figures, so it is
  only a pessimistic bound.
- The simple I^2t ratio (11.7x at 0 mOhm) overstates the headroom. A 0.1 ms pulse heats the die before the heat can
  spread.

**Caveats, all UNVERIFIED:**
- The S2MW data sheet has no short-pulse figure; the calibration borrows the sister part's.
- IFSM is a non-repetitive rating, but this surge recurs at every battery connection.
- The rating starts from a hot junction ("superimposed on rated load"), whereas power-up starts cold. That adds margin
  not counted above.

## A bigger part does not lower the surge (`surge_results.txt`)

An RS3MF-like 3 A die model (`sim_nets/RS3MF_*`) gives 100.6-102.3 A at 0 mOhm and 75 A at 10 mOhm, the same as the
S2MW. The current is set by the battery, cable and capacitors.

## Bigger parts that fit (`fit_results.txt`, `tools/fit_search.py`, `tools/blockers.py`)

The rules checked:
- clearances against other-net copper on B.Cu (GND fill may be cut);
- pads at least 0.3 mm from the board edge;
- courtyards clear of other courtyards, the rule areas, and the J1/J2 M4 nut + DIN 125 washer (more than 4.6 mm from
  the bolt centre);
- each pad touching its own net's present copper.

The present SOD-123F placements pass, as a check of the search.

**Candidate parts (data sheets read 2026-09-30):**
- Shikues RS3MF (C719383): SMAF, 100 A / 8.3 ms. It is the only SMAF part rated at least 100 A.
- MCC S3MB-TP (C668988): SMB, 100 A / 8.3 ms, 200 A / 1 ms square, 150 A repetitive (300 us).
- Jingdao S5MB (C437687): SMB, 200 A.
- Shikues S5MBF (C475748): SMBF, 150 A.

**Fit by site:**
- **D29:** SMAF fits with a 0.5 mm shift. SMB fits only at the clearance limit.
- **D28:** SMAF fits only rotated 90 degrees and moved 1.7 mm over the Output2_drain track. It then needs a new
  via-in-pad down to In3 Vout_1 and a short Vin stub.
- **D30:** nothing larger fits. The site is boxed in by J1's washer, M4's courtyard and the GATE_M4 vias at
  (101.65, 88.05) and (103.10, 92.90). It is also the only place where Vin and Vout_3 come close
  (`tools/alt_sites2.py`). A larger D30 would need M4's gate path (R73 / R47 links) re-routed on F.Cu and B.Cu,
  right beside J1's Vin pour and the m4_source copper.
