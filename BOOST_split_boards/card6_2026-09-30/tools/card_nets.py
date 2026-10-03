"""Net classes of the control card for routing and checks (pure Python, shared by route_card.py and sens_check.py)."""

ANALOG = {
    'Current', 'V_err', 'Net-(U2-In+)', 'Net-(U4-In+)', 'Net-(U14-In+)', 'Net-(U21-In+)', 'Net-(U21-In-)',
    'Net-(Q1-E)', 'Net-(D3-+)', 'Net-(D4-+)', 'Net-(D4--)',
    'Verr1', 'Verr2', 'Verr3', 'Voltage_err_1', 'Voltage_err_2', 'Voltage_err_3',
    '.1Vout_1', '.1Vout_2', '.1Vout_3', 'Net-(U3-In-)', 'Net-(U7-In-)', 'Net-(U13-In-)',
    '.1Vref_1', '.1Vref_2', '.1Vref_3', 'Vref_1', 'Vref_2', 'Vref_3',
    'Net-(U106A-A)', 'Net-(U106B-A)', 'Net-(U106C-A)', 'Net-(U106A-B)', 'Net-(U106B-B)', 'Net-(U106C-B)',
    'Net-(D23-+)', 'Net-(D25-+)', 'Net-(D26-+)', 'Net-(U22-In+)', 'Net-(U23-In+)', 'Net-(U24-In+)',
    'Net-(U26A-P0B)', 'Net-(U26B-P1B)', 'Net-(U26C-P2B)', 'IREF1_input', 'IREF2_input', 'IREF3_input',
    'Vout_1', 'Vout_2', 'Vout_3', 'Output1_drain', 'Output2_drain', 'Output3_drain'}
RAILS = {'analog_5V', '12V'}
# everything else that is not GND or 5V is logic: gate / counter / Schmitt nets, comparator outputs, the J11 enables,
# M1_INHIBIT, the Arduino lines (Vref_n_arduino PWM, IREF1-3 enables, I2C, ARD_M1_INHIBIT: user, 2026-09-22)

def is_logic(net):
    return net not in ANALOG and net not in RAILS and net not in ('GND', '5V')
