from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from youbuyfirst_pipeline.board_stream import BoardPage, BoardStreamCrawler, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher, parse_datetime
from youbuyfirst_pipeline.models import RawPost


class FmkoreaAdapter:
    source = "FMKOREA"
    default_url = "https://www.fmkorea.com/stock"

    def __init__(
        self,
        fetcher: BrowserCapableFetcher,
        url: str | None = None,
        target: CrawlTarget | None = None,
        stream_crawler: BoardStreamCrawler | None = None,
    ) -> None:
        self.fetcher = fetcher
        self.url = url or self.default_url
        self.target = target or CrawlTarget.community_board(self.source, url=self.url, label="FMKOREA stock board")
        self.stream_crawler = stream_crawler or BoardStreamCrawler()

    async def fetch_posts(self) -> list[RawPost]:
        result = await self.fetcher.fetch_html(self.url)
        return self.parse_list_html(result.html, board_id=self.target.board_id or "stock")

    async def fetch_stream(self, watermark: BoardWatermark | None = None) -> BoardStreamResult:
        return await self.stream_crawler.collect(self._fetch_page, watermark)

    async def _fetch_page(self, cursor: str | None) -> BoardPage:
        result = await self.fetcher.fetch_html(_page_url(self.url, cursor))
        posts = self.parse_list_html(result.html, board_id=self.target.board_id or "stock")
        current_page = cursor or "1"
        next_cursor = str(int(current_page) + 1) if posts else None
        return BoardPage(cursor=current_page, posts=posts, next_cursor=next_cursor)

    @staticmethod
    def parse_list_html(html: str, board_id: str = "stock") -> list[RawPost]:
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
                    board_id=board_id,
                    external_id=f"FMKOREA-{post_id}",
                    url=url,
                    title=title,
                    content="",
                    author=author or "",
                    published_at=parse_datetime(date_text),
                    view_count=_parse_count(_first_text(container, ["td.m_no:not(.m_no_voted)", ".view_count"])),
                    recommend_count=_parse_reaction_count(_first_text(container, ["td.m_no_voted", ".recommend_count"])),
                    comment_count=_comment_count(container),
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


def _parse_count(value: str | None) -> int | None:
    if not value:
        return None
    normalized = value.replace(",", "").replace("\xa0", " ").strip()
    return int(normalized) if normalized.isdigit() else None


def _parse_reaction_count(value: str | None) -> int:
    return _parse_count(value) or 0


def _comment_count(container) -> int:
    node = container.select_one(".replyNum")
    if not node:
        return 0
    text = node.get_text("", strip=True).strip("[]")
    return int(text) if text.isdigit() else 0


def _page_url(base_url: str, cursor: str | None) -> str:
    if cursor is None or cursor == "1":
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={cursor}"
