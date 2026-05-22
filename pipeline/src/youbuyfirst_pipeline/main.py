from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.crawl_targets import CrawlTarget, CrawlTargetKind, default_crawl_targets
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher
from youbuyfirst_pipeline.crawlers.fmkorea import FmkoreaAdapter
from youbuyfirst_pipeline.crawlers.naver import NaverBoardAdapter
from youbuyfirst_pipeline.instruments import load_instruments
from youbuyfirst_pipeline.llm import build_llm_provider
from youbuyfirst_pipeline.market_investor_flows import (
    DEFAULT_INVESTOR_FLOW_PROVIDER,
    DEFAULT_INVESTOR_FLOW_HISTORY_LIMIT,
    MarketInvestorFlowProvider,
    build_investor_flow_client,
    configured_investor_flow_symbols,
)
from youbuyfirst_pipeline.market_scheduler import build_investor_flow_refresh_job, build_market_refresh_job
from youbuyfirst_pipeline.market_quotes import (
    DEFAULT_QUOTE_CACHE_TTL_SECONDS,
    MarketChartCandleProvider,
    MarketQuoteProvider,
    configured_quote_symbols,
)
from youbuyfirst_pipeline.matcher import InstrumentMatcher
from youbuyfirst_pipeline.pipeline import CommunityPipeline
from youbuyfirst_pipeline.scheduler import serve
from youbuyfirst_pipeline.source_policy import default_source_policy_registry, runtime_environment_from_env


def build_pipeline() -> CommunityPipeline:
    load_dotenv()
    runtime_environment = runtime_environment_from_env(os.getenv("CRAWL_RUNTIME_ENV"))
    user_agent = os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    )
    fetcher = BrowserCapableFetcher(user_agent=user_agent, timeout_seconds=float(os.getenv("CRAWLER_TIMEOUT_SECONDS", "10")))

    instrument_path = Path(os.getenv("INSTRUMENT_CSV_PATH", "data/instruments.sample.csv"))
    instruments = load_instruments(instrument_path)

    targets = default_crawl_targets(
        instruments,
        naver_stock_codes=_configured_naver_codes(os.getenv("NAVER_STOCK_CODES")),
        fmkorea_url=os.getenv("FMKOREA_STOCK_URL"),
    )
    adapters = _adapters_from_targets(targets, fetcher)

    matcher = InstrumentMatcher(instruments)
    client = SpringIngestionClient(os.getenv("SPRING_BASE_URL", "http://localhost:8080"))
    return CommunityPipeline(
        adapters=adapters,
        matcher=matcher,
        llm_provider=build_llm_provider(),
        client=client,
        source_policy_registry=default_source_policy_registry(),
        runtime_environment=runtime_environment,
    )


def _configured_naver_codes(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [code.strip() for code in value.split(",") if code.strip()]


def _adapters_from_targets(targets: list[CrawlTarget], fetcher: BrowserCapableFetcher) -> list:
    adapters = []
    for target in targets:
        if target.source == "NAVER" and target.kind == CrawlTargetKind.STOCK_BOARD:
            if not target.symbol:
                raise ValueError(f"{target.target_id} is missing symbol")
            adapters.append(NaverBoardAdapter(fetcher, stock_code=target.symbol, target=target))
            continue
        if target.source == "FMKOREA" and target.kind == CrawlTargetKind.COMMUNITY_BOARD:
            adapters.append(FmkoreaAdapter(fetcher, url=target.url, target=target))
            continue
        raise ValueError(f"unsupported crawl target: {target.target_id}")
    return adapters


async def async_main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "run-once",
            "serve",
            "quote-snapshot",
            "quote-push",
            "chart-candles",
            "chart-candles-push",
            "investor-flows",
            "investor-flows-push",
        ],
    )
    parser.add_argument("--interval-minutes", type=int, default=int(os.getenv("CRAWL_INTERVAL_MINUTES", "30")))
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=configured_quote_symbols(os.getenv("MARKET_QUOTE_SYMBOLS")),
        help="Quote symbols such as 005930.KS AAPL NVDA",
    )
    parser.add_argument("--chart-range", default=os.getenv("MARKET_CHART_RANGE", "3M"))
    parser.add_argument("--interval", default=os.getenv("MARKET_CHART_INTERVAL", "1d"))
    parser.add_argument(
        "--investor-flow-symbols",
        nargs="+",
        default=configured_investor_flow_symbols(os.getenv("MARKET_INVESTOR_FLOW_SYMBOLS")),
        help="Domestic investor flow symbols such as 005930.KS 000660.KS 069500.KS",
    )
    parser.add_argument("--trade-date", default=os.getenv("MARKET_INVESTOR_FLOW_TRADE_DATE"))
    parser.add_argument(
        "--investor-flow-limit",
        type=int,
        default=int(os.getenv("MARKET_INVESTOR_FLOW_HISTORY_LIMIT", str(DEFAULT_INVESTOR_FLOW_HISTORY_LIMIT))),
    )
    parser.add_argument(
        "--investor-flow-provider",
        default=os.getenv("MARKET_INVESTOR_FLOW_PROVIDER", DEFAULT_INVESTOR_FLOW_PROVIDER),
        help="Investor flow provider: naver-finance or pykrx",
    )
    parser.add_argument(
        "--market-refresh-interval-minutes",
        type=int,
        default=int(os.getenv("MARKET_REFRESH_INTERVAL_MINUTES", "10")),
    )
    parser.add_argument(
        "--disable-market-refresh",
        action="store_true",
        default=os.getenv("MARKET_REFRESH_ENABLED", "true").lower() in {"0", "false", "no"},
    )
    parser.add_argument(
        "--disable-investor-flow-refresh",
        action="store_true",
        default=os.getenv("MARKET_INVESTOR_FLOW_REFRESH_ENABLED", "true").lower() in {"0", "false", "no"},
    )
    parser.add_argument(
        "--investor-flow-refresh-hour",
        type=int,
        default=int(os.getenv("MARKET_INVESTOR_FLOW_REFRESH_HOUR_LOCAL", "18")),
    )
    parser.add_argument(
        "--investor-flow-refresh-minute",
        type=int,
        default=int(os.getenv("MARKET_INVESTOR_FLOW_REFRESH_MINUTE_LOCAL", "30")),
    )
    parser.add_argument(
        "--investor-flow-refresh-timezone",
        default=os.getenv("MARKET_INVESTOR_FLOW_REFRESH_TIMEZONE", "Asia/Seoul"),
    )
    args = parser.parse_args()

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    if args.command in {"quote-snapshot", "quote-push"}:
        provider = MarketQuoteProvider(
            cache_ttl_seconds=int(os.getenv("MARKET_QUOTE_CACHE_TTL_SECONDS", str(DEFAULT_QUOTE_CACHE_TTL_SECONDS))),
            stale_after_hours=int(os.getenv("MARKET_QUOTE_STALE_AFTER_HOURS", "36")),
        )
        snapshots = provider.snapshots(args.symbols)
        if args.command == "quote-snapshot":
            print(json.dumps({"items": [snapshot.to_api_dict() for snapshot in snapshots]}, ensure_ascii=False, indent=2))
            return
        client = SpringIngestionClient(os.getenv("SPRING_BASE_URL", "http://localhost:8080"))
        client.publish_quote_snapshots(snapshots)
        return

    if args.command in {"chart-candles", "chart-candles-push"}:
        provider = MarketChartCandleProvider(
            cache_ttl_seconds=int(os.getenv("MARKET_CHART_CACHE_TTL_SECONDS", str(DEFAULT_QUOTE_CACHE_TTL_SECONDS))),
            stale_after_hours=int(os.getenv("MARKET_CHART_STALE_AFTER_HOURS", "36")),
        )
        candle_sets = provider.charts(args.symbols, chart_range=args.chart_range, interval=args.interval)
        if args.command == "chart-candles":
            print(json.dumps({"items": [candle_set.to_api_dict() for candle_set in candle_sets]}, ensure_ascii=False, indent=2))
            return
        client = SpringIngestionClient(os.getenv("SPRING_BASE_URL", "http://localhost:8080"))
        client.publish_chart_candles(candle_sets)
        return

    if args.command in {"investor-flows", "investor-flows-push"}:
        provider = MarketInvestorFlowProvider(
            flow_client=build_investor_flow_client(args.investor_flow_provider),
            stale_after_hours=int(os.getenv("MARKET_INVESTOR_FLOW_STALE_AFTER_HOURS", "96")),
        )
        snapshots = provider.snapshots(
            args.investor_flow_symbols,
            trade_date=_parse_trade_date(args.trade_date),
            limit=args.investor_flow_limit,
        )
        if args.command == "investor-flows":
            print(json.dumps({"items": [snapshot.to_api_dict() for snapshot in snapshots]}, ensure_ascii=False, indent=2))
            return
        client = SpringIngestionClient(os.getenv("SPRING_BASE_URL", "http://localhost:8080"))
        client.publish_investor_flows(snapshots)
        return

    pipeline = build_pipeline()
    if args.command == "run-once":
        results = await pipeline.run_once()
        for result in results:
            print(result)
    else:
        market_refresh_job = None
        investor_flow_refresh_job = None
        market_client = SpringIngestionClient(os.getenv("SPRING_BASE_URL", "http://localhost:8080"))
        if not args.disable_market_refresh:
            market_refresh_job = build_market_refresh_job(
                client=market_client,
                symbols=args.symbols,
                chart_range=args.chart_range,
                chart_interval=args.interval,
                quote_cache_ttl_seconds=int(os.getenv("MARKET_QUOTE_CACHE_TTL_SECONDS", str(DEFAULT_QUOTE_CACHE_TTL_SECONDS))),
                quote_stale_after_hours=int(os.getenv("MARKET_QUOTE_STALE_AFTER_HOURS", "36")),
                chart_cache_ttl_seconds=int(os.getenv("MARKET_CHART_CACHE_TTL_SECONDS", str(DEFAULT_QUOTE_CACHE_TTL_SECONDS))),
                chart_stale_after_hours=int(os.getenv("MARKET_CHART_STALE_AFTER_HOURS", "36")),
            )
        if not args.disable_investor_flow_refresh:
            investor_flow_refresh_job = build_investor_flow_refresh_job(
                client=market_client,
                symbols=args.investor_flow_symbols,
                limit=args.investor_flow_limit,
                provider_name=args.investor_flow_provider,
                stale_after_hours=int(os.getenv("MARKET_INVESTOR_FLOW_STALE_AFTER_HOURS", "96")),
            )
        await serve(
            pipeline,
            interval_minutes=args.interval_minutes,
            market_refresh_job=market_refresh_job,
            market_interval_minutes=args.market_refresh_interval_minutes,
            investor_flow_refresh_job=investor_flow_refresh_job,
            investor_flow_hour=args.investor_flow_refresh_hour,
            investor_flow_minute=args.investor_flow_refresh_minute,
            investor_flow_timezone=args.investor_flow_refresh_timezone,
        )


def _parse_trade_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
