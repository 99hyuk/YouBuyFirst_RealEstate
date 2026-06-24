from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.realestate_community_complex_seed import (
    COMMUNITY_COMPLEX_SEEDS,
    CommunityComplexSeed,
    build_observed_community_complex_seed_registry,
)
from youbuyfirst_pipeline.realestate_complex_registry import (
    build_real_estate_complex_registry_from_market_facts,
)
from youbuyfirst_pipeline.realestate_recent_issues import (
    RealEstateRecentIssueSearchTarget,
    RealEstateRecentIssueSearchClient,
    build_recent_issue_content_items,
    load_recent_issue_search_targets,
)
from youbuyfirst_pipeline.realestate_daily_briefing import (
    DEFAULT_DAILY_BRIEFING_MODEL,
    DEFAULT_DAILY_BRIEFING_PROMPT_VERSION,
    apply_daily_briefing_llm_generation,
    build_daily_briefing_input_pack,
    build_rule_based_daily_briefing,
    load_daily_briefing_curated_pack,
)
from youbuyfirst_pipeline.realestate_evidence import build_real_estate_evidence_logs
from youbuyfirst_pipeline.realestate_public_data import (
    REB_RONE_MONTHLY_APT_SALE_PRICE_INDEX_DATASET_ID,
    build_reb_rone_main_snapshot_client_from_env,
    build_reb_rone_monthly_price_index_client_from_env,
    collect_reb_rone_main_snapshot_facts,
    collect_reb_rone_monthly_price_index_facts,
)

logger = logging.getLogger(__name__)
RECENT_ISSUE_CONTENT_KEYWORDS = ("블로그", "영상", "리포트")
REALESTATE_FRONT_TOP10_REQUIRED_ITEMS = 10


class RealEstateRefreshStep(Protocol):
    def run_once(self) -> Any:
        ...


@dataclass(frozen=True)
class RealEstateDailyRefreshStepResult:
    name: str
    status: str
    detail: dict[str, Any]


@dataclass(frozen=True)
class RealEstateDailyRefreshResult:
    status: str
    step_count: int
    ok_count: int
    failed_count: int
    steps: list[RealEstateDailyRefreshStepResult]

    def to_dict(self) -> dict[str, Any]:
        steps = [asdict(step) for step in self.steps]
        return {
            "status": self.status,
            "stepCount": self.step_count,
            "okCount": self.ok_count,
            "failedCount": self.failed_count,
            "top10Readiness": _top10_readiness(steps),
            "steps": steps,
        }


@dataclass(frozen=True)
class RealEstateRecentIssuesRefreshResult:
    status: str
    target_count: int
    item_count: int


@dataclass(frozen=True)
class RealEstateConfigMissingRefreshResult:
    status: str
    missing: list[str]
    message: str


@dataclass(frozen=True)
class RealEstateEvidenceLogRefreshResult:
    status: str
    target_count: int
    log_count: int
    market_fact_count: int
    timeline_event_count: int
    content_item_count: int
    similar_window_count: int = 0
    llm_error_count: int = 0


@dataclass(frozen=True)
class RealEstateDailyBriefingRefreshResult:
    status: str
    briefing_count: int
    candidate_count: int
    source_item_count: int
    llm_error_count: int = 0


@dataclass(frozen=True)
class RealEstateMapLayerRefreshResult:
    status: str
    layer_count: int
    snapshot_count: int
    skipped_target_count: int


@dataclass(frozen=True)
class RealEstateCommunityCrawlRefreshResult:
    status: str
    source_count: int
    seen_post_count: int
    accepted_post_count: int
    skipped_count: int = 0
    blocked_count: int = 0
    failed_count: int = 0


@dataclass(frozen=True)
class RealEstateOfficialStatsRefreshResult:
    status: str
    provider: str
    provider_dataset: str
    fact_count: int


@dataclass(frozen=True)
class RealEstateComplexRegistryRefreshResult:
    status: str
    market_fact_count: int
    target_count: int
    complex_count: int
    alias_count: int
    edge_count: int


@dataclass(frozen=True)
class RealEstateCommunityComplexSeedRefreshResult:
    status: str
    post_count: int
    observed_target_count: int
    target_count: int
    complex_count: int
    alias_count: int
    edge_count: int


class RealEstateCommunityComplexSeedRefreshJob:
    def __init__(
        self,
        *,
        client: SpringIngestionClient,
        window_minutes: int = 10080,
        posts_source: str | None = None,
        posts_limit: int = 1000,
        seeds: Sequence[CommunityComplexSeed] = COMMUNITY_COMPLEX_SEEDS,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.window_minutes = window_minutes
        self.posts_source = posts_source
        self.posts_limit = posts_limit
        self.seeds = tuple(seeds)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateCommunityComplexSeedRefreshResult:
        try:
            now = self.clock()
            window_start = now - timedelta(minutes=self.window_minutes)
            posts = self.client.list_community_posts_for_reaction_refresh(
                source=self.posts_source,
                published_from=_iso_z(window_start),
                published_to=_iso_z(now),
                limit=self.posts_limit,
            )
            existing_aliases = self.client.list_real_estate_aliases(
                review_state="approved",
                ambiguous=False,
            )
        except Exception:
            logger.exception("real-estate community complex seed refresh failed during backend read")
            return RealEstateCommunityComplexSeedRefreshResult(
                status="CLIENT_ERROR",
                post_count=0,
                observed_target_count=0,
                target_count=0,
                complex_count=0,
                alias_count=0,
                edge_count=0,
            )

        registry = build_observed_community_complex_seed_registry(
            posts,
            seeds=self.seeds,
            existing_aliases=existing_aliases,
        )
        status = "OK" if registry.observed_target_ids else "EMPTY"
        try:
            self.client.publish_real_estate_targets(registry.targets)
            self.client.publish_real_estate_complexes(registry.complexes)
            self.client.publish_real_estate_aliases(registry.aliases)
            self.client.publish_real_estate_target_edges(registry.edges)
        except Exception:
            logger.exception("real-estate community complex seed refresh failed during backend push")
            status = "CLIENT_ERROR"

        return RealEstateCommunityComplexSeedRefreshResult(
            status=status,
            post_count=len(posts),
            observed_target_count=len(registry.observed_target_ids),
            target_count=len(registry.targets),
            complex_count=len(registry.complexes),
            alias_count=len(registry.aliases),
            edge_count=len(registry.edges),
        )


class RealEstateComplexRegistryRefreshJob:
    MARKET_FACT_TYPES = ("apt_trade", "apt_rent")

    def __init__(
        self,
        *,
        client: SpringIngestionClient,
        market_fact_limit: int = 1000,
    ) -> None:
        self.client = client
        self.market_fact_limit = market_fact_limit

    def run_once(self) -> RealEstateComplexRegistryRefreshResult:
        try:
            facts = _complex_registry_market_facts(
                self.client,
                fact_types=self.MARKET_FACT_TYPES,
                limit=self.market_fact_limit,
            )
            region_targets_by_lawd_code = _region_targets_by_lawd_code(self.client)
        except Exception:
            logger.exception("real-estate complex registry refresh failed during backend read")
            return RealEstateComplexRegistryRefreshResult(
                status="CLIENT_ERROR",
                market_fact_count=0,
                target_count=0,
                complex_count=0,
                alias_count=0,
                edge_count=0,
            )

        registry = build_real_estate_complex_registry_from_market_facts(
            facts,
            region_targets_by_lawd_code=region_targets_by_lawd_code,
        )
        if not registry.targets:
            return RealEstateComplexRegistryRefreshResult(
                status="EMPTY",
                market_fact_count=len(facts),
                target_count=0,
                complex_count=0,
                alias_count=0,
                edge_count=0,
            )

        try:
            self.client.publish_real_estate_targets(registry.targets)
            self.client.publish_real_estate_complexes(registry.complexes)
            self.client.publish_real_estate_aliases(registry.aliases)
            self.client.publish_real_estate_target_edges(registry.edges)
        except Exception:
            logger.exception("real-estate complex registry refresh failed during backend push")
            return RealEstateComplexRegistryRefreshResult(
                status="CLIENT_ERROR",
                market_fact_count=len(facts),
                target_count=len(registry.targets),
                complex_count=len(registry.complexes),
                alias_count=len(registry.aliases),
                edge_count=len(registry.edges),
            )

        return RealEstateComplexRegistryRefreshResult(
            status="OK",
            market_fact_count=len(facts),
            target_count=len(registry.targets),
            complex_count=len(registry.complexes),
            alias_count=len(registry.aliases),
            edge_count=len(registry.edges),
        )


class RealEstateOfficialStatsRefreshJob:
    def __init__(
        self,
        *,
        client: SpringIngestionClient,
        collector: Callable[[], Sequence[object]] | None = None,
    ) -> None:
        self.client = client
        self.collector = collector or _collect_reb_rone_official_stats_facts

    def run_once(self) -> RealEstateOfficialStatsRefreshResult:
        try:
            facts = list(self.collector())
        except Exception:
            logger.exception("real-estate official stats refresh failed during provider fetch")
            return RealEstateOfficialStatsRefreshResult(
                status="PROVIDER_ERROR",
                provider="reb",
                provider_dataset=REB_RONE_MONTHLY_APT_SALE_PRICE_INDEX_DATASET_ID,
                fact_count=0,
            )

        try:
            if facts:
                self.client.publish_real_estate_market_facts(facts)
        except Exception:
            logger.exception("real-estate official stats refresh failed during backend push")
            return RealEstateOfficialStatsRefreshResult(
                status="CLIENT_ERROR",
                provider="reb",
                provider_dataset=REB_RONE_MONTHLY_APT_SALE_PRICE_INDEX_DATASET_ID,
                fact_count=len(facts),
            )

        return RealEstateOfficialStatsRefreshResult(
            status="OK" if facts else "EMPTY",
            provider="reb",
            provider_dataset=REB_RONE_MONTHLY_APT_SALE_PRICE_INDEX_DATASET_ID,
            fact_count=len(facts),
        )


class RealEstateCommunityCrawlRefreshJob:
    def __init__(self, *, pipeline) -> None:
        self.pipeline = pipeline

    def run_once(self) -> RealEstateCommunityCrawlRefreshResult:
        results = _run_async(self.pipeline.run_once())
        rows = [row for row in results if isinstance(row, dict)]
        seen_post_count = sum(_int_field(row, "seenPosts") for row in rows)
        accepted_post_count = sum(_int_field(row, "acceptedPosts") for row in rows)
        skipped_count = sum(1 for row in rows if _normalized_status(row) == "SKIPPED")
        blocked_count = sum(1 for row in rows if _normalized_status(row) == "BLOCKED")
        failed_count = sum(1 for row in rows if _normalized_status(row) in {"FAILED", "ERROR"})
        status = "EMPTY"
        if rows:
            status = "PARTIAL" if blocked_count or failed_count else "OK"
        return RealEstateCommunityCrawlRefreshResult(
            status=status,
            source_count=len(rows),
            seen_post_count=seen_post_count,
            accepted_post_count=accepted_post_count,
            skipped_count=skipped_count,
            blocked_count=blocked_count,
            failed_count=failed_count,
        )


class RealEstateConfigMissingRefreshJob:
    def __init__(self, *, missing: Sequence[str], message: str) -> None:
        self.missing = list(missing)
        self.message = message

    def run_once(self) -> RealEstateConfigMissingRefreshResult:
        return RealEstateConfigMissingRefreshResult(
            status="CONFIG_MISSING",
            missing=self.missing,
            message=self.message,
        )


class RealEstateMapLayerRefreshJob:
    def __init__(
        self,
        *,
        client: SpringIngestionClient,
        layer_types: Sequence[str] = ("sido", "sigungu"),
        periods: Sequence[str] = ("month", "quarter", "halfYear"),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.layer_types = tuple(layer_types)
        self.periods = tuple(periods)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateMapLayerRefreshResult:
        if not self.layer_types or not self.periods:
            return RealEstateMapLayerRefreshResult(
                status="EMPTY",
                layer_count=0,
                snapshot_count=0,
                skipped_target_count=0,
            )

        as_of = _iso_utc(self.clock())
        snapshot_count = 0
        skipped_target_count = 0
        for layer_type in self.layer_types:
            result = self.client.refresh_real_estate_map_layer_snapshots(
                layer_type=layer_type,
                periods=self.periods,
                as_of=as_of,
            )
            snapshot_count += int(result.get("acceptedSnapshots") or 0)
            skipped_target_count += int(result.get("skippedTargets") or 0)

        return RealEstateMapLayerRefreshResult(
            status="OK",
            layer_count=len(self.layer_types),
            snapshot_count=snapshot_count,
            skipped_target_count=skipped_target_count,
        )


class RealEstateEvidenceLogRefreshJob:
    def __init__(
        self,
        *,
        client: SpringIngestionClient,
        target_type: str = "region",
        window_minutes: int = 60,
        ranking_limit: int = 20,
        market_fact_limit: int = 20,
        timeline_limit: int = 20,
        content_limit: int = 20,
        llm_evaluator: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        similar_windows_provider: Callable[[str, dict[str, Any], dict[str, Any]], Sequence[dict[str, Any]]] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.target_type = target_type
        self.window_minutes = window_minutes
        self.ranking_limit = ranking_limit
        self.market_fact_limit = market_fact_limit
        self.timeline_limit = timeline_limit
        self.content_limit = content_limit
        self.llm_evaluator = llm_evaluator
        self.similar_windows_provider = similar_windows_provider
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateEvidenceLogRefreshResult:
        ranking = self.client.get_real_estate_reaction_ranking(
            target_type=self.target_type,
            window_minutes=self.window_minutes,
            limit=self.ranking_limit,
        )
        ranking = _ranking_with_window_defaults(
            ranking,
            window_minutes=self.window_minutes,
            now=self.clock(),
        )
        rows = [row for row in ranking.get("items", []) if isinstance(row, dict)]
        rows = _fill_ranking_rows_from_map_layer(
            self.client,
            ranking=ranking,
            rows=rows,
            target_type=self.target_type,
            limit=self.ranking_limit,
        )
        if not rows:
            return RealEstateEvidenceLogRefreshResult(
                status="EMPTY",
                target_count=0,
                log_count=0,
                market_fact_count=0,
                timeline_event_count=0,
                content_item_count=0,
                similar_window_count=0,
            )

        logs: list[dict[str, Any]] = []
        market_fact_count = 0
        timeline_event_count = 0
        content_item_count = 0
        similar_window_count = 0
        llm_error_count = 0
        for row in rows:
            target_id = str(row.get("targetId") or row.get("target_id") or "").strip()
            if not target_id:
                continue
            market_facts = self.client.list_real_estate_target_market_facts(
                target_id,
                limit=self.market_fact_limit,
            )
            if not market_facts:
                market_facts = self._national_market_fact_context(limit=self.market_fact_limit)
            timeline_events = self.client.list_real_estate_target_timeline_events(
                target_id,
                limit=self.timeline_limit,
            )
            content_items = _content_items_for_evidence(
                target_id,
                self.client.list_real_estate_target_content_items(
                    target_id,
                    feed="all",
                    limit=self.content_limit,
                ),
            )
            market_fact_count += len(market_facts)
            timeline_event_count += len(timeline_events)
            content_item_count += len(content_items)
            similar_windows = _similar_windows_for_evidence(
                self.similar_windows_provider,
                target_id=target_id,
                ranking_row=row,
                ranking=ranking,
            )
            similar_window_count += len(similar_windows)
            built_logs = build_real_estate_evidence_logs(
                [_snapshot_from_ranking_row(row, ranking)],
                target_id=target_id,
                window_start=ranking["windowStart"],
                evaluated_at=self.clock(),
                market_facts=market_facts,
                timeline_events=timeline_events,
                similar_windows=similar_windows,
                content_items=content_items,
            )
            if self.llm_evaluator is not None:
                evaluated_logs: list[dict[str, Any]] = []
                for log in built_logs:
                    try:
                        evaluated_logs.append(self.llm_evaluator(log))
                    except Exception as exc:
                        llm_error_count += 1
                        logger.warning(
                            "real-estate evidence LLM evaluation failed for target_id=%s; publishing rule-based fallback: %s",
                            target_id,
                            exc,
                        )
                        evaluated_logs.append(_with_llm_fallback_caveat(log))
                built_logs = evaluated_logs
            logs.extend(built_logs)

        if logs:
            self.client.publish_real_estate_evidence_logs(logs)
        needs_attention = any(_log_needs_attention(log) for log in logs)

        return RealEstateEvidenceLogRefreshResult(
            status="PARTIAL" if needs_attention or llm_error_count else "OK" if logs else "EMPTY",
            target_count=len(rows),
            log_count=len(logs),
            market_fact_count=market_fact_count,
            timeline_event_count=timeline_event_count,
            content_item_count=content_item_count,
            similar_window_count=similar_window_count,
            llm_error_count=llm_error_count,
        )

    def _national_market_fact_context(self, *, limit: int) -> list[dict[str, Any]]:
        list_market_facts = getattr(self.client, "list_real_estate_market_facts", None)
        if not callable(list_market_facts):
            return []
        try:
            return list_market_facts(legal_dong_code="00000", limit=limit)
        except Exception:
            logger.exception("real-estate evidence refresh failed to load national market fact context")
            return []


class RealEstateDailyBriefingRefreshJob:
    def __init__(
        self,
        *,
        client: SpringIngestionClient,
        curated_pack_path: str | Path | None = None,
        llm_generator: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        model_name: str = DEFAULT_DAILY_BRIEFING_MODEL,
        prompt_version: str = DEFAULT_DAILY_BRIEFING_PROMPT_VERSION,
        market_fact_limit: int = 40,
        map_target_limit: int = 30,
        content_limit: int = 40,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.curated_pack_path = curated_pack_path
        self.llm_generator = llm_generator
        self.model_name = model_name
        self.prompt_version = prompt_version
        self.market_fact_limit = market_fact_limit
        self.map_target_limit = map_target_limit
        self.content_limit = content_limit
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateDailyBriefingRefreshResult:
        generated_at = self.clock()
        market_facts = self._market_facts()
        map_targets = self._map_targets()
        content_items = self._content_items()
        curated_items = load_daily_briefing_curated_pack(self.curated_pack_path)
        input_pack = build_daily_briefing_input_pack(
            generated_at=generated_at,
            market_facts=market_facts,
            map_targets=map_targets,
            content_items=content_items,
            curated_items=curated_items,
        )
        if not input_pack["candidates"] and not input_pack["sourceItems"]:
            return RealEstateDailyBriefingRefreshResult(
                status="EMPTY",
                briefing_count=0,
                candidate_count=0,
                source_item_count=0,
            )

        llm_error_count = 0
        try:
            if self.llm_generator is None:
                briefing = build_rule_based_daily_briefing(
                    input_pack,
                    model_name="rule-based",
                    prompt_version=self.prompt_version,
                )
            else:
                briefing = apply_daily_briefing_llm_generation(
                    input_pack,
                    self.llm_generator(input_pack),
                    model_name=self.model_name,
                    prompt_version=self.prompt_version,
                )
        except Exception:
            llm_error_count = 1
            logger.exception("real-estate daily briefing LLM generation failed; publishing rule-based fallback")
            briefing = build_rule_based_daily_briefing(
                input_pack,
                model_name="rule-based",
                prompt_version=self.prompt_version,
            )

        self.client.publish_real_estate_daily_briefings([briefing])
        return RealEstateDailyBriefingRefreshResult(
            status="PARTIAL" if llm_error_count else "OK",
            briefing_count=1,
            candidate_count=len(input_pack["candidates"]),
            source_item_count=len(input_pack["sourceItems"]),
            llm_error_count=llm_error_count,
        )

    def _market_facts(self) -> list[dict[str, Any]]:
        try:
            return self.client.list_real_estate_market_facts(
                legal_dong_code="00000",
                limit=self.market_fact_limit,
            )
        except Exception:
            logger.exception("real-estate daily briefing failed to load national market facts")
            return []

    def _map_targets(self) -> list[dict[str, Any]]:
        try:
            return self.client.list_real_estate_map_layer_targets(
                layer_type="sido",
                period="month",
                limit=self.map_target_limit,
            )
        except Exception:
            logger.exception("real-estate daily briefing failed to load map layer targets")
            return []

    def _content_items(self) -> list[dict[str, Any]]:
        list_newsroom_items = getattr(self.client, "list_real_estate_newsroom_items", None)
        if not callable(list_newsroom_items):
            return []
        try:
            return list_newsroom_items(feed="all", page_size=self.content_limit)
        except Exception:
            logger.exception("real-estate daily briefing failed to load newsroom items")
            return []


class RealEstateRecentIssuesRefreshJob:
    def __init__(
        self,
        *,
        client: SpringIngestionClient,
        search_client: RealEstateRecentIssueSearchClient,
        search_targets_jsonl: str | Path | None = None,
        issue_keywords: Sequence[str] | None = None,
        target_type: str = "region",
        window_minutes: int = 60,
        ranking_limit: int = 10,
        result_limit: int = 5,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.search_client = search_client
        self.search_targets_jsonl = Path(search_targets_jsonl) if search_targets_jsonl else None
        self.issue_keywords = tuple(issue_keywords or ())
        self.target_type = target_type
        self.window_minutes = window_minutes
        self.ranking_limit = ranking_limit
        self.result_limit = result_limit
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateRecentIssuesRefreshResult:
        try:
            targets = self._load_targets()
        except Exception as exc:
            logger.warning("real-estate recent issues refresh skipped; input unavailable: %s", exc)
            return RealEstateRecentIssuesRefreshResult(status="INPUT_ERROR", target_count=0, item_count=0)

        try:
            items = build_recent_issue_content_items(
                targets=targets,
                search_client=self.search_client,
                issue_keywords=self.issue_keywords,
                ingested_at=self.clock(),
                result_limit=self.result_limit,
            )
        except Exception:
            logger.exception("real-estate recent issues refresh failed during search")
            return RealEstateRecentIssuesRefreshResult(
                status="PROVIDER_ERROR",
                target_count=len(targets),
                item_count=0,
            )

        try:
            if items:
                self.client.publish_real_estate_content_items(items)
        except Exception:
            logger.exception("real-estate recent issues refresh failed during backend push")
            return RealEstateRecentIssuesRefreshResult(
                status="CLIENT_ERROR",
                target_count=len(targets),
                item_count=len(items),
            )

        result = RealEstateRecentIssuesRefreshResult(
            status="OK",
            target_count=len(targets),
            item_count=len(items),
        )
        logger.info(
            "real-estate recent issues refresh finished; status=%s target_count=%s item_count=%s",
            result.status,
            result.target_count,
            result.item_count,
        )
        return result

    def _load_targets(self):
        if self.search_targets_jsonl is not None:
            return load_recent_issue_search_targets(self.search_targets_jsonl)

        ranking = self.client.get_real_estate_reaction_ranking(
            target_type=self.target_type,
            window_minutes=self.window_minutes,
            limit=self.ranking_limit,
        )
        targets = _recent_issue_targets_from_ranking(ranking)
        return _fill_recent_issue_targets_from_map_layer(
            self.client,
            targets=targets,
            target_type=self.target_type,
            limit=self.ranking_limit,
        )


def _snapshot_from_ranking_row(row: dict[str, Any], ranking: dict[str, Any]) -> dict[str, Any]:
    ratio = row.get("reactionDirectionRatio") or row.get("reaction_direction_ratio") or {}
    freshness = ranking.get("freshness") or {}
    return {
        "snapshotId": row.get("snapshotId") or row.get("snapshot_id"),
        "targetType": row.get("targetType") or row.get("target_type") or "region",
        "targetId": row.get("targetId") or row.get("target_id"),
        "windowStart": ranking.get("windowStart") or ranking.get("window_start"),
        "windowEnd": ranking.get("windowEnd") or ranking.get("window_end"),
        "asOf": freshness.get("asOf") or freshness.get("as_of") or ranking.get("windowEnd") or ranking.get("window_end"),
        "mentionCount": row.get("mentionCount") or row.get("mention_count") or 0,
        "previousMentionCount": row.get("previousMentionCount") or row.get("previous_mention_count") or 0,
        "expectationScore": _ratio_percent(ratio, "expectation"),
        "concernScore": _ratio_percent(ratio, "concern"),
        "neutralScore": _ratio_percent(ratio, "neutral"),
        "heatScore": row.get("heatScore") or row.get("heat_score") or 0,
        "confidence": row.get("confidence"),
        "sourceCount": row.get("sourceCount") or row.get("source_count") or 0,
        "sourceSkew": row.get("sourceSkew") or row.get("source_skew") or 0,
        "coverageStatus": row.get("coverageStatus") or row.get("coverage_status") or freshness.get("coverageStatus") or "unknown",
        "stale": bool(row.get("stale")),
        "issues": row.get("issueMix") or row.get("issues") or [],
    }


def _content_items_for_evidence(target_id: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_items = []
    for item in items:
        if item.get("targets"):
            normalized_items.append(item)
            continue
        copy = dict(item)
        copy["targets"] = [
            {
                "targetId": item.get("targetId") or target_id,
                "linkType": item.get("linkType") or "search_candidate",
                "confidence": item.get("confidence"),
                "reviewState": item.get("reviewState") or "candidate",
            }
        ]
        normalized_items.append(copy)
    return normalized_items


def _similar_windows_for_evidence(
    provider: Callable[[str, dict[str, Any], dict[str, Any]], Sequence[dict[str, Any]]] | None,
    *,
    target_id: str,
    ranking_row: dict[str, Any],
    ranking: dict[str, Any],
) -> list[dict[str, Any]]:
    if provider is None:
        return []
    return [item for item in provider(target_id, ranking_row, ranking) if isinstance(item, dict)]


def _recent_issue_targets_from_ranking(ranking: dict[str, Any]) -> list[RealEstateRecentIssueSearchTarget]:
    targets: list[RealEstateRecentIssueSearchTarget] = []
    for row in ranking.get("items", []):
        if not isinstance(row, dict):
            continue
        target_id = str(row.get("targetId") or row.get("target_id") or "").strip()
        target_type = str(row.get("targetType") or row.get("target_type") or "region").strip()
        display_name = str(row.get("displayName") or row.get("display_name") or "").strip()
        if not target_id or not display_name:
            continue
        keywords = _issue_keywords_from_ranking_row(row)
        targets.append(
            RealEstateRecentIssueSearchTarget(
                target_type=target_type,
                target_id=target_id,
                display_name=display_name,
                keywords=tuple(keywords),
            )
        )
    return targets


def _fill_recent_issue_targets_from_map_layer(
    client: SpringIngestionClient,
    *,
    targets: list[RealEstateRecentIssueSearchTarget],
    target_type: str,
    limit: int,
) -> list[RealEstateRecentIssueSearchTarget]:
    if len(targets) >= limit or target_type != "region":
        return targets[:limit]
    seen_target_ids = {target.target_id for target in targets}
    for map_target in _map_layer_targets_for_fill(client, limit=limit):
        target_id = str(map_target.get("targetId") or map_target.get("target_id") or "").strip()
        if not target_id or target_id in seen_target_ids:
            continue
        display_name = str(map_target.get("displayName") or map_target.get("display_name") or "").strip()
        if not display_name:
            continue
        seen_target_ids.add(target_id)
        targets.append(
            RealEstateRecentIssueSearchTarget(
                target_type=str(map_target.get("targetType") or map_target.get("target_type") or "region").strip(),
                target_id=target_id,
                display_name=display_name,
                keywords=tuple(_issue_keywords_from_map_layer_target(map_target)),
            )
        )
        if len(targets) >= limit:
            break
    return targets[:limit]


def _fill_ranking_rows_from_map_layer(
    client: SpringIngestionClient,
    *,
    ranking: dict[str, Any],
    rows: list[dict[str, Any]],
    target_type: str,
    limit: int,
) -> list[dict[str, Any]]:
    if len(rows) >= limit or target_type != "region":
        return rows[:limit]
    result = list(rows)
    seen_target_ids = {
        str(row.get("targetId") or row.get("target_id") or "").strip()
        for row in result
    }
    for map_target in _map_layer_targets_for_fill(client, limit=limit):
        target_id = str(map_target.get("targetId") or map_target.get("target_id") or "").strip()
        if not target_id or target_id in seen_target_ids:
            continue
        display_name = str(map_target.get("displayName") or map_target.get("display_name") or "").strip()
        if not display_name:
            continue
        seen_target_ids.add(target_id)
        result.append(_ranking_row_from_map_layer_target(map_target, ranking=ranking))
        if len(result) >= limit:
            break
    return result[:limit]


def _map_layer_targets_for_fill(client: SpringIngestionClient, *, limit: int) -> list[dict[str, Any]]:
    list_targets = getattr(client, "list_real_estate_map_layer_targets", None)
    if not callable(list_targets):
        return []
    fetch_limit = max(limit * 2, limit)
    try:
        targets = list_targets(
            layer_type="sido",
            parent_target_id=None,
            period="month",
            limit=fetch_limit,
        )
    except Exception:
        logger.exception("real-estate map layer fallback target load failed")
        return []
    return sorted(
        [target for target in targets if isinstance(target, dict)],
        key=_map_layer_target_sort_key,
    )


def _ranking_row_from_map_layer_target(map_target: dict[str, Any], *, ranking: dict[str, Any]) -> dict[str, Any]:
    period = _map_layer_period(map_target)
    change_pct = _optional_float_field(period.get("changePct") or period.get("change_pct"))
    confidence = _optional_float_field(period.get("confidence"))
    direction = _direction_from_change(change_pct)
    return {
        "targetId": str(map_target.get("targetId") or map_target.get("target_id") or "").strip(),
        "targetType": str(map_target.get("targetType") or map_target.get("target_type") or "region").strip(),
        "displayName": str(map_target.get("displayName") or map_target.get("display_name") or "").strip(),
        "mentionCount": 0,
        "previousMentionCount": 0,
        "mentionDeltaPct": 0.0,
        "reactionDirectionRatio": _ratio_from_change(change_pct),
        "heatScore": _heat_score_from_change(change_pct),
        "confidence": confidence if confidence is not None else 0.5,
        "sourceCount": 0,
        "sourceSkew": 0.0,
        "coverageStatus": "market_data_only",
        "stale": bool(period.get("stale")),
        "issueMix": [
            {
                "issueKey": "price_index",
                "label": "가격지수",
                "share": 1.0,
                "direction": direction,
                "summary": _map_layer_issue_summary(change_pct),
                "confidence": confidence if confidence is not None else 0.5,
            }
        ],
    }


def _issue_keywords_from_map_layer_target(map_target: dict[str, Any]) -> list[str]:
    period = _map_layer_period(map_target)
    change_pct = _optional_float_field(period.get("changePct") or period.get("change_pct"))
    keywords = ["매매가격지수"]
    if change_pct is not None and change_pct > 0:
        keywords.append("상승")
    elif change_pct is not None and change_pct < 0:
        keywords.append("하락")
    return _with_recent_issue_content_keywords(keywords)


def _map_layer_target_sort_key(target: dict[str, Any]) -> tuple[int, float, str]:
    period = _map_layer_period(target)
    status = str(period.get("dataStatus") or period.get("data_status") or "").strip().lower()
    status_rank = 0 if status == "ok" else 1 if status == "partial" else 2
    change_pct = _optional_float_field(period.get("changePct") or period.get("change_pct")) or 0.0
    target_id = str(target.get("targetId") or target.get("target_id") or "")
    return status_rank, -abs(change_pct), target_id


def _map_layer_period(target: dict[str, Any], period_key: str = "month") -> dict[str, Any]:
    periods = target.get("periods")
    if not isinstance(periods, dict):
        return {}
    period = periods.get(period_key)
    if isinstance(period, dict):
        return period
    for value in periods.values():
        if isinstance(value, dict):
            return value
    return {}


def _direction_from_change(change_pct: float | None) -> str:
    if change_pct is not None and change_pct < 0:
        return "concern"
    if change_pct is not None and change_pct > 0:
        return "expectation"
    return "neutral"


def _ratio_from_change(change_pct: float | None) -> dict[str, float]:
    if change_pct is None:
        return {"expectation": 0.2, "concern": 0.2, "neutral": 0.6}
    if change_pct > 0:
        return {"expectation": 0.55, "concern": 0.2, "neutral": 0.25}
    if change_pct < 0:
        return {"expectation": 0.2, "concern": 0.55, "neutral": 0.25}
    return {"expectation": 0.25, "concern": 0.25, "neutral": 0.5}


def _heat_score_from_change(change_pct: float | None) -> int:
    if change_pct is None:
        return 10
    return max(10, min(100, int(round(abs(change_pct) * 100))))


def _map_layer_issue_summary(change_pct: float | None) -> str:
    if change_pct is None:
        return "공식 지도 지표는 확인됐지만 변동률 해석에는 추가 확인이 필요합니다."
    return f"공식 지도 지표 기준 월간 변동률 {change_pct:+.2f}%를 보조 근거로 사용합니다."


def _ranking_with_window_defaults(
    ranking: dict[str, Any],
    *,
    window_minutes: int,
    now: datetime,
) -> dict[str, Any]:
    normalized = dict(ranking or {})
    if normalized.get("windowStart") and normalized.get("windowEnd"):
        return normalized
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    window_end = now.astimezone(timezone.utc)
    window_start = window_end - timedelta(minutes=window_minutes)
    normalized.setdefault("window", f"{window_minutes}m")
    normalized["windowStart"] = normalized.get("windowStart") or _iso_utc(window_start)
    normalized["windowEnd"] = normalized.get("windowEnd") or _iso_utc(window_end)
    freshness = dict(normalized.get("freshness") or {})
    freshness.setdefault("source", "real_estate_map_layer_fallback")
    freshness.setdefault("asOf", normalized["windowEnd"])
    freshness.setdefault("coverageStatus", "market_data_only")
    normalized["freshness"] = freshness
    normalized.setdefault("items", [])
    return normalized


def _issue_keywords_from_ranking_row(row: dict[str, Any]) -> list[str]:
    keywords: list[str] = []
    for issue in row.get("issueMix") or row.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        label = str(issue.get("label") or issue.get("issueKey") or issue.get("issue_key") or "").strip()
        if label and label not in keywords:
            keywords.append(label)
    return _with_recent_issue_content_keywords(keywords or [""])


def _with_recent_issue_content_keywords(keywords: list[str]) -> list[str]:
    result = list(keywords)
    for keyword in RECENT_ISSUE_CONTENT_KEYWORDS:
        if keyword not in result:
            result.append(keyword)
    return result


def _ratio_percent(ratio: dict[str, Any], key: str) -> float:
    value = ratio.get(key) if isinstance(ratio, dict) else 0
    return float(value or 0) * 100


def _optional_float_field(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _utc_day_start(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    normalized = value.astimezone(timezone.utc)
    return normalized.replace(hour=0, minute=0, second=0, microsecond=0)


def _iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _collect_reb_rone_main_snapshot_facts() -> Sequence[object]:
    provider = build_reb_rone_main_snapshot_client_from_env()
    return collect_reb_rone_main_snapshot_facts(provider)


def _collect_reb_rone_official_stats_facts() -> Sequence[object]:
    main_provider = build_reb_rone_main_snapshot_client_from_env()
    monthly_price_index_provider = build_reb_rone_monthly_price_index_client_from_env()
    return [
        *collect_reb_rone_main_snapshot_facts(main_provider),
        *collect_reb_rone_monthly_price_index_facts(monthly_price_index_provider),
    ]


def _region_targets_by_lawd_code(client: SpringIngestionClient) -> dict[str, str]:
    list_targets = getattr(client, "list_real_estate_market_data_targets", None)
    mapping: dict[str, str] = {}
    if callable(list_targets):
        for item in list_targets(enabled=True):
            if not isinstance(item, dict):
                continue
            lawd_code = str(item.get("lawdCode") or item.get("lawd_code") or "").strip()
            target_id = str(item.get("targetId") or item.get("target_id") or "").strip()
            if lawd_code and target_id:
                mapping.setdefault(lawd_code, target_id)
    list_regions = getattr(client, "list_real_estate_regions", None)
    if callable(list_regions):
        for item in list_regions(region_level="eupmyeondong"):
            if not isinstance(item, dict):
                continue
            legal_dong_code = str(item.get("legalDongCode") or item.get("legal_dong_code") or "").strip()
            target_id = str(item.get("targetId") or item.get("target_id") or "").strip()
            if not legal_dong_code or not target_id:
                continue
            mapping.setdefault(legal_dong_code, target_id)
            sigungu_code = legal_dong_code[:5]
            for dong_name in _region_display_name_candidates(item):
                normalized_dong_name = _match_key(dong_name)
                if normalized_dong_name:
                    mapping.setdefault(f"{sigungu_code}:{normalized_dong_name}", target_id)
    return mapping


def _region_display_name_candidates(item: dict[str, Any]) -> list[str]:
    values = [
        item.get("displayName"),
        item.get("display_name"),
        item.get("slug"),
    ]
    candidates: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        candidates.append(text)
        last_token = text.replace("/", " ").replace("-", " ").split()[-1:]
        candidates.extend(last_token)
    return candidates


def _match_key(value: object) -> str:
    if value is None:
        return ""
    return "".join(char for char in str(value) if char.isalnum())


def _complex_registry_market_facts(
    client: SpringIngestionClient,
    *,
    fact_types: Sequence[str],
    limit: int,
) -> list[dict[str, Any]]:
    list_market_facts = getattr(client, "list_real_estate_market_facts", None)
    if not callable(list_market_facts):
        return []
    facts: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    page_size = max(1, min(limit, 500))
    for fact_type in fact_types:
        page = 0
        while True:
            page_facts = list_market_facts(fact_type=fact_type, limit=page_size, page=page)
            if not page_facts:
                break
            for fact in page_facts:
                if not isinstance(fact, dict):
                    continue
                key = _market_fact_identity(fact)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                facts.append(fact)
            if len(page_facts) < page_size:
                break
            page += 1
    return facts


def _market_fact_identity(fact: dict[str, Any]) -> str:
    provider_object_id = str(fact.get("providerObjectId") or fact.get("provider_object_id") or "").strip()
    if provider_object_id:
        return f"provider:{provider_object_id}"
    return f"payload:{repr(sorted(fact.items()))}"


class RealEstateDailyRefreshJob:
    def __init__(self, steps: Sequence[tuple[str, RealEstateRefreshStep]]) -> None:
        self.steps = list(steps)

    def run_once(self) -> RealEstateDailyRefreshResult:
        if not self.steps:
            return RealEstateDailyRefreshResult(
                status="EMPTY",
                step_count=0,
                ok_count=0,
                failed_count=0,
                steps=[],
            )

        step_results: list[RealEstateDailyRefreshStepResult] = []
        for name, step in self.steps:
            try:
                raw_result = step.run_once()
                detail = _result_to_dict(raw_result)
                status = str(detail.get("status") or "OK")
            except Exception as exc:
                logger.exception("real-estate daily refresh step failed; step=%s", name)
                status = "ERROR"
                detail = {"status": status, "error": str(exc)}
            step_results.append(RealEstateDailyRefreshStepResult(name=name, status=status, detail=detail))

        failed_count = sum(1 for step_result in step_results if _is_failed_status(step_result.status))
        attention_count = sum(1 for step_result in step_results if _needs_attention_status(step_result.status))
        ok_count = len(step_results) - failed_count
        result = RealEstateDailyRefreshResult(
            status="OK" if failed_count == 0 and attention_count == 0 else "PARTIAL",
            step_count=len(step_results),
            ok_count=ok_count,
            failed_count=failed_count,
            steps=step_results,
        )
        logger.info(
            "real-estate daily refresh finished; status=%s step_count=%s ok_count=%s failed_count=%s",
            result.status,
            result.step_count,
            result.ok_count,
            result.failed_count,
        )
        return result


def _result_to_dict(result: Any) -> dict[str, Any]:
    if result is None:
        return {"status": "OK"}
    if isinstance(result, dict):
        return dict(result)
    if is_dataclass(result):
        return _camelize_mapping(asdict(result))
    if hasattr(result, "to_dict"):
        payload = result.to_dict()
        if isinstance(payload, dict):
            return payload
    return {"status": "OK", "value": str(result)}


def _top10_readiness(steps: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {
        str(step.get("name") or ""): step.get("detail") if isinstance(step.get("detail"), dict) else {}
        for step in steps
    }
    order = {
        str(step.get("name") or ""): index
        for index, step in enumerate(steps)
    }
    complex_registry = by_name.get("complex_registry", {})
    community_complex_seed = by_name.get("community_complex_seed", {})
    reaction_snapshots = by_name.get("reaction_snapshots", {})
    complex_count = _detail_int(complex_registry, "complexCount", "complex_count")
    alias_count = _detail_int(complex_registry, "aliasCount", "alias_count")
    edge_count = _detail_int(complex_registry, "edgeCount", "edge_count")
    community_observed_count = _detail_int(community_complex_seed, "observedTargetCount", "observed_target_count")
    community_target_count = _detail_int(community_complex_seed, "targetCount", "target_count")
    community_alias_count = _detail_int(community_complex_seed, "aliasCount", "alias_count")
    community_edge_count = _detail_int(community_complex_seed, "edgeCount", "edge_count")
    counts_by_type = reaction_snapshots.get("snapshotCountsByType") or reaction_snapshots.get("snapshot_counts_by_type") or {}
    if not isinstance(counts_by_type, dict):
        counts_by_type = {}
    complex_snapshot_count = _int_value(counts_by_type.get("complex"))
    region_snapshot_count = _int_value(counts_by_type.get("region"))

    missing = []
    if complex_count <= 0:
        missing.append("complex_registry_empty")
    if alias_count <= 0:
        missing.append("complex_alias_empty")
    if edge_count <= 0:
        missing.append("complex_region_edge_empty")
    if "community_complex_seed" not in order:
        missing.append("community_complex_seed_missing")
    if complex_snapshot_count <= 0:
        missing.append("complex_snapshot_empty")
    if region_snapshot_count <= 0:
        missing.append("region_rollup_snapshot_empty")
    if 0 < complex_snapshot_count < REALESTATE_FRONT_TOP10_REQUIRED_ITEMS:
        missing.append("complex_top10_short")
    if 0 < region_snapshot_count < REALESTATE_FRONT_TOP10_REQUIRED_ITEMS:
        missing.append("region_top10_short")
    if (
        "complex_registry" in order
        and "reaction_snapshots" in order
        and order["complex_registry"] > order["reaction_snapshots"]
    ):
        missing = ["complex_registry_order_invalid"]
    if (
        "community_complex_seed" in order
        and "reaction_snapshots" in order
        and order["community_complex_seed"] > order["reaction_snapshots"]
    ):
        missing = ["community_complex_seed_order_invalid"]

    return {
        "status": "READY" if not missing else "PARTIAL",
        "missing": missing,
        "complexRegistry": {
            "complexCount": complex_count,
            "aliasCount": alias_count,
            "edgeCount": edge_count,
        },
        "communityComplexSeed": {
            "observedTargetCount": community_observed_count,
            "targetCount": community_target_count,
            "aliasCount": community_alias_count,
            "edgeCount": community_edge_count,
        },
        "reactionSnapshots": {
            "complex": complex_snapshot_count,
            "region": region_snapshot_count,
        },
        "frontTop10": {
            "requiredItems": REALESTATE_FRONT_TOP10_REQUIRED_ITEMS,
        },
    }


def _detail_int(detail: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key in detail:
            return _int_value(detail.get(key))
    return 0


def _int_value(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _camelize_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            _snake_to_camel(str(key)): _camelize_mapping(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_camelize_mapping(item) for item in value]
    return value


def _snake_to_camel(value: str) -> str:
    parts = value.split("_")
    if len(parts) == 1:
        return value
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _is_failed_status(status: str) -> bool:
    normalized = status.strip().upper()
    return normalized in {"ERROR", "FAILED", "FAIL"} or normalized.endswith("_ERROR")


def _needs_attention_status(status: str) -> bool:
    normalized = status.strip().upper()
    return normalized in {"PARTIAL", "CONFIG_MISSING", "INPUT_MISSING", "EMPTY"}


def _with_llm_fallback_caveat(log: dict[str, Any]) -> dict[str, Any]:
    fallback = dict(log)
    caveats = fallback.get("caveats")
    if not isinstance(caveats, list):
        caveats = []
    fallback["caveats"] = _dedupe_strings([*caveats, "llm_evaluation_failed"])
    fallback["dataQuality"] = "partial"
    return fallback


def _log_needs_attention(log: dict[str, Any]) -> bool:
    caveats = log.get("caveats")
    if not isinstance(caveats, list):
        return False
    required_evidence_missing = {
        "market_fact_missing",
        "national_market_fact_only",
        "timeline_event_missing",
        "search_candidate_missing",
        "llm_evaluation_failed",
        "market_data_only",
    }
    return any(str(caveat) in required_evidence_missing for caveat in caveats)


def _dedupe_strings(values: Sequence[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _run_async(awaitable):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    result_box: dict[str, Any] = {}

    def runner() -> None:
        try:
            result_box["result"] = asyncio.run(awaitable)
        except BaseException as exc:
            result_box["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if "error" in result_box:
        raise result_box["error"]
    return result_box.get("result")


def _int_field(row: dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _normalized_status(row: dict[str, Any]) -> str:
    return str(row.get("status") or row.get("crawlStatus") or "OK").strip().upper()
