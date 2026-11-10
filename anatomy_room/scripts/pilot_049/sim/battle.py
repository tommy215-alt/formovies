"""pilot_049「身長50mの怪獣 vs 世界最強のハンマー投げ選手5万人」の計算（案 A、2026-11-10 ユーザーが OK）。

条件（ユーザー）：5 万人、武器はハンマーだけ。ハンマー投げは丘の上から頭を狙う。ハンマーは同時に当たるものとする。
怪獣は口から炎を吐き、1 回で 1 万人をリタイアさせる。ハンマー投げがギリギリ勝つ。
勝ち方：頭に当てて脳しんとう。脳しんとうのラインは、アメフト（NFL）の選手の頭の速さの変化 7.2 m/s（Pellman ほか 2003）。
著作権・肖像権のため、特定の作品の怪獣や実在の選手は出さない（名前も見た目も）。
python battle.py → battle.json・results.md
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = 9.81
N0 = 50_000              # 人数（ユーザー）
FIRE = 10_000            # 炎 1 回でリタイアする人数（ユーザー）

# ---------------------------------------------------------------- 怪獣（仮定）
H = 50.0                 # 身長 m（怪獣映画でよく使われる規模）
M = 2.0e7                # 体重 kg（2 万トン、同上）
HEAD_F = .05             # 頭の重さの割合（目安：大きな体の生き物の頭として 5%）
HEAD_H = 45.0            # 頭の高さ m
SKIN = .03 * H / 3       # 皮膚：ゾウ（肩の高さ約 3 m）の 2〜4 cm を体の大きさに合わせて
HUMAN_M = 65.0
# ---------------------------------------------------------------- ハンマー（世界陸連の規則・記録）
HAMMER_M = 7.26
HAMMER_D = 86.74         # 世界記録 m（1986 年）
RELEASE_H = 2.0
DV_CONC = 7.2            # 脳しんとうのライン m/s（NFL、Pellman ほか 2003 の脳しんとうの平均）
DV_SAFE = 5.0            # 同じ調査の、脳しんとうにならなかった選手の平均


def run():
    o = {}
    v = math.sqrt(G * HAMMER_D)                       # 45 度で世界記録の距離を出す速さ（空気抵抗なし）
    o["v"] = v
    o["J"] = .5 * HAMMER_M * v * v
    # 平地から：一番高く上がる高さ（頂点では横向きの速さだけ）
    o["flat_top"] = RELEASE_H + (v * math.sin(math.radians(45))) ** 2 / (2 * G)
    o["flat_hit_v"] = v * math.cos(math.radians(45))
    o["rice_mg"] = HAMMER_M / (M / HUMAN_M) * 1e6     # 怪獣から見た重さ（人に当たる物に置きかえて）
    # 丘（頭と同じ高さ）から：同じ高さに戻るので、当たる速さ＝投げた速さ
    o["hill_h"] = HEAD_H - RELEASE_H
    m_head = HEAD_F * M; o["m_head_t"] = m_head / 1000
    dv = lambda n: n * HAMMER_M * v / m_head
    o["need"] = math.ceil(DV_CONC * m_head / (HAMMER_M * v))
    o["dv"] = {str(n): dv(n) for n in (50_000, 40_000, 30_000)}
    o["n_after1"] = N0 - FIRE; o["n_after2"] = N0 - 2 * FIRE
    o["margin"] = o["n_after1"] - o["need"]
    o["skin_cm"] = SKIN * 100
    o["dv_conc"] = DV_CONC; o["dv_safe"] = DV_SAFE
    return o


def fmt(o):
    rows = [
        ("ハンマー 1 本", f"7.26 kg、投げた速さ 秒速 {o['v']:.1f} m、{o['J']:,.0f} J"),
        ("平地から", f"一番高くて {o['flat_top']:.0f} m（怪獣の腰）。怪獣から見ると {o['rice_mg']:.0f} mg の物（米粒 1 粒は約 20 mg）"),
        ("丘（高さ約 43 m）から", f"頭（45 m）に投げた速さのまま当たる"),
        ("頭", f"体重の {HEAD_F*100:.0f}%＝{o['m_head_t']:,.0f} トン"),
        ("脳しんとうのライン", f"頭の速さの変化 秒速 {DV_CONC} m（NFL の脳しんとうの平均。ならなかった選手は 5.0）"),
        ("必要な人数", f"{o['need']:,} 人"),
        ("5 万人なら", f"秒速 {o['dv']['50000']:.1f} m"),
        ("炎 1 回のあと（4 万人）", f"秒速 {o['dv']['40000']:.1f} m → 超える（必要より {o['margin']:,} 人多い）"),
        ("炎 2 回のあと（3 万人）", f"秒速 {o['dv']['30000']:.1f} m → 届かない"),
    ]
    return "# pilot_049 の計算（案 A）\n\n| 項目 | 結果 |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in rows) + "\n"


if __name__ == "__main__":
    o = run()
    (HERE / "battle.json").write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
    md = fmt(o); (HERE / "results.md").write_text(md, encoding="utf-8"); print(md)
