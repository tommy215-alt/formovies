"""pilot_049：5 万人のハンマーの一斉投げで、怪獣を揺らして倒せるか（ブランコを押すのと同じ）。

モデル：怪獣を「かかとを支点にして揺れる直方体」とみる（Housner 1963 のロッキングの式）。
  I θ'' = -W R sin(α·sign θ - θ)、α = atan(b / hc)、R = √(b² + hc²)、I = 4/3 M R²（支点まわり）。
  支点が入れかわる（直立を通る）たびに角速度が r = 1 - 1.5 sin²α 倍になる（エネルギーを失う）。
  一斉投げは、怪獣が人の側から遠ざかる向きに動いているときに当てる（毎回 1 回、ブランコを押す向き）：角運動量 J·h を足す。
  |θ| が α を超えたら倒れる。
python rock.py → rock.json（何回目の一斉投げで倒れるか、揺れの角度の変化）
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = 9.81
M = 2.0e7          # 体重 kg（2 万トン）
B = 5.0            # 足の前後の幅の半分 m（目安）
HC = 20.0          # 重心の高さ m（目安：身長 50 m の 4 割）
HIT = 24.0         # ハンマーが当たる高さ m（battle.py：一番高く上がる高さ）
N = 50_000         # 人数（ユーザー）
HAMMER_M = 7.26
V = math.sqrt(G * 86.74)   # 投げた速さ（世界記録の飛距離から、45 度）
HIT_V = V * math.cos(math.radians(45))   # 一番高い所では横向きの速さだけ（当たるのは頂点）


def simulate(n_people, dt=1e-3, t_max=3600.0):
    a = math.atan(B / HC); R = math.hypot(B, HC); I = 4 / 3 * M * R * R; W = M * G
    r = 1 - 1.5 * math.sin(a) ** 2
    dL = n_people * HAMMER_M * HIT_V * HIT * math.cos(a)   # 当たる向きと支点の位置で少し減る（目安）
    th, om, t, pushes, peaks, last_sign = 0.0, 0.0, 0.0, 0, [], 0
    om += dL / I; pushes = 1
    prev_om = om
    while t < t_max:
        s = 1 if th > 0 else -1 if th < 0 else (1 if om > 0 else -1)
        acc = -W * R * math.sin(a * s - th) / I
        om += acc * dt; th += om * dt; t += dt
        if th * (th - om * dt) < 0:      # 直立を通った → 支点が入れかわる
            om *= r
            if om > 0:                   # 人の側から遠ざかる向き → 一斉投げ
                om += dL / I; pushes += 1
        if prev_om > 0 >= om:            # 揺れのいちばん遠い所
            peaks.append((round(t, 2), pushes, round(math.degrees(th), 3)))
        prev_om = om
        if abs(th) > a:
            return dict(fall=True, t=t, pushes=pushes, peaks=peaks, alpha_deg=math.degrees(a), dL=dL, I=I)
        if pushes > 2000:
            break
    return dict(fall=False, t=t, pushes=pushes, peaks=peaks, alpha_deg=math.degrees(a), dL=dL, I=I)


if __name__ == "__main__":
    o = simulate(N)
    lo = None
    for n in range(1000, N + 1, 1000):   # 何人いれば倒せるか（下限）
        if simulate(n, t_max=7200.0)["fall"]:
            lo = n; break
    o["min_people"] = lo
    o["hit_v"] = HIT_V
    o["per_volley_Ns"] = N * HAMMER_M * HIT_V
    (HERE / "rock.json").write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"倒れる角度 {o['alpha_deg']:.1f} 度、1 回の一斉投げの勢い {o['per_volley_Ns']:.2e} N·s")
    print(f"5 万人：{'倒れる' if o['fall'] else '倒れない'}、{o['pushes']} 回目の一斉投げ、{o['t']:.0f} 秒後")
    print("揺れの角度（秒, 回, 度）:", o["peaks"][:3], "…", o["peaks"][-3:])
    print("倒せる最少の人数（1,000 人きざみ）:", lo)
