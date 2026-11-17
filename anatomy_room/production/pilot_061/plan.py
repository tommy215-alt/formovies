#!/usr/bin/env python3
"""pilot_061「もしも世界中の現金が、いま金に変わったら」（新ドパ設計 2 本目、templates/DESIGN_MODES.md の 9 つ目）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
数字は scripts/pilot_061/sim/gold.json（gold.py）。出典は scripts/pilot_061/fact_check.md。
現金（お札と硬貨）を、同じ値段の金（1 オンス 3,885 ドル）に置き換える。17 の国と地域。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = json.loads((HERE.parents[1] / "scripts" / "pilot_061" / "sim" / "gold.json").read_text(encoding="utf-8"))
R = {r["name"]: r for r in G["regions"]}
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))

# 地図の上の位置（経度, 緯度）。スイスはユーロ圏と重ならないよう少しずらす
POS = {"アメリカ": (-98, 39), "カナダ": (-106, 58), "メキシコ": (-102, 22), "ブラジル": (-52, -10), "ユーロ圏": (6, 49), "イギリス": (-3, 56),
       "スイス": (12, 40), "ロシア": (90, 62), "サウジアラビア": (45, 23), "アフリカ": (20, 3), "インド": (79, 21), "中国": (104, 34),
       "韓国": (128, 37), "日本": (140, 36), "香港": (116, 19), "インドネシア": (113, -2), "オーストラリア": (134, -25)}

# (id, 話者, 読み, 字幕, 場面の中身)。読みは AivisSpeech が読み違えやすい語をかなで（金→きん、お札→おさつ、富→とみ など）
L = [
    ("L00", "W", "もし、世界中の現金が、いま、金に変わったら？", ["もし世界中の 現金が", "いま金に 変わったら？"], "open"),
    ("L01", "M", "おさつも硬貨も、同じ値段のきんに。じゅうななの国と地域だけで、7万3千トン。人類が掘ったきんの、3分の1です。",
     ["お札も硬貨も 同じ値段の金に", "17の国と地域で 7万3千トン", "人類が掘った金の 3分の1"], "world"),
    ("L02", "M", "いちばん高い山は、アメリカ。約2万トン。国の金庫の、2.4倍。", ["いちばん高い山は アメリカ", "約2万トン 国の金庫の2.4倍"], "us"),
    ("L03", "M", "中国、1万8千トン。ユーロ圏、1万5千トン。日本は、5,800トン。", ["中国 1万8千トン", "ユーロ圏 1万5千トン", "日本は 5,800トン"], "big3"),
    ("L04", "M", "一人あたりにすると、いちいは香港、92グラム。スイス、78グラム。アメリカ、58グラム。",
     ["一人あたりにすると", "1位 香港 92グラム", "スイス 78グラム", "アメリカ 58グラム"], "rank"),
    ("L05", "M", "日本は47グラム。ゴルフボールいっこほど。", ["日本は 47グラム", "ゴルフボール1個ほど"], "jp"),
    ("L06", "M", "韓国25グラム、ロシア14グラム、中国13グラム。", ["韓国 25グラム", "ロシア 14グラム", "中国 13グラム"], "mid"),
    ("L07", "M", "イギリスは、豊かでも14グラム。キャッシュレスが進んだからです。", ["イギリスは 豊かでも14グラム", "キャッシュレスが進んだから"], "uk"),
    ("L08", "M", "インド2.5グラム。ブラジル2.3グラム。アフリカは、1グラム。いちえんだま、いちまいの重さです。",
     ["インド 2.5グラム", "ブラジル 2.3グラム", "アフリカは 1グラム（目安）", "1円玉1枚の重さ"], "low"),
    ("L09", "M", "日本との差は、およそ50倍。", ["日本との差は およそ50倍"], "gap"),
    ("L10", "M", "でも、現金は、まだ平らなほう。いえや株も含めた世界のとみでは、上位1.6パーセントの大人が、半分近くを持っています。",
     ["でも 現金はまだ平らな方", "家や株も含めた 世界の富では", "上位1.6%の大人が 半分近くを持つ"], "wealth"),
    ("L11", "W", "金に変えても、格差は消えない。山の高さが、見えるようになるだけ。", ["金に変えても 格差は消えない", "山の高さが 見えるようになるだけ"], "end"),
]

SNAP = json.loads((HERE / "assets" / "snap.json").read_text(encoding="utf-8")) if (HERE / "assets" / "snap.json").exists() else {}   # 拍にそろえる間（production_script.py snap）
lines = []
for i, (lid, who, sp, sub, kind) in enumerate(L):
    lines.append(dict(id=lid, who=who, scene=f"s{i:02d}", speech=sp, sub=sub, pause=round(.15 + SNAP.get(lid, 0.0), 3), kind=kind,
                      fact="scripts/pilot_061/fact_check.md"))

doc = {
    "title": "もしも世界中の現金が金に変わったら",
    "theme": "世界の現金を同じ値段の金に置き換え、国・地域ごとの山と一人あたりの重さで、格差を見せる（新ドパ設計）",
    "note": "新ドパ設計：冒頭の問いと最後は W 冥鳴ひまり、本編は M 阿井田 茂 Calm 速め。BGM は Funk Game Loop（Kevin MacLeod、CC BY 4.0。小節を並べ替えてサビを冒頭と最後に）。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
    "voices": "v7",
    "voice_override": {"M": {"preset": "aida", "speed": 1.55}, "W": {"speed": 1.35, "inton": 1.0}},
    "gap": 0.05,
    "max_duration": 60.0,
    "meta": {},
    "lines": lines,
}
(HERE / "lines.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
regions = [dict(r, lon=POS[r["name"]][0], lat=POS[r["name"]][1]) for r in G["regions"]]
plan = {"lines": [dict(id=l["id"], scene=l["scene"], kind=l["kind"], who=l["who"]) for l in lines],
        "regions": regions, "total_t": G["total_tonnes"], "all_gold_t": 224200, "us_reserve_t": 8133, "jp_reserve_t": 846, "beat": BEAT}
(HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
print("plan:", len(lines), "行", sum(len(l["speech"]) for l in lines), "字")
