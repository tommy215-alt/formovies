#!/usr/bin/env python3
"""pilot_016「大陸は動いている——アルフレート・ヴェーゲナー」（チャンネル「リバース」標準ルール v6・ガイドライン v2.2）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。
テンプレートの外の部品（production/ext/）：BGM warm_drive と効果音（music_ext.py）、注目のアイコンと短いエンディングの画面（hud_ext.js）、
短いエンディングの間（ending_ext.py：案 2、2026-10-29 にユーザーが承認）。本物の写真・図は assets/（scripts/pilot_016/assets.md）。
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

EP = standard.config({
    "id": "pilot_016",
    "out": "reverse_016_wegener.mp4",
    "cues": {
        "hook": ("L01", 0.0), "man": ("L01", 0.40), "ice0": ("L01", 0.78),
        "announce": ("L02", 0.0), "photo": ("L02", 0.25), "bridge": ("L03", 0.0), "sink": ("L03", 0.5),
        "evidence": ("L04", 0.0), "fossil": ("L05", 0.0), "strata": ("L05", 0.38), "glacier": ("L05", 0.62), "paper": ("L06", 0.0), "join": ("L06", 0.4),
        "wall": ("L07", 0.0), "force": ("L07", 0.5), "meeting": ("L08", 0.0), "book": ("L09", 0.0), "quote": ("L10", 0.0),
        "ice": ("L11", 0.0), "birthday": ("L11", 0.4), "leave": ("L11", 0.7), "dive": ("L12", 0.0),
        "sea": ("L13", 0.0), "ridge": ("L13", 0.3), "stripes": ("L14", 0.0), "plates": ("L15", 0.0), "right": ("L15", 0.55),
        "today": ("L16", 0.0), "gps": ("L16", 0.5), "back": ("L17", 0.0), "card": ("L17", 1.0),
    },
    "sfx": [("title", "t0", 1.0, 0.02), ("lock", "t0", 0.6, 0.6), ("whoosh", "man", 0.6, -0.1), ("wind", "man", 0.5), ("deep", "ice0", 0.4),
            ("whoosh", "announce", 0.5, -0.1), ("zoom", "photo", 0.5), ("paper", "photo", 0.3, 0.3),
            ("tagpop", "bridge", 0.5, 0.4), ("tagpop", "bridge", 0.5, 0.8), ("deep", "sink", 0.6), ("waves", "sink", 0.4),
            ("scanline", "evidence", 0.6), ("lock", "evidence", 0.5, 1.0),
            ("tagpop", "fossil", 0.6, 0.1), ("tagpop", "fossil", 0.55, 0.4), ("data", "strata", 0.5), ("tagpop", "glacier", 0.55), ("ring", "glacier", 0.4, 0.3),
            ("paper", "paper", 0.6), ("flip", "join", 0.6), ("lock", "join", 0.6, 0.4),
            ("deep", "wall", 0.5), ("error", "force", 0.4), ("room", "meeting", 0.5), ("hit", "meeting", 0.4, 0.8), ("hit", "meeting", 0.35, 1.6),
            ("flip", "book", 0.6), ("zoom", "book", 0.5, 0.6), ("lock", "quote", 0.6, 0.3),
            ("wind", "ice", 0.6), ("wind", "birthday", 0.4, 0.5), ("step", "leave", 0.35), ("deep", "dive", 0.6), ("whoosh", "dive", 0.5),
            ("waves", "sea", 0.3), ("reveal", "ridge", 0.7), ("scanline", "stripes", 0.6), ("data", "stripes", 0.5, 0.6),
            ("bloom", "right", 0.9), ("glow", "right", 0.5, 0.6),
            ("whoosh", "today", 0.5, -0.1), ("data", "gps", 0.6), ("tagpop", "gps", 0.5, 0.5), ("glow", "back", 0.5), ("discover", "card", 0.4, 0.1)],
    # BGM：冒頭（謎と期待）→ 背景（穏やか）→ 証拠（集中）→ 壁（少し陰る）→ 氷の上（間）→ 海の底へ（集中）→ 発見（明るく開く）→ 現代（安心）
    #   → 最後の一文で冒頭のモードに戻す（くり返し再生でつなぎ目を自然に：ガイドライン v2.2 の 3）
    "music": {"style": "lab_melodic", "sections": [
        ("t0", 0.0, "w_hook"), ("announce", -0.1, "w_story"), ("evidence", -0.1, "w_focus"), ("wall", -0.2, "w_shade"),
        ("ice", -0.1, "w_hold"), ("dive", -0.1, "w_focus"), ("ridge", -0.1, "w_discover"), ("today", -0.1, "w_warm"),
        ("back", -0.1, "w_hook"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "announce", "evidence", "wall", "ice", "sea", "today"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js", "assets/assets.js"],
    "workers": 2,
    "qc_frames": [("t0", 0.3), ("t0", 1.2), ("man", 0.8), ("photo", 1.0), ("sink", 0.8), ("evidence", 1.0), ("glacier", 0.8), ("join", 0.8),
                  ("force", 0.8), ("meeting", 1.5), ("book", 1.5), ("quote", 1.0), ("birthday", 1.0), ("dive", 0.8), ("ridge", 1.0), ("stripes", 1.5),
                  ("right", 1.0), ("gps", 1.0), ("back", 1.5), ("card", 0.3)],
    "scenes": [
        ("1 冒頭（フック）", None, "announce", "最初の 1 秒：アフリカと南アメリカがぴたりと合わさる → 画面いっぱいの見出し → 吹雪の氷床に小さな人影", "w_hook、見出しの一打・合わさる音"),
        ("2 発表と当時の考え", "announce", "evidence", "本物の肖像写真（A1）に寄る → 陸の橋が沈む図", "w_story"),
        ("3 証拠", "evidence", "wall", "海岸線をスキャン → 化石・地層・氷河の跡の札が両岸でつながる → 破れた新聞がつながる", "w_focus"),
        ("4 壁", "wall", "ice", "地球の断面の矢印が消える → 暗い講堂 → 1920 年版の図（A2）→ 一文に照準", "w_shade"),
        ("5 氷の上", "ice", "sea", "吹雪の氷床、基地から遠ざかる二つの人影（後ろ姿）→ 海の中へ", "w_hold"),
        ("6 海の底", "sea", "today", "海嶺から広がる海底 → 左右対称の磁気の縞 → プレートに乗る大陸、温かい光", "w_focus → w_discover"),
        ("7 現代と冒頭へ", "today", "endcard", "大西洋中央海嶺と GPS → 冒頭の二つの大陸に戻り、ゆっくり離れる", "w_warm → w_hook"),
        ("8 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（標準ルール v6・ガイドライン v2.2）",
        "",
        "- 冒頭の最初の 1 秒：決定的な映像（アフリカと南アメリカの海岸線がぴたりと合わさる）。答え（プレート・名前）は言わない。",
        "- 冒頭の問い：「本当に大陸は動くのか？」「なぜ正しい考えが受け入れられなかったのか？」。名前は L02。",
        "- 最後の一文（L17）と画を冒頭につなげる：二つの大陸に戻り、ゆっくり離れる。BGM も冒頭のモードに戻す。",
        "- 本物の写真・図：肖像写真（A1、L02）と 1920 年版の図 23（A2、L09）。画面に小さくクレジット（assets.md）。",
        "- 共通エンディングは短い版（案 2）：明るい画面をやめ、最後の画の上にロゴと決めゼリフ（HUD.endingOverlay）。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.15、行間 0.05 秒（ユーザーの指示：速く、間を少なく）。",
        "- BGM：lab_melodic（B03 Melodic Techno・短調。人物のドラマと発見の題材。ガイドライン v2.3）。",
        "- CG（ガイドライン v2.3 の 2）：2D の図はホログラムの台（3D の板）に。冒頭の合わさる瞬間に衝撃波とカメラの揺れ。夜の書斎で地図に向かう後ろ姿（L04・L09）。吹雪を強く（風の筋・前かがみ・逆光）。",
        "- 人物は顔のない人形の後ろ姿・遠景。手のアップは使わない。大陸の形と動きは説明のための図。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
