from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import Protocol

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.market_investor_flows import (
    InvestorFlowSnapshot,
    MarketInvestorFlowProvider,
    build_investor_flow_client,
)
from youbuyfirst_pipeline.market_quotes import ChartCandleSet, MarketChartCandleProvider, MarketQuoteProvider, QuoteSnapshot

logger = logging.getLogger(__name__)


class QuoteSnapshotProvider(Protocol):
    def snapshots(self, symbols: list[str]) -> list[QuoteSnapshot]:
        ...


class ChartCandleProvider(Protocol):
    def charts(self, symbols: list[str], chart_range: str, interval: str) -> list[ChartCandleSet]:
        ...


class InvestorFlowProvider(Protocol):
    def snapshots(self, symbols: list[str], limit: int) -> list[InvestorFlowSnapshot]:
        ...


class MarketRefreshClient(Protocol):
    def publish_quote_snapshots(self, snapshots: list[QuoteSnapshot]) -> None:
        ...

    def publish_chart_candles(self, candle_sets: list[ChartCandleSet]) -> None:
        ...

    def publish_investor_flows(self, snapshots: list[InvestorFlowSnapshot]) -> None:
        ...

    def claim_chart_candle_refresh_requests(self, limit: int) -> list[dict]:
        ...

    def mark_chart_candle_refresh_failed(self, request: dict, error_message: str) -> None:
        ...


@dataclass(frozen=True)
class MarketRefreshResult:
    quote_status: str
    chart_status: str
    quote_count: int
    chart_count: int


@dataclass(frozen=True)
class InvestorFlowRefreshResult:
    status: str
    count: int


@dataclass(frozen=True)
class ChartCandleOnDemandRefreshResult:
    status: str
    count: int


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


class InvestorFlowRefreshJob:
    def __init__(
            self,
            provider: InvestorFlowProvider,
            client: MarketRefreshClient,
            symbols: list[str],
            limit: int,
    ) -> None:
        self.provider = provider
        self.client = client
        self.symbols = symbols
        self.limit = limit

    def run_once(self) -> InvestorFlowRefreshResult:
        status = "OK"
        count = 0
        try:
            snapshots = self.provider.snapshots(self.symbols, limit=self.limit)
            if snapshots:
                self.client.publish_investor_flows(snapshots)
            count = len(snapshots)
        except Exception:
            status = "PROVIDER_ERROR"
            logger.exception("market investor flow refresh failed")

        result = InvestorFlowRefreshResult(status=status, count=count)
        logger.info(
            "market investor flow refresh finished; status=%s count=%s",
            result.status,
            result.count,
        )
        return result


class ChartCandleOnDemandRefreshJob:
    def __init__(
            self,
            provider: ChartCandleProvider,
            client: MarketRefreshClient,
            claim_limit: int,
    ) -> None:
        self.provider = provider
        self.client = client
        self.claim_limit = claim_limit

    def run_once(self) -> ChartCandleOnDemandRefreshResult:
        try:
            requests = self.client.claim_chart_candle_refresh_requests(self.claim_limit)
        except Exception as exc:
            logger.warning("market chart on-demand refresh claim skipped; backend unavailable: %s", exc)
            return ChartCandleOnDemandRefreshResult(status="CLIENT_ERROR", count=0)

        if not requests:
            return ChartCandleOnDemandRefreshResult(status="OK", count=0)

        status = "OK"
        count = 0
        grouped: dict[tuple[str, str], list[dict]] = {}
        for request in requests:
            key = (str(request.get("range", "3M")), str(request.get("interval", "1d")))
            grouped.setdefault(key, []).append(request)

        for (chart_range, interval), group in grouped.items():
            symbols = [str(request.get("symbol", "")).strip().upper() for request in group if request.get("symbol")]
            if not symbols:
                continue
            try:
                candle_sets = self.provider.charts(symbols, chart_range=chart_range, interval=interval)
                candle_sets = _attach_refresh_attempt_tokens(candle_sets, group)
                self.client.publish_chart_candles(candle_sets)
                count += len(candle_sets)
            except Exception as exc:
                status = "PROVIDER_ERROR"
                logger.exception("market chart on-demand refresh failed")
                for request in group:
                    self.client.mark_chart_candle_refresh_failed(request, str(exc))

        result = ChartCandleOnDemandRefreshResult(status=status, count=count)
        logger.info(
            "market chart on-demand refresh finished; status=%s count=%s claimed=%s",
            result.status,
            result.count,
            len(requests),
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


def build_investor_flow_refresh_job(
        *,
        client: SpringIngestionClient,
        symbols: list[str],
        limit: int,
        stale_after_hours: int,
        provider_name: str | None = None,
) -> InvestorFlowRefreshJob:
    return InvestorFlowRefreshJob(
        provider=MarketInvestorFlowProvider(
            flow_client=build_investor_flow_client(provider_name),
            stale_after_hours=stale_after_hours,
        ),
        client=client,
        symbols=symbols,
        limit=limit,
    )


def _attach_refresh_attempt_tokens(candle_sets: list[ChartCandleSet], requests: list[dict]) -> list[ChartCandleSet]:
    tokens_by_symbol: dict[str, str] = {}
    for request in requests:
        token = str(request.get("refreshAttemptToken", "")).strip()
        symbol = str(request.get("symbol", "")).strip().upper()
        if token and symbol:
            tokens_by_symbol[symbol] = token
    if not tokens_by_symbol:
        return candle_sets
    return [
        replace(candle_set, refresh_attempt_token=tokens_by_symbol.get(candle_set.symbol.upper()))
        if tokens_by_symbol.get(candle_set.symbol.upper())
        else candle_set
        for candle_set in candle_sets
    ]


def build_chart_candle_on_demand_refresh_job(
        *,
        client: SpringIngestionClient,
        claim_limit: int,
        chart_cache_ttl_seconds: int,
        chart_stale_after_hours: int,
) -> ChartCandleOnDemandRefreshJob:
    return ChartCandleOnDemandRefreshJob(
        provider=MarketChartCandleProvider(
            cache_ttl_seconds=chart_cache_ttl_seconds,
            stale_after_hours=chart_stale_after_hours,
        ),
        client=client,
        claim_limit=claim_limit,
    )
