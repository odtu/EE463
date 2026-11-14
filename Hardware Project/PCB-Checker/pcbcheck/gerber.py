"""Read Gerber (RS-274X / X2) and Excellon drill files from any EDA tool."""

import math
import os
import re

from .geometry import Shape, rotate, circle_points

# ---------------------------------------------------------------------------
# Layer identification

LAYER_NAMES = {
    "copper_top": "Top copper", "copper_bottom": "Bottom copper", "copper_inner": "Inner copper",
    "mask_top": "Top solder mask", "mask_bottom": "Bottom solder mask",
    "silk_top": "Top silkscreen", "silk_bottom": "Bottom silkscreen",
    "paste_top": "Top paste", "paste_bottom": "Bottom paste",
    "outline": "Board outline", "drill_pth": "Plated drill", "drill_npth": "Non-plated drill",
    "drill": "Drill", "extra": "Not needed by the fab", "other": "Other / unknown",
}

_EXT = {
    ".gtl": "copper_top", ".gbl": "copper_bottom", ".gts": "mask_top", ".gbs": "mask_bottom",
    ".gto": "silk_top", ".gbo": "silk_bottom", ".gtp": "paste_top", ".gbp": "paste_bottom",
    ".gko": "outline", ".gm1": "outline", ".gml": "outline", ".gm": "outline", ".gmo": "outline",
    ".g1": "copper_inner", ".g2": "copper_inner", ".g3": "copper_inner", ".g4": "copper_inner",
    ".gp1": "copper_inner", ".gp2": "copper_inner",
    ".drl": "drill", ".xln": "drill", ".exc": "drill", ".drd": "drill", ".nc": "drill", ".tap": "drill",
}

_NAME_PATTERNS = [
    # whole-name matches first (Cadence Allegro / OrCAD film names and plain names)
    (r"^(top|toplayer|top_layer|l1|layer1|cmp|component|etch_top)$", "copper_top"),
    (r"^(bottom|bot|btm|bottomlayer|bottom_layer|etch_bottom|sol)$", "copper_bottom"),
    (r"^(psm|tsm|smt|soldermask_top|solder_mask_top|top_mask)$", "mask_top"),
    (r"^(ssm|bsm|smb|soldermask_bottom|solder_mask_bottom|bottom_mask)$", "mask_bottom"),
    (r"^(pss|tsk|sst|silkscreen_top|silk_top|top_silk)$", "silk_top"),
    (r"^(sss|bsk|ssb|silkscreen_bottom|silk_bottom|bottom_silk)$", "silk_bottom"),
    (r"^(psp|tsp|paste_top|top_paste)$", "paste_top"),
    (r"^(ssp|bsp|paste_bottom|bottom_paste)$", "paste_bottom"),
    (r"^(passy|sassy|assy.*|.*assembly.*|fab|fabrication|.*drill_?draw.*)$", "extra"),
    (r"(f[._-]?cu|top[._-]?(layer|copper)|copper[._-]?top|\btop\b(?!.*(silk|mask|paste|overlay)))", "copper_top"),
    (r"(b[._-]?cu|bottom[._-]?(layer|copper)|bot[._-]?(layer|copper)|copper[._-]?bot)", "copper_bottom"),
    (r"(in\d+[._-]?cu|inner|mid\d|internal)", "copper_inner"),
    (r"(f[._-]?mask|top[._-]?(solder)?[._-]?mask|soldermask[._-]?top|topsoldermask)", "mask_top"),
    (r"(b[._-]?mask|bot(tom)?[._-]?(solder)?[._-]?mask|soldermask[._-]?bot)", "mask_bottom"),
    (r"(f[._-]?silk|top[._-]?(silk|overlay)|silk[._-]?top|legend[._-]?top)", "silk_top"),
    (r"(b[._-]?silk|bot(tom)?[._-]?(silk|overlay)|silk[._-]?bot|legend[._-]?bot)", "silk_bottom"),
    (r"(f[._-]?paste|top[._-]?paste)", "paste_top"),
    (r"(b[._-]?paste|bot(tom)?[._-]?paste)", "paste_bottom"),
    (r"(edge[._-]?cuts|outline|board[._-]?edge|keep[._-]?out|mechanical|profile|boardoutline)", "outline"),
]


def classify_file(path, text_head):
    """Guess what a fabrication file is from its X2 attributes, name and extension."""
    name = os.path.basename(path).lower()
    ext = os.path.splitext(name)[1]
    head = text_head
    if ext in (".gbrjob", ".gba", ".gta", ".pos", ".csv", ".rpt") or re.search(
        r"courtyard|crtyd|[._-]fab(?![a-z])|_fab\.|user[._-]?\d|user[._-]?(comments|drawings)|margin|eco\d|adhes|dwgs|cmts|drl[._-]?map|drill[._-]?map", name):
        return "extra"
    if re.search(r"^\s*M48", head, re.M) or ("METRIC" in head[:400] or "INCH" in head[:400]) and re.search(r"^T\d+C", head, re.M):
        if re.search(r"TF\.FileFunction,NonPlated", head) or "npth" in name or "non-plated" in name or "nonplated" in name:
            return "drill_npth"
        if re.search(r"TF\.FileFunction,Plated", head) or "pth" in name or "plated" in name:
            return "drill_pth"
        return "drill"
    m = re.search(r"%TF\.FileFunction,([^*%]*)", head)
    if m:
        parts = m.group(1).split(",")
        kind = parts[0]
        side = ",".join(parts[1:]).lower()
        if kind == "Copper":
            if "top" in side:
                return "copper_top"
            if "bot" in side:
                return "copper_bottom"
            return "copper_inner"
        if kind == "Soldermask":
            return "mask_top" if "top" in side else "mask_bottom"
        if kind == "Legend":
            return "silk_top" if "top" in side else "silk_bottom"
        if kind == "Paste":
            return "paste_top" if "top" in side else "paste_bottom"
        if kind == "Profile":
            return "outline"
        if kind in ("Plated", "NonPlated"):  # drill data written as a Gerber file
            return "gdrill_pth" if kind == "Plated" else "gdrill_npth"
        if kind in ("Other", "Component", "AssemblyDrawing", "FabricationDrawing", "Keep-out", "Glue", "Drillmap"):
            return "extra"
    if ext in (".gbr", ".ger") and re.search(r"[._-](drl|drill)$", os.path.splitext(name)[0]):
        return "gdrill_npth" if "npth" in name else "gdrill_pth"
    if ext in _EXT:
        return _EXT[ext]
    stem = os.path.splitext(name)[0]
    for pat, kind in _NAME_PATTERNS:
        if re.search(pat, stem):
            return kind
    return "other"


# ---------------------------------------------------------------------------
# Apertures and macros

def _safe_eval(expr, vars_):
    expr = expr.strip().replace("x", "*").replace("X", "*")
    expr = re.sub(r"\$(\d+)", lambda m: repr(vars_.get(int(m.group(1)), 0.0)), expr)
    if not re.fullmatch(r"[0-9eE.+\-*/() ]*", expr) or not expr:
        return 0.0
    try:
        return float(eval(expr, {"__builtins__": {}}, {}))  # only digits and operators reach here
    except Exception:
        return 0.0


def _hull(points):
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _gerber_rot(x, y, deg):
    # Gerber angles are CCW with Y up; in file coordinates that is the standard math rotation
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def _macro_points(body, params):
    """Points outlining a macro aperture (for its convex hull) and whether it is a pure circle."""
    vars_ = {i + 1: v for i, v in enumerate(params)}
    pts = []
    circles = 0
    prims = 0
    for stmt in body:
        stmt = stmt.strip()
        if not stmt or stmt.startswith("0"):
            continue
        if stmt.startswith("$"):
            m = re.match(r"\$(\d+)\s*=\s*(.*)", stmt)
            if m:
                vars_[int(m.group(1))] = _safe_eval(m.group(2), vars_)
            continue
        f = [_safe_eval(s, vars_) for s in stmt.split(",")]
        code = int(f[0]) if f else -1
        prims += 1
        if code == 1 and len(f) >= 5:
            if f[1] == 0:
                continue
            d, cx, cy = f[2], f[3], f[4]
            rot = f[5] if len(f) > 5 else 0
            cx, cy = _gerber_rot(cx, cy, rot)
            pts += circle_points(cx, cy, d / 2, 16)
            circles += 1
        elif code in (20, 2) and len(f) >= 7:
            w, x1, y1, x2, y2, rot = f[2], f[3], f[4], f[5], f[6], f[7] if len(f) > 7 else 0
            L = math.hypot(x2 - x1, y2 - y1) or 1
            nx, ny = -(y2 - y1) / L * w / 2, (x2 - x1) / L * w / 2
            for x, y in ((x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny)):
                pts.append(_gerber_rot(x, y, rot))
        elif code == 21 and len(f) >= 6:
            w, h, cx, cy, rot = f[2], f[3], f[4], f[5], f[6] if len(f) > 6 else 0
            for x, y in ((cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)):
                pts.append(_gerber_rot(x, y, rot))
        elif code == 4 and len(f) >= 3:
            n = int(f[2])
            coords = f[3:3 + 2 * (n + 1)]
            rot = f[3 + 2 * (n + 1)] if len(f) > 3 + 2 * (n + 1) else 0
            for i in range(0, len(coords) - 1, 2):
                pts.append(_gerber_rot(coords[i], coords[i + 1], rot))
        elif code == 5 and len(f) >= 6:
            n, cx, cy, d = int(f[2]), f[3], f[4], f[5]
            rot = f[6] if len(f) > 6 else 0
            for i in range(max(n, 3)):
                a = 2 * math.pi * i / max(n, 3)
                pts.append(_gerber_rot(cx + d / 2 * math.cos(a), cy + d / 2 * math.sin(a), rot))
        elif code == 7 and len(f) >= 4:
            cx, cy, od = f[1], f[2], f[3]
            pts += circle_points(cx, cy, od / 2, 16)
    return pts, (prims == 1 and circles == 1)


class Aperture:
    __slots__ = ("code", "kind", "w", "h", "function", "hull", "round")

    def size_min(self):
        return min(self.w, self.h)

    def shape_at(self, x, y):
        if self.kind == "C" or self.round:
            return Shape.point(x, y, self.w / 2)
        if self.kind == "O":
            return Shape.oval(x, y, self.w, self.h)
        if self.kind in ("M", "P") and self.hull and len(self.hull) >= 3:
            return Shape.polygon([(x + px, y + py) for px, py in self.hull])
        return Shape.rect(x, y, self.w, self.h)


class GerberLayer:
    def __init__(self, path, kind):
        self.path = path
        self.kind = kind
        self.draws = []      # (x1, y1, x2, y2, width, function, round_aperture)
        self.arcs = []       # list of point lists drawn with width: (pts, width, function)
        self.flashes = []    # (x, y, Aperture)
        self.regions = []    # list of point lists
        # X2 net names (%TO.N), parallel to the lists above; "" when the file has none
        self.draw_nets, self.arc_nets, self.flash_nets, self.region_nets = [], [], [], []
        self.clear_polarity = False
        self.errors = []
        self.units = "mm"

    @property
    def name(self):
        return os.path.basename(self.path)

    def bbox(self):
        xs, ys = [], []
        for d in self.draws:
            xs += [d[0], d[2]]
            ys += [d[1], d[3]]
        for pts, _, _ in self.arcs:
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
        for x, y, a in self.flashes:
            xs.append(x)
            ys.append(y)
        for r in self.regions:
            xs += [p[0] for p in r]
            ys += [p[1] for p in r]
        if not xs:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def outline_segments(self):
        segs = [(d[0], d[1], d[2], d[3]) for d in self.draws]
        for pts, _, _ in self.arcs:
            segs += [(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]) for i in range(len(pts) - 1)]
        for r in self.regions:
            segs += [(r[i][0], r[i][1], r[(i + 1) % len(r)][0], r[(i + 1) % len(r)][1]) for i in range(len(r))]
        return segs


def _coord(s, fmt_dec, zero_mode, int_digits, scale):
    if s is None:
        return None
    if "." in s:
        return float(s) * scale
    neg = s.startswith("-")
    s2 = s.lstrip("+-")
    if zero_mode == "T":  # trailing zeros omitted
        s2 = s2.ljust(int_digits + fmt_dec, "0")
    v = int(s2 or "0") / (10 ** fmt_dec)
    return (-v if neg else v) * scale


def parse_gerber(path, kind):
    layer = GerberLayer(path, kind)
    with open(path, encoding="latin-1") as fh:
        text = fh.read()
    scale = 1.0
    int_digits, dec = 3, 6
    zero_mode = "L"
    apertures = {}
    macros = {}
    cur_ap = None
    attr_function = ""
    cur_net = ""
    x = y = 0.0
    interp = 1
    multi_quadrant = True
    in_region = False
    contour = []

    for m in re.finditer(r"%([^%]*)%|([^%*]*)\*", text):
        ext, stmt = m.group(1), m.group(2)
        if ext is not None:
            blocks = [b.strip() for b in ext.split("*") if b.strip()]
            if not blocks:
                continue
            if blocks[0].startswith("AM"):
                macros[blocks[0][2:]] = blocks[1:]
                continue
            for head in blocks:  # several commands may share one %...% block
                if head.startswith("FS"):
                    fm = re.match(r"FS([LT])?([AI])?X(\d)(\d)Y(\d)(\d)", head)
                    if fm:
                        zero_mode = fm.group(1) or "L"
                        int_digits, dec = int(fm.group(3)), int(fm.group(4))
                elif head.startswith("MO"):
                    scale = 25.4 if "IN" in head else 1.0
                    layer.units = "in" if scale != 1.0 else "mm"
                elif head.startswith("LP"):
                    if head == "LPC":
                        layer.clear_polarity = True
                elif head.startswith("TA.AperFunction"):
                    attr_function = head.split(",", 1)[1] if "," in head else ""
                elif head.startswith("TO.N,"):
                    cur_net = head[5:].split(",")[0]
                elif head.startswith("TD"):
                    if head in ("TD", "TD.AperFunction"):
                        attr_function = ""
                    if head in ("TD", "TD.N"):
                        cur_net = ""
                elif head.startswith("AD"):
                    am = re.match(r"ADD(\d+)([A-Za-z_.$][\w.$\-]*)(?:,(.*))?", head)
                    if not am:
                        continue
                    ap = Aperture()
                    ap.code = int(am.group(1))
                    name = am.group(2)
                    params = [_f(p) for p in (am.group(3) or "").split("X") if p.strip()] if am.group(3) else []
                    params = [p * scale for p in params]
                    ap.function = attr_function
                    ap.hull = None
                    ap.round = False
                    if name == "C":
                        ap.kind = "C"
                        ap.w = ap.h = params[0] if params else 0.0
                    elif name in ("R", "O"):
                        ap.kind = name
                        ap.w = params[0] if params else 0.0
                        ap.h = params[1] if len(params) > 1 else ap.w
                    elif name == "P":
                        ap.kind = "P"
                        d = params[0] if params else 0.0
                        n = int(params[1] / scale) if len(params) > 1 else 4
                        rot = params[2] / scale if len(params) > 2 else 0
                        ap.hull = [_gerber_rot(d / 2 * math.cos(2 * math.pi * i / n), d / 2 * math.sin(2 * math.pi * i / n), rot)
                                   for i in range(max(n, 3))]
                        ap.w = ap.h = d
                    elif name in macros:
                        ap.kind = "M"
                        raw = [_f(p) for p in (am.group(3) or "").split("X") if p.strip()] if am.group(3) else []
                        pts, is_circle = _macro_points(macros[name], raw)
                        pts = [(px * scale, py * scale) for px, py in pts]
                        ap.hull = _hull(pts) if pts else None
                        if ap.hull:
                            xs = [p[0] for p in ap.hull]
                            ys = [p[1] for p in ap.hull]
                            ap.w, ap.h = max(xs) - min(xs), max(ys) - min(ys)
                        else:
                            ap.w = ap.h = 0.0
                        ap.round = is_circle
                    else:
                        ap.kind = "R"
                        ap.w = ap.h = params[0] if params else 0.0
                    apertures[ap.code] = ap
            continue

        s = stmt.strip()
        if not s:
            continue
        if s.startswith("G04") or s.startswith("M02") or s.startswith("M00"):
            continue
        for g in re.findall(r"G0*(\d+)", s):
            g = int(g)
            if g in (1, 2, 3):
                interp = g
            elif g == 70:  # old-style units: inch
                scale = 25.4
                layer.units = "in"
            elif g == 71:  # old-style units: mm
                scale = 1.0
                layer.units = "mm"
            elif g == 74:
                multi_quadrant = False
            elif g == 75:
                multi_quadrant = True
            elif g == 36:
                in_region = True
                contour = []
            elif g == 37:
                if len(contour) >= 3:
                    layer.regions.append(contour)
                    layer.region_nets.append(cur_net)
                contour = []
                in_region = False
        dm = re.search(r"D0*(\d+)$", s)
        dcode = int(dm.group(1)) if dm else None
        if dcode is not None and dcode >= 10:
            cur_ap = apertures.get(dcode)
            continue
        cm = {k: v for k, v in re.findall(r"([XYIJ])([+-]?[\d.]+)", s)}
        if not cm and dcode is None:
            continue
        nx = _coord(cm.get("X"), dec, zero_mode, int_digits, scale) if "X" in cm else x
        ny = _coord(cm.get("Y"), dec, zero_mode, int_digits, scale) if "Y" in cm else y
        if dcode is None:
            dcode = 1 if cm else None
        if dcode == 2:
            if in_region:
                if len(contour) >= 3:
                    layer.regions.append(contour)
                    layer.region_nets.append(cur_net)
                contour = [(nx, -ny)]
            x, y = nx, ny
            continue
        if dcode == 3:
            if cur_ap is not None:
                layer.flashes.append((nx, -ny, cur_ap))
                layer.flash_nets.append(cur_net)
            x, y = nx, ny
            continue
        if dcode == 1:
            if interp in (2, 3):
                i = _coord(cm.get("I"), dec, zero_mode, int_digits, scale) or 0.0
                j = _coord(cm.get("J"), dec, zero_mode, int_digits, scale) or 0.0
                pts = _arc(x, y, nx, ny, i, j, interp == 2, multi_quadrant)
                pts = [(px, -py) for px, py in pts]
                if in_region:
                    if not contour:
                        contour = [(x, -y)]
                    contour.extend(pts[1:])
                elif cur_ap is not None:
                    layer.arcs.append((pts, cur_ap.size_min(), cur_ap.function))
                    layer.arc_nets.append(cur_net)
            else:
                if in_region:
                    if not contour:
                        contour = [(x, -y)]
                    contour.append((nx, -ny))
                elif cur_ap is not None:
                    layer.draws.append((x, -y, nx, -ny, cur_ap.size_min(), cur_ap.function,
                                        cur_ap.kind == "C" or cur_ap.round))
                    layer.draw_nets.append(cur_net)
            x, y = nx, ny
    return layer


def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _arc(x0, y0, x1, y1, i, j, clockwise, multi):
    if multi:
        cx, cy = x0 + i, y0 + j
    else:  # single quadrant: offsets are unsigned; choose the centre that fits
        best = None
        for sx in (1, -1):
            for sy in (1, -1):
                cx, cy = x0 + sx * abs(i), y0 + sy * abs(j)
                err = abs(math.hypot(x0 - cx, y0 - cy) - math.hypot(x1 - cx, y1 - cy))
                if best is None or err < best[0]:
                    best = (err, cx, cy)
        _, cx, cy = best
    r = math.hypot(x0 - cx, y0 - cy)
    a0 = math.atan2(y0 - cy, x0 - cx)
    a1 = math.atan2(y1 - cy, x1 - cx)
    if clockwise:
        sweep = -((a0 - a1) % (2 * math.pi))
    else:
        sweep = (a1 - a0) % (2 * math.pi)
    if abs(sweep) < 1e-9 and multi:
        sweep = -2 * math.pi if clockwise else 2 * math.pi
    n = max(2, min(128, int(abs(sweep) * max(r, 0.1) / 0.2) + 2))
    pts = [(cx + r * math.cos(a0 + sweep * k / n), cy + r * math.sin(a0 + sweep * k / n)) for k in range(n + 1)]
    pts[0] = (x0, y0)   # keep the exact end points from the file, so outlines close
    pts[-1] = (x1, y1)
    return pts


# ---------------------------------------------------------------------------
# Excellon

class DrillFile:
    def __init__(self, path, kind):
        self.path = path
        self.kind = kind          # drill_pth / drill_npth / drill
        self.holes = []           # (x, y, diameter, plated)
        self.slots = []           # (x1, y1, x2, y2, width, plated)

    @property
    def name(self):
        return os.path.basename(self.path)


def parse_excellon(path, kind):
    df = DrillFile(path, kind)
    with open(path, encoding="latin-1") as fh:
        lines = fh.read().splitlines()
    scale = 1.0
    zero_mode = "LZ"
    int_d, dec_d = 3, 3
    explicit_fmt = False
    tools = {}
    tool = None
    x = y = 0.0
    route_mode = False
    plunged = False
    plated_default = kind != "drill_npth"
    plated = plated_default
    tool_plated = {}
    pending = None
    units_known = False
    saw_decimal = False
    rx = ry = 0          # raw integer coordinates, kept in case the format has to be guessed
    df.raw_holes = []

    def coord(s):
        if s is None:
            return None
        if "." in s:
            return float(s) * scale
        neg = s.startswith("-")
        s2 = s.lstrip("+-")
        if zero_mode == "LZ":  # leading zeros kept, trailing suppressed
            s2 = s2.ljust(int_d + dec_d, "0")
        v = int(s2 or "0") / 10 ** dec_d
        return (-v if neg else v) * scale

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";"):
            m = re.search(r"FILE_FORMAT=(\d):(\d)", line)
            if m:
                int_d, dec_d = int(m.group(1)), int(m.group(2))
                explicit_fmt = True
            if re.search(r"TF\.FileFunction,NonPlated", line):
                plated = plated_default = False
            m = re.search(r"TA\.AperFunction,(\w+)", line)
            if m:
                pending = m.group(1) != "NonPlated"
            # Cadence Allegro lists the tools only in comments: ";T01 Holesize 1. = 16.000000 ... PLATED MILS"
            m = re.match(r";\s*T(\d+)\s+Holesize\s+\S+\s*=\s*([\d.]+).*?\b(NON[_-]?PLATED|PLATED)?\b.*?\b(MILS|MM|INCH|IN)\b",
                         line, re.I)
            if m:
                k = int(m.group(1))
                unit = m.group(4).upper()
                tools[k] = float(m.group(2)) * {"MILS": 0.0254, "MM": 1.0, "INCH": 25.4, "IN": 25.4}[unit]
                tool_plated[k] = not (m.group(3) or "").upper().startswith("NON") and plated_default
            continue
        up = line.upper()
        if up.startswith("METRIC") or up.startswith("M71"):
            scale = 1.0
            units_known = True
            if not explicit_fmt:
                int_d, dec_d = 3, 3
            if "TZ" in up:
                zero_mode = "TZ"
            elif "LZ" in up:
                zero_mode = "LZ"
            m = re.search(r",0*(\d+)\.(\d+)", up)
            if m:
                int_d, dec_d = len(m.group(1)) or 3, len(m.group(2))
            continue
        if up.startswith("INCH") or up.startswith("M72"):
            scale = 25.4
            units_known = True
            if not explicit_fmt:
                int_d, dec_d = 2, 4
            if "TZ" in up:
                zero_mode = "TZ"
            elif "LZ" in up:
                zero_mode = "LZ"
            continue
        tm = re.match(r"T(\d+)(?:F[\d.]+|S[\d.]+|B[\d.]+|H[\d.]+|Z[\d.+-]+)*C([\d.]+)", up)
        if tm:
            tools[int(tm.group(1))] = float(tm.group(2)) * scale
            tool_plated[int(tm.group(1))] = plated_default if pending is None else pending
            pending = None
            continue
        tm = re.match(r"T(\d+)$", up)
        if tm:
            tool = int(tm.group(1))
            plated = tool_plated.get(tool, plated_default)
            continue
        if up.startswith("M15"):
            plunged = True
            continue
        if up.startswith("M16") or up.startswith("M17"):
            plunged = False
            continue
        if up.startswith("G05"):
            route_mode = False
            continue
        if "G85" in up:
            a, b = up.split("G85", 1)
            ma = dict(re.findall(r"([XY])([+-]?[\d.]+)", a))
            mb = dict(re.findall(r"([XY])([+-]?[\d.]+)", b))
            x1 = coord(ma.get("X")) if "X" in ma else x
            y1 = coord(ma.get("Y")) if "Y" in ma else y
            x2 = coord(mb.get("X")) if "X" in mb else x1
            y2 = coord(mb.get("Y")) if "Y" in mb else y1
            if tool in tools:
                df.slots.append((x1, -y1, x2, -y2, tools[tool], plated))
            x, y = x2, y2
            continue
        if up.startswith("G00"):
            route_mode = True
        cm = dict(re.findall(r"([XY])([+-]?[\d.]+)", up))
        if not cm:
            continue
        if any("." in v for v in cm.values()):
            saw_decimal = True
        else:
            rx = int(cm["X"]) if "X" in cm else rx
            ry = int(cm["Y"]) if "Y" in cm else ry
        nx = coord(cm.get("X")) if "X" in cm else x
        ny = coord(cm.get("Y")) if "Y" in cm else y
        if route_mode:
            if plunged and (up.startswith("G01") or up.startswith("G02") or up.startswith("G03")) and tool in tools:
                df.slots.append((x, -y, nx, -ny, tools[tool], plated))
        elif tool in tools:
            df.holes.append((nx, -ny, tools[tool], plated))
            df.raw_holes.append((rx, ry, tools[tool], plated))
        x, y = nx, ny
    # no units/format given and no decimal points: the scale is guessed later from the board size
    df.format_unknown = not units_known and not explicit_fmt and not saw_decimal and bool(df.raw_holes)
    return df


def _fit_drill_format(df, board_bbox):
    """Pick the coordinate scale that puts the most holes on the board."""
    x0, y0, x1, y1 = board_bbox
    best = None
    for factor in [25.4 / 10 ** d for d in (3, 4, 5)] + [1.0 / 10 ** d for d in (2, 3, 4)]:
        pts = [(rx * factor, -ry * factor) for rx, ry, _, _ in df.raw_holes]
        inside = sum(1 for x, y in pts if x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        span = ((max(xs) - min(xs)) * (max(ys) - min(ys))) / max((x1 - x0) * (y1 - y0), 1e-9)
        score = (inside, -abs(1 - min(span, 1.0)))
        if best is None or score > best[0]:
            best = (score, factor)
    f = best[1]
    df.holes = [(rx * f, -ry * f, d, pl) for rx, ry, d, pl in df.raw_holes]
    df.format_guess = f


class FabSet:
    """All Gerber and drill files of one board."""

    def __init__(self):
        self.layers = []
        self.drills = []
        self.skipped = []
        self.folder = ""

    def by_kind(self, kind):
        return [l for l in self.layers if l.kind == kind]

    def copper(self):
        return [l for l in self.layers if l.kind.startswith("copper")]

    def all_holes(self):
        for d in self.drills:
            for h in d.holes:
                yield h
        for d in self.drills:
            for s in d.slots:
                yield ((s[0] + s[2]) / 2, (s[1] + s[3]) / 2, s[4], s[5])

    def outline_segments(self):
        """Board edge segments. Outline/mechanical layers often also carry dimensions and notes,
        so only lines that form closed loops are kept (when there are any).
        Returns (segments, number of ignored segments, closed)."""
        if getattr(self, "_outline", None) is not None:
            return self._outline
        segs = []
        for l in self.by_kind("outline"):
            segs += [s for s in l.outline_segments() if abs(s[0] - s[2]) > 1e-6 or abs(s[1] - s[3]) > 1e-6]
        if not segs:
            self._outline = ([], 0, False)
            return self._outline
        key = {}
        parent = []

        def node(x, y):
            k = (round(x / 0.02), round(y / 0.02))
            if k not in key:
                key[k] = len(parent)
                parent.append(len(parent))
            return key[k]

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        ends = []
        degree = {}
        for x1, y1, x2, y2 in segs:
            a, b = node(x1, y1), node(x2, y2)
            ends.append((a, b))
            degree[a] = degree.get(a, 0) + 1
            degree[b] = degree.get(b, 0) + 1
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        open_comp = {find(n) for n, d in degree.items() if d % 2}
        comps = {}
        for s, (a, b) in zip(segs, ends):
            if find(a) not in open_comp:
                comps.setdefault(find(a), []).append(s)

        def bb(ss):
            xs = [v for s in ss for v in (s[0], s[2])]
            ys = [v for s in ss for v in (s[1], s[3])]
            return min(xs), min(ys), max(xs), max(ys)

        if len(comps) > 1:
            # the board edge is the biggest loop; other loops count only if they are cut-outs,
            # i.e. there is no copper inside them (drawings of coils, keep-outs etc. have copper)
            boxes = {k: bb(v) for k, v in comps.items()}
            outer = max(boxes, key=lambda k: (boxes[k][2] - boxes[k][0]) * (boxes[k][3] - boxes[k][1]))
            centers = []
            for l in self.copper():
                centers += [((d[0] + d[2]) / 2, (d[1] + d[3]) / 2) for d in l.draws[::3]]
                centers += [(x, y) for x, y, _ in l.flashes]
            for k in list(comps):
                if k == outer:
                    continue
                x0, y0, x1, y1 = boxes[k]
                mx, my = (x1 - x0) * 0.2, (y1 - y0) * 0.2
                if any(x0 + mx <= x <= x1 - mx and y0 + my <= y <= y1 - my for x, y in centers):
                    del comps[k]
        kept = [s for v in comps.values() for s in v]
        if kept:
            # sanity check: copper sticking out past the kept outline means we picked the wrong loops
            kb = bb(kept)
            cb = [l.bbox() for l in self.copper() if l.bbox()]
            if cb and (min(b[0] for b in cb) < kb[0] - 1 or min(b[1] for b in cb) < kb[1] - 1 or
                       max(b[2] for b in cb) > kb[2] + 1 or max(b[3] for b in cb) > kb[3] + 1):
                kept = []
        if kept:
            self._outline = (kept, len(segs) - len(kept), True)
        else:
            self._outline = (segs, 0, False)
        return self._outline

    def board_bbox(self):
        segs = self.outline_segments()[0]
        if segs:
            xs = [s[0] for s in segs] + [s[2] for s in segs]
            ys = [s[1] for s in segs] + [s[3] for s in segs]
            return min(xs), min(ys), max(xs), max(ys)
        boxes = [l.bbox() for l in self.copper() if l.bbox()]
        if not boxes:
            return None
        return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


GERBER_EXTS = set(_EXT) | {".gbr", ".ger", ".pho", ".art", ".gbx", ".cmp", ".sol", ".stc", ".sts", ".plc", ".pls"}


def is_fab_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in GERBER_EXTS:
        return True
    if ext in (".txt", ".drl", ""):
        try:
            with open(path, encoding="latin-1") as fh:
                head = fh.read(2000)
        except OSError:
            return False
        return bool(re.search(r"^\s*M48", head, re.M) or "%FS" in head)
    return False


def _gerber_drill(path, kind, head):
    """Drill data written in Gerber format: each flash is a hole, each draw a slot."""
    gl = parse_gerber(path, kind)
    plated = kind == "gdrill_pth"
    df = DrillFile(path, "drill_pth" if plated else "drill_npth")
    df.holes = [(x, y, ap.w, plated) for x, y, ap in gl.flashes if ap.w > 0]
    df.slots = [(x1, y1, x2, y2, w, plated) for x1, y1, x2, y2, w, fn, rnd in gl.draws if w > 0]
    m = re.search(r"%TF\.FileFunction,([^*%]*)", head)
    func = m.group(1) if m else ""
    name = os.path.basename(path).lower()
    df.blind = bool(re.search(r"Blind|Buried", func)) or bool(re.search(r"(front|back|in\d+)-(in\d+|back)-drl|in\d+-(back|front)", name))
    return df


def load_fab_files(paths):
    fs = FabSet()
    for p in sorted(paths):
        try:
            with open(p, encoding="latin-1") as fh:
                head = fh.read(4000)
        except OSError:
            continue
        kind = classify_file(p, head)
        try:
            if kind.startswith("drill"):
                fs.drills.append(parse_excellon(p, kind))
            elif kind.startswith("gdrill"):
                fs.drills.append(_gerber_drill(p, kind, head))
            elif "%FS" in head or "%MO" in head or "G04" in head:
                fs.layers.append(parse_gerber(p, kind))
            else:
                fs.skipped.append(p)
        except Exception as e:  # keep going with the other files
            fs.skipped.append(f"{p} (could not read: {e})")
    if paths:
        fs.folder = os.path.dirname(sorted(paths)[0])
    bb = fs.board_bbox()
    for d in fs.drills:
        if getattr(d, "format_unknown", False) and bb:
            _fit_drill_format(d, bb)
    return fs
