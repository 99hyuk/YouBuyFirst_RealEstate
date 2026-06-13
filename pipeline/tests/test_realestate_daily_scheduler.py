from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_daily_scheduler import (
    RealEstateDailyRefreshJob,
    RealEstateRecentIssuesRefreshJob,
)
from youbuyfirst_pipeline.realestate_recent_issues import SerpApiRecentIssueResult


class _Step:
    def __init__(self, result=None, fail: bool = False) -> None:
        self.result = result or {"status": "OK"}
        self.fail = fail
        self.calls = 0

    def run_once(self):
        self.calls += 1
        if self.fail:
            raise RuntimeError("step failed")
        return self.result


class _RecentIssueSearchClient:
    def __init__(self) -> None:
        self.queries = []

    def search(self, query: str, *, result_limit: int):
        self.queries.append((query, result_limit))
        return [
            SerpApiRecentIssueResult(
                title=f"{query} 기사",
                link="https://example.com/recent-issue",
                source="Example News",
                snippet="최근 이슈 후보입니다.",
            )
        ]


class _RecentIssueSpringClient:
    def __init__(self) -> None:
        self.content_batches = []

    def publish_real_estate_content_items(self, items) -> None:
        self.content_batches.append([item.to_content_item_dict() for item in items])


def test_daily_refresh_job_runs_steps_in_order_and_summarizes_ok_status():
    market_step = _Step({"status": "OK", "fact_count": 3})
    reaction_step = _Step({"status": "OK", "snapshot_count": 2})
    job = RealEstateDailyRefreshJob(
        [
            ("market_facts", market_step),
            ("reaction_snapshots", reaction_step),
        ]
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.step_count == 2
    assert result.ok_count == 2
    assert result.failed_count == 0
    assert [step.name for step in result.steps] == ["market_facts", "reaction_snapshots"]
    assert market_step.calls == 1
    assert reaction_step.calls == 1


def test_daily_refresh_job_marks_partial_when_a_step_fails():
    job = RealEstateDailyRefreshJob(
        [
            ("market_facts", _Step({"status": "OK"})),
            ("reaction_snapshots", _Step(fail=True)),
        ]
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.ok_count == 1
    assert result.failed_count == 1
    assert result.steps[1].status == "ERROR"


def test_recent_issues_refresh_job_publishes_candidate_content(tmp_path):
    targets_path = tmp_path / "targets.jsonl"
    targets_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","displayName":"대전","keywords":["교통"]}',
        encoding="utf-8",
    )
    spring_client = _RecentIssueSpringClient()
    search_client = _RecentIssueSearchClient()
    job = RealEstateRecentIssuesRefreshJob(
        client=spring_client,
        search_client=search_client,
        search_targets_jsonl=targets_path,
        issue_keywords=("교통",),
        result_limit=2,
        clock=lambda: datetime(2026, 6, 14, 0, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.target_count == 1
    assert result.item_count == 1
    assert search_client.queries == [("대전 교통 부동산", 2)]
    assert spring_client.content_batches[0][0]["dataStatus"] == "candidate"
    assert spring_client.content_batches[0][0]["targets"][0]["targetId"] == "region-daejeon"
