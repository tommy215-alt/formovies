"""pilot_049「身長50mの怪獣 vs 世界最強のハンマー投げ選手1万人」の計算（案）。

条件（ユーザー、2026-11-10）：怪獣 1 体と、完全武装したハンマー投げの世界記録級の選手 1 万人。どちらが勝つか。
著作権・肖像権のため、特定の作品の怪獣や実在の選手は出さない（名前も見た目も）。数字だけ公開の記録から。
python battle.py → results.md
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = 9.81
N = 10_000

# ---------------------------------------------------------------- 怪獣（仮定）
H = 50.0                 # 身長 m（怪獣映画でよく使われる規模）
M = 2.0e7                # 体重 kg（2 万トン。同上）
SKIN = .03 * H / 3       # 皮膚の厚さ：ゾウ（肩の高さ約 3 m）の皮膚 2〜4 cm（3 cm）を体の大きさに合わせて拡大
BODY_D = 15.0            # 胴の太さ m（目安）
BASE = 5.0               # 倒れるときの支え（足の幅の半分）m（目安）
ROPE_H = 30.0            # 綱を結ぶ高さ m（腰）
EYE_H = 45.0             # 目の高さ m
HUMAN_M = 65.0           # 比べるための人の体重 kg
# ---------------------------------------------------------------- 人間（公開の記録と装備の値）
HAMMER_M = 7.26          # ハンマーの重さ kg（世界陸連の規則）
HAMMER_D = 86.74         # 世界記録 m（1986 年）
RELEASE_H = 2.0          # 手を離す高さ m（目安）
BULLET_M = .004          # 5.56 mm 弾の重さ kg（目安）
BULLET_V = 920.0         # 89 式小銃の初速 m/s
ROUNDS = 30              # 1 人あたり（弾倉 1 本）
AT_STEEL = .70           # 対戦車弾が貫く鋼の厚さ m（目安：パンツァーファウスト 3 系で広く知られる値）
AT_HOLE = .03            # 穴の半径 m（目安）
PULL = 1000.0            # 1 人が綱を引く力 N（目安：体重 100 kg の選手が踏ん張って約 100 kg 重）
BULLET_GEL = .40         # 小銃弾が肉に入る深さ m（目安：ゼラチンで 30〜50 cm）


def run():
    o = {}
    # ハンマー：飛距離から投げた速さ（45 度、空気抵抗なし）→ 一番高く上がる高さ
    v = math.sqrt(G * HAMMER_D)
    o["hammer_v"] = v
    o["hammer_J"] = .5 * HAMMER_M * v * v
    o["hammer_total_MJ"] = o["hammer_J"] * N / 1e6
    o["hammer_top_m"] = RELEASE_H + (v * math.sin(math.radians(45))) ** 2 / (2 * G)
    o["hammer_reach"] = "膝" if o["hammer_top_m"] < H * .3 else "腰"
    # 怪獣から見ると：重さの比で、人に当たる物に置きかえる
    o["hammer_as_g"] = HAMMER_M / (M / HUMAN_M) * 1000   # g
    # 小銃
    o["bullet_J"] = .5 * BULLET_M * BULLET_V ** 2
    o["bullets"] = N * ROUNDS
    o["bullet_total_MJ"] = o["bullet_J"] * o["bullets"] / 1e6
    o["bullet_pass"] = BULLET_GEL > SKIN
    # 対戦車弾：鋼 70 cm を貫く噴流は、肉（密度 1）ならおよそ √(7.85) 倍の深さ（密度の比の平方根）
    o["at_depth_m"] = AT_STEEL * math.sqrt(7.85 / 1.0)
    vol = math.pi * AT_HOLE ** 2 * o["at_depth_m"] * N
    o["at_wound_m3"] = vol
    o["body_m3"] = M / 1000.0
    o["at_wound_pct"] = vol / o["body_m3"] * 100
    o["at_vs_body"] = o["at_depth_m"] / BODY_D
    # 綱引き：腰（30 m）を横に引いて倒すには、F × 30 m ＞ 重さ × 5 m
    W = M * G
    o["pull_total_MN"] = PULL * N / 1e6
    o["pull_need_MN"] = W * BASE / ROPE_H / 1e6
    o["people_need"] = math.ceil(W * BASE / ROPE_H / PULL)
    o["people_more"] = o["people_need"] - N
    o["skin_cm"] = SKIN * 100
    return o


def fmt(o):
    rows = [
        ("怪獣", f"身長 {H:.0f} m、体重 {M/1e7:.0f}万トン、皮膚の厚さ {o['skin_cm']:.0f} cm（ゾウの皮膚を体の大きさに合わせて）"),
        ("ハンマー", f"投げた速さ 秒速 {o['hammer_v']:.0f} m、1 本 {o['hammer_J']:,.0f} J、1 万本で {o['hammer_total_MJ']:.0f} MJ。一番高く上がって {o['hammer_top_m']:.0f} m → 届くのは{o['hammer_reach']}まで"),
        ("怪獣から見たハンマー", f"人に {o['hammer_as_g']*1000:.0f} mg の物が当たるのと同じ（米粒 1 粒は約 20 mg）"),
        ("小銃", f"1 発 {o['bullet_J']:,.0f} J、{o['bullets']:,} 発で {o['bullet_total_MJ']:.0f} MJ。肉に入る深さ {BULLET_GEL*100:.0f} cm ＜ 皮膚 {o['skin_cm']:.0f} cm → {'中まで届く' if o['bullet_pass'] else '皮膚を抜けない'}"),
        ("対戦車弾", f"1 万発。肉なら約 {o['at_depth_m']:.1f} m まで（胴の太さ {BODY_D:.0f} m の {o['at_vs_body']*100:.0f}%）。傷の合計 {o['at_wound_m3']:.0f} m³＝体の {o['at_wound_pct']:.2f}%"),
        ("綱引き", f"1 万人で {o['pull_total_MN']:.0f} MN。腰を引いて倒すには {o['pull_need_MN']:.0f} MN → {o['people_need']:,} 人必要（あと {o['people_more']:,} 人）"),
    ]
    return "# pilot_049 の計算（案）\n\n| 項目 | 結果 |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in rows) + "\n"


if __name__ == "__main__":
    o = run()
    (HERE / "battle.json").write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
    md = fmt(o); (HERE / "results.md").write_text(md, encoding="utf-8"); print(md)
