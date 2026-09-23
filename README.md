# hololive-tsuushin-feed

ホロライブ通信（https://hololive-tsuushin.com/ ）のRSSフィードを正規化して配信する、**非公式**のRSSフィードです。

元サイトとは一切関係がありません。

## 概要

元サイトのフィードは内容自体はRSSですが、HTTPレスポンスの `Content-Type` が `text/html` で返るため、一部のRSSリーダーから正常に購読できません。

本リポジトリはGitHub Actionsで元フィードを取得・整形し、正常なXMLとして `feed.xml` をGitHub Pagesから配信します。

## 配信内容

以下の情報のみを配信します。

- 記事タイトル
- 元記事URL
- 公開日時
- GUID（元記事URL）

**記事本文・画像・サムネイル・動画等は再配信しません。** 本文は元記事へ直接アクセスしてください。

## フィードURL

```text
https://<github-user>.github.io/hololive-tsuushin-feed/feed.xml
```

## 更新頻度

1日1回（GitHub Actionsの定期実行）。GitHub Actions画面から手動実行も可能です。

## 元サイト

- https://hololive-tsuushin.com/
- https://hololive-tsuushin.com/feed/

## 構成

```text
.
├── .github/workflows/update-feed.yml  # 定期取得・生成・Pagesデプロイ
├── scripts/update_feed.py             # フィード生成スクリプト
├── public/feed.xml                    # 生成物（GitHub Pages公開元）
└── README.md
```

## ローカルでの実行

```bash
python scripts/update_feed.py
```

Python 3 の標準ライブラリのみを使用します。
