import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main
from youbuyfirst_pipeline.realestate_recent_issues import SerpApiRecentIssueResult


class _FakeRecentIssueClient:
    def __init__(self) -> None:
        self.queries = []

    def search(self, query: str, *, result_limit: int):
        self.queries.append((query, result_limit))
        return [
            SerpApiRecentIssueResult(
                title=f"{query} 기사",
                link=f"https://example.com/{len(self.queries)}",
                source="Example News",
                snippet="검색 후보입니다.",
            )
        ]


class _FakeSpringClient:
    def __init__(self) -> None:
        self.content_batches = []

    def publish_real_estate_content_items(self, items) -> None:
        self.content_batches.append([item.to_content_item_dict() for item in items])


def test_realestate_recent_issues_command_prints_candidate_content_payload(monkeypatch, tmp_path, capsys):
    targets_path = tmp_path / "targets.jsonl"
    targets_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","displayName":"대전","keywords":["교통"]}',
        encoding="utf-8",
    )
    fake_client = _FakeRecentIssueClient()
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-recent-issues",
            "--realestate-search-targets-jsonl",
            str(targets_path),
            "--realestate-issue-keywords",
            "교통",
            "--realestate-search-as-of",
            "2026-06-12T01:30:00Z",
            "--serpapi-result-limit",
            "2",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert fake_client.queries == [("대전 교통 부동산", 2)]
    assert payload["items"][0]["sourceId"] == "serpapi:google_news"
    assert payload["items"][0]["dataStatus"] == "candidate"
    assert payload["items"][0]["targets"][0] == {
        "targetId": "region-daejeon",
        "linkType": "search_candidate",
        "confidence": 0.45,
        "reviewState": "candidate",
    }


def test_realestate_recent_issues_push_command_publishes_candidate_content(monkeypatch, tmp_path):
    targets_path = tmp_path / "targets.jsonl"
    targets_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","displayName":"대전","keywords":["교통"]}',
        encoding="utf-8",
    )
    fake_search_client = _FakeRecentIssueClient()
    fake_spring_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: fake_search_client)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_spring_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-recent-issues-push",
            "--realestate-search-targets-jsonl",
            str(targets_path),
            "--realestate-search-as-of",
            "2026-06-12T01:30:00Z",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert fake_search_client.queries == [("대전 교통 부동산", 5)]
    assert fake_spring_client.content_batches[0][0]["title"] == "대전 교통 부동산 기사"
    assert fake_spring_client.content_batches[0][0]["targets"][0]["reviewState"] == "candidate"
