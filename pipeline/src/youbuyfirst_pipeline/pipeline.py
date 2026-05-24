from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from youbuyfirst_pipeline.board_stream import BoardCoverage, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.backoff import CrawlBackoffDecision, CrawlBackoffPolicy, format_utc
from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.crawlers.base import CommunityAdapter, SourceBlockedError
from youbuyfirst_pipeline.llm import LLMProvider
from youbuyfirst_pipeline.matcher import InstrumentMatcher
from youbuyfirst_pipeline.models import Analysis, EnrichedPost, Mention, MentionDecision, RawPost
from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicyDecision,
    SourcePolicyRegistry,
    default_source_policy_registry,
)


class CommunityPipeline:
    def __init__(
        self,
        adapters: list[CommunityAdapter],
        matcher: InstrumentMatcher,
        llm_provider: LLMProvider,
        client: SpringIngestionClient,
        source_policy_registry: SourcePolicyRegistry | None = None,
        runtime_environment: CrawlRuntimeEnvironment = CrawlRuntimeEnvironment.PUBLIC,
        backoff_policy: CrawlBackoffPolicy | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.adapters = adapters
        self.matcher = matcher
        self.llm_provider = llm_provider
        self.client = client
        self.source_policy_registry = source_policy_registry or default_source_policy_registry()
        self.runtime_environment = runtime_environment
        self.backoff_policy = backoff_policy or CrawlBackoffPolicy()
        self.now_provider = now_provider or _utc_now
        self._active_backoffs: dict[str, CrawlBackoffDecision] = {}

    async def run_once(self) -> list[dict]:
        results: list[dict] = []
        for adapter in self.adapters:
            started = self.now_provider()
            run_id = f"{adapter.source.lower()}-{started.strftime('%Y%m%d%H%M')}-{uuid4().hex[:8]}"
            result_context = _target_result_context(adapter)
            backoff_key = _backoff_key(adapter, result_context)
            active_backoff = self._active_backoffs.get(backoff_key)
            if active_backoff and started < active_backoff.retry_after:
                finished = self.now_provider()
                message = _active_backoff_record_message(result_context, active_backoff)
                record_error = self._safe_record_run(
                    adapter.source, run_id, started, finished, "SKIPPED", 0, 0, message
                )
                result = {
                    "source": adapter.source,
                    **result_context,
                    "runId": run_id,
                    "status": "backoff",
                    **_backoff_result_fields(active_backoff),
                    "skipReason": active_backoff.reason,
                }
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
                continue
            if active_backoff:
                self._active_backoffs.pop(backoff_key, None)
            policy_decision = self.source_policy_registry.decide(adapter.source, self.runtime_environment)
            if not policy_decision.allowed:
                finished = self.now_provider()
                skip_message = _skip_record_message(result_context, policy_decision)
                record_error = self._safe_record_run(
                    adapter.source, run_id, started, finished, "SKIPPED", 0, 0, skip_message
                )
                result = {
                    "source": adapter.source,
                    **result_context,
                    "runId": run_id,
                    "status": "skipped",
                    "sourceStatus": policy_decision.policy.status.value,
                    "runtimeEnvironment": self.runtime_environment.value,
                    "skipReason": policy_decision.reason,
                }
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
                continue
            try:
                stream_result = await _fetch_adapter_result(adapter, self.client)
                raw_posts = stream_result.posts
                coverage = _coverage_result_fields(stream_result.coverage)
                enriched = [self._enrich(post) for post in raw_posts]
                finished = self.now_provider()
                self._active_backoffs.pop(backoff_key, None)
                if enriched:
                    result = self.client.ingest(adapter.source, run_id, started, finished, enriched, coverage)
                    if coverage:
                        result["coverage"] = coverage
                    results.append({**result_context, **result})
                else:
                    record_error = self._safe_record_run(
                        adapter.source, run_id, started, finished, "SUCCESS", coverage.get("rowsSeen", 0), 0, None, coverage
                    )
                    empty_result = {
                        "source": adapter.source,
                        **result_context,
                        "runId": run_id,
                        "seenPosts": coverage.get("rowsSeen", 0),
                        "acceptedPosts": 0,
                    }
                    if coverage:
                        empty_result["coverage"] = coverage
                    results.append(empty_result)
                    if record_error:
                        results[-1]["recordError"] = record_error
            except SourceBlockedError as exc:
                finished = self.now_provider()
                backoff = self.backoff_policy.for_exception(exc, started)
                self._active_backoffs[backoff_key] = backoff
                error_message = _failure_record_message(str(exc), backoff)
                record_error = self._safe_record_run(
                    adapter.source, run_id, started, finished, "PARTIAL_FAILURE", 0, 0, error_message
                )
                result = {
                    "source": adapter.source,
                    **result_context,
                    "runId": run_id,
                    "status": "blocked",
                    "error": str(exc),
                    **_backoff_result_fields(backoff),
                }
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
            except Exception as exc:
                finished = self.now_provider()
                backoff = self.backoff_policy.for_exception(exc, started)
                self._active_backoffs[backoff_key] = backoff
                error_message = _failure_record_message(str(exc), backoff)
                record_error = self._safe_record_run(
                    adapter.source, run_id, started, finished, "FAILED", 0, 0, error_message
                )
                result = {
                    "source": adapter.source,
                    **result_context,
                    "runId": run_id,
                    "status": "failed",
                    "error": str(exc),
                    **_backoff_result_fields(backoff),
                }
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
        return results

    def _enrich(self, post: RawPost) -> EnrichedPost:
        text = f"{post.title}\n{post.content}"
        candidates = self.matcher.match(text)
        decisions = self.llm_provider.resolve_mentions(post.title, post.content, candidates)
        accepted_decisions = _accepted_decisions(candidates, decisions)
        mentions = [
            Mention(market=decision.market, symbol=decision.symbol, matched_text=decision.matched_text)
            for decision in accepted_decisions
        ]
        analyses = [
            Analysis(
                market=decision.market,
                symbol=decision.symbol,
                sentiment=decision.reaction_direction,
                confidence=decision.confidence,
                rationale=decision.rationale,
                model=decision.model,
            )
            for decision in accepted_decisions
        ]
        return EnrichedPost(
            source=post.source,
            board_id=post.board_id,
            external_id=post.external_id,
            url=post.url,
            title=post.title,
            content=post.content,
            author=post.author,
            published_at=post.published_at,
            view_count=post.view_count,
            recommend_count=post.recommend_count,
            comment_count=post.comment_count,
            mentions=mentions,
            analyses=analyses,
        )

    def _safe_record_run(
        self,
        source: str,
        run_id: str,
        started: datetime,
        finished: datetime,
        status: str,
        posts_seen: int,
        posts_accepted: int,
        error_message: str | None,
        coverage: dict | None = None,
    ) -> str | None:
        try:
            self.client.record_crawl_run(
                source, run_id, started, finished, status, posts_seen, posts_accepted, error_message, coverage
            )
            return None
        except Exception as exc:
            return str(exc)


def _accepted_decisions(candidates: list[Mention], decisions: list[MentionDecision]) -> list[MentionDecision]:
    candidate_keys = {(candidate.market.upper(), candidate.symbol.upper(), candidate.matched_text) for candidate in candidates}
    accepted: list[MentionDecision] = []
    seen: set[tuple[str, str, str]] = set()
    for decision in decisions:
        key = (decision.market.upper(), decision.symbol.upper(), decision.matched_text)
        if key in seen or key not in candidate_keys or not decision.is_mentioned:
            continue
        seen.add(key)
        accepted.append(decision)
    return accepted


async def _fetch_adapter_result(adapter: CommunityAdapter, client: SpringIngestionClient) -> BoardStreamResult:
    fetch_stream = getattr(adapter, "fetch_stream", None)
    if fetch_stream:
        return await fetch_stream(_watermark_for_adapter(adapter, client))
    return BoardStreamResult(posts=await adapter.fetch_posts(), coverage=None)


def _watermark_for_adapter(adapter: CommunityAdapter, client: SpringIngestionClient) -> BoardWatermark | None:
    target = getattr(adapter, "target", None)
    board_id = getattr(target, "board_id", None)
    if not board_id:
        return None
    get_board_watermark = getattr(client, "get_board_watermark", None)
    if not get_board_watermark:
        return None
    return get_board_watermark(adapter.source, board_id)


def _coverage_result_fields(coverage: BoardCoverage | None) -> dict:
    if coverage is None:
        return {}
    return {
        "pagesFetched": coverage.pages_fetched,
        "rowsSeen": coverage.rows_seen,
        "ignoredPinnedCount": coverage.ignored_pinned_count,
        "duplicateStop": coverage.duplicate_stop,
        "cutoffStop": coverage.cutoff_stop,
        "oldestSeenAt": format_utc(coverage.oldest_seen_at) if coverage.oldest_seen_at else None,
        "newestSeenAt": format_utc(coverage.newest_seen_at) if coverage.newest_seen_at else None,
        "lastCursor": coverage.last_cursor,
        "coverageStatus": coverage.coverage_status,
    }


def _target_result_context(adapter: CommunityAdapter) -> dict:
    target = getattr(adapter, "target", None)
    if target is None:
        return {}
    context = {
        "targetId": target.target_id,
        "targetKind": target.kind.value,
        "targetLabel": target.label,
    }
    if target.market:
        context["targetMarket"] = target.market
    if target.symbol:
        context["targetSymbol"] = target.symbol
    if target.url:
        context["targetUrl"] = target.url
    return context


def _skip_record_message(result_context: dict, policy_decision: SourcePolicyDecision) -> str:
    parts: list[str] = []
    target_id = result_context.get("targetId")
    if target_id:
        parts.append(f"targetId={target_id}")
    parts.extend(
        [
            f"sourceStatus={policy_decision.policy.status.value}",
            f"runtimeEnvironment={policy_decision.runtime_environment.value}",
            f"reason={policy_decision.reason}",
        ]
    )
    return "; ".join(parts)


def _backoff_key(adapter: CommunityAdapter, result_context: dict) -> str:
    return result_context.get("targetId") or adapter.source


def _backoff_result_fields(backoff: CrawlBackoffDecision) -> dict:
    return {
        "backoffCategory": backoff.category,
        "backoffSeconds": backoff.seconds,
        "backoffUntil": format_utc(backoff.retry_after),
        "backoffReason": backoff.reason,
    }


def _failure_record_message(error: str, backoff: CrawlBackoffDecision) -> str:
    return "; ".join(
        [
            error,
            f"backoffCategory={backoff.category}",
            f"backoffSeconds={backoff.seconds}",
            f"backoffUntil={format_utc(backoff.retry_after)}",
            f"backoffReason={backoff.reason}",
        ]
    )


def _active_backoff_record_message(result_context: dict, backoff: CrawlBackoffDecision) -> str:
    parts: list[str] = []
    target_id = result_context.get("targetId")
    if target_id:
        parts.append(f"targetId={target_id}")
    parts.extend(
        [
            f"backoffCategory={backoff.category}",
            f"backoffSeconds={backoff.seconds}",
            f"backoffUntil={format_utc(backoff.retry_after)}",
            f"reason={backoff.reason}",
        ]
    )
    return "; ".join(parts)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
