#!/usr/bin/env python3
"""pilot_039「あなたならどうする？——砂漠で迷子（マウロ・プロスペリ）」（チャンネル「リバース」当事者設計、シリーズ「あなたならどうする？」）の制作スクリプト。

台本は scripts/pilot_039/script_draft.md（2026-11-02 にユーザーが「OK」）、事実は fact_check.md、画像・曲・効果音は assets.md。
BGM は Kevin MacLeod「Smoking Gun」（incompetech、CC BY 4.0）。環境音・効果音は Freesound の CC0（ext/ambience.py）。
3D の場面は Blender（blender/scene.py → work/blender、ext/blender）。目線の演出は ext/kit/pov.js。
オープニングは状況と 2 択だけを冥鳴ひまりが読み、その場の環境音（雨・息づかい・砂嵐など）を強く出す。問いのあとは BGM を止めて心臓の音だけ。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("Smoking Gun.mp3", 88))
import noend_ext  # noqa: E402
noend_ext.apply(pipeline, black=3.4)   # 暗転の上に注意書き（renderer）   # 当事者設計は共通エンディングなし（2026-11-02、ユーザー「エンディングは不要」）。最後は暗転
import ambience  # noqa: E402

ambience.timeline(HERE / "work" / "timeline.json")
ambience.click("click", 2600); ambience.click("click2", 3100, double=True)   # 選択肢の札（無機質なクリック音）
ambience.register("open_storm", HERE / "assets/sfx/sandstorm.mp3", start=30, span=('l00', 'l01', 0.2), norm="rms")
ambience.register("open_breath", HERE / "assets/sfx/breath_run.mp3", start=3, span=('l00', 'l01', 0.2), norm="rms")
ambience.register("heart", HERE / "assets/sfx/heartbeat.mp3", start=0, dur=6, norm="rms")
ambience.register("run", HERE / "assets/sfx/breath_run.mp3", start=10, span=('l01', 'l02', 0.1), norm="rms")
ambience.register("steps", HERE / "assets/sfx/sand_steps.mp3", start=0, span=('l01', 'l03', 0), norm="rms")
ambience.register("storm", HERE / "assets/sfx/sandstorm.mp3", start=90, span=('l02', 'l04', 0.1), norm="rms")
ambience.register("desert", HERE / "assets/sfx/desert.mp3", start=0, span=('l04', 'end', 0), norm="rms")
ambience.register("heli", HERE / "assets/sfx/helicopter.mp3", start=4, span=('l05', 'l06', 0.3), norm="rms")
ambience.register("bats", HERE / "assets/sfx/bats.mp3", start=10, span=('l06', 'l08', 0), norm="rms")
ambience.register("breath", HERE / "assets/sfx/breath_m.mp3", start=2, dur=7, norm="rms")
ambience.register("steps_o", HERE / "assets/sfx/sand_steps.mp3", start=0, span=('l00a', 'l00b', 0.1), norm="rms")
ambience.register("bats_o", HERE / "assets/sfx/bats.mp3", start=10, span=('l00b', 'l01', 0.1), norm="rms")

EP = standard.config({
    "id": "pilot_039",
    "out": "reverse_039_prosperi.mp4",
    "cues": {"open": ["L00", 0.0], "pov": ["L01", 0.0], "ask": ["L08", 0.0], "exp": ["L09", 0.0], "after": ["L13", 0.0], "l00": ["L00", 0.0], "l00m": ["L00", 0.5], "l00a": ["L00a", 0.0], "l00am": ["L00a", 0.5], "l00b": ["L00b", 0.0], "l00bm": ["L00b", 0.5], "l01": ["L01", 0.0], "l01m": ["L01", 0.5], "l02": ["L02", 0.0], "l02m": ["L02", 0.5], "l03": ["L03", 0.0], "l03m": ["L03", 0.5], "l04": ["L04", 0.0], "l04m": ["L04", 0.5], "l05": ["L05", 0.0], "l05m": ["L05", 0.5], "l06": ["L06", 0.0], "l06m": ["L06", 0.5], "l07": ["L07", 0.0], "l07m": ["L07", 0.5], "l08": ["L08", 0.0], "l08m": ["L08", 0.5], "l09": ["L09", 0.0], "l09m": ["L09", 0.5], "l09b": ["L09b", 0.0], "l09bm": ["L09b", 0.5], "l10": ["L10", 0.0], "l10m": ["L10", 0.5], "l11": ["L11", 0.0], "l11m": ["L11", 0.5], "l12": ["L12", 0.0], "l12m": ["L12", 0.5], "l13": ["L13", 0.0], "l13m": ["L13", 0.5]},
    "sfx": [["open_storm", "l00", 1.7, 0], ["open_breath", "l00", 1.2, 0], ["heart", "l00", 0.8, 0], ["click", "l00", 1.0, 0.35], ["click", "l00a", 1.0, 0], ["steps_o", "l00a", 1.5, 0], ["click", "l00b", 1.0, 0], ["bats_o", "l00b", 1.0, 0], ["click", "ask", 1.0, 0], ["click2", "l09b", 1.0, 0], ["run", "l01", 0.9, 0], ["steps", "l01", 0.7, 0], ["storm", "l02", 1.4, 0], ["desert", "l04", 0.8, 0], ["heli", "l05", 1.1, 0], ["bats", "l06", 0.5, 0.4], ["breath", "l07", 0.7, 0], ["heart", "l08", 1.2, 0], ["steps", "l11", 0.5, 0]],
    "sfx_duck": 0.55,
    "music": {"style": "file_039", "sections": [["t0", 0.0, "f_15"], ["pov", -0.05, "f_mid"], ["l08", -0.3, "f_full"], ["l08m", 1.5, "f_mute"], ["l09", -0.05, "f_mid"], ["l13", -0.1, "f_low"]]},
    "segments": ["open", "pov", "ask", "exp", "after"],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "../ext/kit/pov.js", "work/blender/index.js", "../ext/blender/blframes.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 2.0], ["l00a", 0.6], ["l00b", 0.6], ["l01", 0.6], ["l02", 0.6], ["l03", 0.6], ["l04", 0.6], ["l05", 0.6], ["l06", 0.6], ["l07", 0.6], ["l08", 0.6], ["l09", 0.6], ["l09b", 0.6], ["l10", 0.6], ["l11", 0.6], ["l12", 0.6], ["l13", 0.6]],
    "scenes": [("0 open", None, "pov", "", ""), ("1 pov", "pov", "ask", "", ""), ("2 ask", "ask", "exp", "", ""), ("3 exp", "exp", "after", "", ""), ("4 after", "after", "endcard", "", ""), ("5 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- 設計：当事者設計（templates/DESIGN_MODES.md）。前半は当事者の目線（Blender の POV＋pov.js の揺れ・まばたき・ぼけ・息づかい）、後半は三人称の解説。", "- 文字は知的設計の字幕だけ（オープニングの問いは大きく）。", "- 顔は描かない。手は映してよい（ユーザー）。本物の画像は assets.md の権利の確かなものだけ。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
