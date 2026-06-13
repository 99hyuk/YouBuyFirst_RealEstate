from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import httpx

from youbuyfirst_pipeline.board_stream import BoardCoverage, BoardWatermark
from youbuyfirst_pipeline.models import CommentCollectionTarget, DiffusionEvent, EnrichedPost


class SpringIngestionClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 60.0,
    ) -> None:
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
        diffusion_events: Iterable[DiffusionEvent] | None = None,
        comment_collection_targets: Iterable[CommentCollectionTarget] | None = None,
    ) -> dict:
        post_list = list(posts)
        payload = {
            "source": source,
            "runId": run_id,
            "batchStartedAt": _iso(batch_started_at),
            "batchFinishedAt": _iso(batch_finished_at),
            "posts": [self._post_payload(post) for post in post_list],
            "diffusionEvents": [self._diffusion_payload(event) for event in diffusion_events or []],
            "commentCollectionTargets": [
                self._comment_collection_target_payload(target)
                for target in comment_collection_targets or []
            ],
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
            cutoff_at = _parse_iso(payload.get("lastSeenPublishedAt"))
            if not external_id and cutoff_at is None:
                return None
            return BoardWatermark(last_seen_external_id=external_id, cutoff_at=cutoff_at)

    def publish_real_estate_market_facts(self, facts: Iterable[object]) -> None:
        items = [fact.to_ingestion_dict() for fact in facts]
        if not items:
            return
        payload = {
            "items": items,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/realestate/market-facts", json=payload)
            response.raise_for_status()

    def publish_real_estate_public_data_raw_ingestion(self, ingestion: object) -> None:
        payload = ingestion.to_request_dict()
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/internal/realestate/public-data/raw-ingestions",
                json=payload,
            )
            response.raise_for_status()

    def promote_real_estate_public_data_staging(
        self,
        *,
        provider_dataset: str | None = None,
        run_key: str | None = None,
        validation_status: str = "valid",
        limit: int = 1_000,
    ) -> dict:
        payload: dict[str, str | int] = {
            "validationStatus": validation_status,
            "limit": limit,
        }
        if provider_dataset:
            payload["providerDataset"] = provider_dataset
        if run_key:
            payload["runKey"] = run_key
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/internal/realestate/public-data/promote-staging",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return data if isinstance(data, dict) else {}

    def publish_real_estate_regions(self, regions: Iterable[object]) -> None:
        items = [region.to_import_dict() for region in regions]
        if not items:
            return
        payload = {
            "items": items,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/realestate/regions", json=payload)
            response.raise_for_status()

    def publish_real_estate_reaction_snapshots(self, snapshots: Iterable[object]) -> None:
        items = [snapshot.to_request_dict() for snapshot in snapshots]
        if not items:
            return
        payload = {
            "items": items,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/realestate/reaction-snapshots", json=payload)
            response.raise_for_status()

    def publish_real_estate_content_items(self, items: Iterable[object]) -> None:
        payload_items = [item.to_content_item_dict() for item in items]
        if not payload_items:
            return
        payload = {
            "items": payload_items,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/realestate/content-items", json=payload)
            response.raise_for_status()

    def publish_real_estate_evidence_logs(self, logs: Iterable[object]) -> None:
        payload_logs = [
            log.to_request_dict() if hasattr(log, "to_request_dict") else log
            for log in logs
        ]
        if not payload_logs:
            return
        payload = {
            "logs": payload_logs,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/realestate/evidence-logs", json=payload)
            response.raise_for_status()

    def publish_real_estate_alias_candidates(self, candidates: Iterable[object]) -> None:
        items = [
            candidate.to_request_dict() if hasattr(candidate, "to_request_dict") else candidate
            for candidate in candidates
        ]
        if not items:
            return
        payload = {
            "items": items,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/internal/realestate/aliases/candidates", json=payload)
            response.raise_for_status()

    def list_real_estate_public_data_import_runs(
        self,
        *,
        run_keys: list[str] | None = None,
        provider_dataset: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        normalized_run_keys = [run_key.strip() for run_key in run_keys or [] if run_key.strip()]
        params = {"limit": str(len(normalized_run_keys) if normalized_run_keys else limit)}
        if provider_dataset is not None:
            params["providerDataset"] = provider_dataset
        if status is not None:
            params["status"] = status
        if normalized_run_keys:
            params["runKey"] = normalized_run_keys
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(f"{self.base_url}/internal/realestate/public-data/import-runs", params=params)
            response.raise_for_status()
            data = response.json()
        items = data.get("items", []) if isinstance(data, dict) else []
        return [item for item in items if isinstance(item, dict)]

    def list_real_estate_market_data_targets(self, enabled: bool | None = True) -> list[dict]:
        params = {}
        if enabled is not None:
            params["enabled"] = "true" if enabled else "false"
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(f"{self.base_url}/internal/realestate/market-data-targets", params=params)
            response.raise_for_status()
            data = response.json()
        items = data.get("items", []) if isinstance(data, dict) else []
        return [item for item in items if isinstance(item, dict)]

    def list_real_estate_aliases(
        self,
        *,
        review_state: str | None = "approved",
        ambiguous: bool | None = False,
        target_type: str | None = None,
    ) -> list[dict]:
        params = {}
        if review_state is not None:
            params["reviewState"] = review_state
        if ambiguous is not None:
            params["ambiguous"] = "true" if ambiguous else "false"
        if target_type is not None:
            params["targetType"] = target_type
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(f"{self.base_url}/internal/realestate/aliases", params=params)
            response.raise_for_status()
            data = response.json()
        items = data.get("items", []) if isinstance(data, dict) else []
        return [item for item in items if isinstance(item, dict)]

    def list_real_estate_target_edges(
        self,
        *,
        review_state: str | None = "approved",
        edge_type: str | None = None,
        target_id: str | None = None,
        direction: str | None = "both",
    ) -> list[dict]:
        params = {}
        if review_state is not None:
            params["reviewState"] = review_state
        if edge_type is not None:
            params["edgeType"] = edge_type
        if target_id is not None:
            params["targetId"] = target_id
        if direction is not None:
            params["direction"] = direction
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(f"{self.base_url}/internal/realestate/target-edges", params=params)
            response.raise_for_status()
            data = response.json()
        items = data.get("items", []) if isinstance(data, dict) else []
        return [item for item in items if isinstance(item, dict)]

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
        }

    @staticmethod
    def _diffusion_payload(event: DiffusionEvent) -> dict:
        return {
            "externalId": event.external_id,
            "boardId": event.board_id,
            "diffusionType": event.diffusion_type,
            "listPosition": event.list_position,
            "observedAt": _iso(event.observed_at),
            "viewCount": event.view_count,
            "recommendCount": event.recommend_count,
            "commentCount": event.comment_count,
            "diffusionOnly": event.diffusion_only,
        }

    @staticmethod
    def _comment_collection_target_payload(target: CommentCollectionTarget) -> dict:
        return {
            "externalId": target.external_id,
            "boardId": target.board_id,
            "triggerReason": target.trigger_reason,
            "triggeredAt": _iso(target.triggered_at),
            "maxComments": target.max_comments,
            "priority": target.priority,
            "viewCount": target.view_count,
            "recommendCount": target.recommend_count,
            "commentCount": target.comment_count,
        }


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
