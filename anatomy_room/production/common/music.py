"""第 3 話以降の BGM と効果音（すべてここで一から合成。外部音源なし）。

BGM はアップテンポ（BPM 128〜140）で、ドラム・ベース・和音・リード・パッドを別々に作り、
場面ごとの「モード」で各パートの音量を切り替える（同じ音量・同じ厚さで流し続けない）。

  モード  : hook（冒頭の強いつかみ）/ chaos（ドタバタ）/ banter（掛け合い）/ explain（解説：落ち着かせる）/
            reveal（発見：きらめき）/ drop（オチ直前の無音）/ ending（エンディング：薄く）
  スタイル: sky（明るい 8 ビート・きらきらしたリード）/ chip（四角い波のチップチューン）/ funk（はずむベースとマリンバ）
"""
import math

import numpy as np

SR = 48000

# パートごとの音量（モード → {パート: 倍率}）
MODES = {
    "hook":    {"kick": 1.0, "snare": 1.0, "hat": 1.0, "bass": 1.0, "chord": 1.0, "lead": 1.0, "pad": 0.5, "arp": 0.6},
    "chaos":   {"kick": 1.0, "snare": 1.0, "hat": 1.0, "bass": 1.0, "chord": 0.9, "lead": 0.8, "pad": 0.3, "arp": 1.0},
    "banter":  {"kick": 0.85, "snare": 0.8, "hat": 0.8, "bass": 0.9, "chord": 0.75, "lead": 0.0, "pad": 0.35, "arp": 0.0},
    "explain": {"kick": 0.0, "snare": 0.0, "hat": 0.45, "bass": 0.55, "chord": 0.0, "lead": 0.0, "pad": 0.8, "arp": 0.35},
    "reveal":  {"kick": 0.9, "snare": 0.7, "hat": 0.9, "bass": 0.9, "chord": 0.8, "lead": 0.0, "pad": 0.5, "arp": 0.9},
    "drop":    {k: 0.0 for k in ("kick", "snare", "hat", "bass", "chord", "lead", "pad", "arp")},
    "ending":  {"kick": 0.0, "snare": 0.0, "hat": 0.0, "bass": 0.4, "chord": 0.0, "lead": 0.0, "pad": 0.9, "arp": 0.5},
}

STYLES = {
    # 和音は（ルート, 構成音）の 4 小節ループ。周波数は Hz
    "sky":  {"bpm": 136, "chords": [(87.31, [349.23, 440.0, 523.25]), (65.41, [329.63, 392.0, 523.25]),
                                    (73.42, [293.66, 349.23, 440.0]), (58.27, [293.66, 349.23, 466.16])],
             "wave": "saw", "lead_wave": "tri", "swing": 0.0},
    "chip": {"bpm": 140, "chords": [(55.0, [440.0, 523.25, 659.25]), (43.65, [349.23, 440.0, 523.25]),
                                    (65.41, [392.0, 523.25, 659.25]), (49.0, [392.0, 493.88, 587.33])],
             "wave": "square", "lead_wave": "square", "swing": 0.0},
    "funk": {"bpm": 128, "chords": [(65.41, [329.63, 392.0, 493.88]), (55.0, [329.63, 392.0, 523.25]),
                                    (43.65, [349.23, 440.0, 523.25]), (49.0, [392.0, 493.88, 587.33])],
             "wave": "saw", "lead_wave": "marimba", "swing": 0.12},
}


def _osc(kind, f, t):
    ph = (f * t) % 1.0
    if kind == "square":
        return np.where(ph < 0.5, 1.0, -1.0) * 0.6
    if kind == "saw":
        return (2 * ph - 1) * 0.6
    if kind == "tri":
        return (4 * np.abs(ph - 0.5) - 1)
    if kind == "marimba":
        return np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * f * t)


def _lp(x, cutoff):
    """1 次ローパス（明るすぎる波形を丸める）。指数の減衰を FFT で畳み込む。"""
    k = 1 - math.exp(-2 * math.pi * cutoff / SR)
    m = min(len(x), int(6 / k) + 1)
    kern = k * (1 - k) ** np.arange(m)
    L = 1 << (len(x) + m).bit_length()
    return np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(kern, L), L)[: len(x)]


def _note(buf, i, f, dur, amp, kind, attack=0.004, decay=0.15, cutoff=None):
    n = min(int(dur * SR), len(buf) - i)
    if n <= 0 or i < 0:
        return
    t = np.arange(n) / SR
    env = np.minimum(1, t / attack) * np.exp(-t / decay)
    buf[i:i + n] += _osc(kind, f, t) * env * amp  # 音色の丸め（cutoff）はパート全体にまとめてかける


def _noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n)


def _kick(dur=0.32):
    t = np.arange(int(dur * SR)) / SR
    f = 45 + 95 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.13) * 0.9


def _snare(dur=0.22, seed=1):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = _noise(n, seed)
    nz = nz - _lp(nz, 1800)  # 高い成分だけ
    return (0.55 * nz * np.exp(-t / 0.06) + 0.35 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04))


def _hat(dur=0.06, seed=2, open_=False):
    n = int((0.22 if open_ else dur) * SR)
    t = np.arange(n) / SR
    nz = _noise(n, seed)
    nz = nz - _lp(nz, 7000)
    return 0.32 * nz * np.exp(-t / (0.07 if open_ else 0.018))


def bgm(total, sections, style="sky", seed=0):
    """sections = [(開始秒, モード), ...]（開始秒の昇順）。戻り値は (BGM 全体, パートごとの辞書)。"""
    st = STYLES[style]
    bpm = st["bpm"]
    beat = 60 / bpm
    n = int(total * SR)
    parts = {k: np.zeros(n) for k in ("kick", "snare", "hat", "bass", "chord", "lead", "pad", "arp")}
    kick, snare, hat, ohat = _kick(), _snare(), _hat(), _hat(open_=True)
    rng = np.random.default_rng(seed)
    nbeats = int(total / beat) + 2

    def put(name, i, x, amp=1.0):
        if 0 <= i < n:
            m = min(len(x), n - i)
            parts[name][i:i + m] += x[:m] * amp

    # 2 小節のリードのモチーフ（和音の構成音から選ぶ。8 分音符、ところどころ休み）
    motif = [0, None, 2, 1, None, 2, 0, None, 1, 2, None, 0, 2, None, 1, None]
    for b in range(nbeats):
        tb = b * beat
        bar, pos = divmod(b, 4)
        root, tones = st["chords"][bar % 4]
        i = int(tb * SR)
        # ドラム：4 つ打ちのキック、2・4 拍のスネア（クラップ風）、8 分のハイハット（funk は少しはねる）
        put("kick", i, kick)
        if style == "funk" and pos == 3:
            put("kick", int((tb + beat * 0.75) * SR), kick, 0.6)
        if pos in (1, 3):
            put("snare", i, snare)
        for h in (0, 1):
            off = h * beat * (0.5 + st["swing"] * (1 if h else 0))
            put("hat", int((tb + off) * SR), ohat if (h == 1 and pos == 3) else hat, 1.0 if h else 0.6)
        # ベース：8 分音符でルートとオクターブを行き来する
        for h in (0, 1):
            f = root * (2 if (h == 1 and style != "chip") else 1) * (2 if style == "chip" else 1)
            _note(parts["bass"], int((tb + h * beat / 2) * SR), f, beat * 0.45, 0.42, "square" if style == "chip" else "saw",
                  decay=0.12, cutoff=900)
        # 和音：裏拍のスタッカート
        for f in tones:
            _note(parts["chord"], int((tb + beat / 2) * SR), f, beat * 0.3, 0.075, st["wave"], decay=0.07, cutoff=2600)
        # パッド：小節頭で長く
        if pos == 0:
            for f in tones:
                for det in (-0.8, 0.8):
                    _note(parts["pad"], i, (f + det) / 2, beat * 4.2, 0.05, "sin", attack=0.25, decay=2.5)
        # アルペジオ：16 分で構成音を上下
        for k in range(4):
            f = tones[[0, 1, 2, 1][k]] * 2
            _note(parts["arp"], int((tb + k * beat / 4) * SR), f, beat * 0.22, 0.05, "tri" if style != "chip" else "square",
                  decay=0.05, cutoff=5000)
        # リード：2 小節のモチーフ（4 小節ごとに 1 音ずらして変化）
        for h in (0, 1):
            step = (bar % 2) * 8 + pos * 2 + h
            m = motif[step]
            if m is None:
                continue
            idx = (m + (bar // 4) % 3) % 3
            f = tones[idx] * 2
            _note(parts["lead"], int((tb + h * beat / 2) * SR), f, beat * 0.42, 0.11, st["lead_wave"],
                  decay=0.16 if st["lead_wave"] != "marimba" else 0.09, cutoff=4000)

    for name, fc in (("bass", 900), ("chord", 2600), ("arp", 5000), ("lead", 4000)):
        parts[name] = _lp(parts[name], fc)
    # モードの切り替え（0.12 秒でなめらかに）
    t = np.arange(n) / SR
    gains = {k: np.zeros(n) for k in parts}
    sec = sorted(sections) + [(total + 1, None)]
    for (a, mode), (b, _) in zip(sec, sec[1:]):
        ia, ib = max(0, int(a * SR)), min(n, int(b * SR))
        for k in parts:
            gains[k][ia:ib] = MODES[mode][k]
    k = int(0.12 * SR)
    ker = np.ones(k) / k
    mix = np.zeros(n)
    level = {"kick": 0.55, "snare": 0.32, "hat": 0.25, "bass": 0.3, "chord": 0.6, "lead": 0.45, "pad": 0.55, "arp": 0.4}
    out_parts = {}
    for name, x in parts.items():
        g = np.convolve(gains[name], ker, mode="same")
        out_parts[name] = x * g * level[name]
        mix += out_parts[name]
    fade = np.clip(t / 0.05, 0, 1) * np.clip((total - t) / 1.2, 0, 1)
    return mix * fade, out_parts


# ---------------------------------------------------------------- 効果音
def _sweep(dur, f0, f1, amp, kind="sin", curve=1.0):
    t = np.arange(int(dur * SR)) / SR
    f = f0 + (f1 - f0) * (t / dur) ** curve
    ph = np.cumsum(f) / SR
    x = np.sin(2 * np.pi * ph) if kind == "sin" else (2 * (ph % 1) - 1)
    return amp * x * np.sin(np.pi * t / dur) ** 0.5


def _noise_sweep(dur, f0, f1, amp, seed=7):
    n = int(dur * SR)
    x = _noise(n, seed)
    lo = _lp(x, f0)
    hi = _lp(x, f1)
    k = np.linspace(0, 1, n)
    y = lo * (1 - k) + hi * k
    env = np.sin(np.pi * np.arange(n) / n) ** 2
    return amp * y * env / (np.abs(y).max() + 1e-9)


def _tone(f, dur, amp, decay):
    t = np.arange(int(dur * SR)) / SR
    return amp * np.sin(2 * np.pi * f * t) * np.exp(-t / decay) * np.minimum(1, t / 0.003)


def _add(*xs):
    out = np.zeros(max(len(x) for x in xs))
    for x in xs:
        out[: len(x)] += x
    return out


def _delay(x, sec, amp):
    d = int(sec * SR)
    return _add(x, np.concatenate([np.zeros(d), x * amp]))


def sfx_bank():
    t = lambda d: np.arange(int(d * SR)) / SR
    impact = _add(_kick(0.5) * 1.2, _noise(int(0.25 * SR), 11) * np.exp(-t(0.25) / 0.05) * 0.35)
    glitch = np.zeros(int(0.6 * SR))
    r = np.random.default_rng(5)
    for k in range(10):  # 短い四角い波の断片を不規則に
        i = int(r.uniform(0, 0.5) * SR)
        m = int(r.uniform(0.015, 0.05) * SR)
        f = r.uniform(200, 1800)
        glitch[i:i + m] += np.sign(np.sin(2 * np.pi * f * np.arange(m) / SR)) * 0.25
    return {
        "impact": impact,                                                            # 異常事態のインパクト
        "whoosh": _noise_sweep(0.45, 400, 4000, 0.4),
        "rewind": _add(_sweep(0.9, 1400, 180, 0.22, "saw", 0.6), _noise_sweep(0.9, 5000, 300, 0.25, 9)),  # 巻き戻し
        "pop": _add(_tone(660, 0.18, 0.3, 0.05), _tone(990, 0.15, 0.15, 0.04)),
        "ding": _delay(_add(_tone(1318.5, 0.9, 0.25, 0.3), _tone(1975.5, 0.7, 0.12, 0.25)), 0.12, 0.4),  # 発見
        "sparkle": _add(*[np.concatenate([np.zeros(int(k * 0.06 * SR)), _tone(f, 0.4, 0.13, 0.12)])
                          for k, f in enumerate([1568, 1976, 2349, 3136])]),
        "boing": _sweep(0.45, 180, 520, 0.35, "sin", 0.5),                          # ウラの毒舌（コミカル）
        "boop": _add(_tone(392, 0.12, 0.28, 0.05), np.concatenate([np.zeros(int(0.1 * SR)), _tone(311, 0.2, 0.28, 0.08)])),
        "stab": _add(*[_tone(f, 0.35, 0.16, 0.12) for f in (261.6, 329.6, 392.0, 523.3)],
                     _kick(0.3) * 0.5),                                             # オチのアクセント
        "glitch": glitch,
        "scan": _sweep(0.7, 600, 1800, 0.15, "sin", 1.0),
        "ok": _add(_tone(880, 0.12, 0.25, 0.06), np.concatenate([np.zeros(int(0.11 * SR)), _tone(1318.5, 0.3, 0.25, 0.1)])),
        "error": _add(*[np.concatenate([np.zeros(int(k * 0.16 * SR)),
                                        np.sign(np.sin(2 * np.pi * 150 * t(0.12))) * 0.16 * np.exp(-t(0.12) / 0.1)])
                        for k in range(2)]),
        "riser": _noise_sweep(1.0, 300, 6000, 0.3, 13) * np.linspace(0.2, 1, int(1.0 * SR)),
        "cash": _add(_tone(2093, 0.6, 0.2, 0.2), _tone(2637, 0.5, 0.14, 0.18),
                     _noise(int(0.08 * SR), 17) * np.exp(-t(0.08) / 0.02) * 0.2),  # レジの「チーン」
        "snap": _noise(int(0.05 * SR), 19) * np.exp(-t(0.05) / 0.006) * 0.6,       # 指を鳴らす
        "tick": _add(_tone(1320, 0.1, 0.2, 0.025), _tone(2640, 0.07, 0.05, 0.02)),
        "slide": _noise_sweep(0.6, 600, 2400, 0.3, 21),
        "rain": _add(*[np.concatenate([np.zeros(int(k * 0.07 * SR)), _tone(f, 0.12, 0.12, 0.04)])
                       for k, f in enumerate([1200, 900, 1500, 1100, 1700, 1000, 1400, 1250])]),
        "end": _add(_tone(523.25, 2.2, 0.16, 0.8), _tone(783.99, 2.2, 0.13, 0.8), _tone(1046.5, 2.2, 0.1, 0.8)),
    }


def estimate_bpm(x, lo=90, hi=180):
    """BGM の拍の速さを推定する（音量の立ち上がりの自己相関）。品質検証用。"""
    hop = 480  # 10 ms
    m = len(x) // hop
    e = np.sqrt(np.mean(x[: m * hop].reshape(m, hop) ** 2, axis=1))
    on = np.maximum(0, np.diff(e))
    on = on - on.mean()
    ac = np.correlate(on, on, "full")[len(on) - 1:]
    lags = np.arange(len(ac))
    lo_l, hi_l = int(60 / hi * 100), int(60 / lo * 100)
    k = lo_l + int(np.argmax(ac[lo_l:hi_l]))
    return 60 / (k / 100)


# ================================================================ テクノ版（2026-10-26 改修：第 3 話以降）
# 4 つ打ちの重いキック、サイドチェインで「うねる」ベースとパッド、硬いシンセの和音（スタブ）、16 分のアルペジオ。
# 軽いポップ／コミカルな音色は使わない。笑いは映像と効果音の組み合わせで作る。
TECH_STYLES = {
    # 和音は（ルート周波数, 構成音）の 4 小節ループ（短調で緊張感を出す）
    "tech_air":   {"bpm": 132, "chords": [(43.65, [349.23, 415.30, 523.25]), (69.30, [277.18, 349.23, 415.30]),
                                          (51.91, [311.13, 415.30, 523.25]), (77.78, [311.13, 392.00, 466.16])], "seed": 1},
    "tech_data":  {"bpm": 138, "chords": [(55.00, [440.00, 523.25, 659.25]), (55.00, [440.00, 523.25, 659.25]),
                                          (43.65, [349.23, 440.00, 523.25]), (49.00, [392.00, 493.88, 587.33])], "seed": 2},
    "tech_price": {"bpm": 128, "chords": [(73.42, [293.66, 349.23, 440.00]), (58.27, [293.66, 349.23, 466.16]),
                                          (43.65, [349.23, 440.00, 523.25]), (65.41, [329.63, 392.00, 523.25])], "seed": 3},
    # イナクセシブルクイナの回：深く暗いシネマティック（ニ短調 Dm–B♭–F–C、ゆったり）
    "tech_deep":  {"bpm": 100, "chords": [(36.71, [293.66, 349.23, 440.00]), (58.27, [233.08, 293.66, 349.23]),
                                          (43.65, [261.63, 349.23, 440.00]), (65.41, [261.63, 329.63, 392.00])], "seed": 5},
    # PHP 騒動の回：緊張感と未来感（ホ短調。ふざけた印象にしない）
    "tech_net":   {"bpm": 134, "chords": [(41.20, [329.63, 392.00, 493.88]), (65.41, [261.63, 329.63, 392.00]),
                                          (55.00, [329.63, 440.00, 523.25]), (61.74, [311.13, 369.99, 493.88])], "seed": 4},
    # 標準（2026-10-27〜、REVERSE_STANDARD_RULES v2）：ビートのあるダークなテクノ／インダストリアル。
    # 124 BPM、ニ短調（Dm–Dm–B♭–A）。4 つ打ちのキック、うねるベース、金属的な打音（metal）、低いうなり（rumble）。
    # ナレーションの帯域（1〜4 kHz）にかぶる和音（stab）とアルペジオは控えめにし、存在感は低音とリズムで出す
    "tech_drive": {"bpm": 124, "chords": [(36.71, [293.66, 349.23, 440.00]), (36.71, [293.66, 349.23, 440.00]),
                                          (58.27, [293.66, 349.23, 466.16]), (55.00, [277.18, 329.63, 440.00])], "seed": 6},
}
# 希望の和音（2026-10-28〜、標準ルール v3）：doc_hope・doc_warm だけで鳴る長調の進行（ヘ長調 F–C–Dm–B♭）。
# 短調の和音（chords）と同じ 4 小節で回す。旧モードではこのパート（wbass・wpad・keys）は鳴らない
WARM_CHORDS = [(43.65, [349.23, 440.00, 523.25]), (65.41, [329.63, 392.00, 523.25]),
               (36.71, [293.66, 349.23, 440.00]), (58.27, [293.66, 349.23, 466.16])]
# モード → パートの音量。旧モード名（hook/banter/reveal）も受け付ける
TECH_MODES = {
    "intro":   {"kick": 1.0, "clap": 1.0, "hat": 1.0, "ohat": 1.0, "bass": 1.0, "bass_dark": 0.0, "stab": 1.0, "arp": 0.8, "pad": 0.6},
    "chaos":   {"kick": 1.0, "clap": 1.0, "hat": 1.0, "ohat": 1.0, "bass": 1.0, "bass_dark": 0.0, "stab": 0.8, "arp": 1.0, "pad": 0.4},
    "drive":   {"kick": 0.9, "clap": 0.8, "hat": 0.8, "ohat": 0.7, "bass": 0.9, "bass_dark": 0.0, "stab": 0.55, "arp": 0.0, "pad": 0.35},
    "explain": {"kick": 0.55, "clap": 0.0, "hat": 0.5, "ohat": 0.0, "bass": 0.0, "bass_dark": 0.8, "stab": 0.0, "arp": 0.0, "pad": 0.55},
    "lift":    {"kick": 0.9, "clap": 0.7, "hat": 0.9, "ohat": 0.8, "bass": 0.9, "bass_dark": 0.0, "stab": 0.4, "arp": 0.9, "pad": 0.5},
    "drop":    {k: 0.0 for k in ("kick", "clap", "hat", "ohat", "bass", "bass_dark", "stab", "arp", "pad")},
    "ending":  {"kick": 0.0, "clap": 0.0, "hat": 0.25, "ohat": 0.0, "bass": 0.0, "bass_dark": 0.45, "stab": 0.0, "arp": 0.45, "pad": 0.9},
}
TECH_MODES.update(hook=TECH_MODES["intro"], banter=TECH_MODES["drive"], reveal=TECH_MODES["lift"])
# ドキュメンタリー向け（2026-10-27）：ambient＝パッドと低音だけの空間、pulse＝控えめな電子パルス、rise＝発見の瞬間のゆるやかな盛り上がり
TECH_MODES.update(
    ambient={"kick": 0.0, "clap": 0.0, "hat": 0.0, "ohat": 0.0, "bass": 0.0, "bass_dark": 0.55, "stab": 0.0, "arp": 0.0, "pad": 1.0},
    pulse={"kick": 0.35, "clap": 0.0, "hat": 0.2, "ohat": 0.0, "bass": 0.0, "bass_dark": 0.75, "stab": 0.0, "arp": 0.35, "pad": 0.85},
    rise={"kick": 0.6, "clap": 0.0, "hat": 0.35, "ohat": 0.15, "bass": 0.4, "bass_dark": 0.6, "stab": 0.0, "arp": 0.6, "pad": 1.0})


# ドキュメンタリー＋ビート（2026-10-27〜の標準）：静かすぎない。キックは解説中も止めない（密度で展開をつける）
#   doc_hook＝冒頭 1 拍目から全開（キック・ベース・金属音・うなり）、doc_drive＝解説の基本（ビート＋ベース、和音なし）、
#   doc_build＝発見へ向けて密度を上げる（アルペジオ・オープンハット）、doc_break＝一瞬の引き（キックを抜き、低音とハットで保つ）、
#   doc_peak＝核心（全パート）、doc_outro＝余韻（キックを残して薄く）
TECH_MODES.update(
    doc_hook={"kick": 1.0, "clap": 0.6, "hat": 0.8, "ohat": 0.5, "bass": 1.0, "bass_dark": 0.3, "stab": 0.5, "arp": 0.3, "pad": 0.6, "metal": 1.0, "rumble": 1.0},
    doc_drive={"kick": 0.85, "clap": 0.35, "hat": 0.6, "ohat": 0.3, "bass": 0.85, "bass_dark": 0.3, "stab": 0.0, "arp": 0.0, "pad": 0.45, "metal": 0.6, "rumble": 0.5},
    doc_build={"kick": 0.9, "clap": 0.5, "hat": 0.8, "ohat": 0.6, "bass": 0.9, "bass_dark": 0.2, "stab": 0.0, "arp": 0.5, "pad": 0.6, "metal": 0.8, "rumble": 0.7},
    doc_break={"kick": 0.0, "clap": 0.0, "hat": 0.45, "ohat": 0.0, "bass": 0.0, "bass_dark": 0.9, "stab": 0.0, "arp": 0.3, "pad": 0.9, "metal": 0.4, "rumble": 0.8},
    doc_peak={"kick": 1.0, "clap": 0.6, "hat": 0.9, "ohat": 0.7, "bass": 1.0, "bass_dark": 0.2, "stab": 0.35, "arp": 0.5, "pad": 0.7, "metal": 0.9, "rumble": 0.8},
    doc_outro={"kick": 0.6, "clap": 0.0, "hat": 0.4, "ohat": 0.0, "bass": 0.4, "bass_dark": 0.5, "stab": 0.0, "arp": 0.35, "pad": 0.9, "metal": 0.3, "rumble": 0.5})
# 物語の感情に合わせるモード（2026-10-28〜、標準ルール v3。pilot_012 で導入）
#   doc_tense＝不安と緊張（低音中心、控えめなキック、冷たいパルス）、doc_hope＝努力が実る瞬間（短調の低音と和音を抜き、
#   長調の和音・やわらかい鍵盤・温かい低音が約 1.6 秒かけて差し込む。ビートは残す）、doc_alone＝対立と孤独（希望の音を引き、音数を減らす）、
#   doc_warm＝現代の日常への静かな感動（温かい和音＋穏やかなビート）、doc_warm_end＝最後の一文（さらに薄く、余韻）
TECH_MODES.update(
    doc_tense={"kick": 0.75, "clap": 0.0, "hat": 0.35, "ohat": 0.0, "bass": 0.5, "bass_dark": 0.7, "stab": 0.0, "arp": 0.15, "pad": 0.5, "metal": 0.3, "rumble": 0.9},
    doc_hope={"kick": 0.8, "clap": 0.35, "hat": 0.55, "ohat": 0.35, "bass": 0.0, "bass_dark": 0.0, "stab": 0.0, "arp": 0.0, "pad": 0.0, "metal": 0.2, "rumble": 0.25,
              "wbass": 0.9, "wpad": 1.0, "keys": 0.8},
    doc_alone={"kick": 0.35, "clap": 0.0, "hat": 0.25, "ohat": 0.0, "bass": 0.0, "bass_dark": 0.85, "stab": 0.0, "arp": 0.0, "pad": 0.75, "metal": 0.15, "rumble": 0.6},
    doc_warm={"kick": 0.6, "clap": 0.2, "hat": 0.4, "ohat": 0.15, "bass": 0.0, "bass_dark": 0.0, "stab": 0.0, "arp": 0.0, "pad": 0.0, "metal": 0.1, "rumble": 0.15,
              "wbass": 0.7, "wpad": 0.9, "keys": 0.65},
    doc_warm_end={"kick": 0.3, "clap": 0.0, "hat": 0.25, "ohat": 0.0, "bass": 0.0, "bass_dark": 0.0, "stab": 0.0, "arp": 0.0, "pad": 0.0, "metal": 0.0, "rumble": 0.1,
                  "wbass": 0.5, "wpad": 0.85, "keys": 0.45})
WARM_PARTS = ("wbass", "wpad", "keys")   # 切り替えをゆっくり（約 1.6 秒）にするパート：希望が少しずつ差し込むように


def _metal(dur=0.12, seed=51):
    """金属的な打音（インダストリアル）：短いノイズを、倍音の合わない複数の共鳴で鳴らす。高すぎない帯域（〜3 kHz）"""
    t = np.arange(int(dur * SR)) / SR
    x = _noise(len(t), seed) * np.exp(-t / 0.004) * 0.6
    for f, a in ((523, .5), (1187, .35), (1771, .25), (2639, .15)):
        x += a * np.sin(2 * np.pi * f * t + seed) * np.exp(-t / 0.035)
    return _lp(x, 3500) * 0.5


def _supersaw(f, dur, amp, n=5, spread=0.012, attack=0.004, decay=0.25, seed=0):
    t = np.arange(int(dur * SR)) / SR
    r = np.random.default_rng(seed)
    x = np.zeros_like(t)
    for i in range(n):
        d = 1 + spread * (i - (n - 1) / 2) / ((n - 1) / 2)
        ph = (f * d * t + r.random()) % 1.0
        x += 2 * ph - 1
    env = np.minimum(1, t / attack) * np.exp(-t / decay)
    return amp * x / n * env


def _kick_hard(dur=0.4):
    t = np.arange(int(dur * SR)) / SR
    f = 46 + 130 * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    click = _noise(len(t), 31) * np.exp(-t / 0.002) * 0.5
    return np.tanh(1.6 * (body + click)) * 0.85


def _smooth(g, ker):
    """長い窓の移動平均（FFT）。np.convolve だと 1.6 秒の窓で遅すぎるため"""
    L = 1 << (len(g) + len(ker)).bit_length()
    y = np.fft.irfft(np.fft.rfft(g, L) * np.fft.rfft(ker, L), L)
    s = len(ker) // 2
    return y[s:s + len(g)]


def bgm_techno(total, sections, style="tech_air"):
    st = TECH_STYLES[style]
    beat = 60 / st["bpm"]
    n = int(total * SR)
    names = ("kick", "clap", "hat", "ohat", "bass", "stab", "arp", "pad", "metal", "rumble")
    P = {k: np.zeros(n) for k in names}
    warm = any(TECH_MODES[m].get(k, 0) for _, m in sections for k in WARM_PARTS)   # 希望のパートを使う回だけ作る（旧回の処理は変えない）
    if warm:
        P.update({k: np.zeros(n) for k in WARM_PARTS})
    kick = _kick_hard()
    clap = _add(*[np.concatenate([np.zeros(int(d * SR)), _snare(0.18, 40 + i) * .7]) for i, d in enumerate((0, .008, .016))])
    hat, ohat = _hat(0.04, 41), _hat(open_=True, seed=42)
    nb = int(total / beat) + 2
    kicks = []

    def put(name, i, x, amp=1.0):
        if 0 <= i < n:
            m = min(len(x), n - i)
            P[name][i:i + m] += x[:m] * amp

    stab_pat = [0, 0.75, 1.5, 2.5, 3.25]          # 1 小節の中の和音の位置（拍）
    for b in range(nb):
        tb, (bar, pos) = b * beat, divmod(b, 4)
        root, tones = st["chords"][bar % 4]
        i = int(tb * SR)
        put("kick", i, kick); kicks.append(tb)
        if pos in (1, 3):
            put("clap", i, clap)
        for s16 in range(4):                       # 16 分のハイハット（強弱をつける）
            put("hat", int((tb + s16 * beat / 4) * SR), hat, (0.55, 0.3, 0.8, 0.35)[s16])
        put("ohat", int((tb + beat / 2) * SR), ohat, 0.7)
        for s16, a in ((3, 0.8), (6, 0.5), (11, 0.9), (14, 0.6)):   # 金属音：小節の中の決まった 16 分（2 拍で 1 周より長い、うねるパターン）
            if (b % 4) * 4 <= s16 < (b % 4) * 4 + 4:
                put("metal", int((tb + (s16 % 4) * beat / 4) * SR), _metal(seed=51 + s16), a)
        put("rumble", i, _lp(_noise(int(beat * SR), 60 + b % 8), 140) * np.exp(-np.arange(int(beat * SR)) / SR / 0.25) * 1.8)  # キックに続く低いうなり
        for s16 in (1, 2, 3):                      # 裏の 16 分で転がるベース（キックの位置は空ける）
            f = root * (2 if s16 == 2 else 1)
            _note(P["bass"], int((tb + s16 * beat / 4) * SR), f, beat * 0.22, 0.5, "saw", attack=0.002, decay=0.07)
        for s16 in range(4):                       # 16 分のアルペジオ（1 オクターブ上）
            f = tones[(b * 4 + s16) % 3] * (2 if (b // 2) % 2 else 1)
            _note(P["arp"], int((tb + s16 * beat / 4) * SR), f, beat * 0.2, 0.06, "square", attack=0.002, decay=0.045)
        if pos == 0:
            for sp in stab_pat:                    # 硬いシンセの和音
                j = int((tb + sp * beat) * SR)
                for k_, f in enumerate(tones):
                    x = _supersaw(f / 2, beat * 0.4, 0.09, decay=0.11, seed=b + k_)
                    put("stab", j, x)
            for f in tones:                        # パッド（長く、うねる）
                put("pad", i, _supersaw(f / 2, beat * 4.1, 0.05, n=5, spread=.008, attack=.3, decay=3.0, seed=bar))
        if warm:
            wroot, wtones = WARM_CHORDS[bar % 4]
            if pos in (0, 2):                      # 温かい低音：2 拍ずつ伸ばす正弦波（転がさない）
                _note(P["wbass"], i, wroot * 2, beat * 1.9, 0.5, "sin", attack=0.02, decay=0.9)
            if pos == 0:
                for k_, f in enumerate(wtones):    # 長調のパッド：ゆっくり立ち上がる、角の取れた音
                    put("wpad", i, _supersaw(f / 2, beat * 4.1, 0.05, n=3, spread=.004, attack=.6, decay=4.0, seed=200 + bar + k_))
            for s8 in range(2):                    # やわらかい鍵盤：8 分の分散和音（ベルに近い音色、減衰は長め）
                f = wtones[(b * 2 + s8) % 3] * (1 if (b // 4) % 2 else 0.5) * 2
                put("keys", int((tb + s8 * beat / 2) * SR), _bell(f, beat * 1.2, 0.12, 0.35, attack=0.01))
    if warm:
        P["wbass"] = _lp(P["wbass"], 300)
        P["wpad"] = _lp(_lp(P["wpad"], 1200), 1200)
        P["keys"] = _lp(P["keys"], 2500)
    P["bass"] = _lp(P["bass"], 700)
    P["bass_dark"] = _lp(P["bass"], 260)
    P["stab"] = _lp(P["stab"], 3200)
    P["arp"] = _lp(P["arp"], 4200)
    P["pad"] = _lp(P["pad"], 1800)
    # サイドチェイン：キックのたびにベース・和音・パッドを一瞬下げる（うねり）
    t = np.arange(n) / SR
    sc = np.ones(n)
    for kt in kicks:
        a = int(kt * SR)
        if a >= n:
            break
        m = min(n - a, int(beat * SR))
        sc[a:a + m] = np.minimum(sc[a:a + m], 1 - 0.65 * np.exp(-np.arange(m) / SR / 0.11))
    for k in ("bass", "bass_dark", "stab", "pad"):
        P[k] *= sc
    if warm:                                        # 希望のパートは浅めのサイドチェイン（うねりは残し、やわらかく）
        for k in WARM_PARTS:
            P[k] *= 1 - 0.5 * (1 - sc)
    gains = {k: np.zeros(n) for k in P}
    sec = sorted(sections) + [(total + 1, None)]
    for (a, mode), (b, _) in zip(sec, sec[1:]):
        ia, ib = max(0, int(a * SR)), min(n, int(b * SR))
        for k in P:
            gains[k][ia:ib] = TECH_MODES[mode].get(k, 0.0)   # metal・rumble は doc_ モードだけ（旧モードでは鳴らない）
    ker = np.ones(int(0.05 * SR)) / int(0.05 * SR)  # 切り替えは短く（急な展開に合わせる）
    ker_warm = np.ones(int(1.6 * SR)) / int(1.6 * SR)   # 希望のパートは約 1.6 秒かけて差し込む・引く
    level = {"kick": 0.62, "clap": 0.3, "hat": 0.2, "ohat": 0.14, "bass": 0.42, "bass_dark": 0.5, "stab": 0.55, "arp": 0.4, "pad": 0.5,
             "metal": 0.32, "rumble": 0.35, "wbass": 0.45, "wpad": 0.55, "keys": 0.3}
    mix, out = np.zeros(n), {}
    for k, x in P.items():
        g = _smooth(gains[k], ker_warm) if k in WARM_PARTS else np.convolve(gains[k], ker, mode="same")
        out[k] = x * g * level[k]
        mix += out[k]
    mix = np.tanh(1.3 * mix) / 1.3                  # 軽いサチュレーションで硬く
    fade = np.clip(t / 0.01, 0, 1) * np.clip((total - t) / 1.2, 0, 1)
    return mix * fade, out


def sfx_bank_techno():
    t = lambda d: np.arange(int(d * SR)) / SR
    boom_f = 60 * np.exp(-t(0.9) / 0.5) + 34
    boom = np.sin(2 * np.pi * np.cumsum(boom_f) / SR) * np.exp(-t(0.9) / 0.35)
    crack = _noise(int(0.12 * SR), 51); crack = (crack - _lp(crack, 2500)) * np.exp(-t(0.12) / 0.02)
    impact = np.tanh(2 * _add(boom * 0.9, crack * 0.5, _kick_hard(0.4) * 0.7)) * 0.8
    tape = np.sin(2 * np.pi * np.cumsum(440 * (1 - t(0.45) / 0.45) ** 2 + 20) / SR) * (1 - t(0.45) / 0.45) * 0.3
    alarm = np.concatenate([np.sign(np.sin(2 * np.pi * f * t(0.16))) * 0.16 for f in (988, 740, 988, 740)])
    zap_f = 2400 * np.exp(-t(0.12) / 0.025) + 180
    zap = np.sin(2 * np.pi * np.cumsum(zap_f) / SR) * np.exp(-t(0.12) / 0.05) * 0.3
    blips = _add(*[np.concatenate([np.zeros(int(k * 0.045 * SR)), _tone(f, 0.12, 0.16, 0.05) + 0.4 * np.sign(_tone(f, 0.12, 0.16, 0.05))])
                   for k, f in enumerate([880, 1175, 1480, 1976])])
    rev = _noise(int(0.7 * SR), 53); rev = (rev - _lp(rev, 3000)) * (t(0.7) / 0.7) ** 3 * 0.45
    stab = _add(*[_supersaw(f, 0.5, 0.2, decay=0.16, seed=i) for i, f in enumerate((220.0, 261.63, 329.63, 440.0))], _kick_hard(0.3) * 0.6)
    g = np.zeros(int(0.5 * SR)); r = np.random.default_rng(55)
    for k in range(14):
        i = int(r.uniform(0, 0.45) * SR); m = int(r.uniform(0.008, 0.04) * SR)
        g[i:i + m] += np.round(np.sin(2 * np.pi * r.uniform(150, 2500) * np.arange(m) / SR) * 3) / 3 * 0.28
    return {
        "impact": impact,                                      # 衝撃：低音と鋭いアタック
        "sweep_up": _noise_sweep(0.5, 300, 7000, 0.45, 57),    # 急接近
        "sweep_down": _noise_sweep(0.5, 7000, 300, 0.4, 58),
        "glitch": g,                                           # デジタル空間
        "brake": _add(tape, _noise_sweep(0.3, 3000, 200, 0.2, 59)),  # 急停止（テープストップ）
        "discover": _add(blips, _tone(2637, 0.6, 0.08, 0.25)),  # 発見
        "zap": zap,                                            # ウラの鋭いツッコミ（短い電子音）
        "stab": stab,                                          # オチの和音
        "revswell": rev,                                       # オチ前の吸い込み
        "alarm": alarm,                                        # 警告音（窓の冒頭）
        "rewind": _add(_sweep(0.9, 1400, 150, 0.22, "saw", 0.6), _noise_sweep(0.9, 6000, 300, 0.25, 9)),
        "scan": _sweep(0.6, 500, 2400, 0.14, "saw", 1.0),
        "ok": _add(_tone(1046.5, 0.1, 0.22, 0.05), np.concatenate([np.zeros(int(0.09 * SR)), _tone(1568, 0.25, 0.22, 0.08)])),
        "error": _add(*[np.concatenate([np.zeros(int(k * 0.14 * SR)), np.sign(np.sin(2 * np.pi * 110 * t(0.1))) * 0.18 * np.exp(-t(0.1) / 0.08)])
                        for k in range(2)]),
        "riser": _noise_sweep(1.0, 300, 8000, 0.32, 13) * np.linspace(0.15, 1, int(1.0 * SR)),
        "tick": _add(_tone(1760, 0.06, 0.18, 0.015), _tone(3520, 0.04, 0.05, 0.01)),
        "cash": _add(_tone(2093, 0.5, 0.18, 0.18), _tone(2637, 0.4, 0.12, 0.15), _noise(int(0.06 * SR), 17) * np.exp(-t(0.06) / 0.015) * 0.18),
        "rain": _add(*[np.concatenate([np.zeros(int(k * 0.06 * SR)), np.sign(_tone(f, 0.05, 0.1, 0.02)) * 0.08])
                       for k, f in enumerate([1200, 900, 1500, 1100, 1700, 1000, 1400, 1250])]),
    }


# ---------------------------------------------------------------- やわらかい効果音（2026-10-26、PHP の回から）
# sfx_bank_techno の名前はそのままに、耳に刺さる原因を音色から取り除いた版。
# - 矩形波（アラーム・エラー）、2 kHz を超える電子音（ザップ・チック・発見音）、7〜8 kHz まで上がるノイズのスウィープをやめる
# - 驚き・注意は低音寄りの短いヒット、決めは柔らかいデジタル音（正弦波＋ゆっくりした立ち上がり）、切り替えは 2.5 kHz までのスウッシュ
# - 仕上げに 4.5 kHz のローパスを 2 回かけ、音ごとの大きさ（RMS）をそろえる
def _bell(f, dur, amp, decay, attack=0.006):
    """柔らかいベル（基音＋弱い 2 倍音）。立ち上がりを丸めてクリック音を出さない。"""
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t / decay) * np.minimum(1, t / attack)
    return amp * env * (np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t) * np.exp(-t / (decay * 0.4)))


def _swoosh(dur, f0, f1, amp, seed):
    """空気が動くようなスウッシュ（ノイズを帯域で絞り、山型の音量にする）。"""
    n = int(dur * SR)
    x = _noise(n, seed)
    k = np.linspace(0, 1, n)
    lo, hi = _lp(x, min(f0, f1) * 0.5), _lp(x, max(f0, f1))
    band = hi - lo
    y = _lp(band, f0) * (1 - k) + _lp(band, f1) * k
    env = np.sin(np.pi * k) ** 1.6
    return amp * y / (np.max(np.abs(y)) + 1e-9) * env


def _soften(x, cut=4500, rms=0.06):
    y = _lp(_lp(x, cut), cut)
    n = int(0.004 * SR)  # 出だしと終わりを 4 ms でなめらかに
    if len(y) > 2 * n:
        y[:n] *= np.linspace(0, 1, n); y[-n:] *= np.linspace(1, 0, n)
    w = max(1, int(0.25 * SR))  # いちばん大きい 0.25 秒の RMS でそろえる（立ち上がる音も正しく測る）
    c = np.concatenate([[0], np.cumsum(y ** 2)])
    r = np.sqrt(np.max(c[w:] - c[:-w]) / w) if len(y) > w else np.sqrt(np.mean(y ** 2))
    y = y * (rms / (r + 1e-9))
    return np.clip(y, -0.5, 0.5)


def sfx_bank_soft():
    t = lambda d: np.arange(int(d * SR)) / SR
    boom_f = 70 * np.exp(-t(0.7) / 0.18) + 42
    boom = np.sin(2 * np.pi * np.cumsum(boom_f) / SR) * np.exp(-t(0.7) / 0.22) * np.minimum(1, t(0.7) / 0.004)
    thud = _lp(_noise(int(0.08 * SR), 61), 900) * np.exp(-t(0.08) / 0.015)
    impact = np.tanh(1.4 * _add(boom, thud * 2.0))                          # 低い「ドン」（鋭いアタックなし）
    hit = _add(np.sin(2 * np.pi * np.cumsum(140 * np.exp(-t(0.25) / 0.05) + 70) / SR) * np.exp(-t(0.25) / 0.07),
               _bell(392, 0.25, 0.25, 0.06))                                # 短いヒット（注意：警告音の代わり）
    bop = np.sin(2 * np.pi * np.cumsum(520 * np.exp(-t(0.16) / 0.04) + 180) / SR) * np.exp(-t(0.16) / 0.06) * np.minimum(1, t(0.16) / 0.008)
    pops = np.zeros(int(0.4 * SR)); r = np.random.default_rng(65)
    for k in range(6):                                                      # 低いデジタルのぷつぷつ（グリッチの代わり）
        i = int(r.uniform(0, 0.33) * SR); f = r.uniform(180, 520)
        pops[i:i + int(0.05 * SR)] += _bell(f, 0.05, 0.5, 0.015)[: len(pops) - i]
    chord = _add(*[_bell(f, 0.9, 0.22, 0.35, 0.01) for f in (220.0, 277.18, 329.63, 440.0)], _kick_hard(0.3) * 0.35)
    tape = np.sin(2 * np.pi * np.cumsum(260 * (1 - t(0.45) / 0.45) ** 2 + 30) / SR) * (1 - t(0.45) / 0.45)
    bank = {
        "impact": impact,
        "hit": hit,
        "sweep_up": _swoosh(0.45, 300, 2200, 1.0, 67),                     # スウッシュ（切り替え）
        "sweep_down": _swoosh(0.45, 2200, 300, 1.0, 68),
        "glitch": pops,
        "brake": tape,
        "discover": _add(_bell(523.25, 0.5, 0.3, 0.16), np.concatenate([np.zeros(int(0.08 * SR)), _bell(783.99, 0.6, 0.3, 0.2)])),
        "zap": bop,                                                         # ウラの決め：柔らかい「ポン」
        "stab": chord,
        "revswell": _lp(_noise(int(0.7 * SR), 69), 1400) * (t(0.7) / 0.7) ** 3,
        "alarm": _add(hit, np.concatenate([np.zeros(int(0.22 * SR)), hit * 0.7])),  # 二度打ちの低いヒット
        "rewind": _add(_sweep(0.9, 700, 120, 0.3, "sin", 0.6), _swoosh(0.9, 2000, 300, 0.4, 70)),
        "scan": _sweep(0.5, 300, 700, 0.5, "sin", 1.0),
        "ok": _add(_bell(659.25, 0.3, 0.3, 0.09), np.concatenate([np.zeros(int(0.08 * SR)), _bell(987.77, 0.4, 0.26, 0.12)])),
        "error": _add(_bell(196, 0.22, 0.5, 0.07), np.concatenate([np.zeros(int(0.13 * SR)), _bell(164.81, 0.25, 0.5, 0.08)])),
        "riser": _swoosh(1.0, 250, 2000, 1.0, 71) * np.linspace(0.2, 1, int(1.0 * SR)),
        "tick": _add(_bell(880, 0.05, 0.4, 0.008, 0.002), _lp(_noise(int(0.02 * SR), 73), 1800) * np.exp(-t(0.02) / 0.004) * 0.6),
        "cash": _add(_bell(1046.5, 0.4, 0.25, 0.14), _bell(1318.5, 0.35, 0.18, 0.12)),
        "rain": _add(*[np.concatenate([np.zeros(int(k * 0.06 * SR)), _bell(f, 0.05, 0.3, 0.015)]) for k, f in enumerate([600, 450, 750, 550, 850, 500])]),
    }
    # 自然の音（ドキュメンタリー向け）：波・風・草のそよぎ・小さな足音
    n6 = _noise(int(6 * SR), 81)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t(6) / 3.0 - np.pi / 2) ** 2
    bank["waves"] = _lp(n6 - _lp(n6, 120), 900) * swell * np.sin(np.pi * t(6) / 6) ** 0.3
    n4 = _noise(int(4 * SR), 82)
    bank["wind"] = (_lp(n4, 700) - _lp(n4, 180)) * (0.6 + 0.4 * np.sin(2 * np.pi * t(4) / 2.7)) * np.sin(np.pi * t(4) / 4) ** 0.5
    n1 = _noise(int(0.6 * SR), 83)
    bank["rustle"] = (_lp(n1, 1500) - _lp(n1, 400)) * np.sin(np.pi * t(0.6) / 0.6) ** 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t(0.6)))
    bank["step"] = _add(*[np.concatenate([np.zeros(int(k * 0.11 * SR)), _bell(330 - 40 * k, 0.04, 0.4, 0.008, 0.002)]) for k in range(4)])
    bank["deep"] = _add(np.sin(2 * np.pi * np.cumsum(55 * np.exp(-t(1.6) / 1.2) + 28) / SR) * np.exp(-t(1.6) / 0.7) * np.minimum(1, t(1.6) / 0.05),
                        _lp(_noise(int(1.6 * SR), 84), 400) * np.exp(-t(1.6) / 0.4) * 0.3)   # 空間の広がりを感じる低い音
    # 紙と機械の音（pilot_011〜）：紙を折る・切る、機械が動き出す、歯車、紙を広げる、静かな部屋。高い帯域は丸める
    n5 = _noise(int(0.5 * SR), 91)
    crk = np.zeros(int(0.5 * SR)); r2 = np.random.default_rng(92)
    for k in range(9):                                                      # 紙のかさかさ（短い粒）
        i = int(r2.uniform(0, 0.42) * SR); m = int(0.03 * SR)
        crk[i:i + m] += (_lp(_noise(m, 93 + k), 3200) - _lp(_noise(m, 93 + k), 700)) * np.exp(-np.arange(m) / SR / 0.008)
    bank["paper"] = _add(crk, (_lp(n5, 2400) - _lp(n5, 500)) * np.sin(np.pi * t(0.5) / 0.5) ** 2 * 0.3)
    sn = _noise(int(0.18 * SR), 95)
    bank["cut"] = _add((_lp(sn, 3000) - _lp(sn, 900)) * np.sin(np.pi * t(0.18) / 0.18) ** 3,
                       np.concatenate([np.zeros(int(0.14 * SR)), _bell(620, 0.06, 0.3, 0.012, 0.002)]))
    mf = 38 + 40 * np.clip(t(2.2) / 1.6, 0, 1) ** 1.5                       # 機械が動き出す：低いうなりが上がり、規則的な打音が加わる
    motor = np.sin(2 * np.pi * np.cumsum(mf) / SR) * np.minimum(1, t(2.2) / 0.3) * 0.6
    clk = np.zeros(int(2.2 * SR))
    for k, tt in enumerate(np.cumsum(0.42 * 0.82 ** np.arange(12))):
        i = int((0.5 + tt) * SR)
        if i < len(clk) - int(0.04 * SR):
            clk[i:i + int(0.04 * SR)] += _lp(_noise(int(0.04 * SR), 96 + k), 1500) * np.exp(-np.arange(int(0.04 * SR)) / SR / 0.006)
    bank["machine"] = _add(motor, clk * 0.8) * np.minimum(1, (2.2 - t(2.2)) / 0.3)
    g = np.zeros(int(1.6 * SR))
    for k in range(8):                                                      # 歯車がかみ合う：低めの「カチ」が一定の間隔で
        i = int(k * 0.2 * SR); m = int(0.035 * SR)
        g[i:i + m] += _add(_lp(_noise(m, 110 + k), 1800) * np.exp(-np.arange(m) / SR / 0.005), _bell(240 + 30 * (k % 2), 0.035, 0.4, 0.01, 0.001))
    bank["gear"] = g
    nu = _noise(int(0.7 * SR), 120)
    bank["unroll"] = _lp(nu, 1600) * np.sin(np.pi * t(0.7) / 0.7) ** 1.5 * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t(0.7)))   # 設計図を机に広げる
    nr = _noise(int(5 * SR), 121)
    bank["room"] = _lp(nr, 350) * np.sin(np.pi * t(5) / 5) ** 0.4          # 静かな部屋の空気
    lm = np.zeros(int(3 * SR))
    for k in range(12):                                                     # 織機の規則的な音（遠く、低く）
        i = int(k * 0.25 * SR); m = int(0.06 * SR)
        lm[i:i + m] += _lp(_noise(m, 130 + k), 900) * np.exp(-np.arange(m) / SR / 0.012) * (1.0 if k % 2 == 0 else 0.6)
    bank["loom"] = lm
    # 水と光の音（pilot_012〜）：手を洗う水（低めの流れ＋小さなしずく）、希望が差し込む瞬間のやわらかい長調の和音
    nw = _noise(int(1.4 * SR), 140)
    flow = (_lp(nw, 1400) - _lp(nw, 250)) * np.sin(np.pi * t(1.4) / 1.4) ** 1.2 * (0.7 + 0.3 * np.sin(2 * np.pi * 5.3 * t(1.4)))
    drops = np.zeros(int(1.4 * SR)); r3 = np.random.default_rng(141)
    for k in range(10):
        i = int(r3.uniform(0.05, 1.25) * SR); f0 = r3.uniform(300, 620)
        d = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.6 * np.exp(-t(0.06) / 0.015))) / SR) * np.exp(-t(0.06) / 0.018)
        drops[i:i + len(d)] += d[: len(drops) - i] * 0.35
    bank["water"] = _add(flow, drops)
    bank["glow"] = _add(*[np.concatenate([np.zeros(int(k * 0.07 * SR)), _bell(f, 1.8, 0.2, 0.7, 0.05)]) for k, f in enumerate((174.61, 220.0, 261.63, 349.23))])
    level = {"waves": 0.05, "wind": 0.04, "rustle": 0.035, "step": 0.03, "deep": 0.09, "water": 0.04, "glow": 0.05,
             "paper": 0.04, "cut": 0.04, "machine": 0.06, "gear": 0.035, "unroll": 0.035, "room": 0.02, "loom": 0.04,
             "impact": 0.11, "hit": 0.08, "alarm": 0.08, "stab": 0.08, "brake": 0.06, "rewind": 0.06, "revswell": 0.05,
             "sweep_up": 0.045, "sweep_down": 0.045, "riser": 0.04, "tick": 0.05, "scan": 0.04}
    return {k: _soften(v, rms=level.get(k, 0.06)) for k, v in bank.items()}
