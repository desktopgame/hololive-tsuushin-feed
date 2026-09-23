#!/usr/bin/env python3
"""hololive-tsuushin.com の RSS を正規化して feed.xml を生成する。

元フィードは Content-Type が text/html で配信され、XML 宣言の直後に
不正な <head/> 要素が挿入されているため、そのままでは一部の RSS
リーダーで購読できない。本スクリプトは元フィードから必要最低限の項目
(タイトル / 元記事URL / GUID / 公開日時) のみを抽出し、正常な RSS 2.0
として public/feed.xml に出力する。

外部依存は使わず、Python 標準ライブラリのみで実装する。
"""

from __future__ import annotations

import os
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime

SOURCE_URL = "https://hololive-tsuushin.com/feed/"
OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "public",
    "feed.xml",
)

CHANNEL_TITLE = "ホロライブ通信 非公式フィード"
CHANNEL_LINK = "https://hololive-tsuushin.com/"
CHANNEL_DESCRIPTION = (
    "ホロライブ通信の記事タイトルと元記事URLのみを配信する非公式RSSフィード"
)

USER_AGENT = "hololive-tsuushin-feed/1.0 (+https://github.com/)"


def fetch(url: str, timeout: int = 30) -> bytes:
    """元フィードを取得する。"""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise urllib.error.HTTPError(
                url, response.status, "unexpected status", response.headers, None
            )
        return response.read()


def parse_feed(raw: bytes) -> ET.Element:
    """元フィードをパースする。

    XML 宣言の直後に <head/> が挿入されているため、最初の <rss> 要素以降を
    パース対象とする。
    """
    text = raw.decode("utf-8", errors="replace")
    start = text.find("<rss")
    if start == -1:
        raise ValueError("RSS root element (<rss>) was not found in the feed")
    return ET.fromstring(text[start:])


def local_name(tag: str) -> str:
    """名前空間を除いたローカル名を返す。"""
    return tag.rsplit("}", 1)[-1]


def find_child(element: ET.Element, name: str) -> ET.Element | None:
    """名前空間を無視して子要素を探す。"""
    for child in element:
        if local_name(child.tag) == name:
            return child
    return None


def text_of(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def parse_pubdate(value: str) -> str | None:
    """RFC 822 形式の日時を UTC 表記 (+0000) へ正規化する。"""
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def extract_items(root: ET.Element) -> list[dict[str, str]]:
    """channel/item から必要な項目のみを抽出し、URL で重複排除する。"""
    channel = find_child(root, "channel")
    if channel is None:
        raise ValueError("channel element was not found in the feed")

    items: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in channel:
        if local_name(item.tag) != "item":
            continue

        title = text_of(find_child(item, "title"))
        link = text_of(find_child(item, "link"))
        if not title or not link:
            print(f"skip: missing title or link (link={link!r})", file=sys.stderr)
            continue

        if link in seen:
            continue
        seen.add(link)

        pub_date = parse_pubdate(text_of(find_child(item, "pubDate")))

        entry = {"title": title, "link": link, "guid": link}
        if pub_date:
            entry["pubDate"] = pub_date
        items.append(entry)

    return items


def build_rss(items: list[dict[str, str]]) -> bytes:
    """正規化した RSS 2.0 を生成する。"""
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = CHANNEL_TITLE
    ET.SubElement(channel, "link").text = CHANNEL_LINK
    ET.SubElement(channel, "description").text = CHANNEL_DESCRIPTION

    for entry in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = entry["title"]
        ET.SubElement(item, "link").text = entry["link"]
        guid = ET.SubElement(item, "guid", {"isPermaLink": "true"})
        guid.text = entry["guid"]
        if entry.get("pubDate"):
            ET.SubElement(item, "pubDate").text = entry["pubDate"]

    ET.indent(rss, space="  ")
    body = ET.tostring(rss, encoding="utf-8", xml_declaration=False)
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + body + b"\n"


def write_atomically(data: bytes, path: str) -> bool:
    """一時ファイル経由で書き込み、内容に変更がある場合のみ置き換える。"""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    if os.path.exists(path):
        with open(path, "rb") as existing:
            if existing.read() == data:
                print("no changes: feed.xml is up to date")
                return False

    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".feed-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as tmp_file:
            tmp_file.write(data)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    print(f"updated: {path}")
    return True


def main() -> int:
    try:
        raw = fetch(SOURCE_URL)
        root = parse_feed(raw)
        items = extract_items(root)
        if not items:
            raise ValueError("no items could be extracted from the feed")
        data = build_rss(items)
        write_atomically(data, OUTPUT_PATH)
    except urllib.error.HTTPError as error:
        print(f"error: HTTP {error.code} while fetching {SOURCE_URL}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"error: failed to fetch {SOURCE_URL}: {error.reason}", file=sys.stderr)
        return 1
    except (ET.ParseError, ValueError) as error:
        print(f"error: failed to process feed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
