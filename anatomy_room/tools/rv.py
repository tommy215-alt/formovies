#!/usr/bin/env python3
"""rv：制作の時間を短くするための外付けのコマンド（テンプレートの production/common/ と各話のファイルは書き換えない）。

    python tools/rv.py 014 scenes             場面の番号・名前・時間・セリフ ID・キャッシュの有無
    python tools/rv.py 014 render all         完成版まで（変わった場面だけ書き出す）。--full で全場面を作り直す
    python tools/rv.py 014 render scene 3     場面 3 だけを最終の画質で書き出し、音つきで work/rv/scene_03.mp4 に
    python tools/rv.py 014 preview scene 3    場面 3 だけを 10 fps の静止画から軽く作る（確認用。完成版には使わない）

画面に出すのは進捗の 1 行と結果だけ。各工程のログは work/rv/log/ に書く（失敗したときは末尾 5 行だけを出す）。

キャッシュ（どれも入力のハッシュで判定。入力が変われば作り直す）：
- audio：セリフの時刻と音声・BGM の区間・効果音の時刻・music.py と pipeline.py が同じなら、ミックスを作り直さない。
  BGM の合成結果も work/rv/bgm/ にキャッシュする（同じ関数の結果をそのまま保存するので、音は変わらない）
- textcheck：描画のファイルとタイムラインが同じなら飛ばす
- 場面の映像：pipeline.py のキャッシュ（場面の中身のハッシュ）に加えて、描画のコードが変わったときは、
  その場面の見本のコマ（0.5 秒ごと＋最初と最後のコマ）を新しいコードで描き、前回の見本と比べる。
  すべてのコマの差が 2 階調以下なら、前回の mp4 をそのまま使う。見本は場面ごとに新しいページで描く
  （共通部品の描画は前のコマの状態を少し引き継ぐため、順番をそろえないと最大 22 階調ほど揺れる。2026-10-28 に測定）
"""
import contextlib
import hashlib
import importlib.util
import json
import math
import os
import pickle
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent          # anatomy_room
COMMON = ROOT / "production" / "common"
EXT = ROOT / "production" / "ext"          # テンプレートの外に足した部品（music_ext.py・hud_ext.js）
SAMPLE_STEP = 15          # 見本の間隔（コマ）。30 fps で 0.5 秒
TOL = 2                   # 見本の画素の差の許容（階調）。同じ順で描いた静止画の揺れは最大 1
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


def sha(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, bytes) else json.dumps(p, ensure_ascii=False, sort_keys=True).encode())
    return h.hexdigest()[:16]


def fsha(*paths):
    return sha(*[Path(p).read_bytes() for p in paths])


class RV:
    def __init__(self, pid):
        pid = pid if pid.startswith("pilot_") else f"pilot_{int(pid):03d}"
        self.here = ROOT / "production" / pid
        self.script = self.here / "production_script.py"
        spec = importlib.util.spec_from_file_location(f"ps_{pid}", self.script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)          # if __name__ == "__main__" の外は設定だけ
        import pipeline                         # production_script.py が common/ を sys.path に入れている
        self.pipeline = pipeline
        self.cfg = mod.EP
        self.ep = pipeline.Episode(self.script, self.cfg)
        self.work = self.here / "work"
        self.rv = self.work / "rv"
        for d in ("log", "bgm", "samples"):
            (self.rv / d).mkdir(parents=True, exist_ok=True)
        self.state_file = self.rv / "state.json"
        self.state = json.loads(self.state_file.read_text(encoding="utf-8")) if self.state_file.exists() else {}
        if "segments" in self.state and "versions" not in self.state:     # 2026-10-28 の最初の形式の記録を読み替える
            self.state["versions"] = {k: {r["ext"]: {"mp4": r["mp4"], "samples": r["samples"]}} for k, r in self.state["segments"].items()}
            self.state["latest"] = {k: r["ext"] for k, r in self.state["segments"].items()}
        self.state.pop("segments", None)
        self.state.pop("made", None)
        self.t_start = time.time()
        self.logs = []

    def save(self):
        self.state_file.write_text(json.dumps(self.state, ensure_ascii=False, indent=1), encoding="utf-8")

    # ------------------------------------------------------------ 出力
    def say(self, s):
        print(s, flush=True)

    def log_path(self, name):
        p = self.rv / "log" / f"{time.strftime('%Y%m%d_%H%M%S')}_{name}.log"
        self.logs.append(p)
        return p

    def fail(self, name, log):
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-5:] if log.exists() else []
        self.say(f"❌ {name} が失敗（ログ：{log}）")
        for l in tail:
            self.say("   " + l)
        sys.exit(1)

    def step(self, name, *args):
        """production_script.py の工程を、ログをファイルに出して実行する"""
        log = self.log_path(name)
        with open(log, "w", encoding="utf-8") as f:
            r = subprocess.run([sys.executable, str(self.script), name, *args], cwd=self.here, stdout=f, stderr=subprocess.STDOUT, env=ENV)
        if r.returncode:
            self.fail(name, log)
        return log

    # ------------------------------------------------------------ 場面
    def tl(self):
        return self.ep.tl()

    def scenes(self, tl=None):
        """pipeline.step_render と同じ場面の区切り（コマ）と、場面の名前"""
        tl = tl or self.tl()
        fps, n = tl["fps"], math.ceil(tl["duration"] * tl["fps"])
        cues = {**tl["cues"], "endcard": tl["ending_start"]}
        names = {round(cues[c] * fps): c for c in self.cfg["segments"]}
        names[round(cues["endcard"] * fps)] = "endcard"
        bounds = sorted(set([0] + [round(cues[c] * fps) for c in self.cfg["segments"]] + [round(cues["endcard"] * fps), n]))
        out = []
        for a, b in zip(bounds, bounds[1:]):
            if b > a:
                out.append({"name": names.get(a, "lead_in"), "a": a, "b": b})   # lead_in：最初のセリフの前の数コマ
        # 番号は production_script.py の scenes と同じ（1 冒頭 …）。最初のセリフの前の数コマは 0 番
        base = 0 if out and out[0]["name"] == "lead_in" else 1
        for i, s in enumerate(out):
            s["no"] = i + base
        return out

    def code_hash(self):
        """pipeline.step_render と同じ「描画のコード」のハッシュ（場面の mp4 のファイル名に使われる）"""
        files = [self.here / "renderer.html", COMMON / "render_frames.js", COMMON / "stage.js", COMMON / "ending.js",
                 COMMON / "vendor" / "three.min.js"] + [self.here / f for f in self.cfg.get("extra_files", [])]
        return hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()

    def ext_hash(self):
        """描画に使うファイルをすべて含むハッシュ（pipeline の判定に入っていない cine.js・vendor の画像も含める）"""
        files = sorted({(self.here / "renderer.html").resolve(), *[(self.here / f).resolve() for f in self.cfg.get("extra_files", [])],
                        *COMMON.glob("*.js"), *(COMMON / "vendor").rglob("*.js"), *EXT.glob("*.js")})
        return fsha(*files)

    def seg_path(self, tl, s, code):
        return self.work / "segments" / f"{self.ep.segment_key(tl, s['a'], s['b'], code)}.mp4"

    # ------------------------------------------------------------ 見本のコマ（場面の変化の判定）
    def sample_frames(self, s):
        fr = sorted(set(list(range(s["a"], s["b"], SAMPLE_STEP)) + [s["b"] - 1]))
        return fr

    def render_samples(self, segs, tl):
        """各場面の見本を、場面ごとに新しいページで描く（2 本同時）。戻り値：{場面の番号: 一時フォルダ}"""
        fps, out = tl["fps"], {}
        stills = self.work / "stills"
        stills.mkdir(exist_ok=True)
        log = self.log_path("samples")
        lock = threading.Lock()
        todo = list(segs)

        def worker():
            while True:
                with lock:
                    if not todo:
                        return
                    s = todo.pop(0)
                fr = self.sample_frames(s)
                ts = [f"{i / fps:.6f}" for i in fr]
                with lock, open(log, "a", encoding="utf-8") as f:
                    f.write(f"scene {s['no']}: {len(ts)} frames\n")
                r = subprocess.run(["node", str(COMMON / "render_frames.js"), "--dir", str(self.here), "--stills", ",".join(ts)],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
                with lock, open(log, "a", encoding="utf-8") as f:
                    f.write(r.stdout + r.stderr)
                if r.returncode:
                    raise RuntimeError(f"samples scene {s['no']}")
                d = self.rv / "samples" / f"_new_{s['no']:02d}"
                shutil.rmtree(d, ignore_errors=True)
                d.mkdir()
                for i, t in zip(fr, ts):
                    src = stills / ("t" + f"{float(t):.2f}".rjust(6, "0") + ".png")   # render_frames.js の名前の付け方
                    shutil.move(str(src), str(d / f"{i:06d}.png"))
                out[s["no"]] = d

        ths = [threading.Thread(target=worker) for _ in range(min(2, len(segs)))]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        if len(out) != len(segs):
            self.fail("見本のコマ", log)
        return out

    @staticmethod
    def same_samples(d_old, d_new):
        old = sorted(Path(d_old).glob("*.png"))
        if not old or [p.name for p in old] != [p.name for p in sorted(Path(d_new).glob("*.png"))]:
            return False, None
        worst = 0
        for p in old:
            a, b = p.read_bytes(), (Path(d_new) / p.name).read_bytes()
            if a == b:
                continue
            x = np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)
            y = np.asarray(Image.open(Path(d_new) / p.name).convert("RGB"), dtype=np.int16)
            worst = max(worst, int(np.abs(x - y).max()))
            if worst > TOL:
                return False, worst
        return True, worst

    def judge(self, tl, full=False, only=None):
        """各場面を「使い回す」か「書き出す」かに分け、使い回す場面は mp4 を新しいハッシュの名前で置く。
        only：場面の番号を 1 つ指定すると、その場面だけを判定する（ほかの場面の記録は残す）。戻り値：(使い回す場面, 書き出す場面)"""
        code, ext = self.code_hash(), self.ext_hash()
        segs = [s for s in self.scenes(tl) if only is None or s["no"] == only]
        # 記録：場面（区切り・中身）ごとに、描画のファイルの版（ext）→ {"mp4", "samples"}。latest は最後に使った版
        vers, latest = self.state.setdefault("versions", {}), self.state.setdefault("latest", {})
        first = not vers
        seg_dir, smp_dir = self.work / "segments", self.rv / "samples"
        reuse, render, check = [], [], []
        for s in segs:
            nk = f"{s['a']}-{s['b']}-{self.ep.segment_key(tl, s['a'], s['b'], '')}"
            s["rec"], s["path"] = nk, self.seg_path(tl, s, code)
            mine = vers.get(nk, {}).get(ext)
            last = vers.get(nk, {}).get(latest.get(nk, ""))
            if full:
                render.append(s)
            elif mine and (seg_dir / mine["mp4"]).exists():   # この版で前に作った mp4（変わっていない、または変更を元に戻した）
                if seg_dir / mine["mp4"] != s["path"] and not s["path"].exists():
                    shutil.copy2(seg_dir / mine["mp4"], s["path"])
                reuse.append(s)
            elif last and (seg_dir / last["mp4"]).exists() and (smp_dir / last["samples"]).is_dir():
                s["from"] = last
                check.append(s)                               # 描画のファイルだけが変わった：見本で比べる
            elif first and s["path"].exists():
                check.append(s)                               # rv を初めて使う回：既存の mp4 の見本を作るだけ
            else:
                render.append(s)
        sampled = check + render                              # 見本を描く場面（判定で「変わった」場面は render にも入るので、ここで固定する）
        new = self.render_samples(sampled, tl) if sampled else {}
        for s in check:
            ok, worst = self.same_samples(smp_dir / s["from"]["samples"], new[s["no"]]) if "from" in s else (True, 0)
            if ok:
                if "from" in s and seg_dir / s["from"]["mp4"] != s["path"] and not s["path"].exists():
                    shutil.copy2(seg_dir / s["from"]["mp4"], s["path"])
                reuse.append(s)
            else:
                s["worst"] = worst
                render.append(s)
        for s in render:                                      # pipeline に書き出させる（同じ名前の古い mp4 はよける）
            if s["path"].exists():
                s["path"].rename(s["path"].with_suffix(".old.mp4"))
        for s in sampled:                                     # 見本を、この版の記録として残す
            d = smp_dir / f"{s['rec']}_{ext[:10]}"
            shutil.rmtree(d, ignore_errors=True)
            new[s["no"]].rename(d)
            vers.setdefault(s["rec"], {})[ext] = {"mp4": s["path"].name, "samples": d.name}
        for s in segs:
            latest[s["rec"]] = ext
            v = vers.setdefault(s["rec"], {})
            for e in [e for e in v if e != ext][:-1]:         # 版は「今」と「1 つ前」だけ残す
                shutil.rmtree(smp_dir / v[e]["samples"], ignore_errors=True)
                del v[e]
        if only is None:                                      # 今の区切りにない場面の記録と見本を消す（ディスクを使いすぎない）
            live = {s["rec"] for s in segs}
            for k in [k for k in vers if k not in live]:
                for v in vers[k].values():
                    shutil.rmtree(smp_dir / v["samples"], ignore_errors=True)
                del vers[k]
                latest.pop(k, None)
            used = {v["samples"] for vv in vers.values() for v in vv.values()}
            for d in smp_dir.iterdir():                       # どの記録にもない見本（途中で止まったときの残り）を消す
                if d.is_dir() and d.name not in used:
                    shutil.rmtree(d, ignore_errors=True)
        self.save()
        return sorted(reuse, key=lambda s: s["no"]), sorted(render, key=lambda s: s["no"])

    # ------------------------------------------------------------ 音・文字（キャッシュ）
    def audio_key(self, tl):
        cfg = {k: self.cfg.get(k) for k in ("music", "sfx", "sfx_bank", "sfx_duck", "music_lp")}
        cues = {**tl["cues"], "endcard": tl["ending_start"]}
        sfx = [[x[0], cues[x[1]], *x[2:]] for x in self.cfg["sfx"]]
        lines = [[x["id"], x["start"], x["end"], fsha(self.work / "voice" / f"{x['id']}.wav")] for x in tl["lines"]]
        return sha(cfg, sfx, self.ep.sections(tl), lines, tl["duration"], tl["ending_start"],
                   fsha(COMMON / "music.py", COMMON / "pipeline.py", *sorted(EXT.glob("*.py"))))

    def audio(self, tl):
        key = self.audio_key(tl)
        outs = [self.work / f for f in ("mix.wav", "mix_raw.wav", "music.wav", "voice_only.wav")]
        if self.state.get("audio") == key and all(p.exists() for p in outs):
            return "キャッシュ"
        music = self.pipeline.music
        mkey = fsha(COMMON / "music.py", *sorted(EXT.glob("*.py")))   # 外付けの曲調（production/ext/music_ext.py）を変えたら BGM も作り直す

        def memo(fn):
            def wrap(*a, **k):
                f = self.rv / "bgm" / f"{fn.__name__}_{sha(mkey, list(a), k)}.pkl"
                if f.exists():
                    return pickle.loads(f.read_bytes())
                r = fn(*a, **k)
                f.write_bytes(pickle.dumps(r))
                for old in sorted((self.rv / "bgm").glob("*.pkl"), key=lambda p: p.stat().st_mtime)[:-3]:
                    old.unlink()          # 新しい 3 つだけ残す
                return r
            return wrap

        orig = music.bgm_techno, music.bgm
        music.bgm_techno, music.bgm = memo(orig[0]), memo(orig[1])
        log = self.log_path("audio")
        try:
            with open(log, "w", encoding="utf-8") as f, contextlib.redirect_stdout(f):
                self.ep.step_audio()
        except Exception as e:
            with open(log, "a", encoding="utf-8") as f:
                f.write(repr(e))
            self.fail("audio", log)
        finally:
            music.bgm_techno, music.bgm = orig
        self.state["audio"] = key
        self.save()
        return "作り直し"

    def textcheck_start(self):
        """textcheck が必要なら別のプロセスで始める（GPU を使う。CPU を使う audio と同時に動かす）。戻り値：(プロセス, ログ, キー) か None"""
        key = sha(self.ext_hash(), fsha(self.work / "timeline.json"))
        if self.state.get("textcheck") == key and (self.work / "textcheck.json").exists():
            return None
        kept = self.rv / "textcheck" / f"{key}.json"          # 前に同じ入力で検査した結果（変更を元に戻したとき）
        if kept.exists():
            shutil.copy2(kept, self.work / "textcheck.json")
            self.state["textcheck"] = key
            self.save()
            return None
        log = self.log_path("textcheck")
        f = open(log, "w", encoding="utf-8")
        p = subprocess.Popen([sys.executable, str(self.script), "textcheck"], cwd=self.here, stdout=f, stderr=subprocess.STDOUT, env=ENV)
        return p, log, key, f

    def textcheck_wait(self, job):
        if job is None:
            return "キャッシュ"
        p, log, key, f = job
        rc = p.wait()
        f.close()
        if rc:
            self.fail("textcheck", log)
        kd = self.rv / "textcheck"
        kd.mkdir(exist_ok=True)
        shutil.copy2(self.work / "textcheck.json", kd / f"{key}.json")
        for old in sorted(kd.glob("*.json"), key=lambda p: p.stat().st_mtime)[:-3]:
            old.unlink()          # 新しい 3 つだけ残す
        self.state["textcheck"] = key
        self.save()
        return "作り直し"

    # ------------------------------------------------------------ 書き出し（進捗の 1 行）
    def history(self):
        return self.state.setdefault("history", {})          # 場面の名前 → 1 コマあたりの秒（同時 2 本のうち 1 本）

    def run_render(self, render, total):
        """pipeline の render を動かし、場面が終わるたびに 1 行だけ出す"""
        if not render:
            return
        hist, spf_run = self.history(), []
        by_range = {(s["a"], s["b"]): s for s in render}
        log = self.log_path("render")
        t0 = time.time()
        p = subprocess.Popen([sys.executable, str(self.script), "render"], cwd=self.here, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=ENV)
        left = {(s["a"], s["b"]): s for s in render}
        jobs, since = None, {}
        with open(log, "w", encoding="utf-8") as f:
            for line in p.stdout:
                f.write(line)
                f.flush()
                if not line.startswith("segment "):
                    continue
                if jobs is None:                              # pipeline が書いた、同時に動く本ごとの場面の割り当て（今回の場面だけのもの）
                    jobs = [j for j in self.jobs() if all((x["a"], x["b"]) in by_range for x in j)]
                    since = {i: t0 for i in range(len(jobs))}
                a, b = map(int, line.split()[1].split("-"))
                secs = float(line.split(" in ")[1].rstrip("s\n"))
                s = by_range.get((a, b))
                left.pop((a, b), None)
                if s:
                    hist[s["name"]] = secs / (b - a)
                    spf_run.append(secs / (b - a))
                spf = sum(spf_run) / len(spf_run)
                now, rem = time.time(), 0.0
                for i, j in enumerate(jobs or [list(left.values())]):   # 本ごとの残り＝残りのコマ×1 コマの秒−いまの場面の経過
                    if any((x["a"], x["b"]) == (a, b) for x in j):
                        since[i] = now
                    fr = sum(x["b"] - x["a"] for x in j if (x["a"], x["b"]) in left)
                    rem = max(rem, fr * spf - (now - since.get(i, now)) if fr else 0.0)
                no = s["no"] if s else "?"
                self.say(f"シーン{no}/{total} 完了（所要 {secs:.0f}秒）／残り約{math.ceil((max(0.0, rem) + 60) / 60)}分" if left
                         else f"シーン{no}/{total} 完了（所要 {secs:.0f}秒）／書き出し完了、仕上げ中（約1分）")
        if p.wait():
            self.fail("render", log)
        self.save()
        for s in render:                                      # 書き出しが終わったら、よけておいた古い mp4 を消す
            old = s["path"].with_suffix(".old.mp4")
            if old.exists():
                old.unlink()

    def jobs(self):
        out = []
        for jf in sorted(self.work.glob("job*.json")):
            try:
                out.append(json.loads(jf.read_text(encoding="utf-8")))
            except Exception:
                pass
        return [j for j in out if j]

    def estimate(self, render):
        hist = self.history()
        sec = sum((s["b"] - s["a"]) * hist.get(s["name"], 1.25) for s in render) / max(1, min(len(render), self.cfg.get("workers", 3)))
        return sec

    # ------------------------------------------------------------ コマンド
    def cmd_scenes(self):
        tl = self.tl()
        code = self.code_hash()
        lines = json.loads((self.here / "lines.json").read_text(encoding="utf-8"))["lines"]
        self.say("| No | 場面 | 時間 | セリフ | 映像の mp4 |")
        self.say("|---|---|---|---|---|")
        for s in self.scenes(tl):
            ids = [l["id"] for l in lines if l.get("scene") == s["name"]] if s["name"] != "endcard" else ["END1", "END2"]
            self.say(f"| {s['no']} | {s['name']} | {s['a'] / 30:.1f}〜{s['b'] / 30:.1f}s | {', '.join(ids)} | "
                     f"{'あり' if self.seg_path(tl, s, code).exists() else 'なし（書き出しが必要）'} |")

    def prepare(self):
        """voice → audio → textcheck（変わったものだけ）"""
        self.step("voice")
        tl = self.tl()
        job = self.textcheck_start()
        a = self.audio(tl)
        c = self.textcheck_wait(job)
        return tl, a, c

    def cmd_render_all(self, full=False):
        tl, a, c = self.prepare()
        reuse, render = self.judge(tl, full)
        total = max(s["no"] for s in reuse + render)          # 「シーン3/9」の分母（0 番は数えない）
        est = self.estimate(render)
        self.say(f"準備：audio {a}・textcheck {c}／使い回す場面 {len(reuse)}（{', '.join(str(s['no']) for s in reuse) or 'なし'}）・"
                 f"書き出す場面 {len(render)}（{', '.join(str(s['no']) for s in render) or 'なし'}）／残り約{math.ceil((est + 60) / 60)}分")
        self.run_render(render, total)
        if not render:
            self.step("render")          # つなぐだけ（全場面が使い回し）
        for name in ("mux", "docs", "qc"):
            self.step(name)
        qa = self.log_path("video_qa")
        with open(qa, "w", encoding="utf-8") as f:
            subprocess.run([sys.executable, str(ROOT / "tools" / "video_qa.py"), self.here.name, "--sheets"], cwd=ROOT,
                           stdout=f, stderr=subprocess.STDOUT, env=ENV)
        verdict = [l for l in qa.read_text(encoding="utf-8", errors="replace").splitlines() if l.startswith(self.here.name + ":")]
        mins = (time.time() - self.t_start) / 60
        self.say(f"✅ 完成：{self.ep.out.name}（{tl['duration']:.1f}秒）／所要 {mins:.1f}分／video_qa：{verdict[-1].split(': ', 1)[1] if verdict else '結果なし'}")

    def cmd_render_scene(self, no, force=False):
        tl, a, c = self.prepare()
        s = next(x for x in self.scenes(tl) if x["no"] == no)
        path = self.seg_path(tl, s, self.code_hash())
        reuse, render = self.judge(tl, full=force, only=no)
        if not render:
            self.say(f"準備：audio {a}・textcheck {c}／シーン{no}（{s['name']}）は前回と同じ（使い回す）")
        else:
            est = self.estimate(render)
            self.say(f"準備：audio {a}・textcheck {c}／シーン{no}（{s['name']}）を書き出す／残り約{math.ceil((est + 30) / 60)}分")
            job = self.rv / "job_scene.json"
            job.write_text(json.dumps([{"a": s["a"], "b": s["b"], "out": str(path)}]), encoding="utf-8")
            log = self.log_path(f"scene{no}")
            with open(log, "w", encoding="utf-8") as f:
                r = subprocess.run(["node", str(COMMON / "render_frames.js"), "--dir", str(self.here), "--segments", str(job)],
                                   stdout=f, stderr=subprocess.STDOUT, env=ENV)
            if r.returncode:
                self.fail(f"シーン{no}", log)
            secs = float(log.read_text(encoding="utf-8").split(" in ")[-1].split("s")[0])
            self.history()[s["name"]] = secs / (s["b"] - s["a"])
            self.save()
            old = path.with_suffix(".old.mp4")
            if old.exists():
                old.unlink()
            self.say(f"シーン{no}/1 完了（所要 {secs:.0f}秒）")
        out = self.rv / f"scene_{no:02d}.mp4"
        self.mux_clip(path, s, out, tl)
        self.say(f"✅ シーン{no}（{s['name']}、{s['a'] / 30:.1f}〜{s['b'] / 30:.1f}s）：{out}（最終の画質・音つき。完成版は render all でつなぐ）")

    def mux_clip(self, video, s, out, tl):
        fps = tl["fps"]
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-ss", f"{s['a'] / fps:.4f}",
                        "-t", f"{(s['b'] - s['a']) / fps:.4f}", "-i", str(self.work / "mix.wav"), "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(out)], check=True)

    def cmd_preview(self, no, fps_prev=10):
        tl, a, c = self.prepare()
        s = next(x for x in self.scenes(tl) if x["no"] == no)
        fps = tl["fps"]
        step = fps // fps_prev
        fr = list(range(s["a"], s["b"], step))
        self.say(f"プレビュー：シーン{no}（{s['name']}）{len(fr)} コマ（{fps_prev} fps）／残り約{math.ceil((len(fr) * 0.7 + 20) / 60)}分")
        ts = [f"{i / fps:.6f}" for i in fr]
        log = self.log_path(f"preview{no}")
        t0 = time.time()
        with open(log, "w", encoding="utf-8") as f:
            r = subprocess.run(["node", str(COMMON / "render_frames.js"), "--dir", str(self.here), "--stills", ",".join(ts)],
                               stdout=f, stderr=subprocess.STDOUT, env=ENV)
        if r.returncode:
            self.fail("プレビュー", log)
        d = self.rv / "preview_frames"
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir()
        for k, t in enumerate(ts):
            shutil.move(str(self.work / "stills" / ("t" + f"{float(t):.2f}".rjust(6, "0") + ".png")), str(d / f"{k:05d}.png"))
        out = self.rv / f"preview_scene_{no:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(fps_prev), "-i", str(d / "%05d.png"),
                        "-ss", f"{s['a'] / fps:.4f}", "-t", f"{len(fr) / fps_prev:.4f}", "-i", str(self.work / "mix.wav"),
                        "-map", "0:v", "-map", "1:a", "-vf", "scale=540:960", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", str(out)], check=True)
        shutil.rmtree(d, ignore_errors=True)
        self.say(f"✅ プレビュー：{out}（540×960・{fps_prev} fps・確認用）／所要 {(time.time() - t0) / 60:.1f}分")


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        sys.exit(1)
    rv = RV(a[0])
    cmd = a[1:]
    if cmd == ["scenes"]:
        rv.cmd_scenes()
    elif cmd[:2] == ["render", "all"]:
        rv.cmd_render_all(full="--full" in cmd)
    elif cmd[:2] == ["render", "scene"]:
        rv.cmd_render_scene(int(cmd[2]), force="--force" in cmd)
    elif cmd[:2] == ["preview", "scene"]:
        rv.cmd_preview(int(cmd[2]))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
