# pilot_024 事実確認：ソフィー・ブランシャール（設計「悲劇」）

2026-11-01。ChatGPT の結果（`scripts/batch_024_026/gpt_fact_check_prompt.md` への返答）を、Claude が出典で確かめ直した。
判定は `docs/FACT_CHECK_POLICY.md` のラベル。**確認方法**に、本文を読んだのか、検索の要約・抜粋だけなのかを書く。

## 出典
- S1 John Haag, "Blanchard, Madeleine Sophie (1778–1819)", *Women in World History: A Biographical Encyclopedia*（Encyclopedia.com）https://www.encyclopedia.com/women/encyclopedias-almanacs-transcripts-and-maps/blanchard-madeleine-sophie-1778-1819 — **WebFetch で本文から抜き出し**（参考文献：Léon Coutil, *Jean-Pierre Blanchard, physicien-aéronaute*, 1911）
- S2 Smithsonian Magazine「Sophie Blanchard – The High Flying Frenchwoman…」— WebFetch は 403。ChatGPT の要約と検索の抜粋だけ
- S3 Smithsonian Institution「And Away!」https://www.si.edu/collections/snapshot/and-away — ChatGPT の要約だけ（「史上初の女性の職業的気球乗り」、1804 年の初飛行、1805 年の単独飛行）
- S4 米国議会図書館の版画（1811 年 8 月 15 日、ミラノ）の題名 — Wikimedia Commons の記録（`assets.md` の A3）

## 主張

| ID | 台本 | 判定 | 正確な事実・言い方 | 出典・確認方法 |
|---|---|---|---|---|
| FACT-01 | L01・L08 | VERIFIED | 1819 年 7 月 6 日、パリのティヴォリ公園での上昇。67 回目の飛行。花火と「ベンガル花火の冠（crown of Bengal Lights）」を予告していた | S1（本文）。日付は S2・S3 の要約とも一致 |
| FACT-02 | L02・L12 | PARTIALLY_VERIFIED | 「女性として初めての職業の気球乗り」（S3）。台本は「空を飛ぶことを仕事にした、最初の女性」。「航空事故で亡くなった最初の女性」は**「とされる」**で言う | S3（ChatGPT の要約）、S1。検索の抜粋 |
| FACT-03 | L03 | VERIFIED | 夫ジャン＝ピエールは 1785 年 1 月、初めて空からイギリス海峡を越えた（"earliest airborne crossing"）。1808 年 2 月のオランダでの飛行のあと倒れ（脳卒中とみられる）、1809 年 3 月 7 日に死亡。彼女は破産に近く、それもあって飛び続けた | S1（本文）。**「飛行中に倒れ」は「飛行のあとに倒れ」の可能性** → 台本は「1808年の飛行で倒れ」に直す |
| FACT-04 | L05 | VERIFIED | ナポレオンが名誉職（chief of Air Services）に任じ、国の祝典で飛んだ。1810 年 6 月 24 日、皇帝とマリー・ルイーズの結婚の祝いで飛んだ | S1（本文）。称号の原語 "Aéronaute des Fêtes Officielles" は検索の抜粋だけなので画面に出さない |
| FACT-05 | L05b | VERIFIED | 1811 年 8 月 15 日、ミラノで、皇帝・王の一族（LL. AA. II. e RR.）の前で夜に上昇 | S4（版画の題名） |
| FACT-06 | L06 | VERIFIED | アルプスの上、約 9,000 フィートでほとんど凍え、鼻血。1817 年ナントで、水につかった野原を牧草地と見誤って降り、溺れかけた | S1（本文） |
| FACT-07 | L07 | VERIFIED | 夜の上昇で花火を使う見せ物をしていた | S3（ChatGPT の要約）、S1 |
| FACT-08 | L09 | PARTIALLY_VERIFIED | 約 300 メートルで花火が点き、水素に火が移った（S1）。点火の正確な経緯（花火か、ロケットの誤作動か）は資料で違う → 「花火の火が、気球の水素に移った」まで | S1（本文）、検索の抜粋 |
| FACT-09 | L09b | VERIFIED | 観客は着陸を待っていて、爆発に驚いた（"expected a landing"）。**拍手したという話は確認できない → 使わない** | S1（本文） |
| FACT-10 | L10 | VERIFIED | 気球はプロヴァンス通り（ショーシャ通りの角）の家の屋根に落ちた | S1（本文）、検索の抜粋とも一致 |
| FACT-11 | L11 | PARTIALLY_VERIFIED | 燃えた気球の網に絡まり、通りへ落ちた（S2 の要約）。41 歳（1778 年 3 月 25 日生まれ） | S1（生年月日、本文）、S2（要約） |
| FACT-12 | L12 | VERIFIED | 葬儀には「パリじゅう（tout Paris）」が集まった | S1（本文） |
| FACT-13 | L13 | 比喩 | 「花火の夜空が、彼女の最後の舞台になった」は締めの比喩（事実の主張ではない） | — |

## 使わないこと（ChatGPT の注意と Claude の確認）
- 最後の飛行の前の発言（「これが最後」など）：一次資料で確認できない。
- 観客の拍手・叫び声：確認できない（S1 は「着陸を待っていた」）。
- 借金のために危険な飛行を強いられた、と断定しない（S1 は「破産に近く、それもあって」）。
- ルイ 18 世の下での称号：検索の抜粋だけ。台本に入れない。
- ティヴォリ公園の側が遺族に寄付した話：確認できない。

## 物語の核
- 困難：夫の死と破産の寸前 → 一人で飛び続けて仕事にした（FACT-03）。
- 困難：アルプスの上で凍え、洪水の野原で溺れかけた → それでも飛び続けた（FACT-06）。
- 最後の夜：67 回目、花火の冠の予告 → 水素に火（FACT-01・08）。
