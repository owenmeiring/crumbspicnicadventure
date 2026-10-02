"""Procedural lo-fi 8-bit music and sound effects.

A port of the original WebAudio step sequencer. A worker thread renders the
music a fraction of a second ahead into a ring buffer; the audio callback
plays it and mixes sound effects on top with low latency. The music clock is
exposed so walnuts can dance exactly on the beat.
"""

import math
import random
import threading
from collections import deque

import numpy as np

try:
    import sounddevice as sd
except Exception:  # no PortAudio on this machine
    sd = None

SR = 44100
TBL = 2048
_rng = np.random.default_rng()
NOISE = (_rng.random(SR * 2) * 2 - 1).astype(np.float32)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- wavetables
_tables = {}


def _table(kind, nh):
    key = (kind, nh)
    t = _tables.get(key)
    if t is not None:
        return t
    ph = np.arange(TBL) / TBL * 2 * np.pi
    w = np.zeros(TBL)
    if kind == "sine":
        w = np.sin(ph)
    elif kind == "square":
        for n in range(1, nh + 1, 2):
            w += np.sin(n * ph) / n
    elif kind == "sawtooth":
        for n in range(1, nh + 1):
            w += (-1) ** (n + 1) * np.sin(n * ph) / n
    elif kind == "triangle":
        for n in range(1, nh + 1, 2):
            w += (-1) ** ((n - 1) // 2) * np.sin(n * ph) / (n * n)
    else:  # pulse with duty cycle, same coefficients as createPeriodicWave
        d = kind
        for n in range(1, min(nh, 40) + 1):
            re = math.sin(2 * math.pi * n * d) / (n * math.pi)
            im = (1 - math.cos(2 * math.pi * n * d)) / (n * math.pi)
            w += re * np.cos(n * ph) + im * np.sin(n * ph)
    w = (w / max(1e-9, np.max(np.abs(w)))).astype(np.float32)
    _tables[key] = w
    return w


def _osc(kind, freq, n):
    """freq is a float or a per-sample array."""
    if np.isscalar(freq):
        fmax = freq
        phase = (freq / SR) * np.arange(n)
    else:
        fmax = float(np.max(freq))
        phase = np.cumsum(freq) / SR
    nh = max(1, min(64, int(SR / 2 / max(fmax, 1.0))))
    tbl = _table(kind, nh)
    idx = ((phase % 1.0) * TBL).astype(np.int32) & (TBL - 1)
    return tbl[idx]


_firs = {}


def _lowpass_kernel(fc, taps=63):
    fc = float(min(max(fc, 20.0), SR / 2 - 100))
    key = (round(fc), taps)
    h = _firs.get(key)
    if h is None:
        m = np.arange(taps) - (taps - 1) / 2
        h = np.sinc(2 * fc / SR * m) * np.hamming(taps)
        h = (h / h.sum()).astype(np.float32)
        _firs[key] = h
    return h


def lowpass(x, fc):
    return np.convolve(x, _lowpass_kernel(fc))[: len(x)]


def highpass(x, fc):
    h = _lowpass_kernel(fc)
    lp = np.convolve(x, h)[: len(x)]
    d = len(h) // 2
    xd = np.concatenate([np.zeros(d, np.float32), x[: len(x) - d]])
    return xd - lp


def bandpass(x, fc, q):
    bw = fc / max(q, 0.1)
    hi = lowpass(x, fc + bw / 2)
    lo = lowpass(x, max(20.0, fc - bw / 2))
    return hi - lo


def _exp_env(n, v, target, dur):
    t = np.arange(n) / SR
    k = np.minimum(t / max(dur, 1e-4), 1.0)
    return (v * (target / v) ** k).astype(np.float32)


class FIRStream:
    def __init__(self, fc):
        self.h = _lowpass_kernel(fc)
        self.prev = np.zeros(len(self.h) - 1, np.float32)

    def __call__(self, x):
        xx = np.concatenate([self.prev, x])
        self.prev = xx[-(len(self.h) - 1):]
        return np.convolve(xx, self.h, "valid").astype(np.float32)


# ---------------------------------------------------------------- one-shot sfx
_sfx_cache = {}


def make_sfx(a, b, d, ty, v):
    key = (round(a), round(b or 0), round(d, 3), ty, round(v, 3))
    s = _sfx_cache.get(key)
    if s is not None:
        return s
    n = max(1, int(d * SR))
    t = np.arange(n) / SR
    f = np.where(t < d * 0.3, a, b) if b else np.full(n, float(a))
    sig = _osc(ty, f.astype(np.float64), n)
    s = (sig * _exp_env(n, v, 0.001, d)).astype(np.float32)
    _sfx_cache[key] = s
    return s


# ---------------------------------------------------------------- music
CH = [
    [[48, [0, 4, 7, 11]], [45, [0, 3, 7, 10]], [50, [0, 3, 7, 10]], [43, [0, 4, 7, 10]]],
    [[45, [0, 3, 7, 10, 14]], [41, [0, 4, 7, 11]], [50, [0, 3, 7, 10]], [40, [0, 4, 7, 10]]],
    [[50, [0, 3, 7, 10]], [46, [0, 4, 7, 11]], [43, [0, 3, 7, 10]], [45, [0, 4, 7, 10]]],
]
LEAD = [
    [[[2, 76, 3], [6, 79, 2], [8, 81, 4], [13, 79, 2]], [[0, 76, 3], [4, 72, 2], [8, 74, 3], [12, 72, 3]],
     [[2, 74, 3], [6, 77, 2], [8, 76, 4], [14, 74, 2]], [[0, 74, 4], [6, 71, 2], [8, 74, 2], [10, 79, 5]]],
    [[[2, 76, 4], [8, 72, 3], [12, 71, 3]], [[0, 72, 4], [6, 77, 3], [10, 76, 3]],
     [[2, 74, 3], [6, 72, 2], [8, 69, 5]], [[0, 71, 3], [4, 76, 3], [8, 80, 4], [13, 76, 2]]],
]
BOSS_CH = [[45, [0, 3, 7, 12]], [46, [0, 4, 7, 12]], [45, [0, 3, 7, 12]], [44, [0, 3, 6, 9]]]
BOSS_LEAD = [
    [[0, 69, 2], [2, 72, 2], [3, 71, 1], [4, 69, 2], [6, 68, 2], [8, 69, 2], [10, 72, 2], [12, 75, 3], [15, 74, 1]],
    [[0, 70, 2], [2, 73, 2], [4, 74, 2], [6, 70, 2], [8, 73, 3], [11, 70, 1], [12, 69, 3], [15, 68, 1]],
    [[0, 69, 2], [2, 72, 2], [4, 76, 2], [6, 75, 2], [8, 74, 2], [10, 72, 2], [12, 71, 2], [14, 68, 2]],
    [[0, 68, 2], [2, 71, 2], [4, 74, 2], [6, 77, 2], [8, 76, 4], [12, 75, 2], [14, 71, 2]],
]
BOSSBPM = 140
P25, P125 = 0.25, 0.125


class MusicClock:
    """Shared between the game and the sequencer (the original's MG object)."""

    def __init__(self):
        self.bpm = 84
        self.sp = 60 / 84 / 4
        self.beat2 = self.sp * 8
        self.t0 = 0.0
        self.dances = []
        self.intro_pend = False
        self.mood_now = lambda: 0


class Sequencer:
    BUF = SR * 12

    def __init__(self, clock):
        self.G = clock
        self.step = 0
        self.mood = 0
        self.intro_step = 32
        self.next_t = 0.2
        clock.t0 = 0.2
        self.base = 0
        self.buf = np.zeros(self.BUF, np.float32)
        self.ebuf = np.zeros(self.BUF, np.float32)
        self.dhist = np.zeros(SR * 4, np.float32)
        self.dpos = 0
        self.echo_lp = FIRStream(2200)
        self.master_lp = FIRStream(5200)
        self.muted = lambda: False

    # ---- scheduling helpers
    def _add(self, t, sig, echo=False):
        i0 = int(round(t * SR)) - self.base
        if i0 < 0:
            sig = sig[-i0:]
            i0 = 0
        i1 = min(self.BUF, i0 + len(sig))
        if i1 <= i0:
            return
        self.buf[i0:i1] += sig[: i1 - i0]
        if echo:
            self.ebuf[i0:i1] += sig[: i1 - i0]

    def tone(self, t, m, dur, wave="triangle", v=0.1, a=0.006, det=0, lp=None, dist=None, echo=False):
        f = hz(m) * 2 ** (det / 1200)
        n = int((dur + 0.05) * SR)
        sig = _osc(wave, f, n)
        if lp:
            sig = lowpass(sig, lp)
        if dist:
            sig = 0.6 * np.tanh(np.clip(sig * dist, -1, 1) * 7)
        tt = np.arange(n) / SR
        if dur > a:
            env = np.where(tt < a, v * tt / a, v * (0.0001 / v) ** np.minimum((tt - a) / (dur - a), 1.0))
        else:
            env = v * np.minimum(tt / a, 1.0)
        self._add(t, (sig * env).astype(np.float32), echo)

    def nz(self, t, dur, v, kind, f0, q=0.7, f1=None):
        n = int((dur + 0.02) * SR)
        start = random.randint(0, SR // 2)
        src = NOISE[start:start + n]
        if len(src) < n:
            src = np.resize(NOISE, n)

        def filt(x, f):
            return highpass(x, f) if kind == "highpass" else bandpass(x, f, q)

        if f1:
            segs = 8
            out = np.empty(n, np.float32)
            edges = np.linspace(0, n, segs + 1).astype(int)
            for i in range(segs):
                f = f0 * (f1 / f0) ** ((i + 0.5) / segs)
                out[edges[i]:edges[i + 1]] = filt(src, f)[edges[i]:edges[i + 1]]
            sig = out
        else:
            sig = filt(src, f0)
        self._add(t, (sig * _exp_env(n, v, 0.0001, dur)).astype(np.float32))

    def kick(self, t, v):
        n = int(0.32 * SR)
        tt = np.arange(n) / SR
        f = 150 * (42 / 150) ** np.minimum(tt / 0.12, 1.0)
        self._add(t, (_osc("sine", f, n) * _exp_env(n, v, 0.001, 0.3)).astype(np.float32))

    def tom(self, t, f0, v):
        n = int(0.26 * SR)
        tt = np.arange(n) / SR
        f = f0 * 0.5 ** np.minimum(tt / 0.16, 1.0)
        self._add(t, (_osc("sine", f, n) * _exp_env(n, v, 0.001, 0.24)).astype(np.float32))

    def wood(self, t):
        n = int(0.08 * SR)
        tt = np.arange(n) / SR
        f = 1650 * (1050 / 1650) ** np.minimum(tt / 0.04, 1.0)
        self._add(t, (_osc("square", f, n) * _exp_env(n, 0.09, 0.0001, 0.06)).astype(np.float32))

    def snare(self, t, v):
        self.nz(t, 0.17, 0.34 * v, "bandpass", 1900, 0.9)
        self.tone(t, 55, 0.09, "triangle", 0.24 * v, a=0.002)

    def hat(self, t, v, open_=False):
        self.nz(t, 0.16 if open_ else 0.045, 0.075 * v, "highpass", 7500, 0.7)

    def dance_idx(self, t):
        sp = self.G.sp
        for x in self.G.dances:
            d = (t - x) / sp
            if -0.02 < d < 7.98:
                return max(0, min(7, round(d)))
        return -1

    def set_tempo(self, bpm):
        G = self.G
        if bpm == G.bpm:
            return
        G.bpm = bpm
        G.sp = 60 / bpm / 4
        G.beat2 = G.sp * 8
        G.t0 = self.next_t
        G.dances = []

    # ---- the song
    def sched_step(self, step, t):
        G = self.G
        sp = G.sp
        sb, bar = step % 16, (step // 16) % 4
        if sb == 0:
            self.mood = G.mood_now()
        if self.muted():
            return
        mood = self.mood or 0
        root, iv = CH[mood][bar]
        tt = t + sp * 0.2 if sb % 2 else t
        dj = self.dance_idx(t)
        R = random.random
        if mood == 2:
            br, bi = BOSS_CH[bar]
            if sb in (0, 3, 6, 8, 10, 11, 14):
                self.kick(t, 1 if sb == 0 else 0.85)
            if sb in (4, 12):
                self.snare(t, 1)
            if bar == 3 and sb >= 13:
                self.snare(t, 0.55 + (sb - 13) * 0.15)
            elif bar % 2 and sb == 15:
                self.snare(t, 0.4)
            self.hat(t, 1.2 if sb % 4 == 0 else (0.55 if sb % 2 else 0.9), sb in (6, 14))
            if sb == 0 and bar == 0:
                self.nz(t, 0.8, 0.16, "highpass", 5000, 0.6)
            if sb % 2 == 0 or sb in (7, 15):
                n = br - 12 + (12 if sb % 8 == 6 else 0) + (1 if sb == 14 and bar == 3 else 0)
                self.tone(t, n, sp * (0.9 if sb % 2 else 1.7), P25, 0.13, lp=900, a=0.003, dist=5)
                self.tone(t, n - 12, sp * 1.8, "triangle", 0.36, lp=420, a=0.005)
            if sb in (6, 14, 3) or (sb == 11 and bar % 2):
                for i, n in enumerate(bi):
                    self.tone(t, br + 12 + n, sp * 1.2, P125, 0.04, lp=3000, a=0.003, det=i * 4 - 6, dist=2.5)
            if sb == 0:
                self.tone(t, br - 24, sp * 15.5, "sawtooth", 0.04, lp=300, a=0.25, det=-9, dist=2)
            if sb == 0 and bar == 3:
                self.tone(t, br + 6, sp * 15, "triangle", 0.035, a=0.4, det=8)
            if dj < 0:
                for l in BOSS_LEAD[bar]:
                    if l[0] == sb:
                        self.tone(t, l[1], sp * l[2] * 0.85, P125, 0.075, lp=3600, echo=True, a=0.004,
                                  det=0 if sb % 4 else 7, dist=1.6)
                        self.tone(t, l[1] - 12, sp * l[2] * 0.8, P25, 0.045, lp=1800, a=0.004, det=14, dist=3)
            else:
                self._dance(t, tt, dj, br, bi)
            return
        kicks = (0, 7, 10) if bar % 2 else (0, 6, 10)
        if sb in kicks:
            self.kick(tt, 0.95 if sb == 0 else 0.72)
        if sb in (4, 12):
            self.snare(tt, 0.5)
        if sb % 2 == 0:
            self.hat(tt, 1 if sb % 4 == 0 else 0.6, sb == 14 and bar % 2 == 1)
        elif R() < 0.25:
            self.hat(tt, 0.35)
        if R() < 0.22:
            self.nz(tt, 0.012, 0.035, "highpass", 3500, 0.5)
        if sb in (0, 7, 10):
            self.tone(tt, root - 12 + (7 if sb in (10, 11) else 0), sp * 4.2, "triangle", 0.5, lp=800, a=0.008)
        if sb in (2, 10):
            for i, n in enumerate(iv[:4]):
                self.tone(tt, root + 12 + n, sp * 2.2, P25, 0.04, lp=1800, a=0.004, det=i * 3 - 4)
        if sb == 0:
            for i, n in enumerate(iv[:4]):
                self.tone(t, root + 12 + n, sp * 15, "triangle", 0.026, a=0.22, det=i * 5 - 7)
        if dj < 0:
            for l in LEAD[mood][bar]:
                if l[0] == sb and R() < 0.92:
                    self.tone(tt, l[1], sp * l[2] * 0.9, P125, 0.08, lp=3200, echo=True, a=0.01)
        else:
            self._dance(t, tt, dj, root, iv)

    def _dance(self, t, tt, dj, root, iv):
        sp = self.G.sp
        if dj % 2 == 0:
            self.wood(t)
            deg = [1, 2, 3, 2][dj // 2]
            n = root + 24 + iv[min(deg, len(iv) - 1)]
            self.tone(t, n, sp * 1.7, P125, 0.11, lp=4600, echo=True, a=0.004)
            self.tone(t, n + 12, sp * 1.1, "sine", 0.06, a=0.003, echo=True)
        if dj in (2, 6):
            self.nz(t, 0.06, 0.17, "bandpass", 1500, 1.2)
        if dj == 6:
            self.nz(t, sp * 2.1, 0.12, "bandpass", 500, 2.4, 5200)
        if dj == 7:
            self.tone(tt, root + 36 + iv[2], sp * 0.9, P125, 0.07, lp=4800, echo=True)

    def intro(self, i, t):
        if self.muted():
            return
        sp = self.G.sp
        bar, sb, u = i >> 4, i & 15, i / 32
        if bar == 0:
            if sb in (0, 8):
                self.tom(t, 95, 0.7)
            if sb in (3, 11):
                self.tom(t, 80, 0.5)
            if sb % 4 == 0:
                self.wood(t)
            if sb == 0:
                self.tone(t, 21, sp * 30, "sawtooth", 0.05, lp=200, a=1.6, dist=2)
                self.tone(t, 27, sp * 30, "triangle", 0.05, a=2, det=12)
            if sb % 2 == 0 and sb >= 8:
                self.snare(t, 0.12 + sb * 0.008)
        else:
            v = 0.2 + u * 0.9 - 0.25
            if sb in (0, 3, 6):
                self.tom(t, 110 - sb * 4, 0.85)
            if sb >= 8 or sb % 2 == 0:
                self.snare(t, v * (1.15 if sb >= 12 else 0.9))
            if sb % 4 == 0:
                self.kick(t, 0.9)
            if sb == 0:
                self.nz(t, sp * 15, 0.16, "bandpass", 300, 2.2, 7000)
            if sb in (8, 10, 12, 14):
                self.tom(t, 150 - (sb - 8) * 8, 0.7)
            if sb >= 12:
                self.tone(t, 57 + sb, sp * 0.9, P125, 0.05, lp=3000, a=0.002, dist=2)

    def run(self, until):
        G = self.G
        while self.next_t < until:
            if G.intro_pend:
                G.intro_pend = False
                self.step = math.ceil(self.step / 16) * 16
                self.set_tempo(BOSSBPM)
                self.intro_step = 0
            if self.intro_step < 32:
                self.intro(self.intro_step, self.next_t)
                if self.intro_step == 15:
                    G.dances = []
                self.intro_step += 1
                self.next_t += G.sp
                continue
            if self.step % 16 == 0:
                self.set_tempo(BOSSBPM if G.mood_now() == 2 else 84)
            self.sched_step(self.step, self.next_t)
            self.step += 1
            self.next_t += G.sp

    def render(self, n, gain):
        self.run((self.base + n) / SR)
        main = self.buf[:n].copy()
        send = self.ebuf[:n].copy()
        self.buf[:-n] = self.buf[n:]
        self.buf[-n:] = 0
        self.ebuf[:-n] = self.ebuf[n:]
        self.ebuf[-n:] = 0
        self.base += n
        # feedback echo: delay of three steps, low-passed, fed back at .33
        D = int(self.G.sp * 3 * SR)
        L = len(self.dhist)
        idx = (self.dpos - D + np.arange(n)) % L
        dout = self.echo_lp(self.dhist[idx])
        din = send + 0.33 * dout
        widx = (self.dpos + np.arange(n)) % L
        self.dhist[widx] = din
        self.dpos = (self.dpos + n) % L
        mix = self.master_lp((main + 0.5 * dout) * gain)
        th = 0.158
        a = np.abs(mix)
        over = a > th
        mix[over] = np.sign(mix[over]) * (th + (a[over] - th) / 3)
        return mix


class Audio:
    RING = 1 << 16

    def __init__(self):
        self.clock = MusicClock()
        self.seq = Sequencer(self.clock)
        self.sfx_on = True
        self.music_on = True
        self.ring = np.zeros(self.RING, np.float32)
        self.w = 0
        self.r = 0
        self.voices = []
        self.new_voices = deque()
        self.latency = 0.0
        self.ok = False
        self._run = True
        self.stream = None
        if sd is None:
            return
        try:
            self.stream = sd.OutputStream(samplerate=SR, channels=2, dtype="float32",
                                          callback=self._callback, latency="low")
            self.stream.start()
            lat = self.stream.latency
            self.latency = float(lat[1] if isinstance(lat, (tuple, list)) else lat)
            self.ok = True
        except Exception:
            self.stream = None
            return
        self.worker = threading.Thread(target=self._work, daemon=True)
        self.worker.start()

    # ---- threads
    def _work(self):
        target = int(0.12 * SR)
        chunk = 1024
        while self._run:
            if self.w - self.r < target:
                gain = 0.24 if self.music_on else 0.0
                block = self.seq.render(chunk, gain)
                i = self.w % self.RING
                j = i + chunk
                if j <= self.RING:
                    self.ring[i:j] = block
                else:
                    k = self.RING - i
                    self.ring[i:] = block[:k]
                    self.ring[: chunk - k] = block[k:]
                self.w += chunk
            else:
                threading.Event().wait(0.004)

    def _callback(self, outdata, frames, _time, _status):
        avail = self.w - self.r
        take = min(frames, avail)
        out = np.zeros(frames, np.float32)
        if take > 0:
            i = self.r % self.RING
            j = i + take
            if j <= self.RING:
                out[:take] = self.ring[i:j]
            else:
                k = self.RING - i
                out[:k] = self.ring[i:]
                out[k:take] = self.ring[: take - k]
            self.r += take
        while self.new_voices:
            self.voices.append(self.new_voices.popleft())
        keep = []
        for v in self.voices:
            arr, pos = v
            if pos < 0:
                off = -pos
                if off < frames:
                    seg = arr[: frames - off]
                    out[off:off + len(seg)] += seg
            else:
                seg = arr[pos:pos + frames]
                out[: len(seg)] += seg
            if pos + frames < len(arr):
                v[1] = pos + frames
                keep.append(v)
        self.voices = keep
        np.clip(out, -1, 1, out=out)
        outdata[:, 0] = out
        outdata[:, 1] = out

    # ---- game-facing API
    def mtime(self):
        return self.r / SR - self.latency

    def snd(self, a, b, d, ty, v, delay=0.0):
        if not (self.ok and self.sfx_on):
            return
        self.new_voices.append([make_sfx(a, b, d, ty, v), -int(delay * SR)])

    def close(self):
        self._run = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
