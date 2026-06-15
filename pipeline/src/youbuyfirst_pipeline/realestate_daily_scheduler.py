from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.realestate_recent_issues import (
    RealEstateRecentIssueSearchTarget,
    RealEstateRecentIssueSearchClient,
    build_recent_issue_content_items,
    load_recent_issue_search_targets,
)
from youbuyfirst_pipeline.realestate_evidence import build_real_estate_evidence_logs

logger = logging.getLogger(__name__)


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
        return {
            "status": self.status,
            "stepCount": self.step_count,
            "okCount": self.ok_count,
            "failedCount": self.failed_count,
            "steps": [asdict(step) for step in self.steps],
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
        periods: Sequence[str] = ("week", "month", "halfYear"),
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
        rows = [row for row in ranking.get("items", []) if isinstance(row, dict)]
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
        for row in rows:
            target_id = str(row.get("targetId") or row.get("target_id") or "").strip()
            if not target_id:
                continue
            market_facts = self.client.list_real_estate_target_market_facts(
                target_id,
                limit=self.market_fact_limit,
            )
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
                built_logs = [self.llm_evaluator(log) for log in built_logs]
            logs.extend(built_logs)

        if logs:
            self.client.publish_real_estate_evidence_logs(logs)
        needs_attention = any(_log_needs_attention(log) for log in logs)

        return RealEstateEvidenceLogRefreshResult(
            status="PARTIAL" if needs_attention else "OK" if logs else "EMPTY",
            target_count=len(rows),
            log_count=len(logs),
            market_fact_count=market_fact_count,
            timeline_event_count=timeline_event_count,
            content_item_count=content_item_count,
            similar_window_count=similar_window_count,
        )


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
        return _recent_issue_targets_from_ranking(ranking)


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


def _issue_keywords_from_ranking_row(row: dict[str, Any]) -> list[str]:
    keywords: list[str] = []
    for issue in row.get("issueMix") or row.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        label = str(issue.get("label") or issue.get("issueKey") or issue.get("issue_key") or "").strip()
        if label and label not in keywords:
            keywords.append(label)
    return keywords or [""]


def _ratio_percent(ratio: dict[str, Any], key: str) -> float:
    value = ratio.get(key) if isinstance(ratio, dict) else 0
    return float(value or 0) * 100


def _iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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
        return asdict(result)
    if hasattr(result, "to_dict"):
        payload = result.to_dict()
        if isinstance(payload, dict):
            return payload
    return {"status": "OK", "value": str(result)}


def _is_failed_status(status: str) -> bool:
    normalized = status.strip().upper()
    return normalized in {"ERROR", "FAILED", "FAIL"} or normalized.endswith("_ERROR")


def _needs_attention_status(status: str) -> bool:
    normalized = status.strip().upper()
    return normalized in {"PARTIAL", "CONFIG_MISSING", "INPUT_MISSING"}


def _log_needs_attention(log: dict[str, Any]) -> bool:
    caveats = log.get("caveats")
    if not isinstance(caveats, list):
        return False
    required_evidence_missing = {
        "market_fact_missing",
        "timeline_event_missing",
        "search_candidate_missing",
    }
    return any(str(caveat) in required_evidence_missing for caveat in caveats)


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
