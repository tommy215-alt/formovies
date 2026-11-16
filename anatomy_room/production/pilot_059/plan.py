#!/usr/bin/env python3
"""pilot_059「日本アルプスが、ヒマラヤ山脈になったら？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
ev：[ショットの中の秒, 文, 種類]。種類 S＝もしも、L＝長さ、H＝高さ、A＝空、V＝見える、Z＝山頂、W＝天気、C＝比べると。
数字は scripts/pilot_059/sim/himalaya.json（himalaya.py）。出典と確認方法は scripts/pilot_059/fact_check.md。
ユーザーの指示（2026-11-16）：「ヒマラヤ山脈になったら？ならどう？」→ 流れの案に「んじゃあヒマラヤ山脈バージョンで。よろしく。」
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_059" / "sim" / "himalaya.json").read_text(encoding="utf-8"))

SHOTS = [
    dict(id="l00", dur=3.6, what="0 秒目：雲海を突き破ってそびえる雪と氷の巨大な壁（エベレストの実際の標高データ）へ飛んでいく",
         ev=[[.3, "日本アルプスが ヒマラヤになったら？", "S"]]),
    dict(id="l01", dur=5.6, what="地図：日本の衛星画像の上で、日本アルプスから同じ縮尺のヒマラヤが本州の向きに広がる",
         ev=[[.4, f"長さ 約{O['len']:,}km", "L"], [2.6, f"本州の 約{O['len_ratio']:.1f}倍", "C"], [4.0, "北海道の手前まで 届く", "L"]]),
    dict(id="l02", dur=5.2, what="高さ比べ：富士山とエベレストを同じ縮尺で並べる（実際の標高データ）",
         ev=[[.4, f"富士山 {O['fuji']:,}m", "H"], [1.9, f"エベレスト {O['everest']:,}m", "H"], [3.4, f"富士山 約{O['ratio']:.1f}個分", "C"]]),
    dict(id="l03", dur=5.0, what="空：旅客機が山頂のすぐ上を通り過ぎる", ev=[[.4, f"旅客機の高さ 約{O['jet']:,}m", "A"], [2.4, f"山頂は その約{round(O['gap'], -2):,.0f}m下", "A"]]),
    dict(id="l04", dur=5.6, what="東京から：ビル街の向こう、地平線の上に白い壁（望遠、地球の丸みで下は隠れる）",
         ev=[[.4, f"見える距離 約{round(O['see_km'], -1):.0f}km", "V"], [2.4, "東京・名古屋・大阪から 見える", "V"], [4.0, f"下の約{round(O['hidden_m'], -2):,.0f}mは 地球の丸みで隠れる", "V"]]),
    dict(id="l05", dur=5.4, what="山頂：雲海と、やわらかい朝の光", ev=[[.4, "山頂の気圧は 地上の 約1/3", "Z"], [2.6, "8,000m超えは デスゾーン", "Z"]]),
    dict(id="l06", dur=5.0, what="天気：冬の雲が壁にぶつかって積み上がる", ev=[[.4, "冬の風が 8,000mの壁に ぶつかる", "W"], [2.6, "日本海側は もっと大雪に（目安）", "W"]]),
    dict(id="l07", dur=4.4, what="結果（大きな札）", card="result"),
    dict(id="l08", dur=2.0, what="冒頭に戻る（ループ）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    data = {"title": "日本アルプスがヒマラヤになったら？", "theme": "日本アルプスが、ヒマラヤ山脈になったら？（もしも設計）",
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
