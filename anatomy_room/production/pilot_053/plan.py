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

SHOTS = [   # v2（2026-11-13 ユーザーの直し：東京の名所・人と車・風の物・灼熱と豪雨の同時・人のリアクション）
    dict(id="l00", dur=3.5, c=[[0, 0], [1, 0]], what="オープニング：渋谷のスクランブル交差点。人と車でいっぱい、ビルの温度計は 41.8℃。空から雨と雪が同時に降ってくる",
         ev=[[.2, "観測史上 1位が 全部 同時に", "C"]]),
    dict(id="l01", dur=5.0, c=[[0, 0], [1, .1]], what="交差点を見下ろす。5 つの記録の大きな札。傘が開き、人が空を見上げる", card="spec"),
    dict(id="l02", dur=5.5, c=[[0, .1], [1, .3]], what="人のリアクション：傘を差す、両手を上げて驚く、走る。雪と雨が同時に降る",
         ev=[[.4, "41.8℃なのに 雪と大雨", "T"], [3.0, "雨 1時間 153mm", "R"]]),
    dict(id="l03", dur=6.0, c=[[0, .3], [1, 2.5]], what="雪が積もる早回し：車が埋まり、信号が埋まり、4 階へ（11.82 m）。人は逃げる",
         ev=[[.5, "雪がどんどん 積もる", "S"], [3.6, "11.82m＝ビルの4階", "S"]]),
    dict(id="l04", dur=6.0, c=[[0, 2.5], [1, 4]], what="東京タワーと暴風 72.5 m/s：旗がはためき、傘が何本も飛び、看板が揺れる。雪と雨が真横に",
         ev=[[.4, "風 72.5m/s（瞬間 91m/s）", "W"], [3.0, "猛烈な台風の 1.3倍", "C"]]),
    dict(id="l05", dur=5.5, c=[[0, 4], [1, 7]], what="灼熱×豪雨：雨の中で雪から湯気が噴き上がる。温度計 41.8℃ と雨量計 153 mm",
         ev=[[.4, "41.8℃の 熱い雨と風で 雪がとける", "T"], [2.8, "雪どけ＋雨 1時間 351mm", "R"]]),
    dict(id="l06", dur=5.0, c=[[0, 7], [1, 7.2]], what="震度 7：東京タワーが揺れ、ビルから雪がなだれ落ち、水が波立つ",
         ev=[[.3, "震度7", "Q"]]),
    dict(id="l07", dur=5.0, c=[[0, 7.2], [1, 18]], what="雪どけの早回し：交差点の雪が沈み、水があふれ、車が浮く",
         ev=[[.5, f"下水道は 1時間 50mmまで", "C"], [4.0, "雪が 水の下に", "R"]]),
    dict(id="l08", dur=5.0, c=[[0, 18], [.7, 26.3], [1, 26.3]], what="24 時間後：東京タワーのふもとも水深 4.5 m。屋上で手を振る人、ボート",
         ev=[[.5, f"積もってから {MELT_H:.0f}時間で 全部とけた", "S"], [2.6, f"水の深さ 約{WATER_END:.1f}m", "R"]]),
    dict(id="l09", dur=4.5, c=[[0, 26.3], [1, 26.3]], what="結果（大きな札）", card="result"),
    dict(id="l10", dur=2.5, c=[[0, 0], [1, 0]], what="冒頭の交差点に戻る（ループ）"),
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
