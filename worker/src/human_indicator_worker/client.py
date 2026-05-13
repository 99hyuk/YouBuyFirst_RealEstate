from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import httpx

from human_indicator_worker.models import EnrichedPost


class SpringIngestionClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def ingest(
        self,
        source: str,
        run_id: str,
        batch_started_at: datetime,
        batch_finished_at: datetime,
        posts: Iterable[EnrichedPost],
    ) -> dict:
        payload = {
            "source": source,
            "runId": run_id,
            "batchStartedAt": _iso(batch_started_at),
            "batchFinishedAt": _iso(batch_finished_at),
            "posts": [self._post_payload(post) for post in posts],
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/ingestions/community-posts", json=payload)
            response.raise_for_status()
            return response.json()

    def record_crawl_run(
        self,
        source: str,
        run_id: str,
        batch_started_at: datetime,
        batch_finished_at: datetime,
        status: str,
        posts_seen: int,
        posts_accepted: int,
        error_message: str | None = None,
    ) -> None:
        payload = {
            "source": source,
            "runId": run_id,
            "batchStartedAt": _iso(batch_started_at),
            "batchFinishedAt": _iso(batch_finished_at),
            "status": status,
            "postsSeen": posts_seen,
            "postsAccepted": posts_accepted,
            "errorMessage": error_message,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/ingestions/crawl-runs", json=payload)
            response.raise_for_status()

    @staticmethod
    def _post_payload(post: EnrichedPost) -> dict:
        return {
            "externalId": post.external_id,
            "url": post.url,
            "title": post.title,
            "contentSnippet": post.content[:1000],
            "authorDisplayName": post.author,
            "publishedAt": _iso(post.published_at),
            "mentions": [
                {
                    "market": mention.market,
                    "symbol": mention.symbol,
                    "matchedText": mention.matched_text,
                }
                for mention in post.mentions
            ],
            "sentiments": [
                {
                    "market": analysis.market,
                    "symbol": analysis.symbol,
                    "sentiment": analysis.sentiment,
                    "confidence": analysis.confidence,
                    "rationale": analysis.rationale,
                    "model": analysis.model,
                }
                for analysis in post.analyses
            ],
        }


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
