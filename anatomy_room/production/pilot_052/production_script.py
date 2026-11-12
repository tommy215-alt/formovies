#!/usr/bin/env python3
"""pilot_052「ハムスターの回し車で、東京の電気をまかなうには何匹？」（もしも設計の既定、土台は pilot_051）の制作スクリプト。

計算は scripts/pilot_052/sim/hamster.py（hamster.json、条件と仮定 fact_check.md）。ショットとポップアップは plan.py。3D は Blender（blender/scene.py）、l08 の図は renderer.html。
ナレーション・BGM なし。音は環境音と効果音だけ：回し車のカラカラ（間隔を不規則にして一定のリズムにしない）・豆電球がつく音・風・
町と東京のざわめき（Freesound の CC0 の雑踏）・新幹線の通過音（合成）・寝息。共通エンディングなし。
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
HIT = [("l00", .0, .45, "wind"), ("l00", .0, .9, "wheel"), ("l01", .0, .4, "wind"), ("l01", .0, 1.0, "wheel"),
       ("l02", .0, .4, "wind"), ("l02", .0, 1.3, "wheel"), ("l02", 2.3, 1.0, "bulb"),
       ("l03", .0, .6, "wind"), ("l03", .5, .8, "wheel_far"),
       ("l04", .0, .35, "wind"), ("l04", .2, .8, "sleep"), ("l04", 3.0, .8, "wheel"),
       ("l05", .0, .6, "wind"), ("l05", .5, 1.0, "wheel_far"),
       ("l06", .0, .4, "wind"), ("l06", .2, 1.0, "train"),
       ("l07", .0, .6, "city"), ("l07", .5, 1.1, "wheel_far"),
       ("l08", .0, .35, "wind"), ("l09", .0, .6, "city"), ("l09", .0, .7, "wheel_far"), ("l10", .0, .45, "wind"), ("l10", .0, .9, "wheel")]


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
    near = np.zeros(n); r = np.random.default_rng(52)
    B = {p.stem: _load(p) for p in (SFX / "break").glob("*.mp3")}; crowd = _load(SFX / "crowd.mp3")

    def put(x, t, g):
        j = int(t * SR); m = min(len(x), n - j)
        if j < 0:
            x = x[-j:]; j = 0; m = min(len(x), n)
        if m > 0:
            near[j:j + m] += x[:m] * g

    def click(f0, dur=.012):     # 針金の横棒が鳴る小さな音（高い金属の響き）
        tt = np.arange(int(dur * 4 * SR)) / SR; x = np.sin(2 * np.pi * f0 * tt) * np.exp(-tt / dur) + .3 * _hp(r.standard_normal(len(tt)), 3000) * np.exp(-tt / (dur / 3))
        return x

    order = [s["id"] for s in SHOTS]
    for shot, off, g, kind in HIT:
        t = cues[shot] + off; i = order.index(shot); d = (cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]) - t
        if kind == "wind":
            put(_noise_sweep(d + .4, 1400, 500, int(t * 3) + 7, .5), t - .15, .3 * g)
        elif kind == "wheel":        # 回し車：小さな金属音を不規則な間隔で（平均 1 秒に 9 回、ゆらぎ 35%）＋軸のこすれ
            tt = t
            while tt < t + d:
                put(click(r.uniform(2400, 3600)), tt, r.uniform(.05, .12) * g); tt += 1 / 9 * r.uniform(.65, 1.35)
            put(_env(music._lp(_hp(r.standard_normal(int(d * SR)), 800), 2500), .2, .3) * .04, t, g)
        elif kind == "wheel_far":    # たくさんの回し車：細かい金属音のざわめき（重なってリズムが消える）
            for j in range(int(d * 220)):
                put(click(r.uniform(2000, 4200), .008), t + r.uniform(0, d), r.uniform(.01, .03) * g)
        elif kind == "bulb":         # 豆電球がつく：小さな「ぽっ」と、かすかなうなり
            put(_env(np.sin(2 * np.pi * 880 * np.arange(int(.25 * SR)) / SR) * np.exp(-np.arange(int(.25 * SR)) / SR / .06), .002, .1), t, .25 * g)
        elif kind == "sleep":        # 寝息（不規則に）
            tt = t
            while tt < t + 2.6:
                put(_noise_sweep(.9, 900, 400, int(tt * 13), 1.2), tt, .12 * g); tt += r.uniform(1.0, 1.4)
        elif kind == "city":         # 東京のざわめき
            a0 = int(r.uniform(0, 20) * SR); put(_env(crowd[a0:a0 + int((d + .3) * SR)], .3, .4), t - .1, .5 * g)
        elif kind == "train":        # 新幹線の通過：近づいて遠ざかる風の音
            put(_noise_sweep(min(d, 3.6), 600, 3000, 777, .8), t, .8 * g); put(_rumble(min(d, 3.6), 778, 90), t, .4 * g)
    return near


if not getattr(music, "_P052_BEDS", False):
    music._P052_BEDS = True
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
    "id": "pilot_052",
    "out": "reverse_052_hamster_power.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0]] + [["click", c, .7, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_052", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": ["open"] + [s["id"] for s in SHOTS[1:]],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針", "", "- もしも設計の既定（タイトルの帯つき、画面は昼）。ナレーション・BGM なし。回し車 1 匹 0.19 W：豆電球 4 匹、家 1 万匹、町 4,000 万匹、東京 約 1,950 億匹（四国くらいの広さ）。",
                   "- 動物の回なので休憩・昼寝で癒やす。ハムスターと古民家は Sketchfab（CC BY）、空・草は Poly Haven（CC0）、回し車は自作。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
