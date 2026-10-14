"""Whole build of the board sheets (work copy only):

    python build.py        moves an old work/ into old/<time>/, then
                           split_sheets.py -> pcb_link.py (both boards, --sync-fields) -> pcb_set_field.py (U104)
"""
import os, sys, subprocess, shutil, time
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(os.path.join(HERE, '..'))
W = os.path.join(BASE, 'work')


def run(*args):
    print('>', ' '.join(os.path.basename(a) if os.sep in a else a for a in args))
    subprocess.run([sys.executable] + list(args), check=True)


if os.path.exists(W):
    os.makedirs(os.path.join(BASE, 'old'), exist_ok=True)
    shutil.move(W, os.path.join(BASE, 'old', time.strftime('work_%H%M%S')))
run(os.path.join(HERE, 'split_sheets.py'))
for b in ('BOOST_power_RC2', 'BOOST_control_RC2'):
    run(os.path.join(HERE, 'pcb_link.py'), os.path.join(W, b + '.kicad_pcb'), os.path.join(W, b + '.kicad_sch'),
        '--sync-fields')
# U104's units disagree on Sim.Params (KiCad simulation field only); KiCad's parity compares unit E (5)
run(os.path.join(HERE, 'pcb_set_field.py'), os.path.join(W, 'BOOST_control_RC2.kicad_pcb'),
    os.path.join(W, 'BOOST_control_RC2.kicad_sch'), 'U104', '5', 'Sim.Params')
