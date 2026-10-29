# pilot_017：本物の写真・図の権利（2026-10-29 確認）

使うのはパブリックドメイン・CC0・CC BY だけ（ガイドライン v2.2 の 4）。

| ID | 素材 | 出典・ページ | 作者・年 | 権利 | 確認方法 | 使い方・クレジット |
|---|---|---|---|---|---|---|
| A1 | ヘンリエッタ・スワン・リービットの肖像（30 歳ごろ、2388×3171） | https://commons.wikimedia.org/wiki/File:Henrietta_Swan_Leavitt.jpg （ファイル：https://upload.wikimedia.org/wikipedia/commons/0/0c/Henrietta_Swan_Leavitt.jpg ）。Popular Astronomy 30 巻 4 号（1922 年 4 月）などに掲載 | 撮影者不明、1898 年ごろ | パブリックドメイン（米国、1931 年より前の公表。Commons の PD-1923） | Claude が WebFetch でファイルのページを確認 | 「写真：Popular Astronomy (1922) / パブリックドメイン」 |
| A2 | 1912 年の論文の Fig. 2（周期の対数と明るさ。2 本の直線） | HCO Circular 173（1912）、ADS のスキャン https://articles.adsabs.harvard.edu/pdf/1912HarCi.173....1L （John G. Wolbach Library, Harvard-Smithsonian CfA 提供） | Leavitt（署名 E. C. Pickering）、1912 年 | パブリックドメイン（米国、1931 年より前の公表）。古い作品をそのまま写したスキャンには新しい著作権は生じない（米国） | Claude が原論文を画像にして読んだ。ADS のページの利用条件の文言は未確認 | 「図：Harvard College Observatory Circular 173 (1912) / パブリックドメイン」 |
| A3 | アンドロメダ銀河「Sharpest ever view of the Andromeda Galaxy」（heic1502a、長辺 2400 に縮小・回転・切り抜き） | https://esahubble.org/images/heic1502a/ （規約：https://esahubble.org/copyright/ ） | NASA, ESA, J. Dalcanton (University of Washington, USA), B. F. Williams (University of Washington, USA), L. C. Johnson (University of Washington, USA), the PHAT team, and R. Gendler | CC BY 4.0（ESA/Hubble の規約。商用可。クレジットをそのまま。大きく加工したら変更を書く） | Claude が WebFetch で画像のページ（クレジット）と規約のページを確認（2026-10-29） | 画面：「画像：NASA, ESA, J. Dalcanton ほか, R. Gendler（ESA/Hubble）」。説明文に全文と「CC BY 4.0」 |

## 3D の素材（すべて CC0、2026-10-29 に取得）

| 素材 | 出典 | 作者 | 権利 | 使い方 |
|---|---|---|---|---|
| 照明用の画像 HDRI「Wooden Lounge」（1k） | https://polyhaven.com/a/wooden_lounge （API：api.polyhaven.com） | Greg Zaal | CC0（Poly Haven の全素材。https://polyhaven.com/license ） | 部屋の場面の映り込み（PMREM） |
| 木の質感「Wood Table 001」（1k：色・凹凸・粗さ） | https://polyhaven.com/a/wood_table_001 | Dimitrios Savva（撮影）、Rico Cilliers（加工） | CC0 | 机・椅子・腰板・光の箱の枠 |
| 木の床「Old Wood Floor」（1k） | https://polyhaven.com/a/old_wood_floor | Guillaume Monsergent | CC0 | 床 |
| 人体（女性 2 体 × 座る・立つ） | MPFB 2（Blender の拡張、build 20261010）と MakeHuman の system assets（makehuman_system_assets_cc0.zip：服 female_elegantsuit01・female_casualsuit02、靴 shoes02、髪 ponytail01・braid01） | MakeHuman コミュニティ | 作った人体と、この素材の包みは CC0 | `production/pilot_017/assets/make_human.py` で作り GLB に。顔は映さない（後ろ姿・遠景）、手のアップなし。長いスカートとまとめ髪は描画で足した |

※ 描画の部品（three.js r147 の GLTFLoader・RGBELoader・EffectComposer・SSAOPass・BokehPass）は MIT ライセンス（`production/ext/vendor/three147/LICENSE`）。

## 使わないもの

- **ハッブルの「VAR!」の乾板（Carnegie Science）**：非商用・研究・教育のための公開で、出版・配布には許可が要る（ChatGPT の報告・検索の抜粋）。動画では CG で再現し「※再現」と書く。
- **キャノンとリービットの 1913 年の写真**：Commons のファイルのページを確かめられなかった（URL が見つからない）。今回は使わない。
- **ハーバードの乾板の画像（DASCH）**：画像ごとの利用条件を確認できていない。
