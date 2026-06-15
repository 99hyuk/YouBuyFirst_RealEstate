import asyncio
from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_daily_scheduler import (
    RealEstateCommunityCrawlRefreshJob,
    RealEstateDailyRefreshJob,
    RealEstateEvidenceLogRefreshJob,
    RealEstateMapLayerRefreshJob,
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


class _CommunityPipeline:
    def __init__(self, results) -> None:
        self.results = results
        self.calls = 0

    async def run_once(self):
        self.calls += 1
        return self.results


class _RecentIssueSearchClient:
    def __init__(self) -> None:
        self.queries = []

    def search(self, query: str, *, result_limit: int):
        self.queries.append((query, result_limit))
        return [
            SerpApiRecentIssueResult(
                title=f"{query} 기사",
                link=f"https://example.com/recent-issue-{len(self.queries)}",
                source="Example News",
                snippet="최근 이슈 후보입니다.",
            )
        ]


class _RecentIssueSpringClient:
    def __init__(self) -> None:
        self.content_batches = []
        self.ranking_calls = []

    def get_real_estate_reaction_ranking(self, *, target_type: str, window_minutes: int, limit: int):
        self.ranking_calls.append(
            {
                "target_type": target_type,
                "window_minutes": window_minutes,
                "limit": limit,
            }
        )
        return {
            "window": "60m",
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
            "items": [
                {
                    "targetId": "region-daejeon",
                    "targetType": "region",
                    "displayName": "대전광역시",
                    "issueMix": [
                        {"label": "교통"},
                        {"label": "정책"},
                    ],
                },
                {
                    "targetId": "region-seoul-mapo",
                    "targetType": "region",
                    "displayName": "서울 마포구",
                    "issueMix": [],
                },
            ],
        }

    def publish_real_estate_content_items(self, items) -> None:
        self.content_batches.append([item.to_content_item_dict() for item in items])


class _EvidenceSpringClient:
    def __init__(self, ranking: dict | None = None) -> None:
        self.ranking = ranking or {
            "window": "60m",
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
            "freshness": {
                "source": "real_estate_reaction_snapshots",
                "asOf": "2026-06-14T01:02:00Z",
                "coverageStatus": "partial",
            },
            "items": [
                {
                    "targetId": "region-daejeon",
                    "targetType": "region",
                    "displayName": "대전",
                    "mentionCount": 24,
                    "reactionDirectionRatio": {
                        "expectation": 0.58,
                        "concern": 0.27,
                        "neutral": 0.15,
                    },
                    "heatScore": 81,
                    "confidence": 0.74,
                    "sourceCount": 2,
                    "sourceSkew": 0.41,
                    "coverageStatus": "partial",
                    "stale": False,
                    "issueMix": [
                        {
                            "issueKey": "transport",
                            "label": "교통",
                            "share": 0.45,
                            "direction": "expectation",
                            "summary": "광역 교통 기대가 반복됩니다.",
                            "confidence": 0.7,
                        }
                    ],
                }
            ],
        }
        self.ranking_calls = []
        self.market_fact_calls = []
        self.content_calls = []
        self.timeline_calls = []
        self.published_logs = []

    def get_real_estate_reaction_ranking(self, *, target_type: str, window_minutes: int, limit: int):
        self.ranking_calls.append(
            {
                "target_type": target_type,
                "window_minutes": window_minutes,
                "limit": limit,
            }
        )
        return self.ranking

    def list_real_estate_target_market_facts(self, target_id: str, *, limit: int):
        self.market_fact_calls.append({"target_id": target_id, "limit": limit})
        return [
            {
                "targetId": target_id,
                "factType": "apt_trade",
                "providerObjectId": "molit_apt_trade:30110:202606:1",
                "observedAt": "2026-06-03",
                "valueJson": {"dealAmountManwon": 42000},
            }
        ]

    def list_real_estate_target_content_items(self, target_id: str, *, feed: str, limit: int):
        self.content_calls.append({"target_id": target_id, "feed": feed, "limit": limit})
        return [
            {
                "contentId": "serpapi-region-daejeon-transport",
                "title": "대전 교통 이슈 후보",
                "targetId": target_id,
                "linkType": "search_candidate",
                "reviewState": "candidate",
            }
        ]

    def list_real_estate_target_timeline_events(self, target_id: str, *, limit: int):
        self.timeline_calls.append({"target_id": target_id, "limit": limit})
        return [
            {
                "id": "policy-event-supply-daejeon-region-daejeon-primary",
                "targetId": target_id,
                "eventType": "supply",
                "sourceRefType": "policy_event",
                "sourceRefId": "policy-event-supply-daejeon",
                "title": "대전 도심 공급계획 발표",
                "summary": "도심 공급 후보지와 교통 개선 일정이 함께 언급됩니다.",
                "occurredAt": "2026-06-09T00:00:00Z",
                "asOf": "2026-06-09T00:00:00Z",
                "dataStatus": "approved",
            }
        ]

    def publish_real_estate_evidence_logs(self, logs) -> None:
        self.published_logs.append(list(logs))


class _MapLayerSpringClient:
    def __init__(self) -> None:
        self.calls = []

    def refresh_real_estate_map_layer_snapshots(self, *, layer_type: str, periods, as_of: str):
        self.calls.append({"layer_type": layer_type, "periods": list(periods), "as_of": as_of})
        return {
            "layerType": layer_type,
            "periods": list(periods),
            "asOf": as_of,
            "acceptedSnapshots": 2 if layer_type == "sido" else 1,
            "skippedTargets": 3,
        }


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


def test_daily_refresh_job_marks_partial_when_a_step_needs_attention():
    job = RealEstateDailyRefreshJob(
        [
            ("market_facts", _Step({"status": "OK"})),
            ("recent_issues", _Step({"status": "CONFIG_MISSING", "missing": ["SERPAPI_API_KEY"]})),
            ("evidence_logs", _Step({"status": "PARTIAL", "log_count": 1})),
        ]
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.ok_count == 3
    assert result.failed_count == 0
    assert [step.status for step in result.steps] == ["OK", "CONFIG_MISSING", "PARTIAL"]


def test_community_crawl_refresh_job_runs_pipeline_and_summarizes_results():
    pipeline = _CommunityPipeline(
        [
            {
                "source": "PPOMPPU",
                "status": "OK",
                "seenPosts": 8,
                "acceptedPosts": 5,
            },
            {
                "source": "DCINSIDE",
                "status": "blocked",
                "seenPosts": 2,
                "acceptedPosts": 0,
            },
        ]
    )
    job = RealEstateCommunityCrawlRefreshJob(pipeline=pipeline)

    result = job.run_once()

    assert pipeline.calls == 1
    assert result.status == "PARTIAL"
    assert result.source_count == 2
    assert result.seen_post_count == 10
    assert result.accepted_post_count == 5
    assert result.blocked_count == 1
    assert result.failed_count == 0


def test_community_crawl_refresh_job_can_run_inside_existing_event_loop():
    pipeline = _CommunityPipeline(
        [
            {
                "source": "PPOMPPU",
                "status": "OK",
                "seenPosts": 2,
                "acceptedPosts": 1,
            }
        ]
    )
    job = RealEstateCommunityCrawlRefreshJob(pipeline=pipeline)

    async def run_job():
        return job.run_once()

    result = asyncio.run(run_job())

    assert result.status == "OK"
    assert result.source_count == 1
    assert result.seen_post_count == 2
    assert result.accepted_post_count == 1


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


def test_recent_issues_refresh_job_can_use_latest_backend_ranking_as_search_targets():
    spring_client = _RecentIssueSpringClient()
    search_client = _RecentIssueSearchClient()
    job = RealEstateRecentIssuesRefreshJob(
        client=spring_client,
        search_client=search_client,
        search_targets_jsonl=None,
        issue_keywords=(),
        target_type="region",
        window_minutes=60,
        ranking_limit=10,
        result_limit=2,
        clock=lambda: datetime(2026, 6, 14, 0, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.target_count == 2
    assert result.item_count == 3
    assert spring_client.ranking_calls == [
        {
            "target_type": "region",
            "window_minutes": 60,
            "limit": 10,
        }
    ]
    assert search_client.queries == [
        ("대전광역시 교통 부동산", 2),
        ("대전광역시 정책 부동산", 2),
        ("서울 마포구 부동산", 2),
    ]
    assert {item["targets"][0]["targetId"] for item in spring_client.content_batches[0]} == {
        "region-daejeon",
        "region-seoul-mapo",
    }


def test_evidence_log_refresh_job_builds_logs_from_latest_backend_snapshots():
    spring_client = _EvidenceSpringClient()
    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        target_type="region",
        window_minutes=60,
        ranking_limit=5,
        market_fact_limit=10,
        content_limit=10,
        timeline_limit=10,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.target_count == 1
    assert result.log_count == 1
    assert result.market_fact_count == 1
    assert result.timeline_event_count == 1
    assert result.content_item_count == 1
    assert spring_client.ranking_calls == [
        {
            "target_type": "region",
            "window_minutes": 60,
            "limit": 5,
        }
    ]
    published_log = spring_client.published_logs[0][0]
    assert published_log["targetId"] == "region-daejeon"
    assert published_log["evaluatedAt"] == "2026-06-14T02:00:00Z"
    assert "market_fact_missing" not in published_log["caveats"]
    assert "timeline_event_missing" not in published_log["caveats"]
    assert "search_candidate_missing" not in published_log["caveats"]
    assert {item["evidenceType"] for item in published_log["evidenceItems"]} == {
        "reaction",
        "market_fact",
        "timeline_event",
        "search_candidate",
    }


def test_evidence_log_refresh_job_can_attach_similar_window_candidates():
    spring_client = _EvidenceSpringClient()
    similar_calls = []

    def similar_windows_provider(target_id: str, ranking_row: dict, ranking: dict):
        similar_calls.append(
            {
                "target_id": target_id,
                "window_start": ranking["windowStart"],
                "row_target_id": ranking_row["targetId"],
            }
        )
        return [
            {
                "sourceTargetId": target_id,
                "matchedTargetId": "region-gwangju",
                "matchedWindowStart": "2026-03-01T00:00:00Z",
                "matchedWindowEnd": "2026-03-01T01:00:00Z",
                "similarityScore": 0.91,
                "evidenceItem": {
                    "evidenceItemId": "similar-region-daejeon-region-gwangju",
                    "evidenceType": "similar_window",
                    "refType": "similar_window",
                    "refId": "snapshot-gwangju-20260301000000",
                    "label": "유사 과거 window",
                    "valueText": "유사도 91.0% · 매매 +6.0%",
                    "severity": "info",
                },
            }
        ]

    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        similar_windows_provider=similar_windows_provider,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.similar_window_count == 1
    assert similar_calls == [
        {
            "target_id": "region-daejeon",
            "window_start": "2026-06-14T00:00:00Z",
            "row_target_id": "region-daejeon",
        }
    ]
    published_log = spring_client.published_logs[0][0]
    assert "similar_window_missing" not in published_log["caveats"]
    assert {item["evidenceType"] for item in published_log["evidenceItems"]} == {
        "reaction",
        "market_fact",
        "timeline_event",
        "similar_window",
        "search_candidate",
    }


def test_evidence_log_refresh_job_can_apply_llm_evaluator_before_publish():
    spring_client = _EvidenceSpringClient()
    llm_calls = []

    def llm_evaluator(log):
        llm_calls.append(log)
        updated = dict(log)
        updated["summary"] = "관심이 빠르게 증가했고 교통 쟁점이 함께 확인됩니다."
        updated["modelName"] = "gpt-5-mini"
        updated["promptVersion"] = "gms-evidence-v1"
        return updated

    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
        llm_evaluator=llm_evaluator,
    )

    result = job.run_once()

    assert result.status == "OK"
    assert len(llm_calls) == 1
    published_log = spring_client.published_logs[0][0]
    assert published_log["summary"] == "관심이 빠르게 증가했고 교통 쟁점이 함께 확인됩니다."
    assert published_log["modelName"] == "gpt-5-mini"
    assert published_log["promptVersion"] == "gms-evidence-v1"


def test_evidence_log_refresh_job_skips_publish_when_latest_ranking_is_empty():
    spring_client = _EvidenceSpringClient(
        ranking={
            "window": "60m",
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
            "freshness": {
                "source": "real_estate_reaction_snapshots",
                "asOf": "2026-06-14T01:02:00Z",
                "coverageStatus": "empty",
            },
            "items": [],
        }
    )
    job = RealEstateEvidenceLogRefreshJob(client=spring_client)

    result = job.run_once()

    assert result.status == "EMPTY"
    assert result.target_count == 0
    assert result.log_count == 0
    assert spring_client.published_logs == []


def test_evidence_log_refresh_job_marks_partial_when_search_candidates_are_missing():
    class _NoContentEvidenceSpringClient(_EvidenceSpringClient):
        def list_real_estate_target_content_items(self, target_id: str, *, feed: str, limit: int):
            self.content_calls.append({"target_id": target_id, "feed": feed, "limit": limit})
            return []

    spring_client = _NoContentEvidenceSpringClient()
    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        target_type="region",
        window_minutes=60,
        ranking_limit=5,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.log_count == 1
    assert result.content_item_count == 0
    published_log = spring_client.published_logs[0][0]
    assert "search_candidate_missing" in published_log["caveats"]


def test_map_layer_refresh_job_calls_backend_for_each_layer_type():
    spring_client = _MapLayerSpringClient()
    job = RealEstateMapLayerRefreshJob(
        client=spring_client,
        layer_types=("sido", "sigungu"),
        periods=("month", "halfYear"),
        clock=lambda: datetime(2026, 6, 21, 0, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.layer_count == 2
    assert result.snapshot_count == 3
    assert result.skipped_target_count == 6
    assert spring_client.calls == [
        {
            "layer_type": "sido",
            "periods": ["month", "halfYear"],
            "as_of": "2026-06-21T00:00:00Z",
        },
        {
            "layer_type": "sigungu",
            "periods": ["month", "halfYear"],
            "as_of": "2026-06-21T00:00:00Z",
        },
    ]
