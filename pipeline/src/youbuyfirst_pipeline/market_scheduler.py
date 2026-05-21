from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.market_quotes import ChartCandleSet, MarketChartCandleProvider, MarketQuoteProvider, QuoteSnapshot

logger = logging.getLogger(__name__)


class QuoteSnapshotProvider(Protocol):
    def snapshots(self, symbols: list[str]) -> list[QuoteSnapshot]:
        ...


class ChartCandleProvider(Protocol):
    def charts(self, symbols: list[str], chart_range: str, interval: str) -> list[ChartCandleSet]:
        ...


class MarketRefreshClient(Protocol):
    def publish_quote_snapshots(self, snapshots: list[QuoteSnapshot]) -> None:
        ...

    def publish_chart_candles(self, candle_sets: list[ChartCandleSet]) -> None:
        ...


@dataclass(frozen=True)
class MarketRefreshResult:
    quote_status: str
    chart_status: str
    quote_count: int
    chart_count: int


class MarketRefreshJob:
    def __init__(
            self,
            quote_provider: QuoteSnapshotProvider,
            chart_provider: ChartCandleProvider,
            client: MarketRefreshClient,
            symbols: list[str],
            chart_range: str,
            chart_interval: str,
    ) -> None:
        self.quote_provider = quote_provider
        self.chart_provider = chart_provider
        self.client = client
        self.symbols = symbols
        self.chart_range = chart_range
        self.chart_interval = chart_interval

    def run_once(self) -> MarketRefreshResult:
        quote_status = "OK"
        chart_status = "OK"
        quote_count = 0
        chart_count = 0

        try:
            snapshots = self.quote_provider.snapshots(self.symbols)
            self.client.publish_quote_snapshots(snapshots)
            quote_count = len(snapshots)
        except Exception:
            quote_status = "PROVIDER_ERROR"
            logger.exception("market quote refresh failed")

        try:
            candle_sets = self.chart_provider.charts(
                self.symbols,
                chart_range=self.chart_range,
                interval=self.chart_interval,
            )
            self.client.publish_chart_candles(candle_sets)
            chart_count = len(candle_sets)
        except Exception:
            chart_status = "PROVIDER_ERROR"
            logger.exception("market chart candle refresh failed")

        result = MarketRefreshResult(
            quote_status=quote_status,
            chart_status=chart_status,
            quote_count=quote_count,
            chart_count=chart_count,
        )
        logger.info(
            "market refresh finished; quote_status=%s quote_count=%s chart_status=%s chart_count=%s",
            result.quote_status,
            result.quote_count,
            result.chart_status,
            result.chart_count,
        )
        return result


def build_market_refresh_job(
        *,
        client: SpringIngestionClient,
        symbols: list[str],
        chart_range: str,
        chart_interval: str,
        quote_cache_ttl_seconds: int,
        quote_stale_after_hours: int,
        chart_cache_ttl_seconds: int,
        chart_stale_after_hours: int,
) -> MarketRefreshJob:
    return MarketRefreshJob(
        quote_provider=MarketQuoteProvider(
            cache_ttl_seconds=quote_cache_ttl_seconds,
            stale_after_hours=quote_stale_after_hours,
        ),
        chart_provider=MarketChartCandleProvider(
            cache_ttl_seconds=chart_cache_ttl_seconds,
            stale_after_hours=chart_stale_after_hours,
        ),
        client=client,
        symbols=symbols,
        chart_range=chart_range,
        chart_interval=chart_interval,
    )
