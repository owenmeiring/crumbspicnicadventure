"""The level builder.

An in-engine editor inspired by the original HTML builder: paint tiles,
coins, enemies, the start, the goal and a boss arena straight onto the live
level, then play-test it instantly. On top of the original it adds box fill,
an eyedropper, redo, a minimap scrubber, live tile previews, and plain .json
level files you can share (or paste from the HTML version).
"""

import copy
import math
import os
import subprocess
import time

import cairo
import numpy as np
import pygame

from . import art, game, levels
from . import ui as ui_mod
from .canvas import offscreen
from .game import O, S, T, VH, VW
from .levels import EH, THEMES

K = .72            # world zoom while editing
TOP = 34           # world view starts below the top bar and minimap
VIEW_B = TOP + VH * K
PANEL_Y = 311
MM = (6, 21, 500, 12)  # minimap box

OL = "#2b1608"
PANEL = "#2b1608"
BTN = "#45291a"
BTN_HI = "#5d3a24"
CREAM = "#fff3d6"
MUTED = "#c9a98a"
GOLD = "#ffd84d"
RED = "#e8452f"
GREEN = "#3f9d3a"

TOOLS = [  # id, name, key, tile char
    ("ground", "Ground", "1", "#"), ("brick", "Brick", "2", "b"), ("q", "? Block", "3", "?"),
    ("stone", "Stone", "4", "s"), ("dark", "Dark wall", "5", "c"), ("coin", "Coin", "6", None),
    ("ant", "Ant", "7", None), ("nut", "Walnut", "8", None), ("start", "Start", "9", None),
    ("goal", "Goal flag", "0", None), ("boss", "Grand Chili", "B", None), ("arena", "Boss arena", "V", None),
    ("crumble", "Cracker", "K", "k"), ("jelly", "Jelly pad", "J", "j"), ("spike", "Spikes", "X", "x"),
    ("erase", "Eraser", "E", None),
]
TOOL_BY_KEY = {getattr(pygame, "K_" + t[2].lower()): t[0] for t in TOOLS}
TILE_OF = {t[0]: t[3] for t in TOOLS if t[3]}
CAVES = {1, 2, 3, 5}  # themes that come with a ceiling
THEMED_NAMES = {
    "ground": {0: "Grass", 1: "Pantry floor", 2: "Kitchen floor", 3: "Honeycomb", 4: "Cake", 5: "Fudge",
               6: "Jungle soil", 7: "Cloud"},
    "stone": {3: "Wax block", 4: "Ice block", 5: "Mine rock", 6: "Log", 7: "Candy crystal"},
    "dark": {3: "Dark comb", 4: "Blue rock", 5: "Mine wall", 6: "Thick leaves", 7: "Night cloud"},
    "spike": {3: "Stingers", 4: "Ice shards", 7: "Candy shards"},
}
HINTS = {
    "crumble": "Crumbles a moment after Crumb lands on it, then grows back.",
    "jelly": "Bounces Crumb 5 tiles up. A ground pound bounces 8.",
    "spike": "Hurts, then sends Crumb back to the last safe ledge. R flips them.",
    "ground": "Drag to paint. Shift+drag fills a box.", "brick": "Big Crumb smashes these from below.",
    "q": "Holds a pizza, a cookie or a coin.", "stone": "Solid. Two stone ledges in row 8 give the boss perches.",
    "dark": "Ceiling and walls for the pantry and kitchen.", "coin": "Drag to scatter coins in empty cells.",
    "ant": "Click an empty cell on top of solid ground.", "nut": "Click an empty cell on top of solid ground.",
    "start": "Where Crumb begins.", "goal": "The picnic flag. Reaching it wins the level.",
    "boss": "The Grand Chili. Beat it to win the level.", "arena": "Click near an edge to move the boss arena wall.",
    "erase": "Removes whatever is on top. Right-click erases with any tool.",
}
QNAMES = ["pizza", "cookie", "coin"]
BOX_TOOLS = {"ground", "brick", "q", "stone", "dark", "coin", "erase", "crumble", "jelly", "spike"}
MM_COLORS = {"#": None, "b": (230, 169, 90), "?": (248, 211, 77), "s": (79, 135, 148), "c": (40, 46, 72),
             "k": (232, 192, 122), "j": (255, 111, 174), "x": (240, 240, 240), "v": (240, 240, 240)}
SKY = [(108, 184, 230), (45, 36, 71), (74, 26, 20), (90, 52, 8), (200, 220, 245), (30, 18, 10), (255, 150, 100),
       (40, 30, 90)]
GROUND = [(168, 104, 58), (86, 103, 141), (106, 79, 74), (201, 138, 31), (234, 194, 140), (94, 55, 32),
          (110, 68, 40), (244, 232, 246)]

SHORTCUTS = [
    ("Paint / place", "Left mouse"), ("Erase", "Right mouse"), ("Box fill", "Shift + drag"),
    ("Pick tile under cursor", "Alt + click"), ("Pan", "Middle drag or Space + drag"), ("Scroll", "A / D, arrows, wheel"),
    ("Jump to start / end", "Home / End"), ("Tools", "1-0, B, V, K, J, X, E"),
    ("Flip enemy facing / spike direction", "R"),
    ("Cycle ? block contents", "Q"), ("Toggle grid", "G"), ("Play-test", "T"), ("Undo / redo", "Ctrl+Z / Ctrl+Y"),
    ("Save", "Ctrl+S"), ("Copy / paste level JSON", "Ctrl+C / Ctrl+V"), ("Rename", "F2"), ("Width -/+ 8", "[  ]"),
]


# ------------------------------------------------------------------ clipboard
def clip_put(text):
    try:
        pygame.scrap.put_text(text)
        return True
    except Exception:
        pass
    try:
        subprocess.run(["clip"], input=text.encode("utf-16-le"), check=True)
        return True
    except Exception:
        return False


def clip_get():
    try:
        t = pygame.scrap.get_text()
        if t:
            return t
    except Exception:
        pass
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"], capture_output=True,
                           text=True, timeout=5)
        return r.stdout
    except Exception:
        return ""


def text(*a, **kw):
    ui_mod.text(*a, **kw)


class Editor:
    def __init__(self, app):
        self.app = app
        self.E = None
        self.path = None
        self.saved_snapshot = None
        self.tool = "ground"
        self.face = 1
        self.q = "pizza"
        self.spike_down = False
        self.undo, self.redo = [], []
        self.paint = None
        self.stroke_start = None
        self.last = None
        self.hover = None
        self.pan = None
        self.box = None
        self.mm_drag = False
        self.show_grid = True
        self.help = False
        self.picker = False
        self.typing = False
        self.toast_msg, self.toast_t = "", 0.0
        self.scroll = {"left": False, "right": False, "fast": False, "space": False}
        self.buttons = []
        self.mouse = (0, 0)
        self.icons = {}
        self.mm_img = None
        self.mm_buf = None
        self.return_cam = 0

    # ------------------------------------------------------------ lifecycle
    def open(self, L=None, path=None):
        self.E = copy.deepcopy(L) if L else (levels.load_draft() or levels.new_level(0))
        self.path = path
        self.saved_snapshot = copy.deepcopy(self.E) if path else None
        self.undo, self.redo = [], []
        self.app.ui.stack = []
        S.CUST = None
        S.cam = 0
        S.state = "edit"
        S.paused = False
        self.sync()
        self.toast("Level builder. Press F1 for shortcuts.")

    def resume(self):
        """Back from a play-test."""
        self.app.ui.stack = []
        S.CUST = None
        S.paused = False
        S.state = "edit"
        S.cam = self.return_cam
        self.sync()

    def exit(self):
        levels.save_draft(self.E)
        art.set_view(1, 0)
        self.typing = False
        pygame.key.stop_text_input()
        game.to_title()

    def test(self):
        if self.E["goal"] is None and not self.E["boss"]:
            self.toast("No goal or boss, so this level can't be finished yet.")
        levels.save_draft(self.E)
        self.return_cam = S.cam
        art.set_view(1, 0)
        game.play_custom(copy.deepcopy(self.E), True)

    def sync(self):
        cam = S.cam
        game.build_live(self.E)
        game.new_player(False)
        game.place_start(self.E)
        S.cam = max(0, min(self.max_cam(), cam))
        self.mm_img = None

    def max_cam(self):
        return max(0, self.E["w"] * T - VW / K)

    # ------------------------------------------------------------ helpers
    def toast(self, msg):
        self.toast_msg, self.toast_t = msg, time.perf_counter()

    def snapshot(self):
        self.undo.append(copy.deepcopy(self.E))
        if len(self.undo) > 120:
            self.undo.pop(0)
        self.redo.clear()

    def do_undo(self):
        if not self.undo:
            self.toast("Nothing to undo.")
            return
        self.redo.append(copy.deepcopy(self.E))
        self.E = self.undo.pop()
        self.sync()
        levels.save_draft(self.E)

    def do_redo(self):
        if not self.redo:
            self.toast("Nothing to redo.")
            return
        self.undo.append(copy.deepcopy(self.E))
        self.E = self.redo.pop()
        self.sync()
        levels.save_draft(self.E)

    def dirty(self):
        return self.saved_snapshot is None or self.saved_snapshot != self.E

    def cell_at(self, x, y):
        if not (TOP <= y < VIEW_B):
            return None
        wx = x / K + round(S.cam)
        wy = (y - TOP) / K
        return (math.floor(wx / T), math.floor(wy / T))

    def en_at(self, x, y):
        for i, q in enumerate(self.E["enemies"]):
            if q["x"] == x and q["y"] == y:
                return i
        return -1

    def coin_at(self, x, y):
        for i, c in enumerate(self.E["coins"]):
            if c[0] == x and c[1] == y:
                return i
        return -1

    # ------------------------------------------------------------ editing (ported from the original edApply)
    def set_tile(self, x, y, ch):
        E = self.E
        E["g"][y][x] = ch
        if ch != "?" or self.q == "coin":
            E["contents"].pop((x, y), None)
        if ch == "?" and self.q != "coin":
            E["contents"][(x, y)] = self.q
        if ch != ".":
            i = self.en_at(x, y)
            if i >= 0:
                E["enemies"].pop(i)
            i = self.coin_at(x, y)
            if i >= 0:
                E["coins"].pop(i)
        else:
            i = self.en_at(x, y - 1)
            if i >= 0:
                E["enemies"].pop(i)

    def apply(self, c, tool, first):
        E = self.E
        x, y = c
        if x < 0 or y < 0 or x >= E["w"] or y >= EH:
            return
        g = E["g"]
        if tool in TILE_OF:
            if [x, y] == E["start"]:
                if first:
                    self.toast("Can't build on the start.")
                return
            ch = self.tile_char(tool)
            if g[y][x] != ch or (tool == "q" and E["contents"].get((x, y)) != (None if self.q == "coin" else self.q)):
                self.set_tile(x, y, ch)
        elif tool == "coin":
            if g[y][x] == "." and self.coin_at(x, y) < 0 and self.en_at(x, y) < 0:
                E["coins"].append([x, y])
        elif tool in ("ant", "nut"):
            if not first:
                return
            if g[y][x] != "." or y + 1 >= EH or g[y + 1][x] == ".":
                self.toast("Enemies need an empty cell with solid ground under it.")
                return
            i = self.en_at(x, y)
            if i >= 0:
                E["enemies"].pop(i)
            E["enemies"].append({"k": tool, "x": x, "y": y, "d": self.face})
        elif tool == "start":
            if g[y][x] == ".":
                E["start"] = [x, y]
            elif first:
                self.toast("The start needs an empty cell.")
        elif tool == "goal":
            E["goal"] = x
        elif tool == "boss":
            if not first:
                return
            if x > E["w"] - 3:
                self.toast("Too close to the edge for the boss.")
                return
            E["boss"] = {"x": x, "ar0": max(0, x - 10), "ar1": min(E["w"] - 1, x + 5)}
        elif tool == "arena":
            b = E["boss"]
            if not b:
                if first:
                    self.toast("Place a boss first.")
                return
            if abs(x - b["ar0"]) <= abs(x - b["ar1"]):
                b["ar0"] = min(x, b["x"])
            else:
                b["ar1"] = max(x, b["x"] + 2)
        elif tool == "erase":
            i = self.en_at(x, y)
            if i >= 0:
                E["enemies"].pop(i)
            elif (i := self.coin_at(x, y)) >= 0:
                E["coins"].pop(i)
            elif g[y][x] != ".":
                self.set_tile(x, y, ".")
            elif E["boss"] and E["boss"]["x"] <= x <= E["boss"]["x"] + 1 and 8 <= y <= 9:
                E["boss"] = None
            elif E["goal"] is not None and E["goal"] <= x <= E["goal"] + 2 and 3 <= y <= 9:
                E["goal"] = None

    def cells_between(self, a, b):
        x, y = a
        dx, dy = abs(b[0] - x), abs(b[1] - y)
        sx, sy = (1 if x < b[0] else -1), (1 if y < b[1] else -1)
        e = dx - dy
        out = []
        for _ in range(500):
            out.append((x, y))
            if (x, y) == tuple(b):
                break
            e2 = 2 * e
            if e2 > -dy:
                e -= dy
                x += sx
            if e2 < dx:
                e += dx
                y += sy
        return out

    def pick(self, c):
        """Eyedropper: choose the tool for whatever is under the cursor."""
        x, y = c
        E = self.E
        if not (0 <= x < E["w"] and 0 <= y < EH):
            return
        i = self.en_at(x, y)
        if i >= 0:
            self.set_tool(E["enemies"][i]["k"])
            self.face = E["enemies"][i]["d"]
        elif self.coin_at(x, y) >= 0:
            self.set_tool("coin")
        else:
            ch = E["g"][y][x]
            if ch == "v":
                self.set_tool("spike")
                self.spike_down = True
            else:
                for tid, ct in TILE_OF.items():
                    if ct == ch:
                        self.set_tool(tid)
                        if ch == "?":
                            self.q = E["contents"].get((x, y), "coin")
                        if ch == "x":
                            self.spike_down = False
                        break
                else:
                    return
        self.toast("Picked " + self.tool_name(self.tool) + ".")

    def set_tool(self, t):
        self.tool = t
        self.app.menu_sfx("move")

    def tool_name(self, tid):
        """Blocks are named after what they look like in the current theme."""
        th = self.E["theme"] if self.E else 0
        return THEMED_NAMES.get(tid, {}).get(th) or dict((t[0], t[1]) for t in TOOLS)[tid]

    def tile_char(self, tool):
        if tool == "spike":
            return "v" if self.spike_down else "x"
        return TILE_OF[tool]

    # ------------------------------------------------------------ level properties (ported from the original toolbar)
    def set_theme(self, d):
        self.snapshot()
        E = self.E
        v = (E["theme"] + d) % len(THEMES)
        E["theme"] = v
        has_ceiling = any("c" in E["g"][y] for y in (0, 1))
        if v in CAVES and not has_ceiling:
            for x in range(E["w"]):
                E["g"][0][x] = E["g"][1][x] = "c"
        if v not in CAVES and all(ch == "c" for y in (0, 1) for ch in E["g"][y]):
            for x in range(E["w"]):
                E["g"][0][x] = E["g"][1][x] = "."
        self.sync()
        levels.save_draft(E)

    def set_width(self, nw):
        E = self.E
        nw = max(24, min(400, nw))
        if nw == E["w"]:
            return
        self.snapshot()
        ow = E["w"]
        if nw > ow:
            for y in range(EH):
                src = E["g"][y][ow - 1] if (y < 2 or y > 9) else "."
                E["g"][y].extend([src] * (nw - ow))
        else:
            for r in E["g"]:
                del r[nw:]
            E["coins"] = [c for c in E["coins"] if c[0] < nw]
            E["enemies"] = [q for q in E["enemies"] if q["x"] < nw]
            E["contents"] = {k: v for k, v in E["contents"].items() if k[0] < nw}
            E["start"][0] = min(E["start"][0], nw - 1)
            if E["goal"] is not None:
                E["goal"] = min(E["goal"], nw - 1)
            if E["boss"]:
                b = E["boss"]
                b["x"], b["ar0"], b["ar1"] = min(b["x"], nw - 3), min(b["ar0"], nw - 1), min(b["ar1"], nw - 1)
        E["w"] = nw
        self.sync()
        levels.save_draft(E)

    def set_time(self, d):
        self.E["time"] = max(30, min(999, self.E["time"] + d))
        levels.save_draft(self.E)

    # ------------------------------------------------------------ file actions
    def save(self):
        try:
            self.path = levels.save_level(self.E, self.path)
        except OSError as e:
            self.toast(f"Couldn't save: {e.strerror}.")
            return
        self.saved_snapshot = copy.deepcopy(self.E)
        levels.save_draft(self.E)
        self.toast(f"Saved to levels\\{self.path.name}")
        self.app.menu_sfx("ok")

    def copy_json(self):
        import json
        if clip_put(json.dumps(levels.serialize(self.E))):
            self.toast("Level copied to the clipboard as JSON.")
        else:
            self.toast("Couldn't reach the clipboard.")

    def paste_json(self):
        src = clip_get()
        try:
            L = levels.parse_level(src)
        except ValueError as e:
            self.toast(f"Clipboard isn't a level: {e}")
            return
        self.snapshot()
        self.E = L
        self.path = None
        self.saved_snapshot = None
        S.cam = 0
        self.sync()
        levels.save_draft(self.E)
        self.toast(f'Imported "{L["name"]}". Ctrl+Z brings the old one back.')

    def new(self):
        self.snapshot()
        self.E = levels.new_level(self.E["theme"])
        self.path = None
        self.saved_snapshot = None
        S.cam = 0
        self.sync()
        levels.save_draft(self.E)
        self.toast("New level. Ctrl+Z brings the old one back.")

    def open_folder(self):
        levels.LEVEL_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(levels.LEVEL_DIR)
        except OSError:
            self.toast(str(levels.LEVEL_DIR))

    def start_typing(self):
        self.typing = True
        pygame.key.start_text_input()

    def stop_typing(self):
        self.typing = False
        pygame.key.stop_text_input()
        self.E["name"] = self.E["name"].strip()[:24] or "My Level"
        levels.save_draft(self.E)

    # ------------------------------------------------------------ input
    def handle(self, ev):
        t = ev.type
        if self.typing:
            if t == pygame.TEXTINPUT:
                self.E["name"] = (self.E["name"] + ev.text)[:24]
            elif t == pygame.KEYDOWN:
                if ev.key == pygame.K_BACKSPACE:
                    self.E["name"] = self.E["name"][:-1]
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_TAB):
                    self.stop_typing()
            elif t == pygame.MOUSEBUTTONDOWN:
                self.stop_typing()
                self.handle(ev)
            return
        if self.help:
            if t in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.help = False
            return
        if self.picker:
            if t == pygame.MOUSEMOTION:
                self.mouse = self.logical(ev.pos)
            elif t == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.picker_click(*self.logical(ev.pos))
            elif t == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.picker = False
            elif t == pygame.KEYDOWN and pygame.K_1 <= ev.key <= pygame.K_8:
                self.set_theme(ev.key - pygame.K_1 - self.E["theme"])
                self.picker = False
            return
        if t == pygame.KEYDOWN:
            self.key(ev)
        elif t == pygame.KEYUP:
            if ev.key in (pygame.K_LEFT, pygame.K_a):
                self.scroll["left"] = False
            elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                self.scroll["right"] = False
            elif ev.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.scroll["fast"] = False
            elif ev.key == pygame.K_SPACE:
                self.scroll["space"] = False
        elif t == pygame.MOUSEMOTION:
            self.motion(ev)
        elif t == pygame.MOUSEBUTTONDOWN:
            self.press(ev)
        elif t == pygame.MOUSEBUTTONUP:
            self.release(ev)
        elif t == pygame.MOUSEWHEEL:
            step = (ev.x - ev.y) * (140 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 48)
            S.cam = max(0, min(self.max_cam(), S.cam + step))

    def key(self, ev):
        k, mods = ev.key, ev.mod
        ctrl = mods & pygame.KMOD_CTRL
        if ctrl:
            if k == pygame.K_z:
                self.do_redo() if mods & pygame.KMOD_SHIFT else self.do_undo()
            elif k == pygame.K_y:
                self.do_redo()
            elif k == pygame.K_s:
                self.save()
            elif k == pygame.K_c:
                self.copy_json()
            elif k == pygame.K_v:
                self.paste_json()
            elif k == pygame.K_n:
                self.new()
            elif k == pygame.K_o:
                self.open_folder()
            return
        if k == pygame.K_ESCAPE:
            self.exit()
        elif k == pygame.K_F1:
            self.help = True
        elif k == pygame.K_F2:
            self.start_typing()
        elif k in (pygame.K_LEFT, pygame.K_a):
            self.scroll["left"] = True
        elif k in (pygame.K_RIGHT, pygame.K_d):
            self.scroll["right"] = True
        elif k in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            self.scroll["fast"] = True
        elif k == pygame.K_SPACE:
            self.scroll["space"] = True
        elif k == pygame.K_HOME:
            S.cam = 0
        elif k == pygame.K_END:
            S.cam = self.max_cam()
        elif k == pygame.K_r:
            if self.tool == "spike":
                self.flip()
                self.toast("Spikes now point " + ("down." if self.spike_down else "up."))
            else:
                self.face = -self.face
                self.toast("Enemies now face " + ("right." if self.face > 0 else "left."))
        elif k == pygame.K_q:
            self.q = QNAMES[(QNAMES.index(self.q) + 1) % 3]
            self.toast(f"? blocks now hold a {self.q}.")
        elif k == pygame.K_g:
            self.show_grid = not self.show_grid
        elif k == pygame.K_t:
            self.test()
        elif k == pygame.K_LEFTBRACKET:
            self.set_width(self.E["w"] - 8)
        elif k == pygame.K_RIGHTBRACKET:
            self.set_width(self.E["w"] + 8)
        elif k in TOOL_BY_KEY:
            self.set_tool(TOOL_BY_KEY[k])

    def logical(self, pos):
        return self.app.to_logical(pos)

    def motion(self, ev):
        x, y = self.logical(ev.pos)
        self.mouse = (x, y)
        c = self.cell_at(x, y)
        self.hover = c
        if self.pan:
            S.cam = max(0, min(self.max_cam(), self.pan[1] - (x - self.pan[0]) / K))
            return
        if self.mm_drag:
            self.minimap_jump(x)
            return
        if self.box and c:
            self.box[1] = c
            return
        if self.paint and c and self.last and c != self.last and self.paint not in ("ant", "nut", "boss"):
            for q in self.cells_between(self.last, c)[1:]:
                self.apply(q, self.paint, False)
            self.last = c
            self.sync()

    def press(self, ev):
        x, y = self.logical(ev.pos)
        self.mouse = (x, y)
        if ev.button == 1:
            for (l, t, r, b), fn, _tip in self.buttons:
                if l <= x <= r and t <= y <= b:
                    fn()
                    return
            mx, my, mw, mh = MM
            if mx <= x <= mx + mw and my - 2 <= y <= my + mh + 2:
                self.mm_drag = True
                self.minimap_jump(x)
                return
        c = self.cell_at(x, y)
        if c is None:
            return
        mods = pygame.key.get_mods()
        if ev.button == 2 or (ev.button == 1 and self.scroll["space"]):
            self.pan = (x, S.cam)
            return
        if ev.button == 1 and mods & pygame.KMOD_ALT:
            self.pick(c)
            return
        tool = "erase" if ev.button == 3 else (self.tool if ev.button == 1 else None)
        if tool is None:
            return
        self.stroke_start = copy.deepcopy(self.E)
        if mods & pygame.KMOD_SHIFT and tool in BOX_TOOLS:
            self.box = [c, c, tool]
            return
        self.paint = tool
        self.last = c
        self.apply(c, tool, True)
        self.sync()

    def release(self, ev):
        if self.box:
            (x0, y0), (x1, y1), tool = self.box
            for yy in range(min(y0, y1), max(y0, y1) + 1):
                for xx in range(min(x0, x1), max(x0, x1) + 1):
                    self.apply((xx, yy), tool, False)
            self.box = None
            self.sync()
        if self.stroke_start is not None:
            if self.stroke_start != self.E:
                self.undo.append(self.stroke_start)
                if len(self.undo) > 120:
                    self.undo.pop(0)
                self.redo.clear()
                levels.save_draft(self.E)
            self.stroke_start = None
        self.paint = None
        self.pan = None
        self.mm_drag = False

    def minimap_jump(self, x):
        mx, _, mw, _ = MM
        col = (x - mx) / mw * self.E["w"]
        S.cam = max(0, min(self.max_cam(), col * T - VW / K / 2))

    def update(self):
        sp = 22 if self.scroll["fast"] else 9
        if self.scroll["left"]:
            S.cam -= sp
        if self.scroll["right"]:
            S.cam += sp
        S.cam = max(0, min(self.max_cam(), S.cam))

    # ------------------------------------------------------------ drawing
    def draw(self):
        art.set_view(K, TOP)
        art.draw_world()
        self.draw_overlays()
        c = art.g
        c.setTransform(art.RS, 0, 0, art.RS, 0, 0)
        self.buttons = []
        self.draw_top()
        self.draw_bottom()
        self.draw_toast()
        self.draw_tooltip()
        if self.help:
            self.draw_help()
        if self.picker:
            self.draw_picker()

    # ---- theme picker
    def theme_button(self, x, y, w):
        c = art.g
        th = self.E["theme"]
        text("THEME", x, y + 7.5, 8, "800 Sniglet", MUTED, align="left", spacing=.8)
        bx = x + 34
        bw = w - 34
        mx, my = self.mouse
        hot = bx <= mx <= bx + bw and y <= my <= y + 15
        art.rr(bx, y, bw, 15, 4)
        c.fillStyle = BTN_HI if hot else "#170c05"
        c.fill()
        sky, ground = SKY[th], GROUND[th]
        art.rr(bx + 3, y + 3, 9, 9, 2)
        c.fillStyle = "rgb(%d,%d,%d)" % sky
        c.fill()
        c.fillStyle = "rgb(%d,%d,%d)" % ground
        c.fillRect(bx + 3, y + 8.5, 9, 3.5)
        text(THEMES[th], bx + 15, y + 8, 8, "800 Sniglet", CREAM, align="left")
        c.fillStyle = GOLD
        c.beginPath()
        c.moveTo(bx + bw - 10, y + 6)
        c.lineTo(bx + bw - 4, y + 6)
        c.lineTo(bx + bw - 7, y + 10)
        c.closePath()
        c.fill()
        self.buttons.append(((bx, y, bx + bw, y + 15), self.open_picker, "Choose the theme: background, blocks and music"))

    def open_picker(self):
        self.picker = True
        self.app.menu_sfx("ok")

    def picker_cells(self):
        w, h = 104, 92
        x0, y0 = VW / 2 - (4 * w + 3 * 8) / 2, 92
        return [(i, x0 + (i % 4) * (w + 8), y0 + (i // 4) * (h + 10), w, h) for i in range(len(THEMES))]

    def draw_picker(self):
        c = art.g
        ui_mod.dim(.6)
        ui_mod.card(VW / 2 - 236, 52, 472, 266)
        text("CHOOSE A THEME", VW / 2 + 1.5, 74 + 1.5, 19, "'Bagel Fat One'", OL)
        text("CHOOSE A THEME", VW / 2, 74, 19, "'Bagel Fat One'", RED)
        mx, my = self.mouse
        for i, x, y, w, h in self.picker_cells():
            img = self.theme_preview(i, w, h - 20)
            on = i == self.E["theme"]
            hot = x <= mx <= x + w and y <= my <= y + h
            art.rr(x - 2, y - 2, w + 4, h + 4, 8)
            c.fillStyle = RED if on else (GOLD if hot else OL)
            c.fill()
            c.drawImageAt(img, x, y)
            text(THEMES[i], x + w / 2, y + h - 9, 10, "800 Sniglet", RED if on else OL)
        text("Click a theme, or press 1-8. Esc closes.", VW / 2, 304, 9.5, "Sniglet", "#8a5a2b")

    def theme_preview(self, th, w, h):
        """A little postcard of a theme: its real background, ground, a block and a jelly pad."""
        key = ("theme", th, w, h, art.RS)
        img = self.icons.get(key)
        if img is not None:
            return img
        surf, cv = offscreen(w * art.RS, (h + 20) * art.RS, art.RS)
        saved = (art.g, S.TH, S.cam, art.SW, S.grid, S.W, S.P)
        art.g = cv
        S.TH, S.cam, S.W = th, 0, 12
        S.grid = [[0] * 12 for _ in range(12)]
        for x in range(12):
            S.grid[10][x] = S.grid[11][x] = 1
        S.grid[8][7] = S.grid[8][8] = S.grid[9][7] = S.grid[9][8] = 5
        S.grid[9][4] = 9
        try:
            art.rr(0, 0, w, h + 20, 7)
            cv.clip()
            cv.save()
            cv.scale(w / (12 * T), h / (12 * T))
            art.SW = 12 * T
            art.background()
            for (tx, ty) in ((x, y) for y in range(8, 12) for x in range(12)):
                v = S.grid[ty][tx]
                if v:
                    art.draw_tile(v, tx * T, ty * T, tx, ty)
            cv.restore()
            cv.fillStyle = "rgba(255,243,214,.95)"
            cv.fillRect(0, h, w, 20)
        finally:
            art.g, S.TH, S.cam, art.SW, S.grid, S.W, S.P = saved
        surf.flush()
        self.icons[key] = surf
        return surf

    def picker_click(self, x, y):
        for i, cx, cy, w, h in self.picker_cells():
            if cx <= x <= cx + w and cy <= y <= cy + h:
                self.set_theme(i - self.E["theme"])
                self.picker = False
                self.toast(f"Theme: {THEMES[i]}")
                return
        if not (VW / 2 - 236 <= x <= VW / 2 + 236 and 52 <= y <= 318):
            self.picker = False

    def draw_overlays(self):
        c = art.g
        E = self.E
        rc = round(S.cam)
        c.setTransform(art.RS * K, 0, 0, art.RS * K, 0, TOP * art.RS)
        c.save()
        c.beginPath()
        c.rect(0, 0, VW / K, VH)
        c.clip()
        c.translate(-rc, 0)
        x0 = rc // T
        x1 = min(E["w"] - 1, x0 + int(VW / K / T) + 1)
        if self.show_grid:
            c.strokeStyle = "rgba(255,255,255,.16)"
            c.lineWidth = 1 / K
            c.beginPath()
            for x in range(x0, x1 + 2):
                c.moveTo(x * T, 0)
                c.lineTo(x * T, VH)
            for y in range(EH + 1):
                c.moveTo(rc, y * T)
                c.lineTo(rc + VW / K, y * T)
            c.stroke()
        if E["w"] * T < rc + VW / K:
            c.fillStyle = "rgba(10,6,4,.75)"
            c.fillRect(E["w"] * T, 0, VW / K + T, VH)
            c.fillStyle = "rgba(255,243,214,.5)"
            c.fillRect(E["w"] * T, 0, 2, VH)
        for (cx, cy), what in E["contents"].items():
            if x0 <= cx <= x1:
                (art.pizza_art if what == "pizza" else art.cookie_art)(cx * T + 25, cy * T + 7, 6)
        P = S.P
        self.tag("START", P.x + P.w / 2, P.y - 7, "#9dff8a")
        if E["goal"] is not None:
            self.tag("GOAL", E["goal"] * T + 16, 46, GOLD)
        for e in S.enemies:
            if e.x < rc - 40 or e.x > rc + VW / K + 40:
                continue
            d = 1 if e.vx > 0 else -1
            cx, cy = e.x + e.w / 2, e.y - 7
            c.fillStyle = GOLD
            c.strokeStyle = OL
            c.lineWidth = 1.4
            c.beginPath()
            c.moveTo(cx + d * 7, cy)
            c.lineTo(cx - d * 3, cy - 5)
            c.lineTo(cx - d * 3, cy + 5)
            c.closePath()
            c.fill()
            c.stroke()
        if E["boss"] and S.boss:
            b = E["boss"]
            self.tag("BOSS", S.boss.x + S.boss.w / 2, S.boss.y - 8, "#ff8a70")
            c.ctx.set_dash([7, 6])
            c.strokeStyle = "rgba(255,90,70,.9)"
            c.lineWidth = 2.4
            for xx in (b["ar0"] * T, (b["ar1"] + 1) * T):
                c.beginPath()
                c.moveTo(xx, 0)
                c.lineTo(xx, VH)
                c.stroke()
            c.ctx.set_dash([])
            self.tag("ARENA →", b["ar0"] * T + 42, 22, "#ff8a70")
            self.tag("← ARENA", (b["ar1"] + 1) * T - 42, 22, "#ff8a70")
        if self.box:
            (bx0, by0), (bx1, by1), tool = self.box
            l, r = min(bx0, bx1), max(bx0, bx1)
            t, b = min(by0, by1), max(by0, by1)
            col = "rgba(255,106,90," if tool == "erase" else "rgba(255,216,77,"
            c.fillStyle = col + ".22)"
            c.fillRect(l * T, t * T, (r - l + 1) * T, (b - t + 1) * T)
            c.strokeStyle = col + ".95)"
            c.lineWidth = 2.5
            c.strokeRect(l * T + 1, t * T + 1, (r - l + 1) * T - 2, (b - t + 1) * T - 2)
            self.tag(f"{r - l + 1} × {b - t + 1}", (l + r + 1) * T / 2, t * T - 6, CREAM)
        elif self.hover and not self.pan and 0 <= self.hover[0] < E["w"] and 0 <= self.hover[1] < EH:
            hx, hy = self.hover
            c.save()
            c.globalAlpha = .55
            if self.tool in TILE_OF:
                c.drawImageAt(art.tile_img(levels.CHM[self.tile_char(self.tool)], hx, hy), hx * T, hy * T)
            elif self.tool == "coin":
                c.fillStyle = GOLD
                c.beginPath()
                c.ellipse(hx * T + 16, hy * T + 16, 7, 9, 0, 0, 7)
                c.fill()
            elif self.tool in ("ant", "nut"):
                (art.draw_ant if self.tool == "ant" else art.draw_nut)(
                    game.mk_enemy({"k": self.tool, "x": hx, "y": hy, "d": self.face}))
            c.restore()
            c.strokeStyle = "#ff6a5a" if self.tool == "erase" else "#fff3b0"
            c.lineWidth = 2.5
            c.strokeRect(hx * T + 1, hy * T + 1, T - 2, T - 2)
        c.restore()

    def tag(self, s, x, y, col):
        text(s, x, y, 11, "'Bagel Fat One'", col, outline=3, ol="rgba(0,0,0,.75)")

    # ---- panels
    def button(self, rect, label, fn, tip, kind="normal", active=False, size=10):
        c = art.g
        x, y, w, h = rect
        mx, my = self.mouse
        hot = x <= mx <= x + w and y <= my <= y + h
        base = {"normal": BTN, "go": GREEN, "danger": "#8a2a1a"}[kind]
        art.rr(x, y + 2, w, h, 5)
        c.fillStyle = "#140a04"
        c.fill()
        art.rr(x, y + (1 if hot else 0), w, h, 5)
        c.fillStyle = BTN_HI if (hot and kind == "normal") else base
        c.fill()
        if active:
            c.lineWidth = 1.6
            c.strokeStyle = GOLD
            c.stroke()
        text(label, x + w / 2, y + h / 2 + 1.5 + (1 if hot else 0), size, "'Luckiest Guy'", CREAM, spacing=.6)
        self.buttons.append(((x, y, x + w, y + h), fn, tip))

    def stepper(self, x, y, w, label, value, dec, inc, tip):
        c = art.g
        text(label, x, y + 7.5, 8, "800 Sniglet", MUTED, align="left", spacing=.8)
        c.font = "800 8px Sniglet"
        lx = x + c.measureText(label) + 5
        bw = w - (lx - x)
        art.rr(lx, y, bw, 15, 4)
        c.fillStyle = "#170c05"
        c.fill()
        text(value, lx + bw / 2, y + 8, 9.5, "800 Sniglet", CREAM)
        for d, fn in ((-1, dec), (1, inc)):
            ax = lx + 7 if d < 0 else lx + bw - 7
            c.fillStyle = GOLD
            c.beginPath()
            c.moveTo(ax + 3 * d, y + 7.5)
            c.lineTo(ax - 2 * d, y + 4)
            c.lineTo(ax - 2 * d, y + 11)
            c.closePath()
            c.fill()
            half = (lx, y, lx + bw / 2, y + 15) if d < 0 else (lx + bw / 2, y, lx + bw, y + 15)
            self.buttons.append((half, fn, tip))

    def draw_top(self):
        c = art.g
        E = self.E
        c.fillStyle = PANEL
        c.fillRect(0, 0, VW, TOP)
        c.fillStyle = "#140a04"
        c.fillRect(0, TOP - 1.5, VW, 1.5)
        # name
        art.rr(6, 3, 140, 15, 4)
        c.fillStyle = "#170c05"
        c.fill()
        if self.typing:
            c.lineWidth = 1.4
            c.strokeStyle = GOLD
            c.stroke()
        name = E["name"] + ("|" if self.typing and int(time.perf_counter() * 2) % 2 == 0 else "")
        text(name, 12, 11, 10, "'Luckiest Guy'", CREAM, align="left", spacing=.5)
        if not self.typing:
            c.fillStyle = MUTED
            c.save()
            c.translate(138, 10.5)
            c.rotate(.8)
            c.fillRect(-4, -1.2, 8, 2.4)
            c.restore()
        self.buttons.append(((6, 3, 146, 18), self.start_typing, "Rename the level (F2)"))
        self.theme_button(153, 3, 124)
        self.stepper(284, 3, 72, "WIDTH", str(E["w"]), lambda: self.set_width(E["w"] - 8),
                     lambda: self.set_width(E["w"] + 8), "Level width in tiles, 24 to 400 ([ and ])")
        self.stepper(363, 3, 64, "TIME", str(E["time"]), lambda: self.set_time(-10), lambda: self.set_time(10),
                     "Seconds on the clock")
        dirty = self.dirty()
        c.fillStyle = "#ff9a3d" if dirty else "#8fdc63"
        c.beginPath()
        c.arc(439, 10.5, 3, 0, 7)
        c.fill()
        text("UNSAVED" if dirty else "SAVED", 445, 11, 8, "800 Sniglet", MUTED, align="left", spacing=.6)
        self.draw_minimap()

    def build_minimap(self):
        E = self.E
        w = E["w"]
        th = E["theme"]
        arr = np.empty((EH, w, 3), np.uint8)
        arr[:] = SKY[th]
        for y in range(EH):
            row = E["g"][y]
            for x, ch in enumerate(row):
                if ch != ".":
                    col = MM_COLORS[ch] or GROUND[th]
                    arr[y, x] = col
        for cx, cy in E["coins"]:
            arr[cy, cx] = (255, 216, 77)
        for q in E["enemies"]:
            arr[q["y"], q["x"]] = (230, 70, 50) if q["k"] == "ant" else (190, 120, 60)
        if E["goal"] is not None:
            arr[2:10, E["goal"]] = (255, 246, 220)
        if E["boss"]:
            bx = E["boss"]["x"]
            arr[8:10, bx:bx + 2] = (232, 53, 43)
        sx, sy = E["start"]
        arr[sy, sx] = (110, 230, 100)
        bgra = np.empty((EH, w, 4), np.uint8)
        bgra[..., 0], bgra[..., 1], bgra[..., 2], bgra[..., 3] = arr[..., 2], arr[..., 1], arr[..., 0], 255
        self.mm_buf = bytearray(bgra.tobytes())
        self.mm_img = cairo.ImageSurface.create_for_data(memoryview(self.mm_buf), cairo.FORMAT_ARGB32, w, EH, w * 4)

    def draw_minimap(self):
        if self.mm_img is None:
            self.build_minimap()
        c = art.g
        ctx = c.ctx
        mx, my, mw, mh = MM
        w = self.E["w"]
        ctx.save()
        ctx.translate(mx, my)
        ctx.scale(mw / w, mh / EH)
        ctx.set_source_surface(self.mm_img, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_NEAREST)
        ctx.new_path()
        ctx.rectangle(0, 0, w, EH)
        ctx.fill()
        ctx.restore()
        vx = mx + S.cam / T * mw / w
        vw = min(mw, VW / K / T * mw / w)
        c.strokeStyle = CREAM
        c.lineWidth = 1.4
        c.strokeRect(vx, my - .5, vw, mh + 1)
        c.fillStyle = "rgba(255,243,214,.12)"
        c.fillRect(vx, my - .5, vw, mh + 1)

    def draw_bottom(self):
        c = art.g
        y0 = PANEL_Y
        c.fillStyle = "#140a04"
        c.fillRect(0, y0 - 1.5, VW, 1.5)
        c.fillStyle = PANEL
        c.fillRect(0, y0, VW, VH - y0)
        names = {t[0]: self.tool_name(t[0]) for t in TOOLS}
        for i, (tid, name, key, _ch) in enumerate(TOOLS):
            x, y = 5 + i * 26, y0 + 5
            sel = tid == self.tool
            art.rr(x, y, 24, 28, 5)
            c.fillStyle = BTN_HI if sel else BTN
            c.fill()
            if sel:
                c.lineWidth = 2
                c.strokeStyle = GOLD
                c.stroke()
            c.drawImage(self.icon(tid), x + 12, y + 13)
            text(key, x + 20, y + 24, 7, "800 Sniglet", GOLD if sel else MUTED, outline=2, ol="#140a04")
            self.buttons.append(((x, y, x + 24, y + 28), (lambda t=tid: self.set_tool(t)),
                                 f"{names[tid]} ({key})" + ("  NEW" if tid in ("crumble", "jelly", "spike") else "")))
        # context box for the current tool
        bx, by, bw = 424, y0 + 4, 82
        art.rr(bx, by, bw, 30, 6)
        c.fillStyle = "#170c05"
        c.fill()
        text(names[self.tool].upper(), bx + bw / 2, by + 8, 8.5, "'Luckiest Guy'", GOLD, spacing=.6)
        if self.tool == "q":
            label, fn, tip = "HOLDS " + self.q.upper(), self.cycle_q, "Click or press Q to change"
        elif self.tool in ("ant", "nut"):
            label, fn, tip = "FACING " + ("RIGHT" if self.face > 0 else "LEFT"), self.flip, "Click or press R to flip"
        elif self.tool == "spike":
            label, fn, tip = "POINTING " + ("DOWN" if self.spike_down else "UP"), self.flip, "Click or press R to flip"
        elif self.tool in BOX_TOOLS:
            label, fn, tip = "SHIFT = BOX", None, HINTS[self.tool]
        else:
            label, fn, tip = "CLICK TO PLACE", None, HINTS[self.tool]
        text(label, bx + bw / 2, by + 21, 8, "800 Sniglet", CREAM)
        self.buttons.append(((bx, by, bx + bw, by + 30), fn or (lambda: None), tip))
        # status line
        h = self.hover
        if h and 0 <= h[0] < self.E["w"] and 0 <= h[1] < EH:
            status = f"col {h[0]}  ·  row {h[1]}"
        else:
            status = f"{self.E['w']} columns"
        text(status, 8, y0 + 46, 9, "800 Sniglet", CREAM, align="left")
        text("F1 shortcuts", 8, y0 + 59, 8, "Sniglet", MUTED, align="left")
        # actions
        x = 96
        y = y0 + 41
        for label, w, fn, tip, kind in (
                ("UNDO", 34, self.do_undo, "Undo (Ctrl+Z)", "normal"),
                ("REDO", 34, self.do_redo, "Redo (Ctrl+Y)", "normal"),
                ("GRID", 32, self.toggle_grid, "Show or hide the grid (G)", "normal"),
                ("PLAY ▶", 54, self.test, "Play-test this level (T)", "go"),
                ("SAVE", 36, self.save, "Save to your levels folder (Ctrl+S)", "normal"),
                ("COPY", 36, self.copy_json, "Copy the level as JSON to share it (Ctrl+C)", "normal"),
                ("PASTE", 40, self.paste_json, "Load a level from JSON on the clipboard (Ctrl+V)", "normal"),
                ("FOLDER", 44, self.open_folder, "Open your levels folder (Ctrl+O)", "normal"),
                ("NEW", 32, self.new, "Start a new level (Ctrl+N)", "normal"),
                ("EXIT", 34, self.exit, "Back to the title screen (Esc). Your draft is kept.", "danger")):
            self.button((x, y, w, 20), label, fn, tip, kind, active=(label == "GRID" and self.show_grid))
            x += w + 4

    def cycle_q(self):
        self.q = QNAMES[(QNAMES.index(self.q) + 1) % 3]

    def flip(self):
        if self.tool == "spike":
            self.spike_down = not self.spike_down
        else:
            self.face = -self.face

    def toggle_grid(self):
        self.show_grid = not self.show_grid

    def draw_toast(self):
        if not self.toast_msg:
            return
        age = time.perf_counter() - self.toast_t
        if age > 3.2:
            return
        a = min(1, (3.2 - age) / .4)
        c = art.g
        c.font = "800 10px Sniglet"
        w = c.measureText(self.toast_msg) + 26
        x, y = VW / 2 - w / 2, TOP + 8
        c.save()
        c.globalAlpha = a
        art.rr(x, y + 2, w, 20, 10)
        c.fillStyle = "rgba(0,0,0,.5)"
        c.fill()
        art.rr(x, y, w, 20, 10)
        c.fillStyle = PANEL
        c.fill()
        c.lineWidth = 1.4
        c.strokeStyle = GOLD
        c.stroke()
        c.restore()
        text(self.toast_msg, VW / 2, y + 10.5, 10, "800 Sniglet", CREAM, alpha=a)

    def draw_tooltip(self):
        mx, my = self.mouse
        for (l, t, r, b), _fn, tip in self.buttons:
            if l <= mx <= r and t <= my <= b and tip:
                c = art.g
                c.font = "800 9px Sniglet"
                w = c.measureText(tip) + 14
                x = max(4, min(VW - w - 4, (l + r) / 2 - w / 2))
                y = t - 20 if t > VH / 2 else b + 5
                art.rr(x, y, w, 15, 5)
                c.fillStyle = CREAM
                c.fill()
                c.lineWidth = 1.2
                c.strokeStyle = OL
                c.stroke()
                text(tip, x + w / 2, y + 8, 9, "800 Sniglet", OL)
                return

    def draw_help(self):
        ui_mod.dim(.6)
        w, h = 400, 46 + len(SHORTCUTS) * 15 + 26
        x, y = VW / 2 - w / 2, VH / 2 - h / 2
        ui_mod.card(x, y, w, h)
        text("BUILDER SHORTCUTS", VW / 2 + 1.5, y + 25 + 1.5, 20, "'Bagel Fat One'", OL)
        text("BUILDER SHORTCUTS", VW / 2, y + 25, 20, "'Bagel Fat One'", RED)
        for i, (what, keys) in enumerate(SHORTCUTS):
            ry = y + 50 + i * 15
            text(what, x + 22, ry, 10.5, "800 Sniglet", OL, align="left")
            text(keys, x + w - 22, ry, 10.5, "800 Sniglet", "#8a5a2b", align="right")
        text("Press any key to close", VW / 2, y + h - 14, 9.5, "Sniglet", "#8a5a2b")

    # ---- tool icons, drawn with the real game art
    def icon(self, tid):
        key = (tid, self.E["theme"], art.RS)
        img = self.icons.get(key)
        if img is not None:
            return img
        size = 26
        surf, cv = offscreen(23 * art.RS, 23 * art.RS, art.RS)
        cv.scale(23 / size, 23 / size)
        saved = (art.g, S.P, S.boss, S.TH, S.state)
        art.g = cv
        S.TH = self.E["theme"]
        S.state = "edit"
        try:
            self._draw_icon(cv, tid, size)
        finally:
            art.g, S.P, S.boss, S.TH, S.state = saved
        surf.flush()
        self.icons[key] = surf
        return surf

    def _draw_icon(self, c, tid, size):
        if tid in TILE_OF:
            c.save()
            c.translate(1.5, 1.5)
            c.scale(.72, .72)
            art.draw_tile(levels.CHM[TILE_OF[tid]], 0, 0, -50, -50)
            c.restore()
        elif tid == "coin":
            for dx, dy in ((-4, 3), (5, -3)):
                cx, cy = size / 2 + dx, size / 2 + dy
                c.fillStyle = "#7a4a08"; c.beginPath(); c.ellipse(cx, cy, 6.2, 8, 0, 0, 7); c.fill()
                c.fillStyle = "#e0a626"; c.beginPath(); c.ellipse(cx, cy, 5, 6.8, 0, 0, 7); c.fill()
                c.fillStyle = "#ffd84d"; c.beginPath(); c.ellipse(cx - .5, cy - 1, 3.4, 5, 0, 0, 7); c.fill()
        elif tid == "ant":
            c.save(); c.translate(1, 6); c.scale(.74, .74)
            art.draw_ant(O(k="ant", x=3, y=2, w=26, h=20, vx=0, dead=0, f=1))
            c.restore()
        elif tid == "nut":
            c.save(); c.translate(2, 1); c.scale(.68, .68)
            art.draw_nut(O(k="nut", x=3, y=5, w=26, h=26, vx=0, dead=0, mode="walk", st=0, f=1))
            c.restore()
        elif tid == "start":
            c.save(); c.scale(.72, .72)
            S.P = O(x=7, y=3, w=22, h=28, vx=0, vy=0, ground=True, face=1, big=False, fire=False, inv=0, duck=0,
                    mk=2, mt=5)
            art.draw_player()
            c.restore()
        elif tid == "goal":
            c.fillStyle = OL; c.fillRect(6.5, 5, 3.4, 19)
            c.fillStyle = "#d9a25b"; c.fillRect(7.2, 5, 2, 19)
            c.save(); c.beginPath(); c.moveTo(9.5, 6); c.lineTo(22, 9); c.lineTo(9.5, 15); c.closePath(); c.clip()
            art.gingham(9, 5, 14, 11, 0, 0, .8, 3)
            c.restore()
            c.strokeStyle = OL; c.lineWidth = 1.2; c.beginPath(); c.moveTo(9.5, 6); c.lineTo(22, 9); c.lineTo(9.5, 15)
            c.stroke()
            art.cookie_art(8.2, 4.5, 3)
        elif tid == "boss":
            c.save(); c.translate(13, 25); c.scale(.36, .36); c.translate(-28, -64)
            S.P = O(x=999, y=0, w=1, h=1)
            S.boss = O(x=0, y=0, w=56, h=64, flash=0, cd=99, dead=0)
            art.draw_boss()
            c.restore()
        elif tid == "arena":
            c.strokeStyle = "#ff7a5e"; c.lineWidth = 2; c.ctx.set_dash([3, 2])
            for x in (4, 22):
                c.beginPath(); c.moveTo(x, 4); c.lineTo(x, 22); c.stroke()
            c.ctx.set_dash([])
            c.fillStyle = CREAM
            for d in (-1, 1):
                c.beginPath(); c.moveTo(13 + d * 7, 13); c.lineTo(13 + d * 2, 9); c.lineTo(13 + d * 2, 17); c.closePath()
                c.fill()
            c.fillRect(11, 12, 4, 2)
        elif tid == "erase":
            c.save(); c.translate(13, 13); c.rotate(-.6)
            art.rr(-9, -5, 18, 10, 2.5); c.fillStyle = "#ff8fb1"; c.fill()
            c.save(); art.rr(-9, -5, 18, 10, 2.5); c.clip(); c.fillStyle = "#6fa8ff"; c.fillRect(2, -6, 8, 12)
            c.restore()
            art.rr(-9, -5, 18, 10, 2.5); c.lineWidth = 1.4; c.strokeStyle = OL; c.stroke()
            c.restore()
