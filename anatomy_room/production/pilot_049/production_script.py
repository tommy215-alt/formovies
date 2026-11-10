#!/usr/bin/env python3
"""pilot_049「身長50mの怪獣 vs 世界最強のハンマー投げ選手5万人」（もしも設計の既定、土台は pilot_048）の制作スクリプト。

計算は scripts/pilot_049/sim/battle.py（battle.json、条件と仮定 fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）。
ナレーションなし（silent_ext）、BGM なし（曲に聞こえる音も入れない）。音は環境音と効果音だけ：
怪獣の咆哮（Freesound の CC0 の動物の声を低く）・5 万人の声・ハンマーの風切りと金属音・炎・頭に当たる一撃・倒れる地響き。
共通エンディングなし（もしも設計）。最後は怪獣の目が開いて冒頭につながる（ループ）。
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("Cyborg Ninja.mp3", 160), ending_gain=0.0)   # 曲は全区間 f_mute、最後も 0（BGM なし）
import noend_ext  # noqa: E402
noend_ext.apply(pipeline, black=1.0)
import silent_ext  # noqa: E402
silent_ext.apply(pipeline)
import ambience  # noqa: E402
import music  # noqa: E402
from music import SR  # noqa: E402

PLAN = json.loads((HERE / "blender" / "plan.json").read_text(encoding="utf-8"))
SHOTS = PLAN["shots"]
TLP = HERE / "work" / "timeline.json"
SFX = HERE / "assets" / "sfx"
ambience.timeline(TLP)
ambience.click("click", 2600, gain=.7)   # ポップアップが出る音
ambience.register("crowd", SFX / "crowd.mp3", start=5, span=("l00", "l04", 0), norm="rms", fade_out=1.0)

# ショットごとの時計の間隔（秒）。早送りは速く。倒れたら止める
TICK = {"l00": 1.0, "l01": 1.0, "l02": 1.0, "l03": 1.0, "l04": 1.0, "l05": 1.0, "l06": .2, "l07": 1.0, "l08": None, "l09": None,
        "l10": None, "l11": 1.0, "l12": None, "l13": None, "l14": None}
# 音のきっかけ（ショット, 秒, 大きさ, 種類）。
# roar＝怪獣の咆哮（本物の動物の声を低く）、cheer＝5 万人の声、spin＝ハンマーを回す風切り、volley＝一斉に飛ぶ風切り、clank＝腰に当たって跳ね返る金属音、
# fire＝炎（低いごう音とパチパチ）、panic＝逃げる人々、run＝丘を駆け上がる足音、inhale＝息を吸う低い音、whistle＝頭へ向かうハンマーの風切り、
# headhit＝頭に当たる（一瞬静か → 金属と重い一撃）、groan＝ふらつくうめき、misfire＝炎が空へそれる、fall＝倒れる地響き、growl＝最後に目が開く低いうなり
HIT = [("l00", .1, 1.0, "roar"), ("l01", .4, .8, "cheer"),
       ("l02", .3, .9, "spin"), ("l02", .7, 1.0, "volley"), ("l03", .55, 1.0, "clank"),
       ("l04", .3, .7, "roar"), ("l04", 1.0, 1.0, "fire"), ("l04", 1.4, .8, "panic"),
       ("l06", .0, .9, "run"), ("l07", .1, 1.0, "inhale"),
       ("l08", .0, 1.0, "spin"), ("l09", .0, 1.0, "whistle"), ("l10", .34, 1.0, "headhit"),
       ("l11", .2, .9, "groan"), ("l11", 1.05, .8, "misfire"), ("l12", 1.8, 1.0, "fall"),
       ("l13", .1, 1.0, "cheer"), ("l14", 1.0, .7, "growl")]


def _load(p):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x / (np.max(np.abs(x)) + 1e-9)


def _pitch(x, k):
    n = int(len(x) / k)
    return np.interp(np.arange(n) * k, np.arange(len(x)), x) if n > 8 else x


def _env(x, a=.01, b=.25):
    n = len(x); x = x.copy(); ia, ib = min(n, int(a * SR)), min(n, int(b * SR))
    x[:ia] *= np.linspace(0, 1, ia); x[n - ib:] *= np.linspace(1, 0, ib); return x


def _ticks():
    x = _load(SFX / "clock.mp3"); env = np.convolve(np.abs(x), np.ones(96) / 96, mode="same")
    th = .35 * env.max(); on, i, out = [], 0, []
    while i < len(env):
        if env[i] > th:
            on.append(i); i += int(.25 * SR)
        else:
            i += 1
    for j in on[:12]:
        a = max(0, j - int(.004 * SR)); out.append(_env(x[a:a + int(.16 * SR)], .002, .06))
    return out


def _rumble(d=5.0, seed=7, fc=140):   # 地鳴りの余韻：ループしない低いノイズ（1 回ずつ。曲に聞こえないように）
    t = np.arange(int(d * SR)) / SR; r = np.random.default_rng(seed)
    x = music._lp(np.cumsum(r.standard_normal(len(t))) * .02, fc); x -= music._lp(x, 20)
    w = music._lp(r.standard_normal(len(t)), 3); wob = 1 + .35 * w / (np.max(np.abs(w)) + 1e-9)
    x = x * wob / (np.max(np.abs(x * wob)) + 1e-9)
    return x * np.minimum(1, t / .08) * np.exp(-t / (d / 3))


def _heavy(d=5.0, f0=55, seed=11, crack=1.0):   # 重い一撃：割れる音＋沈む低音＋分厚い胴＋余韻（pilot_047）
    t = np.arange(int(d * SR)) / SR; r = np.random.default_rng(seed)
    f = f0 * np.exp(-t / 1.2) + 22; sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.6)
    body = music._lp(r.standard_normal(len(t)), 400) * 5 * np.exp(-t / 1.1)
    hi = r.standard_normal(len(t)) - music._lp(r.standard_normal(len(t)), 1500); cr = hi * np.exp(-t / .045) * crack
    x = 1.0 * sub + .7 * body / (np.max(np.abs(body)) + 1e-9) + .8 * cr / (np.max(np.abs(cr)) + 1e-9)
    x = np.tanh(1.8 * x) / np.tanh(1.8)
    return x * np.minimum(1, t / .002)


def _noise_sweep(d, f0, f1, seed=5, shape=1.5):   # 帯域が動く風のノイズ（近づいて遠ざかる）
    t = np.arange(int(d * SR)) / SR; r = np.random.default_rng(seed); x = r.standard_normal(len(t)); k = t / d
    hi = music._lp(x, f0); lo = music._lp(x, f1); y = hi * (1 - k) + lo * k
    return y / (np.max(np.abs(y)) + 1e-9) * np.sin(np.pi * np.clip(k, 0, 1)) ** shape


def _reverb(x, d=2.5, mix=.35, seed=3):   # 大きな空間の響き（減衰するノイズとの畳み込み）
    r = np.random.default_rng(seed); n = int(d * SR); ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / (d / 5)); ir = music._lp(ir, 3000)
    w = np.convolve(x, ir)[:len(x) + n]; w /= np.max(np.abs(w)) + 1e-9; y = np.zeros(len(w)); y[:len(x)] += x * (1 - mix); return y + w * mix


def beds():
    tl = json.loads(TLP.read_text(encoding="utf-8")); cues = tl["cues"]; total = tl["duration"]; n = int(total * SR) + SR
    near, tick = np.zeros(n), np.zeros(n)
    B = {p.stem: _load(p) for p in (SFX / "break").glob("*.mp3")}
    KJ = {p.stem: _load(p) for p in (SFX / "kaiju").glob("*.mp3")}   # 動物の咆哮（Freesound の CC0）
    pick = lambda pre: [v for k, v in B.items() if k.startswith(pre)]
    TK = _ticks(); r = np.random.default_rng(49); duck = np.ones(n)
    crowd = _load(SFX / "crowd.mp3")

    def put(x, t, g, buf=None):
        j = int(t * SR); m = min(len(x), n - j)
        if j < 0:
            x = x[-j:]; j = 0; m = min(len(x), n)
        if m > 0:
            (near if buf is None else buf)[j:j + m] += x[:m] * g

    def hush(t, pre=.35, post=.4, lo=.12):
        a = int((t - pre) * SR); b_ = int(t * SR); c_ = int((t + post) * SR)
        duck[max(0, a):b_] = np.minimum(duck[max(0, a):b_], np.linspace(1, lo, b_ - max(0, a))); duck[b_:c_] = np.minimum(duck[b_:c_], np.linspace(lo, 1, c_ - b_))

    order = [s["id"] for s in SHOTS]
    for i, k in enumerate(order):   # 時計（経過の秒）
        iv = TICK[k]
        if iv is None:
            continue
        a = cues[k]; b = cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]; t, q = a, 0
        while t < b:
            x = TK[q % len(TK)] * (.4 if iv < .3 else .55); j = int(t * SR); m = min(len(x), n - j); tick[j:j + m] += x[:m]; t += iv; q += 1
    roar1 = KJ["611721"][:int(4.0 * SR)]; roar2 = KJ["469123"][:int(5.0 * SR)]; roar3 = KJ["757589"]
    for shot, off, g, kind in HIT:
        t = cues[shot] + off; dur = next(s["dur"] for s in SHOTS if s["id"] == shot)
        if kind == "roar":       # 咆哮：本物の動物の声を低くして、大きな響き
            put(_reverb(_pitch(roar1, .6), 3.0, .4), t, 1.0 * g); put(_reverb(_pitch(roar3, .5), 3.0, .4), t + .1, .6 * g); put(_rumble(3.0, int(t * 7), 90), t, .4 * g)
        elif kind == "cheer":
            put(_env(crowd[int(1 * SR):int(5 * SR)], .4, 1.0), t, .9 * g)
        elif kind == "spin":     # ハンマーを回す：だんだん速くなる風切り
            for j in range(6):
                put(_noise_sweep(.45, 2200, 700, 70 + j, 1.0), t + .55 * j * (1 - .06 * j), .25 * g * (.6 + .1 * j))
        elif kind == "volley":   # 5 万本が飛ぶ：大きな風の塊
            put(_noise_sweep(3.0, 3000, 500, 81, .8), t, .7 * g); put(_rumble(3.0, 82, 160), t, .3 * g)
        elif kind == "clank":    # 腰に当たって跳ね返る金属音（たくさん、小さく）
            for j in range(40):
                put(_pitch(pick("metal_")[r.integers(5)], r.uniform(.7, 1.3)), t + r.uniform(0, 1.2), r.uniform(.08, .2) * g)
        elif kind == "fire":     # 炎：低いごう音＋パチパチ
            d_ = 2.4; tt = np.arange(int(d_ * SR)) / SR; x = music._lp(r.standard_normal(len(tt)), 700) * (1 + .4 * np.sin(2 * np.pi * 7 * tt))
            x = x / (np.max(np.abs(x)) + 1e-9) * np.minimum(1, tt / .15) * np.minimum(1, (d_ - tt) / .6)
            put(_reverb(x, 2.0, .3), t, .9 * g); put(_rumble(3.0, 91, 120), t, .5 * g)
            for j in range(30):
                put(_env(r.standard_normal(int(.02 * SR)), .001, .015), t + r.uniform(0, 2.3), r.uniform(.1, .3) * g)
        elif kind == "panic":
            put(_env(crowd[int(6 * SR):int(10 * SR)], .2, 1.0), t, .8 * g)
        elif kind == "run":      # 4 万人が丘を駆け上がる：地鳴りのような足音（不規則）
            put(_env(crowd[:int(dur * SR)], .3, .8), t, .5 * g); tt = t
            while tt < t + dur:
                put(_rumble(.6, int(tt * 31), 200), tt, .25 * g * r.uniform(.6, 1)); tt += r.uniform(.08, .2)
        elif kind == "inhale":   # 息を吸う：低いノイズが高くなっていく
            put(_noise_sweep(2.6, 300, 1400, 101, .7), t, .8 * g); put(_rumble(2.6, 102, 80), t, .5 * g)
        elif kind == "whistle":  # 4 万本の風切りが近づく
            put(_noise_sweep(2.8, 900, 3500, 111, 1.2), t, .8 * g)
        elif kind == "headhit":  # 頭に当たる：一瞬静か → 金属の大きな音と重い一撃
            hush(t, .4, .5, .08)
            put(_heavy(4.0, 70, 121, 1.0), t, 1.3 * g); put(_pitch(B["explosion_chunky"], .6), t, .8 * g)
            for j in range(25):
                put(_pitch(pick("metal_")[r.integers(5)], r.uniform(.5, .9)), t + r.uniform(0, .25), r.uniform(.2, .45) * g)
        elif kind == "groan":    # ふらつくうめき：咆哮をさらに低く、ゆっくり
            put(_reverb(_pitch(roar2, .45)[:int(2.6 * SR)], 3.0, .45), t, .8 * g)
        elif kind == "misfire":
            put(_noise_sweep(1.6, 600, 2400, 131, .8), t, .6 * g)
        elif kind == "fall":     # 倒れる地響き
            hush(t, .3, .4, .1)
            put(_heavy(6.0, 40, 141, .6), t, 1.4 * g); put(_rumble(6.0, 142, 120), t + .1, .9 * g); put(_pitch(B["quake"], .6)[:int(4 * SR)], t + .1, .6 * g)
        elif kind == "growl":
            put(_reverb(_pitch(roar1, .4)[:int(2.0 * SR)], 2.5, .4), t, .7 * g)
    put(_rumble(2.6, 1, 120), 0, .3)
    return near, tick * duck


def ambience_crowd():
    return _load(SFX / "crowd.mp3")[:int(4 * SR)]


if not getattr(music, "_P049_BEDS", False):
    music._P049_BEDS = True
    _prev = music.sfx_bank_soft

    def sfx_bank_soft():
        b = _prev()
        if TLP.exists():
            b["bed_near"], b["bed_tick"] = beds()
        return b
    music.sfx_bank_soft = sfx_bank_soft

CUES = {"open": ["L00", 0.0]}
POPS = []
for s in SHOTS:
    L = s["id"].upper(); CUES[s["id"]] = [L, 0.0]
    for j, e in enumerate(s.get("ev", [])):
        c = f"ev_{s['id']}_{j}"; CUES[c] = [L, round(e[0] / s["dur"], 4)]; POPS.append(c)
    if s.get("card"):
        c = f"card_{s['id']}"; CUES[c] = [L, round(.15 / s["dur"], 4)]; POPS.append(c)

EP = standard.config({
    "id": "pilot_049",
    "out": "reverse_049_kaiju_hammer.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0], ["bed_tick", "t0", .55, 0], ["crowd", "l00", .25, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_049", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（タイトルの帯つき）。ナレーション・BGM なし。身長 50 m の怪獣と、ハンマー投げの世界記録級の選手 5 万人の対決（丘から頭を狙う、炎 1 回で 1 万人リタイア、ギリギリ勝つ）。",
                   "- 閃光は使わない：衝突は「一瞬音が消える → 低い衝撃 → 地鳴り」と、揺れ・煙・色の変化で見せる。人は逃げる（崩れる街は無人）。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
