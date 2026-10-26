#!/usr/bin/env python3
"""pilot_006「飛行機の窓、穴が開いてるんだけど!?」（チャンネル「リバース」新構成）の制作スクリプト。

処理の本体は production/common/pipeline.py。ここには、この話だけの設定（きっかけ・効果音・BGM の構成・場面）を書く。
使い方は pipeline.py の冒頭（python3 production_script.py all など）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402

EP = {
    "id": "pilot_006",
    "out": "reverse_006_airplane_window.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "dare": ("L02", 0.45), "gag": ("L04", 0.0), "rewind": ("L05", 0.0), "nothole": ("L05", 0.5),
        "hypo": ("L07", 0.0), "vent": ("L07", 0.45), "deny": ("L08", 0.0), "notout": ("L08", 0.55),
        "explode": ("L09", 0.0), "outer": ("L09", 0.2), "middle": ("L09", 0.55), "inner": ("L09", 0.72), "hole": ("L10", 0.5),
        "pressure": ("L11", 0.0), "arrows": ("L11", 0.62), "howmuch": ("L12", 0.0), "fifty": ("L13", 0.55), "rice": ("L14", 0.0),
        "insight": ("L15", 0.0), "flow": ("L16", 0.4), "equal": ("L17", 0.0), "nopush": ("L17", 0.6),
        "standby": ("L18", 0.0), "outerload": ("L19", 0.0), "crack": ("L19", 0.45), "backup": ("L19", 0.72), "bigrole": ("L20", 0.0),
        "fog": ("L21", 0.0), "outro": ("L22", 0.0), "half": ("L22", 0.55), "jab": ("L23", 0.0), "deadpan": ("L24", 0.0),
        "punch": ("L25", 0.0),
    },
    # 効果音：(名前, きっかけ[, 音量])。鳴らしすぎない（毒舌の音は 2 か所だけ）
    "sfx": [("impact", "gag"), ("whoosh", "gag", 0.8), ("rewind", "rewind"), ("pop", "nothole"),
            ("boop", "deny"), ("whoosh", "explode"), ("slide", "outer", 0.6), ("slide", "middle", 0.6), ("slide", "inner", 0.6),
            ("ding", "hole"), ("riser", "arrows", 0.6), ("impact", "fifty", 0.5), ("boing", "rice"),
            ("sparkle", "flow"), ("ding", "nopush"), ("pop", "standby"),
            ("impact", "crack", 0.6), ("ok", "backup"), ("tick", "fog"), ("boop", "jab"), ("stab", "punch")],
    # BGM：sky（136 BPM）。(きっかけ, ずらす秒, モード)。エンディングは自動
    "music": {"style": "sky", "seed": 6, "sections": [
        ("hook", -1.0, "hook"), ("gag", -0.05, "chaos"), ("rewind", 0.0, "drop"), ("rewind", 1.3, "banter"),
        ("explode", 0.0, "reveal"), ("pressure", 0.0, "explain"), ("rice", 0.0, "banter"), ("insight", 0.0, "explain"),
        ("equal", 0.0, "reveal"), ("standby", 0.0, "banter"), ("outerload", 0.0, "explain"), ("bigrole", 0.0, "banter"),
        ("fog", 0.0, "explain"), ("outro", 0.0, "banter"), ("punch", -0.35, "drop"), ("punch", 0.9, "banter")]},
    # 場面ごとに映像を書き出して保存する区切り
    "segments": ["gag", "hypo", "explode", "pressure", "insight", "standby", "fog", "outro"],
    "extra_files": [],
    "qc_frames": [("hook", 1.5), ("gag", 0.6), ("rewind", 0.5), ("vent", 0.5), ("notout", 0.5), ("outer", 0.6), ("middle", 0.6),
                  ("hole", 0.5), ("arrows", 0.8), ("fifty", 0.6), ("flow", 0.8), ("nopush", 0.6), ("outerload", 0.8),
                  ("backup", 0.6), ("fog", 1.0), ("half", 0.4), ("punch", 0.5)],
    "scenes": [
        ("1 機内（冒頭）", None, "gag", "明るい機内。窓の外は青空と雲。オモテが窓に顔を近づけ、穴を指さす。ウラは右上のワイプ", "BGM hook"),
        ("2 ギャグ：窓が抜ける", "gag", "rewind", "窓がコルクのように「ポンッ」と抜け、オモテが窓へ吸い寄せられる（髪・服がなびく、集中線）。「※ギャグ演出」と表示", "インパクト、風切り音／BGM chaos"),
        ("3 巻き戻し", "rewind", "hypo", "画面が ◀◀ で巻き戻り、ギャグの動きが逆再生で元に戻る。「穴のせいじゃない」で穴に丸", "巻き戻し音／BGM 一瞬止める"),
        ("4 オモテの仮説", "hypo", "explode", "オモテの「換気口説」：穴から空気が外へ出るイメージ（想像）→ ウラが ✕。穴は外とつながっていない", "ブッ（毒舌）／BGM banter"),
        ("5 窓の分解（最大の見せ場）", "explode", "pressure", "3D の窓が 3 枚に分かれて浮かぶ。外側（本命）・真ん中（予備・穴あり）・内側（傷よけ）のラベル。カメラが回り込んで穴に寄る", "スライド音×3、発見音／BGM reveal"),
        ("6 圧力差", "pressure", "insight", "外は空気が薄い・機内は高い気圧。矢印が窓を内側から押す。「手のひら大で約 50kg 分（概算）」、米袋 5 つ", "上昇音、インパクト、ボヨン／BGM explain"),
        ("7 穴の役割に気づく", "insight", "standby", "オモテが気づく：穴から機内の空気がすき間に入り、すき間も機内と同じ気圧に。真ん中の窓の矢印が消える", "きらめき、発見音／BGM explain→reveal"),
        ("8 予備として待機", "standby", "fog", "力を受けるのは外側だけ（矢印）。真ん中に「待機中」。外側にひびが入ると、真ん中が受け止める", "インパクト、成功音／BGM banter・explain"),
        ("9 曇り止め", "fog", "outro", "すき間の湿気が穴から抜けて、曇りが消える", "チック／BGM explain"),
        ("10 オチ", "outro", "endcard", "オモテの負け惜しみ、ウラのツッコミ。最後のひと言の前に BGM を止める", "ブッ、オチの和音／BGM drop→banter"),
        ("11 共通エンディング", "endcard", None, "白い閃光 → 明るい背景に巻き戻しの円弧、大きな「リバース」、タグライン", "BGM を下げる、和音"),
    ],
    "plan_notes": [
        "## 演出の方針",
        "",
        "- 主役の 3D：画面の中央 y≈380〜1200。字幕は中心 y≈1500（Shorts の右側ボタンと下部の説明欄を避ける）。",
        "- オモテは 2D のキャラクターとして画面に登場（表情・ポーズで反応）。ウラは右上のワイプ（話すと口が動く）。",
        "- 窓が抜けるのは **ギャグ演出**（画面に明記）。直後に巻き戻して、ウラが「穴のせいじゃない」と訂正する。穴と窓の破損を因果関係として描かない。",
        "- 窓の構造は **模式図**（機種によって異なる）。圧力の数値は **概算**（客室高度 8,000ft・上空 35,000ft の標準大気で計算）と表示する。",
        "- 「穴があるから安全」とは言わない。安全は窓全体と機体の設計によるもの、と注記する。",
    ],
}

if __name__ == "__main__":
    pipeline.main(__file__, EP)
