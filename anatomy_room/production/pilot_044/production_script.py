#!/usr/bin/env python3
"""pilot_044「あなたならどうする？——船を失った28人（シャクルトン）」（チャンネル「リバース」選択設計、シリーズ「あなたならどうする？」）の制作スクリプト。

台本は scripts/pilot_044/script_draft.md（2026-11-03 にユーザーが「OK」）、事実は fact_check.md、画像・曲・効果音は assets.md。
BGM は Kevin MacLeod「Ghostpocalypse - 7 Master」（incompetech、CC BY 4.0）。環境音・効果音は Freesound の CC0（ext/ambience.py）。
3D の場面は Blender（blender/scene.py → work/blender、ext/blender）。目線の演出は ext/kit/pov.js。
オープニングは状況と 2 択だけを冥鳴ひまりが読み、その場の環境音（雨・息づかい・砂嵐など）を強く出す。問いのあとは BGM を止めて心臓の音だけ。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("Ghostpocalypse - 7 Master.mp3", 160))
import noend_ext  # noqa: E402
noend_ext.apply(pipeline, black=2.8)   # 暗転の上に注意書き（renderer）   # 当事者設計は共通エンディングなし（2026-11-02、ユーザー「エンディングは不要」）。最後は暗転
import ambience  # noqa: E402

ambience.timeline(HERE / "work" / "timeline.json")
ambience.click("click", 2600); ambience.click("click2", 3100, double=True)   # 選択肢の札（無機質なクリック音）
ambience.register("sea", HERE / "assets/sfx/storm_sea.mp3", start=10, span=('l00', 'end', 0), norm="rms")
ambience.register("waves", HERE / "assets/sfx/waves.mp3", start=5, span=('l00', 'end', 0), norm="rms")
ambience.register("wind", HERE / "assets/sfx/wind.mp3", start=30, span=('l00', 'end', 0), norm="rms")
ambience.register("creak", HERE / "assets/sfx/creak.mp3", start=10, dur=6, norm="rms")
ambience.register("heart", HERE / "assets/sfx/heartbeat.mp3", start=0, dur=7, norm="rms")
ambience.register("breath", HERE / "assets/sfx/breath_m.mp3", start=2, dur=6, norm="rms")

EP = standard.config({
    "id": "pilot_044",
    "out": "reverse_044_shackleton.mp4",
    "cues": {"open": ["L00", 0.0], "pov": ["L01", 0.0], "ask": ["L06", 0.0], "exp": ["L07", 0.0], "after": ["L12", 0.0], "l00": ["L00", 0.0], "l00m": ["L00", 0.5], "l00a": ["L00a", 0.0], "l00am": ["L00a", 0.5], "l00b": ["L00b", 0.0], "l00bm": ["L00b", 0.5], "l01": ["L01", 0.0], "l01m": ["L01", 0.5], "l02": ["L02", 0.0], "l02m": ["L02", 0.5], "l03": ["L03", 0.0], "l03m": ["L03", 0.5], "l04": ["L04", 0.0], "l04m": ["L04", 0.5], "l05": ["L05", 0.0], "l05m": ["L05", 0.5], "l06": ["L06", 0.0], "l06m": ["L06", 0.5], "l07": ["L07", 0.0], "l07m": ["L07", 0.5], "l07b": ["L07b", 0.0], "l07bm": ["L07b", 0.5], "l08": ["L08", 0.0], "l08m": ["L08", 0.5], "l09": ["L09", 0.0], "l09m": ["L09", 0.5], "l10": ["L10", 0.0], "l10m": ["L10", 0.5], "l11": ["L11", 0.0], "l11m": ["L11", 0.5], "l12": ["L12", 0.0], "l12m": ["L12", 0.5]},
    "sfx": [["sea", "l00", 0.72, 0], ["wind", "l00", 0.6, 0], ["breath", "l00", 0.3, 0.2], ["click", "l00", 1.0, 0.35], ["click", "l00a", 1.0, 0], ["creak", "l00a", 0.48, 0.2], ["click", "l00b", 1.0, 0], ["waves", "l01", 0.8, 0], ["breath", "l03", 0.5, 0], ["creak", "l05", 0.6, 0], ["breath", "l05", 0.45, 1.0], ["click", "ask", 1.0, 0], ["heart", "ask", 0.7, 0], ["breath", "ask", 0.45, 0], ["click2", "l07b", 1.0, 0], ["creak", "l08", 0.9, 0], ["creak", "l00", 0.48, 1.0], ["waves", "l03", 0.8, 2.0]],
    "final_hold": 0.9,   # 最後のセリフのあとの余韻（2026-11-04）
    "sfx_duck": 0.55,
    "music": {"style": "file_044", "sections": [["t0", 0.0, "f_15"], ["pov", -0.05, "f_mid"], ["l06", -0.3, "f_full"], ["l06m", 1.5, "f_mute"], ["l07", -0.05, "f_mid"], ["l12", -0.1, "f_low"]]},
    "segments": ["open", "pov", "ask", "exp", "after"],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "../ext/kit/pov.js", "work/blender/index.js", "../ext/blender/blframes.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 2.0], ["l00a", 0.6], ["l00b", 0.6], ["l01", 0.6], ["l02", 0.6], ["l03", 0.6], ["l04", 0.6], ["l05", 0.6], ["l06", 0.6], ["l07", 0.6], ["l07b", 0.6], ["l08", 0.6], ["l09", 0.6], ["l10", 0.6], ["l11", 0.6], ["l12", 0.6]],
    "scenes": [("0 open", None, "pov", "", ""), ("1 pov", "pov", "ask", "", ""), ("2 ask", "ask", "exp", "", ""), ("3 exp", "exp", "after", "", ""), ("4 after", "after", "endcard", "", ""), ("5 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- 設計：当事者設計（templates/DESIGN_MODES.md）。前半は当事者の目線（Blender の POV＋pov.js の揺れ・まばたき・ぼけ・息づかい）、後半は三人称の解説。", "- 文字は知的設計の字幕だけ（オープニングの問いは大きく）。", "- 顔は描かない。手は映してよい（ユーザー）。本物の画像は assets.md の権利の確かなものだけ。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
# OPEN_AMB=0.6：冒頭の環境音は声が聞き取れる大きさに（2026-11-04）
