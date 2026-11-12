#!/usr/bin/env python3
"""pilot_051「猫 何匹で、新幹線は動く？」（もしも設計の既定、土台は pilot_050）の制作スクリプト。

計算は scripts/pilot_051/sim/cats.py（cats.json、条件と仮定 fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）、l08 の図は renderer.html。
ナレーションなし（silent_ext）、BGM なし。音は環境音と効果音だけ：猫の鳴き声とゴロゴロ（Freesound の CC0、assets/sfx/cat/）・綱が張る音・
車輪のきしみ（合成）・風。ゴロゴロは長さと音程を変えて重ね、一定の間隔でくり返す音にしない。共通エンディングなし。
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
HIT = [("l00", .0, .5, "wind"), ("l00", .3, .9, "meow"), ("l01", .2, .7, "strain"), ("l01", 2.4, .8, "meow"),
       ("l02", .0, .5, "wind"), ("l02", .4, .8, "chorus"), ("l02", 1.4, .7, "yawn"),
       ("l03", .0, .5, "wind"), ("l03", .3, 1.0, "chorus_big"), ("l03", 3.3, 1.0, "creak"),
       ("l04", .0, .5, "wind"), ("l04", .0, .7, "roll"), ("l04", 1.8, .6, "meow"),
       ("l05", .0, .4, "wind"), ("l05", .2, .8, "purr"), ("l05", 3.0, .5, "kitten"),
       ("l06", .0, .6, "wind"), ("l06", .5, 1.0, "chorus_big"), ("l06", 3.5, 1.0, "chorus_big"),
       ("l07", .0, .35, "wind"), ("l07", .0, 1.0, "purr"), ("l07", 2.4, .4, "kitten"),
       ("l08", .0, .4, "wind"), ("l09", .0, .5, "wind"), ("l09", .2, .9, "chorus"), ("l10", .0, .5, "wind"), ("l10", .5, .7, "meow")]


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
    near = np.zeros(n); r = np.random.default_rng(51)
    C = {p.stem: _load(p) for p in (SFX / "cat").glob("*.mp3")}
    meows = [C[k] for k in ("110011", "412017", "436541")]; kitten = C["196251"]; purrs = [C["260881"], C["130968"]]
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
        if kind == "wind":           # 田園の風（帯域がゆっくり動く）
            put(_noise_sweep(d + .4, 1400, 500, int(t * 3) + 7, .5), t - .15, .35 * g)
        elif kind == "meow":
            put(_env(_pitch(meows[int(r.integers(0, 3))], r.uniform(.95, 1.08)), .005, .15), t, .55 * g)
        elif kind == "kitten":
            put(_env(kitten[:int(1.6 * SR)], .01, .3), t, .4 * g)
        elif kind in ("chorus", "chorus_big"):   # 猫の合唱：鳴き声を音程・時刻をずらして重ねる（くり返しにならないよう不規則に）
            m = 18 if kind == "chorus" else 60; span = min(d, 3.5)
            for j in range(m):
                put(_env(_pitch(meows[int(r.integers(0, 3))], r.uniform(.85, 1.25)), .005, .12), t + r.uniform(0, span), r.uniform(.05, .16) * g * (1 if kind == "chorus" else .8))
        elif kind == "yawn":
            put(_env(_pitch(meows[0], .8), .05, .3), t, .3 * g)
        elif kind == "purr":         # ゴロゴロ：2 つの録音を、長さ・音程を変えて重ねる（一定の間隔にしない）
            for j, p_ in enumerate(purrs):
                a0 = int(r.uniform(0, max(1, len(p_) / SR - d - 1)) * SR); x = _pitch(p_[a0:a0 + int((d + 1) * SR * 1.1)], r.uniform(.94, 1.05))
                put(_env(x, .6, .8), t, (.55 if j == 0 else .35) * g)
        elif kind == "strain":       # 綱が張る：低いきしみ
            put(_noise_sweep(.8, 300, 900, int(t * 5), 1.2), t, .3 * g)
        elif kind == "creak":        # 車輪が回りはじめる：金属のきしみ（低く、1 回）＋重いうなり
            put(_pitch(B["metal_02"], .45), t, .5 * g); put(_rumble(2.4, int(t * 7), 80), t, .5 * g)
        elif kind == "roll":         # ゆっくり転がる車輪の低い音（くり返しにならないノイズ）
            put(_rumble(d, 61, 90), t, .35 * g)
    return near


if not getattr(music, "_P051_BEDS", False):
    music._P051_BEDS = True
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
    "id": "pilot_051",
    "out": "reverse_051_cats_shinkansen.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_051", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（タイトルの帯つき、画面はお昼のように明るく）。ナレーション・BGM なし。猫が綱で新幹線を引く：約 1,100 匹で動き、2,200 匹で時速 2.4 km、坂は 3.7 万匹。",
                   "- 動物の回なので休憩と昼寝の場面で癒やす。CG は Poly Haven（CC0）の素材と、区画にまとめた草・砕石、ジオメトリノードの群れ（1 本 3〜4 時間）。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
