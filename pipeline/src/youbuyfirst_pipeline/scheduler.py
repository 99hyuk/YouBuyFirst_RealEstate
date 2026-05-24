from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from youbuyfirst_pipeline.market_scheduler import ChartCandleOnDemandRefreshJob, InvestorFlowRefreshJob, MarketRefreshJob
from youbuyfirst_pipeline.pipeline import CommunityPipeline

logger = logging.getLogger(__name__)


def configure_scheduler(
        scheduler: AsyncIOScheduler,
        pipeline: CommunityPipeline,
        crawl_interval_minutes: int,
        market_refresh_job: MarketRefreshJob | None = None,
        market_interval_minutes: int = 10,
        investor_flow_refresh_job: InvestorFlowRefreshJob | None = None,
        investor_flow_hour: int = 18,
        investor_flow_minute: int = 30,
        investor_flow_timezone: str = "Asia/Seoul",
        chart_on_demand_refresh_job: ChartCandleOnDemandRefreshJob | None = None,
        chart_on_demand_interval_seconds: int = 60,
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
    if investor_flow_refresh_job is not None:
        scheduler.add_job(
            investor_flow_refresh_job.run_once,
            "cron",
            id="market-investor-flow-refresh",
            day_of_week="mon-fri",
            hour=investor_flow_hour,
            minute=investor_flow_minute,
            timezone=ZoneInfo(investor_flow_timezone),
            next_run_time=None,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
    if chart_on_demand_refresh_job is not None:
        scheduler.add_job(
            chart_on_demand_refresh_job.run_once,
            "interval",
            id="market-chart-on-demand-refresh",
            seconds=chart_on_demand_interval_seconds,
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
        investor_flow_refresh_job: InvestorFlowRefreshJob | None = None,
        investor_flow_hour: int = 18,
        investor_flow_minute: int = 30,
        investor_flow_timezone: str = "Asia/Seoul",
        chart_on_demand_refresh_job: ChartCandleOnDemandRefreshJob | None = None,
        chart_on_demand_interval_seconds: int = 60,
) -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    configure_scheduler(
        scheduler,
        pipeline=pipeline,
        crawl_interval_minutes=interval_minutes,
        market_refresh_job=market_refresh_job,
        market_interval_minutes=market_interval_minutes,
        investor_flow_refresh_job=investor_flow_refresh_job,
        investor_flow_hour=investor_flow_hour,
        investor_flow_minute=investor_flow_minute,
        investor_flow_timezone=investor_flow_timezone,
        chart_on_demand_refresh_job=chart_on_demand_refresh_job,
        chart_on_demand_interval_seconds=chart_on_demand_interval_seconds,
    )
    scheduler.start()
    logger.info(
        "pipeline scheduler started; crawl_interval_minutes=%s market_refresh_enabled=%s market_interval_minutes=%s investor_flow_enabled=%s investor_flow_time=%02d:%02d %s chart_on_demand_enabled=%s chart_on_demand_interval_seconds=%s",
        interval_minutes,
        market_refresh_job is not None,
        market_interval_minutes,
        investor_flow_refresh_job is not None,
        investor_flow_hour,
        investor_flow_minute,
        investor_flow_timezone,
        chart_on_demand_refresh_job is not None,
        chart_on_demand_interval_seconds,
    )
    await asyncio.Event().wait()
