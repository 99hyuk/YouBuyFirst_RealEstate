from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from youbuyfirst_pipeline.realestate_reactions import parse_reaction_datetime


DEFAULT_EVALUATION_VERSION = "realestate-eval-v1"
DEFAULT_PROMPT_VERSION = "rule-evidence-v1"


def build_real_estate_evidence_logs(
    snapshots: Iterable[dict[str, Any]],
    *,
    target_id: str,
    window_start: str | datetime,
    evaluated_at: str | datetime,
    market_facts: Iterable[dict[str, Any]] | None = None,
    timeline_events: Iterable[dict[str, Any]] | None = None,
    similar_windows: Iterable[dict[str, Any]] | None = None,
    content_items: Iterable[dict[str, Any]] | None = None,
    evaluation_version: str = DEFAULT_EVALUATION_VERSION,
    prompt_version: str | None = DEFAULT_PROMPT_VERSION,
    model_name: str | None = None,
) -> list[dict[str, Any]]:
    source_window = _iso(parse_reaction_datetime(window_start))
    snapshot = next(
        (
            _normalize_snapshot(item)
            for item in snapshots
            if _text(item.get("targetId") or item.get("target_id")) == target_id
            and _iso(parse_reaction_datetime(item.get("windowStart") or item.get("window_start"))) == source_window
        ),
        None,
    )
    if snapshot is None:
        raise ValueError(f"reaction snapshot not found: {target_id} {source_window}")

    tone = _tone(snapshot)
    evaluated_at_iso = _iso(parse_reaction_datetime(evaluated_at))
    evidence_items = [
        _reaction_evidence_item(snapshot, tone),
        *_market_fact_evidence_items(target_id, market_facts or []),
        *_timeline_event_evidence_items(target_id, timeline_events or []),
        *_similar_window_evidence_items(target_id, similar_windows or []),
        *_search_candidate_evidence_items(target_id, content_items or []),
    ]

    return [
        {
            "evidenceLogId": _stable_id(
                "evidence",
                target_id,
                _compact_timestamp(snapshot["windowStart"]),
                _compact_timestamp(evaluated_at_iso),
                evaluation_version,
            ),
            "targetId": target_id,
            "snapshotId": snapshot.get("snapshotId"),
            "evaluationVersion": evaluation_version,
            "promptVersion": prompt_version,
            "modelName": model_name,
            "tone": tone,
            "summary": _summary(tone),
            "subtitle": _subtitle(snapshot),
            "caveats": _caveats(snapshot, evidence_items),
            "dataQuality": _data_quality(snapshot),
            "confidence": snapshot.get("confidence"),
            "evaluatedAt": evaluated_at_iso,
            "asOf": snapshot["asOf"],
            "skipReason": None,
            "evidenceItems": evidence_items,
        }
    ]


def load_real_estate_evidence_reaction_snapshots(path: str | Path) -> list[dict[str, Any]]:
    return [_normalize_snapshot(record) for record in _load_json_records(path, "reaction snapshot")]


def load_real_estate_evidence_market_facts(path: str | Path) -> list[dict[str, Any]]:
    return _load_json_records(path, "market fact")


def load_real_estate_evidence_timeline_events(path: str | Path) -> list[dict[str, Any]]:
    return _load_json_records(path, "timeline event")


def load_real_estate_evidence_similar_windows(path: str | Path) -> list[dict[str, Any]]:
    return _load_json_records(path, "similar window")


def load_real_estate_evidence_content_items(path: str | Path) -> list[dict[str, Any]]:
    return _load_json_records(path, "content item")


def _normalize_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "snapshotId": record.get("snapshotId") or record.get("snapshot_id"),
        "targetType": _text(record.get("targetType") or record.get("target_type")),
        "targetId": _text(record.get("targetId") or record.get("target_id")),
        "windowStart": _iso(parse_reaction_datetime(record.get("windowStart") or record.get("window_start"))),
        "windowEnd": _iso(parse_reaction_datetime(record.get("windowEnd") or record.get("window_end"))),
        "asOf": _iso(parse_reaction_datetime(record.get("asOf") or record.get("as_of"))),
        "mentionCount": _int(record.get("mentionCount") or record.get("mention_count")),
        "previousMentionCount": _int(record.get("previousMentionCount") or record.get("previous_mention_count")),
        "expectationScore": _float(record.get("expectationScore") or record.get("expectation_score")),
        "concernScore": _float(record.get("concernScore") or record.get("concern_score")),
        "neutralScore": _float(record.get("neutralScore") or record.get("neutral_score")),
        "heatScore": _float(record.get("heatScore") or record.get("heat_score")),
        "confidence": _optional_float(record.get("confidence")),
        "sourceCount": _int(record.get("sourceCount") or record.get("source_count")),
        "sourceSkew": _float(record.get("sourceSkew") or record.get("source_skew")),
        "coverageStatus": _text(record.get("coverageStatus") or record.get("coverage_status") or "unknown"),
        "stale": bool(record.get("stale")),
        "issues": [_normalize_issue(issue) for issue in record.get("issues", []) if isinstance(issue, dict)],
    }


def _normalize_issue(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "issueKey": _text(record.get("issueKey") or record.get("issue_key")),
        "label": _text(record.get("label") or record.get("issueKey") or record.get("issue_key")),
        "share": _float(record.get("share")),
        "direction": _text(record.get("direction")),
        "summary": _text(record.get("summary")),
        "confidence": _optional_float(record.get("confidence")),
    }


def _reaction_evidence_item(snapshot: dict[str, Any], tone: str) -> dict[str, Any]:
    target_id = snapshot["targetId"]
    compact_window = _compact_timestamp(snapshot["windowStart"])
    return {
        "evidenceItemId": _stable_id("reaction", target_id, compact_window),
        "evidenceType": "reaction",
        "refType": "reaction_snapshot",
        "refId": _stable_id(target_id, compact_window),
        "label": "반응 스냅샷",
        "valueText": (
            f"언급 {snapshot['mentionCount']}건 · "
            f"기대 {snapshot['expectationScore']:.1f}% / 우려 {snapshot['concernScore']:.1f}%"
        ),
        "severity": tone,
    }


def _market_fact_evidence_items(target_id: str, facts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for fact in facts:
        if _text(fact.get("targetId") or fact.get("target_id")) != target_id:
            continue
        fact_type = _text(fact.get("factType") or fact.get("fact_type") or "market_fact")
        provider_object_id = _text(fact.get("providerObjectId") or fact.get("provider_object_id"))
        observed_at = _text(fact.get("observedAt") or fact.get("observed_at") or fact.get("asOf") or fact.get("as_of"))
        ref_id = provider_object_id or _stable_id(target_id, fact_type, observed_at or "unknown")
        items.append(
            {
                "evidenceItemId": _stable_id("market-fact", target_id, fact_type, ref_id),
                "evidenceType": "market_fact",
                "refType": "market_fact",
                "refId": _truncate_id(ref_id),
                "label": _market_fact_label(fact_type),
                "valueText": _market_fact_value_text(fact_type, fact.get("valueJson") or fact.get("value_json") or {}),
                "severity": "info",
            }
        )
    return items


def _timeline_event_evidence_items(target_id: str, events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for event in events:
        if _text(event.get("targetId") or event.get("target_id")) != target_id:
            continue
        event_id = _text(event.get("id") or event.get("timelineEventId") or event.get("timeline_event_id"))
        event_type = _text(event.get("eventType") or event.get("event_type") or "event")
        title = _text(event.get("title") or event.get("summary") or "타임라인 이벤트")
        ref_id = event_id or _stable_id("timeline-event", target_id, event_type, title)
        items.append(
            {
                "evidenceItemId": _stable_id("timeline-event", target_id, ref_id),
                "evidenceType": "timeline_event",
                "refType": "timeline_event",
                "refId": _truncate_id(ref_id),
                "label": f"타임라인: {_timeline_event_type_label(event_type)}",
                "valueText": title[:500],
                "severity": "info",
            }
        )
    return items


def _timeline_event_type_label(event_type: str) -> str:
    return {
        "policy": "정책",
        "supply": "공급",
        "transport": "교통",
        "market_fact": "시장 사실",
        "reaction": "반응",
        "news": "뉴스",
        "content": "콘텐츠",
    }.get(event_type, event_type or "이벤트")


def _similar_window_evidence_items(target_id: str, windows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for window in windows:
        source_target_id = _text(window.get("sourceTargetId") or window.get("source_target_id"))
        if source_target_id and source_target_id != target_id:
            continue
        evidence_item = window.get("evidenceItem") or window.get("evidence_item")
        if isinstance(evidence_item, dict):
            items.append(_normalize_evidence_item(evidence_item))
            continue
        matched_target_id = _text(window.get("matchedTargetId") or window.get("matched_target_id") or "unknown")
        score = _optional_float(window.get("similarityScore") or window.get("similarity_score"))
        value = f"유사도 {score * 100:.1f}%" if score is not None else "유사 과거 후보"
        items.append(
            {
                "evidenceItemId": _stable_id("similar-window", target_id, matched_target_id),
                "evidenceType": "similar_window",
                "refType": "similar_window",
                "refId": _stable_id(matched_target_id, _text(window.get("matchedWindowStart") or "unknown")),
                "label": "유사 과거 window",
                "valueText": value,
                "severity": "info",
            }
        )
    return items


def _search_candidate_evidence_items(target_id: str, content_items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for content in content_items:
        if not _content_targets_include(content, target_id):
            continue
        content_id = _text(content.get("contentId") or content.get("content_id"))
        title = _text(content.get("title") or "최근 이슈 후보")
        ref_id = content_id or _stable_id("content", target_id, title)
        items.append(
            {
                "evidenceItemId": _stable_id("search-candidate", target_id, ref_id),
                "evidenceType": "search_candidate",
                "refType": "content",
                "refId": _truncate_id(ref_id),
                "label": "최근 이슈 후보",
                "valueText": title[:500],
                "severity": "info",
            }
        )
    return items


def _normalize_evidence_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidenceItemId": _truncate_id(_text(item.get("evidenceItemId") or item.get("evidence_item_id"))),
        "evidenceType": _text(item.get("evidenceType") or item.get("evidence_type")),
        "refType": _text(item.get("refType") or item.get("ref_type")),
        "refId": _truncate_id(_text(item.get("refId") or item.get("ref_id"))),
        "label": _text(item.get("label")),
        "valueText": _text(item.get("valueText") or item.get("value_text")),
        "severity": _text(item.get("severity") or "info"),
    }


def _content_targets_include(content: dict[str, Any], target_id: str) -> bool:
    targets = content.get("targets") or []
    if not isinstance(targets, list):
        return False
    for target in targets:
        if isinstance(target, dict) and _text(target.get("targetId") or target.get("target_id")) == target_id:
            return True
    return False


def _tone(snapshot: dict[str, Any]) -> str:
    expectation_score = snapshot["expectationScore"]
    concern_score = snapshot["concernScore"]
    if concern_score >= expectation_score + 15:
        return "caution"
    if expectation_score >= concern_score + 15:
        return "watch"
    return "mixed"


def _summary(tone: str) -> str:
    if tone == "caution":
        return "우려 반응이 상대적으로 강하게 관찰됩니다."
    if tone == "watch":
        return "관심과 기대 반응이 빠르게 관찰됩니다."
    return "기대와 우려가 함께 관찰됩니다."


def _subtitle(snapshot: dict[str, Any]) -> str:
    previous = snapshot["previousMentionCount"]
    current = snapshot["mentionCount"]
    if previous > 0:
        growth = ((current - previous) / previous) * 100
        growth_text = f"{growth:+.1f}%"
    else:
        growth_text = "신규"
    issue_labels = [issue["label"] for issue in snapshot["issues"] if issue.get("label")]
    issue_text = ", ".join(issue_labels[:3]) if issue_labels else "확인 필요"
    return f"언급 {current}건, 직전 대비 {growth_text}, 주요 쟁점: {issue_text}"


def _caveats(snapshot: dict[str, Any], evidence_items: list[dict[str, Any]]) -> list[str]:
    caveats = []
    coverage_status = snapshot["coverageStatus"]
    if coverage_status and coverage_status not in {"ok", "normal", "sufficient"}:
        caveats.append(coverage_status)
    if snapshot["stale"]:
        caveats.append("stale")
    present_types = {item["evidenceType"] for item in evidence_items}
    if "market_fact" not in present_types:
        caveats.append("market_fact_missing")
    if "timeline_event" not in present_types:
        caveats.append("timeline_event_missing")
    if "similar_window" not in present_types:
        caveats.append("similar_window_missing")
    if "search_candidate" not in present_types:
        caveats.append("search_candidate_missing")
    return _dedupe(caveats)


def _data_quality(snapshot: dict[str, Any]) -> str:
    if snapshot["stale"]:
        return "stale"
    coverage_status = snapshot["coverageStatus"]
    if coverage_status in {"ok", "normal", "sufficient"}:
        return "ok"
    return coverage_status or "unknown"


def _market_fact_label(fact_type: str) -> str:
    return {
        "apt_trade": "시장 사실: 매매 실거래",
        "apt_rent": "시장 사실: 전월세",
        "official_apartment_price": "시장 사실: 공동주택 공시가격",
        "unsold_housing": "시장 사실: 미분양",
        "price_index": "시장 사실: 가격지수",
    }.get(fact_type, f"시장 사실: {fact_type}")


def _market_fact_value_text(fact_type: str, value_json: dict[str, Any]) -> str:
    if fact_type == "apt_trade" and isinstance(value_json.get("dealAmountManwon"), (int, float)):
        return f"매매 {_format_number(value_json['dealAmountManwon'])}만원"
    if fact_type == "apt_rent":
        deposit = value_json.get("depositAmountManwon")
        monthly = value_json.get("monthlyRentAmountManwon")
        parts = []
        if isinstance(deposit, (int, float)):
            parts.append(f"보증금 {_format_number(deposit)}만원")
        if isinstance(monthly, (int, float)):
            parts.append(f"월세 {_format_number(monthly)}만원")
        return " / ".join(parts) if parts else "전월세 사실 확인"
    if fact_type == "official_apartment_price" and isinstance(value_json.get("officialPriceWon"), (int, float)):
        return f"공시가격 {_format_number(value_json['officialPriceWon'])}원"
    if fact_type in {"unsold_housing", "price_index"}:
        for key in ("value", "count", "householdCount", "indexValue"):
            if isinstance(value_json.get(key), (int, float)):
                return f"{key} {_format_number(value_json[key])}"
    return "시장 사실 확인"


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
        elif isinstance(payload, dict) and "logs" in payload:
            records = payload.get("logs", [])
        elif isinstance(payload, dict):
            records = [payload]
        else:
            records = payload
    if not isinstance(records, list):
        raise ValueError(f"{label} payload must be a JSON array, object, or JSONL records")
    return [record for record in records if isinstance(record, dict)]


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _compact_timestamp(value: str) -> str:
    parsed = parse_reaction_datetime(value)
    return parsed.strftime("%Y%m%d%H%M%S")


def _stable_id(*parts: str) -> str:
    raw = "-".join(_text(part) for part in parts if _text(part))
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return _truncate_id(slug or hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24])


def _truncate_id(value: str, max_length: int = 120) -> str:
    if len(value) <= max_length:
        return value
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{value[: max_length - 13]}-{digest}"


def _format_number(value: int | float) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.1f}"
    return f"{int(value):,}"


def _dedupe(values: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    return int(float(value or 0))


def _float(value: object) -> float:
    return float(value or 0.0)


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
