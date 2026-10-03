# Tab rectangles and the candidate GND via sets around U16 (2026-10-01); plain Python, no imports.
TABS = {  # tab pad rectangles (mm), from the boards
    'sot223': (95.70, 59.60, 99.50, 61.60),
    'to263': (92.61, 52.87, 103.41, 62.27),
}
# Extra GND vias (x, y), 0.4 mm drill / 0.8 mm pad (the Power netclass via). Chosen clear of the B.Cu 12 V track
# (centre >= 1.05 mm from its centreline) and of the U16 Vin/12V pads.
VIAS_IN_TAB = [(95.95, 59.85), (98.0, 61.1), (99.0, 61.1), (99.0, 60.1)]
VIAS_UNDER_BODY = [(x, y) for y in (63.3, 64.4) for x in (96.6, 97.6, 98.6, 99.6)]
VIAS_WEST = [(94.3, y) for y in (57.3, 58.3, 59.3, 60.3, 61.3)]
VIAS_NORTH = [(x, 58.3) for x in (95.3, 96.3, 97.3)]
VIAS_EAST = [(100.7, y) for y in (58.0, 59.0, 60.0, 61.0, 62.0, 63.0, 64.0)]
# Only possible if the B.Cu 12 V track is moved off the tab: the rest of the tab.
VIAS_TAB_REST = [(96.2, 61.1), (97.1, 60.1), (97.1, 61.1), (98.0, 60.1)]

CONFIGS = {
    'sot223': ('sot223', []),
    'sot223_vias_tab': ('sot223', VIAS_IN_TAB),
    'sot223_vias_around': ('sot223', VIAS_IN_TAB + VIAS_UNDER_BODY + VIAS_WEST + VIAS_NORTH + VIAS_EAST),
    'sot223_vias_all': ('sot223', VIAS_IN_TAB + VIAS_TAB_REST + VIAS_UNDER_BODY + VIAS_WEST + VIAS_NORTH + VIAS_EAST),
    'to263': ('to263', []),
    'sot223_real': ('sot223', []),  # vias already in the exported copper
}


