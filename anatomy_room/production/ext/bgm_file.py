"""外の曲（ファイル）を BGM に使う（悲劇用、2026-10-30〜）。テンプレートの外の部品で、music.bgm_techno を包む。

使い方（各話の production_script.py）：
    import bgm_file
    bgm_file.register("file_blown_away", HERE / "assets/bgm/Blown Away.mp3", bpm=170)
    "music": {"style": "file_blown_away", "sections": [(cue, off, "f_full"), (cue, off, "f_low"), ...]}

場面のモードで曲の音量を変える。曲が動画より短ければ繰り返す。
- "f_full"・"f_mid"・"f_low"・"f_mute"・"f_5"〜"f_95"：曲の音量（GAIN）
- "m70w40" の形：曲 70%・吹雪の環境音 40%（設計「悲劇」2026-10-30〜：後半で曲を無音へ、吹雪の音だけを強く残す）
- smooth：モードの切り替えをなめらかにする秒（既定 0.25。長くすると段階が連続した変化になる）
曲の権利は scripts/pilot_NNN/assets.md に記録する（無料・商用可・収益化で使えるものだけ）。吹雪の音はここで合成する（素材なし）。
"""
import re
import subprocess

import numpy as np

import music
from music import SR

FILES = {}
GAIN = {"f_full": 1.0, "f_mid": .65, "f_low": .3, "f_mute": 0.0, "ending": .35}
GAIN.update({f"f_{p}": p / 100 for p in range(5, 100, 5)})   # 段階的に下げる用（f_85・f_70 など）
RMS = 0.11        # 曲全体の音の大きさ（合成の BGM とだいたい同じ）
WIND_RMS = 0.11   # 吹雪の音（w100 のとき）の大きさ


def register(name, path, start=0.0, bpm=170, gains=None, smooth=0.25):
    """gains：この曲だけのモードの音量（例 {"ending": 0.0}：エンディングで無音のまま）"""
    FILES[name] = {"path": str(path), "start": start, "gains": gains or {}, "smooth": smooth}
    music.TECH_STYLES[name] = {"bpm": bpm, "chords": [], "seed": 0}


def _decode(path, start):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def _wind(n, seed=11):
    """吹雪の環境音：低いうなり（茶色の雑音）＋高い吹き付け、ゆっくり強弱が揺れる突風"""
    r = np.random.default_rng(seed)
    x = r.standard_normal(n)
    low = music._lp(np.cumsum(music._lp(x, 400)) * .02, 500)
    low -= music._lp(low, 30)
    hiss = music._lp(x, 3500) - music._lp(x, 900)
    t = np.arange(n) / SR
    g = r.standard_normal(int(n / SR * 2) + 4)
    gust = np.interp(t, np.arange(len(g)) / 2, g)   # 0.5 秒ごとの揺れ
    gust = music._smooth(gust, np.ones(int(1.2 * SR)) / int(1.2 * SR))
    gust = .6 + .4 * np.tanh(gust * 1.5)
    y = low / (np.sqrt(np.mean(low ** 2)) + 1e-9) * gust + .45 * hiss / (np.sqrt(np.mean(hiss ** 2)) + 1e-9) * gust ** 2
    return y * WIND_RMS / (np.sqrt(np.mean(y ** 2)) + 1e-9)


def _gains(f, m):
    """モード → (曲, 吹雪)"""
    k = re.fullmatch(r"m(\d+)w(\d+)", m or "")
    if k:
        return int(k.group(1)) / 100, int(k.group(2)) / 100
    v = f["gains"].get(m, GAIN.get(m))
    return _gains({"gains": {}}, v) if isinstance(v, str) else (v, 0.0)


def bgm_file(total, sections, style):
    f = FILES[style]
    x = _decode(f["path"], f["start"])
    x *= RMS / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    n = int(total * SR)
    if len(x) < n:
        x = np.tile(x, n // len(x) + 1)
    x = x[:n]
    g, gw = np.ones(n), np.zeros(n)
    sec = sorted(sections) + [(total + 1, None)]
    for (a, m), (b, _) in zip(sec, sec[1:]):
        i, j = max(0, int(a * SR)), min(n, int(b * SR))
        g[i:j], gw[i:j] = _gains(f, m)
    ker = np.ones(int(f["smooth"] * SR)) / int(f["smooth"] * SR)
    g, gw = music._smooth(g, ker), music._smooth(gw, ker)
    t = np.arange(n) / SR
    out = x * g + (_wind(n) * gw if gw.max() > 0 else 0)
    return out * np.clip(t / .01, 0, 1) * np.clip((total - t) / 1.5, 0, 1), {}


if not getattr(music, "_FILE_LOADED", False):
    music._FILE_LOADED = True
    _prev = music.bgm_techno

    def bgm_techno(total, sections, style="tech_air"):
        return bgm_file(total, sections, style) if style in FILES else _prev(total, sections, style)

    music.bgm_techno = bgm_techno
