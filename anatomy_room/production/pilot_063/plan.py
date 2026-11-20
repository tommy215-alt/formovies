#!/usr/bin/env python3
"""pilot_063「あなたの一生を、24時間にしたら？」（新ドパ設計 v2、templates/DESIGN_MODES.md）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
出典は scripts/pilot_063/fact_check.md。一生＝平均寿命 84.34 年（令和7年簡易生命表の男女の単純平均）を 24 時間に。
1 日の時間の使い方は社会生活基本調査 2021（10 歳以上・週全体の平均）。親と過ごす時間は仮定（画面に出す）。
2026-11-19 v4：テレビをスマホに置き換え、趣味などを時計の分に換算（ユーザーの指示）。ユーザーの OK：台本 v1（scripts/pilot_063/script_v1.md）→ v2（script_v2.md：スマホ・趣味・旅行・料理・読書・友達の時間を追加）。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))

# (id, 話者, 読み, 字幕, 場面の中身)。読みは VOICEVOX が読み違えやすい語をかなで、字幕は漢字のまま
L = [
    # 2026-11-20 冒頭 3 秒の強化（ユーザーの指示「最大限印象に残るような問いかけ」）。前：("L00", "W", "もし、あなたの一生を、24時間に縮めたら。いま、何時？", ["あなたの一生を 24時間にしたら", "いま 何時？"], "open"),
    ("L00", "W", "人生を、1日にしたら。あなたは、いま、何時？", ["人生を1日にしたら", "あなたは いま何時？"], "open"),
    ("L01", "M", "平均寿命は、約84年。生まれた瞬間が0時、84歳で、また0時。", ["平均寿命 約84年", "生まれた瞬間が0時 84歳でまた0時"], "dial"),
    ("L02", "M", "20歳は、朝5時41分。30歳は、8時32分。40歳で、もう11時23分。", ["20歳は 朝5時41分", "30歳は 8時32分", "40歳で もう11時23分"], "ages"),
    ("L03", "M", "この1日で、いちばん長いのは、睡眠。約28年、時計の、7時間54分ぶん。", ["いちばん長いのは 睡眠", "約28年＝7時間54分ぶん"], "sleep"),
    ("L04", "M", "仕事は、約12年。食事だけで、約6年。スマホは、約7年、時計の2時間6分。", ["仕事 約12年", "食事 約6年", "スマホ 約7年＝2時間6分"], "work"),
    ("L05", "M", "通勤と通学だけで、約1年10か月。", ["通勤・通学だけで 約1年10か月"], "commute"),
    ("L06", "M", "趣味と娯楽は、約2年10か月。時計の、48分ぶん。", ["趣味・娯楽 約2年10か月", "時計の48分ぶん"], "hobby"),
    ("L07", "M", "泊まりの旅行は、約1年2か月。たった21分。", ["泊まりの旅行 約1年2か月", "たった21分"], "travel"),
    ("L08", "M", "料理は、女性で1時間18分、男性は14分。本や雑誌は、12分。", ["料理 女性1時間18分・男性14分", "本や雑誌 12分"], "cook"),
    ("L09", "M", "友達と会って話す時間は、たった10分。", ["友達と会って話す時間", "たった10分"], "friends"),
    ("L10", "M", "そして、親と過ごす時間は？", ["そして 親と過ごす時間は？"], "parents"),
    ("L11", "M", "家を出るまでは、毎日のように、一緒。", ["家を出るまでは", "毎日のように 一緒"], "home"),
    ("L12", "M", "18歳で家を出て、お盆と正月に、3日ずつ帰る。1日4時間、一緒にいるとして。", ["18歳で家を出て", "お盆と正月に 3日ずつ帰る", "1日4時間 一緒にいるとして"], "visit"),
    ("L13", "M", "親が87歳まで生きても、残りは、約940時間。", ["親が87歳まで生きても", "残りは 約940時間"], "remain"),
    ("L14", "W", "一生の24時間で、たった1分50秒。あなたの残りの時間は、何に使う？", ["一生の24時間で たった1分50秒", "あなたの残りの時間は 何に使う？"], "end"),
]

SNAP = json.loads((HERE / "assets" / "snap.json").read_text(encoding="utf-8")) if (HERE / "assets" / "snap.json").exists() else {}   # 拍にそろえる間（production_script.py snap）
lines = []
for i, (lid, who, sp, sub, kind) in enumerate(L):
    lines.append(dict(id=lid, who=who, scene=f"s{i:02d}", speech=sp, sub=sub, pause=round(.15 + SNAP.get(lid, 0.0), 3), kind=kind,
                      fact="scripts/pilot_063/fact_check.md"))

doc = {
    "title": "あなたの一生を、24時間にしたら？",
    "theme": "平均寿命 84.34 年を 24 時間の時計に。睡眠・仕事・スマホ・食事・通勤で時計が埋まり、最後に親と過ごす時間は 1 分 50 秒（新ドパ設計 v2）",
    "note": "新ドパ設計 v2（061 型）：冒頭と最後は W 春日部つむぎ、本編は M 青山龍星 ノーマル。BGM は Kevin MacLeod「Funk Game Loop」（CC BY 4.0、061 と同じ並べ替え）。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
    "voices": "v7",
    "voice_override": {"M": {"name": "青山龍星", "credit": "VOICEVOX:青山龍星", "styles": {"normal": 13}, "default_style": "normal", "speed": 1.725, "inton": 1.0},
                       "W": {"name": "春日部つむぎ", "credit": "VOICEVOX:春日部つむぎ", "styles": {"normal": 8}, "default_style": "normal", "speed": 1.35, "inton": 1.0}},
    "gap": 0.05,
    "max_duration": 80.0,
    "meta": {},
    "lines": lines,
}
(HERE / "lines.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
plan = {"lines": [dict(id=l["id"], scene=l["scene"], kind=l["kind"], who=l["who"]) for l in lines], "beat": BEAT,
        "life": 84.34, "ages": {"20": "5:41", "30": "8:32", "40": "11:23"}, "min": {"sleep": 474, "work": 208, "tv": 126, "meal": 99, "commute": 31}, "parent_h": 944, "parent_s": 110, "bars": [["スマホ", 7.4, "phone", "2時間6分"], ["趣味・娯楽", 2.81, "hobby", "48分"], ["旅行", 1.21, "travel", "21分"], ["料理（女性）", 4.57, "cook", "1時間18分"], ["料理（男性）", .82, "cook", "14分"], ["読書", .73, "book", "12分"], ["友達", .59, "friends", "10分"]]}
(HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
print("plan:", len(lines), "行", sum(len(l["speech"]) for l in lines), "字")
