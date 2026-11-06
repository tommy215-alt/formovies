"""最初の 30 分：都庁前を中心に 10 km 四方を 25 m のマスで計算する。

人とゾンビを「マスごとの人数」で扱う（連続体のモデル）。0.5 秒きざみ。
出力：data/micro.npz（10 秒ごとの集計と、決まった時刻のマップ）
"""
import math, os
import numpy as np
import params as P
from build_grid import latlon_rc

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
DX = 25.0
N = 640                 # 16 km
DT = 0.5
HANDOFF_MIN = 10        # ここで 1 km の計算（macro.py）に引き継ぐ（ゾンビが範囲の端に届く前）
T_END = HANDOFF_MIN * 60
SNAP_MIN = [0.5, 1, 2, 3, 5, 7, 10]


def box(a, r):
    if r < 1:
        return a
    k = 2 * r + 1
    p = np.pad(a, r)
    c = np.cumsum(p, 0); c = np.vstack([np.zeros((1, c.shape[1])), c]); a = (c[k:] - c[:-k]) / k
    c = np.cumsum(a, 1); c = np.hstack([np.zeros((c.shape[0], 1)), c]); return (c[:, k:] - c[:, :-k]) / k


def blur(a, r):
    return box(box(a, max(1, r // 2)), max(1, r // 2))


def grad(a):
    gy = np.zeros_like(a); gx = np.zeros_like(a)
    gy[1:-1] = (a[2:] - a[:-2]) / 2; gx[:, 1:-1] = (a[:, 2:] - a[:, :-2]) / 2
    return gy, gx


def advect(q, vy, vx, frac_cap=0.9):
    """風上差分で q を速度 (vy, vx)[m/s] で動かす。端からは出ない。"""
    fn = np.clip(vy, 0, None) * DT / DX; fs = np.clip(-vy, 0, None) * DT / DX
    fe = np.clip(vx, 0, None) * DT / DX; fw = np.clip(-vx, 0, None) * DT / DX
    tot = fn + fs + fe + fw
    s = np.where(tot > frac_cap, frac_cap / np.maximum(tot, 1e-12), 1.0)
    fn, fs, fe, fw = fn * s, fs * s, fe * s, fw * s
    fn[-1] = 0; fs[0] = 0; fe[:, -1] = 0; fw[:, 0] = 0
    out = q * (1 - fn - fs - fe - fw)
    out[1:] += (q * fn)[:-1]; out[:-1] += (q * fs)[1:]
    out[:, 1:] += (q * fe)[:, :-1]; out[:, :-1] += (q * fw)[:, 1:]
    return out


def diffuse(q, f):
    out = q * (1 - 4 * f)
    out[1:] += q[:-1] * f; out[:-1] += q[1:] * f; out[:, 1:] += q[:, :-1] * f; out[:, :-1] += q[:, 1:] * f
    out[0] += q[0] * f; out[-1] += q[-1] * f; out[:, 0] += q[:, 0] * f; out[:, -1] += q[:, -1] * f
    return out


def cell_latlon():
    lat0, lon0 = P.START_LATLON
    i = (np.arange(N) - N / 2 + 0.5) * DX
    lat = lat0 + i / 111000.0
    lon = lon0 + i / (111000.0 * math.cos(math.radians(lat0)))
    return lat, lon


def init():
    day = np.load(os.path.join(D, "grid.npz"))["day"]
    lat, lon = cell_latlon()
    mesh_area = 0.925 * 1.130 * 1e6
    pop = np.zeros((N, N))
    for a, la in enumerate(lat):
        r, _ = latlon_rc(la, lon[0])
        for b, lo in enumerate(lon):
            _, c = latlon_rc(la, lo)
            pop[a, b] = day[r, c] * DX * DX / mesh_area
    O = pop * P.OUT_FRAC_NOON
    I = pop - O
    sy = (P.STATION_LATLON[0] - P.START_LATLON[0]) * 111000 / DX + N / 2
    sx = (P.STATION_LATLON[1] - P.START_LATLON[1]) * 111000 * math.cos(math.radians(P.START_LATLON[0])) / DX + N / 2
    yy, xx = np.mgrid[0:N, 0:N]
    st = np.exp(-(((yy - sy) ** 2 + (xx - sx) ** 2) * DX * DX) / (2 * 150.0 ** 2))
    O += P.STATION_CROWD * st / st.sum()
    return O, I, (sy, sx)


def run():
    O, I, st = init(); O = O.astype(np.float32); I = I.astype(np.float32)
    Z = np.zeros((N, N), np.float32); Z[N // 2, N // 2] = 1.0
    nE = int(P.TURN_TIME / DT)
    E = [np.zeros((N, N), np.float32) for _ in range(nE)]
    U = np.ones((N, N), np.float32)
    aware = np.zeros((N, N), bool)
    sight = int(P.Z_SIGHT / DX); hear = int(P.Z_HEAR / DX)
    yy, xx = np.mgrid[0:N, 0:N]
    near_hq = ((yy - N / 2) ** 2 + (xx - N / 2) ** 2) * DX * DX < 1500.0 ** 2
    p_kill = sum(math.comb(P.POLICE_ROUNDS, k) * P.POLICE_HIT ** k * (1 - P.POLICE_HIT) ** (P.POLICE_ROUNDS - k)
                 for k in range(P.HITS_TO_STOP, P.POLICE_ROUNDS + 1))
    cum = dict(bit_out=0.0, bit_in=0.0, police=0.0, police_bit=0.0, police_kill=0.0)
    rows, snaps = [], {}
    pop0 = O.sum() + I.sum()
    steps = int(T_END / DT)
    for k in range(steps + 1):
        t = k * DT
        # かまれた人は 10 秒後にゾンビに
        Z += E.pop(0); E.append(np.zeros((N, N), np.float32))
        Ebuf = E[-1]
        # 屋外でかむ
        busy = O / (O + 1.0)
        b_out = np.minimum(O * 0.9, Z * busy * (1.0 / (P.BITE_TIME + 2.0)) * DT)
        # 開いている建物の中でかむ
        free = Z * (1 - busy)
        acc = I * P.OPEN_FRAC * U   # 入り込める所にいる人
        b_in = np.minimum(acc * 0.5, free * P.INDOOR_BITE * acc / (acc + 20.0) * DT)
        O -= b_out; I -= b_in; Ebuf += b_out + b_in
        cum["bit_out"] += b_out.sum(); cum["bit_in"] += b_in.sum()
        # 警察官
        if t >= P.POLICE_FIRST_MIN * 60:
            n_new = (10 if cum["police"] == 0 else 0) + P.POLICE_RAMP_PER_MIN * DT / 60
            zt = (Z * near_hq).sum()
            if zt > 0.5:
                w = Z * near_hq / zt
                kill = min(n_new * p_kill, zt)
                Z -= w * kill; Ebuf += w * n_new * 0.9
                cum["police_kill"] += kill; cum["police_bit"] += n_new * 0.9
            cum["police"] += n_new
        # 気づく（近くにゾンビ）→ 建物の入口が閉まっていく
        zb = blur(Z + Ebuf, 4)
        aware |= zb > 0.01
        media = t >= P.T_MEDIA_MIN * 60
        lock_rate = np.where(aware, 1 / P.LOCK_TAU, (1 / 600.0) if media else 0.0)
        U = LOCK_MIN_STEP(U, lock_rate)
        # 屋外の人：気づいた人は建物へ、ゾンビから離れる
        sh = np.where(aware, DT / P.SHELTER_TAU, (DT / 600.0) if media else 0.0)
        moved = O * sh
        O -= moved; I += moved
        gy, gx = grad(zb); mag = np.hypot(gy, gx) + 1e-9
        vy = np.where(aware, -gy / mag * P.FLEE_SPEED, 0); vx = np.where(aware, -gx / mag * P.FLEE_SPEED, 0)
        O = advect(O, vy, vx)
        # ゾンビ：見える人へ全力で、いなければうろつく
        a_s = blur(O, sight); a_h = blur(O + 0.02 * I * P.OPEN_FRAC * U, hear)
        gy, gx = grad(a_s + 0.05 * a_h); mag = np.hypot(gy, gx) + 1e-9
        speed = np.where(a_s > 0.05, P.Z_SPRINT, np.where(a_h > 0.05, P.Z_WANDER * 2, 0.0))
        mv = 1 - busy
        Zm = Z * mv
        Z = Z - Zm + advect(Zm, gy / mag * speed, gx / mag * speed)
        Z = diffuse(Z, (P.Z_WANDER ** 2 * 60 / 2) * DT / (DX * DX))
        if k % 20 == 0:
            zz = Z > 0.5
            rmax = (np.sqrt(((yy - N / 2) ** 2 + (xx - N / 2) ** 2)[zz]).max() * DX) if zz.any() else 0
            rows.append((t, Z.sum(), sum(e.sum() for e in E), cum["bit_out"], cum["bit_in"], cum["police"],
                         cum["police_kill"], O.sum(), (I * P.OPEN_FRAC * U).sum(), rmax, (aware.sum() * DX * DX / 1e6)))
        for m in SNAP_MIN:
            if abs(t - m * 60) < DT / 2:
                snaps[f"Z_{m}"] = Z.astype(np.float32); snaps[f"O_{m}"] = O.astype(np.float32)
                snaps[f"I_{m}"] = I.astype(np.float32); snaps[f"E_{m}"] = sum(E).astype(np.float32)
    snaps["I"] = I.astype(np.float32); snaps["U"] = U.astype(np.float32); snaps["E"] = sum(E).astype(np.float32)
    rows = np.array(rows)
    np.savez_compressed(os.path.join(D, "micro.npz"), rows=rows, station=np.array(st), pop0=pop0, **snaps)
    return rows


def LOCK_MIN_STEP(U, rate):
    return P.LOCK_MIN + (U - P.LOCK_MIN) * np.exp(-rate * DT)


if __name__ == "__main__":
    rows = run()
    print("時刻   ゾンビ   変化中  かまれた(外/中)  警察官(倒した)  屋外の人  開いた建物の人  広がり(m)  気づいた範囲(km2)")
    for r in rows:
        if int(r[0]) in (10, 30, 60, 90, 120, 180, 240, 300, 420, 540, 600):
            print(f"{r[0]/60:5.1f}分 {r[1]:9.0f} {r[2]:7.0f} {r[3]:9.0f}/{r[4]:8.0f} {r[5]:6.0f}({r[6]:4.1f}) {r[7]:9.0f} {r[8]:9.0f} {r[9]:7.0f} {r[10]:7.1f}")
