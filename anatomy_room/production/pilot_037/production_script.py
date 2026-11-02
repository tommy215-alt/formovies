#!/usr/bin/env python3
"""pilot_037「あなたならどうする？——密林に、ひとり（ジュリアン・ケプケ）」（チャンネル「リバース」当事者設計、シリーズ「あなたならどうする？」）の制作スクリプト。

台本は scripts/pilot_037/script_draft.md（2026-11-02 にユーザーが「OK」）、事実は fact_check.md、画像・曲・効果音は assets.md。
BGM は Kevin MacLeod「The Escalation」（incompetech、CC BY 4.0）。環境音・効果音は Freesound の CC0（ext/ambience.py）。
3D の場面は Blender（blender/scene.py → work/blender、ext/blender）。目線の演出は ext/kit/pov.js。
オープニングは状況と 2 択だけを冥鳴ひまりが読み、その場の環境音（雨・息づかい・砂嵐など）を強く出す。問いのあとは BGM を止めて心臓の音だけ。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("The Escalation.mp3", 96))
import noend_ext  # noqa: E402
noend_ext.apply(pipeline, black=1.8)   # 当事者設計は共通エンディングなし（2026-11-02、ユーザー「エンディングは不要」）。最後は暗転
import ambience  # noqa: E402

ambience.timeline(HERE / "work" / "timeline.json")
ambience.register("open_rain", HERE / "assets/sfx/jungle_rain.mp3", start=20, span=('l00', 'l01', 0.2), norm="rms")
ambience.register("open_breath", HERE / "assets/sfx/breath_f.mp3", start=0, span=('l00', 'l01', 0.2), norm="rms")
ambience.register("heart", HERE / "assets/sfx/heartbeat.mp3", start=2, dur=6, norm="rms")
ambience.register("cabin", HERE / "assets/sfx/prop_interior.mp3", start=3, span=('l01', 'l04', 0.1), norm="rms")
ambience.register("bolt", HERE / "assets/sfx/lightning.mp3", start=0, dur=5, norm="peak")
ambience.register("fallwind", HERE / "assets/sfx/wind.mp3", start=30, span=('l04', 'l05', 0.1), norm="rms")
ambience.register("jungle", HERE / "assets/sfx/forest_night.mp3", start=10, span=('l05', 'l08', 0.2), norm="rms")
ambience.register("rain", HERE / "assets/sfx/jungle_rain.mp3", start=60, span=('l05', 'end', 0), norm="rms")
ambience.register("stream", HERE / "assets/sfx/stream.mp3", start=5, span=('l08', 'end', 0), norm="rms")
ambience.register("breath", HERE / "assets/sfx/breath_f.mp3", start=0, dur=7, norm="rms")
ambience.register("sniff", HERE / "assets/sfx/sniff.mp3", start=0, dur=None, norm="peak")

EP = standard.config({
    "id": "pilot_037",
    "out": "reverse_037_koepcke.mp4",
    "cues": {"open": ["L00", 0.0], "pov": ["L01", 0.0], "ask": ["L08", 0.0], "exp": ["L09", 0.0], "after": ["L14", 0.0], "l00": ["L00", 0.0], "l00m": ["L00", 0.5], "l01": ["L01", 0.0], "l01m": ["L01", 0.5], "l02": ["L02", 0.0], "l02m": ["L02", 0.5], "l03": ["L03", 0.0], "l03m": ["L03", 0.5], "l04": ["L04", 0.0], "l04m": ["L04", 0.5], "l05": ["L05", 0.0], "l05m": ["L05", 0.5], "l06": ["L06", 0.0], "l06m": ["L06", 0.5], "l07": ["L07", 0.0], "l07m": ["L07", 0.5], "l08": ["L08", 0.0], "l08m": ["L08", 0.5], "l09": ["L09", 0.0], "l09m": ["L09", 0.5], "l10": ["L10", 0.0], "l10m": ["L10", 0.5], "l11": ["L11", 0.0], "l11m": ["L11", 0.5], "l12": ["L12", 0.0], "l12m": ["L12", 0.5], "l13": ["L13", 0.0], "l13m": ["L13", 0.5], "l14": ["L14", 0.0], "l14m": ["L14", 0.5]},
    "sfx": [["open_rain", "l00", 1.6, 0], ["open_breath", "l00", 1.3, 0], ["heart", "l00", 1.0, 0], ["sniff", "l00", 0.8, 2.6], ["cabin", "l01", 1.2, 0], ["bolt", "l02", 1.0, 0.5], ["deep", "l02", 0.7, 0.3], ["bolt", "l03", 0.7, 1.2], ["riser", "l03", 0.5, 0.2], ["fallwind", "l04", 1.4, 0], ["heart", "l04", 0.8, 1.0], ["jungle", "l05", 1.1, 0], ["rain", "l05", 0.6, 0], ["breath", "l05", 0.9, 0.3], ["breath", "l07", 0.7, 0], ["heart", "l08", 1.2, 0], ["stream", "l08", 1.0, 0]],
    "sfx_duck": 0.55,
    "music": {"style": "file_037", "sections": [["t0", 0.0, "f_15"], ["pov", -0.05, "f_mid"], ["l08", -0.3, "f_full"], ["l08m", 1.5, "f_mute"], ["l09", -0.05, "f_mid"], ["l14", -0.1, "f_low"]]},
    "segments": ["open", "pov", "ask", "exp", "after"],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "../ext/kit/pov.js", "work/blender/index.js", "../ext/blender/blframes.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 2.0], ["l01", 0.6], ["l02", 0.6], ["l03", 0.6], ["l04", 0.6], ["l05", 0.6], ["l06", 0.6], ["l07", 0.6], ["l08", 0.6], ["l09", 0.6], ["l10", 0.6], ["l11", 0.6], ["l12", 0.6], ["l13", 0.6], ["l14", 0.6]],
    "scenes": [("0 open", None, "pov", "", ""), ("1 pov", "pov", "ask", "", ""), ("2 ask", "ask", "exp", "", ""), ("3 exp", "exp", "after", "", ""), ("4 after", "after", "endcard", "", ""), ("5 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- 設計：当事者設計（templates/DESIGN_MODES.md）。前半は当事者の目線（Blender の POV＋pov.js の揺れ・まばたき・ぼけ・息づかい）、後半は三人称の解説。", "- 文字は知的設計の字幕だけ（オープニングの問いは大きく）。", "- 顔は描かない。手は映してよい（ユーザー）。本物の画像は assets.md の権利の確かなものだけ。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
