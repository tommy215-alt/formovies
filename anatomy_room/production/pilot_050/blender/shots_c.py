"""pilot_050 のショット l06（優勝のテープ）・l07（ティラノのゴール）・l08（気温 30℃ならリタイア）・l09（結果）。"""
from stage import *

S = {}
TB = 3.1                                  # l06：テープを切る時刻


def _goal_world(clock, seed=81, conf_t0=None):
    base(sun_el=68, sun_rot=20); city.street(y0=-150, y1=120, cross=0); city.gate(.6, "goal", clock)
    city.box("goal_line", -RW, RW, -.2, .2, 0, .008, mat("paint", (.82, .82, .8), .55))
    crowd("cheer0", -40, 45, lod=0, seed=seed, cheer=.85); crowd("cheer1", -150, -40, lod=1, seed=seed + 1); crowd("cheer2", 45, 120, lod=1, seed=seed + 2)
    if conf_t0 is not None:
        city.confetti("conf_l", (-6, .9, 7.2), n=350, t0=conf_t0, seed=seed + 3, spread=3.5, up=6.0); city.confetti("conf_r", (6, .9, 7.2), n=350, t0=conf_t0, seed=seed + 4, spread=3.5, up=6.0)


def _tape_half(name, sx, L=3.3):
    """テープの半分（原点は持つ人の手、中央へのびる）"""
    bm = bmesh.new(); r_ = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(L, .006, .05), verts=r_["verts"])
    bmesh.ops.translate(bm, vec=(-sx * L / 2, 0, 0), verts=r_["verts"])
    o = mesh_obj(name, bm, [mat("tape", (.8, .04, .04), .5)]); o.location = (sx * L, 0, 1.05); o.rotation_mode = "XYZ"; return o


# ------------------------------------------------------------------ l06：優勝（先頭がテープを切る）
def s_l06():
    _goal_world(shot_clock("l06"), conf_t0=TB)
    ld = runners("leader", [(0, -WRV * TB)], WRV, seed=82, mode=3); ld.t3 = TB
    runners("second", [(1.4, -WRV * TB - 60)], 5.8, seed=83)
    people.People("holders", [(-3.45, .1), (3.45, .1)], heading=math.pi, mode=2, seed=84, bib=False, shirts=[(.1, .45, .8)])
    S["tape"] = [_tape_half("tapeL", -1), _tape_half("tapeR", 1)]
    people.People("staff6", [(-6.0, 2.2), (-6.8, -.4), (5.6, 2.6), (6.6, .3), (-7.6, 3.5)], heading=[2.6, 2.2, -2.6, -2.2, 2.4], mode=[1, 2, 1, 2, 1], seed=85, bib=False, shirts=[(.1, .45, .8), (.9, .9, .88)])
    trex.tpose(pos=(0, -5000), amp=0)


def a_l06(u, t, f):
    trex.tpose(pos=(0, -5000), amp=0, t=t)
    k = max(0., t - TB); th = 1.45 * (1 - math.exp(-k * 5) * math.cos(k * 9)) if k > 0 else 0.0
    ph = .7 * (1 - math.exp(-k * 4)) if k > 0 else 0.0
    for o, sx in zip(S["tape"], (-1, 1)):
        keyp(o, f, rot=(0, -sx * th, -sx * ph))
    e = ease(u); cam.look((2.5, 12 - 1.5 * e, 1.3), (0, -2, 3.4), 30)


# ------------------------------------------------------------------ l07：ティラノのゴール（大きな札 goal）
TL = 2.75
W07 = walker(lambda t: 1 - ease((t - TL) / 2.0), y0=-2.2 - V * TL)


def s_l07():
    _goal_world(shot_clock("l07"), seed=91, conf_t0=TL)
    runners("r2", [(3.0, -45)], 4.2, seed=92)


def a_l07(u, t, f):
    y, ph, amp = W07(t)
    dip = smooth(-8.5, -6.5, y) * (1 - smooth(-3.5, -1.5, y)); after = smooth(TL, TL + 1.5, t)
    trex.tpose(pos=(0, y), ph=ph, amp=amp, t=t, neck=(-.12 * dip - .08 * after, 0), head=(-.04 * dip + .1 * after, .12 * after * math.sin(t * .8)), jaw=.06 + .16 * after, pant=.3 + .7 * after, lid=.2 * after)
    d = y + 5.9; p = Vector((3.2, 6.6 + .5 * (d + math.sqrt(d * d + 4)), 1.4)); cam.look(p, aim_above(p, (0, y + 4.6, 0), 8.0), 26)


# ------------------------------------------------------------------ l08：気温 30℃（リタイア）
W08 = walker(lambda t: .55 * (1 - smooth(2.0, 3.0, t)), y0=-14.)
TX8 = -9.0


def _sit8(t):
    return float(smooth(3.0, 4.6, t))


def s_l08():
    base(sun_el=68, sun_rot=270, energy=8.0, exposure=-4.3, haze=(.95, .88, .76), haze_k=.9, d0=90., d1=2600.)
    city.street(y0=-200, y1=200, park=(-1, -130, 130))
    rnd = np.random.default_rng(15)
    P = [(rnd.uniform(-60, -25), rnd.uniform(-120, 120)) for _ in range(60)]
    city.trees(P, seed=16, h=(9, 14), r=(3.0, 4.6), name="park_trees")
    crowd("cheer", -60, 40, sides=(-1,), lod=0, seed=101, fill=.35, cheer=.3); crowd("cheer_r", -200, 200, sides=(1,), lod=1, seed=102, fill=.4)
    people.People("staff", [(-13.4, -6.0), (-12.9, -3.4)], heading=-math.pi / 2, mode=2, seed=103, bib=False, shirts=[(.1, .45, .8)])
    for i, (x, y) in enumerate(((-12.7, -5.6), (-12.3, -3.0))):
        b = bucket(f"bk{i}"); b.location = (x, y, .23)
    P = np.stack([rnd.uniform(-14.2, -11.8, 8), rnd.uniform(-45, -12, 8)], 1); runners("slow", P, rnd.uniform(2.3, 3.0, 8), seed=104)
    S["steam"] = Steam("steam", 14, lambda b: (TX8, W08(b)[0] + .5, 4.4 - 1.9 * _sit8(b)), life=2.8, r=.8, dens=.07, rise=.8, seed=9)


def a_l08(u, t, f):
    y, ph, amp = W08(t); s = _sit8(t)
    trex.tpose(pos=(TX8, y), ph=ph, amp=amp, sit=s, t=t, neck=(-.06 - .25 * s, .05 * s), head=(-.15 * s, .1 * s), jaw=.22, pant=1.0, lid=.5)
    S["steam"].key(t, f)
    e = ease(u); cam.look(Vector((6, 10, 1.7)).lerp(Vector((4, 7, 1.7)), e), (-9, -3, 2.4), 36)


# ------------------------------------------------------------------ l09：結果（大きな札 result）
def s_l09():
    _goal_world(shot_clock("l09"), seed=111, conf_t0=-.9)
    trex.medal(True)
    rnd = np.random.default_rng(17); P = np.stack([rnd.uniform(-11, 11, 8), rnd.uniform(-12, -2, 8)], 1)
    people.People("finishers", P, heading=rnd.uniform(-.5, .5, 8), mode=np.where(rnd.random(8) < .5, 1, 2), seed=112)


def a_l09(u, t, f):
    trex.tpose(pos=(0, 3), heading=.3, amp=0, t=t, neck=(-.04, .05 * math.sin(t * .7)), head=(-.06, .1 * math.sin(t * .7 + .5)), jaw=.12, pant=.25, tail=.03 * math.sin(t))
    e = ease(u); p = Vector((7.5, 17, 1.9)).lerp(Vector((6.6, 15, 2.1)), e)
    cam.look(p, aim_above(p, (-.6, 3 + 4.0, 0), 7.5), 30)
