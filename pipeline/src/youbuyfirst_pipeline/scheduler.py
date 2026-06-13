from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from youbuyfirst_pipeline.pipeline import CommunityPipeline
from youbuyfirst_pipeline.realestate_daily_scheduler import RealEstateDailyRefreshJob
from youbuyfirst_pipeline.realestate_reaction_scheduler import RealEstateReactionSnapshotRefreshJob
from youbuyfirst_pipeline.realestate_scheduler import RealEstateMarketFactsRefreshJob

logger = logging.getLogger(__name__)


def configure_scheduler(
        scheduler: AsyncIOScheduler,
        pipeline: CommunityPipeline,
        crawl_interval_minutes: int,
        realestate_market_facts_refresh_job: RealEstateMarketFactsRefreshJob | None = None,
        realestate_market_facts_interval_minutes: int = 360,
        realestate_reaction_snapshot_refresh_job: RealEstateReactionSnapshotRefreshJob | None = None,
        realestate_reaction_snapshot_interval_minutes: int = 30,
        realestate_daily_refresh_job: RealEstateDailyRefreshJob | None = None,
        realestate_daily_refresh_interval_minutes: int = 1440,
) -> None:
    scheduler.add_job(
        pipeline.run_once,
        "interval",
        id="community-crawl",
        minutes=crawl_interval_minutes,
        next_run_time=None,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    if realestate_market_facts_refresh_job is not None:
        scheduler.add_job(
            realestate_market_facts_refresh_job.run_once,
            "interval",
            id="realestate-market-facts-refresh",
            minutes=realestate_market_facts_interval_minutes,
            next_run_time=datetime.now(timezone.utc),
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
    if realestate_reaction_snapshot_refresh_job is not None:
        scheduler.add_job(
            realestate_reaction_snapshot_refresh_job.run_once,
            "interval",
            id="realestate-reaction-snapshots-refresh",
            minutes=realestate_reaction_snapshot_interval_minutes,
            next_run_time=datetime.now(timezone.utc),
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
    if realestate_daily_refresh_job is not None:
        scheduler.add_job(
            realestate_daily_refresh_job.run_once,
            "interval",
            id="realestate-daily-refresh",
            minutes=realestate_daily_refresh_interval_minutes,
            next_run_time=datetime.now(timezone.utc),
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )


async def serve(
        pipeline: CommunityPipeline,
        interval_minutes: int = 30,
        realestate_market_facts_refresh_job: RealEstateMarketFactsRefreshJob | None = None,
        realestate_market_facts_interval_minutes: int = 360,
        realestate_reaction_snapshot_refresh_job: RealEstateReactionSnapshotRefreshJob | None = None,
        realestate_reaction_snapshot_interval_minutes: int = 30,
        realestate_daily_refresh_job: RealEstateDailyRefreshJob | None = None,
        realestate_daily_refresh_interval_minutes: int = 1440,
) -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    configure_scheduler(
        scheduler,
        pipeline=pipeline,
        crawl_interval_minutes=interval_minutes,
        realestate_market_facts_refresh_job=realestate_market_facts_refresh_job,
        realestate_market_facts_interval_minutes=realestate_market_facts_interval_minutes,
        realestate_reaction_snapshot_refresh_job=realestate_reaction_snapshot_refresh_job,
        realestate_reaction_snapshot_interval_minutes=realestate_reaction_snapshot_interval_minutes,
        realestate_daily_refresh_job=realestate_daily_refresh_job,
        realestate_daily_refresh_interval_minutes=realestate_daily_refresh_interval_minutes,
    )
    scheduler.start()
    logger.info(
        "pipeline scheduler started; crawl_interval_minutes=%s realestate_market_facts_enabled=%s realestate_market_facts_interval_minutes=%s realestate_reaction_snapshot_enabled=%s realestate_reaction_snapshot_interval_minutes=%s realestate_daily_refresh_enabled=%s realestate_daily_refresh_interval_minutes=%s",
        interval_minutes,
        realestate_market_facts_refresh_job is not None,
        realestate_market_facts_interval_minutes,
        realestate_reaction_snapshot_refresh_job is not None,
        realestate_reaction_snapshot_interval_minutes,
        realestate_daily_refresh_job is not None,
        realestate_daily_refresh_interval_minutes,
    )
    await asyncio.Event().wait()
