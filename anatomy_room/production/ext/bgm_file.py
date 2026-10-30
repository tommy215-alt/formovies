"""外の曲（ファイル）を BGM に使う（悲劇用、2026-10-30〜）。テンプレートの外の部品で、music.bgm_techno を包む。

使い方（各話の production_script.py）：
    import bgm_file
    bgm_file.register("file_blown_away", HERE / "assets/bgm/Blown Away.mp3", bpm=170)
    "music": {"style": "file_blown_away", "sections": [(cue, off, "f_full"), (cue, off, "f_low"), ...]}

場面のモード（GAIN）で曲の音量を変える（0.25 秒でなめらかに）。曲が動画より短ければ繰り返す。
曲の権利は scripts/pilot_NNN/assets.md に記録する（無料・商用可・収益化で使えるものだけ）。
"""
import subprocess

import numpy as np

import music
from music import SR

FILES = {}
GAIN = {"f_full": 1.0, "f_mid": .65, "f_low": .3, "f_mute": 0.0, "ending": .35}
RMS = 0.11   # 曲全体の音の大きさ（合成の BGM とだいたい同じ）


def register(name, path, start=0.0, bpm=170):
    FILES[name] = {"path": str(path), "start": start}
    music.TECH_STYLES[name] = {"bpm": bpm, "chords": [], "seed": 0}


def _decode(path, start):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def bgm_file(total, sections, style):
    f = FILES[style]
    x = _decode(f["path"], f["start"])
    x *= RMS / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    n = int(total * SR)
    if len(x) < n:
        x = np.tile(x, n // len(x) + 1)
    x = x[:n]
    g = np.ones(n)
    sec = sorted(sections) + [(total + 1, None)]
    for (a, m), (b, _) in zip(sec, sec[1:]):
        g[max(0, int(a * SR)):min(n, int(b * SR))] = GAIN[m]
    g = music._smooth(g, np.ones(int(.25 * SR)) / int(.25 * SR))
    t = np.arange(n) / SR
    return x * g * np.clip(t / .01, 0, 1) * np.clip((total - t) / 1.5, 0, 1), {}


if not getattr(music, "_FILE_LOADED", False):
    music._FILE_LOADED = True
    _prev = music.bgm_techno

    def bgm_techno(total, sections, style="tech_air"):
        return bgm_file(total, sections, style) if style in FILES else _prev(total, sections, style)

    music.bgm_techno = bgm_techno
