"""Read a KiCad .kicad_pcb file (KiCad 6 to 10) into plain Python objects."""

import json
import math
import os
import re

from . import sexpr as S
from .geometry import Shape, rotate, arc_points, circle_points


class Pad:
    __slots__ = ("fp", "number", "type", "shape", "x", "y", "angle", "w", "h", "drill",
                 "layers", "net", "pinfunction", "pintype", "geom", "area", "rratio")

    @property
    def plated(self):
        return self.type == "thru_hole"

    @property
    def is_smd(self):
        return self.type in ("smd", "connect")

    def label(self):
        return f"{self.fp.ref} pad {self.number}" if self.fp else f"pad {self.number}"


class Footprint:
    def __init__(self):
        self.ref = ""
        self.value = ""
        self.lib = ""
        self.layer = "F.Cu"
        self.x = self.y = self.angle = 0.0
        self.attrs = set()
        self.pads = []
        self.props = {}
        self.texts = []
        self.body = None        # polygon (list of points) of the part body
        self.body_area = 0.0
        self.local_bbox = None

    @property
    def side(self):
        return "B" if self.layer.startswith("B") else "F"

    @property
    def prefix(self):
        m = re.match(r"[A-Za-z_#]+", self.ref)
        return m.group(0).upper() if m else ""

    def text_blob(self):
        return f"{self.lib} {self.value} {self.props.get('Description', '')}".lower()

    def copper_pads(self):
        return [p for p in self.pads if p.layers]

    def __repr__(self):
        return f"<Footprint {self.ref} {self.value}>"


class Track:
    __slots__ = ("kind", "x1", "y1", "x2", "y2", "mid", "w", "layer", "net", "pts", "geom", "length")


class Via:
    __slots__ = ("x", "y", "size", "drill", "layers", "net", "vtype", "geom", "remove_unused", "keep_end")


class Zone:
    def __init__(self):
        self.net = ""
        self.layers = []
        self.name = ""
        self.keepout = False
        self.connect = "thermal"
        self.min_thickness = 0.25
        self.hatch_fill = False
        self.outline = []
        self.fills = []          # list of (layer, points)
        self.priority = 0

    @property
    def filled(self):
        return bool(self.fills)


class Text:
    __slots__ = ("text", "layer", "x", "y", "angle", "height", "width", "thickness",
                 "mirrored", "visible", "owner", "kind")


class Edge:
    def __init__(self):
        self.segs = []
        self.arc_len = 0.0
        self.line_len = 0.0
        self.closed = True
        self.open_points = []

    @property
    def bbox(self):
        if not self.segs:
            return None
        xs = [s[0] for s in self.segs] + [s[2] for s in self.segs]
        ys = [s[1] for s in self.segs] + [s[3] for s in self.segs]
        return min(xs), min(ys), max(xs), max(ys)


class Board:
    def __init__(self):
        self.path = ""
        self.version = ""
        self.generator_version = ""
        self.copper_layers = []
        self.thickness = None
        self.copper_thickness = {}
        self.footprints = []
        self.tracks = []
        self.vias = []
        self.zones = []
        self.texts = []
        self.edge = Edge()
        self.nets = set()
        self.project = {}
        self.title_block = {}

    @property
    def name(self):
        return os.path.splitext(os.path.basename(self.path))[0]

    def fp(self, ref):
        for f in self.footprints:
            if f.ref == ref:
                return f
        return None

    @property
    def pads(self):
        for f in self.footprints:
            for p in f.pads:
                yield p

    def copper_oz(self):
        outer = [self.copper_thickness.get(l) for l in ("F.Cu", "B.Cu") if self.copper_thickness.get(l)]
        if not outer:
            return None
        return round(max(outer) / 0.035 * 2) / 2


# ---------------------------------------------------------------------------

def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _expand_layers(names, copper):
    out = []
    for n in names:
        if n == "*.Cu":
            out.extend(copper)
        elif n == "F&B.Cu":
            out.extend(["F.Cu", "B.Cu"])
        elif n.endswith(".Cu"):
            out.append(n)
    seen = []
    for l in out:
        if l not in seen:
            seen.append(l)
    return seen


class _Ctx:
    def __init__(self):
        self.netmap = {}
        self.copper = ["F.Cu", "B.Cu"]

    def net(self, node):
        n = S.find(node, "net")
        if n is None:
            return ""
        a = S.atoms(n)
        if len(a) >= 2:
            return a[1]
        if len(a) == 1:
            return self.netmap.get(a[0], a[0]) if a[0] in self.netmap else a[0]
        return ""


def _text_from(node, kind, owner, ctx_xy=None):
    t = Text()
    t.kind = kind
    t.owner = owner
    t.layer = S.value(node, "layer", "")
    at = S.find(node, "at")
    a = S.atoms(at) if at else []
    x, y = _f(a[0]) if a else 0.0, _f(a[1]) if len(a) > 1 else 0.0
    t.angle = _f(a[2]) if len(a) > 2 else 0.0
    if ctx_xy:
        x, y = ctx_xy(x, y)
    t.x, t.y = x, y
    eff = S.find(node, "effects")
    t.height = t.width = t.thickness = None
    t.mirrored = False
    hidden = S.flag(node, "hide")
    if eff is not None:
        font = S.find(eff, "font")
        if font is not None:
            size = S.find(font, "size")
            if size:
                sa = S.atoms(size)
                t.height = _f(sa[0]) if sa else None
                t.width = _f(sa[1]) if len(sa) > 1 else t.height
            t.thickness = S.num(font, "thickness")
        just = S.find(eff, "justify")
        if just is not None and "mirror" in S.atoms(just):
            t.mirrored = True
        if S.flag(eff, "hide"):
            hidden = True
    t.visible = not hidden
    return t


def _pad_geom(p, rratio):
    if p.shape == "circle":
        return Shape.point(p.x, p.y, p.w / 2)
    if p.shape == "oval":
        return Shape.oval(p.x, p.y, p.w, p.h, p.angle)
    if p.shape == "roundrect":
        r = min(p.w, p.h) * (rratio if rratio is not None else 0.25)
        return Shape.rect(p.x, p.y, p.w, p.h, p.angle, r)
    return Shape.rect(p.x, p.y, p.w, p.h, p.angle)


def _graphic_points(node, tf=None):
    """Outline points of an fp_/gr_ line, rect, circle, arc or poly."""
    kind = node[0].split("_", 1)[1]
    pts = []
    if kind == "line":
        pts = [S.xy(node, "start"), S.xy(node, "end")]
    elif kind == "rect":
        (x1, y1), (x2, y2) = S.xy(node, "start"), S.xy(node, "end")
        pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
    elif kind == "circle":
        c, e = S.xy(node, "center"), S.xy(node, "end")
        pts = circle_points(c[0], c[1], math.hypot(e[0] - c[0], e[1] - c[1]))
    elif kind == "arc":
        s, m, e = S.xy(node, "start"), S.xy(node, "mid"), S.xy(node, "end")
        if m is None:  # KiCad 5 style arc: start=centre, end=start point, angle
            c, st = s, e
            ang = S.num(node, "angle", 90.0)
            r = math.hypot(st[0] - c[0], st[1] - c[1])
            a0 = math.atan2(st[1] - c[1], st[0] - c[0])
            n = 16
            pts = [(c[0] + r * math.cos(a0 + math.radians(ang) * i / n),
                    c[1] + r * math.sin(a0 + math.radians(ang) * i / n)) for i in range(n + 1)]
        else:
            pts = arc_points(s, m, e)
    elif kind == "poly":
        ptsn = S.find(node, "pts")
        if ptsn is not None:
            for c in ptsn[1:]:
                if isinstance(c, list) and c[0] == "xy":
                    pts.append((_f(c[1]), _f(c[2])))
                elif isinstance(c, list) and c[0] == "arc":
                    pts.extend(arc_points(S.xy(c, "start"), S.xy(c, "mid"), S.xy(c, "end")))
            if pts:
                pts.append(pts[0])
    elif kind == "curve":
        ptsn = S.find(node, "pts")
        pts = [(_f(c[1]), _f(c[2])) for c in ptsn[1:] if isinstance(c, list) and c[0] == "xy"] if ptsn else []
    pts = [p for p in pts if p is not None]
    if tf:
        pts = [tf(x, y) for x, y in pts]
    return kind, pts


def _parse_footprint(node, ctx, board):
    fp = Footprint()
    a = S.atoms(node)
    fp.lib = a[0] if a else ""
    fp.layer = S.value(node, "layer", "F.Cu")
    at = S.find(node, "at")
    aa = S.atoms(at) if at else []
    fp.x, fp.y = _f(aa[0]) if aa else 0.0, _f(aa[1]) if len(aa) > 1 else 0.0
    fp.angle = _f(aa[2]) if len(aa) > 2 else 0.0

    def tf(x, y):
        rx, ry = rotate(x, y, fp.angle)
        return fp.x + rx, fp.y + ry

    attr = S.find(node, "attr")
    if attr is not None:
        fp.attrs = set(S.atoms(attr))
    if S.flag(node, "dnp"):
        fp.attrs.add("dnp")

    for prop in S.findall(node, "property"):
        pa = S.atoms(prop)
        if len(pa) >= 2:
            fp.props[pa[0]] = pa[1]
            if pa[0] in ("Reference", "Value"):
                t = _text_from(prop, "ref" if pa[0] == "Reference" else "value", fp, tf)
                t.text = pa[1]
                fp.texts.append(t)
    for ft in S.findall(node, "fp_text"):
        fa = S.atoms(ft)
        if len(fa) >= 2:
            kind, txt = fa[0], fa[1]
            if kind == "reference":
                fp.props["Reference"] = txt
            elif kind == "value":
                fp.props["Value"] = txt
            t = _text_from(ft, {"reference": "ref", "value": "value"}.get(kind, "user"), fp, tf)
            t.text = txt
            fp.texts.append(t)
    fp.ref = fp.props.get("Reference", "")
    fp.value = fp.props.get("Value", "")

    # body outline in footprint coordinates: fab -> courtyard -> pads
    boxes = {"fab": [], "crtyd": []}
    for g in node[1:]:
        if not isinstance(g, list) or not g or not g[0].startswith("fp_"):
            continue
        if g[0] == "fp_text":
            continue
        layer = S.value(g, "layer", "")
        key = "fab" if layer.endswith("Fab") else "crtyd" if layer.endswith("CrtYd") else None
        if layer == "Edge.Cuts":
            _, pts = _graphic_points(g, tf)
            _add_edge(board, g, pts)
            continue
        if key:
            try:
                _, pts = _graphic_points(g)
                boxes[key].extend(pts)
            except (TypeError, IndexError):
                pass

    for pn in S.findall(node, "pad"):
        p = Pad()
        pa = S.atoms(pn)
        p.fp = fp
        p.number = pa[0] if pa else ""
        p.type = pa[1] if len(pa) > 1 else "smd"
        p.shape = pa[2] if len(pa) > 2 else "rect"
        pat = S.find(pn, "at")
        pp = S.atoms(pat) if pat else []
        lx, ly = _f(pp[0]) if pp else 0.0, _f(pp[1]) if len(pp) > 1 else 0.0
        p.x, p.y = tf(lx, ly)
        # the pad angle in the file is absolute; KiCad leaves it out when it is 0
        p.angle = _f(pp[2]) if len(pp) > 2 else 0.0
        size = S.find(pn, "size")
        sa = S.atoms(size) if size else []
        p.w = _f(sa[0]) if sa else 0.0
        p.h = _f(sa[1]) if len(sa) > 1 else p.w
        dn = S.find(pn, "drill")
        p.drill = None
        if dn is not None:
            da = [x for x in S.atoms(dn) if x != "oval"]
            if da:
                d1 = _f(da[0])
                d2 = _f(da[1]) if len(da) > 1 else d1
                if d1 > 0:
                    p.drill = (d1, d2)
        layers_node = S.find(pn, "layers")
        p.layers = _expand_layers(S.atoms(layers_node) if layers_node else [], ctx.copper)
        if p.type == "np_thru_hole" and p.drill and min(p.w, p.h) <= max(p.drill) + 0.01:
            p.layers = []  # bare hole, no copper
        p.net = ctx.net(pn)
        p.pinfunction = S.value(pn, "pinfunction", "") or ""
        p.pintype = S.value(pn, "pintype", "") or ""
        rr = S.num(pn, "roundrect_rratio")
        p.rratio = rr
        if p.shape == "custom":
            p.shape = "rect"
        p.geom = _pad_geom(p, rr)
        p.area = (math.pi * p.w * p.w / 4) if p.shape == "circle" else p.w * p.h
        fp.pads.append(p)
        if p.layers:
            hw, hh = p.w / 2, p.h / 2
            rel = p.angle - fp.angle
            for cx, cy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
                rx, ry = rotate(cx, cy, rel)
                boxes.setdefault("pads", []).append((lx + rx, ly + ry))

    src = boxes["fab"] or boxes["crtyd"] or boxes.get("pads") or []
    if src:
        xs = [x for x, _ in src]
        ys = [y for _, y in src]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        fp.local_bbox = (x0, y0, x1, y1)
        fp.body = [tf(x0, y0), tf(x1, y0), tf(x1, y1), tf(x0, y1)]
        fp.body_area = (x1 - x0) * (y1 - y0)
    return fp


def _add_edge(board, node, pts):
    kind = node[0].split("_", 1)[1]
    segs = [(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]) for i in range(len(pts) - 1)]
    board.edge.segs.extend(segs)
    length = sum(math.hypot(s[2] - s[0], s[3] - s[1]) for s in segs)
    if kind in ("arc", "circle", "curve"):
        board.edge.arc_len += length
    else:
        board.edge.line_len += length


def _close_check(edge):
    from collections import Counter
    cnt = Counter()
    for x1, y1, x2, y2 in edge.segs:
        if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
            continue
        cnt[(round(x1, 2), round(y1, 2))] += 1
        cnt[(round(x2, 2), round(y2, 2))] += 1
    odd = [p for p, c in cnt.items() if c % 2]
    edge.closed = not odd and bool(edge.segs)
    edge.open_points = odd


def _parse_zone(node, ctx, board):
    z = Zone()
    z.net = S.value(node, "net_name") or ctx.net(node)
    ln = S.find(node, "layers")
    z.layers = S.atoms(ln) if ln else ([S.value(node, "layer")] if S.value(node, "layer") else [])
    z.layers = _expand_layers(z.layers, ctx.copper) if any(l.endswith("Cu") for l in z.layers) else z.layers
    z.name = S.value(node, "name", "") or ""
    z.keepout = S.find(node, "keepout") is not None
    cp = S.find(node, "connect_pads")
    if cp is not None:
        ca = S.atoms(cp)
        if ca:
            z.connect = {"yes": "solid", "no": "none", "thru_hole_only": "tht_solid"}.get(ca[0], "thermal")
    z.min_thickness = S.num(node, "min_thickness", 0.25)
    z.priority = int(S.num(node, "priority", 0) or 0)
    fill = S.find(node, "fill")
    if fill is not None and S.value(fill, "mode") == "hatch":
        z.hatch_fill = True
    poly = S.find(node, "polygon")
    if poly is not None:
        z.outline = _pts(S.find(poly, "pts"))
    for fpn in S.findall(node, "filled_polygon"):
        layer = S.value(fpn, "layer", z.layers[0] if z.layers else "")
        pts = _pts(S.find(fpn, "pts"))
        if len(pts) >= 3:
            z.fills.append((layer, pts))
    return z


def _pts(node):
    out = []
    if node is None:
        return out
    for c in node[1:]:
        if isinstance(c, list) and c:
            if c[0] == "xy":
                out.append((_f(c[1]), _f(c[2])))
            elif c[0] == "arc":
                out.extend(arc_points(S.xy(c, "start"), S.xy(c, "mid"), S.xy(c, "end")))
    return out


def load_board(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        root = S.parse(fh.read())
    if not root or root[0] != "kicad_pcb":
        raise ValueError(f"{path} is not a KiCad PCB file")
    b = Board()
    b.path = os.path.abspath(path)
    b.version = S.value(root, "version", "")
    b.generator_version = S.value(root, "generator_version", "")
    ctx = _Ctx()

    gen = S.find(root, "general")
    if gen is not None:
        b.thickness = S.num(gen, "thickness")
    layers = S.find(root, "layers")
    if layers is not None:
        cu = [l[2] if len(l) > 2 else l[1] for l in layers[1:] if isinstance(l, list) and len(l) > 2]
        cu = [l[1] for l in layers[1:] if isinstance(l, list) and len(l) > 1 and str(l[1]).endswith(".Cu")]
        order = {"F.Cu": -1, "B.Cu": 999}
        b.copper_layers = sorted(cu, key=lambda n: order.get(n, int(re.sub(r"\D", "", n) or 0)))
        ctx.copper = b.copper_layers or ["F.Cu", "B.Cu"]
    tb = S.find(root, "title_block")
    if tb is not None:
        for k in ("title", "date", "rev", "company"):
            v = S.value(tb, k)
            if v:
                b.title_block[k] = v
    setup = S.find(root, "setup")
    if setup is not None:
        st = S.find(setup, "stackup")
        if st is not None:
            for ln in S.findall(st, "layer"):
                la = S.atoms(ln)
                if la and la[0].endswith(".Cu"):
                    t = S.num(ln, "thickness")
                    if t:
                        b.copper_thickness[la[0]] = t
    for n in S.findall(root, "net"):
        a = S.atoms(n)
        if len(a) >= 2:
            ctx.netmap[a[0]] = a[1]
            if a[1]:
                b.nets.add(a[1])

    for node in root[1:]:
        if not isinstance(node, list) or not node:
            continue
        tag = node[0]
        if tag == "footprint" or tag == "module":
            b.footprints.append(_parse_footprint(node, ctx, b))
        elif tag in ("segment", "arc") and S.find(node, "start") is not None and S.find(node, "width") is not None:
            t = Track()
            t.kind = "seg" if tag == "segment" else "arc"
            t.x1, t.y1 = S.xy(node, "start")
            t.x2, t.y2 = S.xy(node, "end")
            t.mid = S.xy(node, "mid")
            t.w = S.num(node, "width", 0.0)
            t.layer = S.value(node, "layer", "")
            t.net = ctx.net(node)
            if t.kind == "arc" and t.mid:
                t.pts = arc_points((t.x1, t.y1), t.mid, (t.x2, t.y2))
            else:
                t.pts = [(t.x1, t.y1), (t.x2, t.y2)]
            t.geom = Shape.polyline(t.pts, t.w / 2)
            t.length = sum(math.hypot(t.pts[i + 1][0] - t.pts[i][0], t.pts[i + 1][1] - t.pts[i][1])
                           for i in range(len(t.pts) - 1))
            b.tracks.append(t)
        elif tag == "via":
            v = Via()
            v.x, v.y = S.xy(node, "at")
            v.size = S.num(node, "size", 0.0)
            v.drill = S.num(node, "drill", 0.0)
            ln = S.find(node, "layers")
            ends = S.atoms(ln) if ln else ["F.Cu", "B.Cu"]
            v.vtype = "through"
            for a in S.atoms(node):
                if a in ("blind", "micro", "buried"):
                    v.vtype = a
            cu = ctx.copper
            if len(ends) >= 2 and ends[0] in cu and ends[1] in cu:
                i0, i1 = sorted((cu.index(ends[0]), cu.index(ends[1])))
                v.layers = cu[i0:i1 + 1]
                if v.vtype == "through" and (i0 != 0 or i1 != len(cu) - 1):
                    v.vtype = "blind"
            else:
                v.layers = list(cu)
            v.net = ctx.net(node)
            v.geom = Shape.point(v.x, v.y, v.size / 2)
            # "remove unused via pads": no copper ring on layers where nothing connects
            v.remove_unused = S.flag(node, "remove_unused_layers")
            v.keep_end = S.flag(node, "keep_end_layers")
            b.vias.append(v)
        elif tag == "zone":
            b.zones.append(_parse_zone(node, ctx, b))
        elif tag in ("gr_text", "gr_text_box"):
            a = S.atoms(node)
            t = _text_from(node, "board", None)
            t.text = a[0] if a else ""
            b.texts.append(t)
        elif tag.startswith("gr_") and S.value(node, "layer") == "Edge.Cuts":
            try:
                _, pts = _graphic_points(node)
                _add_edge(b, node, pts)
            except (TypeError, IndexError):
                pass

    for f in b.footprints:
        for p in f.pads:
            if p.net:
                b.nets.add(p.net)
    _close_check(b.edge)

    pro = os.path.splitext(b.path)[0] + ".kicad_pro"
    if os.path.exists(pro):
        try:
            with open(pro, encoding="utf-8") as fh:
                b.project = json.load(fh)
        except (ValueError, OSError):
            b.project = {}
    return b
