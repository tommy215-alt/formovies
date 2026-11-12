#!/usr/bin/env python3
"""pilot_052「ハムスターの回し車で、東京の電気をまかなうには何匹？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・ハムスターの数・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json（音声なしの行）、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
数 n：[[u, 匹], ...]（u＝ショットの中の進み 0→1）。左上の札に出す。
ポップアップ ev：[ショットの中の秒, 文, 種類]。種類 H＝ハムスター、E＝電気、C＝比べると、Z＝ひと休み。
数字は scripts/pilot_052/sim/hamster.json（hamster.py）から。条件と仮定は scripts/pilot_052/fact_check.md。
ユーザーの承認（2026-11-12）：構想（scripts/pilot_052/concept.md）と計算の結果に「OK」。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_052" / "sim" / "hamster.json").read_text(encoding="utf-8"))
N = O["n"]; NB = round(N["bulb"]); NH = round(N["house"], -3); NT = round(N["town"], -6); NK = round(N["tokyo"], -9)


def oku(n):
    return f"約{n / 1e8:,.0f}億匹"


SHOTS = [
    dict(id="l00", dur=3.0, n=[[0, 1], [1, 1]], what="オープニング：田舎の古民家の縁側。回し車を全力で回す 1 匹。豆電球はつかない（フィラメントがかすかに赤いだけ）",
         ev=[[.25, "1匹で 豆電球は つく？", "E"]]),
    dict(id="l01", dur=5.0, n=[[0, 1], [1, 1]], what="走るハムスターの寄り（顔・足）→ 回し車と発電機", card="spec"),
    dict(id="l02", dur=5.0, n=[[0, 1], [.35, NB], [1, NB]], what="回し車が 4 台に増え、豆電球がぱっとつく",
         ev=[[2.4, f"{NB}匹で ついた", "E"]]),
    dict(id="l03", dur=6.0, n=[[0, NB], [.7, NH], [1, NH]], what="地方の一軒家（かやぶきの古民家）：庭と田んぼのあぜが回し車で埋まっていく空撮",
         ev=[[.5, "家1軒の 1日分の電気", "E"], [2.6, f"→ 約{NH / 1e4:.0f}万匹", "H"], [4.2, f"走るのは 1日 約{O['hours']:.0f}時間", "H"]]),
    dict(id="l04", dur=6.0, n=[[0, NH], [1, NH]], what="ひと休み：止まった回し車の中で丸くなって寝るハムスター。隣の回し車が回り出す（交代）",
         ev=[[.6, "ひと休み", "Z"], [3.0, "1日の 4分の3は 休み", "Z"]]),
    dict(id="l05", dur=6.0, n=[[0, NH], [.8, NT], [1, NT]], what="町全体：田んぼと空き地を回し車が埋める空撮",
         ev=[[.6, "町（家4,000軒）", "E"], [3.0, f"→ {NT / 1e4:,.0f}万匹", "H"]]),
    dict(id="l06", dur=4.0, n=[[0, NT], [1, NT]], what="上京：田園を新幹線が走る（051 の部品）",
         ev=[[.4, "いよいよ 東京へ", "C"]]),
    dict(id="l07", dur=7.0, n=[[0, NT], [.85, NK], [1, NK]], what="東京：ビル街の道と屋上を回し車が埋め尽くす空撮",
         ev=[[.5, f"東京の電気 1日 約{O['tokyo_wh_day'] / 1e12:.1f}億kWh", "E"], [4.2, f"→ {oku(NK)}", "H"]]),
    dict(id="l08", dur=5.0, n=[[0, NK], [1, NK]], what="図：回し車を並べた広さ ＝ 四国とほぼ同じ／えさ 1日 約190万トン",
         ev=[[.5, "回し車を 並べると…", "C"], [2.6, f"えさは 1日 約{O['food_t_day'] / 1e4:.0f}万トン", "C"]]),
    dict(id="l09", dur=4.5, n=[[0, NK], [1, NK]], what="結果（大きな札）", card="result"),
    dict(id="l10", dur=2.5, n=[[0, 1], [1, 1]], what="縁側の 1 匹に戻る（冒頭につながる）"),
]


def main():
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    data = {"title": "ハムスター何匹で東京の電気をまかなえる？", "theme": "ハムスターの回し車で、東京の電気をまかなうには何匹？（もしも設計）",
            "note": "もしも設計の既定（タイトルの帯つき）：ナレーションなし（silent_ext）、情報はポップアップ、BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "silent": True, "gap": 0.0, "max_duration": 60.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "sim": O, "nb": NB, "nh": NH, "nt": NT, "nk": NK, "oku": oku(NK)}
    (HERE / "blender").mkdir(exist_ok=True); (HERE / "assets").mkdir(exist_ok=True)
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、本編 {sum(s['dur'] for s in SHOTS):.1f} 秒、豆電球 {NB} 匹、家 {NH:,.0f}、町 {NT:,.0f}、東京 {oku(NK)}")


if __name__ == "__main__":
    main()
