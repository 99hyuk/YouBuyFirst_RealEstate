from __future__ import annotations

from datetime import datetime, timezone

import pytest

from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.cafe_search import (
    CafeSearchAdapter,
    CafeSearchResult,
    KakaoDaumCafeSearchClient,
    NaverCafeArticleSearchClient,
)


class FakeCafeSearchClient:
    def __init__(self, results: list[CafeSearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, *, result_limit: int) -> list[CafeSearchResult]:
        self.calls.append((query, result_limit))
        return self.results


class QueryAwareCafeSearchClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, *, result_limit: int) -> list[CafeSearchResult]:
        self.calls.append((query, result_limit))
        suffix = len(self.calls)
        return [
            CafeSearchResult(
                title=f"\uc11c\uc6b8 \uc544\ud30c\ud2b8 \uc804\uc138 \ud6c4\uae30 {suffix}",
                link=f"https://cafe.naver.com/estatecafe/{suffix}",
                snippet="\uc804\uc138\uc640 \ub9e4\ub9e4 \ubc18\uc751\uc744 \uc598\uae30\ud558\ub294 \uacf5\uac1c \uce74\ud398 \uae00",
            )
        ]


class FakeKakaoResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "documents": [
                {
                    "title": "<b>\ubd84\ub2f9</b> \uc544\ud30c\ud2b8 \uc804\uc138 \ubc18\uc751",
                    "contents": "\uc804\uc138\uc640 \ub9e4\ub9e4 \ubc18\uc751\uc774 \ub3d9\uc2dc\uc5d0 \uc788\ub294 \uacf5\uac1c \uce74\ud398 \uae00",
                    "url": "https://cafe.daum.net/happy-tech/abc/1",
                    "datetime": "2026-06-17T12:34:56.000+09:00",
                    "cafename": "\ud589\ubcf5\uc7ac\ud14c\ud06c",
                }
            ]
        }


class FakeKakaoHttpxClient:
    calls: list[dict] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None

    def get(self, endpoint: str, *, params: dict, headers: dict) -> FakeKakaoResponse:
        self.calls.append({"endpoint": endpoint, "params": params, "headers": headers, "timeout": self.timeout})
        return FakeKakaoResponse()


class FakeNaverResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "items": [
                {
                    "title": "<b>\ub9c8\ud3ec</b> \uc544\ud30c\ud2b8 \ub9e4\ub9e4 \uc774\uc57c\uae30",
                    "description": "\uc804\uc138\uc640 \uc7ac\uac74\ucd95 \uae30\ub300\uac00 \uac19\uc774 \uc5b8\uae09\ub418\ub294 \uacf5\uac1c \uce74\ud398 \uae00",
                    "link": "https://openapi.naver.com/l?AAABnaver-cafe-article",
                    "cafename": "\ubd80\ub3d9\uc0b0 \uc2a4\ud130\ub514",
                    "cafeurl": "https://cafe.naver.com/estate-study",
                }
            ]
        }


class FakeNaverHttpxClient:
    calls: list[dict] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None

    def get(self, endpoint: str, *, params: dict, headers: dict) -> FakeNaverResponse:
        self.calls.append({"endpoint": endpoint, "params": params, "headers": headers, "timeout": self.timeout})
        return FakeNaverResponse()


class FakePagedNaverResponse:
    status_code = 200

    def __init__(self, params: dict) -> None:
        self.params = params

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        start = int(self.params["start"])
        display = int(self.params["display"])
        return {
            "total": 250,
            "items": [
                {
                    "title": f"\uc11c\uc6b8 \uc544\ud30c\ud2b8 \ub9e4\ub9e4 \uc774\uc57c\uae30 {start + offset}",
                    "description": "\uc804\uc138\uc640 \uc7ac\uac74\ucd95 \uae30\ub300\uac00 \uac19\uc774 \uc5b8\uae09\ub418\ub294 \uacf5\uac1c \uce74\ud398 \uae00",
                    "link": f"https://openapi.naver.com/l?paged-{start + offset}",
                    "cafename": "\ubd80\ub3d9\uc0b0 \uc2a4\ud130\ub514",
                }
                for offset in range(display)
            ],
        }


class FakePagedNaverHttpxClient:
    calls: list[dict] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None

    def get(self, endpoint: str, *, params: dict, headers: dict) -> FakePagedNaverResponse:
        self.calls.append({"endpoint": endpoint, "params": params, "headers": headers, "timeout": self.timeout})
        return FakePagedNaverResponse(params)


@pytest.mark.anyio
async def test_cafe_search_adapter_keeps_only_matching_public_cafe_results():
    client = FakeCafeSearchClient(
        [
            CafeSearchResult(
                title="마포 신축 전세 얘기",
                link="https://cafe.naver.com/somecafe/123",
                snippet="마포 아파트 전세와 학군 이야기",
                date="1일 전",
                source="네이버 카페",
            ),
            CafeSearchResult(
                title="광고 분양 상담",
                link="https://cafe.naver.com/spam/999",
                snippet="분양 상담 문의",
            ),
            CafeSearchResult(
                title="부동산 기사",
                link="https://news.example.com/estate",
                snippet="카페가 아닌 검색 결과",
            ),
        ]
    )
    target = CrawlTarget.community_board(
        "NAVER_CAFE",
        board_id="public_search",
        url="serpapi://google?domain=cafe.naver.com",
    )
    adapter = CafeSearchAdapter(target=target, search_client=client, result_limit=10, query_limit=1)

    result = await adapter.fetch_stream()

    assert client.calls == [(adapter.query, 10)]
    assert [post.external_id for post in result.posts] == ["NAVER_CAFE-public_search-01176c5ce383c930"]
    assert result.posts[0].source == "NAVER_CAFE"
    assert result.posts[0].board_id == "public_search"
    assert result.posts[0].url == "https://cafe.naver.com/somecafe/123"
    assert result.posts[0].title == "마포 신축 전세 얘기"
    assert result.posts[0].content == "마포 아파트 전세와 학군 이야기"
    assert result.posts[0].author == ""
    assert result.posts[0].published_at.tzinfo is not None
    assert result.coverage is not None
    assert result.coverage.coverage_status == "complete"
    assert result.coverage.rows_seen == 3
    assert result.coverage.filtered_count == 2
    assert result.coverage.excluded_title_count == 1
    assert result.coverage.keyword_miss_count == 0
    assert result.coverage.oldest_seen_at is not None


@pytest.mark.anyio
async def test_cafe_search_adapter_excludes_loan_marketing_results():
    client = FakeCafeSearchClient(
        [
            CafeSearchResult(
                title="7\ub4f1\uae09\ubb34\uc9c1\uc790\ub300\ucd9c \uc870\uac74 \ube44\uad50\uc640 \uc8fc\uc758\uc810",
                link="https://cafe.naver.com/loanpromo/1",
                snippet="\ub300\ucd9c \uc0c1\ub2f4\uacfc \uc0c1\ud488 \ud55c\ub3c4\ub97c \ube44\uad50\ud558\ub294 \uae00",
            ),
            CafeSearchResult(
                title="\uac15\ub0a8 \uc544\ud30c\ud2b8 \uc804\uc138 \ud6c4\uae30",
                link="https://cafe.naver.com/estatecafe/2",
                snippet="\uc804\uc138\uc640 \ub9e4\ub9e4 \ubc18\uc751\uc744 \uc598\uae30\ud558\ub294 \uacf5\uac1c \uce74\ud398 \uae00",
            ),
        ]
    )
    target = CrawlTarget.community_board(
        "NAVER_CAFE",
        board_id="public_search",
        url="serpapi://google?domain=cafe.naver.com",
    )
    adapter = CafeSearchAdapter(target=target, search_client=client, result_limit=10, query_limit=1)

    result = await adapter.fetch_stream()

    assert [post.title for post in result.posts] == ["\uac15\ub0a8 \uc544\ud30c\ud2b8 \uc804\uc138 \ud6c4\uae30"]
    assert result.coverage is not None
    assert result.coverage.filtered_count == 1
    assert result.coverage.excluded_title_count == 1


@pytest.mark.anyio
async def test_cafe_search_adapter_uses_ingested_time_when_search_date_is_missing():
    observed_at = datetime(2026, 6, 17, 5, 0, tzinfo=timezone.utc)
    client = FakeCafeSearchClient(
        [
            CafeSearchResult(
                title="대전 둔산 전세 반응",
                link="https://cafe.daum.net/happy-tech/abc/1",
                snippet="대전 둔산 전세와 매물 이야기",
            )
        ]
    )
    target = CrawlTarget.community_board(
        "DAUM_CAFE",
        board_id="public_search",
        url="serpapi://google?domain=cafe.daum.net",
    )
    adapter = CafeSearchAdapter(target=target, search_client=client, now_provider=lambda: observed_at, query_limit=1)

    result = await adapter.fetch_stream()

    assert result.posts[0].published_at == observed_at
    assert result.coverage is not None
    assert result.coverage.newest_seen_at == observed_at


@pytest.mark.anyio
async def test_cafe_search_adapter_expands_public_cafe_discovery_queries():
    client = QueryAwareCafeSearchClient()
    target = CrawlTarget.community_board(
        "NAVER_CAFE",
        board_id="public_search",
        url="serpapi://google?domain=cafe.naver.com",
    )
    adapter = CafeSearchAdapter(target=target, search_client=client, result_limit=5, query_limit=3)

    result = await adapter.fetch_stream()

    assert len(client.calls) == 3
    assert all(call[0].startswith("site:cafe.naver.com") for call in client.calls)
    assert all(call[1] == 5 for call in client.calls)
    assert len(result.posts) == 3
    assert result.coverage is not None
    assert result.coverage.pages_fetched == 3
    assert result.coverage.rows_seen == 3


def test_kakao_daum_cafe_search_client_maps_official_search_results(monkeypatch):
    FakeKakaoHttpxClient.calls = []
    monkeypatch.setattr("httpx.Client", FakeKakaoHttpxClient)
    client = KakaoDaumCafeSearchClient("local-key", timeout_seconds=7)

    results = client.search("site:cafe.daum.net (\ubd80\ub3d9\uc0b0 OR \uc544\ud30c\ud2b8)", result_limit=80)

    assert len(results) == 1
    assert results[0].title == "\ubd84\ub2f9 \uc544\ud30c\ud2b8 \uc804\uc138 \ubc18\uc751"
    assert results[0].link == "https://cafe.daum.net/happy-tech/abc/1"
    assert results[0].date == "2026-06-17T12:34:56.000+09:00"
    assert FakeKakaoHttpxClient.calls == [
        {
            "endpoint": "https://dapi.kakao.com/v2/search/cafe",
            "params": {"query": "\ubd80\ub3d9\uc0b0 \uc544\ud30c\ud2b8", "sort": "recency", "size": 50},
            "headers": {"Authorization": "KakaoAK local-key"},
            "timeout": 7,
        }
    ]


def test_naver_cafe_article_search_client_maps_official_search_results(monkeypatch):
    FakeNaverHttpxClient.calls = []
    monkeypatch.setattr("httpx.Client", FakeNaverHttpxClient)
    client = NaverCafeArticleSearchClient("client-id", "client-secret", timeout_seconds=9)

    results = client.search("site:cafe.naver.com (\ubd80\ub3d9\uc0b0 OR \uc544\ud30c\ud2b8)", result_limit=120)

    assert len(results) == 1
    assert results[0].title == "\ub9c8\ud3ec \uc544\ud30c\ud2b8 \ub9e4\ub9e4 \uc774\uc57c\uae30"
    assert results[0].link == "https://openapi.naver.com/l?AAABnaver-cafe-article"
    assert results[0].snippet == "\uc804\uc138\uc640 \uc7ac\uac74\ucd95 \uae30\ub300\uac00 \uac19\uc774 \uc5b8\uae09\ub418\ub294 \uacf5\uac1c \uce74\ud398 \uae00"
    assert results[0].date is None
    assert FakeNaverHttpxClient.calls == [
        {
            "endpoint": "https://openapi.naver.com/v1/search/cafearticle.json",
            "params": {"query": "\ubd80\ub3d9\uc0b0 \uc544\ud30c\ud2b8", "display": 100, "start": 1, "sort": "date"},
            "headers": {
                "X-Naver-Client-Id": "client-id",
                "X-Naver-Client-Secret": "client-secret",
            },
            "timeout": 9,
        }
    ]


def test_naver_cafe_article_search_client_paginates_to_requested_limit(monkeypatch):
    FakePagedNaverHttpxClient.calls = []
    monkeypatch.setattr("httpx.Client", FakePagedNaverHttpxClient)
    client = NaverCafeArticleSearchClient("client-id", "client-secret", timeout_seconds=9)

    results = client.search("site:cafe.naver.com (\uc11c\uc6b8 OR \uc544\ud30c\ud2b8)", result_limit=120)

    assert len(results) == 120
    assert FakePagedNaverHttpxClient.calls[0]["params"] == {
        "query": "\uc11c\uc6b8 \uc544\ud30c\ud2b8",
        "display": 100,
        "start": 1,
        "sort": "date",
    }
    assert FakePagedNaverHttpxClient.calls[1]["params"] == {
        "query": "\uc11c\uc6b8 \uc544\ud30c\ud2b8",
        "display": 20,
        "start": 101,
        "sort": "date",
    }
