#!/usr/bin/env python3
"""pilot_049「身長50mの怪獣 vs 世界最強のハンマー投げ選手5万人」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・時計（対決の開始からの秒）・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json（音声なしの行）、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
時計 c：[[u, 秒], ...]（u＝ショットの中の進み 0→1）。
ポップアップ ev：[ショットの中の秒, 表示の時刻（秒）, 文, 種類]。種類 K＝怪獣、H＝ハンマー、R＝リタイア、C＝比べると。
数字は scripts/pilot_049/sim/battle.json（battle.py）から。条件と仮定は scripts/pilot_049/fact_check.md。
ユーザーの指示（2026-11-10）：5 万人、武器はハンマーだけ、丘の上から頭を狙う、ハンマーは同時に当たる、炎 1 回で 1 万人リタイア、ハンマー投げがギリギリ勝つ（案 A）。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIM = HERE.parents[1] / "scripts" / "pilot_049" / "sim" / "battle.json"
O = json.loads(SIM.read_text(encoding="utf-8"))
FIRE1, FIRE2 = 20.0, 170.0          # 炎を吐く時刻（2 回目は吐く直前に倒れる）
THROW2 = 164.0                      # 丘からの一斉投げ（当たるのは 2 秒後）
HIT2 = THROW2 + 2.0


def man(n):
    return f"{n // 10000}万人" if n % 10000 == 0 else f"{n:,}人"


SHOTS = [
    dict(id="l00", dur=2.6, c=[[0, -3], [1, -1]], what="オープニング：草原にそびえる怪獣と、手前にずらりと並ぶ 5 万人。タイトル 2 行"),
    dict(id="l01", dur=3.6, c=[[0, 0], [1, 3]], what="対決の開始。両者の紹介", card="spec"),
    dict(id="l02", dur=3.4, c=[[0, 5], [1, 9]], what="平地から 5 万本が一斉に弧を描いて飛ぶ（空から）",
         ev=[[.8, 5, "5万本 一斉に投げる", "H"], [2.0, 7, f"1本 7.26kg・秒速{O['v']:.0f}m", "H"]]),
    dict(id="l03", dur=3.0, c=[[0, 9.5], [1, 12]], what="怪獣の腰に当たって跳ね返る。怪獣は気づかない",
         ev=[[.4, 10, f"届くのは 腰まで（{O['flat_top']:.0f}m）", "H"], [1.5, 11, "怪獣には 米粒1粒くらい", "C"]]),
    dict(id="l04", dur=3.6, c=[[0, 18], [1, 24]], what="怪獣が振り向いて炎を吐く。草原が燃え、1 万人が走って逃げる（リタイア）",
         ev=[[1.0, FIRE1, "炎で 1万人が リタイア", "R"]]),
    dict(id="l05", dur=3.4, c=[[0, 30], [1, 40]], what="作戦：丘（高さ 43 m）から頭を狙う。脳しんとうのライン", card="plan"),
    dict(id="l06", dur=3.4, c=[[0, 60], [1, 150]], what="4 万人が丘を駆け上がる（空から）",
         ev=[[.9, 90, "丘の高さ 43m＝怪獣の頭の高さ", "H"]]),
    dict(id="l07", dur=3.0, c=[[0, 155], [1, 163]], what="怪獣が息を吸う。のどが赤く光る（次の炎）",
         ev=[[.6, 157, "次の炎で 3万人に → 届かない", "C"]]),
    dict(id="l08", dur=3.2, c=[[0, 163], [1, 164.2]], what="丘の上で 4 万人が回転して投げる（スロー）",
         ev=[[1.6, THROW2, "4万本 頭へ", "H"]]),
    dict(id="l09", dur=3.0, c=[[0, 164.2], [1, HIT2 - .02]], what="4 万本が怪獣の頭へ集まる（スロー）"),
    dict(id="l10", dur=2.8, c=[[0, HIT2 - .02], [1, HIT2 + .6]], what="頭に当たる。頭がはじかれる",
         ev=[[.3, HIT2, f"頭が 秒速{O['dv']['40000']:.1f}m で揺れる", "K"], [1.3, HIT2, "脳しんとうのライン 7.2mを超えた", "C"]]),
    dict(id="l11", dur=3.0, c=[[0, HIT2 + .6], [1, FIRE2 - .5]], what="ふらつく怪獣。炎は空へそれる"),
    dict(id="l12", dur=3.6, c=[[0, FIRE2 - .5], [1, FIRE2 + 6]], what="怪獣が倒れる。土煙",
         ev=[[2.0, FIRE2 + 3, "炎の 3秒前だった", "C"]]),
    dict(id="l13", dur=3.0, c=[[0, FIRE2 + 8], [1, FIRE2 + 10]], what="結果：勝者 ハンマー投げ", card="win"),
    dict(id="l14", dur=2.4, c=[[0, FIRE2 + 10], [1, FIRE2 + 12]], what="倒れた怪獣の目が開く（冒頭につながる）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    title = "怪獣vsハンマー投げ5万人"
    data = {"title": title, "theme": "身長50mの怪獣 vs 世界最強のハンマー投げ選手5万人（もしも設計）",
            "note": "もしも設計の既定（タイトルの帯つき）：ナレーションなし（silent_ext）、情報はポップアップ、BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "silent": True, "gap": 0.0, "max_duration": 60.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "sim": O, "fire": [FIRE1, FIRE2], "throw2": THROW2, "hit2": HIT2, "n0": 50000, "fire_n": 10000}
    (HERE / "blender").mkdir(exist_ok=True)
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、本編 {sum(s['dur'] for s in SHOTS):.1f} 秒、必要 {O['need']:,} 人")


if __name__ == "__main__":
    main()
