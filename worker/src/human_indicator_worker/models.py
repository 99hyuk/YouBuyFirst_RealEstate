from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Instrument:
    market: str
    symbol: str
    name: str
    aliases: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Mention:
    market: str
    symbol: str
    matched_text: str


@dataclass(frozen=True)
class Analysis:
    market: str
    symbol: str
    sentiment: str
    confidence: float
    rationale: str
    model: str


@dataclass(frozen=True)
class RawPost:
    source: str
    external_id: str
    url: str
    title: str
    content: str
    author: str
    published_at: datetime


@dataclass(frozen=True)
class EnrichedPost(RawPost):
    mentions: list[Mention] = field(default_factory=list)
    analyses: list[Analysis] = field(default_factory=list)

