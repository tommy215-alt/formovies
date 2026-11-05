"""長い動画（横長 1920×1080、2026-11-05〜、long_001 から）。テンプレートの外の部品で、common/ は変えない。

1. 書き出し：pipeline が呼ぶ common/render_frames.js を、横長の複製 ext/long/render_frames_long.js に差し替える
   （pipeline の subprocess を包み、引数のパスだけを置き換える）。
2. BGM：場面ごとに曲を切り替える（曲ごとに続きから鳴らし、切り替えは xfade 秒で重ねる）。
     long_ext.register_bgm("long_001", {"inv": path, "dawn": path, ...})
     "music": {"style": "long_001", "sections": [(cue, off, "inv"), (cue, off, "dawn@60"), (cue, off, "mute"), ...]}
   モードは "曲の名前" か "曲の名前@音量%"、"mute" は無音、"ending" は直前の曲を 35% で続ける。

使い方（各回の production_script.py）：
    sys.path.insert(0, str(HERE.parent / "ext" / "long"))
    import long_ext
    pipeline, standard = long_ext.setup(HERE)
"""
import subprocess as _sp
import sys
from pathlib import Path

import numpy as np

LONG = Path(__file__).resolve().parent
PROD = LONG.parent.parent
for p in (PROD / "common", PROD / "ext"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

RENDER = LONG / "render_frames_long.js"
FILES = ["../ext/long/render_frames_long.js"]   # 場面のハッシュに入れる（複製を直したら作り直す）
TRACKS = {}
RMS = 0.11


class _Sub:
    """pipeline の subprocess の代わり：common/render_frames.js を横長の複製に置き換える"""

    def __init__(self, common):
        self._old = str(common / "render_frames.js")

    def _fix(self, args):
        return [str(RENDER) if str(a) == self._old else a for a in args] if isinstance(args, (list, tuple)) else args

    def Popen(self, args, *a, **k):
        return _sp.Popen(self._fix(args), *a, **k)

    def run(self, args, *a, **k):
        return _sp.run(self._fix(args), *a, **k)

    def __getattr__(self, name):
        return getattr(_sp, name)


def _decode(path):
    raw = _sp.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x * RMS / (np.sqrt(np.mean(x ** 2)) + 1e-9)


def register_bgm(name, tracks, xfade=1.6):
    import music
    TRACKS[name] = {"tracks": {k: str(v) for k, v in tracks.items()}, "xfade": xfade}
    music.TECH_STYLES[name] = {"bpm": 90, "chords": [], "seed": 0}


def _mode(m, prev):
    if m in (None, "mute"):
        return None, 0.0
    if m == "ending":
        return prev, .35
    k, _, g = m.partition("@")
    return k, (int(g) / 100 if g else 1.0)


def bgm_long(total, sections, style):
    from music import SR
    cfg = TRACKS[style]
    n = int(total * SR)
    out = np.zeros(n)
    cache, play = {}, {}            # 曲ごとの音と、どこまで鳴らしたか
    sec = sorted(sections) + [(total, None)]
    fade = int(cfg["xfade"] * SR)
    prev = None
    for (a, m), (b, _) in zip(sec, sec[1:]):
        key, gain = _mode(m, prev)
        i, j = max(0, int(a * SR)), min(n, int(b * SR))
        if j <= i or key is None:
            prev = key or prev
            continue
        if key not in cache:
            cache[key] = _decode(cfg["tracks"][key])
        x = cache[key]
        if key != prev:
            play[key] = play.get(key, 0)
        s = play[key]
        L = min(n, j + fade) - i                  # 次の区間へ fade だけはみ出して重ねる
        idx = (s + np.arange(L)) % len(x)
        env = np.ones(L)
        if key != prev:
            env[:fade] = np.linspace(0, 1, min(fade, L))[:min(fade, L)] if L >= fade else np.linspace(0, 1, L)
        tail = L - (j - i)
        if tail > 0:
            env[-tail:] *= np.linspace(1, 0, tail)
        out[i:i + L] += x[idx] * env * gain
        play[key] = s + (j - i)
        prev = key
    t = np.arange(n) / SR
    return out * np.clip(t / .02, 0, 1) * np.clip((total - t) / 2.0, 0, 1), {}


def setup(here):
    import pipeline
    import standard
    import music
    import ending_ext
    import aivis_ext
    ending_ext.apply(pipeline)
    aivis_ext.apply(pipeline)
    if not isinstance(pipeline.subprocess, _Sub):
        pipeline.subprocess = _Sub(pipeline.COMMON)
    if not getattr(music, "_LONG_LOADED", False):
        music._LONG_LOADED = True
        prev = music.bgm_techno

        def bgm_techno(total, sections, style="tech_air"):
            return bgm_long(total, sections, style) if style in TRACKS else prev(total, sections, style)
        music.bgm_techno = bgm_techno
    return pipeline, standard
