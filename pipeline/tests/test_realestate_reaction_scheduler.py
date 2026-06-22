from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from youbuyfirst_pipeline.realestate_complex_registry import build_real_estate_complex_registry_from_market_facts
from youbuyfirst_pipeline.realestate_matcher import RealEstateAliasRule
from youbuyfirst_pipeline.realestate_public_data import RealEstateMarketFact
from youbuyfirst_pipeline.realestate_reaction_scheduler import RealEstateReactionSnapshotRefreshJob
from youbuyfirst_pipeline.realestate_target_graph import RealEstateTargetEdgeRule
from youbuyfirst_pipeline.scheduler import configure_scheduler


class _Client:
    def __init__(self, fail_push: bool = False) -> None:
        self.fail_push = fail_push
        self.pushed_batches = []
        self.export_requests = []
        self.export_posts = []

    def publish_real_estate_reaction_snapshots(self, snapshots) -> None:
        if self.fail_push:
            raise RuntimeError("backend unavailable")
        self.pushed_batches.append([snapshot.to_request_dict() for snapshot in snapshots])

    def list_community_posts_for_reaction_refresh(self, *, source, published_from, published_to, limit):
        self.export_requests.append(
            {
                "source": source,
                "published_from": published_from,
                "published_to": published_to,
                "limit": limit,
            }
        )
        return self.export_posts


class _Pipeline:
    async def run_once(self) -> list[str]:
        return []


def test_real_estate_reaction_snapshot_refresh_job_builds_previous_completed_window_and_pushes(tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","alias":"대전","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        "\n".join(
            [
                '{"source":"PPOMPPU:house","externalId":"prev","publishedAt":"2026-06-10T23:40:00Z","title":"대전 전세 불안","contentSnippet":"전세 부담"}',
                '{"source":"PPOMPPU:house","externalId":"now","publishedAt":"2026-06-11T00:20:00Z","title":"대전 GTX 호재","contentSnippet":"교통 개선 기대"}',
                '{"source":"PPOMPPU:house","externalId":"future","publishedAt":"2026-06-11T01:10:00Z","title":"대전 전세","contentSnippet":"아직 다음 window"}',
            ]
        ),
        encoding="utf-8",
    )
    client = _Client()
    now = datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc)
    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=aliases_path,
        community_posts_jsonl=posts_path,
        window_minutes=60,
        clock=lambda: now,
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 1
    assert client.pushed_batches[0][0]["targetId"] == "region-daejeon"
    assert client.pushed_batches[0][0]["windowStart"] == "2026-06-11T00:00:00Z"
    assert client.pushed_batches[0][0]["windowEnd"] == "2026-06-11T01:00:00Z"
    assert client.pushed_batches[0][0]["asOf"] == "2026-06-11T01:02:00Z"
    assert client.pushed_batches[0][0]["mentionCount"] == 1
    assert client.pushed_batches[0][0]["previousMentionCount"] == 1


def test_real_estate_reaction_snapshot_refresh_job_can_read_posts_from_backend_export(tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-gyeonggi-paju","alias":"파주시","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    client = _Client()
    client.export_posts = [
        {
            "source": "PPOMPPU",
            "externalId": "paju-previous",
            "publishedAt": "2026-06-13T23:40:00Z",
            "title": "파주시 전세 우려",
            "contentSnippet": "전세와 공급 부담 언급",
        },
        {
            "source": "PPOMPPU",
            "externalId": "paju-current",
            "publishedAt": "2026-06-14T00:20:00Z",
            "title": "파주시 GTX 기대",
            "contentSnippet": "교통 기대와 신축 언급",
        },
    ]
    now = datetime(2026, 6, 14, 1, 2, tzinfo=timezone.utc)
    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=aliases_path,
        community_posts_jsonl=None,
        backend_posts_source="PPOMPPU",
        backend_posts_limit=100,
        window_minutes=60,
        clock=lambda: now,
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 1
    assert client.export_requests == [
        {
            "source": "PPOMPPU",
            "published_from": "2026-06-13T23:00:00Z",
            "published_to": "2026-06-14T01:00:00Z",
            "limit": 100,
        }
    ]
    assert client.pushed_batches[0][0]["targetId"] == "region-gyeonggi-paju"
    assert client.pushed_batches[0][0]["mentionCount"] == 1
    assert client.pushed_batches[0][0]["previousMentionCount"] == 1


def test_real_estate_reaction_snapshot_refresh_job_can_include_current_window_from_backend_export():
    client = _Client()
    client.export_posts = [
        {
            "source": "PPOMPPU",
            "externalId": "paju-previous",
            "publishedAt": "2026-06-14T00:20:00Z",
            "title": "paju jeonse concern",
            "contentSnippet": "paju supply concern",
        },
        {
            "source": "PPOMPPU",
            "externalId": "paju-current",
            "publishedAt": "2026-06-14T01:20:00Z",
            "title": "paju GTX expectation",
            "contentSnippet": "paju transport topic is repeated",
        },
    ]

    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=None,
        alias_loader=lambda: [
            RealEstateAliasRule(
                target_type="region",
                target_id="region-gyeonggi-paju",
                alias="paju",
                review_state="approved",
                confidence=0.95,
            )
        ],
        community_posts_jsonl=None,
        backend_posts_source="PPOMPPU",
        backend_posts_limit=100,
        window_minutes=60,
        use_current_window=True,
        clock=lambda: datetime(2026, 6, 14, 1, 45, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 1
    assert client.export_requests == [
        {
            "source": "PPOMPPU",
            "published_from": "2026-06-14T00:00:00Z",
            "published_to": "2026-06-14T02:00:00Z",
            "limit": 100,
        }
    ]
    assert client.pushed_batches[0][0]["windowStart"] == "2026-06-14T01:00:00Z"
    assert client.pushed_batches[0][0]["windowEnd"] == "2026-06-14T02:00:00Z"
    assert client.pushed_batches[0][0]["mentionCount"] == 1
    assert client.pushed_batches[0][0]["previousMentionCount"] == 1
    assert client.pushed_batches[0][0]["stale"] is False


def test_real_estate_reaction_snapshot_refresh_job_can_load_aliases_from_backend_loader():
    client = _Client()
    client.export_posts = [
        {
            "source": "PPOMPPU",
            "externalId": "paju-current",
            "publishedAt": "2026-06-14T00:20:00Z",
            "title": "paju GTX expectation",
            "contentSnippet": "paju transport topic is repeated",
        }
    ]
    alias_loads = []

    def load_aliases():
        alias_loads.append("loaded")
        return [
            RealEstateAliasRule(
                target_type="region",
                target_id="region-gyeonggi-paju",
                alias="paju",
                review_state="approved",
                confidence=0.95,
            )
        ]

    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=None,
        alias_loader=load_aliases,
        community_posts_jsonl=None,
        backend_posts_source="PPOMPPU",
        backend_posts_limit=100,
        window_minutes=60,
        clock=lambda: datetime(2026, 6, 14, 1, 2, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert alias_loads == ["loaded"]
    assert result.observation_count == 1
    assert result.snapshot_count == 1
    assert client.pushed_batches[0][0]["targetId"] == "region-gyeonggi-paju"


def test_real_estate_reaction_snapshot_refresh_job_loads_backend_edges_and_rolls_complex_up_to_region():
    client = _Client()
    client.export_posts = [
        {
            "source": "PPOMPPU",
            "externalId": "complex-current",
            "publishedAt": "2026-06-14T00:20:00Z",
            "title": "Sajik Palace reconstruction expectation",
            "contentSnippet": "Sajik Palace transport topic is repeated",
        }
    ]

    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=None,
        alias_loader=lambda: [
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-molit-11110-sajik-palace",
                alias="Sajik Palace",
                review_state="approved",
                confidence=0.95,
            )
        ],
        target_edge_loader=lambda: [
            RealEstateTargetEdgeRule(
                from_target_type="region",
                from_target_id="region-seoul-jongno",
                to_target_type="complex",
                to_target_id="complex-molit-11110-sajik-palace",
                edge_type="contains",
                review_state="approved",
                confidence=0.9,
            )
        ],
        community_posts_jsonl=None,
        backend_posts_source="PPOMPPU",
        backend_posts_limit=100,
        window_minutes=60,
        clock=lambda: datetime(2026, 6, 14, 1, 2, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 2
    assert result.snapshot_counts_by_type == {"complex": 1, "region": 1}
    assert [snapshot["targetId"] for snapshot in client.pushed_batches[0]] == [
        "complex-molit-11110-sajik-palace",
        "region-seoul-jongno",
    ]
    assert client.pushed_batches[0][0]["targetType"] == "complex"
    assert client.pushed_batches[0][1]["targetType"] == "region"


def test_real_estate_reaction_snapshot_refresh_job_can_include_structured_trade_candidate_complexes():
    client = _Client()
    client.export_posts = [
        {
            "source": "PPOMPPU",
            "externalId": "trade-table-current",
            "publishedAt": "2026-06-14T00:20:00Z",
            "title": "weekly trade table",
            "contentSnippet": "WoosungIPark SeoulGangseo Hwagokdong 59.99 4 134500 2026/6/9",
        }
    ]

    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=None,
        alias_loader=lambda: [
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-community-observed-woosung",
                alias="WoosungIPark",
                alias_type="community_observed_trade_table",
                review_state="candidate",
                confidence=0.66,
                source="community:structured-trade-table",
            )
        ],
        target_edge_loader=lambda: [
            RealEstateTargetEdgeRule(
                from_target_type="region",
                from_target_id="region-seoul-gangseo",
                to_target_type="complex",
                to_target_id="complex-community-observed-woosung",
                edge_type="contains",
                review_state="candidate",
                confidence=0.58,
                source="community:structured-trade-table",
            )
        ],
        community_posts_jsonl=None,
        backend_posts_source="PPOMPPU",
        backend_posts_limit=100,
        window_minutes=60,
        candidate_alias_sources=("community:structured-trade-table",),
        candidate_edge_sources=("community:structured-trade-table",),
        clock=lambda: datetime(2026, 6, 14, 1, 2, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 2
    assert result.snapshot_counts_by_type == {"complex": 1, "region": 1}
    assert [snapshot["targetId"] for snapshot in client.pushed_batches[0]] == [
        "complex-community-observed-woosung",
        "region-seoul-gangseo",
    ]
    assert client.pushed_batches[0][0]["coverageStatus"] == "low_sample"
    assert client.pushed_batches[0][1]["coverageStatus"] == "low_sample"


def test_complex_registry_short_alias_feeds_crawl_matching_snapshot_and_region_rollup():
    registry = build_real_estate_complex_registry_from_market_facts(
        [
            RealEstateMarketFact(
                fact_type="apt_trade",
                provider="molit",
                provider_dataset="molit_apt_trade",
                provider_object_id="molit_apt_trade:11440:202606:trade-1",
                legal_dong_code="11440",
                observed_at=datetime(2026, 6, 3, tzinfo=timezone.utc).date(),
                as_of=datetime(2026, 6, 1, tzinfo=timezone.utc).date(),
                ingested_at=datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc),
                value_json={
                    "apartmentName": "마포 래미안 푸르지오",
                    "legalDongName": "아현동",
                    "jibun": "777",
                },
            )
        ],
        region_targets_by_lawd_code={"11440": "region-seoul-mapo"},
    )
    client = _Client()
    client.export_posts = [
        {
            "source": "PPOMPPU:house",
            "externalId": "complex-short-alias-current",
            "publishedAt": "2026-06-14T00:20:00Z",
            "title": "마래푸 전세 불안 얘기 다시 늘었네요",
            "contentSnippet": "마포 래미안 푸르지오라고 안 쓰고 다들 마래푸로 부르는 분위기",
        }
    ]

    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=None,
        alias_loader=lambda: [
            RealEstateAliasRule(
                target_type=alias["targetType"],
                target_id=alias["targetId"],
                alias=alias["alias"],
                alias_type=alias["aliasType"],
                review_state=alias["reviewState"],
                confidence=alias["confidence"],
            )
            for alias in registry.aliases
        ],
        target_edge_loader=lambda: [
            RealEstateTargetEdgeRule(
                from_target_type=edge["fromTargetType"],
                from_target_id=edge["fromTargetId"],
                to_target_type=edge["toTargetType"],
                to_target_id=edge["toTargetId"],
                edge_type=edge["edgeType"],
                review_state=edge["reviewState"],
                confidence=edge["confidence"],
            )
            for edge in registry.edges
        ],
        community_posts_jsonl=None,
        backend_posts_source="PPOMPPU:house",
        backend_posts_limit=100,
        window_minutes=60,
        clock=lambda: datetime(2026, 6, 14, 1, 2, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 2
    assert [snapshot["targetId"] for snapshot in client.pushed_batches[0]] == [
        registry.targets[0]["targetId"],
        "region-seoul-mapo",
    ]
    assert client.pushed_batches[0][0]["targetType"] == "complex"
    assert client.pushed_batches[0][1]["targetType"] == "region"
    assert client.pushed_batches[0][0]["issues"][0]["issueKey"] == "jeonse"


def test_real_estate_reaction_snapshot_refresh_job_rolls_child_region_up_to_parent(tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-seoul-jongno","alias":"종로","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    target_edges_path = tmp_path / "target_edges.jsonl"
    target_edges_path.write_text(
        '{"fromTargetType":"region","fromTargetId":"region-seoul","toTargetType":"region","toTargetId":"region-seoul-jongno","edgeType":"contains","reviewState":"approved","confidence":0.9}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"now","publishedAt":"2026-06-11T00:20:00Z","title":"종로 재건축 기대","contentSnippet":"호재 기대"}',
        encoding="utf-8",
    )
    client = _Client()
    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=aliases_path,
        target_edges_jsonl=target_edges_path,
        community_posts_jsonl=posts_path,
        window_minutes=60,
        clock=lambda: datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 2
    assert [snapshot["targetId"] for snapshot in client.pushed_batches[0]] == [
        "region-seoul",
        "region-seoul-jongno",
    ]


def test_real_estate_reaction_snapshot_refresh_job_reports_input_error_without_push(tmp_path):
    client = _Client()
    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=tmp_path / "missing-aliases.jsonl",
        community_posts_jsonl=tmp_path / "missing-posts.jsonl",
        window_minutes=60,
    )

    result = job.run_once()

    assert result.status == "INPUT_ERROR"
    assert result.observation_count == 0
    assert result.snapshot_count == 0
    assert client.pushed_batches == []


def test_real_estate_reaction_snapshot_refresh_job_reports_client_error_when_push_fails(tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","alias":"대전","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"now","publishedAt":"2026-06-11T00:20:00Z","title":"대전 GTX 호재","contentSnippet":"교통 개선 기대"}',
        encoding="utf-8",
    )
    job = RealEstateReactionSnapshotRefreshJob(
        client=_Client(fail_push=True),
        aliases_jsonl=aliases_path,
        community_posts_jsonl=posts_path,
        window_minutes=60,
        clock=lambda: datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "CLIENT_ERROR"
    assert result.observation_count == 1
    assert result.snapshot_count == 1


def test_configure_scheduler_registers_real_estate_reaction_snapshot_refresh_job():
    scheduler = AsyncIOScheduler(timezone="UTC")
    reaction_job = RealEstateReactionSnapshotRefreshJob(
        client=_Client(),
        aliases_jsonl="aliases.jsonl",
        community_posts_jsonl="posts.jsonl",
        window_minutes=60,
    )

    configure_scheduler(
        scheduler,
        pipeline=_Pipeline(),
        crawl_interval_minutes=30,
        realestate_reaction_snapshot_refresh_job=reaction_job,
        realestate_reaction_snapshot_interval_minutes=15,
    )

    jobs = {job.id: job for job in scheduler.get_jobs()}
    assert jobs["community-crawl"].trigger.interval.total_seconds() == 30 * 60
    assert jobs["realestate-reaction-snapshots-refresh"].trigger.interval.total_seconds() == 15 * 60
