from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_recent_issues import (
    RealEstateRecentIssueSearchTarget,
    SerpApiRecentIssueClient,
    build_recent_issue_content_items,
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
