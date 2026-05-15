from __future__ import annotations

import json
import os
from typing import Protocol

from youbuyfirst_pipeline.models import Mention, MentionDecision


class LLMProvider(Protocol):
    def resolve_mentions(self, title: str, content: str, mentions: list[Mention]) -> list[MentionDecision]:
        ...


class MockLLMProvider:
    model = "mock"

    def resolve_mentions(self, title: str, content: str, mentions: list[Mention]) -> list[MentionDecision]:
        text = f"{title} {content}".lower()
        reaction_direction, confidence, rationale = _mock_reaction(text)

        return [
            _mock_decision(mention, text, reaction_direction, confidence, rationale, self.model)
            for mention in mentions
        ]


class OpenAILLMProvider:
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def resolve_mentions(self, title: str, content: str, mentions: list[Mention]) -> list[MentionDecision]:
        if not mentions:
            return []

        mention_payload = [
            {
                "market": mention.market,
                "symbol": mention.symbol,
                "matchedText": mention.matched_text,
            }
            for mention in mentions
        ]
        candidate_keys = _candidate_keys(mentions)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You resolve Korean investing community post instrument candidates. "
                        "Use only the provided mentions. Mark isMentioned=false when the text is not actually "
                        "about that stock or ETF. Return JSON only. reactionDirection must be bullish, bearish, "
                        "or neutral."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "title": title,
                            "content": content[:1000],
                            "mentions": mention_payload,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "mention_resolution_batch",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "mentionDecisions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "market": {"type": "string"},
                                        "symbol": {"type": "string"},
                                        "matchedText": {"type": "string"},
                                        "isMentioned": {"type": "boolean"},
                                        "reactionDirection": {"type": "string", "enum": ["bullish", "bearish", "neutral"]},
                                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                        "rationale": {"type": "string"},
                                    },
                                    "required": [
                                        "market",
                                        "symbol",
                                        "matchedText",
                                        "isMentioned",
                                        "reactionDirection",
                                        "confidence",
                                        "rationale",
                                    ],
                                },
                            }
                        },
                        "required": ["mentionDecisions"],
                    },
                }
            },
        )
        parsed = json.loads(response.output_text)
        decisions: list[MentionDecision] = []
        for item in parsed.get("mentionDecisions", []):
            market = item["market"].upper()
            symbol = item["symbol"].upper()
            matched_text = item["matchedText"]
            if (market, symbol, matched_text) not in candidate_keys:
                continue
            is_mentioned = bool(item["isMentioned"])
            reaction_direction = item["reactionDirection"] if is_mentioned else "neutral"
            decisions.append(
                MentionDecision(
                    market=market,
                    symbol=symbol,
                    matched_text=matched_text,
                    is_mentioned=is_mentioned,
                    reaction_direction=reaction_direction,
                    confidence=float(item["confidence"]),
                    rationale=item.get("rationale", ""),
                    model=self.model,
                )
            )
        return decisions


def build_llm_provider() -> LLMProvider:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if api_key:
        return OpenAILLMProvider(api_key=api_key, model=model)
    return MockLLMProvider()


def _candidate_keys(mentions: list[Mention]) -> set[tuple[str, str, str]]:
    return {(mention.market.upper(), mention.symbol.upper(), mention.matched_text) for mention in mentions}


def _mock_reaction(text: str) -> tuple[str, float, str]:
    if any(keyword in text for keyword in ["강하다", "기대", "매수", "반등", "호재", "상승"]):
        return "bullish", 0.75, "상승 기대 또는 매수세 표현이 포함됨"
    if any(keyword in text for keyword in ["약하다", "매도", "악재", "하락", "공포", "폭락"]):
        return "bearish", 0.75, "하락 우려 또는 매도 표현이 포함됨"
    return "neutral", 0.55, "명확한 방향성 표현이 약함"


def _mock_decision(
    mention: Mention,
    text: str,
    reaction_direction: str,
    confidence: float,
    rationale: str,
    model: str,
) -> MentionDecision:
    rejection_rationale = _mock_rejection_rationale(mention, text)
    if rejection_rationale:
        return MentionDecision(
            market=mention.market,
            symbol=mention.symbol,
            matched_text=mention.matched_text,
            is_mentioned=False,
            reaction_direction="neutral",
            confidence=0.35,
            rationale=rejection_rationale,
            model=model,
        )
    return MentionDecision(
        market=mention.market,
        symbol=mention.symbol,
        matched_text=mention.matched_text,
        is_mentioned=True,
        reaction_direction=reaction_direction,
        confidence=confidence,
        rationale=rationale,
        model=model,
    )


def _mock_rejection_rationale(mention: Mention, text: str) -> str | None:
    matched_text = mention.matched_text.lower()
    symbol = mention.symbol.upper()
    if symbol == "AAPL" or matched_text in {"애플", "사과"}:
        if any(keyword in text for keyword in ["먹", "사과", "과일", "장보기"]):
            return "과일이나 장보기 맥락으로 보여 종목 언급에서 제외함"
    if symbol == "005930" or "삼성" in matched_text:
        if "삼성 그룹" in text or "삼성그룹" in text:
            return "삼성 그룹 일반 맥락으로 보여 삼성전자 종목 언급에서 제외함"
    return None
