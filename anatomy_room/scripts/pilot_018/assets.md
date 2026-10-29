# pilot_018：本物の写真・図の権利（2026-10-29 確認）

使うのはパブリックドメイン・CC0・CC BY だけ（ガイドライン v2.2 の 4）。

| ID | 素材 | 出典・ページ | 作者・年 | 権利 | 確認方法 | 使い方・クレジット |
|---|---|---|---|---|---|---|
| A1 | ルイ・パスツールの肖像写真（修復版、2388×3292） | https://commons.wikimedia.org/wiki/File:Louis_Pasteur,_foto_av_Paul_Nadar,_Crisco_edit.jpg （元：Smithsonian Institution Libraries） | ポール・ナダール（1856–1939）、1895 年より前 | パブリックドメイン（Commons：Public Domain Mark 1.0、PD-old-80-expired。撮影者の没後 80 年超） | Claude が WebFetch でファイルのページを確認 | 「写真：Paul Nadar／パブリックドメイン」 |
| A2 | 版画「Louis Pasteur (left) watching a colleague trephining a chloroformed rabbit during his research on rabies vaccination」（1885 年 11 月 21 日、ロンドン） | https://wellcomecollection.org/works/jxdzwjnq （画像 V0028849） | 作者不明、1885 年 | Public Domain Mark（Wellcome Collection の API で license「pdm」を確認） | Claude が Wellcome Collection の API（catalogue/v2/works/jxdzwjnq）で確認 | 「版画（1885）：Wellcome Collection／パブリックドメイン」 |

## フォント・3D の素材

| 素材 | 出典 | 権利 | 使い方 |
|---|---|---|---|
| Dela Gothic One | https://github.com/google/fonts/tree/main/ofl/delagothicone （`production/pilot_018/assets/fonts/`、OFL.txt 同梱） | SIL Open Font License 1.1（動画への使用・商用可） | 叩きつける文字・字幕（この回だけの「派手」の試し）。使う文字だけに絞って埋め込み |
| Mochiy Pop One | https://github.com/google/fonts/tree/main/ofl/mochiypopone | SIL Open Font License 1.1 | 小さな文字・札 |
| HDRI・木の質感 | Poly Haven（pilot_017 と同じ：wooden_lounge・wood_table_001・old_wood_floor） | CC0 | 研究室・病室・汽車・講堂 |
| 人体（少年・母親・パスツール・医師・門番 × 立つ・座る・歩く・うつむく） | MPFB 2＋MakeHuman system assets（`production/pilot_018/assets/make_human.py`） | CC0 | 顔は映さない（後ろ姿・逆光のシルエット・遠景）、手のアップなし |

## 使わないもの

- **「Louis Pasteur and his rabies patients」（Paul Renouard による版画、1886）**：Wellcome Collection の API で CC BY-NC（商用不可）。
- **「Rabies vaccination in Pasteur's laboratory in Paris」（Gsell・Pirodon の石版画）**：検索の抜粋で CC BY-NC 4.0（Commons の表示とも食い違う）。使わない。
- **ジョゼフ・マイスターの写真、ジュピーユの像、乾かした脊髄の瓶の写真**：本人・現物の同定と権利を確かめられない（ChatGPT の報告）。CG で再現する。
- **狂犬病ウイルスの電子顕微鏡写真**：個別の権利を未確認。今回は使わない。
