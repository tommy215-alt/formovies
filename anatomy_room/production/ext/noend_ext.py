"""共通エンディングを付けない（設計「悲劇」、2026-10-30〜。ユーザーの指示「最後の『リバース』の演出はカットして、余韻を無くす」）。
テンプレートの外の部品で、pipeline.Episode の step_voice と qc_ending を包む（common/ は変えない）。

各話の production_script.py で：
    import noend_ext
    noend_ext.apply(pipeline)   # ending_ext.apply より後に呼ぶ

step_voice のあとで timeline.json からエンディングの 2 句を外し、最後のセリフの直後（CUT 秒）で本編を終える。
「endcard」の場面は暗転のための短い区間（BLACK 秒）だけ残す（場面ごとの書き出しの仕組みはそのまま使える）。
renderer.html は TL.no_ending を見て、ロゴと決めゼリフを出さずに暗転する。
"""
import json
import math

CUT, BLACK = 0.05, 0.25


def apply(pipeline, black=BLACK):
    """black：最後の一文のあとの暗転の秒（設計「悲劇」2026-10-30〜：時間をかけて 2 秒以上）"""
    if getattr(pipeline.Episode, "_noend_ext", False):
        return
    sv0 = pipeline.Episode.step_voice

    def step_voice(self):
        sv0(self)
        p = self.work / "timeline.json"
        tl = json.loads(p.read_text(encoding="utf-8"))
        body = [x for x in tl["lines"] if not x.get("ending")]
        es = math.ceil((body[-1]["end"] + CUT) * pipeline.FPS) / pipeline.FPS
        tl.update(lines=body, ending_start=round(es, 5), endcard_start=round(es, 5), duration=round(es + black, 5), no_ending=True, blackout=black)
        tl["cues"] = {k: v for k, v in tl["cues"].items() if v < es}
        tl["cues"].update(end1=round(es - .45, 5), end2=round(es - 1.05, 5))   # step_qc が抜き出すコマ（end1+0.4・end2+1.0）を本編の最後のコマに置く
        p.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"noend: 共通エンディングなし（設計「悲劇」）。本編 {body[-1]['end']:.2f}s → 暗転 {es:.2f}s〜（{black:.1f} 秒）→ 全体 {es + black:.2f}s")

    def qc_ending(self, tl, astream):
        body = [x for x in tl["lines"] if not x.get("ending")]
        return ["## 共通エンディング", "",
                "- なし（設計「悲劇」：ユーザーの指示で「リバース」の演出をカット。最後は時間をかけて暗転。`production/ext/noend_ext.py`）",
                f"- 本編の最後のセリフの終わり {body[-1]['end']:.2f}s → 暗転 {tl['ending_start']:.2f}s → 動画の終わり {tl['duration']:.2f}s",
                f"- 音声トラック {float(astream['duration']):.2f}s", ""]

    pipeline.Episode.step_voice = step_voice
    pipeline.Episode.qc_ending = qc_ending
    pipeline.Episode._noend_ext = True
