from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher, parse_datetime
from youbuyfirst_pipeline.models import RawPost


class FmkoreaAdapter:
    source = "FMKOREA"
    default_url = "https://www.fmkorea.com/stock"

    def __init__(self, fetcher: BrowserCapableFetcher, url: str | None = None, target: CrawlTarget | None = None) -> None:
        self.fetcher = fetcher
        self.url = url or self.default_url
        self.target = target or CrawlTarget.community_board(self.source, url=self.url, label="FMKOREA stock board")

    async def fetch_posts(self) -> list[RawPost]:
        result = await self.fetcher.fetch_html(self.url)
        return self.parse_list_html(result.html)

    @staticmethod
    def parse_list_html(html: str) -> list[RawPost]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[RawPost] = []
        seen: set[str] = set()

        rows = soup.select("tr")
        for row in rows:
            classes = set(row.get("class", []))
            if "notice" in classes:
                continue
            anchor = _post_anchor(row)
            if not anchor:
                continue
            href = anchor.get("href", "").strip()
            title = anchor.get_text(" ", strip=True)
            if not href or not title:
                continue
            post_id = _post_id_from_href(href)
            if not post_id:
                continue
            if not post_id or post_id in seen:
                continue
            seen.add(post_id)
            container = row
            date_text = _first_text(container, [".regdate", ".date", ".time", "time"]) if container else None
            author = _first_text(container, [".author", ".member", ".nickname"]) if container else None
            url = href if href.startswith("http") else f"https://www.fmkorea.com{href}"
            posts.append(
                RawPost(
                    source=FmkoreaAdapter.source,
                    external_id=f"FMKOREA-{post_id}",
                    url=url,
                    title=title,
                    content="",
                    author=author or "",
                    published_at=parse_datetime(date_text),
                )
            )
        return posts


def _post_anchor(row):
    for anchor in row.select("td.title a[href^='/']"):
        classes = set(anchor.get("class", []))
        if "replyNum" in classes or anchor.get("href", "").endswith("#comment"):
            continue
        if _post_id_from_href(anchor.get("href", "")):
            return anchor
    return None


def _post_id_from_href(href: str) -> str:
    parsed = urlparse(href)
    path_id = parsed.path.strip("/").split("/")[-1]
    if path_id.isdigit():
        return path_id
    document_srl = parse_qs(parsed.query).get("document_srl", [""])[0]
    return document_srl if document_srl.isdigit() else ""


def _first_text(container, selectors: list[str]) -> str | None:
    for selector in selectors:
        node = container.select_one(selector)
        if node:
            text = node.get_text(" ", strip=True)
            if text:
                return text
    return None
