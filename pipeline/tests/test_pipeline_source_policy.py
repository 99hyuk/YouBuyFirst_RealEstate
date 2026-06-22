from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from youbuyfirst_pipeline.board_stream import BoardCoverage, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.models import DiffusionEvent, RawPost
from youbuyfirst_pipeline.pipeline import CommunityPipeline
from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicy,
    SourcePolicyRegistry,
    SourceStatus,
)


class FakeAdapter:
    def __init__(self, source: str, posts: list[RawPost] | None = None) -> None:
        self.source = source
        self.posts = posts or []
        self.called = False
        self.target = CrawlTarget.community_board(source, board_id="house", url="https://example.com/house")

    async def fetch_posts(self) -> list[RawPost]:
        self.called = True
        return self.posts


class FakeStreamAdapter(FakeAdapter):
    def __init__(self, source: str, result: BoardStreamResult) -> None:
        super().__init__(source)
        self.result = result
        self.received_watermark: BoardWatermark | None = None

    async def fetch_stream(self, watermark: BoardWatermark | None = None) -> BoardStreamResult:
        self.called = True
        self.received_watermark = watermark
        return self.result


class FakeClient:
    def __init__(self) -> None:
        self.recorded_runs: list[dict] = []
        self.ingested_batches: list[dict] = []
        self.watermarks: dict[tuple[str, str], BoardWatermark] = {}

    def ingest(
        self,
        source,
        run_id,
        batch_started_at,
        batch_finished_at,
        posts,
        coverage=None,
        diffusion_events=None,
        comment_collection_targets=None,
    ):
        post_list = list(posts)
        event_list = list(diffusion_events or [])
        comment_target_list = list(comment_collection_targets or [])
        payload = {"source": source, "runId": run_id, "acceptedPosts": len(post_list), "posts": post_list}
        if coverage is not None:
            payload["coverage"] = coverage
        if event_list:
            payload["diffusionEvents"] = event_list
        if comment_target_list:
            payload["commentCollectionTargets"] = comment_target_list
        self.ingested_batches.append(payload)
        return {"source": source, "runId": run_id, "acceptedPosts": len(post_list)}

    def record_crawl_run(
        self,
        source,
        run_id,
        batch_started_at,
        batch_finished_at,
        status,
        posts_seen,
        posts_accepted,
        error_message=None,
        coverage=None,
        target_id=None,
        target_kind=None,
    ):
        recorded = {
            "source": source,
            "runId": run_id,
            "status": status,
            "postsSeen": posts_seen,
            "postsAccepted": posts_accepted,
            "errorMessage": error_message,
            "targetId": target_id,
            "targetKind": target_kind,
        }
        if coverage is not None:
            recorded["coverage"] = coverage
        self.recorded_runs.append(recorded)

    def get_board_watermark(self, source, board_id):
        return self.watermarks.get((source, board_id))


def _pipeline(
    adapter: FakeAdapter,
    registry: SourcePolicyRegistry,
    runtime: CrawlRuntimeEnvironment,
    client: FakeClient | None = None,
    now: datetime | None = None,
) -> CommunityPipeline:
    return CommunityPipeline(
        adapters=[adapter],
        client=client or FakeClient(),
        source_policy_registry=registry,
        runtime_environment=runtime,
        now_provider=(lambda: now) if now else None,
    )


def _enabled_registry(source: str) -> SourcePolicyRegistry:
    return SourcePolicyRegistry({source: SourcePolicy(source, SourceStatus.ENABLED, "review complete")})


def _coverage(rows_seen: int = 0) -> BoardCoverage:
    observed = datetime(2026, 5, 24, 2, 0, tzinfo=timezone.utc) if rows_seen else None
    return BoardCoverage(
        pages_fetched=1,
        rows_seen=rows_seen,
        ignored_pinned_count=0,
        duplicate_stop=False,
        cutoff_stop=False,
        oldest_seen_at=observed,
        newest_seen_at=observed,
        last_cursor="1",
        coverage_status="complete",
        filtered_count=2,
        excluded_title_count=1,
        keyword_miss_count=1,
        duplicate_link_count=3,
    )


def test_public_runtime_skips_local_research_source_without_fetching():
    adapter = FakeAdapter("CAFE")
    registry = SourcePolicyRegistry(
        {
            "CAFE": SourcePolicy("CAFE", SourceStatus.LOCAL_RESEARCH_ONLY, "local only"),
        }
    )
    client = FakeClient()
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.PUBLIC, client)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is False
    assert results[0]["source"] == "CAFE"
    assert results[0]["status"] == "skipped"
    assert results[0]["targetId"] == "CAFE:house"
    assert results[0]["targetKind"] == "community-board"
    assert results[0]["sourceStatus"] == "local-research-only"
    assert results[0]["runtimeEnvironment"] == "public"
    assert "not allowed in public runtime" in results[0]["skipReason"]
    assert client.recorded_runs[0]["errorMessage"] == (
        "targetId=CAFE:house; sourceStatus=local-research-only; "
        "runtimeEnvironment=public; reason=source policy local-research-only is not allowed in public runtime"
    )
    assert client.recorded_runs[0]["targetId"] == "CAFE:house"
    assert client.recorded_runs[0]["targetKind"] == "community-board"


def test_disabled_source_skips_and_records_backend_run():
    adapter = FakeAdapter("UNKNOWN")
    client = FakeClient()
    pipeline = _pipeline(adapter, SourcePolicyRegistry({}), CrawlRuntimeEnvironment.LOCAL, client)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is False
    assert results[0]["status"] == "skipped"
    assert client.recorded_runs[0]["status"] == "SKIPPED"
    assert client.recorded_runs[0]["errorMessage"] == (
        "targetId=UNKNOWN:house; sourceStatus=disabled; "
        "runtimeEnvironment=local; reason=source is not registered; default disabled"
    )


def test_local_runtime_allows_local_research_source_to_fetch():
    adapter = FakeAdapter("CAFE")
    registry = SourcePolicyRegistry(
        {
            "CAFE": SourcePolicy("CAFE", SourceStatus.LOCAL_RESEARCH_ONLY, "local only"),
        }
    )
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.LOCAL)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is True
    assert results[0]["source"] == "CAFE"
    assert results[0]["targetId"] == "CAFE:house"
    assert results[0]["seenPosts"] == 0
    assert results[0]["acceptedPosts"] == 0


def test_enabled_source_ingests_enriched_posts_without_legacy_analysis():
    post = RawPost(
        source="SAFE",
        board_id="house",
        external_id="SAFE-house-1",
        url="https://example.com/1",
        title="regional discussion",
        content="",
        author="anon",
        published_at=datetime.now(timezone.utc),
    )
    adapter = FakeAdapter("SAFE", posts=[post])
    pipeline = _pipeline(adapter, _enabled_registry("SAFE"), CrawlRuntimeEnvironment.PUBLIC)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is True
    assert results[0]["source"] == "SAFE"
    assert results[0]["targetId"] == "SAFE:house"
    assert results[0]["acceptedPosts"] == 1


def test_board_stream_adapter_records_coverage_when_no_new_posts():
    coverage = BoardCoverage(
        pages_fetched=2,
        rows_seen=43,
        ignored_pinned_count=1,
        duplicate_stop=True,
        cutoff_stop=False,
        oldest_seen_at=datetime(2026, 5, 24, 1, 30, tzinfo=timezone.utc),
        newest_seen_at=datetime(2026, 5, 24, 2, 0, tzinfo=timezone.utc),
        last_cursor="2",
        coverage_status="complete",
    )
    adapter = FakeStreamAdapter("SAFE", BoardStreamResult(posts=[], coverage=coverage))
    client = FakeClient()
    pipeline = _pipeline(adapter, _enabled_registry("SAFE"), CrawlRuntimeEnvironment.PUBLIC, client)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is True
    assert results[0]["coverage"]["pagesFetched"] == 2
    assert results[0]["coverage"]["rowsSeen"] == 43
    assert results[0]["coverage"]["filteredOutCount"] == 0
    assert client.recorded_runs[0]["coverage"]["coverageStatus"] == "complete"


def test_board_stream_adapter_receives_db_watermark_for_board_target():
    adapter = FakeStreamAdapter("SAFE", BoardStreamResult(posts=[], coverage=_coverage(1)))
    client = FakeClient()
    client.watermarks[("SAFE", "house")] = BoardWatermark(last_seen_external_id="SAFE-house-100")
    pipeline = _pipeline(
        adapter,
        _enabled_registry("SAFE"),
        CrawlRuntimeEnvironment.PUBLIC,
        client,
        now=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
    )

    results = asyncio.run(pipeline.run_once())

    assert results[0]["coverage"]["rowsSeen"] == 1
    assert results[0]["coverage"]["filteredOutCount"] == 2
    assert results[0]["coverage"]["excludedTitleCount"] == 1
    assert results[0]["coverage"]["keywordMissCount"] == 1
    assert results[0]["coverage"]["duplicateLinkCount"] == 3
    assert adapter.received_watermark == BoardWatermark(
        last_seen_external_id="SAFE-house-100",
        cutoff_at=datetime(2026, 5, 23, 12, 0, tzinfo=timezone.utc),
    )


def test_board_stream_adapter_uses_default_24_hour_cutoff_without_db_watermark():
    adapter = FakeStreamAdapter("SAFE", BoardStreamResult(posts=[], coverage=_coverage()))
    pipeline = _pipeline(
        adapter,
        _enabled_registry("SAFE"),
        CrawlRuntimeEnvironment.PUBLIC,
        FakeClient(),
        now=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
    )

    asyncio.run(pipeline.run_once())

    assert adapter.received_watermark == BoardWatermark(cutoff_at=datetime(2026, 5, 23, 12, 0, tzinfo=timezone.utc))


def test_board_stream_adapter_passes_coverage_to_ingest_for_new_posts():
    post = RawPost(
        source="SAFE",
        board_id="house",
        external_id="SAFE-house-1",
        url="https://example.com/1",
        title="regional discussion",
        content="",
        author="anon",
        published_at=datetime(2026, 5, 24, 2, 0, tzinfo=timezone.utc),
        view_count=10,
        recommend_count=2,
        comment_count=1,
    )
    adapter = FakeStreamAdapter("SAFE", BoardStreamResult(posts=[post], coverage=_coverage(1)))
    client = FakeClient()
    pipeline = _pipeline(adapter, _enabled_registry("SAFE"), CrawlRuntimeEnvironment.PUBLIC, client)

    results = asyncio.run(pipeline.run_once())

    assert results[0]["coverage"]["rowsSeen"] == 1
    assert results[0]["coverage"]["filteredOutCount"] == 2
    assert client.ingested_batches[0]["coverage"]["rowsSeen"] == 1
    assert client.ingested_batches[0]["posts"][0].board_id == "house"
    assert client.ingested_batches[0]["posts"][0].view_count == 10


def test_board_stream_adapter_passes_diffusion_events_to_ingest_even_without_new_posts():
    event = DiffusionEvent(
        external_id="SAFE-house-1",
        board_id="house",
        diffusion_type="popular",
        list_position=1,
        observed_at=datetime(2026, 5, 24, 3, 0, tzinfo=timezone.utc),
        view_count=1000,
        recommend_count=25,
        comment_count=40,
        diffusion_only=True,
    )
    adapter = FakeStreamAdapter("SAFE", BoardStreamResult(posts=[], coverage=_coverage(1), diffusion_events=[event]))
    client = FakeClient()
    pipeline = _pipeline(adapter, _enabled_registry("SAFE"), CrawlRuntimeEnvironment.PUBLIC, client)

    results = asyncio.run(pipeline.run_once())

    assert results[0]["diffusionEventCount"] == 1
    assert client.ingested_batches[0]["posts"] == []
    assert client.ingested_batches[0]["diffusionEvents"] == [event]
    assert client.recorded_runs == []


def test_diffusion_target_generates_list_position_diffusion_events_from_list_posts():
    post = RawPost(
        source="SAFE",
        board_id="house",
        external_id="SAFE-house-100",
        url="https://example.com/100",
        title="popular regional thread",
        content="",
        author="anon",
        published_at=datetime(2026, 5, 24, 3, 1, tzinfo=timezone.utc),
        view_count=1500,
        recommend_count=30,
        comment_count=44,
    )
    adapter = FakeStreamAdapter("SAFE", BoardStreamResult(posts=[post], coverage=_coverage(1)))
    adapter.target = CrawlTarget.community_diffusion_board(
        "SAFE",
        board_id="house",
        diffusion_type="popular",
        url="https://example.com/popular",
    )
    client = FakeClient()
    pipeline = _pipeline(
        adapter,
        _enabled_registry("SAFE"),
        CrawlRuntimeEnvironment.PUBLIC,
        client,
        now=datetime(2026, 5, 24, 3, 5, tzinfo=timezone.utc),
    )

    results = asyncio.run(pipeline.run_once())

    assert results[0]["targetKind"] == "general-board-diffusion"
    assert results[0]["diffusionType"] == "popular"
    event = client.ingested_batches[0]["diffusionEvents"][0]
    assert event.external_id == "SAFE-house-100"
    assert event.diffusion_type == "popular"
    assert event.list_position == 1
    assert event.observed_at == datetime(2026, 5, 24, 3, 5, tzinfo=timezone.utc)
    assert event.diffusion_only is True
    comment_target = client.ingested_batches[0]["commentCollectionTargets"][0]
    assert comment_target.external_id == "SAFE-house-100"
    assert comment_target.trigger_reason == "diffusion"
    assert comment_target.max_comments == 50
    assert comment_target.priority == 50


def test_latest_board_generates_limited_comment_targets_only_for_high_engagement_posts():
    quiet_post = RawPost(
        source="SAFE",
        board_id="house",
        external_id="SAFE-house-quiet",
        url="https://example.com/quiet",
        title="quiet thread",
        content="",
        author="anon",
        published_at=datetime(2026, 5, 24, 3, 1, tzinfo=timezone.utc),
        view_count=120,
        recommend_count=1,
        comment_count=2,
    )
    high_comment_post = RawPost(
        source="SAFE",
        board_id="house",
        external_id="SAFE-house-hot-comments",
        url="https://example.com/hot-comments",
        title="discussion is moving fast",
        content="",
        author="anon",
        published_at=datetime(2026, 5, 24, 3, 2, tzinfo=timezone.utc),
        view_count=700,
        recommend_count=4,
        comment_count=35,
    )
    adapter = FakeStreamAdapter(
        "SAFE",
        BoardStreamResult(posts=[quiet_post, high_comment_post], coverage=_coverage(2)),
    )
    client = FakeClient()
    pipeline = _pipeline(
        adapter,
        _enabled_registry("SAFE"),
        CrawlRuntimeEnvironment.PUBLIC,
        client,
        now=datetime(2026, 5, 24, 3, 5, tzinfo=timezone.utc),
    )

    results = asyncio.run(pipeline.run_once())

    assert results[0]["commentCollectionTargetCount"] == 1
    assert [target.external_id for target in client.ingested_batches[0]["commentCollectionTargets"]] == [
        "SAFE-house-hot-comments"
    ]
    target = client.ingested_batches[0]["commentCollectionTargets"][0]
    assert target.trigger_reason == "high-engagement"
    assert target.max_comments == 30
    assert target.priority == 80
    assert target.comment_count == 35


def test_diffusion_target_ignores_latest_watermark_but_filters_posts_older_than_24_hours():
    old_post = RawPost(
        source="SAFE",
        board_id="house",
        external_id="SAFE-house-popular-old",
        url="https://example.com/popular-old",
        title="old thread resurfaced in popular list",
        content="",
        author="anon",
        published_at=datetime(2026, 5, 20, 3, 1, tzinfo=timezone.utc),
        view_count=15000,
        recommend_count=300,
        comment_count=144,
    )
    recent_post = RawPost(
        source="SAFE",
        board_id="house",
        external_id="SAFE-house-popular-recent",
        url="https://example.com/popular-recent",
        title="recent thread in popular list",
        content="",
        author="anon",
        published_at=datetime(2026, 5, 24, 3, 1, tzinfo=timezone.utc),
        view_count=5000,
        recommend_count=130,
        comment_count=44,
    )
    adapter = FakeStreamAdapter("SAFE", BoardStreamResult(posts=[old_post, recent_post], coverage=_coverage(2)))
    adapter.target = CrawlTarget.community_diffusion_board(
        "SAFE",
        board_id="house",
        diffusion_type="popular",
        url="https://example.com/popular",
    )
    client = FakeClient()
    client.watermarks[("SAFE", "house")] = BoardWatermark(
        last_seen_external_id="SAFE-house-latest-999",
        cutoff_at=datetime(2026, 5, 24, 11, 30, tzinfo=timezone.utc),
    )
    pipeline = _pipeline(
        adapter,
        _enabled_registry("SAFE"),
        CrawlRuntimeEnvironment.PUBLIC,
        client,
        now=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
    )

    results = asyncio.run(pipeline.run_once())

    assert adapter.received_watermark is None
    assert results[0]["diffusionEventCount"] == 1
    assert [post.external_id for post in client.ingested_batches[0]["posts"]] == ["SAFE-house-popular-recent"]
    event = client.ingested_batches[0]["diffusionEvents"][0]
    assert event.external_id == "SAFE-house-popular-recent"
    assert event.list_position == 2
    assert event.observed_at == datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc)
