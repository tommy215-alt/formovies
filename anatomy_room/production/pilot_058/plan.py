#!/usr/bin/env python3
"""pilot_058「キリンぞりで、南極を横断したら？」（もしも設計の既定、templates/DESIGN_MODES.md。pilot_057 犬ぞりの続き）の設計表。

ショットごとの長さ・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
ev：[ショットの中の秒, 文, 種類]。種類 S＝問い、D＝道のり、V＝速さ、W＝寒さ・風、F＝ごはん、Z＝休む、C＝比べると。
数字は scripts/pilot_058/sim/giraffe.json（giraffe.py）。出典と確認方法は scripts/pilot_058/fact_check.md。
ユーザーの指示（2026-11-16）：「犬ぞりじゃなくてキリンぞりにしたら？で動画作ってみてもらっていい？」
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_058" / "sim" / "giraffe.json").read_text(encoding="utf-8"))

SHOTS = [
    dict(id="l00", dur=3.6, what="0 秒目：地吹雪の中、正面の低い位置へ迫ってくる 4 頭のキリンが引くそり",
         ev=[[.3, "キリンぞりで 南極を横断したら？", "S"]]),
    dict(id="l01", dur=5.0, what="南極大陸の衛星画像（NASA Blue Marble、PD）に横断ルート",
         ev=[[.3, f"横断ルート 約{O['route_km']:,}km", "D"], [2.6, f"犬ぞりなら {O['dog_days']}日", "C"]]),
    dict(id="l02", dur=5.0, what="速さ：横から並走、全力で駆けるキリン", ev=[[.4, f"キリンの最高速 時速約{O['vmax']}km", "V"], [2.4, f"走り続ければ 約{O['days_at_vmax']:.0f}日", "C"]]),
    dict(id="l03", dur=5.0, what="でも：歩きに変わるキリン、寒さ", ev=[[.4, "でも 全力は 短い間だけ", "V"], [2.4, f"動物園なら {O['zoo_c']}℃で 室内へ", "W"]]),
    dict(id="l04", dur=5.4, what="厳しさ：曇り空の地吹雪、高い首が風を受ける", ev=[[.4, f"気温 −{abs(O['tmin'])}℃", "W"], [2.5, f"時速{round(O['tip_kmh'], -1):.0f}kmの風で 横倒しの計算", "W"]]),
    dict(id="l05", dur=5.4, what="ごはん：上を向いて食べようとするキリン（木がない）から引いて、4 頭×4 日分のエサの山（約 540 kg、人の背より高い）", ev=[[.4, f"ごはん 1日 約{O['food']}kg", "F"], [2.0, "南極に 木は 1本もない", "F"], [3.4, f"{O['n']}頭×{O['days_at_vmax']:.0f}日分で 約{round(O['food_total_kg'], -1):.0f}kg", "C"]]),
    dict(id="l06", dur=5.6, what="癒やし：休憩。立ったまま口をもぐもぐ（反すう）するキリンに雪が積もる", ev=[[.5, "休むときも 立ったまま", "Z"], [2.8, "長い首に 雪が 積もっていく", "Z"]]),
    dict(id="l07", dur=4.4, what="結果（大きな札）", card="result"),
    dict(id="l08", dur=2.0, what="冒頭に戻る（ループ）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    data = {"title": "キリンぞりで南極を横断したら？", "theme": "キリンぞりで、南極を横断したら？（もしも設計）",
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
