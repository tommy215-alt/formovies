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
