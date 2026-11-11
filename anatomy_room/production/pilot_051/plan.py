#!/usr/bin/env python3
"""pilot_051「猫 何匹で、新幹線は動く？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・猫の数・新幹線の速さ・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json（音声なしの行）、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
猫の数 n：[[u, 匹], ...]（u＝ショットの中の進み 0→1）。速さ v：時速 km（左上の札）。
ポップアップ ev：[ショットの中の秒, 文, 種類]。種類 N＝猫、S＝新幹線、C＝比べると、Z＝ひと休み。
数字は scripts/pilot_051/sim/cats.json（cats.py）から。条件と仮定は scripts/pilot_051/fact_check.md。
ユーザーの承認（2026-11-11）：構想 v2（蝶と 650 万匹をやめ、坂でじわじわ増やす、休憩と昼寝で癒やす）で「両方動画化を進めて」。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIM = HERE.parents[1] / "scripts" / "pilot_051" / "sim" / "cats.json"
O = json.loads(SIM.read_text(encoding="utf-8"))
N0 = round(O["cats_start"], -1)          # 動き出す 約 1,070 → 1,070 匹（画面は「約1,100匹」）
NR = round(O["cats_run"], -1)            # 引き続ける 約 2,230 匹
G = O["cats_grade"]                      # 坂ごとの匹数（1,000 m で x m のぼる）
NG = round(G["20"], -1)                  # 3.7 万匹
KMH = O["speed_kmh"]


def man(n):
    return f"{n / 10000:.1f}万匹".replace(".0万", "万")


SHOTS = [
    dict(id="l00", dur=3.0, n=[[0, 1], [1, 1]], v=0, what="オープニング：青空の下、16 両の白い新幹線。その鼻先で、胴輪をつけた猫が 1 匹、綱をぴんと張って引いている",
         ev=[[.25, "1匹 4kg vs 700トン", "C"]]),
    dict(id="l01", dur=5.0, n=[[0, 1], [1, 1]], v=0, what="猫の顔のアップ（踏んばる前足）→ 引いて見上げる車体", card="spec"),
    dict(id="l02", dur=5.0, n=[[0, 100], [1, 100]], v=0, what="100 匹に増える。びくともしない。あくびをする猫、毛づくろいを始める猫",
         ev=[[.4, "100匹 → びくともしない", "N"], [2.4, "動かすには 2.1トン分の力", "S"]]),
    dict(id="l03", dur=6.0, n=[[0, 100], [.55, N0], [1, N0 + 30]], v=0, what="猫がどんどん増える。車輪のアップ：ゆっくり回りはじめる",
         ev=[[.6, "猫を どんどん増やす", "N"], [3.4, "約1,100匹で 動いた", "S"], [4.4, "鉄の車輪は 転がりやすい", "C"]]),
    dict(id="l04", dur=5.5, n=[[0, NR], [1, NR]], v=KMH, what="猫の列と並んで進むカメラ。新幹線がのろのろ進む。しっぽが揺れる",
         ev=[[.5, "引き続けるには 2,200匹", "N"], [2.6, f"時速{KMH:.1f}km（歩く速さ）", "S"]]),
    dict(id="l05", dur=6.0, n=[[0, NR], [1, NR]], v=0, what="休憩：線路わきの草の上。丸くなる猫、のびをする猫、水を飲む猫、綱にじゃれる子猫。車体の影で涼む",
         ev=[[.6, "ひと休み", "Z"], [3.2, f"猫の列 {O['line_m']['run']:.0f}m", "N"]]),
    dict(id="l06", dur=7.5, n=[[0, NR], [.12, NR], [.3, 5000], [.5, round(G["5"], -2)], [.72, round(G["10"], -2)], [.9, NG], [1, NG]], v=0,
         what="坂。新幹線が止まる → 猫が横から、後ろから、じわじわ加わっていく。カメラは少しずつ高くなり、最後は線路を埋める猫の帯",
         ev=[[.4, "坂（1,000mで20m のぼる）", "S"], [3.0, f"{man(round(G['5'], -2))}", "N"], [4.6, f"{man(round(G['10'], -2))}", "N"],
             [6.4, f"列の長さ {round(O['line_m']['grade20'], -2):.0f}m", "N"]], big=[6.0, f"{man(NG)}"]),
    dict(id="l07", dur=5.5, n=[[0, NG], [1, NG]], v=0, what="昼寝：日なたの屋根の上、線路わき、車体の影で、猫たちが丸くなって寝ている。寝息でおなかが上下する。耳がぴくっと動く",
         ev=[[.6, "猫は 1日12〜16時間 寝る", "Z"], [3.0, "歩くのは 1日10時間", "N"]]),
    dict(id="l08", dur=5.0, n=[[0, NR], [1, NR]], v=0, what="東京 → 新大阪の線の図（上を猫の印がゆっくり進む、途中で寝る印）",
         ev=[[.5, f"東京→新大阪 約{O['days'] / 7:.0f}週間", "S"], [2.5, "新幹線なら 2時間21分", "C"]]),
    dict(id="l09", dur=4.5, n=[[0, N0], [1, N0]], v=0, what="結果：動くのは 約 1,100 匹、大阪まで 約 3 週間", card="result"),
    dict(id="l10", dur=2.5, n=[[0, 1], [1, 1]], v=0, what="群れが散り、最初の 1 匹だけが残って綱を引く（冒頭につながる）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    title = "猫 何匹で、新幹線は動く？"
    data = {"title": title, "theme": "猫 何匹で、新幹線は動く？（もしも設計）",
            "note": "もしも設計の既定（タイトルの帯つき）：ナレーションなし（silent_ext）、情報はポップアップ、BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "silent": True, "gap": 0.0, "max_duration": 60.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "sim": O, "n0": N0, "nr": NR, "ng": NG, "kmh": KMH}
    (HERE / "blender").mkdir(exist_ok=True); (HERE / "assets").mkdir(exist_ok=True)
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、本編 {sum(s['dur'] for s in SHOTS):.1f} 秒、動く {N0:.0f} 匹、引き続ける {NR:.0f} 匹、坂 {NG:.0f} 匹")
    for s in SHOTS:
        for e in s.get("ev", []):
            print("  ", s["id"], e[1])
        if s.get("big"):
            print("  ", s["id"], "big", s["big"][1])


if __name__ == "__main__":
    main()
