#!/usr/bin/env python3
"""long_001「なぜ、間違った科学ほど広まるのか」（チャンネル「リバース」の長い動画の 1 本目、横長 1920×1080、約 8 分）の制作スクリプト。

長い動画の部品は production/ext/long（横長の書き出し・場面ごとに曲を切り替える BGM）。台本は scripts/long_001/script_draft.md、
事実は scripts/long_001/fact_check.md、素材の権利は scripts/long_001/assets.md。
映像（ユーザーの指示 2026-11-05）：2D の図が中心。ピクトグラム・矢印・アイコンを多めに、なめらかに動かし、画面の動きにメリハリを付ける。
3D は使わない（2026-11-05）。冒頭は 2D の大きな文字とズーム（2026-11-05 ユーザーの指示「判子の CG はいまいち」）。要所で画面全体を白黒反転（円が広がる切り替え）。
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
    "comfort": BGM / "Comfortable Mystery.mp3"})

LINES = json.loads((HERE / "lines.json").read_text(encoding="utf-8"))["lines"]
CUES = {x["id"]: (x["id"], 0.0) for x in LINES}
# 行の途中のきっかけ（効果音・演出用）："L56@0.9" のように書くと、その行の 90% の時刻
for k in ["L00@0.27", "L00@0.56", "L00@0.82", "L74@0.18", "L74@0.33", "L74@0.48", "L75@0.35", "L76@0.6", "L06@0.55", "L24@0.5", "L30@0.15", "L36@0.4", "L41@0.75", "L42@0.7", "L47@0.25", "L49@0.55", "L67b@0.7"]:
    lid, f = k.split("@")
    CUES[k] = (lid, float(f))
FIRST = {}
for x in LINES:
    FIRST.setdefault(x["scene"], x["id"])
ORDER = ["open", "truth", "r1", "r2", "r3", "end"]
SEGS = sorted(set([FIRST[s] for s in ORDER] + [x["id"] for i, x in enumerate(LINES) if i % 5 == 0 and x["id"] != "L00"]))

EP = standard.config({
    "id": "long_001",
    "out": "reverse_long_001_replication.mp4",
    "cues": CUES,
    "final_hold": 1.2,
    "sfx": [
        ("whoosh", "L00", 0.5, 0.0), ("stamp", "L00", 0.45, 0.25), ("whoosh", "L00@0.27", 0.5, -0.1), ("stamp", "L00@0.27", 0.45, 0.15), ("whoosh", "L00@0.56", 0.5, -0.1), ("stamp", "L00@0.56", 0.45, 0.15), ("zoom", "L00@0.82", 0.5), ("title", "L00@0.82", 0.45, 0.1),
        ("whoosh", "L06@0.55", 0.4, -0.25), ("impact", "L06@0.55", 0.5), ("zoom", "L07", 0.4), ("title", "L08", 0.4, -1.0),
        ("flip", "L09", 0.35), ("flip", "L13", 0.35), ("flip", "L17", 0.35), ("whoosh", "L21", 0.3),
        ("zoom", "L22", 0.45), ("tick", "L23", 0.3, 1.0), ("data", "L24@0.5", 0.35), ("paper", "L28", 0.3), ("data", "L30@0.15", 0.35), ("ring", "L31", 0.35),
        ("whoosh", "L32", 0.3), ("tagpop", "L33", 0.35), ("data", "L36@0.4", 0.35), ("reveal", "L37", 0.45), ("tick", "L38", 0.3), ("tick", "L39", 0.3), ("tick", "L40", 0.3),
        ("glitch", "L41@0.75", 0.35), ("bloom", "L42@0.7", 0.4),
        ("zoom", "L44", 0.45), ("paper", "L46", 0.35), ("stamp", "L47@0.25", 0.4), ("title", "L48", 0.35), ("data", "L49@0.55", 0.4), ("data", "L53", 0.35),
        ("zoom", "L58", 0.45), ("whoosh", "L59", 0.3), ("data", "L60", 0.35), ("data", "L60b", 0.35, 1.0), ("ring", "L61", 0.35), ("reveal", "L65", 0.45),
        ("shimmer", "L66", 0.35), ("alarm", "L67b@0.7", 0.25), ("data", "L67c", 0.35),
        ("tagpop", "L70", 0.4), ("tagpop", "L71", 0.4), ("tagpop", "L72", 0.4),
        ("deep", "L73", 0.45), ("tagpop", "L74", 0.4, 0.1), ("tagpop", "L74@0.18", 0.4), ("tagpop", "L74@0.33", 0.4), ("tagpop", "L74@0.48", 0.4), ("impact", "L75", 0.5), ("stamp", "L75@0.35", 0.45), ("paper", "L76", 0.35), ("deep", "L76@0.6", 0.45), ("title", "L77", 0.5), ("zoom", "L77", 0.4, 0.05),
    ],
    "music": {"style": "long_001", "sections": [
        ("t0", 0.0, "inv@80"), ("L08", -0.6, "inv@65"),
        ("L22", -0.8, "dawn@75"), ("L32", -0.4, "crypto@80"),
        ("L44", -0.8, "dawn@70"),
        ("L58", -0.8, "dawn@65"),
        ("L66", -0.8, "comfort@70"), ("L73", -0.3, "comfort@45"), ("L75", -0.2, "comfort@60"), ("L77", -0.3, "comfort@40")]},
    "segments": SEGS,
    "extra_files": long_ext.FILES + ["kit_long.js", "assets/assets.js"],
    "workers": 2,
    "qc_frames": [(x["id"], 1.0) for x in LINES],
    "scenes": [
        ("0 冒頭（フック）", None, "L08", "2D：画面いっぱいの「あなたの常識」→ 3 つの話を大きな文字で 1 つずつズーム（見た目55%・モーツァルト・右脳型と左脳型）→ 画面が反転して「本当は、違った」→「なぜ？」→ タイトル", "Investigations"),
        ("1 3 つの話の、もとの研究", "L08", "L22", "カードを 1 枚ずつ開き、実験の手順を図で（背景は話ごとに色を変える）", "Investigations"),
        ("2 理由① 統計の罠", "L22", "L44", "コイン → 5% の約束 → グミ 20 色 → ビートルズの実験（手順 → 結果 → 種明かし 4 つ → 61%）。実験の場面は実験室の背景", "Lightless Dawn → Crypto"),
        ("3 理由② 成功だけが残る", "L44", "L58", "引き出し問題 → 100 の研究 97%→36% → 21→13 → 登録報告 96%→44%", "Lightless Dawn"),
        ("4 理由③ 伝わり方と私たちの心理", "L58", "L66", "伝言ゲーム（温かい色）→ 86% 対 10% → ジョージア州の CD → 1万時間 → 分かりやすさ・真実性の錯覚 → 冒頭の種明かし", "Lightless Dawn"),
        ("5 結論と仕掛け", "L66", "endcard", "ミルグラムの実験 → 3 つのチェック → 最後の仕掛け（この動画のタイトルそのものが「それっぽい話」だった、画面を反転）", "Comfortable Mystery"),
        ("6 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "ending"),
    ],
    "plan_notes": [
        "## 演出の方針（長い動画、2026-11-05 ユーザーの指示）",
        "",
        "- 2D の図が中心。ピクトグラム（顔のない人型）・矢印・アイコンを多めに。動きはなめらか（イージング）に、場面の頭で大きく動いて止める（メリハリ）。背景は基本の暗い青に、カットや実験の場面で色・雰囲気を変える（ユーザーの指示 2026-11-05）。",
        "- 3D は使わない。冒頭は 2D の大きな文字とズーム、要所で画面全体を白黒反転。冒頭の問い「あなたが常識だと思っていること。本当に、正しいですか？」を、最後に視聴者自身へ返す（この動画の数字も、確かめずに信じていなかったか）。",
        "- 本物の資料：Ioannidis 2005（CC BY）、Sumner ら 2014（CC BY、使うなら）、モーツァルトの肖像画（PD）。権利は scripts/long_001/assets.md。",
        "- 声：阿井田 茂 Calm 話速 1.15・抑揚 0.9。BGM：Kevin MacLeod の 5 曲（CC BY 4.0）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
