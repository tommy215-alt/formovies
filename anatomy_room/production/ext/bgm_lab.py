"""BGM の聴き比べ用の 15 パターン（2026-10-29、ユーザーの指示：テンポは今くらい、テクノ感・ビート主体のもの）。テンプレートの外（production/common/music.py は変えない）。

    python anatomy_room/production/ext/bgm_lab.py <出力フォルダ>     # B01.wav〜B15.wav（各 16 小節・約 31 秒）

選ばれたパターンは、あとで music_ext.py に曲調として登録し、場面のモード（w_hook など）で音の厚さを変えられるようにする。
"""
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import music  # noqa: E402
from music import SR, _add, _bell, _hat, _kick_hard, _lp, _noise, _note, _snare, _supersaw  # noqa: E402

N_ = lambda s: int(s * SR)


def hp(x, f):
    return x - _lp(x, f)


def tone(f, dur, amp=1.0, kind="sin", attack=0.005, decay=0.3):
    t = np.arange(N_(dur)) / SR
    if kind == "sin":
        w = np.sin(2 * np.pi * f * t)
    elif kind == "tri":
        w = 2 * np.abs(2 * ((f * t) % 1) - 1) - 1
    elif kind == "saw":
        w = 2 * ((f * t) % 1) - 1
    else:
        w = np.sign(np.sin(2 * np.pi * f * t))
    return amp * w * np.minimum(1, t / attack) * np.exp(-t / decay)


def kick(kind="round"):
    t = np.arange(N_(0.45)) / SR
    if kind == "hard":
        return _kick_hard(0.4)
    if kind == "808":
        f = 42 + 90 * np.exp(-t / 0.04)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.42) * np.minimum(1, t / 0.002)
    if kind == "punch":
        f = 50 + 140 * np.exp(-t / 0.025)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18) + _lp(_noise(len(t), 3), 3000) * np.exp(-t / 0.004) * 0.4
        return np.tanh(1.5 * x) * 0.85
    f = 48 + 75 * np.exp(-t / 0.035)                       # round：丸いキック
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22) * np.minimum(1, t / 0.003) * 0.9


def clap(seed=1):
    return _add(*[np.concatenate([np.zeros(N_(d)), _snare(0.16, seed + i) * .6]) for i, d in enumerate((0, .009, .018))])


def snare_soft(seed=5):
    t = np.arange(N_(0.2)) / SR
    return _add(hp(_noise(len(t), seed), 900) * np.exp(-t / 0.06) * 0.6, np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.5)


def rim():
    return _add(_bell(420, 0.06, 0.5, 0.02, 0.001), hp(_noise(N_(0.03), 7), 1500) * np.exp(-np.arange(N_(0.03)) / SR / 0.006) * 0.4)


def conga(f):
    t = np.arange(N_(0.3)) / SR
    return np.sin(2 * np.pi * np.cumsum(f * (1 + 0.25 * np.exp(-t / 0.02))) / SR) * np.exp(-t / 0.12) * np.minimum(1, t / 0.002)


def shaker(seed):
    t = np.arange(N_(0.05)) / SR
    return hp(_lp(_noise(len(t), seed), 6000), 2200) * np.exp(-t / 0.014)


def acid(freqs_steps, step, n, cut0=300, cut1=2500, res=0.6):
    """303 風：のこぎり波を、音ごとに開く低域通過（1 次を 2 回）＋共鳴の代わりの帯域の強調"""
    out = np.zeros(n)
    for i, f, acc, slide in freqs_steps:
        a = int(i * step * SR); d = step * 0.95
        t = np.arange(N_(d)) / SR
        w = (2 * ((f * t) % 1) - 1) * np.exp(-t / (0.18 if acc else 0.11))
        env = cut0 + (cut1 - cut0) * np.exp(-t / (0.09 if acc else 0.05))
        y = np.zeros_like(w); z1 = z2 = 0.0
        g = 1 - np.exp(-2 * np.pi * env / SR)
        for k in range(len(w)):                            # 2 段の 1 次低域通過（音ごとに短いので速さは足りる）
            z1 += g[k] * (w[k] - z1 + res * (z1 - z2)); z2 += g[k] * (z1 - z2); y[k] = z2
        m = min(len(y), n - a)
        if m > 0:
            out[a:a + m] += y[:m] * (1.3 if acc else 1.0)
    return out


def delay(x, sec, fb=0.4, mix=0.35, n=4):
    out = x.copy()
    for k in range(1, n + 1):
        s = N_(sec * k)
        if s < len(x):
            out[s:] += x[:len(x) - s] * mix * (fb ** (k - 1))
    return out


# 和音の進行（ルート, 和音の構成音）。どれも 4 小節で 1 周
PROG = {
    "Dm": [(73.42, [293.66, 349.23, 440.0]), (58.27, [293.66, 349.23, 466.16]), (65.41, [261.63, 329.63, 392.0]), (55.0, [277.18, 329.63, 440.0])],
    "Am": [(55.0, [261.63, 329.63, 440.0]), (43.65, [261.63, 349.23, 440.0]), (65.41, [261.63, 329.63, 392.0]), (49.0, [293.66, 392.0, 493.88])],
    "D":  [(73.42, [293.66, 369.99, 440.0]), (55.0, [277.18, 329.63, 440.0]), (61.74, [293.66, 369.99, 493.88]), (49.0, [293.66, 392.0, 493.88])],
    "F":  [(43.65, [349.23, 440.0, 523.25]), (65.41, [329.63, 392.0, 523.25]), (73.42, [293.66, 349.23, 440.0]), (58.27, [293.66, 349.23, 466.16])],
    "Em": [(41.2, [329.63, 392.0, 493.88]), (65.41, [329.63, 392.0, 523.25]), (49.0, [293.66, 392.0, 493.88]), (73.42, [293.66, 369.99, 440.0])],
    "Cm": [(65.41, [311.13, 392.0, 523.25]), (51.91, [311.13, 415.3, 523.25]), (58.27, [293.66, 349.23, 466.16]), (49.0, [293.66, 392.0, 466.16])],
    # 短調の進行（i–iv–VI–v。2026-10-29、ユーザーの指示「コードを短調に」）
    "Dm_min": [(73.42, [293.66, 349.23, 440.0]), (49.0, [293.66, 392.0, 466.16]), (58.27, [293.66, 349.23, 466.16]), (55.0, [261.63, 329.63, 440.0])],
    "Cm_min": [(65.41, [311.13, 392.0, 523.25]), (43.65, [349.23, 415.3, 523.25]), (51.91, [311.13, 415.3, 523.25]), (49.0, [293.66, 392.0, 466.16])],
    "Em_min": [(41.2, [329.63, 392.0, 493.88]), (55.0, [329.63, 440.0, 523.25]), (65.41, [329.63, 392.0, 523.25]), (61.74, [293.66, 369.99, 493.88])],
}

# 16 分の打ち込み（x＝鳴らす、o＝弱く）。1 小節＝16 文字
STYLES = {
    "B01": dict(name="Deep House", bpm=123, prog="Am", kick="round", k="x...x...x...x...", hat="..x...x...x...x.", ohat="", clap="....x.......x...", swing=.12,
                bass="sub_off", chords="ep_stab", lead="", pad=.5, perc="shaker", fx=.0),
    "B02": dict(name="Minimal Techno", bpm=125, prog="Dm", kick="punch", k="x...x...x...x...", hat="..x...x...x...x.", ohat="", clap="", swing=.0,
                bass="roll", chords="", lead="click", pad=.15, perc="rim_sparse", fx=.3),
    "B03": dict(name="Melodic Techno", bpm=124, prog="Dm", kick="punch", k="x...x...x...x...", hat="..x...x...x...x.", ohat="..x...x...x...x.", clap="....x.......x...", swing=.0,
                bass="roll", chords="", lead="arp16", pad=.8, perc="", fx=.35),
    "B04": dict(name="Progressive House", bpm=124, prog="F", kick="round", k="x...x...x...x...", hat="x.x.x.x.x.x.x.x.", ohat="..x...x...x...x.", clap="....x.......x...", swing=.0,
                bass="off8", chords="", lead="pluck8", pad=.9, perc="", fx=.3),
    "B05": dict(name="Tech House", bpm=125, prog="Cm", kick="punch", k="x...x...x...x...", hat="x.xxx.xxx.xxx.xx", ohat="..x...x...x...x.", clap="....x.......x...", swing=.1,
                bass="bounce", chords="", lead="", pad=.2, perc="conga", fx=.0),
    "B06": dict(name="Electro", bpm=124, prog="Em", kick="808", k="x.....x...x.....", hat="x.x.x.x.x.x.x.x.", ohat="", clap="....x.......x...", swing=.0,
                bass="808", chords="", lead="square", pad=.3, perc="", fx=.2),
    "B07": dict(name="Synthwave", bpm=122, prog="Am", kick="round", k="x.......x.......", hat="x.x.x.x.x.x.x.x.", ohat="", clap="....x.......x...", swing=.0,
                bass="oct8", chords="saw_pad", lead="", pad=.9, perc="", fx=.25),
    "B08": dict(name="Breakbeat", bpm=124, prog="Dm", kick="punch", k="x.....x...x.....", hat="x.x.x.x.x.x.x.x.", ohat="", clap="....x..x.x..x...", swing=.06,
                bass="sub_long", chords="ep_stab", lead="", pad=.5, perc="", fx=.0),
    "B09": dict(name="Lo-fi Beat", bpm=124, prog="F", kick="round", k="x.....x...x.....", hat="..x...x...x...x.", ohat="", clap="....x.......x...", swing=.2,
                bass="sub_long", chords="keys", lead="", pad=.4, perc="vinyl", fx=.0, soft=True),
    "B10": dict(name="2-step Garage", bpm=128, prog="Cm", kick="round", k="x.....x...x..x..", hat="..x...x...x...x.", ohat="", clap="....x.......x...", swing=.18,
                bass="sub_off", chords="saw_pad", lead="", pad=.7, perc="shaker", fx=.2),
    "B11": dict(name="Afro House", bpm=122, prog="Am", kick="round", k="x...x...x...x...", hat="..x...x...x...x.", ohat="", clap="", swing=.08,
                bass="sub_off", chords="", lead="kalimba", pad=.4, perc="afro", fx=.2),
    "B12": dict(name="Dark Techno", bpm=126, prog="Em", kick="hard", k="x...x...x...x...", hat="..x...x...x...x.", ohat="..x...x...x...x.", clap="", swing=.0,
                bass="rumble", chords="", lead="", pad=.4, perc="rim_sparse", fx=.35),
    "B13": dict(name="Acid Techno", bpm=125, prog="Dm", kick="punch", k="x...x...x...x...", hat="x.x.x.x.x.x.x.x.", ohat="..x...x...x...x.", clap="....x.......x...", swing=.0,
                bass="acid", chords="", lead="", pad=.2, perc="", fx=.2),
    "B14": dict(name="Dub Techno", bpm=122, prog="Cm", kick="round", k="x...x...x...x...", hat="..x...x...x...x.", ohat="", clap="", swing=.0,
                bass="sub_long", chords="dub_stab", lead="", pad=.5, perc="", fx=.6),
    "B15": dict(name="Future Bass Lite", bpm=124, prog="D", kick="round", k="x.......x.......", hat="x.x.x.x.x.x.x.x.", ohat="", clap="....x.......x...", swing=.0,
                bass="sub_long", chords="supersaw", lead="pluck8", pad=.6, perc="", fx=.2),
}


def render(st, bars=16, modes=None, total=None):
    """modes：[(秒, モード名), …] を渡すと、聴き比べ用の流れの代わりに、場面のモード（MODES）で各パートの厚さを変える（動画の BGM）"""
    beat = 60 / st["bpm"]; step = beat / 4
    if total:
        bars = int(np.ceil(total / (4 * beat))) + 1
    n = N_(bars * 4 * beat) + SR
    prog = PROG[st["prog"]]; P = {k: np.zeros(n) for k in ("kick", "clap", "hat", "ohat", "bass", "chords", "lead", "pad", "perc")}
    K = kick(st["kick"]); CL = clap(); OH = _hat(open_=True, seed=42)
    def put(name, t, x, a=1.0):
        i = int(t * SR)
        if 0 <= i < n:
            m = min(len(x), n - i); P[name][i:i + m] += x[:m] * a
    def at(bar, s16):                                      # 16 分の位置（裏の 16 分を少し後ろへずらすスウィング）
        return (bar * 16 + s16) * step + (st["swing"] * step if s16 % 2 else 0)
    for bar in range(bars):
        root, tones = prog[bar % 4]
        for s in range(16):
            if st["k"][s] == "x": put("kick", at(bar, s), K)
            if st["clap"] and st["clap"][s] == "x": put("clap", at(bar, s), snare_soft() if st.get("soft") else CL)
            if st["hat"][s] in "xo": put("hat", at(bar, s), _hat(0.04, 41 + s), (0.5 if s % 4 else 0.7) * (0.6 if st["hat"][s] == "o" else 1))
            if st["ohat"] and st["ohat"][s] == "x": put("ohat", at(bar, s), OH, 0.5)
        # ベース
        b = st["bass"]
        if b == "sub_off":
            for s in (2, 6, 10, 14): put("bass", at(bar, s), tone(root * 2, step * 1.8, .6, "sin", .004, .25))
        elif b == "roll":
            for s in range(16):
                if s % 4: put("bass", at(bar, s), tone(root * (2 if s % 4 == 2 else 1) * 2, step * .9, .45, "saw", .002, .07))
        elif b == "off8":
            for s in (2, 6, 10, 14): put("bass", at(bar, s), tone(root * 2, step * 1.6, .55, "saw", .003, .12))
        elif b == "bounce":
            for s, f in ((2, 1), (3, 2), (6, 1), (10, 1), (11, 1.5), (14, 1)): put("bass", at(bar, s), tone(root * 2 * f, step * .9, .55, "tri", .002, .09))
        elif b == "808":
            for s in (0, 6, 10): put("bass", at(bar, s), tone(root * 2, step * 3.5, .7, "sin", .003, .4))
        elif b == "oct8":
            for s in range(0, 16, 2): put("bass", at(bar, s), tone(root * 2 * (2 if s % 4 else 1), step * 1.7, .45, "saw", .003, .12))
        elif b == "sub_long":
            put("bass", at(bar, 0), tone(root * 2, beat * 2.8, .6, "sin", .01, 1.2)); put("bass", at(bar, 10), tone(root * 2, beat * 1.4, .45, "sin", .01, .6))
        elif b == "rumble":
            for s in range(16):
                if s % 4: put("bass", at(bar, s), tone(root * 2, step * .9, .5, "saw", .002, .05))
        # 和音
        c = st["chords"]
        if c == "ep_stab":
            for s, a in ((0, .9), (6, .6), (10, .8)):
                for f in tones: put("chords", at(bar, s), music_ext_ep(f, beat * 1.3, .07 * a))
        elif c == "saw_pad":
            for f in tones: put("chords", at(bar, 0), _supersaw(f / 2, beat * 4.1, .05, n=5, spread=.01, attack=.3, decay=3.0, seed=bar))
        elif c == "keys":
            for s in (0, 7):
                for k_, f in enumerate(tones): put("chords", at(bar, s) + k_ * .02, _bell(f, beat * 2, .1, .6, .01))
        elif c == "dub_stab":
            for s in (2, 10):
                for f in tones: put("chords", at(bar, s), tone(f, step * 1.5, .08, "saw", .002, .12))
        elif c == "supersaw":
            for s in (0, 3, 6, 10, 12):
                for f in tones: put("chords", at(bar, s), _supersaw(f, step * 1.6, .045, n=5, spread=.012, attack=.01, decay=.2, seed=bar + s))
        # 上もの
        l_ = st["lead"]
        if l_ == "arp16":
            for s in range(16): put("lead", at(bar, s), _bell(tones[s % 3] * (2 if (s // 3) % 2 else 1), step * 1.5, .09, .12, .003))
        elif l_ == "pluck8":
            for s in range(0, 16, 2): put("lead", at(bar, s), tone(tones[(s // 2) % 3] * 2, step * 1.8, .12, "tri", .002, .14))
        elif l_ == "click":
            for s in (3, 7, 11, 13): put("lead", at(bar, s), _bell(1200 + 200 * (s % 3), .03, .3, .008, .001))
        elif l_ == "square":
            for s in (0, 3, 6, 8, 11, 14): put("lead", at(bar, s), tone(tones[s % 3] * 2, step * .8, .06, "sq", .002, .08))
        elif l_ == "kalimba":
            for s in (0, 3, 6, 8, 10, 13): put("lead", at(bar, s), _bell(tones[(s * 2) % 3] * 2, .5, .14, .25, .002))
        # パッド
        if st["pad"]:
            for f in tones: put("pad", at(bar, 0), _supersaw(f / 2, beat * 4.1, .04 * st["pad"], n=3, spread=.005, attack=.6, decay=4.0, seed=100 + bar))
        # 打楽器
        pc = st["perc"]
        if pc == "shaker":
            for s in range(16): put("perc", at(bar, s), shaker(60 + s), .5 if s % 2 else .25)
        elif pc == "conga":
            for s, f in ((3, 220), (7, 330), (10, 220), (14, 260)): put("perc", at(bar, s), conga(f), .35)
        elif pc == "afro":
            for s, f in ((0, 180), (3, 260), (6, 220), (8, 180), (10, 320), (11, 260), (14, 220)): put("perc", at(bar, s), conga(f), .35)
            for s in range(16): put("perc", at(bar, s), shaker(80 + s), .35 if s % 2 else .2)
        elif pc == "rim_sparse":
            for s in (5, 11): put("perc", at(bar, s), rim(), .5)
        elif pc == "vinyl":
            put("perc", at(bar, 0), _lp(_noise(N_(beat * 4), 900 + bar), 2500) * 0.04)
    if st["bass"] == "acid":                                # アシッドベース（16 分のパターン、アクセントつき）
        pat = [(0, 1, 1), (2, 1, 0), (3, 2, 0), (6, 1, 1), (8, 1.5, 0), (10, 1, 0), (11, 2, 1), (14, 1, 0)]
        steps = [(bar * 16 + s, prog[bar % 4][0] * 2 * m, acc, 0) for bar in range(bars) for s, m, acc in pat]
        P["bass"] += acid(steps, step, n) * .35
    # 音色と空間
    P["bass"] = _lp(P["bass"], 900 if st["bass"] in ("acid",) else 500); P["hat"] = _lp(P["hat"], 9000); P["chords"] = _lp(P["chords"], 3500)
    P["lead"] = _lp(P["lead"], 4000); P["pad"] = _lp(_lp(P["pad"], 1500), 1500)
    if st["fx"]:
        for k in ("chords", "lead"):
            P[k] = delay(P[k], beat * .75, .45, st["fx"])
    # サイドチェイン（キックでベースと和音を少し下げる）
    sc = np.ones(n)
    for bar in range(bars):
        for s in range(16):
            if st["k"][s] == "x":
                a = int(at(bar, s) * SR); m = min(n - a, int(beat * SR))
                if m > 0: sc[a:a + m] = np.minimum(sc[a:a + m], 1 - .5 * np.exp(-np.arange(m) / SR / .1))
    for k in ("bass", "chords", "pad"):
        P[k] *= sc
    # 曲の流れ：1〜4 小節＝入り（ビートとパッド）、5〜12＝本編、13〜14＝引き（キックとベースを抜く）、15〜16＝戻り
    t = np.arange(n) / SR; bar_i = (t / (beat * 4)).astype(int)
    g = {k: np.ones(n) for k in P}
    lev = {"kick": .62, "clap": .3, "hat": .18, "ohat": .12, "bass": .5, "chords": .5, "lead": .45, "pad": .5, "perc": .4}
    if modes is None:                                      # 聴き比べ用の流れ
        intro, brk = bar_i < 4, (bar_i >= 12) & (bar_i < 14)
        for k in ("bass", "lead", "chords", "perc", "clap", "ohat"):
            g[k][intro] = 0.0
        for k in ("kick", "bass", "clap"):
            g[k][brk] = 0.0
        ker = np.ones(N_(.03)) / N_(.03)
        mix = sum(P[k] * np.convolve(g[k], ker, mode="same") * lev[k] for k in P)
        end = N_(bars * 4 * beat)
    else:                                                  # 動画の BGM：場面のモードで厚さを変える（旋律のパートは 0.6 秒、打楽器は 0.05 秒でなめらかに）
        sec = sorted(modes) + [(n / SR + 1, None)]
        for (a, m), (b, _) in zip(sec, sec[1:]):
            ia, ib = max(0, int(a * SR)), min(n, int(b * SR))
            for k in P:
                g[k][ia:ib] = MODES[m].get(k, 0.0)
        kd, km = np.ones(N_(.05)) / N_(.05), np.ones(N_(.6)) / N_(.6)
        mix = sum(P[k] * (music._smooth(g[k], km) if k in ("bass", "chords", "lead", "pad") else np.convolve(g[k], kd, mode="same")) * lev[k] for k in P)
        end = N_(total)
    mix = np.tanh(1.2 * mix) / 1.2
    mix = mix[:end] * np.clip(t[:end] / .01, 0, 1) * np.clip((end / SR - t[:end]) / 1.5, 0, 1)
    return mix


# 動画の BGM の曲調（2026-10-29、ユーザーが試聴で選んだ 5 つ。和音は短調）。REVERSE_GUIDELINE_v2.3.md
LAB = {"lab_melodic": ("B03", "Dm_min"), "lab_electro": ("B06", "Em_min"), "lab_break": ("B08", "Dm_min"), "lab_2step": ("B10", "Cm_min"), "lab_dub": ("B14", "Cm_min")}
_m = lambda **kw: {k: kw.get(k, 0.0) for k in ("kick", "clap", "hat", "ohat", "bass", "chords", "lead", "pad", "perc")}
MODES = {   # 場面のモード → パートの厚さ（music_ext の warm_drive と同じ名前）
    "w_hook": _m(kick=1, clap=.6, hat=.8, ohat=.5, bass=1, chords=.8, lead=.7, pad=.8, perc=.6),
    "w_story": _m(kick=.8, clap=.5, hat=.7, ohat=.3, bass=.8, chords=.6, lead=.3, pad=.6, perc=.5),
    "w_focus": _m(kick=.9, clap=.6, hat=.9, ohat=.6, bass=.9, chords=.5, lead=.8, pad=.5, perc=.6),
    "w_discover": _m(kick=1, clap=1, hat=1, ohat=1, bass=1, chords=1, lead=1, pad=1, perc=1),
    "w_shade": _m(kick=.5, hat=.5, bass=.6, chords=.5, pad=.9, perc=.3),
    "w_hold": _m(hat=.3, bass=.3, chords=.7, pad=1, lead=.2),
    "w_rise": _m(kick=.9, clap=.6, hat=.8, ohat=.6, bass=.9, chords=.7, lead=.6, pad=.7, perc=.6),
    "w_warm": _m(kick=.7, clap=.4, hat=.6, ohat=.3, bass=.7, chords=.7, lead=.4, pad=.9, perc=.4),
    "w_end": _m(kick=.4, hat=.4, bass=.4, chords=.7, pad=1),
    "ending": _m(hat=.3, bass=.3, chords=.7, pad=1),
}


def bgm_style(total, sections, style):
    base, prog = LAB[style]
    st = {**STYLES[base], "prog": prog}
    return render(st, modes=sections, total=total), {}


def music_ext_ep(f, dur, amp):
    t = np.arange(N_(dur)) / SR
    return amp * np.exp(-t / .5) * np.minimum(1, t / .006) * (np.sin(2 * np.pi * f * t) + .28 * np.sin(4 * np.pi * f * t) * np.exp(-t / .18))


def write(path, x):
    y = np.int16(np.clip(x / (np.abs(x).max() + 1e-9) * .89, -1, 1) * 32767)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())


if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    only = sys.argv[2:] or list(STYLES)
    for k in only:
        write(out / f"{k}.wav", render(STYLES[k])); print(k, STYLES[k]["name"], flush=True)
