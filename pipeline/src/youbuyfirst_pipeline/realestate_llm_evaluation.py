from __future__ import annotations

import copy
import json
from typing import Any

import httpx


DEFAULT_GMS_OPENAI_BASE_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1"
DEFAULT_GMS_OPENAI_CHAT_MODEL = "gpt-5-mini"
DEFAULT_GMS_EVIDENCE_PROMPT_VERSION = "gms-evidence-v1"

FORBIDDEN_EVALUATION_COPY = (
    "사라",
    "팔아라",
    "청약 넣어라",
    "지금 들어가라",
    "오른다",
    "수익 보장",
    "확정 호재",
    "대출 받아라",
    "매수 기회",
    "매도 신호",
)

ALLOWED_TONES = {"watch", "caution", "mixed", "info"}


class GmsOpenAIChatEvaluationClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_GMS_OPENAI_BASE_URL,
        model_name: str = DEFAULT_GMS_OPENAI_CHAT_MODEL,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GMS api key is required")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name.strip() or DEFAULT_GMS_OPENAI_CHAT_MODEL
        self.timeout_seconds = timeout_seconds

    def evaluate(self, evidence_log: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.model_name,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "developer",
                    "content": _developer_prompt(),
                },
                {
                    "role": "user",
                    "content": json.dumps(_evaluation_context(evidence_log), ensure_ascii=False),
                },
            ],
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return _parse_chat_completion_json(data)


def apply_real_estate_llm_evaluation(
    evidence_log: dict[str, Any],
    evaluation: dict[str, Any],
    *,
    model_name: str,
    prompt_version: str = DEFAULT_GMS_EVIDENCE_PROMPT_VERSION,
) -> dict[str, Any]:
    updated = copy.deepcopy(evidence_log)
    updated["modelName"] = model_name
    updated["promptVersion"] = prompt_version

    summary = _text(evaluation.get("summary"))
    subtitle = _text(evaluation.get("subtitle"))
    tone = _text(evaluation.get("tone"))
    if _contains_forbidden_copy(f"{summary} {subtitle}"):
        updated["skipReason"] = "forbidden_copy_detected"
        updated["caveats"] = _dedupe([*updated.get("caveats", []), "forbidden_copy_detected"])
        return updated

    if summary:
        updated["summary"] = summary
    if subtitle:
        updated["subtitle"] = subtitle
    if tone in ALLOWED_TONES:
        updated["tone"] = tone
    return updated


def _developer_prompt() -> str:
    return (
        "너는 수요자 반응 기반 부동산 시장 해석 서비스의 분석 보조자다. "
        "입력 EvidenceLog의 근거만 사용해 JSON object로 답한다. "
        "필드는 tone, summary, subtitle만 포함한다. "
        "매수, 매도, 청약, 대출 같은 행동을 권유하지 않는다. "
        "사라, 팔아라, 청약 넣어라, 지금 들어가라, 오른다, 수익 보장, 확정 호재 같은 표현을 쓰지 않는다. "
        "가격 상승을 단정하지 말고 관찰, 분석, 근거 부족, stale 상태를 분리해서 표현한다."
    )


def _evaluation_context(evidence_log: dict[str, Any]) -> dict[str, Any]:
    return {
        "targetId": evidence_log.get("targetId"),
        "tone": evidence_log.get("tone"),
        "summary": evidence_log.get("summary"),
        "subtitle": evidence_log.get("subtitle"),
        "caveats": evidence_log.get("caveats", []),
        "dataQuality": evidence_log.get("dataQuality"),
        "confidence": evidence_log.get("confidence"),
        "asOf": evidence_log.get("asOf"),
        "evidenceItems": evidence_log.get("evidenceItems", []),
    }


def _parse_chat_completion_json(data: dict[str, Any]) -> dict[str, Any]:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("GMS chat completion response did not include choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("GMS chat completion response did not include message.content")
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("GMS chat completion content must be a JSON object")
    return parsed


def _contains_forbidden_copy(text: str) -> bool:
    return any(word in text for word in FORBIDDEN_EVALUATION_COPY)


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = _text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _text(value: object) -> str:
    return str(value or "").strip()
