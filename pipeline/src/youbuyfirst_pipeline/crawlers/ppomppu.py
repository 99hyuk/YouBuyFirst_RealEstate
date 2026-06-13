from __future__ import annotations

from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from youbuyfirst_pipeline.board_stream import BoardPage, BoardStreamCrawler, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher, parse_datetime
from youbuyfirst_pipeline.models import RawPost


class PpomppuAdapter:
    source = "PPOMPPU"

    def __init__(
        self,
        fetcher: BrowserCapableFetcher,
        target: CrawlTarget,
        stream_crawler: BoardStreamCrawler | None = None,
    ) -> None:
        if not target.url:
            raise ValueError(f"{target.target_id} is missing url")
        self.fetcher = fetcher
        self.target = target
        self.board_id = target.board_id or "house"
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

        for anchor in soup.select("a[href*='view.php'][href*='no=']"):
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "").strip()
            post_id = _post_id_from_href(href)
            if not title or not post_id or _board_id_from_href(href) != board_id:
                continue
            external_id = f"PPOMPPU-{board_id}-{post_id}"
            if external_id in seen:
                continue
            seen.add(external_id)
            row = anchor.find_parent("tr")
            if row:
                cells = row.find_all("td")
                if not _is_regular_row(cells):
                    continue
                posts.append(
                    RawPost(
                        source=PpomppuAdapter.source,
                        board_id=board_id,
                        external_id=external_id,
                        url=urljoin(base_url, href),
                        title=title,
                        content="",
                        author=_cell_text(cells, 2),
                        published_at=parse_datetime(_cell_text(cells, 3, attr="title")),
                        recommend_count=_parse_recommend_count(_cell_text(cells, 4)),
                        view_count=_parse_count(_cell_text(cells, 5)),
                        comment_count=_comment_count(row, title),
                    )
                )
                continue

            list_item = anchor.find_parent("li")
            mobile_post = _mobile_post_from_list_item(
                list_item=list_item,
                board_id=board_id,
                external_id=external_id,
                href=href,
                base_url=base_url,
            )
            if mobile_post:
                posts.append(mobile_post)
        return posts


def _board_id_from_href(href: str) -> str:
    query = parse_qs(urlparse(href).query)
    return query.get("id", [""])[0]


def _post_id_from_href(href: str) -> str:
    query = parse_qs(urlparse(href).query)
    post_id = query.get("no", [""])[0]
    return post_id if post_id.isdigit() else ""


def _cell_text(cells, index: int, attr: str | None = None) -> str:
    if index >= len(cells):
        return ""
    if attr:
        value = cells[index].get(attr)
        if value:
            return value.strip()
    return cells[index].get_text(" ", strip=True)


def _is_regular_row(cells) -> bool:
    number_text = _cell_text(cells, 0)
    return number_text.isdigit()


def _parse_count(value: str | None) -> int | None:
    if not value:
        return None
    digits = value.replace(",", "").strip()
    return int(digits) if digits.isdigit() else None


def _parse_recommend_count(value: str | None) -> int | None:
    if not value:
        return 0
    first = value.split("-", 1)[0].strip()
    return _parse_count(first) or 0


def _comment_count(row, title: str) -> int | None:
    if row:
        comment = row.select_one(".baseList-c")
        parsed = _parse_count(comment.get_text(" ", strip=True) if comment else None)
        if parsed is not None:
            return parsed
    marker = title.rsplit(" ", 1)[-1].strip("[]")
    return int(marker) if marker.isdigit() else 0


def _mobile_post_from_list_item(
    list_item,
    board_id: str,
    external_id: str,
    href: str,
    base_url: str,
) -> RawPost | None:
    if not list_item:
        return None
    title_node = list_item.select_one("strong")
    if not title_node:
        return None
    comment = title_node.select_one(".rp")
    comment_count = _parse_count(comment.get_text(" ", strip=True) if comment else None) or 0
    for decorative in title_node.select("img, .rp"):
        decorative.decompose()
    title = title_node.get_text(" ", strip=True)
    if not title:
        return None
    time_node = list_item.select_one(".times time")
    view_node = list_item.select_one(".rec_view .view")
    author_node = list_item.select_one(".names")
    return RawPost(
        source=PpomppuAdapter.source,
        board_id=board_id,
        external_id=external_id,
        url=urljoin(base_url, href),
        title=title,
        content="",
        author=author_node.get_text(" ", strip=True) if author_node else "",
        published_at=parse_datetime(time_node.get_text(" ", strip=True) if time_node else None),
        recommend_count=0,
        view_count=_parse_embedded_count(view_node.get_text(" ", strip=True) if view_node else None),
        comment_count=comment_count,
    )


def _parse_embedded_count(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(char for char in value if char.isdigit())
    return int(digits) if digits else None


def _page_url(base_url: str, cursor: str | None) -> str:
    if cursor is None or cursor == "1":
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={cursor}"
