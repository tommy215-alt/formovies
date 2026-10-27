#!/usr/bin/env python3
"""完成動画の品質検査（MASTER_VIDEO_TEMPLATE の固定ルールに合っているか）。

使い方:
    python3 anatomy_room/tools/video_qa.py pilot_006
    python3 anatomy_room/tools/video_qa.py pilot_006 --sheets   # 目視用の 1 秒ごとの一覧も作る

調べること（書き出した mp4 と、制作データ work/timeline.json・work/textcheck.json から）:
  1. 基本仕様：1080×1920・30fps・H.264／AAC 48kHz、尺（90 秒以内。lines.json の max_duration で回ごとに変えられる）
  2. 字幕の欠落：各セリフの途中のコマで、字幕の帯（暗い帯）が画面に出ているか
  3. 最初のコマ：自動のサムネイルになるため、白飛び・ぼやけていないか
  4. 文字の自動検査の結果（textcheck）：0.3 秒を超えて続く問題が 0 件か、フォントにない文字がないか
  5. 共通エンディングがあるか（最後のセリフの後に END1・END2）
  --sheets で qa/sheet_*.jpg（1 秒ごとのコマ 20 枚ずつ）を作る。最後は必ず人の目で全編を見る。
結果は各話の qa_report.md に書く。問題があれば終了コード 1。
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent / "production"
W, H = 1080, 1920
SUB_BAND = (1380, 1580, 400, 580)  # 字幕の帯が来る範囲（y0, y1, x0, x1）。stage.js の subtitles2（中心 x 490・y 1475〜1495）。
# 横は中心の 180px だけ見る（「PHP」のような 3 文字の短い字幕でも帯の幅は約 240px あり、この範囲を覆う）


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def gray_frame(mp4, t, w=W, h=H):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(mp4), "-frames:v", "1", "-vf", f"scale={w}:{h},format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    return a.reshape(h, w).astype(np.float32) if a.size == w * h else None


def sharpness(g):
    return float(np.mean(np.abs(np.diff(g, axis=0))) + np.mean(np.abs(np.diff(g, axis=1))))


def hook_check(ep, mp4, tl, ng):
    """冒頭 3 秒の自動検査と、目視用の切り出し（qa/hook_3s.mp4・qa/hook_strip.jpg）。
    自動で分かるのは「始まりの遅さ・無音・止まった画面」まで。「続きを見たいか」は切り出しを見て人が判断する"""
    import numpy as np
    body = [x for x in tl["lines"] if not x.get("ending")]
    first = body[0]["start"] if body else 99.0
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-t", "3", "-i", str(mp4), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16) / 32768 if pcm else np.zeros(1)
    db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9) if len(x) else -99.0
    d1, d3 = db(a[:16000]), db(a[:48000])
    frames = [gray_frame(mp4, t, 216, 384).astype(float) for t in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.95)]
    motion = float(np.mean([np.mean(np.abs(f1 - f0)) for f0, f1 in zip(frames, frames[1:])]))
    rows = [("最初のナレーションの開始 1.0 秒以内", first <= 1.0, f"{first:.2f} 秒（「{body[0]['speech'][:16]}…」）" if body else "なし"),
            ("最初の 1 秒が無音でない（−40 dBFS 以上）", d1 >= -40, f"{d1:.1f} dBFS"),
            ("最初の 3 秒の音の大きさ（目安 −30 dBFS 以上）", d3 >= -30, f"{d3:.1f} dBFS"),
            ("画面が止まっていない（0.5 秒ごとのコマの差の平均 3 以上）", motion >= 3, f"{motion:.1f}")]
    qa = ep / "qa"
    qa.mkdir(exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-t", "3", "-i", str(mp4), "-c:v", "libx264", "-crf", "20", "-c:a", "aac", str(qa / "hook_3s.mp4")])
    run(["ffmpeg", "-v", "error", "-y", "-t", "3", "-i", str(mp4), "-vf", "fps=2,scale=270:480,tile=6x1", "-frames:v", "1", str(qa / "hook_strip.jpg")])
    out = ["## 冒頭 3 秒", "", "| 項目 | 結果 | 値 |", "|---|---|---|"]
    for name, ok, val in rows:
        out.append(f"| {name} | {'OK' if ok else '**NG**' if '目安' not in name else '要確認'} | {val} |")
        if not ok and "目安" not in name:
            ng.append("冒頭 3 秒")
    out += ["", "- 切り出し：`qa/hook_3s.mp4`（音つき）と `qa/hook_strip.jpg`（0.5 秒ごと）。",
            "- **判断基準：初めて見る人が、この先を見たいと思うか。** 弱ければ冒頭を作り直す（VIDEO_QA_CHECKLIST の「冒頭 3 秒」に記入）", ""]
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ep = ROOT / sys.argv[1]
    sheets = "--sheets" in sys.argv
    mp4 = next((p for p in ep.glob("reverse_*.mp4")), None) or next(ep.glob("*.mp4"))
    tl = json.loads((ep / "work" / "timeline.json").read_text())
    ng, rep = [], [f"# 完成動画の品質検査（{ep.name}）", "", f"- 対象：`{mp4.name}`", "- 検査：`tools/video_qa.py`（MASTER_VIDEO_TEMPLATE の固定ルール）", ""]

    # 1. 基本仕様
    pr = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate:format=duration",
                         "-of", "json", str(mp4)]).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    dur = float(pr["format"]["duration"])
    # 長さの上限：既定は MASTER の 90 秒。ユーザーが長さを指定した回は lines.json の max_duration（可変ルール）
    max_dur = float(json.loads((ep / "lines.json").read_text(encoding="utf-8")).get("max_duration", 90.0))
    spec = [("解像度 1080×1920", v["width"] == W and v["height"] == H, f"{v['width']}×{v['height']}"),
            ("30fps", v["r_frame_rate"] == "30/1", v["r_frame_rate"]),
            ("映像 H.264", v["codec_name"] == "h264", v["codec_name"]),
            ("音声 AAC 48kHz", bool(a) and a["codec_name"] == "aac" and a.get("sample_rate") == "48000", f"{a and a['codec_name']} {a and a.get('sample_rate')}"),
            (f"尺 {max_dur:.0f} 秒以内", dur <= max_dur, f"{dur:.2f} 秒")]
    rep += ["## 1. 基本仕様", "", "| 項目 | 結果 | 値 |", "|---|---|---|"]
    for name, ok, val in spec:
        rep.append(f"| {name} | {'OK' if ok else '**NG**'} | {val} |")
        if not ok:
            ng.append(name)
    rep.append("")

    # 2. 字幕の欠落
    body = [x for x in tl["lines"] if not x.get("ending")]
    miss = []
    y0, y1, x0, x1 = SUB_BAND
    for x in body:
        g = gray_frame(mp4, (x["start"] + x["end"]) / 2)
        if g is None:
            miss.append((x["id"], "コマを取り出せない"))
            continue
        dark = float(np.mean(g[y0:y1, x0:x1] < 70))
        if dark < 0.2:
            miss.append((x["id"], f"暗い帯 {dark:.0%}"))
    rep += ["## 2. 字幕の欠落", "", f"- セリフ {len(body)} 行の途中のコマで、字幕の帯が出ているかを調べた（帯の中心 180px の 20% 以上が暗い色なら「出ている」）。",
            f"- 見つからなかった行：{'なし' if not miss else '、'.join(f'{i}（{why}）' for i, why in miss)}", ""]
    if miss:
        ng.append("字幕の欠落")

    # 3. 最初のコマ（自動のサムネイル）
    g0 = gray_frame(mp4, 0.0)
    ref = [gray_frame(mp4, t) for t in np.linspace(2, min(dur, tl["ending_start"]) - 1, 12)]
    ref = [g for g in ref if g is not None]
    s0, sm = sharpness(g0), float(np.median([sharpness(g) for g in ref]))
    l0 = float(g0.mean())
    ok0 = s0 >= 0.6 * sm and l0 <= 225
    rep += ["## 3. 最初のコマ（自動のサムネイルになる）", "",
            f"- 平均輝度 {l0:.0f}（225 以下）、くっきり度 {s0:.1f}（本編の中央値 {sm:.1f} の 60% 以上）：{'OK' if ok0 else '**要確認**（白飛び・ぼやけ。サムネは thumbnail.png を使うか、最初のコマを止め絵にする）'}",
            f"- サムネイル画像 `thumbnail.png`：{'あり' if (ep / 'thumbnail.png').exists() else 'なし（node ../common/render_frames.js --dir . --thumb で作る）'}", ""]
    if not ok0:
        ng.append("最初のコマ")

    # 4. 文字の自動検査
    tc = ep / "work" / "textcheck.json"
    if tc.exists():
        d = json.loads(tc.read_text())
        step = d.get("step", 0.1)
        runs = {}
        for i in d.get("issues", []):
            runs.setdefault((i["kind"], i["s"]), []).append(i["t"])
        lasting = []
        for (kind, s), ts in runs.items():  # 連続して何コマ続くか（0.3 秒を超えたら問題）
            ts.sort()
            best = cur = 1
            for p, q in zip(ts, ts[1:]):
                cur = cur + 1 if q - p <= step * 1.5 else 1
                best = max(best, cur)
            if best * step > 0.3 + 1e-6:
                lasting.append(f"{kind}「{s}」{best * step:.1f}秒")
        miss_g = d.get("missing_glyphs", [])
        rep += ["## 4. 文字の自動検査（textcheck）", "", f"- 全編 {d.get('frames')} コマ（{step} 秒ごと）",
                f"- 0.3 秒を超えて続く問題：{'なし' if not lasting else '、'.join(lasting)}",
                f"- フォントにない文字：{'なし' if not miss_g else ' '.join(miss_g)}", ""]
        if lasting or miss_g:
            ng.append("文字の自動検査")
        if tc.stat().st_mtime < (ep / "renderer.html").stat().st_mtime:
            rep += ["- **注意**：renderer.html が textcheck より新しい。`python3 production_script.py textcheck` をやり直すこと", ""]
            ng.append("textcheck が古い")
    else:
        rep += ["## 4. 文字の自動検査（textcheck）", "", "- **未実施**（`python3 production_script.py textcheck`）", ""]
        ng.append("textcheck 未実施")

    # 5. 共通エンディング
    endl = [x for x in tl["lines"] if x.get("ending")]
    ok_end = len(endl) == 2 and endl[0]["start"] > body[-1]["end"]
    rep += ["## 5. 共通エンディング", "", f"- {'OK' if ok_end else '**NG**'}：" + "、".join(f"{x['id']}「{x['speech']}」{x['start']:.2f}s" for x in endl), ""]
    if not ok_end:
        ng.append("共通エンディング")

    # 冒頭 3 秒（2026-10-27〜の標準：最初の 3 秒で興味を獲得する。REVERSE_STANDARD_RULES の「冒頭 3 秒」）
    rep += hook_check(ep, mp4, tl, ng)

    # 目視用の一覧
    if sheets:
        qa = ep / "qa"
        qa.mkdir(exist_ok=True)
        for p in qa.glob("f_*.png"):
            p.unlink()
        font = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
        run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"fps=1,scale=360:640,drawtext=fontfile={font}:text='%{{pts\\:hms}}':x=8:y=8:fontsize=26:"
             "fontcolor=yellow:box=1:boxcolor=black", str(qa / "f_%03d.png")])
        n = len(list(qa.glob("f_*.png")))
        for k in range((n + 19) // 20):
            run(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", str(qa / "f_*.png"), "-vf",
                 f"select='between(n\\,{k * 20}\\,{k * 20 + 19})',tile=5x4", "-frames:v", "1", str(qa / f"sheet_{k}.jpg")])
        for p in qa.glob("f_*.png"):
            p.unlink()
        rep += ["## 目視用の一覧", "", f"- `qa/sheet_0.jpg`〜`qa/sheet_{(n + 19) // 20 - 1}.jpg`（1 秒ごと {n} コマ）。**全部を目で見て** VIDEO_QA_CHECKLIST の C 欄に記入する", ""]

    rep += ["## 判定", "", f"- 自動検査：{'すべて OK' if not ng else '**要対応**：' + '、'.join(ng)}",
            "- 自動検査は完了の判定ではない。目視（VIDEO_QA_CHECKLIST）を済ませてから完成とする。", ""]
    (ep / "qa_report.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"{ep.name}: {'OK' if not ng else 'NG: ' + ', '.join(ng)} → {ep / 'qa_report.md'}")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    main()
