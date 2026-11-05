#!/usr/bin/env python3
"""ナレーション収録スタジオ（2026-11-05〜、ユーザーの依頼「台本を上げたらカラオケみたいに読む字幕が出て、録音ボタンで録音。
基本は自動編集で、ピッチと響きだけ変えられるソフト」）。PC の中だけで動く（127.0.0.1）。

使い方（リポジトリの直下で）：
    python anatomy_room/tools/narration_studio/narration_studio.py            # ブラウザで収録画面が開く
    python anatomy_room/tools/narration_studio/narration_studio.py long_001   # その回の台本（lines.json）を開いた状態で始める

流れ：
1. 台本を開く：動画の回（production/<回>/lines.json ＋共通エンディングの決めゼリフ 2 句）か、貼り付けた文章（文ごとに区切る）。
2. 収録：いまの行が大きく出る。録音ボタン（スペースキー）で録音を始めると、目標の速さで文字の色が変わっていく（カラオケ）。
   もう一度押すと止まり、自動で次の行へ。取り直しは行を選んでもう一度録るだけ。
3. 自動編集（録った行から裏で順に）：
   ① 音声認識（faster-whisper、large-v3-turbo、CPU）で単語ごとの時刻 → 「あー」「えー」「えっと」などのフィラーを除き、
      言い直したときは最後の読み直しから使い、長い息つぎを詰める（編集の結果は edit/<行>.wav）
   ② 声の加工：低い雑音の除去・雑音の軽減・サ行の刺さりを抑える・低音を強め（低音域の持ち上げ＋こもりの抑え＋明瞭さ）・
      コンプレッサー・ピッチ（rubberband、フォルマント保持）・話す速さを目標にそろえる・響き（合成した残響）・音量をそろえる
      （結果は out/<行>.wav）。ピッチと響きを変えると②だけをやり直す。
4. 書き出し：動画の回なら production/<回>/recording/final/ に置き、lines.json に "recorded": true を書く
   → production/ext/recorded_ext.py が合成音声の代わりに使う。
保存先：動画の回は production/<回>/recording/、文章のときは tools/narration_studio/projects/<名前>/。
"""
import json
import math
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from difflib import SequenceMatcher
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # anatomy_room
PROD = ROOT / "production"
PORT = 8765
SR = 48000
DEFAULT_SETTINGS = {"pitch": -0.5, "reverb": 18, "rate": 7.0, "credit": ""}   # ピッチ（半音）・響き（%）・目標の速さ（モーラ/秒）
PUNCT = re.compile(r"[\s、。，．,.!！?？「」『』（）()・…ー〜~]")

# ---------------------------------------------------------------------------- 台本
class Project:
    def __init__(self):
        self.name, self.episode, self.dir, self.lines = None, None, None, []
        self.settings = dict(DEFAULT_SETTINGS)
        self.status = {}          # 行 → {"state": 未録音|処理待ち|処理中|完了|失敗, "dur", "msg", "words", "rev"}
        self.lock = threading.Lock()

    def open_episode(self, ep):
        d = PROD / ep
        data = json.loads((d / "lines.json").read_text(encoding="utf-8"))
        ending = json.loads((PROD / "common" / "voices.json").read_text(encoding="utf-8"))["ending"]["parts"]
        lines = [{"id": x["id"], "speech": x["speech"], "sub": x.get("sub", x["speech"])} for x in data["lines"]]
        lines += [{"id": f"END{i + 1}", "speech": p["speech"], "sub": p["speech"]} for i, p in enumerate(ending)]
        self._set(ep, ep, d / "recording", lines)

    def open_text(self, name, text):
        sents = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*|\n+", text) if s.strip()]
        lines = [{"id": f"S{i + 1:03d}", "speech": s, "sub": s} for i, s in enumerate(sents)]
        safe = re.sub(r"[^\w\-]", "_", name or "text")
        self._set(safe, None, HERE / "projects" / safe, lines)

    def _set(self, name, episode, d, lines):
        with self.lock:
            self.name, self.episode, self.dir, self.lines = name, episode, d, lines
            for sub in ("raw", "edit", "out"):
                (d / sub).mkdir(parents=True, exist_ok=True)
            sf = d / "studio.json"
            saved = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else {}
            self.settings = {**DEFAULT_SETTINGS, **saved.get("settings", {})}
            self.status = {}
            for ln in lines:
                st = saved.get("status", {}).get(ln["id"])
                raw = self.raw_path(ln["id"])
                if raw and st and st.get("state") in ("完了", "失敗"):
                    self.status[ln["id"]] = st
                elif raw:
                    self.status[ln["id"]] = {"state": "処理待ち"}; JOBS.put((ln["id"], "full"))
                else:
                    self.status[ln["id"]] = {"state": "未録音"}
            for ln in lines:
                ln["moras"] = moras(ln["speech"])
            self.save()

    def raw_path(self, lid):
        for p in self.dir.glob(f"raw/{lid}.*"):
            return p
        return None

    def line(self, lid):
        return next(x for x in self.lines if x["id"] == lid)

    def save(self):
        (self.dir / "studio.json").write_text(json.dumps({"name": self.name, "episode": self.episode, "settings": self.settings,
                                                          "status": self.status}, ensure_ascii=False, indent=1), encoding="utf-8")


P = Project()
JOBS = queue.Queue()


def moras(text):
    """読みのモーラ数（音声エンジンが動いていれば audio_query から、なければ文字数からの見積もり）"""
    for eng, spk in (("http://127.0.0.1:10101", 1310138977), ("http://127.0.0.1:50021", 13)):
        try:
            u = f"{eng}/audio_query?" + urllib.parse.urlencode({"speaker": spk, "text": text})
            q = json.loads(urllib.request.urlopen(urllib.request.Request(u, method="POST"), timeout=5).read())
            return sum(len(ap["moras"]) for ap in q["accent_phrases"])
        except Exception:
            continue
    return round(len(PUNCT.sub("", text)) * 1.35)


# ---------------------------------------------------------------------------- 音声の入出力
def decode(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def write_wav(path, x, sr=SR):
    y = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-", str(path)], input=y, check=True)


def ffmpeg_filter(x, af, sr=SR):
    y = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-", "-af", af,
                          "-ar", str(sr), "-ac", "1", "-f", "f32le", "-"], input=y, check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


# ---------------------------------------------------------------------------- ① 編集（フィラー・言い直し・長い間）
_MODEL = None


def model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    return _MODEL


def edit(lid):
    ln = P.line(lid)
    x = decode(P.raw_path(lid))
    x16 = decode(P.raw_path(lid), 16000).astype(np.float32)
    segs, _ = model().transcribe(x16, language="ja", word_timestamps=True, beam_size=5, condition_on_previous_text=False,
                                 initial_prompt="えー、あのー、えっと、まあ、" + ln["speech"])
    words = [{"t": w.word.strip(), "s": w.start, "e": w.end} for sg in segs for w in (sg.words or []) if w.word.strip()]
    # 文字起こしを台本と文字単位で突き合わせ、台本にない部分（フィラー・言いかけ・言い直しの前半）を除く。
    # 言い直したときは、台本といちばん長く一致する読み（ふつうは最後の読み直し）が残る
    script = PUNCT.sub("", ln["speech"])
    owner = []                                     # 文字起こしの各文字 → 単語の番号
    for i, w in enumerate(words):
        owner += [i] * len(PUNCT.sub("", w["t"]))
    heard = "".join(PUNCT.sub("", w["t"]) for w in words)
    sm = SequenceMatcher(None, heard, script, autojunk=False)
    extra = np.zeros(len(words))
    for op, a1, a2, _, _ in sm.get_opcodes():
        if op == "insert" or op == "equal" or op == "replace":
            continue
        for k in range(a1, a2):                    # op == "delete"：聞こえたが台本にない文字
            extra[owner[k]] += 1
    for i, w in enumerate(words):
        n = len(PUNCT.sub("", w["t"]))
        w["filler"] = n == 0 or extra[i] / n >= .5
    # 台本とほとんど合わないとき（認識の失敗・無音で文字を作ってしまったとき）は単語では切らず、前後の無音だけを切る
    match = round(SequenceMatcher(None, heard, script, autojunk=False).ratio(), 2) if heard else 0
    kept = [w for w in words if not w["filler"]] if match >= .4 else []
    if not kept:   # 認識できなかったときは、音の大きさで前後の無音だけを切る
        env = np.convolve(np.abs(x), np.ones(960) / 960, "same"); on = np.where(env > env.max() * .06)[0]
        segs_t = [(max(0, on[0] / SR - .05), min(len(x) / SR, on[-1] / SR + .1))] if len(on) else [(0, len(x) / SR)]
    else:
        iv = [[max(0, w["s"] - .06), min(len(x) / SR, w["e"] + .09)] for w in kept]
        segs_t = [iv[0]]
        for a, b in iv[1:]:
            if a - segs_t[-1][1] < .12:
                segs_t[-1][1] = max(segs_t[-1][1], b)
            else:
                segs_t.append([a, b])
    out, prev = [], None
    for a, b in segs_t:
        if prev is not None:
            gap = a - prev
            keep = min(gap, .24)                       # 長い間・息つぎは 0.24 秒まで詰める（間の部屋の音はそのまま使う）
            i0 = int(prev * SR); out.append(x[i0:i0 + int(keep * SR)])
        out.append(x[int(a * SR):int(b * SR)]); prev = b
    y = np.concatenate(out) if out else x
    fade = int(.01 * SR); y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
    write_wav(P.dir / "edit" / f"{lid}.wav", y)
    return {"words": [w["t"] for w in words], "match": match,
            "cut": [w["t"] for w in words if w["filler"] and PUNCT.sub("", w["t"])] if kept else []}


# ---------------------------------------------------------------------------- ② 声の加工（ピッチと響きはここだけ）
def impulse(seconds=1.6, seed=3):
    """合成の残響（部屋の響き）。初期反射＋指数的に減る雑音"""
    r = np.random.default_rng(seed); n = int(seconds * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / (seconds / 6.5))
    for d, g in ((.011, .5), (.019, .35), (.027, .3), (.041, .22)):
        ir[int(d * SR)] += g * 8
    lp = np.convolve(ir, np.ones(9) / 9, "same")       # 高い音を少し丸める
    return lp / np.sqrt(np.sum(lp ** 2))


IR = None


def fftconv(a, b):
    n = len(a) + len(b) - 1; N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, N) * np.fft.rfft(b, N), N)[:len(a)]


def render(lid):
    global IR
    ln, st = P.line(lid), P.settings
    x = decode(P.dir / "edit" / f"{lid}.wav")
    dur = len(x) / SR
    target = ln["moras"] / st["rate"]                       # 目標の速さで読んだときの長さ
    tempo = max(.88, min(1.15, dur / target)) if target > 0 else 1.0   # 速さをそろえる（0.88〜1.15 倍まで）
    pitch = 2 ** (st["pitch"] / 12)
    af = ",".join([
        "highpass=f=70", "afftdn=nr=10:nf=-48:tn=1", "deesser=i=0.35:m=0.5:f=0.5",
        "bass=g=4.5:f=120:w=0.8",                       # 低音を強め（聞き心地のよい厚み）
        "equalizer=f=320:t=q:w=1.1:g=-2",               # こもりを抑える
        "equalizer=f=3200:t=q:w=1.0:g=1.8",             # 言葉の明瞭さ
        "treble=g=-1.5:f=9000",                         # 耳に刺さる高音を少し丸める
        "acompressor=threshold=-21dB:ratio=3:attack=8:release=160:makeup=2.5",
        f"rubberband=pitch={pitch:.5f}:tempo={tempo:.4f}:formant=preserved:transients=smooth",
    ])
    y = ffmpeg_filter(x, af)
    if st["reverb"] > 0:
        if IR is None:
            IR = impulse()
        wet = fftconv(np.concatenate([y, np.zeros(int(.6 * SR))]), IR)
        y = np.concatenate([y, np.zeros(int(.6 * SR))]) * (1 - st["reverb"] / 250) + wet * (st["reverb"] / 100) * .35
        tail = np.where(np.abs(y) > 1e-3)[0]; y = y[:tail[-1] + int(.05 * SR)] if len(tail) else y
    y = ffmpeg_filter(y, "loudnorm=I=-18:TP=-2:LRA=7,alimiter=limit=0.89:level=disabled")
    pad = np.zeros(int(.03 * SR)); y = np.concatenate([pad, y, pad])
    write_wav(P.dir / "out" / f"{lid}.wav", y)
    return len(y) / SR, tempo


def worker():
    while True:
        lid, kind = JOBS.get()
        try:
            if lid not in P.status:
                continue
            P.status[lid] = {**P.status[lid], "state": "処理中"}
            info = {}
            if kind == "full" or not (P.dir / "edit" / f"{lid}.wav").exists():
                info = edit(lid)
            dur, tempo = render(lid)
            P.status[lid] = {**P.status[lid], **info, "state": "完了", "dur": round(dur, 2), "tempo": round(tempo, 3),
                             "rev": time.time()}
        except Exception as e:
            P.status[lid] = {**P.status.get(lid, {}), "state": "失敗", "msg": str(e)[:300]}
        finally:
            P.save()


# ---------------------------------------------------------------------------- 書き出し
def export():
    done = [ln["id"] for ln in P.lines if P.status.get(ln["id"], {}).get("state") == "完了"]
    if P.episode:
        fd = P.dir / "final"; fd.mkdir(exist_ok=True)
        for lid in done:
            (fd / f"{lid}.wav").write_bytes((P.dir / "out" / f"{lid}.wav").read_bytes())
        lp = PROD / P.episode / "lines.json"; d = json.loads(lp.read_text(encoding="utf-8"))
        d["recorded"] = True
        if P.settings.get("credit"):
            d["recorded_credit"] = P.settings["credit"]
        lp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"dir": str(fd), "count": len(done), "missing": [x["id"] for x in P.lines if x["id"] not in done]}
    allx = [decode(P.dir / "out" / f"{lid}.wav") for lid in done]
    gap = np.zeros(int(.35 * SR))
    y = np.concatenate([np.concatenate([a, gap]) for a in allx]) if allx else np.zeros(1)
    out = P.dir / f"{P.name}_narration.wav"; write_wav(out, y)
    return {"file": str(out), "count": len(done)}


# ---------------------------------------------------------------------------- サーバー
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)

    def body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); parts = u.path.strip("/").split("/")
        if u.path in ("/", "/index.html"):
            return self.send(200, (HERE / "studio.html").read_bytes(), "text/html; charset=utf-8")
        if u.path == "/api/state":
            eps = sorted(p.parent.name for p in PROD.glob("*/lines.json"))
            return self.send(200, {"name": P.name, "episode": P.episode, "settings": P.settings, "episodes": eps,
                                   "lines": [{**ln, **P.status.get(ln["id"], {})} for ln in P.lines], "queue": JOBS.qsize()})
        if parts[:2] == ["api", "audio"] and len(parts) == 4:
            lid, kind = parts[2], parts[3]
            p = P.raw_path(lid) if kind == "raw" else P.dir / kind / f"{lid}.wav"
            if p and p.exists():
                return self.send(200, p.read_bytes(), "audio/webm" if p.suffix == ".webm" else "audio/wav")
            return self.send(404, {"error": "no audio"})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path); parts = u.path.strip("/").split("/")
        try:
            if u.path == "/api/open":
                d = json.loads(self.body())
                P.open_episode(d["episode"]) if d.get("episode") else P.open_text(d.get("name", "text"), d["text"])
                return self.send(200, {"ok": True})
            if parts[:2] == ["api", "record"] and len(parts) == 3:
                lid = parts[2]; ext = "webm" if "webm" in self.headers.get("Content-Type", "") else "wav"
                for old in P.dir.glob(f"raw/{lid}.*"):
                    old.unlink()
                (P.dir / "raw" / f"{lid}.{ext}").write_bytes(self.body())
                P.status[lid] = {"state": "処理待ち"}; JOBS.put((lid, "full")); P.save()
                return self.send(200, {"ok": True})
            if u.path == "/api/settings":
                d = json.loads(self.body())
                for k in ("pitch", "reverb", "credit"):
                    if k in d:
                        P.settings[k] = d[k]
                for ln in P.lines:
                    if P.status.get(ln["id"], {}).get("state") == "完了":
                        P.status[ln["id"]]["state"] = "処理待ち"; JOBS.put((ln["id"], "render"))
                P.save()
                return self.send(200, {"ok": True})
            if u.path == "/api/export":
                return self.send(200, export())
        except Exception as e:
            return self.send(500, {"error": str(e)})
        self.send(404, {"error": "not found"})


def main():
    threading.Thread(target=worker, daemon=True).start()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        P.open_episode(args[0])
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"ナレーション収録スタジオ：http://127.0.0.1:{PORT}/ （止めるときは Ctrl+C）")
    if "--no-browser" not in sys.argv:
        threading.Thread(target=lambda: (time.sleep(.8), webbrowser.open(f"http://127.0.0.1:{PORT}/")), daemon=True).start()
    threading.Thread(target=model, daemon=True).start()     # 音声認識のモデルを先に読み込んでおく
    srv.serve_forever()


if __name__ == "__main__":
    main()
