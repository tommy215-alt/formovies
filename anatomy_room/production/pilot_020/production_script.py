#!/usr/bin/env python3
"""pilot_020「あと18キロ——スコットの南極点」（チャンネル「リバース」悲劇用＋ガイドライン v2.4）の制作スクリプト。

悲劇用（templates/DESIGN_MODES.md）：演出はハイテンションな勝負のテンション（器具は出さない、閃光なし）、中身は救いのない実話。
声は話速 1.5（聞き取れる限界近く、ユーザーの指示）。叫ぶ声は L08・L13 だけ（青山龍星「熱血」）。
BGM は外の曲（Kevin MacLeod「Blown Away」、CC BY 4.0）を production/ext/bgm_file.py で使う。場面のモードで音量を変え、人の死の場面は絞る。
処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。素材は assets/（scripts/pilot_020/assets.md）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE.parent / "ext"))
import pipeline  # noqa: E402
import standard  # noqa: E402
import music_ext  # noqa: E402,F401
import bgm_file  # noqa: E402
import ending_ext  # noqa: E402

ending_ext.apply(pipeline)   # 共通エンディングの短い版（この回の処理の中だけ）
bgm_file.register("file_blown_away", HERE / "assets" / "bgm" / "Blown Away.mp3", bpm=170)

V3 = ["../ext/vendor/three147/" + f for f in ["GLTFLoader.js", "RGBELoader.js", "Pass.js", "EffectComposer.js", "RenderPass.js", "ShaderPass.js",
                                               "CopyShader.js", "SimplexNoise.js", "SSAOShader.js", "SSAOPass.js", "BokehShader.js", "BokehPass.js"]]

EP = standard.config({
    "id": "pilot_020",
    "out": "reverse_020_scott.mp4",
    "cues": {
        "hook": ("L01", 0.0), "reveal": ("L01", 0.42), "race": ("L02", 0.0), "goal": ("L02", 0.55), "rival": ("L03", 0.0), "dogs": ("L03", 0.5),
        "haul": ("L04", 0.0), "pony": ("L04", 0.3), "manhaul": ("L04", 0.52),
        "pole": ("L05", 0.0), "blackflag": ("L05", 0.5), "tentp": ("L06", 0.0), "month": ("L06", 0.5), "diary": ("L07", 0.0), "awful": ("L07", 0.42),
        "turn": ("L08", 0.0), "turn2": ("L08", 0.35), "ret": ("L09", 0.0), "evans": ("L09", 0.5), "oates": ("L10", 0.0), "outside": ("L10", 0.35), "gone": ("L10", 0.85),
        "cold": ("L11", 0.0), "study": ("L11", 0.4), "fuel": ("L12", 0.0),
        "tent": ("L13", 0.0), "blizz": ("L14", 0.0), "ready": ("L14", 0.35), "noexit": ("L14", 0.7), "last": ("L15", 0.0), "lastw": ("L15", 0.4),
        "found": ("L16", 0.0), "rocks": ("L16", 0.45), "carried": ("L16", 0.78), "back": ("L17", 0.0), "cut": ("L17", 0.55),
    },
    "sfx": [("impact", "t0", 0.8, 0.02), ("wind", "t0", 0.6), ("riser", "t0", 0.5, 0.2), ("impact", "reveal", 1.0), ("hit", "reveal", 0.8, 0.03), ("stamp", "reveal", 0.8, 0.08), ("glitch", "reveal", 0.5, 0.2),
            ("whoosh", "race", 0.8), ("impact", "race", 0.7, 0.05), ("riser", "race", 0.5, 0.3), ("stamp", "goal", 0.9), ("hit", "goal", 0.7, 0.03), ("zoom", "goal", 0.5, 0.1),
            ("whoosh", "rival", 0.8), ("stamp", "rival", 0.7, 0.3), ("whoosh", "dogs", 0.9), ("hit", "dogs", 0.6, 0.05), ("whoosh", "dogs", 0.6, 0.4),
            ("machine", "haul", 0.6), ("brake", "haul", 0.7, 0.4), ("glitch", "haul", 0.5, 0.45), ("sweep_down", "pony", 0.5), ("impact", "manhaul", 1.0), ("stamp", "manhaul", 0.8, 0.05), ("step", "manhaul", 0.6, 0.3), ("step", "manhaul", 0.6, 0.65),
            ("riser", "pole", 0.7), ("wind", "pole", 0.4, 0.1), ("impact", "blackflag", 1.0), ("deep", "blackflag", 0.8, 0.05), ("glitch", "blackflag", 0.6, 0.15),
            ("impact", "tentp", 1.0), ("zoom", "tentp", 0.6, 0.03), ("stamp", "month", 0.9), ("hit", "month", 0.7, 0.03), ("sweep_down", "month", 0.6, 0.2),
            ("deep", "diary", 0.6), ("paper", "awful", 0.5),
            ("riser", "turn", 0.8), ("impact", "turn2", 1.0), ("whoosh", "turn2", 0.8, 0.03), ("hit", "turn2", 0.7, 0.05),
            ("wind", "ret", 0.5), ("deep", "evans", 0.7), ("wind", "oates", 0.5), ("step", "outside", 0.4), ("step", "outside", 0.4, 0.4), ("wind", "gone", 0.7), ("deep", "gone", 0.6, 0.1),
            ("sweep_down", "cold", 0.7), ("alarm", "cold", 0.5, 0.3), ("impact", "cold", 0.8, 0.45), ("glitch", "study", 0.5), ("data", "study", 0.5, 0.1),
            ("alarm", "fuel", 0.6), ("sweep_down", "fuel", 0.6, 0.3), ("brake", "fuel", 0.5, 0.8),
            ("riser", "tent", 0.8), ("impact", "tent", 1.0, 0.25), ("stamp", "tent", 1.0, 0.3), ("hit", "tent", 0.8, 0.33),
            ("wind", "blizz", 0.8), ("wind", "ready", 0.6), ("tick", "ready", 0.4, 0.2), ("tick", "ready", 0.4, 0.5), ("tick", "ready", 0.4, 0.8), ("brake", "noexit", 0.7), ("deep", "noexit", 0.6, 0.1),
            ("deep", "last", 0.5), ("paper", "lastw", 0.4),
            ("wind", "found", 0.5), ("discover", "rocks", 0.5), ("stamp", "rocks", 0.6, 0.1), ("deep", "carried", 0.5),
            ("rewind", "back", 0.6), ("wind", "back", 0.6, 0.1), ("brake", "cut", 0.8), ("deep", "cut", 0.8, 0.05)],
    # BGM：冒頭から勝負のテンション（全開）→ 南極点の写真で無音 → 振り向いて再び全開 → 帰り道（中）→ オーツ（小）→ 寒さと燃料（中）→「あと18キロ」（全開）
    #      → 吹雪（中）→ 最後の日記（無音）→ 発見と最後の一文（小）
    "music": {"style": "file_blown_away", "sections": [
        ("t0", 0.0, "f_full"), ("diary", -0.1, "f_mute"), ("turn", -0.05, "f_full"), ("ret", -0.1, "f_mid"), ("oates", -0.1, "f_low"), ("cold", -0.1, "f_mid"),
        ("tent", -0.05, "f_full"), ("blizz", 0.2, "f_mid"), ("last", -0.1, "f_mute"), ("found", -0.1, "f_low"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "race", "pole", "ret", "tent", "found"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js", "assets/assets.js", "assets/scene_assets.js"] + V3,
    "workers": 1,   # 3D が重い（pilot_017 で 2 本同時だとブラウザが落ちた）
    "qc_frames": [("t0", 0.3), ("reveal", 0.5), ("race", 0.6), ("goal", 0.4), ("rival", 0.3), ("dogs", 0.5), ("haul", 0.4), ("pony", 0.3), ("manhaul", 0.6),
                  ("pole", 0.5), ("blackflag", 0.4), ("tentp", 0.5), ("month", 0.5), ("diary", 0.6), ("awful", 0.8), ("turn", 0.3), ("turn2", 0.6),
                  ("ret", 0.5), ("evans", 0.6), ("oates", 0.6), ("outside", 0.8), ("gone", 0.4), ("cold", 0.5), ("study", 0.8), ("fuel", 0.8),
                  ("tent", 0.6), ("blizz", 0.6), ("ready", 0.8), ("noexit", 0.6), ("last", 0.5), ("lastw", 0.8), ("found", 0.6), ("rocks", 0.6), ("carried", 0.5),
                  ("back", 0.6), ("cut", 0.8)],
    "scenes": [
        ("1 冒頭（フック）", None, "race", "最初の 1 秒：吹雪の中ではためく黒い旗 → 一打で引くと、そりを引く 5 人の影", "f_full、一打"),
        ("2 競争", "race", "pole", "氷山の間を進む帆船 → 犬ぞりの疾走 → 止まる動力そり・消えるポニー → 人がそりを引く", "f_full"),
        ("3 南極点", "pole", "ret", "黒い旗 → 本物の写真 A2 →「1か月以上」→ 本物の写真 A1（無音）→ 振り向いて北へ（叫ぶ声）", "f_full → f_mute → f_full"),
        ("4 帰り道", "ret", "tent", "5 人が 4 人に → テントを出て吹雪へ消える後ろ姿 → 落ちる温度計 → 空になる燃料と食料", "f_mid → f_low → f_mid"),
        ("5 最後のテント", "tent", "found", "地図の「あと18km」（叫ぶ声）→ 吹雪に叩かれるテント、21 日 → 29 日 → ろうそくの光と最後の日記（無音）", "f_full → f_mid → f_mute"),
        ("6 発見と冒頭へ", "found", "endcard", "雪に埋もれたテント → 岩石標本と化石の葉 → 冒頭の旗、途切れた 18km の線", "f_low"),
        ("7 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（悲劇用＋ガイドライン v2.4）",
        "",
        "- 冒頭の最初の 1 秒：決定的な映像（吹雪の中ではためく黒い旗）。答えは言わない。",
        "- 悲劇用：ハイテンションなのは「勝負」の部分（冒頭〜L08、L13）。速い話速（1.5）・外の BGM（Blown Away、170 BPM）・叩きつける文字・ズームの一打と揺れ・派手な人とものの動き。ギャンブルの器具は出さない。閃光は使わない。",
        "- 人の死（L09・L10・L15）は BGM を絞り、効果音は低い音と風だけ。あざける演出はしない。最後の 2 行も絞ったまま、後味を残す。",
        "- 最後の一文（L17）と画を冒頭につなげる：吹雪の中の旗と、途中で途切れた 18km の線。",
        "- 本物の写真：アムンセンのテントの前のスコット隊（A2）と南極点の 5 人（A1）。どちらも Henry Bowers 撮影、パブリックドメイン。",
        "- ※注記は冒頭に 1 回だけ（ユーザーの設定）。地図は模式図。",
        "- 人物は MPFB の人体の後ろ姿・遠景・吹雪の中の影（顔なし、手のアップなし）。死の瞬間は見せない。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.5、抑揚 1.7、行間 0.03 秒。L08・L13 だけ VOICEVOX:青山龍星「熱血」。BGM：Kevin MacLeod「Blown Away」（CC BY 4.0）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
