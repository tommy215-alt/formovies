#!/usr/bin/env python3
"""pilot_066「選ばれなかった子犬は、どこへ行く？」（新ドパ設計 v2、templates/DESIGN_MODES.md）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
出典は scripts/pilot_066/fact_check.md（東京地裁 平成25年3月14日判決・総務省の通知・報道）。
2026-11-20 ユーザーの OK：台本 v1（scripts/pilot_066/script_v1.md）→ 同日 v2（script_v2.md、「なんで選挙権がなかったのか、なぜ違憲判決が出たのかまで」「冒頭をもうちょい強烈に」）。「知らなかったけど、人権とか生活について考えるようなテーマ」「説教臭くしない」
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))

# (id, 話者, 読み, 字幕, 場面の中身)。読みは VOICEVOX が読み違えやすい語をかなで、字幕は漢字のまま
L = [   # 2026-11-21 ユーザーの OK：scripts/pilot_066/script_v1.md
    ("L00", "W", "ショーケースの子犬。選ばれなかった子は、どこへ行く？", ["ショーケースの 子犬", "選ばれなかった子は どこへ行く？"], "open"),
    ("L01", "M", "店の子犬は、ブリーダーのもとで生まれる。母犬が産むのは、一生で、6回まで。", ["店の子犬は ブリーダーのもとで生まれる", "母犬が産むのは 一生で6回まで"], "breed"),
    ("L02", "M", "この回数が、数で決まったのは、2022年。", ["この回数が 数で決まったのは", "2022年"], "rule"),
    ("L03", "M", "繁殖する業者のもとでは、子犬の約18匹に1匹が、売られる前に死んでいた。", ["繁殖する業者のもとでは", "子犬の約18匹に1匹が", "売られる前に死んでいた"], "death"),
    ("L04", "M", "2013年から、自治体は、業者が持ち込む犬猫の、ひきとりを、断れるようになった。", ["2013年から 自治体は", "業者が持ち込む犬猫の引き取りを", "断れるようになった"], "refuse"),
    ("L05", "M", "翌年の秋。栃木の、かせんじきと山の中で、70匹を超える犬の死骸が見つかった。", ["翌年の秋", "栃木の河川敷と山の中で", "70匹を超える犬の死骸"], "river"),
    ("L06", "M", "人気の犬種ばかり。雌の多くに、何度も出産した跡があった。", ["人気の犬種ばかり", "雌の多くに 何度も出産した跡"], "tags"),
    ("L07", "M", "2021年には、長野で、450匹以上の犬を狭いケージに積んでいた繁殖業者が、逮捕された。", ["2021年 長野", "450匹以上の犬を 狭いケージに", "繁殖業者が逮捕された"], "stack"),
    ("L08", "M", "一方で、ペットショップで、家族に出会えた人もいる。殺処分は、20年で、約39万匹から、約7千匹に減った。", ["一方で ペットショップで", "家族に出会えた人もいる", "殺処分は 20年で", "約39万匹から 約7千匹に"], "home"),
    ("L09", "M", "フランスは、2024年から、店で犬と猫を売ることをやめた。", ["フランスは 2024年から", "店で犬と猫を売るのをやめた"], "france"),
    ("L10", "W", "かわいいを、店で買う。その裏で、何匹が、生まれているんだろう。", ["“かわいい”を 店で買う", "その裏で 何匹が生まれているんだろう"], "end"),
]

SNAP = json.loads((HERE / "assets" / "snap.json").read_text(encoding="utf-8")) if (HERE / "assets" / "snap.json").exists() else {}   # 拍にそろえる間（production_script.py snap）
lines = []
for i, (lid, who, sp, sub, kind) in enumerate(L):
    lines.append(dict(id=lid, who=who, scene=f"s{i:02d}", speech=sp, sub=sub, pause=round(.15 + SNAP.get(lid, 0.0), 3), kind=kind,
                      fact="scripts/pilot_066/fact_check.md"))

doc = {
    "title": "選ばれなかった子犬は、どこへ行く？",
    "theme": "ペットショップの賛否：繁殖の上限、売られる前の死、引き取り拒否のあとの遺棄、劣悪な繁殖業者、そして殺処分の減少とフランスの禁止。最後は買う側の“かわいい”を問う（新ドパ設計 v2）",
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
plan = {"lines": [dict(id=l["id"], scene=l["scene"], kind=l["kind"], who=l["who"]) for l in lines], "beat": BEAT}
(HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
print("plan:", len(lines), "行", sum(len(l["speech"]) for l in lines), "字")
