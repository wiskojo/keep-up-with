from __future__ import annotations

from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import httpx

from keep_up_with.integrations.base import SubscriptionContext, poll_every


@poll_every("web.items", default_interval_seconds=900)
def items(ctx: SubscriptionContext) -> None:
    for feed in ctx.settings().get("feeds") or []:
        for item in feed_items(str(feed)):
            item["feed"] = str(feed)
            key = item.get("id") or item.get("url") or item.get("title")
            if not key:
                continue
            ctx.emit(
                kind="item",
                external_id=str(key),
                summary=f"{item.get('source') or 'Feed'}: {item.get('title') or 'New item'}",
                refs={"url": item.get("url", "")},
                data=item,
            )
    for page in ctx.settings().get("pages") or []:
        for item in page_items(str(page)):
            item["page"] = str(page)
            key = item.get("url") or item.get("title")
            if not key:
                continue
            ctx.emit(
                kind="item",
                external_id=str(key),
                summary=f"{item.get('source') or 'Page'}: {item.get('title') or 'New item'}",
                refs={"url": item.get("url", "")},
                data=item,
            )


def feed_items(url: str) -> list[dict[str, Any]]:
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    if root.tag.rsplit("}", 1)[-1] == "feed":
        return atom_items(root)
    channel = root.find("channel")
    return rss_items(channel) if channel is not None else []


def page_items(url: str) -> list[dict[str, Any]]:
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    parser = PageLinkParser(response.url)
    parser.feed(response.text)
    return parser.items()


class PageLinkParser(HTMLParser):
    def __init__(self, base_url: str | httpx.URL) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = str(base_url)
        parsed = urlparse(self.base_url)
        self.base_path = parsed.path.rstrip("/") + "/"
        self.source = parsed.netloc
        self.current: dict[str, str] | None = None
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        url = urljoin(self.base_url, href)
        parsed = urlparse(url)
        if parsed.netloc != urlparse(self.base_url).netloc:
            return
        if not parsed.path.startswith(self.base_path):
            return
        self.current = {"url": urlunparse(parsed._replace(fragment="")), "title": ""}

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current["title"] = " ".join(
                [self.current["title"], " ".join(data.split())]
            ).strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current is not None:
            if self.current["title"]:
                self.rows.append(
                    {
                        "source": self.source,
                        "title": self.current["title"],
                        "url": self.current["url"],
                    }
                )
            self.current = None

    def items(self) -> list[dict[str, str]]:
        deduped: dict[str, dict[str, str]] = {}
        for row in self.rows:
            deduped.setdefault(row["url"], row)
        return list(deduped.values())


def rss_items(channel: ET.Element) -> list[dict[str, Any]]:
    source = text(channel, "title")
    rows = []
    for item in channel.findall("item"):
        rows.append(
            {
                "source": source,
                "id": text(item, "guid") or text(item, "link"),
                "title": text(item, "title"),
                "url": text(item, "link"),
                "published_at": text(item, "pubDate"),
            }
        )
    return rows


def atom_items(root: ET.Element) -> list[dict[str, Any]]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    source = text(root, "atom:title", ns)
    rows = []
    for entry in root.findall("atom:entry", ns):
        rows.append(
            {
                "source": source,
                "id": text(entry, "atom:id", ns),
                "title": text(entry, "atom:title", ns),
                "url": atom_link(entry, ns),
                "published_at": text(entry, "atom:updated", ns)
                or text(entry, "atom:published", ns),
            }
        )
    return rows


def atom_link(entry: ET.Element, ns: dict[str, str]) -> str:
    for link in entry.findall("atom:link", ns):
        href = link.attrib.get("href")
        if href and link.attrib.get("rel", "alternate") == "alternate":
            return href
    return ""


def text(element: ET.Element, path: str, ns: dict[str, str] | None = None) -> str:
    child = element.find(path, ns or {})
    return " ".join((child.text or "").split()) if child is not None else ""
