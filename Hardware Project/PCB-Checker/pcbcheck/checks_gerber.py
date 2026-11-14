"""Manufacturing checks on Gerber + Excellon files (works for any EDA tool)."""

import math
from collections import Counter

from .geometry import Shape, GridIndex, distance, point_in_poly
from .gerber import LAYER_NAMES
from .rules import fab_limits

MAX_LOCS = 40


class _UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def _outline_segments(fs):
    return fs.outline_segments()[0]


def _copper_objects(layer):
    """(shape, region_id or None) for every copper primitive; region edges become separate shapes."""
    objs = []
    regions = []

    def net_of(lst, i):
        return lst[i] if i < len(lst) else ""

    for i, (x1, y1, x2, y2, w, fn, rnd) in enumerate(layer.draws):
        if w <= 0:
            continue
        objs.append((Shape.segment(x1, y1, x2, y2, w / 2), None, ("track", w, net_of(layer.draw_nets, i))))
    for i, (pts, w, fn) in enumerate(layer.arcs):
        if w > 0 and len(pts) >= 2:
            # one shape per arc piece keeps the distance checks fast on coils and round boards
            for k in range(len(pts) - 1):
                objs.append((Shape.segment(pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], w / 2), None,
                             ("track", w, net_of(layer.arc_nets, i))))
    for i, (x, y, ap) in enumerate(layer.flashes):
        if ap.w > 0:
            objs.append((ap.shape_at(x, y), None, ("pad", ap, net_of(layer.flash_nets, i))))
    for k, pts in enumerate(layer.regions):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        regions.append((pts, (min(xs), min(ys), max(xs), max(ys))))
        n = len(pts)
        rn = net_of(layer.region_nets, k)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            objs.append((Shape.segment(x1, y1, x2, y2, 0.0), k, ("region", k, rn)))
    return objs, regions


def check_files(fs, r):
    r.check("GBR-FILES", "submission", "Gerber and drill files complete", "PCBWay order")
    kinds = Counter(l.kind for l in fs.layers)
    drills = fs.drills
    need = [("copper_top", "error"), ("copper_bottom", "error"), ("outline", "error"),
            ("mask_top", "warning"), ("mask_bottom", "warning"), ("silk_top", "info")]
    for k, sev in need:
        if not kinds.get(k):
            extra = " If the outline is only inside a drawing file (e.g. a fabrication drawing), export it as its own Gerber." \
                if k == "outline" else ""
            r.add("GBR-FILES", sev, f"No {LAYER_NAMES[k].lower()} file found.",
                  fix="Plot again with this layer selected (KiCad: File > Fabrication Outputs > Gerbers). "
                      "If the file is there, give it a standard name or extension (e.g. .GTL/.GBL/.GKO)." + extra)
    if not drills:
        r.add("GBR-FILES", "error", "No drill file (Excellon) found. Without it the board gets no holes.",
              fix="Generate the drill files too (KiCad: Generate Drill Files... in the Gerber dialog).")
    elif not any(h for d in drills for h in d.holes):
        r.add("GBR-FILES", "warning", "The drill file(s) contain no holes.")
    for d in drills:
        if getattr(d, "format_unknown", False):
            r.add("GBR-FILES", "warning",
                  f"{d.name} does not say its units or number format. The checker guessed them from the board size, "
                  "but the fab may guess differently and drill the holes in the wrong places.",
                  fix="Export the drill file with units and decimal points (Excellon with a METRIC/INCH header), "
                      "or include the drill format file your EDA tool writes next to it.")
    if kinds.get("extra"):
        names = ", ".join(l.name for l in fs.layers if l.kind == "extra")
        r.add("GBR-FILES", "info", f"These files are not needed by the fab and can be left out of the zip: {names}.")
    if kinds.get("other"):
        names = ", ".join(l.name for l in fs.layers if l.kind == "other")
        r.add("GBR-FILES", "info", f"Could not tell what these files are: {names}. Check that the fab will recognise them.")
    for s in fs.skipped:
        r.add("GBR-FILES", "info", f"Skipped {s}.")


def check_layers(fs, r, lim):
    r.check("GBR-LAYERS", "fab", "Copper layer count", "PCBWay standard price")
    n = len(fs.copper())
    if n and n != lim["layers"]:
        r.add("GBR-LAYERS", "warning", f"The files have {n} copper layers. PCBWay's standard price is for {lim['layers']} layers.")
    if any(l.clear_polarity for l in fs.copper()):
        r.add("GBR-LAYERS", "info", "Some copper layers use clear (negative) polarity. The spacing check skips those layers; check them in a Gerber viewer.")


def check_outline(fs, r, lim):
    r.check("GBR-OUTLINE", "fab", "Board outline", "DFM")
    segs, ignored, closed = fs.outline_segments()
    if not segs:
        r.skip("GBR-OUTLINE", "no outline file")
        return None
    if not closed:
        cnt = Counter()
        for x1, y1, x2, y2 in segs:
            cnt[(round(x1, 2), round(y1, 2))] += 1
            cnt[(round(x2, 2), round(y2, 2))] += 1
        odd = [p for p, c in cnt.items() if c % 2]
        r.add("GBR-OUTLINE", "error", f"The board outline is not closed: {len(odd)} line end(s) do not meet another line.",
              [(x, y, "outline", "open end") for x, y in odd[:MAX_LOCS]],
              fix="Check the outline in a Gerber viewer; it must be one closed shape.")
    elif ignored:
        r.add("GBR-OUTLINE", "info", f"{ignored} line(s) on the outline layer do not look like the board edge (dimensions, notes "
              "or drawings) and were ignored. Make sure the fab only gets the board edge on this layer.")
    xs = [s[0] for s in segs] + [s[2] for s in segs]
    ys = [s[1] for s in segs] + [s[3] for s in segs]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if min(w, h) < lim["min_board_side"]:
        r.add("GBR-OUTLINE", "warning", f"The board is {w:.1f} x {h:.1f} mm, smaller than {lim['min_board_side']:g} mm on a side.")
    return (min(xs), min(ys), max(xs), max(ys))


def check_tracks(fs, r, lim):
    r.check("GBR-TRACK", "fab", "Minimum track width", f"PCBWay {lim['min_track']} mm")
    bad = []
    for l in fs.copper():
        for x1, y1, x2, y2, w, fn, rnd in l.draws:
            if 0 < w < lim["min_track"] - 1e-4 and "NonConductor" not in (fn or ""):
                bad.append((w, ((x1 + x2) / 2, (y1 + y2) / 2, l.name, f"{w:.3f} mm")))
        for pts, w, fn in l.arcs:
            if 0 < w < lim["min_track"] - 1e-4:
                bad.append((w, (pts[len(pts) // 2][0], pts[len(pts) // 2][1], l.name, f"{w:.3f} mm arc")))
    if bad:
        bad.sort(key=lambda x: x[0])
        r.add("GBR-TRACK", "error", f"{len(bad)} copper line(s) are thinner than {lim['min_track']} mm (thinnest {bad[0][0]:.3f} mm).",
              [b for _, b in bad[:MAX_LOCS]], fix=f"Make tracks at least {lim['min_track']} mm wide.")


def check_drills(fs, r, lim):
    r.check("GBR-DRILL", "fab", "Drill sizes", f"PCBWay min {lim['min_drill']} mm")
    small, big, slots = [], [], []
    for d in fs.drills:
        for x, y, dia, plated in d.holes:
            if dia < lim["min_drill"] - 1e-4:
                small.append((x, y, d.name, f"{dia:.3f} mm"))
            elif dia > lim["max_drill"]:
                big.append((x, y, d.name, f"{dia:.2f} mm"))
        for x1, y1, x2, y2, w, plated in d.slots:
            need = lim["plated_slot_min"] if plated else lim["npth_slot_min"]
            if w < need - 1e-4:
                slots.append(((x1 + x2) / 2, (y1 + y2) / 2, d.name, f"{'plated' if plated else 'non-plated'} slot {w:.2f} mm"))
    blind = [d for d in fs.drills if getattr(d, "blind", False) and (d.holes or d.slots)]
    if blind:
        locs = [(x, y, d.name, "blind/buried via") for d in blind for x, y, _, _ in d.holes][:MAX_LOCS]
        r.add("GBR-DRILL", "error", f"The drill files include blind or buried vias ({', '.join(d.name for d in blind)}). "
              "They are not part of PCBWay's standard price.", locs, fix="Use only through vias.")
    if small:
        r.add("GBR-DRILL", "error", f"{len(small)} hole(s) are smaller than {lim['min_drill']} mm (extra cost at PCBWay).",
              small[:MAX_LOCS], fix="Use 0.3 mm or larger holes.")
    if slots:
        r.add("GBR-DRILL", "error", f"{len(slots)} slot(s) are too narrow for PCBWay.", slots[:MAX_LOCS])
    if big:
        r.add("GBR-DRILL", "info", f"{len(big)} hole(s) are larger than {lim['max_drill']} mm and will be milled.", big[:MAX_LOCS])


def _flash_index(fs):
    idx = {}
    for l in fs.copper():
        gi = GridIndex(1.0)
        for x, y, ap in l.flashes:
            gi.insert((x, y, x, y), (x, y, ap))
        idx[l.name] = gi
    return idx


def check_rings(fs, r, lim):
    r.check("GBR-RING", "fab", "Annular rings", f"PCBWay via {lim['via_ring_min']} mm, pad {lim['pad_ring_min']} mm")
    outer = [l for l in fs.copper() if l.kind in ("copper_top", "copper_bottom")]
    if not outer or not fs.drills:
        r.skip("GBR-RING", "needs copper and drill files")
        return
    fidx = _flash_index(fs)
    err, warn = [], []
    for d in fs.drills:
        for x, y, dia, plated in d.holes:
            if not plated:
                continue
            for l in outer:
                hits = [it for _, it in fidx[l.name].query((x, y, x, y), 0.02)]
                # a pad no bigger than the hole: the EDA tool removed the unused ring on this layer
                hits = [h for h in hits if h[2].size_min() > dia + 0.01]
                if not hits:
                    continue
                ap = hits[0][2]
                ring = (ap.size_min() - dia) / 2
                is_via = "Via" in (ap.function or "") or (dia <= 0.5 and ap.size_min() <= 1.0)
                mn = lim["via_ring_min"] if is_via else lim["pad_ring_min"]
                good = lim["via_ring_good"] if is_via else lim["pad_ring_good"]
                lab = f"{'via' if is_via else 'pad'} {ap.size_min():.2f}/{dia:.2f} mm: ring {ring:.3f} mm"
                if ring < mn - 1e-4:
                    err.append((x, y, l.name, lab))
                elif ring < good - 1e-4:
                    warn.append((x, y, l.name, lab))
                break
    if err:
        r.add("GBR-RING", "error", f"{len(err)} plated hole(s) have a copper ring below the fab minimum.", err[:MAX_LOCS],
              fix="Make the pads bigger or the holes smaller (vias: 0.6 mm pad for a 0.3 mm hole).")
    if warn:
        r.add("GBR-RING", "info", f"{len(warn)} plated hole(s) have a ring just above the minimum.", warn[:MAX_LOCS])


def check_hole_spacing(fs, r, lim):
    r.check("GBR-HOLES", "fab", "Hole-to-hole spacing", f"PCBWay {lim['hole_to_hole_via']} / {lim['hole_to_hole_pad']} mm")
    holes = list(fs.all_holes())
    gi = GridIndex(2.0)
    for h in holes:
        gi.insert((h[0] - h[2] / 2, h[1] - h[2] / 2, h[0] + h[2] / 2, h[1] + h[2] / 2), h)
    bad = []
    seen = set()
    for h in holes:
        for _, o in gi.query((h[0] - h[2] / 2, h[1] - h[2] / 2, h[0] + h[2] / 2, h[1] + h[2] / 2), 0.5):
            if o is h or (id(o), id(h)) in seen:
                continue
            seen.add((id(h), id(o)))
            gap = math.hypot(h[0] - o[0], h[1] - o[1]) - h[2] / 2 - o[2] / 2
            if gap <= -min(h[2], o[2]) / 2:
                continue  # same hole listed twice / slot centre
            need = lim["hole_to_hole_via"] if max(h[2], o[2]) <= 0.45 else lim["hole_to_hole_pad"]
            if gap < need - 1e-4:
                lab = "holes overlap" if gap < 0 else f"{gap:.2f} mm"
                bad.append((gap, ((h[0] + o[0]) / 2, (h[1] + o[1]) / 2, "drill", lab)))
    if bad:
        bad.sort(key=lambda x: x[0])
        worst = "some overlap" if bad[0][0] < 0 else f"closest {bad[0][0]:.2f} mm"
        r.add("GBR-HOLES", "error", f"{len(bad)} pair(s) of holes are too close ({worst}).",
              [b for _, b in bad[:MAX_LOCS]],
              fix="Spread the holes apart. If overlapping hits are meant to make a slot, draw a proper slot (oval hole) instead.")


def check_edge(fs, r, lim):
    r.check("GBR-EDGE", "fab", "Copper to board edge", f"PCBWay {lim['copper_to_edge_min']} mm")
    segs = _outline_segments(fs)
    if not segs:
        r.skip("GBR-EDGE", "no outline file")
        return
    gi = GridIndex(5.0)
    for s in segs:
        sh = Shape.segment(*s, 0.0)
        gi.insert(sh.bbox, sh)
    err, warn = [], []
    for l in fs.copper():
        objs, regions = _copper_objects(l)
        worst_region = {}
        for sh, rid, info in objs:
            best = min((distance(sh, e) for _, e in gi.query(sh.bbox, lim["copper_to_edge_good"])), default=99)
            if best < lim["copper_to_edge_good"] - 0.01:
                x, y = sh.center()
                if rid is not None:
                    if rid not in worst_region or best < worst_region[rid][0]:
                        worst_region[rid] = (best, x, y)
                    continue
                (err if best < lim["copper_to_edge_min"] - 0.01 else warn).append((x, y, l.name, f"{info[0]}: {best:.2f} mm"))
        for rid, (best, x, y) in worst_region.items():
            (err if best < lim["copper_to_edge_min"] - 0.01 else warn).append((x, y, l.name, f"pour: {best:.2f} mm"))
    on_line = sum(1 for e in err if e[3].endswith(": 0.00 mm"))
    if on_line > 200:
        # hundreds of copper pieces lying exactly on "edge" lines: the outline file also holds drawings of the copper
        r.skip("GBR-EDGE", "the outline file seems to contain drawings of the copper too")
        r.check("GBR-OUTLINE", "fab", "Board outline", "DFM")
        r.add("GBR-OUTLINE", "warning", f"{on_line} copper pieces lie exactly on lines of the outline file, so it seems to hold "
              "drawings besides the board edge. The fab could cut along them. The copper-to-edge check was skipped.",
              fix="Export an outline file (e.g. .GKO or Edge.Cuts) that contains only the board edge and cut-outs.")
        return
    if err:
        r.add("GBR-EDGE", "error", f"{len(err)} copper item(s) are closer than {lim['copper_to_edge_min']} mm to the board edge.",
              err[:MAX_LOCS], fix="Pull copper (and pours) at least 0.5 mm back from the outline.")
    if warn:
        r.add("GBR-EDGE", "warning", f"{len(warn)} copper item(s) are within {lim['copper_to_edge_good']} mm of the board edge.", warn[:MAX_LOCS])


def check_spacing(fs, r, lim):
    r.check("GBR-CLEAR", "fab", "Copper-to-copper spacing", f"PCBWay {lim['min_space']} mm")
    floor = lim["min_space"] - 1e-3
    hits = []
    for l in fs.copper():
        if l.clear_polarity:
            continue
        objs, regions = _copper_objects(l)
        n = len(objs)
        uf = _UF(n + len(regions))
        gi = GridIndex(1.0)
        for i, (sh, rid, info) in enumerate(objs):
            gi.insert(sh.bbox, i)
            if rid is not None:
                uf.union(i, n + rid)
        # items inside a pour belong to it
        for i, (sh, rid, info) in enumerate(objs):
            if rid is not None:
                continue
            x, y = sh.segs[0][0], sh.segs[0][1]
            for k, (pts, bb) in enumerate(regions):
                if bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3] and point_in_poly(x, y, pts):
                    uf.union(i, n + k)
        # without net names, shapes almost touching (< 0.02 mm) are taken as one piece of copper
        has_nets = any(layer_nets for layer_nets in (l.draw_nets + l.flash_nets + l.region_nets))
        tol = 0.001 if has_nets else 0.02
        for i, (sh, rid, info) in enumerate(objs):
            for _, j in gi.query(sh.bbox, tol):
                if j > i and distance(sh, objs[j][0]) <= tol:
                    uf.union(i, j)
        seen = set()
        for i, (sh, rid, info) in enumerate(objs):
            gi_i = uf.find(i)
            for _, j in gi.query(sh.bbox, floor):
                if j <= i:
                    continue
                gj = uf.find(j)
                if gi_i == gj or (gi_i, gj) in seen:
                    continue
                na, nb = info[-1], objs[j][2][-1]
                if na and na == nb:
                    continue  # same net (from the Gerber's X2 net attributes)
                d = distance(sh, objs[j][0])
                if d < floor:
                    seen.add((gi_i, gj))
                    seen.add((gj, gi_i))
                    x, y = sh.center()
                    lab = f"{d:.3f} mm" + (f" {na or '?'} / {nb or '?'}" if na or nb else "")
                    hits.append((d, (x, y, l.name, lab), bool(na and nb)))
    if hits:
        hits.sort(key=lambda x: x[0])
        known = all(h[2] for h in hits)
        r.add("GBR-CLEAR", "error",
              f"{len(hits)} place(s) where copper shapes are closer than {lim['min_space']} mm (closest {hits[0][0]:.3f} mm)."
              + ("" if known else " These files have no net names, so some of them may be the same net; check each one."),
              [h[1] for h in hits[:MAX_LOCS]], fix="Move them apart, or run the DRC in your EDA tool with a 0.2 mm clearance.")


def check_silk(fs, r, lim):
    r.check("GBR-SILK", "fab", "Silkscreen line width", f"PCBWay {lim['silk_line_min']} mm")
    thin = []
    for l in fs.layers:
        if not l.kind.startswith("silk"):
            continue
        for x1, y1, x2, y2, w, fn, rnd in l.draws:
            if 0 < w < lim["silk_line_min"] - 1e-3:
                thin.append(w)
    if thin:
        r.add("GBR-SILK", "info", f"{len(thin)} silkscreen line(s) are thinner than {lim['silk_line_min']} mm (thinnest {min(thin):.2f} mm). "
              "They may print broken; text needs 1 mm height and 0.15 mm stroke to be readable.")


def run_gerber_checks(fs, report, oz=1.0, progress=None):
    lim = fab_limits(oz)
    for fn in (check_files, check_layers, check_outline, check_tracks, check_drills, check_rings,
               check_hole_spacing, check_edge, check_spacing, check_silk):
        if progress:
            progress(fn.__name__)
        try:
            if fn is check_files:
                fn(fs, report)
            else:
                fn(fs, report, lim)
        except Exception as e:
            cid = f"INTERNAL-gerber-{fn.__name__}"
            report.check(cid, "fab", f"Checker error in {fn.__name__}")
            report.add(cid, "info", f"This check crashed ({type(e).__name__}: {e}). Please report it to the course staff.")
