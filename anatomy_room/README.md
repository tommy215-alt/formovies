# 世界の解剖室 — YouTube Shorts Studio

> **見えない仕組みを、CGで解き明かす。**

日常・科学・テクノロジー・自然・歴史・社会の「普段は意識しない仕組み」を、CG と 2 人の掛け合いで解き明かす
YouTube Shorts チャンネルの制作プロジェクトです。

## 現在の状態

**パイロット 5 本は第 2 回監査を経て v2 に改訂済み。第 1 話（pilot_005）と第 2 話（pilot_003、演出刷新版）の完成動画を制作しました。**

- 第 1 話：`production/pilot_005/world_anatomy_pilot_005.mp4`（制作方法は `production/pilot_005/production_notes.md`）
- 第 2 話：`production/pilot_003/world_anatomy_pilot_003.mp4`（制作方法は `production/pilot_003/production_notes.md`、改善点は `production/pilot_003/IMPROVEMENTS_FROM_EP1.md`）
- 全動画共通のエンディング：`docs/ENDING_SPEC.md`
- 監査：`audit/summary.md`
- **運営者向けマニュアル（PDF）**：`docs/manual/shorts_manual.pdf`（元は `docs/manual/manual.html`。`node anatomy_room/docs/manual/build_manual.js` で再生成）

| ID | タイトル | 分野 | 判定 |
|----|---------|------|------|
| pilot_001 | 送ったメッセージは、空を飛んでいるのか？ | インターネット | PASS |
| pilot_002 | 蛇口の水は、誰が押している？ | インフラ（水道） | PASS |
| pilot_003 | コンビニおにぎりの海苔は、なぜパリパリなのか？ | 日常・食品包装 | v3 に改訂・**動画化済み**（第 2 話。開封手順は模式図と明記） |
| pilot_004 | エレベーターのロープが切れたら、落ちる？ | 機械・安全・歴史 | PASS |
| pilot_005 | マイナス×マイナスは、なぜプラスになる？ | 数学 | PASS・**動画化済み** |

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
│   ├── RESEARCH_ENVIRONMENT.md   # 調査環境の制約（ネットワーク制限）
│   └── ENDING_SPEC.md            # 全動画共通のエンディング
├── scripts/                      # シナリオ（※動画のプログラムではなく「台本」）
│   └── pilot_00N/
│       ├── script.md             # 基本情報・フック・完全な台本
│       └── fact_check.md         # 事実確認リスト・出典・事実と演出の区別
├── reviews/
│   ├── internal_review/          # 自己レビュー（pilot_00N_review.md, SUMMARY.md）
│   └── chatgpt_review/           # ChatGPT にそのまま貼れるレビュー資料（自動生成）
├── audit/                        # 第 2 回監査の報告書（pilot_00N_audit.md, summary.md）
├── production/common/            # 全話共通：声の設定 voices.json、エンディング ending.js、three.js
├── production/pilot_005/         # 第 1 話の制作物（完成動画・制作スクリプト・完成台本・検証記録）
├── production/pilot_003/         # 第 2 話の制作物（3D・明るい画面・新しい声）
├── templates/
│   └── script_template.md        # 新しいシナリオのひな形
├── branding/                     # チャンネルのアイコン・ヘッダー（render.js で生成）
├── tools/
│   ├── check_scripts.py          # 台本の書式・話速・事実 ID の整合チェック
│   ├── build_chatgpt_review.py   # ChatGPT レビュー資料の生成
│   ├── build_copy_page.py        # スマホ用コピーページ（copy_page.html）の生成
│   └── measure_tts.py            # VOICEVOX で全セリフを合成して尺を実測
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
python3 anatomy_room/tools/build_copy_page.py       # スマホ用コピーページを作り直す
node anatomy_room/branding/render.js                # アイコン・ヘッダーを作り直す（要 Noto Sans CJK JP）
```

## 次にやること（ユーザー）

1. `reviews/chatgpt_review/pilot_00N_chatgpt_review.md` を 1 本ずつ ChatGPT に貼り付けてレビューする。
2. 指摘と、採用するシナリオを Claude に伝える。
3. （公開前）各 `fact_check.md` の出典 URL を開いて本文を確認する。
