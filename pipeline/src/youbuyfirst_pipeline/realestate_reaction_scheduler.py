from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Protocol

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.realestate_matcher import (
    RealEstateAliasRule,
    load_real_estate_alias_rules,
    load_real_estate_posts_for_matching,
    match_real_estate_posts,
    real_estate_posts_for_matching_from_records,
)
from youbuyfirst_pipeline.realestate_reaction_classifier import (
    RuleBasedRealEstateReactionClassifier,
    classify_real_estate_reaction_observations,
)
from youbuyfirst_pipeline.realestate_reactions import build_real_estate_reaction_snapshots
from youbuyfirst_pipeline.realestate_target_graph import (
    RealEstateTargetEdgeRule,
    load_real_estate_target_edge_rules,
    roll_up_real_estate_reaction_observations,
)

logger = logging.getLogger(__name__)


class RealEstateReactionSnapshotClient(Protocol):
    def publish_real_estate_reaction_snapshots(self, snapshots) -> None:
        ...

    def list_community_posts_for_reaction_refresh(
            self,
            *,
            source: str | None,
            published_from: str,
            published_to: str,
            limit: int,
    ) -> list[dict]:
        ...


@dataclass(frozen=True)
class RealEstateReactionSnapshotRefreshResult:
    status: str
    observation_count: int
    snapshot_count: int
    snapshot_counts_by_type: dict[str, int]


class RealEstateReactionSnapshotRefreshJob:
    def __init__(
            self,
            *,
            client: RealEstateReactionSnapshotClient,
            aliases_jsonl: str | Path | None,
            community_posts_jsonl: str | Path | None,
            window_minutes: int,
            alias_loader: Callable[[], list[RealEstateAliasRule]] | None = None,
            target_edges_jsonl: str | Path | None = None,
            target_edge_loader: Callable[[], list[RealEstateTargetEdgeRule]] | None = None,
            backend_posts_source: str | None = None,
            backend_posts_limit: int = 1000,
            stale_after_minutes: int = 360,
            use_current_window: bool = False,
            candidate_alias_sources: tuple[str, ...] = (),
            candidate_edge_sources: tuple[str, ...] = (),
            clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.aliases_jsonl = Path(aliases_jsonl) if aliases_jsonl else None
        self.alias_loader = alias_loader
        self.community_posts_jsonl = Path(community_posts_jsonl) if community_posts_jsonl else None
        self.target_edges_jsonl = Path(target_edges_jsonl) if target_edges_jsonl else None
        self.target_edge_loader = target_edge_loader
        self.backend_posts_source = backend_posts_source.strip() if backend_posts_source else None
        self.backend_posts_limit = backend_posts_limit
        self.window_minutes = window_minutes
        self.stale_after_minutes = stale_after_minutes
        self.use_current_window = use_current_window
        self.candidate_alias_sources = {source.strip() for source in candidate_alias_sources if source.strip()}
        self.candidate_edge_sources = {source.strip() for source in candidate_edge_sources if source.strip()}
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateReactionSnapshotRefreshResult:
        now = _as_utc(self.clock())
        window_start = (
            _current_window_start(now, self.window_minutes)
            if self.use_current_window
            else _previous_completed_window_start(now, self.window_minutes)
        )
        try:
            aliases = self._load_aliases()
            posts = self._load_posts(window_start)
            target_edges = self._load_target_edges()
        except Exception as exc:
            logger.warning("real-estate reaction snapshot refresh skipped; input unavailable: %s", exc)
            return RealEstateReactionSnapshotRefreshResult(
                status="INPUT_ERROR",
                observation_count=0,
                snapshot_count=0,
                snapshot_counts_by_type={},
            )

        try:
            matched_posts = match_real_estate_posts(
                posts,
                aliases,
                include_candidate_sources=self.candidate_alias_sources,
            )
            observations = classify_real_estate_reaction_observations(
                matched_posts,
                classifier=RuleBasedRealEstateReactionClassifier(),
            )
            observations = _observations_for_window(
                observations,
                window_start=window_start,
                window_minutes=self.window_minutes,
            )
            if target_edges:
                observations = roll_up_real_estate_reaction_observations(
                    observations,
                    target_edges,
                    include_candidate_sources=self.candidate_edge_sources,
                )
            snapshots = build_real_estate_reaction_snapshots(
                observations,
                window_start=window_start,
                window_minutes=self.window_minutes,
                as_of=now,
                stale_after_minutes=self.stale_after_minutes,
            )
        except Exception:
            logger.exception("real-estate reaction snapshot refresh failed during aggregation")
            return RealEstateReactionSnapshotRefreshResult(
                status="PROCESSING_ERROR",
                observation_count=0,
                snapshot_count=0,
                snapshot_counts_by_type={},
            )

        try:
            if snapshots:
                self.client.publish_real_estate_reaction_snapshots(snapshots)
        except Exception:
            logger.exception("real-estate reaction snapshot refresh failed during backend push")
            return RealEstateReactionSnapshotRefreshResult(
                status="CLIENT_ERROR",
                observation_count=len(observations),
                snapshot_count=len(snapshots),
                snapshot_counts_by_type=_snapshot_counts_by_type(snapshots),
            )

        result = RealEstateReactionSnapshotRefreshResult(
            status="OK",
            observation_count=len(observations),
            snapshot_count=len(snapshots),
            snapshot_counts_by_type=_snapshot_counts_by_type(snapshots),
        )
        logger.info(
            "real-estate reaction snapshot refresh finished; status=%s observation_count=%s snapshot_count=%s window_start=%s window_minutes=%s",
            result.status,
            result.observation_count,
            result.snapshot_count,
            window_start.isoformat(),
            self.window_minutes,
        )
        return result

    def _load_posts(self, window_start: datetime):
        if self.community_posts_jsonl is not None:
            return load_real_estate_posts_for_matching(self.community_posts_jsonl)
        window = timedelta(minutes=self.window_minutes)
        previous_window_start = window_start - window
        window_end = window_start + window
        records = self.client.list_community_posts_for_reaction_refresh(
            source=self.backend_posts_source,
            published_from=_iso_z(previous_window_start),
            published_to=_iso_z(window_end),
            limit=self.backend_posts_limit,
        )
        return real_estate_posts_for_matching_from_records(records)

    def _load_aliases(self) -> list[RealEstateAliasRule]:
        if self.alias_loader is not None:
            return list(self.alias_loader())
        if self.aliases_jsonl is None:
            raise ValueError("real-estate aliases source is required")
        return load_real_estate_alias_rules(self.aliases_jsonl)

    def _load_target_edges(self) -> list[RealEstateTargetEdgeRule]:
        if self.target_edge_loader is not None:
            return list(self.target_edge_loader())
        if self.target_edges_jsonl is None:
            return []
        return load_real_estate_target_edge_rules(self.target_edges_jsonl)


def build_real_estate_reaction_snapshot_refresh_job(
        *,
        client: SpringIngestionClient,
        aliases_jsonl: str | Path | None,
        community_posts_jsonl: str | Path | None,
        window_minutes: int,
        alias_loader: Callable[[], list[RealEstateAliasRule]] | None = None,
        target_edges_jsonl: str | Path | None = None,
        target_edge_loader: Callable[[], list[RealEstateTargetEdgeRule]] | None = None,
        backend_posts_source: str | None = None,
        backend_posts_limit: int = 1000,
        stale_after_minutes: int = 360,
        use_current_window: bool = False,
        candidate_alias_sources: tuple[str, ...] = (),
        candidate_edge_sources: tuple[str, ...] = (),
) -> RealEstateReactionSnapshotRefreshJob:
    return RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=aliases_jsonl,
        alias_loader=alias_loader,
        community_posts_jsonl=community_posts_jsonl,
        window_minutes=window_minutes,
        target_edges_jsonl=target_edges_jsonl,
        target_edge_loader=target_edge_loader,
        backend_posts_source=backend_posts_source,
        backend_posts_limit=backend_posts_limit,
        stale_after_minutes=stale_after_minutes,
        use_current_window=use_current_window,
        candidate_alias_sources=candidate_alias_sources,
        candidate_edge_sources=candidate_edge_sources,
    )


def _current_window_start(now: datetime, window_minutes: int) -> datetime:
    return _previous_completed_window_start(now, window_minutes) + timedelta(minutes=window_minutes)


def _previous_completed_window_start(now: datetime, window_minutes: int) -> datetime:
    if window_minutes <= 0:
        raise ValueError("window_minutes must be positive")
    normalized = _as_utc(now)
    window = timedelta(minutes=window_minutes)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    elapsed_seconds = int((normalized - epoch).total_seconds())
    window_seconds = int(window.total_seconds())
    current_window_start_seconds = (elapsed_seconds // window_seconds) * window_seconds
    return epoch + timedelta(seconds=current_window_start_seconds - window_seconds)


def _observations_for_window(observations, *, window_start: datetime, window_minutes: int):
    window = timedelta(minutes=window_minutes)
    previous_window_start = window_start - window
    window_end = window_start + window
    return [
        observation
        for observation in observations
        if previous_window_start <= _as_utc(observation.published_at) < window_end
    ]


def _snapshot_counts_by_type(snapshots) -> dict[str, int]:
    counts: dict[str, int] = {}
    for snapshot in snapshots:
        target_type = str(getattr(snapshot, "target_type", "") or "").strip()
        if not target_type:
            continue
        counts[target_type] = counts.get(target_type, 0) + 1
    return dict(sorted(counts.items()))


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso_z(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")
