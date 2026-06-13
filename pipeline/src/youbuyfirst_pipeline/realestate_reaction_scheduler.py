from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Protocol

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.realestate_matcher import (
    load_real_estate_alias_rules,
    load_real_estate_posts_for_matching,
    match_real_estate_posts,
)
from youbuyfirst_pipeline.realestate_reaction_classifier import (
    RuleBasedRealEstateReactionClassifier,
    classify_real_estate_reaction_observations,
)
from youbuyfirst_pipeline.realestate_reactions import build_real_estate_reaction_snapshots
from youbuyfirst_pipeline.realestate_target_graph import (
    load_real_estate_target_edge_rules,
    roll_up_real_estate_reaction_observations,
)

logger = logging.getLogger(__name__)


class RealEstateReactionSnapshotClient(Protocol):
    def publish_real_estate_reaction_snapshots(self, snapshots) -> None:
        ...


@dataclass(frozen=True)
class RealEstateReactionSnapshotRefreshResult:
    status: str
    observation_count: int
    snapshot_count: int


class RealEstateReactionSnapshotRefreshJob:
    def __init__(
            self,
            *,
            client: RealEstateReactionSnapshotClient,
            aliases_jsonl: str | Path,
            community_posts_jsonl: str | Path,
            window_minutes: int,
            target_edges_jsonl: str | Path | None = None,
            stale_after_minutes: int = 360,
            clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.aliases_jsonl = Path(aliases_jsonl)
        self.community_posts_jsonl = Path(community_posts_jsonl)
        self.target_edges_jsonl = Path(target_edges_jsonl) if target_edges_jsonl else None
        self.window_minutes = window_minutes
        self.stale_after_minutes = stale_after_minutes
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateReactionSnapshotRefreshResult:
        now = _as_utc(self.clock())
        window_start = _previous_completed_window_start(now, self.window_minutes)
        try:
            aliases = load_real_estate_alias_rules(self.aliases_jsonl)
            posts = load_real_estate_posts_for_matching(self.community_posts_jsonl)
            target_edges = load_real_estate_target_edge_rules(self.target_edges_jsonl) if self.target_edges_jsonl else []
        except Exception as exc:
            logger.warning("real-estate reaction snapshot refresh skipped; input unavailable: %s", exc)
            return RealEstateReactionSnapshotRefreshResult(
                status="INPUT_ERROR",
                observation_count=0,
                snapshot_count=0,
            )

        try:
            matched_posts = match_real_estate_posts(posts, aliases)
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
                observations = roll_up_real_estate_reaction_observations(observations, target_edges)
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
            )

        result = RealEstateReactionSnapshotRefreshResult(
            status="OK",
            observation_count=len(observations),
            snapshot_count=len(snapshots),
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


def build_real_estate_reaction_snapshot_refresh_job(
        *,
        client: SpringIngestionClient,
        aliases_jsonl: str | Path,
        community_posts_jsonl: str | Path,
        window_minutes: int,
        target_edges_jsonl: str | Path | None = None,
        stale_after_minutes: int = 360,
) -> RealEstateReactionSnapshotRefreshJob:
    return RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=aliases_jsonl,
        community_posts_jsonl=community_posts_jsonl,
        window_minutes=window_minutes,
        target_edges_jsonl=target_edges_jsonl,
        stale_after_minutes=stale_after_minutes,
    )


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


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
