#!/usr/bin/env python3
"""pilot_047「毎日2倍になる隕石。地球は何日もつ？」（もしも設計の既定、参考 pilot_045・046）の制作スクリプト。

計算は scripts/pilot_047/sim/（days.json、条件と仮定 fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）。
ナレーションなし（silent_ext）、BGM なし（曲は全区間 f_mute・ending も 0）。音は環境音だけ：
本物の時計の音（毎日の正午に向けて刻む、早送りの所は速く）・広場の雑踏（避難が始まるまで）・隕石が空を切る音・
爆発と衝突は「一瞬音が消える → 低い衝撃 → 地鳴り」（閃光は使わない分、音で）・窓ガラス・崩れるビル、宇宙は低い衝撃、
地鳴りは 11 日目（初めて地面に届く）から最後に向けて大きく。地球が砕けたあとは無音。
共通エンディングなし（もしも設計）。最後は暗転して冒頭の岩につながる（ループ）。
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
ambience.register("crowd", SFX / "crowd.mp3", start=5, span=("l01", "l05", 0), norm="rms", fade_out=1.2)

# ショットごとの時計の間隔（秒）。正午を待つ所はふつう、早送りは速く。地球が砕けたら止める
TICK = {"l00": 1.0, "l01": 1.0, "l02": .125, "l03": .5, "l04": .25, "l05": .5, "l06": .5, "l07": .25, "l08": .5, "l09": .5, "l10": .5,
        "l11": .25, "l12": .25, "l13": .25, "l14": .125, "l15": .5, "l16": None}
# 落ちる・爆発する瞬間（ショット, 秒, 大きさ, 種類）。種類 streak＝空を切る音、air＝空中の爆発（遠いドーン）、glass、collapse＝ビルが崩れる、
# impact＝地面に衝突（直前に一瞬静かに）、tiles＝瓦が飛ぶ、space＝宇宙（低い衝撃）、shatter＝地球が砕ける
HIT = [("l01", 1.6, .25, "streak"), ("l02", .45, .3, "streak"), ("l02", 1.05, .4, "streak"), ("l02", 1.65, .55, "streak"), ("l02", 2.25, .7, "streak"),
       ("l03", .5, .7, "streak"), ("l03", .7, .6, "air"),
       ("l04", .2, .5, "air"), ("l04", 1.1, .9, "air"), ("l04", 1.3, 1.0, "glass"),
       ("l05", .6, .9, "streak"), ("l05", .8, 1.0, "air"), ("l05", 1.6, 1.0, "collapse"), ("l05", 2.2, .8, "collapse"),
       ("l06", .55, 1.0, "streak"), ("l06", .8, 1.0, "impact"), ("l07", .5, .9, "impact"), ("l07", 1.7, 1.0, "impact"),
       ("l08", .8, 1.0, "impact"), ("l09", .6, 1.0, "impact"), ("l09", .9, .9, "tiles"), ("l10", .4, 1.0, "impact"),
       ("l11", .5, .9, "space"), ("l11", 1.9, 1.0, "space"), ("l12", 1.2, 1.0, "space"), ("l13", 1.2, 1.0, "space"), ("l13", 1.4, .6, "steam"),
       ("l14", .9, .9, "space"), ("l14", 2.2, 1.0, "space"), ("l15", 2.4, 1.0, "shatter")]
# 地鳴り（ショットの頭での大きさ、間は直線）：初めて地面に届く 11 日目から大きく、地球が砕けたら止める
QUAKE = {"l00": .5, "l01": 0, "l05": 0, "l06": .3, "l08": .6, "l10": .8, "l11": .6, "l13": .8, "l15": 1.0, "l16": 0}


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


def _boom(d=2.5, f0=48, seed=3):   # 低い衝撃
    t = np.arange(int(d * SR)) / SR; r = np.random.default_rng(seed)
    x = np.sin(2 * np.pi * (f0 * (1 - .4 * t / d)) * t) * np.exp(-t / .7) + .6 * music._lp(r.standard_normal(len(t)), 220) * 6 * np.exp(-t / .9)
    return x / (np.max(np.abs(x)) + 1e-9) * np.minimum(1, t / .005)


def _streak(d=1.1, seed=5):   # 空を切る音：帯域を下げていく風切りのノイズ（近づいて遠ざかる）
    t = np.arange(int(d * SR)) / SR; r = np.random.default_rng(seed); x = r.standard_normal(len(t))
    hi = music._lp(x, 2400); lo = music._lp(x, 500); k = t / d
    y = hi * (1 - k) + lo * k
    env = np.sin(np.pi * np.clip(k, 0, 1)) ** 1.5
    return y / (np.max(np.abs(y)) + 1e-9) * env


def _steam(d=2.2, seed=9):   # 湯気：高いシューという音
    t = np.arange(int(d * SR)) / SR; r = np.random.default_rng(seed); x = r.standard_normal(len(t)) - music._lp(r.standard_normal(len(t)), 1800)
    return x / (np.max(np.abs(x)) + 1e-9) * np.minimum(1, t / .4) * np.minimum(1, (d - t) / .8)


def beds():
    tl = json.loads(TLP.read_text(encoding="utf-8")); cues = tl["cues"]; total = tl["duration"]; n = int(total * SR) + SR
    near, tick = np.zeros(n), np.zeros(n)
    B = {p.stem: _load(p) for p in (SFX / "break").glob("*.mp3")}
    pick = lambda pre: [v for k, v in B.items() if k.startswith(pre)]
    TK = _ticks(); r = np.random.default_rng(47)
    duck = np.ones(n)   # 衝突の直前に、ほかの音を一瞬下げる（「音が消える」）

    def put(x, t, g, buf=None):
        j = int(t * SR); m = min(len(x), n - j)
        if m > 0:
            (near if buf is None else buf)[j:j + m] += x[:m] * g

    order = [s["id"] for s in SHOTS]
    for i, k in enumerate(order):   # 時計
        iv = TICK[k]
        if iv is None:
            continue
        a = cues[k]; b = cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]; t, q = a, 0
        while t < b:
            x = TK[q % len(TK)] * (.5 if iv < .3 else .7); j = int(t * SR); m = min(len(x), n - j); tick[j:j + m] += x[:m]; t += iv; q += 1
    for shot, off, g, kind in HIT:
        t = cues[shot] + off
        if kind == "streak":
            put(_streak(1.1, int(t * 10)), t - .8, .55 * g)
        elif kind == "air":   # 空中の爆発：遠いドーン（低く、少し遅れて重なる）
            put(_boom(2.6, 40, int(t)), t, .9 * g); put(_pitch(B["explosion_dull"], .55), t + .12, .7 * g)
        elif kind == "glass":
            put(B["glass_big"], t, g)
            for j in range(5):
                put(pick("glass_")[r.integers(6)], t + .12 + .17 * j, .5 * g)
        elif kind == "collapse":   # ビルが崩れる：割れる音を重ね、低い爆発
            put(B["explosion_chunky"], t, .8 * g); put(_boom(3.0, 42, int(t)), t, .9 * g)
            for j in range(5):
                put(_pitch(pick("break_")[r.integers(3)], r.uniform(.55, .85)), t + .1 + .2 * j, .6 * g); put(pick("metal_")[r.integers(5)], t + .25 + .25 * j, .35 * g)
        elif kind == "impact":   # 地面に衝突：直前 0.35 秒は静かに → いちばん低い衝撃
            a = int((t - .4) * SR); b_ = int(t * SR); duck[max(0, a):b_] = np.minimum(duck[max(0, a):b_], np.linspace(1, .12, b_ - max(0, a)))
            c_ = int((t + .5) * SR); duck[b_:c_] = np.minimum(duck[b_:c_], np.linspace(.12, 1, c_ - b_))
            put(_boom(3.5, 34, int(t)), t, 1.1 * g); put(B["explosion_chunky"], t + .02, .7 * g); put(_pitch(B["quake"], .6)[:int(3 * SR)], t + .1, .5 * g)
        elif kind == "tiles":   # 瓦と木が飛ぶ
            for j in range(6):
                put(_pitch(pick("wood_")[r.integers(3)], r.uniform(.8, 1.2)), t + .12 * j, .5 * g); put(pick("hit_")[r.integers(7)], t + .05 + .14 * j, .4 * g)
        elif kind == "space":   # 宇宙：音のない世界だが、演出として低い衝撃だけ
            put(_boom(3.5, 30, int(t)), t, g); put(_pitch(B["explosion_dull"], .5), t, .6 * g)
        elif kind == "steam":
            put(_steam(2.4, int(t)), t, .25 * g)
        elif kind == "shatter":   # 地球が砕ける：いちばん大きな低音と崩れる音 → そのあとは無音
            a = int((t - .6) * SR); b_ = int(t * SR); duck[max(0, a):b_] = np.minimum(duck[max(0, a):b_], np.linspace(1, .05, b_ - max(0, a)))
            put(_boom(4.5, 24, 99), t, 1.3 * g); put(_boom(4.0, 38, 98), t + .15, .8 * g); put(B["explosion_chunky"], t, .8 * g)
            for j in range(6):
                put(_pitch(pick("break_")[r.integers(3)], r.uniform(.4, .6)), t + .1 + .25 * j, .6 * g)
    # 地鳴り：低く唸る音
    qk = _load(SFX / "break" / "quake.mp3"); qk = np.tile(_pitch(qk, .7), n // len(qk) + 2)[:n]; qk = music._lp(qk, 500)
    ks = [k for k in order if k in QUAKE]; ts = [cues[k] for k in ks] + [total]; vs = [QUAKE[k] for k in ks] + [0]
    near += qk / (np.sqrt(np.mean(qk ** 2)) + 1e-9) * .09 * np.interp(np.arange(n) / SR, ts, vs) * duck
    # 地球が砕けたあと（l16）は、余韻の低音だけを残して静かに
    end_a = int((cues["l15"] + 2.4) * SR)
    tick[end_a:] = 0
    return near, tick * duck


if not getattr(music, "_P047_BEDS", False):
    music._P047_BEDS = True
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
    "id": "pilot_047",
    "out": "reverse_047_meteor.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0], ["bed_tick", "t0", .55, 0], ["crowd", "l01", .35, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_047", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（pilot_045 v2.3）。ナレーション・BGM なし。毎日の正午に向けて時計が刻み、隕石が毎日 2 倍になる。",
                   "- 閃光は使わない：衝突は「一瞬音が消える → 低い衝撃 → 地鳴り」と、揺れ・煙・色の変化で見せる。人は逃げる（崩れる街は無人）。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
