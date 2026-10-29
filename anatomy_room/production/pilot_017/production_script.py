#!/usr/bin/env python3
"""pilot_017「宇宙の物差し——ヘンリエッタ・スワン・リービット」（チャンネル「リバース」標準ルール v8・ガイドライン v2.4）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。
テンプレートの外の部品（production/ext/）：BGM lab_dub と効果音（music_ext.py・bgm_lab.py）、注目のアイコンと短いエンディングの画面（hud_ext.js）、
短いエンディングの間（ending_ext.py）、three.js r147 の読み込みと仕上げの部品（ext/vendor/three147/）。
本物の写真・図は assets/（scripts/pilot_017/assets.md）。3D の素材（MPFB の人体・Poly Haven の HDRI と質感、CC0）は assets/scene_assets.js。
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
    "id": "pilot_017",
    "out": "reverse_017_leavitt.mp4",
    "cues": {
        "hook": ("L01", 0.0), "pull": ("L01", 0.16), "q": ("L02", 0.0),
        "problem": ("L03", 0.0), "reveal": ("L03", 0.42), "nomethod": ("L03", 0.78),
        "harvard": ("L04", 0.0), "women": ("L04", 0.42), "plates": ("L04", 0.72), "photo": ("L05", 0.0), "empty": ("L05", 0.55),
        "find": ("L06", 0.0), "count": ("L06", 0.45), "notice": ("L07", 0.0), "pulse": ("L07", 0.3),
        "line": ("L08", 0.0), "draw": ("L08", 0.45), "fig": ("L08", 0.86), "same": ("L09", 0.0), "true": ("L09", 0.55),
        "ruler": ("L10", 0.0), "ticks": ("L10", 0.5), "death": ("L11", 0.0),
        "hubble": ("L12", 0.0), "var": ("L12", 0.5), "jump": ("L13", 0.0), "galaxy": ("L13", 0.62),
        "letter": ("L14", 0.0), "chair": ("L14", 0.64),
        "today": ("L15", 0.0), "back": ("L16", 0.0), "card": ("L16", 1.0),
    },
    "sfx": [("title", "t0", 1.0, 0.02), ("impact", "t0", 0.6, 0.02), ("deep", "t0", 0.5, 0.05), ("whoosh", "pull", 0.7), ("shimmer", "pull", 0.5, 0.3),
            ("whoosh", "q", 0.6), ("zoom", "q", 0.4, 0.4),
            ("scanline", "problem", 0.5), ("tagpop", "reveal", 0.55), ("tagpop", "reveal", 0.55, 0.35), ("deep", "nomethod", 0.5), ("error", "nomethod", 0.35, 0.3),
            ("room", "harvard", 0.4), ("whoosh", "harvard", 0.4, -0.1), ("paper", "women", 0.35), ("flip", "plates", 0.45), ("ring", "plates", 0.35, 0.4),
            ("zoom", "photo", 0.5), ("paper", "photo", 0.3, 0.3), ("deep", "empty", 0.45),
            ("glow", "find", 0.5), ("scan", "find", 0.4, 0.5), ("data", "count", 0.6), ("typer", "count", 0.45, 0.3), ("tagpop", "count", 0.4, 0.8), ("stamp", "count", 0.55, 1.6),
            ("deep", "notice", 0.6), ("tick", "pulse", 0.45), ("tick", "pulse", 0.35, 1.1), ("tick", "pulse", 0.45, 2.0),
            ("reveal", "line", 0.5), ("tagpop", "line", 0.3, 0.3), ("tagpop", "line", 0.3, 0.6), ("lock", "draw", 0.8), ("bloom", "draw", 0.7, 0.1),
            ("zoom", "fig", 0.5), ("paper", "fig", 0.35, 0.2), ("scanline", "same", 0.5), ("ring", "true", 0.5), ("data", "true", 0.45, 0.3),
            ("whoosh", "ruler", 0.7), ("prism", "ruler", 0.5, 0.3), ("tagpop", "ticks", 0.4), ("tagpop", "ticks", 0.4, 0.4), ("tagpop", "ticks", 0.4, 0.8),
            ("deep", "death", 0.6),
            ("ship", "hubble", 0.5), ("deep", "hubble", 0.5, 0.4), ("pencil", "var", 0.6), ("stamp", "var", 0.8, 0.9),
            ("whoosh", "jump", 0.9), ("zoom", "jump", 0.6, 0.3), ("bloom", "galaxy", 0.9), ("glow", "galaxy", 0.5, 0.5),
            ("paper", "letter", 0.5), ("flip", "letter", 0.4, 0.6), ("deep", "chair", 0.5),
            ("whoosh", "today", 0.5), ("data", "today", 0.45, 1.0), ("glow", "back", 0.5), ("zoom", "back", 0.5, 0.8), ("shimmer", "card", 0.5), ("discover", "card", 0.4, 0.1)],
    # BGM：冒頭（謎）→ 問題（陰り）→ 天文台（物語）→ 発見（集中）→ 線が走る（発見）→ 物差し（集中）→ 死（間）→ ハッブル（高まり）→ 手紙（陰り）→ 現代（温かく）→ 冒頭のモードへ戻す
    "music": {"style": "lab_dub", "sections": [
        ("t0", 0.0, "w_hook"), ("problem", -0.1, "w_shade"), ("harvard", -0.1, "w_story"), ("find", -0.1, "w_focus"), ("notice", -0.1, "w_hold"),
        ("line", -0.1, "w_discover"), ("ruler", -0.1, "w_focus"), ("death", -0.2, "w_hold"), ("hubble", -0.1, "w_focus"), ("jump", -0.1, "w_discover"),
        ("letter", -0.2, "w_shade"), ("today", -0.1, "w_warm"), ("back", -0.1, "w_hook"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "problem", "harvard", "find", "line", "ruler", "hubble", "letter", "today"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js", "assets/assets.js", "assets/scene_assets.js"] + V3,
    "workers": 1,   # 3D が重く、2 本同時だとブラウザが落ちた（2026-10-29）
    "qc_frames": [("t0", 0.3), ("pull", 0.8), ("q", 1.0), ("reveal", 0.8), ("women", 0.8), ("plates", 0.6), ("photo", 1.0), ("empty", 0.8),
                  ("find", 0.8), ("count", 1.2), ("pulse", 1.0), ("draw", 0.8), ("fig", 0.8), ("true", 0.8), ("ticks", 1.0), ("death", 1.0),
                  ("hubble", 1.0), ("var", 1.2), ("jump", 1.0), ("galaxy", 1.2), ("letter", 1.0), ("chair", 1.0), ("today", 1.5), ("back", 1.5), ("card", 0.3)],
    "scenes": [
        ("1 冒頭（フック）", None, "problem", "最初の 1 秒：ガラス乾板の上の 1 点が強く明滅 → 一気に引くと無数の星 → 見出し → 夜空へ急上昇（問い）", "w_hook、一打・引きの音"),
        ("2 距離が分からない", "problem", "harvard", "同じ暗さに見える近い小さな星と遠い大きな星（大きさの対比）", "w_shade"),
        ("3 天文台", "harvard", "find", "木の机が並ぶ部屋（PBR・HDRI・SSAO）、乾板を調べる女性たちの後ろ姿 → 本物の肖像写真（A1）→ 誰もいない机", "w_story"),
        ("4 1777 個と気づき", "find", "line", "乾板をのぞく後ろ姿 → 星に印が付き 1777 まで数える → 違う速さで脈打つ 2 つの星（スロー）", "w_focus → w_hold"),
        ("5 一本の線", "line", "ruler", "ホログラムの台に 25 個の点（1912 年の表の値）→ 線が走る（決定的な映像）→ 本物の 1912 年の図（A2）→ 同じ距離の図", "w_discover"),
        ("6 宇宙の物差し", "ruler", "hubble", "線が物差しになって宇宙の奥へ（説明のための図）→ 静かな机、光が消える", "w_focus → w_hold"),
        ("7 アンドロメダ", "hubble", "letter", "望遠鏡のドームが開く → 乾板に VAR!（再現、スロー）→ 銀河系の外へ飛ぶ → 本物のアンドロメダ（A3）", "w_focus → w_discover"),
        ("8 手紙", "letter", "today", "机に届く手紙、誰もいない椅子", "w_shade"),
        ("9 現代と冒頭へ", "today", "endcard", "宇宙望遠鏡と遠ざかる銀河 → 冒頭の乾板の 1 点に戻る", "w_warm → w_hook"),
        ("10 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（標準ルール v8・ガイドライン v2.4）",
        "",
        "- 冒頭の最初の 1 秒：決定的な映像（ガラス乾板の上の 1 点が明滅し、一気に引く）。答え（周期と明るさの関係・名前）は言わない。",
        "- 最後の一文（L16）と画を冒頭につなげる：宇宙から乾板の 1 点に戻る。BGM も冒頭のモードに戻す。",
        "- 本物の写真・図：肖像写真（A1、L05）、1912 年の論文の Fig. 2（A2、L08）、ESA/Hubble のアンドロメダ（A3、L13、CC BY 4.0）。画面にクレジット（assets.md）。",
        "- グラフの 25 個の点は 1912 年の論文の表 I の値（周期の対数と極大の明るさ）。",
        "- CG のリアルさ（v2.4 の 1）：Poly Haven の HDRI（wooden_lounge）と木の質感（wood_table_001・old_wood_floor）、SSAO とレンズのボケ、MPFB の人体（顔は映さない・手のアップなし）。",
        "- 大げさな演出（v2.4 の 2）：冒頭の一打と急な引き、L07 のスロー、L08 の線が走る瞬間、L12 のドームと VAR!（再現）、L13 の飛び込み。事実は誇張しない。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.15、行間 0.05 秒。BGM：lab_dub（B14 Dub Techno・短調。宇宙の奥行き）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
