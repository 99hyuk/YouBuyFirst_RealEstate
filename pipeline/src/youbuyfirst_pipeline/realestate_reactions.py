from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class RealEstateReactionObservation:
    target_type: str
    target_id: str
    published_at: datetime
    source: str
    reaction_direction: str = "neutral"
    issues: list[dict[str, Any]] = field(default_factory=list)
    external_id: str | None = None
    matched_text: str | None = None
    match_source: str | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class RealEstateReactionSnapshotIssue:
    issue_key: str
    label: str
    share: float
    direction: str
    summary: str
    confidence: float

    def to_request_dict(self) -> dict:
        return {
            "issueKey": self.issue_key,
            "label": self.label,
            "share": self.share,
            "direction": self.direction,
            "summary": self.summary,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class RealEstateReactionSnapshot:
    target_type: str
    target_id: str
    window_start: datetime
    window_end: datetime
    as_of: datetime
    mention_count: int
    previous_mention_count: int
    expectation_score: float
    concern_score: float
    neutral_score: float
    heat_score: int
    confidence: float
    source_count: int
    source_skew: float
    coverage_status: str
    stale: bool
    issues: list[RealEstateReactionSnapshotIssue]

    def to_request_dict(self) -> dict:
        return {
            "targetType": self.target_type,
            "targetId": self.target_id,
            "windowStart": _iso(self.window_start),
            "windowEnd": _iso(self.window_end),
            "asOf": _iso(self.as_of),
            "mentionCount": self.mention_count,
            "previousMentionCount": self.previous_mention_count,
            "expectationScore": self.expectation_score,
            "concernScore": self.concern_score,
            "neutralScore": self.neutral_score,
            "heatScore": self.heat_score,
            "confidence": self.confidence,
            "sourceCount": self.source_count,
            "sourceSkew": self.source_skew,
            "coverageStatus": self.coverage_status,
            "stale": self.stale,
            "issues": [issue.to_request_dict() for issue in self.issues],
        }


def build_real_estate_reaction_snapshots(
    observations: Iterable[RealEstateReactionObservation],
    *,
    window_start: datetime,
    window_minutes: int,
    as_of: datetime | None = None,
    stale_after_minutes: int = 360,
) -> list[RealEstateReactionSnapshot]:
    if window_minutes <= 0:
        raise ValueError("window_minutes must be positive")
    if stale_after_minutes <= 0:
        raise ValueError("stale_after_minutes must be positive")

    normalized_window_start = _as_utc(window_start)
    window = timedelta(minutes=window_minutes)
    window_end = normalized_window_start + window
    previous_window_start = normalized_window_start - window
    snapshot_as_of = _as_utc(as_of or datetime.now(timezone.utc))

    current_groups: dict[tuple[str, str], list[RealEstateReactionObservation]] = defaultdict(list)
    previous_counts: Counter[tuple[str, str]] = Counter()
    for observation in observations:
        normalized = _normalize_observation(observation)
        key = (normalized.target_type, normalized.target_id)
        if normalized_window_start <= normalized.published_at < window_end:
            current_groups[key].append(normalized)
            continue
        if previous_window_start <= normalized.published_at < normalized_window_start:
            previous_counts[key] += 1

    snapshots = [
        _build_snapshot(
            key,
            group,
            previous_counts[key],
            window_start=normalized_window_start,
            window_end=window_end,
            as_of=snapshot_as_of,
            stale_after_minutes=stale_after_minutes,
        )
        for key, group in current_groups.items()
    ]
    return sorted(snapshots, key=lambda snapshot: (-snapshot.mention_count, -snapshot.heat_score, snapshot.target_id))


def load_real_estate_reaction_observations(path: str | Path) -> list[RealEstateReactionObservation]:
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    if not text:
        return []

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        if isinstance(payload, dict) and "items" in payload:
            records = payload.get("items", [])
        elif isinstance(payload, dict):
            records = [payload]
        else:
            records = payload

    if not isinstance(records, list):
        raise ValueError("reaction observation payload must be a JSON array or JSONL records")
    return [_observation_from_mapping(record) for record in records if isinstance(record, dict)]


def parse_reaction_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return _as_utc(value)
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return _as_utc(datetime.fromisoformat(normalized))


def _build_snapshot(
    key: tuple[str, str],
    observations: list[RealEstateReactionObservation],
    previous_mention_count: int,
    *,
    window_start: datetime,
    window_end: datetime,
    as_of: datetime,
    stale_after_minutes: int,
) -> RealEstateReactionSnapshot:
    target_type, target_id = key
    mention_count = len(observations)
    direction_counts = Counter(observation.reaction_direction for observation in observations)
    expectation_score = _pct(direction_counts["expectation"], mention_count)
    concern_score = _pct(direction_counts["concern"], mention_count)
    neutral_score = _pct(direction_counts["neutral"], mention_count)
    source_counts = Counter(observation.source for observation in observations if observation.source)
    source_count = len(source_counts)
    source_skew = round(max(source_counts.values()) / mention_count, 2) if source_counts else 0.0
    heat_score = _heat_score(
        mention_count=mention_count,
        previous_mention_count=previous_mention_count,
        expectation_score=expectation_score,
        concern_score=concern_score,
    )
    latest_published_at = max(observation.published_at for observation in observations)
    stale = as_of - latest_published_at > timedelta(minutes=stale_after_minutes)

    return RealEstateReactionSnapshot(
        target_type=target_type,
        target_id=target_id,
        window_start=window_start,
        window_end=window_end,
        as_of=as_of,
        mention_count=mention_count,
        previous_mention_count=previous_mention_count,
        expectation_score=expectation_score,
        concern_score=concern_score,
        neutral_score=neutral_score,
        heat_score=heat_score,
        confidence=_confidence(mention_count, source_count, source_skew, stale=stale),
        source_count=source_count,
        source_skew=source_skew,
        coverage_status=_coverage_status(
            mention_count=mention_count,
            source_skew=source_skew,
            stale=stale,
        ),
        stale=stale,
        issues=_aggregate_issues(observations, mention_count),
    )


def _aggregate_issues(
    observations: list[RealEstateReactionObservation],
    mention_count: int,
) -> list[RealEstateReactionSnapshotIssue]:
    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}
    for observation in observations:
        for raw_issue in observation.issues:
            if not isinstance(raw_issue, dict):
                continue
            issue_key = str(raw_issue.get("issueKey") or raw_issue.get("issue_key") or "").strip()
            if not issue_key:
                continue
            label = str(raw_issue.get("label") or issue_key).strip()
            direction = _normalize_direction(raw_issue.get("direction") or observation.reaction_direction)
            key = (issue_key, label, direction)
            bucket = buckets.setdefault(
                key,
                {
                    "count": 0,
                    "confidence_sum": 0.0,
                    "summary": "",
                },
            )
            bucket["count"] += 1
            bucket["confidence_sum"] += _float(raw_issue.get("confidence"), default=0.5)
            if not bucket["summary"]:
                bucket["summary"] = str(raw_issue.get("summary") or "").strip()

    sorted_items = sorted(
        buckets.items(),
        key=lambda item: (-item[1]["count"], item[0][0]),
    )
    return [
        RealEstateReactionSnapshotIssue(
            issue_key=issue_key,
            label=label,
            share=round(bucket["count"] / mention_count, 2),
            direction=direction,
            summary=bucket["summary"],
            confidence=round(bucket["confidence_sum"] / bucket["count"], 2),
        )
        for (issue_key, label, direction), bucket in sorted_items[:5]
    ]


def _observation_from_mapping(record: dict[str, Any]) -> RealEstateReactionObservation:
    target_type = str(record.get("targetType") or record.get("target_type") or "").strip()
    target_id = str(record.get("targetId") or record.get("target_id") or "").strip()
    published_at = record.get("publishedAt") or record.get("published_at")
    if not target_type or not target_id or not published_at:
        raise ValueError("reaction observation requires targetType, targetId, and publishedAt")

    issues = record.get("issues") or []
    return RealEstateReactionObservation(
        target_type=target_type,
        target_id=target_id,
        published_at=parse_reaction_datetime(published_at),
        source=str(record.get("source") or "unknown").strip() or "unknown",
        reaction_direction=_normalize_direction(
            record.get("reactionDirection")
            or record.get("reaction_direction")
            or record.get("direction")
        ),
        issues=[issue for issue in issues if isinstance(issue, dict)] if isinstance(issues, list) else [],
        external_id=str(record.get("externalId") or record.get("external_id")).strip()
        if record.get("externalId") or record.get("external_id")
        else None,
        matched_text=str(record.get("matchedText") or record.get("matched_text")).strip()
        if record.get("matchedText") or record.get("matched_text")
        else None,
        match_source=str(record.get("matchSource") or record.get("match_source")).strip()
        if record.get("matchSource") or record.get("match_source")
        else None,
        confidence=_float(record.get("confidence"), default=0.0) if record.get("confidence") is not None else None,
    )


def _normalize_observation(observation: RealEstateReactionObservation) -> RealEstateReactionObservation:
    return RealEstateReactionObservation(
        target_type=observation.target_type.strip(),
        target_id=observation.target_id.strip(),
        published_at=_as_utc(observation.published_at),
        source=observation.source.strip() or "unknown",
        reaction_direction=_normalize_direction(observation.reaction_direction),
        issues=observation.issues,
        external_id=observation.external_id,
        matched_text=observation.matched_text,
        match_source=observation.match_source,
        confidence=observation.confidence,
    )


def _normalize_direction(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"expectation", "positive", "bullish", "up", "good"}:
        return "expectation"
    if normalized in {"concern", "negative", "bearish", "down", "bad", "risk"}:
        return "concern"
    return "neutral"


def _heat_score(
    *,
    mention_count: int,
    previous_mention_count: int,
    expectation_score: float,
    concern_score: float,
) -> int:
    increased_mentions = max(0, mention_count - previous_mention_count)
    dominant_reaction_score = max(expectation_score, concern_score)
    score = mention_count * 10 + increased_mentions * 8 + dominant_reaction_score * 0.3
    return int(round(min(100, score)))


def _confidence(mention_count: int, source_count: int, source_skew: float, *, stale: bool = False) -> float:
    score = 0.35 + min(mention_count, 20) * 0.03 + min(source_count, 5) * 0.08 - source_skew * 0.1
    if stale:
        score -= 0.15
    return round(min(0.95, max(0.2, score)), 2)


def _coverage_status(*, mention_count: int, source_skew: float, stale: bool) -> str:
    if stale:
        return "stale"
    if mention_count < 3:
        return "low_sample"
    if source_skew >= 0.8:
        return "source_skewed"
    return "partial"


def _pct(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(value / total * 100, 1)


def _float(value: object, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")
