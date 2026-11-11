"""pilot_050 のショット l03（先頭との差）・l04（後ろの大集団）・l05（20 km の給水）。"""
from stage import *

S = {}


# ------------------------------------------------------------------ l03：先頭は前へ（2 カット、t=TC で切り替え）
TC = 2.6
W03 = walker(lambda t: 1.0, y0=0.)


def s_l03():
    base(); city.street(y0=-700, y1=1400, cross=0)
    crowd("cheer", -700, 700, lod=1, seed=51, fill=.3)
    rnd = np.random.default_rng(9)
    P = np.stack([rnd.uniform(-2.6, 2.6, 8), 145 + rnd.uniform(-3, 3, 8)], 1)
    S["leadA"] = runners("leadA", P, WRV, seed=52)
    P = np.stack([rnd.uniform(-3.5, 3.5, 8), 300 + rnd.uniform(-3, 3, 8)], 1)
    S["leadB"] = runners("leadB", P, WRV, seed=53, lod=1)
    P = np.stack([rnd.uniform(-12, 12, 24), rnd.uniform(15, 140, 24)], 1)
    runners("mid", P, rnd.uniform(5.45, 5.85, 24), seed=54)
    y = -10 - 390 * rnd.random(40) ** .7; P = np.stack([rnd.uniform(-12, 12, 40), y], 1)
    runners("back", P, rnd.uniform(4.4, 5.3, 40), seed=55, lod=1)


def a_l03(u, t, f):
    y, ph, amp = W03(t)
    trex.tpose(pos=(0, y), ph=ph, amp=amp, t=t, jaw=.06, pant=.4)
    a = t < TC
    keyhide(S["leadA"].o, not a, f); keyhide(S["leadB"].o, a, f)
    if a:
        yl = 145 + WRV * t
        cam.look((.6, yl + 60, 1.6), (0, y + 3, 2.6), 200)
    else:
        e = ease((t - TC) / (SPLAN["l03"]["dur"] - TC))
        cam.look((-1.2, y - 13, 8.0 + e), (0, y + 40, 0), 28 + 6 * e)


# ------------------------------------------------------------------ l04：後ろの大集団（ドローン）
W04 = walker(lambda t: 1.0, y0=0.)


def s_l04():
    base(sun_el=65, sun_rot=20); city.street(y0=-2600, y1=300, far=True)
    crowd("cheer", -2600, 300, lod=1, seed=61, fill=.25)
    rnd = np.random.default_rng(11)
    P = np.stack([rnd.uniform(-12, 12, 140), -12 - 290 * rnd.random(140) ** .8], 1)
    runners("near", P, rnd.uniform(2.6, 3.8, 140), seed=62)
    y = -300 - 2300 * np.sqrt(rnd.random(4500)); P = np.stack([rnd.uniform(-13, 13, 4500), y], 1)
    runners("far", P, rnd.uniform(2.3, 3.2, 4500), seed=63, lod=1)


def a_l04(u, t, f):
    y, ph, amp = W04(t)
    trex.tpose(pos=(0, y), ph=ph, amp=amp, t=t, jaw=.06, pant=.5)
    e = ease(u)
    cam.look(Vector((4, y + 22, 12)).lerp(Vector((6, y + 34, 22)), e), (-1, y - 40, 0), 28)


# ------------------------------------------------------------------ l05：20 km の給水（バケツをくわえる）
TX, TG = 1.2, 3.0                       # ティラノの x、くわえる時刻（台は奥の -X 側）
W05 = walker(lambda t: 1 - .22 * smooth(1.6, 2.6, t) * (1 - smooth(3.4, 4.6, t)), y0=0.)


def _pose05(t):
    g = smooth(1.5, 2.9, t) * (1 - smooth(3.0, 3.7, t))                   # 頭を -X（台）へ向ける
    lift = smooth(3.3, 4.5, t) * (1 - smooth(5.3, 6.4, t))                # 上を向いて飲む
    jaw = .32 * smooth(2.1, 2.7, t) * (1 - smooth(2.8, TG, t)) + .1 * smooth(2.8, TG, t)
    y, ph, amp = W05(t)
    trex.tpose(pos=(TX, y), ph=ph, amp=amp, t=t, neck=(-.1 * g + .22 * lift, .3 * g), head=(-.06 * g + .42 * lift, .28 * g), jaw=jaw, pant=.3, lid=.25 * lift)
    return y


def s_l05():
    base(sun_el=72, sun_rot=10); city.street(y0=-80, y1=200)
    yg = W05(TG)[0]; S["yg"] = yg
    crowd("cheer", yg - 40, yg + 60, sides=(-1,), lod=0, seed=71, gaps=()); crowd("cheer_r", -80, 200, sides=(1,), lod=1, seed=72, fill=.5)
    tables("water", -13.2, yg - 10, yg + 14)
    rnd = np.random.default_rng(13); P = np.stack([np.full(7, -12.5), np.linspace(yg - 8, yg + 12, 7) + rnd.uniform(-.4, .4, 7)], 1)
    people.People("staff", P, heading=-math.pi / 2, mode=np.where(rnd.random(7) < .6, 1, 2), seed=73, bib=False, shirts=[(.1, .45, .8)])
    board("wboard", "water", (-13.9, yg + 2, 3.35), 3.6, 1.5, n=(1, 0, 0))
    board("km20", "km20", (-12.6, yg - 22, 2.4), 1.6, 1.6, n=(1, 0, 0))
    P = np.stack([rnd.uniform(-10, -6, 5), rnd.uniform(-6, 30, 5)], 1); runners("run", P, rnd.uniform(4.0, 4.8, 5), seed=74)
    # くわえる瞬間の口の位置から、バケツ・係・台を置く
    _pose05(TG); bpy.context.view_layer.update(); M = wpos(trex.T["head"], MOUTH)
    bc = M + Vector((-.3, 0, -.2)); S["bc"] = bc
    S["bA"] = bucket("bucketA"); S["bA"].location = bc
    S["bB"] = bucket("bucketB"); S["bB"].parent = trex.T["head"]; hp = trex.T["head"]
    S["bB"].location = hp.matrix_world.inverted() @ bc; S["bB"].rotation_euler = (hp.matrix_world.inverted().to_euler())
    hpp = people.People("helper", [(0, 0)], heading=-math.pi / 2, mode=1, seed=75, bib=False, wave=0, shirts=[(.1, .45, .8)])
    hpp.ph[:] = 0; hpp.one[:] = False; hpp.s[:] = 1; hpp.update(0)
    hm = sum(hands(hpp), Vector()) / 2; tgt = bc + Vector((-.33, 0, .05)); hpp.o.location = tgt - hm
    DYN.remove(hpp.update)                                             # 係は動かない（腕を上げたまま）
    platform("stand", hpp.o.location.x - .1, hpp.o.location.y, hpp.o.location.z, w=1.0, d=1.4, open_side=1)
    log("l05 mouth", tuple(round(c, 2) for c in M), "helper", tuple(round(c, 2) for c in hpp.o.location))
    # 水しぶき：飲む間にバケツの縁からこぼれる
    ts = np.linspace(3.3, 5.4, 22); bpos = []
    for tt in ts:
        _pose05(tt); bpy.context.view_layer.update(); bpos.append(np.array(S["bB"].matrix_world.translation))
    bpos = np.array(bpos); n = 700; born = rnd.uniform(3.4, 5.3, n)
    bp = np.stack([np.interp(born, ts, bpos[:, k]) for k in range(3)], 1)
    a = rnd.uniform(0, 6.28, n); p0 = bp + np.stack([np.cos(a) * .3, np.sin(a) * .3, np.full(n, .25)], 1)
    v0 = np.stack([rnd.normal(0, .9, n), V * .85 + rnd.normal(0, .8, n), rnd.uniform(.3, 2.2, n)], 1)
    wm = mat("splash", (.8, .9, 1.0), .02); bs = wm.node_tree.nodes["Principled BSDF"]
    bs.inputs["Transmission Weight"].default_value = 1.0; bs.inputs["IOR"].default_value = 1.33
    city.Drops("splash", p0, v0, born, .016, wm, life=2.0, seed=76)
    S["steam"] = Steam("steam", 12, lambda b: (TX, W05(b)[0] + .6, 4.4), life=2.4, r=.75, dens=.028, rise=1.0, drift=(0, -1.5, 0))


def a_l05(u, t, f):
    y = _pose05(t); fg = int(round(TG * K.FPS))
    keyhide(S["bA"], f >= fg, f); keyhide(S["bB"], f < fg, f)
    S["steam"].key(t, f)
    yh = y + 3.4; tgt = Vector((.2, yh, 3.3)).lerp(Vector((.2, yh, 3.9)), smooth(3.3, 4.5, t))
    cam.look((6.0, 19 + 3.6 * t, 1.6), tgt, 30)
