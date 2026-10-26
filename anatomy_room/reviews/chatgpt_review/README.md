# ChatGPT レビュー資料

**スマホからは** `copy_page.html`（公開版：https://claude.ai/artifact/MrxPiW8hLtaEUJDx5sDkSZ）を開き、「全文をコピー」を押して ChatGPT に貼り付けてください。

1 ファイル＝1 シナリオ。**ファイルの中身をすべてコピーして、そのまま ChatGPT に貼り付けてください。**
冒頭に ChatGPT への依頼文と前提情報（チャンネル・キャラクター・ラベルの定義・調査環境の制約）が入っているので、追加の説明は不要です。

| ファイル | シナリオ | 自己検証の判定 |
|---------|---------|--------------|
| `pilot_001_chatgpt_review.md` | 送ったメッセージは、空を飛んでいるのか？ | PASS |
| `pilot_002_chatgpt_review.md` | 蛇口の水は、誰が押している？ | PASS |
| `pilot_003_chatgpt_review.md` | コンビニおにぎりの海苔は、なぜパリパリなのか？ | PASS（CG 前に包装の実物確認が必要） |
| `pilot_004_chatgpt_review.md` | エレベーターのロープが切れたら、落ちる？ | PASS |
| `pilot_005_chatgpt_review.md` | マイナス×マイナスは、なぜプラスになる？ | PASS |

各ファイルの構成：依頼文 → A. シナリオ全文 → B. 事実確認リストと出典 URL → C. 自己レビュー結果 → D. 特に確認してほしい点

## 注意

- これらのファイルは `tools/build_chatgpt_review.py` で自動生成しています。**直接編集しないでください**。
  台本を直したら、元ファイル（`scripts/pilot_00N/`、`reviews/internal_review/`）を直してから再生成します。
- ChatGPT の回答は、`feedback/pilot_00N.md` として保存するか、そのまま Claude に貼り付けてください。
