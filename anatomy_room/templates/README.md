# templates/ — ショート動画の標準テンプレート（チャンネル「リバース」）

次回以降の制作は、このフォルダから始める。チャットの記憶に頼らず、ここのファイルだけで同じ品質とスタイルを再現できるようにしてある。

| ファイル | 内容 | いつ使う |
|---|---|---|
| `MASTER_VIDEO_TEMPLATE.md` | 標準仕様。固定ルール [F] と可変ルール [V] | 制作の前に必ず読む |
| `VIDEO_PRODUCTION_PROMPT.md` | 制作依頼のテンプレート（題材・事実・長さ・追加条件を埋めるだけ）と、Claude 側の手順 | 新作を頼むとき |
| `VIDEO_QA_CHECKLIST.md` | 完成動画の品質検査表 | 書き出した後、納品の前 |
| `ANALYSIS_pilot_006.md` | 基準にした完成動画（窓の回）の分析。テンプレートの根拠 | ルールを変えるかどうか迷ったとき |
| `SAMPLE_REQUEST_can_bottom.md` | 再現テスト（別の題材で依頼を書いた例） | 依頼の書き方の見本 |

関連する道具：
- `tools/video_qa.py`：完成動画の自動検査（仕様・字幕の欠落・最初のコマ・文字の検査結果・エンディング）と、目視用の一覧（`--sheets`）。
- `production/common/`：制作の共通部品（pipeline・stage.js・music.py・ending.js）。テンプレートの固定ルールの多くは、ここのコードで守られる。

## 運用

1. **新作**：`VIDEO_PRODUCTION_PROMPT.md` の依頼文を埋めて渡す。台本までで止まるので、ChatGPT レビューの後にシナリオを指定する。
2. **完成の判定**：`VIDEO_QA_CHECKLIST.md` を埋めた `production/pilot_00N/qa_checklist.md` が揃ってから完成とする。
3. **ルールの変更**：固定ルールを変えるときはユーザーの承認を得る。`MASTER_VIDEO_TEMPLATE.md` の版を上げ、変更前は `templates/versions/` に残す。
4. **見直し**：3〜5 本ごとに、完成動画で `ANALYSIS_*.md` と同じ分析をし、テンプレートとずれていないかを確かめる。
