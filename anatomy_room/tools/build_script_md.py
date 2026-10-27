#!/usr/bin/env python3
"""制作データ（production/pilot_00N/lines.json と work/timeline.json）から、台本 scripts/pilot_00N/script.md を作る。

チャンネル「リバース」新構成（pilot_006 以降）用。lines.json の meta（学び・面白さ・CG など）と、各行の cg（映像・CG の指示）を使う。
時間は実際の音声合成の長さ。表の書式は check_scripts.py（6 列・時間が連続）に合わせる。

使い方: python3 anatomy_room/tools/build_script_md.py pilot_006 [pilot_007 ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICES = json.loads((ROOT / "production" / "common" / "voices.json").read_text(encoding="utf-8"))


def mmss(t):
    t = int(round(t))
    return f"{t // 60}:{t % 60:02d}"


def build(pid):
    prod = ROOT / "production" / pid
    data = json.loads((prod / "lines.json").read_text(encoding="utf-8"))
    tl = json.loads((prod / "work" / "timeline.json").read_text(encoding="utf-8"))
    meta, v = data["meta"], VOICES[data["voices"]]
    by = {x["id"]: x for x in data["lines"]}
    body = [x for x in tl["lines"] if not x.get("ending")]
    names = {"M": v["M"]["display"], "W": v["W"]["display"]}
    bounds = [0] + [round(x["start"]) for x in body[1:]] + [round(tl["ending_start"])]
    for i in range(1, len(bounds)):  # 1 秒より短いセリフでも、行の時間が 0 秒にならないように
        bounds[i] = max(bounds[i], bounds[i - 1] + 1)
    rows = []
    for i, x in enumerate(body):
        subs = x["sub"] if isinstance(x["sub"], list) else [x["sub"]]
        style = x["voice"]["style"]
        who = f"{names[x['who']]}（{x['who']}）" + (f"・{style}" if style != "normal" else "")
        rows.append(f"| {mmss(bounds[i])}-{mmss(bounds[i + 1])} | {who} | {x['speech']} | {by[x['id']].get('cg', '')} | {' ／ '.join(subs)} | {by[x['id']].get('fact', x['fact'])} |")
    rows.append(f"| {mmss(bounds[-1])}-{mmss(tl['duration'])} | ウラ（W）・共通エンディング | リバース。世界の仕組みを、はじめから。 | "
                f"全動画共通のエンディング（docs/ENDING_SPEC.md）：白い閃光 → 明るい背景に巻き戻しの円弧、大きな「リバース」、タグライン | リバース ／ 世界の仕組みを、はじめから | — |")
    md = [f"# {pid}：{data['title']}", "",
          f"> チャンネル「リバース」新構成（2026-10-26）。テーマ：{data['theme']}",
          f"> `production/{pid}/lines.json`（制作の元データ）と実際の音声の長さから `tools/build_script_md.py` で生成。秒単位の時間と声の設定は `production/{pid}/final_script.md`。", "",
          "## 1. 基本情報", "", "| 項目 | 内容 |", "|------|------|",
          f"| シナリオID | {pid} |", f"| タイトル | {data['title']} |", f"| テーマ | {data['theme']} |",
          f"| 視聴者が得る学び | {meta['learn']} |",
          f"| 尺 | 約 {tl['duration']:.0f} 秒（本編 {tl['ending_start']:.1f} 秒＋共通エンディング {tl['duration'] - tl['ending_start']:.1f} 秒） |",
          f"| この動画の面白さ | {meta['fun']} |", f"| 想定する視聴者の疑問 | {meta['question']} |",
          f"| オモテが巻き込まれる出来事 | {meta['incident']} |", f"| 主な CG 表現 | {meta['cg']} |",
          f"| 声 | {v['M'].get('display', 'オモテ')}＝{v['M']['credit']}、{v['W'].get('display', 'ウラ')}＝{v['W']['credit']}（`voices.json` の `{data['voices']}`） |", "",
          "## 2. フック（冒頭 3 秒）", "", f"- {meta['hook']}", "",
          "## 3. 完全な台本", "",
          "| 時間 | キャラクター・音声 | セリフ | 映像・CGの指示 | 画面字幕 | 事実確認ID |",
          "|------|------------------|--------|---------------|----------|-----------|", *rows, "",
          "- 「キャラクター・音声」の dry／hot／whisper は青山龍星のスタイル（不機嫌／熱血／囁き）。",
          "- 字幕の「／」は、1 つのセリフの中で字幕を切り替える位置。事実確認 ID は同じフォルダの `fact_check.md`。", ""]
    out = ROOT / "scripts" / pid / "script.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    print("wrote", out.relative_to(ROOT.parent))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)
