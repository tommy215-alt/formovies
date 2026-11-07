#!/usr/bin/env python3
"""pilot_046「全人類の体重が1日10%ずつ増えたら？」（もしも設計の既定、参考 pilot_045）の制作スクリプト。

計算は scripts/pilot_046/sim/（結果 results.md、条件と仮定 fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）。
ナレーションなし（silent_ext）、BGM なし（曲は全区間 f_mute・ending も 0）。音は環境音だけ：
本物の時計の音（早送りの所は速く）・朝の雑踏・体重計の電子音・きしみ、壊れる所は割れる音・ぶつかる音・低い爆発を重ねて派手に（ユーザーの指示）、後半は地鳴り。
共通エンディングなし（もしも設計）。最後は朝の体重計に戻る（ループ）。
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
ambience.register("crowd", SFX / "crowd.mp3", start=5, span=("l02", "l06", 0), norm="rms", fade_out=1.5)

# ショットごとの時計の間隔（秒）。最初の 2 日はゆっくり、早送りは速く
TICK = {"l00": 1.0, "l01": 1.0, "l02": .5, "l03": .5, "l04": .5, "l05": .25, "l06": .125, "l07": .5, "l08": 1.0, "l09": .5, "l10": .5,
        "l11": .125, "l12": 1.0, "l13": .25, "l14": .125, "l15": .125, "l16": .125, "l17": 1.0}
# 壊れる瞬間（ショット, 秒, 大きさ, 種類）。種類 wood＝木、glass＝ガラス、metal＝金属、big＝コンクリート・建物（爆発の低音を重ねる）、space＝宇宙（低い衝撃）
CRASH = [("l03", 1.5, .5, "splash"), ("l05", 1.0, .35, "creak"), ("l05", 2.0, .35, "creak"), ("l07", 1.1, .7, "ground"), ("l08", 1.0, 1.0, "big"), ("l08", 1.6, .7, "metal"),
         ("l08", 2.4, .6, "glass"), ("l09", 1.1, 1.0, "wood"), ("l09", 1.5, .6, "big"), ("l10", 1.9, 1.0, "metal"), ("l10", 2.0, .8, "glass"), ("l11", .5, .5, "ground"),
         ("l12", 1.1, 1.0, "big"), ("l12", 1.8, .9, "big"), ("l12", 2.5, 1.0, "big"), ("l12", 3.2, .8, "glass"), ("l13", 1.5, .9, "ground"),
         ("l15", 1.3, 1.0, "space"), ("l16", 1.0, 1.0, "space"), ("l16", 2.0, .8, "space")]
# 地鳴り（ショットの頭での大きさ、間は直線）：コンクリートが砕けるころから大きく、宇宙は低い唸り
QUAKE = {"l00": 0, "l10": 0, "l11": .25, "l12": .7, "l13": 1.0, "l14": .5, "l15": .7, "l16": 1.0, "l17": 0}


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


def _beep(f=2400, d=.09):
    t = np.arange(int(d * SR)) / SR; return np.sin(2 * np.pi * f * t) * np.minimum(1, t / .003) * np.minimum(1, (d - t) / .01) * .6


def _buzzer(d=1.6):   # エレベーターの重量超過のブザー（合成）
    t = np.arange(int(d * SR)) / SR; x = np.sign(np.sin(2 * np.pi * 440 * t)) * .25 + np.sin(2 * np.pi * 880 * t) * .15
    return x * (np.sin(2 * np.pi * 2.5 * t) > 0) * np.minimum(1, t / .01) * np.minimum(1, (d - t) / .05)


def _boom(d=2.5, f0=48, seed=3):   # 低い衝撃（建物・宇宙）
    t = np.arange(int(d * SR)) / SR; r = np.random.default_rng(seed)
    x = np.sin(2 * np.pi * (f0 * (1 - .4 * t / d)) * t) * np.exp(-t / .7) + .6 * music._lp(r.standard_normal(len(t)), 220) * 6 * np.exp(-t / .9)
    return x / (np.max(np.abs(x)) + 1e-9) * np.minimum(1, t / .005)


def beds():
    tl = json.loads(TLP.read_text(encoding="utf-8")); cues = tl["cues"]; total = tl["duration"]; n = int(total * SR) + SR
    near, tick = np.zeros(n), np.zeros(n)
    B = {p.stem: _load(p) for p in (SFX / "break").glob("*.mp3")}
    pick = lambda pre: [v for k, v in B.items() if k.startswith(pre)]
    TK = _ticks(); r = np.random.default_rng(46)
    def put(x, t, g):
        j = int(t * SR); m = min(len(x), n - j)
        if m > 0:
            near[j:j + m] += x[:m] * g
    order = [s["id"] for s in SHOTS]
    for i, k in enumerate(order):   # 時計
        a = cues[k]; b = cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]; iv = TICK[k]; t, q = a, 0
        while t < b:
            x = TK[q % len(TK)] * (.5 if iv < .3 else .7); j = int(t * SR); m = min(len(x), n - j); tick[j:j + m] += x[:m]; t += iv; q += 1
    # 体重計の電子音（冒頭と最後）、エレベーターのブザー
    for c, off in (("l00", .4), ("l00", .55), ("l17", .4), ("l17", .55)):
        put(_beep(), cues[c] + off, .5)
    put(_buzzer(), cues["l04"] + 1.0, .5)
    for shot, off, g, kind in CRASH:
        t = cues[shot] + off
        if kind == "splash":
            put(B["splash_01"], t, .8 * g); put(_pitch(B["splash_02"], .8), t + .3, .6 * g)
        elif kind == "creak":
            put(_pitch(B[f"wood_0{r.integers(1, 4)}"], .6), t, g)
        elif kind == "ground":   # 地面が沈む：鈍い衝撃と崩れる音
            put(_boom(1.5, 70), t, .7 * g); put(_pitch(pick("break_")[r.integers(3)], .7), t + .05, .7 * g)
        elif kind == "wood":
            for j, w in enumerate(pick("wood_")):
                put(_pitch(w, .75 + .1 * j), t + .06 * j, g)
            put(_pitch(B["slam_01"], .7), t + .15, .8 * g); put(_boom(1.8, 60), t, .6 * g)
        elif kind == "glass":
            put(B["glass_big"], t, g); put(pick("glass_")[r.integers(6)], t + .2, .6 * g)
        elif kind == "metal":
            put(B["crash"], t, g); put(pick("metal_")[r.integers(5)], t + .1, .8 * g); put(pick("hit_")[r.integers(7)], t + .25, .6 * g)
        elif kind == "big":   # コンクリート・建物：割れる音を重ね、低い爆発
            put(B["explosion_chunky"], t, .9 * g); put(_boom(3.0, 42, int(t)), t, g)
            for j in range(4):
                put(_pitch(pick("break_")[r.integers(3)], r.uniform(.6, .9)), t + .1 + .18 * j, .7 * g); put(pick("hit_")[r.integers(7)], t + .2 + .22 * j, .5 * g)
        elif kind == "space":   # 宇宙：音のない世界だが、演出として低い衝撃だけ
            put(_boom(3.5, 32, int(t)), t, g); put(_pitch(B["explosion_dull"], .6), t, .6 * g)
    # 地鳴り：低く唸る音を、後半に向けて大きく
    qk = _load(SFX / "break" / "quake.mp3"); qk = np.tile(_pitch(qk, .7), n // len(qk) + 2)[:n]; qk = music._lp(qk, 500)
    ks = [k for k in order if k in QUAKE]; ts = [cues[k] for k in ks] + [total]; vs = [QUAKE[k] for k in ks] + [0]
    near += qk / (np.sqrt(np.mean(qk ** 2)) + 1e-9) * .08 * np.interp(np.arange(n) / SR, ts, vs)
    return near, tick


if not getattr(music, "_P046_BEDS", False):
    music._P046_BEDS = True
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
    "id": "pilot_046",
    "out": "reverse_046_weight.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0], ["bed_tick", "t0", .55, 0], ["crowd", "l02", .35, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_046", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（pilot_045 v2.3）。背景と色調は明るい日常（ユーザーの指示）。",
                   "- 最初の 2 日はゆっくり、壊れる段階は時計をほぼ止めてスロー。壊れる音は派手に。宇宙は現象と日付だけ。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
