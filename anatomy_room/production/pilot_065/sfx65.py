"""pilot_065 の効果音（064 の sfx64.py の複製。MOVES・SEAL だけ 065 用）（新ドパ設計 v2、061 の sfx61.py と同じ作り）：動きも効果音も表拍、控えめ（060・061 と同じ GAIN 1.6）。
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
       "soft": [f"impactSoft_medium_00{i}.ogg" for i in range(2)], "frame": [f"impactSoft_medium_00{i}.ogg" for i in range(2)],
       # v2b（2026-11-19 ユーザーの指示「SE の種類を増やして、もっと目立たせて。冒頭は強めに」）
       "thud": [f"impactPunch_heavy_00{i}.ogg" for i in range(5)], "tin": [f"impactTin_medium_00{i}.ogg" for i in range(5)],
       "plank": [f"impactPlank_medium_00{i}.ogg" for i in range(5)], "softh": [f"impactSoft_heavy_00{i}.ogg" for i in range(5)],
       "woodh": [f"impactWood_heavy_00{i}.ogg" for i in range(5)], "rattle": [f"impactPlate_medium_00{i}.ogg" for i in range(5)],
       "tap": [f"impactGeneric_light_00{i}.ogg" for i in range(5)], "metalh": [f"impactMetal_heavy_00{i}.ogg" for i in range(5)],
       "swish": [f"card-shove-{i}.ogg" for i in range(1, 5)], "pluck": [f"pluck_00{i}.ogg" for i in range(1, 3)], "switch": [f"switch_00{i}.ogg" for i in range(1, 5)], "glass": KEN0["glass"], "tick": ["tick_001.ogg", "tick_002.ogg"]}
# 重ねて作る音（ファイル, ずらす秒, 音量）
MIX = {"run": [(f"footstep_concrete_00{i % 5}.ogg", d, a) for i, (d, a) in enumerate(((0, 1), (.06, .8), (.13, .9), (.19, .7), (.26, .8), (.33, .6), (.4, .7), (.47, .5)))],
       "grass": [(f"footstep_grass_00{i % 5}.ogg", d, a) for i, (d, a) in enumerate(((0, 1), (.14, .8), (.28, .9), (.42, .7)))],
       "rise": [(f"impactPlate_light_00{i % 5}.ogg", d, a) for i, (d, a) in enumerate(((0, 1), (.03, .7), (.07, .8), (.11, .5), (.16, .45)))],
       "wicket": [("impactWood_medium_001.ogg", 0, 1.0), ("impactWood_light_002.ogg", .05, .7), ("impactWood_light_004.ogg", .16, .4)],
       "tower": [("impactMetal_heavy_000.ogg", 0, 1.0), ("impactBell_heavy_001.ogg", .02, .5)],
       "bell": [("impactBell_heavy_003.ogg", 0, 1.0)],
       "watch": [("impactMetal_medium_001.ogg", 0, 1.0), ("tick_001.ogg", .1, .8), ("tick_002.ogg", .35, .6)],          # ストップウォッチが台座に
       "rumble": [("impactPlate_heavy_000.ogg", 0, 1.0), ("impactMining_001.ogg", .05, .7), ("impactPlate_heavy_002.ogg", .2, .5)],   # 柱がせり上がる（重い）
       "cricket": [("impactWood_heavy_000.ogg", 0, 1.0), ("impactWood_light_003.ogg", .12, .7)],                       # バットと球が台座に
       "swishball": [("impactPunch_heavy_001.ogg", 0, 1.0), ("impactTin_medium_002.ogg", .02, .6)]}                    # リングに当たって入る
LEVEL = {"whoosh": .04, "tagpop": .035, "stamp": .08, "drop": .05, "clink": .035, "kick": .045, "bat": .05, "pillar": .05, "soft": .04, "frame": .045,
         "run": .045, "grass": .04, "rise": .04, "wicket": .06, "tower": .07, "bell": .045,
         "thud": .055, "tin": .045, "plank": .05, "softh": .05, "woodh": .06, "rattle": .045, "tap": .045, "metalh": .06, "swish": .04, "pluck": .035, "switch": .03,
         "watch": .055, "rumble": .06, "cricket": .06, "swishball": .055, "glass": .045, "tick": .04}
GAIN = 2.3   # 2026-11-18「SE の音だけもう少し大きく」で 1.6（+4 dB）→ 2026-11-19「もっと目立たせて」で 2.3（さらに約 +3 dB）


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
MOVES = [   # 065 v2（13 場面）：物が動く拍だけ。冒頭は強め
    ("s00", 0, "run", 1.2), ("s00", 2, "run", 1.1), ("s00", 5, "metalh", 1.6),                      # 人形が扉を通る／金の人形が歩く／扉が閉まる
    ("s01", ("L01", 1, 0), "rumble", 1.2),                                                           # 条文の石板が落ちる
    ("s02", 0, "run", 1.0), ("s02", ("L02", 1, 0), "plank", 1.0),                                     # 3 人が歩く／看板
    ("s03", 1, "tap", 1.0), ("s03", ("L03", 1, 0), "stamp", 1.1), ("s03", ("L03", 1, 2), "soft", 1.0), ("s03", ("L03", 2, 0), "plank", 1.0),   # 電卓／判／父／札
    ("s04", 1, "tap", 1.0), ("s04", 2, "tap", 1.0), ("s04", ("L04", 1, 1), "soft", .8),               # はがきが 2 枚／3 枚目は来ない
    ("s05", ("L05", 1, 0), "rumble", 1.1), ("s05", ("L05", 2, 0), "woodh", 1.1),                      # 1950 年の石板／禁治産の札
    ("s06", 1, "swish", 1.0), ("s06", 2, "tin", 1.0), ("s06", ("L06", 2, 0), "metalh", 1.0),          # 札が裏返る／2 行目が変わる／決まりが光る
    ("s07", ("L07", 1, 0), "soft", 1.0), ("s07", ("L07", 2, 0), "tap", .9), ("s07", ("L07", 2, 2), "tap", .9),   # 寄りかかる／白紙の票
    ("s09", ("L09", 0, 1), "thud", 1.0), ("s09", ("L09", 1, 0), "tap", .9),                           # 電卓／投票用紙
    ("s10", ("L10", 2, 0), "woodh", 1.1),                                                            # 証拠の箱が開く（空）
    ("s11", ("L11", 1, 0), "rise", 1.1), ("s11", ("L11", 1, 1), "rise", 1.0), ("s11", ("L11", 1, 2), "rise", 1.0), ("s11", ("L11", 2, 1), "clink", 1.1),   # 起立／金のはがき
    ("s12", 1, "swish", 1.0), ("s12", ("L12", 1, 1), "tap", .9),                                       # 扉が開く／一票が箱へ
]
SEAL = [("s08", ("L08", 2, 0), "stamp", 1.0)]   # 2D の判（違憲）


def events(tl_path, lines, BP, phrase_gain=.8):
    """効果音の一覧（pipeline の sfx の形：[音, cue, 音量, ずらす秒]）。動き・帯／札の出（字幕の句）も音も表拍"""
    tl = json.load(open(tl_path, encoding="utf-8")); cues = tl["cues"]
    out, used = [], {}

    def put(scene, t_abs, name, gain):
        key = round(t_abs / BP)                                     # 拍の番号。同じ拍は 1 つだけ（大きい方）
        if key in used and used[key][2] >= gain:
            return
        used[key] = [name, scene, gain, round(t_abs - cues[scene], 4)]

    st0 = {x["id"]: x for x in tl["lines"] if not x.get("ending")}; lj = {x["id"]: x for x in lines}

    def beat_of(sc, k):
        """数字なら場面の拍。("L06", 句, ずらす拍) なら、その字幕の句が出る拍（renderer.html の phrases() と同じ計算）"""
        if not isinstance(k, (tuple, list)):
            return round(cues[sc] / BP) + k
        lid, j, off = k; L = st0[lid]; sub = lj[lid]["sub"]; tot = len("".join(sub)); acc = len("".join(sub[:j]))
        return round((L["start"] + (L["end"] - L["start"]) * acc / tot - .05) / BP) + off

    for sc, k, name, g in MOVES:
        put(sc, beat_of(sc, k) * BP, name, g)
    for sc, k, name, g in SEAL:
        put(sc, beat_of(sc, k) * BP, name, g)
    # 帯・札（字幕の句）の出：renderer.html の phrases() と同じ計算（拍の頭に丸める）
    st = {x["id"]: x for x in tl["lines"] if not x.get("ending")}
    for li, ln in enumerate(lines):
        L = st.get(ln["id"]); subs = ln["sub"]
        if not L or not subs:
            continue
        tot = len("".join(subs)); acc = 0
        for s in subs:
            a = round((L["start"] + (L["end"] - L["start"]) * acc / tot - .05) / BP) * BP; acc += len(s)
            put(ln["scene"], a, "tagpop" if li % 2 == 0 else "pluck", phrase_gain)
    out = [e for e in sorted(used.values(), key=lambda e: cues[e[1]] + e[3]) if cues[e[1]] + e[3] >= 0]
    n = {}
    for e in out:                                                   # 同じ種類の音は録音を順に回す
        k = e[0]; e[0] = f"{k}_{n.get(k, 0) % len(KEN.get(k, [0]))}"; n[k] = n.get(k, 0) + 1
    return out
