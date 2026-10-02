"""Game state and simulation: levels, Crumb's moves, enemies, the Grand Chili and the goal sequences.

Runs at a fixed 60 updates per second, like the original.
"""

import math
import random

from .levels import CHM, find_ledges, parse_level

T, H, VW, VH = 32, 12, 512, 384
NAMES = ["PICNIC LAWN", "CELLAR PANTRY", "HIGH PICNIC", "HONEYCOMB HOLLOW", "FROSTED PEAKS", "FUDGE MINES",
         "MELON GROVE", "SUNDAE SKIES", "BOSS KITCHEN"]
CARDTXT = ["Run, hop and stomp to the picnic!", "Down in the dark pantry...",
           "Sunshine, sky and a very high picnic", "Sticky, sweet and full of stingers",
           "Icing cliffs and a long way down", "Dig deep. Mind the drips.",
           "Sunset in the treetops", "Above the clouds, under the stars", "The Grand Chili is waiting..."]
TIMES = [260, 250, 250, 420, 450, 460, 480, 520, 300]
LAST = len(NAMES) - 1
CHECKPOINTS = (2, 5, 7)  # 1-3, 1-6 and 1-8: game over continues from the last one reached
# theme -> music mood (0 lawn, 1 cellar, 2 boss, 3 bright adventure, 4 deep caves)
MOOD = {0: 0, 1: 1, 2: 2, 3: 4, 4: 3, 5: 4, 6: 3, 7: 3}
# tile codes: 1 ground, 2 brick, 3 ? block, 4 used block, 5 stone, 6 dark wall,
# 8 crumbling cracker, 9 jelly pad, 10 spikes up, 11 spikes down
CRUMBLE, JELLY, SPIKE_UP, SPIKE_DN = 8, 9, 10, 11
CRUMBLE_T, CRUMBLE_BACK = 26, 170
BASEPAL = dict(crust="#d9964a", shade="#a9642a", hi="#f3c27f", plate="#fbe3b0", ring="rgba(224,150,62,.5)",
               inner="#e8c98a", spk="rgba(200,130,50,.45)", pst="#b06f30", cheek="rgba(255,120,145,.8)",
               leg="#d9964a", shoe="#e8452f", shoe2="#b8301f", fem=0)
PINKPAL = dict(crust="#e98aa6", shade="#b9577a", hi="#ffc3d4", plate="#ffdfe8", ring="rgba(238,120,156,.5)",
               inner="#f6bfd0", spk="rgba(205,90,125,.4)", pst="#b85a78", cheek="rgba(255,82,130,.9)",
               leg="#e98aa6", shoe="#ff6fa0", shoe2="#d94a80", fem=1)
ROLLT, ROLLCD = 17, 300
ROLLNAMES = ["CLASSIC TUMBLE", "TOAST BALL", "CINNAMON ROLL", "FACE BALL"]
OHW, OHM, OHD = 62, 120, 180
GPW, GPV, GPL, GPR, GLIDE = 9, 13.5, 13, 46, 2.3
TQ = [[130, 22, .05, 0, 26], [68, 18, .035, 1, 38], [14, 14, .06, 2, 50]]
rnd = random.random


class O:
    """A loose record, like a JS object: missing fields read as 0."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __getattr__(self, k):
        if k.startswith("__"):
            raise AttributeError(k)
        return 0

    def has(self, k):
        return k in self.__dict__


class State:
    def __init__(self):
        self.PAL = BASEPAL
        self.GS = None
        self.CI = 0
        self.W = 0
        self.GOAL = 0
        self.UG = False
        self.LV = 0
        self.keys = {}
        self.state = "title"
        self.cam = 0.0
        self.lives = 3
        self.score = 0
        self.coinsN = 0
        self.time = 200.0
        self.tick = 0
        self.deadT = 0
        self.clearT = 0
        self.CARD = None
        self.irisO = 99
        self.P = None
        self.enemies, self.grid, self.coins, self.items, self.fx, self.shots, self.bshots = [], [], [], [], [], [], []
        self.bumps, self.contents = {}, {}
        self.boss = None
        self.bossT = 0
        self.TH = 0
        self.CAGE = self.KEYO = self.FS = None
        self.LEDGES = [[77, 79], [83, 85]]
        self.LMID = 80.5
        self.KX = 80.5
        self.AR0, self.AR1 = 52, 67
        self.bossDisp = 6.0
        self.best = 0
        self.tcam = 0.0
        self.tt = 0
        self.shk = 0.0
        self.moodBag = []
        self.qblocks = []
        self.CUSTTIME = 250
        self.tHeld = None
        self.tSndT = 0
        self.ROLLSTYLE = 1
        self.HA = 0.0
        self.menu_rects = []
        self.paused = False
        self.crumble = {}  # (x, y) -> frames since stepped on (>0) or frames until it grows back (<0)
        self.jelly = {}  # (x, y) -> wobble timer
        self.checkpoint = 0  # furthest checkpoint level reached (index)
        self.CUST = None  # the custom level being played, if any
        self.CUSTEDIT = False  # True when that play-test came from the level builder


S = State()
AUDIO = None          # crumb.audio.Audio, set by the app
on_rumble = None      # callback(strength, ms) for gamepad rumble
on_best = None        # callback when the best score changes
on_checkpoint = None  # callback when a new checkpoint is reached


# ------------------------------------------------------------------ sound
def snd(a, b, d, ty, v, delay=0.0):
    if AUDIO:
        AUDIO.snd(a, b, d, ty, v, delay)


def ding():
    snd(988, 1319, .4, "sine", .2)


def pow_():
    for i, f in enumerate([392, 523, 659, 880]):
        snd(f, 0, .14, "square", .07, i * .08)


def shoot():
    snd(800, 300, .12, "sawtooth", .05)


def vib(ms):
    if on_rumble:
        total = sum(ms) if isinstance(ms, list) else ms
        on_rumble(.6 if total > 60 else .35, total)


def bonk():
    snd(220, 110, .12, "square", .08)
    vib(16)


def mtime():
    if AUDIO and AUDIO.ok:
        return AUDIO.mtime()
    return S.tick / 60


def clock():
    return AUDIO.clock if AUDIO else _fallback_clock


class _Clock:
    sp = 60 / 84 / 4
    beat2 = sp * 8
    t0 = .2
    dances = []
    intro_pend = False


_fallback_clock = _Clock()


def dance_slot(mt):
    G = clock()
    need = mt + .55
    later = sorted(x for x in G.dances if x >= need)
    if later and later[0] < need + G.beat2 * 2:
        return later[0]
    tB = G.t0 + math.ceil((need - G.t0) / G.beat2) * G.beat2
    G.dances = [x for x in G.dances + [tB] if x > mt - 4]
    return tB


def mood_now():
    return 0 if S.state in ("title", "edit") else S.LV


# ------------------------------------------------------------------ effects
def txt(x, y, s):
    S.fx.append(O(k="txt", x=x, y=y, vy=-1, life=45, s=s))


def spark_fx(x, y, c):
    for i in range(8):
        a = i * math.pi / 4
        S.fx.append(O(k="spark", x=x, y=y, vx=math.cos(a) * 2.4, vy=math.sin(a) * 2.4 - 1, life=22, c=c))


def coin_fx(x, y):
    S.fx.append(O(k="ring", x=x, y=y, life=16))
    spark_fx(x, y, "#ffd84d")
    txt(x, y - 10, "+100")


def heart_fx(x, y, n):
    for _ in range(n):
        S.fx.append(O(k="heart", x=x + (rnd() - .5) * 14, y=y + (rnd() - .5) * 6, vx=(rnd() - .5) * .6,
                      vy=-.7 - rnd() * .7, life=60 + rnd() * 25, s=.7 + rnd() * .7, ph=rnd() * 6))


def confetti(x, y, n, up=2):
    cols = ["#ff5a4a", "#ffd84d", "#ffffff", "#58b84c", "#57a9ff", "#ff8fc1"]
    for i in range(n):
        a = rnd() * math.pi * 2
        sp = 1.5 + rnd() * 3.2
        S.fx.append(O(k="conf", x=x, y=y, vx=math.cos(a) * sp, vy=math.sin(a) * sp - (up or 2),
                      life=70 + rnd() * 30, c=cols[i % len(cols)], r=rnd() * 6, vr=(rnd() - .5) * .4))


# ------------------------------------------------------------------ levels
def mk(w):
    S.W = w
    S.grid = [[0] * w for _ in range(H)]
    S.coins, S.enemies, S.items, S.fx, S.shots, S.bshots = [], [], [], [], [], []
    S.bumps, S.contents = {}, {}
    S.boss = None
    S.bossT = 0
    S.CAGE = S.KEYO = S.FS = None


def ground(gaps):
    for x in range(S.W):
        if not any(q[0] <= x <= q[1] for q in gaps):
            S.grid[10][x] = 1
            S.grid[11][x] = 1


def arc(x, y, n):
    for i in range(n):
        S.coins.append(O(x=(x + i) * T + 16, y=y * T + 16, got=False))


def ant(x, d):
    S.enemies.append(O(k="ant", x=x * T, y=10 * T - 20, w=26, h=20, vx=d * .7, dead=0))


def nut(x, d):
    S.enemies.append(O(k="nut", x=x * T, y=10 * T - 26, w=26, h=26, vx=d * .6, dead=0, mode="walk", st=0, kick=0))


def row(y, a, b, v):
    for x in range(a, b + 1):
        S.grid[y][x] = v


def pillar(x, h):
    for i in range(h):
        S.grid[9 - i][x] = 5
        S.grid[9 - i][x + 1] = 5


def stairs(x):
    for i in range(4):
        for j in range(i + 1):
            S.grid[9 - j][x + i] = 5


def level1():
    mk(144)
    S.GOAL, S.UG, S.TH = 141, False, 0
    g = S.grid
    ground([[22, 24], [45, 48], [70, 73], [88, 90], [95, 99], [108, 110], [118, 121], [126, 130]])
    row(7, 14, 18, 2); g[7][16] = 3; row(6, 30, 33, 2); g[6][31] = 3
    g[7][38] = 3; g[7][40] = 3; g[4][39] = 3
    row(7, 52, 57, 2); g[7][54] = 3; row(6, 64, 66, 2); g[6][65] = 3; row(7, 78, 82, 2); g[7][80] = 3
    pillar(28, 2); pillar(60, 3); pillar(84, 2)
    g[8][97] = 2; pillar(104, 3); row(7, 112, 116, 2); g[7][114] = 3; pillar(124, 2); g[8][128] = 2; stairs(136)
    S.contents.update({(16, 7): "pizza", (31, 6): "cookie", (54, 7): "cookie", (80, 7): "pizza", (114, 7): "pizza"})
    for a in [(14, 6, 5), (30, 5, 4), (21, 8, 4), (44, 8, 5), (52, 6, 6), (69, 7, 5), (78, 6, 5), (87, 7, 4), (95, 6, 5),
              (102, 7, 4), (107, 6, 5), (112, 5, 5), (118, 6, 4), (126, 7, 5), (131, 6, 4)]:
        arc(*a)
    ant(18, 1); ant(50, -1); ant(75, 1); nut(35, -1); nut(63, 1); nut(92, -1)
    ant(101, 1); nut(107, -1); ant(113, -1); nut(115, 1); ant(117, -1); ant(123, -1); nut(133, -1); ant(132, 1)


def level2():
    mk(125)
    S.GOAL, S.UG, S.TH = 123, True, 1
    g = S.grid
    row(0, 0, S.W - 1, 6); row(1, 0, S.W - 1, 6)
    ground([[20, 21], [38, 40], [58, 60], [74, 75], [86, 89], [104, 107], [113, 115]])
    row(7, 10, 14, 2); g[7][12] = 3; S.contents[(12, 7)] = "pizza"
    for y in range(2, 5):
        row(y, 28, 36, 6)
    row(8, 31, 34, 2); g[8][32] = 3; S.contents[(32, 8)] = "cookie"
    row(6, 44, 52, 2); g[6][48] = 3; S.contents[(48, 6)] = "pizza"
    pillar(16, 2); pillar(26, 3); pillar(54, 2); pillar(66, 3); pillar(83, 3)
    for y in range(2, 6):
        row(y, 92, 101, 6)
    row(7, 102, 103, 2); g[7][102] = 3; S.contents[(102, 7)] = "cookie"; pillar(109, 3); stairs(118)
    for a in [(10, 6, 5), (19, 8, 4), (29, 7, 6), (44, 5, 9), (62, 7, 6), (70, 6, 5), (86, 6, 4), (93, 8, 6),
              (104, 6, 4), (112, 6, 5)]:
        arc(*a)
    ant(24, 1); ant(34, -1); ant(46, 1); ant(56, -1); ant(68, 1); ant(78, -1)
    nut(30, -1); nut(42, 1); nut(64, -1); nut(72, 1); nut(80, -1)
    ant(93, 1); ant(96, -1); nut(99, 1); ant(102, 1); ant(112, -1); ant(116, 1)


CAMP3 = {"name": "level 3", "theme": 0, "time": 250, "w": 80, "start": [2, 9], "goal": 76, "grid": [
    "................................................................................",
    "...................................b?..............c...c........................",
    "...............c...................b..bbbbb.......c.c.c.c.......................",
    "...................................b......b.......c.c.c.c.......................",
    "...................c................bb....b.......c.c.c.c.......................",
    "...........................bbb............b........c...c................#.......",
    "...............c..........................b.....?.........?.....................",
    ".....................?..?......?..b....b..b.........................#...........",
    "..........#.......................b.......b.......bbbbbbb.......................",
    ".........##.......................b.......b.#..#................#...............",
    "###########..........#..#...#..#..##########....##############.............#####",
    "###########..........#..#...#..#..############################.............#####"],
    "contents": {"24,7": "pizza", "21,7": "pizza", "31,7": "cookie"},
    "coins": [[14, 1], [15, 1], [16, 1], [16, 2], [16, 3], [15, 3], [14, 3], [14, 2], [27, 4], [28, 4], [29, 4], [29, 3],
              [28, 3], [27, 3], [27, 2], [28, 2], [29, 1], [28, 1], [27, 1], [29, 2], [51, 2], [51, 3], [51, 4], [55, 2],
              [55, 3], [55, 4], [49, 2], [49, 3], [49, 4], [53, 2], [53, 3], [53, 4], [57, 2], [57, 3], [57, 4], [37, 3],
              [36, 3], [36, 2], [37, 2]],
    "enemies": [["ant", 19, 3, 1], ["ant", 15, 5, 1], ["nut", 36, 9, 1], ["nut", 37, 9, 1], ["nut", 38, 9, 1],
                ["nut", 39, 9, 1], ["nut", 40, 9, 1], ["ant", 44, 10, 1], ["ant", 46, 10, 1], ["ant", 47, 10, 1],
                ["ant", 45, 10, 1], ["nut", 52, 7, 1], ["nut", 55, 7, 1]]}
CAMP3_L = parse_level(CAMP3)


def mk_enemy(q):
    if q["k"] == "ant":
        return O(k="ant", x=q["x"] * T, y=(q["y"] + 1) * T - 20, w=26, h=20, vx=q["d"] * .7, dead=0)
    return O(k="nut", x=q["x"] * T, y=(q["y"] + 1) * T - 26, w=26, h=26, vx=q["d"] * .6, dead=0, mode="walk", st=0,
             kick=0)


def build_live(L):
    """Turn a parsed level (see levels.py) into the live world."""
    mk(L["w"])
    S.TH = L["theme"]
    S.LV = MOOD.get(S.TH, 0)
    S.GOAL = 99999 if L["goal"] is None else L["goal"]
    for y in range(H):
        for x in range(L["w"]):
            S.grid[y][x] = CHM[L["g"][y][x]]
    S.UG = any(v == 6 for v in S.grid[0])
    S.contents.update(L["contents"])
    for c in L["coins"]:
        S.coins.append(O(x=c[0] * T + 16, y=c[1] * T + 16, got=False))
    for q in L["enemies"]:
        S.enemies.append(mk_enemy(q))
    S.LEDGES = [[77, 79], [83, 85]]
    S.LMID = 80.5
    S.KX = L["w"] / 2
    S.bossDisp = 6.0
    S.boss = None
    b = L["boss"]
    if b:
        S.AR0, S.AR1 = b["ar0"], b["ar1"]
        S.KX = (S.AR0 + S.AR1 + 1) / 2
        S.LEDGES = find_ledges(L)
        S.LMID = (lcx(0) + lcx(1)) / 2 / T if len(S.LEDGES) >= 2 else S.KX
        S.boss = O(x=b["x"] * T, y=10 * T - 64, w=56, h=64, vx=-1, vy=0, hp=6, dead=0, flash=0, cd=100)
    _find_qblocks()


def _find_qblocks():
    S.qblocks = [(x, y) for y in range(H) for x in range(S.W) if S.grid[y][x] == 3]


def place_start(L):
    P = S.P
    P.x = L["start"][0] * T + (T - P.w) / 2
    P.y = (L["start"][1] + 1) * T - P.h - .01


def play_custom(L, from_editor=False):
    """Play a custom level (from the level builder or the Custom Levels list)."""
    S.CUST = L
    S.CUSTEDIT = from_editor
    note_best()
    S.lives, S.score, S.coinsN = 3, 0, 0
    S.paused = False
    build_live(L)
    if L["theme"] == 2:
        clock().intro_pend = True
    new_player(False)
    S.deadT = S.clearT = 0
    S.keys = {}
    show_card()


def load_level(n):
    from . import world
    S.CI = n
    S.CUST = None
    S.crumble, S.jelly = {}, {}
    if n in CHECKPOINTS and n > S.checkpoint:
        S.checkpoint = n
        if on_checkpoint:
            on_checkpoint()
    if n == 0:
        level1()
    elif n == 1:
        level2()
    elif n == 2:
        build_live(CAMP3_L)
    else:
        L = world.LEVELS[n]
        build_live(L)
        if n == LAST:
            clock().intro_pend = True
            cx = (L["boss"]["ar1"] - .6) * T
            S.CAGE = O(cx=cx, gy=10 * T, open=0, lock=1, lt=0,
                       q=O(x=0, y=0, w=22, h=28, vx=0, vy=0, ground=True, face=-1, big=False, fire=False, inv=0,
                           duck=0, mk=0, mt=0, dx=6))
    S.LV = MOOD.get(S.TH, 0)
    _find_qblocks()


def continue_game():
    """After a game over: back to the last checkpoint with fresh lives."""
    S.CUST = None
    S.CUSTEDIT = False
    S.lives, S.score, S.coinsN = 3, 0, 0
    S.paused = False
    load_level(S.checkpoint)
    new_player(False)
    show_card()


def respawn_blocks():
    for x, y in S.qblocks:
        S.grid[y][x] = 3
        S.bumps.pop((x, y), None)
    for (x, y) in list(S.crumble):
        S.grid[y][x] = CRUMBLE
    S.crumble = {}
    S.items = []


def new_player(keep):
    P = S.P
    b = keep and P and P.big
    f = keep and P and P.fire
    S.GS = None
    S.P = O(x=64, y=232 if b else 250, w=28 if b else 22, h=42 if b else 28, vx=0, vy=0, ground=False, face=1,
            big=bool(b), fire=bool(f), inv=0, duck=0)
    S.cam = 0
    if S.CUST:
        place_start(S.CUST)
        S.time = S.CUST["time"]
        S.cam = max(0, min(S.W * T - VW, S.P.x - VW / 2.4))
    else:
        S.time = TIMES[S.CI]
    S.P.safe = (S.P.x, S.P.y + S.P.h)


def grow():
    P = S.P
    if P.big:
        return
    b = P.y + P.h
    P.big, P.duck = True, 0
    P.x -= 3
    P.w, P.h = 28, 42
    P.y = b - 42


def shrink():
    P = S.P
    b = P.y + P.h
    P.big, P.duck = False, 0
    P.x += 3
    P.w, P.h = 22, 28
    P.y = b - 28


# ------------------------------------------------------------------ title screen
def title_level():
    S.tHeld = None
    mk(2000)
    S.GOAL, S.UG, S.TH = 99999, False, 0
    ground([])
    S.tcam = S.cam = 0
    S.tt = 0
    for k in range(1, 320):
        for i in range(5):
            S.coins.append(O(x=187 * k + 200 + i * 17, y=306 - 28 * math.sin(math.pi * i / 4), got=False))
    S.P = O(x=200, y=10 * T - 28, w=22, h=28, vx=3.6, vy=0, ground=True, face=1, big=False, fire=False, inv=0, duck=0)
    S.enemies = [O(k="ant", x=130, y=10 * T - 20, w=26, h=20, vx=.7, dead=0, f=1),
                 O(k="nut", x=68, y=10 * T - 26, w=26, h=26, vx=.6, dead=0, mode="walk", st=0, kick=0, f=1),
                 O(k="ant", x=14, y=10 * T - 20, w=26, h=20, vx=.7, dead=0, f=1)]


def t_snd(a, b, d):
    if S.tick - S.tSndT > 5:
        S.tSndT = S.tick
        snd(a, b, d, "triangle", .07)


def t_phys(e):
    gy = 10 * T + 40 - e.h
    if S.tHeld is e:
        nx, ny = e.tx - e.gox, e.ty - e.goy
        e.pvx = e.pvx * .4 + (nx - e.sx) * .6
        e.pvy = e.pvy * .4 + (ny - e.sy) * .6
        e.sx, e.sy = nx, ny
        e.rot = (e.rot or 0) * .9 + math.sin(S.tt * .6) * .1
        e.idle = 0
        e.ret = 0
    else:
        e.pvy += .5
        e.sx += e.pvx
        e.sy += e.pvy
        rest = False
        if e.sx < 0:
            e.sx = 0
            e.pvx = abs(e.pvx) * .65
            if abs(e.pvx) > 2:
                t_snd(170, 80, .08)
        if e.sx > VW - e.w:
            e.sx = VW - e.w
            e.pvx = -abs(e.pvx) * .65
            if abs(e.pvx) > 2:
                t_snd(170, 80, .08)
        if e.sy < 0:
            e.sy = 0
            e.pvy = abs(e.pvy) * .5
        if not e.ret:
            for (l, t, r, b) in S.menu_rects:
                if e.sx + e.w > l and e.sx < r and e.sy + e.h > t and e.sy < b:
                    d = [e.sx + e.w - l, r - e.sx, e.sy + e.h - t, b - e.sy]
                    m = min(d)
                    if m == d[2] and e.pvy >= 0:
                        e.sy = t - e.h
                        if e.pvy > 2.5:
                            e.pvy = -e.pvy * .45
                            t_snd(200, 110, .08)
                        else:
                            e.pvy = 0
                            rest = True
                        e.pvx *= .9
                    elif m == d[3]:
                        e.sy = b
                        e.pvy = abs(e.pvy) * .5
                        t_snd(200, 110, .08)
                    elif m == d[0]:
                        e.sx = l - e.w
                        e.pvx = -abs(e.pvx) * .6
                        t_snd(200, 110, .08)
                    else:
                        e.sx = r
                        e.pvx = abs(e.pvx) * .6
                        t_snd(200, 110, .08)
        if e.sy >= gy:
            e.sy = gy
            if e.pvy > 2.5:
                e.pvy = -e.pvy * .45
                t_snd(140, 60, .1)
                spark_fx(e.sx + S.tcam + e.w / 2, e.sy - 40 + e.h, "#e7d3a8")
            else:
                e.pvy = 0
                rest = True
            e.pvx *= .88
        if rest:
            e.rot *= .8
        else:
            e.rot = (e.rot or 0) + e.pvx * .05
        if rest and abs(e.pvx) < .5:
            e.idle = (e.idle or 0) + 1
            if e.idle > 45:
                e.ret = 1
        else:
            e.idle = 0
        if e.ret:
            q = TQ[e.ti]
            tx = q[0] + math.sin(S.tt * q[2] + q[3]) * q[1]
            e.sx += (tx - e.sx) * .07
            if abs(tx - e.sx) < 2 and e.sy >= gy - 1:
                e.free = 0
                e.ret = 0
                e.rot = 0
    e.pvx = max(-16, min(16, e.pvx))
    e.pvy = max(-16, min(16, e.pvy))
    e.x = S.tcam + e.sx
    e.y = e.sy - 40
    if abs(e.pvx) > .6:
        e.vx = (1 if e.pvx > 0 else -1) * (.7 if e.k == "ant" else .6)


def t_pick(gx, gy):
    for e in reversed(S.enemies):
        if e.dead:
            continue
        sx, sy = e.x - S.tcam, e.y + 40
        if sx - 6 < gx < sx + e.w + 6 and sy - 6 < gy < sy + e.h + 6:
            return e
    return None


def t_grab(gx, gy):
    e = t_pick(gx, gy)
    if not e:
        return False
    S.tHeld = e
    e.free, e.ret, e.idle = 1, 0, 0
    e.sx, e.sy = e.x - S.tcam, e.y + 40
    e.gox, e.goy = gx - e.sx, gy - e.sy
    e.tx, e.ty = gx, gy
    e.pvx = e.pvy = 0
    e.rot = e.rot or 0
    snd(520, 760, .08, "square", .05)
    return True


def t_move(gx, gy):
    if S.tHeld:
        S.tHeld.tx, S.tHeld.ty = gx, gy


def t_release():
    e = S.tHeld
    if e:
        S.tHeld = None
        if abs(e.pvx) + abs(e.pvy) > 6:
            snd(420, 180, .14, "sine", .05)


def title_update():
    S.tt += 1
    S.tcam += 1.7
    S.cam = S.tcam
    P = S.P
    c = S.tt % 110
    hop = 28 * math.sin(math.pi * c / 40) if c < 40 else 0
    P.x = S.tcam + 200
    P.y = 10 * T - 28 - hop
    P.ground = c >= 40
    P.vx = 3.6
    P.vy = (-4 if c < 20 else 4) if c < 40 else 0
    if P.inv > 0:
        P.inv -= 1
    for i, q in enumerate(TQ):
        e = S.enemies[i]
        e.ti = i
        if e.free:
            t_phys(e)
            continue
        cc = (S.tt - q[4] + 110) % 110
        h = 20 * math.sin(math.pi * cc / 28) if cc < 28 else 0
        e.x = S.tcam + q[0] + math.sin(S.tt * q[2] + q[3]) * q[1]
        e.y = 10 * T - e.h - h
    for k in S.coins:
        if not k.got and abs(k.x - (P.x + 11)) < 14 and abs(k.y - (P.y + 14)) < 20:
            k.got = True
            spark_fx(k.x, k.y, "#ffd84d")


# ------------------------------------------------------------------ flow
def note_best():
    if S.score > S.best:
        S.best = S.score
        if on_best:
            on_best()


def show_card():
    if S.CUST:
        S.CARD = O(t=0, len=110, name=S.CUST["name"].upper(), no="CUSTOM LEVEL", sub="")
    else:
        S.CARD = O(t=0, len=126, name=NAMES[S.CI], no=f"WORLD 1-{S.CI + 1}", sub=CARDTXT[S.CI], check=S.CI in CHECKPOINTS)
    S.state = "card"


def level_name():
    return S.CUST["name"].upper() if S.CUST else f"1-{S.CI + 1}  {NAMES[S.CI]}"


def start(level=0):
    S.CUST = None
    S.CUSTEDIT = False
    note_best()
    S.lives, S.score, S.coinsN = 3, 0, 0
    S.paused = False
    load_level(level)
    new_player(False)
    show_card()


def restart_level():
    if S.CUST:
        play_custom(S.CUST, S.CUSTEDIT)
        return
    load_level(S.CI)
    new_player(False)
    S.paused = False
    show_card()


def to_title():
    note_best()
    S.keys = {}
    S.paused = False
    title_level()
    S.state = "title"


def die():
    if S.state != "play":
        return
    vib([40, 30, 90])
    P = S.P
    P.spin = P.wjt = P.ws = 0
    S.state = "dead"
    S.deadT = 0
    P.vy = -9
    S.lives -= 1
    snd(400, 100, .6, "square", .08)


def ohs_of(p):
    if p.ohd > 0:
        return min(1, p.ohd / 45)
    return min(1, max(0, ((p.glt or 0) - OHW) / (OHM - OHW)))


def gp_act():
    P = S.P
    return bool(P and (P.gp > 0 or P.gpf))


def gp_cancel():
    S.P.gp = 0
    S.P.gpf = 0


def hit_boss():
    b = S.boss
    b.hp -= 1
    b.flash = 36
    bonk()
    react()
    spark_fx(b.x + 28, b.y + 30, "#ff8a2a")
    if b.hp <= 0:
        b.dead = 1
        S.bossT = 0
        S.bshots = []
        S.score += 5000
        pow_()
        for i in range(4):
            spark_fx(b.x + 14 + i * 10, b.y + 10 + i * 12, "#ffd84d")
        txt(b.x + 28, b.y - 10, "+5000")


def gp_impact():
    P = S.P
    P.gpf = 0
    P.gp = 0
    P.gpl = GPL
    S.shk = 9
    vib(34)
    cx, fy = P.x + P.w / 2, P.y + P.h
    snd(95, 38, .4, "sine", .24)
    snd(240, 70, .14, "square", .07)
    S.fx.append(O(k="shock", x=cx, y=fy, life=20))
    for i in range(10):
        d = 1 if i % 2 else -1
        S.fx.append(O(k="spark", x=cx + d * 4, y=fy - 2, vx=d * (1.5 + rnd() * 2.6), vy=-1 - rnd() * 2, life=18,
                      c="#e7d3a8"))
    for dx in (2, P.w - 2):
        tx, ty = math.floor((P.x + dx) / T), math.floor((fy + 1) / T)
        if 0 <= ty < H and 0 <= tx < S.W and S.grid[ty][tx] == 2:
            S.grid[ty][tx] = 0
            S.bumps.pop((tx, ty), None)
            S.score += 50
            for i in range(6):
                S.fx.append(O(k="spark", x=tx * T + 16, y=ty * T + 16, vx=(i - 2.5) * 1.4, vy=-3 - (i % 2) * 2,
                              life=30, c="#d9a25b"))
    hit = False
    for e in S.enemies:
        if e.dead:
            continue
        if abs(e.x + e.w / 2 - cx) < GPR and abs(e.y + e.h - fy) < 12:
            if e.k == "ant":
                e.dead = 1
                S.score += 200
                hit = True
                spark_fx(e.x + e.w / 2, e.y + e.h / 2, "#ff8a2a")
            elif e.mode == "walk":
                e.mode = "shell"
                e.vx = e.st = e.dn = e.dpend = 0
                S.score += 200
                hit = True
                spark_fx(e.x + e.w / 2, e.y + e.h / 2, "#ff8a2a")
    for b in S.bshots:
        if abs(b.x + 5 - cx) < GPR + 8 and abs(b.y + 5 - fy) < 40:
            b.life = 0
            S.score += 50
            spark_fx(b.x + 5, b.y + 5, "#ffd84d")
    B = S.boss
    if B and not B.dead and B.flash <= 0 and abs(B.x + B.w / 2 - cx) < GPR + B.w / 2 and abs(B.y + B.h - fy) < 12:
        hit_boss()
        hit = False
    if hit:
        react()


def start_roll():
    P = S.P
    NH, DH = (42, 24) if P.big else (28, 18)
    k = S.keys
    d = -1 if k.get("left") and not k.get("right") else (1 if k.get("right") and not k.get("left") else P.face)
    P.face = P.rdir = d
    P.roll = ROLLT
    P.rcd = ROLLCD
    P.rbuf = 0
    if not P.duck:
        P.duck = 1
        P.y += NH - DH
        P.h = DH
    snd(340, 90, .2, "sawtooth", .045)
    for _ in range(7):
        S.fx.append(O(k="spark", x=P.x + P.w / 2 - d * 6, y=P.y + P.h - 2, vx=-d * (1 + rnd() * 1.6),
                      vy=-.6 - rnd() * 1.1, life=18, c="#e7d3a8"))


def try_roll():
    P = S.P
    if S.state != "play" or not P or P.roll > 0 or gp_act():
        return
    if P.rcd > 0:
        P.rdeny = 14
        snd(150, 110, .08, "square", .04)
        return
    if P.ground:
        start_roll()
    else:
        P.rbuf = 8


def react():
    P = S.P
    if not P:
        return
    if not S.moodBag:
        S.moodBag = [0, 1, 2]
        random.shuffle(S.moodBag)
        if S.moodBag[0] == P.mk:
            S.moodBag.reverse()
    P.mk = S.moodBag.pop(0)
    P.mt = 62


def hurt():
    P = S.P
    if P.roll > 0:
        return
    gp_cancel()
    bonk()
    if P.fire:
        P.fire = False
        P.inv = 90
    elif P.big:
        shrink()
        P.inv = 90
    else:
        die()


def fire():
    P = S.P
    if (S.state == "play" and P.fire and not P.roll > 0 and not gp_act() and not P.throw > 0
            and len(S.shots) < 2):
        # Crumb's fiery sprout curls back with a cookie cradled in its leaves, then whips forward
        # and flings it (see throw_release); THROW_T frames in total
        P.throw = THROW_T
        snd(300, 520, .1, "triangle", .035)


THROW_T, THROW_RELEASE = 14, 8


def sprout_tip(P):
    """Where the leaves of Crumb's sprout are, in world space."""
    s = 1.5 if P.big else 1
    return P.x + P.w / 2 + P.face * 7 * s, P.y + P.h - 36 * s


def throw_release(P):
    x, y = sprout_tip(P)
    S.shots.append(O(x=x - 5, y=y - 5, vx=P.face * 6.4, vy=-3.4, life=110, rot=0.0, trail=[], age=0))
    S.fx.append(O(k="fireburst", x=x, y=y, d=P.face, life=12))
    for _ in range(8):
        a = (rnd() - .5) * 1.2 - .4
        sp = 1.5 + rnd() * 2.5
        S.fx.append(O(k="ember", x=x, y=y, vx=P.face * math.cos(a) * sp, vy=math.sin(a) * sp - .4,
                      life=12 + rnd() * 10, r=1.1 + rnd() * 1.4))
    snd(220, 900, .16, "sawtooth", .045)
    snd(1600, 500, .1, "triangle", .03)


def cookie_blast(x, y):
    """A fire cookie bursting into flames and crumbs."""
    S.fx.append(O(k="blast", x=x, y=y, life=16))
    for i in range(10):
        a = rnd() * math.pi * 2
        sp = 1.5 + rnd() * 3.5
        S.fx.append(O(k="ember", x=x, y=y, vx=math.cos(a) * sp, vy=math.sin(a) * sp - 1, life=16 + rnd() * 14,
                      r=1.4 + rnd() * 2))
    for i in range(7):
        S.fx.append(O(k="crumb", x=x, y=y, vx=(rnd() - .5) * 4, vy=-1.5 - rnd() * 2.5, life=26,
                      c="#dc9c4c" if i % 2 else "#3a1e0e"))
    snd(160, 50, .2, "sawtooth", .06)
    snd(900, 260, .09, "square", .025)


def solid(px, py):
    tx, ty = math.floor(px / T), math.floor(py / T)
    if tx < 0:
        return 1
    if ty < 0 or ty >= H or tx >= S.W:
        return 0
    v = S.grid[ty][tx]
    return 0 if v >= SPIKE_UP else v


def tile(tx, ty):
    if 0 <= ty < H and 0 <= tx < S.W:
        return S.grid[ty][tx]
    return 0


def spike_hit(P):
    """Is Crumb touching the sharp half of any spike tile?"""
    x0, x1 = math.floor((P.x + 3) / T), math.floor((P.x + P.w - 3) / T)
    y0, y1 = math.floor((P.y + 2) / T), math.floor((P.y + P.h - 1) / T)
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            v = tile(tx, ty)
            if v == SPIKE_UP and P.y + P.h > ty * T + 14:
                return v
            if v == SPIKE_DN and P.y < ty * T + 18:
                return v
    return 0


def spike_hurt():
    """Spikes always hurt (even mid-roll), then put Crumb back on the last safe ledge."""
    P = S.P
    gp_cancel()
    P.roll = 0
    if P.inv <= 0:
        bonk()
        S.shk = 6
        if P.fire:
            P.fire = False
        elif P.big:
            shrink()
        else:
            die()
            return
    for _ in range(8):
        S.fx.append(O(k="puff", x=P.x + P.w / 2 + (rnd() - .5) * 16, y=P.y + P.h / 2 + (rnd() - .5) * 16,
                      vx=(rnd() - .5) * 1.4, vy=-.4 - rnd(), life=26))
    sx, foot = P.safe or (64, 278)
    P.duck = 0
    P.h = 42 if P.big else 28
    P.x, P.y = sx, foot - P.h
    P.vx = P.vy = 0
    P.inv = 100
    P.glt = 0
    P.ohd = 0
    S.fx.append(O(k="ring", x=P.x + P.w / 2, y=P.y + P.h / 2, life=16))
    snd(700, 1100, .2, "sine", .06)


def ov(a, b):
    return a.x + a.w > b.x and a.x < b.x + b.w and a.y + a.h > b.y and a.y < b.y + b.h


class R:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


def boss_spit():
    B, P = S.boss, S.P
    d = -1 if P.x < B.x else 1
    hard = B.hp <= 3
    if not B.q:
        B.q = []
    q = B.q

    def ox():
        return B.x + (B.w if d > 0 else 0) - 5

    def oy():
        return B.y + 22

    def roll_():
        S.bshots.append(O(k="roll", x=ox(), y=oy(), vx=d * (4.3 if hard else 3.5), vy=-1, life=280, age=0))

    def seek():
        S.bshots.append(O(k="seek", x=ox(), y=oy(), vx=d * 2.2, vy=-2.4, sp=3.1 if hard else 2.6, life=230, age=0))

    B.sc = pat = ((B.sc or 0) + 1) % 3
    if not hard:
        if pat == 0:
            roll_()
        elif pat == 1:
            seek()
        else:
            seek()
            q.append(O(t=34, f=roll_))
    else:
        if pat == 0:
            roll_()
            q.append(O(t=14, f=seek))
        elif pat == 1:
            seek()
            q.append(O(t=26, f=seek))
            q.append(O(t=52, f=roll_))
        else:
            roll_()
            q.append(O(t=24, f=roll_))
            q.append(O(t=40, f=seek))


def lcx(i):
    return (S.LEDGES[i][0] + S.LEDGES[i][1]) / 2 * T


# ------------------------------------------------------------------ main update
def update():
    S.tick += 1
    if S.shk > 0:
        S.shk = max(0, S.shk - .7)
    for f in S.fx:
        f.life -= 1
        f.x += f.vx or 0
        f.y += f.vy or 0
        if f.k == "spark":
            f.vy += .15
        elif f.k == "coin":
            f.vy += .35
        elif f.k == "crumb":
            f.vy += .12
        elif f.k == "conf":
            f.vy += .07
            f.r += f.vr
            f.vx *= .99
        elif f.k == "ember":
            f.vx *= .93
            f.vy = f.vy * .93 - .06
    S.fx = [f for f in S.fx if f.life > 0]
    st = S.state
    if st == "title":
        title_update()
        return
    if st == "goal":
        goal_update()
        return
    if st == "free":
        free_update()
        return
    if st == "card":
        S.CARD.t += 1
        if S.CARD.t >= S.CARD.len:
            S.state = "play"
            S.irisO = 0
            S.CARD = None
        return
    if st == "clear":
        S.clearT += 1
        if S.CUST:
            if S.clearT > 60:
                S.state = "win"
                note_best()
        elif S.clearT > 46:
            if S.CI == LAST:
                S.state = "win"
                note_best()
                S.checkpoint = 0  # world cleared: the next run starts fresh
                if on_checkpoint:
                    on_checkpoint()
            else:
                load_level(S.CI + 1)
                new_player(True)
                show_card()
        return
    if st == "dead":
        S.deadT += 1
        S.P.vy += .5
        S.P.y += S.P.vy
        if S.deadT > 90:
            if S.lives <= 0:
                S.state = "over"
                note_best()
            else:
                new_player(False)
                respawn_blocks()
                show_card()
        return
    if st != "play":
        return
    play_update()


def stand_effects(P):
    """What Crumb is standing on: jelly bounces, crackers start to crumble, solid ground is remembered as safe."""
    fy = math.floor((P.y + P.h + 1) / T)
    under = [(tx, fy, tile(tx, fy)) for tx in {math.floor((P.x + 3) / T), math.floor((P.x + P.w - 3) / T)}]
    jelly = [u for u in under if u[2] == JELLY]
    if jelly:
        tx, ty, _ = jelly[0]
        pound = bool(P.gpf)
        gp_cancel()
        P.vy = -17 if pound else -14.2
        P.ground = False
        P.bnc = 1
        P._sq = 1
        # the whole slab of joined jelly wobbles together
        x = tx
        while tile(x - 1, ty) == JELLY:
            x -= 1
        while tile(x, ty) == JELLY:
            S.jelly[(x, ty)] = 18
            x += 1
        snd(180, 520, .22, "sine", .09 if pound else .07)
        snd(520, 900, .1, "triangle", .03)
        for i in range(6):
            S.fx.append(O(k="spark", x=tx * T + 4 + i * 5, y=ty * T, vx=(i - 2.5) * .6, vy=-1.5 - rnd(), life=16,
                          c="#ff9ad5" if i % 2 else "#ffffff"))
        return
    for tx, ty, v in under:
        if v == CRUMBLE and (tx, ty) not in S.crumble:
            S.crumble[(tx, ty)] = 1
            snd(330, 200, .06, "square", .025)
    if all(v in (1, 2, 3, 4, 5, 6) for _, _, v in under):
        x0, x1 = math.floor(P.x / T) - 1, math.floor((P.x + P.w) / T) + 1
        near = any(tile(x, y) >= SPIKE_UP for x in range(x0, x1 + 1) for y in range(fy - 2, fy + 1))
        if not near:
            P.safe = (P.x, P.y + P.h)


def update_tiles():
    """Crackers crumble a moment after being stepped on and grow back later; jelly settles."""
    for c in list(S.crumble):
        t = S.crumble[c]
        x, y = c
        if t > 0:
            t += 1
            if t >= CRUMBLE_T:
                S.grid[y][x] = 0
                t = -CRUMBLE_BACK
                snd(220, 90, .14, "square", .035)
                for i in range(6):
                    S.fx.append(O(k="crumb", x=x * T + 4 + i * 5, y=y * T + 10, vx=(rnd() - .5) * 2,
                                  vy=-rnd() * 1.5, life=30, c="#e8c07a" if i % 2 else "#b8843e"))
        else:
            t += 1
            if t >= 0:
                P = S.P
                if P and ov(P, R(x * T, y * T, T, T)):
                    t = -1
                else:
                    S.grid[y][x] = CRUMBLE
                    del S.crumble[c]
                    continue
        S.crumble[c] = t
    for c in list(S.jelly):
        S.jelly[c] -= 1
        if S.jelly[c] <= 0:
            del S.jelly[c]


def play_update():
    P, keys, tick = S.P, S.keys, S.tick
    update_tiles()
    if P.throw > 0:
        P.throw -= 1
        if P.throw == THROW_RELEASE:
            if P.fire and not P.roll > 0:
                throw_release(P)
            else:
                P.throw = 0
    if S.irisO < 40:
        S.irisO += 1
    if P.inv > 0:
        P.inv -= 1
    if P.fire and tick % 4 == 0 and (not P.ground or abs(P.vx) > 2.5):
        S.fx.append(O(k="spark", x=P.x + P.w / 2 - P.face * 8, y=P.y + P.h - 4, vx=-P.face * .6, vy=-1.3, life=16,
                      c="#ff8a2a" if tick % 8 else "#ffd84d"))
    if P.mt > 0:
        P.mt -= 1
    if P.rcd > 0:
        P.rcd -= 1
        if P.rcd == 0:
            P.rflash = 45
            snd(880, 1320, .14, "sine", .08)
    if P.rflash > 0:
        P.rflash -= 1
    if P.rdeny > 0:
        P.rdeny -= 1
    if P.rbuf > 0:
        P.rbuf -= 1
        if P.ground and not P.roll > 0 and not P.rcd > 0:
            start_roll()
    rolling = P.roll > 0
    if P.gpl > 0:
        P.gpl -= 1
    down, jump = keys.get("down"), keys.get("jump")
    if not down:
        P.dpr = 0
    if down and not P.dpr:
        P.dpr = 1
        if not P.ground and not rolling and not gp_act() and not P.gpl > 0:
            P.gp = GPW
            P.gpf = 0
            P.vx *= .3
            snd(520, 180, .12, "triangle", .07)
    if gp_act() or P.gpl > 0:
        P.mk = 0
        P.mt = max(P.mt or 0, 4)
    if rolling and P.ground and P.roll % 4 == 0:
        S.fx.append(O(k="spark", x=P.x + P.w / 2 - P.rdir * 8, y=P.y + P.h - 2, vx=-P.rdir * .7, vy=-.5, life=14,
                      c="#e7d3a8"))
    NH, DH = (42, 24) if P.big else (28, 18)
    if rolling:
        pass
    elif down and not P.duck and P.ground:
        P.duck = 1
        P.y += NH - DH
        P.h = DH
    elif not down and P.duck:
        ny = P.y - (NH - DH)
        if not solid(P.x + 3, ny) and not solid(P.x + P.w - 3, ny):
            P.duck = 0
            P.y = ny
            P.h = NH
    L, Rk = keys.get("left"), keys.get("right")
    mx = 5.2 if keys.get("run") and not P.ohd > 0 else 3.6
    cr = P.duck and P.ground
    # wall slide / wall jump
    P.ws = 0
    if not P.ground and not rolling and not P.duck and not gp_act() and not P.gpl > 0 and not P.wjl > 0:
        pd = 1 if Rk and not L else (-1 if L and not Rk else 0)
        if pd:
            ex = P.x + P.w + 1.2 if pd > 0 else P.x - 1.2
            if solid(ex, P.y + 6) and (solid(ex, P.y + P.h - 7) or solid(ex, P.y + P.h / 2)):
                P.ws = pd
    if P.ws:
        P.wct = 6
        P.wside = P.ws
    elif P.wct > 0:
        P.wct -= 1
    jpress = bool(jump) and not P.jprev
    P.jprev = bool(jump)
    if jpress and not P.ground and P.wct > 0 and not rolling and not P.ohd > 0 and not gp_act() and not P.gpl > 0:
        sd = P.wside
        wx = P.x + P.w if sd > 0 else P.x
        wy = P.y + P.h * .6
        P.vy = -11.2
        P.vx = -sd * 5.6
        P.face = -sd
        P.wjl = 9
        P.wct = 0
        P.ws = 0
        P.wjt = 1
        P.wjf = 12
        P.glt = max(0, (P.glt or 0) - 30)
        snd(330, 760, .14, "square", .05)
        snd(900, 1250, .09, "sine", .04)
        for i in range(9):
            S.fx.append(O(k="spark", x=wx, y=wy + (rnd() - .5) * P.h * .7, vx=-sd * (.6 + rnd() * 2),
                          vy=-.8 - rnd() * 1.4, life=18, c="#e7d3a8" if i % 3 else "#ffffff"))
        S.fx.append(O(k="wjring", x=wx, y=wy, d=sd, life=12))
    if P.wjt > 0:
        P.wjt += 1
        k = min(1, P.wjt / 22)
        e = 1 - (1 - k) ** 2
        P.spin = -P.wside * e * math.pi * 2
        if P.wjt > 22 or P.ground or P.ws:
            P.wjt = 0
            P.spin = 0
    if P.wjf > 0:
        P.wjf -= 1
    if P.ws and P.vy >= 0:
        cxp = P.x + P.w if P.ws > 0 else P.x
        if tick % 3 == 0:
            S.fx.append(O(k="spark", x=cxp, y=P.y + P.h - 4, vx=-P.ws * (.3 + rnd() * .6), vy=-.2 - rnd() * .6,
                          life=14, c="#e7d3a8"))
        if tick % 7 == 0:
            snd(170 + rnd() * 40, 120, .05, "triangle", .022)
    if rolling:
        P.vx = P.rdir * (7 - 3.4 * (1 - P.roll / ROLLT))
        P.roll -= 1
    elif P.wjl > 0:
        P.wjl -= 1
        P.vx *= .985
    elif P.gp > 0:
        P.vx *= .7
    elif P.gpf:
        P.vx = 0
    elif P.gpl > 0:
        P.vx *= .5
    elif Rk and not L and not cr:
        P.vx = min(mx, P.vx + .5)
        P.face = 1
    elif L and not Rk and not cr:
        P.vx = max(-mx, P.vx - .5)
        P.face = -1
    else:
        P.vx *= .8 if P.ground else .95
    if abs(P.vx) < .05:
        P.vx = 0
    if P.ws:
        P.face = -P.ws
    if jump and P.ground and not rolling and not P.gpl > 0 and not P.ohd > 0:
        P.vy = -11.6
        P.ground = False
        snd(300, 600, .15, "square", .04)
    if P.bnc and P.vy >= 0:
        P.bnc = 0
    if not jump and P.vy < -3.5 and not P.bnc:
        P.vy = -3.5
    if P.gp > 0:
        P.vy = -.3
        P.gp -= 1
        if P.gp <= 0:
            P.gpf = 1
            P.vy = GPV
            snd(260, 60, .25, "sawtooth", .06)
    elif P.gpf:
        P.vy = GPV
    elif P.ws and P.vy >= 0:
        P.vy = P.vy + (1.9 - P.vy) * .35 if P.vy > 1.9 else min(1.9, P.vy + .2)
    elif jump and P.vy >= 0 and not rolling and not P.ground and not P.ohd > 0:
        P.glf = 1
        P.vy = P.vy + (GLIDE - P.vy) * .2 if P.vy > GLIDE else min(GLIDE, P.vy + .14)
        if tick % 9 == 0:
            S.fx.append(O(k="spark", x=P.x + P.w / 2 + (rnd() - .5) * 10, y=P.y + P.h - 2, vx=0, vy=-.2, life=12,
                          c="#ffffff"))
    else:
        P.vy = min(12, P.vy + .55)
    if P.ohd > 0:
        P.ohd -= 1
    if P.glf and not P.ground:
        P.glt = (P.glt or 0) + 1
        if P.glt >= OHM:
            P.ohd = OHD
            P.glt = 0
            snd(260, 70, .5, "sawtooth", .07)
            snd(1800, 400, .35, "triangle", .04)
            txt(P.x, P.y - 10, "OVERHEAT!")
            for _ in range(8):
                S.fx.append(O(k="puff", x=P.x + P.w / 2 + (rnd() - .5) * 14, y=P.y - 4, vx=(rnd() - .5) * 1.6,
                              vy=-.6 - rnd() * .8, life=30))
    else:
        P.glt = max(0, (P.glt or 0) - (3 if P.ground else 1))
    o = ohs_of(P)
    if o > .4 and tick % 5 == 0:
        S.fx.append(O(k="puff", x=P.x + P.w / 2 + (rnd() - .5) * 10, y=P.y - 2, vx=(rnd() - .5) * .8, vy=-.7,
                      life=26))
    P.gls = (P.gls or 0) + ((1 if P.glf and not P.ground else 0) - (P.gls or 0)) * .16
    P.gla = (P.gla or 0) + P.gls * .95
    P.glf = 0
    # horizontal move + collide
    P.x += P.vx
    if P.x < 0:
        P.x = 0
        P.vx = 0
    edge = P.x + P.w if P.vx > 0 else P.x
    if P.vx != 0:
        for dy in (2, P.h / 2, P.h - 2):
            if solid(edge, P.y + dy):
                if P.vx > 0:
                    P.x = math.floor(edge / T) * T - P.w - .01
                else:
                    P.x = (math.floor(edge / T) + 1) * T + .01
                P.vx = 0
                break
    # vertical move + collide
    P.y += P.vy
    P.ground = False
    if P.vy >= 0:
        for dx in (2, P.w - 2):
            if solid(P.x + dx, P.y + P.h):
                P.y = math.floor((P.y + P.h) / T) * T - P.h
                P.vy = 0
                P.ground = True
                break
    elif solid(P.x + 2, P.y) or solid(P.x + P.w - 2, P.y):
        cx = P.x + P.w / 2
        px = cx if solid(cx, P.y) else (P.x + 2 if solid(P.x + 2, P.y) else P.x + P.w - 2)
        tx, ty = math.floor(px / T), math.floor(P.y / T)
        P.y = (ty + 1) * T
        P.vy = 0
        S.bumps[(tx, ty)] = 8
        if S.grid[ty][tx] == 2 and P.big:
            S.grid[ty][tx] = 0
            S.bumps.pop((tx, ty), None)
            S.score += 50
            bonk()
            for i in range(6):
                S.fx.append(O(k="spark", x=tx * T + 16, y=ty * T + 16, vx=(i - 2.5) * 1.4, vy=-3 - (i % 2) * 2,
                              life=30, c="#d9a25b"))
        if S.grid[ty][tx] == 3:
            S.grid[ty][tx] = 4
            c = S.contents.get((tx, ty))
            if c:
                t = "cookie" if (c == "pizza" and P.big) else c
                S.items.append(O(t=t, x=tx * T + 5, y=ty * T - 22, w=22, h=22, vx=1.3 if t == "pizza" else 0, vy=-3))
                snd(500, 900, .2, "triangle", .08)
            else:
                S.coinsN += 1
                S.score += 200
                ding()
                S.fx.append(O(k="coin", x=tx * T + 16, y=ty * T - 8, vy=-5, life=28))
                txt(tx * T + 16, ty * T - 30, "+200")
    if P.ground:
        stand_effects(P)
    if P.gpf and P.ground:
        gp_impact()
    if spike_hit(P):
        spike_hurt()
        if S.state != "play":
            return
    if P.y > VH + 40:
        die()
    for c in S.coins:
        if not c.got and abs(c.x - (P.x + P.w / 2)) < 18 and abs(c.y - (P.y + P.h / 2)) < P.h / 2 + 10:
            c.got = True
            S.coinsN += 1
            S.score += 100
            ding()
            coin_fx(c.x, c.y)
    for it in S.items:
        it.vy = min(10, it.vy + .4)
        it.x += it.vx
        if it.vx and solid(it.x + it.w if it.vx > 0 else it.x, it.y + it.h / 2):
            it.vx *= -1
        it.y += it.vy
        if it.vy >= 0 and (solid(it.x + 3, it.y + it.h) or solid(it.x + it.w - 3, it.y + it.h)):
            it.y = math.floor((it.y + it.h) / T) * T - it.h
            it.vy = 0
        if it.y > VH + 50:
            it.gone = 1
        if ov(P, it):
            it.gone = 1
            pow_()
            S.score += 1000
            grow()
            if it.t == "cookie":
                P.fire = True
                txt(it.x, it.y - 6, "FIRE! (F)")
            else:
                txt(it.x, it.y - 6, "BIG!")
            spark_fx(it.x + 11, it.y + 11, "#fff")
    S.items = [i for i in S.items if not i.gone]
    for s in S.shots:
        s.vy = min(8, s.vy + .4)
        s.x += s.vx
        s.y += s.vy
        s.life -= 1
        s.age += 1
        s.rot += s.vx * .11
        s.trail.append((s.x + 5, s.y + 5))
        del s.trail[:-10]
        if S.tick % 2 == 0:
            S.fx.append(O(k="ember", x=s.x + 5 + (rnd() - .5) * 6, y=s.y + 5 + (rnd() - .5) * 6,
                          vx=-s.vx * .12 + (rnd() - .5), vy=(rnd() - .5) - .4, life=12 + rnd() * 10,
                          r=1 + rnd() * 1.4))
        if solid(s.x + (10 if s.vx > 0 else 0), s.y + 5):
            s.life = 0
        elif s.vy > 0 and solid(s.x + 5, s.y + 10):
            s.y = math.floor((s.y + 10) / T) * T - 10
            s.vy = -5
            S.fx.append(O(k="sizzle", x=s.x + 5, y=s.y + 10, life=10))
            for _ in range(4):
                S.fx.append(O(k="ember", x=s.x + 5, y=s.y + 9, vx=(rnd() - .5) * 3, vy=-1 - rnd() * 1.5,
                              life=12 + rnd() * 6, r=1 + rnd()))
            snd(1300, 500, .07, "sawtooth", .018)
        sr = R(s.x, s.y, 10, 10)
        for b in S.bshots:
            if s.life > 0 and b.life > 0 and ov(sr, R(b.x - 2, b.y - 2, 14, 14)):
                b.life = 0
                s.life = 0
                S.score += 50
                bonk()
                spark_fx(b.x + 5, b.y + 5, "#ffd84d")
        for e in S.enemies:
            if not e.dead and s.life > 0 and ov(sr, e):
                e.dead = 1
                s.life = 0
                S.score += 200
                bonk()
                if e.k == "ant" or e.mode == "walk":
                    react()
                spark_fx(e.x + e.w / 2, e.y + e.h / 2, "#ff8a2a")
        B = S.boss
        if B and not B.dead and B.flash <= 0 and s.life > 0 and ov(sr, B):
            s.life = 0
            hit_boss()
        if s.y > VH:
            s.life = 0
            s.quiet = 1
        if s.life <= 0 and not s.quiet:
            cookie_blast(s.x + 5, s.y + 5)
    S.shots = [s for s in S.shots if s.life > 0]
    update_enemies()
    K = S.KEYO
    if K and not K.got and S.state == "play":
        K.t += 1
        K.vy += .4
        K.y += K.vy
        if K.y >= 10 * T - 12:
            K.y = 10 * T - 12
            K.vy = -K.vy * .45 if K.vy > 1.6 else 0
        if ov(P, R(K.x - 12, K.y - 12, 24, 24)):
            free_start()
    if S.boss:
        update_boss()
    update_bshots()
    if S.GOAL < 900 and P.x + P.w > S.GOAL * T + 16 - 3 and P.y + P.h > 62:
        goal_start()
    S.cam = max(0, min(S.W * T - VW, P.x - VW / 2.4))
    S.time -= 1 / 60
    if S.time <= 0:
        die()


def update_enemies():
    P = S.P
    for e in S.enemies:
        if e.dead:
            e.dead += 1
            continue
        if e.kick > 0:
            e.kick -= 1
        if e.k == "nut":
            if e.mode != "walk":
                e.dn = 0
                e.dpend = 0
            else:
                mt = mtime()
                if e.dpend and mt >= e.dstart:
                    e.dpend = 0
                    e.dn = 1
                if e.dn > 0:
                    e.du = (mt - e.dstart) / clock().beat2
                    if e.du >= 1:
                        e.dn = 0
                        e.du = 0
                elif not e.dpend:
                    e.dt = (90 + math.floor(rnd() * 240) if not e.has("dt") else e.dt) - 1
                    if e.dt <= 0:
                        if S.state == "play" and S.cam + 10 < e.x < S.cam + VW - 40 and not e.kick > 0:
                            e.dstart = dance_slot(mt)
                            e.dpend = 1
                        e.dt = 240 + math.floor(rnd() * 200)
        shell = e.k == "nut" and e.mode == "shell"
        if shell:
            e.st += 1
            if e.st > 480:
                e.mode = "walk"
                e.vx = (-1 if P.x < e.x else 1) * .6
        elif not e.dn > 0:
            e.x += e.vx
            f = e.x + e.w if e.vx > 0 else e.x
            if solid(f, e.y + e.h / 2) or not solid(f, e.y + e.h + 4):
                e.vx *= -1
        if e.mode == "slide":
            for o in S.enemies:
                if o is not e and not o.dead and ov(e, o):
                    o.dead = 1
                    S.score += 200
                    bonk()
                    spark_fx(o.x + 13, o.y + 10, "#ff8a2a")
        if not P.roll > 0 and ov(P, e):
            if shell:
                e.mode = "slide"
                e.vx = (1 if P.x + P.w / 2 < e.x + e.w / 2 else -1) * 6.5
                e.kick = 20
                S.score += 100
                bonk()
            elif P.vy > 0 and P.y + P.h - e.y < 18:
                living = e.k == "ant" or e.mode == "walk"
                if e.k == "ant":
                    e.dead = 1
                else:
                    e.mode = "shell"
                    e.vx = 0
                    e.st = 0
                P.y = e.y - P.h - 1
                P.vy = -10 if gp_act() else -8
                if gp_act():
                    gp_cancel()
                    S.shk = 5
                    S.fx.append(O(k="shock", x=P.x + P.w / 2, y=P.y + P.h, life=14))
                S.score += 150
                bonk()
                if living:
                    react()
                txt(e.x, e.y - 6, "+150")
            elif P.inv <= 0 and not e.kick > 0:
                hurt()


def update_boss():
    B, P = S.boss, S.P
    if B.dead:
        S.bossT += 1
        if S.CAGE:
            if S.bossT == 56 and not S.KEYO:
                # drop the key inside this arena (between its walls), wherever the boss fell
                S.KEYO = O(x=max((S.AR0 + 4) * T, min(S.AR1 * T, B.x + B.w / 2)), y=B.y + 22, vy=-7, t=0, got=0)
                spark_fx(S.KEYO.x, S.KEYO.y, "#ffd84d")
                snd(700, 1400, .25, "sine", .09)
        elif S.bossT > 120:
            S.state = "win"
            note_best()
        return
    if B.flash > 0:
        B.flash -= 1
    if not B.has("fcd"):
        B.fcd = 100
    B.fcd -= 1
    if B.fcd <= 0:
        boss_spit()
        B.fcd = (152 if B.hp <= 3 else 180) + math.floor(rnd() * 40)
    if B.q:
        keep = []
        for o in B.q:
            o.t -= 1
            if o.t <= 0:
                o.f()
            else:
                keep.append(o)
        B.q = keep
    S.bossDisp += (B.hp - S.bossDisp) * .03
    B.x += B.vx
    if not B.hopping and not B.ledge:
        if B.x < S.AR0 * T:
            B.vx = abs(B.vx)
        if B.x + B.w > S.AR1 * T:
            B.vx = -abs(B.vx)
    B.vy += .5
    B.y += B.vy
    prevL = B.ledge
    B.ledge = None
    if B.vy >= 0 and (B.hopping == 1 or prevL):
        bcx = B.x + B.w / 2
        for Lg in S.LEDGES:
            if Lg[0] * T < bcx < Lg[1] * T and B.y + B.h - B.vy <= 7 * T + 1 and B.y + B.h >= 7 * T:
                B.y = 7 * T - B.h
                B.vy = 0
                B.ledge = Lg
                break
    gnd = bool(B.ledge) or B.y + B.h >= 10 * T
    if not B.ledge and B.y + B.h >= 10 * T:
        B.y = 10 * T - B.h
        B.vy = 0
    if gnd and B.hopping:
        B.hopping = 0
        B.vx = 0 if B.ledge else (-1 if P.x < B.x else 1)
    B.cd -= 1
    if B.cd <= 0:
        cdv = None

        def hop_to(Lg, vy0):
            tx = (Lg[0] + Lg[1]) / 2 * T
            bc = B.x + B.w / 2
            y, v, n = B.y + B.h, vy0, 0
            while True:
                v += .5
                y += v
                n += 1
                if (v > 0 and y >= 7 * T) or n >= 120:
                    break
            B.vy = vy0
            B.vx = (tx - bc) / n
            B.hopping = 1

        if B.ledge:
            if B.ls == 1:
                B.ls = 2
                cdv = 48
            elif B.ls == 2:
                hop_to(S.LEDGES[1] if B.ledge is S.LEDGES[0] else S.LEDGES[0], -9)
                B.ls = 3
                cdv = 40
            elif B.ls == 3:
                B.ls = 4
                cdv = 48
            else:
                B.vy = -6
                B.vx = -2 if S.LMID * T < B.x + B.w / 2 else 2
                B.hopping = 2
                B.ls = 0
                B.hc = 0
                cdv = 52
        elif gnd and (B.hc or 0) >= 2 and len(S.LEDGES) >= 2:
            bc = B.x + B.w / 2
            hop_to(S.LEDGES[0] if abs(bc - lcx(0)) < abs(bc - lcx(1)) else S.LEDGES[1], -11)
            B.ls = 1
            cdv = 44
        elif gnd and rnd() < .5:
            B.vy = -11
            B.hc = (B.hc or 0) + 1
        B.cd = cdv if cdv is not None else (42 if B.hp <= 3 else 52) + math.floor(rnd() * 40)
    if not P.roll > 0 and ov(P, B):
        if P.vy > 0 and P.y + P.h - B.y < 22 and B.flash <= 0:
            hit_boss()
            P.y = B.y - P.h - 1
            P.vy = -10
            if gp_act():
                gp_cancel()
                S.shk = 6
        elif P.inv <= 0 and B.flash <= 0:
            hurt()


def update_bshots():
    P = S.P
    for b in S.bshots:
        b.age += 1
        b.life -= 1
        if b.k == "seek":
            if b.age < 80:
                tx = P.x + P.w / 2 - (b.x + 5)
                ty = P.y + P.h / 2 - (b.y + 5)
                dl = math.hypot(tx, ty) or 1
                k = .02 if b.age < 14 else .06
                b.vx += (tx / dl * b.sp - b.vx) * k
                b.vy += (ty / dl * b.sp - b.vy) * k
            b.x += b.vx
            b.y += b.vy
            if b.y > 10 * T - 6:
                b.life = 0
        elif b.k == "roll":
            if b.y < 10 * T - 13:
                b.vy += .35
                b.y = min(10 * T - 13, b.y + b.vy)
                if b.y >= 10 * T - 13:
                    b.vy = 0
            else:
                b.y = 10 * T - 13
            b.x += b.vx
        else:
            b.vy += .12
            b.x += b.vx
            b.y += b.vy
            if b.y > 10 * T - 6:
                b.life = 0
        if solid(b.x + 5, b.y + 5):
            b.life = 0
        if S.state == "play" and P.inv <= 0 and not P.roll > 0 and ov(P, R(b.x, b.y, 10, 10)):
            b.life = 0
            hurt()
    S.bshots = [b for b in S.bshots if b.life > 0]


# ------------------------------------------------------------------ goal: bite the pole, slide, hop, walk to the picnic
def slide_x():
    P = S.P
    k = (1.5 if P.big else 1) * .82
    return S.GS.px - 2 - 6.4 * k - P.w / 2


def mouth_y():
    P = S.P
    return P.y + P.h - 16.6 * (1.5 if P.big else 1) * .82


def crumb_burst(n):
    my = mouth_y()
    for _ in range(n):
        S.fx.append(O(k="crumb", x=S.GS.px + (rnd() - .5) * 6, y=my + (rnd() - .3) * 4,
                      vx=(-1 if rnd() < .5 else 1) * (.4 + rnd() * 1.4), vy=-1.2 - rnd() * 1.4, life=30,
                      c="#d9964a" if rnd() < .5 else "#f3c27f"))


def goal_start():
    P = S.P
    P.spin = P.wjt = P.ws = 0
    px, gy = S.GOAL * T + 16, 10 * T
    NH = 42 if P.big else 28
    if P.h != NH:
        P.y -= NH - P.h
        P.h = NH
    P.duck = P.roll = P.rbuf = 0
    gp_cancel()
    P.glt = P.ohd = P.gls = P.glf = P.inv = 0
    P.vx = P.vy = 0
    P.ground = False
    P.face = 1
    P.sl = 1
    S.score += math.floor(S.time) * 10
    P.x = px - P.w / 2
    P.y = max(P.y, 66)
    pic = px + 540
    nw = math.ceil((pic + 360) / T)
    for y in range(H):
        rowv = S.grid[y]
        if len(rowv) < nw:
            rowv.extend([0] * (nw - len(rowv)))
        for x in range(S.GOAL - 2, nw):
            if y >= 10:
                rowv[x] = 1
            elif x > S.GOAL and y >= 2:
                rowv[x] = 0
            elif x > S.GOAL and y < 2:
                rowv[x] = 6 if S.UG else 0
    S.W = nw
    S.enemies = [e for e in S.enemies if e.x < px - 60]
    S.coins = [c for c in S.coins if c.x < px - 40]
    S.items, S.shots, S.bshots = [], [], []
    S.GS = O(ph=0, t=0, px=px, gy=gy, pic=pic, marks=[P.y + P.h - 16.6 * (1.23 if P.big else .82)], vs=.6, hop=0,
             pan=-1, cam0=S.cam, stopX=pic + 4 - P.w * (1.3 if P.big else 1),
             P2=O(x=pic + 4 - P.w / 2, y=gy - P.h, w=P.w, h=P.h, vx=0, vy=0, ground=True, face=-1, big=P.big,
                  fire=False, inv=0, duck=0, mk=2, mt=0))
    P.x = slide_x()
    S.state = "goal"
    snd(180, 90, .12, "square", .09)


def goal_update():
    G, P = S.GS, S.P
    G.t += 1
    P.vx = 0
    P.mt = 0
    if G.ph == 0:
        P.x = slide_x()
        P.vy = 0
        if G.t % 5 == 1:
            snd(300, 120, .06, "square", .06)
            crumb_burst(4)
        if G.t >= 18:
            G.ph, G.t = 1, 0
    elif G.ph == 1:
        G.vs = min(3.8, G.vs + .06)
        P.y += G.vs
        P.vy = G.vs
        P.x = slide_x()
        if G.t % 4 == 0:
            snd(820 + rnd() * 120, 520, .05, "triangle", .03)
            crumb_burst(2)
        if G.t % 6 == 0:
            S.fx.append(O(k="spark", x=G.px + (-4 if rnd() < .5 else 4), y=mouth_y() + 3, vx=0, vy=-.3, life=10,
                          c="#ffffff"))
        if P.y + P.h >= G.gy:
            P.y = G.gy - P.h
            P.vy = 0
            P.ground = True
            P.sl = 2
            G.ph, G.t = 2, 0
            S.shk = 5
            snd(110, 50, .25, "sine", .2)
            for i in range(8):
                d = 1 if i % 2 else -1
                S.fx.append(O(k="spark", x=G.px + d * 4, y=G.gy - 2, vx=d * (1 + rnd() * 2), vy=-1 - rnd() * 1.4,
                              life=16, c="#e7d3a8"))
    elif G.ph == 2:
        P.mk, P.mt = 2, 3
        if G.t == 14:
            P.vy = -9
            P.ground = False
            G.hop = 1
            P.spin = 0
            pow_()
            confetti(G.px, G.gy - 80, 26, 3.5)
        if G.t == 56:
            P.vy = -10.2
            P.ground = False
            G.hop = 2
            P.spin = 0
            snd(500, 900, .15, "square", .05)
        if G.hop:
            P.vy += .55
            P.y += P.vy
            P.spin += (1 if G.hop == 1 else -1) * (.2 if G.hop == 1 else .3)
            if P.vy > 0 and abs(P.vy) < .5 and G.t % 3 == 0:
                spark_fx(P.x + P.w / 2, P.y, "#ffd84d")
            if P.y + P.h >= G.gy and P.vy > 0:
                P.y = G.gy - P.h
                P.vy = 0
                P.ground = True
                P.spin = 0
                if G.hop == 2:
                    G.ph, G.t = 3, 0
                    confetti(G.px, G.gy - 90, 34, 4)
                else:
                    spark_fx(P.x + P.w / 2, G.gy - 4, "#fff")
                    snd(130, 70, .12, "triangle", .08)
                G.hop = 0
    elif G.ph == 3:
        P.face, P.mk, P.mt = 1, 2, 2
        P.ground = True
        if G.t < 6:
            P.vx = 0
        else:
            near = G.stopX - (P.x + P.w / 2)
            v = max(.7, min(4.2, near * .085))
            P.vx = v
            P.x += min(v, max(0, near))
            if G.pan < 0 and P.x > S.cam + VW + 24:
                G.pan = 0
                G.cam0 = S.cam
                G.camT = G.pic - VW / 2
            if 0 <= G.pan < 1:
                G.pan = min(1, G.pan + 1 / 60)
                e = G.pan * G.pan * (3 - 2 * G.pan)
                S.cam = G.cam0 + (G.camT - G.cam0) * e
            if near < 90 and not G.P2.hopped:
                G.P2.hopped = 1
                G.P2.vy = -5.5
                G.P2.ground = False
            lk = max(0, min(1, (34 - near) / 34))
            P.kiss = G.P2.kiss = lk * lk * (3 - 2 * lk) * .9
            if near <= .6 and G.pan >= 1:
                G.ph, G.t = 4, 0
                G.k0 = P.kiss
                P.vx = 0
        q = G.P2
        if not q.ground:
            q.vy += .55
            q.y += q.vy
            if q.y >= G.gy - q.h:
                q.y = G.gy - q.h
                q.vy = 0
                q.ground = True
    elif G.ph == 4:
        P.vx = 0
        P.face = 1
        q = G.P2
        q.face = -1
        P.mt = 2 if G.t < 10 else 0
        q.mt = 0
        k = max(0, min(1, G.t / 12))
        ek0 = k * k * (3 - 2 * k)
        ek = 1 - (1 - (G.k0 or 0) / .9) * (1 - ek0)
        if G.pan < 1:
            G.pan = min(1, G.pan + 1 / 60)
            e = G.pan * G.pan * (3 - 2 * G.pan)
            S.cam = G.cam0 + (G.camT - G.cam0) * e
        rel = max(0, min(1, (G.t - 96) / 12))
        P.kiss = q.kiss = ek * (1 - rel)
        cx = G.pic + 4 - P.w / 2
        _kiss_beats(G.t, cx, P, G.gy)
        if G.t >= 108:
            P.kiss = q.kiss = 0
            S.state = "clear"
            S.clearT = 0


def _kiss_beats(t, cx, P, gy):
    if t == 4:
        snd(520, 700, .08, "triangle", .06)
    if t == 24:
        snd(880, 1250, .07, "sine", .09)
        snd(1100, 1500, .09, "sine", .08, .09)
        heart_fx(cx, P.y - 14, 5)
        confetti(cx, gy - 70, 34, 4)
        pow_()
    if 24 < t < 96 and t % 12 == 0:
        heart_fx(cx, P.y - 14, 1)
        if t % 24 == 0:
            spark_fx(cx, P.y + 4, "#ffb3c9")


# ------------------------------------------------------------------ boss level ending: free the partner from the cage
def free_start():
    P = S.P
    P.spin = P.wjt = P.ws = 0
    S.KEYO.got = 1
    S.state = "free"
    S.bshots = []
    S.FS = O(ph=0, t=0, tx=S.CAGE.cx - 18 - P.w * (1.3 if P.big else 1), hold=1, kiss=0)
    P.vx = P.roll = P.duck = 0
    P.mk, P.mt = 1, 0
    snd(900, 1500, .18, "sine", .09)
    snd(1200, 1800, .14, "sine", .08, .12)
    spark_fx(S.KEYO.x, S.KEYO.y, "#ffd84d")


def free_update():
    F, P, C = S.FS, S.P, S.CAGE
    q, gy = C.q, 10 * T
    F.t += 1
    tc = max(0, min(S.W * T - VW, C.cx - VW / 2 - 10))
    S.cam += (tc - S.cam) * .07
    if F.ph == 0 or not P.ground:
        P.vy += .5
        P.y += P.vy
        if P.y + P.h >= gy:
            P.y = gy - P.h
            P.vy = 0
            P.ground = True
    if F.ph == 0:
        dx = F.tx - (P.x + P.w / 2)
        v = max(.8, min(3.4, abs(dx) * .1))
        P.face = 1 if dx >= 0 else -1
        P.mk = 1
        if abs(dx) <= v:
            P.x += dx
            P.vx = 0
            F.ph, F.t = 1, 0
            P.face = 1
        else:
            P.x += math.copysign(v, dx)
            P.vx = math.copysign(v, dx)
        q.face = -1
    elif F.ph == 1:
        P.vx = 0
        P.face = 1
        P.mk = 1
        if F.t in (12, 20):
            snd(300 + F.t * 6, 200, .06, "square", .06)
        if F.t == 28:
            C.lock = 2
            C.lt = 0
            snd(1600, 900, .16, "triangle", .09)
            spark_fx(C.cx - 27, gy - 26, "#ffd84d")
            F.hold = 0
        if C.lock == 2:
            C.lt += 1
        if F.t >= 46:
            F.ph, F.t = 2, 0
    elif F.ph == 2:
        C.lt += 1
        P.vx = 0
        P.mk, P.mt = 2, 2
        if F.t == 2:
            snd(180, 120, .4, "sawtooth", .05)
        k = min(1, F.t / 26)
        C.open = k * k * (3 - 2 * k)
        if F.t == 8:
            q.hopv = -5
        if q.has("hopv") and q.hopv is not None:
            q.hopv += .5
            q.y += q.hopv
            if q.y >= gy - q.h:
                q.y = gy - q.h
                q.hopv = None
        elif F.t < 8:
            q.y = gy - q.h
        if F.t >= 22 and (not q.has("hopv") or q.hopv is None):
            goal = C.cx - 18 - C.cx
            dxq = goal - q.dx
            q.face = -1
            q.vx = -2
            if abs(dxq) < 2:
                q.dx = goal
                F.ph, F.t = 3, 0
                F.k0 = 0
            else:
                q.dx += math.copysign(min(2.1, abs(dxq) * .25 + .4), dxq)
        if F.t >= 140:
            F.ph, F.t = 3, 0
    elif F.ph == 3:
        P.vx = 0
        P.face = 1
        q.face = -1
        P.mt = 2 if F.t < 10 else 0
        q.mt = 0
        q.y = gy - q.h
        k = max(0, min(1, F.t / 14))
        ek = k * k * (3 - 2 * k)
        rel = max(0, min(1, (F.t - 96) / 12))
        P.kiss = q.kiss = ek * (1 - rel)
        cx = (P.x + P.w / 2 + C.cx + q.dx) / 2
        if F.t == 4:
            snd(520, 700, .08, "triangle", .06)
        if F.t == 24:
            snd(880, 1250, .07, "sine", .09)
            snd(1100, 1500, .09, "sine", .08, .09)
            heart_fx(cx, P.y - 14, 5)
            confetti(cx, gy - 70, 40, 4)
            pow_()
        if 24 < F.t < 96 and F.t % 12 == 0:
            heart_fx(cx, P.y - 14, 1)
            if F.t % 24 == 0:
                spark_fx(cx, P.y + 4, "#ffb3c9")
        if F.t >= 108:
            P.kiss = q.kiss = 0
            S.state = "clear"
            S.clearT = 0
