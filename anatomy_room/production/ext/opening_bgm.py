"""冒頭のオープニング（約 3 秒）の音（2026-10-30〜）。テンプレートの外の部品で、music.bgm_techno を包む。

BGM の場面のモードに "open_soft"（やさしい音）を書くと、その区間は本編の曲を止めて、ここで合成した音を流す。本編の曲はその区間が終わったところから入る。
    "music": {"style": "lab_melodic", "sections": [("t0", 0.0, "open_soft"), ("hook", -0.05, "w_hook"), ...]}
曲の合成（lab_* など）には "open_soft" の区間を "w_hold" として渡す。悲劇のホラー調の音は bgm_file.py のモード h（曲のファイルを使う回）。
"""
import numpy as np

import music
from music import SR


def _soft(n, seed=3):
    """やさしい音：あたたかい和音の帯（長七の和音、ゆっくり立ち上がる）＋ゆっくりのオルゴール＋かすかな空気"""
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    pad = sum(np.sin(2 * np.pi * f * t + .3 * np.sin(2 * np.pi * .2 * t + k)) for k, f in enumerate((130.8, 164.8, 196.0, 246.9, 329.6)))
    pad *= np.minimum(1, t / .8)
    box = np.zeros(n)
    for i, f0 in enumerate((523.3, 659.3, 784.0, 987.8, 784.0, 1046.5)):
        s = int((.25 + i * .5) * SR)
        if s >= n:
            break
        d = np.arange(min(n - s, int(1.8 * SR))) / SR
        box[s:s + len(d)] += (np.sin(2 * np.pi * f0 * d) + .3 * np.sin(2 * np.pi * 2 * f0 * d)) * np.exp(-d / .7) * np.minimum(1, d / .006)
    air = music._lp(r.standard_normal(n), 3000) - music._lp(r.standard_normal(n), 800)
    nm = lambda x: x / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    y = nm(pad) * .6 + nm(box) * .5 + nm(air) * .05
    return y * .1 / (np.sqrt(np.mean(y ** 2)) + 1e-9)


if not getattr(music, "_OPEN_LOADED", False):
    music._OPEN_LOADED = True
    _prev = music.bgm_techno

    def bgm_techno(total, sections, style="tech_air"):
        sec = sorted(sections)
        idx = [i for i, (a, m) in enumerate(sec) if m == "open_soft"]
        if not idx:
            return _prev(total, sections, style)
        i = idx[0]
        a0, a1 = sec[i][0], (sec[i + 1][0] if i + 1 < len(sec) else total)
        out, info = _prev(total, [(a, "w_hold" if m == "open_soft" else m) for a, m in sec], style)
        out = np.array(out, dtype=float)
        n, s0, s1, f = len(out), int(a0 * SR), int(a1 * SR), int(.3 * SR)
        out[:s1] = 0.0
        out[s1:s1 + f] *= np.linspace(0, 1, len(out[s1:s1 + f]))   # 本編の曲は 0.3 秒で入る
        env = np.zeros(n)
        env[s0:s1] = 1.0
        env[s1:s1 + f] = np.linspace(1, 0, len(env[s1:s1 + f]))   # やさしい音は 0.3 秒で消える
        return out + _soft(n) * env, info

    music.bgm_techno = bgm_techno
