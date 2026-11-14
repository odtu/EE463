"""All numbers the checker uses, in one place. Edit here to change a limit.

Sources
- EE463 Hardware Project (github.com/odtu/EE463, "Hardware Project"): specs.
- PCBWay standard-price ("no surcharge") capabilities, checked 2026-09-25.
- IPC-2221B: track current (Fig. 6-4 fit) and conductor spacing (Table 6-1).
"""

# --- EE463 project ---------------------------------------------------------
PROJECT = {
    "name": "EE463 DC-DC converter",
    "vin_min": 20.0,          # V
    "vin_max": 48.0,          # V
    "vout": 12.0,             # V
    "iout_rated": 5.0,        # A (60 W)
    "iout_overload": 7.5,     # A (90 W overload bonus)
    "efficiency_guess": 0.85, # used only to estimate the input current
    "v_peak_margin": 1.25,    # switch-node ringing / input transients above vin_max
}

# --- PCBWay standard price -------------------------------------------------
FAB = {
    "name": "PCBWay standard price",
    "layers": 2,
    "thickness": 1.6,
    "copper_oz": 1.0,
    "min_track": 0.15,              # 6 mil
    "min_space": 0.15,              # 6 mil
    "min_drill": 0.30,
    "max_drill": 6.3,               # larger holes are milled
    "aspect_ratio": 8.0,            # board thickness : drill
    "via_ring_min": 0.13,           # 5 mil (1 oz)
    "via_ring_good": 0.15,
    "pad_ring_min": 0.25,           # component holes, 10 mil (1 oz)
    "pad_ring_good": 0.30,
    "hole_to_hole_via": 0.28,       # 11 mil
    "hole_to_hole_pad": 0.41,       # 16 mil
    "copper_to_edge_min": 0.25,
    "copper_to_edge_good": 0.50,
    "plated_slot_min": 0.50,
    "npth_slot_min": 0.80,
    "silk_text_min": 0.80,          # height
    "silk_text_good": 1.00,
    "silk_line_min": 0.15,
    "min_board_side": 20.0,         # "normal process" below this needs special handling
}

# Track width / spacing minimums for heavier copper (outer layers)
HEAVY_COPPER = {
    2.0: {"min_track": 0.18, "min_space": 0.20, "via_ring_min": 0.18, "pad_ring_min": 0.30},
    3.0: {"min_track": 0.25, "min_space": 0.30, "via_ring_min": 0.20, "pad_ring_min": 0.36},
}

# --- Power layout (general practice, IPC-2221) ------------------------------
POWER = {
    "rise_warn": 20.0,       # degC track temperature rise at rated current -> warning
    "rise_error": 40.0,      # degC -> error
    "min_segment_len": 2.0,  # mm; shorter pieces (pad entries) are not sized for current
    "via_amps_03": 0.5,      # A per 0.3 mm via (conservative)
    "via_amps_04": 0.7,      # A per 0.4 mm via
    # IPC-2221B Table 6-1, spacing between conductors (mm)
    # A6: external component lead/termination, uncoated (pads)
    "pad_spacing": [(15, 0.13), (30, 0.13), (50, 0.13), (100, 0.25), (150, 0.4), (170, 0.4), (250, 0.4)],
    # B4: external conductor with solder mask
    "masked_spacing": [(15, 0.05), (30, 0.05), (50, 0.13), (100, 0.13), (150, 0.4), (170, 0.4), (250, 0.4)],
    "hot_loop_cap_mm": 5.0,       # input ceramic cap to switch pad
    "gate_driver_mm": 15.0,       # driver pin to MOSFET gate pad (straight line)
    "gate_track_mm": 30.0,        # routed length of a gate drive net
    "bootstrap_mm": 5.0,          # bootstrap cap to driver pin
    "fb_divider_mm": 10.0,        # feedback divider to FB pin
    "fb_to_sw_mm": 1.0,           # feedback copper to switch-node copper
    "decap_mm": 4.0,              # small cap to IC supply pin (edge to edge)
    "bulk_cap_mm": 30.0,
    "small_cap_max_F": 1.0e-6,    # caps up to this count as decoupling caps
    "cap_rating_margin": 1.25,    # cap voltage rating >= margin x working voltage
}

ASSEMBLY = {
    "pad_gap_hand": 0.5,     # mm between pads of different parts, for hand soldering/rework
    "smallest_ok": "0603",   # 0402 and smaller are hard to hand-solder
    "mount_hole_keepout": 4.0,  # radius around a mounting hole centre (M3 washer 7 mm)
    "mount_hole_edge": 3.0,     # hole centre to board edge
}


def fab_limits(copper_oz):
    lim = dict(FAB)
    for oz, extra in sorted(HEAVY_COPPER.items()):
        if copper_oz and copper_oz >= oz:
            lim.update(extra)
    return lim


def spacing_for(volts, table):
    for vmax, mm in table:
        if volts <= vmax:
            return mm
    return table[-1][1] + 0.005 * (volts - table[-1][0])
