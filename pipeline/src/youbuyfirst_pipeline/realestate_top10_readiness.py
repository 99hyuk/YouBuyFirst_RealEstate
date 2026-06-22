from __future__ import annotations

from typing import Any


BROAD_REGION_TARGET_IDS = {
    "region-seoul",
    "region-busan",
    "region-daegu",
    "region-incheon",
    "region-gwangju",
    "region-daejeon",
    "region-ulsan",
    "region-sejong",
    "region-gyeonggi",
    "region-gangwon",
    "region-chungbuk",
    "region-chungnam",
    "region-jeonbuk",
    "region-jeonnam",
    "region-gyeongbuk",
    "region-gyeongnam",
    "region-jeju",
}


def build_real_estate_top10_readiness(client: Any, *, window_minutes: int = 10080, limit: int = 10) -> dict[str, Any]:
    required_items = max(1, int(limit or 0))
    aliases = client.list_real_estate_aliases(
        review_state="approved",
        ambiguous=False,
        target_type="complex",
    )
    edges = client.list_real_estate_target_edges(
        review_state="approved",
        edge_type="contains",
        direction="both",
    )
    complex_ranking = client.get_real_estate_reaction_ranking(
        target_type="complex",
        window_minutes=window_minutes,
        limit=limit,
    )
    region_ranking = client.get_real_estate_reaction_ranking(
        target_type="region",
        window_minutes=window_minutes,
        limit=limit,
    )

    complex_items = _items(complex_ranking)
    region_items = _items(region_ranking)
    complex_edges = [edge for edge in edges if _lower(edge.get("toTargetType")) == "complex"]
    complex_target_ids = {
        target_id
        for target_id in [
            *(_target_ids(aliases)),
            *(_target_ids(complex_edges, key="toTargetId")),
            *(_target_ids(complex_items)),
        ]
        if target_id
    }
    market_fact_target_ids = {
        target_id
        for target_id in complex_target_ids
        if target_id.startswith("complex-molit-")
    }
    market_fact_target_ids.update(
        target_id
        for target_id in _source_backed_target_ids(aliases, key="targetId", source_token="molit")
        if target_id
    )
    market_fact_target_ids.update(
        target_id
        for target_id in _source_backed_target_ids(complex_edges, key="toTargetId", source_token="molit")
        if target_id
    )
    community_target_ids = {
        target_id
        for target_id in _source_backed_target_ids(aliases, key="targetId", source_token="community")
        if target_id
    }
    community_target_ids.update(
        target_id
        for target_id in _source_backed_target_ids(complex_edges, key="toTargetId", source_token="community")
        if target_id
    )

    valid_complex_items = [
        item for item in complex_items if _lower(item.get("targetType")) == "complex"
    ]
    invalid_complex_rows = [
        str(item.get("targetId") or "")
        for item in complex_items
        if _lower(item.get("targetType")) != "complex"
    ]
    valid_region_items = [
        item
        for item in region_items
        if _lower(item.get("targetType")) in {"region", "living_area"}
    ]
    broad_region_rows = [
        str(item.get("targetId") or "")
        for item in region_items
        if str(item.get("targetId") or "") in BROAD_REGION_TARGET_IDS
    ]

    missing: list[str] = []
    if not complex_target_ids:
        missing.append("complex_registry_empty")
    if not aliases:
        missing.append("complex_alias_empty")
    if not complex_edges:
        missing.append("complex_region_edge_empty")
    if not market_fact_target_ids:
        missing.append("market_fact_backed_complex_empty")
    if not valid_complex_items:
        missing.append("complex_snapshot_empty")
    if not valid_region_items:
        missing.append("region_rollup_snapshot_empty")
    if valid_complex_items and len(valid_complex_items) < required_items:
        missing.append("complex_top10_short")
    if valid_region_items and not broad_region_rows and len(valid_region_items) < required_items:
        missing.append("region_top10_short")
    if invalid_complex_rows:
        missing.append("complex_ranking_contains_non_complex")
    if broad_region_rows:
        missing.append("region_ranking_contains_broad_sido")

    return {
        "status": "READY" if not missing else "PARTIAL",
        "missing": missing,
        "windowMinutes": window_minutes,
        "limit": limit,
        "complexRegistry": {
            "complexCount": len(complex_target_ids),
            "marketFactBackedComplexCount": len(market_fact_target_ids),
            "communityObservedComplexCount": len(community_target_ids),
            "aliasCount": len(aliases),
            "edgeCount": len(complex_edges),
        },
        "reactionSnapshots": {
            "complex": len(valid_complex_items),
            "region": len(valid_region_items),
        },
        "frontTop10": {
            "requiredItems": required_items,
            "complexItems": len(complex_items),
            "regionItems": len(region_items),
            "complexOnly": not invalid_complex_rows,
            "invalidComplexRows": invalid_complex_rows,
            "broadRegionRows": broad_region_rows,
            "complexSample": _sample_names(valid_complex_items),
            "regionSample": _sample_names(valid_region_items),
        },
    }


def _items(payload: object) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    items = payload.get("items", [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _target_ids(rows: list[dict], *, key: str = "targetId") -> list[str]:
    return [str(row.get(key) or "").strip() for row in rows]


def _source_backed_target_ids(rows: list[dict], *, key: str, source_token: str) -> list[str]:
    result = []
    for row in rows:
        source = _lower(row.get("source"))
        if source_token in source:
            result.append(str(row.get(key) or "").strip())
    return result


def _sample_names(rows: list[dict], *, limit: int = 5) -> list[dict[str, str]]:
    return [
        {
            "targetId": str(row.get("targetId") or ""),
            "displayName": str(row.get("displayName") or row.get("targetId") or ""),
        }
        for row in rows[:limit]
    ]


def _lower(value: object) -> str:
    return str(value or "").strip().lower()
