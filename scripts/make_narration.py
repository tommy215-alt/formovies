"""Synthesize narration with Open JTalk (male HTS voice), assemble with pauses, write timings."""
import json, subprocess, wave, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from narration_data import LINES
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio"); TMP = os.path.join(ROOT, "work", "tts"); os.makedirs(TMP, exist_ok=True)
DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
SR = 48000
LEAD = 0.6  # silence before first line
# per-scene delivery: (speed, pitch shift in half tones, intonation weight)
STYLE = {1: (1.08, -1.5, 1.35), 2: (1.13, -2.0, 1.15), 3: (1.15, -2.0, 1.15),
         4: (1.15, -2.0, 1.2), 5: (1.12, -2.0, 1.2), 6: (1.0, -2.5, 1.1)}

def tts(text, path, scene):
    r, fm, jf = STYLE[scene]
    txt = path + ".txt"; open(txt, "w").write(text)
    raw = path + ".raw.wav"
    subprocess.run(["open_jtalk", "-x", DIC, "-m", VOICE, "-ow", raw, "-r", str(r), "-fm", str(fm),
                    "-jf", str(jf), "-a", "0.55", "-b", "0.4", "-u", "0.5", txt], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-ar", str(SR), "-ac", "1", path], check=True)
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    # trim leading/trailing silence
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, idx[0] - 480): idx[-1] + 2400]
    return a

def main():
    segs, t, timeline = [], LEAD, []
    for i, (scene, text, subs, pause) in enumerate(LINES):
        a = tts(text, os.path.join(TMP, f"l{i:02d}.wav"), scene)
        a = a / (np.sqrt(np.mean(a[np.abs(a) > 0.02] ** 2)) + 1e-9) * 0.12  # per-line level match
        dur = len(a) / SR
        timeline.append(dict(i=i, scene=scene, text=text, subs=subs, start=round(t, 3), end=round(t + dur, 3)))
        segs.append((t, a)); t += dur + pause
    total = t + 0.5
    mix = np.zeros(int(total * SR) + SR, np.float32)
    for st, a in segs:
        s = int(st * SR); mix[s:s + len(a)] += a
    dry = os.path.join(TMP, "narr_dry.wav")
    with wave.open(dry, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    # voice polish: warm low end, de-harsh, light compression, small room, loudness normalize
    af = ("highpass=f=70,equalizer=f=140:t=q:w=1:g=3,equalizer=f=3200:t=q:w=1.2:g=-2.5,"
          "equalizer=f=7000:t=q:w=1:g=-3,acompressor=threshold=-20dB:ratio=3:attack=8:release=120,"
          "aecho=0.8:0.6:28|47:0.10|0.06,loudnorm=I=-16:TP=-1.5:LRA=7")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", dry, "-af", af, "-ar", str(SR), "-ac", "1",
                    os.path.join(OUT, "narration.wav")], check=True)
    scenes = {}
    for e in timeline:
        sc = scenes.setdefault(e["scene"], [e["start"], e["end"]]); sc[1] = e["end"]
    json.dump(dict(total=round(total, 3), lines=timeline, scenes=scenes), open(os.path.join(OUT, "timeline.json"), "w"),
              ensure_ascii=False, indent=1)
    print("total", round(total, 2)); [print(k, v) for k, v in scenes.items()]

if __name__ == "__main__":
    main()
