"""Run route_2026-09-16's router for the 6-layer trial: no plane landing (the planes it would land on are being dropped),
so every route stays on F.Cu, In2, In3, In5 and B.Cu (the layers both variants keep, under their 8-layer names).

    python route6.py COPPER.json OUT_ROUTES.json --nets NET [--jmap SHEET.npz] [other route_signals options]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'route_2026-09-16', 'tools'))
import route_signals as R

R.PLANE_TARGET.clear()
R.main()
