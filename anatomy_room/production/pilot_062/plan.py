#!/usr/bin/env python3
"""pilot_062「人類のスポーツ記録、いちばん"ありえない"のは？」（新ドパ設計 v2、templates/DESIGN_MODES.md）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
出典は scripts/pilot_062/fact_check.md。物差しは偏差値（＝50＋10×z、z は平均から標準偏差の何倍離れているか）。
z：Charles Davis『The Best of the Best』（Discover の記事の本文で確認）ブラッドマン 4.4・ペレ 3.7・カッブ 3.6、Anantha Narayanan（ESPNcricinfo の本文）ブラッドマン 6.6。
2026-11-18 ユーザーの指示：クリケットのルールを少し挟む／打率は「アウト 1 回までに取る点の平均」と言い換える／最後は称える（格が違う）。
2026-11-19 v2（ユーザーの指示）：ボルトも偏差値に（歴代上位 25 人の自己ベストで計算＝85）、ジョーダン 84・ニクラウス 85 を足す、最後の打席・116・18 万人に 1 人は削る、最後は偏差値 94 で締める。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))

# (id, 話者, 読み, 字幕, 場面の中身)。読みは VOICEVOX が読み違えやすい語をかなで、字幕は漢字のまま
L = [
    # 2026-11-20 冒頭 3 秒の強化（ユーザーの指示「最大限印象に残るような問いかけ」）。前：("L00", "W", "もし、人類のスポーツ記録を、全部、同じ物差しで比べたら。いちばん、ありえないのは？",      ["人類のスポーツ記録", "いちばん ありえないのは？"], "open"),
    ("L00", "W", "スポーツ史上、最強のバグ。人類の記録を、全部、同じ物差しで比べたら。どの記録だと思う？", ["スポーツ史上 最強のバグ", "全部 同じ物差しで 比べたら", "どの記録だと 思う？"], "open"),
    ("L01", "M", "物差しは、偏差値。一流の選手たちの中で、どれだけ、飛び抜けているか。", ["物差しは 偏差値", "一流の選手の中で どれだけ飛び抜けているか"], "rule"),
    ("L02", "M", "ボルトの、9秒58。歴代で速い25人の中で、偏差値、85。", ["ボルト 100m 9秒58", "歴代トップ25人の中で 偏差値85"], "bolt"),
    ("L03", "M", "バスケの、マイケル・ジョーダン。1試合の平均得点で、偏差値、84。", ["バスケ マイケル・ジョーダン", "1試合の平均得点 偏差値84"], "jordan"),
    ("L04", "M", "ゴルフの、ジャック・ニクラウス。メジャー優勝の数で、偏差値、85。", ["ゴルフ ジャック・ニクラウス", "メジャー優勝の数 偏差値85"], "nicklaus"),
    ("L05", "M", "野球の、タイカッブ。打率で、偏差値、86。", ["野球 タイ・カッブ", "打率 偏差値86"], "cobb"),
    ("L06", "M", "サッカーの、ペレ。1試合あたりのゴールで、偏差値、87。", ["サッカー ペレ", "1試合あたりのゴール 偏差値87"], "pele"),
    ("L07", "M", "歴史に残る天才たちでも、84から、87。", ["歴史に残る天才たちでも", "偏差値 84〜87"], "cluster"),
    ("L08", "M", "でも、ひとりだけ、別格がいる。クリケットの、ドン・ブラッドマン。", ["でも ひとりだけ 別格がいる", "クリケット ドン・ブラッドマン"], "reveal"),
    ("L09", "M", "クリケットは、投げられた球を、打って、走って、点を取る競技。打者の後ろには、3本の柱。", ["投げられた球を 打って走って 点を取る", "打者の後ろに 3本の柱（ウィケット）"], "crk1"),
    ("L10", "M", "球が柱に当たるか、打球を捕られたら、アウト。アウトになるまで、何点でも、取り続けられる。",
     ["球が柱に当たる・打球を捕られる → アウト", "アウトまで 何点でも取り続けられる"], "crk2"),
    ("L11", "M", "成績は、アウト1回までに取る、点の平均。名選手でも、60点前後。", ["成績＝アウト1回までに取る 点の平均", "名選手でも 60点前後"], "avg"),
    ("L12", "M", "ブラッドマンは、99.94点。名選手の、1.6倍以上。", ["ブラッドマンは 99.94点", "名選手の 1.6倍以上"], "tower"),
    ("L13", "M", "偏差値に直すと、94。天才たちより、さらに、7つもうえ。", ["偏差値に直すと 94", "天才たちより さらに7つも上"], "z"),
    ("L14", "W", "偏差値、94。人類のスポーツで、いちばん、格が違う数字。", ["偏差値 94", "人類のスポーツで いちばん格が違う数字"], "end"),
]

SNAP = json.loads((HERE / "assets" / "snap.json").read_text(encoding="utf-8")) if (HERE / "assets" / "snap.json").exists() else {}   # 拍にそろえる間（production_script.py snap）
lines = []
for i, (lid, who, sp, sub, kind) in enumerate(L):
    lines.append(dict(id=lid, who=who, scene=f"s{i:02d}", speech=sp, sub=sub, pause=round(.15 + SNAP.get(lid, 0.0), 3), kind=kind,
                      fact="scripts/pilot_062/fact_check.md"))

lines[0]["speed"] = 1.45   # 冒頭の問いを元の長さ（L01 の開始）に収める

doc = {
    "title": "人類のスポーツ記録、いちばん\"ありえない\"のは？",
    "theme": "競技をまたいで、偏差値（平均から標準偏差の何倍離れているか）で記録を比べる。ブラッドマンの 99.94（新ドパ設計 v2）",
    "note": "新ドパ設計 v2（061 型）：冒頭と最後は W 春日部つむぎ、本編は M 青山龍星 ノーマル。BGM は JMHBM「Dance the Night Away」（FMA、CC BY 4.0）、ドラムが入る瞬間を 0 秒に。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
    "voices": "v7",
    "voice_override": {"M": {"name": "青山龍星", "credit": "VOICEVOX:青山龍星", "styles": {"normal": 13}, "default_style": "normal", "speed": 1.725, "inton": 1.0},
                       "W": {"name": "春日部つむぎ", "credit": "VOICEVOX:春日部つむぎ", "styles": {"normal": 8}, "default_style": "normal", "speed": 1.35, "inton": 1.0}},
    "gap": 0.05,
    "max_duration": 75.0,
    "meta": {},
    "lines": lines,
}
(HERE / "lines.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
plan = {"lines": [dict(id=l["id"], scene=l["scene"], kind=l["kind"], who=l["who"]) for l in lines], "beat": BEAT,
        "dev": {"ブラッドマン": 4.4, "ペレ": 3.7, "カッブ": 3.6, "ニクラウス": 3.5, "ジョーダン": 3.4, "ボルト": 3.49}, "avg": 99.94, "runs": 6996, "outs": 70}
(HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
print("plan:", len(lines), "行", sum(len(l["speech"]) for l in lines), "字")
