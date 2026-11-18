"""pilot_061 の効果音（2026-11-18 ユーザーの指示）：動きは表拍（拍の頭）、効果音は裏拍（拍の頭から半拍あと）。音量は目立たせない。
テンプレートの外の部品。music.sfx_bank_soft を包んで、金の音を足す（合成。外の素材は使わない）：
- gclink：金の延べ棒が 1 本置かれる「チン」（金属の倍音、短い）
- gpile ：延べ棒が何本か積まれる「チャラッ」（低めの金属音を 4 つ、0.2 秒に散らす）
置き方は events()：(場面, 拍, 音, 音量) の一覧を、各場面の cue からの秒に直す。拍は blender/scene61.py の lbeat と同じ数え方。
"""
import json
import math

import numpy as np

import music
from music import SR, _bell, _lp, _noise, _add, _soften


def _clink(f, dur=.35, amp=1.0, seed=1):
    t = np.arange(int(dur * SR)) / SR
    x = sum(a * np.sin(2 * np.pi * f * m * t + seed * k) * np.exp(-t / (d * dur))
            for k, (m, a, d) in enumerate(((1.0, 1.0, .35), (2.76, .55, .22), (5.40, .3, .12), (8.93, .15, .07))))
    tick = _lp(_noise(int(.01 * SR), 600 + seed), 6000) * np.exp(-np.arange(int(.01 * SR)) / SR / .0015) * .6
    x[:len(tick)] += tick
    return x * amp * np.minimum(1, t / .002)


def bank():
    late = lambda d, x: np.concatenate([np.zeros(int(d * SR)), x])
    b = {"gclink": _clink(1760, .35, 1.0, 3),
         "gpile": _add(*[late(d, _clink(f, .3, a, s)) for d, f, a, s in ((0, 1180, 1, 1), (.05, 1420, .8, 2), (.11, 990, .9, 4), (.19, 1310, .6, 5))])}
    level = {"gclink": .035, "gpile": .045}
    return {k: _soften(v, cut=7000, rms=level[k]) for k, v in b.items()}


if not getattr(music, "_SFX61", False):
    music._SFX61 = True
    _prev = music.sfx_bank_soft

    def sfx_bank_soft():
        d = _prev(); d.update(bank()); return d

    music.sfx_bank_soft = sfx_bank_soft


# (場面, 拍, 音, 音量)：動きの拍。効果音はこの半拍あと。拍は scene61.py の lbeat（場面の cue のあとの最初の拍が 0）
MOVES = [
    ("s00", 1, "gclink", .7), ("s00", 2, "gclink", .6), ("s00", 3, "gclink", .7), ("s00", 4, "gclink", .6), ("s00", 5, "whoosh", .6),
    *[("s01", k, "gpile", .55) for k in range(1, 10)],
    ("s01", 8, "stamp", .5), ("s01", 9, "gclink", .6), ("s01", 10, "gclink", .55), ("s01", 11, "gclink", .6), ("s01", 12, "gclink", .65),
    ("s02", 0, "gpile", .8),
    ("s03", 2, "whoosh", .6), ("s03", 4, "whoosh", .6),
    ("s04", 2, "gclink", .7), ("s04", 3, "gclink", .7), ("s04", 5, "gclink", .7), ("s04", 6, "whoosh", .5), ("s04", 7, "gclink", .6),
    ("s05", 2, "gclink", .55),
    ("s06", 0, "gclink", .65), ("s06", 2, "gclink", .65), ("s06", 4, "gclink", .65), ("s06", 6, "whoosh", .5),
    ("s07", 1, "gclink", .5), ("s07", 4, "whoosh", .5),
    ("s08", 1, "stamp", .55),
    ("s09", 1, "whoosh", .5), ("s09", 3, "gpile", .8), ("s09", 5, "gclink", .6), ("s09", 6, "gpile", .5), ("s09", 7, "whoosh", .45), ("s09", 9, "whoosh", .45),
    ("s10", 1, "whoosh", .5), ("s10", 3, "whoosh", .5), ("s10", 6, "whoosh", .55),
]
SEAL = [("s08", 2, "stamp", .6)]   # 2D の判（CUE.s08 + 2 拍）。CUE そのものから数える


def events(tl_path, lines, BP, phrase_gain=.6):
    """効果音の一覧（pipeline の sfx の形：[音, cue, 音量, ずらす秒]）。動き・帯／札の出（字幕の句）は表拍、音は裏拍"""
    tl = json.load(open(tl_path, encoding="utf-8")); cues = tl["cues"]
    out, used = [], {}

    def put(scene, t_abs, name, gain):
        key = round((t_abs + BP / 2) / BP * 2)                     # 半拍の番号。同じ半拍は 1 つだけ（大きい方）
        if key in used and used[key][2] >= gain:
            return
        used[key] = [name, scene, gain, round(t_abs + BP / 2 - cues[scene], 4)]

    for sc, k, name, g in MOVES:
        c = cues[sc]; put(sc, (math.ceil(c / BP - 1e-6) + k) * BP, name, g)
    for sc, k, name, g in SEAL:
        put(sc, cues[sc] + k * BP, name, g)
    # 帯・札（字幕の句）の出：renderer.html の phrases() と同じ計算（拍の頭に丸める）
    st = {x["id"]: x for x in tl["lines"] if not x.get("ending")}
    for ln in lines:
        L = st.get(ln["id"]); subs = ln["sub"]
        if not L or not subs:
            continue
        tot = len("".join(subs)); acc = 0
        for s in subs:
            a = round((L["start"] + (L["end"] - L["start"]) * acc / tot - .05) / BP) * BP; acc += len(s)
            put(ln["scene"], a, "tagpop", phrase_gain)
    out = sorted(used.values(), key=lambda e: cues[e[1]] + e[3])
    return [e for e in out if cues[e[1]] + e[3] >= 0]
