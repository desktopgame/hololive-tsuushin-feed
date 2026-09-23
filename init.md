# hololive-tsuushin-feed

## 目的

`https://hololive-tsuushin.com/feed/` のRSSフィードを定期取得し、必要最低限の情報だけを残したRSSフィードとしてGitHub Pagesから静的配信する。

元サイトのフィードは内容自体はRSSだが、HTTPレスポンスの `Content-Type` が `text/html` になっており、一部RSSリーダーから正常に購読できない。

このリポジトリでは、元RSSをGitHub Actionsで取得・整形し、`feed.xml` としてGitHub Pagesから配信することで、KaraKeepなどのRSSリーダーから購読可能にする。

## 方針

記事本文や画像などは再配信しない。

元RSSから以下の情報のみを取得して、新しいRSS 2.0フィードを生成する。

* 記事タイトル
* 元記事URL
* 公開日時
* GUID

各記事の `link` および `guid` は元記事URLを使用する。

`description` や本文コンテンツは含めない。

KaraKeep側ではRSSから記事URLを取得し、必要に応じて元サイトの記事本文を直接フェッチする想定。

## 元フィード

```text
https://hololive-tsuushin.com/feed/
```

## 出力

GitHub Pages上で以下のようなURLから取得できることを想定する。

```text
https://<github-user>.github.io/hololive-tsuushin-feed/feed.xml
```

生成されるRSSは概ね以下の形式とする。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>ホロライブ通信 非公式フィード</title>
    <link>https://hololive-tsuushin.com/</link>
    <description>ホロライブ通信の記事タイトルと元記事URLのみを配信する非公式RSSフィード</description>

    <item>
      <title>記事タイトル</title>
      <link>https://hololive-tsuushin.com/...</link>
      <guid isPermaLink="true">https://hololive-tsuushin.com/...</guid>
      <pubDate>Wed, 23 Sep 2026 12:34:56 +0000</pubDate>
    </item>
  </channel>
</rss>
```

## 更新方法

GitHub Actionsを使用して定期更新する。

更新頻度は1日1回を初期値とする。

あわせて `workflow_dispatch` を設定し、GitHub Actions画面から手動実行できるようにする。

処理の流れは以下。

1. 元RSSをHTTP GETで取得する
2. RSS/XMLとしてパースする
3. 各記事から必要な項目のみ抽出する
4. `feed.xml` を生成する
5. 内容に変更がある場合のみコミットする
6. GitHub Pagesから配信する

## 実装

できるだけ依存関係を少なくする。

Python標準ライブラリを優先する。

候補:

* `urllib.request`
* `xml.etree.ElementTree`
* `email.utils`

外部ライブラリは、標準ライブラリのみでは正常なRSS処理が難しい場合のみ追加する。

## ディレクトリ構成

例:

```text
.
├── .github/
│   └── workflows/
│       └── update-feed.yml
├── scripts/
│   └── update_feed.py
├── public/
│   └── feed.xml
├── README.md
└── init.md
```

GitHub Pagesの公開元は `public/` を想定する。

Pagesの構成上、別ディレクトリまたはGitHub Actions経由のデプロイの方が自然であれば変更してよい。

## RSS生成時の要件

### channel

最低限以下を含める。

* `title`
* `link`
* `description`

### item

最低限以下を含める。

* `title`
* `link`
* `guid`
* `pubDate`

### URL

記事URLは必ず元サイトのURLを使用する。

GitHub Pages側の記事ページは作らない。

### GUID

以下の形式とする。

```xml
<guid isPermaLink="true">元記事URL</guid>
```

### 本文

以下は出力しない。

* `description`
* `content:encoded`
* 記事本文
* サムネイル
* 画像
* 動画埋め込み
* コメント情報

## エラー処理

元RSSの取得またはパースに失敗した場合、既存の `feed.xml` を壊さないこと。

失敗時に空のフィードや途中まで生成されたファイルで既存ファイルを上書きしない。

一時ファイルへ生成し、正常完了後に置き換える方式を推奨する。

HTTPエラー時はGitHub Actionsを失敗扱いにする。

## 重複

同一URLの記事を重複して出力しない。

GUIDまたは記事URLをキーとして重複排除する。

## 記事数

元RSSに含まれる記事のみを基本的に出力する。

独自に記事履歴を蓄積する必要はない。

つまり、このリポジトリはRSSアーカイブではなく、元RSSを正規化するプロキシとして扱う。

## GitHub Pages

生成した `feed.xml` がGitHub Pages経由で取得できること。

公開後、以下でContent-Typeを確認する。

```bash
curl -I https://<github-user>.github.io/hololive-tsuushin-feed/feed.xml
```

期待値はXMLとして扱えるContent-Type。

例:

```text
Content-Type: application/xml
```

または

```text
Content-Type: text/xml
```

少なくとも `text/html` ではないことを確認する。

## README

READMEには以下を簡潔に記載する。

* 非公式フィードであること
* 元サイトとは無関係であること
* 記事本文は再配信しないこと
* 元記事タイトル・URL・公開日時のみを配信すること
* フィードURL
* 更新頻度
* 元サイトへのリンク

## 注意事項

このリポジトリは元サイトのRSS配信時のHTTP Content-Type問題を回避するための非公式な中継フィード。

元サイトの記事コンテンツを複製・再公開することを目的としない。

可能な限り、ユーザーが元記事へ直接アクセスする構成にする。

## 完了条件

以下をすべて満たしたら完了。

1. GitHub Actionsから手動実行できる
2. 元RSSを正常に取得できる
3. `feed.xml` が生成される
4. 記事本文が含まれていない
5. 各itemにタイトル・元URL・GUID・公開日時が含まれる
6. GitHub Pagesから `feed.xml` を取得できる
7. `curl -I` で `text/html` 以外のXML系Content-Typeが返る
8. KaraKeepからフィードとして登録・取得できる
