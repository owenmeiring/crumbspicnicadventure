"""Render Crumb (the real game art) into a multi-size Windows .ico for the executable."""

import os
import struct
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import cairo  # noqa: E402
import pygame  # noqa: E402

from crumb import art  # noqa: E402
from crumb.canvas import Canvas  # noqa: E402
from crumb.game import O, S  # noqa: E402

SIZES = (256, 128, 64, 48, 32, 16)


def render(size):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    art.g = Canvas(surf)
    k = size / 33.7
    art.g.setTransform(k, 0, 0, k, 0, 0)
    S.state = "card"
    S.P = O(x=5.8, y=4, w=22, h=28, vx=0, vy=0, ground=True, face=1, big=False, fire=False, inv=0, duck=0, mk=2, mt=5)
    art.draw_player()
    surf.flush()
    img = pygame.image.frombuffer(surf.get_data(), (size, size), "BGRA").copy()
    path = Path(os.environ.get("TEMP", ".")) / f"crumb_icon_{size}.png"
    pygame.image.save(img, str(path))
    return path.read_bytes()


def main(out):
    pygame.init()
    pngs = [render(s) for s in SIZES]
    header = struct.pack("<HHH", 0, 1, len(pngs))
    offset = 6 + 16 * len(pngs)
    entries, blobs = b"", b""
    for s, png in zip(SIZES, pngs):
        entries += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(png), offset + len(blobs))
        blobs += png
    Path(out).write_bytes(header + entries + blobs)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packaging/crumb.ico")
