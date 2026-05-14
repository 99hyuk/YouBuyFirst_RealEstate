from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from youbuyfirst_pipeline.pipeline import CommunityPipeline

logger = logging.getLogger(__name__)


async def serve(pipeline: CommunityPipeline, interval_minutes: int = 30) -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(pipeline.run_once, "interval", minutes=interval_minutes, next_run_time=None)
    scheduler.start()
    logger.info("pipeline scheduler started; interval_minutes=%s", interval_minutes)
    await asyncio.Event().wait()
