#!/usr/bin/env python3
"""pilot_060「日本終末時計」（新ドパ設計、templates/DESIGN_MODES.md の 9 つ目）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
数字は scripts/pilot_060/sim/clock.json（clock.py）。出典は scripts/pilot_060/fact_check.md。
真夜中（0 秒）＝日本の人が全員いなくなる。人口の 10 分の 1 を失うごとに 1 分近づく。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CL = json.loads((HERE.parents[1] / "scripts" / "pilot_060" / "sim" / "clock.json").read_text(encoding="utf-8"))
E = {e["key"]: e for e in CL["events"]}
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))


def s(k):
    return round(E[k]["sec"])


# (id, 話者, 読み, 字幕, 場面の中身, 時計の出来事キー)
L = [
    ("L00", "W", "もし、日本だけの、終末時計があったら。いま、真夜中まで、何秒？", ["もし 日本だけの終末時計があったら", "いま 真夜中まで何秒？"], "open", None),
    ("L01", "M", "真夜中は、日本の人が、一人もいなくなる時。人口の、10分の1を失うごとに、1分進む。", ["真夜中＝日本の人が一人もいなくなる時", "人口の10分の1を失うごとに 1分進む"], "rule", None),
    ("L02", "M", "737年。天然痘の大流行で、人口の、およそ3割が亡くなったとされます。", ["737年 天然痘の大流行", "人口の およそ3割が亡くなった"], "ev", "H1"),
    ("L03", "M", f"真夜中まで、{s('H1')}秒。", [f"真夜中まで {s('H1')}秒"], "hit", "H1"),
    ("L04", "M", f"1780年代、天明の飢饉。死者は90万人以上。{s('H2')}秒。", ["1780年代 天明の飢饉", f"死者90万人以上 → {s('H2')}秒"], "ev", "H2"),
    ("L05", "M", f"1923年、関東大震災。およそ10万5千人。{s('H3')}秒。", ["1923年 関東大震災", f"約10万5千人 → {s('H3')}秒"], "ev", "H3"),
    ("L06", "M", f"1945年。戦争で、およそ310万人。{s('H4')}秒。", ["1945年 戦争", f"約310万人 → {s('H4')}秒"], "ev", "H4"),
    ("L07", "M", f"2011年、東日本大震災。およそ2万2千人。{s('H5')}秒。", ["2011年 東日本大震災", f"約2万2千人 → {s('H5')}秒"], "ev", "H5"),
    ("L08", "M", "では、いまは。", ["では いまは。"], "now", None),
    ("L09", "M", "戦争も、大きな災害もない。でも、日本の人口は、2070年に、およそ8,700万人と推計。50年で、3割が減る。", ["戦争も 大きな災害もない", "でも 2070年の人口は 約8,700万人（推計）", "50年で 3割が減る"], "decline", "P1"),
    ("L10", "M", f"真夜中まで、{s('P1')}秒。1,300年前の、大流行と、ほぼ同じです。", [f"真夜中まで {s('P1')}秒", "1300年前の大流行と ほぼ同じ"], "hit", "P1"),
    ("L11", "M", f"さらに2120年には、5,000万人を割る。{s('P2')}秒。", ["2120年には 5,000万人を割る（参考推計）", f"→ {s('P2')}秒"], "ev", "P2"),
    ("L12", "W", "日本の時計の針は、いまも、静かに進んでいます。", ["日本の時計の針は", "いまも 静かに進んでいる"], "end", None),
]

SNAP = json.loads((HERE / "assets" / "snap.json").read_text(encoding="utf-8")) if (HERE / "assets" / "snap.json").exists() else {}   # 拍にそろえる間（production_script.py snap）
lines = []
for i, (lid, who, sp, sub, kind, ev) in enumerate(L):
    lines.append(dict(id=lid, who=who, scene=f"s{i:02d}", speech=sp, sub=sub, pause=round(.15 + SNAP.get(lid, 0.0), 3), kind=kind, ev=ev,
                      fact="scripts/pilot_060/fact_check.md"))

doc = {
    "title": "日本終末時計",
    "theme": "もし日本だけの終末時計があったら、歴史の中で真夜中まで何秒だったか（新ドパ設計）",
    "note": "新ドパ設計：冒頭の問いと最後は W 冥鳴ひまり、本編は M 阿井田 茂 Calm 速め。BGM は Movement Proposition（Kevin MacLeod、CC BY 4.0）。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
    "voices": "v7",
    "voice_override": {"M": {"preset": "aida", "speed": 1.55}, "W": {"speed": 1.35, "inton": 1.0}},
    "gap": 0.05,
    "max_duration": 60.0,
    "meta": {},
    "lines": lines,
}
(HERE / "lines.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
plan = {"lines": [dict(id=l["id"], scene=l["scene"], kind=l["kind"], ev=l["ev"], who=l["who"]) for l in lines],
        "events": CL["events"], "real": CL["real"], "beat": BEAT}
(HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
print("plan:", len(lines), "行", sum(len(l["speech"]) for l in lines), "字")
