# Metrics, baseline against the copy (review fixes, as of 2026-10-13)

Built from `METRICS.md` (`tools/collect.py`). The copy's design files are byte-identical to step 10's (card = steps
5g, 7e, 8c, 9; power = steps 3, 4, 6b, 10). **(worse)** = worse than the baseline beyond its tolerance; every such row
is listed with who accepted it in FIX_REPORT.md. Rises are IPC-2221 figures, reported, not judged, for necks under
about 5 mm and plane-connected vias.

| Metric | unit / better | baseline | the copy now (step 10) |
|---|---|---|---|
| erc_BOOST | ERC, low | 0 | 0 |
| erc_BOOST_power_RC2 | ERC, low | 0 | 0 |
| erc_BOOST_control_RC2 | ERC, low | 0 | 0 |
| drc_power_err | DRC, low | 0 | 0 |
| drc_power_warn | DRC, low | 49 | 49 |
| drc_power_unc | DRC, low | 0 | 0 |
| drc_power_parity | DRC, low | 0 | 0 |
| drc_card_err | DRC, low | 0 | 0 |
| drc_card_warn | DRC, low | 1 | 1 |
| drc_card_unc | DRC, low | 0 | 0 |
| drc_card_parity | DRC, low | 0 | 0 |
| sync | sync, low | 0 | 0 |
| lt_equiv | , eq | PASS |  |
| br|Vin J1->R1 (DC)|R | R mOhm, low | 1.031 | 1.003 |
| br|Vin J1->R1 (DC)|neck | rise C, low | 38.8 | 29.3 |
| br|Vin J1->R1 (DC)|necklen | neck length mm (info), info | 4.1 | 5.1 |
| br|Vin J1->R1 (DC)|long | rise C, low | 38.8 | 29.3 |
| br|Vin J1->R1 (DC)|over | vias over, low | 4 | 5 **(worse)** |
| br|Vin J1->R1 (DC)|worst | worst via x, low | 1.59 | 1.39 |
| br|Vin caps->R1 (ripple)|R | R mOhm, low | 0.367 | 0.344 |
| br|Vin caps->R1 (ripple)|neck | rise C, low | 9.2 | 6.7 |
| br|Vin caps->R1 (ripple)|necklen | neck length mm (info), info | 3.8 | 5.2 |
| br|Vin caps->R1 (ripple)|long | rise C, low | 9.2 | 6.7 |
| br|Vin caps->R1 (ripple)|over | vias over, low | 0 | 0 |
| br|Vin caps->R1 (ripple)|worst | worst via x, low | 0.82 | 0.72 |
| br|rsense_lo R1->L1|R | R mOhm, low | 0.229 | 0.229 |
| br|rsense_lo R1->L1|neck | rise C, low | 24.1 | 24.1 |
| br|rsense_lo R1->L1|necklen | neck length mm (info), info | 7 | 7 |
| br|rsense_lo R1->L1|long | rise C, low | 24.1 | 24.1 |
| br|rsense_lo R1->L1|over | vias over, low | 7 | 7 |
| br|rsense_lo R1->L1|worst | worst via x, low | 1.34 | 1.34 |
| br|LX L1->M1|R | R mOhm, low | 0.473 | 0.472 |
| br|LX L1->M1|neck | rise C, low | 30.5 | 30.5 |
| br|LX L1->M1|necklen | neck length mm (info), info | 2.2 | 2 |
| br|LX L1->M1|long | rise C, low | 30.5 | 30.5 |
| br|LX L1->M1|over | vias over, low | 0 | 0 |
| br|LX L1->M1|worst | worst via x, low | 0.72 | 0.72 |
| br|LX L1->M7|R | R mOhm, low | 0.451 | 0.45 |
| br|LX L1->M7|neck | rise C, low | 9.5 | 9.5 |
| br|LX L1->M7|necklen | neck length mm (info), info | 1.6 | 1.6 |
| br|LX L1->M7|long | rise C, low | 5.1 | 5.1 |
| br|LX L1->M7|over | vias over, low | 0 | 0 |
| br|LX L1->M7|worst | worst via x, low | 0.5 | 0.5 |
| br|LX L1->M6|R | R mOhm, low | 0.732 | 0.732 |
| br|LX L1->M6|neck | rise C, low | 19.4 | 19.4 |
| br|LX L1->M6|necklen | neck length mm (info), info | 5.2 | 5.2 |
| br|LX L1->M6|long | rise C, low | 19.4 | 19.4 |
| br|LX L1->M6|over | vias over, low | 0 | 0 |
| br|LX L1->M6|worst | worst via x, low | 0.68 | 0.68 |
| br|LX L1->M5|R | R mOhm, low | 1.969 | 1.978 **(worse)** |
| br|LX L1->M5|neck | rise C, low | 56.7 | 55.8 |
| br|LX L1->M5|necklen | neck length mm (info), info | 1.3 | 1.3 |
| br|LX L1->M5|long | rise C, low | 25.8 | 30.3 **(worse)** |
| br|LX L1->M5|over | vias over, low | 0 | 0 |
| br|LX L1->M5|worst | worst via x, low | 0.57 | 0.58 |
| br|m2_source M7->M2|R | R mOhm, low | 0.039 | 0.039 |
| br|m2_source M7->M2|neck | rise C, low | 4.1 | 4.1 |
| br|m2_source M7->M2|necklen | neck length mm (info), info | 0 | 0 |
| br|m2_source M7->M2|long | rise C, low | 0 | 0 |
| br|m2_source M7->M2|over | vias over, low | 0 | 0 |
| br|m2_source M7->M2|worst | worst via x, low | 0 | 0 |
| br|m3_source M6->M3|R | R mOhm, low | 0.041 | 0.041 |
| br|m3_source M6->M3|neck | rise C, low | 5.7 | 5.7 |
| br|m3_source M6->M3|necklen | neck length mm (info), info | 0 | 0 |
| br|m3_source M6->M3|long | rise C, low | 0 | 0 |
| br|m3_source M6->M3|over | vias over, low | 0 | 0 |
| br|m3_source M6->M3|worst | worst via x, low | 0 | 0 |
| br|m4_source M5->M4|R | R mOhm, low | 0.041 | 0.041 |
| br|m4_source M5->M4|neck | rise C, low | 8.6 | 8.6 |
| br|m4_source M5->M4|necklen | neck length mm (info), info | 0 | 0 |
| br|m4_source M5->M4|long | rise C, low | 0 | 0 |
| br|m4_source M5->M4|over | vias over, low | 0 | 0 |
| br|m4_source M5->M4|worst | worst via x, low | 0 | 0 |
| br|Vout_1 M2->bank+J3|R | R mOhm, low | 0.219 | 0.219 |
| br|Vout_1 M2->bank+J3|neck | rise C, low | 17.4 | 17.4 |
| br|Vout_1 M2->bank+J3|necklen | neck length mm (info), info | 0.1 | 0.1 |
| br|Vout_1 M2->bank+J3|long | rise C, low | 5.2 | 5.2 |
| br|Vout_1 M2->bank+J3|over | vias over, low | 0 | 0 |
| br|Vout_1 M2->bank+J3|worst | worst via x, low | 0.8 | 0.8 |
| br|Vout_2 M3->bank+J8|R | R mOhm, low | 0.312 | 0.315 |
| br|Vout_2 M3->bank+J8|neck | rise C, low | 9.4 | 9.5 |
| br|Vout_2 M3->bank+J8|necklen | neck length mm (info), info | 0.9 | 0.9 |
| br|Vout_2 M3->bank+J8|long | rise C, low | 5.8 | 6 |
| br|Vout_2 M3->bank+J8|over | vias over, low | 0 | 0 |
| br|Vout_2 M3->bank+J8|worst | worst via x, low | 0.39 | 0.36 |
| br|Vout_3 M4->bank+J5|R | R mOhm, low | 0.121 | 0.118 |
| br|Vout_3 M4->bank+J5|neck | rise C, low | 4.8 | 4.9 |
| br|Vout_3 M4->bank+J5|necklen | neck length mm (info), info | 1.2 | 1.2 |
| br|Vout_3 M4->bank+J5|long | rise C, low | 1.8 | 2 |
| br|Vout_3 M4->bank+J5|over | vias over, low | 0 | 0 |
| br|Vout_3 M4->bank+J5|worst | worst via x, low | 0.5 | 0.36 |
| br|Vout_1 M2->J3 (LED DC)|R | R mOhm, low | 8.459 | 8.459 |
| br|Vout_1 M2->J3 (LED DC)|neck | rise C, low | 17.7 | 17.7 |
| br|Vout_1 M2->J3 (LED DC)|necklen | neck length mm (info), info | 2.8 | 2.8 |
| br|Vout_1 M2->J3 (LED DC)|long | rise C, low | 17.7 | 17.7 |
| br|Vout_1 M2->J3 (LED DC)|over | vias over, low | 0 | 0 |
| br|Vout_1 M2->J3 (LED DC)|worst | worst via x, low | 0.39 | 0.39 |
| br|Vout_2 M3->J8 (LED DC)|R | R mOhm, low | 3.077 | 3.082 |
| br|Vout_2 M3->J8 (LED DC)|neck | rise C, low | 5.4 | 5.4 |
| br|Vout_2 M3->J8 (LED DC)|necklen | neck length mm (info), info | 5.6 | 5.6 |
| br|Vout_2 M3->J8 (LED DC)|long | rise C, low | 5.4 | 5.4 |
| br|Vout_2 M3->J8 (LED DC)|over | vias over, low | 0 | 0 |
| br|Vout_2 M3->J8 (LED DC)|worst | worst via x, low | 0.12 | 0.12 |
| br|Vout_3 M4->J5 (LED DC)|R | R mOhm, low | 1.623 | 1.623 |
| br|Vout_3 M4->J5 (LED DC)|neck | rise C, low | 2.4 | 2.4 |
| br|Vout_3 M4->J5 (LED DC)|necklen | neck length mm (info), info | 4.1 | 4.1 |
| br|Vout_3 M4->J5 (LED DC)|long | rise C, low | 2.4 | 2.4 |
| br|Vout_3 M4->J5 (LED DC)|over | vias over, low | 0 | 0 |
| br|Vout_3 M4->J5 (LED DC)|worst | worst via x, low | 0.09 | 0.09 |
| br|Output1_drain J4->M10|R | R mOhm, low | 1.968 | 1.968 |
| br|Output1_drain J4->M10|neck | rise C, low | 4.1 | 4.1 |
| br|Output1_drain J4->M10|necklen | neck length mm (info), info | 1.3 | 1.3 |
| br|Output1_drain J4->M10|long | rise C, low | 3.8 | 3.8 |
| br|Output1_drain J4->M10|over | vias over, low | 0 | 0 |
| br|Output1_drain J4->M10|worst | worst via x, low | 0 | 0 |
| br|Output2_drain J7->M9|R | R mOhm, low | 2.868 | 2.868 |
| br|Output2_drain J7->M9|neck | rise C, low | 6.6 | 6.6 |
| br|Output2_drain J7->M9|necklen | neck length mm (info), info | 1.3 | 1.3 |
| br|Output2_drain J7->M9|long | rise C, low | 3.5 | 3.5 |
| br|Output2_drain J7->M9|over | vias over, low | 0 | 0 |
| br|Output2_drain J7->M9|worst | worst via x, low | 0 | 0 |
| br|Output3_drain J6->M8|R | R mOhm, low | 2.992 | 2.992 |
| br|Output3_drain J6->M8|neck | rise C, low | 4.6 | 4.6 |
| br|Output3_drain J6->M8|necklen | neck length mm (info), info | 10.1 | 10.1 |
| br|Output3_drain J6->M8|long | rise C, low | 4.6 | 4.6 |
| br|Output3_drain J6->M8|over | vias over, low | 0 | 0 |
| br|Output3_drain J6->M8|worst | worst via x, low | 0 | 0 |
| br|M10-S M10->R52|R | R mOhm, low | 0.31 | 0.31 |
| br|M10-S M10->R52|neck | rise C, low | 3.1 | 3.1 |
| br|M10-S M10->R52|necklen | neck length mm (info), info | 1.2 | 1.2 |
| br|M10-S M10->R52|long | rise C, low | 0 | 0 |
| br|M10-S M10->R52|over | vias over, low | 0 | 0 |
| br|M10-S M10->R52|worst | worst via x, low | 0 | 0 |
| br|M9-S M9->R53|R | R mOhm, low | 0.284 | 0.284 |
| br|M9-S M9->R53|neck | rise C, low | 9.5 | 9.5 |
| br|M9-S M9->R53|necklen | neck length mm (info), info | 0 | 0 |
| br|M9-S M9->R53|long | rise C, low | 0 | 0 |
| br|M9-S M9->R53|over | vias over, low | 0 | 0 |
| br|M9-S M9->R53|worst | worst via x, low | 0 | 0 |
| br|M8-S M8->R7|R | R mOhm, low | 0.236 | 0.236 |
| br|M8-S M8->R7|neck | rise C, low | 1.4 | 1.4 |
| br|M8-S M8->R7|necklen | neck length mm (info), info | 1.6 | 1.6 |
| br|M8-S M8->R7|long | rise C, low | 0 | 0 |
| br|M8-S M8->R7|over | vias over, low | 0 | 0 |
| br|M8-S M8->R7|worst | worst via x, low | 0 | 0 |
| br|GND M1->input caps+J2|R | R mOhm, low | 0.147 | 0.146 |
| br|GND M1->input caps+J2|neck | rise C, low | 10.4 | 10.5 |
| br|GND M1->input caps+J2|necklen | neck length mm (info), info | 0.2 | 0.2 |
| br|GND M1->input caps+J2|long | rise C, low | 4.5 | 4.9 **(worse)** |
| br|GND M1->input caps+J2|over | vias over, low | 0 | 0 |
| br|GND M1->input caps+J2|worst | worst via x, low | 0.98 | 0.98 |
| br|GND ch1 bank->input|R | R mOhm, low | 0.381 | 0.37 |
| br|GND ch1 bank->input|neck | rise C, low | 5.1 | 5.9 **(worse)** |
| br|GND ch1 bank->input|necklen | neck length mm (info), info | 2.3 | 0.5 |
| br|GND ch1 bank->input|long | rise C, low | 5.1 | 5 |
| br|GND ch1 bank->input|over | vias over, low | 0 | 0 |
| br|GND ch1 bank->input|worst | worst via x, low | 0.93 | 0.9 |
| br|GND ch2 bank->input|R | R mOhm, low | 0.688 | 0.668 |
| br|GND ch2 bank->input|neck | rise C, low | 6.1 | 8 **(worse)** |
| br|GND ch2 bank->input|necklen | neck length mm (info), info | 2.7 | 0.2 |
| br|GND ch2 bank->input|long | rise C, low | 6.1 | 5.8 |
| br|GND ch2 bank->input|over | vias over, low | 0 | 0 |
| br|GND ch2 bank->input|worst | worst via x, low | 0.97 | 0.95 |
| br|GND ch3 bank->input|R | R mOhm, low | 0.443 | 0.438 |
| br|GND ch3 bank->input|neck | rise C, low | 5.1 | 4.7 |
| br|GND ch3 bank->input|necklen | neck length mm (info), info | 5.8 | 5.6 |
| br|GND ch3 bank->input|long | rise C, low | 5.1 | 4.7 |
| br|GND ch3 bank->input|over | vias over, low | 1 | 1 |
| br|GND ch3 bank->input|worst | worst via x, low | 1.13 | 1.12 |
| br|GND R52 return|R | R mOhm, low | 0.727 | 0.714 |
| br|GND R52 return|neck | rise C, low | 0.4 | 0.5 |
| br|GND R52 return|necklen | neck length mm (info), info | 8.5 | 0.3 |
| br|GND R52 return|long | rise C, low | 0.4 | 0.3 |
| br|GND R52 return|over | vias over, low | 0 | 0 |
| br|GND R52 return|worst | worst via x, low | 0.5 | 0.5 |
| br|GND R53 return|R | R mOhm, low | 0.906 | 0.889 |
| br|GND R53 return|neck | rise C, low | 0.3 | 0.5 |
| br|GND R53 return|necklen | neck length mm (info), info | 8.9 | 0.4 |
| br|GND R53 return|long | rise C, low | 0.3 | 0.3 |
| br|GND R53 return|over | vias over, low | 0 | 0 |
| br|GND R53 return|worst | worst via x, low | 0.61 | 0.61 |
| br|GND R7 return|R | R mOhm, low | 0.847 | 0.836 |
| br|GND R7 return|neck | rise C, low | 0.3 | 0.3 |
| br|GND R7 return|necklen | neck length mm (info), info | 6.5 | 0.6 |
| br|GND R7 return|long | rise C, low | 0.3 | 0.3 |
| br|GND R7 return|over | vias over, low | 0 | 0 |
| br|GND R7 return|worst | worst via x, low | 0.47 | 0.47 |
| br|loop LX M1->M7|R | R mOhm, low | 0.453 | 0.451 |
| br|loop LX M1->M7|neck | rise C, low | 13.6 | 13.4 |
| br|loop LX M1->M7|necklen | neck length mm (info), info | 1.5 | 1.6 |
| br|loop LX M1->M7|long | rise C, low | 7.7 | 7.4 |
| br|loop LX M1->M7|over | vias over, low | 0 | 0 |
| br|loop LX M1->M7|worst | worst via x, low | 0.45 | 0.45 |
| br|loop LX M1->M6|R | R mOhm, low | 1.129 | 1.128 |
| br|loop LX M1->M6|neck | rise C, low | 18.5 | 18.4 |
| br|loop LX M1->M6|necklen | neck length mm (info), info | 5.4 | 5.4 |
| br|loop LX M1->M6|long | rise C, low | 18.5 | 18.4 |
| br|loop LX M1->M6|over | vias over, low | 0 | 0 |
| br|loop LX M1->M6|worst | worst via x, low | 0.66 | 0.66 |
| br|loop LX M1->M5|R | R mOhm, low | 1.854 | 1.86 **(worse)** |
| br|loop LX M1->M5|neck | rise C, low | 56.7 | 55.9 |
| br|loop LX M1->M5|necklen | neck length mm (info), info | 1.3 | 1.3 |
| br|loop LX M1->M5|long | rise C, low | 25.4 | 27.4 **(worse)** |
| br|loop LX M1->M5|over | vias over, low | 0 | 0 |
| br|loop LX M1->M5|worst | worst via x, low | 0.57 | 0.57 |
| br|loop Vout_1 M2->ceramics|R | R mOhm, low | 0.237 | 0.237 |
| br|loop Vout_1 M2->ceramics|neck | rise C, low | 18.7 | 18.7 |
| br|loop Vout_1 M2->ceramics|necklen | neck length mm (info), info | 0 | 0 |
| br|loop Vout_1 M2->ceramics|long | rise C, low | 4.9 | 4.9 |
| br|loop Vout_1 M2->ceramics|over | vias over, low | 0 | 0 |
| br|loop Vout_1 M2->ceramics|worst | worst via x, low | 0.95 | 0.95 |
| br|loop Vout_2 M3->ceramics|R | R mOhm, low | 0.457 | 0.46 |
| br|loop Vout_2 M3->ceramics|neck | rise C, low | 6.4 | 6.5 |
| br|loop Vout_2 M3->ceramics|necklen | neck length mm (info), info | 1.2 | 1.3 |
| br|loop Vout_2 M3->ceramics|long | rise C, low | 4.4 | 4.4 |
| br|loop Vout_2 M3->ceramics|over | vias over, low | 2 | 2 |
| br|loop Vout_2 M3->ceramics|worst | worst via x, low | 1.1 | 1.06 |
| br|loop Vout_3 M4->ceramics|R | R mOhm, low | 0.682 | 0.601 |
| br|loop Vout_3 M4->ceramics|neck | rise C, low | 84.9 | 90.3 **(worse)** |
| br|loop Vout_3 M4->ceramics|necklen | neck length mm (info), info | 1.3 | 1 |
| br|loop Vout_3 M4->ceramics|long | rise C, low | 55.3 | 58.7 **(worse)** |
| br|loop Vout_3 M4->ceramics|over | vias over, low | 3 | 5 **(worse)** |
| br|loop Vout_3 M4->ceramics|worst | worst via x, low | 2.8 | 1.82 |
| br|loop GND ch1 ceramics->M1|R | R mOhm, low | 1.037 | 1.006 |
| br|loop GND ch1 ceramics->M1|neck | rise C, low | 25.8 | 26.1 **(worse)** |
| br|loop GND ch1 ceramics->M1|necklen | neck length mm (info), info | 3.8 | 3.7 |
| br|loop GND ch1 ceramics->M1|long | rise C, low | 25.8 | 26.1 **(worse)** |
| br|loop GND ch1 ceramics->M1|over | vias over, low | 5 | 5 |
| br|loop GND ch1 ceramics->M1|worst | worst via x, low | 2.06 | 2.06 |
| br|loop GND ch2 ceramics->M1|R | R mOhm, low | 1.123 | 0.993 |
| br|loop GND ch2 ceramics->M1|neck | rise C, low | 12.1 | 20.1 **(worse)** |
| br|loop GND ch2 ceramics->M1|necklen | neck length mm (info), info | 0.6 | 0.1 |
| br|loop GND ch2 ceramics->M1|long | rise C, low | 7.2 | 6.1 |
| br|loop GND ch2 ceramics->M1|over | vias over, low | 3 | 5 **(worse)** |
| br|loop GND ch2 ceramics->M1|worst | worst via x, low | 3.6 | 1.71 |
| br|loop GND ch3 ceramics->M1|R | R mOhm, low | 0.916 | 0.911 |
| br|loop GND ch3 ceramics->M1|neck | rise C, low | 40.1 | 38.2 |
| br|loop GND ch3 ceramics->M1|necklen | neck length mm (info), info | 2.7 | 2.8 |
| br|loop GND ch3 ceramics->M1|long | rise C, low | 40.1 | 38.2 |
| br|loop GND ch3 ceramics->M1|over | vias over, low | 4 | 4 |
| br|loop GND ch3 ceramics->M1|worst | worst via x, low | 2.72 | 2.73 |
| loopL_ch1 | loop L nH, low | 1.49 | 1.49 |
| loopL_ch2 | loop L nH, low | 2 | 2 |
| loopL_ch3 | loop L nH, low | 2.77 | 2.74 |
| gnd_max_mV | GND max mV, low | 8.06 | 8.08 |
| offset_R52 | sense offset mV, low | 0.65 | 0.65 |
| offset_R53 | sense offset mV, low | 1.1 | 1.1 |
| offset_R7 | sense offset mV, low | 0.76 | 0.76 |
| cover_signal | over GND %, high | 47 | 47 |
| cover_gate | over GND %, high | 27 | 27 |
| sense|SNS_CH1 | over GND %, high | 100 | 100 |
| sense|SNS_CH2 | over GND %, high | 100 | 100 |
| sense|SNS_CH3 | over GND %, high | 83 | 83 |
| sense|ISNS_P | over GND %, high | 100 | 100 |
| sense|ISNS_N | over GND %, high | 64 | 64 |
| sense|Current | over GND %, high | 63 | 63 |
| sense|IREF1_input | over GND %, high | 81 | 81 |
| sense|IREF2_input | over GND %, high | 93 | 93 |
| sense|IREF3_input | over GND %, high | 44 | 44 |
| sense|all | over GND %, high | 74 | 74 |
| gate_unret|M1 | unreturned %, low | 4 | 4 |
| gate_unret|M2 | unreturned %, low | 42 | 42 |
| gate_unret|M7 | unreturned %, low | 38 | 38 |
| gate_unret|M3 | unreturned %, low | 52 | 52 |
| gate_unret|M6 | unreturned %, low | 33 | 33 |
| gate_unret|M4 | unreturned %, low | 37 | 37 |
| gate_unret|M5 | unreturned %, low | 13 | 13 |
| gate_unret|M8 | unreturned %, low | 0 | 0 |
| gate_unret|M9 | unreturned %, low | 0 | 0 |
| gate_unret|M10 | unreturned %, low | 0 | 0 |
| u16_tab | K/W, low | 23.61 |  |
| u16_bg | K, low | 16.04 |  |
| u16_tj | C, low | 117.8 |  |
| pieces|power|F.Cu | GND pieces, low | 15 | 15 |
| bigpiece|power|F.Cu | largest GND piece mm2, high | 2059.0 | 2060.0 |
| pieces|power|In1.Cu | GND pieces, low | 1 | 1 |
| bigpiece|power|In1.Cu | largest GND piece mm2, high | 4829.0 | 4829.0 |
| pieces|power|In2.Cu | GND pieces, low | 4 | 4 |
| bigpiece|power|In2.Cu | largest GND piece mm2, high | 2317.0 | 2317.0 |
| pieces|power|In3.Cu | GND pieces, low | 9 | 9 |
| bigpiece|power|In3.Cu | largest GND piece mm2, high | 1309.0 | 1309.0 |
| pieces|power|In4.Cu | GND pieces, low | 16 | 15 |
| bigpiece|power|In4.Cu | largest GND piece mm2, high | 707.0 | 774.0 |
| pieces|power|B.Cu | GND pieces, low | 17 | 18 **(worse)** |
| bigpiece|power|B.Cu | largest GND piece mm2, high | 1039.0 | 1038.0 |
| gnd_split_tracks|power | tracks splitting GND, low | 35 | 36 **(worse)** |
| gnd_slices3mm|power | GND slices >= 3 mm, low | 60 | 58 |
| jogs|power | jogs, low | 674 | 667 |
| pieces|card|F.Cu | GND pieces, low | 27 | 28 **(worse)** |
| bigpiece|card|F.Cu | largest GND piece mm2, high | 348.0 | 343.0 **(worse)** |
| pieces|card|In1.Cu | GND pieces, low | 12 | 11 |
| bigpiece|card|In1.Cu | largest GND piece mm2, high | 895.0 | 972.0 |
| pieces|card|In2.Cu | GND pieces, low | 11 | 11 |
| bigpiece|card|In2.Cu | largest GND piece mm2, high | 2 | 2 |
| pieces|card|In3.Cu | GND pieces, low | 11 | 11 |
| bigpiece|card|In3.Cu | largest GND piece mm2, high | 1068.0 | 1067.0 |
| pieces|card|In4.Cu | GND pieces, low | 9 | 8 |
| bigpiece|card|In4.Cu | largest GND piece mm2, high | 627.0 | 952.0 |
| pieces|card|B.Cu | GND pieces, low | 18 | 18 |
| bigpiece|card|B.Cu | largest GND piece mm2, high | 362.0 | 362.0 |
| gnd_split_tracks|card | tracks splitting GND, low | 79 | 79 |
| gnd_slices3mm|card | GND slices >= 3 mm, low | 95 | 93 |
| jogs|card | jogs, low | 2600 | 2551 |
| card_gap_tracks | tracks over plane gaps, low | 106 | 106 |
| card_gap_mm | mm over plane gaps, low | 196.0 | 198.9 **(worse)** |
| card_stacked | stacked track pairs, low | 83 | 82 |
| sens_inp | plane %, high | 65.6 | 65.6 |
| sens_inp_fvias | foreign vias < 2 mm, low | 0 | 0 |
| sens_cur | plane %, high | 82.4 | 82.4 |
| sens_cur_fvias | foreign vias < 2 mm, low | 0 | 0 |
| sens_verr | plane %, high | 90.4 | 90.4 |
| sens_verr_fvias | foreign vias < 2 mm, low | 0 | 0 |
| sim|base|ptvs | , eq | 0.012 |  |
| sim|base|etvs | , eq | 0.01 |  |
| sim|base|iled1 | A, eq | 2.635 |  |
| sim|base|iled2 | A, eq | 2.371 |  |
| sim|base|iled3 | A, eq | 2.371 |  |
| sim|base|vout1 | , eq | 23.296 |  |
| sim|base|vout2 | , eq | 33.132 |  |
| sim|base|vout3 | , eq | 33.108 |  |
| sim|base|vd1 | , eq | 1.49 |  |
| sim|base|vd2 | , eq | 1.454 |  |
| sim|base|vd3 | , eq | 1.452 |  |
| sim|base|lxmax | , eq | 81.785 |  |
| sim|base|lxmax1 | , eq | 60.975 |  |
| sim|base|lxss | , eq | 60.414 |  |
| sim|base|id19min | , eq | -2.108 |  |
| sim|base|ptvs_ss | , eq | 0.009 |  |
| sim|base|il1avg | , eq | -16.737 |  |
