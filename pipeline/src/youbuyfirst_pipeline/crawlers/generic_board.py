from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from youbuyfirst_pipeline.board_stream import BoardPage, BoardStreamCrawler, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher, parse_datetime
from youbuyfirst_pipeline.models import RawPost


@dataclass(frozen=True)
class GenericParsedList:
    posts: list[RawPost]
    filtered_count: int = 0
    excluded_title_count: int = 0
    keyword_miss_count: int = 0
    duplicate_link_count: int = 0


@dataclass(frozen=True)
class GenericBoardSourceConfig:
    href_pattern: re.Pattern[str]
    external_id_pattern: re.Pattern[str]
    title_cleanup_pattern: re.Pattern[str] | None = None
    page_url_template: str | None = None
    require_real_estate_keyword: bool = False
    excluded_title_pattern: re.Pattern[str] | None = None
    title_max_chars: int = 180


_REAL_ESTATE_KEYWORD_PATTERN = re.compile(
    r"부동산|아파트|전세|월세|전월세|매매|실거래|집값|주택|분양|청약|재건축|재개발|"
    r"입주|미분양|임대|대출|금리|학군|교통|신도시|상권|오피스텔|빌라|토지|상가|"
    r"강남|서초|송파|마포|성수|분당|판교|동탄|광교|송도|세종|대전|파주|검단|"
    r"둔촌|헬리오|래미안|자이|푸르지오|아이파크|힐스테이트|롯데캐슬|"
    r"real estate|apartment|jeonse",
    re.IGNORECASE,
)
_COMMON_EXCLUDED_TITLE_PATTERN = re.compile(
    r"구인|구직|채용|hiring|recruit|job|분양대행|상담문의|매물접수|광고|홍보|오픈채팅|도박|토토|성인",
    re.IGNORECASE,
)


_SOURCE_CONFIGS = {
    "CLIEN": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/service/board/park/\d+"),
        external_id_pattern=re.compile(r"/service/board/park/(\d+)"),
        title_cleanup_pattern=re.compile(r"^(?:\d+\s+)?(?P<title>.+?)(?:\s+\d+){0,4}\s+\d{1,2}:\d{2}\s+\d+(?:\s+\S+)?$"),
    ),
    "COOK82": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/entiz/read\.php\?num=\d+"),
        external_id_pattern=re.compile(r"[?&]num=(\d+)"),
    ),
    "DEALAGORA": GenericBoardSourceConfig(
        href_pattern=re.compile(r"(?:^|/|\./)view\.php\?[^\"']*code=community[^\"']*[&?]idx=\d+"),
        external_id_pattern=re.compile(r"[?&]idx=(\d+)"),
        title_cleanup_pattern=re.compile(r"^(?P<title>.+?)(?:\s+딜\s*아고라\s+|\s+\d{4}-\d{2}-\d{2}\s+\d+\s+\d+\s+\d+).*$"),
        page_url_template="https://dealagora.co.kr/subpage/bbs/borad.php?cate=&code=community&order=new&page={page}",
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "THEQOO": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/square/\d+"),
        external_id_pattern=re.compile(r"/square/(\d+)"),
        page_url_template="https://theqoo.net/square?page={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "MLBPARK": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/mp/b\.php\?[^\"']*m=view[^\"']*b=bullpen[^\"']*id=\d+"),
        external_id_pattern=re.compile(r"[?&]id=(\d+)"),
        page_url_template="https://mlbpark.donga.com/mp/b.php?m=list&b=bullpen&p={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "NATEPANN": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/talk/\d+"),
        external_id_pattern=re.compile(r"/talk/(\d+)"),
        page_url_template="https://pann.nate.com/talk/c20002?page={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "TODAYHUMOR": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/board/view\.php\?[^\"']*table=(?:economy|freeboard)[^\"']*no=\d+"),
        external_id_pattern=re.compile(r"[?&]no=(\d+)"),
        page_url_template="https://www.todayhumor.co.kr/board/list.php?table={board_id}&page={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "RULIWEB": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/community/board/300143/read/\d+"),
        external_id_pattern=re.compile(r"/read/(\d+)"),
        page_url_template="https://bbs.ruliweb.com/community/board/300143?page={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "BOBAEDREAM": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/view\?[^\"']*code=freeb[^\"']*No=\d+", re.IGNORECASE),
        external_id_pattern=re.compile(r"[?&]No=(\d+)", re.IGNORECASE),
        page_url_template="https://www.bobaedream.co.kr/list?code=freeb&page={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "INSTIZ": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/name/\d+"),
        external_id_pattern=re.compile(r"/name/(\d+)"),
        page_url_template="https://www.instiz.net/name?page={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "SLRCLUB": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/bbs/vx2\.php\?[^\"']*id=free[^\"']*no=\d+"),
        external_id_pattern=re.compile(r"[?&]no=(\d+)"),
        page_url_template="https://www.slrclub.com/bbs/zboard.php?id=free&page={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
    "INVEN": GenericBoardSourceConfig(
        href_pattern=re.compile(r"/board/webzine/2097/\d+"),
        external_id_pattern=re.compile(r"/board/webzine/2097/(\d+)"),
        page_url_template="https://www.inven.co.kr/board/webzine/2097?p={page}",
        require_real_estate_keyword=True,
        excluded_title_pattern=_COMMON_EXCLUDED_TITLE_PATTERN,
    ),
}
SUPPORTED_GENERIC_BOARD_SOURCES = frozenset(_SOURCE_CONFIGS)


class GenericLinkBoardAdapter:
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
        if target.source not in _SOURCE_CONFIGS:
            raise ValueError(f"{target.target_id} has unsupported generic board source")
        self.fetcher = fetcher
        self.target = target
        self.source = target.source
        self.board_id = target.board_id
        self.url = target.url
        self.stream_crawler = stream_crawler or BoardStreamCrawler(max_pages_per_run=1)

    async def fetch_posts(self) -> list[RawPost]:
        result = await self.fetcher.fetch_html(self.url)
        return self.parse_list_html(result.html, source=self.source, board_id=self.board_id, base_url=self.url)

    async def fetch_stream(self, watermark: BoardWatermark | None = None) -> BoardStreamResult:
        return await self.stream_crawler.collect(self._fetch_page, watermark)

    async def _fetch_page(self, cursor: str | None) -> BoardPage:
        page = _cursor_page(cursor)
        url = _page_url_for_cursor(self.url, self.board_id, _SOURCE_CONFIGS[self.source], page)
        if url is None:
            return BoardPage(cursor=cursor, posts=[], next_cursor=None)
        result = await self.fetcher.fetch_html(url)
        parsed = self.parse_list_html_with_stats(result.html, source=self.source, board_id=self.board_id, base_url=url)
        return BoardPage(
            cursor=str(page),
            posts=parsed.posts,
            next_cursor=str(page + 1),
            filtered_count=parsed.filtered_count,
            excluded_title_count=parsed.excluded_title_count,
            keyword_miss_count=parsed.keyword_miss_count,
            duplicate_link_count=parsed.duplicate_link_count,
        )

    @staticmethod
    def parse_list_html(html: str, *, source: str, board_id: str, base_url: str) -> list[RawPost]:
        return GenericLinkBoardAdapter.parse_list_html_with_stats(
            html,
            source=source,
            board_id=board_id,
            base_url=base_url,
        ).posts

    @staticmethod
    def parse_list_html_with_stats(html: str, *, source: str, board_id: str, base_url: str) -> GenericParsedList:
        normalized_source = source.strip().upper()
        config = _SOURCE_CONFIGS.get(normalized_source)
        if config is None:
            raise ValueError(f"unsupported generic board source: {source}")

        soup = BeautifulSoup(html, "html.parser")
        posts: list[RawPost] = []
        seen: set[str] = set()
        filtered_count = 0
        excluded_title_count = 0
        keyword_miss_count = 0
        duplicate_link_count = 0
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not config.href_pattern.search(href):
                continue
            external_post_id = _external_post_id(config, href)
            if not external_post_id:
                continue
            external_id = f"{normalized_source}-{board_id}-{external_post_id}"
            if external_id in seen:
                duplicate_link_count += 1
                continue
            title = _clean_title(anchor.get_text(" ", strip=True), config)
            if not title:
                continue
            filter_reason = _title_filter_reason(title, config)
            if filter_reason:
                filtered_count += 1
                if filter_reason == "excluded_title":
                    excluded_title_count += 1
                if filter_reason == "keyword_miss":
                    keyword_miss_count += 1
                continue
            seen.add(external_id)
            posts.append(
                RawPost(
                    source=normalized_source,
                    board_id=board_id,
                    external_id=external_id,
                    url=urljoin(base_url, href),
                    title=title,
                    content="",
                    author="",
                    published_at=parse_datetime(_time_hint(_context_text(anchor))),
                    view_count=None,
                    recommend_count=0,
                    comment_count=0,
                )
            )
        return GenericParsedList(
            posts=posts,
            filtered_count=filtered_count,
            excluded_title_count=excluded_title_count,
            keyword_miss_count=keyword_miss_count,
            duplicate_link_count=duplicate_link_count,
        )


def _external_post_id(config: GenericBoardSourceConfig, href: str) -> str:
    match = config.external_id_pattern.search(href)
    return match.group(1) if match else ""


def _clean_title(raw_title: str, config: GenericBoardSourceConfig) -> str:
    title = re.sub(r"\s+", " ", raw_title).strip()
    if not title:
        return ""
    if config.title_cleanup_pattern:
        match = config.title_cleanup_pattern.match(title)
        if match:
            title = match.group("title").strip()
    return _truncate_title(title, config.title_max_chars)


def _is_allowed_title(title: str, config: GenericBoardSourceConfig) -> bool:
    return _title_filter_reason(title, config) == ""


def _title_filter_reason(title: str, config: GenericBoardSourceConfig) -> str:
    if config.excluded_title_pattern and config.excluded_title_pattern.search(title):
        return "excluded_title"
    if config.require_real_estate_keyword and not _REAL_ESTATE_KEYWORD_PATTERN.search(title):
        return "keyword_miss"
    return ""


def _truncate_title(title: str, max_chars: int) -> str:
    if len(title) <= max_chars:
        return title
    return f"{title[: max(1, max_chars - 3)].rstrip()}..."


def _time_hint(text: str) -> str | None:
    match = re.search(
        r"\b\d{4}[.-]\d{1,2}[.-]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?\b"
        r"|\b\d{2}[.-]\d{1,2}[.-]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?\b"
        r"|\b\d{1,2}:\d{2}(?::\d{2})?\b",
        text,
    )
    return match.group(0) if match else None


def _context_text(anchor) -> str:
    for tag_name in ("tr", "li", "article"):
        parent = anchor.find_parent(tag_name)
        if parent is not None:
            return parent.get_text(" ", strip=True)
    return anchor.parent.get_text(" ", strip=True) if anchor.parent is not None else anchor.get_text(" ", strip=True)


def _cursor_page(cursor: str | None) -> int:
    if cursor in {None, ""}:
        return 1
    try:
        return max(1, int(cursor))
    except ValueError:
        return 1


def _page_url_for_cursor(
    base_url: str,
    board_id: str,
    config: GenericBoardSourceConfig,
    page: int,
) -> str | None:
    if page <= 1:
        return base_url
    if not config.page_url_template:
        return None
    return config.page_url_template.format(page=page, board_id=board_id)
