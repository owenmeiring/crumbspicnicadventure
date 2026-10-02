"""Custom level format, validation and storage.

The JSON format is the same one the original HTML level builder exported, so
levels made there import here unchanged. Levels live as plain .json files in
%APPDATA%\\CrumbsPicnicRun\\levels, one per level, easy to share.
"""

import json
import os
import re
from pathlib import Path

EH = 12
CHM = {".": 0, "#": 1, "b": 2, "?": 3, "s": 5, "c": 6, "k": 8, "j": 9, "x": 10, "v": 11}
THEMES = ["Picnic Lawn", "Cellar Pantry", "Boss Kitchen", "Honeycomb Hollow", "Frosted Peaks", "Fudge Mines",
          "Melon Grove", "Sundae Skies"]
DATA_DIR = Path(os.environ.get("APPDATA") or Path.home()) / "CrumbsPicnicRun"
LEVEL_DIR = DATA_DIR / "levels"
DRAFT = DATA_DIR / "draft.json"


class LevelError(ValueError):
    pass


def new_level(theme=0, w=80):
    g = [["."] * w for _ in range(EH)]
    for x in range(w):
        g[10][x] = g[11][x] = "#"
        if theme > 0:
            g[0][x] = g[1][x] = "c"
    return {"name": "My Level", "theme": theme, "time": 250, "w": w, "start": [2, 9], "goal": w - 4, "g": g,
            "contents": {}, "coins": [], "enemies": [], "boss": None}


def serialize(L):
    return {"crumb": 1, "name": L["name"], "theme": L["theme"], "time": L["time"], "w": L["w"],
            "start": list(L["start"]), "goal": L["goal"], "grid": ["".join(r) for r in L["g"]],
            "contents": {f"{x},{y}": v for (x, y), v in L["contents"].items()},
            "coins": [list(c) for c in L["coins"]],
            "enemies": [[q["k"], q["x"], q["y"], q["d"]] for q in L["enemies"]],
            "boss": dict(L["boss"]) if L["boss"] else None}


def _n(v, a, b, d):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return d
    if v != v or v in (float("inf"), float("-inf")):
        return d
    return max(a, min(b, round(v)))


def parse_level(src):
    o = json.loads(src) if isinstance(src, str) else src
    if not isinstance(o, dict) or not isinstance(o.get("grid"), list) or len(o["grid"]) != EH:
        raise LevelError(f'"grid" must be a list of {EH} rows')
    w = len(o["grid"][0] or "")
    if not 24 <= w <= 400:
        raise LevelError("level width must be 24 to 400 columns")
    g = []
    for r in o["grid"]:
        if not isinstance(r, str) or len(r) != w:
            raise LevelError("all grid rows must be the same length")
        for ch in r:
            if ch not in CHM:
                raise LevelError(f'unknown tile "{ch}"')
        g.append(list(r))
    st = o.get("start") or [2, 9]
    L = {"name": str(o.get("name") or "Custom Level")[:24], "theme": _n(o.get("theme"), 0, len(THEMES) - 1, 0),
         "time": _n(o.get("time"), 30, 999, 250), "w": w, "g": g,
         "start": [_n(st[0], 0, w - 1, 2), _n(st[1], 0, EH - 1, 9)],
         "goal": None if o.get("goal") is None else _n(o["goal"], 0, w - 1, w - 4),
         "contents": {}, "coins": [], "enemies": [], "boss": None}
    for k, v in (o.get("contents") or {}).items():
        m = re.fullmatch(r"(\d+),(\d+)", k) if isinstance(k, str) else None
        x, y = (int(m[1]), int(m[2])) if m else (k if isinstance(k, tuple) else (-1, -1))
        if v in ("pizza", "cookie") and 0 <= y < EH and 0 <= x < w and g[y][x] == "?":
            L["contents"][(x, y)] = v
    seen = set()
    for c in o.get("coins") or []:
        if not isinstance(c, (list, tuple)) or len(c) < 2:
            continue
        x, y = _n(c[0], 0, w - 1, -1), _n(c[1], 0, EH - 1, -1)
        if x >= 0 and y >= 0 and (x, y) not in seen:
            seen.add((x, y))
            L["coins"].append([x, y])
    for q in o.get("enemies") or []:
        if not isinstance(q, (list, tuple)) or len(q) < 4 or q[0] not in ("ant", "nut"):
            continue
        L["enemies"].append({"k": q[0], "x": _n(q[1], 0, w - 1, 0), "y": _n(q[2], 0, EH - 2, 9),
                             "d": -1 if _n(q[3], -1, 1, 1) < 0 else 1})
    b = o.get("boss")
    if isinstance(b, dict):
        bx = _n(b.get("x"), 0, w - 3, w - 10)
        L["boss"] = {"x": bx, "ar0": _n(b.get("ar0"), 0, w - 1, max(0, bx - 10)),
                     "ar1": _n(b.get("ar1"), 0, w - 1, min(w - 1, bx + 5))}
    return L


def find_ledges(L):
    r, out = L["g"][7], []
    x = L["boss"]["ar0"]
    while x <= L["boss"]["ar1"] and x < L["w"]:
        if r[x] == "s":
            a = x
            while x + 1 < L["w"] and r[x + 1] == "s":
                x += 1
            out.append([a, x + 1])
        x += 1
    return out[:2] if len(out) >= 2 else []


# ---------------------------------------------------------------- files
def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "level"


def list_levels():
    """[(path, parsed level)] for every valid level file, newest first."""
    out = []
    if LEVEL_DIR.exists():
        for p in sorted(LEVEL_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                out.append((p, parse_level(p.read_text("utf-8"))))
            except (OSError, ValueError):
                pass
    return out


def save_level(L, path=None):
    LEVEL_DIR.mkdir(parents=True, exist_ok=True)
    path = path or LEVEL_DIR / f"{slug(L['name'])}.json"
    path.write_text(json.dumps(serialize(L), indent=1), "utf-8")
    return path


def delete_level(path):
    try:
        Path(path).unlink()
    except OSError:
        pass


def save_draft(L):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DRAFT.write_text(json.dumps(serialize(L)), "utf-8")
    except OSError:
        pass


def load_draft():
    try:
        return parse_level(DRAFT.read_text("utf-8"))
    except (OSError, ValueError):
        return None
