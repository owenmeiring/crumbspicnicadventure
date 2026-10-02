"""World 1, stages 1-4 to 1-9: built with a tiny level-building language.

Coordinates are in tiles. Rows run 0 (top) to 11; the floor is rows 10-11.
Movement limits the layouts are designed around (small Crumb):
  - a jump climbs 3 tiles; a running jump clears about 5-6 tiles
  - floating (hold jump while falling) stretches that to 10+ tiles, but overheats after 2 seconds
  - jelly pads bounce 5 tiles high (8 with a ground pound)
  - wall jumps climb between walls 2-3 tiles apart
"""

from .levels import EH

HONEY, FROST, FUDGE, MELON, SKY, KITCHEN = 3, 4, 5, 6, 7, 2


class Lv:
    def __init__(self, w, theme, name, time, ceiling=False):
        self.w, self.theme, self.name, self.time = w, theme, name, time
        self.g = [["."] * w for _ in range(EH)]
        for x in range(w):
            self.g[10][x] = self.g[11][x] = "#"
            if ceiling:
                self.g[0][x] = self.g[1][x] = "c"
        self.coins, self.enemies, self.contents = [], [], {}
        self.goal, self.boss = None, None

    # ---- tiles
    def fill(self, x0, x1, y0, y1, ch):
        for y in range(max(0, y0), min(EH - 1, y1) + 1):
            for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                self.g[y][x] = ch
        return self

    def pit(self, x0, x1):
        return self.fill(x0, x1, 10, 11, ".")

    def spikes(self, x0, x1, y=9):
        """Toothpicks pointing up, standing on whatever is below."""
        return self.fill(x0, x1, y, y, "x")

    def drips(self, x0, x1, y):
        """Toothpicks pointing down, hanging from whatever is above."""
        return self.fill(x0, x1, y, y, "v")

    def plat(self, x, y, n=1, ch="s"):
        return self.fill(x, x + n - 1, y, y, ch)

    def block(self, x0, x1, top, ch="#", bottom=9):
        return self.fill(x0, x1, top, bottom, ch)

    def pillar(self, x, top, n=1, ch="s"):
        """A column from `top` all the way down (through the floor rows)."""
        return self.fill(x, x + n - 1, top, 11, ch)

    def jelly(self, x, y, n=1):
        return self.fill(x, x + n - 1, y, y, "j")

    def crumble(self, x, y, n=1):
        return self.fill(x, x + n - 1, y, y, "k")

    def bricks(self, x, y, n=1):
        return self.fill(x, x + n - 1, y, y, "b")

    def q(self, x, y, what=None):
        self.g[y][x] = "?"
        if what:
            self.contents[(x, y)] = what
        return self

    # ---- things
    def coin(self, x, y, n=1):
        for i in range(n):
            if self.g[y][x + i] == ".":
                self.coins.append([x + i, y])
        return self

    def arc(self, x, y, n):
        for i in range(n):
            dy = -1 if 0 < i < n - 1 else 0
            if n >= 5 and 1 < i < n - 2:
                dy = -2
            self.coin(x + i, y + dy)
        return self

    def ant(self, x, y, d=-1):
        self.enemies.append({"k": "ant", "x": x, "y": y, "d": d})
        return self

    def nut(self, x, y, d=-1):
        self.enemies.append({"k": "nut", "x": x, "y": y, "d": d})
        return self

    def done(self, goal=None, boss=None):
        self.goal, self.boss = goal, boss
        for q in self.enemies:
            assert self.g[q["y"]][q["x"]] == ".", (self.name, "enemy inside a tile", q)
            assert self.g[q["y"] + 1][q["x"]] in "#bsck?j", (self.name, "enemy floating", q)
        return {"name": self.name, "theme": self.theme, "time": self.time, "w": self.w, "g": self.g,
                "start": [2, 9], "goal": goal, "contents": self.contents, "coins": self.coins,
                "enemies": self.enemies, "boss": boss}


# ============================================================ 1-4 HONEYCOMB HOLLOW
def honeycomb():
    L = Lv(252, HONEY, "Honeycomb Hollow", 420, ceiling=True)
    L.arc(6, 7, 5).q(12, 6, "pizza").ant(16, 9)
    # first stingers, then a cracker bridge over the honey pit
    L.spikes(20, 23).arc(19, 6, 6)
    L.pit(27, 35).crumble(27, 9, 9).coin(28, 7, 7)
    # a ledge with stingers hanging low over it: walk it, don't jump on it
    L.block(40, 45, 7, "s").drips(41, 44, 2).coin(41, 6, 4).ant(47, 9)
    # jelly up onto a honey shelf
    L.jelly(53, 10, 2).block(57, 62, 5, "s").coin(53, 6, 2).coin(53, 4, 2).nut(60, 4)
    # drop across the honey lake via a two-wide stub
    L.pit(63, 74).pillar(68, 8, 2).arc(64, 6, 4).arc(70, 7, 4)
    # low tunnel with critters
    L.q(78, 6, "cookie").q(79, 6).fill(81, 92, 2, 6, "c").ant(85, 9).nut(90, 9).coin(82, 9, 2).coin(87, 9, 2)
    # first wall-jump shaft: under the hanging comb, then up between the walls
    L.fill(100, 101, 2, 7, "c").block(104, 110, 4, "s").coin(102, 5).coin(103, 3).coin(102, 8)
    # cracker run along the top with stingers waiting below
    L.crumble(111, 4, 7).spikes(111, 124).plat(118, 6, 4).coin(112, 3, 5).ant(120, 5)
    # bouncing over the long honey pit
    L.pit(128, 149)
    for x in (131, 137, 143):
        L.pillar(x, 9).jelly(x, 9)
    L.arc(132, 5, 5).arc(138, 5, 5).arc(144, 6, 5)
    # first float: a ten-wide gap with a coin trail to follow
    L.pit(154, 163).coin(155, 7, 2).coin(157, 6, 3).coin(160, 7, 3)
    # platforms over a stinger floor, guarded
    L.spikes(170, 189)
    L.plat(172, 7, 3).plat(178, 7, 3).plat(184, 7, 3).ant(179, 6, 1).nut(185, 6)
    L.arc(176, 5, 3).arc(182, 5, 3)
    # cracker staircase up and over
    L.crumble(196, 8).crumble(199, 6).crumble(202, 4).block(205, 211, 4, "s").coin(206, 3, 5)
    L.pit(212, 220).jelly(216, 10).fill(216, 216, 11, 11, "s").arc(213, 6, 7)
    L.ant(228, 9).nut(233, 9).arc(226, 7, 5)
    return L.done(goal=242)


# ============================================================ 1-5 FROSTED PEAKS
def frosted():
    L = Lv(272, FROST, "Frosted Peaks", 450)
    L.arc(5, 7, 5).q(9, 6, "pizza").ant(15, 9)
    # three cake tiers up to the first summit
    L.block(23, 27, 8).block(28, 32, 6).block(33, 37, 4).arc(29, 4, 4).arc(33, 2, 5)
    # the gorge: float it, or risk the lone cracker
    L.pit(38, 48).crumble(43, 6).coin(40, 4, 3).coin(44, 5, 3)
    L.block(49, 55, 6).nut(53, 5)
    # chimney one: up between the ice pillar and the cake cliff
    L.fill(62, 62, 2, 7, "s").block(66, 76, 2).coin(63, 8, 3).coin(64, 5).coin(64, 3)
    # icing bridge high above the shards
    L.crumble(77, 3, 10).plat(87, 3, 4).spikes(77, 100).coin(78, 2, 8)
    # big glide down to the landing pillar
    L.pit(101, 111).block(106, 112, 8).fill(106, 112, 10, 11, "#").coin(94, 5, 3).coin(99, 6, 3).coin(103, 7, 2)
    # ice cave: hanging shards overhead, single shards underfoot. Small hops only.
    L.fill(118, 134, 0, 5, "s").drips(119, 133, 6).spikes(124, 124).spikes(129, 129).ant(127, 9)
    L.coin(120, 8, 3).coin(131, 8, 3)
    # avalanche of crackers
    L.pit(142, 170)
    for x, y in ((145, 8), (150, 8), (155, 7), (160, 8), (164, 6)):
        L.crumble(x, y, 2).coin(x, y - 2, 2)
    # chimney two: taller, with shards waiting at the bottom
    L.spikes(178, 180).fill(182, 182, 1, 7, "s").block(185, 193, 1).coin(183, 8).coin(184, 5).coin(183, 3)
    # the long glide with one rest stop
    L.spikes(194, 215).pit(216, 224).block(208, 210, 5, "s").fill(208, 210, 6, 9, "s")
    L.coin(197, 3, 4).coin(202, 4, 4).coin(213, 4, 4).coin(219, 5, 4)
    L.block(225, 240, 7).ant(230, 6).nut(236, 6, 1).arc(226, 5, 5)
    L.ant(248, 9).arc(244, 7, 6)
    return L.done(goal=262)


# ============================================================ 1-6 FUDGE MINES (checkpoint)
def fudge():
    L = Lv(272, FUDGE, "Fudge Mines", 460, ceiling=True)
    L.q(10, 6, "cookie").q(11, 6).arc(5, 7, 4).ant(17, 9)
    # the sealed vault: pound through the bricks to get in
    L.block(21, 23, 8).block(24, 44, 6).fill(30, 38, 7, 9, ".").bricks(30, 6, 4).fill(39, 44, 7, 9, ".")
    L.fill(40, 40, 2, 5, "c").coin(31, 8, 7).coin(26, 5, 3).nut(36, 9)
    # stalactite corridor: short hops between fudge pits
    L.fill(46, 68, 2, 5, "c").drips(47, 67, 6).pit(50, 51).pit(56, 58).pit(63, 64).coin(53, 8, 2).coin(60, 8, 2)
    # jelly shaft up to the cliff
    L.jelly(78, 10, 2).block(80, 82, 5, "s").jelly(82, 5).block(84, 95, 4, "s").coin(79, 6).coin(81, 3).arc(85, 3, 5)
    # plank bridge over the fudge river (it won't hold you long)
    L.pit(96, 121).crumble(96, 5, 12).crumble(112, 5, 4).plat(119, 6, 3).coin(97, 4, 10).coin(113, 4, 3)
    # two floors: bricks up top (pound through at the wall), critters below
    L.block(125, 160, 6, "#", 7).bricks(140, 6, 2).bricks(140, 7, 2).fill(145, 145, 2, 5, "c")
    L.q(130, 5, "pizza").coin(126, 5, 3).coin(134, 5, 5)
    L.ant(131, 9).nut(137, 9).ant(149, 9, 1).spikes(144, 144).spikes(153, 154)
    # chimney out of the big chamber
    L.spikes(178, 180).fill(182, 182, 2, 7, "c").block(186, 199, 3, "s").coin(183, 6).coin(184, 4).ant(174, 9)
    L.coin(176, 8, 4)
    # cliff run, then glide down the fudge falls
    L.nut(195, 2, -1).coin(188, 2, 4).pit(211, 220).block(200, 210, 3, "s").coin(203, 2, 4)
    L.block(221, 230, 8).coin(213, 5, 2).coin(216, 6, 3).ant(226, 7)
    L.nut(240, 9).ant(246, 9).arc(236, 7, 5).arc(250, 7, 4)
    return L.done(goal=262)


# ============================================================ 1-7 MELON GROVE
def melon():
    L = Lv(282, MELON, "Melon Grove", 480)
    L.arc(5, 7, 4).q(9, 6, "pizza").ant(13, 9)
    # branch hopping over the grove floor (it's a long way down)
    L.pit(16, 58)
    for x, y, n in ((18, 8, 2), (23, 7, 2), (28, 8, 1), (32, 6, 2), (37, 7, 2), (42, 5, 3), (48, 7, 1), (52, 8, 2)):
        L.plat(x, y, n).coin(x, y - 1, n)
    L.ant(43, 4)
    # thorn floor under a canopy of perches
    L.spikes(72, 98).plat(74, 7, 2).plat(79, 5, 2).crumble(84, 7, 2).plat(89, 5, 2).plat(94, 7, 2)
    L.coin(79, 4, 2).coin(89, 4, 2).q(66, 6, "cookie")
    # melon bounces at four heights
    L.pit(101, 129)
    for x, top in ((104, 9), (110, 7), (116, 9), (122, 6)):
        L.pillar(x, top).jelly(x, top)
    L.arc(105, 4, 5).arc(111, 3, 5).arc(117, 4, 5)
    # trunk chimney, then a canopy walk and falling leaves
    L.fill(139, 139, 2, 7, "s").fill(142, 143, 2, 9, "s").pit(144, 160).plat(144, 3, 9).crumble(153, 4, 8)
    L.coin(140, 6).coin(141, 4).coin(145, 2, 6).coin(154, 3, 6).ant(150, 2)
    # thorny branches overhead, critters underfoot
    L.plat(166, 5, 6).drips(166, 6, 6).plat(178, 5, 6).drips(178, 6, 6).plat(191, 5, 4).drips(191, 6, 4)
    L.pit(175, 176).pit(188, 189).ant(170, 9).nut(181, 9).ant(184, 9, 1).nut(193, 9)
    # the tall tree and the long glide
    L.plat(196, 7, 2).plat(199, 4, 1).block(200, 203, 2, "s").pit(204, 235)
    L.crumble(218, 6, 2).pillar(227, 9).jelly(227, 9)
    L.coin(206, 2, 4).coin(212, 4, 4).coin(221, 5, 4).coin(229, 5, 4)
    L.arc(240, 7, 5).ant(247, 9).nut(255, 9).ant(260, 9, 1)
    return L.done(goal=272)


# ============================================================ 1-8 SUNDAE SKIES (checkpoint)
def sundae():
    L = Lv(302, SKY, "Sundae Skies", 520)
    L.pit(12, 299).fill(296, 301, 10, 11, "#").arc(4, 7, 4)
    # island hopping, some with candy shards hanging underneath
    for x, y, n, under in ((15, 8, 3, False), (21, 6, 2, True), (26, 8, 2, False), (31, 5, 3, True),
                           (42, 5, 2, True), (47, 8, 3, False)):
        L.fill(x, x + n - 1, y, y + 1, "#").coin(x, y - 1, n)
        if under:
            L.drips(x, x + n - 1, y + 2)
    L.crumble(37, 7, 2).q(32, 2, "pizza")
    # jelly chain at mixed heights
    for x, top in ((55, 9), (61, 7), (67, 9), (73, 6), (79, 8)):
        L.pillar(x, top).jelly(x, top)
        L.coin(x - 2, top - 4, 2)
    # landing cloud and the wall-jump tower over the void
    L.fill(84, 90, 9, 11, "#").ant(88, 8).fill(92, 92, 1, 5, "s").fill(95, 96, 3, 11, "s")
    L.coin(93, 7).coin(94, 5).coin(93, 3)
    L.fill(97, 104, 3, 4, "#").nut(101, 2)
    # crumbling cloud stairs down, then a shard-topped island
    for x, y in ((108, 5), (113, 6), (118, 7), (123, 5)):
        L.crumble(x, y, 2).coin(x, y - 1, 2)
    L.fill(128, 134, 7, 8, "#").spikes(129, 131, 6).q(132, 3, "cookie")
    # glide to the fortress
    L.coin(137, 6, 3).coin(141, 7, 3)
    L.fill(147, 177, 8, 9, "#").fill(152, 172, 3, 4, "#").drips(152, 172, 5)
    L.ant(159, 7).nut(164, 7).ant(169, 7, 1).coin(156, 7, 2).coin(166, 7, 2)
    # the gauntlet: four floats with nowhere safe to dawdle
    L.fill(181, 183, 6, 7, "#").fill(193, 194, 6, 7, "#").crumble(205, 7, 2).fill(217, 218, 8, 9, "#")
    L.fill(227, 233, 7, 8, "#").spikes(229, 231, 6).coin(186, 4, 4).coin(197, 5, 4).coin(209, 6, 4).coin(221, 7, 4)
    # last stretch: jelly, a shaft and home
    L.pillar(240, 9).jelly(240, 9).fill(246, 252, 7, 8, "#").ant(250, 6)
    L.fill(258, 258, 2, 7, "s").fill(261, 268, 3, 11, "s").coin(259, 6).coin(260, 4).fill(256, 257, 9, 11, "#")
    L.fill(276, 283, 6, 11, "#").nut(281, 5).coin(270, 4, 4)
    L.fill(284, 301, 10, 11, "#").arc(286, 7, 5)
    return L.done(goal=292)


# ============================================================ 1-9 BOSS KITCHEN (longer)
def kitchen():
    L = Lv(125, KITCHEN, "Boss Kitchen", 300, ceiling=True)
    L.arc(5, 7, 4).q(9, 6, "pizza").q(10, 6, "cookie")
    # new opening: shard-lined soup hops
    L.pit(14, 16).spikes(19, 21).pit(24, 27).crumble(25, 8, 2).pit(31, 34).plat(32, 7, 2).drips(30, 35, 2)
    L.coin(14, 7, 3).coin(24, 6, 4).coin(31, 5, 4)
    # the original approach, shifted along
    o = 34
    for a, b in ((15, 17), (26, 28), (36, 38), (44, 46), (52, 55), (60, 63)):
        L.pit(a + o, b + o)
    L.bricks(6 + o, 7, 5).q(7 + o, 7, "pizza").q(9 + o, 7, "cookie")
    L.bricks(14 + o, 8, 5).q(16 + o, 8, "cookie").bricks(30 + o, 7, 5).q(32 + o, 7, "pizza").bricks(40 + o, 8, 4)
    L.pillar(22 + o, 7, 2).pillar(48 + o, 8, 2).pillar(67 + o, 7, 2)
    L.bricks(56 + o, 7, 4).q(57 + o, 7, "pizza").bricks(64 + o, 7, 3).q(65 + o, 7, "cookie")
    for x, y, n in ((14, 6, 5), (19, 8, 3), (30, 5, 5), (40, 6, 4), (52, 6, 4), (60, 6, 4)):
        L.arc(x + o, y, n)
    for k, x, d in (("ant", 12, 1), ("nut", 20, -1), ("ant", 33, 1), ("nut", 41, 1), ("ant", 50, -1),
                    ("ant", 57, 1), ("nut", 59, -1), ("ant", 65, 1), ("nut", 70, -1)):
        if L.g[10][x + o] == "#" and L.g[9][x + o] == ".":
            (L.ant if k == "ant" else L.nut)(x + o, 9, d)
    # arena: two stone perches and the far wall
    ar0, ar1 = 73 + o, 88 + o
    L.plat(77 + o, 7, 2).plat(83 + o, 7, 2).fill(89 + o, 90 + o, 2, 9, "c").arc(76 + o, 6, 3).arc(83 + o, 6, 3)
    return L.done(goal=None, boss={"x": 83 + o, "ar0": ar0, "ar1": ar1})


def _build():
    from .levels import parse_level, serialize
    out = {}
    for i, f in ((3, honeycomb), (4, frosted), (5, fudge), (6, melon), (7, sundae), (8, kitchen)):
        L = f()
        out[i] = parse_level(serialize(L))  # same validation as any level file
    return out


LEVELS = _build()
