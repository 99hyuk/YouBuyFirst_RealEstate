from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import uuid4

from youbuyfirst_pipeline.board_stream import BoardCoverage, BoardStreamResult, BoardWatermark
from youbuyfirst_pipeline.backoff import CrawlBackoffDecision, CrawlBackoffPolicy, format_utc
from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.crawl_targets import CrawlTargetKind
from youbuyfirst_pipeline.crawlers.base import CommunityAdapter, SourceBlockedError
from youbuyfirst_pipeline.llm import LLMProvider
from youbuyfirst_pipeline.matcher import InstrumentMatcher
from youbuyfirst_pipeline.models import (
    Analysis,
    CommentCollectionTarget,
    DiffusionEvent,
    EnrichedPost,
    Mention,
    MentionDecision,
    RawPost,
)
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
        default_board_lookback_hours: float | None = 24,
        diffusion_max_age_hours: float | None = 24,
        comment_trigger_min_comments: int = 30,
        comment_trigger_min_recommends: int = 30,
        comment_trigger_min_views: int = 5000,
        high_engagement_max_comments: int = 30,
        diffusion_max_comments: int = 50,
    ) -> None:
        self.adapters = adapters
        self.matcher = matcher
        self.llm_provider = llm_provider
        self.client = client
        self.source_policy_registry = source_policy_registry or default_source_policy_registry()
        self.runtime_environment = runtime_environment
        self.backoff_policy = backoff_policy or CrawlBackoffPolicy()
        self.now_provider = now_provider or _utc_now
        self.default_board_lookback_hours = default_board_lookback_hours
        self.diffusion_max_age_hours = diffusion_max_age_hours
        self.comment_trigger_min_comments = comment_trigger_min_comments
        self.comment_trigger_min_recommends = comment_trigger_min_recommends
        self.comment_trigger_min_views = comment_trigger_min_views
        self.high_engagement_max_comments = high_engagement_max_comments
        self.diffusion_max_comments = diffusion_max_comments
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
                stream_result = await _fetch_adapter_result(
                    adapter,
                    self.client,
                    default_cutoff_at=self._default_cutoff_at(started),
                )
                raw_posts = stream_result.posts
                diffusion_positioned_posts = _positioned_diffusion_posts_for_adapter(
                    adapter,
                    raw_posts,
                    started,
                    self.diffusion_max_age_hours,
                )
                if diffusion_positioned_posts is not None:
                    raw_posts = [post for _list_position, post in diffusion_positioned_posts]
                    diffusion_events = stream_result.diffusion_events or _diffusion_events_for_adapter(
                        adapter,
                        diffusion_positioned_posts,
                        started,
                    )
                else:
                    diffusion_events = stream_result.diffusion_events
                coverage = _coverage_result_fields(stream_result.coverage)
                enriched = [self._enrich(post) for post in raw_posts]
                comment_collection_targets = _comment_collection_targets_for_run(
                    adapter,
                    raw_posts,
                    diffusion_events,
                    started,
                    min_comments=self.comment_trigger_min_comments,
                    min_recommends=self.comment_trigger_min_recommends,
                    min_views=self.comment_trigger_min_views,
                    high_engagement_max_comments=self.high_engagement_max_comments,
                    diffusion_max_comments=self.diffusion_max_comments,
                )
                finished = self.now_provider()
                self._active_backoffs.pop(backoff_key, None)
                if enriched or diffusion_events or comment_collection_targets:
                    result = self.client.ingest(
                        adapter.source,
                        run_id,
                        started,
                        finished,
                        enriched,
                        coverage,
                        diffusion_events=diffusion_events,
                        comment_collection_targets=comment_collection_targets,
                    )
                    if coverage:
                        result["coverage"] = coverage
                    if diffusion_events:
                        result["diffusionEventCount"] = len(diffusion_events)
                    if comment_collection_targets:
                        result["commentCollectionTargetCount"] = len(comment_collection_targets)
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
        find_alias_candidates = getattr(self.matcher, "alias_candidates", None)
        alias_candidates = [
            replace(
                candidate,
                context_snippet=_trim_to(text, 500),
                sample_url=post.url,
                observed_at=post.published_at,
            )
            for candidate in (find_alias_candidates(text) if find_alias_candidates else [])
        ]
        decisions = self.llm_provider.resolve_mentions(post.title, post.content, candidates)
        candidates_by_key = {_mention_key(candidate): candidate for candidate in candidates}
        accepted_decisions = _accepted_decisions(candidates, decisions)
        mentions = [
            Mention(
                market=decision.market,
                symbol=decision.symbol,
                matched_text=decision.matched_text,
                instrument_id=_candidate_instrument_id(candidates_by_key, decision),
            )
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
                instrument_id=_candidate_instrument_id(candidates_by_key, decision),
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
            alias_candidates=alias_candidates,
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

    def _default_cutoff_at(self, started: datetime) -> datetime | None:
        if self.default_board_lookback_hours is None or self.default_board_lookback_hours <= 0:
            return None
        return started - timedelta(hours=self.default_board_lookback_hours)


def _accepted_decisions(candidates: list[Mention], decisions: list[MentionDecision]) -> list[MentionDecision]:
    candidate_keys = {_mention_key(candidate) for candidate in candidates}
    accepted: list[MentionDecision] = []
    seen: set[tuple[str, str, str]] = set()
    for decision in decisions:
        key = _decision_key(decision)
        if key in seen or key not in candidate_keys or not decision.is_mentioned:
            continue
        seen.add(key)
        accepted.append(decision)
    return accepted


def _candidate_instrument_id(candidates_by_key: dict[tuple[str, str, str], Mention], decision: MentionDecision) -> int | None:
    candidate = candidates_by_key.get(_decision_key(decision))
    return candidate.instrument_id if candidate else None


def _mention_key(mention: Mention) -> tuple[str, str, str]:
    return (mention.market.upper(), mention.symbol.upper(), mention.matched_text)


def _decision_key(decision: MentionDecision) -> tuple[str, str, str]:
    return (decision.market.upper(), decision.symbol.upper(), decision.matched_text)


def _trim_to(value: str, max_length: int) -> str:
    return value if len(value) <= max_length else value[:max_length]


async def _fetch_adapter_result(
    adapter: CommunityAdapter,
    client: SpringIngestionClient,
    default_cutoff_at: datetime | None = None,
) -> BoardStreamResult:
    fetch_stream = getattr(adapter, "fetch_stream", None)
    if fetch_stream:
        return await fetch_stream(_watermark_for_adapter(adapter, client, default_cutoff_at))
    return BoardStreamResult(posts=await adapter.fetch_posts(), coverage=None)


def _watermark_for_adapter(
    adapter: CommunityAdapter,
    client: SpringIngestionClient,
    default_cutoff_at: datetime | None = None,
) -> BoardWatermark | None:
    target = getattr(adapter, "target", None)
    if target is not None and target.kind == CrawlTargetKind.GENERAL_BOARD_DIFFUSION:
        return None
    board_id = getattr(target, "board_id", None)
    if not board_id:
        return None
    get_board_watermark = getattr(client, "get_board_watermark", None)
    watermark = get_board_watermark(adapter.source, board_id) if get_board_watermark else None
    cutoff_at = _later_datetime(watermark.cutoff_at if watermark else None, default_cutoff_at)
    if watermark is None:
        return BoardWatermark(cutoff_at=cutoff_at) if cutoff_at else None
    return BoardWatermark(last_seen_external_id=watermark.last_seen_external_id, cutoff_at=cutoff_at)


def _later_datetime(left: datetime | None, right: datetime | None) -> datetime | None:
    if left is None:
        return right
    if right is None:
        return left
    return max(left, right)


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
        "targetPriority": target.priority,
        "targetIntervalSeconds": target.crawl_interval_seconds,
    }
    if target.market:
        context["targetMarket"] = target.market
    if target.symbol:
        context["targetSymbol"] = target.symbol
    if target.url:
        context["targetUrl"] = target.url
    if getattr(target, "diffusion_type", None):
        context["diffusionType"] = target.diffusion_type
    return context


def _positioned_diffusion_posts_for_adapter(
    adapter: CommunityAdapter,
    posts: list[RawPost],
    observed_at: datetime,
    max_age_hours: float | None,
) -> list[tuple[int, RawPost]] | None:
    target = getattr(adapter, "target", None)
    if target is None or target.kind != CrawlTargetKind.GENERAL_BOARD_DIFFUSION:
        return None
    cutoff_at = _diffusion_cutoff_at(observed_at, max_age_hours)
    positioned_posts = list(enumerate(posts, start=1))
    if cutoff_at is None:
        return positioned_posts
    return [
        (list_position, post)
        for list_position, post in positioned_posts
        if _as_utc(post.published_at) >= cutoff_at
    ]


def _diffusion_events_for_adapter(adapter: CommunityAdapter, positioned_posts: list[tuple[int, RawPost]], observed_at: datetime) -> list[DiffusionEvent]:
    target = getattr(adapter, "target", None)
    if target is None or target.kind != CrawlTargetKind.GENERAL_BOARD_DIFFUSION:
        return []
    diffusion_type = getattr(target, "diffusion_type", None)
    if not diffusion_type:
        return []
    events: list[DiffusionEvent] = []
    for list_position, post in positioned_posts:
        events.append(
            DiffusionEvent(
                external_id=post.external_id,
                board_id=post.board_id or target.board_id,
                diffusion_type=diffusion_type,
                list_position=list_position,
                observed_at=observed_at,
                view_count=post.view_count,
                recommend_count=post.recommend_count,
                comment_count=post.comment_count,
                diffusion_only=True,
            )
        )
    return events


def _comment_collection_targets_for_run(
    adapter: CommunityAdapter,
    posts: list[RawPost],
    diffusion_events: list[DiffusionEvent],
    triggered_at: datetime,
    min_comments: int,
    min_recommends: int,
    min_views: int,
    high_engagement_max_comments: int,
    diffusion_max_comments: int,
) -> list[CommentCollectionTarget]:
    target_map: dict[str, CommentCollectionTarget] = {}
    for event in diffusion_events:
        if not _has_comments(event.comment_count):
            continue
        _add_comment_collection_target(
            target_map,
            CommentCollectionTarget(
                external_id=event.external_id,
                board_id=event.board_id,
                trigger_reason="diffusion",
                triggered_at=event.observed_at,
                max_comments=diffusion_max_comments,
                priority=50,
                view_count=event.view_count,
                recommend_count=event.recommend_count,
                comment_count=event.comment_count,
            ),
        )

    if _is_diffusion_adapter(adapter):
        return list(target_map.values())

    for post in posts:
        if not _is_high_engagement_post(post, min_comments, min_recommends, min_views):
            continue
        _add_comment_collection_target(
            target_map,
            CommentCollectionTarget(
                external_id=post.external_id,
                board_id=post.board_id,
                trigger_reason="high-engagement",
                triggered_at=triggered_at,
                max_comments=high_engagement_max_comments,
                priority=80,
                view_count=post.view_count,
                recommend_count=post.recommend_count,
                comment_count=post.comment_count,
            ),
        )
    return list(target_map.values())


def _add_comment_collection_target(target_map: dict[str, CommentCollectionTarget], target: CommentCollectionTarget) -> None:
    current = target_map.get(target.external_id)
    if current is None or target.priority < current.priority:
        target_map[target.external_id] = target


def _is_high_engagement_post(post: RawPost, min_comments: int, min_recommends: int, min_views: int) -> bool:
    if not _has_comments(post.comment_count):
        return False
    return (
        _at_least(post.comment_count, min_comments)
        or _at_least(post.recommend_count, min_recommends)
        or _at_least(post.view_count, min_views)
    )


def _has_comments(value: int | None) -> bool:
    return value is not None and value > 0


def _at_least(value: int | None, threshold: int) -> bool:
    return threshold > 0 and value is not None and value >= threshold


def _is_diffusion_adapter(adapter: CommunityAdapter) -> bool:
    target = getattr(adapter, "target", None)
    return target is not None and target.kind == CrawlTargetKind.GENERAL_BOARD_DIFFUSION


def _diffusion_cutoff_at(observed_at: datetime, max_age_hours: float | None) -> datetime | None:
    if max_age_hours is None or max_age_hours <= 0:
        return None
    return _as_utc(observed_at) - timedelta(hours=max_age_hours)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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
