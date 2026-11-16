#!/usr/bin/env python3
"""pilot_056「頭の小さなプロペラで、空を飛んだら？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
ev：[ショットの中の秒, 文, 種類]。種類 S＝条件、W＝風、P＝パワー、R＝回る、C＝比べると。
数字は scripts/pilot_056/sim/rotor.json（rotor.py）。出典と仮定は scripts/pilot_056/fact_check.md。
ユーザーの承認（2026-11-15）：候補から「1.で行こうか」、流れの案に「よろしくー」。作品名・キャラクター・道具の名前は出さない。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_056" / "sim" / "rotor.json").read_text(encoding="utf-8"))

SHOTS = [
    dict(id="l00", dur=3.6, what="0 秒目：土管の空き地。頭のプロペラで浮き上がりかけた子ども、足もとの砂が爆発的に吹き飛ぶ",
         ev=[[.3, "頭のプロペラで 浮くには？", "S"]]),
    dict(id="l01", dur=4.6, what="条件：子どもとプロペラの寄り", ev=[[.3, "体重 35kg（10歳の平均）", "S"], [1.9, f"プロペラ 直径{O['d'] * 100:.0f}cm", "S"]]),
    dict(id="l02", dur=5.0, what="風：地面すれすれ、砂と小石と葉っぱが外へ吹き飛ぶ", ev=[[.4, f"足もとの風 時速 約{round(O['wake_kmh'], -1):.0f}km", "W"], [2.6, f"猛烈な台風の {O['typhoon_ratio']:.1f}倍", "C"]]),
    dict(id="l03", dur=4.6, what="風で土管が転がり、板の塀がばたつく", ev=[[.4, "土管も 転がる", "W"]]),
    dict(id="l04", dur=6.0, what="パワー：浮いた子どもの横に軽自動車", ev=[[.4, f"必要なパワー 約{O['power_ps']:.0f}馬力", "P"], [2.6, "軽自動車 1台分の エンジン", "C"]]),
    dict(id="l05", dur=5.6, what="オチ：反動で体が逆に回り始める", ev=[[.5, "反動で 体が逆に回る", "R"], [2.8, f"1秒後には 1秒に {O['spin_rps_1s']:.0f}回転", "R"]]),
    dict(id="l06", dur=5.0, what="もっと速く回る（コマのよう）", ev=[[.4, f"3秒後には 1秒に {O['spin_rps_3s']:.0f}回転", "R"]]),
    dict(id="l07", dur=4.2, what="結果（大きな札）", card="result"),
    dict(id="l08", dur=2.0, what="冒頭に戻る（ループ）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    data = {"title": "頭のプロペラで空を飛んだら？", "theme": "頭の小さなプロペラで、空を飛んだら？（もしも設計）",
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
