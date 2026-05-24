from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from youbuyfirst_pipeline.board_stream import BoardCoverage, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.models import RawPost
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
        self.target = CrawlTarget.stock_board(source, market="KR", symbol="005930")

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


class FakeMatcher:
    def match(self, text: str) -> list:
        return []


class FakeLLMProvider:
    def resolve_mentions(self, title: str, content: str, mentions: list) -> list:
        return []


class FakeClient:
    def __init__(self) -> None:
        self.recorded_runs: list[dict] = []
        self.ingested_batches: list[dict] = []
        self.watermarks: dict[tuple[str, str], BoardWatermark] = {}

    def ingest(self, source, run_id, batch_started_at, batch_finished_at, posts, coverage=None):
        post_list = list(posts)
        payload = {"source": source, "runId": run_id, "acceptedPosts": len(post_list), "posts": post_list}
        if coverage is not None:
            payload["coverage"] = coverage
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
    ):
        recorded = {
            "source": source,
            "runId": run_id,
            "status": status,
            "postsSeen": posts_seen,
            "postsAccepted": posts_accepted,
            "errorMessage": error_message,
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
) -> CommunityPipeline:
    return CommunityPipeline(
        adapters=[adapter],
        matcher=FakeMatcher(),
        llm_provider=FakeLLMProvider(),
        client=client or FakeClient(),
        source_policy_registry=registry,
        runtime_environment=runtime,
    )


def test_public_runtime_skips_local_research_source_without_fetching():
    adapter = FakeAdapter("NAVER")
    registry = SourcePolicyRegistry(
        {
            "NAVER": SourcePolicy("NAVER", SourceStatus.LOCAL_RESEARCH_ONLY, "local only"),
        }
    )
    client = FakeClient()
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.PUBLIC, client)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is False
    assert results[0]["source"] == "NAVER"
    assert results[0]["status"] == "skipped"
    assert results[0]["targetId"] == "NAVER:KR:005930"
    assert results[0]["targetKind"] == "stock-board"
    assert results[0]["sourceStatus"] == "local-research-only"
    assert results[0]["runtimeEnvironment"] == "public"
    assert "not allowed in public runtime" in results[0]["skipReason"]
    assert client.recorded_runs == [
        {
            "source": "NAVER",
            "runId": results[0]["runId"],
            "status": "SKIPPED",
            "postsSeen": 0,
            "postsAccepted": 0,
            "errorMessage": (
                "targetId=NAVER:KR:005930; sourceStatus=local-research-only; "
                "runtimeEnvironment=public; reason=source policy local-research-only is not allowed in public runtime"
            ),
        }
    ]


def test_disabled_source_skips_and_records_backend_run():
    adapter = FakeAdapter("UNKNOWN")
    registry = SourcePolicyRegistry({})
    client = FakeClient()
    pipeline = CommunityPipeline(
        adapters=[adapter],
        matcher=FakeMatcher(),
        llm_provider=FakeLLMProvider(),
        client=client,
        source_policy_registry=registry,
        runtime_environment=CrawlRuntimeEnvironment.LOCAL,
    )

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is False
    assert results[0]["status"] == "skipped"
    assert client.recorded_runs == [
        {
            "source": "UNKNOWN",
            "runId": results[0]["runId"],
            "status": "SKIPPED",
            "postsSeen": 0,
            "postsAccepted": 0,
            "errorMessage": (
                "targetId=UNKNOWN:KR:005930; sourceStatus=disabled; "
                "runtimeEnvironment=local; reason=source is not registered; default disabled"
            ),
        }
    ]


def test_local_runtime_allows_local_research_source_to_fetch():
    adapter = FakeAdapter("NAVER")
    registry = SourcePolicyRegistry(
        {
            "NAVER": SourcePolicy("NAVER", SourceStatus.LOCAL_RESEARCH_ONLY, "local only"),
        }
    )
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.LOCAL)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is True
    assert results[0]["source"] == "NAVER"
    assert results[0]["targetId"] == "NAVER:KR:005930"
    assert results[0]["seenPosts"] == 0
    assert results[0]["acceptedPosts"] == 0


def test_enabled_source_still_ingests_enriched_posts():
    post = RawPost(
        source="SAFE",
        external_id="SAFE-1",
        url="https://example.com/1",
        title="테스트",
        content="",
        author="anon",
        published_at=datetime.now(timezone.utc),
    )
    adapter = FakeAdapter("SAFE", posts=[post])
    registry = SourcePolicyRegistry(
        {
            "SAFE": SourcePolicy("SAFE", SourceStatus.ENABLED, "review complete"),
        }
    )
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.PUBLIC)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is True
    assert results[0]["source"] == "SAFE"
    assert results[0]["targetId"] == "SAFE:KR:005930"
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
    registry = SourcePolicyRegistry(
        {
            "SAFE": SourcePolicy("SAFE", SourceStatus.ENABLED, "review complete"),
        }
    )
    client = FakeClient()
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.PUBLIC, client)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is True
    assert results[0]["coverage"]["pagesFetched"] == 2
    assert results[0]["coverage"]["rowsSeen"] == 43
    assert client.recorded_runs[0]["coverage"]["coverageStatus"] == "complete"


def test_board_stream_adapter_receives_db_watermark_for_board_target():
    adapter = FakeStreamAdapter(
        "SAFE",
        BoardStreamResult(
            posts=[],
            coverage=BoardCoverage(
                pages_fetched=1,
                rows_seen=1,
                ignored_pinned_count=0,
                duplicate_stop=True,
                cutoff_stop=False,
                oldest_seen_at=datetime(2026, 5, 24, 1, 30, tzinfo=timezone.utc),
                newest_seen_at=datetime(2026, 5, 24, 1, 30, tzinfo=timezone.utc),
                last_cursor="1",
                coverage_status="complete",
            ),
        ),
    )
    adapter.target = CrawlTarget.community_board("SAFE", board_id="stock", url="https://example.com/stock")
    registry = SourcePolicyRegistry(
        {
            "SAFE": SourcePolicy("SAFE", SourceStatus.ENABLED, "review complete"),
        }
    )
    client = FakeClient()
    client.watermarks[("SAFE", "stock")] = BoardWatermark(last_seen_external_id="SAFE-stock-100")
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.PUBLIC, client)

    results = asyncio.run(pipeline.run_once())

    assert results[0]["coverage"]["duplicateStop"] is True
    assert adapter.received_watermark == BoardWatermark(last_seen_external_id="SAFE-stock-100")


def test_board_stream_adapter_passes_coverage_to_ingest_for_new_posts():
    post = RawPost(
        source="SAFE",
        board_id="stock",
        external_id="SAFE-1",
        url="https://example.com/1",
        title="테스트",
        content="",
        author="anon",
        published_at=datetime(2026, 5, 24, 2, 0, tzinfo=timezone.utc),
        view_count=10,
        recommend_count=2,
        comment_count=1,
    )
    coverage = BoardCoverage(
        pages_fetched=1,
        rows_seen=1,
        ignored_pinned_count=0,
        duplicate_stop=False,
        cutoff_stop=False,
        oldest_seen_at=post.published_at,
        newest_seen_at=post.published_at,
        last_cursor="1",
        coverage_status="complete",
    )
    adapter = FakeStreamAdapter("SAFE", BoardStreamResult(posts=[post], coverage=coverage))
    registry = SourcePolicyRegistry(
        {
            "SAFE": SourcePolicy("SAFE", SourceStatus.ENABLED, "review complete"),
        }
    )
    client = FakeClient()
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.PUBLIC, client)

    results = asyncio.run(pipeline.run_once())

    assert results[0]["coverage"]["rowsSeen"] == 1
    assert client.ingested_batches[0]["coverage"]["rowsSeen"] == 1
    assert client.ingested_batches[0]["posts"][0].board_id == "stock"
    assert client.ingested_batches[0]["posts"][0].view_count == 10
