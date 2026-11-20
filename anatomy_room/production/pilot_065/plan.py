#!/usr/bin/env python3
"""pilot_065「2013年まで、選挙に行けなかった日本人」（新ドパ設計 v2、templates/DESIGN_MODES.md）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
出典は scripts/pilot_065/fact_check.md（東京地裁 平成25年3月14日判決・総務省の通知・報道）。
2026-11-20 ユーザーの OK：台本 v1（scripts/pilot_065/script_v1.md）。「知らなかったけど、人権とか生活について考えるようなテーマ」「説教臭くしない」
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))

# (id, 話者, 読み, 字幕, 場面の中身)。読みは VOICEVOX が読み違えやすい語をかなで、字幕は漢字のまま
L = [
    ("L00", "W", "2013年まで、選挙に行けない、にほんじんが、約13万人いた。", ["2013年まで 選挙に行けない日本人が", "約13万人いた"], "open"),
    ("L01", "M", "罪を犯したわけじゃない。ある制度を、使っただけ。", ["罪を犯したわけじゃない", "ある制度を 使っただけ"], "door"),
    ("L02", "M", "茨城に住む、知的障害のある女性。選挙は、一度も休まなかった。", ["茨城に住む 知的障害のある女性", "選挙は 一度も休まなかった"], "home"),
    ("L03", "M", "選挙こうほうを読み込んで、両親と、投票所へ。", ["選挙公報を読み込んで", "両親と 投票所へ"], "walk"),
    ("L04", "M", "2007年。お金の管理を心配した父が、こうけんにんになった。", ["2007年", "お金の管理を心配した父が", "後見人になった"], "guard"),
    ("L05", "M", "すると、選挙のはがきが、届かなくなった。", ["すると", "選挙のはがきが 届かなくなった"], "mail"),
    ("L06", "M", "法律には、こう書いてあった。せいねんひこうけんにんは、選挙権を有しない。", ["法律には こう書いてあった", "成年被後見人は", "選挙権を有しない"], "law"),
    ("L07", "M", "お金の計算が苦手なことと、誰に投票するかを選ぶこと。それは、同じこと？", ["お金の計算が苦手なこと", "誰に投票するかを選ぶこと", "それは 同じこと？"], "scale"),
    ("L08", "M", "彼女は、国を訴えた。2013年3月、裁判所は、憲法違反と判断した。", ["彼女は 国を訴えた", "2013年3月", "裁判所は 憲法違反と判断した"], "court"),
    ("L09", "M", "2か月後、法律は、全会一致で変わった。", ["2か月後", "法律は 全会一致で変わった"], "diet"),
    ("L10", "M", "その夏の選挙から、彼女のはがきは、また届くようになった。", ["その夏の選挙から", "彼女のはがきは また届くようになった"], "mail2"),
    ("L11", "W", "当たり前の一票。それは、誰が、決めていたんだろう。", ["当たり前の一票", "それは 誰が決めていたんだろう"], "end"),
]

SNAP = json.loads((HERE / "assets" / "snap.json").read_text(encoding="utf-8")) if (HERE / "assets" / "snap.json").exists() else {}   # 拍にそろえる間（production_script.py snap）
lines = []
for i, (lid, who, sp, sub, kind) in enumerate(L):
    lines.append(dict(id=lid, who=who, scene=f"s{i:02d}", speech=sp, sub=sub, pause=round(.15 + SNAP.get(lid, 0.0), 3), kind=kind,
                      fact="scripts/pilot_065/fact_check.md"))

doc = {
    "title": "2013年まで、選挙に行けなかった日本人",
    "theme": "成年後見を受けると選挙権を失う決まりがあった。一度も投票を休まなかった女性が国を訴え、2013年に違憲判決、法律が全会一致で変わった（新ドパ設計 v2）",
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
