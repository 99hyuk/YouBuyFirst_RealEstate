from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from youbuyfirst_pipeline.realestate_reactions import parse_reaction_datetime


@dataclass(frozen=True)
class RealEstateSimilarWindowMatch:
    source_target_id: str
    source_window_start: str
    matched_target_id: str
    matched_window_start: str
    matched_window_end: str
    similarity_score: float
    match_reason: str
    issue_overlap: list[str]
    after_market_summary: dict[str, Any]
    caveat: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceTargetId": self.source_target_id,
            "sourceWindowStart": self.source_window_start,
            "matchedTargetId": self.matched_target_id,
            "matchedWindowStart": self.matched_window_start,
            "matchedWindowEnd": self.matched_window_end,
            "similarityScore": self.similarity_score,
            "matchReason": self.match_reason,
            "issueOverlap": self.issue_overlap,
            "afterMarketSummary": self.after_market_summary,
            "caveat": self.caveat,
            "evidenceItem": self.to_evidence_item_dict(),
        }

    def to_evidence_item_dict(self) -> dict[str, str | None]:
        value_text = f"유사도 {self.similarity_score * 100:.1f}%"
        market_flow = _primary_market_flow_label(self.after_market_summary)
        if market_flow:
            value_text = f"{value_text} · {market_flow}"
        return {
            "evidenceItemId": _stable_id(
                "similar-window",
                self.source_target_id,
                self.source_window_start,
                self.matched_target_id,
                self.matched_window_start,
            ),
            "evidenceType": "similar_window",
            "refType": "similar_window",
            "refId": _stable_id(
                "similar-window-ref",
                self.source_target_id,
                self.source_window_start,
                self.matched_target_id,
                self.matched_window_start,
            ),
            "label": "유사 과거 window",
            "valueText": value_text,
            "severity": "info",
        }


def load_real_estate_reaction_snapshot_payloads(path: str | Path) -> list[dict[str, Any]]:
    records = _load_json_records(path, "reaction snapshot")
    return [_normalize_snapshot(record) for record in records]


def load_real_estate_market_fact_payloads(path: str | Path) -> list[dict[str, Any]]:
    records = _load_json_records(path, "market fact")
    return [_normalize_market_fact(record) for record in records]


def find_real_estate_similar_windows(
    snapshots: Iterable[dict[str, Any]],
    *,
    source_target_id: str,
    source_window_start: str | datetime,
    market_facts: Iterable[dict[str, Any]] | None = None,
    horizon_days: int = 90,
    top_n: int = 5,
) -> list[RealEstateSimilarWindowMatch]:
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive")
    if top_n <= 0:
        raise ValueError("top_n must be positive")

    normalized_snapshots = [_normalize_snapshot(snapshot) for snapshot in snapshots]
    source_window = _iso(parse_reaction_datetime(source_window_start))
    source = next(
        (
            snapshot
            for snapshot in normalized_snapshots
            if snapshot["targetId"] == source_target_id
            and snapshot["windowStart"] == source_window
        ),
        None,
    )
    if source is None:
        raise ValueError(f"source reaction snapshot not found: {source_target_id} {source_window}")

    facts = [_normalize_market_fact(fact) for fact in market_facts or []]
    source_start = parse_reaction_datetime(source["windowStart"])
    scored_matches: list[tuple[float, RealEstateSimilarWindowMatch]] = []
    for candidate in normalized_snapshots:
        if candidate["targetId"] == source["targetId"] and candidate["windowStart"] == source["windowStart"]:
            continue
        candidate_start = parse_reaction_datetime(candidate["windowStart"])
        if candidate_start >= source_start:
            continue
        score, reason, issue_overlap = _score_snapshot_pair(source, candidate)
        after_market_summary = _after_market_summary(
            candidate,
            facts,
            horizon_days=horizon_days,
        )
        caveat = None if after_market_summary["items"] else "market_fact_missing"
        scored_matches.append(
            (
                score,
                RealEstateSimilarWindowMatch(
                    source_target_id=source["targetId"],
                    source_window_start=source["windowStart"],
                    matched_target_id=candidate["targetId"],
                    matched_window_start=candidate["windowStart"],
                    matched_window_end=candidate["windowEnd"],
                    similarity_score=score,
                    match_reason=reason,
                    issue_overlap=issue_overlap,
                    after_market_summary=after_market_summary,
                    caveat=caveat,
                ),
            )
        )

    return [
        match
        for _, match in sorted(
            scored_matches,
            key=lambda item: (-item[0], item[1].matched_window_start, item[1].matched_target_id),
        )[:top_n]
    ]


def _score_snapshot_pair(source: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, str, list[str]]:
    reaction_similarity = 1.0 - min(
        (
            abs(source["expectationScore"] - candidate["expectationScore"])
            + abs(source["concernScore"] - candidate["concernScore"])
            + abs(source["neutralScore"] - candidate["neutralScore"])
        )
        / 300.0,
        1.0,
    )
    heat_similarity = 1.0 - min(abs(source["heatScore"] - candidate["heatScore"]) / 100.0, 1.0)
    mention_similarity = 1.0 - min(abs(_mention_growth(source) - _mention_growth(candidate)) / 4.0, 1.0)
    issue_similarity, issue_overlap = _issue_similarity(source, candidate)
    score = round(
        max(
            0.0,
            min(
                1.0,
                reaction_similarity * 0.40
                + heat_similarity * 0.20
                + issue_similarity * 0.25
                + mention_similarity * 0.15,
            ),
        ),
        4,
    )
    reason = (
        f"reaction:{reaction_similarity:.2f} "
        f"issue:{issue_similarity:.2f} "
        f"heat:{heat_similarity:.2f} "
        f"mention:{mention_similarity:.2f}"
    )
    return score, reason, issue_overlap


def _issue_similarity(source: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, list[str]]:
    source_issues = {issue["issueKey"] for issue in source["issues"] if issue.get("issueKey")}
    candidate_issues = {issue["issueKey"] for issue in candidate["issues"] if issue.get("issueKey")}
    if not source_issues and not candidate_issues:
        return 0.5, []
    union = source_issues | candidate_issues
    if not union:
        return 0.0, []
    overlap = sorted(source_issues & candidate_issues)
    return round(len(overlap) / len(union), 4), overlap


def _after_market_summary(
    candidate: dict[str, Any],
    facts: list[dict[str, Any]],
    *,
    horizon_days: int,
) -> dict[str, Any]:
    window_end = parse_reaction_datetime(candidate["windowEnd"])
    horizon_end = window_end + timedelta(days=horizon_days)
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for fact in facts:
        if fact["targetId"] != candidate["targetId"]:
            continue
        observed_at = fact["observedAt"]
        if observed_at < window_end or observed_at > horizon_end:
            continue
        metric = _market_metric_key(fact)
        if metric is None:
            continue
        key, value = metric
        buckets.setdefault((fact["factType"], key), []).append({**fact, "metricValue": value})

    items = []
    for (fact_type, metric), bucket in sorted(buckets.items()):
        ordered = sorted(bucket, key=lambda item: item["observedAt"])
        if len(ordered) < 2:
            continue
        first = ordered[0]
        last = ordered[-1]
        first_value = float(first["metricValue"])
        last_value = float(last["metricValue"])
        delta_pct = round(((last_value - first_value) / abs(first_value)) * 100, 2) if first_value else None
        items.append(
            {
                "factType": fact_type,
                "metric": metric,
                "firstObservedAt": first["observedAtLabel"],
                "lastObservedAt": last["observedAtLabel"],
                "firstValue": first_value,
                "lastValue": last_value,
                "deltaPct": delta_pct,
                "sampleCount": len(ordered),
            }
        )

    return {
        "horizonDays": horizon_days,
        "items": items,
    }


def _market_metric_key(fact: dict[str, Any]) -> tuple[str, float] | None:
    value_json = fact.get("valueJson")
    if not isinstance(value_json, dict):
        return None
    preferred_metrics = {
        "apt_trade": ("dealAmountManwon",),
        "apt_rent": ("depositAmountManwon", "monthlyRentAmountManwon"),
        "official_apartment_price": ("officialPriceWon",),
        "unsold_housing": ("value", "count", "householdCount"),
        "price_index": ("indexValue", "value"),
    }
    for metric in preferred_metrics.get(fact["factType"], tuple(value_json.keys())):
        value = value_json.get(metric)
        if isinstance(value, (int, float)):
            return metric, float(value)
    return None


def _primary_market_flow_label(summary: dict[str, Any]) -> str | None:
    items = summary.get("items") if isinstance(summary, dict) else None
    if not items:
        return None
    first = items[0]
    delta_pct = first.get("deltaPct")
    if delta_pct is None:
        return None
    prefix = {
        "apt_trade": "매매",
        "apt_rent": "전월세",
        "official_apartment_price": "공시가격",
        "unsold_housing": "미분양",
        "price_index": "가격지수",
    }.get(first.get("factType"), str(first.get("factType") or "시장"))
    sign = "+" if delta_pct > 0 else ""
    return f"{prefix} {sign}{delta_pct:.1f}%"


def _normalize_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    issues = record.get("issues") or []
    return {
        "targetType": _text(record.get("targetType") or record.get("target_type")),
        "targetId": _text(record.get("targetId") or record.get("target_id")),
        "windowStart": _iso(parse_reaction_datetime(record.get("windowStart") or record.get("window_start"))),
        "windowEnd": _iso(parse_reaction_datetime(record.get("windowEnd") or record.get("window_end"))),
        "mentionCount": _int(record.get("mentionCount") or record.get("mention_count")),
        "previousMentionCount": _int(record.get("previousMentionCount") or record.get("previous_mention_count")),
        "expectationScore": _float(record.get("expectationScore") or record.get("expectation_score")),
        "concernScore": _float(record.get("concernScore") or record.get("concern_score")),
        "neutralScore": _float(record.get("neutralScore") or record.get("neutral_score")),
        "heatScore": _float(record.get("heatScore") or record.get("heat_score")),
        "issues": [_normalize_issue(issue) for issue in issues if isinstance(issue, dict)],
    }


def _normalize_issue(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "issueKey": _text(record.get("issueKey") or record.get("issue_key")),
        "direction": _text(record.get("direction")),
        "share": _float(record.get("share")),
    }


def _normalize_market_fact(record: dict[str, Any]) -> dict[str, Any]:
    observed_raw = record.get("observedAt") or record.get("observed_at")
    return {
        "targetId": _text(record.get("targetId") or record.get("target_id")),
        "factType": _text(record.get("factType") or record.get("fact_type")),
        "observedAt": _parse_market_datetime(observed_raw),
        "observedAtLabel": _observed_label(observed_raw),
        "valueJson": record.get("valueJson") or record.get("value_json") or {},
    }


def _load_json_records(path: str | Path, label: str) -> list[dict[str, Any]]:
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
        raise ValueError(f"{label} payload must be a JSON array or JSONL records")
    return [record for record in records if isinstance(record, dict)]


def _mention_growth(snapshot: dict[str, Any]) -> float:
    previous = max(1, snapshot["previousMentionCount"])
    return (snapshot["mentionCount"] - snapshot["previousMentionCount"]) / previous


def _parse_market_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = _text(value)
        if not text:
            raise ValueError("market fact observedAt is required")
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _observed_label(value: object) -> str:
    text = _text(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    return _iso(_parse_market_datetime(value))


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(*parts: str) -> str:
    value = "-".join(parts)
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:120]


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    return int(float(value or 0))


def _float(value: object) -> float:
    return float(value or 0.0)
