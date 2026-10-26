#!/usr/bin/env python3
"""pilot_009「結局、今回のPHP騒動は何だったの？」（チャンネル「リバース」）の制作スクリプト。

処理の本体は production/common/pipeline.py。ここには、この話だけの設定（きっかけ・効果音・BGM の構成・場面）を書く。
使い方は pipeline.py の冒頭（python3 production_script.py all など）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402

EP = {
    "id": "pilot_009",
    "out": "reverse_009_php.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "maint2": ("L02", 0.45), "calm": ("L03", 0.0), "blame": ("L04", 0.0), "php": ("L05", 0.0), "who": ("L06", 0.0),
        "three": ("L07", 0.3), "lost": ("L08", 0.0), "dive": ("L09", 0.55),
        "kitchen": ("L10", 0.0), "table": ("L11", 0.0), "galley": ("L11", 0.55), "press": ("L12", 0.45),
        "flow": ("L13", 0.0), "check": ("L14", 0.0), "record": ("L14", 0.42), "ret": ("L14", 0.72), "phptag": ("L15", 0.7),
        "chef": ("L16", 0.3), "recipe": ("L17", 0.12), "machine": ("L17", 0.55), "seven": ("L18", 0.5), "many": ("L19", 0.0),
        "vuln": ("L20", 0.0), "holes": ("L20", 0.62), "sleepy": ("L21", 0.0), "jaku": ("L22", 0.5), "shadow": ("L23", 0.1),
        "nologin": ("L23", 0.45), "block": ("L24", 0.0), "side": ("L25", 0.25), "checkall": ("L25", 0.6),
        "notvirus": ("L26", 0.0), "nv": ("L27", 0.0), "neq": ("L27", 0.45), "report": ("L28", 0.0), "precaution": ("L28", 0.5),
        "why": ("L29", 0.0), "gas": ("L30", 0.0), "patch": ("L31", 0.0), "steps": ("L31", 0.22), "pausing": ("L31", 0.78), "gov": ("L31", 0.8),
        "spread": ("L32", 0.0), "sametype": ("L33", 0.0), "homework": ("L33", 0.55),
        "safe": ("L34", 0.0), "overstate": ("L35", 0.0), "oldver": ("L35", 0.6), "replace": ("L36", 0.0), "noupd": ("L36", 0.6),
        "checklist": ("L37", 0.0), "staff": ("L38", 0.0),
        "outro": ("L39", 0.0), "notif": ("L40", 0.5), "later": ("L41", 0.0), "punch": ("L42", 0.0), "tonight": ("L43", 0.0),
    },
    # 効果音：(名前, きっかけ[, 音量[, ずらす秒]])。毒舌の決めの音（zap）は 2 か所まで
    "sfx": [("sweep_up", "t0"), ("tick", "t0", 0.9, 0.2), ("error", "t0", 0.9, 0.42), ("alarm", "t0", 0.8, 0.45), ("impact", "t0", 1.0, 0.48),
            ("glitch", "t0", 0.8, 0.9), ("error", "t0", 0.7, 1.15),
            ("error", "maint2", 0.8), ("error", "maint2", 0.7, 0.55), ("impact", "php", 0.9), ("stab", "php", 0.8), ("tick", "who"),
            ("sweep_down", "dive", 0.8), ("scan", "kitchen", 0.6), ("tick", "press"), ("sweep_up", "flow", 0.6), ("scan", "check", 0.6),
            ("tick", "record"), ("ok", "ret"), ("stab", "phptag", 0.6), ("discover", "seven"),
            ("impact", "holes", 0.8), ("glitch", "holes", 0.6, 0.1), ("tick", "jaku"), ("alarm", "shadow", 0.45), ("brake", "block", 0.8),
            ("scan", "checkall", 0.6), ("zap", "nv", 0.7), ("tick", "neq"), ("ok", "precaution", 0.7),
            ("sweep_down", "gas", 0.6), ("scan", "steps", 0.6), ("tick", "pausing"), ("tick", "gov"),
            ("error", "spread", 0.7, 0.3), ("error", "spread", 0.6, 0.9), ("error", "spread", 0.6, 1.5), ("discover", "homework"),
            ("zap", "overstate", 0.6), ("scan", "replace", 0.6), ("ok", "checklist", 0.7), ("ok", "outro"), ("tick", "notif"),
            ("revswell", "punch", 0.8, -0.7), ("stab", "punch"), ("ok", "tonight", 0.8)],
    # BGM：tech_net（134 BPM、ホ短調）。(きっかけ, ずらす秒, モード)。エンディングは自動
    "music": {"style": "tech_net", "sections": [
        ("t0", 0.0, "intro"), ("hook", 0.0, "drive"), ("maint2", 0.0, "chaos"), ("php", -0.1, "drop"), ("who", 0.0, "drive"),
        ("kitchen", 0.0, "explain"), ("flow", 0.0, "drive"), ("phptag", 0.0, "explain"), ("seven", 0.0, "lift"),
        ("vuln", 0.0, "drive"), ("jaku", 0.0, "explain"), ("block", 0.0, "drive"), ("side", 0.0, "explain"),
        ("notvirus", 0.0, "explain"), ("why", 0.0, "drive"), ("gas", 0.0, "explain"), ("spread", 0.0, "lift"), ("safe", 0.0, "explain"),
        ("outro", 0.0, "drive"), ("punch", -0.35, "drop"), ("tonight", 0.0, "drive")]},
    # 場面ごとに映像を書き出して保存する区切り
    "lead_in": 1.5,  # 冒頭 1.5 秒はセリフなしの「つかみ」（cold）
    "segments": ["hook", "kitchen", "flow", "vuln", "notvirus", "why", "spread", "safe", "outro"],
    "extra_files": [],
    "qc_frames": [("t0", 0.3), ("t0", 1.0), ("hook", 0.8), ("maint2", 0.6), ("php", 0.6), ("three", 0.6), ("table", 1.0), ("press", 0.8),
                  ("ret", 0.6), ("machine", 0.8), ("seven", 0.8), ("holes", 0.6), ("nologin", 0.8), ("block", 0.6), ("checkall", 0.6),
                  ("neq", 0.8), ("precaution", 0.8), ("gas", 0.8), ("steps", 1.2), ("gov", 0.8), ("homework", 0.8), ("oldver", 0.6),
                  ("noupd", 0.6), ("checklist", 1.0), ("notif", 0.6), ("punch", 0.5)],
    "scenes": [
        ("1 つかみ", None, "hook", "スマホの予約ボタンを押した瞬間、画面がメンテナンス中に切り替わる（警告音・揺れ）", "エラー音・警告音／BGM intro"),
        ("2 次々止まる", "hook", "kitchen", "注文アプリ・銀行のスマホも次々メンテナンス。大きな「PHP」が落ちてくる → 「……誰？」", "エラー音、インパクト／BGM chaos → drop"),
        ("3 厨房のたとえ", "kitchen", "flow", "レストランの断面（※たとえ）：客席＝画面、厨房＝サーバー。オモテが注文票を追いかける", "スキャン音／BGM explain"),
        ("4 本物の流れ", "flow", "vuln", "スマホ → サーバー（①空き確認 ②記録 ③結果を返す）→ 予約完了。PHP＝レシピの言葉＋厨房の機械。約7割（W3Techs）", "成功音、発見音／BGM drive → lift"),
        ("5 弱点", "vuln", "notvirus", "機械に穴が 2 つ（10月21日、重大な脆弱性 2件）。裏口の怪しい影（※イメージ）、オモテが扉をふさぐ", "インパクト、警告音／BGM drive"),
        ("6 ウイルスではない", "notvirus", "why", "PHP≠ウイルス、穴がある≠攻撃された、多くは予防の停止", "／BGM explain"),
        ("7 なぜ止めた", "why", "spread", "ガス漏れのたとえ（※たとえ）→ ①版を調べる ②更新 ③確認 の間は一時停止。国の注意喚起", "スキャン音／BGM explain"),
        ("8 同じ型", "spread", "safe", "店の看板が次々メンテナンス、厨房は全部同じ型の機械 → 同じ宿題（※停止したのは一部）", "エラー音、発見音／BGM lift"),
        ("9 PHP は危険？", "safe", "outro", "言葉そのものは危険ではない。問題は穴の残った古い版。更新 → 確認 → 再開", "／BGM explain"),
        ("10 オチ", "outro", "endcard", "予約できた → スマホにも更新 3件 → 「あとで」が穴になる → 今夜やります", "BGM drop → drive"),
        ("11 共通エンディング", "endcard", None, "リバース。世界の仕組みを、はじめから。", "BGM を下げる"),
    ],
    "plan_notes": [
        "## 演出の方針",
        "",
        "- テンプレート：`templates/MASTER_VIDEO_TEMPLATE.md`。可変ルールとして、長さは本編 110 秒前後（ユーザーの指定：約 90〜120 秒）、声は v5（v4 の約 0.9 倍の速さ）。",
        "- たとえ（レストラン・ガス漏れ）を使ったら、直後に本物の仕組みを図で見せる。たとえの場面には「※たとえ」、怪しい影には「※イメージ」。",
        "- 区別して見せる：脆弱性がある／悪用されるおそれ／攻撃を試みる動きの報告／実際の被害。停止＝被害ではない。修正版の公開＝全サービスの対策完了ではない。",
        "- PHP を使うすべてのサイトが止まった・危険だった、と誤解させない（「※停止したのは一部」）。",
    ],
}

if __name__ == "__main__":
    pipeline.main(__file__, EP)
