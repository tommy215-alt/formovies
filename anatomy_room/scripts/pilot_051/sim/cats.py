# -*- coding: utf-8 -*-
"""pilot_051 もしも設計「猫 何匹で、新幹線は動く？」

16 両の新幹線を、猫が綱で引く。動き出すのに何匹、引き続けるのに何匹、坂では何匹、
東京から新大阪まで何日、新幹線のモーターと同じ力を出すには何匹かを計算する。
使い方: python cats.py  → results.md・cats.json を書く。

元の値（出典は ../fact_check.md）
  列車の重さ 700 t ……………… N700S 16 両（JR 東海の計画「700 t 以下」）
  動き出すときの抵抗 30 N/t …… 出発抵抗（ころ軸受）
  進むときの抵抗 ………………… 100 系の式 g(1.273 + 0.001v + 0.0001381v²) N/t（v は km/h）
  坂の抵抗 9.8 N/t（1‰ あたり）、東海道新幹線の最大勾配 20‰
  モーター 305 kW × 56 台 ＝ 17,080 kW
  東京〜新大阪 515.4 km（実際の距離）、最速 2 時間 21 分
  猫の歩く速さ 秒速 0.67 m、最高 時速 48 km
目安（出典のない仮定）は ASSUME にまとめた。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81

TRAIN_T = 700.0
START_N_PER_T = 30.0
GRADE_N_PER_T = 9.8          # 1‰ あたり
GRADE_MAX = 20.0             # ‰
MOTOR_KW = 305.0 * 56
DIST_KM = 515.4
FASTEST_MIN = 2 * 60 + 21
CAT_WALK = 0.67              # m/s
CAT_TOP_KMH = 48.0
PET_CATS = 8847000           # 日本の飼い猫（2025 年、目安）

ASSUME = {
    "cat_kg": 4.0,           # 猫 1 匹の体重
    "pull_long": 0.10,       # 引き続けられる力 = 体重の 10%（牛・馬が荷を引くときの目安）
    "pull_start": 0.50,      # 一瞬だけ出せる力 = 体重の 50%
    "walk_hours": 10.0,      # 1 日に歩く時間（残りの 14 時間は寝る）
}


def running(v_kmh):
    """平らな線路を進むときの抵抗 [N/t]"""
    return G * (1.273 + 0.001 * v_kmh + 0.0001381 * v_kmh ** 2)


def main():
    w = ASSUME["cat_kg"] * G
    f_long, f_start = w * ASSUME["pull_long"], w * ASSUME["pull_start"]
    v_kmh = CAT_WALK * 3.6

    need_start = TRAIN_T * START_N_PER_T
    need_run = TRAIN_T * running(v_kmh)
    cats_start = need_start / f_start
    cats_run = need_run / f_long
    grades = {}
    for g in (1, 3, 5, 10, 15, 20):
        grades[g] = (need_run + TRAIN_T * GRADE_N_PER_T * g) / f_long
    cat_w = f_long * CAT_WALK
    cats_motor = MOTOR_KW * 1000 / cat_w
    hours = DIST_KM / v_kmh
    days = hours / ASSUME["walk_hours"]
    # 猫の列：1 匹に前後 0.6 m・左右 0.4 m、線路の幅（複線の敷地 約 11 m）に 25 匹ならぶ
    row = 25
    line_m = {k: v / row * 0.6 for k, v in (("start", cats_start), ("run", cats_run), ("grade20", grades[20]), ("motor", cats_motor))}

    out = {
        "cat_pull_long_n": f_long, "cat_pull_start_n": f_start, "cat_watt": cat_w,
        "need_start_n": need_start, "need_run_n": need_run,
        "cats_start": cats_start, "cats_run": cats_run, "cats_grade": grades,
        "speed_kmh": v_kmh, "hours": hours, "days": days,
        "cats_motor": cats_motor, "motor_share_of_pets": cats_motor / PET_CATS,
        "times_slower": hours * 60 / FASTEST_MIN, "line_m": line_m,
    }
    L = ["# pilot_051 計算の結果（cats.py）", "",
         "## 猫 1 匹", "",
         "- 体重 %.0f kg（重さ %.1f N）" % (ASSUME["cat_kg"], w),
         "- 引き続けられる力：%.2f N（約 %.0f g のおもりを持ち上げる力）" % (f_long, f_long / G * 1000),
         "- 一瞬だけ出せる力：%.1f N（約 %.0f kg）" % (f_start, f_start / G),
         "- 歩く速さ：秒速 %.2f m ＝ 時速 %.1f km、引く仕事 %.2f W" % (CAT_WALK, v_kmh, cat_w),
         "",
         "## 列車（%.0f t）" % TRAIN_T, "",
         "- 動き出すのに要る力：%s N（約 %.1f t の物を持ち上げる力）" % (format(round(need_start), ","), need_start / G / 1000),
         "- 時速 %.1f km で進み続けるのに要る力：%s N（約 %.0f kg）" % (v_kmh, format(round(need_run), ","), need_run / G),
         "",
         "## 何匹", "",
         "- 動き出す（一瞬の力）：%s 匹 → 約 1,100 匹" % format(round(cats_start), ","),
         "- 平らな線路を引き続ける：%s 匹 → 約 2,200 匹" % format(round(cats_run), ","),
         ]
    L += ["- 坂 %d‰（1000 m で %d m のぼる）：%s 匹" % (g, g, format(round(n), ",")) for g, n in grades.items()]
    L += ["- モーター（%s kW）と同じ仕事：%s 匹 → 約 650 万匹（日本の飼い猫 約 885 万匹の %.0f%%）"
          % (format(round(MOTOR_KW), ","), format(round(cats_motor), ","), 100 * out["motor_share_of_pets"]),
          "",
          "## 東京 → 新大阪（%.1f km）" % DIST_KM, "",
          "- 休まず歩いて %.1f 時間（%.1f 日）" % (hours, hours / 24),
          "- 1 日 %.0f 時間だけ歩くと %.1f 日 → 約 3 週間" % (ASSUME["walk_hours"], days),
          "- 新幹線の最速 2 時間 21 分の %.0f 倍" % out["times_slower"],
          "- 猫の最高の速さ 時速 %.0f km は、新幹線の最高 時速 285 km の約 1/%.0f" % (CAT_TOP_KMH, 285 / CAT_TOP_KMH),
          "",
          "## 猫の列の長さ（横に %d 匹、前後 0.6 m）" % row, ""]
    L += ["- %s：%.0f m" % (k, v) for k, v in line_m.items()]
    L += ["", "## 目安にした値", ""] + ["- %s = %s" % kv for kv in ASSUME.items()] + [""]

    open(os.path.join(HERE, "results.md"), "w", encoding="utf-8").write("\n".join(L))
    json.dump(out, open(os.path.join(HERE, "cats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main()
