#!/usr/bin/env python3
"""pilot_050「ティラノサウルスがマラソン大会に出たら、優勝できる？」（もしも設計の既定、土台は pilot_049）の制作スクリプト。

計算は scripts/pilot_050/sim/race.py（race.json、条件と仮定 fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）。
ナレーションなし（silent_ext）、BGM なし（曲に聞こえる音も入れない）。音は環境音と効果音だけ：
沿道のざわめきと歓声（Freesound の CC0 の雑踏）・号砲・重い一歩（1 ショットに 2 歩まで、一定の間隔にしない）・警告の音・風・水・湯気・息。
共通エンディングなし（もしも設計）。最後は次の大会のスタートラインで、冒頭につながる（ループ）。
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
HIT = [("l00", .0, .55, "murmur"), ("l01", .0, 1.0, "gun"), ("l01", .2, 1.0, "cheer"), ("l01", 2.2, .7, "stomp"), ("l01", 3.5, .8, "stomp"),
       ("l02", .0, .45, "murmur"), ("l02", 1.15, .9, "alarm"), ("l02", 3.8, .8, "stomp"),
       ("l03", .0, .6, "wind"), ("l03", .0, .5, "pack"), ("l03", .9, .45, "breath"), ("l03", 3.3, .5, "breath"),
       ("l04", .0, .8, "wind"), ("l04", .2, .3, "murmur"),
       ("l05", .0, .5, "murmur"), ("l05", 2.95, 1.0, "bite"), ("l05", 3.4, 1.0, "splash"), ("l05", 3.9, .6, "steam"),
       ("l06", .0, .55, "murmur"), ("l06", 3.05, 1.0, "cheer_big"),
       ("l07", 1.05, .8, "stomp"), ("l07", 2.3, .9, "stomp"), ("l07", 2.7, 1.0, "cheer_big"), ("l07", 3.5, .8, "pant"),
       ("l08", .0, .9, "heat"), ("l08", .6, .45, "steam"), ("l08", 3.5, 1.0, "slump"), ("l08", 4.7, .9, "sigh"),
       ("l09", .0, .9, "cheer"), ("l10", .0, .55, "murmur")]


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
    tl = json.loads(TLP.read_text(encoding="utf-8")); cues = tl["cues"]; total = tl["duration"]; n = int(total * SR) + SR
    near = np.zeros(n)
    B = {p.stem: _load(p) for p in (SFX / "break").glob("*.mp3")}
    r = np.random.default_rng(50)
    crowd = _load(SFX / "crowd.mp3")

    def put(x, t, g):
        j = int(t * SR); m = min(len(x), n - j)
        if j < 0:
            x = x[-j:]; j = 0; m = min(len(x), n)
        if m > 0:
            near[j:j + m] += x[:m] * g

    def walla(d, off, pitch=1.0):   # 雑踏（CC0）をショットの長さだけ。ショットごとに違うところから
        x = _pitch(crowd, pitch); a = int(off * SR) % max(1, len(x) - int(d * SR) - 1); return _env(x[a:a + int(d * SR)], .25, .35)

    def cheer(d, seed, big=1.0):    # 歓声：雑踏を重ね、明るい帯域のふくらみ（不規則に揺れる）
        t = np.arange(int(d * SR)) / SR; x = walla(d, 3 + seed * 2.3, 1.12)[:len(t)]; x2 = walla(d, 11 + seed * 1.7, .94)[:len(t)]
        x = np.pad(x, (0, len(t) - len(x))) + .8 * np.pad(x2, (0, len(t) - len(x2)))
        sw = music._lp(r.standard_normal(len(t)), 2.5); sw = 1 + .3 * sw / (np.max(np.abs(sw)) + 1e-9)
        roar = music._lp(_hp(r.standard_normal(len(t)), 500), 2500); roar = roar / (np.max(np.abs(roar)) + 1e-9)
        return (x / (np.max(np.abs(x)) + 1e-9) + .45 * big * roar) * sw * np.minimum(1, t / .25) * np.minimum(1, (d - t) / .9)

    order = [s["id"] for s in SHOTS]
    for shot, off, g, kind in HIT:
        t = cues[shot] + off; i = order.index(shot); d = (cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]) - t
        if kind == "murmur":         # 沿道のざわめき（ショットの終わりまで、前後と少し重ねる）
            put(walla(d + .4, 2 + i * 2.7), t - .15, .6 * g)
        elif kind == "gun":          # 号砲：乾いた破裂音＋街の反響
            put(_reverb(_heavy(1.6, 140, 201, 1.4), 2.2, .45), t, .9 * g)
        elif kind == "cheer":
            put(cheer(d + .3, i), t, .9 * g)
        elif kind == "cheer_big":    # 大歓声：大きな歓声＋手の音（ばらばらの短いノイズ）
            put(cheer(d + .3, i + 7, 1.6), t, 1.1 * g)
            for j in range(160):
                put(_env(_hp(r.standard_normal(int(.012 * SR)), 1200), .001, .008), t + r.uniform(0, d), r.uniform(.03, .09) * g)
        elif kind == "stomp":        # 重い一歩：低い衝撃と地面の響き（1 回ずつ）
            put(_heavy(2.2, 42, int(t * 13), .25), t, .9 * g); put(_rumble(1.6, int(t * 7), 90), t, .4 * g)
        elif kind == "alarm":        # 警告：下がる 2 音（1 回だけ）
            tt = np.arange(int(.9 * SR)) / SR; f = np.where(tt < .45, 880, 660); ph = 2 * np.pi * np.cumsum(f) / SR
            x = np.sign(np.sin(ph)) * .35 + np.sin(ph) * .6
            x = music._lp(x, 3000) * ((tt % .45) < .38) * np.minimum(1, (tt % .45) / .01); put(_reverb(x, 1.2, .2), t, .45 * g)
        elif kind == "wind":         # 風（帯域がゆっくり動く）
            put(_noise_sweep(d + .3, 1800, 500, int(t * 3), .5), t - .1, .5 * g)
        elif kind == "pack":         # 集団の足音のざわめき（くり返しにならない細かいノイズ）
            for j in range(int(d * 40)):
                put(_env(music._lp(r.standard_normal(int(.03 * SR)), 900), .002, .02), t + r.uniform(0, d), r.uniform(.03, .08) * g)
        elif kind == "breath":       # 荒い息（ランナー、不規則に 2 回）
            for dt in (0, r.uniform(.5, .7)):
                put(_noise_sweep(.42, 2600, 900, int((t + dt) * 9), 1.4), t + dt, .35 * g)
        elif kind == "bite":         # くわえる：硬い音（バケツ）
            put(_pitch(B["metal_01"], .8), t, .5 * g); put(_pitch(B["hit_05"], .7), t, .6 * g)
        elif kind == "splash":       # 水がこぼれる：水っぽいノイズ（帯域の揺れ）＋しぶき
            dd = 2.2; tt = np.arange(int(dd * SR)) / SR; x = r.standard_normal(len(tt)); x = music._lp(x, 2200) - music._lp(x, 300)
            wob = np.abs(music._lp(r.standard_normal(len(tt)), 18)); x = x * wob / (np.max(np.abs(x * wob)) + 1e-9) * np.minimum(1, tt / .05) * np.exp(-tt / .9)
            put(x, t, .8 * g)
            for j in range(70):
                put(_env(_hp(r.standard_normal(int(.02 * SR)), 2500), .001, .015), t + r.uniform(0, 1.6), r.uniform(.05, .15) * g)
        elif kind == "steam":        # 湯気：高い息のようなノイズ
            dd = min(d, 3.0); x = _hp(music._lp(r.standard_normal(int(dd * SR)), 7000), 2500); put(_env(x / (np.max(np.abs(x)) + 1e-9), .6, 1.0) * .4, t, g)
        elif kind == "pant":         # ティラノの荒い息：低いノイズの吸う・吐く（間隔をばらつかせる）
            tt = t
            for j in range(3):
                put(_noise_sweep(.55, 700, 250, int(tt * 5), 1.2), tt, .5 * g); put(_rumble(.6, int(tt * 3), 70), tt, .25 * g); tt += r.uniform(.6, .85)
        elif kind == "heat":         # 夏の熱い風（低く、ゆっくり）＋遠いざわめき
            put(_noise_sweep(d + .3, 900, 400, 401, .4), t - .1, .5 * g); put(walla(d, 21, .9), t, .25 * g)
        elif kind == "slump":        # 座りこむ：重い沈む音
            put(_heavy(3.0, 34, 411, .15), t, 1.0 * g); put(_rumble(3.0, 412, 70), t + .1, .6 * g)
        elif kind == "sigh":         # 長い息
            put(_noise_sweep(1.8, 600, 220, 421, 1.0), t, .6 * g); put(_rumble(1.8, 422, 60), t, .3 * g)
    return near


if not getattr(music, "_P050_BEDS", False):
    music._P050_BEDS = True
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
    "id": "pilot_050",
    "out": "reverse_050_trex_marathon.mp4",
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
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（タイトルの帯つき、050 から画面はお昼のように明るく）。ナレーション・BGM なし。ティラノサウルスが早歩き（時速 19 km）で 42.195 km を歩き通す。",
                   "- 優勝（世界記録のペース）には届かないが 3.7 万人中 33 位。気温 30℃なら 17.7 km で体温が限界になってリタイア。足音は 1 ショット 2 歩まで、くり返す音は使わない。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
