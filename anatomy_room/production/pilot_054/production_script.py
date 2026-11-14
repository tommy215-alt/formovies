#!/usr/bin/env python3
"""pilot_054「全人類 82 億人が、渋谷のスクランブル交差点に集まったら？」（新もしも設計、templates/DESIGN_MODES.md）の制作スクリプト。

計算は scripts/pilot_054/sim/crowd.py（crowd.json）。ショット・セリフ・ポップアップは plan.py。3D は Blender（blender/scene.py）、地図は renderer.html。
声：冒頭の問いと最後の答えは W 冥鳴ひまり、途中は M 阿井田 茂 Calm（lines.json）。BGM なし。
音：0 秒目に重い一撃と群衆のどよめき、人の中では群衆のざわめき（Freesound CC0）、上がる・広がるところは風の音。一定の間隔でくり返す音は使わない。閃光なし。共通エンディングなし。
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
noend_ext.apply(pipeline, black=0.0)
import silent_ext  # noqa: E402
silent_ext.apply(pipeline)                 # 最後のループの画（L08）だけ無音
import ambience  # noqa: E402
import music  # noqa: E402
from music import SR  # noqa: E402

PLAN = json.loads((HERE / "blender" / "plan.json").read_text(encoding="utf-8"))
SHOTS = PLAN["shots"]
TLP = HERE / "work" / "timeline.json"
SFX = HERE / "assets" / "sfx"
ambience.timeline(TLP)
ambience.click("click", 2600, gain=.7)   # ポップアップが出る音

# 音のきっかけ（ショット, 秒, 大きさ, 種類）。一定の間隔でくり返す音は使わない
HIT = [("l00", .0, 1.0, "impact"), ("l00", .0, 1.0, "crowd"), ("l00", 1.2, .6, "rise"),
       ("l01", .0, 1.3, "crowd"), ("l02", .0, .8, "crowd"),
       ("l03", .0, .7, "crowd"), ("l03", .0, .9, "rise"),
       ("l04", .0, .7, "spread"), ("l05", .0, .4, "spread"), ("l06", .0, 1.1, "spread"), ("l06", .0, .5, "crowd"),
       ("l07", .0, .9, "impact"), ("l08", .0, 1.0, "crowd")]


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
    CR = _load(SFX / "crowd.mp3")
    for shot, off, g, kind in HIT:
        t = cues[shot] + off; i = order.index(shot); d = (cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]) - t
        if kind == "crowd":          # 大勢のざわめき（Freesound CC0、毎回ちがう場所から切り出す）
            k0 = int(r.uniform(0, max(1, len(CR) - (d + .6) * SR))); x = CR[k0:k0 + int((d + .6) * SR)]
            put(_env(x, .25, .35), t - .15, .55 * g)
        elif kind == "impact":       # 重い一撃（0 秒目と答え）
            put(_heavy(3.0, 48, 551 + int(t), .5), t, .8 * g)
        elif kind == "rise":         # カメラが上がる風
            put(_noise_sweep(d + .3, 400, 2400, int(t * 7) + 5, .8), t, .35 * g)
        elif kind == "spread":       # 人の塗りが広がる：低いうねり
            put(_noise_sweep(d + .4, 300, 900, int(t * 11) + 9, .6), t, .4 * g); put(_rumble(d + .4, int(t * 13), 90), t, .25 * g)
    return near


if not getattr(music, "_P054_BEDS", False):
    music._P054_BEDS = True
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
    CUES[s["id"]] = [s["id"].upper(), 0.0]
    POPS += [[s["id"], e[0]] for e in s.get("ev", [])] + ([[s["id"], .15]] if s.get("card") else [])

EP = standard.config({
    "id": "pilot_054",
    "out": "reverse_054_humanity_shibuya.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0]] + [["click", c, .7, off] for c, off in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_054", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js", "assets/map/map.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 終わり（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- 新もしも設計（2026-11-15〜）：0 秒目に人でぎっしりの交差点、冒頭で問いを声で読み「どこまで埋まると思う？」と予想させる、答えは最後、冒頭の画にループ。",
                   "- 1 m² に 2 人で、陸の上だけを交差点から近い順に埋める。渋谷区 3,022 万人 → 日本人全員 61 km²（山手線の内側くらい）→ 82 億人で半径 約 40 km（東京都の 1.86 倍）。",
                   "- 人は簡易のピクトグラム。押しつぶし・けがは描かない（安全に立てる密度）。閃光・点滅なし。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
