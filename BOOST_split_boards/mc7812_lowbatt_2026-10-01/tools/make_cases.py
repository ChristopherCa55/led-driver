# Build the low-battery case netlists from sim/BOOST.net (LTspice -netlist of the shipped BOOST.asc, sha 99d0b375).
# Changes per case: U16 model, battery source (+ pack resistance), a 120 ohm Arduino-buck load on 12V,
# a .save list with the 12 V rail, U21, M1_INHIBIT and the drivers' supplies, and new .meas lines.
# Usage (from the sim folder): python ../tools/make_cases.py
import re

base = open('BOOST.net', encoding='utf-8').read()

SAVE = ('.save V(vin) V(lx) V(vout_1) V(vout_2) V(vout_3) I(D19) I(SIM_LED1) I(SIM_LED2) I(SIM_LED3) '
        'V(12V) V(5V) V(N010) V(N011) V(N013) V(M1_INHIBIT) V(M1_ON) V(PBAT) V(P001) I(SIM_RPACK) '
        'V(N019) V(m2_source) V(N032) V(m3_source) V(N040) V(m4_source) V(srv1) V(srv2) V(srv3)')

STEADY_MEAS = '''
.meas TRAN V12min MIN V(12V) FROM 5m TO 30m
.meas TRAN V12avg AVG V(12V) FROM 25m TO 30m
.meas TRAN VINavg AVG V(vin) FROM 25m TO 30m
.meas TRAN INHmax MAX V(M1_INHIBIT) FROM 5m TO 30m
.meas TRAN ILED1 AVG I(SIM_LED1) FROM 25m TO 30m
.meas TRAN ILED2 AVG I(SIM_LED2) FROM 25m TO 30m
.meas TRAN ILED3 AVG I(SIM_LED3) FROM 25m TO 30m
.meas TRAN LXmax MAX V(lx)
.meas TRAN LXss MAX V(lx) FROM 25m TO 30m
.meas TRAN Etvs INTEG (-1)*V(LX)*I(D19)
.meas TRAN VDDA2min MIN V(N019)-V(m2_source) FROM 5m TO 30m
.meas TRAN VDDA3min MIN V(N032)-V(m3_source) FROM 5m TO 30m
.meas TRAN VDDA4min MIN V(N040)-V(m4_source) FROM 5m TO 30m
'''

RAMP_MEAS = '''
.meas TRAN V12min MIN V(12V) FROM 5m TO 40m
.meas TRAN LXmax MAX V(lx)
.meas TRAN LXafter8 MAX V(lx) FROM 8m TO 40m
.meas TRAN Etvs INTEG (-1)*V(LX)*I(D19)
.meas TRAN Tcut1 WHEN V(N013)=2.5 RISE=1 TD=5m
.meas TRAN Tcut2 WHEN V(N013)=2.5 RISE=2 TD=5m
.meas TRAN Tcut3 WHEN V(N013)=2.5 RISE=3 TD=5m
.meas TRAN Tcut4 WHEN V(N013)=2.5 RISE=4 TD=5m
.meas TRAN Tcut5 WHEN V(N013)=2.5 RISE=5 TD=5m
.meas TRAN Trel1 WHEN V(N013)=2.5 FALL=1 TD=5m
.meas TRAN Trel2 WHEN V(N013)=2.5 FALL=2 TD=5m
.meas TRAN VOCcut1 FIND V(PBAT) WHEN V(N013)=2.5 RISE=1 TD=5m
.meas TRAN VINcut1 FIND V(vin) WHEN V(N013)=2.5 RISE=1 TD=5m
.meas TRAN V12cut1 FIND V(12V) WHEN V(N013)=2.5 RISE=1 TD=5m
.meas TRAN ILED1_10 AVG I(SIM_LED1) FROM 6m TO 8m
.meas TRAN VDDA2min MIN V(N019)-V(m2_source) FROM 5m TO 40m
.meas TRAN VDDA3min MIN V(N032)-V(m3_source) FROM 5m TO 40m
.meas TRAN VDDA4min MIN V(N040)-V(m4_source) FROM 5m TO 40m
'''

CASES = {
    # name: (U16 model, battery source value, pack resistance, tran, meas)
    'A_7812typ_12V': ('MC7812_TYP', '12', '0', '30m', STEADY_MEAS),
    'B_7812wc_12V': ('MC7812_WC', '12', '0', '30m', STEADY_MEAS),
    'C_7812typ_ramp_R50m': ('MC7812_TYP', 'PWL(0 13 8m 13 33m 11.8 40m 11.8)', '0.05', '40m', RAMP_MEAS),
    'D_lm2940_ramp_R50m': ('LM2940_12', 'PWL(0 13 8m 13 33m 11.8 40m 11.8)', '0.05', '40m', RAMP_MEAS),
    # second round: stiff pack, pessimistic dropout, a steady hold in the chopping region, LM2940 lower down
    'E_7812typ_ramp_R10m': ('MC7812_TYP', 'PWL(0 12.3 8m 12.3 33m 11.1 40m 11.1)', '0.01', '40m', RAMP_MEAS),
    'F_7812wc_ramp_R50m': ('MC7812_WC', 'PWL(0 13.5 8m 13.5 33m 12.3 40m 12.3)', '0.05', '40m', RAMP_MEAS),
    'G_7812typ_hold12p3_R50m': ('MC7812_TYP', '12.3', '0.05', '40m', RAMP_MEAS),
    'H_lm2940_ramp_low_R50m': ('LM2940_12', 'PWL(0 11.8 8m 11.8 33m 10.6 40m 10.6)', '0.05', '40m', RAMP_MEAS),
    'I_7812typ_hold11p85_R50m': ('MC7812_TYP', '11.85', '0.05', '40m', RAMP_MEAS),
}

for name, (model, vbat, rpack, tran, meas) in CASES.items():
    s = base
    s, n = re.subn(r'^X§U16 Vin 12V 0 LM2940_12', 'X§U16 Vin 12V 0 ' + model, s, flags=re.M); assert n == 1
    s, n = re.subn(r'^V§SIM_VBATT P001 0 14\s*$', 'V§SIM_VBATT PBAT 0 %s\nR§SIM_RPACK PBAT P001 %s\n'
                   'R§SIM_ARDLOAD 12V 0 120' % (vbat, rpack if rpack != '0' else '1u'), s, flags=re.M); assert n == 1
    s, n = re.subn(r'^\.tran 30m startup uic', '.tran %s startup uic' % tran, s, flags=re.M); assert n == 1
    s = re.sub(r'^\.save .*\n', '', s, flags=re.M)          # drop any old .save line
    s = re.sub(r'^\.meas .*\n', '', s, flags=re.M)          # drop the old .meas lines
    s = s.replace('\n.end', '\n.lib MC7812.lib\n' + SAVE + meas + '.end')
    assert s.count('.lib MC7812.lib') == 1
    open(name + '.net', 'w', encoding='utf-8').write(s)
    print('wrote', name + '.net')
