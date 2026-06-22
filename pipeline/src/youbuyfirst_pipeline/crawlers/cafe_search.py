from __future__ import annotations

import hashlib
import html
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from urllib.parse import parse_qs, urlparse

import httpx

from youbuyfirst_pipeline.board_stream import BoardCoverage, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import SourceBlockedError, parse_datetime
from youbuyfirst_pipeline.models import RawPost


CAFE_SEARCH_SOURCES = frozenset({"NAVER_CAFE", "DAUM_CAFE"})

_SOURCE_DOMAINS = {
    "NAVER_CAFE": ("cafe.naver.com", "m.cafe.naver.com", "openapi.naver.com"),
    "DAUM_CAFE": ("cafe.daum.net", "m.cafe.daum.net"),
}
_SOURCE_SITE_QUERY = {
    "NAVER_CAFE": "site:cafe.naver.com",
    "DAUM_CAFE": "site:cafe.daum.net",
}
_CAFE_QUERY_GROUPS = (
    ("강남", "송파", "서초", "마포", "아파트"),
    ("분당", "판교", "광교", "동탄", "아파트"),
    ("평택", "파주", "수원", "용인", "아파트"),
    ("인천", "송도", "청라", "검단", "아파트"),
    ("대전", "세종", "부산", "대구", "아파트"),
    ("전세", "입주물량", "미분양", "공급", "아파트"),
    ("재건축", "재개발", "목동", "여의도", "성수"),
    ("청약", "분양", "신축", "입주", "단지"),
    ("래미안", "자이", "힐스테이트", "푸르지오", "더샵"),
    ("대출규제", "DSR", "부동산", "정책", "아파트"),
)
_REALESTATE_QUERY_TERMS = (
    "부동산",
    "아파트",
    "전세",
    "매매",
    "재건축",
    "재개발",
    "청약",
    "분양",
    "대출",
    "학군",
    "교통",
)
_REALESTATE_TEXT_PATTERN = re.compile(
    r"부동산|아파트|전세|월세|전월세|매매|실거래|집값|주택|분양|청약|재건축|재개발|"
    r"입주|미분양|대출|금리|학군|교통|신도시|상급지|강남|서초|송파|마포|성수|"
    r"분당|판교|동탄|광교|송도|세종|대전|파주|수원|용인|인천",
    re.IGNORECASE,
)
_EXCLUDED_TEXT_PATTERN = re.compile(
    r"구인|구직|채용|recruit|job|광고|홍보|분양상담|상담문의|스팸|도박|성인|무료상담|상담신청|"
    r"현장\s*상담석|전문\s*상담석|급매물\s*팩트\s*체크|로열층\s*클린\s*매물|내\s*집\s*마련\s*기회",
    re.IGNORECASE,
)
_LOAN_MARKETING_TEXT_PATTERN = re.compile(
    r"무직자대출|신용대출|대환대출|사업자대출|아파트구입대출|후순위아파트담보대출|대부|캐피탈|마이너스통장|"
    r"대출\s*(?:상담|상품|한도|조건|가능|승인|신청|비교)|"
    r"주담대\s*(?:금리|한도|상담)|주택담보대출\s*(?:실행|금리|한도|상담)|담보대출\s*(?:진행|실행|상담)|"
    r"금리\s*(?:비교|낮아서|최저)|최저\s*금리|은행\s*보험사|전문가\s*상담|"
    r"등급무직자|DSR\s*미적용\s*대출\s*상품|DSR\s*미적용\s*한도|LTV\s*100|대출\s*문의",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CafeSearchResult:
    title: str
    link: str
    snippet: str | None = None
    date: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class CafeParsedResults:
    posts: list[RawPost]
    filtered_count: int = 0
    excluded_title_count: int = 0
    keyword_miss_count: int = 0
    duplicate_link_count: int = 0


class CafeSearchClient(Protocol):
    def search(self, query: str, *, result_limit: int) -> list[CafeSearchResult]:
        ...


class SerpApiCafeSearchClient:
    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = "https://serpapi.com/search",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> SerpApiCafeSearchClient:
        api_key = os.getenv("SERPAPI_API_KEY", "").strip()
        if not api_key:
            raise SourceBlockedError("SERPAPI_API_KEY is required for public cafe search discovery")
        return cls(
            api_key,
            timeout_seconds=float(os.getenv("SERPAPI_TIMEOUT_SECONDS", "30")),
        )

    def search(self, query: str, *, result_limit: int) -> list[CafeSearchResult]:
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "output": "json",
            "google_domain": "google.co.kr",
            "gl": "kr",
            "hl": "ko",
            "num": result_limit,
            "tbs": "qdr:w,sbd:1",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.endpoint, params=params)
        if response.status_code in {401, 402, 403, 429}:
            raise SourceBlockedError(
                f"SerpApi cafe discovery failed: status={response.status_code}",
                status_code=response.status_code,
            )
        response.raise_for_status()
        data = response.json()
        error = str(data.get("error") or "").strip()
        if error:
            raise SourceBlockedError(f"SerpApi cafe discovery failed: {error}")
        return _parse_serpapi_results(data)


class KakaoDaumCafeSearchClient:
    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = "https://dapi.kakao.com/v2/search/cafe",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> KakaoDaumCafeSearchClient:
        api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
        if not api_key:
            raise SourceBlockedError("KAKAO_REST_API_KEY is required for Daum Cafe public search discovery")
        return cls(
            api_key,
            timeout_seconds=float(os.getenv("KAKAO_SEARCH_TIMEOUT_SECONDS", os.getenv("SERPAPI_TIMEOUT_SECONDS", "30"))),
        )

    def search(self, query: str, *, result_limit: int) -> list[CafeSearchResult]:
        params = {
            "query": _kakao_search_query(query),
            "sort": "recency",
            "size": max(1, min(result_limit, 50)),
        }
        headers = {
            "Authorization": f"KakaoAK {self.api_key}",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.endpoint, params=params, headers=headers)
        if response.status_code in {401, 402, 403, 429}:
            raise SourceBlockedError(
                f"Kakao Daum Cafe discovery failed: status={response.status_code}",
                status_code=response.status_code,
            )
        response.raise_for_status()
        data = response.json()
        return _parse_kakao_cafe_results(data)


class NaverCafeArticleSearchClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        endpoint: str = "https://openapi.naver.com/v1/search/cafearticle.json",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> NaverCafeArticleSearchClient:
        client_id = os.getenv("NAVER_SEARCH_CLIENT_ID", "").strip()
        client_secret = os.getenv("NAVER_SEARCH_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            raise SourceBlockedError(
                "NAVER_SEARCH_CLIENT_ID and NAVER_SEARCH_CLIENT_SECRET are required for Naver Cafe public search discovery"
            )
        return cls(
            client_id,
            client_secret,
            timeout_seconds=float(os.getenv("NAVER_SEARCH_TIMEOUT_SECONDS", os.getenv("SERPAPI_TIMEOUT_SECONDS", "30"))),
        )

    def search(self, query: str, *, result_limit: int) -> list[CafeSearchResult]:
        normalized_query = _provider_search_query(query)
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        target_count = max(1, min(result_limit, 1000))
        results: list[CafeSearchResult] = []
        with httpx.Client(timeout=self.timeout_seconds) as client:
            start = 1
            while len(results) < target_count and start <= 1000:
                display = min(100, target_count - len(results), 1001 - start)
                params = {
                    "query": normalized_query,
                    "display": max(1, display),
                    "start": start,
                    "sort": "date",
                }
                response = client.get(self.endpoint, params=params, headers=headers)
                if response.status_code in {401, 402, 403, 429}:
                    raise SourceBlockedError(
                        f"Naver CafeArticle discovery failed: status={response.status_code}",
                        status_code=response.status_code,
                    )
                response.raise_for_status()
                data = response.json()
                page_results = _parse_naver_cafe_results(data)
                results.extend(page_results)
                if len(page_results) < display:
                    break
                total = _int_or_zero(data.get("total"))
                if total and start + display > total:
                    break
                start += display
        return results[:target_count]


class CafeSearchAdapter:
    def __init__(
        self,
        target: CrawlTarget,
        search_client: CafeSearchClient | None = None,
        *,
        result_limit: int | None = None,
        query_limit: int | None = None,
        now_provider=None,
    ) -> None:
        if target.source not in CAFE_SEARCH_SOURCES:
            raise ValueError(f"{target.target_id} has unsupported cafe search source")
        if not target.board_id:
            raise ValueError(f"{target.target_id} is missing board_id")
        self.target = target
        self.source = target.source
        self.board_id = target.board_id
        self.search_client = search_client
        self.result_limit = result_limit or int(os.getenv("CAFE_SEARCH_RESULT_LIMIT", "200"))
        self.query_limit = max(1, query_limit or int(os.getenv("CAFE_SEARCH_QUERY_LIMIT", "10")))
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self.queries = _queries_for_target(target)[:self.query_limit]
        self.query = self.queries[0]

    async def fetch_posts(self) -> list[RawPost]:
        return (await self.fetch_stream()).posts

    async def fetch_stream(self, watermark: BoardWatermark | None = None) -> BoardStreamResult:
        observed_at = _as_utc(self.now_provider())
        search_client = self.search_client or _default_search_client_for_source(self.source)
        results: list[CafeSearchResult] = []
        for query in self.queries:
            results.extend(search_client.search(query, result_limit=self.result_limit))
        parsed = _posts_from_results(
            results,
            source=self.source,
            board_id=self.board_id,
            observed_at=observed_at,
        )
        posts = _apply_watermark(parsed.posts, watermark)
        return BoardStreamResult(
            posts=posts,
            coverage=BoardCoverage(
                pages_fetched=len(self.queries),
                rows_seen=len(results),
                ignored_pinned_count=0,
                duplicate_stop=False,
                cutoff_stop=False,
                oldest_seen_at=_oldest_seen_at(posts),
                newest_seen_at=_newest_seen_at(posts),
                last_cursor="search",
                coverage_status="complete",
                filtered_count=parsed.filtered_count,
                excluded_title_count=parsed.excluded_title_count,
                keyword_miss_count=parsed.keyword_miss_count,
                duplicate_link_count=parsed.duplicate_link_count,
            ),
        )


def _query_for_target(target: CrawlTarget) -> str:
    return _queries_for_target(target)[0]


def _queries_for_target(target: CrawlTarget) -> list[str]:
    explicit_query = _query_from_url(target.url)
    if explicit_query:
        return [explicit_query]
    site_query = _SOURCE_SITE_QUERY[target.source]
    return [f'{site_query} ({" OR ".join(group)})' for group in _CAFE_QUERY_GROUPS]


def _query_from_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    value = query.get("q") or query.get("query")
    if value:
        return value[0].strip()
    domain = (query.get("domain") or [""])[0].strip()
    if domain:
        return ""
    return ""


def _parse_serpapi_results(data: dict[str, Any]) -> list[CafeSearchResult]:
    raw_results = data.get("organic_results") or []
    results: list[CafeSearchResult] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        link = str(item.get("link") or "").strip()
        if not title or not link:
            continue
        results.append(
            CafeSearchResult(
                title=title,
                link=link,
                snippet=str(item.get("snippet")).strip() if item.get("snippet") else None,
                date=str(item.get("date")).strip() if item.get("date") else None,
                source=str(item.get("source")).strip() if item.get("source") else None,
            )
        )
    return results


def _parse_kakao_cafe_results(data: dict[str, Any]) -> list[CafeSearchResult]:
    raw_results = data.get("documents") or []
    results: list[CafeSearchResult] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        title = _strip_html(str(item.get("title") or "").strip())
        link = str(item.get("url") or "").strip()
        if not title or not link:
            continue
        results.append(
            CafeSearchResult(
                title=title,
                link=link,
                snippet=_strip_html(str(item.get("contents") or "").strip()) if item.get("contents") else None,
                date=str(item.get("datetime")).strip() if item.get("datetime") else None,
                source=str(item.get("cafename")).strip() if item.get("cafename") else "Daum Cafe",
            )
        )
    return results


def _parse_naver_cafe_results(data: dict[str, Any]) -> list[CafeSearchResult]:
    raw_results = data.get("items") or []
    results: list[CafeSearchResult] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        title = _strip_html(str(item.get("title") or "").strip())
        link = str(item.get("link") or "").strip()
        if not title or not link:
            continue
        results.append(
            CafeSearchResult(
                title=title,
                link=link,
                snippet=_strip_html(str(item.get("description") or "").strip()) if item.get("description") else None,
                date=None,
                source=str(item.get("cafename")).strip() if item.get("cafename") else "Naver Cafe",
            )
        )
    return results


def _default_search_client_for_source(source: str) -> CafeSearchClient:
    if (
        source == "NAVER_CAFE"
        and os.getenv("NAVER_SEARCH_CLIENT_ID", "").strip()
        and os.getenv("NAVER_SEARCH_CLIENT_SECRET", "").strip()
    ):
        return NaverCafeArticleSearchClient.from_env()
    if source == "DAUM_CAFE" and os.getenv("KAKAO_REST_API_KEY", "").strip():
        return KakaoDaumCafeSearchClient.from_env()
    return SerpApiCafeSearchClient.from_env()


def _kakao_search_query(query: str) -> str:
    return _provider_search_query(query)


def _provider_search_query(query: str) -> str:
    without_site = re.sub(r"site:\S+", " ", query)
    without_operators = re.sub(r"[()]", " ", without_site).replace(" OR ", " ")
    return re.sub(r"\s+", " ", without_operators).strip()


def _strip_html(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def _posts_from_results(
    results: list[CafeSearchResult],
    *,
    source: str,
    board_id: str,
    observed_at: datetime,
) -> CafeParsedResults:
    posts: list[RawPost] = []
    seen: set[str] = set()
    filtered_count = 0
    excluded_title_count = 0
    keyword_miss_count = 0
    duplicate_link_count = 0
    for result in results:
        filter_reason = _result_filter_reason(result, source=source)
        if filter_reason:
            filtered_count += 1
            if filter_reason == "excluded_title":
                excluded_title_count += 1
            if filter_reason == "keyword_miss":
                keyword_miss_count += 1
            continue
        external_id = _external_id(source, board_id, result.link)
        if external_id in seen:
            duplicate_link_count += 1
            continue
        seen.add(external_id)
        posts.append(
            RawPost(
                source=source,
                board_id=board_id,
                external_id=external_id,
                url=result.link,
                title=_trim(result.title, 180),
                content=_trim(result.snippet or "", 500),
                author="",
                published_at=_published_at(result.date, observed_at=observed_at),
                view_count=None,
                recommend_count=0,
                comment_count=0,
            )
        )
    return CafeParsedResults(
        posts=posts,
        filtered_count=filtered_count,
        excluded_title_count=excluded_title_count,
        keyword_miss_count=keyword_miss_count,
        duplicate_link_count=duplicate_link_count,
    )


def _is_allowed_result(result: CafeSearchResult, *, source: str) -> bool:
    return _result_filter_reason(result, source=source) == ""


def _result_filter_reason(result: CafeSearchResult, *, source: str) -> str:
    domain = _domain(result.link)
    if not _domain_matches_source(domain, source=source):
        return "domain_miss"
    searchable = " ".join(part for part in [result.title, result.snippet or "", result.source or ""] if part)
    if _EXCLUDED_TEXT_PATTERN.search(searchable):
        return "excluded_title"
    if _LOAN_MARKETING_TEXT_PATTERN.search(searchable):
        return "excluded_title"
    if not _REALESTATE_TEXT_PATTERN.search(searchable):
        return "keyword_miss"
    return ""


def _domain_matches_source(domain: str, *, source: str) -> bool:
    return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in _SOURCE_DOMAINS[source])


def _domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _external_id(source: str, board_id: str, url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"{source}-{board_id}-{digest}"


def _published_at(date_text: str | None, *, observed_at: datetime) -> datetime:
    if not date_text:
        return observed_at
    relative = _relative_datetime(date_text, observed_at=observed_at)
    if relative:
        return relative
    iso = _iso_datetime(date_text)
    if iso:
        return iso
    return _as_utc(parse_datetime(date_text))


def _iso_datetime(value: str) -> datetime | None:
    normalized = value.strip()
    if not normalized or "T" not in normalized:
        return None
    try:
        return _as_utc(datetime.fromisoformat(normalized.replace("Z", "+00:00")))
    except ValueError:
        return None


def _relative_datetime(value: str, *, observed_at: datetime) -> datetime | None:
    normalized = value.strip().lower()
    if normalized in {"어제", "yesterday"}:
        return observed_at - timedelta(days=1)
    match = re.search(r"(\d+)\s*(분|시간|일|주|개월|년|minute|hour|day|week|month|year)s?\s*(?:전|ago)?", normalized)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    if unit in {"분", "minute"}:
        return observed_at - timedelta(minutes=amount)
    if unit in {"시간", "hour"}:
        return observed_at - timedelta(hours=amount)
    if unit in {"일", "day"}:
        return observed_at - timedelta(days=amount)
    if unit in {"주", "week"}:
        return observed_at - timedelta(weeks=amount)
    if unit in {"개월", "month"}:
        return observed_at - timedelta(days=amount * 30)
    if unit in {"년", "year"}:
        return observed_at - timedelta(days=amount * 365)
    return None


def _apply_watermark(posts: list[RawPost], watermark: BoardWatermark | None) -> list[RawPost]:
    if watermark is None:
        return posts
    filtered: list[RawPost] = []
    for post in posts:
        if post.external_id == watermark.last_seen_external_id:
            continue
        if watermark.cutoff_at is not None and post.published_at < watermark.cutoff_at:
            continue
        filtered.append(post)
    return filtered


def _oldest_seen_at(posts: list[RawPost]) -> datetime | None:
    return min((post.published_at for post in posts), default=None)


def _newest_seen_at(posts: list[RawPost]) -> datetime | None:
    return max((post.published_at for post in posts), default=None)


def _trim(value: str, max_chars: int) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max(1, max_chars - 3)].rstrip()}..."


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
