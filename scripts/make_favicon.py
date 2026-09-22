"""Build MailTrace tab icons (ICO + PNG) with the stdlib only."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "static"
TEAL = (62, 224, 201, 255)
DARK = (7, 11, 18, 255)
WHITE = (232, 238, 248, 255)


def _pixel(size: int, x: int, y: int) -> tuple[int, int, int, int]:
    px = (x + 0.5) / size
    py = (y + 0.5) / size
    dx = px - 0.5
    dy = py - 0.42
    r = (dx * dx + dy * dy) ** 0.5
    if r <= 0.14:
        return WHITE
    if r <= 0.30:
        return TEAL
    # pin tip
    if py > 0.42:
        half = max(0.0, 0.30 - (py - 0.42) * 0.72)
        if abs(dx) <= half and py < 0.92:
            return TEAL
    corner = min(px, py, 1 - px, 1 - py)
    if corner < 0.06:
        return (0, 0, 0, 0)
    return DARK


def raster(size: int) -> list[tuple[int, int, int, int]]:
    return [_pixel(size, x, y) for y in range(size) for x in range(size)]


def png_bytes(size: int) -> bytes:
    rows = []
    pix = raster(size)
    i = 0
    for _y in range(size):
        row = bytearray([0])
        for _x in range(size):
            row.extend(pix[i])
            i += 1
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", ihdr)
    out += chunk(b"IDAT", zlib.compress(raw, 9))
    out += chunk(b"IEND", b"")
    return out


def ico_bytes(sizes: tuple[int, ...] = (16, 32, 48)) -> bytes:
    pngs = [png_bytes(s) for s in sizes]
    offset = 6 + 16 * len(pngs)
    buf = struct.pack("<HHH", 0, 1, len(pngs))
    for size, png in zip(sizes, pngs):
        w = 0 if size == 256 else size
        buf += struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(png), offset)
        offset += len(png)
    return buf + b"".join(pngs)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "favicon-32.png").write_bytes(png_bytes(32))
    (ROOT / "favicon-16.png").write_bytes(png_bytes(16))
    (ROOT / "favicon.ico").write_bytes(ico_bytes())
    print("wrote", ROOT / "favicon.ico")


if __name__ == "__main__":
    main()
