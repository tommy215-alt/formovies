"""自分で読んだナレーションを使う（2026-11-05〜、tools/narration_studio/ で収録）。

lines.json に "recorded": true がある回だけ、production/<回>/recording/final/<行 ID>.wav（48 kHz・モノラル・16 bit）が
ある行は合成音声の代わりにその録音を置く（共通エンディングの END1・END2 も）。録音がない行は従来どおり合成する。
クレジットは "recorded_credit"（書かなければ「ナレーション：収録」）。
"""
import json

DEFAULT_CREDIT = "ナレーション：収録"


def apply(pipeline):
    E = pipeline.Episode
    if getattr(E, "_recorded_ext", False):
        return
    E._recorded_ext = True
    sc0, sv0 = E.synth_cached, E.step_voice

    def recorded(self, ln):
        if not self.lines().get("recorded"):
            return None
        f = self.here / "recording" / "final" / f"{ln['id']}.wav"
        return f if f.exists() else None

    def synth_cached(self, ln, cache):
        f = recorded(self, ln)
        if f is None:
            return sc0(self, ln, cache)
        p = {**self.voice_params(ln), "recorded": True}
        # 読みの情報はないので、文末の音程の検査（qc_endings）はこの行を飛ばす（accent_phrases が空なら None）
        q = {"kana": ln["speech"], "accent_phrases": [], "speedScale": 1.0, "prePhonemeLength": 0.0}
        return f.read_bytes(), q, p, False

    def step_voice(self):
        r = sv0(self)
        d = self.lines()
        if d.get("recorded"):
            f = self.work / "timeline.json"
            tl = json.loads(f.read_text(encoding="utf-8"))
            if all(x.get("voice", {}).get("recorded") or recorded(self, x) for x in tl["lines"]):
                tl["credits"] = [d.get("recorded_credit", DEFAULT_CREDIT)]   # 全部を自分で読んだときは合成音声のクレジットを外す
            else:
                tl["credits"].insert(0, d.get("recorded_credit", DEFAULT_CREDIT))
            f.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
        return r

    E.synth_cached, E.step_voice = synth_cached, step_voice
