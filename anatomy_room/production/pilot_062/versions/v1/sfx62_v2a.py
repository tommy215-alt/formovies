"""pilot_062 の効果音（新ドパ設計 v2、061 の sfx61.py と同じ作り）：動きも効果音も表拍、控えめ（060・061 と同じ GAIN 1.6）。
Kenney の録音（CC0、assets/sfx/）を pedalboard で整えて使う。同じ音が続かないよう何種類かを順に回す。
- drop：道具が台座に落ちる（impactPlank_medium ではなく impactWood_medium）　- clink：人形・金の玉（impactPlate_light・impactMetal_light）
- run：走る足音（footstep_concrete を重ねる）　- grass：芝の上を走る（footstep_grass）　- kick：球を蹴る（impactPunch_medium）
- bat：バットで打つ（impactWood_light）　- wicket：球が柱に当たりベイルが飛ぶ（impactWood_medium＋impactWood_light）
- pillar：金の柱がせり上がる（impactMetal_medium）　- tower：ブラッドマンの柱（impactMetal_heavy＋impactBell_heavy）　- whoosh・tagpop・stamp は 061 と同じ
置き方は events()：(場面, 拍, 音, 音量)。拍は blender/scene62.py の lbeat と同じ（0＝切り替わりの拍）。
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
KEN = {"whoosh": KEN0["whoosh"], "tagpop": KEN0["tagpop"], "stamp": KEN0["stamp"], "drop": [f"impactWood_medium_00{i}.ogg" for i in range(3)],
       "clink": [f"impactMetal_light_00{i}.ogg" for i in range(5)], "kick": [f"impactPunch_medium_00{i}.ogg" for i in range(5)],
       "bat": [f"impactWood_light_00{i}.ogg" for i in range(5)], "pillar": [f"impactMetal_medium_00{i}.ogg" for i in range(5)],
       "soft": [f"impactSoft_medium_00{i}.ogg" for i in range(2)], "frame": [f"impactSoft_medium_00{i}.ogg" for i in range(2)]}
# 重ねて作る音（ファイル, ずらす秒, 音量）
MIX = {"run": [(f"footstep_concrete_00{i % 5}.ogg", d, a) for i, (d, a) in enumerate(((0, 1), (.06, .8), (.13, .9), (.19, .7), (.26, .8), (.33, .6), (.4, .7), (.47, .5)))],
       "grass": [(f"footstep_grass_00{i % 5}.ogg", d, a) for i, (d, a) in enumerate(((0, 1), (.14, .8), (.28, .9), (.42, .7)))],
       "rise": [(f"impactPlate_light_00{i % 5}.ogg", d, a) for i, (d, a) in enumerate(((0, 1), (.03, .7), (.07, .8), (.11, .5), (.16, .45)))],
       "wicket": [("impactWood_medium_001.ogg", 0, 1.0), ("impactWood_light_002.ogg", .05, .7), ("impactWood_light_004.ogg", .16, .4)],
       "tower": [("impactMetal_heavy_000.ogg", 0, 1.0), ("impactBell_heavy_001.ogg", .02, .5)],
       "bell": [("impactBell_heavy_003.ogg", 0, 1.0)]}
LEVEL = {"whoosh": .04, "tagpop": .035, "stamp": .08, "drop": .05, "clink": .035, "kick": .045, "bat": .05, "pillar": .05, "soft": .04, "frame": .045,
         "run": .045, "grass": .04, "rise": .04, "wicket": .06, "tower": .07, "bell": .045}
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
MOVES = [   # v2（2026-11-19）：場面の並べ替え（ジョーダン・ニクラウス・天才 5 人の柱・偏差値 94）
    *[("s00", k, "drop", .8) for k in (0, 1, 3, 4, 6, 7)], ("s00", 9, "whoosh", .5), ("s00", 12, "whoosh", .45),
    ("s01", 0, "rise", .7), ("s01", 3, "whoosh", .5), ("s01", 6, "clink", .7),
    ("s02", 1, "run", .9), ("s02", 3, "whoosh", .5), ("s02", 5, "whoosh", .45), ("s02", 6, "pillar", .9),
    ("s03", 1, "soft", .7), ("s03", 2, "clink", .8), ("s03", 4, "pillar", .9), ("s03", 6, "whoosh", .45),
    ("s04", 1, "clink", .7), ("s04", 2, "soft", .8), ("s04", 4, "pillar", .9), ("s04", 6, "whoosh", .45),
    ("s05", 1, "bat", 1.0), ("s05", 3, "pillar", .9), ("s05", 5, "whoosh", .45),
    ("s06", 1, "kick", .9), ("s06", 2, "soft", .8), ("s06", 4, "pillar", .9), ("s06", 6, "whoosh", .45),
    *[("s07", k, "pillar", .75) for k in (1, 2, 3)], ("s07", 5, "whoosh", .45),
    ("s08", 2, "tower", 1.0), ("s08", 3, "whoosh", .5), ("s08", 5, "frame", .8), ("s08", 7, "whoosh", .5),
    ("s09", 2, "whoosh", .5), ("s09", 3, "bat", 1.0), ("s09", 5, "grass", .8), ("s09", 7, "grass", .7), ("s09", 8, "whoosh", .45),
    ("s10", 1, "whoosh", .45), ("s10", 2, "wicket", 1.0), *[("s10", 4 + i, "clink", .75) for i in range(6)],
    *[("s11", k, "pillar", .7) for k in (1, 2, 3, 4)], ("s11", 6, "whoosh", .45),
    ("s12", 1, "tower", 1.0), ("s12", 3, "whoosh", .45),
    ("s13", 1, "whoosh", .5), ("s13", 3, "whoosh", .45), ("s13", 4, "drop", .8),
    ("s14", 0, "bell", .8), ("s14", 2, "whoosh", .45), ("s14", 5, "whoosh", .45),
]
SEAL = [("s02", 5, "stamp", .7)]   # 2D の判（9.58）


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
