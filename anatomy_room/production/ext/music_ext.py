"""テンプレートの外に足す音の部品（2026-10-29〜、pilot_015 の修正事項。案 A：production/common/music.py は変えない）。

各話の production_script.py で `import music_ext` すると、その回の処理の中だけで次が使えるようになる：
- BGM の曲調 "warm_drive"（124 BPM。安心して聴けるテクノ：長調の和音、丸いキック、やわらかいベース、エレクトリックピアノ、パッド。
  金属的な打音と低いうなりは使わない）。モード（場面の感情）は WARM_MODES。
- 効果音（sfx_bank "soft" に足す）：title・stamp・zoom・tagpop・data・typer・shimmer・prism・ship・flip・bloom・whoosh・ring。
music.TECH_STYLES に登録し、music.bgm_techno と music.sfx_bank_soft を包む（ほかの曲調・効果音の音は変わらない）。
"""
import numpy as np

import music
from music import SR, _add, _bell, _lp, _noise, _note, _smooth, _soften, _supersaw, _sweep, _swoosh

# 和音（ルート, 構成音）の 4 小節ループ。明るい進行（ニ長調 D–A–Bm–G）と、陰る進行（Bm–G–Em–F#m：短調に寄せすぎない）
WARM_STYLES = {
    "warm_drive": {"bpm": 124, "seed": 15,
                   "chords": [(73.42, [293.66, 369.99, 440.00]), (55.00, [277.18, 329.63, 440.00]),
                              (61.74, [293.66, 369.99, 493.88]), (49.00, [293.66, 392.00, 493.88])],
                   "shade": [(61.74, [293.66, 369.99, 493.88]), (49.00, [293.66, 392.00, 493.88]),
                             (41.20, [329.63, 392.00, 493.88]), (46.25, [277.18, 369.99, 440.00])]},
}
# モード → パートの音量。b＝明るい進行、s＝陰る進行（切り替えは 0.8 秒かけてなめらかに）
_P = ("kick", "rim", "shaker", "bass_b", "bass_s", "ep_b", "ep_s", "pad_b", "pad_s", "arp", "swell")
def _m(**kw):
    return {k: kw.get(k, 0.0) for k in _P}
WARM_MODES = {
    "w_hook":     _m(kick=0.85, rim=0.25, shaker=0.35, bass_b=0.7, ep_b=0.45, pad_b=0.8, swell=1.0),   # 冒頭：1 拍目から存在感、謎と期待
    "w_story":    _m(kick=0.6, rim=0.3, shaker=0.45, bass_b=0.6, ep_b=0.6, pad_b=0.5),                # 背景の説明：穏やかに進む
    "w_focus":    _m(kick=0.7, rim=0.4, shaker=0.6, bass_b=0.7, ep_b=0.45, pad_b=0.4, arp=0.35),      # 方法・集中：少し密度を上げる
    "w_discover": _m(kick=0.85, rim=0.5, shaker=0.7, bass_b=0.85, ep_b=0.8, pad_b=0.85, arp=0.7, swell=0.6),   # 発見：明るく開く
    "w_shade":    _m(kick=0.4, shaker=0.3, bass_s=0.6, ep_s=0.55, pad_s=0.7),                         # 壁：少し陰る（怖くしない）
    "w_hold":     _m(pad_s=0.85, ep_s=0.3),                                                          # 間：ビートを抜く（短く）
    "w_rise":     _m(kick=0.75, rim=0.4, shaker=0.55, bass_b=0.75, ep_b=0.7, pad_b=0.7, arp=0.4),      # 再評価：前へ進む
    "w_warm":     _m(kick=0.55, shaker=0.4, bass_b=0.6, ep_b=0.65, pad_b=0.85, arp=0.3),              # 現代：安心と余韻
    "w_end":      _m(kick=0.25, shaker=0.2, ep_b=0.4, pad_b=0.8),                                    # 最後の一文
    "ending":     _m(shaker=0.2, ep_b=0.45, pad_b=0.8),
}
_MELODIC = ("bass_b", "bass_s", "ep_b", "ep_s", "pad_b", "pad_s", "arp", "swell")


def _soft_kick(dur=0.36):
    """丸いキック：低い正弦波が下がるだけ（硬いクリックなし）"""
    t = np.arange(int(dur * SR)) / SR
    f = 48 + 75 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2) * np.minimum(1, t / 0.003) * 0.9


def _ep(f, dur, amp, decay=0.7):
    """エレクトリックピアノに近い音：基音＋弱い倍音（ゆっくり減衰）、立ち上がりは丸める"""
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t / decay) * np.minimum(1, t / 0.006)
    return amp * env * (np.sin(2 * np.pi * f * t) + 0.28 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.18) + 0.08 * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.08))


def bgm_warm(total, sections, style="warm_drive"):
    st = WARM_STYLES[style]
    beat = 60 / st["bpm"]
    n = int(total * SR)
    P = {k: np.zeros(n) for k in _P}
    kick = _soft_kick()
    rim = _add(_bell(330, 0.08, 0.5, 0.025, 0.002), _lp(_noise(int(0.05 * SR), 301), 1800) * np.exp(-np.arange(int(0.05 * SR)) / SR / 0.01) * 0.5)
    shk = [(_lp(_noise(int(0.05 * SR), 310 + i), 5000) - _lp(_noise(int(0.05 * SR), 310 + i), 1800)) * np.exp(-np.arange(int(0.05 * SR)) / SR / 0.012) for i in range(4)]
    nb = int(total / beat) + 2
    kicks = []

    def put(name, i, x, amp=1.0):
        if 0 <= i < n:
            m = min(len(x), n - i)
            P[name][i:i + m] += x[:m] * amp

    ep_pat = [(0, 1.0), (1.5, 0.7), (2.5, 0.8), (3.5, 0.6)]    # 1 小節の中のエレピの位置（拍）と強さ：少し跳ねる
    for b in range(nb):
        tb, (bar, pos) = b * beat, divmod(b, 4)
        i = int(tb * SR)
        put("kick", i, kick); kicks.append(tb)
        if pos in (1, 3):
            put("rim", i, rim)
        for s16 in range(4):
            put("shaker", int((tb + s16 * beat / 4) * SR), shk[s16], (0.5, 0.25, 0.8, 0.3)[s16])
        for key, chords in (("b", st["chords"]), ("s", st["shade"])):
            root, tones = chords[bar % 4]
            for s8 in range(2):                                  # ベース：8 分で根音とオクターブ（転がしすぎない）
                f = root * (2 if (pos * 2 + s8) % 4 == 3 else 1) * 2
                _note(P["bass_" + key], int((tb + s8 * beat / 2) * SR), f, beat * 0.45, 0.5, "sin", attack=0.01, decay=0.22)
            if pos == 0:
                for sp, a in ep_pat:
                    j = int((tb + sp * beat) * SR)
                    for k_, f in enumerate(tones):
                        put("ep_" + key, j, _ep(f, beat * 1.6, 0.07 * a, decay=0.55 + 0.1 * k_))
                for k_, f in enumerate(tones):
                    put("pad_" + key, i, _supersaw(f / 2, beat * 4.1, 0.045, n=3, spread=.004, attack=.5, decay=4.0, seed=400 + bar + k_ + (50 if key == "s" else 0)))
        root, tones = st["chords"][bar % 4]
        for s8 in range(2):                                      # 明るいアルペジオ（8 分、やわらかいベル。発見の場面だけ）
            f = tones[(b * 2 + s8) % 3] * 2
            put("arp", int((tb + s8 * beat / 2) * SR), _bell(f, beat * 0.8, 0.08, 0.25, attack=0.008))
    # 冒頭の光が広がる音（swell）：4 小節かけて上がる空気の帯（w_hook・w_discover で鳴る）
    sw = _lp(_noise(n, 330), 1500) - _lp(_noise(n, 330), 300)
    P["swell"] = sw * (0.5 + 0.5 * np.sin(2 * np.pi * np.arange(n) / SR / (beat * 16) - np.pi / 2)) * 0.25
    for k in ("bass_b", "bass_s"):
        P[k] = _lp(P[k], 380)
    for k in ("ep_b", "ep_s"):
        P[k] = _lp(P[k], 2600)
    for k in ("pad_b", "pad_s"):
        P[k] = _lp(_lp(P[k], 1100), 1100)
    P["arp"] = _lp(P["arp"], 2400)
    # 浅いサイドチェイン：キックのたびにベースとパッドを少しだけ下げる（揺れは残し、硬くしない）
    t = np.arange(n) / SR
    sc = np.ones(n)
    for kt in kicks:
        a = int(kt * SR)
        if a >= n:
            break
        m = min(n - a, int(beat * SR))
        sc[a:a + m] = np.minimum(sc[a:a + m], 1 - 0.35 * np.exp(-np.arange(m) / SR / 0.1))
    for k in ("bass_b", "bass_s", "pad_b", "pad_s"):
        P[k] *= sc
    gains = {k: np.zeros(n) for k in P}
    sec = sorted(sections) + [(total + 1, None)]
    for (a, mode), (b, _) in zip(sec, sec[1:]):
        ia, ib = max(0, int(a * SR)), min(n, int(b * SR))
        for k in P:
            gains[k][ia:ib] = WARM_MODES[mode].get(k, 0.0)
    ker = np.ones(int(0.05 * SR)) / int(0.05 * SR)
    ker_m = np.ones(int(0.8 * SR)) / int(0.8 * SR)
    level = {"kick": 0.6, "rim": 0.22, "shaker": 0.16, "bass_b": 0.5, "bass_s": 0.5, "ep_b": 0.55, "ep_s": 0.55,
             "pad_b": 0.5, "pad_s": 0.5, "arp": 0.35, "swell": 0.3}
    mix, out = np.zeros(n), {}
    for k, x in P.items():
        g = _smooth(gains[k], ker_m) if k in _MELODIC else np.convolve(gains[k], ker, mode="same")
        out[k] = x * g * level[k]
        mix += out[k]
    mix = np.tanh(1.1 * mix) / 1.1
    fade = np.clip(t / 0.01, 0, 1) * np.clip((total - t) / 1.2, 0, 1)
    return mix * fade, out


def sfx_extra():
    t = lambda d: np.arange(int(d * SR)) / SR
    z = lambda d: np.zeros(int(d * SR))
    late = lambda d, x: np.concatenate([z(d), x])
    bank = {}
    # 冒頭の見出しが光とともに出る：低い一打＋空気の広がり＋長調の和音（明るく、刺さらない）
    boom = np.sin(2 * np.pi * np.cumsum(62 * np.exp(-t(1.6) / 0.25) + 38) / SR) * np.exp(-t(1.6) / 0.5) * np.minimum(1, t(1.6) / 0.004)
    bank["title"] = _add(boom * 1.2, _swoosh(1.6, 300, 1800, 0.35, 501) * np.linspace(1, 0.2, int(1.6 * SR)),
                         *[late(0.05 + k * 0.04, _bell(f, 1.5, 0.18, 0.7, 0.02)) for k, f in enumerate((146.83, 220.0, 293.66, 369.99))])
    # 判を押す：低くこもった「ドン」と、紙が鳴る短い音
    th = np.sin(2 * np.pi * np.cumsum(110 * np.exp(-t(0.3) / 0.03) + 60) / SR) * np.exp(-t(0.3) / 0.08)
    bank["stamp"] = _add(th * 1.3, _lp(_noise(int(0.12 * SR), 502), 1400) * np.exp(-t(0.12) / 0.02) * 0.8)
    # 寄る・拡大：上がる空気と、最後に小さな 2 音
    bank["zoom"] = _add(_swoosh(0.5, 300, 2200, 0.9, 503), late(0.42, _bell(523.25, 0.25, 0.25, 0.08)), late(0.48, _bell(659.25, 0.3, 0.2, 0.1)))
    # 札が付く：短く柔らかい 2 音
    bank["tagpop"] = _add(_bell(587.33, 0.12, 0.35, 0.04, 0.003), late(0.06, _bell(880.0, 0.16, 0.25, 0.05, 0.003)))
    # データの読み込み：低めの小さな音が並ぶ
    bank["data"] = _add(*[late(k * 0.055, _bell(f, 0.05, 0.3, 0.015, 0.002)) for k, f in enumerate((392, 440, 494, 523, 587, 659, 587))])
    # 手紙の文字が打たれる：低いカタカタ
    ty = z(0.9)
    for k in range(9):
        i = int((k * 0.095 + (0.02 if k % 3 == 1 else 0)) * SR); m = int(0.03 * SR)
        ty[i:i + m] += _lp(_noise(m, 520 + k), 1700) * np.exp(-np.arange(m) / SR / 0.005)
    bank["typer"] = ty
    # 光がほどける：やわらかいきらめき（高すぎない）
    r = np.random.default_rng(530); sh = z(1.4)
    for k in range(10):
        i = int(r.uniform(0, 1.0) * SR); f = r.choice([587.33, 659.25, 739.99, 880.0, 987.77])
        x = _bell(f, 0.4, 0.16, 0.16, 0.03); sh[i:i + len(x)] += x[: len(sh) - i]
    bank["shimmer"] = sh
    # プリズムで虹の帯に分かれる：上がる音ときらめき
    bank["prism"] = _add(_sweep(0.8, 220, 880, 0.3, "sin", 0.7) * np.sin(np.pi * t(0.8) / 0.8), late(0.3, sh[: int(1.1 * SR)] * 0.8))
    # 船の汽笛（遠く、低い）
    hf = 73.42
    horn = (np.sin(2 * np.pi * hf * t(1.6)) + 0.5 * np.sin(4 * np.pi * hf * t(1.6)) + 0.25 * np.sin(6 * np.pi * hf * t(1.6))) * np.sin(np.pi * t(1.6) / 1.6) ** 0.6
    bank["ship"] = _lp(horn, 500)
    # ページをめくる
    nf = _noise(int(0.3 * SR), 540)
    bank["flip"] = (_lp(nf, 2600) - _lp(nf, 500)) * np.sin(np.pi * t(0.3) / 0.3) ** 2 * (0.7 + 0.3 * np.sin(2 * np.pi * 22 * t(0.3)))
    # 発見の光が開く：逆回しのような高まりから、長調の和音へ
    bank["bloom"] = _add(_lp(_noise(int(0.6 * SR), 550), 1300) * (t(0.6) / 0.6) ** 3 * 0.8,
                         *[late(0.6 + k * 0.03, _bell(f, 1.6, 0.18, 0.7, 0.02)) for k, f in enumerate((293.66, 369.99, 440.0, 587.33))])
    # 場面転換：短い空気の音（sweep_up より低く、短い）
    bank["whoosh"] = _swoosh(0.35, 250, 1400, 1.0, 560)
    # 波紋のように広がる注目の輪
    bank["ring"] = _add(_bell(440, 0.6, 0.25, 0.25, 0.01), late(0.1, _bell(554.37, 0.6, 0.18, 0.25, 0.01)))
    level = {"title": 0.12, "stamp": 0.1, "zoom": 0.045, "tagpop": 0.04, "data": 0.035, "typer": 0.035, "shimmer": 0.03,
             "prism": 0.045, "ship": 0.05, "flip": 0.04, "bloom": 0.07, "whoosh": 0.04, "ring": 0.04}
    return {k: _soften(v, rms=level[k]) for k, v in bank.items()}


# ---------------------------------------------------------------- 登録（この回の処理の中だけ）
if not getattr(music, "_EXT_LOADED", False):
    music._EXT_LOADED = True
    music.TECH_STYLES.update({k: {"bpm": v["bpm"], "chords": v["chords"], "seed": v["seed"]} for k, v in WARM_STYLES.items()})
    _orig_techno, _orig_soft = music.bgm_techno, music.sfx_bank_soft

    def bgm_techno(total, sections, style="tech_air"):
        return bgm_warm(total, sections, style) if style in WARM_STYLES else _orig_techno(total, sections, style)

    def sfx_bank_soft():
        b = _orig_soft()
        b.update(sfx_extra())
        return b

    music.bgm_techno, music.sfx_bank_soft = bgm_techno, sfx_bank_soft
