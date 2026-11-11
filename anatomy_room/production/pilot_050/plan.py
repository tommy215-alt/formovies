#!/usr/bin/env python3
"""pilot_050「ティラノサウルスがマラソン大会に出たら、優勝できる？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・時計（号砲からの秒）・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json（音声なしの行）、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
時計 c：[[u, 秒], ...]（u＝ショットの中の進み 0→1）。
ポップアップ ev：[ショットの中の秒, 表示の時刻（秒）, 文, 種類]。種類 T＝ティラノ、R＝ランナー、H＝体温、C＝比べると。
数字は scripts/pilot_050/sim/race.json（race.py）から。条件と仮定は scripts/pilot_050/fact_check.md。
ユーザーの承認（2026-11-11）：構想（scripts/pilot_050/concept.md）の流れのまま「ティラノはOK」。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIM = HERE.parents[1] / "scripts" / "pilot_050" / "sim" / "race.json"
O = json.loads(SIM.read_text(encoding="utf-8"))
V = O["v_max"]                       # 秒速 5.4 m（早歩きの限界）
WR = O["wr"]                         # 先頭のゴール 1:59:30
FIN = O["main"]["time"]              # ティラノのゴール 2:10:14
HOT = O["cases"]["30"]               # 気温 30℃：17.7 km でリタイア
T20 = 20000 / V                      # 20 km の通過（約 1:01:44）
RISE20 = O["main"]["temp_rise"] * T20 / FIN


def hms(t):
    t = int(round(t)); return f"{t // 3600}時間{t % 3600 // 60}分{t % 60}秒"


SHOTS = [
    dict(id="l00", dur=3.0, c=[[0, -5], [1, 0]], what="オープニング：スタートライン。3.7 万人のランナーの列の中に、ゼッケンをつけたティラノサウルスが 1 頭",
         ev=[[.25, 0, "参加者 3.7万人＋1頭", "R"]]),
    dict(id="l01", dur=5.0, c=[[0, 0], [1, 20]], what="号砲。低いカメラ：ランナーの列の上をティラノサウルスの足がまたいでいく", card="spec"),
    dict(id="l02", dur=6.0, c=[[0, 20], [1, 60]], what="脚のアップ。脚の骨に赤い警告（走ると骨が耐えられない）→ 早歩きで進む", card="walk"),
    dict(id="l03", dur=5.5, c=[[0, 300], [1, 900]], what="先頭集団の後ろ。少しずつ離される",
         ev=[[.7, 300, f"先頭 時速{O['wr_kmh']:.0f}km", "R"], [2.4, 600, f"ティラノ 時速{O['v_max_kmh']:.0f}km（早歩き）", "T"]]),
    dict(id="l04", dur=5.5, c=[[0, 1800], [1, 2700]], what="空から：長いランナーの列を、ティラノサウルスがごぼう抜きにした後の位置（先頭のすぐ後ろ）",
         ev=[[.7, 1800, "市民ランナー 平均 時速9km", "R"], [2.6, 2400, "ほぼ全員より 速い", "C"]]),
    dict(id="l05", dur=6.5, c=[[0, T20 - 14], [1, T20 + 16]], what="20 km の給水所。係がバケツを差し出す。湯気の立つ体",
         ev=[[.6, T20 - 10, "体が大きいと 熱が逃げにくい", "H"], [2.4, T20, f"20km 体温+{RISE20:.1f}℃", "H"],
             [4.3, T20 + 8, f"完走には おにぎり{round(O['main']['onigiri'], -1):.0f}個分", "C"]]),
    dict(id="l06", dur=5.0, c=[[0, WR - 14], [.62, WR], [1, WR + 8]], what="ゴール。先頭のランナーがテープを切る。ティラノサウルスはまだ見えない",
         ev=[[3.1, WR, f"優勝 {hms(WR)}", "R"], [4.0, WR, f"ティラノ あと{O['behind_wr_km']:.1f}km", "T"]]),
    dict(id="l07", dur=5.5, c=[[0, FIN - 12], [.5, FIN], [1, FIN]], what="ティラノサウルスがゴールの門をくぐる（門より背が低い姿勢で）", card="goal"),
    dict(id="l08", dur=6.5, c=[[0, HOT["time"] - 45], [.6, HOT["time"]], [1, HOT["time"]]], what="もし夏だったら：強い日ざしの下、歩みが遅くなり、日かげに座りこむ",
         ev=[[.5, HOT["time"] - 40, f"もし 気温{HOT['air']}℃だったら", "C"], [3.9, HOT["time"], f"{HOT['km']:.1f}kmで リタイア", "H"],
             [5.0, HOT["time"], "体温+3℃で 限界", "H"]]),
    dict(id="l09", dur=4.5, c=[[0, FIN], [1, FIN]], what="結果：優勝はできない。でも上位 0.1%（完走メダルをかけたティラノサウルス）", card="result"),
    dict(id="l10", dur=2.5, c=[[0, -5], [1, -2.5]], what="次の大会のスタートライン（冒頭につながる）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    title = "ティラノサウルスはマラソンで優勝できる？"
    data = {"title": title, "theme": "ティラノサウルスがマラソン大会に出たら、優勝できる？（もしも設計）",
            "note": "もしも設計の既定（タイトルの帯つき）：ナレーションなし（silent_ext）、情報はポップアップ、BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "silent": True, "gap": 0.0, "max_duration": 60.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "sim": O, "v": V, "wr": WR, "fin": FIN, "t20": T20, "n": 36697,
            "hot": {"air": HOT["air"], "time": HOT["time"], "km": HOT["km"]}, "fin_text": hms(FIN), "wr_text": hms(WR)}
    (HERE / "blender").mkdir(exist_ok=True)
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、本編 {sum(s['dur'] for s in SHOTS):.1f} 秒、ゴール {hms(FIN)}、20 km で +{RISE20:.2f}℃")
    for s in SHOTS:
        for e in s.get("ev", []):
            print("  ", s["id"], e[2])


if __name__ == "__main__":
    main()
