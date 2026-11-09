#!/usr/bin/env python3
"""pilot_048「東京に体長500mのポメラニアンが現れたら？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・時計（1 日目 0:00 からの秒）・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json（音声なしの行）、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
時計 c：[[u, 秒], ...]（u＝ショットの中の進み 0→1）。
ポップアップ ev：[ショットの中の秒, 表示の時刻（秒）, 文, 種類]。種類 D＝ポメラニアン、B＝被害、P＝人々、C＝比べると。
末尾に ? が付いたもの（例 "B?"）は計算に入っていない予想で、札に「（予想）」と出す。
数字は scripts/pilot_048/sim/pom.json（pom.py）から。条件と仮定は scripts/pilot_048/fact_check.md。
ユーザーの指示（2026-11-09）：体長 500 m、なるべくリアルに、うんち・散歩・吐息・肉球など細部、最後は東京が全滅。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIM = HERE.parents[1] / "scripts" / "pilot_048" / "sim" / "pom.json"


def hm(h, m, s=0.0):
    return h * 3600 + m * 60 + s


O = json.loads(SIM.read_text(encoding="utf-8"))["out"]
Z0 = hm(7, 21)                       # ハッスルタイムの始まり
ZRATE = O["zoomie_km2"] / (O["zoomie_min"] * 60)   # 1 秒に踏む面積（km²）
FULL = Z0 + O["ward23_km2"] / ZRATE  # 23 区をすべて踏んだ時刻

SHOTS = [
    dict(id="l00", dur=2.6, c=[[0, hm(5, 59, 30)], [1, hm(5, 59, 33)]], what="オープニング：新宿の高層ビルの向こうに座る巨大なポメラニアン。目の高さがスカイツリーと同じ。タイトル 2 行"),
    dict(id="l01", dur=3.6, c=[[0, hm(5, 59, 55)], [1, hm(6, 0, 10)]], what="6:00 夜明けの代々木公園。霧の中に、ふわふわの巨大な影", card="spec"),
    dict(id="l02", dur=3.4, c=[[0, hm(6, 2)], [1, hm(6, 2, 20)]], what="6:02 渋谷のスクランブル交差点：真上から肉球が下りてきて、地面がめり込む",
         ev=[[.7, hm(6, 2, 4), f"肉球 {O['pad_m']:.0f}m・足の幅 {O['paw_m']:.0f}m", "D"], [2.1, hm(6, 2, 13), "一歩ごとに 地面がめり込む", "B"]]),
    dict(id="l03", dur=3.4, c=[[0, hm(6, 5)], [1, hm(6, 6)]], what="6:05 くんくん：濡れた鼻がビルの屋上の高さに。鼻息で車と街路樹が吹き飛ぶ",
         ev=[[.8, hm(6, 5, 15), f"鼻の穴 直径{O['nostril_d_m']:.0f}m", "D"], [1.9, hm(6, 5, 40), f"鼻息 秒速{O['breath_wind_ms']:.0f}m", "D"],
             [2.6, hm(6, 5, 45), "日本で観測された 最大の風を超える", "C"]]),
    dict(id="l04", dur=3.0, c=[[0, hm(6, 8)], [1, hm(6, 8, 15)]], what="6:08 「ワン」：口が開く。窓が震え、人々が走り出す",
         ev=[[.7, hm(6, 8, 4), "ワン！ 23区のどこでも 聞こえる", "D"], [1.8, hm(6, 8, 10), "避難が始まる", "P"]]),
    dict(id="l05", dur=3.4, c=[[0, hm(6, 20)], [1, hm(6, 24)]], what="6:20 散歩：明治通りを歩く（空から、横に並んで追う）",
         ev=[[.6, hm(6, 21), f"歩く速さ 時速{O['walk_kmh']:.0f}km", "D"], [1.9, hm(6, 23), "いつもの散歩は 北海道〜沖縄より長い", "C"]]),
    dict(id="l06", dur=3.6, c=[[0, hm(6, 40)], [1, hm(6, 41, 30)]], what="6:40 うんち：東京ドームのとなりで、しっぽを上げてしゃがむ → 湯気の立つ山",
         ev=[[1.3, hm(6, 40, 50), f"1回 東京ドーム{O['poop_dome']:.1f}杯分", "D"], [2.4, hm(6, 41, 15), f"高さ{O['poop_h_m']:.0f}m 20階建てのビル", "C"]]),
    dict(id="l07", dur=3.2, c=[[0, hm(7, 0)], [1, hm(7, 1, 30)]], what="7:00 マーキング：スカイツリーに片足を上げる → 足もとの川があふれる",
         ev=[[.9, hm(7, 0, 30), f"1回 25mプール{O['pee_pools']:.0f}杯分", "D"], [2.1, hm(7, 1), "隅田川が あふれる", "B?"]]),
    dict(id="l08", dur=3.2, c=[[0, hm(7, 10)], [1, hm(7, 10, 40)]], what="7:10 ブルブル：体を振るたびに毛が飛び、吹雪のように街に降る",
         ev=[[.8, hm(7, 10, 10), f"抜け毛 1本{O['coat_m']:.0f}m", "D"], [2.0, hm(7, 10, 25), "毛が 雪のように降る", "B?"]]),
    dict(id="l09", dur=2.8, c=[[0, hm(7, 15)], [1, hm(7, 16)]], what="7:15 ハァハァ：舌を出す。熱く湿った風",
         ev=[[.8, hm(7, 15, 20), f"ハァハァ 1分に{O['pant_per_min']:.0f}回 38℃の風", "D"]]),
    dict(id="l10", dur=3.0, c=[[0, hm(7, 20)], [1, hm(7, 20, 50)]], what="7:20 遊びのおじぎ（前足を伏せてお尻を上げる）。しっぽが揺れる", card="zoomie"),
    dict(id="l11", dur=3.4, c=[[0, hm(7, 21)], [1, hm(7, 21, 30)]], what="7:21 走り出す：低い位置から。衝撃波で窓が一斉に割れる",
         ev=[[.9, hm(7, 21, 8), f"時速{O['run_kmh']:,.0f}km マッハ{O['run_mach']:.2f}", "D"], [2.0, hm(7, 21, 18), "窓ガラスが 60km先まで割れる", "B"]]),
    dict(id="l12", dur=3.4, c=[[0, hm(7, 26)], [1, hm(7, 58)]], what="7:26〜 空から：23 区に走った跡がぐるぐる増えていく",
         ev=[[.7, hm(7, 30), f"一歩 {O['stride_km']:.1f}km", "D"], [2.0, hm(7, 50), "1km以内の木造の家が こわれる", "B"]]),
    dict(id="l13", dur=2.8, c=[[0, hm(8, 20, 30)], [1, hm(8, 21, 30)]], what="8:21 名所：走り抜けるポメラニアンに東京タワーがなぎ倒される",
         ev=[[1.1, FULL, "23区を すべて踏んだ", "B"]]),
    dict(id="l14", dur=3.0, c=[[0, hm(8, 59)], [1, hm(8, 59, 50)]], what="8:59 走り終えてゴロン（へそ天）。平らになった新宿の上で",
         ev=[[.8, hm(8, 59, 15), "ハッスルタイム 終わり", "D"]]),
    dict(id="l15", dur=3.0, c=[[0, hm(9, 0)], [1, hm(9, 1)]], what="9:00 真上から：平らになった東京", card="end"),
    dict(id="l16", dur=2.4, c=[[0, hm(9, 1)], [1, hm(9, 1, 20)]], what="がれきの上でおすわり、首をかしげる → 冒頭の座った姿につながる（ループ）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    title = "東京に体長500mのポメラニアンが現れたら？"
    data = {"title": title, "theme": title + "（もしも設計）",
            "note": "もしも設計の既定（pilot_045 v2.3＋pilot_047 のタイトルの帯）：ナレーションなし（silent_ext）、情報はポップアップ、BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "silent": True, "gap": 0.0, "max_duration": 60.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "sim": O, "zoom0": Z0, "zrate": ZRATE, "full": FULL}
    (HERE / "blender").mkdir(exist_ok=True)
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、本編 {sum(s['dur'] for s in SHOTS):.1f} 秒、23区をすべて踏む {int(FULL // 3600)}:{int(FULL % 3600 // 60):02d}")


if __name__ == "__main__":
    main()
