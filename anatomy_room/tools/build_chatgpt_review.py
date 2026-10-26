#!/usr/bin/env python3
"""ChatGPT 向けレビュー資料（reviews/chatgpt_review/pilot_*_chatgpt_review.md）を生成する。

各シナリオの script.md・fact_check.md・内部レビューを 1 ファイルにまとめ、
冒頭に ChatGPT への依頼文、末尾に「特に確認してほしい点」を置く。
1 ファイルをそのまま ChatGPT に貼り付ければレビューできる形にする。

使い方: python3 anatomy_room/tools/build_chatgpt_review.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reviews" / "chatgpt_review"
ASK_HEADING = "## ChatGPT に特に確認してほしい点"

PREAMBLE = """\
# ChatGPT レビュー依頼：{title}（{pid}）

> この文書は、YouTube Shorts チャンネル「世界の解剖室」のシナリオ 1 本分のレビュー資料です。
> 生成日：{date}。元ファイル：`anatomy_room/scripts/{pid}/` と `anatomy_room/reviews/internal_review/{pid}_review.md`。

## あなたへの依頼

あなたは、科学・技術のファクトチェッカー兼、YouTube Shorts の脚本レビュアーです。
以下のシナリオについて、次の順にレビューしてください。

1. **事実の誤り**：台本のセリフ・字幕・映像指示に、科学的・技術的・歴史的な誤りがないか。
   誤りがあれば、該当する時間とセリフを引用し、正しい内容と、可能なら根拠となる資料を示してください。
2. **誤解を生む簡略化**：間違いではないが、視聴者が誤った結論を導きそうな表現がないか。
3. **事実確認リストの妥当性**：各 FACT の検証結果（VERIFIED / QUALIFIED / UNVERIFIED / INCORRECT）が妥当か。
   出典が主張を本当に裏付けているか、あなたの知識で疑わしい点があれば指摘してください。
4. **掛け合いと構成**：キャラクター設定どおりか、テンポ、わかりやすさ、冒頭の引き、最後の納得感。
5. **末尾の「特に確認してほしい点」** への回答。

最後に、総合判定を **PASS / NEEDS_REVISION / HOLD** のどれかで示し、修正が必要なら具体的な修正案（セリフの書き換え案）を出してください。
確信が持てない点は、推測で断定せず「不確か」と明記してください。

### 前提情報

- **チャンネル**：世界の解剖室（キャッチコピー「見えない仕組みを、CGで解き明かす。」）。縦型 9:16、60〜90 秒、CG・3D・図解中心。
- **M（男性役）**：アホっぽい、好奇心旺盛、少し天然、思い込みが激しい。視聴者の素朴な疑問や勘違いを代弁する。ときに本質を突く。単なる愚か者として描かない。
- **W（女性役、名前未定）**：スマート、知識豊富、論理的、落ち着いている、毒舌。ツッコミは短く知的に。人格否定はしない。
- **台本表の記号**：［比喩］＝映像上の比喩・演出（現実そのものではない）。事実確認ID の `JOKE` ＝キャラクターの冗談（訂正またはオチで回収する）、`—` ＝事実の主張なし。
- **検証ラベル**：VERIFIED＝出典で直接確認／QUALIFIED＝条件・注意点付きで使用可／UNVERIFIED＝根拠不十分／INCORRECT＝誤り。
- **調査環境の制約**：制作環境のネットワーク制限により、出典の本文は直接開けず、検索ツールが返した要約・引用抜粋（「検索抜粋」）で確認しています。抜粋の取り違えや文脈の見落としがありうる点を踏まえてレビューしてください。

---

"""


def section_body(text, heading):
    """'## heading' から次の同レベル見出しの手前までを返す（見出し行は除く）。"""
    m = re.search(rf"^{re.escape(heading)}\s*$", text, flags=re.M)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(r"^## ", rest, flags=re.M)
    return (rest[: n.start()] if n else rest).strip()


def demote(text):
    """見出しを 1 段下げる（まとめた文書の中で階層をそろえるため）。"""
    return re.sub(r"^(#{1,5}) ", r"#\1 ", text, flags=re.M)


def build(pid, date):
    sdir = ROOT / "scripts" / pid
    script = (sdir / "script.md").read_text(encoding="utf-8")
    facts = (sdir / "fact_check.md").read_text(encoding="utf-8")
    review = (ROOT / "reviews" / "internal_review" / f"{pid}_review.md").read_text(encoding="utf-8")

    title = re.search(r"^# \S+：(.+)$", script, flags=re.M).group(1).strip()
    asks = section_body(review, ASK_HEADING)
    review_wo_asks = review.split(ASK_HEADING, 1)[0].rstrip()
    # 各ファイル先頭の H1 は、まとめた文書では不要
    strip_h1 = lambda t: re.sub(r"\A# .*\n+", "", t)

    parts = [
        PREAMBLE.format(title=title, pid=pid, date=date),
        "## A. シナリオ全文\n\n" + demote(strip_h1(script)).strip(),
        "## B. 事実確認リストと出典 URL\n\n" + demote(strip_h1(facts)).strip(),
        "## C. 自己レビュー結果\n\n" + demote(strip_h1(review_wo_asks)).strip(),
        "## D. ChatGPT に特に確認してほしい点\n\n" + asks,
    ]
    return "\n\n---\n\n".join(parts).rstrip() + "\n"


def main():
    import datetime
    date = datetime.date.today().isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    pids = sorted(p.name for p in (ROOT / "scripts").glob("pilot_*") if (p / "fact_check.md").exists())
    for pid in pids:
        path = OUT / f"{pid}_chatgpt_review.md"
        path.write_text(build(pid, date), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT.parent)} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
