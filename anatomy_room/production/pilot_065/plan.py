#!/usr/bin/env python3
"""pilot_065「2013年まで、選挙に行けなかった日本人」（新ドパ設計 v2、templates/DESIGN_MODES.md）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
出典は scripts/pilot_065/fact_check.md（東京地裁 平成25年3月14日判決・総務省の通知・報道）。
2026-11-20 ユーザーの OK：台本 v1（scripts/pilot_065/script_v1.md）→ 同日 v2（script_v2.md、「なんで選挙権がなかったのか、なぜ違憲判決が出たのかまで」「冒頭をもうちょい強烈に」）。「知らなかったけど、人権とか生活について考えるようなテーマ」「説教臭くしない」
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))

# (id, 話者, 読み, 字幕, 場面の中身)。読みは VOICEVOX が読み違えやすい語をかなで、字幕は漢字のまま
L = [   # v2（2026-11-20 ユーザーの OK：scripts/pilot_065/script_v2.md）
    ("L00", "W", "罪を犯していないのに、選挙権を奪われた、にほんじんが、13万人いた。", ["罪を犯して いないのに", "選挙権を 奪われた 日本人が", "13万人いた"], "open"),
    ("L01", "M", "2013年まで、法律に、こう書いてあった。せいねんひこうけんにんは、選挙権を有しない。", ["2013年まで 法律に こう書いてあった", "成年被後見人は", "選挙権を有しない"], "law"),
    ("L02", "M", "茨城の、知的障害のある女性。20歳から25年、選挙をほとんど休まなかった。", ["茨城の 知的障害のある女性", "20歳から25年", "選挙をほとんど休まなかった"], "walk"),
    ("L03", "M", "でも、数の計算が苦手。2007年、お金を心配した父が、こうけんにんになった。", ["でも 数の計算が苦手", "2007年 お金を心配した父が", "後見人になった"], "guard"),
    ("L04", "M", "すると、選挙のはがきが、届かなくなった。", ["すると", "選挙のはがきが 届かなくなった"], "mail"),
    ("L05", "M", "なぜか。1950年の選挙の法律は、明治からの、きんちさんという制度の人を、選挙から外していた。", ["なぜか", "1950年の選挙の法律は", "明治からの「禁治産」という制度の人を", "選挙から外していた"], "old"),
    ("L06", "M", "2000年、制度は、せいねんこうけんに変わった。でも、選挙から外す決まりは、そのまま残った。", ["2000年 制度は成年後見に変わった", "でも 選挙から外す決まりは", "そのまま残った"], "kept"),
    ("L07", "M", "国の言い分は、判断する力がないと、無効な票や、不正な投票のおそれがある。", ["国の言い分は", "判断する力がないと", "無効な票や 不正な投票のおそれがある"], "state"),
    ("L08", "M", "彼女は、国を訴えた。2013年3月、裁判所の答えは、違憲。", ["彼女は 国を訴えた", "2013年3月", "裁判所の答えは 違憲"], "court"),
    ("L09", "M", "こうけんで見るのは、お金を管理する力。誰に投票するかを選ぶ力とは、別のもの。", ["後見で見るのは お金を管理する力", "誰に投票するかを選ぶ力とは", "別のもの"], "scale"),
    ("L10", "M", "不正を防ぐのに、選挙権を丸ごと奪うしかない、という証拠もない。", ["不正を防ぐのに", "選挙権を丸ごと奪うしかない", "という証拠もない"], "proof"),
    ("L11", "M", "2か月後、法律は、全会一致で変わった。その夏の選挙から、彼女も、また投票できる。", ["2か月後", "法律は 全会一致で変わった", "その夏の選挙から 彼女も また投票できる"], "diet"),
    ("L12", "W", "当たり前の一票。それは、誰が、決めていたんだろう。", ["当たり前の一票", "それは 誰が決めていたんだろう"], "end"),
]

SNAP = json.loads((HERE / "assets" / "snap.json").read_text(encoding="utf-8")) if (HERE / "assets" / "snap.json").exists() else {}   # 拍にそろえる間（production_script.py snap）
lines = []
for i, (lid, who, sp, sub, kind) in enumerate(L):
    lines.append(dict(id=lid, who=who, scene=f"s{i:02d}", speech=sp, sub=sub, pause=round(.15 + SNAP.get(lid, 0.0), 3), kind=kind,
                      fact="scripts/pilot_065/fact_check.md"))

doc = {
    "title": "2013年まで、選挙に行けなかった日本人",
    "theme": "（v2）罪を犯していないのに選挙権を奪われた。成年後見を受けると選挙権を失う決まりがあった。一度も投票を休まなかった女性が国を訴え、2013年に違憲判決、法律が全会一致で変わった（新ドパ設計 v2）",
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
