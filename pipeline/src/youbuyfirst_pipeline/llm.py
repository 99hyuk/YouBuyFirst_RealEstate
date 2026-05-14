from __future__ import annotations

import json
import os
from typing import Protocol

from youbuyfirst_pipeline.models import Analysis, Mention


class LLMProvider(Protocol):
    def analyze(self, title: str, content: str, mentions: list[Mention]) -> list[Analysis]:
        ...


class MockLLMProvider:
    model = "mock"

    def analyze(self, title: str, content: str, mentions: list[Mention]) -> list[Analysis]:
        text = f"{title} {content}".lower()
        if any(keyword in text for keyword in ["강하다", "기대", "매수", "반등", "호재", "상승"]):
            sentiment = "bullish"
            confidence = 0.75
            rationale = "상승 기대 또는 매수세 표현이 포함됨"
        elif any(keyword in text for keyword in ["약하다", "매도", "악재", "하락", "공포", "폭락"]):
            sentiment = "bearish"
            confidence = 0.75
            rationale = "하락 우려 또는 매도 표현이 포함됨"
        else:
            sentiment = "neutral"
            confidence = 0.55
            rationale = "명확한 방향성 표현이 약함"

        return [
            Analysis(
                market=mention.market,
                symbol=mention.symbol,
                sentiment=sentiment,
                confidence=confidence,
                rationale=rationale,
                model=self.model,
            )
            for mention in mentions
        ]


class OpenAILLMProvider:
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def analyze(self, title: str, content: str, mentions: list[Mention]) -> list[Analysis]:
        if not mentions:
            return []

        mention_payload = [mention.__dict__ for mention in mentions]
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You classify Korean investing community posts by instrument. "
                        "Return JSON only. Sentiment must be bullish, bearish, or neutral."
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
                    "name": "sentiment_batch",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "analyses": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "market": {"type": "string"},
                                        "symbol": {"type": "string"},
                                        "sentiment": {"type": "string", "enum": ["bullish", "bearish", "neutral"]},
                                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                        "rationale": {"type": "string"},
                                    },
                                    "required": ["market", "symbol", "sentiment", "confidence", "rationale"],
                                },
                            }
                        },
                        "required": ["analyses"],
                    },
                }
            },
        )
        parsed = json.loads(response.output_text)
        return [
            Analysis(
                market=item["market"].upper(),
                symbol=item["symbol"].upper(),
                sentiment=item["sentiment"],
                confidence=float(item["confidence"]),
                rationale=item.get("rationale", ""),
                model=self.model,
            )
            for item in parsed.get("analyses", [])
        ]


def build_llm_provider() -> LLMProvider:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if api_key:
        return OpenAILLMProvider(api_key=api_key, model=model)
    return MockLLMProvider()

