#!/usr/bin/env python3
"""pilot_064「同じ赤ちゃんが、違う国に生まれたら？」（新ドパ設計 v2、templates/DESIGN_MODES.md）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
出典は scripts/pilot_064/fact_check.md（世界銀行 WDI 2026-11-11 更新・厚生労働省 第 4 回生命表）。
2026-11-19 ユーザーの OK：台本 v1（scripts/pilot_064/script_v1.md）。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))

# (id, 話者, 読み, 字幕, 場面の中身)。読みは VOICEVOX が読み違えやすい語をかなで、字幕は漢字のまま
L = [
    ("L00", "W", "もし、生まれる国を、くじで引くとしたら。あなたは、どこを引く？", ["生まれる国を くじで引いたら", "あなたは どこを引く？"], "open"),
    ("L01", "M", "世界で1年に生まれる赤ちゃんは、約1億3千万人。日本に生まれるのは、約190人に1人。", ["世界で1年に生まれる赤ちゃん 約1億3千万人", "日本に生まれるのは 約190人に1人"], "crowd"),
    ("L02", "M", "同じ赤ちゃんを、4つの国に置いてみる。日本、アメリカ、インド、そして、アフリカのチャド。", ["同じ赤ちゃんを 4つの国に", "日本", "アメリカ", "インド", "そして アフリカのチャド"], "four"),
    ("L03", "M", "平均寿命は、日本84年、アメリカ79年、インド72年。チャドは、55年。", ["平均寿命", "日本 84年", "アメリカ 79年", "インド 72年", "チャドは 55年"], "life"),
    ("L04", "M", "生まれた場所だけで、約29年。人生の、3分の1。", ["生まれた場所だけで 約29年", "人生の 3分の1"], "gap"),
    ("L05", "M", "5歳まで生きられない子は、日本で約400人に1人。チャドでは、約10人に1人。", ["5歳まで生きられない子", "日本 約400人に1人", "チャド 約10人に1人"], "u5"),
    ("L06", "M", "18歳までに学校で学べる年数は、日本で約14年。チャドは、約5年。", ["18歳までに学校で学べる年数", "日本 約14年", "チャド 約5年"], "school"),
    ("L07", "M", "1人あたりの所得は、約40倍。チャドの1年分を、日本では、ここのかで稼ぐ。", ["1人あたりの所得 約40倍", "チャドの1年分を 日本では9日で稼ぐ"], "income"),
    ("L08", "M", "赤ちゃんは、まだ何もしていない。違うのは、生まれた場所だけ。", ["赤ちゃんは まだ何もしていない", "違うのは 生まれた場所だけ"], "same"),
    ("L09", "M", "しかも、くじは場所だけじゃない。100年前の日本の平均寿命は、約43年。いまのチャドより、短い。", ["くじは 場所だけじゃない", "100年前の日本 平均寿命 約43年", "いまのチャドより 短い"], "past"),
    ("L10", "M", "同じ国でも、生まれた時代で、人生は変わる。", ["同じ国でも", "生まれた時代で 人生は変わる"], "era"),
    ("L11", "W", "あなたが選んでいない、その幸運。あなたは、何に使う？", ["あなたが選んでいない その幸運", "あなたは 何に使う？"], "end"),
]

SNAP = json.loads((HERE / "assets" / "snap.json").read_text(encoding="utf-8")) if (HERE / "assets" / "snap.json").exists() else {}   # 拍にそろえる間（production_script.py snap）
lines = []
for i, (lid, who, sp, sub, kind) in enumerate(L):
    lines.append(dict(id=lid, who=who, scene=f"s{i:02d}", speech=sp, sub=sub, pause=round(.15 + SNAP.get(lid, 0.0), 3), kind=kind,
                      fact="scripts/pilot_064/fact_check.md"))

doc = {
    "title": "同じ赤ちゃんが、違う国に生まれたら？",
    "theme": "同じ金の赤ちゃんを日本・アメリカ・インド・チャドに置くと、寿命・5歳まで生きる割合・学ぶ年数・所得が大きく違う。100年前の日本は、いまのチャドより短かった（新ドパ設計 v2）",
    "note": "新ドパ設計 v2（061 型）：冒頭と最後は W 春日部つむぎ、本編は M 青山龍星 ノーマル。BGM は JMHBM「Dance the Night Away」（CC BY 4.0、062・063 と同じ）。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
    "voices": "v7",
    "voice_override": {"M": {"name": "青山龍星", "credit": "VOICEVOX:青山龍星", "styles": {"normal": 13}, "default_style": "normal", "speed": 1.725, "inton": 1.0},
                       "W": {"name": "春日部つむぎ", "credit": "VOICEVOX:春日部つむぎ", "styles": {"normal": 8}, "default_style": "normal", "speed": 1.35, "inton": 1.0}},
    "gap": 0.05,
    "max_duration": 80.0,
    "meta": {},
    "lines": lines,
}
(HERE / "lines.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
C = [["日本", 84.04, "jp"], ["アメリカ", 78.89, "us"], ["インド", 72.24, "in"], ["チャド", 55.24, "td"]]
plan = {"lines": [dict(id=l["id"], scene=l["scene"], kind=l["kind"], who=l["who"]) for l in lines], "beat": BEAT,
        "countries": C, "u5": {"jp": 417, "td": 10}, "school": {"jp": 13.64, "td": 5.31}, "gni": {"jp": 38340, "td": 970}, "days": 9,
        "past": [["1920年代", 42.6], ["1950年ごろ", 61.3], ["いま", 84.04]]}
(HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
print("plan:", len(lines), "行", sum(len(l["speech"]) for l in lines), "字")
