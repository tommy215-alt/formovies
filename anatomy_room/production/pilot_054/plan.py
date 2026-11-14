#!/usr/bin/env python3
"""pilot_054「全人類 82 億人が、渋谷のスクランブル交差点に集まったら？」（新もしも設計、templates/DESIGN_MODES.md）の設計表。

ショット・セリフ・人数・ポップアップを、ここ 1 か所で決める。ショットの長さは声の長さで決まる（work/timeline.json）。
    python plan.py   → lines.json、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
n：集まった人数 [[u, 人数], ...]（u＝ショットの中の進み 0→1。間は対数で補間）。地図の塗りの半径は人数から（sim の curve）。
ev：[ショットの中の秒, 文, 種類]。種類 P＝人、A＝広さ、C＝比べると。
数字は scripts/pilot_054/sim/crowd.json（crowd.py）。出典と仮定は scripts/pilot_054/fact_check.md。
ユーザーの指示（2026-11-15）：候補 1 で「作ってみて」。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_054" / "sim" / "crowd.json").read_text(encoding="utf-8"))
NEAR = 3.1e5        # 3D の画の人（交差点から半径 約 220 m に 1 m² 2 人）
SH, JP, WD = O["shibuya"]["people"], O["japan"]["people"], O["world"]["people"]

SHOTS = [
    dict(id="l00", n=[[0, 2e3], [1, NEAR]], what="0 秒目：交差点はもう人でぎっしり。カメラが上がると、どの道も人で埋まっている",
         lines=[("W", "全人類、はちじゅうに億人が、渋谷のスクランブル交差点に集まったら？", "全人類82億人が 渋谷の\nスクランブル交差点に集まったら？", .3)]),
    dict(id="l01", n=[[0, NEAR], [1, NEAR]], what="人の中の目の高さ。まわりの人が手を振る。予想を聞く", prompt=True,
         lines=[("W", "どこまで埋まると思う？", "どこまで埋まると思う？", 1.0)]),
    dict(id="l02", n=[[0, NEAR], [1, NEAR]], what="真上から：1 m² のます目に 2 人", ev=[[.3, "1m²に 2人（安全に立てる目安）", "P"]],
         lines=[("M", "1平方メートルに2人ずつ。安全に立てる目安で、詰めていく。", "1m²に2人ずつ\n安全に立てる目安で 詰めていく", .25)]),
    dict(id="l03", n=[[0, NEAR], [1, SH]], what="真上から一気に上がる。見える街がすべて人",
         ev=[[.3, f"渋谷区が いっぱい：{SH / 1e4:,.0f}万人", "P"]],
         lines=[("M", "渋谷区がいっぱいで、3000万人。", "渋谷区がいっぱいで 3,000万人", .8)]),
    dict(id="l04", n=[[0, SH], [1, JP]], what="地図：人の塗りが広がる（日本人全員）", map=[3.2, 8.0],
         ev=[[.2, f"日本人 全員：{JP / 1e8:.2f}億人", "P"], [1.2, f"{O['japan']['area_km2']:.0f}km²＝山手線の内側（約63km²）くらい", "C"]],
         lines=[("M", "日本人全員で、山手線の内側くらい。", "日本人全員で 山手線の内側くらい", .6)]),
    dict(id="l05", n=[[0, JP], [1, JP]], what="地図：まだこれだけ", map=[8.0, 14.0],
         lines=[("M", "それでも、まだ世界の1.5%。", "それでも まだ世界の1.5％", .5)]),
    dict(id="l06", n=[[0, JP], [1, WD]], what="地図：一気に広がる。横浜・大宮・八王子・千葉に届く", map=[14.0, 58.0], towns=True,
         lines=[("M", "横浜、大宮、八王子、そして千葉まで。", "横浜 大宮 八王子 そして千葉まで", 1.8)]),
    dict(id="l07", n=[[0, WD], [1, WD]], what="答え（大きな札）：半径 40 km・東京都 約 2 つ分", map=[58.0, 63.0], towns=True, card="result",
         lines=[("W", "答えは、半径40キロ。東京都、およそ2つ分。", "答えは 半径40km\n東京都 およそ2つ分", 1.4)]),
    dict(id="l08", n=[[0, 2e3], [1, 2e3]], what="冒頭の交差点に戻る（ループ）", hold=2.0, lines=[]),
]


def main():
    lines = []
    for s in SHOTS:
        if not s["lines"]:
            lines.append({"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s.get("hold", 1.5),
                          "fact": "—", "what": s["what"]}); continue
        for j, (who, sp, sub, pause) in enumerate(s["lines"]):
            lines.append({"id": s["id"].upper() + ("" if j == 0 else "abc"[j - 1]), "who": who, "scene": s["id"], "speech": sp, "sub": sub.split("\n"),
                          "pause": pause, "fact": "scripts/pilot_054/fact_check.md", "what": s["what"]})
    data = {"title": "全人類が渋谷に集まったら？", "theme": "全人類 82 億人が、渋谷のスクランブル交差点に集まったら？（新もしも設計）",
            "note": "新もしも設計（templates/DESIGN_MODES.md）：冒頭の問いと最後の答えは W 冥鳴ひまり、途中は M 阿井田 茂 Calm。BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "voice_override": {"M": {"preset": "aida", "speed": 1.3}, "W": {"speed": 1.25, "inton": 1.0}},
            "gap": 0.05, "max_duration": 45.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "sim": O, "near": NEAR}
    (HERE / "blender").mkdir(exist_ok=True); (HERE / "assets").mkdir(exist_ok=True)
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、{len(lines)} 行")


if __name__ == "__main__":
    main()
