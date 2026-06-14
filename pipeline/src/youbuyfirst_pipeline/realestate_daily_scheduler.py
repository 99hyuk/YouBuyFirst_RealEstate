from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.realestate_recent_issues import (
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
class RealEstateEvidenceLogRefreshResult:
    status: str
    target_count: int
    log_count: int
    market_fact_count: int
    content_item_count: int


@dataclass(frozen=True)
class RealEstateMapLayerRefreshResult:
    status: str
    layer_count: int
    snapshot_count: int
    skipped_target_count: int


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
        content_limit: int = 20,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.target_type = target_type
        self.window_minutes = window_minutes
        self.ranking_limit = ranking_limit
        self.market_fact_limit = market_fact_limit
        self.content_limit = content_limit
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
                content_item_count=0,
            )

        logs: list[dict[str, Any]] = []
        market_fact_count = 0
        content_item_count = 0
        for row in rows:
            target_id = str(row.get("targetId") or row.get("target_id") or "").strip()
            if not target_id:
                continue
            market_facts = self.client.list_real_estate_target_market_facts(
                target_id,
                limit=self.market_fact_limit,
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
            content_item_count += len(content_items)
            logs.extend(
                build_real_estate_evidence_logs(
                    [_snapshot_from_ranking_row(row, ranking)],
                    target_id=target_id,
                    window_start=ranking["windowStart"],
                    evaluated_at=self.clock(),
                    market_facts=market_facts,
                    content_items=content_items,
                )
            )

        if logs:
            self.client.publish_real_estate_evidence_logs(logs)

        return RealEstateEvidenceLogRefreshResult(
            status="OK" if logs else "EMPTY",
            target_count=len(rows),
            log_count=len(logs),
            market_fact_count=market_fact_count,
            content_item_count=content_item_count,
        )


class RealEstateRecentIssuesRefreshJob:
    def __init__(
        self,
        *,
        client: SpringIngestionClient,
        search_client: RealEstateRecentIssueSearchClient,
        search_targets_jsonl: str | Path,
        issue_keywords: Sequence[str] | None = None,
        result_limit: int = 5,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.search_client = search_client
        self.search_targets_jsonl = Path(search_targets_jsonl)
        self.issue_keywords = tuple(issue_keywords or ())
        self.result_limit = result_limit
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateRecentIssuesRefreshResult:
        try:
            targets = load_recent_issue_search_targets(self.search_targets_jsonl)
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
        ok_count = len(step_results) - failed_count
        result = RealEstateDailyRefreshResult(
            status="OK" if failed_count == 0 else "PARTIAL",
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
