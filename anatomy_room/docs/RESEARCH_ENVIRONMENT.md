# 調査環境の記録（RESEARCH_ENVIRONMENT）

## パイロット 5 本の調査時（2026-10-26）の制約

- 制作環境（Claude Code のクラウド環境）のネットワーク設定により、Web ページの **本文を直接開くことができなかった**。
  - 例：`www.soumu.go.jp`、`www.rfc-editor.org`、`www.waterworks.metro.tokyo.lg.jp`、`www.cloudflare.com`、
    `www2.telegeography.com`、`laws.e-gov.go.jp`、`www.otis.com` などへの接続が、環境のネットワークポリシーで拒否された（HTTP 403）。
- 使えたのは **Web 検索ツール**（検索結果の要約と、資料からの引用抜粋）のみ。
- そのため、出典はすべて「確認方法：`検索抜粋`」として記録している。数学の主張は `数学的導出` で確認した。

## この制約が意味すること

- 抜粋は資料の一部であり、前後の文脈や但し書きを見落としている可能性がある。
- 抜粋の文言は検索ツールが整形したもので、原文と細部が異なる可能性がある。
- したがって、**公開前に、各 `fact_check.md` の出典 URL を人が開いて本文を確認すること** を推奨する。
  特に「公開前に本文確認が必要」と書いた項目を優先する。

## 制約を外す方法

環境のネットワークアクセス設定で、必要なドメインを許可するか、より広いアクセスレベルにすると、本文を直接確認できるようになる。
手順：https://code.claude.com/docs/en/cloud-environments#network-access
