"""冒頭のオープニング（約 3 秒）の音（2026-10-30〜）。テンプレートの外の部品で、music.bgm_techno を包む。

BGM の場面のモードに "open_soft"（やさしい音）か "open_eerie"（ゆっくり、少し不気味で気を引く音）を書くと、その区間は本編の曲を止めて、ここで合成した音を流す。本編の曲はその区間が終わったところから入る。
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


def _eerie(n, seed=7):
    """少し不気味で気を引く音（2026-10-30、ユーザー「ゆっくりなのはいいが、少し不気味な感じで気を引いて」）：
    短調の低い持続音（半音でかすかにぶつかる）＋ゆっくりの鼓動＋音程がわずかに揺れるオルゴール（短調で下がる）＋終わりに逆回しのふくらみ"""
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    drone = sum(a * np.sin(2 * np.pi * f * t + .4 * np.sin(2 * np.pi * .15 * t + k)) for k, (f, a) in enumerate(((110.0, 1), (130.8, .7), (164.8, .5), (116.5, .25))))
    drone *= np.minimum(1, t / 1.0)
    beat = np.zeros(n)
    for s in np.arange(.35, n / SR, 1.05):   # ゆっくりの鼓動（約 57 BPM、2 打で 1 組）
        for off, a in ((0, 1), (.22, .6)):
            i = int((s + off) * SR)
            d = np.arange(min(n - i, int(.4 * SR))) / SR
            if i < n:
                beat[i:i + len(d)] += a * np.sin(2 * np.pi * (55 + 30 * np.exp(-d / .03)) * d) * np.exp(-d / .12)
    box = np.zeros(n)
    for i, f0 in enumerate((880.0, 830.6, 659.3, 622.3, 523.3)):   # ラ・ソ♯・ミ・レ♯・ド（短調で下がる）
        s = int((.3 + i * .55) * SR)
        if s >= n:
            break
        d = np.arange(min(n - s, int(1.6 * SR))) / SR
        f1 = f0 * (1 + .004 * np.sin(2 * np.pi * 5 * d))
        box[s:s + len(d)] += (np.sin(2 * np.pi * np.cumsum(f1) / SR) + .25 * np.sin(2 * np.pi * 2.01 * np.cumsum(f1) / SR)) * np.exp(-d / .6) * np.minimum(1, d / .006)
    swell = music._lp(r.standard_normal(n), 2500) * np.clip((t - (n / SR - 1.2)) / 1.2, 0, 1) ** 2
    nm = lambda x: x / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    y = nm(drone) * .55 + nm(beat) * .45 + nm(box) * .5 + nm(swell) * .15
    return y * .1 / (np.sqrt(np.mean(y ** 2)) + 1e-9)


def _chime(n, seed=5):
    """謎が解ける瞬間のようなチャイム（2026-10-30、ユーザー「チャララララーンみたいな、ゼルダのチャイムみたいな感じ」）：
    ベルの音色で駆け上がるアルペジオ（自作の音の並び。既存の曲の旋律はなぞらない）→ 最後の音と和音をのばす＋きらめき＋やわらかい和音の帯"""
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    def bell(f0, dur, dec):
        d = np.arange(int(dur * SR)) / SR
        return (np.sin(2 * np.pi * f0 * d) + .35 * np.sin(2 * np.pi * 2.0 * f0 * d) * np.exp(-d / (dec * .4)) + .12 * np.sin(2 * np.pi * 3.01 * f0 * d) * np.exp(-d / (dec * .2))) * np.exp(-d / dec) * np.minimum(1, d / .003)
    arp = np.zeros(n)
    notes = (293.7, 370.0, 440.0, 554.4, 659.3, 740.0, 880.0, 1108.7, 1318.5)   # レ・ファ♯・ラ・ド♯・ミ…（D の長九の和音を 2 オクターブ駆け上がる）
    for i, f0 in enumerate(notes):
        s = int((.12 + i * .075) * SR)
        last = i == len(notes) - 1
        b = bell(f0, 2.6 if last else 1.2, 1.1 if last else .45) * (1.3 if last else 1.0)
        arp[s:s + len(b)] += b[:max(0, n - s)]
    hold = np.zeros(n)
    s = int((.12 + (len(notes) - 1) * .075) * SR)
    for f0 in (587.3, 740.0, 880.0, 1108.7):   # 最後に和音をそっと重ねる
        b = bell(f0, 2.4, 1.0) * .45
        hold[s:s + len(b)] += b[:max(0, n - s)]
    pad = sum(np.sin(2 * np.pi * f * t + .3 * np.sin(2 * np.pi * .25 * t + k)) for k, f in enumerate((146.8, 220.0, 277.2, 329.6)))
    pad *= np.clip((t - .6) / .8, 0, 1)
    spark = np.zeros(n)
    for _ in range(14):   # きらめき（高い小さな粒）
        s = int((.8 + r.random() * 1.6) * SR); b = bell(2200 + r.random() * 1800, .4, .12) * .3
        spark[s:s + len(b)] += b[:max(0, n - s)]
    nm = lambda x: x / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    y = nm(arp) * .7 + nm(hold) * .35 + nm(pad) * .3 + nm(spark) * .12
    return y * .1 / (np.sqrt(np.mean(y ** 2)) + 1e-9)


SOUNDS = {"open_soft": _soft, "open_eerie": _eerie, "open_chime": _chime}


if not getattr(music, "_OPEN_LOADED", False):
    music._OPEN_LOADED = True
    _prev = music.bgm_techno

    def bgm_techno(total, sections, style="tech_air"):
        sec = sorted(sections)
        idx = [i for i, (a, m) in enumerate(sec) if m in SOUNDS]
        if not idx:
            return _prev(total, sections, style)
        i = idx[0]
        a0, a1, kind = sec[i][0], (sec[i + 1][0] if i + 1 < len(sec) else total), sec[i][1]
        out, info = _prev(total, [(a, "w_hold" if m in SOUNDS else m) for a, m in sec], style)
        out = np.array(out, dtype=float)
        n, s0, s1, f = len(out), int(a0 * SR), int(a1 * SR), int(.3 * SR)
        out[:s1] = 0.0
        out[s1:s1 + f] *= np.linspace(0, 1, len(out[s1:s1 + f]))   # 本編の曲は 0.3 秒で入る
        env = np.zeros(n)
        env[s0:s1] = 1.0
        env[s1:s1 + f] = np.linspace(1, 0, len(env[s1:s1 + f]))   # やさしい音は 0.3 秒で消える
        return out + SOUNDS[kind](n) * env, info

    music.bgm_techno = bgm_techno
