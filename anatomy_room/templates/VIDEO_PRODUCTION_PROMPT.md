# VIDEO PRODUCTION PROMPT — 次回からの制作依頼テンプレート

> 使い方：下の「依頼文」をコピーし、【入力】の 4 項目（＋任意項目）だけ埋めて Claude に渡す。
> 書かなかった項目は `anatomy_room/templates/MASTER_VIDEO_TEMPLATE.md` の既定値を自動で使う。
> このファイルだけで次の会話から始められるように書いてある（チャットの記憶に頼らない）。

---

## 依頼文（ここからコピー）

```
リバースの新作ショート動画を作ってください。

【入力】（必須）
- 今回の題材：
- 動画で伝えたい事実（箇条書き。出典が分かれば添える）：
  -
  -
- 想定する動画の長さ：（例：本編 65 秒前後。未記入なら既定）
- 必要な追加条件：（例：なし／オモテに〇〇をさせたい／〇〇には触れない）

【入力】（任意。未記入なら MASTER の既定）
- 制作の範囲：台本まで ／ 台本＋動画（既定：台本まで。動画は私がシナリオを指定してから）
- 冒頭の事件のアイデア：
- BGM のテンポ・雰囲気：（既定：テクノ 125〜150 BPM の中から題材に合わせて）
- 入れたい数字・図：
- 避けたい表現：

【守ること】
- anatomy_room/templates/MASTER_VIDEO_TEMPLATE.md の固定ルール [F] をすべて守る。可変ルール [V] は題材に合わせて決め、決めた内容を scene_plan.md に書く。
- 最初に CLAUDE.md と MASTER_VIDEO_TEMPLATE.md を読む。
- 事実確認は FACT_CHECK_POLICY.md に従う（確認方法を書く。検索の抜粋なら「検索抜粋」）。
- 文字の品質は TEXT_QUALITY.md と VIDEO_QA_CHECKLIST.md に従う。一箇所でも文字切れ・文字化け・はみ出しが残れば納品しない。
- 確かめていない項目を「確認済み」と書かない。
- 課金・外部サービスの契約・YouTube への投稿はしない。
- 既存の台本や設定を上書きする前にバックアップを取る。
```

---

## Claude 側の手順（依頼を受けたら、この順で進める）

### 0. 準備
- `CLAUDE.md` → **`templates/REVERSE_STANDARD_RULES.md`（最優先の既定値、v2）** → `templates/MASTER_VIDEO_TEMPLATE.md` → `docs/` の関連文書を読む。
- 新しい番号のフォルダを決める（`scripts/pilot_00N/`、`production/pilot_00N/`）。

### 1. 事実確認（`scripts/pilot_00N/fact_check.md`）
- 【伝えたい事実】を 1 つずつ確認し、判定ラベル（`FACT_CHECK_POLICY.md`）と確認方法を書く。
- 数字は計算の前提を書く（窓の回の「約 50kg 分」＝客室高度 8,000ft・上空 35,000ft の標準大気で計算）。
- 確認できない事実は台本に入れないか、「〜と言われている」にする。

### 2. 台本（`production/pilot_00N/lines.json` → `scripts/pilot_00N/script.md`）
- MASTER §8 の骨組みで 20〜30 行。各行に `who`（M/W）・`speech`（読む文）・`sub`（字幕）・`style`・`fact`・`cg`。
- オモテに「間違った仮説」と「鋭い気づき」を必ず 1 つずつ。ウラの毒舌は人格否定にしない。
- `python3 anatomy_room/tools/measure_tts.py` で尺を実測（本編 60〜75 秒に収める）。
- `python3 anatomy_room/tools/build_script_md.py pilot_00N`
  → `check_scripts.py` → `build_chatgpt_review.py` → `build_copy_page.py`。
  コピーページの Artifact（https://claude.ai/artifact/MrxPiW8hLtaEUJDx5sDkSZ）を同じファイルで再公開する。
- **ここで止めて、ユーザーの ChatGPT レビューとシナリオ指定を待つ**（制作の範囲が「台本＋動画」でも、指定があるまで CG・音声合成・書き出しをしない）。

### 3. 演出設計（`production/pilot_00N/production_script.py`・`scene_plan.md`）
- **v2（2026-10-27〜）**：EP は `production/common/standard.py` の `standard.config({...})` で作る（ロゴなし・BGM `tech_drive`・やわらかい効果音・`lead_in` 0.1 秒が既定値で入る）。`lines.json` の `"voices"` は `"v7"`。
  - その回で書くのは `out`、`cues`、`sfx`、`music.sections`（doc_hook → doc_drive／doc_build／doc_break／doc_peak → doc_outro → ending）、`segments`、`scenes`、`plan_notes`。
  - 旧版（v1 まで）：既存の回（`pilot_006`）の `production_script.py` をひな形にして、EP の設定をすべて書いていた（`lead_in: 1.5` など）。
- `renderer.html` は `pilot_006/renderer.html` を土台にし、場面関数（SCN）だけ題材に合わせて作り替える。
  - 共通部品（`common/stage.js`）は直接変えない。足りない部品は stage.js に追加し、3 本の textcheck をやり直す。
- **冒頭 3 秒を最初に決める**（REVERSE_STANDARD_RULES の「冒頭 3 秒のルール」）：1 秒目の刺激（映像・音）、矛盾や意外性のある最初の一文、BGM の 1 拍目と効果音の位置、最初のコマ（止め絵として成り立つか）。書き出し前に冒頭の静止画を確認し、完成後は `qa/hook_3s.mp4` で「続きを見たいか」を判断する。
- 注記（uiNote）は v2 の基準で必要なものだけにする。左上のロゴは出さない。

### 4. 書き出しと検査
```bash
# VOICEVOX ENGINE を 127.0.0.1:50021 で起動しておく
cd anatomy_room/production/pilot_00N
python3 production_script.py all          # voice → audio → textcheck → render → mux → docs → qc
node ../common/render_frames.js --dir . --thumb   # サムネ用 thumbnail.png
python3 ../../tools/video_qa.py pilot_00N --sheets
```
- `VIDEO_QA_CHECKLIST.md` を上から埋める（自動 → 目視 → 音 → 事実 → 報告）。
- 直したら書き出し直し、もう一度、全編を目視する。

### 5. 報告
- 変更内容、動画の保存先、目視で確認した範囲（何秒〜何秒・何コマ）、残っている問題、確かめていない項目。

---

## 入力が足りないときの既定値（MASTER より）

| 項目 | 既定 |
|---|---|
| 長さ | 本編 65 秒前後（60〜75 秒）、全体 90 秒以内 |
| 制作の範囲 | 台本まで（動画はユーザーのシナリオ指定の後） |
| 冒頭の事件 | 題材の「ありえない瞬間」をギャグ演出で（「※ギャグ演出」と明記）→ 巻き戻し |
| BGM | テクノ。既存の 3 スタイルから選ぶか、125〜150 BPM の新しいスタイルを足す |
| 数字 | 1〜2 個まで。概算なら「※概算」 |
| 場面数 | 10〜12（エンディングを含む） |
| オチ | オモテの負け惜しみ → ウラの毒舌 → BGM を止めて冷静なひと言 → 立ち直り → 共通エンディング |
