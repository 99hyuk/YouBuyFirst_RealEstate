from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher, parse_datetime
from youbuyfirst_pipeline.models import RawPost


class NaverBoardAdapter:
    source = "NAVER"
    base_url = "https://finance.naver.com"

    def __init__(self, fetcher: BrowserCapableFetcher, stock_code: str, target: CrawlTarget | None = None) -> None:
        self.fetcher = fetcher
        self.stock_code = stock_code
        self.target = target or CrawlTarget.stock_board(self.source, market="KR", symbol=stock_code)

    async def fetch_posts(self) -> list[RawPost]:
        url = f"{self.base_url}/item/board.naver?code={self.stock_code}"
        result = await self.fetcher.fetch_html(url)
        posts = self.parse_list_html(result.html, stock_code=self.stock_code)
        if posts:
            return posts
        browser_result = await self.fetcher._fetch_browser(url)
        return self.parse_list_html(browser_result.html, stock_code=self.stock_code)

    @staticmethod
    def parse_list_html(html: str, stock_code: str) -> list[RawPost]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[RawPost] = []
        seen: set[str] = set()

        for anchor in soup.select("td.title a[href*='board_read'], a[href*='board_read.naver']"):
            href = anchor.get("href", "").strip()
            title = (anchor.get("title") or anchor.get_text(" ", strip=True)).strip()
            if not href or not title:
                continue
            query = parse_qs(urlparse(href).query)
            naver_id = query.get("nid", [None])[0] or href
            external_id = f"NAVER-{stock_code}-{naver_id}"
            if external_id in seen:
                continue
            seen.add(external_id)
            row = anchor.find_parent("tr")
            cells = row.find_all("td") if row else []
            title_index = _cell_index(cells, anchor.find_parent("td"))
            date_text = _published_at_text(cells, title_index)
            author = _author_text(cells, title_index)
            posts.append(
                RawPost(
                    source=NaverBoardAdapter.source,
                    external_id=external_id,
                    url=urljoin(NaverBoardAdapter.base_url, href),
                    title=title,
                    content="",
                    author=author,
                    published_at=parse_datetime(date_text),
                )
            )
        return posts


def _cell_text(cells, index: int) -> str:
    if index >= len(cells):
        return ""
    return cells[index].get_text(" ", strip=True)


def _cell_index(cells, cell) -> int:
    for index, candidate in enumerate(cells):
        if candidate is cell:
            return index
    return -1


def _published_at_text(cells, title_index: int) -> str:
    candidate_indices = []
    if title_index > 0:
        candidate_indices.append(title_index - 1)
    if title_index >= 0:
        candidate_indices.append(title_index + 1)
    candidate_indices.extend(range(len(cells)))

    seen: set[int] = set()
    for index in candidate_indices:
        if index in seen or index < 0 or index >= len(cells):
            continue
        seen.add(index)
        text = _cell_text(cells, index)
        if _looks_like_datetime(text):
            return text
    return ""


def _author_text(cells, title_index: int) -> str:
    start = title_index + 1 if title_index >= 0 else 0
    for index in range(start, len(cells)):
        text = _cell_text(cells, index)
        if text and not _looks_like_datetime(text) and not _looks_like_count(text):
            return text
    return ""


def _looks_like_datetime(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"(\d{4}[.-]\d{1,2}[.-]\d{1,2}\.?\s+\d{1,2}:\d{2}|\d{2,4}[.-]\d{1,2}[.-]\d{1,2}\.?|\d{1,2}:\d{2})",
            value.strip(),
        )
    )


def _looks_like_count(value: str) -> bool:
    return bool(re.fullmatch(r"[\d,]+|[\d.]+[만천백]?", value.strip()))
