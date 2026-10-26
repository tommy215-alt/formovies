#!/usr/bin/env python3
"""pilot_007「QRコードを消したら、オモテが消えた」（チャンネル「リバース」新構成）の制作スクリプト。

処理の本体は production/common/pipeline.py。ここには、この話だけの設定（きっかけ・効果音・BGM の構成・場面）を書く。
使い方は pipeline.py の冒頭（python3 production_script.py all など）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402

EP = {
    "id": "pilot_007",
    "out": "reverse_007_qr_code.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "dare": ("L02", 0.4), "erase": ("L03", 0.55), "glitch": ("L04", 0.0), "suck": ("L04", 0.4),
        "inside": ("L06", 0.0), "scan": ("L07", 0.5), "why": ("L08", 0.0),
        "parity": ("L09", 0.0), "twice": ("L10", 0.0), "stingy": ("L11", 0.0), "nums": ("L12", 0.15), "sum": ("L12", 0.7),
        "lose5": ("L13", 0.0), "solve": ("L14", 0.0), "jab": ("L15", 0.0),
        "restore": ("L16", 0.0), "rsname": ("L16", 0.1), "fill": ("L16", 0.55), "back": ("L17", 0.0),
        "levels": ("L18", 0.0), "compare": ("L18", 0.4), "logo": ("L19", 0.0), "cover": ("L20", 0.2), "greed": ("L21", 0.0),
        "wait": ("L22", 0.0), "vanish": ("L23", 0.0), "dark": ("L24", 0.0),
        "finder": ("L25", 0.0), "notfound": ("L25", 0.55), "limit": ("L26", 0.0), "where": ("L27", 0.0),
        "rescue": ("L28", 0.0), "redraw": ("L28", 0.45), "deadpan": ("L29", 0.0), "punch": ("L30", 0.0),
    },
    "sfx": [("slide", "erase", 0.7), ("glitch", "glitch"), ("impact", "glitch", 0.6), ("whoosh", "suck"), ("boing", "inside", 0.7),
            ("scan", "scan"), ("ok", "scan", 0.9), ("pop", "nums"), ("pop", "sum"), ("whoosh", "lose5", 0.6), ("ding", "solve"),
            ("boop", "jab"), ("sparkle", "fill"), ("ding", "back", 0.7), ("tick", "compare"), ("error", "compare", 0.7),
            ("pop", "cover"), ("slide", "wait", 0.8), ("glitch", "vanish"), ("error", "notfound", 0.8), ("tick", "limit"),
            ("ding", "where", 0.6), ("sparkle", "redraw"), ("ok", "redraw", 0.8), ("stab", "punch")],
    # BGM：chip（140 BPM）
    "music": {"style": "chip", "seed": 7, "sections": [
        ("hook", -1.0, "hook"), ("glitch", -0.05, "chaos"), ("inside", 0.0, "banter"), ("parity", 0.0, "explain"),
        ("solve", 0.0, "reveal"), ("jab", 0.4, "banter"), ("restore", 0.0, "explain"), ("back", 0.0, "reveal"),
        ("levels", 0.0, "explain"), ("logo", 0.0, "banter"), ("vanish", -0.1, "drop"), ("dark", 0.0, "explain"), ("finder", 0.0, "explain"),
        ("rescue", 0.0, "banter"), ("punch", -0.35, "drop"), ("punch", 0.9, "banter")]},
    "segments": ["glitch", "inside", "parity", "restore", "levels", "logo", "vanish", "finder", "rescue"],
    "extra_files": ["qr_demo.js"],
    "qc_frames": [("hook", 1.5), ("erase", 0.4), ("suck", 0.5), ("inside", 0.6), ("scan", 0.7), ("twice", 0.5), ("sum", 0.5),
                  ("lose5", 0.5), ("solve", 0.6), ("fill", 0.8), ("back", 0.5), ("compare", 1.0), ("cover", 0.8), ("wait", 0.6),
                  ("vanish", 0.5), ("notfound", 0.4), ("limit", 0.8), ("redraw", 0.8), ("punch", 0.6)],
    "scenes": [
        ("1 巨大な QR コード（冒頭）", None, "glitch", "明るい壁に巨大な QR コード。オモテが巨大な消しゴムで一部を消す", "BGM hook、消す音"),
        ("2 ギャグ：吸い込まれる", "glitch", "inside", "画面がグリッチし、オモテがドット絵になってコードの中へ吸い込まれる（明らかに非現実の演出）", "グリッチ音、インパクト／BGM chaos"),
        ("3 コードの中", "inside", "parity", "巨大なマスの上に、左腕が欠けたドット絵のオモテ。読み取り光線が走り「読み取り成功」（実際の検証結果）", "スキャン音、成功音／BGM banter"),
        ("4 予備の情報（たとえ）", "parity", "restore", "3・5・2 と合計 10 のブロック。5 が消え、オモテが 10−3−2＝5 と解く。「※たとえ」と表示", "ポップ、発見音、ブッ／BGM explain→reveal"),
        ("5 復元（最大の見せ場）", "restore", "levels", "消えたマスが、残りのマスから光の線で計算されて埋まっていき、オモテの腕が戻る", "きらめき、発見音／BGM explain→reveal"),
        ("6 4 段階と比較", "levels", "logo", "L・M・Q・H の棒グラフ（コード語の約 7・15・25・30%）。同じ消し方で L は ✕、H は ○（実際の検証結果）", "チック、エラー音／BGM explain"),
        ("7 ロゴ付き QR", "logo", "vanish", "真ん中にロゴが載った QR。オモテが調子に乗って角を消しにいく", "ポップ、スライド／BGM banter"),
        ("8 消えた", "vanish", "finder", "角の位置検出パターンが消え、オモテも消える。読み取り機に「コードが見つかりません」", "グリッチ、エラー音／BGM drop"),
        ("9 目印と限界", "finder", "rescue", "3 つの角の四角が光る（位置を探す目印）。「最大でも約 3 割（コード語）」。オモテ「どこを・どれだけ」", "エラー音、チック、発見音／BGM explain"),
        ("10 救出とオチ", "rescue", "endcard", "ウラが目印を描き直し、オモテが戻る。最後のひと言の前に BGM を止める", "きらめき、成功音、オチの和音／BGM banter→drop"),
        ("11 共通エンディング", "endcard", None, "白い閃光 → 明るい背景に巻き戻しの円弧、大きな「リバース」、タグライン", "BGM を下げる、和音"),
    ],
    "plan_notes": [
        "## 演出の方針",
        "",
        "- QR コードは本物（`qr_demo.py` で生成した、文字列「REVERSE」・バージョン 1・誤り訂正レベル H／L）。",
        "  「読める／読めない」の表示は、`qr_demo.py` で OpenCV の読み取りを実際に試した結果（`qr_demo.json`）だけを使う。",
        "- 吸い込まれる・腕が欠ける・消えるのは、明らかに非現実のギャグ演出（ドット絵・グリッチ）。",
        "- 「3・5・2 と合計 10」は予備の情報の **たとえ**（実際のリード・ソロモン符号はもっと複雑）と画面に表示する。",
        "- 「約 3 割」は **コード語** の割合（面積ではない）。欠けた場所や印刷の状態で結果が変わることを画面と台本の両方で伝える。",
        "- 位置検出パターン（角の 3 つの四角）は、データの復元とは別の役割（コードを見つける目印）として描き分ける。",
    ],
}

if __name__ == "__main__":
    pipeline.main(__file__, EP)
