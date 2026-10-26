# 世界の解剖室 — YouTube Shorts Studio

> **見えない仕組みを、CGで解き明かす。**

日常・科学・テクノロジー・自然・歴史・社会の「普段は意識しない仕組み」を、CG と 2 人の掛け合いで解き明かす
YouTube Shorts チャンネルの制作プロジェクトです。

## 現在の状態

**パイロット 5 本のシナリオ制作と自己検証が完了し、ユーザーによる ChatGPT レビュー待ちです。**
動画（CG・音声・書き出し）は、採用シナリオが指定されるまで制作しません。

| ID | タイトル | 分野 | 判定 |
|----|---------|------|------|
| pilot_001 | 送ったメッセージは、空を飛んでいるのか？ | インターネット | PASS |
| pilot_002 | 蛇口の水は、誰が押している？ | インフラ（水道） | PASS |
| pilot_003 | コンビニおにぎりの海苔は、なぜパリパリなのか？ | 日常・食品包装 | PASS |
| pilot_004 | エレベーターのロープが切れたら、落ちる？ | 機械・安全・歴史 | PASS |
| pilot_005 | マイナス×マイナスは、なぜプラスになる？ | 数学 | PASS |

## ファイル構成

```
anatomy_room/
├── README.md                     # このファイル
├── docs/
│   ├── CHANNEL_POLICY.md         # チャンネルの目的・テーマ・動画仕様
│   ├── CHARACTER_GUIDE.md        # M と W の設定、掛け合いのルール
│   ├── SCRIPT_RULES.md           # 台本の構成・書式・字幕
│   ├── FACT_CHECK_POLICY.md      # 事実確認・出典管理・判定ラベル
│   ├── PRODUCTION_WORKFLOW.md    # 工程と開始条件
│   └── RESEARCH_ENVIRONMENT.md   # 調査環境の制約（ネットワーク制限）
├── scripts/                      # シナリオ（※動画のプログラムではなく「台本」）
│   └── pilot_00N/
│       ├── script.md             # 基本情報・フック・完全な台本
│       └── fact_check.md         # 事実確認リスト・出典・事実と演出の区別
├── reviews/
│   ├── internal_review/          # 自己レビュー（pilot_00N_review.md, SUMMARY.md）
│   └── chatgpt_review/           # ChatGPT にそのまま貼れるレビュー資料（自動生成）
├── templates/
│   └── script_template.md        # 新しいシナリオのひな形
├── tools/
│   ├── check_scripts.py          # 台本の書式・話速・事実 ID の整合チェック
│   └── build_chatgpt_review.py   # ChatGPT レビュー資料の生成
└── output/                       # 完成動画の書き出し先（現在は空）
```

依頼時の構成案から変えた点：
- リポジトリ直下には以前の別企画（黒板の動画）のファイルと `scripts/`（動画パイプラインのプログラム）があるため、
  名前の衝突を避けて、このプロジェクトを `anatomy_room/` にまとめた。今後のセッションでも読まれるよう、`CLAUDE.md` はリポジトリ直下に置いた。
- 書式チェックとレビュー資料の生成を自動化する `tools/` を追加した。
- 調査環境の制約を記録する `docs/RESEARCH_ENVIRONMENT.md` を追加した。

## よく使うコマンド

```bash
python3 anatomy_room/tools/check_scripts.py         # 台本の機械チェック
python3 anatomy_room/tools/build_chatgpt_review.py  # ChatGPT レビュー資料を作り直す
```

## 次にやること（ユーザー）

1. `reviews/chatgpt_review/pilot_00N_chatgpt_review.md` を 1 本ずつ ChatGPT に貼り付けてレビューする。
2. 指摘と、採用するシナリオを Claude に伝える。
3. （公開前）各 `fact_check.md` の出典 URL を開いて本文を確認する。
