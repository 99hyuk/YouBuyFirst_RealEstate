from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from youbuyfirst_pipeline.realestate_reactions import RealEstateReactionObservation


@dataclass(frozen=True)
class RealEstateTargetEdgeRule:
    from_target_type: str
    from_target_id: str
    to_target_type: str
    to_target_id: str
    edge_type: str = "contains"
    review_state: str = "approved"
    confidence: float = 1.0
    source: str | None = None


def load_real_estate_target_edge_rules(path: str | Path) -> list[RealEstateTargetEdgeRule]:
    records = _load_json_records(path)
    return [_edge_from_mapping(record) for record in records]


def roll_up_real_estate_reaction_observations(
    observations: Iterable[RealEstateReactionObservation],
    edges: Iterable[RealEstateTargetEdgeRule],
    *,
    edge_types: set[str] | None = None,
    include_candidate_sources: set[str] | None = None,
) -> list[RealEstateReactionObservation]:
    original_observations = list(observations)
    direct_observation_keys = {
        (
            observation.target_type.strip(),
            observation.target_id.strip(),
            observation.external_id,
            observation.source,
        )
        for observation in original_observations
    }
    parent_edges_by_child = _parent_edges_by_child(
        edges,
        edge_types=edge_types or {"contains"},
        include_candidate_sources=include_candidate_sources or set(),
    )
    derived: dict[tuple[str, str, str | None, str], RealEstateReactionObservation] = {}

    for observation in original_observations:
        child_key = (observation.target_type.strip(), observation.target_id.strip())
        for ancestor_edge, confidence_factor, source_key in _ancestor_edges(child_key, parent_edges_by_child):
            direct_key = (
                ancestor_edge.from_target_type,
                ancestor_edge.from_target_id,
                observation.external_id,
                observation.source,
            )
            if direct_key in direct_observation_keys:
                continue
            key = (
                ancestor_edge.from_target_type,
                ancestor_edge.from_target_id,
                observation.external_id,
                observation.source,
            )
            derived_observation = RealEstateReactionObservation(
                target_type=ancestor_edge.from_target_type,
                target_id=ancestor_edge.from_target_id,
                published_at=observation.published_at,
                source=observation.source,
                reaction_direction=observation.reaction_direction,
                issues=observation.issues,
                external_id=observation.external_id,
                matched_text=f"rollup:{source_key[1]}",
                match_source=f"target_graph:{ancestor_edge.edge_type}",
                confidence=_rollup_confidence(observation.confidence, confidence_factor),
            )
            existing = derived.get(key)
            if existing is not None and _confidence_rank(existing.confidence) >= _confidence_rank(derived_observation.confidence):
                continue
            derived[key] = derived_observation

    return sorted([*derived.values(), *original_observations], key=lambda item: (item.target_id, item.source))


def _parent_edges_by_child(
    edges: Iterable[RealEstateTargetEdgeRule],
    *,
    edge_types: set[str],
    include_candidate_sources: set[str],
) -> dict[tuple[str, str], list[RealEstateTargetEdgeRule]]:
    result: dict[tuple[str, str], list[RealEstateTargetEdgeRule]] = {}
    for edge in edges:
        normalized = _normalize_edge(edge)
        if not _is_confirmed_edge(normalized, include_candidate_sources=include_candidate_sources):
            continue
        if normalized.edge_type not in edge_types:
            continue
        child_key = (normalized.to_target_type, normalized.to_target_id)
        result.setdefault(child_key, []).append(normalized)
    for entries in result.values():
        entries.sort(key=lambda entry: (entry.from_target_type, entry.from_target_id, entry.edge_type))
    return result


def _is_confirmed_edge(edge: RealEstateTargetEdgeRule, *, include_candidate_sources: set[str]) -> bool:
    if edge.review_state == "approved":
        return True
    source = (edge.source or "").strip()
    return edge.review_state == "candidate" and bool(source) and source in include_candidate_sources


def _ancestor_edges(
    child_key: tuple[str, str],
    parent_edges_by_child: dict[tuple[str, str], list[RealEstateTargetEdgeRule]],
) -> list[tuple[RealEstateTargetEdgeRule, float, tuple[str, str]]]:
    ancestors: list[tuple[RealEstateTargetEdgeRule, float, tuple[str, str]]] = []
    stack = [(child_key, 1.0, child_key, {child_key})]
    while stack:
        current_key, confidence_factor, source_key, visited = stack.pop()
        for edge in parent_edges_by_child.get(current_key, []):
            parent_key = (edge.from_target_type, edge.from_target_id)
            if parent_key in visited:
                continue
            next_confidence = confidence_factor * edge.confidence
            ancestors.append((edge, next_confidence, source_key))
            stack.append((parent_key, next_confidence, source_key, {*visited, parent_key}))
    return sorted(ancestors, key=lambda item: (item[0].from_target_id, item[0].to_target_id))


def _normalize_edge(edge: RealEstateTargetEdgeRule) -> RealEstateTargetEdgeRule:
    return RealEstateTargetEdgeRule(
        from_target_type=edge.from_target_type.strip(),
        from_target_id=edge.from_target_id.strip(),
        to_target_type=edge.to_target_type.strip(),
        to_target_id=edge.to_target_id.strip(),
        edge_type=edge.edge_type.strip().lower() or "contains",
        review_state=edge.review_state.strip().lower() or "approved",
        confidence=round(max(0.0, min(1.0, float(edge.confidence))), 2),
        source=edge.source,
    )


def _edge_from_mapping(record: dict[str, Any]) -> RealEstateTargetEdgeRule:
    from_target_type = str(record.get("fromTargetType") or record.get("from_target_type") or "").strip()
    from_target_id = str(record.get("fromTargetId") or record.get("from_target_id") or "").strip()
    to_target_type = str(record.get("toTargetType") or record.get("to_target_type") or "").strip()
    to_target_id = str(record.get("toTargetId") or record.get("to_target_id") or "").strip()
    if not from_target_type or not from_target_id or not to_target_type or not to_target_id:
        raise ValueError("target edge requires fromTargetType, fromTargetId, toTargetType, and toTargetId")
    return RealEstateTargetEdgeRule(
        from_target_type=from_target_type,
        from_target_id=from_target_id,
        to_target_type=to_target_type,
        to_target_id=to_target_id,
        edge_type=str(record.get("edgeType") or record.get("edge_type") or "contains").strip().lower() or "contains",
        review_state=str(record.get("reviewState") or record.get("review_state") or "approved").strip().lower(),
        confidence=round(_float(record.get("confidence"), default=1.0), 2),
        source=str(record.get("source")).strip() if record.get("source") else None,
    )


def _load_json_records(path: str | Path) -> list[dict[str, Any]]:
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
        raise ValueError("target edge input must be JSON array, {items: []}, or JSONL")
    return [record for record in records if isinstance(record, dict)]


def _rollup_confidence(value: float | None, factor: float) -> float | None:
    if value is None:
        return None
    return round(max(0.0, min(1.0, value * factor)), 2)


def _confidence_rank(value: float | None) -> float:
    if value is None:
        return -1.0
    return value


def _float(value: object, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
