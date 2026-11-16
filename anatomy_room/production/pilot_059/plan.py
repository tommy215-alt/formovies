#!/usr/bin/env python3
"""pilot_059「日本アルプスが、ヒマラヤ山脈になったら？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
ev：[ショットの中の秒, 文, 種類]。種類 S＝もしも、H＝高さ、L＝長さ、P＝場所、N＝日本全体、A＝雪崩、V＝見える、C＝比べると。
数字は scripts/pilot_059/sim/himalaya.json（himalaya.py）。出典と確認方法は scripts/pilot_059/fact_check.md。
ユーザーの指示（2026-11-16）：「ヒマラヤ山脈になったら？ならどう？」→「んじゃあヒマラヤ山脈バージョンで。よろしく。」
 v2（同日）：「弱いな。ヒマラヤ山脈の中心を日本アルプスの中心において、日本アルプスがいきなり盛り上がって人が戸惑う様子を描いて欲しい。エベレストはどの市になるのか、日本の平均高度や平均気温なども表して欲しい。雪崩が起きたらどこまで被害が出るのかとかも出して。全般的に迫力に欠ける。」
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
O = json.loads((HERE.parents[1] / "scripts" / "pilot_059" / "sim" / "himalaya.json").read_text(encoding="utf-8"))

SHOTS = [
    dict(id="l00", dur=3.8, what="0 秒目：松本の通り。地面が揺れ、北アルプスが目の前で盛り上がる。歩いていた人が立ち止まる", ev=[[.3, "日本アルプスが ヒマラヤになったら？", "S"]]),
    dict(id="l01", dur=4.6, what="見上げる人たちの後ろから、8,000m 級の白い壁（アンナプルナの山群、実際の標高データ）。頭を抱える・指さす・後ずさる",
         ev=[[.3, f"松本の目の前に アンナプルナ {O['annapurna']:,}m", "H"], [2.4, f"北アルプス {O['kita']:,}m → {O['annapurna']:,}m", "C"]]),
    dict(id="l02", dur=5.2, what="地図：ヒマラヤの真ん中を日本アルプスの真ん中に。本州をおおって広がる",
         ev=[[.3, f"長さ 約{O['len']:,}km", "L"], [2.2, f"本州の 約{O['len_ratio']:.1f}倍", "C"], [3.8, "九州の西から 北海道まで", "L"]]),
    dict(id="l03", dur=4.8, what="地図を寄せる：山形にエベレストの印", ev=[[.3, "エベレストは 山形県 高畠町に", "P"], [2.4, f"東京から 約{round(O['tokyo_ev_km'], -1):.0f}km", "P"]]),
    dict(id="l04", dur=5.8, what="新しい日本の立体地図（高さは強調）", ev=[[.3, f"日本の平均標高 約{round(O['avg_now'], -1):.0f}m → 約{round(O['avg_new'], -2):,.0f}m", "N"],
         [2.2, f"平均気温は 約{O['dT']:.0f}℃ 下がる（目安）", "N"], [4.0, f"国土は 約{O['area_ratio']:.1f}倍に", "N"]]),
    dict(id="l05", dur=6.0, what="雪崩：高い斜面から雪煙が谷の町へ迫る", ev=[[.3, f"大雪崩は 時速 約{O['av_kmh']}km", "A"], [2.2, f"ペルーの大雪崩なら 約{O['av_km']}km先まで", "A"],
         [4.0, "山形市・米沢市・福島市まで 届く", "A"]]),
    dict(id="l06", dur=4.4, what="東京から：ビル街の向こうに白い山並み（望遠、地球の丸みで下は隠れる）", ev=[[.3, f"東京からも 見える（約{round(O['tokyo_ev_km'], -1):.0f}km）", "V"],
         [2.2, f"下の約{round(O['hidden_tokyo_m'], -2):,.0f}mは 地球の丸みで隠れる", "V"]]),
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
