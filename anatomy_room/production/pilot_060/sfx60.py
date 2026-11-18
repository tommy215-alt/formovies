"""pilot_060 v4 の効果音（新ドパ設計 v2、061 の sfx61.py と同じ作り）：動きも効果音も表拍、控えめ。
Kenney の録音（CC0、assets/sfx/）を pedalboard で整えて使う。同じ音が続かないよう何種類かを順に回す。
- tick：時計の針が動く（interface の tick＋rpg の metalClick）　- fall：人形が倒れる（陶器の軽い音 impactPlate_light を重ねる）
- plaque：年の木札が落ちる（impactWood_medium）　- frame：写真の額が置かれる（impactSoft_medium）　- whoosh・tagpop・stamp は 061 と同じ
置き方は events()：(場面, 拍, 音, 音量)。拍は blender/scene60.py の lbeat と同じ（0＝切り替わりの拍）。
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np

import music
from music import SR, _soften

SFXDIR = Path(__file__).resolve().parent / "assets" / "sfx"
KEN0 = {"gclink": [f"impactMetal_light_00{i}.ogg" for i in range(5)], "gpile": [f"chips-stack-{i}.ogg" for i in range(1, 7)],
       "whoosh": [f"card-slide-{i}.ogg" for i in range(1, 5)], "tagpop": [f"select_00{i}.ogg" for i in range(1, 5)],
       "stamp": ["impactWood_heavy_000.ogg"], "glass": [f"impactGlass_light_00{i}.ogg" for i in range(4)],
       "heavy": ["impactMetal_heavy_000.ogg"], "soft": [f"impactSoft_heavy_00{i}.ogg" for i in range(2)], "tap": [f"impactGeneric_light_00{i}.ogg" for i in range(2)]}
KEN = {"whoosh": KEN0["whoosh"], "tagpop": KEN0["tagpop"], "stamp": KEN0["stamp"], "tick": ["tick_001.ogg", "tick_002.ogg"],
       "plaque": [f"impactWood_medium_00{i}.ogg" for i in range(3)], "frame": [f"impactSoft_medium_00{i}.ogg" for i in range(2)]}
# 重ねて作る音（ファイル, ずらす秒, 音量）
MIX = {"bigtick": [("metalClick.ogg", 0, 1.0), ("tick_001.ogg", .01, .6)],                                  # 針が大きく動いて着く
       "fall": [(f"impactPlate_light_00{i % 5}.ogg", d, a) for i, (d, a) in enumerate(((0, 1), (.04, .7), (.09, .8), (.15, .5), (.21, .45)))],   # 人形がまとめて倒れる
       "fall1": [("impactPlate_light_002.ogg", 0, 1.0)]}
LEVEL = {"whoosh": .04, "tagpop": .035, "stamp": .08, "tick": .025, "plaque": .05, "frame": .045, "bigtick": .05, "fall": .045, "fall1": .035}   # 合成の版と同じ控えめの大きさ
GAIN = 1.6   # 2026-11-18 ユーザーの指示「SE の音だけもう少し大きく」：全体を約 +4 dB


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
            out[f"{k}_{i}"] = _soften(_load(fn), cut=9500, rms=LEVEL[k] * GAIN)
    for k, parts in MIX.items():
        y = np.zeros(int(1.2 * SR))
        for fn, d, a in parts:
            x = _load(fn); i = int(d * SR); y[i:i + len(x)] += a * x[:len(y) - i]
        out[f"{k}_0"] = _soften(y, cut=9500, rms=LEVEL[k] * GAIN)
    return out


if not getattr(music, "_SFX60", False):
    music._SFX60 = True
    _prev = music.sfx_bank_soft

    def sfx_bank_soft():
        d = _prev(); d.update(bank()); return d

    music.sfx_bank_soft = sfx_bank_soft


# (場面, 拍, 音, 音量)：動きの拍。効果音も同じ拍の頭。拍は scene61.py の lbeat（場面の cue のあとの最初の拍が 0）
MOVES = [
    *[("s00", k, "tick", .5) for k in range(2, 11)], ("s00", 2, "whoosh", .4), ("s00", 4, "whoosh", .55), ("s00", 6, "whoosh", .55),
    ("s01", 2, "whoosh", .5), ("s01", 4, "fall", .8), ("s01", 5, "bigtick", .9),
    ("s02", 0, "plaque", .8), ("s02", 2, "fall", .9), ("s02", 3, "fall", .9), ("s02", 5, "whoosh", .5),
    ("s03", 1, "bigtick", 1.0),
    ("s04", 0, "plaque", .8), ("s04", 2, "frame", .8), ("s04", 4, "fall1", .8), ("s04", 5, "bigtick", .9), ("s04", 7, "whoosh", .5),
    ("s05", 0, "plaque", .8), ("s05", 2, "frame", .8), ("s05", 4, "whoosh", .5), ("s05", 6, "bigtick", .9),
    ("s06", 0, "plaque", .8), ("s06", 2, "frame", .8), ("s06", 3, "fall1", .8), ("s06", 5, "bigtick", .9),
    ("s07", 0, "plaque", .8), ("s07", 2, "frame", .8), ("s07", 3, "whoosh", .5), ("s07", 5, "bigtick", .9),
    ("s08", 1, "whoosh", .6),
    ("s09", 2, "plaque", .8), *[("s09", 3 + j, "fall1", .55) for j in range(8)], ("s09", 4, "whoosh", .45), ("s09", 10, "whoosh", .45),
    ("s10", 1, "bigtick", 1.0), ("s10", 2, "tagpop", .6), ("s10", 4, "whoosh", .5),
    ("s11", 0, "plaque", .8), ("s11", 1, "fall", .9), ("s11", 3, "bigtick", 1.0),
    *[("s12", k, "tick", .45) for k in range(1, 5)], ("s12", 2, "whoosh", .45),
]
SEAL = [("s03", 1, "stamp", .7), ("s04", 5, "stamp", .6), ("s05", 6, "stamp", .6), ("s06", 5, "stamp", .6), ("s07", 5, "stamp", .6), ("s10", 1, "stamp", .7), ("s11", 3, "stamp", .7)]   # 2D の秒の判（針と同じ拍なので、大きい方だけ鳴る）


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
        c = cues[sc]; put(sc, (round(c / BP) + k) * BP, name, g)
    for sc, k, name, g in SEAL:
        put(sc, (round(cues[sc] / BP) + k) * BP, name, g)
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
        k = e[0]; e[0] = f"{k}_{n.get(k, 0) % len(KEN.get(k, [0]))}"; n[k] = n.get(k, 0) + 1
    return out
