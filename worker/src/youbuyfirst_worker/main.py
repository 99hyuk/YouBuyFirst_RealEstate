from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from youbuyfirst_worker.client import SpringIngestionClient
from youbuyfirst_worker.crawlers.base import BrowserCapableFetcher
from youbuyfirst_worker.crawlers.fmkorea import FmkoreaAdapter
from youbuyfirst_worker.crawlers.naver import NaverBoardAdapter
from youbuyfirst_worker.instruments import load_instruments
from youbuyfirst_worker.llm import build_llm_provider
from youbuyfirst_worker.matcher import InstrumentMatcher
from youbuyfirst_worker.pipeline import CommunityPipeline
from youbuyfirst_worker.scheduler import serve


def build_pipeline() -> CommunityPipeline:
    load_dotenv()
    user_agent = os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    )
    fetcher = BrowserCapableFetcher(user_agent=user_agent, timeout_seconds=float(os.getenv("CRAWLER_TIMEOUT_SECONDS", "10")))

    instrument_path = Path(os.getenv("INSTRUMENT_CSV_PATH", "data/instruments.sample.csv"))
    instruments = load_instruments(instrument_path)

    configured_naver_codes = os.getenv("NAVER_STOCK_CODES")
    if configured_naver_codes:
        naver_codes = [code.strip() for code in configured_naver_codes.split(",") if code.strip()]
    else:
        naver_codes = [instrument.symbol for instrument in instruments if instrument.market == "KR"]
    adapters = [NaverBoardAdapter(fetcher, stock_code=code) for code in naver_codes]
    adapters.append(FmkoreaAdapter(fetcher, url=os.getenv("FMKOREA_STOCK_URL")))

    matcher = InstrumentMatcher(instruments)
    client = SpringIngestionClient(os.getenv("SPRING_BASE_URL", "http://localhost:8080"))
    return CommunityPipeline(
        adapters=adapters,
        matcher=matcher,
        llm_provider=build_llm_provider(),
        client=client,
    )


async def async_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run-once", "serve"])
    parser.add_argument("--interval-minutes", type=int, default=int(os.getenv("CRAWL_INTERVAL_MINUTES", "30")))
    args = parser.parse_args()

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    pipeline = build_pipeline()
    if args.command == "run-once":
        results = await pipeline.run_once()
        for result in results:
            print(result)
    else:
        await serve(pipeline, interval_minutes=args.interval_minutes)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
