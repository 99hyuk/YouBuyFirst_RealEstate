from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


DEFAULT_GMS_GEMINI_BASE_URL = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com"
DEFAULT_GMS_GEMINI_EMBEDDING_MODEL = "gemini-embedding-2"


@dataclass(frozen=True)
class RealEstateEmbeddingInput:
    input_id: str
    target_type: str
    target_id: str
    ref_type: str
    ref_id: str
    text: str
    provider: str = "gms:gemini"
    model_name: str = DEFAULT_GMS_GEMINI_EMBEDDING_MODEL

    def to_embedding_dict(self, embedding: list[float]) -> dict:
        return {
            "inputId": self.input_id,
            "targetType": self.target_type,
            "targetId": self.target_id,
            "refType": self.ref_type,
            "refId": self.ref_id,
            "provider": self.provider,
            "modelName": self.model_name,
            "text": self.text,
            "embedding": embedding,
            "dimensions": len(embedding),
            "dataStatus": "generated",
        }


class GmsGeminiEmbeddingClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_GMS_GEMINI_BASE_URL,
        model_name: str = DEFAULT_GMS_GEMINI_EMBEDDING_MODEL,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GMS api key is required")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name.strip() or DEFAULT_GMS_GEMINI_EMBEDDING_MODEL
        self.timeout_seconds = timeout_seconds

    def embed_text(self, text: str) -> list[float]:
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("text is required")

        endpoint = f"{self.base_url}/v1beta/models/{self.model_name}:embedContent"
        payload = {
            "content": {
                "parts": [
                    {
                        "text": normalized_text,
                    }
                ]
            }
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                endpoint,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return _parse_gemini_embedding(data)


def load_real_estate_embedding_inputs(path: str | Path) -> list[dict[str, Any]]:
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
        raise ValueError("embedding input must be JSON array, {items: []}, or JSONL")
    return [record for record in records if isinstance(record, dict)]


def build_real_estate_embedding_inputs(
    records: list[dict[str, Any]],
    *,
    model_name: str = DEFAULT_GMS_GEMINI_EMBEDDING_MODEL,
) -> list[RealEstateEmbeddingInput]:
    return [_embedding_input_from_reaction_snapshot(record, model_name=model_name) for record in records]


def _parse_gemini_embedding(data: dict[str, Any]) -> list[float]:
    embedding = data.get("embedding")
    values = embedding.get("values") if isinstance(embedding, dict) else None
    if not isinstance(values, list) or not values:
        raise ValueError("Gemini embedding response did not include embedding.values")
    return [float(value) for value in values]


def _embedding_input_from_reaction_snapshot(
    record: dict[str, Any],
    *,
    model_name: str,
) -> RealEstateEmbeddingInput:
    target_type = str(record.get("targetType") or record.get("target_type") or "").strip()
    target_id = str(record.get("targetId") or record.get("target_id") or "").strip()
    window_start = str(record.get("windowStart") or record.get("window_start") or "").strip()
    window_end = str(record.get("windowEnd") or record.get("window_end") or "").strip()
    if not target_type or not target_id or not window_start:
        raise ValueError("reaction snapshot embedding requires targetType, targetId, and windowStart")
    input_id = f"reaction-window:{target_id}:{window_start}"
    return RealEstateEmbeddingInput(
        input_id=input_id,
        target_type=target_type,
        target_id=target_id,
        ref_type="reaction_snapshot",
        ref_id=str(record.get("snapshotId") or record.get("id") or input_id),
        text=_reaction_snapshot_embedding_text(record, window_start=window_start, window_end=window_end),
        model_name=model_name,
    )


def _reaction_snapshot_embedding_text(record: dict[str, Any], *, window_start: str, window_end: str) -> str:
    target_id = str(record.get("targetId") or record.get("target_id") or "").strip()
    mention_count = _value(record, "mentionCount", "mention_count", default=0)
    expectation_score = _value(record, "expectationScore", "expectation_score", default=0)
    concern_score = _value(record, "concernScore", "concern_score", default=0)
    heat_score = _value(record, "heatScore", "heat_score", default=0)
    issue_text = "; ".join(_issue_text(issue) for issue in _issues(record) if _issue_text(issue))
    parts = [
        f"target {target_id}",
        f"window {window_start}~{window_end or 'unknown'}",
        f"언급 {mention_count}건",
        f"기대 {expectation_score}%",
        f"우려 {concern_score}%",
        f"heat {heat_score}",
    ]
    if issue_text:
        parts.append(f"쟁점 {issue_text}")
    return " | ".join(parts)


def _issues(record: dict[str, Any]) -> list[dict[str, Any]]:
    issues = record.get("issues") or record.get("issueMix") or []
    return [issue for issue in issues if isinstance(issue, dict)] if isinstance(issues, list) else []


def _issue_text(issue: dict[str, Any]) -> str:
    label = str(issue.get("label") or issue.get("issueKey") or issue.get("issue_key") or "").strip()
    summary = str(issue.get("summary") or "").strip()
    if label and summary:
        return f"{label}: {summary}"
    return label or summary


def _value(record: dict[str, Any], *keys: str, default: Any) -> Any:
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return default
