"""A small HTML-canvas-style drawing API on top of cairo.

The original game was drawn with the browser's 2D canvas. Cairo has the same
model (paths, curves, clipping, gradients), so this wrapper keeps the canvas
semantics the art code relies on: paths survive fill/stroke/clip, fillRect
leaves the current path alone, and fill/stroke styles are saved by save().
"""

import math
from functools import lru_cache
from pathlib import Path

import cairo
import numpy as np
import pygame

FONT_DIR = Path(__file__).parent / "assets" / "fonts"
FONT_FILES = {
    "bagel": "BagelFatOne-Regular.ttf",
    "sniglet": "Sniglet-Regular.ttf",
    "sniglet-bold": "Sniglet-ExtraBold.ttf",
    "luckiest": "LuckiestGuy-Regular.ttf",
}
CAPS = {"butt": cairo.LINE_CAP_BUTT, "round": cairo.LINE_CAP_ROUND, "square": cairo.LINE_CAP_SQUARE}
JOINS = {"miter": cairo.LINE_JOIN_MITER, "round": cairo.LINE_JOIN_ROUND, "bevel": cairo.LINE_JOIN_BEVEL}


@lru_cache(maxsize=8192)
def parse_color(c):
    c = c.strip()
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            r, g, b = (int(ch * 2, 16) for ch in h)
        else:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r / 255, g / 255, b / 255, 1.0)
    if c.startswith("rgb"):
        parts = [p.strip() for p in c[c.index("(") + 1 : c.rindex(")")].split(",")]
        r, g, b = (float(p) / 255 for p in parts[:3])
        a = float(parts[3]) if len(parts) > 3 else 1.0
        return (r, g, b, max(0.0, min(1.0, a)))
    return (0.0, 0.0, 0.0, 0.0)


def color(c):
    return c if isinstance(c, tuple) else parse_color(c)


def rgba(r, g, b, a=1.0):
    return (r / 255, g / 255, b / 255, max(0.0, min(1.0, a)))


class Gradient:
    def __init__(self, kind, args):
        self.kind, self.args, self.stops = kind, args, []

    def addColorStop(self, off, c):
        self.stops.append((off, color(c)))

    def pattern(self, alpha):
        if self.kind == "lin":
            p = cairo.LinearGradient(*self.args)
        else:
            x0, y0, r0, x1, y1, r1 = self.args
            p = cairo.RadialGradient(x0, y0, max(0.0, r0), x1, y1, max(0.0, r1))
        for off, (r, g, b, a) in self.stops:
            p.add_color_stop_rgba(off, r, g, b, a * alpha)
        return p


class Font:
    """Parses canvas font strings like "800 15px Sniglet,sans-serif"."""

    _cache = {}

    @classmethod
    def get(cls, spec):
        f = cls._cache.get(spec)
        if f is None:
            f = cls._cache[spec] = cls(spec)
        return f

    def __init__(self, spec):
        s = spec.lower()
        self.size = 10.0
        for tok in s.replace(",", " ").split():
            if tok.endswith("px"):
                self.size = float(tok[:-2])
                break
        bold = " 800 " in f" {s} " or "bold" in s
        if "bagel" in s:
            self.key = "bagel"
        elif "luckiest" in s:
            self.key = "luckiest"
        elif "sniglet" in s:
            self.key = "sniglet-bold" if bold else "sniglet"
        else:
            self.key = "arial-bold" if bold else "arial"


_pg_fonts = {}


def pg_font(key, px):
    k = (key, px)
    f = _pg_fonts.get(k)
    if f is None:
        if key in FONT_FILES:
            f = pygame.font.Font(str(FONT_DIR / FONT_FILES[key]), px)
        else:
            f = pygame.font.SysFont("arial", px, bold=key.endswith("bold"))
        _pg_fonts[k] = f
    return f


_text_cache = {}


def _to_cairo(surf):
    w, h = surf.get_size()
    raw = np.frombuffer(pygame.image.tobytes(surf, "BGRA"), dtype=np.uint8).reshape(h, w, 4)
    out = np.empty_like(raw)
    a = raw[..., 3:4].astype(np.uint16)
    out[..., :3] = (raw[..., :3].astype(np.uint16) * a // 255).astype(np.uint8)
    out[..., 3] = raw[..., 3]
    buf = bytearray(out.tobytes())
    img = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, w, h, w * 4)
    return img, buf


def text_image(text, key, px, rgb, outline=0, spacing=0):
    k = (text, key, px, rgb, outline, spacing)
    hit = _text_cache.get(k)
    if hit:
        return hit
    f = pg_font(key, px)
    col = tuple(int(round(v * 255)) for v in rgb)
    advances = [f.size(ch)[0] for ch in text] if spacing else None
    if outline:
        f.outline = outline
    if spacing:
        # lay glyphs out by their plain advance so outlined and filled text line up
        glyphs = [f.render(ch, True, col) for ch in text]
        w = sum(advances) + spacing * max(0, len(glyphs) - 1) + outline * 2
        surf = pygame.Surface((max(1, w), max(gl.get_height() for gl in glyphs)), pygame.SRCALPHA)
        x = 0
        for gl, adv in zip(glyphs, advances):
            surf.blit(gl, (x, 0))
            x += adv + spacing
    else:
        surf = f.render(text, True, col)
    asc = f.get_ascent() + outline
    if outline:
        f.outline = 0
    img, buf = _to_cairo(surf)
    hit = (img, buf, surf.get_width(), surf.get_height(), asc)
    if len(_text_cache) > 3000:
        _text_cache.clear()
    _text_cache[k] = hit
    return hit


class Canvas:
    def __init__(self, surface):
        self.surface = surface
        self.ctx = cairo.Context(surface)
        self.ctx.set_line_width(1)
        self.fillStyle = (0.0, 0.0, 0.0, 1.0)
        self.strokeStyle = (0.0, 0.0, 0.0, 1.0)
        self.globalAlpha = 1.0
        self.font = "10px sans-serif"
        self.textAlign = "start"
        self.textBaseline = "alphabetic"
        self.letterSpacing = 0
        self._lw = 1.0
        self._stack = []

    # ---- state ----
    def save(self):
        self.ctx.save()
        self._stack.append((self.fillStyle, self.strokeStyle, self.globalAlpha, self.font,
                            self.textAlign, self.textBaseline, self.letterSpacing, self._lw))

    def restore(self):
        self.ctx.restore()
        if self._stack:
            (self.fillStyle, self.strokeStyle, self.globalAlpha, self.font,
             self.textAlign, self.textBaseline, self.letterSpacing, self._lw) = self._stack.pop()

    @property
    def lineWidth(self):
        return self._lw

    @lineWidth.setter
    def lineWidth(self, v):
        self._lw = v
        self.ctx.set_line_width(v)

    @property
    def lineCap(self):
        return None

    @lineCap.setter
    def lineCap(self, v):
        self.ctx.set_line_cap(CAPS[v])

    @property
    def lineJoin(self):
        return None

    @lineJoin.setter
    def lineJoin(self, v):
        self.ctx.set_line_join(JOINS[v])

    def setTransform(self, a, b, c, d, e, f):
        self.ctx.set_matrix(cairo.Matrix(a, b, c, d, e, f))

    def translate(self, x, y):
        self.ctx.translate(x, y)

    def rotate(self, a):
        self.ctx.rotate(a)

    def scale(self, x, y):
        if x == 0 or y == 0:
            x = x or 1e-4
            y = y or 1e-4
        self.ctx.scale(x, y)

    # ---- paths ----
    def beginPath(self):
        self.ctx.new_path()

    def moveTo(self, x, y):
        self.ctx.move_to(x, y)

    def lineTo(self, x, y):
        self.ctx.line_to(x, y)

    def closePath(self):
        self.ctx.close_path()

    def quadraticCurveTo(self, cx, cy, x, y):
        ctx = self.ctx
        if not ctx.has_current_point():
            ctx.move_to(cx, cy)
        x0, y0 = ctx.get_current_point()
        ctx.curve_to(x0 + 2 / 3 * (cx - x0), y0 + 2 / 3 * (cy - y0),
                     x + 2 / 3 * (cx - x), y + 2 / 3 * (cy - y), x, y)

    def bezierCurveTo(self, c1x, c1y, c2x, c2y, x, y):
        if not self.ctx.has_current_point():
            self.ctx.move_to(c1x, c1y)
        self.ctx.curve_to(c1x, c1y, c2x, c2y, x, y)

    def arc(self, x, y, r, a0, a1, ccw=False):
        r = max(0.0, r)
        a1 = _clamp_sweep(a0, a1, ccw)
        if ccw:
            self.ctx.arc_negative(x, y, r, a0, a1)
        else:
            self.ctx.arc(x, y, r, a0, a1)

    def ellipse(self, x, y, rx, ry, rot, a0, a1, ccw=False):
        ctx = self.ctx
        rx = max(rx, 1e-3)
        ry = max(ry, 1e-3)
        a1 = _clamp_sweep(a0, a1, ccw)
        m = ctx.get_matrix()
        ctx.translate(x, y)
        if rot:
            ctx.rotate(rot)
        ctx.scale(rx, ry)
        if ccw:
            ctx.arc_negative(0, 0, 1, a0, a1)
        else:
            ctx.arc(0, 0, 1, a0, a1)
        ctx.set_matrix(m)

    def rect(self, x, y, w, h):
        self.ctx.rectangle(x, y, w, h)

    def roundRect(self, x, y, w, h, r):
        rr_path(self.ctx, x, y, w, h, r)

    # ---- painting ----
    def _source(self, style):
        if isinstance(style, Gradient):
            self.ctx.set_source(style.pattern(self.globalAlpha))
        else:
            r, g, b, a = color(style)
            self.ctx.set_source_rgba(r, g, b, a * self.globalAlpha)

    def fill(self, rule=None):
        self._source(self.fillStyle)
        if rule == "evenodd":
            self.ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            self.ctx.fill_preserve()
            self.ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        else:
            self.ctx.fill_preserve()

    def stroke(self):
        self._source(self.strokeStyle)
        self.ctx.stroke_preserve()

    def clip(self):
        self.ctx.clip_preserve()

    def fillRect(self, x, y, w, h):
        ctx = self.ctx
        path = ctx.copy_path() if ctx.has_current_point() else None
        ctx.new_path()
        ctx.rectangle(x, y, w, h)
        self._source(self.fillStyle)
        ctx.fill()
        if path is not None:
            ctx.append_path(path)

    def strokeRect(self, x, y, w, h):
        ctx = self.ctx
        path = ctx.copy_path() if ctx.has_current_point() else None
        ctx.new_path()
        ctx.rectangle(x, y, w, h)
        self._source(self.strokeStyle)
        ctx.stroke()
        if path is not None:
            ctx.append_path(path)

    def createLinearGradient(self, x0, y0, x1, y1):
        return Gradient("lin", (x0, y0, x1, y1))

    def createRadialGradient(self, x0, y0, r0, x1, y1, r1):
        return Gradient("rad", (x0, y0, r0, x1, y1, r1))

    # ---- text ----
    def _device_scale(self):
        xx, yx, xy, yy, _, _ = self.ctx.get_matrix()
        return max(0.25, math.sqrt(abs(xx * yy - xy * yx)))

    def measureText(self, text):
        f = Font.get(self.font)
        k = self._device_scale()
        px = max(4, int(round(f.size * k)))
        fo = pg_font(f.key, px)
        w = fo.size(text)[0] + self.letterSpacing * k * max(0, len(text) - 1)
        return w / k

    def _draw_text(self, text, x, y, style, outline_w):
        if not text:
            return
        f = Font.get(self.font)
        k = self._device_scale()
        px = max(4, int(round(f.size * k)))
        r, g, b, a = color(style) if not isinstance(style, Gradient) else (1, 1, 1, 1)
        ol = int(round(outline_w * k / 2)) if outline_w else 0
        sp = int(round(self.letterSpacing * k))
        img, _buf, w, h, asc = text_image(text, f.key, px, (r, g, b), ol, sp)
        w_u, h_u = w / k, h / k
        if self.textAlign == "center":
            x -= w_u / 2
        elif self.textAlign in ("right", "end"):
            x -= w_u - ol / k
        else:
            x -= ol / k
        if self.textBaseline == "top":
            y -= ol / k
        elif self.textBaseline == "middle":
            y -= h_u / 2
        else:
            y -= asc / k
        ctx = self.ctx
        path = ctx.copy_path() if ctx.has_current_point() else None
        alpha = max(0.0, min(1.0, a * self.globalAlpha))
        xx, yx, xy, yy, _, _ = ctx.get_matrix()
        ctx.save()
        if abs(yx) < 1e-9 and abs(xy) < 1e-9 and abs(xx - yy) < 1e-6:
            # unrotated: snap to whole device pixels so cairo can copy the glyphs without resampling
            dx, dy = ctx.user_to_device(x, y)
            ctx.identity_matrix()
            blit(ctx, img, round(dx), round(dy), w, h, alpha)
        else:
            ctx.translate(x, y)
            ctx.scale(1 / k, 1 / k)
            blit(ctx, img, 0, 0, w, h, alpha)
        ctx.restore()
        if path is not None:
            ctx.new_path()
            ctx.append_path(path)

    def fillRects(self, rects):
        """Fill many same-coloured rectangles in one pass."""
        ctx = self.ctx
        path = ctx.copy_path() if ctx.has_current_point() else None
        ctx.new_path()
        for r in rects:
            ctx.rectangle(*r)
        self._source(self.fillStyle)
        ctx.fill()
        if path is not None:
            ctx.append_path(path)

    def drawImage(self, img, cx, cy):
        """Paint a pre-rendered device-resolution image centred on a user-space point, pixel-aligned."""
        ctx = self.ctx
        dx, dy = ctx.user_to_device(cx, cy)
        w, h = img.get_width(), img.get_height()
        ctx.save()
        ctx.identity_matrix()
        blit(ctx, img, round(dx - w / 2), round(dy - h / 2), w, h, self.globalAlpha)
        ctx.restore()

    def drawImageAt(self, img, x, y):
        """Paint a device-resolution image with its top-left at a user-space point, pixel-aligned."""
        ctx = self.ctx
        dx, dy = ctx.user_to_device(x, y)
        ctx.save()
        ctx.identity_matrix()
        blit(ctx, img, round(dx), round(dy), img.get_width(), img.get_height(), self.globalAlpha)
        ctx.restore()

    def fillText(self, text, x, y):
        self._draw_text(str(text), x, y, self.fillStyle, 0)

    def strokeText(self, text, x, y):
        self._draw_text(str(text), x, y, self.strokeStyle, max(1.0, self._lw))


def blit(ctx, img, x, y, w, h, alpha):
    ctx.set_source_surface(img, x, y)
    ctx.new_path()
    ctx.rectangle(x, y, w, h)
    if alpha >= 1.0:
        ctx.fill()
    else:
        ctx.clip()
        ctx.paint_with_alpha(alpha)


def offscreen(w, h, scale):
    """A transparent device-resolution surface plus a Canvas drawing into it at the given scale."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, int(math.ceil(w))), max(1, int(math.ceil(h))))
    cv = Canvas(surf)
    cv.setTransform(scale, 0, 0, scale, 0, 0)
    return surf, cv


TAU = 2 * math.pi


def _clamp_sweep(a0, a1, ccw):
    """Canvas draws exactly one full turn when the sweep is 2*pi or more; cairo would overlap."""
    if not ccw and a1 - a0 >= TAU:
        return a0 + TAU
    if ccw and a0 - a1 >= TAU:
        return a0 - TAU
    return a1


def rr_path(ctx, x, y, w, h, r):
    r = max(0.0, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()
