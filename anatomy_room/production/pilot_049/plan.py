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
FIRE1 = 20.0                        # 1 回目の炎（平地）
THROW2 = 164.0                      # 丘からの一斉投げ（当たるのは 2 秒後）
HIT2 = THROW2 + 2.0
FIRE2 = HIT2 + 1.0                  # 2 回目の炎：一撃の 1 秒あとに丘へ届く（ユーザー「炎を届かせて」、2026-11-10）


def man(n):
    return f"{n // 10000}万人" if n % 10000 == 0 else f"{n:,}人"


# 2026-11-10 ユーザーの直し：炎とハンマーの演出に力を入れる（迫真のカメラ・質の高い CG）、2 回目の炎は丘に届かせる、倒れるところを派手に
SHOTS = [
    dict(id="l00", dur=2.6, c=[[0, -3], [1, -1]], what="オープニング：群衆の向こうにそびえる怪獣。タイトル 2 行"),
    dict(id="l01", dur=3.4, c=[[0, 0], [1, 3]], what="対決の開始。両者の紹介", card="spec"),
    dict(id="l02", dur=3.2, c=[[0, 5], [1, 9]], what="平地から 5 万本が一斉に弧を描いて飛ぶ（空から）",
         ev=[[.7, 5, "5万本 一斉に投げる", "H"], [1.9, 7, f"1本 7.26kg・秒速{O['v']:.0f}m", "H"]]),
    dict(id="l03", dur=2.8, c=[[0, 9.5], [1, 12]], what="怪獣の腰に当たって跳ね返る。怪獣は気づかない",
         ev=[[.4, 10, f"届くのは 腰まで（{O['flat_top']:.0f}m）", "H"], [1.4, 11, "怪獣には 米粒1粒くらい", "C"]]),
    dict(id="l04", dur=4.2, c=[[0, 17], [1, 24]], what="炎 1 回目：低い位置から。頭上を炎が走り、草原に当たって燃え広がる。手前の選手が走って逃げる",
         ev=[[1.6, FIRE1, "炎で 1万人が リタイア", "R"]]),
    dict(id="l05", dur=3.2, c=[[0, 30], [1, 40]], what="作戦：丘（高さ 43 m）から頭を狙う。脳しんとうのライン", card="plan"),
    dict(id="l06", dur=3.0, c=[[0, 60], [1, 150]], what="4 万人が丘の上に集まる（空から）",
         ev=[[.8, 90, "丘の高さ 43m＝怪獣の頭の高さ", "H"]]),
    dict(id="l07", dur=2.8, c=[[0, 155], [1, 163]], what="怪獣が息を吸う。のどが赤く光る（次の炎）",
         ev=[[.6, 157, "次の炎を浴びたら 3万人 → 足りない", "C"]]),
    dict(id="l08", dur=3.4, c=[[0, 163], [1, 163.9]], what="丘の上で選手たちが回転する（スロー、本物のハンマーの形）"),
    dict(id="l09", dur=3.2, c=[[0, 163.9], [1, 164.4]], what="一斉に放す：何千本ものハンマーがカメラの横を抜けて怪獣へ",
         ev=[[.5, THROW2, "4万本 頭へ", "H"]]),
    dict(id="l10", dur=3.4, c=[[0, 164.4], [1, HIT2 - .02]], what="ハンマーと一緒に飛ぶカメラ：群れの中から、迫る怪獣の頭（スロー）"),
    dict(id="l11", dur=2.8, c=[[0, HIT2 - .02], [1, HIT2 + .6]], what="頭に当たる。頭がはじかれる",
         ev=[[.3, HIT2, f"頭が 秒速{O['dv']['40000']:.1f}m で揺れる", "K"], [1.3, HIT2, "脳しんとうのライン 7.2mを超えた", "C"]]),
    dict(id="l12", dur=3.6, c=[[0, HIT2 + .6], [1, FIRE2 + 2]], what="ふらつく怪獣が最後の炎を吐く。炎は丘に届き、選手が逃げる",
         ev=[[1.0, FIRE2, "炎が丘に届く 1万人が リタイア", "R"], [2.3, FIRE2 + 1, "でも 一撃は 1秒早かった", "C"]]),
    dict(id="l13", dur=4.4, c=[[0, FIRE2 + 2], [1, FIRE2 + 9]], what="怪獣が倒れる（スロー）。地響き、土煙の輪、飛び散る土"),
    dict(id="l14", dur=3.0, c=[[0, FIRE2 + 10], [1, FIRE2 + 12]], what="結果：勝者 ハンマー投げ", card="win"),
    dict(id="l15", dur=2.4, c=[[0, FIRE2 + 12], [1, FIRE2 + 14]], what="倒れた怪獣の目が開く（冒頭につながる）"),
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
