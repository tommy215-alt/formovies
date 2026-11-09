#!/usr/bin/env python3
"""pilot_047「毎日2倍になる隕石。地球は何日もつ？」（もしも設計の既定、templates/DESIGN_MODES.md）の設計表。

ショットごとの長さ・時計（1 日目 0:00 からの秒）・ポップアップを、ここ 1 か所で決める。
    python plan.py   → lines.json（音声なしの行）、assets/plan.js（renderer.html）、blender/plan.json（scene.py）
時計 c：[[u, 秒], ...]（u＝ショットの中の進み 0→1）。毎日の正午（12:00:00）に隕石が落ちる。
ポップアップ ev：[ショットの中の秒, 表示の時刻（秒）, 文, 種類]。種類 R＝隕石、B＝被害、P＝人々、C＝比べると、U＝地球。
末尾に ? が付いたもの（例 "U?"）は計算に入っていない予想で、札に「（予想）」と出す。
数字は scripts/pilot_047/sim/days.json（impact.py → population.py）から。条件と仮定は scripts/pilot_047/fact_check.md。
ユーザーの指示（2026-11-09）：1 日目 10 cm、毎日 2 倍、都庁の真上、毎日正午、予告なし、人は逃げる、28 日目に地球が砕ける、
たとえは分かりやすく（車・原爆・地震・恐竜の隕石・大きさ）、15 日目は「残る逃げ場は宮古島・石垣島など」だけ、全体 60 秒以内。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIM = HERE.parents[1] / "scripts" / "pilot_047" / "sim" / "days.json"
D, NOON = 86400, 43200


def noon(d, s=0.0):
    """d 日目の正午から s 秒"""
    return (d - 1) * D + NOON + s


SHOTS = [
    dict(id="l00", dur=2.6, c=[[0, noon(28, -3)], [1, noon(28, -1)]], what="オープニング：28 日目、新宿の空を覆う岩の底。タイトル 2 行"),
    dict(id="l01", dur=4.0, c=[[0, noon(1, -2)], [1, noon(1, 2)]], what="1 日目：都庁前の広場、正午。昼の空に小さな光の筋。誰も気づかない", card="spec"),
    dict(id="l02", dur=5.0, c=[x for i, d in enumerate(range(2, 7)) for x in ([i / 5, noon(d, -.5)], [(i + .999) / 5, noon(d, .5)])],
         what="2〜6 日目：毎日の正午に 1 本ずつ（1 日 1 秒、ユーザー「もう少しゆっくり」）。光の筋が太くなる。人々が見上げる",
         ev=[[2.5, noon(4), "昼でも見える 火の玉", "R"]]),
    dict(id="l03", dur=2.4, c=[[0, noon(7, -1)], [1, noon(7, 4)]], what="7 日目：上空で爆発。少し遅れてドーン。人々が見上げる",
         ev=[[.7, noon(7), "上空36kmで 爆発", "R"]]),
    dict(id="l04", dur=3.4, c=[[0, noon(8, -1)], [.25, noon(8, 1)], [.35, noon(9, -1)], [1, noon(9, 6)]], what="8〜9 日目：窓が震えて割れる → 人々が荷物を持って駅へ",
         ev=[[1.2, noon(9), "77km先まで 窓が割れるかも", "B"], [2.0, noon(9), "避難が始まる", "P"]]),
    dict(id="l05", dur=4.0, c=[[0, noon(10, -1)], [1, noon(10, 5)]], what="10 日目：上空 7 km の爆発を見上げ → 衝撃波が地面を走り、無人の新宿のビルが外へ次々に倒れる",
         ev=[[.8, noon(10), "上空7kmで 爆発", "R"], [1.6, noon(10), "8km以内のビルが 崩れる", "B"]]),
    dict(id="l06", dur=3.2, c=[[0, noon(11, -1)], [1, noon(11, 5)]], what="11 日目：初めて地面に届く。都庁があった所にクレーター",
         ev=[[.8, noon(11), "初めて 地面に届く", "R"], [1.7, noon(11), "クレーター 1.6km", "B"]]),
    dict(id="l07", dur=3.0, c=[[0, noon(12, -1)], [.4, noon(12, 3)], [.5, noon(13, -1)], [1, noon(13, 5)]], what="12〜13 日目：カメラが上がる。関東の街に被害の円",
         ev=[[.5, noon(12), "ビルが崩れる 31km", "B"], [1.7, noon(13), "ビルが崩れる 66km", "B"]]),
    dict(id="l08", dur=3.4, c=[[0, noon(14, -1)], [1, noon(14, 6)]], what="14 日目：関東の地図。円が関東を覆い、街の光が消える",
         ev=[[.8, noon(14), "関東の街が 消える", "B"], [1.9, noon(14), "服が燃える 111km", "B"]]),
    dict(id="l09", dur=2.8, c=[[0, noon(15, -1)], [1, noon(15, 5)]], what="15 日目：名所のカット。名古屋城に爆風が届く",
         ev=[[.6, noon(15), "名古屋まで ビルが崩れる", "B"], [1.5, noon(15), "残る逃げ場は 宮古島・石垣島など", "P"]]),
    dict(id="l10", dur=3.0, c=[[0, noon(16, -1)], [1, noon(16, 5)]], what="16 日目：日本の地図。円が石垣島まで覆う", card="noplace",
         ev=[[.4, noon(16), "爆風が 日本全体に", "B"]]),
    # 17 日目より後は要所だけ（ユーザー「日本より範囲が大きくなってきたら日数をもっと省略して要所だけ」）
    dict(id="l11", dur=3.4, c=[[0, noon(18, -1.8)], [1, noon(18, 1.6)]], what="18 日目：13 km の岩を後ろから追い、東京へ。カメラが引いて焼けた円",
         ev=[[2.0, noon(18), "クレーター 150km", "B"]]),
    dict(id="l12", dur=2.8, c=[[0, noon(20, -.9)], [1, noon(20, 1.9)]], what="20 日目：光る尾を引いて東京へ → 爆風の輪が地球を一周",
         ev=[[1.0, noon(20), "爆風が 地球を一周", "B"]]),
    dict(id="l13", dur=2.8, c=[[0, noon(23, -1)], [1, noon(23, 1.8)]], what="23 日目：光る尾を引いて東京へ → 海が白い湯気になっていく",
         ev=[[1.1, noon(23), "海をすべて 蒸発させられる力", "U"]]),
    dict(id="l14", dur=2.6, c=[[0, noon(26, -1)], [1, noon(26, 1.6)]], what="26 日目：月とほぼ同じ大きさの岩が、月と並んで地球へ迫る"),
    dict(id="l15", dur=4.2, c=[[0, noon(28, -2)], [1, noon(28, 4)]], what="28 日目：地球より大きな岩が迫り、地球が砕ける", card="loop"),
    dict(id="l16", dur=1.8, c=[[0, noon(28, 4)], [1, noon(28, 6)]], what="砕けたかけらが流れ星のように散る → 暗転（冒頭の岩につながる）"),
]


def main():
    days = json.loads(SIM.read_text(encoding="utf-8"))
    keep = ["day", "L_m", "energy_kind", "energy_text", "burst_m", "glass_km", "bldg_km", "cloth_km", "crater_km", "counter"]
    dd = [{k: d.get(k) for k in keep} for d in days]
    lines = [{"id": s["id"].upper(), "who": "M", "scene": s["id"], "speech": "", "sub": "", "silent": True, "hold": s["dur"],
              "fact": "画面のポップアップ（plan.py）", "what": s["what"]} for s in SHOTS]
    title = "毎日2倍になる隕石。地球は何日もつ？"
    data = {"title": title, "theme": title + "（もしも設計）",
            "note": "もしも設計の既定（pilot_045 v2.3）：ナレーションなし（silent_ext）、情報はポップアップ、BGM なし。中身は plan.py で決め、python plan.py でこのファイルを作る（直接直さない）。",
            "voices": "v7", "silent": True, "gap": 0.0, "max_duration": 60.0, "meta": {}, "lines": lines}
    (HERE / "lines.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    plan = {"shots": SHOTS, "days": dd, "start_hour": 0}
    (HERE / "blender" / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "assets" / "plan.js").write_text("window.PLAN = " + json.dumps(plan, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"plan: {len(SHOTS)} ショット、本編 {sum(s['dur'] for s in SHOTS):.1f} 秒")


if __name__ == "__main__":
    main()
