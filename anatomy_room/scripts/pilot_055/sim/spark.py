#!/usr/bin/env python3
"""pilot_055「10万ボルトの電撃が、現実にあったら？」の計算（もしも設計）。
空気で火花が飛ぶ電圧：球の電極で 1 cm に 約 30 kV、とがった電極で 1 cm に 約 12 kV（schoolphysics、本文で確認）。
火花の長さ ≒ 電圧 ÷ その値（短いすき間の目安。長い火花・雷は一様ではないので、雷は「何 km も」とだけ言う）。
    python spark.py → spark.json・results.md
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V = 1e5                   # 10 万ボルト
E_SPHERE = 30e3           # V/cm 球の電極（一様に近い）
E_POINT = 12e3            # V/cm とがった電極
TARGET_M = 5.0            # 相手までの距離（演出の設定）
LADDER = [("冬の静電気", 3e3), ("新幹線の架線", 25e3), ("10万ボルト", 1e5), ("送電線", 5e5), ("雷", 1e8)]


def main():
    out = {"v": V, "cm_sphere": V / E_SPHERE, "cm_point": V / E_POINT, "target_m": TARGET_M,
           "need_v": TARGET_M * 100 * E_SPHERE, "need_ratio": TARGET_M * 100 * E_SPHERE / V, "outlet_ratio": V / 100,
           "ladder": [{"name": n, "v": v, "cm": v / E_SPHERE} for n, v in LADDER]}
    (HERE / "spark.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# pilot_055 計算の結果（spark.py）", "",
         f"- 10 万ボルトの火花：球の電極なら 約 {out['cm_sphere']:.1f} cm、とがった先なら 約 {out['cm_point']:.1f} cm",
         f"- 家のコンセント（100 V）の {out['outlet_ratio']:,.0f} 倍",
         f"- {TARGET_M:.0f} m 先に届かせるには 約 {out['need_v'] / 1e4:,.0f} 万ボルト（10 万ボルトの {out['need_ratio']:.0f} 倍）",
         "- 比べると（球の電極の目安で火花の長さ）：" + "、".join(f"{x['name']} {x['v']:,.0f} V→{x['cm']:.2g} cm" for x in out["ladder"])]
    (HERE / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    main()
