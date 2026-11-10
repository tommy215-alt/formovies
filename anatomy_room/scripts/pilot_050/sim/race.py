# -*- coding: utf-8 -*-
"""pilot_050 もしも設計「ティラノサウルスがマラソン大会に出たら、優勝できる？」

ティラノサウルスを 42.195 km 走らせ（正しくは早歩き）、体温がどこまで上がるかを 1 秒ごとに計算する。
使い方: python race.py  → results.md・race.json を書く。

元の値（出典は ../fact_check.md）
  体重 7,206.7 kg ……………… Sellers ほか 2017（PeerJ 5:e3420）の模型
  最高の速さ 秒速 5.4 m …… 同（骨が耐えられる速さ。走れず、早歩きまで）
  ふだんの歩く速さ 秒速 1.28 m …… van Bijlert ほか 2021
  動くときに使うエネルギー …… Taylor・Heglund・Maloiy 1982 の式（鳥と哺乳類 62 種）
      E/M [W/kg] = 10.7·M^-0.316·v + 6.03·M^-0.303
  出せる力の上限（最大酸素摂取量）…… Taylor ほか 1981 の式 1.92·M^0.809 [ml O2/s]、1 ml = 20.1 J
目安（出典のない仮定）は ASSUME にまとめた。
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

M = 7206.7            # kg
V_MAX = 5.4           # m/s（時速 19.4 km）
V_PREF = 1.28         # m/s
DIST = 42195.0        # m
WR = 1 * 3600 + 59 * 60 + 30      # 世界記録 1:59:30（2026 年 4 月）
CUTOFF = 7 * 3600                 # 大きな市民マラソンの制限時間 7 時間
STARTERS = 36697                  # 東京マラソン 2024 の出走者数（規模の目安）

ASSUME = {
    "body_temp": 38.0,       # ℃ はじめの体温（鳥と哺乳類の間）
    "temp_limit": 3.0,       # ℃ これだけ上がったら早歩きをやめる（41 ℃）
    "heat_capacity": 3470.0, # J/kg/K 体の比熱（動物の体の標準的な値）
    "area_k": 0.10,          # 体の表面積 = k·M^(2/3) m2（哺乳類の目安）
    "body_diam": 1.8,        # m 胴の太さ（風で冷える量の計算に使う）
    "skin_drop": 4.0,        # ℃ 皮膚は体の中より 4 ℃ 低い（血をたくさん流しているとき）
    "wind": 2.0,             # m/s そよ風（止まっていても体に当たる風）
    "h_rad": 5.0,            # W/m2/K 放射で逃げる分
    "sun": 600.0,            # W/m2 3 月の昼の日射
    "sun_abs": 0.7,          # 日射を吸う割合
    "sun_area": 0.25,        # 日の当たる面積 = 表面積の 1/4
    "breath": 0.15,          # 息（あえぎ）で逃がす熱 = 出る熱の 15%
}


def power(v):
    """動くときに使うエネルギー [W]（平地なので、ほぼすべて熱になる）"""
    return (10.7 * M ** -0.316 * v + 6.03 * M ** -0.303) * M


def vo2max_power():
    return 1.92 * M ** 0.809 * 20.1


def area():
    return ASSUME["area_k"] * M ** (2.0 / 3.0)


def h_conv(v):
    """太い円柱に風が当たるときの冷え方（Hilpert の式）。当たる風＝進む速さとそよ風の合成"""
    d = ASSUME["body_diam"]
    nu_air, k_air = 1.5e-5, 0.025
    re = math.hypot(v, ASSUME["wind"]) * d / nu_air
    nu = 0.0266 * re ** 0.805 if re > 4e4 else 0.193 * re ** 0.618
    return nu * k_air / d


def loss(v, tb, air):
    """体から逃げる熱 [W]（風＋放射＋息 − 日射）"""
    a = area()
    skin = tb - ASSUME["skin_drop"]
    conv = (h_conv(v) + ASSUME["h_rad"]) * a * (skin - air)
    sun = ASSUME["sun"] * ASSUME["sun_abs"] * ASSUME["sun_area"] * a
    return conv - sun + ASSUME["breath"] * power(v)


def balance_speed(tb, air):
    """熱がこもらない速さ（出る熱＝逃げる熱）を二分法で求める"""
    lo, hi = 0.0, V_MAX
    if power(hi) - loss(hi, tb, air) <= 0:
        return hi
    if power(lo) - loss(lo, tb, air) > 0:
        return 0.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if power(mid) - loss(mid, tb, air) > 0:
            hi = mid
        else:
            lo = mid
    return lo


def race(air, dt=1.0):
    """はじめから最高の速さで進み、体温が上限に着いたら、熱がこもらない速さに落とす。"""
    c = ASSUME["heat_capacity"] * M
    t, x, tb = 0.0, 0.0, ASSUME["body_temp"]
    top = tb + ASSUME["temp_limit"]
    log, hot = [], None
    energy = 0.0
    while x < DIST and t < 24 * 3600:
        if tb < top and hot is None:
            v = V_MAX
        else:
            if hot is None:
                hot = {"t": t, "km": x / 1000}
            v = balance_speed(top, air)
            if v < 0.05:        # 止まっても冷えない → その場で動けない
                break
        p = power(v)
        tb = min(top, tb + (p - loss(v, tb, air)) * dt / c)
        energy += p * dt
        x += v * dt
        t += dt
        if int(t) % 60 == 0:
            log.append({"min": int(t // 60), "km": round(x / 1000, 2), "temp": round(tb, 2), "v": round(v, 2)})
    return {
        "air": air, "finished": x >= DIST, "time": t, "km": x / 1000, "temp_end": tb,
        "hot": hot, "v_after": balance_speed(top, air) if hot else None,
        "kcal": energy / 4184, "log": log,
    }


def hms(s):
    s = int(round(s))
    return "%d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60)


def main():
    top500 = json.load(open(os.path.join(HERE, "tokyo2026_men_top500_times.json"), encoding="utf-8"))["times"]
    secs = [int(a) * 3600 + int(b) * 60 + int(c) for a, b, c in (t.split(":") for t in top500)]

    best = DIST / V_MAX
    out = {
        "mass": M, "v_max": V_MAX, "v_max_kmh": V_MAX * 3.6, "wr": WR, "wr_kmh": DIST / WR * 3.6,
        "best_time": best, "behind_wr": best - WR, "behind_wr_km": (DIST - V_MAX * WR) / 1000,
        "pref_time": DIST / V_PREF, "power_max_kw": power(V_MAX) / 1000, "vo2max_kw": vo2max_power() / 1000,
        "area": area(), "cases": {},
    }
    lines = ["# pilot_050 計算の結果（race.py）", ""]
    lines += ["## 速さ", "",
              "- ティラノサウルスの最高の速さ：秒速 %.1f m ＝ 時速 %.1f km（早歩き）" % (V_MAX, V_MAX * 3.6),
              "- マラソンの世界記録 %s のペース：時速 %.1f km" % (hms(WR), DIST / WR * 3.6),
              "- 最高の速さで 42.195 km：%s（世界記録より %s おそい。優勝者がゴールしたとき、あと %.1f km）"
              % (hms(best), hms(best - WR), out["behind_wr_km"]),
              "- ふだんの歩く速さ（時速 %.1f km）なら：%s（制限時間 7 時間に間に合わない）" % (V_PREF * 3.6, hms(DIST / V_PREF)),
              "- 最高の速さで使うエネルギー：%.1f kW（出せる上限の目安 %.1f kW の %.0f%%）"
              % (out["power_max_kw"], out["vo2max_kw"], 100 * out["power_max_kw"] / out["vo2max_kw"]),
              ""]
    lines += ["## 体温（気温ごと）", "",
              "| 気温 | 結果 | タイム | 体温が上限（+%.0f℃）に着く所 | そのあとの速さ | 使ったエネルギー |" % ASSUME["temp_limit"],
              "|---|---|---|---|---|---|"]
    for air in (5, 10, 15, 20, 25, 30):
        r = race(air)
        out["cases"][str(air)] = {k: v for k, v in r.items() if k != "log"}
        out["cases"][str(air)]["log"] = r["log"][::5]
        hot = "着かない（ゴールで +%.1f℃）" % (r["temp_end"] - ASSUME["body_temp"]) if not r["hot"] \
            else "%.1f km（%s）" % (r["hot"]["km"], hms(r["hot"]["t"]))
        after = "—" if not r["hot"] else "時速 %.1f km" % (r["v_after"] * 3.6)
        res = "完走" if r["finished"] and r["time"] <= CUTOFF else ("時間切れ" if r["finished"] else "リタイア（%.1f km）" % r["km"])
        lines.append("| %d℃ | %s | %s | %s | %s | %.0f kcal |" % (air, res, hms(r["time"]) if r["finished"] else "—", hot, after, r["kcal"]))
    lines.append("")

    main_case = race(10)
    t = main_case["time"]
    rank = sum(1 for s in secs if s < t) + 1
    out["main"] = {"air": 10, "time": t, "rank_men_tokyo2026": rank, "kcal": main_case["kcal"],
                   "temp_rise": main_case["temp_end"] - ASSUME["body_temp"],
                   "onigiri": main_case["kcal"] / 180.0}
    lines += ["## 画面に出す回（気温 10℃）", "",
              "- タイム %s、ゴールでの体温 +%.1f℃" % (hms(t), out["main"]["temp_rise"]),
              "- 東京マラソン 2026 の男子の記録に当てはめると %d 位（%s より速い人が %d 人）" % (rank, hms(t), rank - 1),
              "- 参加者 %s 人のうち上位 %.2f%%" % (format(STARTERS, ","), 100.0 * rank / STARTERS),
              "- 使ったエネルギー %.0f kcal（おにぎり 1 個 180 kcal として %.0f 個）" % (main_case["kcal"], out["main"]["onigiri"]),
              "- 5 km ごとの体温：" + "、".join(
                  "%d km +%.1f℃" % (k, next(l["temp"] for l in main_case["log"] if l["km"] >= k) - ASSUME["body_temp"])
                  for k in (10, 20, 30, 40)),
              ""]
    lines += ["## 目安にした値", ""] + ["- %s = %s" % kv for kv in ASSUME.items()] + [""]

    open(os.path.join(HERE, "results.md"), "w", encoding="utf-8").write("\n".join(lines))
    json.dump(out, open(os.path.join(HERE, "race.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
