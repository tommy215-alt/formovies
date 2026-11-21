# pilot_066 事実確認（2026-11-21、台本 v1）「人間が見つけて、27年で消えた動物」

ユーザーの指示：「世界で絶滅してる動物について。近代でどれくらいペースが上がっているかと、具体的に人類のせいで絶滅した動物のエピソードを入れる（リョコウバトみたいなメジャーなものではなく）」

確認方法の表記：【本文】＝ページの本文を読んだ（curl・WebFetch）。【抄録】＝論文の要旨を Europe PMC の API で読んだ（本文の表は未確認）。【検索】＝検索結果の要約・抜粋で読んだ。【計算】＝自分の計算。

| # | 台本の内容 | 種類 | 確認方法・出典 |
|---|---|---|---|
| 1 | ステラーカイギュウ：1741 年、ベーリング島で見つかった | 事実 | 【本文】ロンドン自然史博物館（NHM）https://www.nhm.ac.uk/discover/stellers-sea-cow-first-historical-extinction-of-marine-mammal-at-human-hands.html ：「formally 'discovered' the sea cows in 1741 when the ship on which he was travelling became marooned on what's now Bering Island」 |
| 2 | 大人は体長 10 メートル、重さ 11 トンにもなった | 事実 | 【本文】同：「adults could reach up to 10 metres in length while weighing up to 11 tonnes」 |
| 3 | ラッコの毛皮を狩りに来た人たちが、食料として狩った | 事実 | 【本文】同：毛皮商人がラッコを見つけ、「they'd stock up on the meat of the Steller's sea cow」 |
| 4 | 1768 年には絶滅。見つかってから、わずか 27 年 | 事実 | 【本文】同：「Within just 27 years of being formally described」「hunted into extinction by 1768」 |
| 5 | いま、脊椎動物が消えるペースは、ふだんの最大 100 倍 | 事実 | 【抄録】Ceballos et al. 2015, Science Advances 1: e1400253（Europe PMC の API で要旨）：「the average rate of vertebrate species loss over the last century is up to 100 times higher than the background rate」。背景絶滅率は 2 E/MSY（従来の 2 倍の控えめな仮定） |
| 6 | この 100 年で消えた数は、自然なら 800 年から 1 万年かかる | 事実 | 【抄録】同：「the number of species that have gone extinct in the last century would have taken, depending on the vertebrate taxon, between 800 and 10,000 years to disappear」 |
| 7 | ニホンカワウソ：明治から毛皮のために獲られ、川の工事や水の汚れで減った | 事実 | 【検索】環境省・EIC ネット・京都府レッドデータブックの要約：減少は「毛皮目的の過剰な捕獲」が主因、のちに河川工事・水質悪化 |
| 8 | 1979 年、高知県の新荘川で撮られたのが最後 | 事実 | 【検索】百科事典系の情報（須崎市の新荘川河口で撮影）。環境省の資料の本文は未確認 |
| 9 | 2012 年、環境省が絶滅と判断 | 事実 | 【検索】環境省 第 4 次レッドリスト（2012 年 8 月）：北海道亜種・本州以南亜種とも「絶滅危惧 IA 類」→「絶滅（EX）」。昭和まで生息した哺乳類が絶滅とされたのは初めて（報道） |
| 10 | クリスマス島（オーストラリア）の小さなコウモリ（クリスマスアブラコウモリ） | 事実 | 【本文】Mongabay 2012-05-23、Scientific American 2009-09-08、Wikipedia |
| 11 | 1994 年から 2006 年で 8 割以上減った | 事実 | 【本文】Mongabay：「Between 1994 to 2006, the population fell by over 80 percent」 |
| 12 | 2009 年 1 月、残り 20 匹ほど。研究者は捕まえて守る計画をすぐ始めるよう国に求めた | 事実 | 【本文】Mongabay：Lumsden 氏が「captive breeding program is established immediately」と警告、「as low as 20 bats」。2006 年にも国の委員会が飼育繁殖を求めた（Wikipedia） |
| 13 | 捕獲の許可が出たのは 2009 年 8 月。見つかったのは、声（超音波）の 1 匹だけ | 事実 | 【本文】Mongabay：「In August 2009, Lumsden was finally given permission to capture bats」「Four weeks of surveying located only a single bat through its echolocation」。Wikipedia は政府の発表を 7 月とする（許可は 8 月で台詞にする） |
| 14 | 8 月 26 日の声が最後の記録 | 事実 | 【本文】Mongabay・Wikipedia：最後の超音波の声は 2009 年 8 月 26 日。IUCN「絶滅を日付で示せる数少ない例」（Mongabay の引用） |
| 15 | 原因ははっきりしない（人が持ち込んだアリやヘビなどが疑われる） | 事実 | 【本文】Mongabay「Scientists still don't know what pushed the bat to extinction」。候補：外来のアリ（yellow crazy ant）、ヘビ（common wolf snake）、オオムカデ、ネコ、ネズミ、殺虫剤など（Wikipedia） |

## 説明・演出（事実ではない）

- 動物は模型の再現（3D）。カイギュウ・カワウソ・コウモリの姿は復元図などをもとにした想像を含む → 画面に「再現」。
- 本物の写真は使う場合だけ assets.md に権利を記録（ニホンカワウソの最後の写真は権利が不明なので使わない）。
