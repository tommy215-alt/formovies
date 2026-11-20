#!/usr/bin/env python3
"""pilot_065「2013年まで、選挙に行けなかった日本人」（新ドパ設計 v2、061 型）の制作スクリプト。

中身は plan.py（lines.json・assets/plan.js）。3D は blender/scene65.py（Cycles）、文字と仕上げは renderer.html。
声：冒頭と最後は W 春日部つむぎ、本編は M 青山龍星 ノーマル。BGM：Kevin MacLeod「Funk Game Loop」（CC BY 4.0、061 の並べ替え）105 BPM。
**BGM に合わせた編集**：動画の 0 秒＝曲の小節の頭（assets/bgm/beats.json）。セリフの始まりを拍にそろえる（python production_script.py snap）。
動き・効果音は拍の頭。閃光なし。共通エンディングなし（最後の画が冒頭につながる）。
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
bgm_file.register("file_065", HERE / "assets" / "bgm" / BGM, start=START, bpm=round(BEAT["bpm"]), gains={"ending": .0, "f_open": 1.8, "f_up": 1.5, "f_mid2": 1.25, "f_low": .95}, smooth=.3)
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


# 効果音（v4、新ドパ設計 v2）：動き・帯・札・判の出も効果音も表拍。Kenney の録音（CC0）＋pedalboard、音量は控えめ（sfx65.py）
sys.path.insert(0, str(HERE)); import sfx65  # noqa: E402
SFX = sfx65.events(TLP, LINES, P) if TLP.exists() else []

EP = standard.config({
    "id": "pilot_065",
    "out": "reverse_065_vote_restored.mp4",
    "lead_in": 0.0,
    "cues": {l["scene"]: [l["id"], 0.0] for l in LINES},
    "sfx": SFX,
    "final_hold": P * 2,
    "music": {"style": "file_065", "sections": [["s00", 0.0, "f_open"], ["s01", 0.0, "f_up"], ["s04", 0.0, "f_low"], ["s08", 0.0, "f_up"], ["s12", 0.0, "f_mid2"]]},
    "segments": [l["scene"] for l in LINES],
    "extra_files": epkit.FILES + ["assets/plan.js", "work/blender/index.js", "../ext/blender/blframes.js"],
    "workers": 2,
    "qc_frames": [[l["scene"], .5] for l in LINES],
    "scenes": [(f"{i} {l['scene']}", l["scene"] if i else None, LINES[i + 1]["scene"] if i + 1 < len(LINES) else "endcard", l["id"], "") for i, l in enumerate(LINES)]
              + [(f"{len(LINES)} 終わり（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- 新ドパ設計 v2（061 型）：3D（Blender）。体育館の投票所の扉が閉まる → 居間で選挙公報と入場券 → 朝の住宅街を両親と → 後見人の書類 → 郵便受けに彼女のはがきだけ来ない → 資料室の条文の石板 → 天秤（電卓と投票用紙）→ 法廷 → 国会の議場で一斉に起立 → はがきが 3 枚そろう → 投票所の扉が開き、一票が箱へ。", "- 説教臭くしない：責める言葉・べき論なし。人は顔のない模型、実名・写真なし。閃光・点滅なし。"],
})

if __name__ == "__main__":
    if sys.argv[1:] == ["snap"]:
        snap()
    else:
        pipeline.main(__file__, EP)
