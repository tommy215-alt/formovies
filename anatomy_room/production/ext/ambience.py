"""外の環境音・効果音のファイルを、効果音（sfx）として置く（当事者設計、2026-11-02〜）。テンプレートの外の部品で、music.sfx_bank_soft を包む。

使い方（各話の production_script.py。kit の回は epkit.setup のあと）：
    import ambience
    ambience.register("amb_rain", HERE / "assets/sfx/rain.mp3", dur=12, loop=True)          # 雨の環境音を 12 秒（短ければ繰り返す）
    ambience.register("hit_thunder", HERE / "assets/sfx/thunder.mp3", start=1.2, dur=4, norm="peak")
    "sfx": [["amb_rain", "l05", 1.0, 0.0], ...]   # （名前, きっかけ, 音量, ずらす秒）。置き方は従来の効果音と同じ
- span=("l01", "l04", 0.3)：l01 から l04 の 0.3 秒後までの長さにする（work/timeline.json の cue から。音を置く cue は sfx 側で l01 にする）。
  timeline(HERE / "work" / "timeline.json") を先に呼ぶ。音声の工程（audio）は声の工程のあとなので、そのときには timeline がある。
- norm="rms"（既定）：環境音の大きさをそろえる（RMS 0.1）。"peak"：一発の音（最大 0.9）。
- 音はすべて PD・CC0・CC BY だけ（scripts/pilot_NNN/assets.md に、ページの URL とライセンスを書く）。
- 元のファイルは assets/sfx/（make_assets と同じく、src は git に入れてよい大きさに切ってから置く）。
"""
import subprocess

import numpy as np

import music
from music import SR

import json

FILES = {}
TL = {"path": None}


def timeline(path):
    TL["path"] = str(path)


def register(name, path, start=0.0, dur=None, gain=1.0, fade_in=.05, fade_out=.4, loop=False, norm="rms", span=None):
    FILES[name] = dict(path=str(path), start=start, dur=dur, gain=gain, fade_in=fade_in, fade_out=fade_out, loop=loop, norm=norm, span=span)


SYN = {}


def click(name, pitch=2600, gain=1.0, double=False):
    """選択肢を示すときの無機質なクリック音（合成。2026-11-02 ユーザーの指示「もっとクリック音ぽい無機質な感じ」）"""
    SYN[name] = dict(pitch=pitch, gain=gain, double=double)


def _click(c):
    n = int(.12 * SR); t = np.arange(n) / SR; r = np.random.default_rng(7)
    noise = r.standard_normal(n); noise = noise - music._lp(noise, 2500)
    x = noise * np.exp(-t / .0018) + .55 * np.sin(2 * np.pi * c["pitch"] * t) * np.exp(-t / .010) + .25 * np.sin(2 * np.pi * c["pitch"] * 2.01 * t) * np.exp(-t / .005)
    if c["double"]:
        k = int(.055 * SR); x[k:] += .7 * x[:n - k]
    return x * .9 / (np.max(np.abs(x)) + 1e-9) * c["gain"]


def _span(f):
    a, b, tail = (*f["span"], 0.0)[:3]
    cues = json.load(open(TL["path"], encoding="utf-8"))["cues"]
    cues = {**cues, "end": json.load(open(TL["path"], encoding="utf-8"))["ending_start"]}
    return max(.2, cues[b] - cues[a] + tail)


def _load(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(f["start"]), "-i", f["path"], "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    dur = _span(f) if f["span"] else f["dur"]
    if dur:
        n = int(dur * SR)
        if len(x) < n:
            x = np.tile(x, n // max(1, len(x)) + 1)
        x = x[:n]
    x = x * (.1 / (np.sqrt(np.mean(x ** 2)) + 1e-9) if f["norm"] == "rms" else .9 / (np.max(np.abs(x)) + 1e-9))
    a, b = int(f["fade_in"] * SR), int(f["fade_out"] * SR)
    if a:
        x[:a] *= np.linspace(0, 1, min(a, len(x)))
    if b and len(x) > b:
        x[-b:] *= np.linspace(1, 0, b)
    return x * f["gain"]


if not getattr(music, "_AMB_LOADED", False):
    music._AMB_LOADED = True
    _prev = music.sfx_bank_soft

    def sfx_bank_soft():
        b = _prev()
        b.update({k: _load(f) for k, f in FILES.items()})
        b.update({k: _click(c) for k, c in SYN.items()})
        return b

    music.sfx_bank_soft = sfx_bank_soft
