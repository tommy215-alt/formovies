#!/usr/bin/env python3
"""スマホからコピーできる ChatGPT レビュー資料のページ（HTML）を生成する。

reviews/chatgpt_review/pilot_*_chatgpt_review.md を読み込み、
1 ページに 5 本分の「全文コピー」ボタンと、長すぎて貼れないとき用の「パートごとのコピー」ボタンを並べる。
先に build_chatgpt_review.py を実行しておくこと。

使い方: python3 anatomy_room/tools/build_copy_page.py
"""
import base64
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "reviews" / "chatgpt_review"
OUT = SRC / "copy_page.html"
ICON = ROOT / "branding" / "icon_800.png"

# パート分割の見出し（build_chatgpt_review.py の構成に合わせる）
PART_RE = re.compile(r"^## (?:あなたへの依頼|A\. |B\. |C\. |D\. )", re.M)
PART_LABELS = ["依頼文", "A 台本", "B 事実確認", "C 自己レビュー", "D 確認してほしい点"]


def split_parts(text):
    """依頼文（冒頭〜前提情報）/ A / B / C / D に分ける。"""
    starts = [m.start() for m in PART_RE.finditer(text)]
    if len(starts) != 5:
        raise SystemExit(f"見出しが 5 つ見つからない（{len(starts)} 個）")
    starts[0] = 0  # 依頼文には冒頭のタイトルも含める
    bounds = starts + [len(text)]
    return [text[a:b].strip().removesuffix("---").strip() + "\n" for a, b in zip(bounds, bounds[1:])]


def main():
    items = []
    for path in sorted(SRC.glob("pilot_*_chatgpt_review.md")):
        text = path.read_text(encoding="utf-8")
        title = re.search(r"^# ChatGPT レビュー依頼：(.+)（(pilot_\d+)）", text, re.M)
        # 最新の判定（第 2 回監査の「判定：v1 → v2」があればその v2、なければ自己レビューの総合判定）
        part_c = text.split("## C. ", 1)[1]
        latest = re.findall(r"判定：\S+ → (PASS|NEEDS_REVISION|HOLD)", part_c)
        verdict = latest[-1] if latest else (re.search(r"\*\*(PASS|NEEDS_REVISION|HOLD)\*\*", part_c) or [None, "—"])[1]
        parts = split_parts(text)
        head = parts[0]
        items.append({
            "id": title.group(2),
            "title": title.group(1),
            "verdict": verdict,
            "full": text,
            # パート単体で貼っても意味が通るよう、A〜D には依頼文の要約を前置きする
            "parts": [head] + [
                f"（{title.group(2)} のレビュー資料の続きです。前のメッセージの依頼文に従って確認してください）\n\n{p}"
                for p in parts[1:]
            ],
        })

    icon = ""
    if ICON.exists():  # ページを軽くするため 128px に縮小して埋め込む
        from io import BytesIO
        from PIL import Image
        buf = BytesIO()
        Image.open(ICON).convert("RGB").resize((128, 128), Image.LANCZOS).save(buf, "PNG", optimize=True)
        icon = base64.b64encode(buf.getvalue()).decode()
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    cards = "\n".join(card(i, it) for i, it in enumerate(items))
    OUT.write_text(TEMPLATE.replace("%%CARDS%%", cards).replace("%%DATA%%", data)
                   .replace("%%ICON%%", icon), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT.parent)} ({OUT.stat().st_size // 1024} KB, {len(items)} 本)")


def card(i, it):
    n = len(it["full"])
    part_btns = "".join(
        f'<button type="button" class="part" data-i="{i}" data-p="{j}">'
        f'<span>{html.escape(lbl)}</span><small>{len(p):,}字</small></button>'
        for j, (lbl, p) in enumerate(zip(PART_LABELS, it["parts"]))
    )
    return f"""
<article class="card" id="{it['id']}">
  <header>
    <p class="pid">{it['id'].replace('_', ' ').upper()} <span class="verdict{' nr' if it['verdict'] != 'PASS' else ''}">{it['verdict']}</span></p>
    <h2>{html.escape(it['title'])}</h2>
  </header>
  <button type="button" class="copy-all" data-i="{i}">
    <span class="label">全文をコピー</span><span class="count">{n:,}字</span>
  </button>
  <details>
    <summary>長すぎて貼れないときは、パートごとにコピー</summary>
    <p class="hint">上から順に、1 つずつ別のメッセージで送ってください。</p>
    <div class="parts">{part_btns}</div>
  </details>
</article>"""


TEMPLATE = """<title>解剖室レビュー資料</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&family=IBM+Plex+Sans+JP:wght@400;600;700&display=swap">
<style>
/* 1 カラムのカード列。スマホで親指が届く大きなボタンを主役にする */
:root {
  --bg: #F3F6FA; --surface: #FFFFFF; --fg: #0E1A2B; --muted: #546478;
  --line: #D5DEE9; --accent: #0B8FB0; --accent-fg: #FFFFFF; --ok: #1F7A4D; --warn: #A15C00;
  --sans: "IBM Plex Sans JP", "Hiragino Sans", "Noto Sans JP", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0A1424; --surface: #111F36; --fg: #EAF1F8; --muted: #93A8BF;
  --line: #22385A; --accent: #46D3F0; --accent-fg: #06121F; --ok: #5FD39A; --warn: #FFB547; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0A1424; --surface: #111F36; --fg: #EAF1F8; --muted: #93A8BF;
  --line: #22385A; --accent: #46D3F0; --accent-fg: #06121F; --ok: #5FD39A; --warn: #FFB547; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font-family: var(--sans); font-size: 15px; line-height: 1.6; }
.wrap { max-width: 640px; margin: 0 auto; display: grid; gap: 16px;
  padding-block: 20px 48px;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.top { display: flex; gap: 14px; align-items: center; }
.top img { width: 52px; height: 52px; border-radius: 50%; flex: none; }
.top h1 { font-size: 20px; margin: 0; line-height: 1.3; text-wrap: balance; }
.top p { margin: 2px 0 0; color: var(--muted); font-size: 13px; }
.how { margin: 0; padding: 12px 14px; border: 1px solid var(--line); border-radius: 10px;
  color: var(--muted); font-size: 13.5px; }
.how strong { color: var(--fg); }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
  padding: 16px; display: grid; gap: 12px; min-width: 0; }
.card header { display: grid; gap: 4px; }
.pid { margin: 0; font-family: var(--mono); font-size: 12px; letter-spacing: .12em; color: var(--muted);
  display: flex; gap: 8px; align-items: center; }
.verdict.nr { color: var(--warn); }
.verdict { color: var(--ok); border: 1px solid currentColor; border-radius: 99px; padding: 0 8px; letter-spacing: .06em; }
.card h2 { margin: 0; font-size: 17px; line-height: 1.45; text-wrap: balance; }
button { font: inherit; cursor: pointer; }
button:focus-visible, summary:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.copy-all { display: flex; justify-content: space-between; align-items: center; gap: 12px;
  min-height: 56px; padding: 0 18px; border: 0; border-radius: 12px;
  background: var(--accent); color: var(--accent-fg); font-weight: 700; font-size: 16px; }
.copy-all .count { font-family: var(--mono); font-weight: 500; font-size: 13px; opacity: .85;
  font-variant-numeric: tabular-nums; }
.copy-all.done, .part.done { background: var(--ok); color: var(--surface); border-color: var(--ok); }
details summary { color: var(--muted); font-size: 13.5px; cursor: pointer; padding: 4px 0; }
.hint { margin: 6px 0 10px; color: var(--muted); font-size: 13px; }
.parts { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
.part { display: flex; justify-content: space-between; align-items: center; gap: 8px;
  min-height: 44px; padding: 0 12px; border: 1px solid var(--line); border-radius: 10px;
  background: transparent; color: var(--fg); font-size: 14px; text-align: left; }
.part small { font-family: var(--mono); color: inherit; opacity: .7; font-variant-numeric: tabular-nums; }
.fallback { display: grid; gap: 8px; }
.fallback p { margin: 0; font-size: 13px; color: var(--muted); }
.fallback textarea { width: 100%; box-sizing: border-box; height: 160px; font: 12px/1.5 var(--mono);
  background: var(--bg); color: var(--fg); border: 1px solid var(--line); border-radius: 8px; padding: 8px; }
.toast { position: fixed; left: 50%; transform: translateX(-50%);
  bottom: calc(20px + env(safe-area-inset-bottom, 0px));
  background: var(--fg); color: var(--bg); padding: 10px 16px; border-radius: 99px; font-size: 14px;
  opacity: 0; transition: opacity .2s; pointer-events: none; }
.toast.show { opacity: 1; }
@media (prefers-reduced-motion: reduce) { .toast { transition: none; } }
</style>

<main class="wrap">
  <div class="top">
    <img src="data:image/png;base64,%%ICON%%" alt="">
    <div>
      <h1>世界の解剖室　ChatGPT レビュー資料</h1>
      <p>パイロット 5 本・1 本ずつ ChatGPT に貼り付けてレビュー</p>
    </div>
  </div>
  <p class="how"><strong>使い方：</strong>「全文をコピー」を押して、ChatGPT の入力欄に貼り付けて送信。依頼文が入っているので説明は不要です。
  貼り付けが途中で切れる場合は「パートごとにコピー」を使ってください。</p>
  %%CARDS%%
</main>
<div class="toast" id="toast" role="status" aria-live="polite"></div>

<script type="application/json" id="data">%%DATA%%</script>
<script>
const items = JSON.parse(document.getElementById("data").textContent);
const toast = document.getElementById("toast");
let timer;
function say(msg) {
  toast.textContent = msg; toast.classList.add("show");
  clearTimeout(timer); timer = setTimeout(() => toast.classList.remove("show"), 2200);
}
function legacyCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
  document.body.appendChild(ta); ta.select(); ta.setSelectionRange(0, text.length);
  let ok = false; try { ok = document.execCommand("copy"); } catch (e) {}
  ta.remove(); return ok;
}
function showFallback(btn, text) {
  const card = btn.closest(".card");
  let box = card.querySelector(".fallback");
  if (!box) {
    box = document.createElement("div"); box.className = "fallback";
    box.innerHTML = '<p>自動コピーできませんでした。下の欄を長押しして「すべて選択」→「コピー」してください。</p><textarea readonly></textarea>';
    card.appendChild(box);
  }
  const ta = box.querySelector("textarea"); ta.value = text; ta.focus(); ta.select();
}
function markDone(btn) {
  btn.classList.add("done");
  setTimeout(() => btn.classList.remove("done"), 2500);
}
async function copy(btn, text, label) {
  try {
    await navigator.clipboard.writeText(text);
    markDone(btn); say(label + "をコピーしました");
  } catch (e) {
    if (legacyCopy(text)) { markDone(btn); say(label + "をコピーしました"); }
    else showFallback(btn, text);
  }
}
document.addEventListener("click", (ev) => {
  const all = ev.target.closest(".copy-all");
  if (all) { const it = items[+all.dataset.i]; copy(all, it.full, it.id + " の全文"); return; }
  const part = ev.target.closest(".part");
  if (part) {
    const it = items[+part.dataset.i]; const j = +part.dataset.p;
    copy(part, it.parts[j], it.id + " の" + part.querySelector("span").textContent);
  }
});
</script>
"""

if __name__ == "__main__":
    main()
