#!/usr/bin/env python3
"""pilot_048「東京に体長500mのポメラニアンが現れたら？」（もしも設計の既定、土台は pilot_047）の制作スクリプト。

計算は scripts/pilot_048/sim/（pom.py → pom.json、条件と仮定 fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）。
ナレーションなし（silent_ext）、BGM なし（曲は全区間 f_mute・ending も 0。曲に聞こえる音も入れない）。音は環境音と犬の音だけ：
本物の時計の音・朝の雑踏・本物の犬の音（吠え声・くんくん・ハァハァ・ブルブル。Freesound の CC0）を低くして大きな響きをつけたもの・
足が地面にめり込む重い一撃（pilot_047 の _heavy）・鼻息の突風・ガラス・衝撃波。地鳴りは一撃ごとの余韻だけ（ループしない）。
共通エンディングなし（もしも設計）。最後は暗転して冒頭の座った姿につながる（ループ）。
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
ambience.register("crowd", SFX / "crowd.mp3", start=5, span=("l02", "l04", 0), norm="rms", fade_out=1.0)

# ショットごとの時計の間隔（秒）。早送りは速く。走り終えたら止める
TICK = {"l00": 1.0, "l01": 1.0, "l02": 1.0, "l03": 1.0, "l04": 1.0, "l05": .5, "l06": .5, "l07": .5, "l08": 1.0, "l09": 1.0, "l10": 1.0,
        "l11": 1.0, "l12": .2, "l13": .5, "l14": 1.0, "l15": None, "l16": None}
# 音のきっかけ（ショット, 秒, 大きさ, 種類）。
# deepbark＝低い「ワフッ」（本物の吠え声を低くする）、breath＝ゆっくりの寝息のような息、whoosh＝大きな物が空気を押す音、step＝足が地面にめり込む重い一撃、
# cars＝車が転がる、sniff＝くんくん（本物を低く）、gust＝鼻息の突風、bark＝「ワン」、crowd_panic＝人々が走り出す、walkstep＝歩く足音、
# squish＝うんちが出る重い音、plop＝山が地面に着く、steam＝湯気、stream＝おしっこの水流、flood＝川があふれる、shake＝ブルブル（本物を低く）、
# pant＝ハァハァ（本物を低く）、yip＝遊びの小さな声、boom＝衝撃波（2 連のドーン）、glass＝窓ガラスが一斉に割れる、far＝遠くのドーン、
# tower＝鉄の塔がきしんで倒れる、grunt＝満足のため息
HIT = [("l00", .15, 1.0, "deepbark"), ("l00", .2, .6, "whoosh"),
       ("l01", .2, .8, "breath"),
       ("l02", .3, .8, "whoosh"), ("l02", 1.87, 1.0, "step"), ("l02", 1.95, .8, "cars"),
       ("l03", .1, 1.0, "sniff"), ("l03", 1.87, 1.0, "gust"), ("l03", 2.0, .8, "cars"),
       ("l04", .55, 1.0, "bark"), ("l04", 1.1, .8, "crowd_panic"),
       ("l05", .0, .7, "walkstep"),
       ("l06", .2, .5, "whoosh"), ("l06", 1.4, 1.0, "squish"), ("l06", 2.4, .9, "plop"), ("l06", 2.7, .5, "steam"),
       ("l07", .35, .5, "whoosh"), ("l07", 1.1, 1.0, "stream"), ("l07", 1.6, .8, "flood"),
       ("l08", .15, 1.0, "shake"),
       ("l09", .0, 1.0, "pant"),
       ("l10", .3, .9, "yip"), ("l10", 1.1, .6, "whoosh"), ("l10", 1.9, .8, "yip"),
       ("l11", .35, .8, "step"), ("l11", 1.15, 1.0, "boom"), ("l11", 1.25, 1.0, "glass"),
       ("l12", .1, .7, "far"),
       ("l13", .25, .9, "boom"), ("l13", .85, 1.0, "tower"),
       ("l14", .3, .9, "step"), ("l14", .9, .8, "grunt"), ("l14", 1.2, .7, "pant")]


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
    D = {p.stem.split("_")[0]: _load(p) for p in (SFX / "dog").glob("*.mp3")}   # 本物の犬の音（Freesound の CC0）
    pick = lambda pre: [v for k, v in B.items() if k.startswith(pre)]
    TK = _ticks(); r = np.random.default_rng(48)
    duck = np.ones(n)

    def put(x, t, g, buf=None):
        j = int(t * SR); m = min(len(x), n - j)
        if j < 0:
            x = x[-j:]; j = 0; m = min(len(x), n)
        if m > 0:
            (near if buf is None else buf)[j:j + m] += x[:m] * g

    def hush(t, pre=.35, post=.4, lo=.15):   # 一撃の直前に、ほかの音（時計）を一瞬下げる
        a = int((t - pre) * SR); b_ = int(t * SR); c_ = int((t + post) * SR)
        duck[max(0, a):b_] = np.minimum(duck[max(0, a):b_], np.linspace(1, lo, b_ - max(0, a))); duck[b_:c_] = np.minimum(duck[b_:c_], np.linspace(lo, 1, c_ - b_))

    order = [s["id"] for s in SHOTS]
    for i, k in enumerate(order):   # 時計
        iv = TICK[k]
        if iv is None:
            continue
        a = cues[k]; b = cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]; t, q = a, 0
        while t < b:
            x = TK[q % len(TK)] * (.45 if iv < .3 else .6); j = int(t * SR); m = min(len(x), n - j); tick[j:j + m] += x[:m]; t += iv; q += 1
    bark = D["813120"]; pant = np.concatenate([D["827433"], D["841349"]]); sniff = D["483039"]; shk = D["619251"]
    for shot, off, g, kind in HIT:
        t = cues[shot] + off; dur = next(s["dur"] for s in SHOTS if s["id"] == shot)
        if kind == "deepbark":   # 低い「ワフッ」：本物の小型犬の吠え声を 1/3 の高さに、響きをつけて
            put(_reverb(_pitch(bark, .33), 2.8, .4), t, 1.0 * g); put(_heavy(2.5, 45, 1, .0), t + .02, .45 * g)
        elif kind == "breath":   # ゆっくりの息（ハァハァを低く遅く）
            put(_env(_pitch(pant[:int(2.5 * SR)], .35), .4, 1.2), t, .55 * g); put(_noise_sweep(3.0, 900, 300, 31, 1.0), t + .4, .25 * g)
        elif kind == "whoosh":
            put(_noise_sweep(1.6, 1400, 220, int(t * 9), 1.3), t, .55 * g); put(_rumble(1.8, int(t * 9) + 1, 80), t, .35 * g)
        elif kind == "step":     # 足が地面にめり込む：重い一撃＋割れる地面＋余韻
            hush(t); put(_heavy(5.0, 55, int(t * 7), .6), t, 1.2 * g); put(_pitch(B["explosion_chunky"], .6), t + .02, .7 * g)
            put(_pitch(B["quake"], .6)[:int(3 * SR)], t + .08, .45 * g); put(_rumble(4.5, int(t * 7) + 3), t + .1, .6 * g)
            for j in range(5):
                put(_pitch(pick("break_")[r.integers(3)], r.uniform(.5, .8)), t + .25 + .2 * j, .3 * g)
        elif kind == "cars":
            for j in range(8):
                put(pick("metal_")[r.integers(5)], t + r.uniform(0, 1.3), .4 * g); put(pick("hit_")[r.integers(7)], t + r.uniform(0, 1.3), .3 * g)
        elif kind == "sniff":    # くんくん：本物を低く
            put(_reverb(_pitch(sniff[int(.2 * SR):int(2.6 * SR)], .45), 1.8, .3), t, .9 * g)
        elif kind == "gust":     # 鼻息の突風
            put(_noise_sweep(2.6, 2200, 300, 77, .7), t, .9 * g); put(_rumble(2.5, 78, 120), t, .6 * g); put(_reverb(_pitch(sniff[int(1.0 * SR):int(1.6 * SR)], .3), 2.0, .4), t, .7 * g)
        elif kind == "bark":     # 「ワン」：低く大きく。窓が震える音
            hush(t, .3, .2, .1)
            put(_reverb(_pitch(bark, .38), 3.5, .45), t, 1.0 * g); put(_heavy(3.0, 60, 4, .0), t, .4 * g)
            for j in range(6):
                put(pick("glass_")[r.integers(6)], t + .15 + r.uniform(0, .6), .18 * g)
        elif kind == "crowd_panic":
            put(_env(ambience_crowd(), .3, .8), t, .55 * g)
        elif kind == "walkstep":   # 歩く足音：0.55 秒ごとに重い足音（不規則に少しずらす）
            tt = t
            while tt < t + dur:
                put(_heavy(2.0, 50, int(tt * 13), .25), tt, .5 * g * r.uniform(.8, 1.0)); put(_rumble(1.6, int(tt * 13) + 1, 100), tt + .05, .3 * g); tt += .55 + r.uniform(-.05, .05)
        elif kind == "squish":   # うんちが出る：低い湿った音（ノイズを低く、ゆっくり揺らす）
            d_ = 1.4; tt = np.arange(int(d_ * SR)) / SR; x = music._lp(r.standard_normal(len(tt)), 260) * (1 + .6 * np.sin(2 * np.pi * 5 * tt))
            x = x / (np.max(np.abs(x)) + 1e-9) * np.sin(np.pi * tt / d_) ** .7; put(_reverb(x, 1.5, .3), t, .8 * g)
        elif kind == "plop":
            hush(t, .2, .3, .3); put(_heavy(3.0, 40, 21, .1), t, 1.0 * g); put(_pitch(pick("splash_")[0], .4), t, .6 * g)
        elif kind == "steam":
            tt = np.arange(int(2.4 * SR)) / SR; x = r.standard_normal(len(tt)) - music._lp(r.standard_normal(len(tt)), 1800)
            put(x / (np.max(np.abs(x)) + 1e-9) * np.minimum(1, tt / .4) * np.minimum(1, (2.4 - tt) / .8), t, .2 * g)
        elif kind == "stream":   # 水の流れ（大きな滝のような音）
            d_ = 2.2; tt = np.arange(int(d_ * SR)) / SR; x = music._lp(r.standard_normal(len(tt)), 1200) - music._lp(r.standard_normal(len(tt)), 150)
            put(x / (np.max(np.abs(x)) + 1e-9) * np.minimum(1, tt / .2) * np.minimum(1, (d_ - tt) / .5), t, .7 * g)
        elif kind == "flood":
            for j in range(3):
                put(_pitch(pick("splash_")[j % 2], .5), t + .4 * j, .5 * g)
            put(_rumble(2.5, 61, 300), t, .4 * g)
        elif kind == "shake":    # ブルブル：本物（犬が体を振る）を低く
            put(_reverb(_pitch(shk[:int(3.0 * SR)], .5), 1.5, .25), t, 1.0 * g)
            for j in range(4):
                put(_noise_sweep(.7, 1600, 400, 90 + j, 1.0), t + .25 + .3 * j, .35 * g)
        elif kind == "pant":     # ハァハァ：本物を低く
            put(_reverb(_pitch(pant[:int(2.2 * SR)], .55), 1.2, .2), t, .9 * g)
        elif kind == "yip":      # 遊びの声：吠え声を少し低く短く
            put(_reverb(_pitch(bark, .55), 1.5, .3), t, .7 * g)
        elif kind == "boom":     # 衝撃波：2 連のドーン（N 波）
            hush(t, .3, .3, .1); put(_heavy(3.5, 70, int(t * 5), 1.0), t, 1.3 * g); put(_heavy(3.5, 60, int(t * 5) + 1, .8), t + .12, 1.0 * g)
        elif kind == "glass":    # 窓ガラスが一斉に割れる
            put(B["glass_big"], t, .9 * g)
            for j in range(22):
                put(pick("glass_")[r.integers(6)], t + r.uniform(0, 2.2), r.uniform(.25, .55) * g)
        elif kind == "far":      # 遠くのドーン（不規則に）
            tt = t
            while tt < t + dur:
                put(_heavy(2.5, 45, int(tt * 17), .3), tt, .35 * g * r.uniform(.6, 1.0)); tt += r.uniform(.35, .8)
        elif kind == "tower":    # 鉄の塔がきしんで倒れる
            for j in range(5):
                put(_pitch(pick("metal_")[r.integers(5)], r.uniform(.3, .5)), t + .15 * j, .6 * g)
            put(_heavy(4.0, 50, 13, .7), t + 1.0, 1.0 * g); put(_pitch(B["crash"], .5), t + 1.0, .7 * g)
        elif kind == "grunt":    # 満足のため息（ハァハァの 1 回を低く長く）
            put(_env(_pitch(pant[int(.1 * SR):int(.7 * SR)], .3), .1, .6), t, .7 * g)
    put(_rumble(2.6, 1, 120), 0, .3)
    return near, tick * duck


def ambience_crowd():
    return _load(SFX / "crowd.mp3")[:int(4 * SR)]


if not getattr(music, "_P048_BEDS", False):
    music._P048_BEDS = True
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
    "id": "pilot_048",
    "out": "reverse_048_pomeranian.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0], ["bed_tick", "t0", .55, 0], ["crowd", "l02", .35, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_048", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（pilot_045 v2.3＋タイトルの帯）。ナレーション・BGM なし。体長 500 m のポメラニアンの一日（肉球・鼻息・吠え声・散歩・うんち・マーキング・ブルブル・ハァハァ・ハッスルタイム）。",
                   "- 閃光は使わない：衝突は「一瞬音が消える → 低い衝撃 → 地鳴り」と、揺れ・煙・色の変化で見せる。人は逃げる（崩れる街は無人）。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
