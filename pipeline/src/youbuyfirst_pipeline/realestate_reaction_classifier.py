from __future__ import annotations

import json
from datetime import timezone
from pathlib import Path
from typing import Any, Iterable

from youbuyfirst_pipeline.realestate_matcher import (
    RealEstateMatchedPost,
    RealEstateTargetMention,
    parse_real_estate_match_datetime,
)
from youbuyfirst_pipeline.realestate_reactions import RealEstateReactionObservation


class RuleBasedRealEstateReactionClassifier:
    model = "rule-realestate-reaction-v1"

    def classify_post(self, post: RealEstateMatchedPost) -> list[RealEstateReactionObservation]:
        text = f"{post.title}\n{post.content_snippet}"
        direction, confidence = _classify_direction(text)
        issues = _classify_issues(text)
        if issues:
            direction, confidence = _direction_from_issues(direction, confidence, issues)

        return [
            RealEstateReactionObservation(
                target_type=mention.target_type,
                target_id=mention.target_id,
                published_at=post.published_at,
                source=post.source,
                reaction_direction=direction,
                issues=issues,
                external_id=post.external_id,
                matched_text=mention.matched_text,
                match_source=mention.match_source,
                confidence=confidence,
            )
            for mention in post.mentions
        ]


def classify_real_estate_reaction_observations(
    posts: Iterable[RealEstateMatchedPost],
    *,
    classifier: RuleBasedRealEstateReactionClassifier | None = None,
) -> list[RealEstateReactionObservation]:
    reaction_classifier = classifier or RuleBasedRealEstateReactionClassifier()
    observations: list[RealEstateReactionObservation] = []
    for post in posts:
        observations.extend(reaction_classifier.classify_post(post))
    return observations


def real_estate_reaction_observation_to_dict(observation: RealEstateReactionObservation) -> dict:
    payload = {
        "source": observation.source,
        "externalId": observation.external_id,
        "targetType": observation.target_type,
        "targetId": observation.target_id,
        "publishedAt": _iso(observation.published_at),
        "matchedText": observation.matched_text,
        "matchSource": observation.match_source,
        "reactionDirection": observation.reaction_direction,
        "confidence": observation.confidence,
        "issues": observation.issues,
    }
    return {key: value for key, value in payload.items() if value is not None}


def load_real_estate_matched_posts(path: str | Path) -> list[RealEstateMatchedPost]:
    records = _load_json_records(path)
    return [_matched_post_from_mapping(record) for record in records]


def _classify_direction(text: str) -> tuple[str, float]:
    expectation_hits = _keyword_hits(text, _EXPECTATION_KEYWORDS)
    concern_hits = _keyword_hits(text, _CONCERN_KEYWORDS)
    if expectation_hits > concern_hits:
        return "expectation", 0.65 + min(expectation_hits, 3) * 0.04
    if concern_hits > expectation_hits:
        return "concern", 0.65 + min(concern_hits, 3) * 0.04
    return "neutral", 0.55


def _direction_from_issues(
    fallback_direction: str,
    fallback_confidence: float,
    issues: list[dict[str, Any]],
) -> tuple[str, float]:
    directions = [issue.get("direction") for issue in issues]
    expectation_count = directions.count("expectation")
    concern_count = directions.count("concern")
    if expectation_count > concern_count:
        return "expectation", 0.73
    if concern_count > expectation_count:
        return "concern", round(max(fallback_confidence, 0.73 + concern_count * 0.03), 2)
    return fallback_direction, round(fallback_confidence, 2)


def _classify_issues(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for definition in _ISSUE_DEFINITIONS:
        if not any(keyword in text for keyword in definition["keywords"]):
            continue
        issues.append(
            {
                "issueKey": definition["issueKey"],
                "label": definition["label"],
                "direction": definition["direction"],
                "summary": definition["summary"],
                "confidence": 0.78,
            }
        )
    return issues


def _matched_post_from_mapping(record: dict[str, Any]) -> RealEstateMatchedPost:
    source = str(record.get("source") or "").strip()
    external_id = str(record.get("externalId") or record.get("external_id") or "").strip()
    published_at = record.get("publishedAt") or record.get("published_at")
    if not source or not external_id or not published_at:
        raise ValueError("matched post requires source, externalId, and publishedAt")

    return RealEstateMatchedPost(
        source=source,
        external_id=external_id,
        published_at=parse_real_estate_match_datetime(published_at),
        url=str(record.get("url")).strip() if record.get("url") else None,
        title=str(record.get("title") or "").strip(),
        content_snippet=str(record.get("contentSnippet") or record.get("content_snippet") or "").strip(),
        mentions=[
            _mention_from_mapping(mention)
            for mention in record.get("mentions", [])
            if isinstance(mention, dict)
        ],
    )


def _mention_from_mapping(record: dict[str, Any]) -> RealEstateTargetMention:
    return RealEstateTargetMention(
        target_type=str(record.get("targetType") or record.get("target_type") or "").strip(),
        target_id=str(record.get("targetId") or record.get("target_id") or "").strip(),
        matched_text=str(record.get("matchedText") or record.get("matched_text") or "").strip(),
        match_source=str(record.get("matchSource") or record.get("match_source") or "").strip(),
        confidence=round(_float(record.get("confidence"), default=0.5), 2),
        review_state=str(record.get("reviewState") or record.get("review_state") or "approved").strip(),
        alias_type=str(record.get("aliasType") or record.get("alias_type") or "official").strip(),
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
        raise ValueError("matched post input must be JSON array, {items: []}, or JSONL")
    return [record for record in records if isinstance(record, dict)]


def _keyword_hits(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _float(value: object, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _iso(value) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


_EXPECTATION_KEYWORDS = [
    "기대",
    "호재",
    "개선",
    "확정",
    "개통",
    "수혜",
    "역세권",
    "상승",
    "좋다",
    "좋아",
]

_CONCERN_KEYWORDS = [
    "우려",
    "불안",
    "악재",
    "부담",
    "규제",
    "하락",
    "폭락",
    "미분양",
    "공급과잉",
    "대출",
    "금리",
    "전세난",
]

_ISSUE_DEFINITIONS = [
    {
        "issueKey": "transport",
        "label": "교통",
        "direction": "expectation",
        "keywords": ["GTX", "지하철", "역세권", "교통", "개통", "노선", "철도"],
        "summary": "교통 호재와 접근성 기대가 함께 언급됨",
    },
    {
        "issueKey": "jeonse",
        "label": "전세",
        "direction": "concern",
        "keywords": ["전세", "역전세", "전세난", "보증금"],
        "summary": "전세 가격과 보증금 부담 우려가 언급됨",
    },
    {
        "issueKey": "loan_rate",
        "label": "대출·금리",
        "direction": "concern",
        "keywords": ["대출", "금리", "DSR", "이자", "상환"],
        "summary": "대출, 금리, 상환 부담 우려가 언급됨",
    },
    {
        "issueKey": "supply",
        "label": "공급",
        "direction": "concern",
        "keywords": ["미분양", "공급과잉", "입주폭탄", "물량 부담"],
        "summary": "공급 물량과 미분양 부담이 언급됨",
    },
    {
        "issueKey": "policy",
        "label": "정책",
        "direction": "concern",
        "keywords": ["규제", "정책", "토허제", "세금"],
        "summary": "정책과 규제 불확실성이 언급됨",
    },
    {
        "issueKey": "school",
        "label": "학군",
        "direction": "expectation",
        "keywords": ["학군", "초품아", "학교"],
        "summary": "학군과 교육 여건 기대가 언급됨",
    },
    {
        "issueKey": "redevelopment",
        "label": "재건축·재개발",
        "direction": "expectation",
        "keywords": ["재건축", "재개발", "정비구역"],
        "summary": "정비사업 기대가 언급됨",
    },
]
