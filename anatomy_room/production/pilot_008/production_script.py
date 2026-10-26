#!/usr/bin/env python3
"""pilot_008「298円と300円。その2円に騙されるな」（チャンネル「リバース」新構成）の制作スクリプト。

処理の本体は production/common/pipeline.py。ここには、この話だけの設定（きっかけ・効果音・BGM の構成・場面）を書く。
使い方は pipeline.py の冒頭（python3 production_script.py all など）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402

EP = {
    "id": "pilot_008",
    "out": "reverse_008_price_298.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "basket": ("L02", 0.3), "dare": ("L03", 0.3), "jab0": ("L04", 0.0),
        "rain": ("L05", 0.0), "flip": ("L05", 0.5), "calm": ("L06", 0.0),
        "left": ("L07", 0.0), "key": ("L08", 0.3), "scanline": ("L08", 0.45), "bucket": ("L10", 0.0), "name": ("L11", 0.55),
        "same": ("L12", 0.0), "flat": ("L13", 0.0), "cross": ("L13", 0.55), "insight": ("L14", 0.0),
        "menu": ("L15", 0.0), "pick": ("L16", 0.3), "reveal": ("L17", 0.25), "study": ("L18", 0.0), "paper": ("L19", 0.0),
        "jab": ("L20", 0.0), "caveat": ("L21", 0.0), "notalways": ("L22", 0.0), "factors": ("L22", 0.35), "nine": ("L23", 0.0),
        "rule": ("L24", 0.0), "final": ("L25", 0.0), "shoes": ("L25", 0.5), "almost": ("L26", 0.0), "wallet": ("L27", 0.0),
        "punch": ("L28", 0.0),
    },
    "sfx": [("impact", "t0", 1.0, 0.05), ("sweep_up", "t0", 0.7, 0.3), ("rain", "t0", 0.9, 0.4), ("impact", "t0", 0.6, 0.85), ("brake", "t0", 0.7, 1.25),
            ("tick", "basket", 0.7), ("zap", "dare"), ("rain", "rain"), ("sweep_up", "rain", 0.6), ("tick", "flip"),
            ("zap", "jab0"), ("discover", "key"), ("scan", "scanline", 0.8), ("impact", "bucket", 0.6), ("tick", "name"),
            ("tick", "flat"), ("impact", "cross", 0.7), ("sweep_down", "menu"), ("tick", "pick"), ("discover", "reveal"),
            ("brake", "paper"), ("tick", "factors"), ("tick", "nine"), ("discover", "rule", 0.7),
            ("tick", "shoes"), ("impact", "almost", 0.8), ("cash", "wallet"), ("revswell", "punch", 0.8, -0.7), ("stab", "punch")],
    # BGM：funk（128 BPM）
    "music": {"style": "tech_price", "sections": [
        ("t0", 0.0, "intro"), ("hook", 0.0, "drive"), ("rain", -0.05, "chaos"), ("left", -0.1, "drive"), ("key", 0.0, "explain"),
        ("bucket", 0.0, "lift"), ("same", 0.0, "explain"), ("cross", -0.3, "drop"), ("cross", 0.1, "lift"), ("menu", 0.0, "drive"),
        ("study", 0.0, "explain"), ("paper", 0.0, "drive"), ("caveat", 0.0, "drive"), ("notalways", 0.0, "explain"),
        ("rule", 0.0, "lift"), ("final", 0.0, "drive"), ("almost", -0.3, "drop"), ("wallet", 0.0, "drive"),
        ("punch", -0.35, "drop"), ("punch", 0.9, "drive")]},
    "lead_in": 1.5,  # 冒頭 1.5 秒はセリフなしの「つかみ」（cold）
    "segments": ["hook", "rain", "left", "same", "menu", "caveat", "rule", "final"],
    "extra_files": [],
    "qc_frames": [("t0", 0.3), ("t0", 0.9), ("hook", 0.6), ("basket", 0.5), ("rain", 0.7), ("flip", 0.8), ("key", 0.6), ("scanline", 1.0), ("bucket", 0.8),
                  ("name", 0.5), ("same", 0.8), ("cross", 0.6), ("pick", 0.6), ("reveal", 0.6), ("study", 1.2), ("paper", 0.6),
                  ("factors", 1.2), ("nine", 1.5), ("rule", 1.0), ("shoes", 0.8), ("almost", 0.6), ("wallet", 0.6), ("punch", 0.8)],
    "scenes": [
        ("1 スーパーの棚（冒頭）", None, "rain", "明るい売り場。298 円と 300 円の同じお菓子（架空のパッケージ）。オモテが 298 円をカゴへ。ウラが指を鳴らすと「ウラ商店（実験中）」の看板", "BGM hook、指を鳴らす音"),
        ("2 値札の雨", "rain", "left", "天井から値札が大量に降り、298→498→998→1,980 と数字がめくれる。オモテが目を回す", "値札の音、風切り音／BGM chaos"),
        ("3 左端の数字（最大の見せ場）", "left", "same", "巨大な 298 と 300。視線が左から右へ走り、左端の 2 と 3 が大きくなる。「200 円台」「300 円台」の箱に振り分けられる", "発見音、スキャン音／BGM banter→explain→reveal"),
        ("4 左端が同じなら", "same", "menu", "299 と 298 を並べると左端が同じで印象の差はほぼなし（メーターが動かない）。298 と 300 では大きく動く（演出上の比較）", "チック、発見音／BGM explain"),
        ("5 メニューの順番", "menu", "caveat", "高い順のメニューからオモテが 1,280 円を選ぶ →「高い順」と明かされる。「※実験の一例」と表示", "スライド、ポップ、発見音、ボヨン／BGM banter・explain"),
        ("6 必ずではない", "caveat", "rule", "「必ず」に ✕。原価・ライバル店・売り方のカード。9 で終わる値段の実験の注記", "ポップ、チック／BGM explain"),
        ("7 次の買い物の一言", "rule", "final", "値札を虫めがねで最後の桁まで読む", "きらめき／BGM reveal"),
        ("8 オチ", "final", "endcard", "オモテが 1,980 円の靴を「千円台」と言い張る →「ほぼ 2,000 円」。財布が飛んでいく", "インパクト、レジの音、オチの和音／BGM drop→banter"),
        ("9 共通エンディング", "endcard", None, "白い閃光 → 明るい背景に巻き戻しの円弧、大きな「リバース」、タグライン", "BGM を下げる、和音"),
    ],
    "plan_notes": [
        "## 演出の方針",
        "",
        "- 商品・店はすべて架空（実在の商品名・ロゴ・店名は描かない）。",
        "- 画面のメーターや「安く感じる度」は **演出上の比較** で、研究の測定値ではないと明記する。",
        "- 研究の紹介は「〜という実験がある」「効き方は商品や状況で変わる」にとどめ、「298 円なら必ず売れる」とは言わない。",
        "- オモテの「千円台だから安い」は左端の数字効果のたとえとしてのオチ（ウラが即座に訂正する）。",
    ],
}

if __name__ == "__main__":
    pipeline.main(__file__, EP)
