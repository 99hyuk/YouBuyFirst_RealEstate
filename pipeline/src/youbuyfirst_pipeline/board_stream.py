from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime

from youbuyfirst_pipeline.models import DiffusionEvent, RawPost


FetchBoardPage = Callable[[str | None], Awaitable["BoardPage"]]
Sleep = Callable[[float], Awaitable[None]]
RandomDelay = Callable[[float, float], float]


@dataclass(frozen=True)
class BoardWatermark:
    last_seen_external_id: str | None = None
    cutoff_at: datetime | None = None


@dataclass(frozen=True)
class BoardPage:
    cursor: str
    posts: list[RawPost]
    next_cursor: str | None = None
    ignored_pinned_count: int = 0


@dataclass(frozen=True)
class BoardCoverage:
    pages_fetched: int
    rows_seen: int
    ignored_pinned_count: int
    duplicate_stop: bool
    cutoff_stop: bool
    oldest_seen_at: datetime | None
    newest_seen_at: datetime | None
    last_cursor: str | None
    coverage_status: str


@dataclass(frozen=True)
class BoardStreamResult:
    posts: list[RawPost]
    coverage: BoardCoverage | None
    diffusion_events: list[DiffusionEvent] = field(default_factory=list)


class BoardStreamCrawler:
    def __init__(
        self,
        max_pages_per_run: int = 20,
        max_posts_per_run: int = 500,
        page_delay_min_seconds: float = 0.0,
        page_delay_max_seconds: float = 0.0,
        sleeper: Sleep | None = None,
        random_delay: RandomDelay | None = None,
    ) -> None:
        if max_pages_per_run < 1:
            raise ValueError("max_pages_per_run must be at least 1")
        if max_posts_per_run < 1:
            raise ValueError("max_posts_per_run must be at least 1")
        if page_delay_min_seconds < 0 or page_delay_max_seconds < 0:
            raise ValueError("page_delay values must be non-negative")
        if page_delay_min_seconds > page_delay_max_seconds:
            raise ValueError("page_delay_min_seconds must be less than or equal to page_delay_max_seconds")
        self.max_pages_per_run = max_pages_per_run
        self.max_posts_per_run = max_posts_per_run
        self.page_delay_min_seconds = page_delay_min_seconds
        self.page_delay_max_seconds = page_delay_max_seconds
        self._sleeper = sleeper or asyncio.sleep
        self._random_delay = random_delay or random.uniform

    async def collect(self, fetch_page: FetchBoardPage, watermark: BoardWatermark | None = None) -> BoardStreamResult:
        watermark = watermark or BoardWatermark()
        cursor: str | None = None
        posts: list[RawPost] = []
        pages_fetched = 0
        rows_seen = 0
        ignored_pinned_count = 0
        duplicate_stop = False
        cutoff_stop = False
        limit_stop = False
        oldest_seen_at: datetime | None = None
        newest_seen_at: datetime | None = None
        last_cursor: str | None = None

        while pages_fetched < self.max_pages_per_run:
            await self._wait_between_pages(pages_fetched)
            page = await fetch_page(cursor)
            pages_fetched += 1
            last_cursor = page.cursor
            ignored_pinned_count += page.ignored_pinned_count

            for post in page.posts:
                rows_seen += 1
                oldest_seen_at = _min_datetime(oldest_seen_at, post.published_at)
                newest_seen_at = _max_datetime(newest_seen_at, post.published_at)
                if post.external_id == watermark.last_seen_external_id:
                    duplicate_stop = True
                    continue
                if watermark.cutoff_at is not None and post.published_at < watermark.cutoff_at:
                    cutoff_stop = True
                    continue
                if watermark.cutoff_at is None and (duplicate_stop or cutoff_stop):
                    continue
                posts.append(post)
                if len(posts) >= self.max_posts_per_run:
                    limit_stop = True

            if duplicate_stop or cutoff_stop or limit_stop or page.next_cursor is None:
                break
            cursor = page.next_cursor
        else:
            limit_stop = True

        coverage_status = "partial" if limit_stop else "complete"
        return BoardStreamResult(
            posts=posts,
            coverage=BoardCoverage(
                pages_fetched=pages_fetched,
                rows_seen=rows_seen,
                ignored_pinned_count=ignored_pinned_count,
                duplicate_stop=duplicate_stop,
                cutoff_stop=cutoff_stop,
                oldest_seen_at=oldest_seen_at,
                newest_seen_at=newest_seen_at,
                last_cursor=last_cursor,
                coverage_status=coverage_status,
            ),
        )

    async def _wait_between_pages(self, pages_fetched: int) -> None:
        if pages_fetched == 0 or self.page_delay_max_seconds <= 0:
            return
        delay_seconds = self._random_delay(self.page_delay_min_seconds, self.page_delay_max_seconds)
        delay_seconds = min(max(delay_seconds, self.page_delay_min_seconds), self.page_delay_max_seconds)
        if delay_seconds > 0:
            await self._sleeper(delay_seconds)


def _min_datetime(current: datetime | None, candidate: datetime) -> datetime:
    return candidate if current is None or candidate < current else current


def _max_datetime(current: datetime | None, candidate: datetime) -> datetime:
    return candidate if current is None or candidate > current else current
