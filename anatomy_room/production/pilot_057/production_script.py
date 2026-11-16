#!/usr/bin/env python3
"""pilot_057「犬ぞりで、南極を横断したら？」（もしも設計の既定、土台は pilot_056）の制作スクリプト。

数字は scripts/pilot_057/sim/antarctica.py（antarctica.json、出典と確認方法は fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py、ショットごとに別のプロセスで描く）。
ナレーション・BGM なし。音は合成：地吹雪のごう音（強まったり弱まったり）、そりの滑る音、雪を踏む足音（不規則）、地図の上のやわらかい風、休憩のしずかな風。
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
HIT = [("l00", .0, 1.2, "blizzard"), ("l00", .0, 1.0, "runner"), ("l00", .0, 1.0, "crunch"), ("l01", .0, .9, "high"), ("l01", 2.3, .8, "swish"),
       ("l02", .0, 1.5, "blizzard"), ("l02", .0, .5, "crunch"), ("l03", .0, .7, "blizzard"), ("l03", .0, 1.1, "runner"), ("l03", .0, 1.2, "crunch"),
       ("l04", .0, .6, "blizzard"), ("l04", .0, .8, "runner"), ("l04", .0, 1.0, "crunch"), ("l04", .0, 1.0, "pant"), ("l05", .0, 1.0, "calm"),
       ("l06", .0, .6, "calm"), ("l06", .0, .8, "runner"), ("l06", .0, .9, "crunch"), ("l07", .0, .7, "blizzard"), ("l07", .0, .6, "runner"),
       ("l08", .0, 1.2, "blizzard"), ("l08", .0, 1.0, "runner"), ("l08", .0, 1.0, "crunch")]


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
        if kind == "blizzard":       # 地吹雪：帯域が動く風のノイズ＋低いうなり（強まったり弱まったり）
            put(_noise_sweep(d + .3, 1800, 500, int(t * 3) + 7, .25), t - .1, .55 * g); put(_rumble(d + .3, int(t * 7) + 1, 120), t, .22 * g)
        elif kind == "high":         # 上空：高い所の細い風
            put(_noise_sweep(d + .3, 3000, 1800, int(t * 5) + 3, .5), t - .1, .18 * g)
        elif kind == "swish":        # 地図の線が伸びる：やわらかい風切り（1 回）
            put(_noise_sweep(2.2, 600, 2600, 91, 1.2), t, .3 * g)
        elif kind == "runner":       # そりの滑走：細かい「しゃー」（ゆっくり揺れる）
            am = .7 + .3 * music._lp(r.standard_normal(n_), 2.0) / .03
            x = _hp(music._lp(r.standard_normal(n_), 5000), 1500) * np.clip(am, .3, 1.2); put(_env(x / (np.max(np.abs(x)) + 1e-9), .3, .3), t, .12 * g)
        elif kind == "crunch":       # 10 頭が雪を蹴る音：細かい粒がびっしり重なった「ざー」（1 歩ずつは聞こえない＝リズムにしない）
            tc = t
            while tc < t + d:
                k_ = int(r.uniform(.008, .02) * SR); ck = r.standard_normal(k_) * np.exp(-np.arange(k_) / (k_ / 4))
                put(music._lp(_hp(ck, 1200), 6000), tc, r.uniform(.01, .035) * g); tc += r.exponential(.006)
        elif kind == "pant":         # 白い息：短い息の音（間隔はばらばら）
            for tc in (t + .5, t + 1.9, t + 3.6):                  # 3 回だけ、間隔はそろえない
                k_ = int(r.uniform(.25, .4) * SR); e_ = np.sin(np.linspace(0, np.pi, k_)) ** 2
                put(music._lp(_hp(r.standard_normal(k_), 700), 2500) * e_, tc, r.uniform(.05, .08) * g)
        elif kind == "calm":         # 休憩：しずかな風（遠く）
            put(_noise_sweep(d + .3, 700, 400, int(t * 3) + 5, .2), t - .1, .2 * g)
    return near


if not getattr(music, "_P057_BEDS", False):
    music._P057_BEDS = True
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
    "id": "pilot_057",
    "out": "reverse_057_dogsled.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_057", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（タイトルの帯つき、画面は昼）。ナレーション・BGM なし。犬ぞりで南極を横断したら、を 1989–90 年の国際南極横断隊の記録（約 6,000 km・220 日）で答える。",
                   "- 南極大陸は日本の約 37 倍、気温 −48℃・風 時速 約 160 km、1 日 約 27 km、そり犬は 1 日 約 1 万 kcal。休憩で丸まって眠る犬（癒やし）。今は犬を南極に連れて行けない（1994 年に全頭退去）。閃光なし。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
