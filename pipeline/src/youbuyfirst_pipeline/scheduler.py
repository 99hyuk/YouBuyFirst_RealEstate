from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from youbuyfirst_pipeline.market_scheduler import MarketRefreshJob
from youbuyfirst_pipeline.pipeline import CommunityPipeline

logger = logging.getLogger(__name__)


def configure_scheduler(
        scheduler: AsyncIOScheduler,
        pipeline: CommunityPipeline,
        crawl_interval_minutes: int,
        market_refresh_job: MarketRefreshJob | None = None,
        market_interval_minutes: int = 10,
) -> None:
    scheduler.add_job(
        pipeline.run_once,
        "interval",
        id="community-crawl",
        minutes=crawl_interval_minutes,
        next_run_time=None,
        replace_existing=True,
    )
    if market_refresh_job is not None:
        scheduler.add_job(
            market_refresh_job.run_once,
            "interval",
            id="market-refresh",
            minutes=market_interval_minutes,
            next_run_time=datetime.now(timezone.utc),
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )


async def serve(
        pipeline: CommunityPipeline,
        interval_minutes: int = 30,
        market_refresh_job: MarketRefreshJob | None = None,
        market_interval_minutes: int = 10,
) -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    configure_scheduler(
        scheduler,
        pipeline=pipeline,
        crawl_interval_minutes=interval_minutes,
        market_refresh_job=market_refresh_job,
        market_interval_minutes=market_interval_minutes,
    )
    scheduler.start()
    logger.info(
        "pipeline scheduler started; crawl_interval_minutes=%s market_refresh_enabled=%s market_interval_minutes=%s",
        interval_minutes,
        market_refresh_job is not None,
        market_interval_minutes,
    )
    await asyncio.Event().wait()
