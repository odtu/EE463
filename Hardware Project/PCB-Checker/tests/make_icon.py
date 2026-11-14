"""Draw kicad_plugin/icon.png (24x24: green rounded square with a white check mark)."""

import os
import struct
import zlib

S = 24
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad_plugin", "icon.png")


def inside_rounded(x, y, r=5):
    cx = min(max(x, r), S - 1 - r)
    cy = min(max(y, r), S - 1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def near_check(x, y):
    pts = [(5.5, 12.5), (10, 17), (18.5, 7.5)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        if (x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2 <= 2.0 ** 2:
            return True
    return False


rows = b""
for y in range(S):
    row = b"\x00"
    for x in range(S):
        if not inside_rounded(x, y):
            row += bytes((0, 0, 0, 0))
        elif near_check(x + 0.5, y + 0.5):
            row += bytes((255, 255, 255, 255))
        else:
            row += bytes((46, 125, 50, 255))
    rows += row


def chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", S, S, 8, 6, 0, 0, 0)) + \
    chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")
with open(OUT, "wb") as fh:
    fh.write(png)
print("wrote", os.path.abspath(OUT))
