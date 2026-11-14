"""Compact drawing data (lines, polygons, circles per layer) for the report's board view."""

MAX_FILL_POINTS = 250000

LAYER_COLORS = {
    "F.Cu": "#d9453b", "B.Cu": "#3b7dd8", "In1.Cu": "#c9a227", "In2.Cu": "#2a9d8f",
    "In3.Cu": "#9b5de5", "In4.Cu": "#f15bb5",
}


def _r(v):
    return round(v, 3)


def _shape_into(layer, sh):
    if sh.poly:
        pts = []
        for x, y in sh.poly:
            pts += [_r(x), _r(y)]
        layer["p"].append(pts)
        if sh.r > 0:  # rounded rectangle: stroke the core outline with 2r
            for x1, y1, x2, y2 in sh.segs:
                layer["l"].append([_r(x1), _r(y1), _r(x2), _r(y2), _r(2 * sh.r)])
    elif len(sh.segs) == 1 and sh.segs[0][0] == sh.segs[0][2] and sh.segs[0][1] == sh.segs[0][3]:
        layer["c"].append([_r(sh.segs[0][0]), _r(sh.segs[0][1]), _r(sh.r)])
    else:
        for x1, y1, x2, y2 in sh.segs:
            layer["l"].append([_r(x1), _r(y1), _r(x2), _r(y2), _r(2 * sh.r)])


def _new_layer(name, label):
    return {"id": name, "label": label, "color": LAYER_COLORS.get(name, "#888"), "l": [], "p": [], "c": [], "f": []}


def _decimate(polys):
    total = sum(len(p) for p in polys)
    step = max(1, total // MAX_FILL_POINTS + (1 if total > MAX_FILL_POINTS else 0))
    out = []
    for pts in polys:
        sub = pts[::step] if len(pts) > 12 else pts
        flat = []
        for x, y in sub:
            flat += [_r(x), _r(y)]
        out.append(flat)
    return out


def from_kicad(board):
    order = list(reversed(board.copper_layers))  # bottom first, top drawn last
    layers = {n: _new_layer(n, {"F.Cu": "Top", "B.Cu": "Bottom"}.get(n, n.replace(".Cu", ""))) for n in order}
    for t in board.tracks:
        if t.layer in layers:
            for i in range(len(t.pts) - 1):
                layers[t.layer]["l"].append([_r(t.pts[i][0]), _r(t.pts[i][1]), _r(t.pts[i + 1][0]), _r(t.pts[i + 1][1]), _r(t.w)])
    for f in board.footprints:
        for p in f.pads:
            for l in p.layers:
                if l in layers:
                    _shape_into(layers[l], p.geom)
    fills = {n: [] for n in order}
    for z in board.zones:
        if z.keepout:
            continue
        for l, pts in z.fills:
            if l in fills:
                fills[l].append(pts)
    allf = [p for l in order for p in fills[l]]
    dec = _decimate(allf)
    k = 0
    for l in order:
        for _ in fills[l]:
            layers[l]["f"].append(dec[k])
            k += 1
    vias = [[_r(v.x), _r(v.y), _r(v.size / 2), _r(v.drill / 2)] for v in board.vias]
    holes = [[_r(p.x), _r(p.y), _r(min(p.drill) / 2)] for p in board.pads if p.drill]
    parts = []
    for f in board.footprints:
        if f.body:
            parts.append([f.ref, _r(f.x), _r(f.y), [c for x, y in f.body for c in (_r(x), _r(y))], f.side])
    outline = [[_r(a), _r(b), _r(c), _r(d)] for a, b, c, d in board.edge.segs]
    return _finish([layers[n] for n in order], outline, vias, holes, parts)


def from_gerber(fs):
    kinds = [("copper_bottom", "B.Cu", "Bottom"), ("copper_inner", "In1.Cu", "Inner"), ("copper_top", "F.Cu", "Top")]
    out_layers = []
    for kind, lid, label in kinds:
        for gl in fs.by_kind(kind):
            L = _new_layer(lid, label)
            for x1, y1, x2, y2, w, fn, rnd in gl.draws:
                L["l"].append([_r(x1), _r(y1), _r(x2), _r(y2), _r(w)])
            for pts, w, fn in gl.arcs:
                for i in range(len(pts) - 1):
                    L["l"].append([_r(pts[i][0]), _r(pts[i][1]), _r(pts[i + 1][0]), _r(pts[i + 1][1]), _r(w)])
            for x, y, ap in gl.flashes:
                _shape_into(L, ap.shape_at(x, y))
            L["f"] = _decimate(gl.regions)
            out_layers.append(L)
    outline = []
    for gl in fs.by_kind("outline"):
        pass
    outline = [[_r(a), _r(b), _r(c), _r(d)] for a, b, c, d in fs.outline_segments()[0]]
    holes = [[_r(x), _r(y), _r(d / 2)] for x, y, d, _ in fs.all_holes()]
    return _finish(out_layers, outline, [], holes, [])


def _finish(layers, outline, vias, holes, parts):
    xs, ys = [], []
    for s in outline:
        xs += [s[0], s[2]]
        ys += [s[1], s[3]]
    if not xs:
        for L in layers:
            for l in L["l"]:
                xs += [l[0], l[2]]
                ys += [l[1], l[3]]
            for c in L["c"]:
                xs.append(c[0])
                ys.append(c[1])
    bbox = [min(xs), min(ys), max(xs), max(ys)] if xs else [0, 0, 100, 100]
    return {"bbox": bbox, "layers": layers, "outline": outline, "vias": vias, "holes": holes, "parts": parts}
