#!/usr/bin/env python3
"""pilot_056「頭の小さなプロペラで、空を飛んだら？」（もしも設計の既定、土台は pilot_055）の制作スクリプト。

計算は scripts/pilot_056/sim/rotor.py（rotor.json、出典と仮定は fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py、ショットごとに別のプロセスで描く）。
ナレーション・BGM なし。音は合成：プロペラの高いうなり（途切れない）、吹き下ろす風のごう音、砂が当たる音、土管が転がる音、回る体の風切り音（だんだん速く）。
一定の間隔でくり返す音は使わない。閃光なし。共通エンディングなし。
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

# 時計の音は使わない（2026-11-10 ユーザー「裏でドラムの音が鳴ってる。もしも設計から完全に消して」：一定の間隔の音がドラムに聞こえた）
# 音のきっかけ（ショット, 秒, 大きさ, 種類）。リズムになる音（一定の間隔でくり返す音）は使わない。足音は 1 ショットに 2 歩まで
HIT = [("l00", .0, 1.0, "rotor"), ("l00", .0, 1.0, "gale"), ("l01", .0, .8, "rotor"), ("l01", .0, .6, "gale"),
       ("l02", .0, .9, "rotor"), ("l02", .0, 1.2, "gale"), ("l02", .0, .8, "grit"), ("l03", .0, .8, "rotor"), ("l03", .0, 1.0, "gale"), ("l03", .6, 1.0, "roll"),
       ("l04", .0, .8, "rotor"), ("l04", .0, .7, "gale"), ("l05", .0, .9, "rotor"), ("l05", .0, .7, "gale"), ("l05", .6, 1.0, "spin"),
       ("l06", .0, 1.0, "rotor"), ("l06", .0, .8, "gale"), ("l06", .0, 1.2, "spin_fast"), ("l07", .0, .6, "rotor"), ("l07", .0, .5, "gale"), ("l07", .0, .8, "spin_fast"),
       ("l08", .0, 1.0, "rotor"), ("l08", .0, 1.0, "gale")]


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


def _hp(x, fc):
    return x - music._lp(x, fc)


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
    tl = json.loads(TLP.read_text(encoding="utf-8")); cues = tl["cues"]; n = int(tl["duration"] * SR) + SR
    near = np.zeros(n); r = np.random.default_rng(53)
    B = {p.stem: _load(p) for p in (SFX / "break").glob("*.mp3")}

    def put(x, t, g):
        j = int(t * SR); m = min(len(x), n - j)
        if j < 0:
            x = x[-j:]; j = 0; m = min(len(x), n)
        if m > 0:
            near[j:j + m] += x[:m] * g

    order = [s["id"] for s in SHOTS]
    for shot, off, g, kind in HIT:
        t = cues[shot] + off; i = order.index(shot); d = (cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]) - t
        n_ = int((d + .3) * SR); tt = np.arange(n_) / SR
        if kind == "rotor":          # プロペラ：高いうなり（ゆっくり揺れる、途切れない）
            f0 = 310 + 6 * music._lp(r.standard_normal(n_), 1.0) / .02; ph = np.cumsum(f0) / SR
            x = np.sin(2 * np.pi * ph) + .5 * np.sin(4 * np.pi * ph) + .25 * np.sin(6 * np.pi * ph); x += .5 * _hp(r.standard_normal(n_), 3000)
            put(_env(x / np.max(np.abs(x)), .15, .15), t - .1, .16 * g)
        elif kind == "gale":         # 吹き下ろす風のごう音（強まったり弱まったり）
            put(_noise_sweep(d + .3, 1600, 600, int(t * 3) + 7, .2), t - .1, .5 * g); put(_rumble(d + .3, int(t * 7) + 1, 110), t, .25 * g)
        elif kind == "grit":         # 砂・小石が当たる（不規則なぱらぱら）
            tc = t
            while tc < t + d:
                k_ = int(.006 * SR); ck = r.standard_normal(k_) * np.exp(-np.arange(k_) / (k_ / 5)); put(_hp(ck, 2500), tc, r.uniform(.03, .1) * g); tc += r.exponential(.02)
        elif kind == "roll":         # 土管が転がって落ちる（低いごろごろ＋どすん）
            put(_rumble(3.0, 777, 90), t, .7 * g); put(_heavy(2.0, 50, 778, .3), t + 1.8, .6 * g)
        elif kind in ("spin", "spin_fast"):   # 回る体の風切り音（回るほど高く速く）
            k0 = .3 if kind == "spin" else .8; k = np.clip(k0 + (1 - k0) * tt / max(d, .1), 0, 1); f = 2 + 20 * k
            am = .5 + .5 * np.sin(2 * np.pi * np.cumsum(f) / SR); x = music._lp(r.standard_normal(n_), 1500) * am
            put(_env(x / (np.max(np.abs(x)) + 1e-9), .3, .3), t, .35 * g)
    return near


if not getattr(music, "_P056_BEDS", False):
    music._P056_BEDS = True
    _prev = music.sfx_bank_soft

    def sfx_bank_soft():
        b = _prev()
        if TLP.exists():
            b["bed_near"] = beds()
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
    "id": "pilot_056",
    "out": "reverse_056_head_propeller.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_056", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（タイトルの帯つき、画面は昼）。ナレーション・BGM なし。アニメでおなじみの頭のプロペラで空を飛ぶのを、運動量理論で計算（作品名・キャラクター・道具の名前は出さない）。",
                   "- 体重 35 kg・直径 20 cm：足もとの風 時速 約 490 km（猛烈な台風の 2.5 倍）、約 64 馬力（軽自動車 1 台分）、反動で体が逆に回る（1 秒後に毎秒 7 回転）。けがは描かない。閃光なし。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
