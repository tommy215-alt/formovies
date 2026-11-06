#!/usr/bin/env python3
"""pilot_045「もしも東京にゾンビが一体現れたら？」（チャンネル「リバース」もしも設計）の制作スクリプト。

条件はユーザーが決め、Claude が計算した（scripts/pilot_045/sim/、結果 sim/results.md、仮定 fact_check.md）。
流れ：地上（都庁前、カメラ 1.5 m）→ 新宿の街（300 m〜3 km）→ 関東（30 km）→ 日本（300 km〜）→ 宇宙 → 最初の一体に戻る（ループ）。
3D の場面は Blender（blender/scene.py → work/blender）。広がりの地図は計算の結果から作る（blender/make_maps.py）。
BGM は Kevin MacLeod「Cyborg Ninja」（incompetech、CC BY 4.0、pilot_035 と同じ）。効果音は Freesound の CC0（assets.md）。
共通エンディングなし（もしも設計）。最後の一言と画が冒頭にもどる。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("Cyborg Ninja.mp3", 160))
import noend_ext  # noqa: E402
noend_ext.apply(pipeline, black=1.5)   # もしも設計は共通エンディングなし。最後は短く暗転して冒頭へ（ループ）
import ambience  # noqa: E402

ambience.timeline(HERE / "work" / "timeline.json")
ambience.click("click", 2600)   # 札が出る音
ambience.register("crowd", HERE / "assets/sfx/crowd.mp3", start=5, span=("l00", "l06", 0), norm="rms")
ambience.register("radio", HERE / "assets/sfx/radio.mp3", start=3, dur=4, norm="rms")
ambience.register("heli", HERE / "assets/sfx/helicopter.mp3", start=2, dur=6, norm="rms")
ambience.register("heart", HERE / "assets/sfx/heartbeat.mp3", start=0, dur=5, norm="rms")
ambience.register("wind", HERE / "assets/sfx/wind.mp3", start=30, span=("l10", "end", 0), norm="rms")
ambience.register("breath", HERE / "assets/sfx/breath_m.mp3", start=2, dur=4, norm="rms")

LINES = ["l%02d" % i for i in range(17)]
CUES = {"open": ["L00", 0.0], "ground": ["L01", 0.0], "city": ["L03", 0.0], "kanto": ["L06", 0.0], "japan": ["L10", 0.0],
        "space": ["L15", 0.0], "loop": ["L16", 0.0]}
for i in range(17):
    CUES["l%02d" % i] = ["L%02d" % i, 0.0]; CUES["l%02dm" % i] = ["L%02d" % i, 0.5]

EP = standard.config({
    "id": "pilot_045",
    "out": "reverse_045_zombie_tokyo.mp4",
    "cues": CUES,
    "sfx": [["crowd", "l00", 0.55, 0], ["click", "l01", 1.0, 0.2], ["click", "l02", 1.0, 0.3], ["breath", "l02", 0.35, 0.2],
            ["click", "l03", 1.0, 0.2], ["radio", "l04", 0.55, 0], ["click", "l04", 1.0, 0.3], ["click", "l05", 1.0, 0.2],
            ["click", "l06", 1.0, 0.3], ["click", "l07", 1.0, 0.2], ["heli", "l08", 0.6, 0], ["click", "l08", 1.0, 0.3],
            ["click", "l09", 1.0, 0.2], ["heart", "l10", 0.6, 0], ["click", "l10", 1.0, 0.2], ["click", "l11", 1.0, 0.1],
            ["click", "l12", 1.0, 0.1], ["click", "l13", 1.0, 0.2], ["click", "l14", 1.0, 0.2], ["click", "l15", 1.0, 0.3],
            ["wind", "l10", 0.35, 0], ["click", "l16", 1.0, 0.1]],
    "final_hold": 1.8,
    "sfx_duck": 0.55,
    "music": {"style": "file_045", "sections": [["t0", 0.0, "f_60"], ["ground", -0.05, "f_mid"], ["city", -0.05, "f_full"], ["l09", -0.1, "f_low"],
                                                 ["l10", -0.05, "f_mid"], ["l11", -0.05, "f_full"], ["space", -0.2, "f_low"], ["loop", -0.1, "f_mute"]]},
    "segments": ["open", "ground", "city", "kanto", "japan", "space", "loop"],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[c, 0.6] for c in LINES[1:]],
    "scenes": [("0 open", None, "ground", "", ""), ("1 ground", "ground", "city", "", ""), ("2 city", "city", "kanto", "", ""),
               ("3 kanto", "kanto", "japan", "", ""), ("4 japan", "japan", "space", "", ""), ("5 space", "space", "loop", "", ""),
               ("6 loop", "loop", "endcard", "", ""), ("7 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- 設計：もしも設計（templates/DESIGN_MODES.md）。小さいところ（都庁前の一体、カメラ 1.5 m）から、段階ごとにカメラが高くなる。",
                   "- ステータス（経過・ゾンビの数・範囲）はポップアウトの札、カメラの高さは右の目盛り。ナレーションは状況だけ。",
                   "- 人物は簡易的なピクトグラム（男女・子ども・高齢者・警察官・自衛官の区別）。血は出さない。", "- 地図の広がりは計算の結果（sim/）。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
