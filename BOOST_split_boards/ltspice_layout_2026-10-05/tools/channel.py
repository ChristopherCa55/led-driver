"""The three per-channel blocks (CREG, REF, EA), drawn by one function each so that channels 2 and 3 are exact
copies of channel 1 (H10). Coordinates are relative to each block's top-left corner; Y is the row top."""

CH = {
    1: dict(n=1, vout='Vout_1', drain='Output1_drain', irefin='IREF1_input', iref='IREF1', srv='SRV1', vref='.1Vref_1',
            vrefa='Vref_1', vout10='.1Vout_1', verri='Voltage_err_1', verr='Verr1',
            led='SIM_LED1', m='M10', rs='R52', opc='U11', rg='R56', cf='C45', cbc='C33', cbc_flip=False,
            sim='SIM_IREF1', r29='R29', r54='R54', c100='C100', pot='U26A', r94='R94', r95='R95', sw='U106C',
            opr='U24', cint='C67', rint='R98', r96='R96', r97='R97', c68='C68', dd='D26', cbr='C32', cbr_flip=False,
            simv='SIM_VREF1', r101='R101', c103='C103', r6='R6', c46='C46', r9='R9', r8='R8', r2='R2', r3='R3',
            ope='U3', r27='R27', r28='R28', c13='C13', cbe='C66', cbe_flip=False),
    2: dict(n=2, vout='Vout_2', drain='Output2_drain', irefin='IREF2_input', iref='IREF2', srv='SRV2', vref='.1Vref_2',
            vrefa='Vref_2', vout10='.1Vout_2', verri='Voltage_err_2', verr='Verr2',
            led='SIM_LED2', m='M9', rs='R53', opc='U12', rg='R50', cf='C44', cbc='C34', cbc_flip=False,
            sim='SIM_IREF2', r29='R30', r54='R55', c100='C101', pot='U26B', r94='R25', r95='R36', sw='U106B',
            opr='U23', cint='C64', rint='R93', r96='R91', r97='R92', c68='C65', dd='D25', cbr='C38', cbr_flip=True,
            simv='SIM_VREF2', r101='R100', c103='C93', r6='R33', c46='C43', r9='R35', r8='R34', r2='R31', r3='R32',
            ope='U7', r27='R37', r28='R38', c13='C11', cbe='C36', cbe_flip=True),
    3: dict(n=3, vout='Vout_3', drain='Output3_drain', irefin='IREF3_input', iref='IREF3', srv='SRV3', vref='.1Vref_3',
            vrefa='Vref_3', vout10='.1Vout_3', verri='Voltage_err_3', verr='Verr3',
            led='SIM_LED3', m='M8', rs='R7', opc='U6', rg='R22', cf='C41', cbc='C35', cbc_flip=False,
            sim='SIM_IREF3', r29='R57', r54='R58', c100='C102', pot='U26C', r94='R87', r95='R88', sw='U106A',
            opr='U22', cint='C49', rint='R90', r96='R44', r97='R89', c68='C59', dd='D23', cbr='C63', cbr_flip=False,
            simv='SIM_VREF3', r101='R77', c103='C47', r6='R41', c46='C42', r9='R43', r8='R42', r2='R39', r3='R40',
            ope='U13', r27='R45', r28='R46', c13='C10', cbe='C37', cbe_flip=True),
}

SIM_NOTE = 'simulation only - not on the PCB'
CREG_W, REF_W, EA_W = 1152, 1328, 1696
ROW_H = 1056
REF_H = 1440


def L(x, y, size=2):
    return ('Left', x, y, size)


def R(x, y, size=2):
    return ('Right', x, y, size)


def ABOVE(x, y, size=2):          # text centred on x, bottom at y
    return ('Bottom', x, y, size)


def BELOW(x, y, size=2):          # text centred on x, top at y
    return ('Top', x, y, size)


# ===================================================================================================== CREG
def creg(d, X, Y, c, temp):
    """LED current regulator. Returns the points where the drain and setpoint wires leave towards REF."""
    xa, xr = X + 352, X + 224
    xu, xs, xc = xa + 256, xa + 416, xa + 480
    yu = Y + 752
    d.T(X + 16, Y + 24, '[CREG%d] Channel %d LED current regulator (power board)' % (c['n'], c['n']))
    # Vout in, LED (simulation only)
    d.W((xa - 64, Y + 64), (xa, Y + 64), (xa, Y + 128))
    d.F(xa - 64, Y + 64, c['vout'], 'In')
    d.Pa(c['led'], xa - 16, Y + 128, 'R0', {'name': L(xa + 32, Y + 144), 'value': L(xa + 32, Y + 176)})
    d.frame(xa - 48, Y + 96, xa + 528, Y + 272)
    d.T(xa + 32, Y + 240, SIM_NOTE)
    # drain node, sink FET, sense resistor
    d.W((xa, Y + 192), (xa, Y + 320), (xa, Y + 352))
    d.W((xa, Y + 320), (xa + 432, Y + 320))
    d.F(xa + 432, Y + 320, c['drain'])
    d.Pa(c['m'], xa - 48, Y + 352, 'R0', {'name': L(xa + 16, Y + 384), 'value': L(xa + 16, Y + 416)})
    d.W((xa, Y + 448), (xa, Y + 480), (xa, Y + 512))
    d.res_v(c['rs'], xa, Y + 512, texts={'name': R(xa - 32, Y + 536), 'value': R(xa - 32, Y + 568)})
    d.G((xa, Y + 592))
    # sense feedback into In- from above; the op-amp is mirrored so its inputs face REF
    d.W((xa, Y + 480), (xa + 208, Y + 480), (xs, Y + 480), (xs, yu + 48), (xu + 32, yu + 48))
    d.F(xa + 208, Y + 480, 'SNS_CH%d' % c['n'])
    d.Pa(c['opc'], xu, yu, 'M0', {'name': L(xu + 48, yu + 128), 'value': L(xu + 48, yu + 160)})
    d.G((xu, yu + 96))
    d.W((xu, yu + 32), (xu, yu - 48), (xu - 48, yu - 48), (xu - 96, yu - 48))
    d.F(xu - 48, yu - 48, 'analog_5V')
    d.cap(c['cbc'], xu - 96, yu - 48, c['cbc_flip'], {'name': R(xu - 128, yu - 16), 'value': R(xu - 128, yu + 16)})
    d.G((xu - 96, yu + 16))
    # gate drive OUT -> R -> gate
    d.W((xa - 48, Y + 432), (xr, Y + 432), (xr, Y + 480))
    d.res_v(c['rg'], xr, Y + 480, texts={'name': R(xr - 32, Y + 504), 'value': R(xr - 32, Y + 536)})
    d.W((xr, Y + 560), (xr, yu + 64), (xu - 32, yu + 64))
    # setpoint input with its filter cap
    d.W((xu + 32, yu + 80), (xc, yu + 80), (xc + 224, yu + 80))
    d.F(xc + 224, yu + 80, c['irefin'])
    d.cap(c['cf'], xc, yu + 80, False, {'name': L(xc + 32, yu + 96), 'value': L(xc + 32, yu + 128)})
    d.G((xc, yu + 144))
    d.frame(X, Y, X + CREG_W, Y + ROW_H)
    return {'drain': (xa + 432, Y + 320), 'irefin': (xc + 224, yu + 80)}


# ===================================================================================================== REF
def ref(d, X, Y, c, cr, temp, extras=False):
    """Setpoint (digipot) + sample-and-hold + integrator. cr = creg() result (wires continue from there)."""
    p94, xs6, pp = X + 160, X + 480, X + 272
    xL = xs6 + 288
    xo, xR = xL + 224, xL + 384
    sx = X + 640
    d.T(X + 16, Y + 24, '[REF%d] Channel %d LED-current setpoint and headroom servo (control card)' % (c['n'], c['n']))
    # ---- drain sense divider -> 4066 switch
    d.W(cr['drain'], (p94, Y + 320))
    d.res_v(c['r94'], p94, Y + 320, texts={'name': L(p94 + 32, Y + 344), 'value': L(p94 + 32, Y + 376)})
    d.W((p94, Y + 400), (p94, Y + 432), (p94, Y + 464))
    d.res_v(c['r95'], p94, Y + 464, texts={'name': L(p94 + 32, Y + 488), 'value': L(p94 + 32, Y + 520)})
    d.G((p94, Y + 544))
    d.W((p94, Y + 432), (xs6, Y + 432))
    d.Pa(c['sw'], xs6, Y + 432, 'R0', {'name': R(xs6 + 32, Y + 352), 'value': R(xs6 + 32, Y + 380, 1)})
    d.G((xs6 + 16, Y + 480))
    q = (xs6 + 144, Y + 304)                                     # 5V rail; C23 (ch1 only) hangs from q
    d.W((xs6 + 48, Y + 400), (xs6 + 48, Y + 304), q, (xs6 + 208, Y + 304))
    d.F(xs6 + 208, Y + 304, '5V')
    # ---- integrator (headroom servo)
    d.W((xs6 + 80, Y + 432), (xL, Y + 432), (xo - 32, Y + 432))
    d.Pa(c['opr'], xo, Y + 384, 'R0', {'name': L(xo + 48, Y + 480), 'value': L(xo + 48, Y + 512)})
    d.G((xo, Y + 480))
    d.W((xo, Y + 416), (xo, Y + 304), (xo - 48, Y + 304), (xo - 96, Y + 304))
    d.F(xo - 48, Y + 304, 'analog_5V')
    d.cap(c['cbr'], xo - 96, Y + 304, c['cbr_flip'], {'name': R(xo - 128, Y + 336), 'value': R(xo - 128, Y + 368)})
    d.G((xo - 96, Y + 368))
    d.W((xL, Y + 432), (xL, Y + 208), (xL, Y + 112), (xo - 128, Y + 112))
    d.cap_h(c['cint'], xo - 128, Y + 112, True, {'name': ABOVE(xo - 96, Y + 88), 'value': BELOW(xo - 96, Y + 136)})
    d.W((xo - 64, Y + 112), (xR, Y + 112), (xR, Y + 208), (xR, Y + 448))
    d.W((xL, Y + 208), (xo + 32, Y + 208))
    d.res_h(c['rint'], xo + 32, Y + 208, True, {'name': ABOVE(xo + 72, Y + 184), 'value': BELOW(xo + 72, Y + 232)})
    d.W((xo + 112, Y + 208), (xR, Y + 208))
    d.W((xo + 32, Y + 448), (xo + 96, Y + 448), (xR, Y + 448), (xR + 48, Y + 448))
    d.F(xo + 96, Y + 448, c['srv'])
    d.Pa(c['dd'], xR + 48, Y + 464, 'R270', {'name': ABOVE(xR + 80, Y + 424), 'value': BELOW(xR + 80, Y + 472)})
    # In+ reference divider
    d.W((xo - 32, Y + 464), (xo - 96, Y + 464), (xo - 96, Y + 560), (xo, Y + 560))
    d.W((xo - 128, Y + 464), (xo - 96, Y + 464))
    d.res_h(c['r96'], xo - 208, Y + 464, True, {'name': BELOW(xo - 168, Y + 488), 'value': BELOW(xo - 168, Y + 512)})
    d.W((xo - 208, Y + 464), (xo - 240, Y + 464))
    d.F(xo - 240, Y + 464, 'analog_5V')
    d.res_v(c['r97'], xo - 96, Y + 560, texts={'name': R(xo - 128, Y + 584), 'value': R(xo - 128, Y + 616)})
    d.G((xo - 96, Y + 640))
    d.cap(c['c68'], xo, Y + 560, False, {'name': L(xo + 32, Y + 576), 'value': L(xo + 32, Y + 608)})
    d.G((xo, Y + 624))
    # ---- setpoint: SIM PWM -> divider -> digipot wiper -> CREG
    d.W((pp, Y + 784), (pp, Y + 688), (pp - 96, Y + 688), (pp - 224, Y + 688))
    d.res_v(c['r54'], pp - 96, Y + 688, texts={'name': L(pp - 64, Y + 712), 'value': L(pp - 64, Y + 744)})
    d.G((pp - 96, Y + 768))
    d.cap(c['c100'], pp - 224, Y + 688, False, {'name': L(pp - 192, Y + 704), 'value': L(pp - 192, Y + 736)})
    d.G((pp - 224, Y + 752))
    d.Pa(c['pot'], pp, Y + 832, 'M0', {'name': L(pp + 32, Y + 800), 'value': L(pp + 32, Y + 832, 1),
                                       'spiceline': L(pp + 32, Y + 856, 1)})
    d.W(cr['irefin'], (pp - 48, Y + 832))
    d.W((pp, Y + 688), (pp + 64, Y + 688))
    d.res_h(c['r29'], pp + 64, Y + 688, True, {'name': ABOVE(pp + 104, Y + 664), 'value': BELOW(pp + 104, Y + 712)})
    d.W((pp + 144, Y + 688), (X + 480, Y + 688), (xs6 + 64, Y + 688), (sx, Y + 688), (sx, Y + 784))
    d.F(X + 480, Y + 688, c['iref'])
    d.W((xs6 + 64, Y + 688), (xs6 + 64, Y + 480))
    d.Pa(c['sim'], sx, Y + 768, 'R0', {'name': L(sx + 48, Y + 800), 'value': L(sx - 32, Y + 912, 0)})
    d.G((sx, Y + 864))
    d.frame(sx - 64, Y + 736, sx + 624, Y + 944)
    d.T(sx + 48, Y + 848, SIM_NOTE)
    if extras:
        ref1_extras(d, X, Y, q, pp)
    else:
        d.G((pp, Y + 880))
    d.frame(X, Y, X + REF_W, Y + REF_H)
    return {'vref': (xR + 112, Y + 448), 'q': q}


# ===================================================================================================== EA
def ea(d, X, Y, c, rf, temp):
    xo, xn = X + 896, X + 672
    xR = xo + 160
    d.T(X + 16, Y + 24, '[EA%d] Channel %d output-voltage error amplifier, Vout_%d -> Verr%d (control card)' % (
        c['n'], c['n'], c['n'], c['n']))
    # Vout_x / 10 -> inverting input, R3 feedback
    d.W((X + 176, Y + 64), (X + 224, Y + 64), (X + 224, Y + 176))
    d.F(X + 176, Y + 64, c['vout'], 'In')
    d.res_h(c['r9'], X + 224, Y + 176, False, {'name': ABOVE(X + 264, Y + 152), 'value': BELOW(X + 264, Y + 200)})
    d.W((X + 304, Y + 176), (X + 384, Y + 176), (X + 448, Y + 176), (X + 512, Y + 176))
    d.F(X + 448, Y + 176, c['vout10'])
    d.res_v(c['r8'], X + 384, Y + 176, texts={'name': L(X + 416, Y + 200), 'value': L(X + 416, Y + 232)})
    d.G((X + 384, Y + 256))
    d.res_h(c['r2'], X + 512, Y + 176, False, {'name': ABOVE(X + 552, Y + 152), 'value': BELOW(X + 552, Y + 200)})
    d.W((X + 592, Y + 176), (xn, Y + 176), (X + 768, Y + 176))
    d.res_h(c['r3'], X + 768, Y + 176, False, {'name': ABOVE(X + 808, Y + 152), 'value': BELOW(X + 808, Y + 200)})
    d.W((X + 848, Y + 176), (xR, Y + 176), (xR, Y + 432))
    d.W((xn, Y + 176), (xn, Y + 416), (xo - 32, Y + 416))
    d.Pa(c['ope'], xo, Y + 368, 'R0', {'name': L(xo + 48, Y + 496), 'value': L(xo + 48, Y + 528)})
    d.G((xo, Y + 464))
    d.W((xo, Y + 400), (xo, Y + 304), (xo - 48, Y + 304), (xo - 96, Y + 304))
    d.F(xo - 48, Y + 304, 'analog_5V')
    d.cap(c['cbe'], xo - 96, Y + 304, c['cbe_flip'], {'name': R(xo - 128, Y + 336), 'value': R(xo - 128, Y + 368)})
    d.G((xo - 96, Y + 368))
    # output filter -> Verr
    d.W((xo + 32, Y + 432), (xR, Y + 432), (xR + 128, Y + 432), (xR + 256, Y + 432))
    d.F(xR + 128, Y + 432, c['verri'])
    d.res_h(c['r27'], xR + 256, Y + 432, True, {'name': ABOVE(xR + 296, Y + 408), 'value': BELOW(xR + 296, Y + 456)})
    d.W((xR + 336, Y + 432), (xR + 400, Y + 432), (xR + 528, Y + 432), (xR + 592, Y + 432))
    d.res_v(c['r28'], xR + 400, Y + 432, True, {'name': L(xR + 432, Y + 472), 'value': L(xR + 432, Y + 504)})
    d.G((xR + 400, Y + 512))
    d.cap(c['c13'], xR + 528, Y + 432, True, {'name': L(xR + 560, Y + 472), 'value': L(xR + 560, Y + 504)})
    d.G((xR + 528, Y + 496))
    temp(xR + 592, Y + 432, c['verr'], 'Out', 'EA%d' % c['n'], 'to U28 in CONTROL (not yet redrawn)')
    # .1Vref from REF -> In+, with R6 from the Vref_x filter and C46
    d.W(rf['vref'], (X + 288, Y + 448), (X + 640, Y + 448), (X + 736, Y + 448), (xo - 32, Y + 448))
    d.F(X + 288, Y + 448, c['vref'])
    d.cap(c['c46'], X + 640, Y + 448, False, {'name': R(X + 608, Y + 464), 'value': R(X + 608, Y + 496)})
    d.G((X + 640, Y + 512))
    d.res_v(c['r6'], X + 736, Y + 448, True, {'name': L(X + 768, Y + 480), 'value': L(X + 768, Y + 512)})
    d.W((X + 736, Y + 528), (X + 736, Y + 624))
    # SIM Vref source -> R101 -> Vref_x node (C103)
    d.Pa(c['simv'], X + 96, Y + 608, 'R0', {'name': L(X + 144, Y + 672), 'value': L(X + 48, Y + 768)})
    d.G((X + 96, Y + 704))
    d.frame(X + 32, Y + 560, X + 544, Y + 848)
    d.T(X + 48, Y + 816, SIM_NOTE)
    d.W((X + 96, Y + 624), (X + 336, Y + 624), (X + 576, Y + 624))
    d.F(X + 336, Y + 624, 'Vref_%d_arduino' % c['n'])
    d.res_h(c['r101'], X + 576, Y + 624, True, {'name': ABOVE(X + 616, Y + 600), 'value': BELOW(X + 616, Y + 648)})
    d.W((X + 656, Y + 624), (X + 736, Y + 624), (X + 800, Y + 624), (X + 864, Y + 624))
    d.F(X + 800, Y + 624, c['vrefa'])
    d.cap(c['c103'], X + 864, Y + 624, False, {'name': L(X + 896, Y + 640), 'value': L(X + 896, Y + 672)})
    d.G((X + 864, Y + 688))
    d.frame(X, Y, X + EA_W, Y + ROW_H)


def ref1_extras(d, X, Y, q, pp):
    """REF1 only: C23 (bypass of the 4066 package) on the U106C rail, and U26E (the MCP4451 control/supply unit) with
    its strap resistors, below the pot. U26A's A terminal is wired to U26E's ground (same package)."""
    d.cap('C23', q[0], q[1], False, {'name': L(q[0] + 32, q[1] + 40), 'value': L(q[0] + 32, q[1] + 72)})
    d.G((q[0], q[1] + 64))
    d.T(q[0] - 240, q[1] - 72, 'C23: bypass of the 4066')
    d.T(q[0] - 240, q[1] - 40, 'package (U106A/B/C)')
    ux, uy = X + 560, Y + 1152
    d.Pa('U26E', ux, uy, 'R0', {'name': L(ux + 112, uy + 48), 'value': L(ux + 112, uy + 80, 1)})
    d.W((ux, uy - 112), (ux, uy - 160))
    d.W((ux, uy - 160), (ux - 160, uy - 160))
    d.W((ux, uy - 160), (ux + 80, uy - 160), (ux + 160, uy - 160))
    d.F(ux + 80, uy - 160, '5V')
    d.cap('C26', ux - 160, uy - 160, False, {'name': R(ux - 192, uy - 144), 'value': R(ux - 192, uy - 112)})
    d.G((ux - 160, uy - 96))
    d.res_v('R103', ux + 160, uy - 160, texts={'name': L(ux + 192, uy - 136), 'value': L(ux + 192, uy - 104)})
    d.W((ux + 160, uy - 80), (ux + 160, uy), (ux + 96, uy))
    d.W((ux - 96, uy - 32), (ux - 128, uy - 32))
    d.F(ux - 128, uy - 32, 'SCL')
    d.W((ux - 96, uy), (ux - 192, uy))
    d.F(ux - 192, uy, 'SDA')
    d.W((ux - 48, uy + 112), (ux - 48, uy + 128), (ux - 128, uy + 128))
    d.res_v('R102', ux - 128, uy + 128, texts={'name': R(ux - 160, uy + 152), 'value': R(ux - 160, uy + 184)})
    d.W((ux, uy + 112), (ux, uy + 128))
    d.res_v('R99', ux, uy + 128, texts={'name': R(ux - 32, uy + 152), 'value': R(ux - 32, uy + 184)})
    d.W((ux + 48, uy + 112), (ux + 48, uy + 240))
    d.W((pp, Y + 880), (pp, uy + 240), (ux - 128, uy + 240), (ux, uy + 240), (ux + 48, uy + 240))
    d.W((ux - 128, uy + 208), (ux - 128, uy + 240))
    d.W((ux, uy + 208), (ux, uy + 240))
    d.G((ux + 48, uy + 240))
    d.T(ux + 112, uy + 176, 'U26E: MCP4451 control unit, serves U26A/B/C')
