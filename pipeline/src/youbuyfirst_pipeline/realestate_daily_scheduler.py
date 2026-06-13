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
