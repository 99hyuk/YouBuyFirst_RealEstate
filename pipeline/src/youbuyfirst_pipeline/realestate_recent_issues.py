from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx


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
            "tbm": "nws",
            "num": result_limit,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.endpoint, params=params)
            response.raise_for_status()
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
                url_key = (target.target_id, result.link)
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                items.append(_content_item_from_result(target, result, query=query, ingested_at=ingested_at))
    return items


def build_recent_issue_query(display_name: str, keyword: str) -> str:
    return " ".join(part for part in [display_name.strip(), keyword.strip(), "부동산"] if part)


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
) -> RealEstateRecentIssueContentItem:
    return RealEstateRecentIssueContentItem(
        content_id=_content_id(result.link),
        source_id="serpapi:google_news",
        content_type="news",
        title=_trim(result.title, 200),
        snippet=_trim(result.snippet, 1000),
        url=result.link,
        domain=_domain(result.link),
        published_at=None,
        metric_label=_trim(f"query: {query}", 120),
        status_label="search_candidate",
        ingested_at=_as_utc(ingested_at),
        data_status="candidate",
        target_id=target.target_id,
        link_type="search_candidate",
        confidence=0.45,
        review_state="candidate",
    )


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
