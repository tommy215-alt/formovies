"""pilot_061 の効果音（2026-11-18 ユーザーの指示）：動きも効果音も表拍（拍の頭）。音量は目立たせない（最初は裏拍だったが、ユーザーの指示で表拍に）。
テンプレートの外の部品。music.sfx_bank_soft を包んで、金の音を足す。
v2（2026-11-18 ユーザーの指示「SE も新しいのに」）：合成をやめ、Kenney の録音（CC0、assets/sfx/、元は %LOCALAPPDATA%/reverse_tools/kenney_sfx）を
pedalboard（低域・高域を切る、軽いコンプ、小さな部屋の響き）で整えて使う。同じ音が続かないよう、何種類かを順に回す。
- gclink：延べ棒・金の玉が置かれる（impactMetal_light）　- gpile：延べ棒の山（chips-stack）
- whoosh：カメラが寄る・回る（card-slide）　- tagpop：帯・札が出る（interface の select）　- stamp：天秤が傾く・判（impactWood_heavy）
置き方は events()：(場面, 拍, 音, 音量) の一覧を、各場面の cue からの秒に直す。拍は blender/scene61.py の lbeat と同じ数え方。
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np

import music
from music import SR, _soften

SFXDIR = Path(__file__).resolve().parent / "assets" / "sfx"
KEN = {"gclink": [f"impactMetal_light_00{i}.ogg" for i in range(5)], "gpile": [f"chips-stack-{i}.ogg" for i in range(1, 7)],
       "whoosh": [f"card-slide-{i}.ogg" for i in range(1, 5)], "tagpop": [f"select_00{i}.ogg" for i in range(1, 5)],
       "stamp": ["impactWood_heavy_000.ogg"]}
LEVEL = {"gclink": .035, "gpile": .045, "whoosh": .04, "tagpop": .035, "stamp": .08}   # 合成の版と同じ控えめの大きさ


def _load(fn, dur=.7):
    from pedalboard import Pedalboard, HighpassFilter, LowpassFilter, Compressor, Reverb
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(SFXDIR / fn), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    x = np.concatenate([x, np.zeros(int(.25 * SR), np.float32)])[:int(dur * SR)]
    fx = Pedalboard([HighpassFilter(140), LowpassFilter(9500), Compressor(threshold_db=-20, ratio=3, attack_ms=2, release_ms=80),
                     Reverb(room_size=.22, damping=.6, wet_level=.08, dry_level=.95)])
    y = fx(x.reshape(1, -1), SR)[0].astype(np.float64)
    f = int(.08 * SR); y[-f:] *= np.linspace(1, 0, f)
    return y


def bank():
    out = {}
    for k, files in KEN.items():
        for i, fn in enumerate(files):
            out[f"{k}_{i}"] = _soften(_load(fn), cut=9500, rms=LEVEL[k])
    return out


if not getattr(music, "_SFX61", False):
    music._SFX61 = True
    _prev = music.sfx_bank_soft

    def sfx_bank_soft():
        d = _prev(); d.update(bank()); return d

    music.sfx_bank_soft = sfx_bank_soft


# (場面, 拍, 音, 音量)：動きの拍。効果音も同じ拍の頭。拍は scene61.py の lbeat（場面の cue のあとの最初の拍が 0）
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
    """効果音の一覧（pipeline の sfx の形：[音, cue, 音量, ずらす秒]）。動き・帯／札の出（字幕の句）も音も表拍"""
    tl = json.load(open(tl_path, encoding="utf-8")); cues = tl["cues"]
    out, used = [], {}

    def put(scene, t_abs, name, gain):
        key = round(t_abs / BP)                                     # 拍の番号。同じ拍は 1 つだけ（大きい方）
        if key in used and used[key][2] >= gain:
            return
        used[key] = [name, scene, gain, round(t_abs - cues[scene], 4)]

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
    out = [e for e in sorted(used.values(), key=lambda e: cues[e[1]] + e[3]) if cues[e[1]] + e[3] >= 0]
    n = {}
    for e in out:                                                   # 同じ種類の音は録音を順に回す
        k = e[0]; e[0] = f"{k}_{n.get(k, 0) % len(KEN[k])}"; n[k] = n.get(k, 0) + 1
    return out
