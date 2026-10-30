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


def _horror(n, seed=5):
    """オープニング用の不安定な音（2026-10-30〜、pilot_021）：うなる低音、半音でぶつかる高い音の揺れ、音程のずれたオルゴールの音"""
    r = np.random.default_rng(seed)
    t = np.arange(n) / SR
    drone = np.sin(2 * np.pi * 55 * t) + .8 * np.sin(2 * np.pi * 58.3 * t) + .5 * np.sin(2 * np.pi * 82.4 * t + np.sin(2 * np.pi * .3 * t))
    drone += .6 * (music._lp(r.standard_normal(n), 220) * 8)
    hi = sum(np.sin(2 * np.pi * f0 * (1 + .006 * np.sin(2 * np.pi * (.4 + .13 * k) * t)) * t) for k, f0 in enumerate((740.0, 784.0, 1046.5, 1108.7))) * .25
    hi *= .5 + .5 * np.sin(2 * np.pi * .5 * t - 1.2)
    box = np.zeros(n)
    notes = (659.3, 622.3, 523.3, 493.9, 466.2, 659.3, 698.5, 392.0)   # 半音で下がって戻る、少しずつ音程がずれる
    for i, f0 in enumerate(notes):
        s = int((.18 + i * .42) * SR)
        if s >= n:
            break
        d = np.arange(min(n - s, int(1.2 * SR))) / SR
        f1 = f0 * (1 + .012 * r.standard_normal())
        box[s:s + len(d)] += (np.sin(2 * np.pi * f1 * d) + .35 * np.sin(2 * np.pi * 2.01 * f1 * d)) * np.exp(-d / .35) * np.minimum(1, d / .004)
    y = drone / (np.sqrt(np.mean(drone ** 2)) + 1e-9) * .5 + hi / (np.sqrt(np.mean(hi ** 2)) + 1e-9) * .35 + box / (np.sqrt(np.mean(box ** 2)) + 1e-9) * .6
    return y * .11 / (np.sqrt(np.mean(y ** 2)) + 1e-9)


def _gains(f, m):
    """モード → (曲, 吹雪, ホラー調の音)"""
    k = re.fullmatch(r"m(\d+)w(\d+)(?:h(\d+))?", m or "")
    if k:
        return int(k.group(1)) / 100, int(k.group(2)) / 100, int(k.group(3) or 0) / 100
    v = f["gains"].get(m, GAIN.get(m))
    return _gains({"gains": {}}, v) if isinstance(v, str) else (v, 0.0, 0.0)


def bgm_file(total, sections, style):
    """モード "mXXwYYhZZ"：h はオープニング用のホラー調の音（h が 0 でない区間は曲を止め、曲は h が終わったところから始める）"""
    f = FILES[style]
    n = int(total * SR)
    g, gw, gh = np.ones(n), np.zeros(n), np.zeros(n)
    sec = sorted(sections) + [(total + 1, None)]
    for (a, m), (b, _) in zip(sec, sec[1:]):
        i, j = max(0, int(a * SR)), min(n, int(b * SR))
        g[i:j], gw[i:j], gh[i:j] = _gains(f, m)
    hmask = gh > 0
    start = int(np.argmin(hmask)) if hmask[0] else 0   # オープニング（h の区間）が終わるところ
    x = _decode(f["path"], f["start"])
    x *= RMS / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    x = np.concatenate([np.zeros(start), x])
    if len(x) < n:
        x = np.concatenate([x, np.tile(x[start:], (n - len(x)) // max(1, len(x) - start) + 1)])
    x = x[:n]
    ker = np.ones(int(f["smooth"] * SR)) / int(f["smooth"] * SR)
    g, gw = music._smooth(g, ker), music._smooth(gw, ker)
    g[hmask] = 0.0
    if start:
        g[start:start + int(.3 * SR)] *= np.linspace(0, 1, len(g[start:start + int(.3 * SR)]))
    kh = np.ones(int(.2 * SR)) / int(.2 * SR)
    t = np.arange(n) / SR
    out = x * g + (_wind(n) * gw if gw.max() > 0 else 0) + (_horror(n) * music._smooth(gh, kh) if hmask.any() else 0)
    return out * np.clip(t / .01, 0, 1) * np.clip((total - t) / 1.5, 0, 1), {}


if not getattr(music, "_FILE_LOADED", False):
    music._FILE_LOADED = True
    _prev = music.bgm_techno

    def bgm_techno(total, sections, style="tech_air"):
        return bgm_file(total, sections, style) if style in FILES else _prev(total, sections, style)

    music.bgm_techno = bgm_techno
