from __future__ import annotations

from bs4 import BeautifulSoup

from youbuyfirst_pipeline.board_stream import BoardPage, BoardStreamCrawler, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher, parse_datetime
from youbuyfirst_pipeline.models import RawPost


class DcinsideAdapter:
    source = "DCINSIDE"

    def __init__(
        self,
        fetcher: BrowserCapableFetcher,
        target: CrawlTarget,
        stream_crawler: BoardStreamCrawler | None = None,
    ) -> None:
        if not target.url:
            raise ValueError(f"{target.target_id} is missing url")
        if not target.board_id:
            raise ValueError(f"{target.target_id} is missing board_id")
        self.fetcher = fetcher
        self.target = target
        self.board_id = target.board_id
        self.url = target.url
        self.stream_crawler = stream_crawler or BoardStreamCrawler()

    async def fetch_posts(self) -> list[RawPost]:
        result = await self.fetcher.fetch_html(self.url)
        return self.parse_list_html(result.html, board_id=self.board_id, base_url=self.url)

    async def fetch_stream(self, watermark: BoardWatermark | None = None) -> BoardStreamResult:
        return await self.stream_crawler.collect(self._fetch_page, watermark)

    async def _fetch_page(self, cursor: str | None) -> BoardPage:
        result = await self.fetcher.fetch_html(_page_url(self.url, cursor))
        posts = self.parse_list_html(result.html, board_id=self.board_id, base_url=self.url)
        current_page = cursor or "1"
        next_cursor = str(int(current_page) + 1) if posts else None
        return BoardPage(cursor=current_page, posts=posts, next_cursor=next_cursor)

    @staticmethod
    def parse_list_html(html: str, board_id: str, base_url: str) -> list[RawPost]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[RawPost] = []
        seen: set[str] = set()

        for row in soup.select("tr.ub-content, tr.us-post"):
            number_text = _first_text(row, [".gall_num", "td:nth-of-type(1)"])
            if not number_text or not number_text.strip().isdigit():
                continue
            anchor = row.select_one(".gall_tit a[href*='view']")
            if not anchor:
                continue
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "").strip()
            if not title or not href:
                continue
            external_id = f"DCINSIDE-{board_id}-{number_text.strip()}"
            if external_id in seen:
                continue
            seen.add(external_id)
            posts.append(
                RawPost(
                    source=DcinsideAdapter.source,
                    board_id=board_id,
                    external_id=external_id,
                    url=href if href.startswith("http") else f"https://gall.dcinside.com{href}",
                    title=title,
                    content="",
                    author=_author_text(row),
                    published_at=parse_datetime(_date_text(row)),
                    view_count=_parse_count(_first_text(row, [".gall_count", "td:nth-of-type(5)"])),
                    recommend_count=_parse_count(_first_text(row, [".gall_recommend", "td:nth-of-type(6)"])),
                    comment_count=_comment_count(row),
                )
            )
        return posts


def _first_text(container, selectors: list[str]) -> str | None:
    for selector in selectors:
        node = container.select_one(selector)
        if node:
            text = node.get_text(" ", strip=True)
            if text:
                return text
    return None


def _author_text(row) -> str:
    writer = row.select_one(".gall_writer")
    if not writer:
        return ""
    return writer.get("data-nick") or writer.get_text(" ", strip=True)


def _date_text(row) -> str | None:
    date = row.select_one(".gall_date, td:nth-of-type(4)")
    if not date:
        return None
    return date.get("title") or date.get_text(" ", strip=True)


def _parse_count(value: str | None) -> int | None:
    if not value:
        return None
    digits = value.replace(",", "").strip()
    return int(digits) if digits.isdigit() else None


def _comment_count(row) -> int:
    reply = row.select_one(".reply_num")
    if not reply:
        return 0
    text = reply.get_text("", strip=True).strip("[]")
    return int(text) if text.isdigit() else 0


def _page_url(base_url: str, cursor: str | None) -> str:
    if cursor is None or cursor == "1":
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={cursor}"
