#!/usr/bin/env python3
"""pilot_053「日本の観測史上最大の記録が、東京で同時に起きたら？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・時計（始まりからの時間）・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
時計 c：[[u, 時間], ...]（u＝ショットの中の進み 0→1）。雪の深さ・水の深さはこの時計から計算する（sim の値で直線に）。
ポップアップ ev：[ショットの中の秒, 文, 種類]。種類 S＝雪、T＝暑さ、R＝雨、W＝風、Q＝地震、C＝比べると。
数字は scripts/pilot_053/sim/disaster.json（disaster.py）。記録と仮定は scripts/pilot_053/fact_check.md。
ユーザーの承認（2026-11-13）：流れの案に「うん、よろしく」。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_053" / "sim" / "disaster.json").read_text(encoding="utf-8"))
SNOW = 11.82; MELT_H = O["hours_melt"]; WATER_END = O["water_left_m"]

SHOTS = [
    dict(id="l00", dur=3.0, c=[[0, 0], [1, 0]], what="オープニング：真夏の青空の下、ビル街が 4 階まで雪に埋まっている。気温 41.8℃",
         ev=[[.2, "観測史上 1位を 全部 同時に", "C"]]),
    dict(id="l01", dur=5.0, c=[[0, 0], [1, 0]], what="同じ街、ゆっくり寄る。5 つの記録の大きな札", card="spec"),
    dict(id="l02", dur=6.0, c=[[0, 0], [1, 0]], what="図：2 階建ての家の断面。11.82 m の雪に埋まり、屋根に 1 m² あたり 2.4 トン",
         ev=[[.4, "雪 11.82m＝ビルの4階", "S"], [2.6, "屋根に 1m²あたり 2.4トン", "S"]]),
    dict(id="l03", dur=6.0, c=[[0, 0], [1, 3]], what="41.8℃：雪から湯気、雪の面が下がり始める",
         ev=[[.5, "41.8℃の 熱い風が 雪をとかす", "T"], [3.0, "1時間に 198mm とける", "T"]]),
    dict(id="l04", dur=6.0, c=[[0, 3], [1, 6]], what="雨 153 mm：雪どけの水と合わせて道に水がたまる",
         ev=[[.5, "雨 1時間 153mm", "R"], [2.4, "雪どけと合わせて 1時間 351mm", "R"], [4.2, "下水道は 1時間 50mmまで", "C"]]),
    dict(id="l05", dur=5.0, c=[[0, 6], [1, 8]], what="風 72.5 m/s：雨と雪が横に飛ぶ、旗や看板が揺れる",
         ev=[[.4, "風 72.5m/s（瞬間 91m/s）", "W"], [2.4, "猛烈な台風の 1.3倍の風", "C"]]),
    dict(id="l06", dur=5.0, c=[[0, 8], [1, 8.2]], what="震度 7：画面が揺れ、水が波立つ",
         ev=[[.3, "震度7", "Q"]]),
    dict(id="l07", dur=6.0, c=[[0, 8.2], [.75, 24], [1, 24]], what="24 時間後：雪が消え、2 階まで水につかったビル街の空撮",
         ev=[[.6, f"雪は {MELT_H:.0f}時間で 全部とけた", "S"], [3.4, f"水の深さ 約{WATER_END:.1f}m", "R"]]),
    dict(id="l08", dur=4.5, c=[[0, 24], [1, 24]], what="結果（大きな札）", card="result"),
    dict(id="l09", dur=2.5, c=[[0, 0], [1, 0]], what="冒頭の、雪に埋まった真夏の街に戻る（ループ）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    data = {"title": "観測史上最大が全部同時に起きたら？", "theme": "日本の観測史上最大の記録が、東京で同時に起きたら？（もしも設計）",
            "note": "もしも設計の既定（タイトルの帯つき）：ナレーションなし（silent_ext）、情報はポップアップ、BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "silent": True, "gap": 0.0, "max_duration": 60.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "sim": O, "snow": SNOW, "melt_h": MELT_H, "water_end": WATER_END}
    (HERE / "blender").mkdir(exist_ok=True); (HERE / "assets").mkdir(exist_ok=True)
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、本編 {sum(s['dur'] for s in SHOTS):.1f} 秒、雪 {MELT_H:.1f} 時間でとける、水 {WATER_END:.2f} m")


if __name__ == "__main__":
    main()
