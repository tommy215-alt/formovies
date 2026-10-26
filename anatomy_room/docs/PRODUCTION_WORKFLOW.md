# 制作ワークフロー（PRODUCTION_WORKFLOW）

各工程には **開始条件** がある。条件を満たさないまま次の工程に進まない。

| # | 工程 | 担当 | 開始条件 | 成果物 |
|---|------|------|---------|--------|
| 1 | 方針の確認 | Claude | — | `CLAUDE.md`, `docs/` |
| 2 | テーマ選定・調査 | Claude | 工程 1 | 調査メモ、出典候補 |
| 3 | 台本執筆 | Claude | 工程 2 で主な事実の出典が揃っている | `scripts/pilot_00N/script.md` |
| 4 | 事実確認・自己検証（別工程） | Claude | 工程 3 | `fact_check.md`, `reviews/internal_review/` |
| 5 | ChatGPT レビュー資料の生成 | Claude | 工程 4 で判定が出ている | `reviews/chatgpt_review/` |
| 6 | **外部レビューと採用判断** | **ユーザー** | 工程 5 | 採用シナリオの指定、修正指示 |
| 7 | 修正 | Claude | 工程 6 の指示 | 台本・レビュー資料の更新 |
| 8 | 声・外見・美術の決定 | ユーザー＋Claude | 工程 6 で採用が決まった | キャラクター仕様 |
| 9 | 絵コンテ・CG 制作 | Claude | **ユーザーが採用シナリオを明示的に指定した後のみ** | 絵コンテ、CG |
| 10 | 音声合成・字幕・編集 | Claude | 工程 9 | 音声、字幕、動画ファイル（`output/`） |
| 11 | 公開前の最終確認 | ユーザー | 工程 10 | 出典の本文確認、権利確認 |
| 12 | アップロード・公開 | ユーザー（または明示の指示を受けた Claude） | 工程 11 | YouTube 公開 |

## 現在地

- 5 本：第 2 回監査を経て v2 に改訂（`audit/summary.md`）。
- **pilot_005：ユーザーの指示（2026-10-26）で工程 9〜10 を実施し、完成動画を書き出した**（`production/pilot_005/`）。工程 11（公開前の最終確認）と 12（公開）はユーザー待ち。
- 他の 4 本の動画制作は、ユーザーの採用指定があるまで開始しない。

## ChatGPT レビューの回し方（工程 6）

1. `reviews/chatgpt_review/pilot_00N_chatgpt_review.md` を 1 本ずつ ChatGPT に貼り付ける。
2. 末尾の「ChatGPT に特に確認してほしい点」に答えてもらう。
3. 指摘を `reviews/chatgpt_review/feedback/pilot_00N.md`（新規作成）に保存するか、Claude に貼り付けて渡す。
4. 採用するシナリオと修正方針を Claude に伝える。

## 修正時の手順（工程 7）

1. `script.md` と `fact_check.md` を直す。
2. `reviews/internal_review/pilot_00N_review.md` の「修正した箇所」に追記する。
3. `python3 tools/check_scripts.py` で書式・話速・事実 ID の整合を確認する。
4. `python3 tools/build_chatgpt_review.py` でレビュー資料を作り直す。

## 将来の工程のメモ（今回は実施しない）

- 以前の企画（リポジトリ直下）で、Blender + VOICEVOX + FFmpeg による無料の Shorts 制作パイプラインを作った実績がある。
  2 人の掛け合い・キャラクター表示に合わせて流用・拡張できる可能性がある。
- 音声合成エンジンを使う場合は、話者ごとの利用規約とクレジット表記を確認する。
