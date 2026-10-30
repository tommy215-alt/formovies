#!/usr/bin/env python3
"""pilot_022「自分で細菌を飲んだ医師——ピロリ菌」（チャンネル「リバース」知的設計＋ガイドライン v2.4）の制作スクリプト。

知的設計（templates/DESIGN_MODES.md、参考 pilot_017）：落ち着いた科学ドキュメンタリー。字幕は S.docSub、見出しは uiCard、効果音はやわらかく、ゆっくりした寄り。
冒頭のオープニング（約 3 秒、ユーザーの指示）：結論の文字を大きく、W の声（冥鳴ひまり）が読み、本物の写真を中央、背景は動く CG、やさしい音（ext/opening_bgm.py のモード open_soft）。
共通エンディングは短い版（ending_ext）。BGM は lab_melodic（落ち着いた曲調。直前の知的設計は lab_dub）。
処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。素材は assets/（scripts/pilot_022/assets.md）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE.parent / "ext"))
import pipeline  # noqa: E402
import standard  # noqa: E402
import music_ext  # noqa: E402,F401
import opening_bgm  # noqa: E402,F401
import ending_ext  # noqa: E402

ending_ext.apply(pipeline)   # 共通エンディングの短い版（この回の処理の中だけ）

V3 = ["../ext/vendor/three147/" + f for f in ["GLTFLoader.js", "RGBELoader.js", "Pass.js", "EffectComposer.js", "RenderPass.js", "ShaderPass.js",
                                               "CopyShader.js", "SimplexNoise.js", "SSAOShader.js", "SSAOPass.js", "BokehShader.js", "BokehPass.js"]]

EP = standard.config({
    "id": "pilot_022",
    "out": "reverse_022_marshall.mp4",
    "cues": {
        "open": ("L00", 0.0), "hook": ("L01", 0.0), "drink": ("L01", 0.55), "acid": ("L02", 0.0), "notaccepted": ("L02", 0.62),
        "find": ("L03", 0.0), "spiral": ("L03", 0.5), "join": ("L04", 0.0), "nogrow": ("L04", 0.7),
        "grow": ("L05", 0.0), "easter": ("L05", 0.12), "colony": ("L05", 0.7), "reject": ("L06", 0.0), "stampc": ("L06", 0.55),
        "self": ("L07", 0.0), "decide": ("L08", 0.0), "days": ("L09", 0.0), "sick": ("L09", 0.3), "inflam": ("L09", 0.62),
        "proof": ("L10", 0.0), "bars": ("L10", 0.35), "nih": ("L11", 0.0), "nobel": ("L12", 0.0), "medal": ("L12", 0.35),
        "today": ("L13", 0.0), "back": ("L14", 0.0), "card": ("L14", 1.0),
    },
    "sfx": [("shimmer", "t0", 0.4, 0.05), ("glow", "t0", 0.4, 0.3),
            ("title", "hook", 0.8, 0.02), ("deep", "hook", 0.5, 0.05), ("zoom", "drink", 0.4), ("glow", "drink", 0.4, 0.3),
            ("whoosh", "acid", 0.5), ("scanline", "acid", 0.4, 0.4), ("tagpop", "acid", 0.4, 1.2), ("tagpop", "acid", 0.4, 1.6), ("deep", "notaccepted", 0.45),
            ("room", "find", 0.4), ("scan", "spiral", 0.5), ("lock", "spiral", 0.5, 0.6), ("paper", "join", 0.35), ("tick", "nogrow", 0.35), ("tick", "nogrow", 0.35, 0.6),
            ("flip", "easter", 0.4), ("flip", "easter", 0.35, 0.25), ("reveal", "colony", 0.6), ("bloom", "colony", 0.5, 0.2), ("paper", "reject", 0.35), ("stamp", "stampc", 0.55),
            ("deep", "self", 0.45), ("scanline", "self", 0.35, 0.4), ("room", "decide", 0.35), ("glow", "decide", 0.35, 0.8),
            ("tick", "days", 0.35), ("tick", "days", 0.35, 0.5), ("tick", "days", 0.35, 1.0), ("deep", "sick", 0.5), ("scan", "inflam", 0.45), ("data", "inflam", 0.4, 0.4),
            ("whoosh", "proof", 0.45), ("data", "bars", 0.45), ("ring", "bars", 0.35, 0.8), ("room", "nih", 0.35), ("paper", "nih", 0.3, 0.6),
            ("bloom", "medal", 0.6), ("discover", "medal", 0.5, 0.1), ("shimmer", "medal", 0.4, 0.5),
            ("glow", "today", 0.45), ("prism", "today", 0.35, 0.6), ("zoom", "back", 0.4, 0.4), ("shimmer", "card", 0.5), ("discover", "card", 0.4, 0.1)],
    # BGM：オープニングはやさしい音（open_soft）→ 冒頭（謎）→ 常識（陰り）→ 発見（物語）→ 培養（集中）→ 不採用（陰り）→ 自己実験（集中・間）→ 証明（高まり）→ ノーベル（発見）→ 現代（温かく）→ 冒頭へ
    "music": {"style": "lab_melodic", "sections": [
        ("t0", 0.0, "open_soft"), ("hook", -0.05, "w_hook"), ("notaccepted", -0.1, "w_shade"), ("find", -0.1, "w_story"), ("grow", -0.1, "w_focus"), ("colony", -0.1, "w_discover"),
        ("reject", -0.1, "w_shade"), ("self", -0.1, "w_focus"), ("sick", -0.15, "w_hold"), ("proof", -0.1, "w_rise"), ("medal", -0.1, "w_discover"),
        ("today", -0.1, "w_warm"), ("back", -0.1, "w_hook"), ("end1", -0.6, "ending")]},
    "segments": ["open", "hook", "find", "grow", "self", "proof", "today"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js", "assets/assets.js", "assets/scene_assets.js"] + V3,
    "workers": 1,
    "qc_frames": [("open", 0.4), ("open", 2.0), ("hook", 0.5), ("drink", 0.6), ("acid", 1.0), ("notaccepted", 0.8), ("find", 0.8), ("spiral", 0.8), ("join", 0.8), ("nogrow", 0.6),
                  ("easter", 0.6), ("colony", 0.8), ("reject", 0.6), ("stampc", 0.5), ("self", 0.8), ("decide", 1.0), ("days", 0.6), ("sick", 0.8), ("inflam", 0.8),
                  ("proof", 0.6), ("bars", 1.0), ("nih", 1.0), ("medal", 0.8), ("today", 1.0), ("back", 1.0), ("card", 0.3)],
    "scenes": [
        ("0 オープニング（約 3 秒）", None, "hook", "結論の文字を大きく、本物の写真（A1：ピロリ菌の電子顕微鏡写真）を中央、背景はゆっくり漂う菌の 3D。やさしい音", "open_soft"),
        ("1 冒頭（フック）", "hook", "find", "最初の 1 秒：実験台の上の濁った液体の小瓶（再現）→ 酸の満ちた胃の 3D、ストレス・胃酸の札", "w_hook → w_shade"),
        ("2 発見", "find", "grow", "顕微鏡をのぞく後ろ姿 → 視野の中のらせん形の菌（模式）→ 何も生えない培養皿", "w_story"),
        ("3 培養と不採用", "grow", "self", "連休の暦 → 培養皿に広がる菌のコロニー → 不採用の判", "w_focus → w_discover → w_shade"),
        ("4 自分の胃で", "self", "proof", "「原因？」→ 小瓶を前にした後ろ姿（手のアップなし）→ 日付 → 赤く腫れる胃（模式）。まねしないで、の注意", "w_focus → w_hold"),
        ("5 証明", "proof", "today", "除菌の模式図 → 会議の机（顔なし）→ メダルの光（再現）", "w_rise → w_discover"),
        ("6 現代と冒頭へ", "today", "endcard", "元の色に戻る胃 → 冒頭の小瓶", "w_warm → w_hook"),
        ("7 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（知的設計＋ガイドライン v2.4＋オープニング）",
        "",
        "- オープニング：結論の文字を画面の上〜中ほどに大きく、W の声ではっきり読む。本物の写真（ピロリ菌の電子顕微鏡写真、CC BY 4.0）を中央に。背景は動く CG。やさしい音。",
        "- 冒頭（本編）の最初の 1 秒：実験台の上の濁った液体の小瓶（決定的な映像）。",
        "- 知的設計：字幕は S.docSub、見出しは uiCard、効果音はやわらかく、ゆっくりした寄り。決定的な瞬間（菌のコロニーが広がる、胃が腫れる）だけ光の転換。",
        "- 最後の一文と画を冒頭につなげる：小瓶に戻る。",
        "- 人物は MPFB の人体の後ろ姿（顔なし、手のアップなし）。マーシャル・ウォレンの写真は CC BY-SA なので使わない。",
        "- 自己実験はまねしないよう、L01〜L09 の画面に注意書き。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.15、行間 0.05 秒。オープニングだけ VOICEVOX:冥鳴ひまり。BGM：lab_melodic。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
