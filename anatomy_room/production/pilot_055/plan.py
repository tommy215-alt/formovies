#!/usr/bin/env python3
"""pilot_055「10万ボルトの電撃が、現実にあったら？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
ev：[ショットの中の秒, 文, 種類]。種類 V＝電気、P＝届いた距離、C＝比べると。
数字は scripts/pilot_055/sim/spark.json（spark.py）。出典は scripts/pilot_055/fact_check.md。
ユーザーの承認（2026-11-15）：流れの案に「それでいこう。試しに40秒くらいで」。同日「1500万ボルトの場合も盛り込んで」→ l05b。作品名・キャラクター・技名の絵は出さない（10万ボルトは電圧の数字として）。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_055" / "sim" / "spark.json").read_text(encoding="utf-8"))

SHOTS = [
    dict(id="l00", dur=3.4, what="0 秒目：昼のバトル場。電気をまとった黄色い服の人が、5 m 先の的の人形と向き合う",
         ev=[[.3, "相手まで 5m", "P"]]),
    dict(id="l01", dur=4.2, what="ためる：体じゅうを電気が走る", ev=[[.3, "10万ボルト", "V"], [1.8, "家のコンセント（100V）の 1,000倍", "C"]]),
    dict(id="l02", dur=5.0, what="発射（スロー）：手から飛んだ電撃が、指先から数 cm で消える", ev=[[2.6, "届いたのは 約3cm", "P"]]),
    dict(id="l03", dur=5.4, what="指先と定規のアップ：火花は 3 cm 余り", ev=[[.3, "空気は 電気を通しにくい", "V"], [2.2, "1cm 飛ぶのに 約3万ボルト", "V"]]),
    dict(id="l04", dur=6.4, what="電圧の比べっこ（はしご）", ladder=True),
    dict(id="l05", dur=5.0, what="5 m 先に当てるには", ev=[[.3, f"5m 飛ばすには 約{O['need_v'] / 1e4:,.0f}万ボルト", "V"], [2.2, f"10万ボルトの {O['need_ratio']:.0f}倍", "C"]]),
    dict(id="l05b", dur=4.6, what="もし 1,500 万ボルトなら：太い電撃が 5 m 飛んで的に当たり、的がゆれて焦げ、煙", ev=[[.2, "もし 1,500万ボルトなら", "V"], [1.3, "5m 先まで 届く", "P"], [2.6, f"雷（約1億V）の 約{1e8 / O['need_v']:.0f}分の1", "C"]]),
    dict(id="l06", dur=5.2, what="オチ：的の目の前まで歩いて行って、パチッ", ev=[[.4, "当てるには…", "P"], [3.2, "目の前まで 近づくしかない", "P"]]),
    dict(id="l07", dur=4.0, what="結果（大きな札）", card="result"),
    dict(id="l08", dur=2.0, what="冒頭に戻る（ループ）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    data = {"title": "10万ボルトの電撃が現実にあったら？", "theme": "10万ボルトの電撃が、現実にあったら？（もしも設計）",
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
