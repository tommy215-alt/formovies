"""pilot_050 のショット l00（スタート前）・l01（号砲）・l02（走れない脚）・l10（冒頭に戻る）。"""
from stage import *

S = {}
TY0 = -8.0                                   # スタート前のティラノの腰の y
AVOID = [(0, -3, 2.6), (0, -7, 2.6), (0, -11, 2.4), (0, -14.5, 2.0)]
FRONT, DENS = -1.0, .4                       # 先頭の列の y、1 人あたりの面積（m²）
YBACK = FRONT - PLAN["n"] * DENS / 28.0      # 最後尾の y（約 -525 m）


def _start_world(lod0_y=-46., strip=None, keep=None):
    """スタートの通り：門・応援・36,697 人のランナー。strip：(x0, x1, y0) の帯（x0〜x1・y>y0）に人を置かない"""
    base(sun_el=70, sun_rot=20)
    city.street(y0=-640, y1=900); city.gate(2, "start")
    c0 = crowd("cheer0", -60, 60, lod=0, seed=11); c1 = crowd("cheer1", -640, -60, lod=1, seed=12, fill=.7); c2 = crowd("cheer2", 60, 900, lod=1, seed=13, fill=.5)
    P = people.grid(PLAN["n"], -14, 14, YBACK, FRONT, seed=21, avoid=AVOID)
    if strip:
        x0, x1, y0 = strip; P = P[~((P[:, 0] > x0) & (P[:, 0] < x1) & (P[:, 1] > y0))]
    near = P[P[:, 1] > lod0_y]; far = P[P[:, 1] <= lod0_y]
    return near, far


# ------------------------------------------------------------------ l00 / l10：スタート前（ループ）
def _s_start():
    near, far = _start_world()
    rnd = np.random.default_rng(3); md = np.where(rnd.random(len(near)) < .12, 1, 2)
    S["near"] = people.split("run0", near, heading=0.0, mode=md, seed=31, wave=.6)
    S["far"] = people.People("run1", far, heading=0.0, mode=2, seed=32, lod=1)
    log("start world", len(near), len(far))


def _trex_wait(tt):
    trex.tpose(pos=(0, TY0), amp=0, t=tt, head=(.04 * math.sin(tt * .9), -.1 + .12 * math.sin(tt * .55 + .4)), neck=(0, -.04 + .05 * math.sin(tt * .55)), jaw=.04, tail=.03 * math.sin(tt * .7))


C00 = [((4, 16, 7), (0, -10, 3)), ((2.6, 4.5, 1.8), (-.4, -6.5, 3.3))]


def s_l00():
    _s_start()


def a_l00(u, t, f):
    _trex_wait(t); e = ease(u)
    (p0, a0), (p1, a1) = C00
    cam.look(Vector(p0).lerp(Vector(p1), e), Vector(a0).lerp(Vector(a1), e), 28)


def s_l10():
    _s_start()
    off = -SPLAN["l10"]["dur"]                # l10 の終わり＝l00 の始まり（人の腕の振りもつなげる）
    DYN[:] = [(lambda fn: (lambda t: fn(t + off)))(fn) for fn in DYN]


def a_l10(u, t, f):
    _trex_wait(t - SPLAN["l10"]["dur"]); e = ease(u)
    p0, a0 = C00[0]; ps = Vector(p0) + Vector((2, 6, 1.5))
    cam.look(ps.lerp(Vector(p0), e), Vector(a0), 28)


# ------------------------------------------------------------------ l01：号砲（大きな札 spec）
W01 = walker(lambda t: ease((t - .5) / 2.5), y0=TY0)


def s_l01():
    near, far = _start_world(lod0_y=-50., strip=(-7.5, 2.5, -45))
    keep = ~((np.abs(near[:, 0]) < 2.3) & (near[:, 1] > -40))
    near = near[keep]; rnd = np.random.default_rng(5); ay = np.abs(near[:, 1] - FRONT)
    sp = np.clip(5.9 - ay * .05 + rnd.normal(0, .25, len(near)), 2.5, 5.9); sp[ay < 3] = rnd.uniform(5.5, 5.9, (ay < 3).sum())
    S["near"] = people.People("run0", near, heading=0.0, speed=sp, mode=0, seed=31, delay=.15 + ay * .12)
    S["far"] = people.People("run1", far[far[:, 1] > -250], heading=0.0, mode=2, seed=32, lod=1)
    city.confetti("conf_l", (-12, 3, 7), n=400, t0=.1, seed=3); city.confetti("conf_r", (12, 3, 7), n=400, t0=.1, seed=4)


def a_l01(u, t, f):
    y, ph, amp = W01(t)
    dip = smooth(-7., -4.5, y) * (1 - smooth(-1.5, 1.0, y))           # 門の下で首を少し下げる
    trex.tpose(pos=(0, y), ph=ph, amp=amp, t=t, neck=(-.15 * dip, 0), head=(-.05 * dip, 0), jaw=.06, pant=.2 * amp)
    p = Vector((-4.6, y + 13.5, .9)); cam.look(p, aim_above(p, (0, y + 4.6, 0), 9.3), 24)


# ------------------------------------------------------------------ l02：実は走れない（脚の骨、大きな札 walk）
W02 = walker(lambda t: 1.0, y0=100.)


def s_l02():
    base(); city.street(y0=-60, y1=300)
    crowd("cheer", 60, 200, sides=(-1,), lod=0, seed=41); crowd("cheer_r", 60, 200, sides=(1,), lod=1, seed=42, fill=.5)
    rnd = np.random.default_rng(7); P = np.stack([rnd.uniform(-6.0, -3.0, 6), 100 + rnd.uniform(-9, 5, 6)], 1)
    runners("fast", P, rnd.uniform(5.55, 5.9, 6), seed=43)


def a_l02(u, t, f):
    y, ph, amp = W02(t)
    trex.tpose(pos=(0, y), ph=ph, amp=amp, t=t, jaw=.05, pant=.3)
    k = smooth(.18, .38, u) * (1 - smooth(.72, .88, u)); trex.xray(k, 6.0 * k, f)
    cam.look((13, y + 2.0, 1.6), (0, y + 1.6, 3.9), 28)
