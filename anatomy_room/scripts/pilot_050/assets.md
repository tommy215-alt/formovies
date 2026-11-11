# pilot_050 素材と権利

> PD・CC0・CC BY（と互換の規約）だけ。本物の写真は使わない（もしも設計、すべて CG）。実在の選手・大会の名前やロゴは出さない。

## 3D（すべて自作、Blender 5.2 の Cycles）

- ティラノサウルス（メタボールで組んだ自作の模型）、人のピクトグラム、街・道・門・給水台・バケツ・紙ふぶき・湯気：`production/pilot_050/blender/`（コードで作った）
- 空：Blender の空のノード（手続き的）
- 文字の画像（スタート・ゴール・給水・20km・ゼッケン）：`blender/make_tex.py` で作った（書体は下のとおり）

## 書体

- BIZ UDPゴシック Bold（SIL OFL 1.1）：画面の札
- Dela Gothic One（SIL OFL 1.1）：上のタイトルの帯

## 効果音

- 雑踏：Generic Exterior Walla by brunoboselli https://freesound.org/s/634880/ （CC0、pilot_049 と同じファイル `assets/sfx/crowd.mp3`）
- 金属・打撃：`assets/sfx/break/`：75 CC0 breaking / falling / hit sfx by rubberduck https://opengameart.org/content/75-cc0-breaking-falling-hit-sfx （CC0、`scripts/pilot_046/assets.md`）。この回は metal_01・hit_05 だけを使った
- 号砲・足音・風・水・湯気・息・警告の音・歓声のふくらみ：ノイズと正弦波から合成（`production_script.py`）

## BGM

- なし（もしも設計）。パイプラインの都合で `assets/bgm/Cyborg Ninja.mp3`（Kevin MacLeod、CC BY 4.0）を読み込むが、全区間 音量 0（f_mute）で、動画には入らない。説明文にも書かない。
