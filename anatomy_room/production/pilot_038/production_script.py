#!/usr/bin/env python3
"""pilot_038「あなたならどうする？——発射直後の雷（アポロ12号）」（チャンネル「リバース」当事者設計、シリーズ「あなたならどうする？」）の制作スクリプト。

台本は scripts/pilot_038/script_draft.md（2026-11-02 にユーザーが「OK」）、事実は fact_check.md、画像・曲・効果音は assets.md。
BGM は Kevin MacLeod「Decisions」（incompetech、CC BY 4.0）。環境音・効果音は Freesound の CC0（ext/ambience.py）。
3D の場面は Blender（blender/scene.py → work/blender、ext/blender）。目線の演出は ext/kit/pov.js。
オープニングは状況と 2 択だけを冥鳴ひまりが読み、その場の環境音（雨・息づかい・砂嵐など）を強く出す。問いのあとは BGM を止めて心臓の音だけ。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("Decisions.mp3", 80))
import noend_ext  # noqa: E402
noend_ext.apply(pipeline, black=3.4)   # 暗転の上に注意書き（renderer）   # 当事者設計は共通エンディングなし（2026-11-02、ユーザー「エンディングは不要」）。最後は暗転
import ambience  # noqa: E402

ambience.timeline(HERE / "work" / "timeline.json")
ambience.click("click", 2600); ambience.click("click2", 3100, double=True)   # 選択肢の札（無機質なクリック音）
ambience.register("open_rocket", HERE / "assets/sfx/rocket.mp3", start=0, span=('l00', 'l01', 0.2), norm="rms")
ambience.register("bolt", HERE / "assets/sfx/lightning.mp3", start=0, dur=5, norm="peak")
ambience.register("radio", HERE / "assets/sfx/radio_noise.mp3", start=5, dur=3, norm="rms")
ambience.register("room", HERE / "assets/sfx/control_room.mp3", start=2, span=('l01', 'end', 0), norm="rms")
ambience.register("launch", HERE / "assets/sfx/shuttle.mp3", start=8, dur=3.5, norm="rms")
ambience.register("breath", HERE / "assets/sfx/breath_m.mp3", start=2, dur=7, norm="rms")
ambience.register("heart", HERE / "assets/sfx/heartbeat.mp3", start=0, dur=6, norm="rms")
ambience.register("room_ask", HERE / "assets/sfx/control_room.mp3", start=40, span=('ask', 'exp', 0), norm="rms")
ambience.register("radio_ask", HERE / "assets/sfx/radio_noise.mp3", start=12, span=('ask', 'exp', 0), norm="rms")
ambience.register("radio_open", HERE / "assets/sfx/radio_noise.mp3", start=20, span=('l00', 'l01', 0.1), norm="rms")

EP = standard.config({
    "id": "pilot_038",
    "out": "reverse_038_apollo12.mp4",
    "cues": {"open": ["L00", 0.0], "pov": ["L01", 0.0], "ask": ["L07", 0.0], "exp": ["L08", 0.0], "after": ["L13", 0.0], "l00": ["L00", 0.0], "l00m": ["L00", 0.5], "l00a": ["L00a", 0.0], "l00am": ["L00a", 0.5], "l00b": ["L00b", 0.0], "l00bm": ["L00b", 0.5], "l01": ["L01", 0.0], "l01m": ["L01", 0.5], "l02": ["L02", 0.0], "l02m": ["L02", 0.5], "l03": ["L03", 0.0], "l03m": ["L03", 0.5], "l04": ["L04", 0.0], "l04m": ["L04", 0.5], "l05": ["L05", 0.0], "l05m": ["L05", 0.5], "l06": ["L06", 0.0], "l06m": ["L06", 0.5], "l07": ["L07", 0.0], "l07m": ["L07", 0.5], "l08": ["L08", 0.0], "l08m": ["L08", 0.5], "l08b": ["L08b", 0.0], "l08bm": ["L08b", 0.5], "l09": ["L09", 0.0], "l09m": ["L09", 0.5], "l10": ["L10", 0.0], "l10m": ["L10", 0.5], "l11": ["L11", 0.0], "l11m": ["L11", 0.5], "l12": ["L12", 0.0], "l12m": ["L12", 0.5], "l13": ["L13", 0.0], "l13m": ["L13", 0.5]},
    "sfx": [["open_rocket", "l00", 1.6, 0], ["bolt", "l00", 1.0, 0.6], ["radio", "l00", 0.7, 0.8], ["breath", "l00", 0.12, 0.2], ["heart", "l00", 0.25, 0], ["click", "l00", 1.0, 0.35], ["radio_open", "l00", 0.8, 0], ["alarm", "l00", 0.55, 0.9], ["alarm", "l00", 0.5, 1.9], ["click", "l00a", 1.0, 0], ["alarm", "l00a", 0.5, 0.4], ["click", "l00b", 1.0, 0], ["alarm", "l00b", 0.5, 0.4], ["click", "ask", 1.0, 0], ["room_ask", "ask", 1.3, 0], ["radio_ask", "ask", 0.9, 0], ["alarm", "ask", 0.5, 0.6], ["alarm", "ask", 0.45, 2.2], ["alarm", "ask", 0.45, 3.8], ["alarm", "ask", 0.4, 5.4], ["click2", "l08b", 1.0, 0], ["ok", "l10", 0.5, 2.5], ["room", "l01", 0.8, 0], ["launch", "l02", 1.2, 0], ["bolt", "l03", 1.0, 0], ["radio", "l03", 0.8, 0.15], ["alarm", "l03", 0.5, 0.8], ["alarm", "l03", 0.5, 1.6], ["alarm", "l03", 0.5, 2.4], ["alarm", "l04", 0.65, 0.1], ["alarm", "l04", 0.6, 0.9], ["alarm", "l04", 0.6, 1.7], ["alarm", "l04", 0.55, 2.5], ["alarm", "l04", 0.55, 3.3], ["alarm", "l05", 0.6, 0.2], ["alarm", "l05", 0.6, 1.0], ["alarm", "l05", 0.6, 1.8], ["alarm", "l05", 0.6, 2.6], ["alarm", "l05", 0.55, 3.4], ["radio", "l05", 0.6, 1.0], ["deep", "l06", 0.6, 0], ["breath", "l06", 0.1, 0], ["heart", "l07", 0.45, 0], ["scan", "l11", 0.3, 0.15], ["bolt", "l12", 0.5, 0.3]],
    "sfx_duck": 0.55,
    "music": {"style": "file_038", "sections": [["t0", 0.0, "f_15"], ["pov", -0.05, "f_mid"], ["l07", -0.3, "f_full"], ["l07m", 1.5, "f_mute"], ["l08", -0.05, "f_mid"], ["l13", -0.1, "f_low"]]},
    "segments": ["open", "pov", "ask", "exp", "after"],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "../ext/kit/pov.js", "work/blender/index.js", "../ext/blender/blframes.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 2.0], ["l00a", 0.6], ["l00b", 0.6], ["l01", 0.6], ["l02", 0.6], ["l03", 0.6], ["l04", 0.6], ["l05", 0.6], ["l06", 0.6], ["l07", 0.6], ["l08", 0.6], ["l08b", 0.6], ["l09", 0.6], ["l10", 0.6], ["l11", 0.6], ["l12", 0.6], ["l13", 0.6]],
    "scenes": [("0 open", None, "pov", "", ""), ("1 pov", "pov", "ask", "", ""), ("2 ask", "ask", "exp", "", ""), ("3 exp", "exp", "after", "", ""), ("4 after", "after", "endcard", "", ""), ("5 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- 設計：当事者設計（templates/DESIGN_MODES.md）。前半は当事者の目線（Blender の POV＋pov.js の揺れ・まばたき・ぼけ・息づかい）、後半は三人称の解説。", "- 文字は知的設計の字幕だけ（オープニングの問いは大きく）。", "- 顔は描かない。手は映してよい（ユーザー）。本物の画像は assets.md の権利の確かなものだけ。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
