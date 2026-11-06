# 完成動画の品質検査（pilot_045）

- 対象：`reverse_045_zombie_tokyo.mp4`
- 検査：`tools/video_qa.py`（MASTER_VIDEO_TEMPLATE の固定ルール）

## 1. 基本仕様

| 項目 | 結果 | 値 |
|---|---|---|
| 解像度 1080×1920 | OK | 1080×1920 |
| 30fps | OK | 30/1 |
| 映像 H.264 | OK | h264 |
| 音声 AAC 48kHz | OK | aac 48000 |
| 尺 70 秒以内 | OK | 58.10 秒 |

## 2. 字幕の欠落

- セリフ 17 行の途中のコマで、字幕の帯が出ているかを調べた（帯の中心 180px の 20% 以上が暗い色なら「出ている」）。
- 見つからなかった行：なし

## 3. 最初のコマ（自動のサムネイルになる）

- 平均輝度 18（225 以下）、くっきり度 1.9（本編の中央値 4.0 の 60% 以上）：**要確認**（白飛び・ぼやけ。サムネは thumbnail.png を使うか、最初のコマを止め絵にする）
- サムネイル画像 `thumbnail.png`：なし（node ../common/render_frames.js --dir . --thumb で作る）

## 4. 文字の自動検査（textcheck）

- 全編 581 コマ（0.1 秒ごと）
- 0.3 秒を超えて続く問題：right_ui「1m」56.6秒、small「1m」56.6秒、right_ui「10m」56.6秒、small「10m」56.6秒、right_ui「100m」56.6秒、small「100m」56.6秒、right_ui「1km」56.6秒、small「1km」56.6秒、small「10km」56.6秒、small「100km」56.6秒、small「1000km」56.6秒、right_ui「高さ 1.6 m」0.7秒、right_ui「高さ 1.5 m」3.9秒、overlap「一体現れたら？ ／ 1000km」3.3秒、right_ui「高さ 2.2 m」1.0秒、right_ui「高さ 2.4 m」0.6秒、right_ui「高さ 6.0 m」0.8秒、overlap「10m ／ 高さ 6.0 m」0.8秒、right_ui「高さ 22 m」1.2秒、right_ui「高さ 23 m」0.5秒、right_ui「高さ 24 m」0.4秒、right_ui「高さ 25 m」0.5秒、right_ui「高さ 26 m」1.2秒、right_ui「高さ 2.8 m」0.5秒、right_ui「高さ 3.3 m」0.4秒、overlap「10km ／ 高さ 5.2 km」0.4秒、overlap「100km ／ 高さ 50 km」0.5秒、right_ui「高さ 2.3 m」0.4秒、right_ui「高さ 3.4 m」0.8秒、overlap「10m ／ 高さ 3.4 m」0.8秒、overlap「1000km ／ 高さ 360 km」0.6秒、overlap「1000km ／ 高さ 520 km」0.4秒、overlap「1000km ／ 高さ 560 km」0.6秒
- フォントにない文字：なし

## 5. 共通エンディング

- **NG**：

## 冒頭 3 秒

| 項目 | 結果 | 値 |
|---|---|---|
| 最初のナレーションの開始 1.0 秒以内 | OK | 0.10 秒（「東京に、ゾンビが一体、現れたら？…」） |
| 最初の 1 秒が無音でない（−40 dBFS 以上） | OK | -17.2 dBFS |
| 最初の 3 秒の音の大きさ（目安 −30 dBFS 以上） | OK | -15.5 dBFS |
| 画面が止まっていない（0.5 秒ごとのコマの差の平均 3 以上） | OK | 7.9 |

- 切り出し：`qa/hook_3s.mp4`（音つき）と `qa/hook_strip.jpg`（0.5 秒ごと）。
- **判断基準：初めて見る人が、この先を見たいと思うか。** 弱ければ冒頭を作り直す（VIDEO_QA_CHECKLIST の「冒頭 3 秒」に記入）

## 目視用の一覧

- `qa/sheet_0.jpg`〜`qa/sheet_2.jpg`（1 秒ごと 58 コマ）。**全部を目で見て** VIDEO_QA_CHECKLIST の C 欄に記入する

## 判定

- 自動検査：**要対応**：最初のコマ、文字の自動検査、共通エンディング
- 自動検査は完了の判定ではない。目視（VIDEO_QA_CHECKLIST）を済ませてから完成とする。
