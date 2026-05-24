from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import httpx

from youbuyfirst_pipeline.board_stream import BoardCoverage, BoardWatermark
from youbuyfirst_pipeline.market_investor_flows import InvestorFlowSnapshot
from youbuyfirst_pipeline.market_quotes import ChartCandleSet, QuoteSnapshot
from youbuyfirst_pipeline.models import EnrichedPost


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
        coverage: dict | BoardCoverage | None = None,
    ) -> dict:
        payload = {
            "source": source,
            "runId": run_id,
            "batchStartedAt": _iso(batch_started_at),
            "batchFinishedAt": _iso(batch_finished_at),
            "posts": [self._post_payload(post) for post in posts],
            **_coverage_payload(coverage),
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
        coverage: dict | BoardCoverage | None = None,
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
            **_coverage_payload(coverage),
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/ingestions/crawl-runs", json=payload)
            response.raise_for_status()

    def get_board_watermark(self, source: str, board_id: str) -> BoardWatermark | None:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(
                f"{self.base_url}/internal/crawl-watermarks",
                params={"source": source, "boardId": board_id},
            )
            if response.status_code == 204:
                return None
            response.raise_for_status()
            payload = response.json()
            external_id = payload.get("lastSeenExternalId")
            return BoardWatermark(last_seen_external_id=external_id) if external_id else None

    def publish_quote_snapshots(self, snapshots: Iterable[QuoteSnapshot]) -> None:
        payload = {
            "items": [snapshot.to_api_dict() for snapshot in snapshots],
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/market/quote-snapshots", json=payload)
            response.raise_for_status()

    def publish_chart_candles(self, candle_sets: Iterable[ChartCandleSet]) -> None:
        payload = {
            "items": [candle_set.to_request_dict() for candle_set in candle_sets],
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/market/chart-candles", json=payload)
            response.raise_for_status()

    def publish_investor_flows(self, snapshots: Iterable[InvestorFlowSnapshot]) -> None:
        items = [snapshot.to_request_dict() for snapshot in snapshots]
        if not items:
            return
        payload = {
            "items": items,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/market/investor-flows", json=payload)
            response.raise_for_status()

    @staticmethod
    def _post_payload(post: EnrichedPost) -> dict:
        return {
            "externalId": post.external_id,
            "boardId": post.board_id,
            "url": post.url,
            "title": post.title,
            "contentSnippet": post.content[:1000],
            "authorDisplayName": post.author,
            "publishedAt": _iso(post.published_at),
            "viewCount": post.view_count,
            "recommendCount": post.recommend_count,
            "commentCount": post.comment_count,
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


def _coverage_payload(coverage: dict | BoardCoverage | None) -> dict:
    if coverage is None:
        return {}
    if isinstance(coverage, dict):
        return coverage
    return {
        "pagesFetched": coverage.pages_fetched,
        "rowsSeen": coverage.rows_seen,
        "ignoredPinnedCount": coverage.ignored_pinned_count,
        "duplicateStop": coverage.duplicate_stop,
        "cutoffStop": coverage.cutoff_stop,
        "oldestSeenAt": _iso(coverage.oldest_seen_at) if coverage.oldest_seen_at else None,
        "newestSeenAt": _iso(coverage.newest_seen_at) if coverage.newest_seen_at else None,
        "lastCursor": coverage.last_cursor,
        "coverageStatus": coverage.coverage_status,
    }
