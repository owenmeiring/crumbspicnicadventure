"""In-engine menus: title screen, how to play, options, pause, game over and the win screen.

Everything is drawn with the same art pipeline as the game and works with
keyboard, gamepad or mouse.
"""

import math

from . import art
from .canvas import offscreen
from .game import LAST, NAMES, ROLLNAMES, S, VH, VW

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
    def __init__(self, items, back=None, grid=None):
        self.items = items
        self.sel = 0
        self.rects = []
        self.back = back
        self.pulse = 0
        self.grid = grid  # optional rows of item indexes for 2-D navigation

    def _cell(self):
        for r, row in enumerate(self.grid):
            if self.sel in row:
                return r, row.index(self.sel)
        return 0, 0

    def nav(self, action, sfx):
        if self.grid and action in ("up", "down", "left", "right"):
            r, c = self._cell()
            if action in ("up", "down"):
                r = (r + (1 if action == "down" else -1)) % len(self.grid)
                c = min(c, len(self.grid[r]) - 1)
            else:
                row = self.grid[r]
                if len(row) == 1:
                    return
                c = (c + (1 if action == "right" else -1)) % len(row)
            self.sel = self.grid[r][c]
            sfx("move")
            return
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


def draw_ribbon():
    bx, by, bw, bh = VW / 2 - 165, 105, 330, 60

    def draw(cv):
        cv.translate(-bx, -by)
        _ribbon()
    g().drawImageAt(_cached(("ribbon", VW), bw, bh, draw), bx, by)


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


def draw_plaque(menu, i, cx, cy, w, h, size, primary, t, sides=(-1, 1)):
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
        for d in sides:
            art.cookie_art(cx + d * (w / 2 + 16 + bob), cy, 7.5)
    s = pulse
    menu.rects.append((cx - w / 2 * s, cy - h / 2 * s, cx + w / 2 * s, cy + h / 2 * s + 5))


TITLE_LAYOUT = [  # x offset from screen centre, cy, w, h, font size, primary, cookie sides
    (0, 170, 210, 40, 25, True, (-1, 1)),
    (-78, 212, 148, 26, 14, False, (-1,)), (78, 212, 148, 26, 14, False, (1,)),
    (-78, 245, 148, 26, 14, False, (-1,)), (78, 245, 148, 26, 14, False, (1,)),
    (0, 278, 110, 24, 13, False, (-1, 1)),
]
TITLE_GRID = [[0], [1, 2], [3, 4], [5]]


def draw_title(menu, t):
    c = g()
    c.setTransform(art.RS, 0, 0, art.RS, 0, 0)
    menu.rects = []
    draw_logo(t)
    draw_ribbon()
    for i, (dx, cy, w, h, size, primary, sides) in enumerate(TITLE_LAYOUT[:len(menu.items)]):
        draw_plaque(menu, i, VW / 2 + dx, cy, w, h, size, primary, t, sides)
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


# ---------------------------------------------------------------- custom levels browser
class CustomPanel:
    """Lists the level files in the levels folder: play, edit or delete them, or import from the clipboard."""
    ACTIONS = ["PLAY", "EDIT", "DELETE"]
    FOOT = ["IMPORT FROM CLIPBOARD", "OPEN FOLDER", "BACK"]
    ROWS = 6

    def __init__(self, ui):
        self.ui = ui
        self.items = []
        self.sel = 0
        self.act = 0
        self.top = 0
        self.confirm = None
        self.msg = ""
        self.rects = []

    def refresh(self):
        from . import levels
        self.items = levels.list_levels()
        self.sel = 0 if self.items else len(self.items)
        self.act = 0
        self.top = 0
        self.confirm = None

    def count(self):
        return len(self.items) + 1  # the footer row

    def nav(self, action, sfx):
        n = self.count()
        on_foot = self.sel == len(self.items)
        if action in ("up", "down"):
            self.sel = (self.sel + (1 if action == "down" else -1)) % n
            self.act = 0
            self.confirm = None
            sfx("move")
        elif action in ("left", "right"):
            k = len(self.FOOT) if on_foot else len(self.ACTIONS)
            self.act = (self.act + (1 if action == "right" else -1)) % k
            self.confirm = None
            sfx("move")
        elif action == "ok":
            sfx("ok")
            self.activate()
        elif action == "back":
            sfx("back")
            self.ui.pop()
        self.top = max(0, min(self.top, self.sel, max(0, len(self.items) - self.ROWS)))
        if self.sel < len(self.items) and self.sel >= self.top + self.ROWS:
            self.top = self.sel - self.ROWS + 1

    def activate(self):
        from . import levels
        if self.sel == len(self.items):
            what = self.FOOT[self.act]
            if what == "BACK":
                self.ui.pop()
            elif what == "OPEN FOLDER":
                self.ui.app.editor.open_folder()
            else:
                from .editor import clip_get
                try:
                    L = levels.parse_level(clip_get())
                except ValueError as e:
                    self.msg = f"Clipboard isn't a level: {e}"
                    return
                path = levels.save_level(L)
                self.refresh()
                self.msg = f'Imported "{L["name"]}" to levels\\{path.name}'
            return
        path, L = self.items[self.sel]
        what = self.ACTIONS[self.act]
        if what == "PLAY":
            self.ui.stack = []
            from .game import play_custom
            play_custom(L, False)
        elif what == "EDIT":
            self.ui.app.editor.open(L, path)
        elif self.confirm == self.sel:
            levels.delete_level(path)
            self.refresh()
            self.msg = f'Deleted "{L["name"]}".'
        else:
            self.confirm = self.sel
            self.msg = "Press DELETE again to remove this level for good."

    def hit(self, x, y):
        for i, (l, t, r, b, row, act) in enumerate(self.rects):
            if l <= x <= r and t <= y <= b:
                return i
        return -1

    def mouse_move(self, x, y, sfx):
        i = self.hit(x, y)
        if i >= 0:
            row, act = self.rects[i][4:]
            if (row, act) != (self.sel, self.act):
                self.sel, self.act = row, act
                sfx("move")

    def mouse_down(self, x, y, sfx):
        i = self.hit(x, y)
        if i < 0:
            return False
        self.sel, self.act = self.rects[i][4:]
        sfx("ok")
        self.activate()
        return True

    def draw(self, t):
        from .levels import THEMES
        c = g()
        dim(.55)
        w, h = 430, 320
        x, y = VW / 2 - w / 2, VH / 2 - h / 2
        card(x, y, w, h)
        text("CUSTOM LEVELS", VW / 2 + 1.8, y + 27 + 1.8, 24, "'Bagel Fat One'", OL)
        text("CUSTOM LEVELS", VW / 2, y + 27, 24, "'Bagel Fat One'", RED)
        self.rects = []
        if not self.items:
            text("No custom levels yet.", VW / 2, y + 100, 15, "800 Sniglet", OL)
            text("Open the LEVEL BUILDER, make one and press Save,", VW / 2, y + 124, 11.5, "Sniglet", OL)
            text("or copy a level's JSON and import it below.", VW / 2, y + 140, 11.5, "Sniglet", OL)
        for vis, i in enumerate(range(self.top, min(len(self.items), self.top + self.ROWS))):
            path, L = self.items[i]
            ry = y + 50 + vis * 33
            on = self.sel == i
            art.rr(x + 16, ry, w - 32, 29, 7)
            c.fillStyle = "#ffe3a0" if on else "#fff"
            c.fill()
            c.lineWidth = 2 if on else 1.4
            c.strokeStyle = OL
            c.stroke()
            text(L["name"].upper(), x + 26, ry + 11, 13, "'Luckiest Guy'", OL, align="left", spacing=.8)
            info = f"{THEMES[L['theme']]}  ·  {L['w']} wide" + ("  ·  boss" if L["boss"] else "")
            text(info, x + 26, ry + 22.5, 9, "Sniglet", "#8a5a2b", align="left")
            bx = x + w - 20
            for a in range(len(self.ACTIONS) - 1, -1, -1):
                label = self.ACTIONS[a]
                if a == 2 and self.confirm == i:
                    label = "SURE?"
                bw = 50 if a == 2 else 40
                bx -= bw + 4
                hot = on and self.act == a
                art.rr(bx, ry + 6, bw, 17, 5)
                c.fillStyle = (RED if a != 0 else "#3f9d3a") if hot else "#f3e2c0"
                c.fill()
                c.lineWidth = 1.4
                c.strokeStyle = OL
                c.stroke()
                text(label, bx + bw / 2, ry + 15.5, 10.5, "'Luckiest Guy'", CREAM if hot else OL,
                     outline=2 if hot else 0, spacing=.6)
                self.rects.append((bx, ry + 6, bx + bw, ry + 23, i, a))
        if len(self.items) > self.ROWS:
            text(f"{self.top + 1}-{min(len(self.items), self.top + self.ROWS)} of {len(self.items)}", x + w - 22,
                 y + 27, 9, "Sniglet", "#8a5a2b", align="right")
        fy = y + h - 34
        widths = [170, 110, 70]
        fx = VW / 2 - (sum(widths) + 8 * 2) / 2
        for a, (label, bw) in enumerate(zip(self.FOOT, widths)):
            hot = self.sel == len(self.items) and self.act == a
            art.rr(fx, fy + 3, bw, 22, 7); c.fillStyle = OL; c.fill()
            art.rr(fx, fy, bw, 22, 7); c.fillStyle = RED if hot else "#fff6dc"; c.fill()
            c.lineWidth = 2; c.strokeStyle = OL; c.stroke()
            text(label, fx + bw / 2, fy + 12, 12, "'Luckiest Guy'", CREAM if hot else "#d8382a",
                 outline=2.4 if hot else 0, spacing=.8)
            self.rects.append((fx, fy, fx + bw, fy + 25, len(self.items), a))
            fx += bw + 8
        if self.msg:
            text(self.msg, VW / 2, fy - 11, 10, "800 Sniglet", "#8a5a2b")


# ---------------------------------------------------------------- the UI controller
class UI:
    def __init__(self, app):
        self.app = app
        self.stack = []
        self.t = 0
        self.title_menu = Menu([
            Item("START GAME", self.start_or_continue),
            Item("HOW TO PLAY", lambda: self.push("howto")),
            Item("OPTIONS", lambda: self.push("options")),
            Item("LEVEL BUILDER", lambda: app.editor.open()),
            Item("CUSTOM LEVELS", self.open_custom),
            Item("QUIT", app.quit),
        ], grid=TITLE_GRID)
        self.howto = Menu([Item("GOT IT", self.pop)], back=self.pop)
        self.options = Menu([
            Item("SOUND EFFECTS", lr=lambda d: app.toggle("sfx"), value=lambda: "ON" if app.cfg["sfx"] else "OFF"),
            Item("MUSIC", lr=lambda d: app.toggle("music"), value=lambda: "ON" if app.cfg["music"] else "OFF"),
            Item("ROLL STYLE", lr=self._roll, value=lambda: ROLLNAMES[S.ROLLSTYLE]),
            Item("FULLSCREEN", lr=lambda d: app.toggle("fullscreen"), value=lambda: "ON" if app.cfg["fullscreen"] else "OFF"),
            Item("BACK", self.pop),
        ], back=self.pop)
        self.pause = Menu([], back=self.resume)
        self.over = Menu([], back=self.quit_to_title)
        self.win = Menu([], back=self.quit_to_title)
        self.custom = CustomPanel(self)
        self.startmenu = Menu([
            Item(lambda: f"CONTINUE  1-{S.checkpoint + 1}  {NAMES[S.checkpoint]}", self.cont),
            Item("NEW GAME", self.new_game),
            Item("BACK", self.pop),
        ], back=self.pop)
        self.dev = Menu([Item(f"1-{i + 1}  {n}", (lambda i=i: self.dev_go(i))) for i, n in enumerate(NAMES)] + [
            Item("ROLL SPRITE", lr=self._roll, value=lambda: ROLLNAMES[S.ROLLSTYLE]),
            Item("CLOSE", self.pop)], back=self.pop)
        self._end_state = None

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

    def open_custom(self):
        self.custom.refresh()
        self.custom.msg = ""
        self.stack.append("custom")

    def start(self):
        self.stack = []
        from .game import start
        start()

    def start_or_continue(self):
        if S.checkpoint > 0:
            self.push("startmenu")
        else:
            self.new_game()

    def new_game(self):
        S.checkpoint = 0
        self.app.save_checkpoint()
        self.start()

    def cont(self):
        self.stack = []
        from .game import continue_game
        continue_game()

    def retry(self):
        self.stack = []
        from .game import restart_level, start
        if S.CUST:
            restart_level()
        else:
            start()

    def to_editor(self):
        self.stack = []
        self.app.editor.resume()

    def resume(self):
        self.stack = []
        S.paused = False

    def restart(self):
        self.stack = []
        from .game import restart_level
        restart_level()

    def quit_to_title(self):
        self.stack = []
        from_list = bool(S.CUST) and not S.CUSTEDIT
        from .game import to_title
        to_title()
        self.title_menu.sel = 0
        if from_list:
            self.title_menu.sel = 4
            self.open_custom()

    def dev_go(self, i):
        self.stack = []
        from .game import load_level, new_player, note_best
        S.CUST = None
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
            items = [Item("RESUME", self.resume), Item("RESTART LEVEL", self.restart)]
            if S.CUSTEDIT:
                items.append(Item("BACK TO EDITOR", self.to_editor))
            items.append(Item("OPTIONS", lambda: self.push("options")))
            if not S.CUSTEDIT:
                items.append(Item("QUIT TO TITLE", self.quit_to_title))
            self.pause.items = items
            self.pause.back = self.resume
            S.paused = True
            self.stack = ["pause"]
            self.pause.sel = 0

    def _end_menus(self):
        """Game over and win menus depend on where the level came from."""
        if self._end_state == (S.state, bool(S.CUST), S.CUSTEDIT, S.checkpoint):
            return
        self._end_state = (S.state, bool(S.CUST), S.CUSTEDIT, S.checkpoint)
        if S.CUSTEDIT:
            tail, back = Item("BACK TO EDITOR", self.to_editor), self.to_editor
        elif S.CUST:
            tail, back = Item("CUSTOM LEVELS", self.quit_to_title), self.quit_to_title
        else:
            tail, back = Item("TITLE SCREEN", self.quit_to_title), self.quit_to_title
        if not S.CUST and S.checkpoint > 0:
            self.over.items = [Item(f"CONTINUE FROM 1-{S.checkpoint + 1}", self.cont),
                               Item("RESTART WORLD", self.new_game), tail]
        else:
            self.over.items = [Item("TRY AGAIN", self.retry), tail]
        self.win.items = [Item("PLAY AGAIN", self.retry), tail]
        self.over.back = self.win.back = back
        self.over.sel = self.win.sel = 0

    # ---- input
    def active(self):
        if self.stack:
            return getattr(self, self.stack[-1])
        if S.state == "title":
            return self.title_menu
        if S.state in ("over", "win"):
            self._end_menus()
            return self.over if S.state == "over" else self.win
        self._end_state = None
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
        if isinstance(m, CustomPanel):
            m.mouse_move(x, y, self.app.menu_sfx)
        elif m:
            i = m.hit(x, y)
            if i >= 0 and i != m.sel:
                m.sel = i
                self.app.menu_sfx("move")

    def mouse_down(self, x, y):
        m = self.active()
        if not m:
            return False
        if isinstance(m, CustomPanel):
            return m.mouse_down(x, y, self.app.menu_sfx)
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
        if S.state in ("over", "win"):
            self._end_menus()
        if S.state == "over" and not self.stack:
            draw_end(self.over, "GAME OVER", [f"Score {S.score:06d}", f"Best {S.best:06d}"], t)
        if S.state == "win" and not self.stack:
            if S.CUST:
                title, black = ("BOSS DEFEATED!" if S.CUST["boss"] else "LEVEL COMPLETE!"), False
            else:
                final = S.CI == LAST
                title, black = ("TOGETHER AGAIN!" if final else "PICNIC TIME!"), final
            draw_end(self.win, title, [f"Score {S.score:06d}", f"Best {S.best:06d}"], t, black=black)
        for name in self.stack:
            m = getattr(self, name)
            if name == "howto":
                draw_howto(m, t)
            elif name == "options":
                dim(.5)
                panel_menu(m, "OPTIONS", VW / 2 - 160, 70, 320, t=t)
            elif name == "pause":
                dim(.6)
                panel_menu(m, "PAUSED", VW / 2 - 130, 80, 260, t=t, values=False)
            elif name == "dev":
                dim(.6)
                panel_menu(m, "DEV MENU", VW / 2 - 170, 40, 340, row_h=24, t=t)
            elif name == "custom":
                m.draw(t)
            elif name == "startmenu":
                dim(.5)
                panel_menu(m, "START GAME", VW / 2 - 170, 110, 340, t=t, values=False)
        if S.state in ("play", "dead", "goal", "free", "clear") and S.paused and not self.stack:
            S.paused = False

