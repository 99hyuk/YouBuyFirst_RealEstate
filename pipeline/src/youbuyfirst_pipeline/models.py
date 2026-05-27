from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Instrument:
    market: str
    symbol: str
    name: str
    aliases: list[str] = field(default_factory=list)
    instrument_id: int | None = None


@dataclass(frozen=True)
class InstrumentAliasRule:
    market: str
    symbol: str
    alias: str
    status: str = "ACCEPTED"
    confidence: float = 1.0
    ambiguous: bool = False
    source: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class Mention:
    market: str
    symbol: str
    matched_text: str


@dataclass(frozen=True)
class AliasCandidate:
    alias: str
    suggested_market: str | None
    suggested_symbol: str | None
    reason: str
    context_snippet: str | None = None
    sample_url: str | None = None
    observed_at: datetime | None = None


@dataclass(frozen=True)
class MentionDecision:
    market: str
    symbol: str
    matched_text: str
    is_mentioned: bool
    reaction_direction: str
    confidence: float
    rationale: str
    model: str


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
    board_id: str | None = None
    view_count: int | None = None
    recommend_count: int | None = None
    comment_count: int | None = None


@dataclass(frozen=True)
class DiffusionEvent:
    external_id: str
    board_id: str | None
    diffusion_type: str
    list_position: int | None
    observed_at: datetime
    view_count: int | None = None
    recommend_count: int | None = None
    comment_count: int | None = None
    diffusion_only: bool = False


@dataclass(frozen=True)
class CommentCollectionTarget:
    external_id: str
    board_id: str | None
    trigger_reason: str
    triggered_at: datetime
    max_comments: int
    priority: int
    view_count: int | None = None
    recommend_count: int | None = None
    comment_count: int | None = None


@dataclass(frozen=True)
class EnrichedPost(RawPost):
    mentions: list[Mention] = field(default_factory=list)
    analyses: list[Analysis] = field(default_factory=list)
    alias_candidates: list[AliasCandidate] = field(default_factory=list)
