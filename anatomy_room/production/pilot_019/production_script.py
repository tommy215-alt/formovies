#!/usr/bin/env python3
"""pilot_019「海の上の時計——ジョン・ハリソン」（チャンネル「リバース」ドパ設計＋ガイドライン v2.4）の制作スクリプト。

ドパ設計（templates/DESIGN_MODES.md）：叩きつける文字（slam）・跳ねる字幕（popSub）・画面の一打。閃光は使わない（2026-10-30 ユーザー「まぶしい」）。
叫ぶ声は要所の 2 行（L01・L10）だけ：lines.json の voice_override に style "shout"＝VOICEVOX:青山龍星「熱血」。
処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。
テンプレートの外の部品（production/ext/）：BGM lab_electro と効果音（music_ext.py・bgm_lab.py）、注目のアイコンと短いエンディング（hud_ext.js・ending_ext.py）、
three.js r147 の読み込みと仕上げの部品（ext/vendor/three147/）。素材は assets/（scripts/pilot_019/assets.md）。
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
    "id": "pilot_019",
    "out": "reverse_019_harrison.mp4",
    "cues": {
        "hook": ("L01", 0.0), "crash": ("L01", 0.17), "crash2": ("L01", 0.7), "storm": ("L02", 0.0), "chart": ("L02", 0.3), "lost": ("L02", 0.66),
        "lon": ("L03", 0.0), "lonq": ("L03", 0.5), "prize": ("L04", 0.0), "money": ("L04", 0.62),
        "key": ("L05", 0.0), "diff": ("L05", 0.55), "drift": ("L06", 0.0), "heat": ("L06", 0.55),
        "harrison": ("L07", 0.0), "portrait": ("L07", 0.55), "h1": ("L08", 0.0), "h2": ("L08", 0.12), "h3": ("L08", 0.24), "years": ("L08", 0.62),
        "noans": ("L09", 0.0), "h4": ("L10", 0.0), "small": ("L10", 0.5), "watch": ("L11", 0.0), "plate": ("L11", 0.45),
        "trial": ("L12", 0.0), "arrive": ("L12", 0.62), "board": ("L13", 0.0), "pay": ("L14", 0.0), "pay2": ("L14", 0.22), "none": ("L14", 0.55),
        "today": ("L15", 0.0), "gps": ("L15", 0.5), "back": ("L16", 0.0), "answer": ("L16", 0.45),
    },
    "sfx": [("impact", "t0", 0.8, 0.02), ("wind", "t0", 0.5, 0.0), ("riser", "t0", 0.5, 0.3), ("impact", "crash", 1.0), ("hit", "crash", 0.8, 0.03), ("deep", "crash", 0.7, 0.05), ("glitch", "crash", 0.4, 0.3), ("impact", "crash2", 0.9), ("stamp", "crash2", 0.7, 0.05),
            ("wind", "storm", 0.4), ("data", "chart", 0.5), ("tagpop", "chart", 0.6, 0.4), ("tagpop", "chart", 0.6, 0.9), ("stamp", "lost", 0.9), ("deep", "lost", 0.6, 0.05),
            ("whoosh", "lon", 0.7), ("zap", "lon", 0.4, 0.4), ("glitch", "lonq", 0.6), ("brake", "lonq", 0.4, 0.1),
            ("whoosh", "prize", 0.6), ("stamp", "prize", 0.6, 0.6), ("impact", "money", 1.0), ("hit", "money", 0.6, 0.05), ("prism", "money", 0.5, 0.2),
            ("tick", "key", 0.6), ("tick", "key", 0.6, 0.5), ("gear", "key", 0.5, 0.8), ("zoom", "diff", 0.6), ("tagpop", "diff", 0.6, 0.3), ("ok", "diff", 0.5, 0.8),
            ("brake", "drift", 0.5), ("glitch", "drift", 0.6, 0.4), ("tick", "drift", 0.4, 0.8), ("tick", "drift", 0.4, 1.1), ("alarm", "heat", 0.4), ("glitch", "heat", 0.7, 0.2),
            ("room", "harrison", 0.5), ("step", "harrison", 0.4, 0.3), ("impact", "portrait", 0.8), ("zoom", "portrait", 0.5, 0.05),
            ("stamp", "h1", 0.8), ("gear", "h1", 0.5, 0.05), ("stamp", "h2", 0.8), ("gear", "h2", 0.5, 0.05), ("stamp", "h3", 0.9), ("gear", "h3", 0.5, 0.05),
            ("rewind", "years", 0.5), ("typer", "years", 0.5, 0.1), ("impact", "years", 0.9, 0.3),
            ("sweep_down", "noans", 0.5), ("deep", "noans", 0.6, 0.2),
            ("riser", "h4", 0.6), ("whoosh", "small", 0.8), ("impact", "small", 1.0, 0.1), ("discover", "small", 0.9, 0.15), ("shimmer", "small", 0.6, 0.4),
            ("gear", "watch", 0.5), ("tick", "watch", 0.5, 0.4), ("tick", "watch", 0.5, 0.8), ("tick", "watch", 0.5, 1.2), ("zoom", "plate", 0.6), ("paper", "plate", 0.5, 0.05),
            ("whoosh", "trial", 0.7), ("sweep_up", "trial", 0.4, 0.5), ("data", "trial", 0.4, 1.0), ("impact", "arrive", 1.0), ("stamp", "arrive", 0.7, 0.05), ("ok", "arrive", 0.5, 0.2),
            ("room", "board", 0.4), ("paper", "board", 0.5, 0.4), ("stamp", "board", 0.8, 1.2),
            ("stamp", "pay", 0.7), ("stamp", "pay2", 0.7), ("brake", "none", 0.6), ("deep", "none", 0.6, 0.1),
            ("whoosh", "today", 0.6), ("wind", "today", 0.3, 0.2), ("zap", "gps", 0.6), ("data", "gps", 0.5, 0.2), ("tagpop", "gps", 0.6, 0.6),
            ("rewind", "back", 0.6), ("wind", "back", 0.4, 0.1), ("whoosh", "answer", 0.7), ("discover", "answer", 0.6, 0.1)],
    # BGM：嵐（緊張）→ 経度の謎（物語）→ 狂う時計（陰り）→ 工房（集中）→ H3 の行き詰まり（間）→ 発想の転換（発見）→ 試験（集中）→ 委員会（陰り）→ 現代（温かく）→ 冒頭のモードへ
    "music": {"style": "lab_electro", "sections": [
        ("t0", 0.0, "w_hook"), ("lon", -0.1, "w_story"), ("drift", -0.1, "w_shade"), ("harrison", -0.1, "w_focus"), ("noans", -0.15, "w_hold"),
        ("h4", -0.1, "w_rise"), ("small", -0.05, "w_discover"), ("trial", -0.1, "w_focus"), ("board", -0.1, "w_shade"), ("today", -0.1, "w_warm"),
        ("back", -0.1, "w_hook"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "lon", "harrison", "h4", "trial", "today"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js", "assets/assets.js", "assets/scene_assets.js"] + V3,
    "workers": 1,   # 3D が重い（pilot_017 で 2 本同時だとブラウザが落ちた）
    "qc_frames": [("t0", 0.3), ("crash", 0.2), ("crash", 0.8), ("crash2", 0.5), ("chart", 0.8), ("lost", 0.5), ("lon", 1.0), ("lonq", 0.5), ("prize", 0.8), ("money", 0.5),
                  ("key", 0.8), ("diff", 0.8), ("drift", 0.8), ("heat", 0.5), ("harrison", 1.0), ("portrait", 0.6), ("h1", 0.2), ("h3", 0.3), ("years", 0.5),
                  ("noans", 1.0), ("h4", 0.6), ("small", 0.6), ("watch", 1.0), ("plate", 0.8), ("trial", 1.5), ("arrive", 0.5), ("board", 1.2),
                  ("pay2", 0.5), ("none", 1.0), ("today", 1.0), ("gps", 1.0), ("back", 1.0), ("answer", 1.2)],
    "scenes": [
        ("1 冒頭（フック）", None, "lon", "最初の 1 秒：嵐の夜、帆船が岩に激突（スロー・一打）→ 海図の推定位置と本当の位置 →「1300人以上」", "w_hook、一打"),
        ("2 経度の謎", "lon", "harrison", "緯線は光り経線は消える地球 → 金貨と「£20,000」→ 2 つの時計の時差 → 揺れて狂う振り子時計", "w_story → w_shade"),
        ("3 ハリソン", "harrison", "h4", "木の工房の後ろ姿 → 本物の肖像（A2）→ H1・H2・H3 の一打 →「19年」→ 巨大な H3 の前の後ろ姿", "w_focus → w_hold"),
        ("4 発想の転換", "h4", "trial", "決定的な瞬間：H4 が回り込んで現れる（速い寄り・光の転換、閃光なし）→ H4 の回転 → 1767 年の図版（A1）", "w_rise → w_discover"),
        ("5 試験と賞金", "trial", "today", "大西洋の航路 →「5秒」→ 委員会の長い机 → 金額の札と空の 2 万ポンド", "w_focus → w_shade"),
        ("6 現代と冒頭へ", "today", "endcard", "クックの帆船 → GPS の衛星 → 嵐の海から H4 の文字盤へ（冒頭とつながる）", "w_warm → w_hook"),
        ("7 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（ドパ設計＋ガイドライン v2.4）",
        "",
        "- 冒頭の最初の 1 秒：決定的な映像（嵐の夜、帆船が岩に激突）。答えは言わない。",
        "- ドパ設計：叩きつける大きな文字（Dela Gothic One・Mochiy Pop One、OFL）、跳ねる字幕、ズームの一打・揺れ・グリッチ・スピード線、効果音を多めに。**閃光は使わない**（場面の切り替えは一打と短い暗転）。",
        "- 決定的な瞬間（L10）：巨大な H3 から一気に寄り、小さな H4 が回り込んで現れる。冷たい光から金色の光へ。",
        "- 最後の一文（L16）と画を冒頭につなげる：嵐の海に戻り、H4 の文字盤へ。",
        "- 本物の写真・図：ハリソンの肖像の版画（A2）と 1767 年の H4 の図版（A1）。",
        "- ※注記は冒頭に 1 回だけ（ユーザーの設定）。",
        "- 人物は MPFB の人体の後ろ姿・遠景（顔なし、手のアップなし）。H1〜H4・帆船は再現 CG。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.15、行間 0.05 秒。L01・L10 だけ VOICEVOX:青山龍星「熱血」（抑揚 1.5）。BGM：lab_electro（B06・短調）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
