"""ティラノサウルスの早歩きの脚の計算（bpy なし。python gait.py で確かめる）。
歩幅（左右 1 回ずつ）6.5 m・周期 1.2 秒 → 秒速 5.4 m。足は地面についている間、世界に対して動かない（すべらない）。"""
import math

HIP = 3.1
J_HIP, J_KNEE, J_ANK, J_MTP = (0.0, HIP), (.80, 2.14), (-.03, .95), (.26, .15)   # 置いた姿勢の関節 (y, z)
STRIDE, DUTY, PERIOD = 6.5, .554, 6.5 / 5.4


def _ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


L_FEM, L_TIB, L_MET = _len(J_HIP, J_KNEE), _len(J_KNEE, J_ANK), _len(J_ANK, J_MTP)
R_FEM, R_TIB, R_MET = _ang(J_HIP, J_KNEE), _ang(J_KNEE, J_ANK), _ang(J_ANK, J_MTP)


def lerp(a, b, u):
    return a + (b - a) * u


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def hip_z(ph, amp, sit):
    return lerp(HIP - amp * (.06 + .2 * (.5 + .5 * math.cos(4 * math.pi * ph - .5))), 1.22, sit)


def leg(p, amp, hz, sit, info=None):
    """p：この脚の周期の中の位置（0＝着地）。返す：もも・すね・中足・指の、置いた姿勢からの回転（絶対）"""
    c = lerp(.1, .9, sit); h = STRIDE * DUTY / 2 * amp
    if p < DUTY:
        s = p / DUTY; fy = c + h * (1 - 2 * s); fz = 0.0; a = 70 + amp * lerp(-18, 34, s ** 1.5); tp = 0.0
    else:
        s = (p - DUTY) / (1 - DUTY); e = s * s * (3 - 2 * s); fy = c + h * (-1 + 2 * e); fz = amp * .7 * math.sin(math.pi * s)
        a = 70 + amp * (lerp(34, -18, s) + 42 * math.sin(math.pi * s)); tp = -amp * .6 * math.sin(math.pi * s)
    a = math.radians(lerp(a, 25, sit))
    F = (fy, J_MTP[1] + fz); A = (F[0] - L_MET * math.cos(a), F[1] + L_MET * math.sin(a))
    dy, dz = A[0], A[1] - hz; d0 = math.hypot(dy, dz); d = max(abs(L_FEM - L_TIB) + .05, min(L_FEM + L_TIB - .02, d0))
    phi = math.atan2(dz, dy); al = math.acos(max(-1, min(1, (L_FEM ** 2 + d * d - L_TIB ** 2) / (2 * L_FEM * d))))
    fem = phi + al; kp = (L_FEM * math.cos(fem), hz + L_FEM * math.sin(fem)); tib = math.atan2(A[1] - kp[1], A[0] - kp[0])
    if info is not None:
        info.update(d0=d0, dmax=L_FEM + L_TIB - .02, knee=kp, ank=A, foot=F)
    return _wrap(fem - R_FEM), _wrap(tib - R_TIB), _wrap(-a - R_MET), tp


if __name__ == "__main__":
    print("femur %.2f tibia %.2f meta %.2f  reach %.2f" % (L_FEM, L_TIB, L_MET, L_FEM + L_TIB))
    worst = 0
    for i in range(0, 100, 4):
        ph = i / 100; hz = hip_z(ph, 1, 0); I = {}; r = leg(ph, 1, hz, 0, I); worst = max(worst, I["d0"] - I["dmax"])
        print("p %.2f hip %.2f foot (%.2f, %.2f) knee (%.2f, %.2f) d %.2f %s rot %s" % (ph, hz, *I["foot"], *I["knee"], I["d0"], "OVER" if I["d0"] > I["dmax"] else "", " ".join("%4.0f" % math.degrees(x) for x in r)))
    print("worst over-reach %.3f" % worst)
    I = {}; print("sit", [round(math.degrees(x)) for x in leg(.2, 0, hip_z(0, 0, 1), 1, I)], I)
