"""Synthesize the narration, assemble it on the timeline, write timings.

ENGINE=voicevox (default): VOICEVOX ENGINE on 127.0.0.1:50021, speaker 青山龍星 (credit: VOICEVOX:青山龍星).
  Each line starts at the same time as in timeline_slots.json (the cut timing the CG was rendered to);
  a line that would overrun its slot is re-synthesised slightly faster.
ENGINE=openjtalk: Open JTalk + HTS male voice (fallback, no external engine needed)."""
import json, subprocess, wave, os, sys, urllib.request, urllib.parse
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

VV = "http://127.0.0.1:50021"
VV_SPEAKER = {1: 13, 2: 13, 3: 13, 4: 13, 5: 13, 6: 84}   # 青山龍星 ノーマル / しっとり(ending)
VV_STYLE = {1: (1.0, 1.25), 2: (1.0, 1.1), 3: (1.0, 1.1), 4: (1.0, 1.15), 5: (1.0, 1.15), 6: (0.95, 1.05)}  # speed, intonation


def vv_tts(text, path, scene, speed_mul=1.0):
    spk = VV_SPEAKER[scene]; speed, inton = VV_STYLE[scene]
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    q = json.loads(op.open(urllib.request.Request(f"{VV}/audio_query?" + urllib.parse.urlencode({"text": text, "speaker": spk}), method="POST")).read())
    q.update(speedScale=speed * speed_mul, intonationScale=inton, pitchScale=-0.02, prePhonemeLength=0.05,
             postPhonemeLength=0.08, outputSamplingRate=SR, outputStereo=False)
    req = urllib.request.Request(f"{VV}/synthesis?speaker={spk}", data=json.dumps(q).encode(), headers={"Content-Type": "application/json"})
    open(path, "wb").write(op.open(req).read())
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    idx = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, idx[0] - 480): idx[-1] + 2400]


def main_voicevox():
    slots = json.load(open(os.path.join(OUT, "timeline_slots.json")))["lines"]
    segs, timeline = [], []
    for i, (scene, text, subs, pause) in enumerate(LINES):
        st = slots[i]["start"]
        if scene == 6 and timeline and timeline[-1]["scene"] == 6:   # closing lines may flow freely (slow, lingering)
            st = timeline[-1]["end"] + 0.3
        room = (slots[i + 1]["start"] - st - 0.12) if i + 1 < len(slots) and LINES[i + 1][0] != 6 else 4.0
        mul = 1.0
        for _ in range(6):
            a = vv_tts(text, os.path.join(TMP, f"v{i:02d}.wav"), scene, mul)
            dur = len(a) / SR
            if dur <= room: break
            mul *= min(1.12, dur / room * 1.01)
        a = a / (np.sqrt(np.mean(a[np.abs(a) > 0.02] ** 2)) + 1e-9) * 0.12
        timeline.append(dict(i=i, scene=scene, text=text, subs=subs, start=round(st, 3), end=round(st + len(a) / SR, 3), speed=round(mul, 3)))
        segs.append((st, a))
        print(i, round(len(a) / SR, 2), "slot", round(room, 2), "speed x", round(mul, 3))
    finish(segs, timeline, slots[-1]["end"] + 0.5 + 0.5)


def finish(segs, timeline, total):
    mix = np.zeros(int(total * SR) + SR, np.float32)
    for st, a in segs:
        s = int(st * SR); mix[s:s + len(a)] += a
    dry = os.path.join(TMP, "narr_dry.wav")
    with wave.open(dry, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    af = ("highpass=f=60,equalizer=f=120:t=q:w=1:g=1.5,equalizer=f=6500:t=q:w=1:g=-1.5,"
          "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,aecho=0.8:0.6:24|41:0.07|0.04,loudnorm=I=-16:TP=-1.5:LRA=7")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", dry, "-af", af, "-ar", str(SR), "-ac", "1",
                    os.path.join(OUT, "narration.wav")], check=True)
    scenes = {}
    for e in timeline:
        sc = scenes.setdefault(e["scene"], [e["start"], e["end"]]); sc[1] = e["end"]
    json.dump(dict(total=round(total, 3), lines=timeline, scenes=scenes), open(os.path.join(OUT, "timeline.json"), "w"),
              ensure_ascii=False, indent=1)
    print("total", round(total, 2))


def main():
    if os.environ.get("ENGINE", "voicevox") == "voicevox":
        return main_voicevox()
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
