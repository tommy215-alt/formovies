#!/usr/bin/env python3
"""pilot_057「犬ぞりで、南極を横断したら？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
ev：[ショットの中の秒, 文, 種類]。種類 S＝問い、M＝大きさ、W＝寒さ、D＝道のり、F＝ごはん、Z＝休む、G＝ゴール、C＝比べると。
数字は scripts/pilot_057/sim/antarctica.json（antarctica.py）。出典と確認方法は scripts/pilot_057/fact_check.md。
ユーザーの指示（2026-11-16）：「南極を犬ぞりで横断したら？にしようか。南極大陸の大きさと厳しさ、そして犬の健気さと可愛さを迫力を出した全力のCGで再現して。」
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_057" / "sim" / "antarctica.json").read_text(encoding="utf-8"))

SHOTS = [
    dict(id="l00", dur=3.6, what="0 秒目：地吹雪の中、正面の低い位置へ迫ってくる犬ぞり隊（ハスキー 10 頭）",
         ev=[[.3, "犬ぞりで 南極を横断したら？", "S"]]),
    dict(id="l01", dur=5.6, what="大きさ：南極大陸の衛星画像（NASA Blue Marble、PD）を上空から。横断ルートが伸びる、日本列島の長さの線と比べる",
         ev=[[.3, f"南極大陸 日本の 約{O['area_ratio']:.0f}倍", "M"], [2.5, f"横断ルート 約{O['route_km']:,}km", "D"], [4.0, f"日本列島の 約{O['route_vs_japan']:.0f}倍", "C"]]),
    dict(id="l02", dur=5.0, what="厳しさ：地平線まで氷の高原、横殴りの地吹雪の中を小さく進む隊", ev=[[.4, f"気温 −{abs(O['tmin_c']):.0f}℃", "W"], [2.4, f"風 時速 約{round(O['wind_kmh'], -1):.0f}km", "W"]]),
    dict(id="l03", dur=5.0, what="道のり：横から並走、雪を蹴って走る犬たち", ev=[[.4, f"1日 約{O['km_per_day']:.0f}km", "D"], [2.4, f"それを {O['days']}日", "D"]]),
    dict(id="l04", dur=5.4, what="けなげさ：先頭の犬の寄り、霜のついた毛、白い息、まっすぐ前を見る", ev=[[.4, f"そり犬の ごはん 1日 約{O['dog_kcal']:,}kcal", "F"], [2.6, f"人の 約{O['dog_vs_human']:.0f}日分", "C"]]),
    dict(id="l05", dur=5.8, what="癒やし：休憩。雪の上に座ってうとうとする犬たちに、雪がしんしんと積もる", ev=[[.5, "休むときは 雪の上で そのまま", "Z"], [2.8, "雪が積もる＝体温が 逃げていない", "Z"]]),
    dict(id="l06", dur=5.0, what="ゴール：海辺の基地の小屋と氷の崖、到着する隊", ev=[[.4, f"{O['days']}日 約{O['route_km']:,}km", "G"], [2.4, "1990年 実際に 横断した", "G"]]),
    dict(id="l07", dur=4.4, what="結果（大きな札）", card="result"),
    dict(id="l08", dur=2.0, what="冒頭に戻る（ループ）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    data = {"title": "犬ぞりで南極を横断したら？", "theme": "犬ぞりで、南極を横断したら？（もしも設計）",
            "note": "もしも設計の既定（タイトルの帯つき）：ナレーションなし（silent_ext）、情報はポップアップ、BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "silent": True, "gap": 0.0, "max_duration": 60.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "sim": O}
    (HERE / "blender").mkdir(exist_ok=True); (HERE / "assets").mkdir(exist_ok=True)
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、本編 {sum(s['dur'] for s in SHOTS):.1f} 秒")


if __name__ == "__main__":
    main()
