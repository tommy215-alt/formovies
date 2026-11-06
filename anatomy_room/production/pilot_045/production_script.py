#!/usr/bin/env python3
"""pilot_045「もしも東京にゾンビが一体現れたら？」（チャンネル「リバース」もしも設計）の制作スクリプト。v2（2026-11-06）。

条件はユーザーが決め、Claude が計算した（scripts/pilot_045/sim/、結果 sim/results.md、仮定 fact_check.md）。
v2（ユーザーの指示）：ナレーションなし（silent_ext、行は音声のない区切り）・情報はポップアップ・BGM なし。
音は環境音だけ：時計の音（合成、早送りの所は速く）・雑踏（はじめ）・悲鳴とゾンビのうめき声（だんだん増える）。
ショットの長さとポップアップは plan.py（lines.json・assets/plan.js・blender/plan.json を作る）。3D は Blender（blender/scene.py）。
共通エンディングなし（もしも設計）。最後は最初の一体に戻る（ループ）。
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("Cyborg Ninja.mp3", 160))   # 曲は全区間 f_mute（BGM なし）
import noend_ext  # noqa: E402
noend_ext.apply(pipeline, black=1.0)   # もしも設計は共通エンディングなし。最後は短く暗転して冒頭へ（ループ）
import silent_ext  # noqa: E402
silent_ext.apply(pipeline)
import ambience  # noqa: E402
import music  # noqa: E402
from music import SR  # noqa: E402

PLAN = json.loads((HERE / "blender" / "plan.json").read_text(encoding="utf-8"))
SHOTS = PLAN["shots"]
TLP = HERE / "work" / "timeline.json"
ambience.timeline(TLP)
ambience.click("click", 2600, gain=.8)   # ポップアップが出る音
ambience.register("crowd", HERE / "assets/sfx/crowd.mp3", start=5, span=("l00", "l06", 0), norm="rms", fade_out=2.5)
ambience.register("crowd_end", HERE / "assets/sfx/crowd.mp3", start=40, span=("l18", "end", 0), norm="rms", fade_in=.6)
ambience.register("radio", HERE / "assets/sfx/radio.mp3", start=3, dur=3.5, norm="rms")
ambience.register("heli", HERE / "assets/sfx/helicopter.mp3", start=2, dur=4.5, norm="rms")
ambience.register("heart", HERE / "assets/sfx/heartbeat.mp3", start=0, dur=4, norm="rms")

# ---------------------------------------------------------------- 悲鳴・うめき声・時計（ショットごとの密度で散らす）
SFX = HERE / "assets" / "sfx"
GROANS = sorted((SFX / "groan").glob("grunt_*.mp3")) + sorted((SFX / "groan").glob("undead_*.mp3"))
SCREAMS = sorted((SFX / "scream").glob("*.mp3"))
# ショットごと：[悲鳴/秒, うめき/秒, 遠さ（0＝近い・1＝遠い地図）, 時計の間隔（秒）]。だんだん増える（ユーザー「徐々に悲鳴やうめき声を増やす」）
DENS = {"l00": [0, .5, 0, .5], "l01": [0, .9, 0, .5], "l02": [0, 1.0, 0, .5], "l03": [1.0, 1.6, 0, .5], "l04": [1.6, 2.2, .2, .25],
        "l05": [2.0, 2.6, .5, .5], "l06": [2.2, 3.0, .1, .5], "l07": [2.6, 3.4, .6, .25], "l08": [2.4, 3.6, .3, .25], "l09": [3.0, 4.0, .9, .125],
        "l10": [2.6, 4.4, .3, .25], "l11": [2.0, 5.0, .2, .5], "l12": [3.2, 5.2, .9, .125], "l13": [3.6, 5.6, .9, .25], "l14": [3.4, 6.0, .5, .25],
        "l15": [4.0, 6.4, .95, .125], "l16": [4.4, 6.8, .95, .125], "l17": [4.6, 7.2, 1.0, .125], "l18": [0, 0, 0, .5]}


def _load(p):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x / (np.max(np.abs(x)) + 1e-9)


def _pitch(x, k):   # 再生の速さを変えて音程を変える（k>1 で高く）
    n = int(len(x) / k)
    return np.interp(np.arange(n) * k, np.arange(len(x)), x) if n > 8 else x


def _env(x, a=.01, b=.25):
    n = len(x); x = x.copy(); ia, ib = min(n, int(a * SR)), min(n, int(b * SR))
    x[:ia] *= np.linspace(0, 1, ia); x[n - ib:] *= np.linspace(1, 0, ib); return x


def _tick(hi):
    n = int(.05 * SR); t = np.arange(n) / SR; r = np.random.default_rng(3)
    nz = r.standard_normal(n); nz = nz - music._lp(nz, 1800)
    f = 3400 if hi else 2700
    x = .55 * nz * np.exp(-t / .0012) + np.sin(2 * np.pi * f * t) * np.exp(-t / .004) + .35 * np.sin(2 * np.pi * f * .5 * t) * np.exp(-t / .007)
    return x / np.max(np.abs(x))


def beds():
    tl = json.loads(TLP.read_text(encoding="utf-8")); cues = tl["cues"]; total = tl["duration"]; n = int(total * SR) + SR
    near, far, tick = np.zeros(n), np.zeros(n), np.zeros(n)
    G = [_load(p) for p in GROANS]; Sc = [_load(p) for p in SCREAMS]
    r = np.random.default_rng(45)
    order = [s["id"] for s in SHOTS]
    for i, k in enumerate(order):
        a = cues[k]; b = cues[order[i + 1]] if i + 1 < len(order) else tl["ending_start"]
        rs, rg, dist, iv = DENS[k]
        for rate, src, gain, kind in ((rs, Sc, .55, "s"), (rg, G, .5, "g")):
            if rate <= 0:
                continue
            t = a + r.exponential(1 / rate)
            while t < b:
                x = src[r.integers(len(src))]
                if kind == "s":   # 悲鳴：長い素材は一部を切り出す。音程を変えて別の人に（低め＝男性）
                    L = int(r.uniform(.5, 1.6) * SR); s0 = r.integers(0, max(1, len(x) - L)); x = _pitch(x[s0:s0 + L], r.uniform(.72, 1.18))
                else:   # うめき：ジタバタの間抜けさ。少し高め・低めに散らす
                    x = _pitch(x, r.uniform(.8, 1.3))
                x = _env(x) * gain * r.uniform(.45, 1.0)
                j = int(t * SR); m = min(len(x), n - j)
                if m > 0:
                    if r.random() < dist:
                        far[j:j + m] += x[:m] * .8
                    else:
                        near[j:j + m] += x[:m]
                t += r.exponential(1 / rate)
        # 時計：チッ・チッ（早送りの所は速く）
        t, hi = a, True
        while t < b:
            j = int(t * SR); x = _tick(hi) * (.5 if iv < .3 else .65); m = min(len(x), n - j); tick[j:j + m] += x[:m]; t += iv; hi = not hi
    far = music._lp(music._lp(far, 1400), 1400)   # 遠く：高い音を落とし、短い響き
    far = far + .45 * np.r_[np.zeros(int(.11 * SR)), far[:-int(.11 * SR)]] + .25 * np.r_[np.zeros(int(.23 * SR)), far[:-int(.23 * SR)]]
    # 最初の一人が気づいた瞬間：近くの大きな悲鳴（l02 の 0.7 秒。かまれるのは 1.6 秒）
    j = int((cues["l02"] + .7) * SR); x = _env(Sc[0][: int(1.6 * SR)], .005, .4) * 1.3; near[j:j + len(x)] += x[: n - j]
    return near, far * .9, tick


if not getattr(music, "_P045_BEDS", False):
    music._P045_BEDS = True
    _prev = music.sfx_bank_soft

    def sfx_bank_soft():
        b = _prev()
        if TLP.exists():
            b["bed_near"], b["bed_far"], b["bed_tick"] = beds()
        return b
    music.sfx_bank_soft = sfx_bank_soft

# ---------------------------------------------------------------- きっかけ（ショットの頭＝行の頭、ポップアップ＝ショットの中の秒）
CUES = {"open": ["L00", 0.0]}
POPS = []
for s in SHOTS:
    L = s["id"].upper(); CUES[s["id"]] = [L, 0.0]
    for j, e in enumerate(s.get("ev", [])):
        c = f"ev_{s['id']}_{j}"; CUES[c] = [L, round(e[0] / s["dur"], 4)]; POPS.append(c)
    if s.get("card"):
        c = f"card_{s['id']}"; CUES[c] = [L, round(.15 / s["dur"], 4)]; POPS.append(c)

SEG = ["open"] + [s["id"] for s in SHOTS[1:]]
EP = standard.config({
    "id": "pilot_045",
    "out": "reverse_045_zombie_tokyo.mp4",
    "lead_in": 0.0,
    "cues": CUES,
    "sfx": [["bed_near", "t0", 1.0, 0], ["bed_far", "t0", 1.0, 0], ["bed_tick", "t0", .55, 0], ["crowd", "l00", .42, 0], ["crowd_end", "l18", .55, 0],
            ["heart", "l02", .7, 0], ["radio", "l06", .45, 0], ["heli", "l11", .6, 0]] + [["click", c, .8, 0] for c in POPS],
    "final_hold": 0.0,
    "music": {"style": "file_045", "sections": [["t0", 0.0, "f_mute"]]},
    "segments": SEG,
    "extra_files": epkit.FILES + ["../ext/kit/shots.js", "work/blender/index.js", "../ext/blender/blframes.js", "assets/plan.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 1.5]] + [[s["id"], 0.6] for s in SHOTS[1:]],
    "scenes": [(f"{i} {s['id']}", s["id"] if i else None, SHOTS[i + 1]["id"] if i + 1 < len(SHOTS) else "endcard", "", "") for i, s in enumerate(SHOTS)]
              + [(f"{len(SHOTS)} 暗転（エンディングなし）", "endcard", None, "", "")],
    "plan_notes": ["## 演出の方針（v2）", "", "- 設計：もしも設計（templates/DESIGN_MODES.md）。ナレーションなし、情報はポップアップ（plan.py）。BGM なし、環境音だけ。",
                   "- 小さいところ（都庁前の一体）から、段階ごとにカメラが高くなる。インフラが止まるカット（電車・道路・停電）は想定（計算に入っていない）。",
                   "- ゾンビはジタバタして少し間抜けに。人物は簡易的なピクトグラム。血は出さない。", "- 地図の広がりと数字は計算の結果（sim/）。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
