from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

MAX_SEARCH_RESULT_AGE_DAYS = 45
TRUSTED_REALESTATE_VIDEO_QUERY = "site:youtube.com/watch (집코노미 OR 매부리TV OR 삼프로TV OR 부읽남TV OR 김작가TV OR 땅집고 OR KB부동산TV OR 부동산R114)"


@dataclass(frozen=True)
class RealEstateRecentIssueSearchTarget:
    target_type: str
    target_id: str
    display_name: str
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class SerpApiRecentIssueResult:
    title: str
    link: str
    source: str | None = None
    date: str | None = None
    snippet: str | None = None


class SerpApiRecentIssueError(RuntimeError):
    pass


@dataclass(frozen=True)
class RealEstateRecentIssueContentItem:
    content_id: str
    source_id: str
    content_type: str
    title: str
    snippet: str | None
    url: str
    domain: str | None
    published_at: datetime | None
    metric_label: str
    status_label: str
    ingested_at: datetime
    data_status: str
    target_id: str
    link_type: str
    confidence: float
    review_state: str

    def to_content_item_dict(self) -> dict:
        return {
            "contentId": self.content_id,
            "sourceId": self.source_id,
            "contentType": self.content_type,
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "domain": self.domain,
            "publishedAt": _iso(self.published_at) if self.published_at else None,
            "metricLabel": self.metric_label,
            "statusLabel": self.status_label,
            "ingestedAt": _iso(self.ingested_at),
            "dataStatus": self.data_status,
            "targets": [
                {
                    "targetId": self.target_id,
                    "linkType": self.link_type,
                    "confidence": self.confidence,
                    "reviewState": self.review_state,
                }
            ],
        }


class RealEstateRecentIssueSearchClient(Protocol):
    def search(self, query: str, *, result_limit: int) -> list[SerpApiRecentIssueResult]:
        ...


class SerpApiRecentIssueClient:
    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 30.0,
        endpoint: str = "https://serpapi.com/search",
    ) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.endpoint = endpoint

    def search(self, query: str, *, result_limit: int) -> list[SerpApiRecentIssueResult]:
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "output": "json",
            "google_domain": "google.co.kr",
            "gl": "kr",
            "hl": "ko",
            "num": result_limit,
        }
        if _uses_news_search(query):
            params["tbm"] = "nws"
        params["tbs"] = "qdr:m,sbd:1"
        with httpx.Client(timeout=self.timeout_seconds) as client:
            try:
                response = client.get(self.endpoint, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                raise SerpApiRecentIssueError(f"SerpApi request failed: status={status_code}") from None
            data = response.json()
        return _parse_serpapi_results(data)


def load_recent_issue_search_targets(path: str | Path) -> list[RealEstateRecentIssueSearchTarget]:
    records = _load_json_records(path)
    return [_target_from_mapping(record) for record in records]


def build_recent_issue_content_items(
    *,
    targets: list[RealEstateRecentIssueSearchTarget],
    search_client: RealEstateRecentIssueSearchClient,
    issue_keywords: tuple[str, ...],
    ingested_at: datetime,
    result_limit: int,
) -> list[RealEstateRecentIssueContentItem]:
    items: list[RealEstateRecentIssueContentItem] = []
    seen_urls: set[tuple[str, str]] = set()
    for target in targets:
        keywords = issue_keywords or target.keywords
        for keyword in keywords:
            query = build_recent_issue_query(target.display_name, keyword)
            for result in search_client.search(query, result_limit=result_limit):
                published_at = _published_at_from_result(result, ingested_at)
                if not _result_matches_query_intent(result, query=query):
                    continue
                if _is_stale_search_result(published_at, ingested_at=ingested_at):
                    continue
                if _is_search_noise_result(result):
                    continue
                url_key = (target.target_id, result.link)
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                items.append(
                    _content_item_from_result(
                        target,
                        result,
                        query=query,
                        ingested_at=ingested_at,
                        published_at=published_at,
                    )
                )
    return items


def build_recent_issue_query(display_name: str, keyword: str) -> str:
    normalized_keyword = keyword.strip()
    if normalized_keyword == "블로그":
        return " ".join(part for part in [display_name.strip(), "아파트", "부동산", "시장", "블로그"] if part)
    if normalized_keyword in {"영상", "유튜브"}:
        return " ".join(part for part in [display_name.strip(), "부동산", "시장", "분석", "토론", "영상", TRUSTED_REALESTATE_VIDEO_QUERY] if part)
    if normalized_keyword == "리포트":
        return " ".join(part for part in [display_name.strip(), "부동산", "시장", "리포트"] if part)
    return " ".join(part for part in [display_name.strip(), keyword.strip(), "부동산"] if part)


def _uses_news_search(query: str) -> bool:
    normalized = query.lower()
    return not _contains_any(normalized, ("영상", "유튜브", "youtube", "블로그", "브런치", "커뮤니티", "카페"))


def _parse_serpapi_results(data: dict[str, Any]) -> list[SerpApiRecentIssueResult]:
    raw_results = data.get("organic_results") or data.get("news_results") or []
    results = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        link = str(item.get("link") or "").strip()
        if not title or not link:
            continue
        results.append(
            SerpApiRecentIssueResult(
                title=title,
                link=link,
                source=str(item.get("source")).strip() if item.get("source") else None,
                date=str(item.get("date")).strip() if item.get("date") else None,
                snippet=str(item.get("snippet")).strip() if item.get("snippet") else None,
            )
        )
    return results


def _content_item_from_result(
    target: RealEstateRecentIssueSearchTarget,
    result: SerpApiRecentIssueResult,
    *,
    query: str,
    ingested_at: datetime,
    published_at: datetime | None = None,
) -> RealEstateRecentIssueContentItem:
    content_type = _content_type_for_result(result, query=query)
    return RealEstateRecentIssueContentItem(
        content_id=_content_id(result.link),
        source_id="serpapi:google_news",
        content_type=content_type,
        title=_trim(result.title, 200),
        snippet=_trim(result.snippet, 1000),
        url=result.link,
        domain=_domain(result.link),
        published_at=published_at,
        metric_label=_trim(f"query: {query}", 120),
        status_label="search_candidate",
        ingested_at=_as_utc(ingested_at),
        data_status="candidate",
        target_id=target.target_id,
        link_type="search_candidate",
        confidence=0.45,
        review_state="candidate",
    )


def _content_type_for_result(result: SerpApiRecentIssueResult, *, query: str) -> str:
    domain = (_domain(result.link) or "").lower()
    if "youtube.com" in domain or "youtu.be" in domain:
        return "video"
    if _is_link_domain(domain):
        return "link"
    if _is_report_domain(domain):
        return "report"
    return "news"


def _is_search_noise_result(result: SerpApiRecentIssueResult) -> bool:
    domain = (_domain(result.link) or "").lower()
    searchable = " ".join(
        part
        for part in [
            result.title,
            result.snippet or "",
            result.source or "",
            result.link,
            domain,
        ]
        if part
    ).lower()
    if _is_job_domain(domain):
        return True
    if domain == "gogogogo.kr" and "/share/youtube/" in result.link:
        return True
    if _contains_any(searchable, ("채용", "구인", "구직", "recruit", "jobkorea", "saramin", "wanted")):
        return True
    if (_is_link_domain(domain) or _is_video_domain(domain)) and _is_low_quality_media_candidate(searchable):
        return True
    return False


def _result_matches_query_intent(result: SerpApiRecentIssueResult, *, query: str) -> bool:
    normalized_query = query.lower()
    domain = (_domain(result.link) or "").lower()
    searchable = " ".join(
        part
        for part in [result.title, result.snippet or "", result.source or "", domain]
        if part
    ).lower()

    if "블로그" in normalized_query:
        return _is_link_domain(domain)
    if "영상" in normalized_query or "유튜브" in normalized_query:
        return _is_video_domain(domain) and not _is_invalid_youtube_candidate_url(result.link) and _is_trusted_real_estate_video_candidate(searchable)
    if "리포트" in normalized_query:
        return _is_report_domain(domain) or _contains_any(searchable, ("리포트", "보고서", "전망", "연구원", "시장 동향"))
    return True


def _is_stale_search_result(published_at: datetime | None, *, ingested_at: datetime) -> bool:
    if published_at is None:
        return False
    published_at = _as_utc(published_at)
    ingested_at = _as_utc(ingested_at)
    age = ingested_at - published_at
    return age > timedelta(days=MAX_SEARCH_RESULT_AGE_DAYS)


def _is_low_quality_media_candidate(searchable: str) -> bool:
    if re.search(r"보증금\s*\d|월세\s*\d", searchable):
        return True
    if _contains_any(
        searchable,
        (
            "속눈썹",
            "펜션",
            "캠핑",
            "맛집",
            "전통시장",
            "체험단",
            "원룸텔",
            "고시원",
            "일반공장",
            "경매",
            "법원입찰",
            "급매매 추천",
            "매물 홍보",
            "소액으로",
            "논 밭",
            "임야",
            "전원생활",
            "토지매매",
            "하이엔드 타운하우스",
            "아늑한",
            "언박싱",
        ),
    ):
        return True
    return False


def _is_trusted_real_estate_video_candidate(searchable: str) -> bool:
    return _contains_any(
        searchable,
        (
            "부읽남",
            "부동산 읽어주는 남자",
            "집코노미",
            "매부리tv",
            "삼프로tv",
            "3protv",
            "김작가 tv",
            "스튜tv",
            "스마트튜브",
            "빠숑",
            "kb부동산tv",
            "부동산r114",
            "직방tv",
            "땅집고",
        ),
    )


def _is_invalid_youtube_candidate_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if not _is_video_domain(hostname):
        return False
    if hostname == "youtu.be":
        return False
    return not parsed.path.startswith("/watch")


def _published_at_from_result(result: SerpApiRecentIssueResult, ingested_at: datetime) -> datetime | None:
    date_text = (result.date or "").strip()
    if not date_text:
        return None

    absolute = _parse_absolute_date(date_text)
    if absolute:
        return absolute

    relative = _parse_relative_date(date_text, ingested_at=ingested_at)
    if relative:
        return relative

    return None


def _parse_absolute_date(value: str) -> datetime | None:
    normalized = value.strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace("년", ".").replace("월", ".").replace("일", ".")
    normalized = normalized.replace("/", ".").replace("-", ".")
    normalized = re.sub(r"\.+", ".", normalized).strip(". ")

    ymd = re.search(r"(?P<year>20\d{2})\.(?P<month>\d{1,2})\.(?P<day>\d{1,2})", normalized)
    if ymd:
        return _date_parts_to_utc(ymd.group("year"), ymd.group("month"), ymd.group("day"))

    mdy = re.search(r"(?P<month>\d{1,2})\.(?P<day>\d{1,2})\.(?P<year>20\d{2})", normalized)
    if mdy:
        return _date_parts_to_utc(mdy.group("year"), mdy.group("month"), mdy.group("day"))

    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _date_parts_to_utc(year: str, month: str, day: str) -> datetime | None:
    try:
        return datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_relative_date(value: str, *, ingested_at: datetime) -> datetime | None:
    normalized = value.strip().lower()
    base = _as_utc(ingested_at)
    if normalized in {"yesterday", "어제"}:
        return base - timedelta(days=1)

    match = re.search(r"(\d+)\s*(분|시간|일|주|개월|달|년)\s*전", normalized)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        return base - _relative_delta(amount, unit)

    match = re.search(r"(\d+)\s*(minute|hour|day|week|month|year)s?\s+ago", normalized)
    if match:
        return base - _relative_delta(int(match.group(1)), match.group(2))

    return None


def _relative_delta(amount: int, unit: str) -> timedelta:
    if unit in {"분", "minute"}:
        return timedelta(minutes=amount)
    if unit in {"시간", "hour"}:
        return timedelta(hours=amount)
    if unit in {"일", "day"}:
        return timedelta(days=amount)
    if unit in {"주", "week"}:
        return timedelta(weeks=amount)
    if unit in {"개월", "달", "month"}:
        return timedelta(days=amount * 30)
    if unit in {"년", "year"}:
        return timedelta(days=amount * 365)
    return timedelta(0)


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle in value for needle in needles)


def _is_report_domain(domain: str) -> bool:
    return domain in {
        "www.reb.or.kr",
        "www.molit.go.kr",
        "www.krihs.re.kr",
        "www.khug.or.kr",
        "www.hf.go.kr",
        "www.bok.or.kr",
        "www.fss.or.kr",
        "www.kdi.re.kr",
        "www.kbfg.com",
        "www.kbstar.com",
        "kbthink.com",
        "www.hanaif.re.kr",
        "www.hanafn.com",
        "www.shinhan.com",
        "www.woorifg.com",
        "www.nhwm.com",
        "www.miraeasset.com",
        "securities.miraeasset.com",
        "www.samsungpop.com",
    }


def _is_link_domain(domain: str) -> bool:
    return _contains_any(domain, ("blog.", "brunch", "tistory", "cafe."))


def _is_video_domain(domain: str) -> bool:
    return _contains_any(domain, ("youtube.com", "youtu.be"))


def _is_job_domain(domain: str) -> bool:
    return _contains_any(domain, ("jobkorea", "saramin", "wanted"))


def _content_id(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return f"serpapi-issue-{digest}"


def _domain(url: str) -> str | None:
    hostname = urlparse(url).hostname
    return hostname.lower() if hostname else None


def _load_json_records(path: str | Path) -> list[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        if isinstance(payload, dict) and "items" in payload:
            records = payload.get("items", [])
        elif isinstance(payload, dict):
            records = [payload]
        else:
            records = payload
    if not isinstance(records, list):
        raise ValueError("recent issue target input must be JSON array, {items: []}, or JSONL")
    return [record for record in records if isinstance(record, dict)]


def _target_from_mapping(record: dict[str, Any]) -> RealEstateRecentIssueSearchTarget:
    target_type = str(record.get("targetType") or record.get("target_type") or "").strip()
    target_id = str(record.get("targetId") or record.get("target_id") or "").strip()
    display_name = str(record.get("displayName") or record.get("display_name") or "").strip()
    keywords = record.get("keywords") or ()
    if isinstance(keywords, str):
        keyword_values = tuple(keyword.strip() for keyword in keywords.split(",") if keyword.strip())
    else:
        keyword_values = tuple(str(keyword).strip() for keyword in keywords if str(keyword).strip())
    if not target_type or not target_id or not display_name:
        raise ValueError("recent issue target requires targetType, targetId, and displayName")
    return RealEstateRecentIssueSearchTarget(
        target_type=target_type,
        target_id=target_id,
        display_name=display_name,
        keywords=keyword_values,
    )


def _trim(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped[:max_length]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")
