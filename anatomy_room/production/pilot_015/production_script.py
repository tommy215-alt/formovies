#!/usr/bin/env python3
"""pilot_015「太陽は何でできているか——セシリア・ペイン」（チャンネル「リバース」標準ルール v5・ガイドライン v2.1＋ pilot_015 の修正事項）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。
修正事項（scripts/pilot_015/production_request.md）の部品はテンプレートの外の production/ext/：
安心して聴ける BGM "warm_drive" と追加の効果音（music_ext.py）、注目のアイコンと冒頭の見出し（hud_ext.js）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE.parent / "ext"))
import pipeline  # noqa: E402
import standard  # noqa: E402
import music_ext  # noqa: E402,F401  読み込むだけで warm_drive と追加の効果音が使えるようになる（この回の処理の中だけ）

EP = standard.config({
    "id": "pilot_015",
    "out": "reverse_015_cecilia_payne.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "who": ("L01", 0.26), "letter0": ("L01", 0.62), "stamp": ("L01", 0.76),
        "cambridge": ("L02", 0.0), "lecture": ("L03", 0.0), "degree": ("L04", 0.0), "ship": ("L05", 0.0),
        "harvard": ("L06", 0.0), "plate": ("L06", 0.5),
        "method": ("L07", 0.0), "lines": ("L07", 0.45), "temp": ("L08", 0.0), "ion": ("L08", 0.55), "saha": ("L09", 0.0), "night": ("L10", 0.0),
        "result": ("L11", 0.0), "table": ("L11", 0.35), "twoel": ("L12", 0.0), "hhe": ("L12", 0.55), "bars": ("L13", 0.0), "million": ("L13", 0.5),
        "letter": ("L14", 0.0), "letterread": ("L15", 0.0), "impossible": ("L15", 0.12), "theory": ("L15", 0.62),
        "thesis": ("L16", 0.0), "p188": ("L16", 0.55), "notreal": ("L17", 0.0),
        "after": ("L18", 0.0), "y1929": ("L18", 0.25), "assist": ("L19", 0.0), "prof": ("L20", 0.0), "prof2": ("L20", 0.45),
        "today": ("L21", 0.0), "core": ("L22", 0.0), "sky": ("L23", 0.0), "back": ("L24", 0.0), "card": ("L24", 1.0),
    },
    # 効果音（やわらかい音色のまま数を増やす。pilot_014 の約 30 → 約 60）：(効果音, きっかけ, 音量, ずらす秒)
    "sfx": [("title", "t0", 1.0, 0.02), ("whoosh", "who", 0.7, -0.1), ("room", "who", 0.4, 0.1), ("typer", "letter0", 0.6, 0.1),
            ("stamp", "stamp", 1.0), ("lock", "stamp", 0.6, 0.15),
            ("whoosh", "cambridge", 0.6, -0.1), ("wind", "cambridge", 0.35), ("ring", "lecture", 0.5, 0.5), ("room", "lecture", 0.35),
            ("scanline", "degree", 0.45, 0.2), ("lock", "degree", 0.6, 0.9), ("ship", "ship", 0.7, 0.1), ("waves", "ship", 0.45),
            ("whoosh", "harvard", 0.6, -0.1), ("data", "harvard", 0.5, 0.5), ("zoom", "plate", 0.7), ("lock", "plate", 0.5, 0.55),
            ("prism", "method", 0.9), ("scanline", "lines", 0.55), ("tagpop", "lines", 0.6, 0.5), ("tagpop", "lines", 0.55, 0.85),
            ("tagpop", "lines", 0.55, 1.2), ("tagpop", "lines", 0.5, 1.55),
            ("data", "temp", 0.5, 0.2), ("zap", "ion", 0.5), ("ring", "ion", 0.4, 0.1), ("paper", "saha", 0.5), ("pencil", "saha", 0.5, 0.6),
            ("tick", "night", 0.35, 0.3), ("tick", "night", 0.3, 1.3), ("room", "night", 0.35),
            ("whoosh", "result", 0.6, -0.1), ("data", "table", 0.7), ("tick", "table", 0.35, 0.6), ("tick", "table", 0.3, 1.0),
            ("reveal", "twoel", 0.8), ("bloom", "hhe", 1.0, -0.1), ("glow", "hhe", 0.6, 0.6), ("riser", "bars", 0.5), ("impact", "million", 0.8),
            ("ring", "million", 0.5, 0.2),
            ("whoosh", "letter", 0.5, -0.1), ("paper", "letter", 0.5, 0.3), ("typer", "letterread", 0.6), ("stamp", "impossible", 0.9, 0.25),
            ("lock", "impossible", 0.6, 0.45), ("deep", "theory", 0.5), ("flip", "thesis", 0.7, 0.1), ("zoom", "p188", 0.7), ("lock", "p188", 0.6, 0.3), ("bloom", "notreal", 0.8, 0.2),
            ("glow", "notreal", 0.5, 0.9),
            ("whoosh", "after", 0.6, -0.1), ("reveal", "y1929", 0.7), ("glow", "y1929", 0.5, 0.4), ("lock", "assist", 0.45, 0.4), ("tick", "assist", 0.35, 1.0),
            ("ok", "prof", 0.6, 0.4), ("glow", "prof2", 0.5),
            ("whoosh", "today", 0.5, -0.1), ("tagpop", "today", 0.5, 0.8), ("zoom", "core", 0.7), ("shimmer", "core", 0.6, 0.5), ("shimmer", "sky", 0.5),
            ("tagpop", "sky", 0.5, 0.8), ("tagpop", "sky", 0.45, 1.3), ("glow", "back", 0.6), ("discover", "card", 0.45, 0.2)],
    # BGM：安心して聴けるテクノ（warm_drive、124 BPM のまま）。場面の感情で変える
    #   冒頭（謎と期待）→ 背景（穏やか）→ 方法（集中）→ 発見（明るく開く）→ 手紙と留保（少し陰る → 一瞬の間）→ 再評価（前へ）→ 現代（安心と余韻）
    "music": {"style": "warm_drive", "sections": [
        ("t0", 0.0, "w_hook"), ("cambridge", -0.1, "w_story"), ("method", -0.1, "w_focus"), ("twoel", -0.2, "w_discover"),
        ("letter", -0.2, "w_shade"), ("notreal", -0.1, "w_rise"), ("after", -0.1, "w_rise"), ("today", -0.1, "w_warm"),
        ("card", 0.0, "w_end"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "cambridge", "harvard", "method", "result", "letter", "after", "today"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js"],
    "final_hold": 1.2,   # 最後のセリフのあと、太陽の光から引いていく余韻（秒）。全体を 120 秒以内に収める
    "workers": 2,
    "qc_frames": [("t0", 0.4), ("t0", 1.5), ("who", 1.0), ("stamp", 0.6), ("cambridge", 1.5), ("lecture", 2.0), ("degree", 2.0), ("ship", 2.0),
                  ("harvard", 1.5), ("plate", 1.5), ("method", 1.0), ("lines", 1.5), ("temp", 1.0), ("ion", 1.0), ("saha", 1.5), ("night", 1.5),
                  ("table", 1.5), ("hhe", 1.0), ("million", 1.0), ("letter", 1.5), ("impossible", 1.5), ("p188", 1.0), ("notreal", 1.5),
                  ("y1929", 1.5), ("assist", 1.5), ("prof2", 1.5), ("today", 2.0), ("core", 2.0), ("sky", 2.0), ("back", 2.0), ("card", 1.5)],
    "scenes": [
        ("1 冒頭（フック）", None, "cambridge", "暗闇に太陽の光が差し込み、画面いっぱいの問い → 机の研究者（後ろ姿）→ 手紙の「clearly impossible」に赤い丸", "w_hook、見出しの一打・判の音"),
        ("2 ケンブリッジ", "cambridge", "harvard", "霧の建物 → 講堂の日食の写真 → 一つだけ空いた学位の枠 → 夜の海を渡る船", "w_story"),
        ("3 ハーバード", "harvard", "method", "乾板の棚 → 1 枚の乾板を拡大鏡で", "w_story"),
        ("4 方法", "method", "result", "光がプリズムで虹の帯に → 黒い線に元素の札 → 温度で原子の状態が変わる → 机の後ろ姿 → 夜と朝", "w_focus"),
        ("5 結果", "result", "letter", "表の数字 → 地球と似た並び → H と He の線だけが光る（決定的な映像）→ 水素の棒が画面を突き抜ける", "w_focus → w_discover"),
        ("6 手紙と論文", "letter", "after", "1925 の封筒 → 手紙の一文に赤い丸 → 論文の表 XXVIII、水素の値に注目 → 温かく光る（消さずに残した答え）", "w_shade → w_rise"),
        ("7 その後", "after", "today", "1929 → 再び H の線 → 扉の札 TECHNICAL ASSISTANT → PROFESSOR", "w_rise"),
        ("8 現代", "today", "endcard", "太陽の成分の円グラフ → 中心の核融合 → 夜空の星に H・He の札 → 冒頭の光へ引く", "w_warm → w_end"),
        ("9 共通エンディング", "endcard", None, "リバース。世界の仕組みを、はじめから。", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（ガイドライン v2.1＋ pilot_015 の修正事項）",
        "",
        "- 冒頭の問い：「太陽は何でできている？」「なぜ正しい答えが『ありえない』と言われた？」。名前は L02、答え（水素）は L12 まで出さない。",
        "- 冒頭 3 秒：暗闇に太陽の光が差し込み、画面いっぱいの太字の見出し（光の帯が横切る）と、低い一打と和音の効果音（title）。見出しが出ている間は字幕を出さない（同じ文を重ねない）。",
        "- **決定的な映像**：L12、スペクトルの帯の中で H と He の線だけが強く光り、札が付く瞬間（BGM は w_discover、効果音は bloom）。",
        "- 注目・拡大のときは ext/hud_ext.js の拡大鏡・元素の札・スキャン枠・データ表示・赤い丸を使う。一画面に出しすぎない。",
        "- 手紙・論文の英文は資料の文面だけ（手紙は書き起こし、論文は 188 ページの本文）。宛名や署名は作らない。",
        "- 人物は顔のない人形の後ろ姿・遠景。手のアップは使わない。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.12（7.7 モーラ/秒）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
