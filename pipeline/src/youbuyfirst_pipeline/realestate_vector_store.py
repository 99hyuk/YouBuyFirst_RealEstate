from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any

import httpx

from youbuyfirst_pipeline.realestate_reactions import parse_reaction_datetime
from youbuyfirst_pipeline.realestate_similarity import (
    primary_market_flow_label,
    summarize_after_market_facts,
)


DEFAULT_QDRANT_COLLECTION = "realestate_reaction_windows"
DEFAULT_QDRANT_DISTANCE = "Cosine"


class QdrantRealEstateVectorStoreClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        collection_name: str = DEFAULT_QDRANT_COLLECTION,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not base_url.strip():
            raise ValueError("Qdrant base_url is required")
        self.base_url = base_url.rstrip("/")
        self.api_key = (api_key or "").strip()
        self.collection_name = collection_name.strip() or DEFAULT_QDRANT_COLLECTION
        self.timeout_seconds = timeout_seconds

    def ensure_collection(self, *, vector_size: int, distance: str = DEFAULT_QDRANT_DISTANCE) -> dict[str, Any]:
        if vector_size <= 0:
            raise ValueError("vector_size must be positive")
        return self._request(
            "PUT",
            f"/collections/{self.collection_name}",
            json={"vectors": {"size": vector_size, "distance": distance}},
        )

    def upsert_points(self, points: list[dict[str, Any]]) -> dict[str, Any]:
        if not points:
            return {"result": {"operation_id": None}}
        return self._request(
            "PUT",
            f"/collections/{self.collection_name}/points",
            json={"points": points},
        )

    def search(
        self,
        *,
        vector: list[float],
        top_n: int,
        exclude_input_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if top_n <= 0:
            raise ValueError("top_n must be positive")
        payload: dict[str, Any] = {
            "vector": vector,
            "limit": top_n,
            "with_payload": True,
        }
        if exclude_input_id:
            payload["filter"] = {
                "must_not": [
                    {
                        "key": "inputId",
                        "match": {"value": exclude_input_id},
                    }
                ]
            }
        response = self._request("POST", f"/collections/{self.collection_name}/points/search", json=payload)
        result = response.get("result")
        return result if isinstance(result, list) else []

    def _request(self, method: str, path: str, *, json: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.request(method, f"{self.base_url}{path}", headers=headers, json=json)
            response.raise_for_status()
            return response.json()


def load_real_estate_embedding_payloads(path: str | Path) -> list[dict[str, Any]]:
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
        raise ValueError("embedding payload must be a JSON array, {items: []}, object, or JSONL")
    return [_normalize_embedding_item(record) for record in records if isinstance(record, dict)]


def build_qdrant_points(embedding_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points = []
    for item in embedding_items:
        embedding = item["embedding"]
        payload = {key: value for key, value in item.items() if key != "embedding"}
        points.append(
            {
                "id": _point_id(item["inputId"]),
                "vector": embedding,
                "payload": payload,
            }
        )
    return points


def qdrant_search_results_to_similar_windows(
    *,
    source_input: dict[str, Any],
    search_results: list[dict[str, Any]],
    market_facts: list[dict[str, Any]] | None = None,
    horizon_days: int | None = None,
) -> list[dict[str, Any]]:
    source_target_id = str(source_input.get("targetId") or "").strip()
    source_window_start = _window_start(source_input) or "unknown"
    items = []
    for result in search_results:
        payload = result.get("payload") if isinstance(result, dict) else None
        if not isinstance(payload, dict):
            continue
        score = round(float(result.get("score") or 0.0), 4)
        matched_target_id = str(payload.get("targetId") or "unknown").strip() or "unknown"
        ref_id = str(payload.get("refId") or result.get("id") or _stable_id("qdrant", matched_target_id)).strip()
        matched_window_start = _window_start(payload) or "unknown"
        matched_window_end = _window_end(payload) or "unknown"
        if not _is_past_window(source_window_start, matched_window_start):
            continue
        text = str(payload.get("text") or "").strip()
        after_market_summary = {"horizonDays": None, "items": []}
        caveat = "market_fact_not_joined"
        if market_facts is not None:
            after_market_summary = summarize_after_market_facts(
                target_id=matched_target_id,
                window_end=matched_window_end,
                market_facts=market_facts,
                horizon_days=horizon_days or 90,
            )
            caveat = None if after_market_summary["items"] else "market_fact_missing"
        value_text = f"유사도 {score * 100:.1f}%"
        market_flow = primary_market_flow_label(after_market_summary)
        if market_flow:
            value_text = f"{value_text} · {market_flow}"
        elif text:
            value_text = f"{value_text} · {text[:80]}"
        items.append(
            {
                "sourceTargetId": source_target_id,
                "sourceWindowStart": source_window_start,
                "matchedTargetId": matched_target_id,
                "matchedWindowStart": matched_window_start,
                "matchedWindowEnd": matched_window_end,
                "similarityScore": score,
                "matchReason": "qdrant:cosine",
                "issueOverlap": [],
                "afterMarketSummary": after_market_summary,
                "caveat": caveat,
                "evidenceItem": {
                    "evidenceItemId": _stable_id("similar-window", source_target_id, matched_target_id, ref_id),
                    "evidenceType": "similar_window",
                    "refType": "similar_window",
                    "refId": ref_id,
                    "label": "유사 과거 window",
                    "valueText": value_text,
                    "severity": "info",
                },
            }
        )
    return items


def find_embedding_by_input_id(items: list[dict[str, Any]], input_id: str) -> dict[str, Any]:
    normalized = input_id.strip()
    for item in items:
        if item.get("inputId") == normalized:
            return item
    raise ValueError(f"embedding input not found: {normalized}")


def _normalize_embedding_item(record: dict[str, Any]) -> dict[str, Any]:
    embedding = record.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("embedding item requires non-empty embedding")
    normalized_embedding = [float(value) for value in embedding]
    input_id = str(record.get("inputId") or record.get("input_id") or "").strip()
    if not input_id:
        raise ValueError("embedding item requires inputId")
    return {
        "inputId": input_id,
        "targetType": str(record.get("targetType") or record.get("target_type") or "").strip(),
        "targetId": str(record.get("targetId") or record.get("target_id") or "").strip(),
        "refType": str(record.get("refType") or record.get("ref_type") or "").strip(),
        "refId": str(record.get("refId") or record.get("ref_id") or input_id).strip(),
        "provider": str(record.get("provider") or "").strip(),
        "modelName": str(record.get("modelName") or record.get("model_name") or "").strip(),
        "text": str(record.get("text") or "").strip(),
        "embedding": normalized_embedding,
        "dimensions": int(record.get("dimensions") or len(normalized_embedding)),
        "dataStatus": str(record.get("dataStatus") or record.get("data_status") or "generated").strip(),
        **_optional_window_fields(record),
    }


def _optional_window_fields(record: dict[str, Any]) -> dict[str, Any]:
    fields = {}
    for output_key, *input_keys in (
        ("windowStart", "windowStart", "window_start"),
        ("windowEnd", "windowEnd", "window_end"),
        ("asOf", "asOf", "as_of"),
    ):
        for key in input_keys:
            value = record.get(key)
            if value:
                fields[output_key] = str(value)
                break
    return fields


def _window_start(item: dict[str, Any]) -> str | None:
    explicit = str(item.get("windowStart") or item.get("window_start") or "").strip()
    if explicit:
        return explicit
    return _window_part_from_input_id(item, index=2)


def _window_end(item: dict[str, Any]) -> str | None:
    explicit = str(item.get("windowEnd") or item.get("window_end") or "").strip()
    if explicit:
        return explicit
    return _window_part_from_input_id(item, index=3)


def _window_part_from_input_id(item: dict[str, Any], *, index: int) -> str | None:
    input_id = str(item.get("inputId") or item.get("input_id") or "").strip()
    window_parts = _window_parts_from_input_id(input_id)
    if index == 2:
        return window_parts.get("windowStart")
    if index == 3:
        return window_parts.get("windowEnd")
    return None


def _window_parts_from_input_id(input_id: str) -> dict[str, str]:
    prefix = "reaction-window:"
    if not input_id.startswith(prefix):
        return {}
    _, _, window_blob = input_id[len(prefix) :].partition(":")
    if not window_blob:
        return {}
    if "Z:" in window_blob:
        window_start, window_end = window_blob.split("Z:", 1)
        return {"windowStart": f"{window_start}Z", "windowEnd": window_end}
    return {}


def _is_past_window(source_window_start: str, matched_window_start: str) -> bool:
    if source_window_start == "unknown" or matched_window_start == "unknown":
        return True
    try:
        return parse_reaction_datetime(matched_window_start) < parse_reaction_datetime(source_window_start)
    except (TypeError, ValueError):
        return True


def _point_id(input_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"youbuyfirst-realestate:{input_id.strip()}"))


def _stable_id(*parts: str) -> str:
    raw = "-".join(str(part or "").strip() for part in parts)
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:120] or hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
