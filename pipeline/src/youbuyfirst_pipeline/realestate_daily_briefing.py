from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import httpx

from youbuyfirst_pipeline.realestate_llm_evaluation import DEFAULT_GMS_OPENAI_BASE_URL


DEFAULT_GMS_ANTHROPIC_BASE_URL = "https://gms.ssafy.io/gmsapi/api.anthropic.com/v1"
DEFAULT_DAILY_BRIEFING_MODEL = "claude-opus-4-8"
DEFAULT_DAILY_BRIEFING_PROMPT_VERSION = "daily-briefing-v1"
REQUIRED_SECTION_TITLES = (
    "오늘의 핵심 흐름",
    "주목할 지역과 이유",
    "시장 변수",
    "관련 뉴스·리포트",
)
INTERNAL_LENSES = (
    ("new_variables", "새 변수"),
    ("repeated_flow", "반복 흐름"),
    ("accumulated_direction", "누적 방향"),
    ("regional_importance", "지역 중요도"),
)
FORBIDDEN_TIME_WINDOW_LABELS = ("24시간", "7일", "1개월", "3개월")
FORBIDDEN_BRIEFING_COPY = (
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
FORBIDDEN_BRIEFING_STYLE_COPY = (
    "관망 심리",
    "속으로 부글",
    "부글거",
    "모습을 보인다",
    "관전 포인트",
    "부상하고 있다",
    "자극하면서",
)
DEFAULT_HEADLINES = (
    "주요 시장 변수 점검",
    "수도권 지역 흐름 확인",
    "정책·공급 이슈 관찰",
)
MIN_COLUMN_BODY_CHARACTERS = 650
TARGET_COLUMN_BODY_CHARACTERS = 900
MIN_SECTION_BODY_CHARACTERS = {
    "오늘의 핵심 흐름": 170,
    "주목할 지역과 이유": 80,
    "시장 변수": 50,
    "관련 뉴스·리포트": 70,
}
SHORT_TERM_MAP_PERIODS = ("week", "weekly", "1w", "month", "monthly", "1m")


class GmsOpenAIChatDailyBriefingClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_GMS_OPENAI_BASE_URL,
        model_name: str = DEFAULT_DAILY_BRIEFING_MODEL,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GMS api key is required")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name.strip() or DEFAULT_DAILY_BRIEFING_MODEL
        self.timeout_seconds = timeout_seconds

    def generate(self, input_pack: dict[str, Any]) -> dict[str, Any]:
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
                    "content": json.dumps(input_pack, ensure_ascii=False),
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


class GmsAnthropicMessagesDailyBriefingClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_GMS_ANTHROPIC_BASE_URL,
        model_name: str = DEFAULT_DAILY_BRIEFING_MODEL,
        timeout_seconds: float = 60.0,
        max_tokens: int = 8192,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GMS api key is required")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name.strip() or DEFAULT_DAILY_BRIEFING_MODEL
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens

    def generate(self, input_pack: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "system": _developer_prompt(),
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "아래 입력팩만 근거로 JSON object만 반환하세요. "
                        "마크다운 코드블록이나 설명 문장은 넣지 마세요.\n"
                        f"{json.dumps(input_pack, ensure_ascii=False)}"
                    ),
                }
            ],
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return _parse_anthropic_message_json(data)


def build_daily_briefing_input_pack(
    *,
    generated_at: datetime,
    market_facts: Iterable[dict[str, Any]] | None = None,
    map_targets: Iterable[dict[str, Any]] | None = None,
    content_items: Iterable[dict[str, Any]] | None = None,
    curated_items: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    generated_at = _aware_utc(generated_at)
    source_items = [_source_item_from_curated(item, idx) for idx, item in enumerate(curated_items or [], start=1)]
    candidates: list[dict[str, Any]] = []
    candidates.extend(_candidates_from_curated(curated_items or []))
    candidates.extend(_candidates_from_content_items(content_items or []))
    candidates.extend(_candidates_from_market_facts(market_facts or []))
    candidates.extend(_candidates_from_map_targets(map_targets or []))
    candidates = sorted(
        [candidate for candidate in candidates if candidate.get("title")],
        key=lambda candidate: float(candidate.get("importance") or 0.5),
        reverse=True,
    )

    return {
        "briefingDate": generated_at.date().isoformat(),
        "generatedAt": generated_at.isoformat().replace("+00:00", "Z"),
        "analysisLenses": [
            {
                "id": lens_id,
                "label": label,
                "usage": "internal_only",
            }
            for lens_id, label in INTERNAL_LENSES
        ],
        "writingRules": {
            "presentation": "하나의 자연스러운 시장 브리핑",
            "dashboard": "summaryHeadlines exactly 3, short noun-style Korean headlines",
            "tone": "건조한 금융권 리서치 브리프",
            "structure": "core flow carries the detailed thesis; regions and variables stay concise",
            "minimumBodyCharacters": MIN_COLUMN_BODY_CHARACTERS,
            "targetBodyCharacters": TARGET_COLUMN_BODY_CHARACTERS,
            "sectionBodyMinimums": MIN_SECTION_BODY_CHARACTERS,
            "sectionStyle": {
                "오늘의 핵심 흐름": "4-6 sentences, detailed interpretation",
                "주목할 지역과 이유": "2-3 concise sentences, short-term region signal only",
                "시장 변수": "2-3 concise sentences, key variables only",
                "관련 뉴스·리포트": "1-2 concise sentences, source trail only",
            },
            "avoidSectionLabels": "explicit_time_window_titles",
            "excludeTopics": ["데이터 부족", "공개 지연"],
            "forbiddenActionCopy": list(FORBIDDEN_BRIEFING_COPY),
            "forbiddenStyleCopy": list(FORBIDDEN_BRIEFING_STYLE_COPY),
            "avoid": "기사 제목 단순 나열, 지역 순위 복붙, 후보 목록 요약, 감정적 기사체, 투자 행동 권유",
        },
        "requiredSections": list(REQUIRED_SECTION_TITLES),
        "candidates": candidates[:80],
        "sourceItems": source_items[:30],
    }


def load_daily_briefing_curated_pack(path: str | Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    pack_path = Path(path)
    if not pack_path.exists():
        raise FileNotFoundError(pack_path)
    text = pack_path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if pack_path.suffix.lower() == ".jsonl":
        return [
            item
            for line in text.splitlines()
            if line.strip()
            for item in [_as_dict(json.loads(line))]
            if item
        ]
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        items = parsed.get("items") or parsed.get("sourceItems") or parsed.get("candidates") or []
        return [item for item in items if isinstance(item, dict)]
    return []


def apply_daily_briefing_llm_generation(
    input_pack: dict[str, Any],
    generation: dict[str, Any],
    *,
    model_name: str,
    prompt_version: str = DEFAULT_DAILY_BRIEFING_PROMPT_VERSION,
) -> dict[str, Any]:
    title = _text(generation.get("title")) or "오늘의 부동산 시장 브리핑"
    headlines = [_text(value) for value in generation.get("summaryHeadlines") or []]
    headlines = [value for value in headlines if value]
    if len(headlines) != 3:
        raise ValueError("daily briefing generation must include exactly three summaryHeadlines")
    candidates = [candidate for candidate in input_pack.get("candidates", []) if isinstance(candidate, dict)]
    sections = _normalized_sections(generation.get("sections") or [], _rule_based_sections(candidates))
    source_items = _normalized_source_items(
        generation.get("sourceItems") or input_pack.get("sourceItems") or [],
        candidates,
    )
    focus_regions = _normalized_focus_regions(
        generation.get("focusRegions") or [],
        candidates,
    )
    _validate_output_copy(title, headlines, sections, extra_values=_raw_section_copy_values(generation.get("sections") or []))

    briefing_date = _text(input_pack.get("briefingDate"))
    generated_at = _text(input_pack.get("generatedAt"))
    if not briefing_date or not generated_at:
        raise ValueError("daily briefing input pack requires briefingDate and generatedAt")

    return {
        "briefingId": f"daily-briefing-{briefing_date.replace('-', '')}-{_version_suffix(prompt_version)}",
        "briefingDate": briefing_date,
        "title": title,
        "summaryHeadlines": headlines,
        "sections": sections,
        "focusRegions": focus_regions,
        "modelName": model_name,
        "promptVersion": prompt_version,
        "generatedAt": generated_at,
        "sourceItems": source_items,
    }


def build_rule_based_daily_briefing(
    input_pack: dict[str, Any],
    *,
    model_name: str = "rule-based",
    prompt_version: str = DEFAULT_DAILY_BRIEFING_PROMPT_VERSION,
) -> dict[str, Any]:
    candidates = [candidate for candidate in input_pack.get("candidates", []) if isinstance(candidate, dict)]
    candidate_titles = [_noun_headline(candidate.get("title")) for candidate in candidates]
    headlines = _dedupe([title for title in candidate_titles if title])
    for fallback in DEFAULT_HEADLINES:
        if len(headlines) >= 3:
            break
        if fallback not in headlines:
            headlines.append(fallback)
    generated = {
        "title": "오늘의 부동산 시장 브리핑",
        "summaryHeadlines": headlines[:3],
        "sections": _rule_based_sections(candidates),
        "focusRegions": _rule_based_focus_regions(candidates),
        "sourceItems": input_pack.get("sourceItems", []),
    }
    return apply_daily_briefing_llm_generation(
        input_pack,
        generated,
        model_name=model_name,
        prompt_version=prompt_version,
    )


def _developer_prompt() -> str:
    return (
        "너는 부동산 시장 브리핑 작성자다. 입력팩의 후보와 출처만 사용해 JSON object를 작성한다. "
        "출력 필드는 title, summaryHeadlines, sections, focusRegions, sourceItems다. "
        "summaryHeadlines는 대시보드에 그대로 보이는 짧은 명사형 한국어 헤드라인 3개다. "
        "sections는 오늘의 핵심 흐름, 주목할 지역과 이유, 시장 변수, 관련 뉴스·리포트 네 제목으로 쓴다. "
        "sections는 반드시 배열 또는 위 네 제목을 key로 둔 object로 쓰고, 네 섹션을 모두 포함한다. "
        "본문은 건조한 금융권 리서치 브리프처럼 쓴다. 감정적 기사체, 은유, 시장 의인화, 과장 표현을 쓰지 않는다. "
        "오늘의 핵심 흐름 섹션에만 자세한 논지를 싣고, 주목할 지역과 이유 및 시장 변수 섹션은 2-3문장으로 간결하게 쓴다. "
        "기사 제목이나 지역명을 단순 나열하지 말고, 단기 지역 신호는 1년 누적 변화율이 아니라 입력팩의 short-term period 신호를 우선한다. "
        "관망 심리, 속으로 부글거린다, 모습을 보인다, 관전 포인트 같은 표현은 절대 쓰지 않는다. "
        f"sections body 전체는 가능하면 {TARGET_COLUMN_BODY_CHARACTERS}자 이상, 최소 {MIN_COLUMN_BODY_CHARACTERS}자 이상이어야 한다. "
        "sourceItems는 시장 전체 흐름, 지역 흐름, 정책, 공급, 전세, 공식 지표와 직접 관련된 근거만 골라 쓴다. "
        "sourceItems는 candidateId/sourceItemId를 보존하고 가능한 원문 URL, 출처 domain 또는 sourceLabel을 포함한다. "
        "기간을 쪼갠 제목을 화면 문구처럼 쓰지 않는다. "
        "데이터 부족, 공개 지연은 이번 브리핑 본문에서 제외한다. "
        "매수, 매도, 청약, 대출 행동을 권유하거나 가격 상승을 단정하지 않는다."
    )


def _candidates_from_curated(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        title = _text(item.get("title") or item.get("headline") or item.get("label"))
        if not title:
            continue
        candidates.append(
            {
                "candidateId": _text(item.get("candidateId") or item.get("sourceItemId")) or f"curated-{index}",
                "lens": _lens(item.get("lens"), default="new_variables"),
                "title": title,
                "summary": _text(item.get("summary") or item.get("snippet") or item.get("reason")),
                "targetId": _text(item.get("targetId")),
                "sourceType": _text(item.get("sourceType")) or "curated",
                "sourceId": _text(item.get("sourceId")),
                "domain": _text(item.get("domain")),
                "sourceLabel": _source_label(item),
                "url": _source_url(item),
                "importance": _importance(item.get("importance"), 0.8),
            }
        )
    return candidates


def _candidates_from_content_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        title = _text(item.get("title"))
        if not title:
            continue
        if _is_low_signal_briefing_content(title, _text(item.get("contentType"))):
            continue
        candidates.append(
            {
                "candidateId": _text(item.get("contentId")) or f"content-{index}",
                "lens": "new_variables",
                "title": title,
                "summary": _text(item.get("snippet") or item.get("metricLabel")),
                "targetId": _text(item.get("targetId")),
                "sourceType": _text(item.get("contentType")) or "content",
                "sourceId": _text(item.get("sourceId")),
                "domain": _text(item.get("domain")),
                "sourceLabel": _source_label(item),
                "url": _source_url(item),
                "publishedAt": _text(item.get("publishedAt")),
                "importance": 0.75,
            }
        )
    return candidates


def _candidates_from_market_facts(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        value_json = item.get("valueJson") if isinstance(item.get("valueJson"), dict) else {}
        title = _text(
            value_json.get("label")
            or value_json.get("regionName")
            or value_json.get("name")
            or item.get("factType")
        )
        if not title:
            continue
        candidates.append(
            {
                "candidateId": _text(item.get("providerObjectId")) or f"market-fact-{index}",
                "lens": "accumulated_direction",
                "title": title,
                "summary": _market_fact_summary(item, value_json),
                "targetId": _text(item.get("targetId")),
                "sourceType": "market_fact",
                "provider": _text(item.get("provider")),
                "sourceLabel": _text(item.get("provider")),
                "asOf": _text(item.get("asOf") or item.get("observedAt")),
                "importance": 0.65,
            }
        )
    return candidates


def _candidates_from_map_targets(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        display_name = _text(item.get("displayName") or item.get("name") or item.get("targetId"))
        if not display_name:
            continue
        period, change_pct = _short_term_change_pct(item.get("periods"))
        candidates.append(
            {
                "candidateId": _text(item.get("targetId")) or f"map-target-{index}",
                "lens": "regional_importance",
                "title": f"{display_name} 지역 흐름",
                "summary": "" if change_pct is None else f"단기 변화율 {change_pct:+.2f}%",
                "targetId": _text(item.get("targetId")),
                "sourceType": "map_layer",
                "sourceLabel": "전국 지역 지도",
                "period": period,
                "importance": 0.7 + min(abs(change_pct or 0) / 10, 0.2),
            }
        )
    return candidates


def _source_item_from_curated(item: dict[str, Any], display_order: int) -> dict[str, Any]:
    return {
        "sourceItemId": _text(item.get("sourceItemId") or item.get("candidateId")) or f"curated-source-{display_order}",
        "sourceType": _text(item.get("sourceType")) or "curated",
        "refId": _text(item.get("refId") or item.get("contentId")),
        "label": _source_label(item) or "참고 자료",
        "title": _text(item.get("title") or item.get("headline") or item.get("label")) or "참고 자료",
        "url": _source_url(item),
        "displayOrder": display_order,
    }


def _normalized_sections(
    values: Iterable[object] | Mapping[str, object],
    fallback_sections: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if isinstance(values, Mapping):
        values = [
            {
                "title": title,
                "body": body,
                "displayOrder": index,
            }
            for index, (title, body) in enumerate(values.items(), start=1)
        ]
    sections = []
    for index, raw in enumerate(values, start=1):
        if not isinstance(raw, dict):
            continue
        section = {
            "sectionId": _text(raw.get("sectionId")) or _section_id_from_title(raw.get("title"), index),
            "title": _text(raw.get("title")),
            "body": _text(raw.get("body")),
            "displayOrder": int(raw.get("displayOrder") or index),
        }
        if section["title"] and section["body"]:
            sections.append(section)
    by_title = {}
    for section in sections:
        by_title.setdefault(section["title"], section)
    fallback_by_title = {
        _text(section.get("title")): section
        for section in (fallback_sections or [])
        if isinstance(section, dict) and _text(section.get("title")) and _text(section.get("body"))
    }
    canonical_sections = []
    for index, title in enumerate(REQUIRED_SECTION_TITLES, start=1):
        section = by_title.get(title) or fallback_by_title.get(title)
        if section:
            canonical_sections.append(
                {
                    "sectionId": _text(section.get("sectionId")) or _section_id_from_title(title, index),
                    "title": title,
                    "body": _text(section.get("body")),
                    "displayOrder": index,
                }
            )
    titles = [section["title"] for section in canonical_sections]
    if any(title not in titles for title in REQUIRED_SECTION_TITLES):
        raise ValueError("daily briefing generation must include all required narrative sections")
    return canonical_sections


def _normalized_source_items(
    values: Iterable[object],
    candidates: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidate_by_id = _candidates_by_id(candidates or [])
    source_items = []
    for index, raw in enumerate(values, start=1):
        if not isinstance(raw, dict):
            continue
        raw_id = _text(
            raw.get("sourceItemId")
            or raw.get("candidateId")
            or raw.get("contentId")
            or raw.get("refId")
        )
        candidate = candidate_by_id.get(raw_id, {})
        title = _text(raw.get("title") or raw.get("label") or candidate.get("title"))
        if not title:
            continue
        source_items.append(
            {
                "sourceItemId": raw_id or f"source-{index}",
                "sourceType": _text(raw.get("sourceType") or raw.get("contentType") or candidate.get("sourceType")) or "content",
                "refId": _text(raw.get("refId") or raw.get("contentId") or candidate.get("candidateId")),
                "label": _source_label(raw, candidate),
                "title": title,
                "url": _source_url(raw) or _text(candidate.get("url")),
                "displayOrder": int(raw.get("displayOrder") or index),
            }
        )
    return source_items


def _normalized_focus_regions(
    values: Iterable[object],
    candidates: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    label_by_target_id = {
        _text(candidate.get("targetId")): _text(candidate.get("title"))
        for candidate in (candidates or [])
        if isinstance(candidate, dict)
        and _text(candidate.get("targetId"))
        and _text(candidate.get("title"))
    }
    regions = []
    for index, raw in enumerate(values, start=1):
        if not isinstance(raw, dict):
            continue
        target_id = _text(raw.get("targetId") or raw.get("id") or raw.get("candidateId"))
        label = _text(
            raw.get("label")
            or raw.get("displayName")
            or raw.get("name")
            or label_by_target_id.get(target_id)
            or target_id
        )
        if not label:
            continue
        regions.append(
            {
                "targetId": target_id,
                "label": label,
                "reason": _text(raw.get("reason") or raw.get("summary")),
                "displayOrder": int(raw.get("displayOrder") or index),
            }
        )
    return regions


def _rule_based_sections(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = {lens_id: [] for lens_id, _label in INTERNAL_LENSES}
    for candidate in candidates:
        grouped.setdefault(candidate.get("lens") or "new_variables", []).append(candidate)
    return [
        {
            "sectionId": "flow",
            "title": "오늘의 핵심 흐름",
            "body": _column_body_from_candidates(
                [*grouped.get("new_variables", []), *grouped.get("repeated_flow", [])],
                lead="오늘의 핵심은 새로 붙은 변수와 반복되는 흐름이 같은 방향으로 읽히는지 확인하는 데 있습니다.",
                interpretation="단기 뉴스만 보면 각각의 사건처럼 보이지만, 부동산 시장에서는 정책 기대, 전세 부담, 거래 대기 수요가 함께 묶일 때 체감 방향이 만들어집니다.",
                implication="따라서 이번 브리핑은 특정 지역의 가격 방향을 단정하기보다 어떤 재료가 반복되고 어디에서 수급 압력으로 이어지는지 확인하는 관찰 노트로 읽는 편이 적절합니다.",
            ),
        },
        {
            "sectionId": "regions",
            "title": "주목할 지역과 이유",
            "body": _column_body_from_candidates(
                grouped.get("regional_importance", []),
                lead="지역별로는 수도권 주요 생활권과 전국 단위 예외 신호가 있는 권역을 나눠 봐야 합니다.",
                interpretation="같은 변화율이라도 서울 핵심권, 경기 외곽, 지방 광역시가 의미하는 수요의 성격은 다릅니다.",
                implication="주목 지역은 순위 자체보다 왜 관심이 붙었는지, 그 이유가 거래·전세·공급 중 어디에서 반복되는지 확인할 때 해석력이 생깁니다.",
            ),
        },
        {
            "sectionId": "variables",
            "title": "시장 변수",
            "body": _column_body_from_candidates(
                grouped.get("accumulated_direction", []),
                lead="시장 변수는 정책, 전세, 거래, 공급이 따로 움직이는지 아니면 같은 방향으로 누적되는지에 달려 있습니다.",
                interpretation="세제나 대출 같은 정책 이슈는 매물 의사결정과 임대 기대를 바꿀 수 있고, 공급 일정은 그 압력을 완충하거나 키울 수 있습니다.",
                implication="핵심은 변수를 하나씩 나열하는 것이 아니라 어떤 조합이 특정 생활권의 체감 압력으로 연결되는지 점검하는 것입니다.",
            ),
        },
        {
            "sectionId": "sources",
            "title": "관련 뉴스·리포트",
            "body": _column_body_from_candidates(
                candidates,
                lead="관련 뉴스와 리포트는 오늘의 해석을 만든 재료로 연결됩니다.",
                interpretation="개별 기사 하나를 결론으로 삼기보다 여러 출처에서 정책, 전세, 공급, 지역 흐름이 반복해서 만나는 지점을 확인해야 합니다.",
                implication="아래 근거는 투자 행동을 지시하는 신호가 아니라 브리핑의 판단 재료를 검토하기 위한 출처 목록입니다.",
            ),
        },
    ]


def _rule_based_focus_regions(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    regions = []
    seen = set()
    for candidate in candidates:
        target_id = _text(candidate.get("targetId"))
        if not target_id or target_id in seen:
            continue
        seen.add(target_id)
        regions.append(
            {
                "targetId": target_id,
                "label": _text(candidate.get("title")),
                "reason": _text(candidate.get("summary")),
            }
        )
        if len(regions) >= 5:
            break
    return regions


def _column_body_from_candidates(
    candidates: list[dict[str, Any]],
    *,
    lead: str,
    interpretation: str,
    implication: str,
) -> str:
    signals = _candidate_signal_sentence(candidates)
    if signals:
        return f"{lead} 현재 확인되는 재료는 {signals}입니다. {interpretation} {implication}"
    return f"{lead} {interpretation} {implication}"


def _candidate_signal_sentence(candidates: list[dict[str, Any]]) -> str:
    pieces = []
    for candidate in candidates:
        title = _text(candidate.get("title"))
        summary = _text(candidate.get("summary"))
        if not title:
            continue
        if summary:
            pieces.append(f"{title}({summary})")
        else:
            pieces.append(title)
        if len(pieces) >= 3:
            break
    return ", ".join(_dedupe(pieces))


def _raw_section_copy_values(values: object) -> list[str]:
    if isinstance(values, Mapping):
        raw_values = []
        for title, body in values.items():
            raw_values.extend([_text(title), _text(body)])
        return raw_values
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        return []
    raw_values = []
    for raw in values:
        if isinstance(raw, dict):
            raw_values.extend([_text(raw.get("title")), _text(raw.get("body"))])
        else:
            raw_values.append(_text(raw))
    return raw_values


def _validate_output_copy(
    title: str,
    headlines: list[str],
    sections: list[dict[str, Any]],
    *,
    extra_values: Iterable[str] | None = None,
) -> None:
    values = [title, *headlines]
    for section in sections:
        values.append(_text(section.get("title")))
        values.append(_text(section.get("body")))
    values.extend([_text(value) for value in (extra_values or [])])
    joined = " ".join(values)
    if any(label in joined for label in FORBIDDEN_TIME_WINDOW_LABELS):
        raise ValueError("daily briefing output must not expose time-window labels")
    if any(word in joined for word in FORBIDDEN_BRIEFING_COPY):
        raise ValueError("daily briefing output includes forbidden action copy")
    if any(word in joined for word in FORBIDDEN_BRIEFING_STYLE_COPY):
        raise ValueError("daily briefing output includes overheated news-style copy")
    _validate_column_body(sections)


def _validate_column_body(sections: list[dict[str, Any]]) -> None:
    total_body_characters = sum(len(_text(section.get("body"))) for section in sections)
    if total_body_characters < MIN_COLUMN_BODY_CHARACTERS:
        raise ValueError("daily briefing output must include column-style body length")
    for section in sections:
        title = _text(section.get("title"))
        minimum = MIN_SECTION_BODY_CHARACTERS.get(title)
        if minimum and len(_text(section.get("body"))) < minimum:
            raise ValueError(f"daily briefing output must include column-style body for section: {title}")


def _market_fact_summary(item: dict[str, Any], value_json: dict[str, Any]) -> str:
    pieces = []
    for key in ("value", "changePct", "dealAmountManwon", "count", "unit"):
        value = value_json.get(key)
        if value is not None:
            pieces.append(f"{key}={value}")
    provider = _text(item.get("provider") or item.get("providerDataset"))
    if provider:
        pieces.append(f"provider={provider}")
    return ", ".join(pieces)


def _short_term_change_pct(periods: object) -> tuple[str | None, float | None]:
    if not isinstance(periods, dict):
        return None, None
    for period in SHORT_TERM_MAP_PERIODS:
        value = periods.get(period)
        if not isinstance(value, dict):
            continue
        change = value.get("changePct")
        if not isinstance(change, (int, float)):
            continue
        canonical_period = "week" if period in {"week", "weekly", "1w"} else "month"
        return canonical_period, float(change)
    return None, None


def _noun_headline(value: object) -> str:
    text = _text(value)
    for suffix in ("입니다", "합니다", "됩니다", "했습니다", "하고 있습니다", "관찰됩니다", "."):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text.strip()


def _section_id_from_title(value: object, index: int) -> str:
    title = _text(value)
    mapping = {
        "오늘의 핵심 흐름": "flow",
        "주목할 지역과 이유": "regions",
        "시장 변수": "variables",
        "관련 뉴스·리포트": "sources",
    }
    return mapping.get(title, f"section-{index}")


def _lens(value: object, *, default: str) -> str:
    normalized = _text(value)
    allowed = {lens_id for lens_id, _label in INTERNAL_LENSES}
    return normalized if normalized in allowed else default


def _importance(value: object, default: float) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(float(value), 1.0))
    return default


def _version_suffix(prompt_version: str) -> str:
    normalized = _text(prompt_version) or DEFAULT_DAILY_BRIEFING_PROMPT_VERSION
    suffix = normalized.rsplit("-", 1)[-1]
    return suffix if suffix.startswith("v") else "v1"


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


def _parse_anthropic_message_json(data: dict[str, Any]) -> dict[str, Any]:
    content_items = data.get("content")
    if not isinstance(content_items, list) or not content_items:
        raise ValueError("GMS Anthropic message response did not include content")
    text_parts = [
        item.get("text")
        for item in content_items
        if isinstance(item, dict)
        and item.get("type") == "text"
        and isinstance(item.get("text"), str)
    ]
    content = "\n".join(text_parts).strip()
    if not content:
        raise ValueError("GMS Anthropic message response did not include text content")
    parsed = json.loads(_strip_json_code_fence(content))
    if not isinstance(parsed, dict):
        raise ValueError("GMS Anthropic message content must be a JSON object")
    return parsed


def _strip_json_code_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _is_low_signal_briefing_content(title: str, source_type: str) -> bool:
    if source_type not in {"news", "content", ""}:
        return False
    personal_tokens = (
        "홍석현",
        "홍라희",
        "누나",
        "가족 부동산",
        "차입",
        "담보로 묶였다",
        "상속",
        "재산",
    )
    market_tokens = (
        "시장",
        "정책",
        "세제",
        "전세",
        "공급",
        "청약",
        "금리",
        "거래",
        "가격",
        "지수",
        "미분양",
        "입주",
        "재건축",
        "재개발",
        "부동산 시장",
    )
    personal_score = sum(1 for token in personal_tokens if token in title)
    market_score = sum(1 for token in market_tokens if token in title)
    return personal_score >= 2 and market_score <= 1


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _dedupe(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        normalized = _text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _as_dict(value: object) -> dict[str, Any]:
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _source_url(item: Mapping[str, Any]) -> str:
    return _text(
        item.get("canonicalUrl")
        or item.get("canonical_url")
        or item.get("resolvedUrl")
        or item.get("resolved_url")
        or item.get("originalUrl")
        or item.get("original_url")
        or item.get("sourceUrl")
        or item.get("source_url")
        or item.get("url")
    )


def _source_label(item: Mapping[str, Any], fallback: Mapping[str, Any] | None = None) -> str:
    fallback = fallback or {}
    return _text(
        item.get("label")
        or item.get("sourceLabel")
        or item.get("source_label")
        or item.get("domain")
        or item.get("sourceName")
        or item.get("source_name")
        or fallback.get("label")
        or fallback.get("sourceLabel")
        or fallback.get("domain")
        or fallback.get("sourceId")
        or item.get("sourceId")
        or item.get("sourceType")
        or item.get("contentType")
    )


def _candidates_by_id(candidates: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for key in ("candidateId", "sourceItemId", "contentId", "refId"):
            value = _text(candidate.get(key))
            if value:
                result.setdefault(value, candidate)
    return result
