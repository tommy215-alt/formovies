#!/usr/bin/env python3
"""pilot_063「あなたの一生を、24時間にしたら？」（新ドパ設計 v2、templates/DESIGN_MODES.md）の設計。ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）
出典は scripts/pilot_063/fact_check.md。一生＝平均寿命 84.34 年（令和7年簡易生命表の男女の単純平均）を 24 時間に。
1 日の時間の使い方は社会生活基本調査 2021（10 歳以上・週全体の平均）。親と過ごす時間は仮定（画面に出す）。
2026-11-19 ユーザーの OK：台本 v1（scripts/pilot_063/script_v1.md）→ v2（script_v2.md：スマホ・趣味・旅行・料理・読書・友達の時間を追加）。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEAT = json.loads((HERE / "assets" / "bgm" / "beats.json").read_text(encoding="utf-8"))

# (id, 話者, 読み, 字幕, 場面の中身)。読みは VOICEVOX が読み違えやすい語をかなで、字幕は漢字のまま
L = [
    ("L00", "W", "もし、あなたの一生を、24時間に縮めたら。いま、何時？", ["あなたの一生を 24時間にしたら", "いま 何時？"], "open"),
    ("L01", "M", "平均寿命は、約84年。生まれた瞬間が0時、84歳で、また0時。", ["平均寿命 約84年", "生まれた瞬間が0時 84歳でまた0時"], "dial"),
    ("L02", "M", "20歳は、朝5時41分。30歳は、8時32分。40歳で、もう11時23分。", ["20歳は 朝5時41分", "30歳は 8時32分", "40歳で もう11時23分"], "ages"),
    ("L03", "M", "この1日で、いちばん長いのは、睡眠。約28年、時計の、7時間54分ぶん。", ["いちばん長いのは 睡眠", "約28年＝7時間54分ぶん"], "sleep"),
    ("L04", "M", "仕事は、約12年。テレビなどは、約7年半。食事だけで、約6年。", ["仕事 約12年", "テレビなど 約7年半", "食事 約6年"], "work"),
    ("L05", "M", "通勤と通学だけで、約1年10か月。", ["通勤・通学だけで 約1年10か月"], "commute"),
    ("L06", "M", "スマホでネットを見る時間は、1日約2時間。一生なら、約7年。", ["スマホでネット 1日約2時間", "一生なら 約7年"], "phone"),
    ("L07", "M", "趣味と娯楽は、約2年10か月。泊まりの旅行は、約1年2か月。", ["趣味・娯楽 約2年10か月", "泊まりの旅行 約1年2か月"], "hobby"),
    ("L08", "M", "料理は、女性で約4年半、男性は約10か月。本や雑誌を読むのは、約9か月。", ["料理 女性 約4年半・男性 約10か月", "本や雑誌を読む 約9か月"], "cook"),
    ("L09", "M", "友達と会って話す時間は、たった7か月。", ["友達と会って話す時間", "たった7か月"], "friends"),
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
    "theme": "平均寿命 84.34 年を 24 時間の時計に。睡眠・仕事・テレビ・食事・通勤で時計が埋まり、最後に親と過ごす時間は 1 分 50 秒（新ドパ設計 v2）",
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
        "life": 84.34, "ages": {"20": "5:41", "30": "8:32", "40": "11:23"}, "min": {"sleep": 474, "work": 208, "tv": 128, "meal": 99, "commute": 31}, "parent_h": 944, "parent_s": 110, "bars": [["スマホ", 7.4, "phone"], ["趣味・娯楽", 2.81, "hobby"], ["旅行", 1.21, "travel"], ["料理（女性）", 4.57, "cook"], ["料理（男性）", .82, "cook"], ["読書", .73, "book"], ["友達", .59, "friends"]]}
(HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
print("plan:", len(lines), "行", sum(len(l["speech"]) for l in lines), "字")
