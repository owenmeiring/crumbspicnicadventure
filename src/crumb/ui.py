"""In-engine menus: title screen, how to play, options, pause, game over and the win screen.

Everything is drawn with the same art pipeline as the game and works with
keyboard, gamepad or mouse.
"""

import math

from . import art
from .canvas import offscreen
from .game import NAMES, ROLLNAMES, S, VH, VW

OL = "#2b1608"
CREAM = "#fff3d6"
RED = "#e8452f"
sin = math.sin


class Item:
    def __init__(self, label, ok=None, lr=None, value=None):
        self.label, self.ok, self.lr, self.value = label, ok, lr, value

    def text(self):
        return self.label() if callable(self.label) else self.label

    def val(self):
        return self.value() if self.value else None


class Menu:
    def __init__(self, items, back=None):
        self.items = items
        self.sel = 0
        self.rects = []
        self.back = back
        self.pulse = 0

    def nav(self, action, sfx):
        if action in ("up", "down"):
            self.sel = (self.sel + (1 if action == "down" else -1)) % len(self.items)
            sfx("move")
        elif action in ("left", "right"):
            it = self.items[self.sel]
            if it.lr:
                it.lr(1 if action == "right" else -1)
                sfx("toggle")
        elif action == "ok":
            it = self.items[self.sel]
            sfx("ok")
            if it.ok:
                it.ok()
            elif it.lr:
                it.lr(1)
        elif action == "back" and self.back:
            sfx("back")
            self.back()

    def hit(self, x, y):
        for i, (l, t, r, b) in enumerate(self.rects):
            if l <= x <= r and t <= y <= b:
                return i
        return -1


# ---------------------------------------------------------------- drawing helpers
def g():
    return art.g


def text(s, x, y, size, font="'Bagel Fat One'", color="#fff", align="center", base="middle", outline=0, ol=OL,
         spacing=0, alpha=1.0):
    c = g()
    c.save()
    c.globalAlpha = alpha
    c.font = f"{size}px {font}"
    c.textAlign = align
    c.textBaseline = base
    c.letterSpacing = spacing
    if outline:
        c.lineWidth = outline
        c.strokeStyle = ol
        c.strokeText(s, x, y)
    c.fillStyle = color
    c.fillText(s, x, y)
    c.restore()


def card(x, y, w, h, fill=CREAM):
    c = g()
    art.rr(x, y + 5, w, h, 13); c.fillStyle = OL; c.fill()
    art.rr(x, y, w, h, 13); c.fillStyle = fill; c.fill()
    c.lineWidth = 3.5; c.strokeStyle = OL; c.stroke()


def dim(a=.6):
    c = g()
    c.fillStyle = f"rgba(20,12,6,{a})"
    c.fillRect(0, 0, VW, VH)


def keycap(x, y, label):
    """Draws a key at (x, y) top-left and returns its width."""
    c = g()
    arrows = {"LEFT": -1, "RIGHT": 1, "DOWN": 2, "UP": 3}
    if label in arrows:
        w = 18
    else:
        c.font = "800 10px Sniglet"
        w = max(18, c.measureText(label) + 12)
    art.rr(x, y + 2.5, w, 15, 4); c.fillStyle = OL; c.fill()
    art.rr(x, y, w, 15, 4); c.fillStyle = "#fff"; c.fill(); c.lineWidth = 1.4; c.strokeStyle = OL; c.stroke()
    if label in arrows:
        d = arrows[label]
        cx, cy = x + w / 2, y + 7.5
        c.beginPath()
        if d in (-1, 1):
            c.moveTo(cx + 3.5 * d, cy); c.lineTo(cx - 2.5 * d, cy - 4); c.lineTo(cx - 2.5 * d, cy + 4)
        elif d == 2:
            c.moveTo(cx, cy + 3.5); c.lineTo(cx - 4, cy - 2.5); c.lineTo(cx + 4, cy - 2.5)
        else:
            c.moveTo(cx, cy - 3.5); c.lineTo(cx - 4, cy + 2.5); c.lineTo(cx + 4, cy + 2.5)
        c.closePath(); c.fillStyle = OL; c.fill()
    else:
        text(label, x + w / 2, y + 8, 10, "800 Sniglet", OL)
    return w


def keys_row(x_right, y, parts):
    """Lay out keycaps and small words right-aligned to x_right."""
    c = g()
    widths = []
    for p in parts:
        if isinstance(p, str) and p.startswith("~"):
            c.font = "10px Sniglet"
            widths.append(c.measureText(p[1:]) + 6)
        else:
            if p in ("LEFT", "RIGHT", "DOWN", "UP"):
                widths.append(18 + 3)
            else:
                c.font = "800 10px Sniglet"
                widths.append(max(18, c.measureText(p) + 12) + 3)
    x = x_right - sum(widths)
    for p, w in zip(parts, widths):
        if isinstance(p, str) and p.startswith("~"):
            text(p[1:], x + w / 2, y + 8, 10, "Sniglet", "#6b5440")
        else:
            keycap(x, y, p)
        x += w


# ---------------------------------------------------------------- the title screen
LOGO = [("CRUMB'S", 29, [-4, 2, -2, 3, -3, 2, -2], "#fff3d6", "#ffffff"),
        ("PICNIC", 58, [-3, 2, -2, 3, -2, 2], "#ffc94a", "#fff2b0"),
        ("RUN", 58, [2, -3, 3], "#ee4a36", "#ff9078")]


def draw_logo(t):
    c = g()
    c.save()
    c.translate(VW / 2, 70)
    c.rotate(-1.5 * math.pi / 180)
    c.translate(-VW / 2, -70)
    rows = [((LOGO[0],), 34), ((LOGO[1], LOGO[2]), 84)]
    idx = 0
    for words, cy in rows:
        c.font = f"{words[0][1]}px 'Bagel Fat One'"
        gap = 11 if len(words) > 1 else 0
        widths = [[c.measureText(ch) for ch in w[0]] for w in words]
        total = sum(sum(ws) for ws in widths) + gap * (len(words) - 1)
        x = VW / 2 - total / 2
        for wi, (word, size, rots, col, hi) in enumerate(words):
            for i, ch in enumerate(word):
                cw = widths[wi][i]
                bob = -sin((t / 60) * 2 * math.pi / 1.7 + idx * .2 * 2 * math.pi / 1.7) * size * .08
                c.drawImage(_logo_img(ch, size, rots[i % len(rots)] - 1.5, col, hi), x + cw / 2, cy + bob)
                x += cw
                idx += 1
            x += gap
    c.restore()


_cache = {}


def _cached(key, w, h, draw):
    """Render something static once at device resolution."""
    key = key + (art.RS,)
    img = _cache.get(key)
    if img is None:
        surf, cv = offscreen(w * art.RS, h * art.RS, art.RS)
        saved = art.g
        art.g = cv
        try:
            draw(cv)
        finally:
            art.g = saved
        surf.flush()
        _cache[key] = img = surf
    return img


def _logo_img(ch, size, rot, col, hi):
    d = size * 2.4

    def draw(cv):
        cv.translate(d / 2, d / 2)
        _logo_letter(ch, size, rot, col, hi)
    return _cached(("logo", ch, size, rot, col, hi), d, d, draw)


def _logo_letter(ch, size, rot, col, hi):
    c = g()
    o = size * .114
    c.save()
    c.rotate(rot * math.pi / 180)
    c.font = f"{size}px 'Bagel Fat One'"
    c.textAlign = "center"
    c.textBaseline = "middle"
    c.lineJoin = "round"
    c.lineWidth = o * 2
    c.strokeStyle = OL
    for dy in (o * 2.4, o * 1.7):
        c.strokeText(ch, 0, dy)
        c.fillStyle = OL
        c.fillText(ch, 0, dy)
    c.strokeText(ch, 0, 0)
    c.fillStyle = col
    c.fillText(ch, 0, 0)
    c.beginPath()
    c.rect(-size, -size, size * 2, size * .93)  # top 44% of the glyph gets the highlight colour
    c.clip()
    c.fillStyle = hi
    c.fillText(ch, 0, 0)
    c.restore()


RIBBON_BOX = (VW / 2 - 165, 105, 330, 60)


def draw_ribbon():
    bx, by, bw, bh = RIBBON_BOX

    def draw(cv):
        cv.translate(-bx, -by)
        _ribbon()
    g().drawImageAt(_cached(("ribbon",), bw, bh, draw), bx, by)


def _ribbon():
    c = g()
    w, h = 300, 26
    x, y = VW / 2 - w / 2, 120
    c.save()
    c.translate(VW / 2, y + h / 2)
    c.rotate(1.2 * math.pi / 180)
    c.translate(-VW / 2, -(y + h / 2))
    art.rr(x, y + 4, w, h, 6); c.fillStyle = OL; c.fill()
    art.rr(x, y, w, h, 6); c.save(); c.clip()
    art.gingham(x, y, w, h, 0, 0, .6, 6.5)
    c.restore()
    art.rr(x, y, w, h, 6); c.lineWidth = 2.5; c.strokeStyle = OL; c.stroke()
    label = "Run · Stomp · Picnic"
    c.font = "15px 'Bagel Fat One'"
    lw = c.measureText(label) + 24
    art.rr(VW / 2 - lw / 2, y + 3, lw, h - 6, 5); c.fillStyle = CREAM; c.fill(); c.lineWidth = 2; c.strokeStyle = OL; c.stroke()
    text(label, VW / 2, y + h / 2 + .5, 15, "'Bagel Fat One'", OL, spacing=.9)
    c.restore()


def draw_plaque(menu, i, cx, cy, w, h, size, primary, t):
    c = g()
    it = menu.items[i]
    on = menu.sel == i
    pulse = 1 + (sin(t * .1) * .03 if on else 0)
    c.save()
    c.translate(cx, cy)
    c.scale(pulse, pulse)
    x, y = -w / 2, -h / 2
    art.rr(x, y + 5, w, h, 9); c.fillStyle = OL if (primary or on) else "#d8382a"; c.fill()
    art.rr(x, y, w, h, 9)
    c.fillStyle = RED if (primary or on) else "#fff6dc"
    c.fill()
    if primary or on:
        c.save(); art.rr(x, y, w, h, 9); c.clip()
        c.fillStyle = "rgba(255,255,255,.22)"; c.fillRect(x, y, w, h * .3)
        c.restore()
    art.rr(x, y, w, h, 9); c.lineWidth = 2.6; c.strokeStyle = OL if (primary or on) else "#d8382a"; c.stroke()
    if primary or on:
        text(it.text(), 0, 1.5, size, "'Luckiest Guy'", CREAM, outline=3.2, spacing=1.2)
    else:
        text(it.text(), 0, 1.5, size, "'Luckiest Guy'", "#d8382a", spacing=1.2)
    c.restore()
    if on:
        bob = sin(t * .15) * 2.5
        for d in (-1, 1):
            art.cookie_art(cx + d * (w / 2 + 16 + bob), cy, 7.5)
    s = pulse
    menu.rects.append((cx - w / 2 * s, cy - h / 2 * s, cx + w / 2 * s, cy + h / 2 * s + 5))


def draw_title(menu, t):
    c = g()
    c.setTransform(art.RS, 0, 0, art.RS, 0, 0)
    menu.rects = []
    draw_logo(t)
    draw_ribbon()
    layout = [(170, 210, 40, 25, True), (212, 176, 28, 16, False), (246, 176, 28, 16, False), (280, 176, 28, 16, False)]
    for i, (cy, w, h, size, primary) in enumerate(layout[:len(menu.items)]):
        draw_plaque(menu, i, VW / 2, cy, w, h, size, primary, t)
    S.menu_rects = list(menu.rects)
    # best score badge
    best = "BEST " + str(S.best).zfill(6)
    c.font = "800 12px Sniglet"
    bw = c.measureText(best) + 18
    art.rr(10, 12.5, bw, 22, 7); c.fillStyle = OL; c.fill()
    art.rr(10, 10, bw, 22, 7); c.fillStyle = "rgba(255,243,214,.94)"; c.fill(); c.lineWidth = 2; c.strokeStyle = OL; c.stroke()
    text(best, 10 + bw / 2, 21.5, 12, "800 Sniglet", OL)
    # control hints on the dirt
    if not draw_title.panel_open:
        hint_bar([("UP", "DOWN", "~choose"), ("ENTER", "~select")], VH - 12)
    text("v1.0", VW - 8, VH - 11, 9, "Sniglet", "rgba(255,243,214,.6)", align="right")


draw_title.panel_open = False


def hint_bar(groups, y):
    c = g()
    parts = []
    for gi, grp in enumerate(groups):
        if gi:
            parts.append("~   ")
        parts.extend(grp)
    widths = []
    for p in parts:
        if p.startswith("~"):
            c.font = "11px Sniglet"
            widths.append(c.measureText(p[1:]) + 6)
        elif p in ("LEFT", "RIGHT", "DOWN", "UP"):
            widths.append(21)
        else:
            c.font = "800 10px Sniglet"
            widths.append(max(18, c.measureText(p) + 12) + 3)
    x = VW / 2 - sum(widths) / 2
    for p, w in zip(parts, widths):
        if p.startswith("~"):
            text(p[1:], x + w / 2, y, 11, "800 Sniglet", CREAM, outline=2.5)
        else:
            keycap(x, y - 8, p)
        x += w


# ---------------------------------------------------------------- panels
def panel_menu(menu, title, x, y, w, row_h=26, t=0, values=True):
    """A cream card with a heading and a list of selectable rows."""
    c = g()
    n = len(menu.items)
    h = 58 + n * row_h + 10
    card(x, y, w, h)
    text(title, x + w / 2 + 1.8, y + 30 + 1.8, 25, "'Bagel Fat One'", OL)
    text(title, x + w / 2, y + 30, 25, "'Bagel Fat One'", RED)
    menu.rects = []
    for i, it in enumerate(menu.items):
        ry = y + 58 + i * row_h
        on = menu.sel == i
        rx, rw = x + 16, w - 32
        if on:
            art.rr(rx, ry + 2.5, rw, row_h - 4, 7); c.fillStyle = OL; c.fill()
            art.rr(rx, ry, rw, row_h - 4, 7); c.fillStyle = RED; c.fill(); c.lineWidth = 2; c.strokeStyle = OL; c.stroke()
        val = it.val() if values else None
        col = CREAM if on else OL
        if val is None:
            if on:
                text(it.text(), x + w / 2, ry + (row_h - 4) / 2 + 1, 15, "'Luckiest Guy'", col, outline=2.6, spacing=1)
            else:
                text(it.text(), x + w / 2, ry + (row_h - 4) / 2 + 1, 15, "'Luckiest Guy'", col, spacing=1)
        else:
            if on:
                text(it.text(), rx + 12, ry + (row_h - 4) / 2 + 1, 15, "'Luckiest Guy'", col, align="left", outline=2.6, spacing=1)
                text("‹  " + val + "  ›", rx + rw - 12, ry + (row_h - 4) / 2 + 1, 15, "'Luckiest Guy'", "#ffd84d",
                     align="right", outline=2.6, spacing=1)
            else:
                text(it.text(), rx + 12, ry + (row_h - 4) / 2 + 1, 15, "'Luckiest Guy'", col, align="left", spacing=1)
                text(val, rx + rw - 12, ry + (row_h - 4) / 2 + 1, 15, "'Luckiest Guy'", "#b0402c", align="right", spacing=1)
        if on:
            bob = sin(t * .15) * 2
            art.cookie_art(rx - 2 + bob, ry + (row_h - 4) / 2, 6.5)
        menu.rects.append((rx, ry, rx + rw, ry + row_h - 4))
    return h


HOWTO = [
    ("Move", ["LEFT", "RIGHT", "~or", "A", "D"]),
    ("Jump (hold = higher)", ["SPACE", "~or", "W"]),
    ("Run", ["SHIFT"]),
    ("Crouch", ["DOWN", "~or", "S"]),
    ("Throw fire cookie", ["F"]),
    ("Roll dodge (5s cooldown)", ["E"]),
    ("Ground pound (in air)", ["DOWN", "~or", "S"]),
    ("Float (hold in air)", ["SPACE"]),
    ("Wall slide / wall jump", ["LEFT", "RIGHT", "~into wall, then", "SPACE"]),
]
NOTE = ["Grab a pizza to grow big and smash bricks from below.",
        "Grab a cookie to throw fire cookies. Stomp the ants and",
        "shellnuts, reach the picnic blanket, and beat the Grand Chili!"]


def draw_howto(menu, t):
    c = g()
    w, h = 430, 346
    x, y = VW / 2 - w / 2, VH / 2 - h / 2 - 2
    dim(.55)
    card(x, y, w, h)
    text("HOW TO PLAY", x + w / 2 + 1.8, y + 28 + 1.8, 25, "'Bagel Fat One'", OL)
    text("HOW TO PLAY", x + w / 2, y + 28, 25, "'Bagel Fat One'", RED)
    for i, (label, keys) in enumerate(HOWTO):
        ry = y + 50 + i * 21
        text(label, x + 22, ry + 8, 13, "800 Sniglet", OL, align="left")
        keys_row(x + w - 20, ry, keys)
    ny = y + 50 + len(HOWTO) * 21 + 10
    c.fillStyle = "rgba(43,22,8,.15)"; c.fillRect(x + 20, ny - 6, w - 40, 1.5)
    for i, line in enumerate(NOTE):
        text(line, x + w / 2, ny + 6 + i * 14, 11.5, "Sniglet", OL)
    text("Gamepad:  A jump  ·  X fire  ·  B roll  ·  RB run  ·  START pause", x + w / 2, ny + 52, 10.5, "800 Sniglet",
         "#8a5a2b")
    menu.rects = []
    bw, bh = 120, 26
    bx, by = VW / 2 - bw / 2, y + h - bh - 12
    art.rr(bx, by + 4, bw, bh, 8); c.fillStyle = OL; c.fill()
    art.rr(bx, by, bw, bh, 8); c.fillStyle = RED; c.fill(); c.lineWidth = 2.4; c.strokeStyle = OL; c.stroke()
    text("GOT IT", VW / 2, by + bh / 2 + 1.5, 16, "'Luckiest Guy'", CREAM, outline=2.8, spacing=1.2)
    menu.rects.append((bx, by, bx + bw, by + bh + 4))


def draw_end(menu, title, lines, t, black=False):
    c = g()
    if black:
        c.fillStyle = "#000"; c.fillRect(0, 0, VW, VH)
    else:
        dim(.6)
    w = 300
    n = len(menu.items)
    h = 70 + len(lines) * 18 + n * 28 + 18
    x, y = VW / 2 - w / 2, VH / 2 - h / 2
    card(x, y, w, h)
    text(title, VW / 2 + 2, y + 34 + 2, 30, "'Bagel Fat One'", OL)
    text(title, VW / 2, y + 34, 30, "'Bagel Fat One'", "#ffd84d", outline=4)
    for i, ln in enumerate(lines):
        text(ln, VW / 2, y + 66 + i * 18, 14, "800 Sniglet", OL)
    menu.rects = []
    top = y + 66 + len(lines) * 18 + 6
    for i, it in enumerate(menu.items):
        ry = top + i * 28
        on = menu.sel == i
        rx, rw = x + 30, w - 60
        if on:
            art.rr(rx, ry + 2.5, rw, 24, 7); c.fillStyle = OL; c.fill()
            art.rr(rx, ry, rw, 24, 7); c.fillStyle = RED; c.fill(); c.lineWidth = 2; c.strokeStyle = OL; c.stroke()
            text(it.text(), VW / 2, ry + 13, 15, "'Luckiest Guy'", CREAM, outline=2.6, spacing=1)
            art.cookie_art(rx - 2 + sin(t * .15) * 2, ry + 12, 6.5)
        else:
            text(it.text(), VW / 2, ry + 13, 15, "'Luckiest Guy'", OL, spacing=1)
        menu.rects.append((rx, ry, rx + rw, ry + 24))


# ---------------------------------------------------------------- the UI controller
class UI:
    def __init__(self, app):
        self.app = app
        self.stack = []
        self.t = 0
        self.title_menu = Menu([
            Item("START GAME", self.start),
            Item("HOW TO PLAY", lambda: self.push("howto")),
            Item("OPTIONS", lambda: self.push("options")),
            Item("QUIT", app.quit),
        ])
        self.howto = Menu([Item("GOT IT", self.pop)], back=self.pop)
        self.options = Menu([
            Item("SOUND EFFECTS", lr=lambda d: app.toggle("sfx"), value=lambda: "ON" if app.cfg["sfx"] else "OFF"),
            Item("MUSIC", lr=lambda d: app.toggle("music"), value=lambda: "ON" if app.cfg["music"] else "OFF"),
            Item("ROLL STYLE", lr=self._roll, value=lambda: ROLLNAMES[S.ROLLSTYLE]),
            Item("FULLSCREEN", lr=lambda d: app.toggle("fullscreen"), value=lambda: "ON" if app.cfg["fullscreen"] else "OFF"),
            Item("BACK", self.pop),
        ], back=self.pop)
        self.pause = Menu([
            Item("RESUME", self.resume),
            Item("RESTART LEVEL", self.restart),
            Item("OPTIONS", lambda: self.push("options")),
            Item("QUIT TO TITLE", self.quit_to_title),
        ], back=self.resume)
        self.over = Menu([Item("TRY AGAIN", self.start), Item("TITLE SCREEN", self.quit_to_title)],
                         back=self.quit_to_title)
        self.win = Menu([Item("PLAY AGAIN", self.start), Item("TITLE SCREEN", self.quit_to_title)],
                        back=self.quit_to_title)
        self.dev = Menu([Item(f"LEVEL {i + 1}  {n}", (lambda i=i: self.dev_go(i))) for i, n in enumerate(NAMES)] + [
            Item("ROLL SPRITE", lr=self._roll, value=lambda: ROLLNAMES[S.ROLLSTYLE]),
            Item("CLOSE", self.pop)], back=self.pop)

    # ---- flow
    def _roll(self, d):
        S.ROLLSTYLE = (S.ROLLSTYLE + d) % len(ROLLNAMES)
        self.app.cfg["roll"] = S.ROLLSTYLE
        self.app.save()

    def push(self, name):
        self.stack.append(name)
        getattr(self, name).sel = 0

    def pop(self):
        if self.stack:
            self.stack.pop()

    def start(self):
        self.stack = []
        from .game import start
        start()

    def resume(self):
        self.stack = []
        S.paused = False

    def restart(self):
        self.stack = []
        from .game import restart_level
        restart_level()

    def quit_to_title(self):
        self.stack = []
        from .game import to_title
        to_title()
        self.title_menu.sel = 0

    def dev_go(self, i):
        self.stack = []
        from .game import load_level, new_player, note_best
        fresh = S.state not in ("play", "dead", "clear", "goal")
        if fresh:
            note_best()
            S.lives, S.score, S.coinsN = 3, 0, 0
        keep = not fresh and S.state == "play"
        load_level(i)
        new_player(keep)
        S.state = "play"
        S.paused = False
        S.deadT = S.clearT = 0

    def open_pause(self):
        if S.state in ("play", "dead", "goal", "free", "clear", "card") and not S.paused:
            S.paused = True
            self.stack = ["pause"]
            self.pause.sel = 0

    # ---- input
    def active(self):
        if self.stack:
            return getattr(self, self.stack[-1])
        if S.state == "title":
            return self.title_menu
        if S.state == "over":
            return self.over
        if S.state == "win":
            return self.win
        return None

    def wants_input(self):
        return self.active() is not None

    def nav(self, action):
        m = self.active()
        if m is None:
            return False
        if action == "back" and m is self.title_menu:
            m.sel = len(m.items) - 1
            self.app.menu_sfx("move")
            return True
        m.nav(action, self.app.menu_sfx)
        return True

    def mouse_move(self, x, y):
        m = self.active()
        if m:
            i = m.hit(x, y)
            if i >= 0 and i != m.sel:
                m.sel = i
                self.app.menu_sfx("move")

    def mouse_down(self, x, y):
        m = self.active()
        if not m:
            return False
        i = m.hit(x, y)
        if i >= 0:
            m.sel = i
            m.nav("ok", self.app.menu_sfx)
            return True
        return False

    # ---- draw
    def draw(self):
        self.t += 1
        t = self.t
        c = g()
        c.setTransform(art.RS, 0, 0, art.RS, 0, 0)
        if S.state == "title":
            draw_title.panel_open = bool(self.stack)
            draw_title(self.title_menu, t)
        if S.state == "over" and not self._over_stack():
            draw_end(self.over, "GAME OVER", [f"Score {S.score:06d}", f"Best {S.best:06d}"], t)
        if S.state == "win" and not self._over_stack():
            final = S.CI == 3
            draw_end(self.win, "TOGETHER AGAIN!" if final else "PICNIC TIME!",
                     [f"Score {S.score:06d}", f"Best {S.best:06d}"], t, black=final)
        for name in self.stack:
            m = getattr(self, name)
            if name == "howto":
                draw_howto(m, t)
            elif name == "options":
                dim(.5)
                panel_menu(m, "OPTIONS", VW / 2 - 160, 70, 320, t=t)
            elif name == "pause":
                dim(.6)
                panel_menu(m, "PAUSED", VW / 2 - 130, 90, 260, t=t, values=False)
            elif name == "dev":
                dim(.6)
                panel_menu(m, "DEV MENU", VW / 2 - 170, 40, 340, row_h=24, t=t)
        if S.state in ("play", "dead", "goal", "free", "clear") and S.paused and not self.stack:
            S.paused = False

    def _over_stack(self):
        return bool(self.stack)
