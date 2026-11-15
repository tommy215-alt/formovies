#!/usr/bin/env python3
"""pilot_055「10万ボルトの電撃が、現実にあったら？」（もしも設計の既定、土台は pilot_053）の制作スクリプト。

計算は scripts/pilot_055/sim/spark.py（spark.json、出典は fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）、電圧の比べっこ（l04）は renderer.html。
ナレーション・BGM なし。音は合成：電気のパチパチ（不規則）・ためるときのうなり・小さな「パチッ」・大きな電撃の雷鳴、外の風。一定の間隔でくり返す音は使わない。閃光なし。共通エンディングなし。
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
HIT = [("l00", .0, .6, "crackle"), ("l00", .0, .35, "wind"),
       ("l01", .0, 1.0, "charge"), ("l02", .0, .5, "charge_end"), ("l02", 1.0, .9, "pichi"), ("l02", .0, .3, "wind"),
       ("l03", .0, .5, "crackle"), ("l03", .0, .3, "wind"),
       ("l04", .6, .25, "pichi"), ("l04", 1.6, .45, "pichi"), ("l04", 2.6, .7, "zap"), ("l04", 3.6, .9, "zap"), ("l04", 4.6, 1.0, "thunder"),
       ("l05", .0, .4, "crackle"), ("l05b", .0, .8, "charge_end"), ("l05b", .8, 1.0, "thunder"), ("l05b", .8, .6, "zap"),
       ("l06", .0, .3, "wind"), ("l06", .0, .3, "crackle"), ("l06", 3.4, 1.0, "pichi"),
       ("l07", .0, .35, "wind"), ("l08", .0, .5, "crackle"), ("l08", .0, .35, "wind")]


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

    def click(f0=3000, d=.004):   # 火花の 1 つ（高い音の短いはじけ）
        tt = np.arange(int(d * SR)) / SR; x = r.standard_normal(len(tt)) * np.exp(-tt / (d / 4)); return _hp(x, f0)

    for shot, off, g, kind in HIT:
        t = cues[shot] + off; i = order.index(shot); d = (cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]) - t
        if kind == "wind":
            put(_noise_sweep(d + .4, 900, 400, int(t * 3) + 7, .5), t - .15, .18 * g)
        elif kind == "crackle":      # パチパチ（不規則な間隔）
            tt = t
            while tt < t + d:
                put(click(r.uniform(2000, 5000), r.uniform(.002, .008)), tt, r.uniform(.05, .18) * g); tt += r.exponential(.07)
        elif kind == "charge":       # ためる：低いうなりが少しずつ高く強く＋パチパチが増える
            n_ = int((d + .2) * SR); tt = np.arange(n_) / SR; k = np.clip(tt / d, 0, 1)
            f = 70 + 160 * k ** 1.5; hum = np.sin(2 * np.pi * np.cumsum(f) / SR) + .4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
            put(_env(hum * (.2 + .8 * k), .2, .2), t, .25 * g)
            tc = t
            while tc < t + d:
                kk = (tc - t) / d; put(click(r.uniform(2500, 6000), r.uniform(.002, .01)), tc, r.uniform(.08, .25) * g * (.3 + kk)); tc += r.exponential(.12 - .09 * kk)
        elif kind == "charge_end":   # うなりの続き（撃つ直前まで）
            n_ = int(1.0 * SR); tt = np.arange(n_) / SR; hum = np.sin(2 * np.pi * 230 * tt) + .4 * np.sin(4 * np.pi * 230 * tt)
            put(_env(hum, .01, .05), t, .25 * g)
        elif kind == "pichi":        # 小さな「パチッ」
            put(click(1800, .012), t, .9 * g); put(click(4000, .005), t + .01, .5 * g)
        elif kind == "zap":          # 中くらいの放電：ジジッ
            for k_ in range(int(8 + 10 * g)):
                put(click(r.uniform(1500, 4000), r.uniform(.004, .012)), t + k_ * r.uniform(.006, .014), r.uniform(.3, .6) * g)
        elif kind == "thunder":      # 雷鳴：割れる音と低い余韻（1 回）
            put(_heavy(3.0, 60, 571 + int(t), 1.0), t, .7 * g); put(_rumble(3.5, 572 + int(t), 120), t + .05, .6 * g)
    return near


if not getattr(music, "_P055_BEDS", False):
    music._P055_BEDS = True
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
    "id": "pilot_055",
    "out": "reverse_055_100kv.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_055", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（タイトルの帯つき、画面は昼）。ナレーション・BGM なし。アニメの「10万ボルトの電撃」を、電圧の数字として現実の物理で確かめる（作品名・キャラクター・技の絵は出さない）。",
                   "- 空気は 1 cm に 約 3 万ボルトで火花が飛ぶ → 10 万ボルトで届くのは 約 3 cm。5 m 先に当てるには 約 1,500 万ボルト。的は木の人形、けがは描かない。閃光・点滅なし。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
