#!/usr/bin/env python3
"""long_001「心理学の3分の2は、やり直すと消えた」（チャンネル「リバース」の長い動画の 1 本目、横長 1920×1080、約 8 分）の制作スクリプト。

長い動画の部品は production/ext/long（横長の書き出し・場面ごとに曲を切り替える BGM）。台本は scripts/long_001/script_draft.md、
事実は scripts/long_001/fact_check.md、素材の権利は scripts/long_001/assets.md。
映像（ユーザーの指示 2026-11-05）：2D の図が中心。ピクトグラム・矢印・アイコンを多めに、なめらかに動かし、画面の動きにメリハリを付ける。
CG（3D）は視聴者に問いを投げる 3 か所だけ（冒頭 L00・第 2 章 L42・最後 L57〜L58）。
声：本編＝AivisSpeech 阿井田 茂 Calm（話速 1.15・抑揚 0.9、「やや低温気味で落ち着いた、温かみのあるトーン」）、冒頭 L00 と決めゼリフ＝冥鳴ひまり。
BGM：Kevin MacLeod（incompetech、CC BY 4.0）の 5 曲を場面ごとに。
きっかけ（cues）はセリフ ID と同じ名前で全行ぶん自動で作る（renderer.html は CUE.L09a のように使う）。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "long"))
import long_ext  # noqa: E402

pipeline, standard = long_ext.setup(HERE)
import music_ext  # noqa: E402,F401  効果音（title・stamp・whoosh など）

BGM = HERE / "assets" / "bgm"
long_ext.register_bgm("long_001", {
    "inv": BGM / "Investigations.mp3", "dawn": BGM / "Lightless Dawn.mp3", "crypto": BGM / "Crypto.mp3",
    "satiate": BGM / "Satiate - only strings.mp3", "comfort": BGM / "Comfortable Mystery.mp3"})

LINES = json.loads((HERE / "lines.json").read_text(encoding="utf-8"))["lines"]
CUES = {x["id"]: (x["id"], 0.0) for x in LINES}
FIRST = {}
for x in LINES:
    FIRST.setdefault(x["scene"], x["id"])

EP = standard.config({
    "id": "long_001",
    "out": "reverse_long_001_replication.mp4",
    "cues": CUES,
    "final_hold": 1.2,
    "sfx": [
        ("title", "L00", 0.5, 0.0), ("tagpop", "L01", 0.45), ("tagpop", "L02", 0.45), ("tagpop", "L03", 0.45), ("tagpop", "L04", 0.45), ("tagpop", "L05", 0.45),
        ("stamp", "L06b", 0.55, 1.6), ("whoosh", "L07a", 0.35), ("title", "L08", 0.4, -1.2),
        ("flip", "L09a", 0.35), ("flip", "L10a", 0.35), ("flip", "L11", 0.35), ("flip", "L12", 0.35), ("flip", "L13a", 0.35), ("whoosh", "L14b", 0.3),
        ("zoom", "L15", 0.4), ("data", "L18a", 0.35, 1.0), ("ring", "L19", 0.35, 1.4),
        ("zoom", "L20", 0.4), ("paper", "L22a", 0.35, 1.5), ("stamp", "L22c", 0.35, 2.4),
        ("zoom", "L23", 0.4), ("data", "L25", 0.35, 0.6), ("stamp", "L26", 0.45, 2.0), ("whoosh", "L27b", 0.25), ("whoosh", "L27c", 0.25), ("bloom", "L28", 0.4, 3.0),
        ("zoom", "L30", 0.4), ("data", "L31b", 0.35, 2.5), ("ring", "L33", 0.35, 4.0),
        ("zoom", "L34", 0.4), ("shimmer", "L36", 0.4, 2.0),
        ("title", "L37a", 0.35, -0.8), ("data", "L38b", 0.4, 2.2), ("deep", "L42", 0.45),
        ("title", "L43a", 0.35, -0.8), ("stamp", "L45", 0.5, 2.6), ("bloom", "L46", 0.35, 1.5), ("data", "L48", 0.35, 1.0),
        ("title", "L49", 0.35, -0.8), ("reveal", "L50a", 0.45), ("shimmer", "L52a", 0.35), ("tagpop", "L54", 0.4), ("tagpop", "L55", 0.4), ("tagpop", "L56", 0.4), ("deep", "L57", 0.4), ("glow", "L58", 0.4, 2.5),
    ],
    "music": {"style": "long_001", "sections": [
        ("t0", 0.0, "inv@80"), ("L08", -0.6, "inv@70"),
        ("L15", -0.8, "dawn@75"), ("L23", -0.8, "crypto@80"), ("L30", -0.8, "dawn@75"),
        ("L37a", -0.8, "dawn@60"), ("L42", -0.3, "dawn@45"),
        ("L43a", -0.8, "satiate@65"), ("L46", -0.4, "comfort@70"),
        ("L49", -0.8, "comfort@70"), ("L57", -0.3, "comfort@55")]},
    "segments": [FIRST[s] for s in ("truth", "m1", "m2", "m3", "m4", "m5", "scale", "irony", "end")] + ["L00", "L09a", "L10a", "L11", "L12", "L13a", "L16", "L21", "L24", "L27a", "L31a", "L32", "L35a", "L38a", "L40", "L43b", "L47", "L50a", "L52a", "L53"],
    "extra_files": long_ext.FILES + ["kit_long.js", "assets/assets.js"],
    "workers": 2,
    "qc_frames": [(x["id"], 1.0) for x in LINES],
    "scenes": [
        ("0 冒頭（フック）", None, "L08", "CG①：判子が迫る暗い空間 → 5 枚のカード（ピクトグラム）→ 一斉に「?」の判子 → タイトル", "Investigations"),
        ("1 5 つの話の正体", "L08", "L15", "5 枚のカードを 1 枚ずつ開いて、元の研究と広まった話を左右に並べる（矢印・アイコン）", "Investigations"),
        ("2 仕組み① 偶然", "L15", "L20", "20 色のグミ、5%＝20 マスに 1 マス、緑だけが光る、新聞の見出し", "Lightless Dawn"),
        ("3 仕組み② 引き出し", "L20", "L23", "20 の研究室のピクトグラム、19 本が引き出しへ、1 本だけ雑誌へ", "Lightless Dawn"),
        ("4 仕組み③ 分かれ道", "L23", "L30", "2 つのヘッドホン・20 人、20.1 歳 対 21.5 歳、分かれ道の迷路、5% の棒がふくらむ", "Crypto"),
        ("5 仕組み④ 伝言ゲーム", "L30", "L34", "研究 → 発表 → 新聞 → テレビ → 本の矢印、86% 対 10%、モーツァルトの肖像画（PD）、赤ちゃんと CD", "Lightless Dawn"),
        ("6 仕組み⑤ あなたの脳", "L34", "L37a", "頭のピクトグラム、分かりやすさの物差し、鍵のかかった箱", "Lightless Dawn"),
        ("7 どれくらい起きていたのか", "L37a", "L43a", "100 個の点（97 → 36）、21 本（13）、Ioannidis 2005 の 1 ページ目（CC BY）、CG②：消えた点", "Lightless Dawn"),
        ("8 最大の皮肉と立ち直り", "L43a", "L49", "署名欄、走行距離の一様な分布、撤回の判子 → 事前登録の流れ、96% 対 44%", "Satiate → Comfortable Mystery"),
        ("9 結論", "L49", "endcard", "鍵の箱が開く（真実性の錯覚）、残った点、3 つのチェック、CG③：新しいカード", "Comfortable Mystery"),
        ("10 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "ending"),
    ],
    "plan_notes": [
        "## 演出の方針（長い動画、2026-11-05 ユーザーの指示）",
        "",
        "- 2D の図が中心。ピクトグラム（顔のない人型）・矢印・アイコンを多めに。動きはなめらか（イージング）に、場面の頭で大きく動いて止める（メリハリ）。",
        "- CG は視聴者に問いを投げる 3 か所だけ（冒頭・L42・L57〜L58）。",
        "- 本物の資料：Ioannidis 2005（CC BY）、Sumner ら 2014（CC BY、使うなら）、モーツァルトの肖像画（PD）。権利は scripts/long_001/assets.md。",
        "- 声：阿井田 茂 Calm 話速 1.15・抑揚 0.9。BGM：Kevin MacLeod の 5 曲（CC BY 4.0）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
