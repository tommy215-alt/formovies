#!/usr/bin/env python3
"""pilot_053「日本の観測史上最大の記録が、東京で同時に起きたら？」（もしも設計の既定、土台は pilot_052）の制作スクリプト。

計算は scripts/pilot_053/sim/disaster.py（disaster.json、記録と仮定は fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）、l02 の図は renderer.html。
ナレーション・BGM なし。音は環境音と効果音だけ（合成と、OpenGameArt の CC0 の木の割れる音）：真夏の風・雪がとける水音・激しい雨・暴風・
地震の地鳴り（重く、1 回）・家がきしむ音・湖になった街の水音。一定の間隔でくり返す音は使わない。閃光なし。共通エンディングなし。
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
HIT = [("l00", .0, .7, "rain"), ("l00", .0, .5, "wind"), ("l01", .0, .6, "rain"), ("l01", .0, .5, "wind"),   # v2（2026-11-13）：交差点の雨と風
       ("l02", .0, .8, "rain"), ("l02", .0, .5, "wind"), ("l03", .0, .6, "wind"), ("l03", .0, .5, "rain"),
       ("l04", .0, 1.0, "storm"), ("l04", .0, .9, "wind"), ("l04", 2.2, .8, "creak"),          # 東京タワーと暴風、看板がきしむ
       ("l05", .0, 1.1, "rain"), ("l05", .0, .8, "drip"),                                      # 熱い雨で雪がとける
       ("l06", .0, .7, "storm"), ("l06", .3, 1.0, "quake"),
       ("l07", .0, .5, "drip"), ("l07", .0, .8, "lap"), ("l08", .0, .7, "lap"), ("l08", .0, .4, "wind"), ("l09", .0, .5, "wind"),
       ("l10", .0, .6, "rain"), ("l10", .0, .4, "wind")]


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
        if kind == "wind":
            put(_noise_sweep(d + .4, 1200, 500, int(t * 3) + 7, .5), t - .15, .3 * g)
        elif kind == "drip":         # 雪がとける水音：細かいしずく（不規則）
            for j in range(int(d * 30)):
                tt = np.arange(int(.05 * SR)) / SR; f0 = r.uniform(900, 2200); x = np.sin(2 * np.pi * f0 * tt * (1 + 2 * tt)) * np.exp(-tt / .012)
                put(x, t + r.uniform(0, d), r.uniform(.02, .07) * g)
        elif kind == "rain":         # 激しい雨：広い帯域のノイズ（ゆっくり揺れる）
            x = r.standard_normal(int((d + .5) * SR)); x = music._lp(x, 6000) - music._lp(x, 300); wob = 1 + .25 * music._lp(r.standard_normal(len(x)), 1.5) / .05
            x = _env(x * np.clip(wob, .5, 1.5) / (np.max(np.abs(x)) + 1e-9), .4, .5); put(x, t - .2, .45 * g)
        elif kind == "storm":        # 暴風：低いうなりが強まったり弱まったり（不規則）
            put(_noise_sweep(d + .3, 500, 180, int(t * 5) + 3, .3), t - .1, .7 * g); put(_rumble(d + .3, int(t * 9), 120), t, .4 * g)
        elif kind == "quake":        # 震度 7：重い地鳴り（1 回）＋建物のきしみ・割れる音
            put(_heavy(4.5, 34, 531, .3), t, .9 * g); put(_rumble(4.5, 532, 70), t, 1.0 * g)
            for j in range(10):
                put(_pitch(B[["break_01", "break_02", "break_03"][j % 3]], r.uniform(.5, .8)), t + .4 + r.uniform(0, 3.0), r.uniform(.08, .2) * g)
        elif kind == "creak":        # 家がきしんで、つぶれる（1 回）
            put(_pitch(B["break_02"], .45), t, .5 * g); put(_heavy(2.5, 40, 541, .2), t + .2, .6 * g)
        elif kind == "lap":          # 湖になった街：ちゃぷちゃぷ（不規則）
            for j in range(int(d * 4)):
                put(_env(music._lp(r.standard_normal(int(.3 * SR)), 700), .05, .2), t + r.uniform(0, d), r.uniform(.05, .12) * g)
    return near


if not getattr(music, "_P053_BEDS", False):
    music._P053_BEDS = True
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
    "id": "pilot_053",
    "out": "reverse_053_records_tokyo.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_053", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（タイトルの帯つき、画面は昼）。ナレーション・BGM なし。気象庁の観測史上 1 位（41.8℃・積雪 11.82 m・雨 153 mm/h・風 72.5 m/s・震度 7）を東京で同時に。",
                   "- v2（2026-11-13 ユーザーの直し）：渋谷のスクランブル交差点と東京タワー。人と車、傘・旗・案内板（気温 41.8℃・雨量 153 mm/h）。人は驚いて逃げ、けが・犠牲は描かない。暑さで雪が約 24 時間でとけ、雨と合わせて街に水深 約 4.5 m（屋上で手を振る人、ボート）。閃光・点滅なし。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
