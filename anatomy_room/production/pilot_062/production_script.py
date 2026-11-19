#!/usr/bin/env python3
"""pilot_062「日本終末時計」（新ドパ設計、templates/DESIGN_MODES.md の 9 つ目）の制作スクリプト。

中身は plan.py（lines.json・assets/plan.js）、計算は scripts/pilot_062/sim/clock.py。映像は renderer.html（2D）。
声：冒頭と最後は W 冥鳴ひまり、本編は M 阿井田 茂 Calm 速め。BGM：Kevin MacLeod「Movement Proposition」（CC BY 4.0）126 BPM。
**BGM に合わせた編集**：動画の 0 秒＝曲の小節の頭（assets/bgm/beats.json）。セリフの始まりを拍にそろえる（python production_script.py snap）。
画面の動き・効果音も拍の頭に出す（renderer.html の BEAT）。閃光なし。共通エンディングなし（最後の画が冒頭につながる）。
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))
BGM = BEAT.get("file", "Movement Proposition.mp3")   # v3：Raving Energy（前の曲は beats_movement_proposition.json）
P = BEAT["period"]
START = BEAT["phase"] + P * BEAT.get("start_beats", 9)            # 曲のこの秒を動画の 0 秒に（小節の頭、前奏のあとの音の厚いところ）
pipeline, standard = epkit.setup(HERE, "intel", bgm=(BGM, round(BEAT["bpm"])), ending_gain=.0)
import bgm_file  # noqa: E402
bgm_file.register("file_062", HERE / "assets" / "bgm" / BGM, start=START, bpm=round(BEAT["bpm"]), gains={"ending": .0}, smooth=.3)
import noend_ext  # noqa: E402
noend_ext.apply(pipeline, black=0.0)

LINES = json.loads((HERE / "lines.json").read_text(encoding="utf-8"))["lines"]
TLP = HERE / "work" / "timeline.json"
SNAP = HERE / "assets" / "snap.json"


def snap():
    """セリフの始まりを拍（P 秒ごと）にそろえる：前の行の pause を延ばす。plan.py が snap.json を読む"""
    tl = json.loads(TLP.read_text(encoding="utf-8")); st = {x["id"]: x for x in tl["lines"]}
    old = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
    add, shift = {}, 0.0
    for a, b in zip(LINES, LINES[1:]):
        t = st[b["id"]]["start"] + shift; k = math.ceil((t - .045) / P); d = k * P - t   # 開始はコマ（1/30 秒）に丸められるので、拍より少し後ろでも同じ拍とみなす
        if d < .08:                   # ほとんど拍の上なら、そのまま（小さく前へずらすと詰まって聞こえる）
            d = 0.0
        add[a["id"]] = round(old.get(a["id"], 0.0) + d, 3); shift += d
    SNAP.write_text(json.dumps(add, ensure_ascii=False, indent=1), encoding="utf-8")
    print("snap:", sum(add.values()) - sum(old.values()), "秒のばした")


# 効果音（v4、新ドパ設計 v2）：動き・帯・札・判の出も効果音も表拍。Kenney の録音（CC0）＋pedalboard、音量は控えめ（sfx62.py）
sys.path.insert(0, str(HERE)); import sfx62  # noqa: E402
SFX = sfx62.events(TLP, LINES, P) if TLP.exists() else []

EP = standard.config({
    "id": "pilot_062",
    "out": "reverse_062_sports_outlier.mp4",
    "lead_in": 0.0,
    "cues": {l["scene"]: [l["id"], 0.0] for l in LINES},
    "sfx": SFX,
    "final_hold": P * 2,
    "music": {"style": "file_062", "sections": [["s00", 0.0, "f_full"], ["s01", 0.0, "f_85"], ["s08", 0.0, "f_full"], ["s09", 0.0, "f_70"], ["s12", 0.0, "f_full"], ["s13", 0.0, "f_85"], ["s14", 0.0, "f_full"]]},
    "segments": [l["scene"] for l in LINES],
    "extra_files": epkit.FILES + ["assets/plan.js", "work/blender/index.js", "../ext/blender/blframes.js"],
    "workers": 2,
    "qc_frames": [[l["scene"], .5] for l in LINES],
    "scenes": [(f"{i} {l['scene']}", l["scene"] if i else None, LINES[i + 1]["scene"] if i + 1 < len(LINES) else "endcard", l["id"], "") for i, l in enumerate(LINES)]
              + [(f"{len(LINES)} 終わり（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- 新ドパ設計 v2（061 型）：3D（Blender）。場面ごとに舞台を変える（陸上のトラック・バスケのコート・ゴルフのグリーン・野球場・サッカー場・クリケット場）。動き・効果音は表拍、カメラは拍に合わせて素早く。",
                   "- 物差しは偏差値（50＋10×z）。柱の高さ＝偏差値。天才 5 人（84〜87）の柱はほぼ同じ高さ、ブラッドマンの柱だけ空へ。最後は偏差値 94 の記念碑（v2）。閃光・点滅なし。"],
})

if __name__ == "__main__":
    if sys.argv[1:] == ["snap"]:
        snap()
    else:
        pipeline.main(__file__, EP)
