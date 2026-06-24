import asyncio
import json
import sys
from types import SimpleNamespace

from youbuyfirst_pipeline import main as pipeline_main
from youbuyfirst_pipeline.realestate_recent_issues import SerpApiRecentIssueResult
from youbuyfirst_pipeline.source_policy import CrawlRuntimeEnvironment


class _FakePipeline:
    async def run_once(self):
        return [{"source": "PPOMPPU", "status": "OK", "seenPosts": 2, "acceptedPosts": 1}]


class _FakeSpringClient:
    pass


class _RuntimeAwarePipeline(_FakePipeline):
    runtime_environment = CrawlRuntimeEnvironment.PUBLIC


class _FakeRefreshJob:
    def run_once(self) -> dict:
        return {"status": "OK"}


class _FakeRecentIssueClient:
    def __init__(self) -> None:
        self.queries = []

    def search(self, query: str, *, result_limit: int):
        self.queries.append({"query": query, "result_limit": result_limit})
        return [
            SerpApiRecentIssueResult(
                title=f"{query} 최근 이슈",
                link="https://example.com/realestate/recent-issue",
                source="Example News",
                snippet="최근 이슈 후보입니다.",
            )
        ]


class _DailyRefreshSpringClient:
    def __init__(self) -> None:
        self.content_batches = []
        self.published_logs = []
        self.map_layer_calls = []

    def get_real_estate_reaction_ranking(self, *, target_type: str, window_minutes: int, limit: int):
        return {
            "window": f"{window_minutes}m",
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
            "items": [
                {
                    "targetId": "region-daejeon",
                    "targetType": target_type,
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

    def publish_real_estate_content_items(self, items) -> None:
        self.content_batches.append([item.to_content_item_dict() for item in items])

    def list_real_estate_target_market_facts(self, target_id: str, *, limit: int):
        return [
            {
                "targetId": target_id,
                "factType": "apt_trade",
                "providerObjectId": "molit_apt_trade:30110:202606:1",
                "observedAt": "2026-06-03",
                "valueJson": {"dealAmountManwon": 42000},
            }
        ]

    def list_real_estate_target_timeline_events(self, target_id: str, *, limit: int):
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

    def list_real_estate_target_content_items(self, target_id: str, *, feed: str, limit: int):
        return [
            {
                "contentId": "serpapi-region-daejeon-transport",
                "title": "대전 교통 이슈 후보",
                "targetId": target_id,
                "linkType": "search_candidate",
                "reviewState": "candidate",
            }
        ]

    def publish_real_estate_evidence_logs(self, logs) -> None:
        self.published_logs.append(list(logs))

    def refresh_real_estate_map_layer_snapshots(self, *, layer_type: str, periods, as_of: str):
        self.map_layer_calls.append({"layer_type": layer_type, "periods": list(periods), "as_of": as_of})
        return {
            "layerType": layer_type,
            "periods": list(periods),
            "asOf": as_of,
            "acceptedSnapshots": 2,
            "skippedTargets": 0,
        }


class _ReadinessSpringClient:
    def list_real_estate_aliases(self, **_kwargs):
        return [
            {
                "targetType": "complex",
                "targetId": "complex-molit-1144010100-maraepu",
                "alias": "마래푸",
                "source": "molit:market-fact",
            }
        ]

    def list_real_estate_target_edges(self, **_kwargs):
        return [
            {
                "fromTargetType": "region",
                "fromTargetId": "region-1144010100",
                "toTargetType": "complex",
                "toTargetId": "complex-molit-1144010100-maraepu",
                "edgeType": "contains",
                "source": "molit:market-fact",
            }
        ]

    def get_real_estate_reaction_ranking(self, *, target_type: str, window_minutes: int, limit: int):
        assert window_minutes == 10080
        assert limit == 10
        return {
            "items": [
                {
                    "targetType": target_type,
                    "targetId": f"{target_type}-readiness-{index}",
                    "displayName": f"{target_type} readiness {index}",
                }
                for index in range(10)
            ]
        }
        if target_type == "complex":
            return {
                "items": [
                    {
                        "targetType": "complex",
                        "targetId": "complex-molit-1144010100-maraepu",
                        "displayName": "마포래미안푸르지오",
                    }
                ]
            }
        return {
            "items": [
                {
                    "targetType": "region",
                    "targetId": "region-seoul-mapo",
                    "displayName": "서울 마포구",
                }
            ]
        }


class _FakeQdrantClient:
    collection_name = "realestate_reaction_windows"

    def __init__(self, *, ready: bool = True) -> None:
        self.ready = ready
        self.search_requests = []

    def collection_info(self):
        if not self.ready:
            return {"status": "missing", "result": None}
        return {
            "result": {
                "status": "green",
                "points_count": 8,
                "vectors_count": 8,
            }
        }

    def search(self, *, vector, top_n: int, exclude_input_id: str | None = None):
        self.search_requests.append(
            {
                "vector": vector,
                "top_n": top_n,
                "exclude_input_id": exclude_input_id,
            }
        )
        return [
            {
                "id": "matched-window",
                "score": 0.93,
                "payload": {
                    "targetId": "region-gwangju",
                    "refId": "snapshot-gwangju-20260301000000",
                    "windowStart": "2026-03-01T00:00:00Z",
                    "windowEnd": "2026-03-01T01:00:00Z",
                    "text": "광주 전세 우려와 교통 기대",
                },
            }
        ]


def _daily_embedding_item(target_id: str = "region-daejeon") -> dict:
    return {
        "inputId": f"reaction-window:{target_id}:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z",
        "targetType": "region",
        "targetId": target_id,
        "refType": "reaction_snapshot",
        "refId": f"snapshot-{target_id}-20260614000000",
        "provider": "gms:gemini",
        "modelName": "gemini-embedding-2",
        "text": "대전 교통 기대와 공급 우려",
        "embedding": [0.1, 0.2, 0.3],
        "dimensions": 3,
        "dataStatus": "generated",
        "windowStart": "2026-06-14T00:00:00Z",
        "windowEnd": "2026-06-14T01:00:00Z",
    }


def test_build_pipeline_from_args_applies_crawl_runtime_environment(monkeypatch):
    pipeline = _RuntimeAwarePipeline()
    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: pipeline)

    result = pipeline_main._build_pipeline_from_args(SimpleNamespace(crawl_runtime_environment="local"))

    assert result is pipeline
    assert result.runtime_environment == CrawlRuntimeEnvironment.LOCAL


def test_serve_command_can_enable_real_estate_market_facts_refresh(monkeypatch):
    captured = {}
    realestate_job = object()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: realestate_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--realestate-market-facts-refresh-interval-minutes",
            "720",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert captured["kwargs"]["realestate_market_facts_refresh_job"] is realestate_job
    assert captured["kwargs"]["realestate_market_facts_interval_minutes"] == 720


def test_serve_command_can_enable_real_estate_reaction_snapshot_refresh(monkeypatch):
    captured = {}
    builder_kwargs = {}
    reaction_job = object()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    def fake_build_reaction_job(**kwargs):
        builder_kwargs.update(kwargs)
        return reaction_job

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        fake_build_reaction_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-aliases-jsonl",
            "aliases.jsonl",
            "--community-posts-jsonl",
            "posts.jsonl",
            "--reaction-window-minutes",
            "60",
            "--reaction-stale-after-minutes",
            "180",
            "--realestate-reaction-snapshots-refresh-interval-minutes",
            "15",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert captured["kwargs"]["realestate_reaction_snapshot_refresh_job"] is reaction_job
    assert captured["kwargs"]["realestate_reaction_snapshot_interval_minutes"] == 15
    assert builder_kwargs["stale_after_minutes"] == 180


def test_serve_command_can_enable_reaction_snapshot_refresh_from_backend_posts(monkeypatch):
    captured = {}
    builder_kwargs = {}
    reaction_job = object()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    def fake_build_reaction_job(**kwargs):
        builder_kwargs.update(kwargs)
        return reaction_job

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        fake_build_reaction_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-aliases-jsonl",
            "aliases.jsonl",
            "--realestate-use-backend-community-posts",
            "--realestate-community-posts-source",
            "PPOMPPU",
            "--realestate-community-posts-limit",
            "250",
            "--realestate-reaction-use-current-window",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert captured["kwargs"]["realestate_reaction_snapshot_refresh_job"] is reaction_job
    assert builder_kwargs["community_posts_jsonl"] is None
    assert builder_kwargs["backend_posts_source"] == "PPOMPPU"
    assert builder_kwargs["backend_posts_limit"] == 250
    assert builder_kwargs["use_current_window"] is True


def test_serve_command_can_enable_reaction_snapshot_refresh_from_backend_aliases(monkeypatch):
    captured = {}
    builder_kwargs = {}
    reaction_job = object()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    def fake_build_reaction_job(**kwargs):
        builder_kwargs.update(kwargs)
        return reaction_job

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        fake_build_reaction_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-use-backend-aliases",
            "--realestate-use-backend-community-posts",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert captured["kwargs"]["realestate_reaction_snapshot_refresh_job"] is reaction_job
    assert builder_kwargs["aliases_jsonl"] is None
    assert callable(builder_kwargs["alias_loader"])
    assert builder_kwargs["community_posts_jsonl"] is None


def test_serve_command_can_group_real_estate_refresh_jobs_into_daily_refresh(monkeypatch, tmp_path):
    captured = {}
    market_job = _FakeRefreshJob()
    targets_path = tmp_path / "targets.jsonl"
    targets_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","displayName":"대전","keywords":["교통"]}',
        encoding="utf-8",
    )

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: market_job,
    )
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: _FakeRecentIssueClient())
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--realestate-daily-refresh-interval-minutes",
            "1440",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--enable-realestate-recent-issues-refresh",
            "--realestate-search-targets-jsonl",
            str(targets_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert captured["kwargs"]["realestate_market_facts_refresh_job"] is None
    assert captured["kwargs"]["realestate_daily_refresh_interval_minutes"] == 1440
    assert [name for name, _step in daily_job.steps] == ["market_facts", "recent_issues"]


def test_serve_command_can_group_recent_issue_refresh_from_backend_ranking(monkeypatch):
    captured = {}
    spring_client = _FakeSpringClient()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: _FakeRecentIssueClient())
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-recent-issues-refresh",
            "--realestate-daily-reaction-window-minutes",
            "1440",
            "--realestate-recent-issues-ranking-limit",
            "10",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == ["recent_issues"]
    recent_issue_step = daily_job.steps[0][1]
    assert recent_issue_step.client is spring_client
    assert recent_issue_step.search_targets_jsonl is None
    assert recent_issue_step.target_type == "region"
    assert recent_issue_step.window_minutes == 1440
    assert recent_issue_step.ranking_limit == 10


def test_daily_refresh_uses_7d_reaction_window_by_default(monkeypatch):
    captured = {}
    spring_client = _FakeSpringClient()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: _FakeRecentIssueClient())
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-use-backend-aliases",
            "--realestate-use-backend-community-posts",
            "--enable-realestate-recent-issues-refresh",
            "--enable-realestate-evidence-logs-refresh",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == [
        "reaction_snapshots",
        "recent_issues",
        "evidence_logs",
    ]
    assert daily_job.steps[0][1].window_minutes == 10080
    assert daily_job.steps[1][1].window_minutes == 10080
    assert daily_job.steps[2][1].window_minutes == 10080


def test_serve_command_can_group_full_mvp_daily_refresh_in_order(monkeypatch):
    captured = {}
    pipeline = _FakePipeline()
    spring_client = _FakeSpringClient()
    market_job = _FakeRefreshJob()
    official_stats_job = _FakeRefreshJob()
    community_seed_job = _FakeRefreshJob()
    reaction_job = _FakeRefreshJob()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: pipeline)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: market_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        lambda **kwargs: reaction_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "RealEstateOfficialStatsRefreshJob",
        lambda **kwargs: official_stats_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "RealEstateCommunityComplexSeedRefreshJob",
        lambda **kwargs: community_seed_job,
    )
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: _FakeRecentIssueClient())
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--enable-realestate-official-stats-refresh",
            "--enable-realestate-daily-crawl-refresh",
            "--enable-realestate-community-complex-seed-refresh",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-aliases-jsonl",
            "aliases.jsonl",
            "--realestate-use-backend-community-posts",
            "--enable-realestate-recent-issues-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--enable-realestate-map-layer-refresh",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == [
        "market_facts",
        "official_stats",
        "community_crawl",
        "community_complex_seed",
        "reaction_snapshots",
        "recent_issues",
        "evidence_logs",
        "map_layers",
    ]
    assert daily_job.steps[2][1].pipeline is pipeline


def test_serve_command_can_insert_complex_registry_before_reaction_snapshots(monkeypatch):
    captured = {}
    pipeline = _FakePipeline()
    spring_client = _FakeSpringClient()
    market_job = _FakeRefreshJob()
    official_stats_job = _FakeRefreshJob()
    complex_registry_job = _FakeRefreshJob()
    reaction_job = _FakeRefreshJob()
    reaction_kwargs = {}

    async def fake_serve(*args, **kwargs):
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: pipeline)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: market_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        lambda **kwargs: reaction_kwargs.update(kwargs) or reaction_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "RealEstateOfficialStatsRefreshJob",
        lambda **kwargs: official_stats_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "RealEstateComplexRegistryRefreshJob",
        lambda **kwargs: complex_registry_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--enable-realestate-official-stats-refresh",
            "--enable-realestate-complex-registry-refresh",
            "--enable-realestate-daily-crawl-refresh",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-use-backend-aliases",
            "--realestate-use-backend-target-edges",
            "--realestate-use-backend-community-posts",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == [
        "market_facts",
        "official_stats",
        "complex_registry",
        "community_crawl",
        "reaction_snapshots",
    ]
    assert reaction_kwargs["alias_loader"] is not None
    assert reaction_kwargs["target_edge_loader"] is not None
    assert reaction_kwargs["target_edges_jsonl"] is None


def test_serve_command_can_insert_community_complex_seed_before_reaction_snapshots(monkeypatch):
    captured = {}
    pipeline = _FakePipeline()
    spring_client = _FakeSpringClient()
    community_seed_job = _FakeRefreshJob()
    reaction_job = _FakeRefreshJob()
    reaction_kwargs = {}

    async def fake_serve(*args, **kwargs):
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: pipeline)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(
        pipeline_main,
        "RealEstateCommunityComplexSeedRefreshJob",
        lambda **kwargs: community_seed_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        lambda **kwargs: reaction_kwargs.update(kwargs) or reaction_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-daily-crawl-refresh",
            "--enable-realestate-community-complex-seed-refresh",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-use-backend-aliases",
            "--realestate-use-backend-target-edges",
            "--realestate-use-backend-community-posts",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == [
        "community_crawl",
        "community_complex_seed",
        "reaction_snapshots",
    ]
    assert reaction_kwargs["candidate_alias_sources"] == ("community:structured-trade-table",)
    assert reaction_kwargs["candidate_edge_sources"] == ("community:structured-trade-table",)


def test_complex_registry_refresh_implicitly_wires_backend_aliases_and_edges_for_reaction_snapshots(monkeypatch):
    captured = {}
    pipeline = _FakePipeline()
    spring_client = _FakeSpringClient()
    complex_registry_job = _FakeRefreshJob()
    reaction_job = _FakeRefreshJob()
    reaction_kwargs = {}

    async def fake_serve(*args, **kwargs):
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: pipeline)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        lambda **kwargs: reaction_kwargs.update(kwargs) or reaction_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "RealEstateComplexRegistryRefreshJob",
        lambda **kwargs: complex_registry_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-complex-registry-refresh",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-use-backend-community-posts",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == [
        "complex_registry",
        "reaction_snapshots",
    ]
    assert reaction_kwargs["alias_loader"] is not None
    assert reaction_kwargs["aliases_jsonl"] is None
    assert reaction_kwargs["target_edge_loader"] is not None
    assert reaction_kwargs["target_edges_jsonl"] is None


def test_realestate_daily_refresh_command_runs_once_and_prints_summary(monkeypatch, capsys):
    pipeline = _FakePipeline()
    spring_client = _DailyRefreshSpringClient()
    market_job = _FakeRefreshJob()
    official_stats_job = _FakeRefreshJob()
    reaction_job = _FakeRefreshJob()

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: pipeline)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: market_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        lambda **kwargs: reaction_job,
    )
    monkeypatch.setattr(
        pipeline_main,
        "RealEstateOfficialStatsRefreshJob",
        lambda **kwargs: official_stats_job,
    )
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: _FakeRecentIssueClient())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-daily-refresh",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--enable-realestate-official-stats-refresh",
            "--enable-realestate-daily-crawl-refresh",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-aliases-jsonl",
            "aliases.jsonl",
            "--realestate-use-backend-community-posts",
            "--enable-realestate-recent-issues-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--enable-realestate-map-layer-refresh",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "OK"
    assert [step["name"] for step in payload["steps"]] == [
        "market_facts",
        "official_stats",
        "community_crawl",
        "reaction_snapshots",
        "recent_issues",
        "evidence_logs",
        "map_layers",
    ]


def test_realestate_daily_refresh_command_keeps_running_when_serpapi_key_is_missing(monkeypatch, capsys):
    spring_client = _DailyRefreshSpringClient()

    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-daily-refresh",
            "--enable-realestate-recent-issues-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--enable-realestate-map-layer-refresh",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PARTIAL"
    assert [step["name"] for step in payload["steps"]] == [
        "recent_issues",
        "evidence_logs",
        "map_layers",
    ]
    assert payload["steps"][0]["status"] == "CONFIG_MISSING"
    assert payload["steps"][0]["detail"]["missing"] == ["SERPAPI_API_KEY"]
    assert payload["steps"][1]["status"] == "OK"
    assert payload["steps"][2]["status"] == "OK"


def test_realestate_daily_refresh_map_layer_default_periods_include_week_and_year(monkeypatch, capsys):
    spring_client = _DailyRefreshSpringClient()

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-daily-refresh",
            "--enable-realestate-map-layer-refresh",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "OK"
    assert spring_client.map_layer_calls
    assert spring_client.map_layer_calls[0]["periods"] == ["week", "month", "quarter", "halfYear", "year"]


def test_realestate_top10_readiness_command_reads_backend_chain_state(monkeypatch, capsys):
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _ReadinessSpringClient())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-top10-readiness",
            "--realestate-daily-reaction-window-minutes",
            "10080",
            "--realestate-top10-readiness-limit",
            "10",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "READY"
    assert payload["windowMinutes"] == 10080
    assert payload["complexRegistry"]["marketFactBackedComplexCount"] == 1
    assert payload["reactionSnapshots"] == {"complex": 10, "region": 10}
    assert payload["frontTop10"]["complexOnly"] is True


def test_serve_command_can_group_evidence_log_refresh_into_daily_refresh(monkeypatch):
    captured = {}
    spring_client = _FakeSpringClient()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--realestate-daily-reaction-window-minutes",
            "1440",
            "--realestate-evidence-ranking-limit",
            "3",
            "--realestate-evidence-market-fact-limit",
            "7",
            "--realestate-evidence-timeline-limit",
            "6",
            "--realestate-evidence-content-limit",
            "5",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == ["evidence_logs"]
    evidence_step = daily_job.steps[0][1]
    assert evidence_step.client is spring_client
    assert evidence_step.target_type == "region"
    assert evidence_step.window_minutes == 1440
    assert evidence_step.ranking_limit == 3
    assert evidence_step.market_fact_limit == 7
    assert evidence_step.timeline_limit == 6
    assert evidence_step.content_limit == 5


def test_serve_command_can_enable_gms_llm_for_daily_evidence_refresh(monkeypatch):
    captured = {}
    spring_client = _FakeSpringClient()

    class _FakeLlmClient:
        def evaluate(self, log):
            return {
                "tone": "watch",
                "summary": "관심이 빠르게 증가했고 근거 확인이 필요합니다.",
                "subtitle": "시장 사실과 반응 지표를 함께 봅니다.",
            }

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "_gms_openai_evaluation_client", lambda **_kwargs: _FakeLlmClient())
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--evidence-use-gms-llm",
            "--evidence-llm-model",
            "gpt-5-mini",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    evidence_step = daily_job.steps[0][1]
    assert evidence_step.llm_evaluator is not None


def test_serve_command_can_attach_similar_windows_jsonl_to_daily_evidence_refresh(monkeypatch, tmp_path):
    captured = {}
    spring_client = _FakeSpringClient()
    similar_windows_path = tmp_path / "similar-windows.json"
    similar_windows_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "sourceTargetId": "region-daejeon",
                        "sourceWindowStart": "2026-06-14T00:00:00Z",
                        "matchedTargetId": "region-gwangju",
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
                    },
                    {
                        "sourceTargetId": "region-busan",
                        "sourceWindowStart": "2026-06-14T00:00:00Z",
                        "matchedTargetId": "region-jeju",
                        "similarityScore": 0.73,
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--evidence-similar-windows-jsonl",
            str(similar_windows_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    evidence_step = daily_job.steps[0][1]
    similar_windows = evidence_step.similar_windows_provider(
        "region-daejeon",
        {"targetId": "region-daejeon"},
        {"windowStart": "2026-06-14T00:00:00Z"},
    )
    assert [item["matchedTargetId"] for item in similar_windows] == ["region-gwangju"]


def test_serve_command_can_attach_qdrant_similar_provider_to_daily_evidence_refresh(monkeypatch, tmp_path):
    captured = {}
    spring_client = _FakeSpringClient()
    fake_qdrant = _FakeQdrantClient()
    embeddings_path = tmp_path / "embeddings.json"
    embeddings_path.write_text(json.dumps({"items": [_daily_embedding_item()]}, ensure_ascii=False), encoding="utf-8")

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "_qdrant_vector_store_client", lambda: fake_qdrant)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--similar-engine",
            "qdrant",
            "--embeddings-jsonl",
            str(embeddings_path),
            "--similar-top-n",
            "1",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    evidence_step = daily_job.steps[0][1]
    similar_windows = evidence_step.similar_windows_provider(
        "region-daejeon",
        {"targetId": "region-daejeon"},
        {
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
        },
    )
    assert [item["matchedTargetId"] for item in similar_windows] == ["region-gwangju"]
    assert similar_windows[0]["evidenceItem"]["evidenceType"] == "similar_window"
    assert fake_qdrant.search_requests == [
        {
            "vector": [0.1, 0.2, 0.3],
            "top_n": 21,
            "exclude_input_id": "reaction-window:region-daejeon:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z",
        }
    ]


def test_serve_command_qdrant_similar_provider_skips_when_collection_is_not_ready(monkeypatch, tmp_path):
    captured = {}
    spring_client = _FakeSpringClient()
    fake_qdrant = _FakeQdrantClient(ready=False)
    embeddings_path = tmp_path / "embeddings.json"
    embeddings_path.write_text(json.dumps({"items": [_daily_embedding_item()]}, ensure_ascii=False), encoding="utf-8")

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "_qdrant_vector_store_client", lambda: fake_qdrant)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--similar-engine",
            "qdrant",
            "--embeddings-jsonl",
            str(embeddings_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    evidence_step = captured["kwargs"]["realestate_daily_refresh_job"].steps[0][1]
    assert evidence_step.similar_windows_provider(
        "region-daejeon",
        {"targetId": "region-daejeon"},
        {
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
        },
    ) == []
    assert fake_qdrant.search_requests == []


def test_serve_command_can_group_map_layer_refresh_into_daily_refresh(monkeypatch):
    captured = {}
    spring_client = _FakeSpringClient()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-map-layer-refresh",
            "--realestate-map-layer-types",
            "sido",
            "sigungu",
            "--realestate-map-layer-periods",
            "month",
            "halfYear",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == ["map_layers"]
    map_step = daily_job.steps[0][1]
    assert map_step.client is spring_client
    assert map_step.layer_types == ("sido", "sigungu")
    assert map_step.periods == ("month", "halfYear")
