#!/usr/bin/env python3
"""pilot_014「目の見えない少年が、世界の読み方を変えた——ルイ・ブライユ」（チャンネル「リバース」標準ルール v5・ガイドライン v2.1）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。映像品質の部品は common/cine.js、注目マークは stage.js の hud*。
ナレーションの声は lines.json の voice_override（VOICEVOX:青山龍星 しっとり）。使い方は pipeline.py の冒頭。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402
import standard  # noqa: E402

EP = standard.config({
    "id": "pilot_014",
    "out": "reverse_014_louis_braille.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "blur": ("L01", 0.22), "dots": ("L01", 0.45), "boy": ("L01", 0.72),
        "village": ("L02", 0.0), "shop": ("L02", 0.45), "accident": ("L03", 0.0), "dark": ("L04", 0.0),
        "school": ("L05", 0.0), "books": ("L06", 0.0), "write": ("L07", 0.0), "cannot": ("L07", 0.45),
        "barbier": ("L08", 0.0), "cell12": ("L09", 0.0), "finger": ("L10", 0.35),
        "invent": ("L11", 0.0), "six": ("L11", 0.0), "letters": ("L12", 0.0), "grid": ("L13", 0.0), "grid63": ("L13", 0.45), "slate": ("L14", 0.0), "book1829": ("L15", 0.0),
        "struggle": ("L16", 0.0), "director": ("L17", 0.0), "death": ("L18", 0.0),
        "spread": ("L19", 0.0), "y1854": ("L19", 0.0), "world": ("L20", 0.0),
        "today": ("L21", 0.0), "back": ("L22", 0.0), "last": ("L23", 0.0), "card": ("L23", 1.0),
    },
    # 効果音：やわらかい音色。紙・点の出現・照準・発見の瞬間に限って。(効果音, きっかけ, 音量, ずらす秒)
    "sfx": [("paper", "t0", 0.7, 0.05), ("deep", "blur", 0.6), ("lock", "dots", 0.8, 0.1), ("glow", "boy", 0.5),
            ("room", "village", 0.5, -0.2), ("tick", "shop", 0.4, 0.3), ("deep", "dark", 0.5, 0.4),
            ("room", "school", 0.5, -0.2), ("step", "school", 0.4, 0.4), ("paper", "books", 0.6, 0.3), ("deep", "cannot", 0.35, 0.1),
            ("scanline", "barbier", 0.5), ("tick", "cell12", 0.4, 0.2), ("lock", "finger", 0.6, 0.2),
            ("reveal", "six", 0.8), ("tick", "letters", 0.4, 0.2), ("tick", "letters", 0.35, 0.9), ("tick", "letters", 0.35, 1.6),
            ("glow", "grid63", 0.6), ("tick", "slate", 0.45, 0.4), ("tick", "slate", 0.4, 0.8), ("tick", "slate", 0.4, 1.2), ("paper", "book1829", 0.6, 0.2),
            ("room", "struggle", 0.6, -0.2), ("deep", "death", 0.45, 0.2),
            ("reveal", "y1854", 0.6), ("sweep_up", "world", 0.35, -0.2), ("glow", "world", 0.5, 0.8),
            ("paper", "today", 0.5, 0.3), ("deep", "last", 0.35, 0.6)],
    # BGM：冒頭は静寂に近い緊張 → 少年時代は控えめで少し寂しい → 方式との出会いでリズム → 発明で層を増やし、63 の形で和音が変わる
    #   → 広まらない現実（冷たく）→ 死（引き）→ 1854 で希望 → 世界へ広がる → 引き算して余韻
    "music": {"sections": [
        ("t0", 0.0, "doc_break"), ("dots", -0.1, "doc_tense"), ("village", -0.2, "doc_alone"), ("barbier", -0.2, "doc_drive"),
        ("six", -0.1, "doc_build"), ("grid63", -0.1, "doc_hope"), ("struggle", -0.3, "doc_alone"), ("death", 0.0, "doc_break"),
        ("y1854", -0.2, "doc_hope"), ("world", -0.2, "doc_warm"), ("last", 0.0, "doc_warm_end"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "village", "school", "barbier", "invent", "struggle", "spread", "today"],
    "extra_files": [],
    "final_hold": 2.6,   # 最後のセリフのあと、最後の一文「一人の工夫が、世界の可能性を広げる。」を表示する余韻（秒）
    "workers": 2,   # 同時に書き出すブラウザの数（pilot_013 で 3 は起動直後に閉じた）
    "qc_frames": [("t0", 0.3), ("blur", 0.5), ("dots", 0.6), ("boy", 1.0), ("village", 1.0), ("shop", 1.0), ("accident", 1.5), ("dark", 1.5),
                  ("school", 1.0), ("books", 1.5), ("write", 1.0), ("cannot", 1.0), ("barbier", 1.0), ("cell12", 1.5), ("finger", 1.0),
                  ("six", 1.0), ("letters", 1.5), ("grid63", 1.0), ("slate", 1.5), ("book1829", 1.5), ("struggle", 1.5), ("director", 2.0),
                  ("death", 1.5), ("y1854", 1.5), ("world", 2.0), ("today", 2.0), ("back", 1.0), ("last", 1.5), ("card", 0.8)],
    "scenes": [
        ("1 冒頭（フック）", None, "village", "暗闇で本が開く → 文字がぼやけて消える → 紙から 6 つの点が浮き上がり、照準が合う →「15歳の少年」で点に光", "静寂に近い doc_break → 点で doc_tense、紙・低い音・照準の音"),
        ("2 少年の世界", "village", "school", "19 世紀の村 → 馬具の作業場（作業台の道具、事故は描かない）→ 窓の光がぼやけて暗くなる", "doc_alone（控えめで少し寂しい）"),
        ("3 盲学校", "school", "barbier", "学校の廊下と遠くの少年の後ろ姿 → 浮き出し文字の本（斜めの光）→ 机の少年（遠景）", "doc_alone"),
        ("4 既存の方法では足りない", "barbier", "invent", "暗い背景に 12 点の図（枠）→ 指先の輪郭を重ねると、はみ出す", "doc_drive、線が横切る音・照準"),
        ("5 挑戦と試行錯誤", "invent", "struggle", "12 点 → 6 点（指先に収まる）→ A〜J が組み上がる → 63 の形の格子 → 点を打つ板 → 1829 年の本", "doc_build → 63 の形で doc_hope（和音が変わる）"),
        ("6 すぐには世界は変わらない", "struggle", "spread", "冷たい教室と浮き出し文字の本の棚、一枚の点字の紙 → 1852、夜の窓", "doc_alone → doc_break"),
        ("7 少年の人生を超えて", "spread", "today", "1854 → 地球の上に点が広がる（イメージ）", "doc_hope → doc_warm"),
        ("8 今と余韻", "today", "endcard", "現代の図書館の点字の本・駅の表示 → 冒頭の本に温かい光 → 引き、最後の一文を表示", "doc_warm → doc_warm_end"),
        ("9 共通エンディング", "endcard", None, "リバース。世界の仕組みを、はじめから。", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（ガイドライン v2.1）",
        "",
        "- 冒頭の問い：「目の見えない人が自分で読み書きできる文字を、15 歳の少年がどうやって？」。名前は L02 まで出さない。",
        "- 物語の核：読めても書けない浮き出し文字 → 12 点の方式との出会い → 6 点・文字・数字への作り変え → 15 歳で 63 通り → 生前は広まらない → 死後 2 年で正式に → 世界へ。",
        "- **決定的な映像**：L11〜L13、12 点が 6 点に減って指先の輪郭に収まり、A〜J が組み上がり、63 の形が格子に並ぶ瞬間（照準・発見の音・doc_hope の和音）。",
        "- 手のアップは使わない（ガイドライン 6）。少年は後ろ姿・遠景。点は紙から押し出される動きで見せる。",
        "- 声：VOICEVOX:青山龍星 しっとり（落ち着いた歴史ドラマ向け）。",
        "- 事実の範囲：バルビエの方式を「軍事用」と言わない（説が分かれる）。試作の回数や会話を作らない。教師を悪人として描かない。点字を唯一の手段と言わない。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
