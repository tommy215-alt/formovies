#!/usr/bin/env python3
"""pilot_061「もしも世界中の現金が、いま金に変わったら」（新ドパ設計 2 本目、templates/DESIGN_MODES.md の 9 つ目）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
数字は scripts/pilot_061/sim/gold.json（gold.py）。出典は scripts/pilot_061/fact_check.md。
お金（マネーストック：現金・預金。v2 でユーザーの指示）を、同じ値段の金（1 オンス 3,885 ドル）に置き換える。17 の国と地域。
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

# v2（ユーザーの指示）：現金だけでなく、預金・キャッシュレスも含む「お金」（マネーストック）。数字は gold.json の broad。
# 読みは AivisSpeech が読み違えやすい語をかなで（金→きん、富→とみ など）。字幕は漢字のまま
L = [
    ("L00", "W", "もし、世界中のお金が、いま、金に変わったら？", ["もし世界中の お金が", "いま金に 変わったら？"], "open"),
    ("L01", "M", "現金も、預金も、スマホの残高も。17の国と地域で、107万トン。人類が掘ったきんの、4.8倍。きんが、まるで足りません。",
     ["現金も 預金も スマホの残高も", "17の国と地域で 107万トン", "人類が掘った金の 4.8倍", "金が まるで足りない"], "world"),
    ("L02", "M", "いちばん多いのは、中国。43万トン。", ["いちばん多いのは 中国", "43万トン"], "china"),
    ("L03", "M", "アメリカ、19万トン。ユーロ圏、16万トン。日本は、8万3千トン。", ["アメリカ 19万トン", "ユーロ圏 16万トン", "日本は 8万3千トン"], "big3"),
    ("L04", "M", "一人あたりでは、1位スイス、2位香港、どちらも1.3キロ。日本は4位、671グラム。",
     ["一人あたりでは", "1位スイス 2位香港 どちらも1.3キロ", "日本は4位 671グラム"], "rank"),
    ("L05", "M", "直径4センチ。ピンポン玉ほどの、きんの玉です。", ["直径4センチ", "ピンポン玉ほどの 金の玉"], "jp"),
    ("L06", "M", "中国、306グラム。ロシア、95グラム。インド、20グラム。", ["中国 306グラム", "ロシア 95グラム", "インド 20グラム"], "mid"),
    ("L07", "M", "アフリカは、およそ9グラム。直径1センチの粒です。", ["アフリカは およそ9グラム（推計）", "直径1センチの粒"], "low"),
    ("L08", "M", "日本との差は、およそ75倍。", ["日本との差は およそ75倍"], "gap"),
    ("L09", "M", "でも、お金は、とみの一部。いえや株も含めた世界のとみでは、上位1.6パーセントの大人が、半分近くを持っています。",
     ["でも お金は 富の一部", "家や株も含めた 世界の富では", "上位1.6%の大人が 半分近くを持つ"], "wealth"),
    ("L10", "W", "きんに変えても、格差は消えない。数字では見えなかった差が、目に見えるようになるだけ。", ["金に変えても 格差は消えない", "数字では 見えなかった差が", "目に見えるようになるだけ"], "end"),
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
regions = [dict(r, lon=POS[r["name"]][0], lat=POS[r["name"]][1]) for r in G["broad"]]
plan = {"lines": [dict(id=l["id"], scene=l["scene"], kind=l["kind"], who=l["who"]) for l in lines],
        "regions": regions, "total_t": G["broad_total_t"], "all_gold_t": 224200, "us_reserve_t": 8133, "jp_reserve_t": 846, "beat": BEAT}
(HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
print("plan:", len(lines), "行", sum(len(l["speech"]) for l in lines), "字")
