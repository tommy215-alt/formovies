# pilot_045 の素材と権利（もしも設計）

> PD・CC0・CC BY（と互換の規約）だけ。本物の写真は使わない（CG と計算の地図だけ）。

## データ（計算と地図）

- 人口：2020 年国勢調査 1 km メッシュ（e-Stat 統計地図、statsId T001140）。政府統計の利用規約（出典を書けば加工・公開してよい、CC BY 4.0 と互換）。
- 昼間人口：東京都「東京都の昼間人口（令和 2 年）」第 1 表。東京都の利用規約（CC BY 4.0 と互換）。
- メッシュと区市町村の対応：総務省統計局「市区町村別メッシュ・コード一覧」。
- 陸地の形：Natural Earth 10m land（パブリックドメイン）。
- 都庁・新宿の街は模式（実際の建物の形ではない）。建物の高さは昼間人口から作った。

## 音楽

- v2（2026-11-06〜）は BGM なし（ユーザーの指示「BGMを消して、環境音を強く」）。曲のファイルは制作の土台の都合で読み込むが、全区間の音量 0（f_mute）。
- v1 で使った曲：**Cyborg Ninja**（Kevin MacLeod、incompetech、CC BY 4.0）。権利の確認は `scripts/pilot_035/assets.md`。

## v2 で加えた効果音（OpenGameArt、すべて CC0。2026-11-06 に各ページの License(s) 欄が CC0 であることを確かめた）

- ゾンビのうめき声（`assets/sfx/groan/grunt_1〜24.mp3`）：Zombies Sound Pack by artisticdude https://opengameart.org/content/zombies-sound-pack （zombies.zip の zombie-1〜24.wav を mp3 に）
- ゾンビのうめき声（`groan/undead_1〜4.mp3`）：Undead Moans by AntumDeluge https://opengameart.org/content/undead-moans （同梱の LICENSE.txt も CC0 1.0）
- うめき声（`groan/moans.mp3`）：zombie moans by Darsycho https://opengameart.org/content/zombie-moans
- 悲鳴（`scream/scream_a.mp3`）：Female Scream 1 by Nocturnal_Vanguard https://opengameart.org/content/female-scream-1
- 悲鳴（`scream/scream_b.mp3`）：Female High Pitched Scream SFX by WuxiaScrub https://opengameart.org/content/female-high-pitched-scream-sfx
- 悲鳴（`scream/scream_c.mp3`）：Horror Scream1 by Vinrax https://opengameart.org/content/horror-scream1
- 悲鳴は音程を変えて（低め＝男性の声に近く）別の人の声として散らす。時計の音は自前の合成（production_script.py の `_tick`）。

## 効果音（Freesound、CC0。前の回で各ページのライセンスを確かめたもの）

- crowd：Generic Exterior Walla by brunoboselli https://freesound.org/s/634880/ （pilot_043）
- radio：Radio Noise.wav by RutgerMuller https://freesound.org/s/50750/ （pilot_040）
- heli：Helicopter Flyby / Pass by mil0001 https://freesound.org/s/241190/ （pilot_039）
- heart：Heartbeat Sound [60bpm] by Seth_Makes_Sounds https://freesound.org/s/850306/ （pilot_038）
- breath：Scared Male Heavy Breathing by casiba842 https://freesound.org/s/554307/ （pilot_038）
- wind：Howling winter storm ambient sounds by DBlover https://freesound.org/s/505999/ （pilot_044）
- 札のクリック音：自前の合成（ambience.click）

## 3D

- すべて Blender で自前に作った模式（人物は顔のないピクトグラム）。
