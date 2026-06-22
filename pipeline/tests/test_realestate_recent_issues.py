from datetime import datetime, timezone

import httpx
import pytest

from youbuyfirst_pipeline.realestate_recent_issues import (
    RealEstateRecentIssueSearchTarget,
    SerpApiRecentIssueError,
    SerpApiRecentIssueResult,
    SerpApiRecentIssueClient,
    _is_stale_search_result,
    build_recent_issue_content_items,
    build_recent_issue_query,
    load_recent_issue_search_targets,
)


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class _FakeHttpxClient:
    gets: list[dict] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self) -> "_FakeHttpxClient":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def get(self, url: str, params: dict) -> _Response:
        self.gets.append({"url": url, "params": params, "timeout": self.timeout})
        return _Response(
            {
                "organic_results": [
                    {
                        "position": 1,
                        "title": "대전 도시철도 2호선 착공 이슈",
                        "link": "https://example.com/news/daejeon-tram",
                        "source": "Example News",
                        "date": "2026.06.10",
                        "snippet": "교통 이슈 후보가 다시 언급되고 있습니다.",
                    }
                ]
            }
        )


class _RateLimitedHttpxClient:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self) -> "_RateLimitedHttpxClient":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def get(self, url: str, params: dict) -> _Response:
        request = httpx.Request("GET", url, params=params)
        response = httpx.Response(429, request=request)
        raise httpx.HTTPStatusError("too many requests", request=request, response=response)


def test_serpapi_recent_issue_client_uses_google_news_parameters(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.realestate_recent_issues.httpx.Client", _FakeHttpxClient)
    client = SerpApiRecentIssueClient(api_key="test-key", timeout_seconds=12)

    results = client.search("대전 교통 부동산", result_limit=3)

    assert _FakeHttpxClient.gets == [
        {
            "url": "https://serpapi.com/search",
            "params": {
                "engine": "google",
                "q": "대전 교통 부동산",
                "api_key": "test-key",
                "output": "json",
                "google_domain": "google.co.kr",
                "gl": "kr",
                "hl": "ko",
                "tbm": "nws",
                "tbs": "qdr:m,sbd:1",
                "num": 3,
            },
            "timeout": 12,
        }
    ]
    assert results[0].title == "대전 도시철도 2호선 착공 이슈"
    assert results[0].link == "https://example.com/news/daejeon-tram"
    assert results[0].source == "Example News"
    assert results[0].date == "2026.06.10"
    assert results[0].snippet == "교통 이슈 후보가 다시 언급되고 있습니다."


def test_serpapi_recent_issue_client_sanitizes_provider_errors(monkeypatch):
    monkeypatch.setattr("youbuyfirst_pipeline.realestate_recent_issues.httpx.Client", _RateLimitedHttpxClient)
    client = SerpApiRecentIssueClient(api_key="secret-key", timeout_seconds=12)

    with pytest.raises(SerpApiRecentIssueError) as exc_info:
        client.search("서울 부동산", result_limit=3)

    message = str(exc_info.value)
    assert "status=429" in message
    assert "secret-key" not in message
    assert "api_key" not in message


def test_serpapi_recent_issue_client_uses_general_search_for_video_and_blog(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.realestate_recent_issues.httpx.Client", _FakeHttpxClient)
    client = SerpApiRecentIssueClient(api_key="test-key", timeout_seconds=12)

    client.search("서울특별시 부동산 영상", result_limit=2)

    assert _FakeHttpxClient.gets[0]["params"]["q"] == "서울특별시 부동산 영상"
    assert "tbm" not in _FakeHttpxClient.gets[0]["params"]
    assert _FakeHttpxClient.gets[0]["params"]["tbs"] == "qdr:m,sbd:1"


def test_recent_issue_query_narrows_blog_and_video_searches():
    assert build_recent_issue_query("서울특별시 강남구", "블로그") == "서울특별시 강남구 아파트 부동산 시장 블로그"
    assert build_recent_issue_query("서울특별시 강남구", "영상") == "서울특별시 강남구 부동산 시장 분석 토론 영상 site:youtube.com/watch (집코노미 OR 매부리TV OR 삼프로TV OR 부읽남TV OR 김작가TV OR 땅집고 OR KB부동산TV OR 부동산R114)"
    assert build_recent_issue_query("서울특별시 강남구", "리포트") == "서울특별시 강남구 부동산 시장 리포트"


def test_recent_issue_results_become_candidate_content_without_interest_scoring():
    target = RealEstateRecentIssueSearchTarget(
        target_type="region",
        target_id="region-daejeon",
        display_name="대전",
        keywords=("교통", "정책"),
    )
    client = _StaticRecentIssueClient()

    items = build_recent_issue_content_items(
        targets=[target],
        search_client=client,
        issue_keywords=("교통",),
        ingested_at=datetime(2026, 6, 12, 1, 30, tzinfo=timezone.utc),
        result_limit=5,
    )

    assert len(items) == 1
    item = items[0]
    payload = item.to_content_item_dict()
    assert payload == {
        "contentId": item.content_id,
        "sourceId": "serpapi:google_news",
        "contentType": "news",
        "title": "대전 교통 이슈 후보",
        "snippet": "도시철도 이슈가 최근 기사로 확인됩니다.",
        "url": "https://example.com/daejeon-transport",
        "domain": "example.com",
        "publishedAt": None,
        "metricLabel": "query: 대전 교통 부동산",
        "statusLabel": "search_candidate",
        "ingestedAt": "2026-06-12T01:30:00Z",
        "dataStatus": "candidate",
        "targets": [
            {
                "targetId": "region-daejeon",
                "linkType": "search_candidate",
                "confidence": 0.45,
                "reviewState": "candidate",
            }
        ],
    }
    assert "position" not in payload
    assert "resultCount" not in payload


def test_recent_issue_results_keep_serpapi_published_date():
    target = RealEstateRecentIssueSearchTarget(
        target_type="region",
        target_id="region-incheon",
        display_name="Incheon",
        keywords=("policy",),
    )
    client = _DatedRecentIssueClient()

    items = build_recent_issue_content_items(
        targets=[target],
        search_client=client,
        issue_keywords=("policy",),
        ingested_at=datetime(2026, 6, 17, 3, 0, tzinfo=timezone.utc),
        result_limit=3,
    )

    payloads = [item.to_content_item_dict() for item in items]
    assert payloads[0]["publishedAt"] == "2026-06-16T00:00:00Z"
    assert payloads[1]["publishedAt"] == "2026-06-17T00:00:00Z"


def test_recent_issue_stale_filter_keeps_recent_previous_year_results():
    assert not _is_stale_search_result(
        datetime(2025, 12, 31, 12, 0, tzinfo=timezone.utc),
        ingested_at=datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc),
    )
    assert _is_stale_search_result(
        datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc),
        ingested_at=datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc),
    )


def test_recent_issue_results_classify_reports_videos_and_links():
    target = RealEstateRecentIssueSearchTarget(
        target_type="region",
        target_id="region-seoul",
        display_name="서울특별시",
        keywords=("리포트",),
    )
    client = _MixedContentRecentIssueClient()

    items = build_recent_issue_content_items(
        targets=[target],
        search_client=client,
        issue_keywords=("리포트", "영상", "블로그"),
        ingested_at=datetime(2026, 6, 12, 1, 30, tzinfo=timezone.utc),
        result_limit=5,
    )

    content_types = [item.to_content_item_dict()["contentType"] for item in items]
    assert content_types == ["report", "video", "link"]


def test_recent_issue_results_keep_media_finance_quotes_as_news():
    target = RealEstateRecentIssueSearchTarget(
        target_type="region",
        target_id="region-gyeonggi",
        display_name="경기도",
        keywords=("부동산",),
    )
    client = _FinanceQuoteRecentIssueClient()

    items = build_recent_issue_content_items(
        targets=[target],
        search_client=client,
        issue_keywords=("부동산",),
        ingested_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
        result_limit=2,
    )

    content_types = [item.to_content_item_dict()["contentType"] for item in items]
    assert content_types == ["news", "report", "news"]


def test_recent_issue_results_drop_obvious_search_noise():
    target = RealEstateRecentIssueSearchTarget(
        target_type="region",
        target_id="region-seoul",
        display_name="서울특별시",
        keywords=("영상",),
    )
    client = _SearchNoiseRecentIssueClient()

    items = build_recent_issue_content_items(
        targets=[target],
        search_client=client,
        issue_keywords=("영상",),
        ingested_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
        result_limit=3,
    )

    payloads = [item.to_content_item_dict() for item in items]
    assert [payload["title"] for payload in payloads] == ["서울 주택시장 해설 영상 - 집코노미"]
    assert [payload["contentType"] for payload in payloads] == ["video"]


def test_recent_issue_results_drop_stale_and_low_quality_blog_candidates():
    target = RealEstateRecentIssueSearchTarget(
        target_type="region",
        target_id="region-busan",
        display_name="부산광역시",
        keywords=("블로그",),
    )
    client = _StaleBlogRecentIssueClient()

    items = build_recent_issue_content_items(
        targets=[target],
        search_client=client,
        issue_keywords=("블로그",),
        ingested_at=datetime(2026, 6, 17, tzinfo=timezone.utc),
        result_limit=4,
    )

    payloads = [item.to_content_item_dict() for item in items]
    assert [payload["title"] for payload in payloads] == ["부산 아파트 전세와 매매가 흐름 블로그"]
    assert payloads[0]["publishedAt"] == "2026-06-16T00:00:00Z"


def test_load_recent_issue_search_targets_from_jsonl(tmp_path):
    path = tmp_path / "targets.jsonl"
    path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","displayName":"대전","keywords":["교통","정책"]}',
        encoding="utf-8",
    )

    targets = load_recent_issue_search_targets(path)

    assert targets == [
        RealEstateRecentIssueSearchTarget(
            target_type="region",
            target_id="region-daejeon",
            display_name="대전",
            keywords=("교통", "정책"),
        )
    ]


class _StaticRecentIssueClient:
    def search(self, query: str, *, result_limit: int):
        assert query == "대전 교통 부동산"
        assert result_limit == 5
        return [
            type(
                "Result",
                (),
                {
                    "title": "대전 교통 이슈 후보",
                    "link": "https://example.com/daejeon-transport",
                    "source": "Example News",
                    "date": None,
                    "snippet": "도시철도 이슈가 최근 기사로 확인됩니다.",
                },
            )()
        ]


class _MixedContentRecentIssueClient:
    def search(self, query: str, *, result_limit: int):
        if "리포트" in query:
            return [
                SerpApiRecentIssueResult(
                    title="KB부동산 월간 주택시장 리포트",
                    link="https://www.kbstar.com/report/seoul",
                    source="KB국민은행",
                    snippet="금융사 리서치 자료입니다.",
                )
            ]
        if "영상" in query:
            return [
                SerpApiRecentIssueResult(
                    title="서울 주택시장 분석 영상 - 집코노미",
                    link="https://www.youtube.com/watch?v=demo",
                    source="YouTube",
                    snippet="집코노미 토론 후보입니다.",
                )
            ]
        if "블로그" in query:
            return [
                SerpApiRecentIssueResult(
                    title="서울 전세 현장 블로그 후기",
                    link="https://blog.naver.com/demo/1",
                    source="네이버 블로그",
                    snippet="블로그 원문 후보입니다.",
                )
            ]
        return []


class _DatedRecentIssueClient:
    def search(self, query: str, *, result_limit: int):
        assert query == "Incheon policy 부동산"
        assert result_limit == 3
        return [
            SerpApiRecentIssueResult(
                title="absolute date result",
                link="https://example.com/absolute-date",
                source="Example News",
                date="2026.06.16",
                snippet="absolute date",
            ),
            SerpApiRecentIssueResult(
                title="relative date result",
                link="https://example.com/relative-date",
                source="Example News",
                date="3 hours ago",
                snippet="relative date",
            ),
        ]


class _FinanceQuoteRecentIssueClient:
    def search(self, query: str, *, result_limit: int):
        assert query == "경기도 부동산 부동산"
        assert result_limit == 2
        return [
            SerpApiRecentIssueResult(
                title='KB부동산 "경기 남부 아파트값 강세"',
                link="https://news.einfomax.co.kr/news/articleView.html?idxno=4419533",
                source="연합인포맥스",
                snippet="언론사가 KB부동산 발언을 인용한 기사입니다.",
            ),
            SerpApiRecentIssueResult(
                title="KB부동산 주간 주택시장 리포트",
                link="https://www.kbstar.com/report/demo",
                source="KB국민은행",
                snippet="금융사 리서치 자료입니다.",
            ),
            SerpApiRecentIssueResult(
                title="KB금융, 부동산 시장 진단 담은 보고서 발간",
                link="https://www.handmk.com/news/articleView.html?idxno=37730",
                source="핸드메이커",
                snippet="언론사가 보고서 발간 소식을 다룬 기사입니다.",
            ),
        ]


class _SearchNoiseRecentIssueClient:
    def search(self, query: str, *, result_limit: int):
        assert query == "서울특별시 부동산 시장 분석 토론 영상 site:youtube.com/watch (집코노미 OR 매부리TV OR 삼프로TV OR 부읽남TV OR 김작가TV OR 땅집고 OR KB부동산TV OR 부동산R114)"
        assert result_limit == 3
        return [
            SerpApiRecentIssueResult(
                title="부동산 채널 유튜브 PD 채용",
                link="https://www.jobkorea.co.kr/Recruit/GI_Read/demo",
                source="잡코리아",
                snippet="채용 공고입니다.",
            ),
            SerpApiRecentIssueResult(
                title="YOUTUBE 영상 보기",
                link="https://gogogogo.kr/share/youtube/EcoJ8VurLhc",
                source="공유 페이지",
                snippet="유튜브 공유 래퍼입니다.",
            ),
            SerpApiRecentIssueResult(
                title="경기도부동산",
                link="https://www.youtube.com/hashtag/demo",
                source="YouTube",
                snippet="집값전망 영상 모음입니다.",
            ),
            SerpApiRecentIssueResult(
                title="서울 주택시장 해설 영상 - 집코노미",
                link="https://www.youtube.com/watch?v=demo",
                source="YouTube",
                snippet="집코노미 시장 분석 영상입니다.",
            ),
        ]


class _StaleBlogRecentIssueClient:
    def search(self, query: str, *, result_limit: int):
        assert query == "부산광역시 아파트 부동산 시장 블로그"
        assert result_limit == 4
        return [
            SerpApiRecentIssueResult(
                title="고시공고 상세보기 - 홍천군청",
                link="https://www.hongcheon.go.kr/news/notice",
                source="홍천군청",
                date="2026.06.17",
                snippet="행정 공고 페이지입니다.",
            ),
            SerpApiRecentIssueResult(
                title="부산 아파트 시장 해설 영상",
                link="https://www.youtube.com/watch?v=blog-query-video",
                source="YouTube",
                date="2026.06.17",
                snippet="부동산 시장 영상입니다.",
            ),
            SerpApiRecentIssueResult(
                title="부산 아파트 재건축 블로그 정리",
                link="https://blog.naver.com/demo/old",
                source="네이버 블로그",
                date="2025.12.20",
                snippet="작년 부동산 시장 분석 글입니다.",
            ),
            SerpApiRecentIssueResult(
                title="부산시 공장 경매 사하구 일반공장 경매",
                link="https://reyauction01.tistory.com/demo",
                source="티스토리",
                date="2026.06.16",
                snippet="경매 물건 홍보 글입니다.",
            ),
            SerpApiRecentIssueResult(
                title="부산 아파트 전세와 매매가 흐름 블로그",
                link="https://blog.naver.com/demo/fresh",
                source="네이버 블로그",
                date="2026.06.16",
                snippet="최근 부동산 시장과 단지 흐름을 정리한 글입니다.",
            ),
        ]
