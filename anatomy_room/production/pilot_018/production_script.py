#!/usr/bin/env python3
"""pilot_018「パスツールと少年——狂犬病のワクチン」（チャンネル「リバース」標準ルール v8・ガイドライン v2.4）の制作スクリプト。

この回だけの試し（ユーザーの指示 2026-10-29）：演出と文字を派手に。反応を見て、標準にするか決める。
処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。
テンプレートの外の部品（production/ext/）：BGM lab_break と効果音（music_ext.py・bgm_lab.py）、注目のアイコンと短いエンディング（hud_ext.js・ending_ext.py）、
three.js r147 の読み込みと仕上げの部品（ext/vendor/three147/）。素材は assets/（scripts/pilot_018/assets.md）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE.parent / "ext"))
import pipeline  # noqa: E402
import standard  # noqa: E402
import music_ext  # noqa: E402,F401
import ending_ext  # noqa: E402

ending_ext.apply(pipeline)   # 共通エンディングの短い版（この回の処理の中だけ）

V3 = ["../ext/vendor/three147/" + f for f in ["GLTFLoader.js", "RGBELoader.js", "Pass.js", "EffectComposer.js", "RenderPass.js", "ShaderPass.js",
                                               "CopyShader.js", "SimplexNoise.js", "SSAOShader.js", "SSAOPass.js", "BokehShader.js", "BokehPass.js"]]

EP = standard.config({
    "id": "pilot_018",
    "out": "reverse_018_pasteur.mp4",
    "cues": {
        "hook": ("L01", 0.0), "pull": ("L01", 0.12), "boy": ("L01", 0.45),
        "bite": ("L02", 0.0), "num14": ("L02", 0.68), "deadly": ("L03", 0.0), "deadly2": ("L03", 0.45),
        "paris": ("L04", 0.0), "portrait": ("L05", 0.0), "jars": ("L05", 0.42),
        "risk": ("L06", 0.0), "scale": ("L06", 0.42), "notdoc": ("L07", 0.0), "notdoc2": ("L07", 0.45),
        "inject": ("L08", 0.0), "date": ("L08", 0.47), "shot": ("L08", 0.62), "days": ("L09", 0.0), "ten": ("L09", 0.55),
        "saved": ("L10", 0.0), "dawn": ("L10", 0.4), "academy": ("L11", 0.0),
        "world": ("L12", 0.0), "inst": ("L13", 0.0), "gate": ("L14", 0.0),
        "today": ("L15", 0.0), "prevent": ("L15", 0.55), "back": ("L16", 0.0), "card": ("L16", 1.0),
    },
    "sfx": [("impact", "t0", 0.8, 0.02), ("title", "t0", 0.9, 0.02), ("whoosh", "pull", 0.8), ("hit", "pull", 0.6, 0.05), ("riser", "pull", 0.4, 0.4), ("stamp", "boy", 0.7), ("glitch", "boy", 0.4, 0.4),
            ("whoosh", "bite", 0.6), ("wind", "bite", 0.4, 0.2), ("impact", "num14", 0.9), ("stamp", "num14", 0.7, 0.05), ("alarm", "num14", 0.35, 0.3),
            ("deep", "deadly", 0.7), ("glitch", "deadly", 0.6, 0.1), ("hit", "deadly2", 0.8), ("zap", "deadly2", 0.4, 0.1),
            ("whoosh", "paris", 0.7), ("machine", "paris", 0.4, 0.1), ("sweep_up", "paris", 0.4, 1.2),
            ("impact", "portrait", 0.8), ("zoom", "portrait", 0.6, 0.05), ("tagpop", "jars", 0.6), ("tagpop", "jars", 0.55, 0.25), ("tagpop", "jars", 0.55, 0.5), ("tagpop", "jars", 0.55, 0.75),
            ("paper", "risk", 0.5), ("zoom", "risk", 0.5, 0.1), ("gear", "scale", 0.5), ("tick", "scale", 0.4, 0.4), ("tick", "scale", 0.4, 0.8),
            ("brake", "notdoc", 0.6), ("impact", "notdoc2", 0.9), ("stab", "notdoc2", 0.6, 0.05), ("glitch", "notdoc2", 0.4, 0.2),
            ("tick", "inject", 0.6), ("tick", "inject", 0.6, 0.5), ("tick", "inject", 0.6, 1.0), ("riser", "inject", 0.5, 0.8), ("stamp", "date", 0.9), ("impact", "shot", 0.9), ("hit", "shot", 0.6, 0.05),
            ("rewind", "days", 0.5), ("typer", "days", 0.6, 0.2), ("tick", "days", 0.4, 0.4), ("tick", "days", 0.4, 0.7), ("tick", "days", 0.4, 1.0), ("tick", "days", 0.4, 1.3), ("stamp", "ten", 0.9), ("impact", "ten", 0.6, 0.02),
            ("sweep_down", "saved", 0.4), ("discover", "dawn", 0.9), ("bloom", "dawn", 0.9, 0.05), ("shimmer", "dawn", 0.6, 0.3),
            ("room", "academy", 0.4), ("hit", "academy", 0.5, 0.5), ("hit", "academy", 0.4, 0.8), ("hit", "academy", 0.4, 1.1),
            ("whoosh", "world", 0.7), ("zap", "world", 0.4, 0.3), ("zap", "world", 0.4, 0.6), ("zap", "world", 0.4, 0.9), ("prism", "world", 0.6, 1.2),
            ("impact", "inst", 0.8), ("stamp", "inst", 0.6, 0.05), ("unroll", "inst", 0.5, 0.4), ("step", "gate", 0.4), ("glow", "gate", 0.5, 0.3),
            ("deep", "today", 0.7), ("data", "today", 0.6, 0.3), ("impact", "prevent", 0.8), ("ok", "prevent", 0.6, 0.1),
            ("rewind", "back", 0.7), ("whoosh", "back", 0.6, 0.2), ("impact", "card", 0.6), ("discover", "card", 0.4, 0.1)],
    # BGM：冒頭（緊張）→ かまれた（陰り）→ パリへ（物語）→ 迷い（陰り）→ 注射（集中・高まり）→ 発病しない（発見）→ 世界へ（温かく）→ 現代（集中）→ 冒頭のモードへ戻す
    "music": {"style": "lab_break", "sections": [
        ("t0", 0.0, "w_hook"), ("bite", -0.1, "w_shade"), ("paris", -0.1, "w_story"), ("risk", -0.1, "w_shade"), ("inject", -0.1, "w_focus"),
        ("saved", -0.15, "w_hold"), ("dawn", -0.1, "w_discover"), ("world", -0.1, "w_warm"), ("today", -0.1, "w_focus"), ("back", -0.1, "w_hook"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "bite", "paris", "risk", "inject", "saved", "world", "today"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js", "assets/assets.js", "assets/scene_assets.js"] + V3,
    "workers": 1,   # 3D が重い（pilot_017 で 2 本同時だとブラウザが落ちた）
    "qc_frames": [("t0", 0.3), ("pull", 0.6), ("boy", 0.8), ("bite", 1.0), ("num14", 0.6), ("deadly2", 0.6), ("paris", 1.0), ("portrait", 0.8), ("jars", 1.0),
                  ("risk", 0.8), ("scale", 1.0), ("notdoc2", 0.4), ("date", 0.4), ("shot", 0.5), ("days", 1.0), ("ten", 0.5), ("saved", 0.6), ("dawn", 0.8),
                  ("academy", 1.5), ("world", 1.5), ("inst", 1.0), ("gate", 1.5), ("today", 1.5), ("prevent", 0.8), ("back", 1.5), ("card", 0.3)],
    "scenes": [
        ("1 冒頭（フック）", None, "bite", "最初の 1 秒：琥珀色の光、瓶に吊られた脊髄（再現）→ 一打で引くと少年の後ろ姿、巨大な文字", "w_hook、一打"),
        ("2 かまれた", "bite", "paris", "夕暮れの村と犬の影 →「14か所」が叩きつけられる → 赤く脈打つ神経", "w_shade"),
        ("3 パリへ", "paris", "risk", "夜汽車の光とスピード線 → 本物の肖像写真（A1）→ 瓶の列と日数の札", "w_story"),
        ("4 迷い", "risk", "inject", "本物の 1885 年の版画（A2）→ 揺れる天秤 →「医師じゃない」", "w_shade"),
        ("5 10 日間", "inject", "saved", "時計のスロー → 7月6日・最初の注射の一打 → 10 日の暦の早回し", "w_focus"),
        ("6 発病しなかった", "saved", "world", "無音 → 朝の光の大転換 → 講堂", "w_hold → w_discover"),
        ("7 世界へ", "world", "today", "地球儀に世界からパリへ光の線 → 研究所の扉 → 門に立つ後ろ姿", "w_warm"),
        ("8 現代と冒頭へ", "today", "endcard", "世界地図の光の点 →「防げる」→ 冒頭の瓶と少年に戻る", "w_focus → w_hook"),
        ("9 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（標準ルール v8・ガイドライン v2.4＋この回だけの「派手」の試し）",
        "",
        "- 冒頭の最初の 1 秒：決定的な映像（琥珀色の光の中、瓶に吊られた脊髄）。答えは言わない。",
        "- 派手さの試し：画面に叩きつける大きな文字（Dela Gothic One・Mochiy Pop One、OFL）、跳ねる字幕、ズームの一打・揺れ・閃光・スピード線・色の切り替え、効果音を多めに。",
        "- 最後の一文（L16）と画を冒頭につなげる：瓶と少年の後ろ姿に戻る。",
        "- 本物の写真・図：パスツールの肖像（A1）と 1885 年の版画（A2）。",
        "- ※注記は冒頭に 1 回だけ（ユーザーの設定）。",
        "- 人物は MPFB の人体の後ろ姿・遠景（顔なし、手のアップなし）。かまれる瞬間・注射の瞬間は直接見せない（影・音・一打で表す）。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.15、行間 0.05 秒。BGM：lab_break（B08 Breakbeat・短調）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
