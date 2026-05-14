from __future__ import annotations

from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher, parse_datetime
from youbuyfirst_pipeline.models import RawPost


class NaverBoardAdapter:
    source = "NAVER"
    base_url = "https://finance.naver.com"

    def __init__(self, fetcher: BrowserCapableFetcher, stock_code: str) -> None:
        self.fetcher = fetcher
        self.stock_code = stock_code

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
            date_text = _cell_text(cells, 1)
            author = _cell_text(cells, 2)
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
