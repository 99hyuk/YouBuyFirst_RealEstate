from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx

from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import SourceBlockedError
from youbuyfirst_pipeline.pipeline import CommunityPipeline
from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicy,
    SourcePolicyRegistry,
    SourceStatus,
)


NOW = datetime(2026, 5, 15, 0, 0, tzinfo=timezone.utc)


class FakeAdapter:
    def __init__(self, source: str, errors: list[Exception] | None = None) -> None:
        self.source = source
        self.errors = errors or []
        self.calls = 0
        self.target = CrawlTarget.stock_board(source, market="KR", symbol="005930")

    async def fetch_posts(self) -> list:
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return []


class FakeMatcher:
    def match(self, text: str) -> list:
        return []


class FakeLLMProvider:
    def resolve_mentions(self, title: str, content: str, mentions: list) -> list:
        return []


class FakeClient:
    def __init__(self) -> None:
        self.recorded_runs: list[dict] = []

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
    ):
        self.recorded_runs.append(
            {
                "source": source,
                "runId": run_id,
                "status": status,
                "postsSeen": posts_seen,
                "postsAccepted": posts_accepted,
                "errorMessage": error_message,
            }
        )


def _enabled_registry(source: str) -> SourcePolicyRegistry:
    return SourcePolicyRegistry({source: SourcePolicy(source, SourceStatus.ENABLED, "safe test source")})


def _pipeline(adapter: FakeAdapter, client: FakeClient) -> CommunityPipeline:
    return CommunityPipeline(
        adapters=[adapter],
        matcher=FakeMatcher(),
        llm_provider=FakeLLMProvider(),
        client=client,
        source_policy_registry=_enabled_registry(adapter.source),
        runtime_environment=CrawlRuntimeEnvironment.PUBLIC,
        now_provider=lambda: NOW,
    )


def test_blocked_run_sets_backoff_and_next_run_skips_fetch():
    adapter = FakeAdapter("SAFE", errors=[SourceBlockedError("https://example.com returned 429")])
    client = FakeClient()
    pipeline = _pipeline(adapter, client)

    first = asyncio.run(pipeline.run_once())
    second = asyncio.run(pipeline.run_once())

    assert adapter.calls == 1
    assert first[0]["status"] == "blocked"
    assert first[0]["backoffCategory"] == "blocked"
    assert first[0]["backoffSeconds"] == 21600
    assert first[0]["backoffUntil"] == "2026-05-15T06:00:00Z"
    assert client.recorded_runs[0]["status"] == "PARTIAL_FAILURE"
    assert "backoffCategory=blocked" in client.recorded_runs[0]["errorMessage"]

    assert second[0]["status"] == "backoff"
    assert second[0]["backoffCategory"] == "blocked"
    assert second[0]["backoffUntil"] == "2026-05-15T06:00:00Z"
    assert client.recorded_runs[1]["status"] == "SKIPPED"
    assert "backoffUntil=2026-05-15T06:00:00Z" in client.recorded_runs[1]["errorMessage"]


def test_timeout_failure_records_transient_backoff_metadata():
    adapter = FakeAdapter("SAFE", errors=[httpx.TimeoutException("read timed out")])
    client = FakeClient()
    pipeline = _pipeline(adapter, client)

    result = asyncio.run(pipeline.run_once())

    assert result[0]["status"] == "failed"
    assert result[0]["backoffCategory"] == "transient-error"
    assert result[0]["backoffSeconds"] == 900
    assert result[0]["backoffUntil"] == "2026-05-15T00:15:00Z"
    assert client.recorded_runs[0]["status"] == "FAILED"
    assert "backoffCategory=transient-error" in client.recorded_runs[0]["errorMessage"]
