from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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
    pass
