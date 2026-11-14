"""Checks for KiCad boards: PCBWay manufacturing limits, the EE463 power stage,
layout, testing and assembly."""

import heapq
import math
import re
from collections import defaultdict

from .geometry import (Shape, GridIndex, distance, point_in_poly, point_seg_dist,
                       ipc2221_rise, ipc2221_width, poly_area)
from .analysis import Analysis, fmt_cap, voltage_rating, SUPPLY_PIN_RE, IC_POWER_PIN_RE, base_name, _natural
from .rules import PROJECT, POWER, ASSEMBLY, fab_limits, spacing_for

MAX_LOCS = 40


def _loc(x, y, layer="", label=""):
    return (x, y, layer, label)


def _fmt(v, nd=2):
    return f"{v:.{nd}f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


class Ctx:
    """Board + analysis + spatial indexes shared by all checks."""

    def __init__(self, board, report, overrides=None, overload=False, oz=None):
        self.b = board
        self.r = report
        self.a = Analysis(board, overrides, overload)
        self.oz = oz or board.copper_oz() or 1.0
        self.lim = fab_limits(self.oz)
        self.outer = {"F.Cu", "B.Cu"}
        # copper items per layer: (kind, obj, net, shape, footprint)
        self.items = defaultdict(list)
        for t in board.tracks:
            self.items[t.layer].append(("track", t, t.net, t.geom, None))
        track_ends = {(t.layer, t.net, round(x, 3), round(y, 3))
                      for t in board.tracks for x, y in ((t.x1, t.y1), (t.x2, t.y2))}
        for v in board.vias:
            for l in v.layers:
                sh = v.geom
                if v.remove_unused and not (v.keep_end and l in ("F.Cu", "B.Cu")) and \
                        (l, v.net, round(v.x, 3), round(v.y, 3)) not in track_ends:
                    sh = Shape.point(v.x, v.y, v.drill / 2)  # ring removed: only the plated hole is left
                self.items[l].append(("via", v, v.net, sh, None))
        for f in board.footprints:
            for p in f.pads:
                for l in p.layers:
                    self.items[l].append(("pad", p, p.net, p.geom, f))
        self.index = {}
        for l, lst in self.items.items():
            gi = GridIndex(2.0)
            for it in lst:
                gi.insert(it[3].bbox, it)
            self.index[l] = gi
        # zone fills per (net, layer): islands with bboxes, and an index of their edges
        self.fills = defaultdict(list)
        self.fill_bbox = defaultdict(list)
        self.fill_edges = {}
        for z in board.zones:
            if z.keepout:
                continue
            for layer, pts in z.fills:
                self.fills[(z.net, layer)].append(pts)
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                self.fill_bbox[(z.net, layer)].append((min(xs), min(ys), max(xs), max(ys)))
        for key, islands in self.fills.items():
            gi = GridIndex(2.0)
            for k, pts in enumerate(islands):
                n = len(pts)
                for i in range(n):
                    x1, y1 = pts[i]
                    x2, y2 = pts[(i + 1) % n]
                    gi.insert((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)), (x1, y1, x2, y2, k))
            self.fill_edges[key] = gi
        self.edge_index = GridIndex(5.0)
        for s in board.edge.segs:
            sh = Shape.segment(*s, 0.0)
            self.edge_index.insert(sh.bbox, sh)

    def edge_dist(self, shape, limit=10.0):
        best = float("inf")
        for _, sh in self.edge_index.query(shape.bbox, limit):
            d = distance(shape, sh)
            best = min(best, d)
        return best

    def islands_at(self, net, layer, x, y):
        out = []
        for k, (bb, pts) in enumerate(zip(self.fill_bbox.get((net, layer), []), self.fills.get((net, layer), []))):
            if bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3] and point_in_poly(x, y, pts):
                out.append(k)
        return out

    def in_fill(self, net, layer, x, y):
        return bool(self.islands_at(net, layer, x, y))

    def pad_islands(self, p, layer, margin=0.6):
        """Fill islands of the pad's own net that reach the pad (directly or by thermal spokes)."""
        found = set(self.islands_at(p.net, layer, p.x, p.y))
        gi = self.fill_edges.get((p.net, layer))
        if gi is not None:
            for _, (x1, y1, x2, y2, k) in gi.query(p.geom.bbox, margin):
                if k in found:
                    continue
                if distance(p.geom, Shape.segment(x1, y1, x2, y2, 0)) <= margin:
                    found.add(k)
        return found

    def pad_touches_fill(self, p, layer, margin=0.6):
        return bool(self.pad_islands(p, layer, margin))


# ---------------------------------------------------------------------------
# Manufacturing


def check_stackup(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-STACKUP", "fab", "Layers, thickness and copper weight", "PCBWay standard price")
    n = len(b.copper_layers)
    if n != lim["layers"]:
        r.add("FAB-STACKUP", "warning",
              f"The board has {n} copper layers. PCBWay's standard price is for {lim['layers']} layers; "
              f"{n} layers cost extra and may not be covered by the sponsored round.",
              fix="Ask the course staff before ordering more than 2 layers, or move the design to 2 layers.")
    if b.thickness and abs(b.thickness - lim["thickness"]) > 0.01:
        r.add("FAB-STACKUP", "warning",
              f"Board thickness is {b.thickness} mm. Standard price is {lim['thickness']} mm.",
              fix="Board Setup > Physical Stackup: set the board thickness to 1.6 mm.")
    oz = b.copper_oz()
    if oz and oz > lim["copper_oz"]:
        r.add("FAB-STACKUP", "warning",
              f"The stackup says {oz:g} oz outer copper. Standard price is 1 oz; heavier copper costs extra.",
              fix="Use 1 oz and make the power copper wider (pours on both layers joined by vias) instead.")


def check_outline(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-OUTLINE", "fab", "Board outline (Edge.Cuts)", "DFM")
    e = b.edge
    if not e.segs:
        r.add("FAB-OUTLINE", "error", "There is no board outline on the Edge.Cuts layer. The fab cannot cut the board.",
              fix="Draw one closed outline on Edge.Cuts (a rectangle with rounded corners is fine).")
        return
    if not e.closed:
        locs = [_loc(x, y, "Edge.Cuts", "open end") for x, y in e.open_points[:MAX_LOCS]]
        r.add("FAB-OUTLINE", "error",
              f"The board outline is not closed: {len(e.open_points)} line end(s) do not meet another line.",
              locs, fix="Zoom in on the marked ends on Edge.Cuts and join the lines so the outline is one closed shape.")
    x0, y0, x1, y1 = e.bbox
    w, h = x1 - x0, y1 - y0
    if min(w, h) < lim["min_board_side"]:
        r.add("FAB-OUTLINE", "warning",
              f"The board is {w:.1f} x {h:.1f} mm. Boards with a side under {lim['min_board_side']:g} mm need special handling at the fab.")


def check_zones_filled(c):
    r, b = c.r, c.b
    r.check("FAB-ZONES", "fab", "Copper pours filled", "DFM")
    unfilled = [z for z in b.zones if not z.keepout and any(l.endswith(".Cu") for l in z.layers) and not z.filled]
    if unfilled:
        locs = []
        for z in unfilled[:MAX_LOCS]:
            if z.outline:
                xs = [p[0] for p in z.outline]
                ys = [p[1] for p in z.outline]
                locs.append(_loc(sum(xs) / len(xs), sum(ys) / len(ys), ",".join(z.layers), f"{z.net or 'no net'} zone"))
        r.add("FAB-ZONES", "warning",
              f"{len(unfilled)} copper zone(s) are not filled ({', '.join(sorted({z.net or 'no net' for z in unfilled}))}). "
              "Unfilled zones are missing from the Gerbers unless KiCad refills them while plotting.",
              locs, fix="Press B (Edit > Fill All Zones) and save before running the checker and plotting Gerbers.")
    hatched = [z for z in b.zones if not z.keepout and z.hatch_fill]
    if hatched:
        r.add("FAB-ZONES", "info", f"{len(hatched)} zone(s) use a hatched fill. Use solid fills for power and ground.")


def check_track_width(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-TRACK", "fab", "Minimum track width", f"PCBWay {lim['min_track']} mm")
    bad = [t for t in b.tracks if t.w < lim["min_track"] - 1e-4 and t.layer.endswith(".Cu")]
    if bad:
        locs = [_loc((t.x1 + t.x2) / 2, (t.y1 + t.y2) / 2, t.layer, f"{t.w} mm {t.net}") for t in bad[:MAX_LOCS]]
        r.add("FAB-TRACK", "error",
              f"{len(bad)} track piece(s) are thinner than {lim['min_track']} mm (thinnest {min(t.w for t in bad)} mm). "
              "PCBWay charges extra below 6 mil.", locs,
              fix=f"Make every track at least {lim['min_track']} mm (0.2 mm or more for signals is easier).")


def check_clearance(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-CLEAR", "fab", "Copper-to-copper spacing", f"PCBWay {lim['min_space']} mm")
    floor = lim["min_space"] - 1e-3
    hits = {}
    for layer, lst in c.items.items():
        gi = c.index[layer]
        for i, it in enumerate(lst):
            kind, obj, net, sh, fp = it
            for _, other in gi.query(sh.bbox, floor):
                okind, oobj, onet, osh, ofp = other
                if oobj is obj or net == onet:
                    continue  # same net, or two pieces of unconnected copper
                if kind == "pad" and okind == "pad" and fp is ofp:
                    continue  # spacing inside one part is the footprint's business
                key = (id(obj), id(oobj)) if id(obj) < id(oobj) else (id(oobj), id(obj))
                if key in hits:
                    continue
                d = distance(sh, osh)
                if d < floor:
                    x, y = sh.center()
                    hits[key] = (d, layer, x, y, _desc(it), _desc(other))
    if hits:
        items = sorted(hits.values())
        locs = [_loc(x, y, l, f"{d:.3f} mm: {a} / {bb}") for d, l, x, y, a, bb in items[:MAX_LOCS]]
        r.add("FAB-CLEAR", "error",
              f"{len(items)} place(s) where copper of different nets is closer than {lim['min_space']} mm "
              f"(closest {items[0][0]:.3f} mm, 0 means touching = short circuit).", locs,
              fix="Move the tracks apart or run KiCad's DRC with a 0.2 mm clearance rule and fix what it shows.")


def _desc(it):
    kind, obj, net, sh, fp = it
    if kind == "pad":
        return f"{fp.ref}.{obj.number} [{net or 'no net'}]"
    if kind == "via":
        return f"via [{net or 'no net'}]"
    return f"track [{net or 'no net'}]"


def check_drills(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-DRILL", "fab", "Drill sizes and via types", f"PCBWay min drill {lim['min_drill']} mm")
    small, blind, big, aspect = [], [], [], []
    th = b.thickness or 1.6
    for v in b.vias:
        if v.vtype != "through":
            blind.append(_loc(v.x, v.y, "", f"{v.vtype} via"))
        if v.drill < lim["min_drill"] - 1e-4:
            small.append(_loc(v.x, v.y, "", f"via drill {v.drill} mm"))
        elif v.drill and th / v.drill > lim["aspect_ratio"]:
            aspect.append(_loc(v.x, v.y, "", f"via drill {v.drill} mm"))
    for p in b.pads:
        if p.drill:
            d = min(p.drill)
            if d < lim["min_drill"] - 1e-4:
                small.append(_loc(p.x, p.y, "", f"{p.label()} drill {d} mm"))
            if max(p.drill) > lim["max_drill"]:
                big.append(_loc(p.x, p.y, "", f"{p.label()} drill {max(p.drill)} mm"))
    if small:
        r.add("FAB-DRILL", "error", f"{len(small)} hole(s) are smaller than {lim['min_drill']} mm. "
              "Smaller holes cost extra at PCBWay.", small[:MAX_LOCS],
              fix="Use 0.3 mm drill / 0.6 mm diameter vias (or 0.4 / 0.8 mm for power).")
    if blind:
        r.add("FAB-DRILL", "error", f"{len(blind)} blind/buried/micro via(s). Only through vias are standard price.",
              blind[:MAX_LOCS], fix="Change them to through vias.")
    if aspect:
        r.add("FAB-DRILL", "warning", f"{len(aspect)} via(s) exceed the {lim['aspect_ratio']:g}:1 aspect ratio for a {th} mm board.",
              aspect[:MAX_LOCS])
    if big:
        r.add("FAB-DRILL", "info", f"{len(big)} hole(s) are larger than {lim['max_drill']} mm and will be milled. That is fine; just check the size.",
              big[:MAX_LOCS])


def check_rings(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-RING", "fab", "Annular rings", f"PCBWay via {lim['via_ring_min']} mm, pad {lim['pad_ring_min']} mm")
    err, warn = [], []
    for v in b.vias:
        ring = (v.size - v.drill) / 2
        if ring < lim["via_ring_min"] - 1e-4:
            err.append(_loc(v.x, v.y, "", f"via {v.size}/{v.drill} mm: ring {ring:.3f} mm"))
        elif ring < lim["via_ring_good"] - 1e-4:
            warn.append(_loc(v.x, v.y, "", f"via {v.size}/{v.drill} mm: ring {ring:.3f} mm"))
    for p in b.pads:
        if p.type == "thru_hole" and p.drill and p.layers:
            ring = (min(p.w, p.h) - min(p.drill)) / 2 if p.shape != "oval" or p.drill[0] == p.drill[1] else \
                min(p.w - p.drill[0], p.h - p.drill[1]) / 2
            if max(p.drill) <= 0.5 and max(p.w, p.h) <= 1.0:  # thermal/stitching via inside a footprint
                if ring < lim["via_ring_min"] - 1e-4:
                    err.append(_loc(p.x, p.y, "", f"{p.label()} (via): ring {ring:.3f} mm"))
                continue
            if ring < lim["pad_ring_min"] - 1e-4:
                err.append(_loc(p.x, p.y, "", f"{p.label()}: ring {ring:.3f} mm"))
            elif ring < lim["pad_ring_good"] - 1e-4:
                warn.append(_loc(p.x, p.y, "", f"{p.label()}: ring {ring:.3f} mm"))
    if err:
        r.add("FAB-RING", "error", f"{len(err)} hole(s) have a copper ring thinner than the fab minimum "
              f"(vias {lim['via_ring_min']} mm, component pads {lim['pad_ring_min']} mm). The drill can break out of the pad.",
              err[:MAX_LOCS], fix="Make the pad bigger or the hole smaller. Vias: 0.6 mm pad for a 0.3 mm hole.")
    if warn:
        r.add("FAB-RING", "info", f"{len(warn)} hole(s) have a ring just above the minimum. OK for the fab, but tight for hand soldering.",
              warn[:MAX_LOCS])


def check_slots(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-SLOT", "fab", "Slot widths", "PCBWay")
    bad = []
    for p in b.pads:
        if p.drill and abs(p.drill[0] - p.drill[1]) > 1e-3:
            w = min(p.drill)
            need = lim["plated_slot_min"] if p.type == "thru_hole" else lim["npth_slot_min"]
            if w < need - 1e-4:
                bad.append(_loc(p.x, p.y, "", f"{p.label()}: {'plated' if p.type == 'thru_hole' else 'non-plated'} slot {w} mm"))
    if bad:
        r.add("FAB-SLOT", "error", f"{len(bad)} slot(s) are narrower than PCBWay allows "
              f"(plated {lim['plated_slot_min']} mm, non-plated {lim['npth_slot_min']} mm).", bad)


def check_hole_spacing(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-HOLES", "fab", "Hole-to-hole spacing", f"PCBWay {lim['hole_to_hole_via']} / {lim['hole_to_hole_pad']} mm")
    holes = [(v.x, v.y, v.drill / 2, "via", None, "via") for v in b.vias if v.drill]
    for p in b.pads:
        if p.drill:
            holes.append((p.x, p.y, min(p.drill) / 2, "pad", p, p.label()))
    gi = GridIndex(2.0)
    for h in holes:
        gi.insert((h[0] - h[2], h[1] - h[2], h[0] + h[2], h[1] + h[2]), h)
    seen = set()
    bad = []
    for h in holes:
        for j, o in gi.query((h[0] - h[2], h[1] - h[2], h[0] + h[2], h[1] + h[2]), 0.5):
            if o is h or (id(o), id(h)) in seen:
                continue
            seen.add((id(h), id(o)))
            if h[4] is not None and o[4] is not None and h[4].fp is o[4].fp:
                continue  # holes inside one footprint are the part maker's design
            gap = math.hypot(h[0] - o[0], h[1] - o[1]) - h[2] - o[2]
            need = lim["hole_to_hole_via"] if h[3] == o[3] == "via" else lim["hole_to_hole_pad"]
            if gap < need - 1e-4:
                bad.append((gap, _loc((h[0] + o[0]) / 2, (h[1] + o[1]) / 2, "", f"{h[5]} / {o[5]}: {gap:.2f} mm")))
    if bad:
        bad.sort(key=lambda x: x[0])
        r.add("FAB-HOLES", "error", f"{len(bad)} pair(s) of holes are too close together "
              f"(min {lim['hole_to_hole_via']} mm between vias, {lim['hole_to_hole_pad']} mm otherwise; closest {bad[0][0]:.2f} mm).",
              [l for _, l in bad[:MAX_LOCS]], fix="Spread the vias out (about 1 mm pitch for a via array).")


def check_edge(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-EDGE", "fab", "Copper to board edge", f"PCBWay {lim['copper_to_edge_min']} mm, good {lim['copper_to_edge_good']} mm")
    if not b.edge.segs:
        r.skip("FAB-EDGE", "no board outline")
        return
    err, warn = [], []
    seen = set()
    for layer, lst in c.items.items():
        for kind, obj, net, sh, fp in lst:
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            d = c.edge_dist(sh, lim["copper_to_edge_good"])
            if d < lim["copper_to_edge_good"] - 0.01:
                x, y = sh.center()
                lab = _desc((kind, obj, net, sh, fp)) + f": {d:.2f} mm"
                (err if d < lim["copper_to_edge_min"] - 0.01 else warn).append(_loc(x, y, layer, lab))
    for z in b.zones:
        if z.keepout:
            continue
        worst = None
        for layer, pts in z.fills:
            step = max(1, len(pts) // 4000)
            for x, y in pts[::step]:
                sh = Shape.point(x, y, 0)
                d = c.edge_dist(sh, lim["copper_to_edge_good"])
                if d < lim["copper_to_edge_good"] - 0.01 and (worst is None or d < worst[0]):
                    worst = (d, x, y, layer)
        if worst:
            d, x, y, layer = worst
            (err if d < lim["copper_to_edge_min"] - 0.01 else warn).append(_loc(x, y, layer, f"{z.net or 'no net'} pour: {d:.2f} mm"))
    if err:
        r.add("FAB-EDGE", "error", f"{len(err)} copper item(s) are closer than {lim['copper_to_edge_min']} mm to the board edge. "
              "The router can cut into them and expose or short the copper.", err[:MAX_LOCS],
              fix="Move them in. For pours: Board Setup > Constraints > Copper to edge clearance = 0.5 mm, then refill (B).")
    if warn:
        r.add("FAB-EDGE", "warning", f"{len(warn)} copper item(s) are within {lim['copper_to_edge_good']} mm of the board edge.",
              warn[:MAX_LOCS], fix="Keep 0.5 mm between copper and the edge (more for high-voltage nets).")


def _silk_texts(b):
    for t in b.texts:
        if t.layer.endswith("SilkS") or t.layer.endswith("Silkscreen"):
            yield t
    for f in b.footprints:
        for t in f.texts:
            if t.visible and (t.layer.endswith("SilkS") or t.layer.endswith("Silkscreen")):
                yield t


def check_silk(c):
    r, b, lim = c.r, c.b, c.lim
    r.check("FAB-SILK", "fab", "Silkscreen text size", f"PCBWay {lim['silk_text_min']} mm height, {lim['silk_line_min']} mm line")
    err, warn, thin = [], [], []
    for t in _silk_texts(b):
        if not t.text or not t.height:
            continue
        lab = f"'{t.text[:20]}' {t.height} mm" + (f" ({t.owner.ref})" if t.owner else "")
        if t.height < lim["silk_text_min"] - 1e-3:
            err.append(_loc(t.x, t.y, t.layer, lab))
        elif t.height < lim["silk_text_good"] - 1e-3:
            warn.append(_loc(t.x, t.y, t.layer, lab))
        if t.thickness and t.thickness < lim["silk_line_min"] - 1e-3:
            thin.append(_loc(t.x, t.y, t.layer, f"'{t.text[:20]}' stroke {t.thickness} mm"))
    if err:
        r.add("FAB-SILK", "warning", f"{len(err)} silkscreen text(s) are smaller than {lim['silk_text_min']} mm and will not be readable.",
              err[:MAX_LOCS], fix="Make silkscreen text at least 1.0 mm high with a 0.15 mm stroke.")
    if warn:
        r.add("FAB-SILK", "info", f"{len(warn)} silkscreen text(s) are under 1.0 mm high.", warn[:MAX_LOCS])
    if thin:
        r.add("FAB-SILK", "info", f"{len(thin)} silkscreen text(s) have a stroke under {lim['silk_line_min']} mm and may print broken.",
              thin[:MAX_LOCS])


# ---------------------------------------------------------------------------
# Power stage


def check_power_found(c):
    r, a = c.r, c.a
    r.check("PWR-FOUND", "power", "Power stage recognised")
    missing = []
    if not a.magnetics:
        missing.append("a power inductor or transformer (reference L.. or T.., pads of 1 mm² or more)")
    if not a.mosfets and not a.switch_ics:
        missing.append("a power switch (MOSFET Q.. or a converter IC with a SW pin)")
    if not a.power_connectors:
        missing.append("input/output power connectors (J..) on the power nets")
    if missing:
        r.add("PWR-FOUND", "warning",
              "The checker could not find " + "; ".join(missing) + ". The power checks below may be incomplete.",
              fix="Use standard references (Q, L, D, C, J, U), keep footprints from the right library, "
                  "or name the nets in pcb_checker.json (see README).")
    if a.hc and not a.input and not a.transformers:
        r.add("PWR-FOUND", "info", "Could not tell which nets are the input side. Name the input net VIN (or list it under "
              "\"input\" in pcb_checker.json) so the 48 V checks use the right nets.")
    if a.hc and not a.output:
        r.add("PWR-FOUND", "info", "Could not tell which nets are the 12 V output. Name the output net VOUT (or list it under "
              "\"output\" in pcb_checker.json).")


def _power_graph(c, net):
    """Copper of one net as a graph; returns nodes, adjacency, costs."""
    b = c.b
    nodes = []
    for t in b.tracks:
        if t.net == net:
            nodes.append(("track", t))
    for v in b.vias:
        if v.net == net:
            nodes.append(("via", v))
    for p in c.a.net_pads.get(net, []):
        nodes.append(("pad", p))
    n_items = len(nodes)
    fill_node = {}
    for (n, layer), lst in c.fills.items():
        if n == net:
            for k, pts in enumerate(lst):
                fill_node[(layer, k)] = len(nodes)
                nodes.append(("fill", (layer, pts)))
    idx = {id(o): i for i, (_, o) in enumerate(nodes)}
    adj = defaultdict(set)
    gi = GridIndex(2.0)
    for i in range(n_items):
        gi.insert(nodes[i][1].geom.bbox, i)
    for i in range(n_items):
        k, o = nodes[i]
        li = _layers(k, o)
        for _, j in gi.query(o.geom.bbox, 0.01):
            if j <= i:
                continue
            kj, oj = nodes[j]
            if not li & _layers(kj, oj):
                continue
            if distance(o.geom, oj.geom) <= 0.005:
                adj[i].add(j)
                adj[j].add(i)
        if not fill_node:
            continue
        for layer in li:
            if k == "track":
                isl = set(c.islands_at(net, layer, o.x1, o.y1)) | set(c.islands_at(net, layer, o.x2, o.y2))
            elif k == "via":
                isl = c.islands_at(net, layer, o.x, o.y)
            else:
                isl = c.pad_islands(o, layer)
            for kk in isl:
                j = fill_node.get((layer, kk))
                if j is not None:
                    adj[i].add(j)
                    adj[j].add(i)
    # small costs for vias/pads/pours so a via only counts when the current has to pass through it
    step = {"via": 0.01, "pad": 0.001, "fill": 0.0001}
    cost = [o.length if k == "track" else step[k] for k, o in nodes]
    return nodes, adj, cost, idx


def _layers(kind, o):
    if kind == "track":
        return {o.layer}
    if kind == "via":
        return set(o.layers)
    if kind == "pad":
        return set(o.layers)
    return {o[0]}


def _dijkstra(adj, cost, src):
    dist = {src: cost[src]}
    pq = [(cost[src], src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, float("inf")):
            continue
        for v in adj[u]:
            nd = d + cost[v]
            if nd < dist.get(v, float("inf")) - 1e-9:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def _power_path(c, net):
    """Indexes of graph nodes that lie on a shortest path between two power terminals."""
    nodes, adj, cost, idx = _power_graph(c, net)
    terms = [idx[id(p)] for p in c.a.terminals.get(net, []) if id(p) in idx]
    terms = list(dict.fromkeys(terms))
    if len(terms) < 2:
        return nodes, set(), cost
    dists = {t: _dijkstra(adj, cost, t) for t in terms}
    on = set()
    for i, ti in enumerate(terms):
        for tj in terms[i + 1:]:
            if nodes[ti][1].fp is nodes[tj][1].fp:
                continue
            dij = dists[ti].get(tj)
            if dij is None:
                continue
            di, dj = dists[ti], dists[tj]
            for n in di:
                if n in dj and di[n] + dj[n] - cost[n] <= dij + 1e-6:
                    on.add(n)
    return nodes, on, cost


def check_power_paths(c):
    r, a = c.r, c.a
    r.check("PWR-WIDTH", "power", "Power track width for the rated current", "IPC-2221")
    r.check("PWR-VIAS", "power", "Vias where the power path changes layer", "~0.5 A per 0.3 mm via")
    rated = f"{a.i_out:g} A output" + (" (90 W overload bonus)" if a.overload else "")
    for net in sorted(a.hc, key=_natural):
        if not a.terminals.get(net):
            continue
        nodes, on, cost = _power_path(c, net)
        if not on:
            continue
        cur = a.net_current.get(net, a.i_out)
        narrow = []
        for i in on:
            k, o = nodes[i]
            if k != "track" or o.length < POWER["min_segment_len"]:
                continue
            mx, my = (o.x1 + o.x2) / 2, (o.y1 + o.y2) / 2
            if c.in_fill(net, o.layer, mx, my):
                continue
            outer = o.layer in c.outer
            rise = ipc2221_rise(cur, o.w, c.oz, outer)
            if rise > POWER["rise_warn"]:
                narrow.append((rise, o))
        if narrow:
            narrow.sort(key=lambda x: -x[0])
            worst, wt = narrow[0]
            need = ipc2221_width(cur, POWER["rise_warn"], c.oz, wt.layer in c.outer)
            sev = "error" if worst > POWER["rise_error"] else "warning"
            locs = [_loc((t.x1 + t.x2) / 2, (t.y1 + t.y2) / 2, t.layer, f"{t.w} mm, ~{rise:.0f} °C rise")
                    for rise, t in narrow[:MAX_LOCS]]
            hot = "more than 100" if worst > 100 else f"about {worst:.0f}"
            r.add("PWR-WIDTH", sev,
                  f"{net}: {len(narrow)} track piece(s) on the power path are too narrow for ~{cur:.1f} A. "
                  f"The narrowest ({wt.w} mm) would heat up by {hot} °C (IPC-2221, {c.oz:g} oz).",
                  locs, refs=[net],
                  fix=f"Make them at least {need:.1f} mm wide (20 °C rise) or replace them with a copper pour; "
                      "parallel copper on both layers, joined by vias, also works.")
        vias = [nodes[i][1] for i in on if nodes[i][0] == "via"]
        if vias:
            cap = sum(POWER["via_amps_04"] if v.drill >= 0.39 else POWER["via_amps_03"] * max(v.drill, 0.2) / 0.3 for v in vias)
            if cap < cur:
                need = math.ceil(cur / POWER["via_amps_03"])
                locs = [_loc(v.x, v.y, "", f"via {v.drill} mm") for v in vias[:MAX_LOCS]]
                r.add("PWR-VIAS", "warning",
                      f"{net}: the power path changes layer through {len(vias)} via(s), good for about {cap:.1f} A, "
                      f"but this net carries ~{cur:.1f} A.", locs, refs=[net],
                      fix=f"Use at least {need} vias of 0.3 mm (or fewer 0.4 mm ones), placed across the current flow, "
                          "or keep the power path on one layer.")


def check_hv_spacing(c):
    r, a = c.r, c.a
    r.check("PWR-SPACING", "power", "Spacing for 48 V (exposed pads)", "IPC-2221B A6")
    hv = {n for n, v in a.net_voltage.items() if v > 30}
    if not hv:
        r.skip("PWR-SPACING", "no nets above 30 V found")
        return
    bad = {}
    for layer in ("F.Cu", "B.Cu"):
        for kind, p, net, sh, fp in c.items.get(layer, []):
            if kind != "pad" or net not in hv:
                continue
            for _, o in c.index[layer].query(sh.bbox, 0.5):
                okind, op, onet, osh, ofp = o
                if okind != "pad" or ofp is fp or onet == net or not onet:
                    continue
                dv = abs(a.net_voltage.get(net, PROJECT["vin_max"]) - a.net_voltage.get(onet, 0.0))
                need = spacing_for(dv, POWER["pad_spacing"])
                key = tuple(sorted((id(p), id(op))))
                if key in bad:
                    continue
                d = distance(sh, osh)
                if d < need - 1e-3:
                    bad[key] = (d, need, dv, _loc((p.x + op.x) / 2, (p.y + op.y) / 2, layer,
                                                  f"{fp.ref}.{p.number} [{net}] / {ofp.ref}.{op.number} [{onet}]: {d:.2f} mm"))
    if bad:
        items = sorted(bad.values(), key=lambda x: x[0])
        r.add("PWR-SPACING", "warning",
              f"{len(items)} pad pair(s) with up to {max(i[2] for i in items):.0f} V between them are closer than IPC-2221B "
              f"allows for bare pads (closest {items[0][0]:.2f} mm, needs {items[0][1]} mm).",
              [i[3] for i in items[:MAX_LOCS]], fix="Move the parts apart; keep 0.3 mm or more around input and switch-node pads.")


def check_connectors(c):
    r, a, b = c.r, c.a, c.b
    r.check("PWR-CONN", "power", "Input/output connectors", "EE463 step 9")
    if not a.power_connectors:
        r.add("PWR-CONN", "warning", "No power connector found on the input or output nets. The board needs an input and an output connection that can carry the load current.")
        return
    for f in a.power_connectors:
        pads = f.copper_pads()
        if len(pads) >= 2:
            pitch = min(math.hypot(p.x - q.x, p.y - q.y) for i, p in enumerate(pads) for q in pads[i + 1:])
        else:
            pitch = 99
        per_net = defaultdict(int)
        for p in pads:
            if p.net in a.hc:
                per_net[p.net] += 1
        for net, cnt in per_net.items():
            cur = a.net_current.get(net, a.i_out)
            if pitch <= 2.6 and cur / cnt > 3.0:
                r.add("PWR-CONN", "warning",
                      f"{f.ref} ({f.value}) carries ~{cur:.1f} A on {net} through {cnt} pin(s) at {pitch:.2f} mm pitch. "
                      "Connectors with 2.54 mm pitch or less (pin headers, JST) are rated about 1-3 A per pin.",
                      [_loc(f.x, f.y, f.layer, f.ref)], refs=[f.ref],
                      fix="Use a 5.08 mm screw terminal, banana jacks or XT30/XT60, or put several pins in parallel.")
        if b.edge.segs and f.body:
            body = Shape.polygon(f.body)
            d = c.edge_dist(body, 30)
            if d > 5:
                r.add("PWR-CONN", "info", f"{f.ref} is {d:.0f} mm from the board edge. Power connectors are easier to use at the edge, facing out.",
                      [_loc(f.x, f.y, f.layer, f.ref)], refs=[f.ref])
        near = False
        for t in _silk_texts(b):
            if t.owner is not None and t.owner is not f and t.kind in ("ref", "value"):
                continue
            if math.hypot(t.x - f.x, t.y - f.y) < 10 + (math.sqrt(f.body_area) if f.body_area else 0) and \
                    re.search(r"[+\-]|GND|V|IN|OUT|0V", t.text, re.I) and not re.fullmatch(r"[A-Z]+\d+", t.text):
                near = True
                break
        if not near:
            r.add("PWR-CONN", "warning",
                  f"No polarity/voltage label found on the silkscreen next to {f.ref}. Swapped input wires destroy the board.",
                  [_loc(f.x, f.y, f.layer, f.ref)], refs=[f.ref],
                  fix="Add silkscreen text such as 'VIN 20-48V +  -' / '12V OUT +  -' next to each pin.")


def check_cap_voltage(c):
    r, a = c.r, c.a
    r.check("PWR-CAPV", "power", "Capacitor voltage ratings", "rating >= 1.25 x working voltage")
    unknown = []
    for f in a.caps:
        nets = {p.net for p in f.copper_pads()}
        if not nets & a.gnd:
            continue  # e.g. a bootstrap cap only sees the voltage between its own pins
        v_work = max((a.net_voltage.get(n, 0.0) for n in nets - a.gnd), default=0.0)
        if v_work <= 0:
            continue
        rating = voltage_rating(f)
        if rating is None:
            if nets & (a.input | a.output | a.sw):
                unknown.append(f.ref)
            continue
        need = v_work * POWER["cap_rating_margin"]
        if rating < v_work:
            r.add("PWR-CAPV", "error", f"{f.ref} ({f.value}) is rated {rating:g} V but sits on a ~{v_work:g} V net. It will fail.",
                  [_loc(f.x, f.y, f.layer, f.ref)], refs=[f.ref], fix=f"Use a part rated {math.ceil(need)} V or more (63 V for the 48 V input).")
        elif rating < need:
            r.add("PWR-CAPV", "warning", f"{f.ref} ({f.value}) is rated {rating:g} V on a ~{v_work:g} V net; keep at least 25 % margin "
                  "(and ceramic capacitors lose most of their capacitance near their rated voltage).",
                  [_loc(f.x, f.y, f.layer, f.ref)], refs=[f.ref], fix=f"Use a part rated {math.ceil(need)} V or more.")
    if unknown:
        r.add("PWR-CAPV", "info",
              f"Voltage rating unknown for {len(unknown)} power capacitor(s): {', '.join(sorted(unknown, key=_natural))}. "
              "Check them by hand: input side >= 63 V, output side >= 16 V.",
              fix="Put the rating in the value (e.g. '100uF 63V') or in a 'Voltage' field so the checker can read it.")


def _nearest(pad, pads):
    best = (float("inf"), None)
    for q in pads:
        d = distance(pad.geom, q.geom)
        if d < best[0]:
            best = (d, q)
    return best


def check_hot_loop(c):
    r, a = c.r, c.a
    r.check("PWR-LOOP", "power", "Hot loop: input capacitor at the switches", "SMPS-001/002")
    if not a.sw:
        r.skip("PWR-LOOP", "no switch node found")
        return
    cer = [f for f in a.input_caps if a.is_ceramic(f)]
    if not a.input_caps or not a.input:
        r.skip("PWR-LOOP", "input side not identified")
        return
    if not cer:
        r.add("PWR-LOOP", "warning", "No ceramic capacitor found between the input and ground. Electrolytic caps alone "
              "cannot supply the fast switching current; the switch node will ring.",
              fix="Put 1-3 ceramic capacitors (e.g. 2.2-10 µF 100 V X7R) right at the switches, across input and ground.")
        return
    cap_pads_in = [p for f in cer for p in f.copper_pads() if p.net in a.input]
    cap_pads_gnd = [p for f in cer for p in f.copper_pads() if p.net in a.gnd]
    switches = [f for f in a.mosfets + a.power_diodes + a.switch_ics
                if any(p.net in a.sw for p in f.copper_pads())]
    for f in switches:
        named = any(p.pinfunction for p in f.pads)
        for p in f.copper_pads():
            if p.net in a.input:
                pool = cap_pads_in
            elif p.net in a.gnd:
                pool = cap_pads_gnd
            else:
                continue
            if f in a.mosfets and a.fet_roles[f.ref].get(id(p)) == "G":
                continue
            if f in a.switch_ics:
                # only the converter IC's own power pins; without pin names, only its input pin
                if named and not IC_POWER_PIN_RE.match(p.pinfunction or ""):
                    continue
                if not named and p.net not in a.input:
                    continue
            d, q = _nearest(p, pool)
            if q is None:
                continue
            if d > POWER["hot_loop_cap_mm"]:
                r.add("PWR-LOOP", "warning",
                      f"{f.ref} pin {p.number} ({p.net}) is {d:.1f} mm from the nearest input ceramic capacitor ({q.fp.ref}). "
                      "The switching loop (input cap - switches - ground) should be as small as possible.",
                      [_loc(p.x, p.y, p.layers[0] if p.layers else "", f"{f.ref}.{p.number}"),
                       _loc(q.x, q.y, q.layers[0] if q.layers else "", q.fp.ref)], refs=[f.ref, q.fp.ref],
                      fix=f"Place a ceramic input capacitor within {POWER['hot_loop_cap_mm']:g} mm of the switch, on the same side, "
                          "connected without vias.")
                break
            if p.is_smd and q.is_smd and p.layers and q.layers and p.layers[0] != q.layers[0]:
                r.add("PWR-LOOP", "warning",
                      f"The nearest input ceramic capacitor {q.fp.ref} is on the other side of the board from {f.ref}. "
                      "The loop current then has to pass through vias.",
                      [_loc(p.x, p.y, p.layers[0], f.ref), _loc(q.x, q.y, q.layers[0], q.fp.ref)], refs=[f.ref, q.fp.ref])
                break


def check_gate_drive(c):
    r, a, b = c.r, c.a, c.b
    r.check("PWR-GATE", "power", "Gate driver close to the MOSFETs", "SMPS-014")
    if not a.gates:
        r.skip("PWR-GATE", "no MOSFET gates found")
        return
    for g in a.gates:
        if not g.driver:
            if g.fet in a.mosfets and any(p.net in a.sw for p in a.fet_power_pads(g.fet)):
                r.add("PWR-GATE", "info", f"Could not trace the gate of {g.fet.ref} ({g.gate_pad.net}) to a driver IC. "
                      "Check by hand that the driver is close and the gate loop is short.",
                      [_loc(g.gate_pad.x, g.gate_pad.y, "", g.fet.ref)], refs=[g.fet.ref])
            continue
        d = math.hypot(g.driver_pad.x - g.gate_pad.x, g.driver_pad.y - g.gate_pad.y)
        if d > POWER["gate_driver_mm"]:
            r.add("PWR-GATE", "warning",
                  f"{g.driver.ref} pin {g.driver_pad.number} is {d:.0f} mm from the gate of {g.fet.ref}. "
                  "A long gate loop slows switching and picks up noise.",
                  [_loc(g.gate_pad.x, g.gate_pad.y, "", f"{g.fet.ref} gate"),
                   _loc(g.driver_pad.x, g.driver_pad.y, "", f"{g.driver.ref}.{g.driver_pad.number}")],
                  refs=[g.fet.ref, g.driver.ref],
                  fix=f"Move the driver within about {POWER['gate_driver_mm']:g} mm of the MOSFET, and run the gate and its "
                      "return (source) side by side.")
        length = sum(t.length for t in b.tracks if t.net in g.nets)
        if length > POWER["gate_track_mm"]:
            r.add("PWR-GATE", "warning", f"The gate drive tracks of {g.fet.ref} ({', '.join(g.nets)}) are {length:.0f} mm long in total.",
                  [_loc(g.gate_pad.x, g.gate_pad.y, "", g.fet.ref)], refs=[g.fet.ref],
                  fix=f"Keep the gate drive under about {POWER['gate_track_mm']:g} mm.")


def check_bootstrap(c):
    r, a = c.r, c.a
    r.check("PWR-BOOT", "power", "Bootstrap capacitor at the driver", "SMPS-016")
    if not a.bootstrap:
        r.skip("PWR-BOOT", "no bootstrap capacitor found")
        return
    for cap, cp, icp in a.bootstrap:
        d = distance(cp.geom, icp.geom)
        if d > POWER["bootstrap_mm"]:
            r.add("PWR-BOOT", "warning", f"Bootstrap capacitor {cap.ref} is {d:.1f} mm from {icp.fp.ref} pin {icp.number}.",
                  [_loc(cp.x, cp.y, "", cap.ref), _loc(icp.x, icp.y, "", f"{icp.fp.ref}.{icp.number}")], refs=[cap.ref],
                  fix="Place it right next to the driver's boot/HB and SW/HS pins, on the same side, without vias.")


def check_feedback(c):
    r, a, b = c.r, c.a, c.b
    r.check("PWR-FB", "power", "Feedback divider and feedback routing", "SMPS-006/007")
    if not a.feedback:
        r.skip("PWR-FB", "no FB pin found (KiCad needs pin names from the schematic)")
        return
    sw_items = defaultdict(list)
    for layer, lst in c.items.items():
        for it in lst:
            if it[2] in a.sw:
                sw_items[layer].append(it[3])
    for (layer_net, layer), fills in c.fills.items():
        if layer_net in a.sw:
            for pts in fills:
                sw_items[layer].append(Shape.polygon(pts))
    for p, rs in a.feedback:
        for rf in rs:
            rp = [q for q in rf.copper_pads() if q.net == p.net]
            if rp:
                d = distance(rp[0].geom, p.geom)
                if d > POWER["fb_divider_mm"]:
                    r.add("PWR-FB", "warning", f"Feedback resistor {rf.ref} is {d:.0f} mm from {p.fp.ref} pin {p.number} ({p.pinfunction}). "
                          "A long feedback node picks up switching noise.",
                          [_loc(rp[0].x, rp[0].y, "", rf.ref), _loc(p.x, p.y, "", f"{p.fp.ref}.{p.number}")], refs=[rf.ref],
                          fix="Put the divider right at the FB pin and run the long track from the divider's top to the output instead.")
        close = []
        for t in b.tracks:
            if t.net != p.net:
                continue
            for sh in sw_items.get(t.layer, []):
                if distance(t.geom, sh) < POWER["fb_to_sw_mm"]:
                    close.append(_loc((t.x1 + t.x2) / 2, (t.y1 + t.y2) / 2, t.layer, "FB track near SW"))
                    break
        if close:
            r.add("PWR-FB", "warning", f"The feedback net {p.net} runs within {POWER['fb_to_sw_mm']:g} mm of switch-node copper.",
                  close[:MAX_LOCS], refs=[p.net], fix="Route the feedback away from the switch node and the inductor, ideally with ground between them.")


def check_under_magnetics(c):
    r, a, b = c.r, c.a, c.b
    r.check("PWR-MAG", "power", "No tracks under inductors and transformers", "SMPS-006")
    for f in a.magnetics:
        if not f.body:
            continue
        body = Shape.polygon(f.body)
        own = {p.net for p in f.pads}
        hits = defaultdict(list)
        for t in b.tracks:
            if t.net in own or t.net in a.gnd:
                continue
            if distance(t.geom, body) <= 0:
                hits[t.net].append(_loc((t.x1 + t.x2) / 2, (t.y1 + t.y2) / 2, t.layer, t.net))
        if hits:
            locs = [l for v in hits.values() for l in v][:MAX_LOCS]
            r.add("PWR-MAG", "warning",
                  f"Tracks of {', '.join(sorted(hits))} run under {f.ref}. The magnetic field couples noise into them.",
                  locs, refs=[f.ref], fix="Route around the inductor; only a ground pour should be under it.")


def check_thermal(c):
    r, a, b = c.r, c.a, c.b
    r.check("PWR-THERMAL", "power", "Copper for cooling the power parts", "THM-001/007")
    for f in a.mosfets + a.power_diodes + a.switch_ics:
        pads = f.copper_pads()
        if not pads:
            continue
        big = max(pads, key=lambda p: p.area)
        if f.attrs & {"through_hole"} or big.type == "thru_hole":
            if re.search(r"to-?220|to-?247|to-?3p", f.lib.lower()):
                hs = [g for g in b.footprints if re.search(r"heatsink|heat_sink", g.text_blob()) or g.prefix == "HS"]
                if not hs:
                    r.add("PWR-THERMAL", "info", f"{f.ref} is a through-hole power package. Check its losses: at 60 W it may need a heatsink (with insulation if the tab is not grounded).",
                          [_loc(f.x, f.y, f.layer, f.ref)], refs=[f.ref])
            continue
        if big.area < 3.0:
            continue
        layer = big.layers[0] if big.layers else "F.Cu"
        if not c.pad_touches_fill(big, layer):
            tracks = [t for t in b.tracks if t.net == big.net and t.layer == layer and distance(t.geom, big.geom) <= 0]
            widest = max((t.w for t in tracks), default=0)
            if widest < max(big.w, big.h) * 0.8:
                r.add("PWR-THERMAL", "warning",
                      f"{f.ref} pad {big.number} ({big.net}, {big.area:.0f} mm²) has no copper pour around it. SMD power parts "
                      "cool through the board copper.", [_loc(big.x, big.y, layer, f.ref)], refs=[f.ref],
                      fix="Add a copper zone on this net around the pad (a few cm²), on both layers joined by thermal vias.")
                continue
        if len(b.copper_layers) >= 2:
            nv = sum(1 for v in b.vias if v.net == big.net and distance(v.geom, big.geom) <= 1.5)
            if nv == 0:
                r.add("PWR-THERMAL", "info", f"No thermal vias at {f.ref} pad {big.number}. Vias under/next to the pad move heat to the other layer.",
                      [_loc(big.x, big.y, layer, f.ref)], refs=[f.ref], fix="Add 0.3 mm vias at about 1-1.2 mm pitch in or next to the pad.")


def check_ground(c):
    r, a, b = c.r, c.a, c.b
    r.check("PWR-GND", "power", "Ground pour", "STK-003")
    gz = [z for z in b.zones if not z.keepout and z.net in a.gnd]
    if not gz:
        r.add("PWR-GND", "warning", "There is no ground copper pour. A switching converter needs a low-impedance ground (ideally a solid plane under the power stage).",
              fix="Add a GND zone, at least on the bottom layer, and refill (B).")
    elif len(b.copper_layers) == 2 and not any("B.Cu" in z.layers for z in gz):
        r.add("PWR-GND", "info", "There is no ground pour on the bottom layer. On a 2-layer board, keep the bottom as unbroken ground as far as possible.")


# ---------------------------------------------------------------------------
# Layout


def check_decoupling(c):
    r, a = c.r, c.a
    r.check("LAY-DECAP", "layout", "Decoupling capacitors at IC supply pins", "PWR-006")
    has_pinfo = any(p.pintype or p.pinfunction for f in a.ics for p in f.pads)
    small = []
    for f in a.caps:
        pads = f.copper_pads()
        nets = {p.net for p in pads}
        v = a.cap_value.get(f.ref)
        if len(pads) == 2 and nets & a.gnd and (v is None or v <= POWER["small_cap_max_F"]) and not a.is_polarized(f):
            small.extend(p for p in pads if p.net not in a.gnd)
    by_net = defaultdict(list)
    for p in small:
        by_net[p.net].append(p)
    seen = set()
    for f in a.ics:
        for p in f.copper_pads():
            if not p.net or p.net in a.gnd:
                continue
            if has_pinfo:
                is_supply = p.pintype == "power_in" or bool(SUPPLY_PIN_RE.match(p.pinfunction or ""))
            else:
                bn = base_name(p.net)
                is_supply = p.net in by_net and bool(re.match(r"^\+|VCC|VDD|\d+V\d*|VREF|VBIAS", bn))
            if not is_supply or (f.ref, p.net) in seen:
                continue
            seen.add((f.ref, p.net))
            pool = by_net.get(p.net, [])
            if not pool:
                if p.net in a.hc:
                    continue  # covered by the hot-loop check
                r.add("LAY-DECAP", "warning", f"{f.ref} pin {p.number} ({p.pinfunction or p.net}) has no small (<= 1 µF) capacitor to ground on {p.net}.",
                      [_loc(p.x, p.y, p.layers[0] if p.layers else "", f"{f.ref}.{p.number}")], refs=[f.ref],
                      fix="Add a 100 nF ceramic capacitor right at the pin, with its ground pad going straight to ground.")
                continue
            d, q = _nearest(p, pool)
            if d > POWER["decap_mm"]:
                r.add("LAY-DECAP", "warning",
                      f"{f.ref} pin {p.number} ({p.pinfunction or p.net}): nearest decoupling capacitor {q.fp.ref} "
                      f"({fmt_cap(a.cap_value.get(q.fp.ref))}) is {d:.1f} mm away.",
                      [_loc(p.x, p.y, p.layers[0] if p.layers else "", f"{f.ref}.{p.number}"), _loc(q.x, q.y, "", q.fp.ref)],
                      refs=[f.ref, q.fp.ref], fix=f"Move it within ~{POWER['decap_mm']:g} mm (closer is better), same side as the IC.")


def check_angles(c):
    r, b = c.r, c.b
    r.check("LAY-ACUTE", "layout", "No acute track angles", "DFM-008")
    r.check("LAY-CORNER", "layout", "Track corners at 45°", "EST-001")
    nodes = defaultdict(list)
    for t in b.tracks:
        if t.kind != "seg" or t.length < 0.01:
            continue
        for (x, y), (ox, oy) in (((t.x1, t.y1), (t.x2, t.y2)), ((t.x2, t.y2), (t.x1, t.y1))):
            nodes[(t.layer, t.net, round(x, 3), round(y, 3))].append((ox - x, oy - y))
    acute, right = [], []
    gi = c.index
    for (layer, net, x, y), dirs in nodes.items():
        if len(dirs) < 2:
            continue
        pt = Shape.point(x, y, 0)
        if any(k in ("pad", "via") and distance(sh, pt) <= 0 for _, (k, o, n, sh, fp) in gi[layer].query(pt.bbox, 0.01)):
            continue
        for i in range(len(dirs)):
            for j in range(i + 1, len(dirs)):
                ax, ay = dirs[i]
                bx, by = dirs[j]
                cosang = (ax * bx + ay * by) / (math.hypot(ax, ay) * math.hypot(bx, by))
                ang = math.degrees(math.acos(max(-1, min(1, cosang))))
                if ang < 89:
                    acute.append(_loc(x, y, layer, f"{ang:.0f}° on {net}"))
                elif ang < 91 and len(dirs) == 2:
                    right.append(_loc(x, y, layer, f"90° on {net}"))
    if acute:
        r.add("LAY-ACUTE", "warning", f"{len(acute)} track junction(s) form an acute angle (< 90°). Acute corners trap etchant and make weak copper.",
              acute[:MAX_LOCS], fix="Redraw those corners as two 45° bends.")
    if right:
        r.add("LAY-CORNER", "info", f"{len(right)} track corner(s) are 90°. Use 45° corners (or arcs).", right[:MAX_LOCS])


def check_dangling(c):
    r, b = c.r, c.b
    r.check("LAY-DANGLE", "layout", "No dangling track ends", "EST-009")
    bad = []
    ends = defaultdict(int)
    for t in b.tracks:
        for x, y in ((t.x1, t.y1), (t.x2, t.y2)):
            ends[(t.layer, t.net, round(x, 3), round(y, 3))] += 1
    for t in b.tracks:
        for x, y in ((t.x1, t.y1), (t.x2, t.y2)):
            if ends[(t.layer, t.net, round(x, 3), round(y, 3))] >= 2:
                continue  # meets another track end exactly
            pt = Shape.point(x, y, 0)
            ok = False
            for _, (k, o, n, sh, fp) in c.index[t.layer].query(pt.bbox, max(t.w, 0.05)):
                if o is t:
                    continue
                if n != t.net and t.net:
                    continue
                if distance(sh, pt) <= t.w / 2 + 0.005:
                    ok = True
                    break
            if not ok and c.in_fill(t.net, t.layer, x, y):
                ok = True
            if not ok:
                bad.append(_loc(x, y, t.layer, t.net or "no net"))
    if bad:
        r.add("LAY-DANGLE", "warning", f"{len(bad)} track end(s) are not connected to anything (leftover pieces or broken connections).",
              bad[:MAX_LOCS], fix="Delete the leftover pieces or finish the connection.")


def check_via_in_pad(c):
    r, b = c.r, c.b
    r.check("LAY-VIAPAD", "layout", "No open vias in SMD pads", "VIA-001")
    bad = []
    for v in b.vias:
        for layer in ("F.Cu", "B.Cu"):
            for _, (k, p, n, sh, fp) in c.index.get(layer, GridIndex()).query(v.geom.bbox, 0):
                if k != "pad" or not p.is_smd:
                    continue
                if p.area >= 4.0 or re.match(r"^(EP|PAD|TAB|0)$", p.pinfunction or p.number or "", re.I):
                    continue
                if sh.contains_point(v.x, v.y):
                    bad.append(_loc(v.x, v.y, layer, f"via in {fp.ref}.{p.number}"))
    if bad:
        r.add("LAY-VIAPAD", "warning", f"{len(bad)} via(s) sit inside small SMD pads. Solder flows down the open via and the joint starves.",
              bad[:MAX_LOCS], fix="Move the via next to the pad with a short track (0.25 mm or more from the pad edge).")


# ---------------------------------------------------------------------------
# Testing, assembly, mechanics


def check_test_points(c):
    r, a = c.r, c.a
    r.check("TST-POINTS", "test", "Test points (EE463: verify supplies and gate signals)", "TST-001")
    probe_nets = defaultdict(list)
    for f in a.test_points:
        for p in f.copper_pads():
            if p.net:
                probe_nets[p.net].append(f.ref)
    for f in a.connectors:
        for p in f.copper_pads():
            if p.net:
                probe_nets[p.net].append(f.ref)

    def has(nets):
        return any(n in probe_nets for n in nets)

    if not a.test_points:
        r.add("TST-POINTS", "warning", "The board has no test points. EE463 asks you to check the auxiliary supplies and gate signals before powering the power stage.",
              fix="Add test points (or a small header) for ground, each auxiliary supply, each gate signal and the switch node.")
    if a.gnd and not any(n in probe_nets and any(x.startswith("TP") for x in probe_nets[n]) for n in a.gnd):
        r.add("TST-POINTS", "warning", "No test point on ground. Every probe needs a ground point nearby.",
              fix="Add one or two GND test points (a loop or hook type is easiest for scope probes).")
    switching = [g for g in a.gates if not a.sw or any(p.net in a.sw for p in a.fet_power_pads(g.fet))]
    for g in switching:
        if g.fet in a.mosfets and not has(g.nets) and not any(
                p.net in probe_nets for p in ([g.driver_pad] if g.driver_pad else [])):
            r.add("TST-POINTS", "warning", f"No test point on the gate signal of {g.fet.ref} ({' / '.join(g.nets)}).",
                  [_loc(g.gate_pad.x, g.gate_pad.y, "", g.fet.ref)], refs=[g.fet.ref],
                  fix="Add a test point on the gate (or the driver output) so you can see the gate waveform.")
    aux = set()
    for f in a.ics:
        for p in f.copper_pads():
            if p.net and p.net not in a.gnd and p.net not in a.hc and (
                    p.pintype == "power_in" or SUPPLY_PIN_RE.match(p.pinfunction or "")):
                aux.add(p.net)
    for n in sorted(aux, key=_natural):
        if n not in probe_nets:
            r.add("TST-POINTS", "warning", f"No test point on the auxiliary supply {n}.", refs=[n],
                  fix="Add a test point so you can check this supply before turning on the power stage.")
    for n in sorted(a.sw, key=_natural):
        if n not in probe_nets:
            r.add("TST-POINTS", "info", f"No test point on the switch node {n}. It is useful for checking the switching waveform.", refs=[n])
    for side, nets in (("input", a.input), ("output", a.output)):
        if nets and not has(nets):
            r.add("TST-POINTS", "warning", f"No connector or test point on the {side} side ({', '.join(sorted(nets))}).")


def check_board_info(c):
    r, b = c.r, c.b
    r.check("TST-INFO", "test", "Board identification on the silkscreen", "SLK-008")
    texts = " | ".join(t.text for t in _silk_texts(b) if t.text)
    if not re.search(r"EE\s*463|group|grp|team|\bG\d+\b", texts, re.I):
        r.add("TST-INFO", "info", "No course/group name found on the silkscreen. All groups' boards come back from the fab together.",
              fix="Add 'EE463 Group <n>' and your names on the silkscreen.")
    if not re.search(r"\$\{REVISION\}|\brev\.?\s*[A-Z0-9]|\bv\d+(\.\d+)?\b|\bR\d\b", texts, re.I):
        r.add("TST-INFO", "info", "No revision found on the silkscreen (e.g. 'Rev A' or 'v1.0'). You may order a second version.")


def check_pad_spacing(c):
    r, b = c.r, c.b
    r.check("ASM-SPACING", "test", "Room between parts for hand soldering", f">= {ASSEMBLY['pad_gap_hand']} mm pad to pad")
    pairs = {}
    for layer in ("F.Cu", "B.Cu"):
        for kind, p, net, sh, fp in c.items.get(layer, []):
            if kind != "pad":
                continue
            for _, (k2, q, n2, sh2, fp2) in c.index[layer].query(sh.bbox, ASSEMBLY["pad_gap_hand"]):
                if k2 != "pad" or fp2 is fp:
                    continue
                key = tuple(sorted((fp.ref, fp2.ref)))
                d = distance(sh, sh2)
                if d < ASSEMBLY["pad_gap_hand"] - 1e-3 and (key not in pairs or d < pairs[key][0]):
                    pairs[key] = (d, _loc((p.x + q.x) / 2, (p.y + q.y) / 2, layer, f"{key[0]} / {key[1]}: {d:.2f} mm"))
    if pairs:
        items = sorted(pairs.values(), key=lambda x: x[0])
        r.add("ASM-SPACING", "warning", f"{len(items)} pair(s) of parts have pads closer than {ASSEMBLY['pad_gap_hand']} mm "
              f"(closest {items[0][0]:.2f} mm). That is hard to solder and rework by hand.",
              [l for _, l in items[:MAX_LOCS]], fix="Spread them to 0.5 mm or more between pads.")


def check_small_parts(c):
    r, b = c.r, c.b
    r.check("ASM-SMALL", "test", "Part sizes you can hand-solder", "0603 or larger")
    small = [f for f in b.footprints if re.search(r"(?<!\d)(0402|0201|01005)(_|$)|_(1005|0603|0402)Metric", f.lib)]
    if small:
        r.add("ASM-SMALL", "warning", f"{len(small)} part(s) use 0402 or smaller packages: "
              f"{', '.join(sorted((f.ref for f in small), key=_natural)[:30])}. These are very hard to solder by hand.",
              [_loc(f.x, f.y, f.layer, f.ref) for f in small[:MAX_LOCS]], fix="Use 0603 or 0805 parts.")


def check_mounting(c):
    r, a, b = c.r, c.a, c.b
    r.check("MEC-HOLES", "test", "Mounting holes", "MEC-002/011")
    if not a.mount_holes:
        r.add("MEC-HOLES", "info", "No mounting holes. Holes for M3 standoffs keep the board off the bench and are needed for an enclosure (compactness bonus).")
        return
    for h in a.mount_holes:
        own = {p.net for p in h.pads if p.net}
        bad = []
        center = Shape.point(h.x, h.y, ASSEMBLY["mount_hole_keepout"])
        for layer, lst in c.items.items():
            for _, (k, o, n, sh, fp) in c.index[layer].query(center.bbox, 0):
                if fp is h or (n and n in own) or (n in a.gnd and own & a.gnd):
                    continue
                if distance(sh, center) <= 0:
                    bad.append(_desc((k, o, n, sh, fp)))
        if bad:
            r.add("MEC-HOLES", "warning", f"{len(bad)} item(s) are within {ASSEMBLY['mount_hole_keepout']:g} mm of mounting hole {h.ref} "
                  "(the screw head / washer area): " + ", ".join(sorted(set(bad))[:8]),
                  [_loc(h.x, h.y, "", h.ref)], refs=[h.ref], fix="Keep an 8 mm circle around M3 holes free of parts and tracks.")
        if b.edge.segs:
            d = c.edge_dist(Shape.point(h.x, h.y, 0), 10)
            if d < ASSEMBLY["mount_hole_edge"]:
                r.add("MEC-HOLES", "info", f"Mounting hole {h.ref} is {d:.1f} mm from the board edge (centre). 4 mm or more is stronger.",
                      [_loc(h.x, h.y, "", h.ref)], refs=[h.ref])


ALL_CHECKS = [
    check_stackup, check_outline, check_zones_filled, check_track_width, check_clearance, check_drills,
    check_rings, check_slots, check_hole_spacing, check_edge, check_silk,
    check_power_found, check_power_paths, check_hv_spacing, check_connectors, check_cap_voltage,
    check_hot_loop, check_gate_drive, check_bootstrap, check_feedback, check_under_magnetics, check_thermal,
    check_ground,
    check_decoupling, check_angles, check_dangling, check_via_in_pad,
    check_test_points, check_board_info, check_pad_spacing, check_small_parts, check_mounting,
]


def run_kicad_checks(board, report, overrides=None, overload=False, oz=None, progress=None):
    c = Ctx(board, report, overrides, overload, oz)
    for fn in ALL_CHECKS:
        if progress:
            progress(fn.__name__)
        try:
            fn(c)
        except Exception as e:  # one broken check must not stop the others
            cid = f"INTERNAL-{fn.__name__}"
            report.check(cid, "layout", f"Checker error in {fn.__name__}")
            report.add(cid, "info", f"This check crashed ({type(e).__name__}: {e}). Please report it to the course staff.")
    return c
