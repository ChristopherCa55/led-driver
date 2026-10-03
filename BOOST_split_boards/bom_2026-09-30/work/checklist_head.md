# BOOST order checklist, scenario A (updated 2026-10-01)

Two JLCPCB orders (power: 5 PCBs, 2 assembled; card: 5 panels, 2 assembled), plus four small orders elsewhere.
**Total $663.24 with the McMaster pad** (shipping and tax not included). Every price is read, except the two Farnell
UK prices converted from GBP (marked "GBP").

**Since 2026-09-25 ($760.83):**
- the control card is 6 layers with 0.5 oz inner copper ($56.83 instead of $137.04);
- the pre-charge diodes D28-D30 (S2MW) are on the power board;
- the savings you approved on 2026-10-01 are in the design files and the BOM:
  - EEH-ZS1H221P on six of the 220 uF positions;
  - the card's 0.5 oz inner copper;
  - TLV9001 op-amps.
- JLC stock and prices were read again on 2026-10-01.

## Before you order

- [ ] **Decide the 12 V regulator U16** (COST_SUMMARY "Ways to save"). The BOM in this folder still has LM2940S-12/NOPB
      (C2877347), with only 2 in stock. The SOT-223 swap (UTC LM2940G-12-AA3-R or TI LM2940IMPX-12) changes the
      power board, so the gerbers, BOM and CPL get regenerated after you choose.
- [x] **The design files:** schematic rev6 plus D28-D30 and the 2026-10-01 changes, the 8-layer power board and the
      6-layer card, all in `BOOST_package/KiCad/`. The gerbers, BOM and CPL in this folder match them.
- [ ] **Stock**, on JLC's BOM page after upload (2026-10-01 values in brackets).
  - LM2940S-12/NOPB C2877347: need 2 (2), until the regulator is decided
  - EEH-ZU1E681UP C29664285: need 6 (10)
  - EEH-ZU1H221P C6843593: need 6 (14)
  - EEH-ZS1H221P C385885: need 12 (1263)
  - TLV9001IDBVR C398363: need 18 (48438)
  - MCP4451-103E/ST C145613: need 2 (40)
  - TR3D476K025C0250 C4979367: need 2 (63)
  - CD74HC4066M96 C179842: need 2 (73)
- [ ] Optional: read the TG-AD30 price (URL at the bottom). If a 1.5 mm sheet of 150 x 150 mm or less costs about
      $40 or less, buy it instead of the McMaster pad.
