"""Final edit: shot frames -> upscale to 1080x1920, colour grade, grain, scene transitions, logo end card,
burned-in ASS subtitles and the mixed soundtrack -> H.264/AAC MP4.

Usage: python3 scripts/compose.py [--from SEC --to SEC] [--out PATH]
"""
import argparse, os, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS, W, H = 30, 1080, 1920
ORDER = ["A1", "B1", "B2", "B3", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4", "D5a", "D5b", "E1", "E2", "E3", "F1", "F2"]
SHOTS = {"A1": (0.0, 8.2), "B1": (8.2, 12.9), "B2": (12.9, 17.2), "B3": (17.2, 20.4), "C1": (20.4, 26.3), "C2": (26.3, 30.5),
         "C3": (30.5, 34.0), "C4": (34.0, 40.2), "D1": (40.2, 44.1), "D2": (44.1, 48.6), "D3": (48.6, 54.1), "D4": (54.1, 59.3),
         "D5a": (59.3, 65.9), "D5b": (65.9, 70.3), "E1": (70.3, 74.8), "E2": (74.8, 79.2), "E3": (79.2, 84.6), "F1": (84.6, 91.0), "F2": (91.0, 95.0)}
SCENE_CUTS = [8.2, 20.4, 40.2, 70.3, 84.6]   # dip-to-black between chapters
TOTAL = 95.0


def frame_list():
    seq = []
    for s in ORDER:
        a, b = SHOTS[s]
        n = int(round(b * FPS)) - int(round(a * FPS))
        for i in range(n): seq.append((s, i + 1))
    return seq


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = 1 - 0.32 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
VIG = np.clip(VIG, 0.55, 1)[..., None]
GRAD = np.clip((yy - H * 0.70) / (H * 0.30), 0, 1)[..., None] ** 1.4   # darken bottom for subtitle legibility
LOGO = Image.open(os.path.join(ROOT, "assets", "logo.png"))
LOGO = LOGO.resize((int(LOGO.width * 0.85), int(LOGO.height * 0.85)), Image.LANCZOS)
rng = np.random.default_rng(0)


def grade(a):
    # gentle filmic S-curve + split tone (cool shadows, warm highlights)
    a = a / 255.0
    a = a + 0.06 * np.sin(np.pi * a) * (a - 0.5) * 2
    lum = a.mean(2, keepdims=True)
    a = a + (0.5 - lum) * np.array([-0.012, 0.004, 0.018]) + (lum - 0.5) * np.array([0.02, 0.006, -0.018])
    return np.clip(a, 0, 1)


def load(shot, idx):
    p = os.path.join(ROOT, "assets", "frames", "shots", shot, f"{idx:04d}.jpg")
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return None
    return Image.open(p).convert("RGB")


def process(img, t):
    img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    a = grade(np.asarray(img, np.float32))
    a = a * VIG * (1 - 0.45 * GRAD)
    # chapter dips
    k = 1.0
    for c in SCENE_CUTS:
        d = abs(t - c)
        if d < 0.22: k = min(k, 0.15 + 0.85 * d / 0.22)
    if t < 0.5: k = min(k, t / 0.5)
    if t > 90.4: k = min(k, max(0.22, 1 - (t - 90.4) / 1.1))   # settle down for the end card
    a = a * k
    a = a + rng.normal(0, 0.012, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)   # film grain
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    if t >= 92.0:
        al = min(1.0, (t - 92.0) / 0.6)
        lg = LOGO.copy(); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * al)))
        out.paste(lg, ((W - lg.width) // 2, 1130), lg)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=TOTAL)
    ap.add_argument("--out", default=os.path.join(ROOT, "final_short.mp4"))
    args = ap.parse_args()
    seq = frame_list()
    f0, f1 = int(args.t0 * FPS), min(len(seq), int(args.t1 * FPS))
    ass = os.path.join(ROOT, "work", "subs.ass")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", str(f0 / FPS), "-t", str((f1 - f0) / FPS), "-i", os.path.join(ROOT, "assets", "audio", "mix.wav"),
           "-vf", f"setpts=PTS+{f0 / FPS}/TB,ass={ass},setpts=PTS-STARTPTS",
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", args.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    last = Image.new("RGB", (720, 1280))
    missing = 0
    for i in range(f0, f1):
        s, idx = seq[i]
        img = load(s, idx)
        if img is None: img = last; missing += 1
        last = img
        p.stdin.write(process(img, i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print("written", args.out, "frames", f1 - f0, "missing", missing)


if __name__ == "__main__":
    main()
