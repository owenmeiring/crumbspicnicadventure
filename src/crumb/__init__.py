"""Crumb's Picnic Run: a little toast's platformer adventure."""

import json
import os
import time
from pathlib import Path

import cairo
import pygame

from . import art, game
from . import ui as ui_mod
from .audio import Audio
from .canvas import Canvas
from .editor import Editor
from .game import S, VH, VW, O

TITLE = "Crumb's Picnic Run"
SAVE_DIR = Path(os.environ.get("APPDATA") or Path.home()) / "CrumbsPicnicRun"
SAVE_FILE = SAVE_DIR / "save.json"
DEFAULTS = {"sfx": True, "music": True, "fullscreen": False, "roll": 1, "best": 0, "checkpoint": 0}
STEP = 1 / 60

PLAY_KEYS = {
    pygame.K_LEFT: "left", pygame.K_a: "left", pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_SPACE: "jump", pygame.K_UP: "jump", pygame.K_w: "jump",
    pygame.K_LSHIFT: "run", pygame.K_RSHIFT: "run", pygame.K_z: "run",
    pygame.K_DOWN: "down", pygame.K_s: "down",
}
MENU_KEYS = {
    pygame.K_UP: "up", pygame.K_w: "up", pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left", pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_RETURN: "ok", pygame.K_KP_ENTER: "ok", pygame.K_SPACE: "ok",
    pygame.K_ESCAPE: "back", pygame.K_BACKSPACE: "back",
}
# XInput layout as reported by SDL's joystick API
PAD_A, PAD_B, PAD_X, PAD_Y, PAD_LB, PAD_RB, PAD_BACK, PAD_START = range(8)
DEADZONE = .45


class App:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.cfg = dict(DEFAULTS)
        self.load()
        S.best = int(self.cfg.get("best", 0))
        S.ROLLSTYLE = int(self.cfg.get("roll", 1)) % len(game.ROLLNAMES)
        cp = int(self.cfg.get("checkpoint", 0))
        S.checkpoint = cp if cp in game.CHECKPOINTS else 0
        pygame.display.set_caption(TITLE)
        self.windowed_size = (1024, 768)
        self.screen = None
        self.apply_display()
        self.set_icon()

        self.audio = Audio()
        self.audio.sfx_on = self.cfg["sfx"]
        self.audio.music_on = self.cfg["music"]
        self.audio.clock.mood_now = game.mood_now
        self.audio.seq.muted = lambda: not self.audio.music_on
        game.AUDIO = self.audio
        game.on_rumble = self.rumble
        game.on_best = self.save_best
        game.on_checkpoint = self.save_checkpoint

        self.editor = Editor(self)
        self.ui = ui_mod.UI(self)
        try:
            pygame.scrap.init()
        except Exception:
            pass
        game.title_level()
        S.state = "title"

        self.running = True
        self.kb = {}
        self.padk = {}
        self.held = set()
        self.joys = {}
        self.hat = (0, 0)
        self.stick_dir = None
        self.stick_next = 0.0
        self.dev_taps = []
        self.fade = 1.0
        self.mouse_seen = 0.0

    # ------------------------------------------------------------ settings
    def load(self):
        try:
            self.cfg.update(json.loads(SAVE_FILE.read_text("utf-8")))
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            SAVE_FILE.write_text(json.dumps(self.cfg, indent=2), "utf-8")
        except OSError:
            pass

    def save_checkpoint(self):
        self.cfg["checkpoint"] = S.checkpoint
        self.save()

    def save_best(self):
        self.cfg["best"] = S.best
        self.save()

    def toggle(self, name):
        self.cfg[name] = not self.cfg[name]
        if name == "sfx":
            self.audio.sfx_on = self.cfg["sfx"]
        elif name == "music":
            self.audio.music_on = self.cfg["music"]
        elif name == "fullscreen":
            self.apply_display()
        self.save()

    def quit(self):
        self.running = False

    # ------------------------------------------------------------ display
    def apply_display(self):
        if self.cfg["fullscreen"]:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.make_surface()

    def make_surface(self):
        w, h = self.screen.get_size()
        rs = max(1.0, min(w / VW, h / VH))
        sw, sh = int(VW * rs), int(VH * rs)
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
        art.g = Canvas(self.surface)
        art.RS = rs
        self.frame = pygame.image.frombuffer(self.surface.get_data(), (sw, sh), "BGRA")
        self.offset = ((w - sw) // 2, (h - sh) // 2)
        self.rs = rs

    def set_icon(self):
        size = 64
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        saved_g, saved_p, saved_state = art.g, S.P, S.state
        art.g = Canvas(surf)
        art.g.setTransform(1.9, 0, 0, 1.9, 0, 0)
        S.state = "card"
        S.P = O(x=5.8, y=4, w=22, h=28, vx=0, vy=0, ground=True, face=1, big=False, fire=False, inv=0, duck=0,
                mk=2, mt=5)
        art.draw_player()
        surf.flush()
        icon = pygame.image.frombuffer(surf.get_data(), (size, size), "BGRA").copy()
        pygame.display.set_icon(icon)
        art.g, S.P, S.state = saved_g, saved_p, saved_state

    def to_logical(self, pos):
        return (pos[0] - self.offset[0]) / self.rs, (pos[1] - self.offset[1]) / self.rs

    # ------------------------------------------------------------ feedback
    def rumble(self, strength, ms):
        for j in self.joys.values():
            try:
                j.rumble(strength * .6, strength, int(ms))
            except Exception:
                pass

    def menu_sfx(self, kind):
        a = self.audio
        if kind == "move":
            a.snd(520, 0, .05, "square", .035)
        elif kind == "ok":
            a.snd(660, 990, .12, "square", .045)
        elif kind == "back":
            a.snd(440, 330, .1, "square", .035)
        else:
            a.snd(700, 0, .06, "triangle", .06)

    # ------------------------------------------------------------ input
    def in_game(self):
        return S.state not in ("title", "over", "win", "edit") and not self.ui.stack

    EDITOR_EVENTS = (pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                     pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL)

    def handle(self, ev):
        t = ev.type
        if S.state == "edit" and t in self.EDITOR_EVENTS:
            if t == pygame.KEYDOWN and (ev.key == pygame.K_F11 or (ev.key == pygame.K_RETURN and ev.mod & pygame.KMOD_ALT)):
                self.toggle("fullscreen")
                return
            if t == pygame.MOUSEMOTION:
                self.mouse_seen = time.perf_counter()
            self.editor.handle(ev)
            return
        if t == pygame.QUIT:
            self.running = False
        elif t == pygame.VIDEORESIZE and not self.cfg["fullscreen"]:
            self.windowed_size = (max(320, ev.w), max(240, ev.h))
            self.screen = pygame.display.get_surface()
            self.make_surface()
        elif t == pygame.WINDOWFOCUSLOST:
            self.kb.clear()
            self.held.clear()
            if self.in_game():
                self.ui.open_pause()
        elif t == pygame.KEYDOWN:
            self.key_down(ev)
        elif t == pygame.KEYUP:
            self.held.discard(ev.key)
            if ev.key in PLAY_KEYS:
                self.kb[PLAY_KEYS[ev.key]] = False
        elif t == pygame.MOUSEMOTION:
            self.mouse_seen = time.perf_counter()
            x, y = self.to_logical(ev.pos)
            if S.state == "title":
                game.t_move(x, y)
            self.ui.mouse_move(x, y)
        elif t == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            x, y = self.to_logical(ev.pos)
            if not self.ui.mouse_down(x, y) and S.state == "title" and not self.ui.stack:
                game.t_grab(x, y)
        elif t == pygame.MOUSEBUTTONUP and ev.button == 1:
            game.t_release()
        elif t == pygame.JOYDEVICEADDED:
            j = pygame.joystick.Joystick(ev.device_index)
            self.joys[j.get_instance_id()] = j
        elif t == pygame.JOYDEVICEREMOVED:
            self.joys.pop(ev.instance_id, None)
            self.padk.clear()
        elif t == pygame.JOYBUTTONDOWN:
            self.pad_button(ev.button, True)
        elif t == pygame.JOYBUTTONUP:
            self.pad_button(ev.button, False)
        elif t == pygame.JOYHATMOTION:
            hx, hy = ev.value
            if self.ui.wants_input():
                if hy and hy != self.hat[1]:
                    self.ui.nav("up" if hy > 0 else "down")
                if hx and hx != self.hat[0]:
                    self.ui.nav("right" if hx > 0 else "left")
            self.hat = (hx, hy)

    def key_down(self, ev):
        k = ev.key
        repeat = k in self.held
        self.held.add(k)
        if k == pygame.K_F11 or (k == pygame.K_RETURN and ev.mod & pygame.KMOD_ALT):
            if not repeat:
                self.toggle("fullscreen")
            return
        if k == pygame.K_g and not repeat:
            now = time.perf_counter()
            self.dev_taps = [x for x in self.dev_taps if now - x < 1.4] + [now]
            if len(self.dev_taps) >= 5:
                self.dev_taps = []
                if "dev" not in self.ui.stack:
                    self.kb.clear()
                    self.ui.push("dev")
                return
        if self.ui.wants_input():
            act = MENU_KEYS.get(k)
            if act:
                self.ui.nav(act)
            return
        if k in (pygame.K_ESCAPE, pygame.K_p) and not repeat:
            self.kb.clear()
            self.ui.open_pause()
            return
        if k in PLAY_KEYS:
            self.kb[PLAY_KEYS[k]] = True
        if repeat:
            return
        if k in (pygame.K_f, pygame.K_x):
            game.fire()
        elif k == pygame.K_e:
            game.try_roll()

    def pad_button(self, b, down):
        if self.ui.wants_input():
            if down:
                if b in (PAD_A, PAD_START):
                    self.ui.nav("ok")
                elif b == PAD_B:
                    self.ui.nav("back")
            return
        if b == PAD_A:
            self.padk["jump"] = down
        elif b in (PAD_Y, PAD_LB, PAD_RB):
            self.padk["run"] = down
        elif down and b == PAD_X:
            game.fire()
        elif down and b == PAD_B:
            game.try_roll()
        elif down and b == PAD_START:
            self.padk.clear()
            self.ui.open_pause()

    def poll_pad(self):
        ax = ay = 0.0
        trig = False
        for j in self.joys.values():
            try:
                if j.get_numaxes() >= 2:
                    ax, ay = j.get_axis(0), j.get_axis(1)
                if j.get_numaxes() >= 6:
                    trig = j.get_axis(4) > .3 or j.get_axis(5) > .3
            except pygame.error:
                pass
        hx, hy = self.hat
        if self.ui.wants_input():
            d = "up" if ay < -DEADZONE else "down" if ay > DEADZONE else \
                "left" if ax < -DEADZONE else "right" if ax > DEADZONE else None
            now = time.perf_counter()
            if d != self.stick_dir:
                self.stick_dir = d
                self.stick_next = now + .35
                if d:
                    self.ui.nav(d)
            elif d and now >= self.stick_next:
                self.stick_next = now + .12
                self.ui.nav(d)
            return
        self.padk["left"] = ax < -DEADZONE or hx < 0
        self.padk["right"] = ax > DEADZONE or hx > 0
        self.padk["down"] = ay > DEADZONE or hy < 0
        self.padk["run_t"] = trig

    def merged_keys(self):
        keys = {n: bool(self.kb.get(n) or self.padk.get(n)) for n in ("left", "right", "jump", "run", "down")}
        keys["run"] = keys["run"] or bool(self.padk.get("run_t"))
        return keys

    # ------------------------------------------------------------ loop
    def update(self):
        if S.state == "edit":
            self.editor.update()
            S.keys = {}
            game.update()
            return
        if S.paused or "dev" in self.ui.stack:
            return
        S.keys = self.merged_keys() if self.in_game() else {}
        game.update()

    def render(self):
        if S.state == "edit":
            self.editor.draw()
            self.present()
            return
        art.set_view(1, 0)
        title_free = S.state == "title" and not self.ui.stack
        art.draw_world(hide_free=title_free)
        art.draw_overlays()
        self.ui.draw()
        if title_free:
            art.draw_free_enemies()
        self.present()

    def present(self):
        if self.fade > 0:
            c = art.g
            c.setTransform(art.RS, 0, 0, art.RS, 0, 0)
            c.fillStyle = (0.0, 0.0, 0.0, self.fade)
            c.fillRect(0, 0, VW, VH)
        self.surface.flush()
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.frame, self.offset)
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        acc = 0.0
        last = time.perf_counter()
        while self.running:
            now = time.perf_counter()
            dt = min(.1, now - last)
            last = now
            acc += dt
            for ev in pygame.event.get():
                self.handle(ev)
            self.poll_pad()
            while acc >= STEP:
                self.update()
                acc -= STEP
            self.fade = max(0.0, self.fade - dt * 2)
            show_mouse = (not self.in_game()) or now - self.mouse_seen < 2
            if pygame.mouse.get_visible() != show_mouse:
                pygame.mouse.set_visible(show_mouse)
            self.render()
            clock.tick(144)
        self.save()
        self.audio.close()
        pygame.quit()


def main() -> None:
    App().run()
