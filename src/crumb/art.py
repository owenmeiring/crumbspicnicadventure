"""All of the game's artwork, ported shape-for-shape from the original canvas code."""

import math
import random

from .canvas import offscreen, rr_path
from .game import (GPL, GPW, OHD, OHM, PINKPAL, BASEPAL, ROLLCD, ROLLT, NAMES, H, S, T, VH, VW, mouth_y, ohs_of)

g = None  # the Canvas, set by the app
RS = 2.0  # render scale: device pixels per game pixel
OL = "#2b1608"
PI = math.pi
sin, cos = math.sin, math.cos
rnd = random.random


def rr(x, y, w, h, r):
    g.beginPath()
    rr_path(g.ctx, x, y, w, h, r)


def cel(cx, cy, rx, ry, base, shade, hi=None):
    g.fillStyle = OL
    g.beginPath(); g.ellipse(cx, cy, rx + 2, ry + 2, 0, 0, 7); g.fill()
    g.fillStyle = base
    g.beginPath(); g.ellipse(cx, cy, rx, ry, 0, 0, 7); g.fill()
    g.save(); g.beginPath(); g.ellipse(cx, cy, rx, ry, 0, 0, 7); g.clip()
    g.fillStyle = shade
    g.beginPath(); g.ellipse(cx - rx * .35, cy - ry * .3, rx * 1.1, ry * 1.1, 0, 0, 7)
    g.rect(cx - rx - 2, cy - ry - 2, rx * 2 + 4, ry * 2 + 4); g.fill("evenodd")
    g.restore()
    if hi:
        g.fillStyle = hi
        g.beginPath(); g.ellipse(cx - rx * .42, cy - ry * .5, rx * .26, ry * .17, -.6, 0, 7); g.fill()


def limb(pts, c, w):
    g.lineCap = "round"; g.lineJoin = "round"
    g.beginPath(); g.moveTo(*pts[0])
    for p in pts[1:]:
        g.lineTo(*p)
    g.strokeStyle = OL; g.lineWidth = w + 2.4; g.stroke()
    g.strokeStyle = c; g.lineWidth = w; g.stroke()
    g.lineCap = "butt"


def ell(cx, cy, rx, ry, fill, rot=0):
    g.beginPath(); g.ellipse(cx, cy, rx, ry, rot, 0, 7)
    g.fillStyle = fill; g.fill(); g.strokeStyle = OL; g.lineWidth = .95; g.stroke()


def sparkle(x, y, r, al):
    g.save(); g.globalAlpha = max(0, al); g.translate(x, y); g.fillStyle = "#fff3b0"
    g.beginPath(); g.moveTo(0, -r); g.quadraticCurveTo(0, 0, r, 0); g.quadraticCurveTo(0, 0, 0, r)
    g.quadraticCurveTo(0, 0, -r, 0); g.quadraticCurveTo(0, 0, 0, -r); g.fill(); g.restore()


def hsh(a, b):
    return ((a * 73856093) & 0xFFFFFFFF) ^ ((b * 19349663) & 0xFFFFFFFF)


def gsolid(x, y):
    return 0 <= x < S.W and 0 <= y < H and S.grid[y][x] != 0


def glow(cx, cy, r0, r1, rgb, a):
    gl = g.createRadialGradient(cx, cy, r0, cx, cy, r1)
    gl.addColorStop(0, f"rgba({rgb},{a})"); gl.addColorStop(1, f"rgba({rgb},0)")
    g.fillStyle = gl; g.beginPath(); g.arc(cx, cy, r1, 0, 7); g.fill()


# ======================================================================= items
def cookie_art(cx, cy, r):
    ol = max(1, r * .16)
    g.fillStyle = OL; g.beginPath(); g.arc(cx, cy, r + ol, 0, 7); g.fill()
    g.fillStyle = "#dc9c4c"; g.beginPath(); g.arc(cx, cy, r, 0, 7); g.fill()
    g.save(); g.beginPath(); g.arc(cx, cy, r, 0, 7); g.clip()
    g.fillStyle = "#b26e2e"; g.beginPath(); g.arc(cx - r * .35, cy - r * .3, r * 1.1, 0, 7)
    g.rect(cx - r - 2, cy - r - 2, r * 2 + 4, r * 2 + 4); g.fill("evenodd")
    for a in [[-.35, -.35, .2], [.3, -.25, .17], [-.1, .3, .2], [.45, .35, .15], [-.55, .15, .13]]:
        g.fillStyle = "#3a1e0e"; g.beginPath(); g.ellipse(cx + a[0] * r, cy + a[1] * r, r * a[2], r * a[2] * .85, .4, 0, 7); g.fill()
        if r > 7:
            g.fillStyle = "#7a4a2a"; g.beginPath()
            g.arc(cx + a[0] * r - r * a[2] * .3, cy + a[1] * r - r * a[2] * .3, r * a[2] * .3, 0, 7); g.fill()
    g.restore()
    g.fillStyle = "#ffe2a8"; g.beginPath(); g.ellipse(cx - r * .5, cy - r * .55, r * .26, r * .14, -.7, 0, 7); g.fill()


def pizza_art(cx, cy, r):
    top = cy - r * .72

    def tri():
        g.beginPath(); g.moveTo(cx - r, top); g.lineTo(cx + r, top); g.lineTo(cx, cy + r * 1.08); g.closePath()

    g.lineJoin = "round"
    tri(); g.fillStyle = "#ffcf55"; g.fill()
    g.save(); tri(); g.clip()
    g.fillStyle = "#e9a52e"; g.beginPath(); g.moveTo(cx + r * .1, top); g.lineTo(cx + r, top); g.lineTo(cx, cy + r * 1.08); g.closePath(); g.fill()
    g.fillStyle = "#ffe9a3"; g.beginPath(); g.ellipse(cx - r * .5, top + r * .85, r * .11, r * .35, .5, 0, 7); g.fill()
    for p in [[-.32, -.12, .22], [.32, -.04, .2], [0, .42, .17]]:
        g.fillStyle = "#6e1a12"; g.beginPath(); g.arc(cx + p[0] * r, cy + p[1] * r, r * p[2] + 1, 0, 7); g.fill()
        g.fillStyle = "#d0402f"; g.beginPath(); g.arc(cx + p[0] * r, cy + p[1] * r, r * p[2], 0, 7); g.fill()
        g.fillStyle = "#ff8a70"; g.beginPath(); g.arc(cx + p[0] * r - r * .06, cy + p[1] * r - r * .06, r * p[2] * .3, 0, 7); g.fill()
    g.restore()
    tri(); g.strokeStyle = OL; g.lineWidth = 2; g.stroke()
    cx0, cw, cy0, ch = cx - r - 1.5, r * 2 + 3, top - r * .34, r * .5
    rr(cx0, cy0, cw, ch, r * .25); g.fillStyle = "#e6a95a"; g.fill()
    g.save(); rr(cx0, cy0, cw, ch, r * .25); g.clip()
    g.fillStyle = "#c0812f"; g.fillRect(cx0, cy0 + ch * .55, cw, ch); g.fillStyle = "#f7cf8a"; g.fillRect(cx0, cy0, cw, ch * .25)
    g.restore()
    rr(cx0, cy0, cw, ch, r * .25); g.strokeStyle = OL; g.lineWidth = 2; g.stroke()


# ======================================================================= backgrounds
def tile_x(period, par, fn):
    rc = round(S.cam)
    off = -((rc * par) % period)
    x = off - period
    while x < VW + period:
        fn(x)
        x += period


def wdeco(period, fn):
    rc = round(S.cam)
    off = -(rc % period)
    x = off - period
    while x < VW + period:
        fn(x, x + rc)
        x += period


def hill_y(sx, par, base, amp, f):
    x = sx + round(S.cam) * par
    return base + sin(x * f) * amp + sin(x * f * 2.3 + 1.7) * amp * .4


def hill(par, base, amp, f, col, edge):
    pts = [(x, hill_y(x, par, base, amp, f)) for x in range(0, VW + 9, 8)]
    g.beginPath(); g.moveTo(0, VH)
    for p in pts:
        g.lineTo(*p)
    g.lineTo(VW, VH); g.closePath(); g.fillStyle = col; g.fill()
    g.strokeStyle = edge; g.lineWidth = 2; g.beginPath(); g.moveTo(*pts[0])
    for p in pts[1:]:
        g.lineTo(*p)
    g.stroke()


RID = [[0, 250], [90, 160], [150, 215], [230, 120], [320, 200], [400, 150], [480, 225], [560, 170], [640, 250]]


def mountains():
    def one(ox):
        g.beginPath(); g.moveTo(ox, VH)
        for p in RID:
            g.lineTo(ox + p[0], p[1])
        g.lineTo(ox + 640, VH); g.closePath(); g.fillStyle = "#b8c6e8"; g.fill()
        for i in (1, 3, 5, 7):
            p, n = RID[i], RID[i + 1]
            g.fillStyle = "#95a6d2"; g.beginPath(); g.moveTo(ox + p[0], p[1]); g.lineTo(ox + n[0], n[1])
            g.lineTo(ox + n[0], 300); g.lineTo(ox + p[0], 300); g.closePath(); g.fill()
            g.fillStyle = "#fff"; g.beginPath(); g.moveTo(ox + p[0], p[1]); g.lineTo(ox + p[0] - 15, p[1] + 24)
            g.lineTo(ox + p[0] - 6, p[1] + 19); g.lineTo(ox + p[0], p[1] + 26); g.lineTo(ox + p[0] + 6, p[1] + 19)
            g.lineTo(ox + p[0] + 15, p[1] + 24); g.closePath(); g.fill()
    tile_x(640, .08, one)


def cloud(x, y, s):
    g.save(); g.translate(x, y); g.scale(s, s)
    pf = [[0, 0, 30, 13], [22, 5, 22, 10], [-22, 5, 20, 9], [8, -8, 16, 10]]
    g.fillStyle = "#c5d5ec"
    for p in pf:
        g.beginPath(); g.ellipse(p[0], p[1] + 4, p[2], p[3], 0, 0, 7); g.fill()
    g.fillStyle = "#fff"
    for p in pf:
        g.beginPath(); g.ellipse(p[0], p[1], p[2], p[3], 0, 0, 7); g.fill()
    g.restore()


def pine(x, y, s):
    g.save(); g.translate(x, y); g.scale(s, s)
    g.fillStyle = "#5a3a22"; g.fillRect(-3.5, -12, 7, 12); g.fillStyle = "#8a5a34"; g.fillRect(-2, -11, 4, 11)
    g.fillStyle = "#6b4326"; g.fillRect(0, -11, 2, 11)
    for t in [[-46, -12, 21], [-58, -26, 17], [-68, -40, 13]]:
        def p():
            g.beginPath(); g.moveTo(0, t[0]); g.lineTo(-t[2], t[1]); g.lineTo(t[2], t[1]); g.closePath()
        p(); g.fillStyle = "#3f9a4a"; g.fill()
        g.save(); p(); g.clip(); g.fillStyle = "#2b7539"; g.beginPath(); g.moveTo(0, t[0]); g.lineTo(t[2], t[1])
        g.lineTo(0, t[1]); g.closePath(); g.fill()
        g.fillStyle = "#7fd07a"; g.beginPath(); g.moveTo(-1, t[0] + 6); g.lineTo(-t[2] * .5, t[1] - 4)
        g.lineTo(-t[2] * .3, t[1] - 4); g.closePath(); g.fill(); g.restore()
        p(); g.strokeStyle = "#2a6a36"; g.lineWidth = 1.5; g.lineJoin = "round"; g.stroke()
    g.restore()


def flower(x, y, c, k):
    hg, hx = 8 + k * 3, x + (k - 1) * .8
    g.strokeStyle = OL; g.lineWidth = 3; g.beginPath(); g.moveTo(x, y); g.lineTo(hx, y - hg); g.stroke()
    g.strokeStyle = "#3f9a4a"; g.lineWidth = 1.5; g.beginPath(); g.moveTo(x, y); g.lineTo(hx, y - hg); g.stroke()
    g.fillStyle = "#3f9a4a"; g.beginPath(); g.ellipse(x + 3, y - 4, 3, 1.4, -.5, 0, 7); g.fill()
    for i in range(5):
        a = i * PI * 2 / 5
        g.fillStyle = c; g.strokeStyle = OL; g.lineWidth = .8
        g.beginPath(); g.arc(hx + cos(a) * 3, y - hg + sin(a) * 3, 2.3, 0, 7); g.fill(); g.stroke()
    g.fillStyle = "#ffd84d"; g.beginPath(); g.arc(hx, y - hg, 2, 0, 7); g.fill()


def bird(x, y, ph):
    w = sin(ph) * 4
    g.strokeStyle = "#3b3550"; g.lineWidth = 1.6; g.lineCap = "round"
    g.beginPath(); g.moveTo(x - 6, y - w * .6 + 1); g.quadraticCurveTo(x - 3, y - w - 2, x, y)
    g.quadraticCurveTo(x + 3, y - w - 2, x + 6, y - w * .6 + 1); g.stroke(); g.lineCap = "butt"


def butterfly(x, y, c, ph):
    w = abs(sin(ph)) * 4 + 1
    g.fillStyle = OL; g.beginPath(); g.ellipse(x - 3, y, w + 1, 4.5, -.4, 0, 7); g.ellipse(x + 3, y, w + 1, 4.5, .4, 0, 7); g.fill()
    g.fillStyle = c; g.beginPath(); g.ellipse(x - 3, y, w, 3.5, -.4, 0, 7); g.ellipse(x + 3, y, w, 3.5, .4, 0, 7); g.fill()
    g.fillStyle = OL; g.fillRect(x - .6, y - 3, 1.2, 6)


FC = ["#ff5d73", "#ffd84d", "#ffffff", "#ff9ad5", "#8fb6ff"]


def sun():
    P = S.P
    p = max(0, min(1, P.x / (S.W * T))) if P else 0
    sx, sy, r = 70 + p * (VW - 140), 88 - sin(p * PI) * 40, 17
    glow(sx, sy, r * .5, r * 3, "255,240,150", .55)
    g.save(); g.translate(sx, sy); g.rotate(S.tick * .004); g.strokeStyle = "#e8a020"; g.lineWidth = 3; g.lineCap = "round"
    for i in range(10):
        a = i * PI / 5
        g.beginPath(); g.moveTo(cos(a) * (r + 4), sin(a) * (r + 4)); g.lineTo(cos(a) * (r + 9), sin(a) * (r + 9)); g.stroke()
    g.restore(); g.lineCap = "butt"
    g.fillStyle = "#e8961a"; g.beginPath(); g.arc(sx, sy, r + 1.8, 0, 7); g.fill()
    g.fillStyle = "#ffd84d"; g.beginPath(); g.arc(sx, sy, r, 0, 7); g.fill()
    g.save(); g.beginPath(); g.arc(sx, sy, r, 0, 7); g.clip()
    g.fillStyle = "#f2b524"; g.beginPath(); g.arc(sx - r * .3, sy - r * .3, r * 1.05, 0, 7); g.rect(sx - r - 1, sy - r - 1, r * 2 + 2, r * 2 + 2); g.fill("evenodd")
    g.restore()
    g.fillStyle = "#fff6c2"; g.beginPath(); g.ellipse(sx - r * .4, sy - r * .45, r * .25, r * .16, -.6, 0, 7); g.fill()


def bg_lawn():
    tick = S.tick
    sky = g.createLinearGradient(0, 0, 0, VH)
    sky.addColorStop(0, "#6cb8e6"); sky.addColorStop(.6, "#bfe6f2"); sky.addColorStop(1, "#fdeec4")
    g.fillStyle = sky; g.fillRect(0, 0, VW, VH)
    sun(); mountains()
    for i in range(5):
        x = ((i * 260 - S.cam * .12 + tick * .1) % 1300 + 1300) % 1300 - 150
        cloud(x, 44 + (i * 37) % 64, .8 + (i % 3) * .25)
    for i in range(3):
        x = ((tick * .55 + i * 190) % (VW + 80) + VW + 80) % (VW + 80) - 40
        bird(x, 64 + i * 24 + sin(tick * .03 + i * 2) * 6, tick * .22 + i * 1.7)
    hill(.2, 268, 14, .006, "#a4d98f", "#86c477")
    hill(.35, 292, 16, .007, "#82c96f", "#62b056")
    pines = [[60, .85], [210, 1], [330, .75], [450, .9]]
    tile_x(560, .35, lambda ox: [pine(ox + t[0], hill_y(ox + t[0], .35, 292, 16, .007) + 2, t[1]) for t in pines])
    hill(.35, 292, 16, .007, "#82c96f", "#62b056")

    def shadows(ox):
        for t in pines:
            x = ox + t[0]
            g.fillStyle = "rgba(35,100,55,.25)"; g.beginPath(); g.ellipse(x, hill_y(x, .35, 292, 16, .007) + 4, 15 * t[1], 3, 0, 0, 7); g.fill()
    tile_x(560, .35, shadows)
    dg = g.createLinearGradient(0, 322, 0, VH); dg.addColorStop(0, "rgba(24,60,40,0)"); dg.addColorStop(1, "rgba(20,45,35,.6)")
    g.fillStyle = dg; g.fillRect(0, 322, VW, VH - 322)

    def flowers(sx, wx):
        k = math.floor(wx / 256)
        o = 70 + (k % 3) * 40
        tx = math.floor((wx + o) / T)
        if k % 2 == 0 and gsolid(tx, 10) and not gsolid(tx, 9):
            flower(sx + o, 321, FC[k % 5], k % 3)
    wdeco(256, flowers)
    for i, bf in enumerate([["#ff9a3d", 0], ["#ff7fc0", 1.7]]):
        t = tick * .02 + bf[1]
        butterfly(140 + i * 190 + sin(t * 1.3) * 40, 236 + sin(t * 2.1) * 16, bf[0], tick * .3 + i)


def brick_wall(par, col):
    off = -((round(S.cam) * par) % 48)
    rects = []
    for y in range(64, 320, 24):
        rects.append((0, y, VW, 1.5))
        st = 24 if ((y - 64) // 24) % 2 else 0
        x = off - 48 + st
        while x < VW + 48:
            rects.append((x, y, 1.5, 24))
            x += 48
    g.fillStyle = col
    g.fillRects(rects)


def lantern(x, y):
    g.fillStyle = OL; g.fillRect(x - 4.5, 64, 9, 5.5); g.fillStyle = "#5a5a66"; g.fillRect(x - 3, 64, 6, 3.8)
    g.strokeStyle = "#5a5a66"; g.lineWidth = 2; g.beginPath(); g.moveTo(x, 64); g.lineTo(x, y - 11); g.stroke()
    r = 78 + sin(S.tick * .13 + x) * 5
    gl = g.createRadialGradient(x, y + 2, 4, x, y + 2, r)
    gl.addColorStop(0, "rgba(255,200,110,.5)"); gl.addColorStop(1, "rgba(255,200,110,0)")
    g.fillStyle = gl; g.beginPath(); g.arc(x, y + 2, r, 0, 7); g.fill()
    g.fillStyle = OL; rr(x - 8.5, y - 9.5, 17, 23, 3); g.fill(); g.fillStyle = "#ffd56a"; rr(x - 6.5, y - 7.5, 13, 19, 2); g.fill()
    g.fillStyle = "#fff2b8"; g.fillRect(x - 3, y - 3, 6, 9)
    g.fillStyle = OL; g.fillRect(x - .8, y - 8, 1.6, 20)
    g.beginPath(); g.moveTo(x - 11, y - 9); g.lineTo(x + 11, y - 9); g.lineTo(x, y - 18); g.closePath(); g.fill()


def barrel(x, y):
    g.fillStyle = "rgba(0,0,0,.35)"; g.beginPath(); g.ellipse(x, y + 1, 23, 3.6, 0, 0, 7); g.fill()
    g.fillStyle = OL; rr(x - 18.5, y - 41, 37, 41, 10); g.fill()
    g.fillStyle = "#8a5a34"; rr(x - 17, y - 39.5, 34, 38, 9); g.fill()
    g.save(); rr(x - 17, y - 39.5, 34, 38, 9); g.clip()
    g.fillStyle = "#6b4326"; g.fillRect(x + 5, y - 40, 14, 40); g.fillStyle = "#b57a45"; g.fillRect(x - 13, y - 36, 4, 30)
    for by in (y - 32, y - 11):
        g.fillStyle = "#2f2f3a"; g.fillRect(x - 18, by, 36, 5); g.fillStyle = "#5b5b6c"; g.fillRect(x - 18, by, 36, 1.5)
    g.fillStyle = "rgba(0,0,0,.25)"; g.fillRect(x - 2, y - 40, 1.5, 40); g.restore()


_atmos = {}


def atmos(top, side):
    """The ceiling shade and vignette never move, so they're rendered once per size."""
    global g
    key = (top, side, RS)
    img = _atmos.get(key)
    if img is None:
        surf, cv = offscreen(VW * RS, VH * RS, RS)
        saved, g = g, cv
        try:
            _atmos_draw(top, side)
        finally:
            g = saved
        surf.flush()
        _atmos.clear()
        _atmos[key] = img = surf
    g.drawImageAt(img, 0, 0)


def _atmos_draw(top, side):
    gr = g.createLinearGradient(0, 64, 0, 150)
    gr.addColorStop(0, f"rgba(0,0,0,{top})"); gr.addColorStop(1, "rgba(0,0,0,0)")
    g.fillStyle = gr; g.fillRect(0, 64, VW, 86)
    vg = g.createRadialGradient(VW / 2, 190, 110, VW / 2, 190, 330)
    vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, f"rgba(0,0,0,{side})")
    g.fillStyle = vg; g.fillRect(0, 0, VW, VH)


def bg_cellar():
    tick = S.tick
    s = g.createLinearGradient(0, 0, 0, VH); s.addColorStop(0, "#1a1530"); s.addColorStop(1, "#2d2447")
    g.fillStyle = s; g.fillRect(0, 0, VW, VH)
    brick_wall(.4, "rgba(255,255,255,.05)")
    g.fillStyle = "rgba(0,0,0,.28)"; g.fillRect(0, 292, VW, 28); g.fillStyle = "rgba(255,255,255,.07)"; g.fillRect(0, 292, VW, 1.5)
    atmos(.4, .5)
    tile_x(600, .6, lambda ox: lantern(ox + 280, 146))

    def barrels(sx, wx):
        t1, t2 = math.floor((wx + 120 - 18) / T), math.floor((wx + 120 + 18) / T)
        if gsolid(t1, 10) and gsolid(t2, 10) and not gsolid(t1, 9) and not gsolid(t2, 9):
            barrel(sx + 120, 320)
    wdeco(704, barrels)
    for i in range(14):
        x = ((i * 97 + tick * (.08 + (i % 3) * .05) - round(S.cam) * (.25 + (i % 4) * .1)) % VW + VW) % VW
        y = 90 + ((i * 53) % 210) + sin(tick * .03 + i) * 10
        g.globalAlpha = .3 + .3 * sin(tick * .05 + i * 2); g.fillStyle = "#ffe9a0"
        g.beginPath(); g.arc(x, y, 1.5 + (i % 2), 0, 7); g.fill()
    g.globalAlpha = 1


def arc_window(cx):
    top, r, by = 90, 24, 200

    def path(q):
        g.beginPath(); g.moveTo(cx - q, by); g.lineTo(cx - q, top + r); g.arc(cx, top + r, q, PI, 0); g.lineTo(cx + q, by); g.closePath()

    path(r + 5); g.fillStyle = OL; g.fill()
    path(r + 3); g.fillStyle = "#8a685d"; g.fill()
    g.save(); path(r + 3); g.clip(); g.fillStyle = "#5b423b"; g.fillRect(cx + 6, top - 4, 30, 140)
    g.fillStyle = "#b58f82"; g.fillRect(cx - r - 4, top - 4, 3, 140); g.restore()
    g.save(); path(r); g.clip()
    sk = g.createLinearGradient(0, top, 0, by); sk.addColorStop(0, "#141c45"); sk.addColorStop(1, "#42418a")
    g.fillStyle = sk; g.fillRect(cx - r, top, r * 2, by - top)
    for i, p in enumerate([[-9, 20], [7, 12], [11, 42], [-13, 58], [2, 74]]):
        g.globalAlpha = .55 + .4 * sin(S.tick * .05 + i * 1.7); g.fillStyle = "#fff"; g.fillRect(cx + p[0], top + p[1], 2, 2)
    g.globalAlpha = 1
    g.fillStyle = "#fff6d0"; g.beginPath(); g.arc(cx + 8, top + 30, 7, 0, 7); g.fill()
    g.fillStyle = "#e6dcae"; g.beginPath(); g.arc(cx + 10.5, top + 28, 5.5, 0, 7); g.fill()
    g.restore()
    g.strokeStyle = OL; g.lineWidth = 3; g.beginPath(); g.moveTo(cx, top); g.lineTo(cx, by)
    g.moveTo(cx - r, top + r + 18); g.lineTo(cx + r, top + r + 18); g.stroke()
    g.fillStyle = OL; g.fillRect(cx - r - 9, by, 2 * (r + 9), 9); g.fillStyle = "#a07f73"; g.fillRect(cx - r - 7, by + 1.5, 2 * (r + 7), 6)
    g.fillStyle = "#c9a99b"; g.fillRect(cx - r - 7, by + 1.5, 2 * (r + 7), 2)


def stone_column(x):
    g.fillStyle = OL; g.fillRect(x - 15, 64, 30, 260)
    g.fillStyle = "#7d5d53"; g.fillRect(x - 13, 64, 26, 260)
    g.fillStyle = "#5b423b"; g.fillRect(x + 3, 64, 10, 260)
    g.fillStyle = "#a07f73"; g.fillRect(x - 13, 64, 4, 260)
    g.fillStyle = "rgba(0,0,0,.25)"
    for y in range(104, 320, 40):
        g.fillRect(x - 13, y, 26, 1.5)
    g.fillStyle = OL; g.fillRect(x - 19, 64, 38, 15); g.fillStyle = "#8f6d62"; g.fillRect(x - 17, 65.5, 34, 11.5)
    g.fillStyle = "#5b423b"; g.fillRect(x + 4, 65.5, 13, 11.5); g.fillStyle = "#b58f82"; g.fillRect(x - 17, 65.5, 34, 2.5)


def grand_oven(x):
    y, r, tick = 150, 58, S.tick
    glow(x, y, r * .6, r * 2.6, "255,130,50", .30)
    g.fillStyle = OL; g.beginPath(); g.arc(x, y, r + 13, 0, 7); g.fill()
    g.fillStyle = "#8a685d"; g.beginPath(); g.arc(x, y, r + 10.5, 0, 7); g.fill()
    g.save(); g.beginPath(); g.arc(x, y, r + 10.5, 0, 7); g.clip(); g.fillStyle = "#5b423b"; g.fillRect(x + 8, y - r - 12, r + 16, 2 * r + 24); g.restore()
    g.strokeStyle = "#b58f82"; g.lineWidth = 3; g.beginPath(); g.arc(x, y, r + 8, PI * 1.05, PI * 1.65); g.stroke()
    g.strokeStyle = "rgba(0,0,0,.3)"; g.lineWidth = 1.5
    for i in range(16):
        an = i * PI / 8
        g.beginPath(); g.moveTo(x + cos(an) * (r + 2), y + sin(an) * (r + 2)); g.lineTo(x + cos(an) * (r + 10), y + sin(an) * (r + 10)); g.stroke()
    g.fillStyle = OL; g.beginPath(); g.arc(x, y, r + 2, 0, 7); g.fill()
    gr = g.createRadialGradient(x, y + r * .5, 4, x, y, r)
    gr.addColorStop(0, "#ffd76a"); gr.addColorStop(.55, "#ff8a2a"); gr.addColorStop(1, "#7a1a10")
    g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill()
    g.save(); g.beginPath(); g.arc(x, y, r, 0, 7); g.clip()
    for ps in range(2):
        for k in range(5):
            bx = x - r * .72 + k * r * .36
            h = (26 if ps else 38) + sin(tick * .2 + k * 1.7) * 9
            sw = sin(tick * .13 + k * 2.3) * 4
            w = 7 if ps else 10
            by = y + r
            g.fillStyle = "#ffe27a" if ps else "#ff7a1f"
            g.beginPath(); g.moveTo(bx - w, by); g.quadraticCurveTo(bx - w * .6, by - h * .6, bx + sw, by - h)
            g.quadraticCurveTo(bx + w * .6, by - h * .6, bx + w, by); g.closePath(); g.fill()
    g.restore()
    g.strokeStyle = OL; g.lineWidth = 3; g.beginPath(); g.moveTo(x - r, y); g.lineTo(x + r, y)
    g.moveTo(x - r * .28, y - r); g.lineTo(x - r * .28, y + r); g.moveTo(x + r * .28, y - r); g.lineTo(x + r * .28, y + r); g.stroke()


def chimney(x):
    w = 92
    g.fillStyle = OL; g.fillRect(x - w - 2, 64, 2 * w + 4, 166)
    g.fillStyle = "#6b4f47"; g.fillRect(x - w, 64, 2 * w, 166)
    g.fillStyle = "#4f3832"; g.fillRect(x + w * .35, 64, w * .65, 166)
    g.fillStyle = "#8f6d62"; g.fillRect(x - w, 64, 4, 166)
    g.fillStyle = "rgba(0,0,0,.22)"
    for r in range(7):
        y = 64 + r * 24
        g.fillRect(x - w, y, 2 * w, 1.5)
        for k in range(-3, 4):
            jx = x + k * 46 + (23 if r % 2 else 0)
            if x - w + 2 < jx < x + w - 2:
                g.fillRect(jx, y, 1.5, 24)


def bg_kitchen():
    tick = S.tick
    s = g.createLinearGradient(0, 0, 0, VH); s.addColorStop(0, "#2a0f12"); s.addColorStop(1, "#4a1a14")
    g.fillStyle = s; g.fillRect(0, 0, VW, VH)
    brick_wall(.4, "rgba(255,255,255,.035)")
    tile_x(256, .4, lambda ox: (arc_window(ox + 128), stone_column(ox)))
    rc = round(S.cam)
    off = -((rc * .4) % 20)
    sc = math.floor((rc * .4) / 20)
    ox = S.KX * T - rc
    if -200 < ox < VW + 200:
        chimney(ox)
    g.fillStyle = OL; g.fillRect(0, 226, VW, 12); g.fillStyle = "#8f6d62"; g.fillRect(0, 228, VW, 8)
    g.fillStyle = "#b58f82"; g.fillRect(0, 228, VW, 2); g.fillStyle = "#5b423b"; g.fillRect(0, 233, VW, 3)
    g.fillStyle = "#4a1814"; g.fillRect(0, 238, VW, 82)
    checks, shine, lines = [], [], []
    for r in range(4):
        x, c = off - 20, 0
        while x < VW + 20:
            if (r + sc + c) % 2 == 0:
                checks.append((x, 238 + r * 20, 20, 20))
            shine.append((x, 238 + r * 20, 20, 2))
            x += 20
            c += 1
    for r in range(5):
        lines.append((0, 238 + r * 20, VW, 1.5))
    x = off - 20
    while x < VW + 20:
        lines.append((x, 238, 1.5, 80))
        x += 20
    g.fillStyle = "#5f211b"; g.fillRects(checks)
    g.fillStyle = "rgba(255,170,120,.10)"; g.fillRects(shine)
    g.fillStyle = "rgba(0,0,0,.35)"; g.fillRects(lines)
    atmos(.35, .4)
    if -160 < ox < VW + 160:
        grand_oven(ox)
    for i in range(18):
        life = (tick * (.5 + (i % 5) * .15) + i * 61) % 320
        y = VH - life
        x = ((i * 97 + sin(life * .05 + i) * 14 - rc * (.3 + (i % 4) * .08)) % VW + VW) % VW
        g.globalAlpha = (1 - life / 320) * .85; g.fillStyle = "#ffb347" if i % 3 else "#ff6a1f"
        g.fillRect(x, y, 2 + (i % 3), 2 + (i % 3))
    g.globalAlpha = 1
    gl = g.createLinearGradient(0, 220, 0, VH)
    gl.addColorStop(0, "rgba(255,90,30,0)"); gl.addColorStop(1, f"rgba(255,90,30,{.28 + sin(tick * .08) * .05})")
    g.fillStyle = gl; g.fillRect(0, 220, VW, VH - 220)


def background():
    if S.TH == 0:
        bg_lawn()
    elif S.TH == 1:
        bg_cellar()
    else:
        bg_kitchen()


# ======================================================================= tiles
def blk(px, py, base, hi, lo, r):
    rr(px + 1, py + 1, T - 2, T - 2, r); g.fillStyle = base; g.fill()
    g.save(); rr(px + 1, py + 1, T - 2, T - 2, r); g.clip()
    g.fillStyle = lo; g.fillRect(px, py + T - 9, T, 9); g.fillRect(px + T - 7, py, 7, T)
    g.fillStyle = hi; g.fillRect(px, py, T, 5); g.fillRect(px, py, 4, T - 9)
    g.restore()
    rr(px + 1, py + 1, T - 2, T - 2, r); g.strokeStyle = OL; g.lineWidth = 2; g.stroke()


def draw_ground(v, px, py, tx, ty):
    h = hsh(tx, ty)
    up, dn, lf, rt = gsolid(tx, ty - 1), gsolid(tx, ty + 1), gsolid(tx - 1, ty), gsolid(tx + 1, ty)
    if v == 6:
        c = ["#4a2f2c", "#2c1a18", "#1a0f0e"] if S.TH == 2 else ["#3a4368", "#252c4a", "#161b30"]
    elif S.TH == 0:
        c = ["#a8683a", "#84502c", "#5a3a1c"]
    else:
        c = ["#6a4f4a", "#463430", "#33231f"] if S.TH == 2 else ["#56678d", "#3a4870", "#2a3557"]
    g.fillStyle = c[0]; g.fillRect(px, py, T, T)
    if S.TH == 0 and v == 1:
        if ty > 10:
            g.fillStyle = "rgba(60,30,10,.28)"; g.fillRect(px, py, T, T)
        g.fillStyle = "#c9a27a"; g.strokeStyle = "#5a3a1c"; g.lineWidth = 1
        for p in [[7 + h % 10, 19 + (h >> 3) % 8, 3, 2.2], [20 + (h >> 5) % 7, 24 + (h >> 7) % 5, 2.2, 1.6]]:
            g.beginPath(); g.ellipse(px + p[0], py + p[1], p[2], p[3], 0, 0, 7); g.fill(); g.stroke()
        if not up:
            g.fillStyle = "#4fae45"; g.fillRect(px, py, T, 11)
            g.fillStyle = "#8be07a"; g.fillRect(px, py + 2, T, 2)
            g.fillStyle = "#3a8f36"; g.fillRect(px, py + 8, T, 3)
            for i in range(4):
                x = px + i * 8
                g.beginPath(); g.moveTo(x, py + 10); g.lineTo(x + 8, py + 10); g.lineTo(x + 4, py + 16); g.closePath(); g.fill()
    else:
        g.fillStyle = c[1]
        g.fillRect(px, py + 15, T, 2)
        g.fillRect(px + (8 if ty % 2 else 0), py + 2, 2, 13); g.fillRect(px + (24 if ty % 2 else 16), py + 2, 2, 13)
        g.fillRect(px + (0 if ty % 2 else 8), py + 17, 2, T - 17); g.fillRect(px + (16 if ty % 2 else 24), py + 17, 2, T - 17)
        if v == 1 and not up:
            g.fillStyle = "rgba(255,255,255,.2)"; g.fillRect(px, py + 2, T, 3)
    g.fillStyle = OL
    if not up:
        g.fillRect(px, py, T, 2)
    if not lf:
        g.fillRect(px, py, 2, T)
    if not rt:
        g.fillRect(px + T - 2, py, 2, T)
    if not dn and ty < H - 1:
        g.fillRect(px, py + T - 2, T, 2)


def draw_tile(v, px, py, tx, ty):
    if v in (1, 6):
        draw_ground(v, px, py, tx, ty)
        return
    h = hsh(tx, ty)
    if v == 2:
        blk(px, py, "#e6a95a", "#f7cd85", "#b8742e", 8)
        g.lineCap = "round"
        for i in range(3):
            x = px + 8 + i * 8
            g.strokeStyle = "#a5651f"; g.lineWidth = 3.2; g.beginPath(); g.moveTo(x - 2, py + 21); g.lineTo(x + 3, py + 10); g.stroke()
            g.strokeStyle = "#fbdca0"; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x - 3.2, py + 21); g.lineTo(x + 1.8, py + 10); g.stroke()
        g.lineCap = "butt"; g.fillStyle = "#fff3c9"
        for a in [[6, 7], [25, 9], [24, 24]]:
            g.beginPath(); g.ellipse(px + a[0], py + a[1], 1.5, .9, .6, 0, 7); g.fill()
    elif v in (3, 4):
        on = v == 3
        blk(px, py, "#f8d34d" if on else "#aa9d74", "#ffe98a" if on else "#c6ba91", "#d9a520" if on else "#7f7350", 6)
        for a in [[7, 8], [25, 25], [8, 25]]:
            g.beginPath(); g.ellipse(px + a[0], py + a[1], 3, 2.6, 0, 0, 7); g.fillStyle = "#b8860b" if on else "#5f5538"; g.fill()
            g.beginPath(); g.ellipse(px + a[0] + .6, py + a[1] + .6, 2, 1.6, 0, 0, 7); g.fillStyle = "#e8b92a" if on else "#8a7d58"; g.fill()
        if on:
            g.font = "bold 20px Arial"; g.textAlign = "center"; g.textBaseline = "middle"
            g.fillStyle = "#fff3b0"; g.fillText("?", px + 15, py + 16); g.fillStyle = "#9a6408"; g.fillText("?", px + 16, py + 17)
    elif v == 5:
        blk(px, py, "#4f8794", "#86b9c4", "#2f5560", 3)
        g.strokeStyle = "#2f5560"; g.lineWidth = 1.3; g.beginPath(); g.moveTo(px + 8 + h % 8, py + 5)
        g.lineTo(px + 12 + h % 8, py + 13); g.lineTo(px + 9 + h % 8, py + 20); g.stroke()
        g.fillStyle = OL
        for a in [[5, 5], [T - 6, 5], [5, T - 6], [T - 6, T - 6]]:
            g.beginPath(); g.arc(px + a[0], py + a[1], 1.3, 0, 7); g.fill()


_tiles = {}
_tiles_rs = None


def tile_img(v, tx, ty):
    """Tiles never change once drawn, so each one is rendered once and reused."""
    global g, _tiles_rs
    if _tiles_rs != RS or len(_tiles) > 3000:
        _tiles.clear()
        _tiles_rs = RS
    key = (v, S.TH, tx, ty, gsolid(tx, ty - 1), gsolid(tx, ty + 1), gsolid(tx - 1, ty), gsolid(tx + 1, ty))
    img = _tiles.get(key)
    if img is None:
        surf, cv = offscreen(T * RS + 2, T * RS + 2, RS)
        saved, g = g, cv
        try:
            draw_tile(v, 0, 0, tx, ty)
        finally:
            g = saved
        surf.flush()
        _tiles[key] = img = surf
    return img


def soup():
    g.fillStyle = "#e8552b"; g.fillRect(round(S.cam) - 2, 10 * T + 8, VW + 4, 2 * T)
    g.fillStyle = "#ffb347"
    for i in range(10):
        x = S.cam + ((i * 61 + S.tick * .6) % VW)
        y = 10 * T + 10 + sin(S.tick * .1 + i) * 3
        g.beginPath(); g.arc(x, y, 4 + (i % 3), 0, 7); g.fill()


# ======================================================================= enemies
def draw_ant(e):
    if e.vx:
        e.f = 1 if e.vx > 0 else -1
    d = e.f or 1
    tick = S.tick
    c1, ph, aw = "#6b2f1a", tick * .4 + e.x * .05, sin(tick * .2 + e.x) * 1.5
    g.save(); g.translate(e.x + 13, e.y + e.h); g.scale(d, .45 if e.dead else 1)
    limb([[10, -15], [13 + aw, -21], [17 + aw, -22]], "#3a1c10", 1.2)
    limb([[8, -16], [9 + aw, -22], [12 + aw, -25]], "#3a1c10", 1.2)
    if not e.dead:
        for i, hx in enumerate([-5, 1, 7]):
            sw = sin(ph + i * 2.1) * 3
            limb([[hx, -7], [hx + (i - 1) * 2.5 + sw * .5, -3], [hx + (i - 1) * 4 + sw, 0]], "#4a2214", 1.6)
    cel(-9, -10, 7.5, 6.2, c1, "#43200f", "#a5603c")
    cel(0, -10.5, 5, 4.6, c1, "#43200f", "#a5603c")
    cel(9, -12, 5.4, 5.2, "#7b3a20", "#4e2612", "#b8724a")
    g.fillStyle = OL; g.beginPath(); g.ellipse(11, -13.5, 3.4, 3.8, 0, 0, 7); g.fill()
    g.fillStyle = "#fff"; g.beginPath(); g.ellipse(11, -13.5, 2.4, 2.8, 0, 0, 7); g.fill()
    g.fillStyle = OL; g.beginPath(); g.arc(11.9, -13.2, 1.3, 0, 7); g.fill()
    limb([[8, -18], [13.5, -16]], OL, 1.4)
    limb([[13, -9.5], [16.5, -8], [15.5, -5.5]], "#f2d6a8", 1.3)
    limb([[12, -8], [15, -5.5], [13.5, -4]], "#f2d6a8", 1.3)
    g.restore()


def walnut_path(cx, cy, rx, ry):
    g.beginPath()
    for i in range(73):
        a = i / 72 * PI * 2
        k = 1 + .05 * cos(5 * a + 1) + .026 * cos(9 * a + .3)
        x, y = cx + cos(a) * rx * k, cy + sin(a) * ry * k
        if i:
            g.lineTo(x, y)
        else:
            g.moveTo(x, y)
    g.closePath()


WRINK = [[-.5, -.62, .5, .3], [.42, -.6, .45, -.4], [-.68, -.12, .4, .5], [.62, -.05, .42, -.3], [-.46, .42, .44, -.2],
         [.4, .5, .4, .45], [-.12, -.34, .34, .2], [.2, .15, .36, -.5], [-.22, .72, .3, .1], [.14, -.82, .3, -.1],
         [-.78, .42, .28, .2], [.76, .36, .28, -.2]]


def walnut_body(rx, ry, sb, ss, sh, rim=False):
    walnut_path(0, 0, rx, ry); g.fillStyle = sb; g.fill()
    g.save(); walnut_path(0, 0, rx, ry); g.clip()
    g.fillStyle = ss; g.beginPath(); g.rect(-rx - 3, -ry - 3, rx * 2 + 6, ry * 2 + 6)
    g.ellipse(-rx * .2, -ry * .18, rx, ry, 0, 0, 7); g.fill("evenodd")
    g.lineCap = "round"; g.strokeStyle = "rgba(58,30,10,.72)"; g.lineWidth = .75
    for w in WRINK:
        x, y, l, an = w[0] * rx, w[1] * ry, w[2] * rx, w[3]
        dx, dy = cos(an) * l * .5, sin(an) * l * .5
        g.beginPath(); g.moveTo(x - dx, y - dy); g.quadraticCurveTo(x + dy * .9, y - dx * .9, x + dx, y + dy); g.stroke()
    g.fillStyle = "rgba(58,30,10,.55)"
    for p in [[-.3, .3], [.5, -.3], [-.55, -.4], [.05, .55], [.3, -.7]]:
        g.beginPath(); g.arc(p[0] * rx, p[1] * ry, .7, 0, 7); g.fill()
    g.strokeStyle = "#4a2a10"; g.lineWidth = 1.35; g.beginPath(); g.moveTo(-.04 * rx, -ry * 1.05)
    g.bezierCurveTo(-rx * .3, -ry * .35, rx * .26, ry * .3, rx * .02, ry * 1.05); g.stroke()
    g.strokeStyle = sh; g.lineWidth = .75; g.beginPath(); g.moveTo(-.04 * rx - 1.3, -ry * .92)
    g.bezierCurveTo(-rx * .3 - 1.3, -ry * .35, rx * .26 - 1.3, ry * .3, rx * .02 - 1.3, ry * .9); g.stroke()
    if rim:
        g.strokeStyle = "#efd9a8"; g.lineWidth = 2.3; g.lineCap = "round"; g.beginPath(); g.ellipse(0, 0, rx * .94, ry * .94, 0, -1.2, 1.2); g.stroke()
        g.strokeStyle = "rgba(58,30,10,.8)"; g.lineWidth = .65; g.beginPath(); g.ellipse(0, 0, rx * .8, ry * .8, 0, -1.2, 1.2); g.stroke()
    g.restore()
    g.fillStyle = sh; g.beginPath(); g.ellipse(-rx * .52, -ry * .55, rx * .2, ry * .12, -.65, 0, 7); g.fill()
    walnut_path(0, 0, rx, ry); g.strokeStyle = OL; g.lineWidth = .95; g.lineJoin = "round"; g.stroke()


def band_tail(p0, p1, p2, w):
    g.lineCap = "round"; g.beginPath(); g.moveTo(*p0); g.quadraticCurveTo(p1[0], p1[1], p2[0], p2[1])
    g.strokeStyle = OL; g.lineWidth = w + 1.8; g.stroke(); g.strokeStyle = "#d9382c"; g.lineWidth = w; g.stroke(); g.lineCap = "butt"


def boot(x, y, c, hi):
    def p():
        g.beginPath(); g.moveTo(x, y - 5.2); g.lineTo(x + 5, y - 5.2); g.bezierCurveTo(x + 7.6, y - 4.8, x + 10.4, y - 3.8, x + 10.4, y - 1.8)
        g.bezierCurveTo(x + 10.4, y - .4, x + 9.4, y, x + 8, y); g.lineTo(x + .6, y); g.bezierCurveTo(x - .8, y, x - 1, y - 1.4, x - .6, y - 2.6); g.closePath()
    p(); g.fillStyle = c; g.fill()
    g.save(); g.clip(); g.fillStyle = "#3f2210"; g.fillRect(x - 2, y - 1.5, 16, 3); g.fillStyle = hi
    g.beginPath(); g.ellipse(x + 7.4, y - 3.6, 3, 1.3, -.25, 0, 7); g.fill(); g.restore()
    g.strokeStyle = OL; g.lineWidth = .95; g.lineJoin = "round"; p(); g.stroke()


def stand_nut(e, sb, ss, sh):
    tick = S.tick
    dn = e.dn > 0
    u = min(1, max(0, e.du)) if dn else 0
    dph = u * PI * 4
    ph = tick * .28 + e.x * .1
    sw = sin(dph) if dn else sin(ph)
    bob = 0 if dn else abs(sw) * .9
    fl = sin(tick * (.95 if dn else .45) + e.x * .05)
    g.translate(0, -bob); g.lineJoin = "round"
    l1 = max(0, sw) * (3.2 if dn else 2.2)
    l2 = max(0, -sw) * (3.2 if dn else 2.2)
    s1, s2 = sw * 2.2, -sw * 2.2
    skin, skinD = "#e6c48b", "#c9a366"

    def leg(x0, x1, y1):
        g.lineCap = "round"; g.strokeStyle = OL; g.lineWidth = 4.4; g.beginPath(); g.moveTo(x0, -8); g.lineTo(x1, y1); g.stroke()
        g.strokeStyle = skinD; g.lineWidth = 2.6; g.stroke(); g.lineCap = "butt"

    bx1, by1, bx2, by2 = -3 + s1 * .4, -l1, 4.2 + s2 * .4, -l2
    if l1 > .3:
        leg(-1.6, bx1 + 2.6, by1 - 4.6)
    boot(bx1, by1, "#5c3418", "#8a552b")
    g.save(); g.translate(-6.2, -16); g.rotate(-.2 + sw * (.08 if dn else .02)); walnut_body(9.8, 11.2, sb, ss, sh, True); g.restore()
    if l2 > .3:
        leg(3.6, bx2 + 2.8, by2 - 4.6)
    boot(bx2, by2, "#6f3f1d", "#a06a37")

    def body_p():
        g.beginPath(); g.moveTo(-3.2, -19); g.bezierCurveTo(-7.4, -14.4, -6.8, -6.4, -2.6, -4.2)
        g.bezierCurveTo(.4, -2.8, 5.6, -3, 7.4, -5.2); g.bezierCurveTo(10, -8.6, 9.2, -15, 6.4, -19); g.closePath()
    body_p(); g.fillStyle = skin; g.fill()
    g.save(); body_p(); g.clip(); g.fillStyle = "#cfa96c"; g.beginPath(); g.rect(-10, -22, 24, 22)
    g.ellipse(-.4, -12.6, 9, 9, 0, 0, 7); g.fill("evenodd"); g.restore()
    body_p(); g.strokeStyle = OL; g.lineWidth = .95; g.stroke()

    def belly():
        g.beginPath(); g.moveTo(-.8, -17.4); g.bezierCurveTo(-4.4, -13.6, -3.6, -7.6, .4, -6)
        g.bezierCurveTo(3.4, -5, 6.6, -6.4, 7.4, -9); g.bezierCurveTo(8.4, -12.4, 6.6, -16, 3.8, -17.6); g.closePath()
    belly(); g.fillStyle = "#f6e4ba"; g.fill()
    g.save(); belly(); g.clip(); g.strokeStyle = "#c9a262"; g.lineWidth = .7
    for y in (-14.6, -12.2, -9.8, -7.4):
        g.beginPath(); g.moveTo(-5, y); g.quadraticCurveTo(2.4, y + 1.5, 10, y); g.stroke()
    g.fillStyle = "#e5cf9f"; g.beginPath(); g.rect(-8, -20, 20, 20); g.ellipse(1.2, -12.6, 6.2, 6.2, 0, 0, 7); g.fill("evenodd"); g.restore()
    belly(); g.strokeStyle = "#b58a52"; g.lineWidth = .75; g.stroke()
    pump = abs(sin(dph + PI / 2)) * 3.4 if dn else 0
    fy = -10.6 - (pump if dn else -sw * .7)
    g.lineCap = "round"; g.strokeStyle = OL; g.lineWidth = 4.2; g.beginPath(); g.moveTo(5, -16); g.quadraticCurveTo(10.8, -13.6, 8, fy); g.stroke()
    g.strokeStyle = skin; g.lineWidth = 2.4; g.stroke(); g.lineCap = "butt"
    ell(8.1, fy, 2.9, 2.7, "#f0d29c")
    g.fillStyle = "#f0d29c"; g.strokeStyle = OL; g.lineWidth = .8; g.beginPath(); g.ellipse(8.6, fy - 2.6, 1, 1.4, .2, 0, 7); g.fill(); g.stroke()
    hx, hy = -2.4, 1.6

    def head_p():
        g.beginPath(); g.moveTo(-1 + hx, -21.6 + hy)
        g.bezierCurveTo(-1.4 + hx, -27.4 + hy, 4.4 + hx, -30 + hy, 9.6 + hx, -28 + hy)
        g.bezierCurveTo(13 + hx, -26.6 + hy, 13.8 + hx, -24.4 + hy, 15.2 + hx, -22.8 + hy)
        g.bezierCurveTo(17.2 + hx, -21.4 + hy, 17.6 + hx, -18.8 + hy, 15.8 + hx, -17.4 + hy)
        g.bezierCurveTo(14.6 + hx, -16.4 + hy, 12.6 + hx, -16.4 + hy, 11.4 + hx, -15.6 + hy)
        g.bezierCurveTo(8.6 + hx, -13.8 + hy, 2.6 + hx, -14.4 + hy, -.2 + hx, -17.6 + hy)
        g.bezierCurveTo(-1.4 + hx, -19 + hy, -1.2 + hx, -20.4 + hy, -1 + hx, -21.6 + hy); g.closePath()
    head_p(); g.fillStyle = "#f1d3a0"; g.fill()
    g.save(); head_p(); g.clip(); g.fillStyle = "#d6ae76"; g.beginPath(); g.rect(-8, -36, 32, 32)
    g.ellipse(4.2 + hx, -23.6 + hy, 10.6, 7.4, 0, 0, 7); g.fill("evenodd"); g.restore()
    head_p(); g.strokeStyle = OL; g.lineWidth = .95; g.stroke()
    g.fillStyle = OL; g.beginPath(); g.arc(14.6 + hx, -20.6 + hy, .65, 0, 7); g.fill()
    g.strokeStyle = OL; g.lineWidth = .85; g.lineCap = "round"
    if dn:
        g.beginPath(); g.moveTo(11 + hx, -18.6 + hy); g.quadraticCurveTo(13.4 + hx, -19 + hy, 15.6 + hx, -18.4 + hy)
        g.quadraticCurveTo(14.8 + hx, -15.6 + hy, 13.2 + hx, -15.6 + hy); g.quadraticCurveTo(11.6 + hx, -15.6 + hy, 11 + hx, -18.6 + hy)
        g.fillStyle = "#7a2a1c"; g.fill(); g.lineWidth = .7; g.stroke()
    else:
        g.beginPath(); g.moveTo(10.6 + hx, -17.6 + hy); g.quadraticCurveTo(13.2 + hx, -16.6 + hy, 15.2 + hx, -18 + hy); g.stroke()
    for q in [[5.7 + hx, -22.2 + hy, 2.7, 3.1, 6.8 + hx, -22.1 + hy, 1.4, 1.8], [11.3 + hx, -22 + hy, 2.1, 2.6, 12.1 + hx, -21.9 + hy, 1.05, 1.45]]:
        if dn:
            g.strokeStyle = OL; g.lineWidth = 1; g.lineCap = "round"; g.beginPath(); g.moveTo(q[0] - q[2] * .85, q[1] + 2)
            g.quadraticCurveTo(q[0], q[1] - 2.4, q[0] + q[2] * .85, q[1] + 2); g.stroke()
            continue
        g.beginPath(); g.ellipse(q[0], q[1], q[2], q[3], 0, 0, 7); g.fillStyle = "#fff"; g.fill(); g.strokeStyle = OL; g.lineWidth = .85; g.stroke()
        g.fillStyle = OL; g.beginPath(); g.ellipse(q[4], q[5], q[6], q[7], 0, 0, 7); g.fill()
        g.fillStyle = "#fff"; g.beginPath(); g.arc(q[4] - .45, q[5] - .65, .5, 0, 7); g.fill()
    if dn:
        g.fillStyle = "rgba(255,120,140,.65)"; g.beginPath(); g.ellipse(7.4 + hx, -18.8 + hy, 1.6, 1, 0, 0, 7); g.fill()
    kx, ky = -.6 + hx, -26 + hy
    band_tail([kx, ky], [kx - 3.4, ky + .6 + fl * .8], [kx - 7.4, ky + 2.6 + fl * 1.3], 1.7)
    band_tail([kx, ky], [kx - 3, ky + 1.9], [kx - 6.6, ky + 4.6 - fl * 1.2], 1.7)
    g.lineCap = "round"; g.beginPath(); g.moveTo(kx, ky); g.quadraticCurveTo(6.4 + hx, -29.4 + hy, 12.4 + hx, -26.8 + hy)
    g.strokeStyle = OL; g.lineWidth = 3.7; g.stroke(); g.strokeStyle = "#d9382c"; g.lineWidth = 1.9; g.stroke()
    g.strokeStyle = "#ff8b7a"; g.lineWidth = .55; g.beginPath(); g.moveTo(2.6 + hx, -27.6 + hy)
    g.quadraticCurveTo(6.6 + hx, -29 + hy, 9.8 + hx, -27.8 + hy); g.stroke(); g.lineCap = "butt"
    ell(kx, ky, 1.6, 1.6, "#c22c22")


def draw_nut(e):
    if e.vx:
        e.f = 1 if e.vx > 0 else -1
    tick = S.tick
    d = e.f or 1
    shell = e.mode != "walk"
    slide = e.mode == "slide"
    wake = e.mode == "shell" and e.st > 400
    flash = wake and (tick >> 2) % 2
    sb = "#e6b57c" if flash else "#a86f35"
    ss = "#c48a52" if flash else "#6b421b"
    sh = "#f9dcb0" if flash else "#dcac6a"
    g.save(); g.translate(e.x + 13, e.y + e.h); g.scale(d, .45 if e.dead else 1)
    if not shell:
        if e.dn > 0:
            u = min(1, max(0, e.du))
            h = abs(sin(u * PI * 4))
            k = max(0, 1 - h * 5)
            hop = h * 3.6
            sys_ = 1 + (h - .5) * .05 - k * .14
            sxs = 1 + k * .09
            rot = sin(u * PI * 2) * .07
            if u > .75:
                th = (u - .75) / .25 * PI * 2
                c = cos(th)
                if abs(c) < .14:
                    c = -.14 if c < 0 else .14
                sxs = c
            g.translate(0, -hop); g.rotate(rot); g.scale(sxs, sys_)
        stand_nut(e, sb, ss, sh)
        if e.dn > 0:
            u = min(1, max(0, e.du))
            if .05 < u < .97:
                for k in range(2):
                    t = (u * 2.6 + k * .5) % 1
                    x = 1 + k * 9 + sin(t * 6 + k) * 2
                    y = -30 - t * 15
                    g.globalAlpha = min(1, (1 - t) * 1.6); g.fillStyle = "#fff6c8"; g.strokeStyle = OL; g.lineWidth = .7
                    g.beginPath(); g.ellipse(x, y, 1.7, 1.25, -.4, 0, 7); g.fill(); g.stroke()
                    g.lineCap = "round"; g.beginPath(); g.moveTo(x + 1.5, y - .3); g.lineTo(x + 1.5, y - 5.4)
                    g.quadraticCurveTo(x + 3.5, y - 4.4, x + 3.3, y - 2.6); g.stroke(); g.lineCap = "butt"
                    g.globalAlpha = 1
        g.restore()
        return
    cy, rx, ry = -12.2, 12.6, 12.2
    g.save(); g.translate(sin(tick * 1.7) * 1.1 if wake else 0, cy)
    if slide:
        g.rotate(e.x * .085 * d)
    walnut_body(rx, ry, sb, ss, sh)
    g.restore()
    if not slide:
        g.save(); g.translate(sin(tick * 1.7) * 1.1 if wake else 0, 0)
        g.beginPath(); g.ellipse(2.2, -5.6, 7.6, 3.1, 0, 0, 7); g.fillStyle = OL; g.fill()
        g.fillStyle = "#3a1c0c"; g.beginPath(); g.ellipse(2.2, -5.6, 6.6, 2.3, 0, 0, 7); g.fill()
        er = 2.2 if wake else 1.8
        for x in (-1.4, 5.4):
            g.fillStyle = "#fff"; g.beginPath(); g.ellipse(x, -5.6, 1.9, er, 0, 0, 7); g.fill()
            g.fillStyle = OL; g.beginPath(); g.ellipse(x + .7, -5.5, .95, er * .72, 0, 0, 7); g.fill()
        g.strokeStyle = OL; g.lineWidth = .9; g.lineCap = "round"; g.beginPath(); g.moveTo(-3.6, -8.4); g.lineTo(.4, -7.4)
        g.moveTo(8.4, -8.4); g.lineTo(4.4, -7.4); g.stroke(); g.lineCap = "butt"
        g.restore()
    else:
        g.strokeStyle = "rgba(255,255,255,.75)"; g.lineWidth = 1.5; g.lineCap = "round"
        for i in range(3):
            g.beginPath(); g.moveTo(-17 - i * 3, -6 - i * 5); g.lineTo(-23 - i * 3, -6 - i * 5); g.stroke()
        g.lineCap = "butt"
    g.restore()


def draw_enemy(e):
    if e.dead > 30 or e.x < S.cam - 40 or e.x > S.cam + VW + 40:
        return
    rt = e.rot and abs(e.rot) > .01
    if rt:
        g.save(); g.translate(e.x + e.w / 2, e.y + e.h / 2); g.rotate(e.rot); g.translate(-e.x - e.w / 2, -e.y - e.h / 2)
    if e.k == "ant":
        draw_ant(e)
    else:
        draw_nut(e)
    if rt:
        g.restore()


# ======================================================================= the Grand Chili
def chili_path(dx, dy, begin):
    if begin:
        g.beginPath()
    g.moveTo(-22 + dx, -52 + dy)
    g.bezierCurveTo(-25 + dx, -66 + dy, 25 + dx, -66 + dy, 22 + dx, -52 + dy)
    g.bezierCurveTo(22 + dx, -36 + dy, 20 + dx, -20 + dy, 13 + dx, -9 + dy)
    g.quadraticCurveTo(10 + dx, -3 + dy, 5 + dx, -3 + dy)
    g.bezierCurveTo(-5 + dx, -12 + dy, -19 + dx, -32 + dy, -22 + dx, -52 + dy)
    g.closePath()


def evil_eye(x, y, sg, dd, blink, hurt, B):
    g.lineCap = "round"; g.lineJoin = "round"; g.strokeStyle = OL
    if hurt:
        g.lineWidth = 3; g.beginPath(); g.moveTo(x + sg * 5, y - 6); g.lineTo(x - sg * 4, y); g.lineTo(x + sg * 5, y + 6); g.stroke(); g.lineCap = "butt"
        return
    if blink:
        g.lineWidth = 3; g.beginPath(); g.moveTo(x - 7, y - 3 if sg < 0 else y + 1); g.lineTo(x + 7, y + 1 if sg < 0 else y - 3); g.stroke(); g.lineCap = "butt"
        return
    g.fillStyle = OL; g.beginPath(); g.ellipse(x, y, 8.8, 9.4, 0, 0, 7); g.fill()
    g.save(); g.beginPath(); g.ellipse(x, y, 7.6, 8.2, 0, 0, 7); g.clip()
    g.fillStyle = "#fff8dc"; g.fillRect(x - 9, y - 10, 18, 20)
    g.fillStyle = "#ffb020"; g.beginPath(); g.ellipse(x + dd * 1.6, y + 2, 4.8, 5.6, 0, 0, 7); g.fill()
    g.fillStyle = OL; g.beginPath(); g.ellipse(x + dd * 1.8, y + 2.2, 2.6, 4.6, 0, 0, 7); g.fill()
    g.fillStyle = "#fff"; g.beginPath(); g.arc(x + dd * 1.8 - 1, y - .6, 1.2, 0, 7); g.fill()
    yR, yL = (y - 1, y - 6.5) if sg < 0 else (y - 6.5, y - 1)
    g.fillStyle = B; g.beginPath(); g.moveTo(x - 10, y - 11); g.lineTo(x + 10, y - 11); g.lineTo(x + 10, yR); g.lineTo(x - 10, yL); g.closePath(); g.fill()
    g.restore()
    g.lineWidth = 3; g.beginPath(); g.moveTo(x - 8.5, yL); g.lineTo(x + 8.5, yR); g.stroke()
    g.lineCap = "butt"


def draw_boss():
    b, P, tick = S.boss, S.P, S.tick
    d = -1 if P.x < b.x else 1
    hurt = b.flash > 0
    fl = hurt and (b.flash >> 2) % 2
    opn = (b.cd < 14 or hurt) and not b.dead
    bl = (tick % 210) < 8
    g.save(); g.translate(round(b.x + 28), round(b.y + 64)); g.scale(d, 1)
    B = "#ffffff" if fl else "#e8352b"
    Sd = "#ffd9d3" if fl else "#a5201c"
    Hh = "#ffffff" if fl else "#ff8a70"
    if not hurt:
        pl = 1 + sin(tick * .1) * .08
        glow(0, -34, 10, 64 * pl, "255,70,40", .32)
    for x in (-5, 13):
        cel(x, -6, 6.5, 4, "#fff" if fl else "#c22f28", "#ffd9d3" if fl else "#8a1a16", "#fff" if fl else "#ff8f80")
    for sd in (-1, 1):
        cel(sd * 23, -31 + sin(tick * .12 + sd) * 2.5, 5, 4.2, B, Sd, Hh)
    chili_path(0, 0, True); g.fillStyle = B; g.fill()
    g.save(); chili_path(0, 0, True); g.clip()
    g.fillStyle = Sd; g.beginPath(); g.rect(-40, -80, 80, 90); chili_path(-7, -3, False); g.fill("evenodd")
    g.fillStyle = Hh; g.beginPath(); g.ellipse(-14, -50, 3.6, 10, .25, 0, 7); g.fill()
    g.beginPath(); g.ellipse(-11, -35, 2.2, 4.5, .15, 0, 7); g.fill()
    g.restore()
    chili_path(0, 0, True); g.strokeStyle = OL; g.lineWidth = 3; g.lineJoin = "round"; g.stroke()
    limb([[-4, -63], [-9, -71], [-18, -70]], "#3f9a4a", 5)
    g.fillStyle = OL; g.beginPath(); g.ellipse(0, -61.5, 13, 6.4, 0, 0, 7); g.fill()
    g.fillStyle = "#3f9a4a"; g.beginPath(); g.ellipse(0, -61.5, 11, 4.8, 0, 0, 7); g.fill()
    g.fillStyle = "#2b7a32"; g.beginPath(); g.ellipse(4, -60.5, 7, 3, 0, 0, 7); g.fill()
    evil_eye(-10, -45, -1, 1, bl, hurt, B); evil_eye(10, -45, 1, 1, bl, hurt, B)
    if opn:
        g.fillStyle = OL; g.beginPath(); g.ellipse(0, -30, 6.5, 7.5, 0, 0, 7); g.fill()
        g.fillStyle = "#ff5a6e"; g.beginPath(); g.ellipse(0, -26.5, 3.8, 2.6, 0, 0, 7); g.fill()
        g.fillStyle = "#fff"; g.strokeStyle = OL; g.lineWidth = 1.2
        g.beginPath(); g.moveTo(-5.5, -36); g.lineTo(-2, -36); g.lineTo(-3.8, -31.5); g.closePath(); g.fill(); g.stroke()
        g.beginPath(); g.moveTo(5.5, -36); g.lineTo(2, -36); g.lineTo(3.8, -31.5); g.closePath(); g.fill(); g.stroke()
    else:
        g.beginPath(); g.moveTo(-13, -35); g.quadraticCurveTo(0, -21, 13, -35); g.quadraticCurveTo(0, -31, -13, -35); g.closePath()
        g.fillStyle = "#3a0a10"; g.fill(); g.strokeStyle = OL; g.lineWidth = 2.2; g.lineJoin = "round"; g.stroke()
        g.fillStyle = "#fff"; g.lineWidth = 1.2
        g.beginPath(); g.moveTo(-9, -34.6); g.lineTo(-5.5, -33.9); g.lineTo(-7.3, -29.8); g.closePath(); g.fill(); g.stroke()
        g.beginPath(); g.moveTo(9, -34.6); g.lineTo(5.5, -33.9); g.lineTo(7.3, -29.8); g.closePath(); g.fill(); g.stroke()
    g.save(); g.translate(1, -60 + sin(tick * .1) * .8); g.rotate(-.12)

    def cp():
        g.beginPath(); g.moveTo(-15, 0); g.lineTo(-15, -14); g.lineTo(-7.5, -7); g.lineTo(0, -17); g.lineTo(7.5, -7); g.lineTo(15, -14); g.lineTo(15, 0); g.closePath()
    cp(); g.fillStyle = "#ffd23f"; g.fill()
    g.save(); cp(); g.clip(); g.fillStyle = "#e0a416"; g.fillRect(0, -20, 20, 22); g.fillStyle = "#fff0a0"; g.fillRect(-14, -13, 3, 10)
    g.fillStyle = "#f0b52a"; g.fillRect(-16, -5, 32, 5); g.restore()
    cp(); g.strokeStyle = OL; g.lineWidth = 2.2; g.lineJoin = "round"; g.stroke()
    g.fillStyle = OL; g.beginPath(); g.arc(0, -2.6, 3.6, 0, 7); g.fill(); g.fillStyle = "#ff4d6d"; g.beginPath(); g.arc(0, -2.6, 2.5, 0, 7); g.fill()
    g.fillStyle = "#fff"; g.fillRect(-1.2, -3.8, 1.2, 1.2)
    for p in [[-15, -14], [0, -17], [15, -14]]:
        g.fillStyle = OL; g.beginPath(); g.arc(p[0], p[1], 2.6, 0, 7); g.fill()
        g.fillStyle = "#fff"; g.beginPath(); g.arc(p[0], p[1], 1.6, 0, 7); g.fill()
    g.restore()
    g.restore()


# ======================================================================= Crumb
def eye(cx, cy, rx, ry, f, blink, lk):
    ex, ey = cx + lk[0] * .4, cy + lk[1] * .5
    if blink:
        g.strokeStyle = OL; g.lineWidth = .9; g.lineCap = "round"; g.beginPath(); g.moveTo(cx - rx, cy + .8)
        g.quadraticCurveTo(cx, cy + 2.4, cx + rx, cy + .8); g.stroke(); g.lineCap = "butt"
        return
    g.fillStyle = OL; g.beginPath(); g.ellipse(ex, ey, rx, ry, 0, 0, 7); g.fill()
    g.fillStyle = "#fff"; g.beginPath(); g.arc(ex - rx * .3, ey - ry * .35, rx * .4, 0, 7); g.fill()


def sprout(fire, sw, sp=None):
    c1 = "#f0742e" if fire else "#58b84c"
    c2 = "#b8401a" if fire else "#2f7a32"
    c3 = "#ffc48a" if fire else "#a6e88f"

    def leaf(px, py, d, sc, rot):
        g.save(); g.translate(px, py); g.rotate(rot); g.scale(d * sc, sc)

        def p():
            g.beginPath(); g.moveTo(0, 0); g.bezierCurveTo(3, -9, 15, -11, 19, -4); g.bezierCurveTo(14, 2, 6, 3, 0, 0); g.closePath()
        p(); g.fillStyle = c1; g.fill()
        g.save(); p(); g.clip()
        g.fillStyle = c2; g.beginPath(); g.moveTo(-1, 0); g.lineTo(19, -4); g.lineTo(20, 6); g.lineTo(-1, 6); g.closePath(); g.fill()
        g.fillStyle = c3; g.beginPath(); g.ellipse(9, -6.5, 5, 1.4, -.15, 0, 7); g.fill()
        g.restore()
        p(); g.strokeStyle = OL; g.lineWidth = .75 / sc; g.stroke()
        g.beginPath(); g.moveTo(1, -1); g.quadraticCurveTo(9, -5, 17, -4); g.lineWidth = .5 / sc; g.stroke()
        g.restore()

    if sp:
        k, cs, ty2 = sp[1], cos(sp[0]), -33
        g.lineCap = "round"; g.lineJoin = "round"
        g.strokeStyle = OL; g.lineWidth = 3; g.beginPath(); g.moveTo(0, -26); g.lineTo(0, ty2); g.stroke()
        g.strokeStyle = c2; g.lineWidth = 2.4; g.stroke(); g.strokeStyle = c1; g.lineWidth = 1; g.stroke()
        g.fillStyle = f"rgba(255,170,90,{.3 * k})" if fire else f"rgba(140,225,120,{.34 * k})"
        g.beginPath(); g.ellipse(0, ty2 - .5, 21 * k + 2, 3.2, 0, 0, 7); g.fill()
        leaf(0, ty2, cs, .95, 0); leaf(0, ty2, -cs, .95, 0)
        g.fillStyle = OL; g.beginPath(); g.arc(0, ty2, 1.9, 0, 7); g.fill(); g.fillStyle = c3; g.beginPath(); g.arc(-.3, ty2 - .3, .9, 0, 7); g.fill()
        g.lineCap = "butt"
        return
    tx, ty = sw * .8, -34
    g.lineCap = "round"; g.lineJoin = "round"
    g.strokeStyle = OL; g.lineWidth = 3; g.beginPath(); g.moveTo(0, -26); g.quadraticCurveTo(-1, -31, tx, ty); g.stroke()
    g.strokeStyle = c2; g.lineWidth = 2.4; g.stroke()
    g.strokeStyle = c1; g.lineWidth = 1; g.stroke()
    leaf(-.5 + sw * .4, -29.5, -1, .72, 0)
    leaf(tx, ty + 1, 1, 1, 0)
    leaf(tx, ty - 1, 1, .5, -1.3)
    g.lineCap = "butt"


def crust_path(dx, dy, b):
    if b:
        g.beginPath()
    g.moveTo(-10.5 + dx, -4.5 + dy); g.lineTo(-10.5 + dx, -19 + dy)
    g.bezierCurveTo(-13.8 + dx, -19 + dy, -14 + dx, -27 + dy, -8.5 + dx, -27.5 + dy)
    g.bezierCurveTo(-5 + dx, -30.8 + dy, 5 + dx, -30.8 + dy, 8.5 + dx, -27.5 + dy)
    g.bezierCurveTo(14 + dx, -27 + dy, 13.8 + dx, -19 + dy, 10.5 + dx, -19 + dy)
    g.lineTo(10.5 + dx, -4.5 + dy); g.quadraticCurveTo(0 + dx, -3 + dy, -10.5 + dx, -4.5 + dy); g.closePath()


def plate_path(dx, dy, b):
    if b:
        g.beginPath()
    g.moveTo(-8 + dx, -6.5 + dy); g.lineTo(-8 + dx, -19.6 + dy)
    g.bezierCurveTo(-11.3 + dx, -19.6 + dy, -11.4 + dx, -25.6 + dy, -7 + dx, -26 + dy)
    g.bezierCurveTo(-3.8 + dx, -28.6 + dy, 3.8 + dx, -28.6 + dy, 7 + dx, -26 + dy)
    g.bezierCurveTo(11.4 + dx, -25.6 + dy, 11.3 + dx, -19.6 + dy, 8 + dx, -19.6 + dy)
    g.lineTo(8 + dx, -6.5 + dy); g.quadraticCurveTo(0 + dx, -5.2 + dy, -8 + dx, -6.5 + dy); g.closePath()


def shoe(x, y, f):
    PAL = S.PAL
    g.save(); g.translate(x, y); g.scale(f * .78, .78)

    def p():
        g.beginPath(); g.moveTo(-6, 0); g.lineTo(-6, -4.4); g.quadraticCurveTo(-6, -6.4, -4, -6.4); g.lineTo(.8, -6.4)
        g.quadraticCurveTo(3, -6.4, 4.6, -4.8); g.quadraticCurveTo(7.8, -3.9, 7.8, -1.7); g.quadraticCurveTo(7.8, 0, 6, 0); g.closePath()
    p(); g.fillStyle = PAL["shoe"]; g.fill()
    g.save(); p(); g.clip()
    g.fillStyle = PAL["shoe2"]; g.fillRect(-7, -3.8, 16, 1.9)
    g.fillStyle = "#fff3d6"; g.fillRect(-7, -2, 16, 2)
    g.fillStyle = "#d9c9a0"; g.fillRect(-7, -.7, 16, .8)
    g.fillStyle = "#ff9a80"; g.beginPath(); g.ellipse(2.8, -5, 2.2, .9, -.3, 0, 7); g.fill()
    g.restore()
    p(); g.strokeStyle = OL; g.lineWidth = .85; g.lineJoin = "round"; g.stroke()
    g.restore()


def flame(x, y, sc, rot, al=1, st=1):
    g.save(); g.translate(x, y); g.rotate(rot); g.scale(sc, sc * (st or 1)); g.globalAlpha = al
    g.beginPath(); g.moveTo(0, -9); g.bezierCurveTo(3.8, -5, 4.2, -1, 0, 1.8); g.bezierCurveTo(-4.2, -1, -3.8, -5, 0, -9); g.closePath()
    g.fillStyle = "#ff6a1c"; g.fill(); g.strokeStyle = "#8a2410"; g.lineWidth = .55 / sc; g.lineJoin = "round"; g.stroke()
    g.beginPath(); g.moveTo(0, -5.4); g.bezierCurveTo(2, -3, 2.2, -.6, 0, .8); g.bezierCurveTo(-2.2, -.6, -2, -3, 0, -5.4); g.closePath()
    g.fillStyle = "#ffd23f"; g.fill(); g.restore()


def draw_roll_ball(P, f, q):
    tick = S.tick
    R_ = 11.5
    cy = -R_
    pb = max(0, min(1, (q - .22) / .63))
    ang = f * pb * PI * 2 * 2.4
    st = S.ROLLSTYLE

    def circ(x, y, r):
        g.beginPath(); g.arc(x, y, r, 0, 7)
    for i in (2, 1):
        g.globalAlpha = .28 / i; g.fillStyle = "#e9b26a" if st == 2 else "#d9964a"; circ(-f * i * 9, cy, R_ - i * 1.3); g.fill()
    g.globalAlpha = 1; g.lineCap = "round"
    for i in range(3):
        y = cy - 7 + i * 7
        x = -f * (R_ + 3 + ((tick * 1.3 + i * 5) % 6))
        g.strokeStyle = "rgba(255,255,255,.8)"; g.lineWidth = 1.1; g.beginPath(); g.moveTo(x, y); g.lineTo(x - f * (6 - i), y); g.stroke()
    g.save(); g.translate(0, cy)
    if st == 2:
        g.fillStyle = "#e9b26a"; circ(0, 0, R_); g.fill()
        g.save(); circ(0, 0, R_ - .6); g.clip(); g.rotate(ang); g.lineCap = "round"
        for arm in range(2):
            g.beginPath()
            a = 0.0
            first = True
            while a <= PI * 6.4:
                r = 1.2 + (R_ - 1) * a / (PI * 6.4)
                x, y = r * cos(a + arm * PI), r * sin(a + arm * PI)
                if first:
                    g.moveTo(x, y)
                    first = False
                else:
                    g.lineTo(x, y)
                a += .25
            g.strokeStyle = "#fff1cf" if arm else "#8a4a1f"; g.lineWidth = 1.7 if arm else 2; g.stroke()
        g.restore()
        g.save(); circ(0, 0, R_ - .6); g.clip(); g.fillStyle = "rgba(120,60,20,.28)"; circ(2.4, 2.6, R_ + .5); g.fill("evenodd"); g.restore()
    else:
        g.fillStyle = "#d9964a"; circ(0, 0, R_); g.fill()
        g.save(); g.rotate(ang); g.strokeStyle = "#a9642a"; g.lineWidth = 2.6
        for k in range(4):
            g.beginPath(); g.arc(0, 0, R_ - 1.5, k * PI / 2 + .2, k * PI / 2 + 1.1); g.stroke()
        g.restore()
        g.fillStyle = "#e8c98a"; circ(0, 0, R_ - 3.4); g.fill()
        g.save(); circ(0, 0, R_ - 3.4); g.clip(); g.fillStyle = "#fbe3b0"; circ(-1.5, -1.5, R_ - 3.4); g.fill(); g.restore()
        if st == 1:
            g.save(); g.rotate(ang); g.fillStyle = "rgba(200,130,50,.55)"
            for k in range(4):
                g.beginPath(); g.arc(cos(k * PI / 2 + .5) * 4.4, sin(k * PI / 2 + .5) * 4.4, .75, 0, 7); g.fill()
            g.restore()
        g.strokeStyle = "#b06f30"; g.lineWidth = .6; circ(0, 0, R_ - 3.4); g.stroke()
        if st == 3:
            g.strokeStyle = OL; g.lineWidth = 1; g.lineCap = "round"
            for x in (-3.3, 3.3):
                g.beginPath(); g.moveTo(x + f * 1.2 - 1.7, -.6); g.quadraticCurveTo(x + f * 1.2, -4, x + f * 1.2 + 1.7, -.6); g.stroke()
            g.beginPath(); g.arc(f * 1.2, 1.4, 2, .3, PI - .3); g.stroke()
            g.fillStyle = "rgba(255,120,145,.8)"
            for x in (-5.2, 5.2):
                g.beginPath(); g.ellipse(x + f * 1.2, 2.2, 1.5, .95, 0, 0, 7); g.fill()
    g.fillStyle = "rgba(255,255,255,.5)"; g.beginPath(); g.ellipse(-4.6, -6.2, 1.6, 3, .7, 0, 7); g.fill()
    g.strokeStyle = OL; g.lineWidth = .9; circ(0, 0, R_); g.stroke()
    g.restore()
    g.save(); g.translate(0, 5); sprout(P.fire, max(-2, min(2, -f * 1.8 + sin(tick * .8) * .4))); g.restore()
    if P.fire:
        flame(-f * (R_ + 4), cy + 2, .75, -f * PI / 2, .9, 1.3); flame(-f * (R_ + 6), cy - 5, .6, -f * PI / 2, .7, 1.3)


def draw_bow(x, y):
    g.save(); g.translate(x, y); g.rotate(-.3); g.lineJoin = "round"; g.strokeStyle = OL; g.lineWidth = .8
    g.fillStyle = "#ff7fae"
    for d in (-1, 1):
        g.beginPath(); g.moveTo(0, 0); g.quadraticCurveTo(d * 3, -4.4, d * 5.6, -2.4); g.quadraticCurveTo(d * 6.2, 1.6, d * 5, 3.2)
        g.quadraticCurveTo(d * 2.6, 2.6, 0, 0); g.fill(); g.stroke()
    g.fillStyle = "#ff4f8d"; g.beginPath(); g.arc(0, 0, 1.5, 0, 7); g.fill(); g.stroke()
    g.restore()


def draw_player():
    P = S.P
    if not P:
        return
    st, tick, PAL = S.state, S.tick, S.PAL
    if P.inv > 0 and st == "play" and (P.inv >> 2) % 2:
        return
    f = P.face
    s = 1.5 if P.big else 1
    g.save(); g.translate(P.x + P.w / 2, P.y + P.h)
    if P.spin:
        pv = 12.3 * s
        g.translate(0, -pv); g.rotate(P.spin); g.translate(0, pv)
    if P.kiss:
        g.rotate(f * P.kiss * .27)
    if P.sl == 1:
        g.translate(sin(tick * 1.7) * .5, 0)
    o = ohs_of(P)
    if o > .15 and st == "play":
        g.translate((rnd() - .5) * o * 2.4, (rnd() - .5) * o * 1.5)
    rl = P.roll > 0
    rq = 1 - P.roll / ROLLT if rl else 0
    gw = P.gp > 0
    gf = bool(P.gpf)
    gpl = P.gpl > 0
    tuck = (rl and S.ROLLSTYLE == 0) or gw or gf
    if gw:
        pv, pr = 12.3 * s, 1 - P.gp / GPW
        g.translate(0, -pv); g.rotate(f * pr * PI * 2); g.translate(0, pv)
    if rl and S.ROLLSTYLE > 0 and .22 <= rq < .85:
        g.scale(s, s); g.scale(.82, .82); draw_roll_ball(P, f, rq); g.restore()
        return
    if tuck:
        pv = 12.3 * s
        g.translate(0, -pv); g.rotate(f * rq * PI * 2); g.translate(0, pv)
    g.scale(s, s * P.h / (42 if P.big else 28) if (P.duck and not rl) else s); g.scale(.82, .82)
    t = tick * .3 * max(.3, abs(P.vx) / 3)
    mv = P.ground and abs(P.vx) > .2 and not rl
    a = sin(t) * 4 if mv else 0
    air = not P.ground or tuck
    if P.has("_g") and P._g is False and P.ground:
        P._sq = 1
    P._sq = max(0, (P._sq or 0) - .09)
    P._g = bool(P.ground)
    sx = sy = 1
    if air:
        if P.vy < -1:
            sy, sx = 1.08, .94
        elif P.vy > 2:
            sy, sx = 1.05, .96
    else:
        br = sin(tick * .07) * .012
        sy, sx = 1 + br, 1 - br
        if mv:
            bb = abs(sin(t)) * .03
            sy += bb
            sx -= bb
    sy *= 1 - .16 * P._sq
    sx *= 1 + .14 * P._sq
    if gf:
        sx, sy = .86, 1.2
    elif gw:
        sx, sy = 1.06, .94
    elif gpl:
        k = P.gpl / GPL
        sx, sy = 1 + .34 * k, 1 - .32 * k
    if gf:
        g.lineCap = "round"
        for i in range(3):
            ph = (tick * 1.4 + i * 5) % 14
            xx = (i - 1) * 7
            g.strokeStyle = f"rgba(255,255,255,{.85 - ph / 20})"; g.lineWidth = 1.3
            g.beginPath(); g.moveTo(xx, -38 - ph); g.lineTo(xx, -49 - ph); g.stroke()
        g.lineCap = "butt"
    if rl:
        if S.ROLLSTYLE == 0:
            sx = sy = 1
        elif rq < .22:
            sx, sy = 1.15, .62
        else:
            k = (rq - .85) / .15
            sx, sy = .9 + .1 * k, 1.14 - .14 * k
    ws = P.ws if (P.ws and not P.ground and st == "play" and not rl) else 0
    wjf = P.wjf > 0 and st == "play" and not rl
    lean = -ws * .07 if ws else (0 if (P.duck or rl) else max(-.12, min(.12, P.vx * (.03 if P.ground else .02))))
    zoom = mv and abs(P.vx) >= 4.8 and st != "dead"
    ouch = st == "dead" or P.inv > 52
    sk = ohs_of(P)
    sick = sk > .3 and st == "play" and not rl and not ouch
    mood = (P.mk if P.has("mk") else -1) if (not ouch and P.mt > 0) else -1
    if zoom and not P.fire:
        g.lineCap = "round"
        for i in range(3):
            ph = (tick * .9 + i * 7) % 16
            yy, xx = -9 - i * 8.5, -f * (15 + ph * .7)
            g.strokeStyle = f"rgba(255,255,255,{.75 - ph / 26})"; g.lineWidth = 1.1
            g.beginPath(); g.moveTo(xx, yy); g.lineTo(xx - f * (5 + i * 1.5), yy); g.stroke()
        g.lineCap = "butt"
    if P.fire and st != "dead" and (zoom or mv):
        for i in range(3 if zoom else 1):
            ph = (tick * .7 + i * 5) % 12
            yy = (-10 - i * 7 if zoom else -12) + sin(tick * .6 + i) * .7
            xx = -f * (9 + ph * .3)
            sc = (.95 if zoom else .62) * (1 - ph / 30)
            flame(xx, yy, sc, -f * PI / 2 + sin(tick * .5 + i * 2) * .12, 1 - ph / 16, 1.35)
    if mood == 2:
        g.translate(0, -abs(sin(tick * .5)) * 1.1)
    if mood == 0:
        g.translate(sin(tick * 2.2) * .35, 0)
    if ouch:
        g.translate(sin(tick * 1.6) * (.6 if st == "dead" else (P.inv - 52) * .03), 0)
    if ws:
        g.translate(ws * 2.8, 0)
    g.rotate(-f * .07 if ouch else lean); g.scale(sx, sy)
    l1 = 5 if tuck else (1.8 if air else (max(0, cos(t)) * 2.4 if mv else 0))
    l2 = 5 if tuck else (1.8 if air else (max(0, -cos(t)) * 2.4 if mv else 0))
    f1 = -4.2 if tuck else -6.4 + (-1.5 if air else a)
    f2 = 4.2 if tuck else 6.4 + (1.5 if air else -a)
    if ws:
        sw = sin(tick * .5) * .6
        if ws > 0:
            f2, l2, f1, l1 = 7, 3.6, -4.4 + sw, -.4
        else:
            f1, l1, f2, l2 = -7, 3.6, 4.4 - sw, -.4
    for q in [[-5, f1, l1], [5, f2, l2]]:
        g.lineCap = "round"; g.strokeStyle = OL; g.lineWidth = 3.2; g.beginPath(); g.moveTo(q[0], -10); g.lineTo(q[1] + f * .6, -5.6 - q[2]); g.stroke()
        g.strokeStyle = PAL["leg"]; g.lineWidth = 2.3; g.stroke(); g.lineCap = "butt"
    if P.fire and st != "dead":
        fk = sin(tick * .5)
        bg = 1.35 if air else 1
        for q in [[f1, l1, 0], [f2, l2, 1.7]]:
            flame(q[0] - f * 3.6, -q[1] - 1.5, (.55 + fk * .07 * (-1 if q[2] else 1)) * bg, -f * .5 + sin(tick * .4 + q[2]) * .12)
    shoe(f1, -l1, f); shoe(f2, -l2, f)
    g.save(); g.translate(0, -5)
    crust_path(0, 0, True); g.fillStyle = PAL["crust"]; g.fill()
    g.save(); crust_path(0, 0, True); g.clip()
    g.fillStyle = PAL["shade"]; g.beginPath(); g.rect(-20, -40, 40, 40); crust_path(-3, -2.5, False); g.fill("evenodd")
    g.fillStyle = PAL["hi"]; g.beginPath(); g.ellipse(-11.7, -23.4, 1.4, 3, .15, 0, 7); g.fill()
    g.restore()
    crust_path(0, 0, True); g.strokeStyle = OL; g.lineWidth = .85; g.lineJoin = "round"; g.stroke()
    plate_path(0, 0, True); g.fillStyle = PAL["plate"]; g.fill()
    g.save(); plate_path(0, 0, True); g.clip()
    g.strokeStyle = PAL["ring"]; g.lineWidth = 3.4; plate_path(0, 0, True); g.stroke()
    g.fillStyle = PAL["inner"]; g.beginPath(); g.rect(-20, -40, 40, 40); plate_path(-2.4, -1.8, False); g.fill("evenodd")
    g.fillStyle = PAL["spk"]
    for p in [[-3.2, -25.6], [3.6, -25], [-4.8, -8.8], [4.4, -8.4], [0, -8.2]]:
        g.beginPath(); g.arc(p[0], p[1], .5, 0, 7); g.fill()
    g.restore()
    plate_path(0, 0, True); g.strokeStyle = PAL["pst"]; g.lineWidth = .6; g.stroke()
    g.fillStyle = PAL["cheek"]
    for x in (-6.6, 6.6):
        g.beginPath(); g.ellipse(x + f * .8, -12.4, 1.9, 1.2, 0, 0, 7); g.fill()
    bl = st in ("play", "title") and (tick % 230) < 7 and not zoom and not ouch and mood < 0
    lk = (max(-1, min(1, P.vx / 4)), -1 if P.vy < -1 else (1 if P.vy > 3 else 0))
    ex1, ex2, mx = -4.6 + f * .8, 4.6 + f * .8, f * .8
    g.lineCap = "round"; g.lineJoin = "round"
    if P.sl == 1:
        g.strokeStyle = OL; g.lineWidth = 1.1
        for e in [[ex1 + 1.6, 1], [ex2 + .4, -1]]:
            g.beginPath(); g.moveTo(e[0] - 1.9 * e[1], -18.6); g.lineTo(e[0] + 1.7 * e[1], -16.4); g.lineTo(e[0] - 1.9 * e[1], -14.2); g.stroke()
        g.lineWidth = .8; g.beginPath(); g.moveTo(ex1 + .6, -21); g.lineTo(ex1 + 4.4, -19.6); g.moveTo(ex2 + 2, -21.4); g.lineTo(ex2 - 1.2, -19.8); g.stroke()
    elif P.kiss > .55:
        g.strokeStyle = OL; g.lineWidth = 1.05
        for x in (ex1, ex2):
            g.beginPath(); g.moveTo(x - 2, -15.4); g.quadraticCurveTo(x, -19, x + 2, -15.4); g.stroke()
        g.fillStyle = "#e0607a"; g.strokeStyle = OL; g.lineWidth = .6; g.beginPath(); g.ellipse(mx + f * 2.6, -11.6, 1.9, 1.45, 0, 0, 7); g.fill(); g.stroke()
        g.fillStyle = "rgba(255,255,255,.65)"; g.beginPath(); g.arc(mx + f * 2.4, -12.1, .45, 0, 7); g.fill()
    elif ws:
        lkx = sin(tick * .12) * .5
        g.strokeStyle = OL; g.lineWidth = .85
        for x in (ex1, ex2):
            g.fillStyle = "#fff"; g.beginPath(); g.ellipse(x, -16.4, 2.3, 2.9, 0, 0, 7); g.fill(); g.stroke()
            g.fillStyle = OL; g.beginPath(); g.arc(x + lkx * .5 - ws * .3, -17.4, 1.15, 0, 7); g.fill()
        g.lineWidth = .9; g.beginPath(); g.moveTo(ex1 - 2.2, -20.6); g.lineTo(ex1 + 2, -21.8); g.moveTo(ex2 + 2.2, -20.6); g.lineTo(ex2 - 2, -21.8); g.stroke()
        g.beginPath(); g.moveTo(mx - 3.2, -10.2); g.quadraticCurveTo(mx - 1.6, -12, mx, -10.2); g.quadraticCurveTo(mx + 1.6, -8.4, mx + 3.2, -10.2); g.stroke()
        dy = (tick * .35) % 7
        g.globalAlpha = 1 - dy / 9; g.fillStyle = "#8fd3ff"; g.strokeStyle = "#2b6d99"; g.lineWidth = .6
        sx_ = -ws * 9.6
        g.beginPath(); g.moveTo(sx_, -24 + dy); g.quadraticCurveTo(sx_ + 2.3, -20.6 + dy, sx_, -19 + dy); g.quadraticCurveTo(sx_ - 2.3, -20.6 + dy, sx_, -24 + dy)
        g.fill(); g.stroke(); g.globalAlpha = 1
    elif wjf:
        g.strokeStyle = OL; g.lineWidth = 1.05
        for x in (ex1, ex2):
            g.beginPath(); g.moveTo(x - 2.1, -15.4); g.quadraticCurveTo(x, -19.2, x + 2.1, -15.4); g.stroke()
        g.fillStyle = "#8c2b1f"; g.beginPath(); g.moveTo(mx - 3.4, -11.6); g.quadraticCurveTo(mx, -7.6, mx + 3.4, -11.6); g.closePath(); g.fill(); g.stroke()
        g.fillStyle = "#ff8a8a"; g.beginPath(); g.ellipse(mx, -9.6, 1.7, .8, 0, 0, 7); g.fill()
    elif ouch:
        g.strokeStyle = OL; g.lineWidth = 1
        for e in [[ex1, 1], [ex2, -1]]:
            g.beginPath(); g.moveTo(e[0] - 1.9 * e[1], -18.6); g.lineTo(e[0] + 1.7 * e[1], -16.4); g.lineTo(e[0] - 1.9 * e[1], -14.2); g.stroke()
        g.fillStyle = "#7a2a1c"; g.beginPath(); g.ellipse(mx, -11.6, 1.7, 1.45, 0, 0, 7); g.fill()
        g.lineWidth = .7; g.strokeStyle = OL; g.stroke()
        g.fillStyle = "#ff8d9b"; g.beginPath(); g.ellipse(mx, -10.9, .9, .5, 0, 0, 7); g.fill()
        dy = (tick * .35) % 6
        g.fillStyle = "#bfe8ff"; g.strokeStyle = "#3d84b0"; g.lineWidth = .55
        g.beginPath(); g.moveTo(10.6, -24 + dy); g.quadraticCurveTo(13.4, -20.6 + dy, 10.6, -19 + dy); g.quadraticCurveTo(7.8, -20.6 + dy, 10.6, -24 + dy); g.fill(); g.stroke()
    elif sick:
        g.fillStyle = f"rgba(120,195,70,{.5 * sk})"; plate_path(0, 0, True); g.fill()
        g.strokeStyle = OL; g.lineWidth = .8
        for e in [[ex1, 1], [ex2, -1]]:
            g.save(); g.translate(e[0], -16.4); g.rotate(tick * .3 * e[1]); g.beginPath()
            a_ = 0.0
            g.moveTo(0, 0)
            a_ += .35
            while a_ <= PI * 4.4:
                r = a_ * .22
                g.lineTo(cos(a_) * r, sin(a_) * r)
                a_ += .35
            g.stroke(); g.restore()
        g.lineWidth = .95; g.beginPath(); g.moveTo(mx - 2.8, -10.8); g.quadraticCurveTo(mx - 1.4, -12.6, mx, -10.8); g.quadraticCurveTo(mx + 1.4, -9, mx + 2.8, -10.8); g.stroke()
        g.fillStyle = "#bfe8ff"; g.strokeStyle = "#3d84b0"; g.lineWidth = .55
        for o_ in (0, 3):
            dy = (tick * .4 + o_) % 6
            g.beginPath(); g.moveTo(10.6 - o_ * .6, -24 + dy); g.quadraticCurveTo(13.4 - o_ * .6, -20.6 + dy, 10.6 - o_ * .6, -19 + dy)
            g.quadraticCurveTo(7.8 - o_ * .6, -20.6 + dy, 10.6 - o_ * .6, -24 + dy); g.fill(); g.stroke()
    elif rl:
        g.strokeStyle = OL; g.lineWidth = 1.05
        for x in (ex1, ex2):
            g.beginPath(); g.moveTo(x - 2, -15.4); g.quadraticCurveTo(x, -19, x + 2, -15.4); g.stroke()
        g.beginPath(); g.arc(mx, -12.6, 2.2, .25, PI - .25); g.stroke()
    elif mood == 0:
        g.save()
        for e in [[ex1, 1], [ex2, -1]]:
            g.save(); g.beginPath(); g.moveTo(e[0] - 3 * e[1], -19.6); g.lineTo(e[0] + 3 * e[1], -16.6); g.lineTo(e[0] + 3 * e[1], -12)
            g.lineTo(e[0] - 3 * e[1], -12); g.closePath(); g.clip()
            g.fillStyle = OL; g.beginPath(); g.ellipse(e[0] + .2 * e[1], -16.2, 2, 2.6, 0, 0, 7); g.fill()
            g.fillStyle = "#fff"; g.beginPath(); g.arc(e[0] - .4 * e[1], -15.6, .65, 0, 7); g.fill(); g.restore()
            g.strokeStyle = OL; g.lineWidth = .9; g.beginPath(); g.moveTo(e[0] - 2.4 * e[1], -18.5); g.lineTo(e[0] + 2.4 * e[1], -16.5); g.stroke()
        g.strokeStyle = OL; g.lineWidth = 1; g.beginPath(); g.moveTo(mx - 2.4, -10.6); g.quadraticCurveTo(mx, -12.8, mx + 2.4, -10.6); g.stroke()
        g.strokeStyle = "#e0413a"; g.lineWidth = .95
        ax, ay = 8.6, -25.6
        for d in [[-1, -1], [1, -1], [-1, 1], [1, 1]]:
            g.beginPath(); g.moveTo(ax + d[0] * .7, ay + d[1] * .7); g.quadraticCurveTo(ax + d[0] * 2.4, ay + d[1] * .8, ax + d[0] * 2.5, ay + d[1] * 2.5); g.stroke()
        g.restore()
    elif mood == 1:
        for x in (ex1, ex2):
            g.fillStyle = OL; g.beginPath(); g.ellipse(x, -16, 2.05, 2.95, 0, 0, 7); g.fill()
            g.fillStyle = "#fff"; g.beginPath(); g.arc(x - .7, -17.2, .85, 0, 7); g.fill(); g.beginPath(); g.arc(x + .7, -14.9, .4, 0, 7); g.fill()
        g.strokeStyle = OL; g.lineWidth = .95; g.beginPath(); g.moveTo(mx - 2, -10.5); g.quadraticCurveTo(mx - 1, -12, mx, -11); g.quadraticCurveTo(mx + 1, -12.2, mx + 2, -10.6); g.stroke()
        dy = (tick * .12) % 4
        g.fillStyle = "#bfe8ff"; g.strokeStyle = "#3d84b0"; g.lineWidth = .5
        g.beginPath(); g.moveTo(-9.6, -23 + dy); g.quadraticCurveTo(-7.4, -20.4 + dy, -9.6, -19 + dy); g.quadraticCurveTo(-11.8, -20.4 + dy, -9.6, -23 + dy); g.fill(); g.stroke()
    elif mood == 2:
        g.strokeStyle = OL; g.lineWidth = 1.05
        for x in (ex1, ex2):
            g.beginPath(); g.moveTo(x - 2, -15.2); g.quadraticCurveTo(x, -19, x + 2, -15.2); g.stroke()
        g.beginPath(); g.moveTo(mx - 3.6, -13.8); g.quadraticCurveTo(mx, -12.6, mx + 3.6, -13.8); g.quadraticCurveTo(mx + 3.2, -7.4, mx, -7.4)
        g.quadraticCurveTo(mx - 3.2, -7.4, mx - 3.6, -13.8); g.closePath()
        g.fillStyle = "#7a2a1c"; g.fill(); g.lineWidth = .7; g.stroke()
        g.save(); g.clip(); g.fillStyle = "#ff8d9b"; g.beginPath(); g.ellipse(mx, -7.8, 2.3, 2, 0, 0, 7); g.fill(); g.restore()
        g.fillStyle = "#bfe8ff"
        for p in [[-9.6, -14], [9.6, -14]]:
            k = sin(tick * .5) * .6
            g.beginPath(); g.ellipse(p[0], p[1] + k, .9, 1.3, 0, 0, 7); g.fill()
    elif zoom:
        g.strokeStyle = OL; g.lineWidth = 1.05
        for x in (ex1, ex2):
            g.beginPath(); g.moveTo(x - 2, -15.4); g.quadraticCurveTo(x, -19.2, x + 2, -15.4); g.stroke()

        def mouth():
            g.beginPath(); g.moveTo(mx - 3, -13.6); g.quadraticCurveTo(mx, -13, mx + 3, -13.6); g.quadraticCurveTo(mx + 2.6, -8.6, mx, -8.6)
            g.quadraticCurveTo(mx - 2.6, -8.6, mx - 3, -13.6); g.closePath()
        mouth(); g.fillStyle = "#7a2a1c"; g.fill(); g.lineWidth = .7; g.stroke()
        g.save(); mouth(); g.clip(); g.fillStyle = "#ff8d9b"; g.beginPath(); g.ellipse(mx, -8.9, 1.9, 1.6, 0, 0, 7); g.fill(); g.restore()
    else:
        eye(ex1, -16.4, 1.9, 2.7, f, bl, lk); eye(ex2, -16.4, 1.9, 2.7, f, bl, lk)
        g.strokeStyle = OL; g.lineWidth = .95; g.beginPath(); g.arc(mx, -12.4, 1.9, .3, PI - .3); g.stroke()
    if PAL["fem"]:
        g.strokeStyle = OL; g.lineWidth = .8; g.lineCap = "round"
        for e in [[ex1, -1], [ex2, 1]]:
            x = e[0] + e[1] * 2.3
            g.beginPath(); g.moveTo(x, -18.2); g.lineTo(x + e[1] * 1.9, -19.4); g.moveTo(x, -17.2); g.lineTo(x + e[1] * 2.3, -17.6); g.stroke()
    g.lineCap = "butt"
    g.save(); g.translate(0, -3.5)
    swy = -f * 2 if P.ohd > 0 else max(-2, min(2, sin(tick * .07) * 1.2 - P.vx * .35 + (.6 if P.vy < -1 else (-.6 if P.vy > 3 else 0))))
    sprout(P.fire, swy, (P.gla or 0, P.gls) if (P.gls or 0) > .04 else None)
    if PAL["fem"]:
        draw_bow(-7.4, -22.4)
    g.restore()
    g.restore()
    g.restore()


def draw_as(p, pal):
    sv = S.P
    S.P = p
    S.PAL = pal
    draw_player()
    S.P = sv
    S.PAL = BASEPAL


# ======================================================================= goal, picnic, cage, key
def gingham(x, y, w, h, ox, oy, a, c=7):
    g.fillStyle = "#fff6dc"; g.fillRect(x, y, w, h)
    cols, rows = [], []
    cx = 0
    while cx < w:
        if math.floor((ox + cx) / c) % 2 == 0:
            cols.append((x + cx, y, min(c, w - cx), h))
        cx += c
    ry = math.floor(oy / c) * c
    while ry < oy + h:
        t = y + (ry - oy)
        rows.append((x, max(y, t), w, min(c, y + h - max(y, t))))
        ry += 2 * c
    # stripes overlap at the crossings, so paint each direction separately like the original
    g.fillStyle = f"rgba(216,56,42,{a})"
    g.fillRects(cols)
    g.fillRects(rows)


def bread_face(cx, cy, sc):
    g.save(); g.translate(cx, cy); g.scale(sc, sc); g.lineJoin = "round"

    def body(k):
        g.beginPath(); g.moveTo(-7 * k, 8 * k); g.lineTo(-7 * k, -2 * k); g.bezierCurveTo(-11 * k, -3 * k, -11 * k, -10 * k, -6 * k, -10 * k)
        g.bezierCurveTo(-3 * k, -13 * k, 3 * k, -13 * k, 6 * k, -10 * k); g.bezierCurveTo(11 * k, -10 * k, 11 * k, -3 * k, 7 * k, -2 * k)
        g.lineTo(7 * k, 8 * k); g.closePath()
    body(1); g.fillStyle = "#e6a95a"; g.fill(); g.strokeStyle = OL; g.lineWidth = 1.6; g.stroke()
    body(.74); g.fillStyle = "#fbe3b0"; g.fill()
    g.fillStyle = OL; g.beginPath(); g.arc(-2.6, 0, .95, 0, 7); g.arc(2.6, 0, .95, 0, 7); g.fill()
    g.strokeStyle = OL; g.lineWidth = .8; g.beginPath(); g.arc(0, 2.2, 1.9, .25, PI - .25); g.stroke()
    g.fillStyle = "rgba(255,130,120,.55)"; g.beginPath(); g.arc(-4.4, 2.4, 1.1, 0, 7); g.arc(4.4, 2.4, 1.1, 0, 7); g.fill()
    g.strokeStyle = "#2f7a32"; g.lineWidth = 1; g.beginPath(); g.moveTo(0, -11); g.lineTo(0, -14); g.stroke()
    g.fillStyle = "#58b84c"; g.strokeStyle = OL; g.lineWidth = .7
    for d in (-1, 1):
        g.beginPath(); g.moveTo(0, -13.6); g.quadraticCurveTo(d * 3, -18, d * 6.4, -14.4); g.quadraticCurveTo(d * 3, -13, 0, -13.6); g.fill(); g.stroke()
    g.restore()


def draw_picnic(cx):
    gx, gy = cx - 16, 10 * T
    g.save(); g.lineJoin = "round"
    bl = [[gx - 46, gy], [gx + 78, gy], [gx + 64, gy - 9], [gx - 32, gy - 9]]

    def blanket():
        g.beginPath(); g.moveTo(*bl[0])
        for q in bl[1:]:
            g.lineTo(*q)
        g.closePath()
    blanket(); g.save(); g.clip(); gingham(gx - 46, gy - 9, 124, 9, gx, 0, .72, 3); g.restore()
    blanket(); g.strokeStyle = OL; g.lineWidth = 2; g.stroke()
    g.strokeStyle = "#d8382a"; g.lineWidth = 1.3; g.beginPath()
    x = gx - 44
    while x < gx + 78:
        g.moveTo(x, gy); g.lineTo(x - .6, gy + 2.4)
        x += 4
    g.stroke()
    g.restore()
    g.save(); g.translate(gx - 18, gy - 8)
    g.fillStyle = OL; g.beginPath(); g.roundRect(-6.5, -14, 13, 14.5, 3); g.fill()
    g.fillStyle = "#c72f43"; g.beginPath(); g.roundRect(-5, -11, 10, 11, 2.4); g.fill()
    g.fillStyle = "rgba(255,255,255,.45)"; g.fillRect(-3.4, -9.6, 1.6, 7)
    g.fillStyle = "#fff6dc"; g.fillRect(-6.5, -16, 13, 3.4); g.fillStyle = "#d8382a"; g.fillRect(-6.5, -14.2, 13, 1.4)
    g.restore()
    cookie_art(gx + 2, gy - 13, 5.2)
    g.save(); g.translate(gx + 50, gy - 8)
    g.strokeStyle = OL; g.lineWidth = 3; g.beginPath(); g.arc(0, -11, 10.5, PI, 0); g.stroke()
    g.strokeStyle = "#d9a25b"; g.lineWidth = 1.4; g.beginPath(); g.arc(0, -11, 10.5, PI, 0); g.stroke()
    g.fillStyle = "#f0c987"; g.strokeStyle = OL; g.lineWidth = 1.6
    g.beginPath(); g.moveTo(-12, -18); g.quadraticCurveTo(-6, -26, 0, -21); g.quadraticCurveTo(6, -27, 12, -18); g.closePath(); g.fill(); g.stroke()
    g.fillStyle = "#d8382a"; g.beginPath(); g.arc(-5.5, -19.5, 3.4, 0, 7); g.fill(); g.stroke()
    g.fillStyle = "#2f7a32"; g.fillRect(-5.2, -24.6, 1.2, 2.6)

    def basket():
        g.beginPath(); g.moveTo(-14, -18); g.lineTo(14, -18); g.lineTo(11, 2); g.lineTo(-11, 2); g.closePath()
    basket(); g.fillStyle = "#c98b4a"; g.fill(); g.save(); g.clip()
    g.strokeStyle = "#8a5a2b"; g.lineWidth = 1.1; g.beginPath()
    for i in range(-16, 18, 5):
        g.moveTo(i, -19); g.lineTo(i + 8, 3); g.moveTo(i + 8, -19); g.lineTo(i, 3)
    g.stroke()
    g.fillStyle = "rgba(255,255,255,.18)"; g.fillRect(-14, -18, 28, 3.4); g.restore()
    g.strokeStyle = OL; g.lineWidth = 1.8; basket(); g.stroke()
    g.restore()


def draw_feast(cx):
    gx, gy, t = cx - 16, 10 * T, S.tick
    g.save(); g.lineJoin = "round"; g.lineCap = "round"
    fl = 1 + sin(t * .31) * .05 + sin(t * .13) * .05
    gr = g.createRadialGradient(gx - 34, gy - 16, 2, gx - 34, gy - 16, 78 * fl)
    gr.addColorStop(0, "rgba(255,190,90,.38)"); gr.addColorStop(1, "rgba(255,190,90,0)")
    g.fillStyle = gr; g.fillRect(gx - 120, gy - 100, 240, 100)
    sl = [[gx - 54, gy], [gx + 100, gy], [gx + 88, gy - 10], [gx - 42, gy - 10]]

    def slab():
        g.beginPath(); g.moveTo(*sl[0])
        for q in sl[1:]:
            g.lineTo(*q)
        g.closePath()
    slab(); g.fillStyle = "#8a7a70"; g.fill(); g.save(); g.clip()
    g.fillStyle = "#a19186"; g.fillRect(gx - 54, gy - 10, 156, 2.6)
    g.strokeStyle = "rgba(40,28,24,.45)"; g.lineWidth = 1; g.beginPath()
    for c in [[-24, -10, -28, 0], [30, -10, 34, 0], [60, -10, 57, 0]]:
        g.moveTo(gx + c[0], gy + c[1]); g.lineTo(gx + c[2], gy + c[3])
    g.moveTo(gx - 48, gy - 5); g.lineTo(gx + 94, gy - 5); g.stroke()
    g.fillStyle = "#4f9a4a"
    for m in [[-44, 1], [-6, 1.4], [52, 1.2]]:
        g.beginPath(); g.ellipse(gx + m[0], gy - 9, 7, 2.4 * m[1], 0, 0, 7); g.fill()
    g.restore()
    slab(); g.strokeStyle = OL; g.lineWidth = 2; g.stroke()
    g.fillStyle = "#5f5049"; g.fillRect(gx - 54, gy, 154, 2.4)

    def sh(x, y, r):
        g.fillStyle = "rgba(20,12,8,.42)"; g.beginPath(); g.ellipse(x, y, r, r * .3, 0, 0, 7); g.fill()

    def can(x, h, ph):
        g.fillStyle = OL; g.fillRect(x - 3.3, gy - 5 - h, 6.6, h + .4); g.fillStyle = "#fff0cf"; g.fillRect(x - 2.2, gy - 5 - h + 1, 4.4, h - .6)
        g.fillStyle = "#f2dcae"; g.fillRect(x + .6, gy - 5 - h + 1, 1.6, h - .6)
        g.fillStyle = "#fff0cf"; g.beginPath(); g.ellipse(x - 1.2, gy - 5 - h + 4, 1, 2.2, 0, 0, 7); g.fill()
        fh, sw, y = 5.6 + sin(t * .4 + ph) * 1.1, sin(t * .23 + ph) * .9, gy - 5 - h
        g.fillStyle = "#ff8a2a"; g.beginPath(); g.moveTo(x - 2.6, y - 2); g.quadraticCurveTo(x - 2.4 + sw * .3, y - fh * .6, x + sw, y - fh - 2)
        g.quadraticCurveTo(x + 2.4 + sw * .3, y - fh * .6, x + 2.6, y - 2); g.quadraticCurveTo(x, y + .2, x - 2.6, y - 2); g.fill()
        g.strokeStyle = OL; g.lineWidth = 1; g.stroke()
        g.fillStyle = "#ffe066"; g.beginPath(); g.ellipse(x + sw * .3, y - 3.4, 1.3, 2.4, 0, 0, 7); g.fill()
    sh(gx - 26, gy - 5, 7); sh(gx - 16, gy - 5, 6); can(gx - 26, 13, 2); can(gx - 16, 8, 0)
    sh(gx + 36, gy - 5, 15); g.save(); g.translate(gx + 36, gy - 5)
    g.fillStyle = OL; g.beginPath(); g.ellipse(0, -6.6, 12.4, 6.2, 0, 0, 7); g.fill(); g.fillRect(-12.4, -7, 24.8, 7)
    g.beginPath(); g.ellipse(0, 0, 12.4, 4.4, 0, 0, 7); g.fill()
    g.fillStyle = "#e0a72f"; g.fillRect(-11, -7, 22, 6.6); g.beginPath(); g.ellipse(0, -.6, 11, 3.6, 0, 0, 7); g.fill()
    g.fillStyle = "#ffd45a"; g.beginPath(); g.ellipse(0, -7, 11, 5, 0, 0, 7); g.fill()
    g.fillStyle = "#e0a72f"
    for h in [[-4, -7.6, 1.8, 1], [4, -6, 1.4, .8], [0, -9.4, 1, .6], [6, -8.8, 1.1, .7]]:
        g.beginPath(); g.ellipse(h[0], h[1], h[2], h[3], 0, 0, 7); g.fill()
    for h in [[-7, -3], [2, -2.2], [8, -3.6]]:
        g.beginPath(); g.ellipse(h[0], h[1], 1.5, 1.1, 0, 0, 7); g.fill()
    g.restore()
    sh(gx + 64, gy - 4, 15); g.save(); g.translate(gx + 64, gy - 4)
    g.fillStyle = OL; g.beginPath(); g.moveTo(-10.6, -21); g.quadraticCurveTo(-14, -10, -10.6, 1); g.lineTo(10.6, 1); g.quadraticCurveTo(14, -10, 10.6, -21); g.closePath(); g.fill()
    g.fillStyle = "#9a5f2c"; g.beginPath(); g.moveTo(-9, -20); g.quadraticCurveTo(-12.4, -10, -9, 0); g.lineTo(9, 0); g.quadraticCurveTo(12.4, -10, 9, -20); g.closePath(); g.fill()
    g.save(); g.clip(); g.strokeStyle = "#744420"; g.lineWidth = 1; g.beginPath()
    for x in (-5, 0, 5):
        g.moveTo(x, -21); g.lineTo(x, 1)
    g.stroke()
    g.fillStyle = "rgba(255,255,255,.16)"; g.fillRect(-12, -21, 4, 22)
    for y in (-16, -3):
        g.fillStyle = "#3a3f4a"; g.fillRect(-14, y, 28, 3); g.fillStyle = "#6e7686"; g.fillRect(-14, y, 28, 1)
    g.restore()
    g.fillStyle = OL; g.beginPath(); g.ellipse(0, -20.6, 9.6, 3.2, 0, 0, 7); g.fill(); g.fillStyle = "#c98a4e"; g.beginPath(); g.ellipse(0, -20.8, 8.2, 2.4, 0, 0, 7); g.fill()
    g.fillStyle = OL; g.fillRect(-2.2, -9, 4.4, 5.4); g.fillStyle = "#d6b25a"; g.fillRect(-1.2, -8, 2.4, 3.6)
    g.restore()

    def mush(x, y, k, c1, c2, gl_):
        sh(x, y, 7 * k); g.save(); g.translate(x, y); g.scale(k, k)
        pl = 1 + sin(t * .07 + x) * .12
        gg = g.createRadialGradient(0, -7, 1, 0, -7, 16 * pl); gg.addColorStop(0, gl_); gg.addColorStop(1, "rgba(0,0,0,0)")
        g.fillStyle = gg; g.beginPath(); g.arc(0, -7, 16 * pl, 0, 7); g.fill()
        g.fillStyle = OL; g.fillRect(-2.8, -7, 5.6, 7.4); g.fillStyle = "#f3ead0"; g.fillRect(-1.6, -7, 3.2, 7)
        g.fillStyle = OL; g.beginPath(); g.ellipse(0, -8, 7.4, 5.6, 0, PI, 0); g.closePath(); g.fill()
        g.fillStyle = c1; g.beginPath(); g.ellipse(0, -8, 6, 4.2, 0, PI, 0); g.closePath(); g.fill()
        g.fillStyle = c2
        for o_ in [[-2.6, -10, 1.2], [1.8, -11, 1], [3.2, -8.6, .8]]:
            g.beginPath(); g.arc(o_[0], o_[1], o_[2], 0, 7); g.fill()
        g.restore()
    mush(gx - 38, gy - 4, .95, "#39c2b0", "#c8fff4", "rgba(80,255,220,.5)")
    mush(gx + 86, gy - 4, .85, "#ff7aa8", "#ffe0ec", "rgba(255,120,190,.45)")
    if t % 60 < 30:
        sparkle(gx - 22, gy - 34 - ((t % 60) / 2), 3, 1 - (t % 60) / 30)
    g.restore()


def pole_draw(px, gy):
    g.save()
    g.fillStyle = OL; g.fillRect(px - 3.6, 64, 7.2, gy - 64)
    g.fillStyle = "#d9a25b"; g.fillRect(px - 2.4, 64, 4.8, gy - 64)
    g.fillStyle = "#f1c98a"; g.fillRect(px - 2.4, 64, 1.6, gy - 64)
    g.fillStyle = "#a8672e"
    for y in range(74, gy - 12, 16):
        g.fillRect(px - 2.4, y, 4.8, 2.2)
    g.fillStyle = OL; g.fillRect(px - 6, gy - 8, 12, 8); g.fillStyle = "#b8813f"; g.fillRect(px - 4.8, gy - 6.8, 9.6, 6.8)
    g.fillStyle = "#d9a25b"; g.fillRect(px - 4.8, gy - 6.8, 9.6, 2)
    g.restore()


def draw_goal(gx):
    t, gy, px = S.tick, 10 * T, gx + 16
    amp = 1.9 if S.state == "clear" else 1
    pole_draw(px, gy)
    if S.GS:
        for m in S.GS.marks:
            g.fillStyle = "#8a5a2b"; g.strokeStyle = OL; g.lineWidth = .8
            g.beginPath(); g.arc(px - 3.6, m, 2.1, -PI / 2, PI / 2); g.fill(); g.stroke()
    x0, y0, W2, H2, N = px + 2, 70, 56, 40, 28
    sw = W2 / N

    def wave(i):
        return sin(t * .085 - i * .42) * 3.2 * amp * (i / N) + sin(t * .05 - i * .2) * 1.2 * amp * (i / N)
    pts = []
    for i in range(N):
        sx = x0 + i * sw
        dy = wave(i)
        u = i / N
        c = (u - .74) / .26 * H2 * .5 if u > .74 else 0
        slp = (wave(i + 1) - wave(i)) * 2
        parts = [[0, H2 / 2 - c], [H2 / 2 + c, H2]] if c > 0 else [[0, H2]]
        for pr in parts:
            g.save(); g.beginPath(); g.rect(sx, y0 + dy + pr[0], sw + .6, pr[1] - pr[0]); g.clip()
            gingham(sx, y0 + dy, sw + .6, H2, i * sw, 0, .78)
            g.fillStyle = f"rgba(20,0,0,{max(0, min(.34, .1 + slp * .09))})"; g.fillRect(sx, y0 + dy, sw + .6, H2)
            if slp < -.6:
                g.fillStyle = f"rgba(255,255,255,{min(.25, -slp * .06)})"; g.fillRect(sx, y0 + dy, sw + .6, H2)
            g.restore()
        pts.append([sx, dy, c])
    g.strokeStyle = OL; g.lineWidth = 2; g.lineJoin = "round"; g.lineCap = "round"
    g.beginPath()
    for i, q in enumerate(pts):
        (g.lineTo if i else g.moveTo)(q[0], y0 + q[1])
    g.stroke()
    g.beginPath()
    for i, q in enumerate(pts):
        yy = y0 + q[1] + H2 - (H2 / 2 - q[2] if q[2] > 0 else 0)
        (g.lineTo if i else g.moveTo)(q[0], yy)
    g.stroke()
    q = pts[N - 1]
    e = y0 + q[1]
    g.beginPath(); g.moveTo(q[0], e + H2 / 2 - q[2]); g.lineTo(q[0] - sw * 4, e + H2 / 2); g.lineTo(q[0], e + H2 / 2 + q[2]); g.stroke()
    g.beginPath(); g.moveTo(x0, y0 - 1); g.lineTo(x0, y0 + H2 + 1); g.stroke()
    k = 7
    dy = wave(k) + sin(t * .085 - k * .42 + .6) * .6
    g.fillStyle = "rgba(255,246,220,.92)"; g.beginPath(); g.arc(x0 + k * sw + 8, y0 + dy + H2 / 2, 14.5, 0, 7); g.fill()
    g.strokeStyle = OL; g.lineWidth = 1.4; g.stroke(); bread_face(x0 + k * sw + 8, y0 + dy + H2 / 2 + 2, 1)
    g.lineCap = "butt"
    cookie_art(px, 60 + sin(t * .07) * 1.2, 7.4)
    sparkle(px - 14, 66, 5, .55 + .45 * sin(t * .11)); sparkle(px + W2 + 8, 86, 4, .55 + .45 * sin(t * .13 + 2))
    sparkle(px + 30, 58, 3.4, .55 + .45 * sin(t * .1 + 4))


def bite_overlay():
    P, GS = S.P, S.GS
    s = 1.5 if P.big else 1
    k = s * .82
    mx, my = P.x + P.w / 2 + 6.4 * k, mouth_y() + sin(S.tick * 1.7) * .4
    o = max(0, sin(GS.t * .75)) * 1.7 if GS.ph == 0 else 0
    g.save(); g.translate(mx, my); g.scale(k, k); g.lineJoin = "round"
    g.fillStyle = "#fffaf0"; g.strokeStyle = OL; g.lineWidth = .8
    rr(-4.7, -3.6 - o, 4.3, 3.8, 1.2); g.fill(); g.stroke(); rr(.4, -3.6 - o, 4.3, 3.8, 1.2); g.fill(); g.stroke()
    rr(-3.8, .1 + o, 3.5, 2.7, 1); g.fill(); g.stroke(); rr(.3, .1 + o, 3.5, 2.7, 1); g.fill(); g.stroke()
    g.strokeStyle = "#b03a50"; g.lineWidth = 1.05; g.lineCap = "round"
    g.beginPath(); g.moveTo(-6.4, -.3); g.quadraticCurveTo(0, -4.8 - o, 6.4, -.3); g.stroke()
    g.beginPath(); g.moveTo(-6.4, -.3); g.quadraticCurveTo(0, 4.6 + o, 6.4, -.3); g.stroke()
    g.restore()


def draw_key(x, y, k, rot, glow_):
    tick = S.tick
    g.save(); g.translate(x, y)
    if glow_:
        pl = 1 + sin(tick * .14) * .15
        glow(0, 0, 2, 22 * pl, "255,240,150", .7)
        if tick % 50 < 14:
            sparkle(8, -9, 5, 1 - (tick % 50) / 14)
    g.rotate(rot); g.scale(k, k); g.lineJoin = "round"; g.lineCap = "round"
    g.strokeStyle = OL; g.lineWidth = 5.6; g.beginPath(); g.moveTo(-2, 0); g.lineTo(11, 0); g.stroke()
    g.strokeStyle = "#ffd84d"; g.lineWidth = 2.8; g.beginPath(); g.moveTo(-2, 0); g.lineTo(11, 0); g.stroke()
    g.fillStyle = OL; g.fillRect(6.4, 0, 3.6, 5.6); g.fillRect(10.2, 0, 2.6, 4.4)
    g.fillStyle = "#ffd84d"; g.fillRect(7.3, 0, 1.8, 4.4); g.fillRect(11, 0, 1, 3.2)
    g.fillStyle = OL; g.beginPath(); g.arc(-7.6, 0, 6.2, 0, 7); g.fill()
    g.fillStyle = "#ffd84d"; g.beginPath(); g.arc(-7.6, 0, 4.4, 0, 7); g.fill()
    g.fillStyle = "#b98a12"; g.beginPath(); g.arc(-7.6, 0, 1.9, 0, 7); g.fill()
    g.fillStyle = "rgba(255,255,255,.7)"; g.beginPath(); g.ellipse(-9.4, -2, 1.2, .8, -.6, 0, 7); g.fill()
    g.restore()


def draw_mouth_key():
    P, FS = S.P, S.FS
    k = (1.5 if P.big else 1) * .82
    mx, my = P.x + P.w / 2 + P.face * 5.5 * k, mouth_y() + .5
    rot = 0
    if FS.ph == 1:
        rot = sin(min(FS.t, 30) * .45) * .5 * (1 if FS.t < 30 else 0)
    g.save(); g.translate(mx + P.face * 6, my - 1); g.scale(P.face, 1); draw_key(0, 0, .78 * (1.3 if P.big else 1), rot, False); g.restore()


def draw_cage():
    C, P, FS, t = S.CAGE, S.P, S.FS, S.tick
    cx, gy, w, h = C.cx, C.gy, 56, 64
    L, R_, top = cx - w / 2, cx + w / 2, gy - h
    g.save(); g.lineJoin = "round"; g.lineCap = "round"
    g.fillStyle = "rgba(0,0,0,.25)"; g.beginPath(); g.ellipse(cx, gy + 1, w / 2 + 8, 4, 0, 0, 7); g.fill()
    g.fillStyle = "rgba(40,14,10,.55)"; g.fillRect(L + 3, top + 6, w - 6, h - 9)
    q = C.q
    q.big, q.w, q.h = P.big, P.w, P.h
    q.x = cx + q.dx - q.w / 2
    if not (FS and FS.ph >= 2):
        q.y = gy - q.h - (abs(sin(t * .22)) * 4 if ((t + 30) % 150) < 36 else 0)
        draw_as(q, PINKPAL)

    def bar(x, y0, y1):
        g.strokeStyle = OL; g.lineWidth = 4.4; g.beginPath(); g.moveTo(x, y0); g.lineTo(x, y1); g.stroke()
        g.strokeStyle = "#8f97a6"; g.lineWidth = 2.4; g.beginPath(); g.moveTo(x, y0); g.lineTo(x, y1); g.stroke()
        g.strokeStyle = "#d6dce8"; g.lineWidth = .9; g.beginPath(); g.moveTo(x - .7, y0 + 1); g.lineTo(x - .7, y1 - 1); g.stroke()
    dw = 22
    hx, dL = L + 4 + dw, L + 4
    x = hx + 8
    while x <= R_ - 6:
        bar(x, top + 6, gy - 5)
        x += 8
    sc = 1 - C.open * .86
    g.save(); g.translate(hx, 0); g.scale(sc, 1); g.translate(-hx, 0)
    g.strokeStyle = OL; g.lineWidth = 4.4; g.strokeRect(dL + 1, top + 10, dw - 2, h - 18)
    g.strokeStyle = "#8f97a6"; g.lineWidth = 2.4; g.strokeRect(dL + 1, top + 10, dw - 2, h - 18)
    x = dL + 8
    while x < hx - 2:
        bar(x, top + 10, gy - 8)
        x += 7
    g.restore()
    g.fillStyle = OL
    for y in (top + 16, gy - 16):
        g.fillRect(hx - 2, y, 4, 6)

    def post(x):
        g.strokeStyle = OL; g.lineWidth = 6.6; g.beginPath(); g.moveTo(x, top + 4); g.lineTo(x, gy); g.stroke()
        g.strokeStyle = "#a9b1c0"; g.lineWidth = 4; g.beginPath(); g.moveTo(x, top + 4); g.lineTo(x, gy); g.stroke()
        g.strokeStyle = "#eef2fa"; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x - 1.1, top + 6); g.lineTo(x - 1.1, gy - 2); g.stroke()
    post(L + 2); post(R_ - 2)
    g.fillStyle = OL; g.fillRect(L - 3, gy - 6, w + 6, 6); g.fillStyle = "#6b5a4a"; g.fillRect(L - 2, gy - 5, w + 4, 4)
    g.fillStyle = "#8d7a66"; g.fillRect(L - 2, gy - 5, w + 4, 1.4)
    g.fillStyle = OL; g.fillRect(L - 2, top + 2, w + 4, 7); g.fillStyle = "#a9b1c0"; g.fillRect(L - 1, top + 3, w + 2, 4.4)
    g.fillStyle = "#eef2fa"; g.fillRect(L - 1, top + 3, w + 2, 1.3)
    g.beginPath(); g.moveTo(L - 1, top + 3); g.quadraticCurveTo(cx, top - 20, R_ + 1, top + 3); g.closePath(); g.fillStyle = OL; g.fill()
    g.beginPath(); g.moveTo(L + 2, top + 3); g.quadraticCurveTo(cx, top - 15, R_ - 2, top + 3); g.closePath(); g.fillStyle = "#8f97a6"; g.fill()
    g.beginPath(); g.moveTo(L + 8, top + 2); g.quadraticCurveTo(cx - 8, top - 9, cx - 2, top - 10); g.strokeStyle = "rgba(255,255,255,.55)"; g.lineWidth = 1.6; g.stroke()
    g.strokeStyle = OL; g.lineWidth = 4; g.beginPath(); g.arc(cx, top - 16, 4.6, 0, 7); g.stroke()
    g.strokeStyle = "#d6dce8"; g.lineWidth = 1.8; g.beginPath(); g.arc(cx, top - 16, 4.6, 0, 7); g.stroke()
    lx, ly = dL + 1, gy - 28
    if C.lock == 1:
        g.fillStyle = OL; g.fillRect(lx - 7.4, ly - 2, 14.8, 12.6); g.fillStyle = "#ffd84d"; g.fillRect(lx - 6, ly - .6, 12, 9.8)
        g.fillStyle = "#fff3a0"; g.fillRect(lx - 6, ly - .6, 12, 2.4)
        g.strokeStyle = OL; g.lineWidth = 3.4; g.beginPath(); g.arc(lx, ly - 2, 4.6, PI, 0); g.stroke()
        g.strokeStyle = "#d6dce8"; g.lineWidth = 1.6; g.beginPath(); g.arc(lx, ly - 2, 4.6, PI, 0); g.stroke()
        g.fillStyle = OL; g.beginPath(); g.arc(lx, ly + 4, 1.5, 0, 7); g.fill(); g.fillRect(lx - .7, ly + 4, 1.4, 3.4)
    elif C.lock == 2:
        k = C.lt
        g.save(); g.translate(lx + k * .5, ly + 4 + k * k * .22); g.rotate(k * .11)
        g.fillStyle = OL; g.fillRect(-7.4, -6, 14.8, 12.6); g.fillStyle = "#ffd84d"; g.fillRect(-6, -4.6, 12, 9.8)
        g.strokeStyle = OL; g.lineWidth = 3.4; g.beginPath(); g.arc(-2, -6, 4.6, PI, 0); g.stroke()
        g.restore()
    g.restore()
    if FS and FS.ph >= 2:
        draw_as(q, PINKPAL)


# ======================================================================= frame
def iris(cx, cy, r):
    g.save(); g.fillStyle = "#000"; g.beginPath(); g.rect(0, 0, VW, VH); g.arc(cx, cy, max(1, r), 0, PI * 2, True); g.fill("evenodd"); g.restore()


def draw_fx():
    g.textBaseline = "alphabetic"
    for f in S.fx:
        k = f.k
        if k == "txt":
            g.globalAlpha = min(1, f.life / 20); g.font = "14px 'Bagel Fat One'"; g.textAlign = "center"
            g.fillStyle = "#000"; g.fillText(f.s, f.x + 1, f.y + 1); g.fillStyle = "#fff8b0"; g.fillText(f.s, f.x, f.y)
        elif k == "spark":
            g.globalAlpha = max(0, f.life / 22); g.fillStyle = f.c; g.fillRect(f.x - 2, f.y - 2, 4, 4)
        elif k == "wjring":
            q = 12 - f.life
            g.globalAlpha = min(1, f.life / 8); g.strokeStyle = "#fff3d6"; g.lineWidth = 2.4; g.lineCap = "round"
            a0 = PI if f.d > 0 else 0
            for i in range(3):
                r = q * 2.6 + 5 + i * 4
                g.beginPath(); g.arc(f.x, f.y, r, a0 - .9 + (i - 1) * .15, a0 + .9 - (i - 1) * .15); g.stroke()
            g.globalAlpha = 1; g.lineCap = "butt"
        elif k == "shock":
            q = 20 - f.life
            g.globalAlpha = min(1, f.life / 14); g.strokeStyle = "#fff3d6"; g.lineWidth = 3
            g.beginPath(); g.ellipse(f.x, f.y - 2, q * 3.4 + 6, q * .8 + 2, 0, 0, 7); g.stroke()
            g.globalAlpha *= .5; g.strokeStyle = "#e7d3a8"; g.lineWidth = 2
            g.beginPath(); g.ellipse(f.x, f.y - 2, q * 2.2 + 4, q * .5 + 1.5, 0, 0, 7); g.stroke()
        elif k == "heart":
            g.globalAlpha = min(1, f.life / 25); g.save(); g.translate(f.x + sin(f.ph + f.life * .12) * 3, f.y); g.scale(f.s, f.s)
            g.beginPath(); g.moveTo(0, 4); g.bezierCurveTo(-7, -1, -4.5, -7, 0, -3); g.bezierCurveTo(4.5, -7, 7, -1, 0, 4)
            g.fillStyle = "#ff5d8f"; g.fill(); g.strokeStyle = OL; g.lineWidth = 1; g.stroke()
            g.fillStyle = "rgba(255,255,255,.6)"; g.beginPath(); g.arc(-2.4, -2.4, 1, 0, 7); g.fill(); g.restore()
        elif k == "crumb":
            g.globalAlpha = min(1, f.life / 14); g.fillStyle = f.c; g.fillRect(f.x - 1.2, f.y - 1.2, 2.6, 2.6)
        elif k == "conf":
            g.globalAlpha = min(1, f.life / 20); g.save(); g.translate(f.x, f.y); g.rotate(f.r); g.fillStyle = f.c; g.fillRect(-3, -1.6, 6, 3.2); g.restore()
        elif k == "puff":
            q = 1 - f.life / 30
            g.globalAlpha = max(0, f.life / 30) * .85; g.fillStyle = "#f2f2f2"; g.strokeStyle = "rgba(120,120,120,.5)"; g.lineWidth = .8
            g.beginPath(); g.arc(f.x, f.y, 2.5 + q * 5, 0, 7); g.fill(); g.stroke()
        elif k == "ring":
            g.globalAlpha = f.life / 16; g.strokeStyle = "#ffe887"; g.lineWidth = 3; g.beginPath(); g.arc(f.x, f.y, (16 - f.life) * 2 + 6, 0, 7); g.stroke()
        elif k == "coin":
            g.globalAlpha = min(1, f.life / 10)
            w = abs(cos(f.life * .5)) * 7 + 1
            g.fillStyle = "#ffd84d"; g.beginPath(); g.ellipse(f.x, f.y, w, 9, 0, 0, 7); g.fill()
        g.globalAlpha = 1


def draw_world(hide_free=False):
    """Background plus everything in the level, in world space."""
    tick, cam = S.tick, S.cam
    g.setTransform(RS, 0, 0, RS, 0, 0)
    background()
    g.save()
    shk = S.shk
    g.translate(-round(cam) + ((rnd() - .5) * shk * .9 if shk > 0 else 0),
                ((rnd() - .5) * shk * .9 if shk > 0 else 0) + (40 if S.state == "title" else 0))
    if S.TH == 2:
        soup()
    x0 = math.floor(cam / T)
    x1 = min(S.W - 1, x0 + 17)
    grid, bumps = S.grid, S.bumps
    for ty in range(H):
        rowv = grid[ty]
        for tx in range(max(0, x0), x1 + 1):
            v = rowv[tx]
            if not v:
                continue
            py = ty * T
            b = bumps.get((tx, ty))
            if b:
                py -= b if b > 4 else 8 - b
            g.drawImageAt(tile_img(v, tx, ty), tx * T, py)
    for k in list(bumps):
        bumps[k] -= 1
        if bumps[k] <= 0:
            del bumps[k]
    for c in S.coins:
        if c.got or c.x < cam - 20 or c.x > cam + VW + 20:
            continue
        w = abs(cos(tick * .08 + c.x)) * 6 + 2
        y = c.y + sin(tick * .06 + c.x) * 2
        g.fillStyle = "#7a4a08"; g.beginPath(); g.ellipse(c.x, y, w + 1.6, 9.6, 0, 0, 7); g.fill()
        g.fillStyle = "#e0a626"; g.beginPath(); g.ellipse(c.x, y, w, 8, 0, 0, 7); g.fill()
        g.fillStyle = "#ffd84d"; g.beginPath(); g.ellipse(c.x - .5, y - 1, max(1, w - 2), 6, 0, 0, 7); g.fill()
        g.fillStyle = "#fff6c2"; g.fillRect(c.x - 1, y - 5, 2, 4)
    for it in S.items:
        cx, cy = it.x + 11, it.y + 11
        pl = 1 + sin(tick * .12) * .12
        glow(cx, cy, 3, 26 * pl, "255,240,150", .55)
        (pizza_art if it.t == "pizza" else cookie_art)(cx, cy, 11)
    if S.GOAL < 900 and cam - 120 < S.GOAL * T < cam + VW + 120:
        draw_goal(S.GOAL * T)
    GS = S.GS
    if GS and cam - 120 < GS.pic < cam + VW + 120:
        (draw_feast if S.LV == 1 else draw_picnic)(GS.pic)
        draw_as(GS.P2, PINKPAL)
    if S.CAGE and cam - 100 < S.CAGE.cx < cam + VW + 100:
        draw_cage()
    for e in S.enemies:
        if hide_free and e.free:
            continue
        draw_enemy(e)
    for s in S.shots:
        g.fillStyle = "rgba(255,140,30,.8)"; g.beginPath(); g.ellipse(s.x + 5 - s.vx * 1.2, s.y + 5, 7, 4, 0, 0, 7); g.fill()
        cookie_art(s.x + 5, s.y + 5, 5)
    B = S.boss
    if B and (not B.dead or ((tick >> 2) % 2 and (not S.CAGE or S.bossT < 56))):
        draw_boss()
    for b in S.bshots:
        sk = b.k == "seek"
        cx, cy, vx, vy = b.x + 5, b.y + 5, b.vx or 0, b.vy or 0
        for i in range(4, 0, -1):
            g.globalAlpha = .42 - i * .07; g.fillStyle = "#ff3d6e" if sk else "#ff8a2a"
            g.beginPath(); g.arc(cx - vx * i * 1.7, cy - vy * i * 1.7, 6.4 - i * 1.15, 0, 7); g.fill()
        g.globalAlpha = 1
        g.fillStyle = OL; g.beginPath(); g.arc(cx, cy, 7.4, 0, 7); g.fill()
        g.fillStyle = "#ff3d6e" if sk else "#ff7a1f"; g.beginPath(); g.arc(cx, cy, 6.2, 0, 7); g.fill()
        g.fillStyle = "#ffb0c4" if sk else "#ffc24d"; g.beginPath(); g.arc(cx - .6, cy - .6, 3.7, 0, 7); g.fill()
        g.fillStyle = "#fff6c8"; g.beginPath(); g.arc(cx - 1.3, cy - 1.4, 1.7, 0, 7); g.fill()
        if sk:
            g.fillStyle = OL; g.beginPath(); g.moveTo(cx + vx * .9 - 2.4, cy + vy * .9 - 4.6); g.lineTo(cx + vx * .9, cy + vy * .9 - 8)
            g.lineTo(cx + vx * .9 + 2.4, cy + vy * .9 - 4.6); g.fill()
    draw_player()
    P = S.P
    if P and P.sl == 1 and GS:
        bite_overlay()
    K = S.KEYO
    if K and not K.got:
        draw_key(K.x, K.y + sin(K.t * .1) * (2.5 if K.vy == 0 else 0), 1.25, sin(K.t * .05) * .25, True)
    if S.FS and S.FS.ph <= 1 and S.FS.hold != 0:
        draw_mouth_key()
    draw_fx()
    g.restore()


def draw_free_enemies():
    """Enemies being thrown around on the title screen fly above the menu."""
    g.save(); g.setTransform(RS, 0, 0, RS, 0, 0); g.translate(-round(S.cam), 40)
    for e in S.enemies:
        if e.free:
            draw_enemy(e)
    g.restore()


def draw_overlays():
    st = S.state
    g.setTransform(RS, 0, 0, RS, 0, 0)
    if st not in ("title",):
        hud()
    if st == "clear" and S.FS and S.CAGE:
        k = min(1, S.clearT / 44)
        iris(S.CAGE.cx - 30 - round(S.cam), S.CAGE.gy - 14, (1 - k * k) * 620 + 1)
    if st == "clear" and S.GS:
        k = min(1, S.clearT / 44)
        iris(S.GS.pic - 7 - round(S.cam), S.GS.gy - 14, (1 - k * k) * 620 + 1)
    if st == "play" and S.irisO < 30 and S.P:
        k = S.irisO / 30
        iris(S.P.x + S.P.w / 2 - round(S.cam), S.P.y + S.P.h / 2, 1 + k * k * 620)
    if st == "card":
        draw_card()


def draw_card():
    C, t = S.CARD, S.CARD.t
    a = min(1, t / 8)
    out = max(0, min(1, (t - (C.len - 10)) / 10))
    g.fillStyle = "#000"; g.fillRect(0, 0, VW, VH)

    def band(y):
        for i in range(-2, VW // 16 + 2):
            for j in range(2):
                x = i * 16 + ((t * .6) % 16) * (1 if y < 100 else -1)
                g.fillStyle = "#e8452f" if (i + j) & 1 else "#fff3d6"; g.fillRect(x, y + j * 8, 16, 8)
        g.fillStyle = OL; g.fillRect(0, y + 16 if y < 100 else y - 3, VW, 3)
    band(0); band(VH - 16)
    g.save(); g.globalAlpha = 1 - out; g.textAlign = "center"; g.textBaseline = "middle"
    sl = (1 - (1 - a) ** 3) * 22
    g.fillStyle = "#fff3d6"; g.font = "800 15px Sniglet"; g.letterSpacing = 4
    g.fillText(C.no, VW / 2, 96 - 22 + sl)
    g.letterSpacing = 0
    g.font = "40px 'Bagel Fat One'"; g.lineWidth = 6; g.strokeStyle = OL; g.lineJoin = "round"
    g.strokeText(C.name, VW / 2, 136 - 22 + sl); g.fillStyle = "#ffd84d"; g.fillText(C.name, VW / 2, 136 - 22 + sl)
    g.fillStyle = "#e8452f"; g.fillRect(VW / 2 - 70, 170, 140, 3)
    bob = abs(sin(t * .16)) * 5
    fy = 262
    sv, scam = S.P, S.cam
    S.cam = 0
    big = bool(sv and sv.big)
    S.P = O_(x=VW / 2 - 74 - 11, y=0, w=28 if big else 22, h=42 if big else 28, vx=0, vy=0, ground=True, face=1,
             big=big, fire=bool(sv and sv.fire), inv=0, duck=0, mk=1, mt=0)
    S.P.y = fy - S.P.h - bob
    draw_player()
    S.P, S.cam = sv, scam
    g.fillStyle = "rgba(255,255,255,.14)"; g.beginPath(); g.ellipse(VW / 2 - 74, fy + 1, 17 - bob, 3.4, 0, 0, 7); g.fill()
    g.textAlign = "left"
    g.fillStyle = "#fff3d6"; g.font = "26px 'Bagel Fat One'"; g.fillText("×", VW / 2 - 30, fy - 18)
    g.fillStyle = "#ffd84d"; g.font = "44px 'Bagel Fat One'"; g.fillText(str(max(0, S.lives)), VW / 2 - 6, fy - 18)
    g.fillStyle = "#b9a98f"; g.font = "800 11px Sniglet"; g.letterSpacing = 3
    g.fillText("LIFE LEFT" if S.lives == 1 else "LIVES LEFT", VW / 2 - 30, fy + 6)
    g.letterSpacing = 0
    g.textAlign = "center"
    if C.sub:
        g.fillStyle = "#d8c9ac"; g.font = "800 13px Sniglet"; g.fillText(C.sub, VW / 2, 326)
    g.restore()


def hud():
    P, tick = S.P, S.tick
    g.textBaseline = "top"
    F = "'Bagel Fat One'"

    def t(s, x, a, y, sz=14):
        g.font = f"{sz}px {F}"; g.textAlign = a
        g.fillStyle = "rgba(0,0,0,.55)"; g.fillText(s, x + 1, y + 1); g.fillStyle = "#fff"; g.fillText(s, x, y)
    g.fillStyle = OL; g.beginPath(); g.ellipse(18, 18, 7.6, 8.6, 0, 0, 7); g.fill()
    g.fillStyle = "#e0a626"; g.beginPath(); g.ellipse(18, 18, 6, 7, 0, 0, 7); g.fill()
    g.fillStyle = "#ffd84d"; g.beginPath(); g.ellipse(17.4, 17.2, 4, 5.2, 0, 0, 7); g.fill()
    g.fillStyle = "#fff6c2"; g.fillRect(16, 13, 1.6, 4)
    t("x " + str(S.coinsN).zfill(2), 30, "left", 10)
    t("SCORE " + str(S.score).zfill(6), VW / 2, "center", 10)
    t("LIVES " + str(max(0, S.lives)), VW - 12, "right", 10)
    t("TIME " + str(max(0, math.ceil(S.time))), VW - 12, "right", 28)
    t(NAMES[S.CI], 12, "left", 30, 11)
    if P and S.state in ("play", "dead"):
        lkd = P.ohd > 0
        h = P.ohd / OHD if lkd else min(1, (P.glt or 0) / OHM)
        act = lkd or h > .02
        S.HA += ((1 if act else 0) - S.HA) * .12
        if S.HA > .02:
            bw, bh, bx = 40, 5, 84
            by = VH - 27 - bh / 2
            g.save(); g.globalAlpha = S.HA * .85
            rr(bx - 1.5, by - 1.5, bw + 3, bh + 3, 4); g.fillStyle = "rgba(0,0,0,.5)"; g.fill()
            if h > 0:
                g.save(); rr(bx, by, bw, bh, 2.5); g.clip()
                g.fillStyle = ("#ff3b2a" if (tick >> 2) & 1 else "#c21f14") if lkd else ("#ffd84d" if h < .5 else ("#ff9a2a" if h < .8 else "#ff4a2a"))
                g.fillRect(bx, by, bw * h, bh); g.restore()
            g.font = f"9px {F}"; g.textAlign = "left"; g.textBaseline = "middle"
            lb = f"{P.ohd / 60:.1f}s" if lkd else "HEAT"
            g.fillStyle = "rgba(0,0,0,.5)"; g.fillText(lb, bx + bw + 5, by + bh / 2 + .8)
            g.fillStyle = "#ffb0a0" if lkd else "#fff"; g.fillText(lb, bx + bw + 4, by + bh / 2)
            g.restore(); g.textBaseline = "top"
    if P and P.fire:
        t("FIRE READY: PRESS F", VW / 2, "center", 28, 11)
    if P and S.state in ("play", "dead", "clear"):
        cx, cy, r = 27, VH - 27, 13
        rem = max(0, P.rcd or 0)
        ready = rem <= 0
        dn = sin(tick * 2.2) * 2 if P.rdeny > 0 else 0
        g.save(); g.translate(dn, 0)
        g.fillStyle = "rgba(0,0,0,.45)"; g.beginPath(); g.arc(cx, cy, r + 2.5, 0, 7); g.fill()
        g.fillStyle = "#8fdc63" if ready else "#3a2a22"; g.beginPath(); g.arc(cx, cy, r, 0, 7); g.fill()
        if not ready:
            g.fillStyle = "#ffce54"; g.beginPath(); g.moveTo(cx, cy); g.arc(cx, cy, r - 1.6, -PI / 2, -PI / 2 + PI * 2 * (1 - rem / ROLLCD)); g.closePath(); g.fill()
            g.fillStyle = "#3a2a22"; g.beginPath(); g.arc(cx, cy, r - 5.4, 0, 7); g.fill()
        else:
            g.fillStyle = f"rgba(255,255,255,{.25 + .2 * sin(tick * .12)})"; g.beginPath(); g.arc(cx - 2, cy - 3, r - 6, 0, 7); g.fill()
        g.strokeStyle = "#ff6a5a" if P.rdeny > 0 else OL; g.lineWidth = 1.6; g.beginPath(); g.arc(cx, cy, r, 0, 7); g.stroke()
        g.textBaseline = "middle"; g.textAlign = "center"; g.font = f"13px {F}"
        lab = "E" if ready else str(math.ceil(rem / 60))
        g.fillStyle = OL; g.fillText(lab, cx + .6, cy + 1.4); g.fillStyle = "#fff" if ready else "#ffe9ae"; g.fillText(lab, cx, cy + .6)
        if P.rflash > 0:
            k = 1 - P.rflash / 45
            g.globalAlpha = 1 - k; g.strokeStyle = "#fff"; g.lineWidth = 2; g.beginPath(); g.arc(cx, cy, r + 2 + k * 12, 0, 7); g.stroke(); g.globalAlpha = 1
        g.restore(); g.textBaseline = "top"
        t("ROLL", cx + r + 7, "left", cy - 6, 11)
    B = S.boss
    if B and not B.dead:
        bw, bh = 200, 7
        bx, by = VW / 2 - bw / 2, 62
        f = max(0, B.hp / 6)
        ch = max(f, S.bossDisp / 6)
        t("GRAND CHILI", VW / 2, "center", 45, 12)
        g.fillStyle = "rgba(0,0,0,.35)"; rr(bx - 2, by - 2, bw + 4, bh + 4, 5.5); g.fill()
        g.fillStyle = "rgba(22,10,8,.88)"; rr(bx, by, bw, bh, 3.5); g.fill()
        g.save(); rr(bx, by, bw, bh, 3.5); g.clip()
        g.fillStyle = "#ffd0c8"; g.fillRect(bx, by, bw * ch, bh)
        gr = g.createLinearGradient(0, by, 0, by + bh); gr.addColorStop(0, "#ff7a63"); gr.addColorStop(1, "#c22f28")
        g.fillStyle = gr; g.fillRect(bx, by, bw * f, bh)
        g.fillStyle = "rgba(255,255,255,.35)"; g.fillRect(bx, by + 1, bw * f, 1.4)
        g.restore()
        g.strokeStyle = "rgba(255,255,255,.4)"; g.lineWidth = 1; rr(bx, by, bw, bh, 3.5); g.stroke()


from .game import O as O_  # noqa: E402  (used by draw_card's stand-in Crumb)
