"""2D geometry used by the checks: shapes, distances and a grid index.

Units are millimetres. KiCad's Y axis points down and positive angles
turn counter-clockwise on screen.
"""

import math


def rotate(x, y, deg):
    """Rotate (x, y) by deg degrees the way KiCad does (CCW on screen, Y down)."""
    if not deg:
        return x, y
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return x * c + y * s, -x * s + y * c


def point_seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / L2
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _orient(ax, ay, bx, by, cx, cy):
    v = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)


def segs_intersect(a, b):
    x1, y1, x2, y2 = a
    x3, y3, x4, y4 = b
    o1 = _orient(x1, y1, x2, y2, x3, y3)
    o2 = _orient(x1, y1, x2, y2, x4, y4)
    o3 = _orient(x3, y3, x4, y4, x1, y1)
    o4 = _orient(x3, y3, x4, y4, x2, y2)
    return o1 != o2 and o3 != o4 and o1 * o2 <= 0 and o3 * o4 <= 0 and not (o1 == o2 == 0)


def seg_seg_dist(a, b):
    if segs_intersect(a, b):
        return 0.0
    x1, y1, x2, y2 = a
    x3, y3, x4, y4 = b
    return min(point_seg_dist(x1, y1, *b), point_seg_dist(x2, y2, *b),
               point_seg_dist(x3, y3, *a), point_seg_dist(x4, y4, *a))


def point_in_poly(px, py, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > py) != (yj > py):
            x = xi + (py - yi) * (xj - xi) / (yj - yi)
            if px < x:
                inside = not inside
        j = i
    return inside


def poly_area(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def arc_points(start, mid, end, max_err=0.01):
    """Polyline through an arc given by three points."""
    (x1, y1), (x2, y2), (x3, y3) = start, mid, end
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return [start, end]
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1 = math.atan2(y1 - uy, x1 - ux)
    a2 = math.atan2(y2 - uy, x2 - ux)
    a3 = math.atan2(y3 - uy, x3 - ux)

    def ccw_span(a, b):
        return (b - a) % (2 * math.pi)

    if ccw_span(a1, a2) <= ccw_span(a1, a3):
        sweep = ccw_span(a1, a3)
    else:
        sweep = -ccw_span(a3, a1)
    step = 2 * math.acos(max(-1.0, min(1.0, 1 - max_err / r))) if r > max_err else math.pi / 4
    n = max(2, int(abs(sweep) / max(step, 1e-3)) + 1)
    n = min(n, 256)
    return [(ux + r * math.cos(a1 + sweep * i / n), uy + r * math.sin(a1 + sweep * i / n)) for i in range(n + 1)]


def circle_points(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


class Shape:
    """A core (points/segments, optionally a filled polygon) grown by radius r.

    Tracks are a segment + half width, round pads/vias a point + radius,
    rectangular pads a polygon, rounded rectangles a smaller polygon + radius.
    """
    __slots__ = ("segs", "poly", "r", "bbox")

    def __init__(self, segs, r=0.0, poly=None):
        self.segs = segs
        self.poly = poly
        self.r = r
        xs = [s[0] for s in segs] + [s[2] for s in segs]
        ys = [s[1] for s in segs] + [s[3] for s in segs]
        self.bbox = (min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)

    @staticmethod
    def point(x, y, r):
        return Shape([(x, y, x, y)], r)

    @staticmethod
    def segment(x1, y1, x2, y2, r):
        return Shape([(x1, y1, x2, y2)], r)

    @staticmethod
    def polyline(pts, r):
        return Shape([(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]) for i in range(len(pts) - 1)] or
                     [(pts[0][0], pts[0][1], pts[0][0], pts[0][1])], r)

    @staticmethod
    def polygon(pts, r=0.0):
        n = len(pts)
        segs = [(pts[i][0], pts[i][1], pts[(i + 1) % n][0], pts[(i + 1) % n][1]) for i in range(n)]
        return Shape(segs, r, list(pts))

    @staticmethod
    def rect(cx, cy, w, h, angle=0.0, r=0.0):
        """Rectangle w x h centred at (cx, cy); with r, a rounded rectangle of
        the same outer size."""
        hw, hh = max(w / 2 - r, 0.0), max(h / 2 - r, 0.0)
        if hw == 0 and hh == 0:
            return Shape.point(cx, cy, r)
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        pts = []
        for x, y in corners:
            rx, ry = rotate(x, y, angle)
            pts.append((cx + rx, cy + ry))
        if hw == 0 or hh == 0:
            return Shape.segment(pts[0][0], pts[0][1], pts[2][0], pts[2][1], r)
        return Shape.polygon(pts, r)

    @staticmethod
    def oval(cx, cy, w, h, angle=0.0):
        if abs(w - h) < 1e-9:
            return Shape.point(cx, cy, w / 2)
        if w > h:
            d, r = (w - h) / 2, h / 2
            ax, ay = rotate(d, 0, angle)
        else:
            d, r = (h - w) / 2, w / 2
            ax, ay = rotate(0, d, angle)
        return Shape.segment(cx - ax, cy - ay, cx + ax, cy + ay, r)

    def contains_point(self, x, y, tol=0.0):
        if self.poly and point_in_poly(x, y, self.poly):
            return True
        return min(point_seg_dist(x, y, *s) for s in self.segs) <= self.r + tol

    def center(self):
        x0, y0, x1, y1 = self.bbox
        return (x0 + x1) / 2, (y0 + y1) / 2


def distance(a, b):
    """Edge-to-edge gap between two shapes (0 when they touch or overlap)."""
    if a.poly and b.segs and point_in_poly(b.segs[0][0], b.segs[0][1], a.poly):
        return 0.0
    if b.poly and a.segs and point_in_poly(a.segs[0][0], a.segs[0][1], b.poly):
        return 0.0
    best = float("inf")
    for sa in a.segs:
        for sb in b.segs:
            d = seg_seg_dist(sa, sb)
            if d < best:
                best = d
                if d == 0:
                    break
        if best == 0:
            break
    return max(0.0, best - a.r - b.r)


def bbox_gap(b1, b2):
    dx = max(b1[0] - b2[2], b2[0] - b1[2], 0)
    dy = max(b1[1] - b2[3], b2[1] - b1[3], 0)
    return math.hypot(dx, dy)


class GridIndex:
    """Uniform grid of bounding boxes for fast neighbour queries."""

    def __init__(self, cell=2.0):
        self.cell = cell
        self.cells = {}
        self.items = []

    def insert(self, bbox, item):
        idx = len(self.items)
        self.items.append((bbox, item))
        c = self.cell
        for ix in range(int(math.floor(bbox[0] / c)), int(math.floor(bbox[2] / c)) + 1):
            for iy in range(int(math.floor(bbox[1] / c)), int(math.floor(bbox[3] / c)) + 1):
                self.cells.setdefault((ix, iy), []).append(idx)
        return idx

    def query(self, bbox, margin=0.0):
        c = self.cell
        found = set()
        for ix in range(int(math.floor((bbox[0] - margin) / c)), int(math.floor((bbox[2] + margin) / c)) + 1):
            for iy in range(int(math.floor((bbox[1] - margin) / c)), int(math.floor((bbox[3] + margin) / c)) + 1):
                lst = self.cells.get((ix, iy))
                if lst:
                    found.update(lst)
        out = []
        for i in found:
            b, item = self.items[i]
            if bbox_gap(b, bbox) <= margin:
                out.append((i, item))
        return out


def ipc2221_width(current, delta_t, oz=1.0, outer=True):
    """Track width in mm for a current (A) and temperature rise (degC), IPC-2221."""
    k = 0.048 if outer else 0.024
    area = (current / (k * delta_t ** 0.44)) ** (1 / 0.725)  # mil^2
    return area / (1.378 * oz) * 0.0254


def ipc2221_rise(current, width_mm, oz=1.0, outer=True):
    """Temperature rise (degC) of a track carrying `current` A, IPC-2221."""
    k = 0.048 if outer else 0.024
    area = width_mm / 0.0254 * 1.378 * oz
    if area <= 0:
        return float("inf")
    return (current / (k * area ** 0.725)) ** (1 / 0.44)
