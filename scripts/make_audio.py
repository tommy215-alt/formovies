"""Self-made score and sound design (pure numpy synthesis; no third-party samples).

Outputs (48 kHz stereo WAV):
  assets/audio/bgm.wav   — documentary-style score, follows the scene structure
  assets/audio/sfx.wav   — chalk, slates, whooshes, impacts, ambience
  assets/audio/mix.wav   — narration + ducked BGM + SFX, loudness-normalised
"""
import json, math, os, random, subprocess, sys, wave
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, "assets", "audio")
BOARDS = os.path.join(ROOT, "assets", "frames", "boards")
SR = 48000
TOTAL = 95.0
N = int(TOTAL * SR)
rng = np.random.default_rng(1)
SHOTS = {"A1": 0.0, "B2": 12.9, "C2": 26.3, "C3": 30.5, "D1": 40.2, "D5b": 65.9, "F1": 84.6}


def t_axis(n): return np.arange(n) / SR


def write(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(path, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def read(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        ch = w.getnchannels()
    return a.reshape(-1, ch).mean(1) if ch > 1 else a


def bandnoise(n, lo, hi):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)


def reverb(x, decay=2.5, mix=0.3, predelay=0.02):
    """Convolution with synthetic exponentially decaying noise (stereo decorrelated)."""
    n = int(decay * SR)
    t = t_axis(n)
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-6.9 * t / decay)
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        ir /= np.sqrt(np.sum(ir ** 2))
        X = np.fft.rfft(x, len(x) + len(ir)); H = np.fft.rfft(ir, len(x) + len(ir))
        out.append(np.fft.irfft(X * H)[:len(x)])
    wet = np.stack(out, 1)
    dry = np.stack([x, x], 1) if x.ndim == 1 else x
    return dry * (1 - mix) + wet * mix


def env_adsr(n, a=0.01, d=0.2, s=0.6, r=0.5, hold=None):
    hold = hold if hold is not None else n / SR - a - d - r
    seg = [np.linspace(0, 1, max(1, int(a * SR))), np.linspace(1, s, max(1, int(d * SR))),
           np.full(max(0, int(hold * SR)), s), np.linspace(s, 0, max(1, int(r * SR)))]
    e = np.concatenate(seg)
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def note_hz(name):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11, "Bb": 10, "Eb": 3}
    p, o = name[:-1], int(name[-1])
    return 440 * 2 ** ((names[p] + 12 * (o + 1) - 69) / 12)


CHORDS = {"Dm": ["D3", "A3", "D4", "F4", "A4"], "Bb": ["Bb2", "F3", "D4", "F4", "Bb4"], "F": ["F2", "C3", "F3", "A3", "C5"],
          "C": ["C3", "G3", "E4", "G4", "C5"], "Gm": ["G2", "D3", "G3", "Bb3", "D4"], "A": ["A2", "E3", "C#4", "E4", "A4"],
          "Fmaj7": ["F2", "C3", "E4", "A4", "C5"], "Bbmaj7": ["Bb2", "F3", "A3", "D4", "F4"]}


def pad(chord, dur, bright=0.5, amp=0.12):
    n = int(dur * SR); t = t_axis(n); y = np.zeros(n)
    for i, nm in enumerate(CHORDS[chord]):
        f = note_hz(nm)
        for det in (-0.12, 0.0, 0.11):   # detuned saw-ish via a few harmonics
            ff = f * 2 ** (det / 12 / 4)
            ph = rng.uniform(0, 6.28)
            for h in range(1, 7):
                y += np.sin(2 * np.pi * ff * h * t + ph * h) / h * (bright ** (h - 1)) * 0.25
    y *= env_adsr(n, a=min(1.2, dur * 0.3), d=0.5, s=0.85, r=min(1.5, dur * 0.35))
    return y / 8 * amp * 8 / len(CHORDS[chord])


def piano(f, dur=3.0, amp=0.2):
    n = int(dur * SR); t = t_axis(n)
    y = sum(np.sin(2 * np.pi * f * h * t) * (0.6 ** (h - 1)) * np.exp(-t * (1.2 + h * 0.8)) for h in range(1, 7))
    y += 0.3 * np.sin(2 * np.pi * f * 2.001 * t) * np.exp(-t * 3)
    y *= np.minimum(1, t / 0.004)
    return y * amp


def pluck(f, dur=1.5, amp=0.12):
    n = int(dur * SR); t = t_axis(n)
    y = sum(np.sin(2 * np.pi * f * h * t) * (0.5 ** (h - 1)) * np.exp(-t * (3 + h * 1.5)) for h in range(1, 6))
    return y * np.minimum(1, t / 0.002) * amp


def timpani(dur=3.0, f=55, amp=0.5):
    n = int(dur * SR); t = t_axis(n)
    y = np.sin(2 * np.pi * f * t * (1 + 0.15 * np.exp(-t * 8))) * np.exp(-t * 1.6)
    y += 0.3 * bandnoise(n, 60, 400) * np.exp(-t * 12)
    return y * amp


def low_pulse(f, dur, amp=0.1):
    n = int(dur * SR); t = t_axis(n)
    y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return y * np.exp(-t * 6) * np.minimum(1, t / 0.005) * amp


def add(buf, x, at):
    s = int(at * SR)
    if s >= len(buf): return
    e = min(len(buf), s + len(x)); buf[s:e] += x[:e - s]


# ------------------------------------------------------------------ score
def score():
    m = np.zeros(N + SR * 4)
    beat = 0.75   # 80 bpm
    # 1) 0–8.2  mystery: low drone + glassy shimmer + sparse piano
    n = int(8.6 * SR); t = t_axis(n)
    drone = (np.sin(2 * np.pi * 73.4 * t) + 0.5 * np.sin(2 * np.pi * 110 * t + 1)) * env_adsr(n, 2.5, 0.5, 0.9, 1.5) * 0.07
    shimmer = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (1174.7, 1396.9, 1760.0)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t)) * env_adsr(n, 3, 0.5, 0.8, 2) * 0.008
    add(m, drone + shimmer, 0)
    for at, nm in ((0.4, "D5"), (2.2, "A4"), (3.9, "F5"), (5.6, "E5"), (6.9, "A4")):
        add(m, piano(note_hz(nm), 3.5, 0.06), at)
    add(m, timpani(3, 46, 0.25), 7.95)
    # 2) 8.2–20.4  the 19th-century room: warm pad + harp arpeggio
    prog = [("Dm", 8.2), ("Bb", 11.2), ("F", 14.2), ("C", 17.2)]
    for ch, at in prog:
        add(m, pad(ch, 3.4, 0.35, 0.10), at)
        notes = CHORDS[ch][1:]
        for k in range(8):
            add(m, pluck(note_hz(notes[k % len(notes)]) * (2 if k % 4 == 3 else 1), 1.4, 0.035), at + k * beat / 2)
    # 3) 20.4–40.2 the turning point: rise, impact, pulse
    n = int(2.0 * SR); t = t_axis(n)
    rise = bandnoise(n, 300, 6000) * (t / 2.0) ** 2 * 0.08
    add(m, rise, 18.6)
    add(m, timpani(4, 41, 0.45), 20.4)
    prog = [("Dm", 20.4), ("Bb", 23.4), ("F", 26.4), ("C", 29.4), ("Dm", 32.4), ("Bb", 35.4), ("C", 38.4)]
    for ch, at in prog:
        add(m, pad(ch, 3.4, 0.55, 0.12), at)
        root = note_hz(CHORDS[ch][0]) / (2 if note_hz(CHORDS[ch][0]) > 90 else 1)
        for k in range(8):
            add(m, low_pulse(root, 0.5, 0.09 if k % 2 == 0 else 0.05), at + k * beat / 2)
        for k in range(4):
            add(m, piano(note_hz(CHORDS[ch][2 + k % 3]) * 2, 1.5, 0.03), at + k * beat)
    add(m, timpani(4, 41, 0.35), 25.6)   # slates unite into one board
    # 4) 40.2–70.3  why green? — minimal clock-like ostinato, then warm Japan section
    add(m, timpani(3, 49, 0.2), 40.2)
    for k in range(int((59.3 - 40.2) / (beat / 2))):
        at = 40.2 + k * beat / 2
        f = note_hz(["A4", "D5", "F5", "D5"][k % 4])
        add(m, pluck(f, 0.8, 0.022), at)
    prog = [("Dm", 40.2), ("Gm", 43.2), ("Dm", 46.2), ("A", 49.2), ("Dm", 52.2), ("Gm", 55.2), ("A", 58.2)]
    for ch, at in prog: add(m, pad(ch, 3.4, 0.3, 0.07), at)
    prog = [("F", 59.3), ("C", 62.3), ("Dm", 65.3), ("Bb", 68.3)]
    for ch, at in prog:
        add(m, pad(ch, 3.4, 0.4, 0.10), at)
        for k in range(4): add(m, piano(note_hz(CHORDS[ch][2 + k % 3]), 2.5, 0.045), at + k * beat)
    # 5) 70.3–84.6  modern: uplifting, fuller
    add(m, rise[: int(1.5 * SR)], 68.8); add(m, timpani(3, 44, 0.35), 70.3)
    prog = [("Bb", 70.3), ("F", 73.3), ("C", 76.3), ("Dm", 79.3), ("Bb", 82.3)]
    for ch, at in prog:
        add(m, pad(ch, 3.4, 0.6, 0.12), at)
        root = note_hz(CHORDS[ch][0]) / (2 if note_hz(CHORDS[ch][0]) > 90 else 1)
        for k in range(8):
            add(m, low_pulse(root, 0.5, 0.08), at + k * beat / 2)
            add(m, pluck(note_hz(CHORDS[ch][1 + k % 4]) * 2, 0.9, 0.025), at + k * beat / 2)
    # 6) 84.6–95  coda: solo piano over a held pad, resolving and fading
    add(m, pad("Fmaj7", 6.0, 0.3, 0.08), 84.6); add(m, pad("Dm", 6.5, 0.25, 0.07), 90.0)
    for at, nm in ((84.8, "A4"), (85.6, "C5"), (86.4, "F5"), (88.0, "E5"), (89.6, "D5"), (91.4, "A4"), (92.2, "D5"), (93.0, "F5")):
        add(m, piano(note_hz(nm), 4.0, 0.06), at)
    m = m[:N]
    st = reverb(m, 3.2, 0.35)
    return st


# ------------------------------------------------------------------ sfx
def chalk_from_pen(name, start, gain=0.25, pencil=False):
    pens = json.load(open(os.path.join(BOARDS, name, "pen.json")))
    n = int(len(pens) / 30 * SR) + SR
    env = np.zeros(n)
    prev = None
    for i, p in enumerate(pens):
        s, e = int(i / 30 * SR), int((i + 1) / 30 * SR)
        if p and prev:
            speed = math.hypot(p[0] - prev[0], p[1] - prev[1]) * 30
            env[s:e] = min(1.0, 0.25 + speed * 2.5)
        prev = p
    env = np.convolve(env, np.ones(400) / 400, "same")
    tex = bandnoise(n, 1800 if not pencil else 2500, 7000 if not pencil else 9000)
    gr = (rng.random(n) < 0.004).astype(float); gr = np.convolve(gr, np.exp(-np.arange(200) / 30), "same")  # grit
    y = (tex * (0.6 + 0.6 * gr)) * env * gain
    return y, start


def clack(amp=0.3, f=900):
    n = int(0.25 * SR); t = t_axis(n)
    y = bandnoise(n, 400, 5000) * np.exp(-t * 60) * 0.6 + np.sin(2 * np.pi * f * t) * np.exp(-t * 40) * 0.5
    y += np.sin(2 * np.pi * 160 * t) * np.exp(-t * 25) * 0.6
    return y * amp


def whoosh(dur=1.2, amp=0.2, up=True):
    n = int(dur * SR); t = t_axis(n)
    e = np.sin(np.pi * t / dur) ** 2
    y = bandnoise(n, 200, 3000) * e
    return y * amp


def tick(amp=0.05):
    n = int(0.05 * SR); t = t_axis(n)
    return bandnoise(n, 2000, 8000) * np.exp(-t * 300) * amp


def sfx():
    m = np.zeros(N + SR * 4)
    for name, st in SHOTS.items():
        y, at = chalk_from_pen(name, st, 0.10 if name != "F1" else 0.08)
        add(m, y, at)
    # B2: slate pencil (lighter, higher) + cloth wipe
    y, at = chalk_from_pen("B2", 12.9, 0.06, pencil=True); add(m, y, at)
    add(m, whoosh(0.7, 0.05), 12.9 + 72 / 30)
    # B1: slates set down on desks / ambience clock
    for k, at in enumerate((8.5, 9.3, 9.9, 11.0)): add(m, clack(0.12, 700 + 60 * k), at)
    for k in range(12): add(m, tick(0.025 if k % 2 else 0.035), 8.4 + k * 1.0)
    # C1: slates fly and land on the wall (same random sequence as blender_shots.shot_C1)
    rnd = random.Random(4); order = list(range(24)); rnd.shuffle(order)
    for i in range(24):
        f0 = 12 + int(i * 3.2) + rnd.randint(0, 6); f1 = f0 + 42
        rnd.uniform(-0.5, 0.5); rnd.uniform(-1, 1); rnd.uniform(-0.6, 0.6)
        add(m, clack(0.09, 800 + 25 * (i % 7)), 20.4 + (f1 - 1) / 30)
        if i % 4 == 0: add(m, whoosh(0.8, 0.03), 20.4 + f0 / 30)
    # transitions
    for at in (8.0, 20.1, 40.0, 70.0, 84.4):
        add(m, whoosh(1.0, 0.07), at - 0.3)
    # D3: enamel firing glow — low roar + crackle
    n = int(2.0 * SR); t = t_axis(n)
    roar = bandnoise(n, 60, 900) * np.sin(np.pi * t / 2.0) * 0.07
    crack = (rng.random(n) < 0.0015) * rng.standard_normal(n) * 0.25
    add(m, roar + np.convolve(crack, np.exp(-np.arange(300) / 40), "same"), 48.6 + 75 / 30)
    # E1: digital wake-up blip when the e-board appears
    n = int(0.4 * SR); t = t_axis(n)
    add(m, (np.sin(2 * np.pi * 880 * t) + np.sin(2 * np.pi * 1320 * t)) * np.exp(-t * 10) * 0.05, 70.3 + 75 / 30)
    # room tone
    air = bandnoise(N, 80, 1500) * 0.006
    m[:N] += air
    # final chime on the logo
    for f, a in ((1174.7, 0.05), (1760, 0.03), (2349, 0.015)):
        n = int(4 * SR); t = t_axis(n); add(m, np.sin(2 * np.pi * f * t) * np.exp(-t * 1.2) * a, 91.6)
    return reverb(m[:N], 1.2, 0.18)


def main():
    tl = json.load(open(os.path.join(AUD, "timeline.json")))
    bgm = score(); fx = sfx()
    narr = read(os.path.join(AUD, "narration.wav"))
    narr = np.pad(narr, (0, max(0, N - len(narr))))[:N]
    # ducking envelope from the narration timeline (smooth 250 ms ramps)
    duck = np.ones(N)
    for l in tl["lines"]:
        s, e = int((l["start"] - 0.15) * SR), int((l["end"] + 0.1) * SR)
        duck[max(0, s):e] = 0.35
    k = int(0.25 * SR); duck = np.convolve(duck, np.ones(k) / k, "same")
    fade = np.ones(N); fl = int(2.5 * SR); fade[-fl:] = np.linspace(1, 0, fl) ** 1.5
    bgm_d = bgm * (duck * fade)[:, None]
    write(os.path.join(AUD, "bgm.wav"), bgm / (np.abs(bgm).max() + 1e-9) * 0.9)
    write(os.path.join(AUD, "sfx.wav"), fx / (np.abs(fx).max() + 1e-9) * 0.9)
    mix = np.stack([narr, narr], 1) * 1.0 + bgm_d * 1.3 + fx * 0.9 * fade[:, None]
    pre = os.path.join(ROOT, "work", "mix_pre.wav"); write(pre, mix * 0.8)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", pre, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR),
                    os.path.join(AUD, "mix.wav")], check=True)
    print("audio ok")


if __name__ == "__main__":
    main()
