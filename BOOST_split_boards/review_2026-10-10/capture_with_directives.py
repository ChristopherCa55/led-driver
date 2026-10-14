"""ltspice_capture.py, but the cropped copy keeps the SPICE directives (as plain text, so nothing can run).

    python capture_with_directives.py FILE.asc OUTDIR --region x1,y1,x2,y2 --name NAME
"""
import os, sys
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                                                 'ltspice_layout_handoff_2026-10-05', 'tools')))
import ltspice_capture as LC

_orig = LC.crop_lines
LC.crop_lines = lambda sch, r, keep_directives=False: _orig(sch, r, True)
if __name__ == '__main__':
    LC.main()
