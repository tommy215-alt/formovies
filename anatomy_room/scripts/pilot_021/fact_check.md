# pilot_021：事実確認リスト（アンドレーの北極気球探検、1897 年）

調査日：2026-10-30（ユーザーの PC のセッション）。確認方法の定義は `docs/FACT_CHECK_POLICY.md`。設計「悲劇」（3 回目の更新）。

**確認の流れ**：ChatGPT の報告（`gpt_fact_check_prompt.md` への回答）を下書きにし、Claude が主な出典に当たり直した。WebFetch は本文を取得し、小さなモデルが質問に沿って抜き出す方法（全文を一字一句は読んでいない）。日記の原本（スウェーデン語）は未確認。

## 物語の核

- **困難**：出発直後に向きを操る引き綱の一部を失い、操縦できなくなった（S1）。雨と霧で気球に氷がつき、約 65 時間で氷の上に降りた（S1）。約 3 か月・約 400 km、氷の上を歩いた（S1）。
- **本人たちがしたこと**：伝書鳩で通信を送った（「All well on board」、S3）。そりを引いて歩き続け、10 月初めにクヴィト島に着いた（S1）。ストリンドベリは写真を撮り続けた（S4）。
- **結末**：1930 年 8 月、ノルウェーの調査隊（グンナル・ホルン）が遺体を見つけた（S1）。死因は今も分かっていない（S1・S5）。フィルムが現像され、探検の写真が残った（S4）。

## 出典

| ID | 資料 | URL | 確認方法 |
|---|---|---|---|
| S1 | Svalbard Museum「The Andrée Expedition」 | https://svalbardmuseum.no/en/the-andre-expedition | **Claude が WebFetch で本文を確認** |
| S2 | Grenna Museum「The Andrée Expedition」 | （ChatGPT の報告による。Claude は本文を取得できなかった） | ChatGPT の報告のみ |
| S3 | 伝書鳩の通信（7 月 13 日）：H. Lachambre & A. Machuron『Andrée and His Balloon』（1898、Project Gutenberg 63603）、1897・1930 年の新聞（Papers Past） | https://gutenberg.org/files/63603/63603-h/63603-h.htm ・ https://paperspast.natlib.govt.nz/newspapers/DOM19300827.2.64 | 検索の抜粋のみ（資料どうしで文面は一致。鳩を撃った人・日は資料で違う） |
| S4 | Moderna Museet「Biographies – the first photographers」、収蔵品のシリーズ「Ingenjör Andrées luftfärd」 | https://www.modernamuseet.se/ ・ https://sis.modernamuseet.se/ | ChatGPT の報告＋Claude の検索の抜粋（「93 枚」は Claude の検索では確認できず） |
| S5 | M. Personne「Andrée-expeditionens män dog troligen av botulism」Läkartidningen 97(12), 2000 | PubMed 10765627 | 検索の抜粋（書誌）のみ。「死因はまだ決まっていない」の裏づけ |
| S6 | Polarhistorie.no「1930 Bratvaag-ekspedisjonen」 | （ChatGPT の報告による） | ChatGPT の報告のみ（8 月 6 日の発見） |

## 事実確認リスト

### FACT-01（冒頭）
- **主張**：1930 年、北極圏の島（クヴィト島）で、33 年前（1897 年）に消えた 3 人が見つかった。カメラには、まだ現像されていないフィルムが残っていた。
- **出典**：S1（"in August 1930, a Norwegian expedition to Franz Josef Land led by Gunnar Horn happened upon the men's remains"）、S4（フィルムは 1930 年に見つかり、ジョン・ヘルツベリが現像した）、S6
- **検証結果**：VERIFIED（S1 は WebFetch、フィルムは S4 の検索の抜粋と ChatGPT の報告）
- **注意点**：「北極の島」ではなく「北極圏の島」。フィルムが無傷だったとは言わない。

### FACT-02
- **主張**：アンドレーは水素の気球で北極点を目指した。隊員はアンドレー・ストリンドベリ・フレンケル。
- **出典**：S1（"11 July 1897, Salomon August Andrée, Nils Strindberg, and Knut Frænkel set off for the North Pole"、水素の気球「Örnen」）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：役割（ストリンドベリ＝写真、フレンケル＝技術者）は ChatGPT の報告。「前代未聞」は演出の言い方（「無謀」とは言わない）。

### FACT-03
- **主張**：1896 年は風が合わずに断念。1897 年 7 月 11 日に「ワシ号」で出発した。
- **出典**：S1（"His first attempt in 1896 had to be abandoned because the wind was from the wrong direction."／"11 July 1897"）
- **検証結果**：VERIFIED（WebFetch）

### FACT-04
- **主張**：出発直後に、向きを操るための長い引き綱の一部が外れ、操縦できなくなった。
- **出典**：S1（"Immediately after the launch, some of the drag-ropes were lost and the crew were unable to steer the balloon."）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「この瞬間に死が決まった」とは言わない。

### FACT-05
- **主張**：伝書鳩の通信に「All well on board」（全員無事）。その後、知らせは途絶えた。
- **出典**：S3（7 月 13 日 12 時 30 分の通信、"All well on board. This is the third pigeon despatch."）
- **検証結果**：PARTIALLY_VERIFIED（当時の刊行物・新聞の転載。原本は未確認）
- **注意点**：「最後の通信」とは言わない（3 通目と書かれている）。台本は「そのあと、知らせは途絶えた」（1930 年まで消息が分からなかったことは S1）。

### FACT-06
- **主張**：雨と霧で気球に氷がつき、約 65 時間で氷の上に降りた。
- **出典**：S1（"rain and fog led to formation of ice on the balloon and after just 65 hours aloft, they were forced to land."）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：氷だけが原因とは言わない（水素の漏れ・操縦できないことも）。台本は「雨と霧で、気球に氷がついた。…気球は、氷の上に降りた」。

### FACT-07
- **主張**：3 人はそりを引いて氷の上を約 3 か月歩いた。氷が風と海流で流された。
- **出典**：S1（"a three-month, 400 kilometre long trek on foot across the ice"）、ChatGPT の報告（氷が流されるため、歩いた距離と実際の移動が一致しない）
- **検証結果**：VERIFIED（期間は WebFetch）／流氷は PARTIALLY_VERIFIED（広く知られた事実、ChatGPT の報告）

### FACT-08
- **主張**：10 月初め、クヴィト島にたどり着き、そこで記録が途切れた。
- **出典**：S1（"In early October they reached Kvitøya."）、ChatGPT の報告（ストリンドベリの手帳の最後の記録は 10 月 17 日とされる）
- **検証結果**：VERIFIED（到着は WebFetch）
- **注意点**：最後の記録の日を死んだ日と言わない。

### FACT-09
- **主張**：1930 年、ノルウェーの調査隊が島で彼らを見つけた。
- **出典**：S1（"in August 1930, a Norwegian expedition … led by Gunnar Horn happened upon the men's remains"）、S6（8 月 6 日、ブラートヴォーグ号）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：3 人目（フレンケル）は後の別の船の調査で見つかった（ChatGPT の報告）→ 台本は「島で彼らを見つけた」。

### FACT-10
- **主張**：なぜ亡くなったのかは、今も分かっていない。寒さ・病気・中毒・ホッキョクグマなど、説はいくつもある。
- **出典**：S1（旋毛虫症〔ホッキョクグマの肉〕、一酸化炭素中毒、ホッキョクグマの襲撃）、S5（ボツリヌス症ほか）、S2（"The cause of death still eludes us."、ChatGPT の報告）
- **検証結果**：VERIFIED（「確定していない」こと）
- **注意点**：死因を断定しない。

### FACT-11
- **主張**：フィルムは現像された。氷の上の気球、そりを引く隊員の写真が残った。
- **出典**：S4（ヘルツベリが 1930 年に現像）、写真 A1（氷の上の気球）・A3（そり）
- **検証結果**：VERIFIED（写真そのものが残っている）
- **注意点**：枚数（93 枚）は Claude の検索で確認できなかった → 台本で言わない。写真は「最期」を写したものではない。

## 言わないこと

- 死因の断定（旋毛虫症・ボツリヌス症など）／「無謀な計画」／「綱が外れた瞬間に失敗が決まった」
- 「10 月 17 日に死亡」／「93 枚」（未確認）／「婚約者への手紙が見つかった」（手紙は見つかっていない）
- 「北極点に着いた」
