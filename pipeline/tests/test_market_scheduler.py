from datetime import datetime, timezone
from decimal import Decimal

from youbuyfirst_pipeline.market_quotes import ChartCandleBar, ChartCandleSet
from youbuyfirst_pipeline.market_scheduler import ChartCandleOnDemandRefreshJob, InvestorFlowRefreshJob, MarketRefreshJob
from youbuyfirst_pipeline.scheduler import configure_scheduler


class _QuoteProvider:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[list[str]] = []

    def snapshots(self, symbols: list[str]) -> list[str]:
        self.calls.append(symbols)
        if self.fail:
            raise RuntimeError("quote provider failed")
        return [f"quote:{symbol}" for symbol in symbols]


class _ChartProvider:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[list[str], str, str]] = []

    def charts(self, symbols: list[str], chart_range: str, interval: str) -> list[str]:
        self.calls.append((symbols, chart_range, interval))
        if self.fail:
            raise RuntimeError("chart provider failed")
        return [f"chart:{symbol}:{chart_range}:{interval}" for symbol in symbols]


class _RealChartProvider:
    def charts(self, symbols: list[str], chart_range: str, interval: str) -> list[ChartCandleSet]:
        return [
            ChartCandleSet(
                symbol=symbol,
                name=symbol,
                market="US",
                currency="USD",
                chart_range=chart_range,
                interval=interval,
                provider="test",
                delay_label="test",
                as_of=datetime(2026, 5, 24, tzinfo=timezone.utc),
                stale=False,
                data_status="OK",
                bars=[
                    ChartCandleBar(
                        date="2026-05-24",
                        open=Decimal("10.00"),
                        high=Decimal("11.00"),
                        low=Decimal("9.00"),
                        close=Decimal("10.50"),
                        volume=1000,
                    )
                ],
            )
            for symbol in symbols
        ]


class _InvestorFlowProvider:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[list[str]] = []

    def snapshots(self, symbols: list[str], limit: int) -> list[str]:
        self.calls.append([*symbols, f"limit:{limit}"])
        if self.fail:
            raise RuntimeError("investor flow provider failed")
        return [f"flow:{symbol}" for symbol in symbols]


class _Client:
    def __init__(self, fail_claim: bool = False) -> None:
        self.fail_claim = fail_claim
        self.quote_batches: list[list[str]] = []
        self.chart_batches: list[list[str]] = []
        self.investor_flow_batches: list[list[str]] = []
        self.chart_refresh_requests: list[dict] = []
        self.failed_chart_refreshes: list[dict] = []

    def publish_quote_snapshots(self, snapshots: list[str]) -> None:
        self.quote_batches.append(snapshots)

    def publish_chart_candles(self, candle_sets: list[str]) -> None:
        self.chart_batches.append(candle_sets)

    def publish_investor_flows(self, snapshots: list[str]) -> None:
        self.investor_flow_batches.append(snapshots)

    def claim_chart_candle_refresh_requests(self, limit: int) -> list[dict]:
        if self.fail_claim:
            raise RuntimeError("backend unavailable")
        claimed = self.chart_refresh_requests[:limit]
        self.chart_refresh_requests = self.chart_refresh_requests[limit:]
        return claimed

    def mark_chart_candle_refresh_failed(self, request: dict, error_message: str) -> None:
        self.failed_chart_refreshes.append({**request, "errorMessage": error_message})


class _Pipeline:
    async def run_once(self) -> list[str]:
        return []


def test_market_refresh_job_pushes_quotes_and_chart_candles():
    quote_provider = _QuoteProvider()
    chart_provider = _ChartProvider()
    client = _Client()
    job = MarketRefreshJob(
        quote_provider=quote_provider,
        chart_provider=chart_provider,
        client=client,
        symbols=["005930.KS", "AAPL"],
        chart_range="3M",
        chart_interval="1d",
    )

    result = job.run_once()

    assert result.quote_status == "OK"
    assert result.chart_status == "OK"
    assert result.quote_count == 2
    assert result.chart_count == 2
    assert quote_provider.calls == [["005930.KS", "AAPL"]]
    assert chart_provider.calls == [(["005930.KS", "AAPL"], "3M", "1d")]
    assert client.quote_batches == [["quote:005930.KS", "quote:AAPL"]]
    assert client.chart_batches == [["chart:005930.KS:3M:1d", "chart:AAPL:3M:1d"]]


def test_market_refresh_job_keeps_chart_push_when_quote_push_fails():
    quote_provider = _QuoteProvider(fail=True)
    chart_provider = _ChartProvider()
    client = _Client()
    job = MarketRefreshJob(
        quote_provider=quote_provider,
        chart_provider=chart_provider,
        client=client,
        symbols=["005930.KS"],
        chart_range="3M",
        chart_interval="1d",
    )

    result = job.run_once()

    assert result.quote_status == "PROVIDER_ERROR"
    assert result.chart_status == "OK"
    assert result.quote_count == 0
    assert result.chart_count == 1
    assert client.quote_batches == []
    assert client.chart_batches == [["chart:005930.KS:3M:1d"]]


def test_investor_flow_refresh_job_pushes_previous_day_flows():
    provider = _InvestorFlowProvider()
    client = _Client()
    job = InvestorFlowRefreshJob(
        provider=provider,
        client=client,
        symbols=["005930.KS", "000660.KS"],
        limit=20,
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.count == 2
    assert provider.calls == [["005930.KS", "000660.KS", "limit:20"]]
    assert client.investor_flow_batches == [["flow:005930.KS", "flow:000660.KS"]]


def test_investor_flow_refresh_job_reports_provider_error():
    client = _Client()
    job = InvestorFlowRefreshJob(
        provider=_InvestorFlowProvider(fail=True),
        client=client,
        symbols=["005930.KS"],
        limit=20,
    )

    result = job.run_once()

    assert result.status == "PROVIDER_ERROR"
    assert result.count == 0
    assert client.investor_flow_batches == []


def test_chart_candle_on_demand_refresh_job_claims_and_pushes_grouped_requests():
    provider = _ChartProvider()
    client = _Client()
    client.chart_refresh_requests = [
        {"symbol": "MSFT", "range": "1M", "interval": "1d"},
        {"symbol": "TSLA", "range": "1M", "interval": "1d"},
        {"symbol": "005930.KS", "range": "3M", "interval": "1d"},
    ]
    job = ChartCandleOnDemandRefreshJob(provider=provider, client=client, claim_limit=20)

    result = job.run_once()

    assert result.status == "OK"
    assert result.count == 3
    assert provider.calls == [
        (["MSFT", "TSLA"], "1M", "1d"),
        (["005930.KS"], "3M", "1d"),
    ]
    assert client.chart_batches == [
        ["chart:MSFT:1M:1d", "chart:TSLA:1M:1d"],
        ["chart:005930.KS:3M:1d"],
    ]
    assert client.failed_chart_refreshes == []


def test_chart_candle_on_demand_refresh_job_marks_claimed_requests_failed_on_provider_error():
    client = _Client()
    client.chart_refresh_requests = [{"symbol": "MSFT", "range": "1M", "interval": "1d"}]
    job = ChartCandleOnDemandRefreshJob(provider=_ChartProvider(fail=True), client=client, claim_limit=20)

    result = job.run_once()

    assert result.status == "PROVIDER_ERROR"
    assert result.count == 0
    assert client.chart_batches == []
    assert client.failed_chart_refreshes == [
        {
            "symbol": "MSFT",
            "range": "1M",
            "interval": "1d",
            "errorMessage": "chart provider failed",
        }
    ]


def test_chart_candle_on_demand_refresh_job_attaches_attempt_tokens_to_pushed_candles():
    client = _Client()
    client.chart_refresh_requests = [
        {"symbol": "MSFT", "range": "1M", "interval": "1d", "refreshAttemptToken": "token-msft"},
    ]
    job = ChartCandleOnDemandRefreshJob(provider=_RealChartProvider(), client=client, claim_limit=20)

    result = job.run_once()

    assert result.status == "OK"
    assert result.count == 1
    assert client.chart_batches[0][0].refresh_attempt_token == "token-msft"
    assert client.chart_batches[0][0].to_request_dict()["refreshAttemptToken"] == "token-msft"


def test_chart_candle_on_demand_refresh_job_skips_when_claim_endpoint_is_unavailable():
    provider = _ChartProvider()
    client = _Client(fail_claim=True)
    job = ChartCandleOnDemandRefreshJob(provider=provider, client=client, claim_limit=20)

    result = job.run_once()

    assert result.status == "CLIENT_ERROR"
    assert result.count == 0
    assert provider.calls == []
    assert client.chart_batches == []
    assert client.failed_chart_refreshes == []


def test_configure_scheduler_registers_market_refresh_interval_job():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler(timezone="UTC")
    market_job = MarketRefreshJob(
        quote_provider=_QuoteProvider(),
        chart_provider=_ChartProvider(),
        client=_Client(),
        symbols=["005930.KS"],
        chart_range="3M",
        chart_interval="1d",
    )
    investor_flow_job = InvestorFlowRefreshJob(
        provider=_InvestorFlowProvider(),
        client=_Client(),
        symbols=["005930.KS"],
        limit=20,
    )
    on_demand_chart_job = ChartCandleOnDemandRefreshJob(
        provider=_ChartProvider(),
        client=_Client(),
        claim_limit=20,
    )

    configure_scheduler(
        scheduler,
        pipeline=_Pipeline(),
        crawl_interval_minutes=30,
        market_refresh_job=market_job,
        market_interval_minutes=10,
        investor_flow_refresh_job=investor_flow_job,
        investor_flow_hour=18,
        investor_flow_minute=30,
        chart_on_demand_refresh_job=on_demand_chart_job,
        chart_on_demand_interval_seconds=60,
    )

    jobs = {job.id: job for job in scheduler.get_jobs()}
    assert jobs["community-crawl"].trigger.interval.total_seconds() == 30 * 60
    assert jobs["market-refresh"].trigger.interval.total_seconds() == 10 * 60
    assert jobs["market-chart-on-demand-refresh"].trigger.interval.total_seconds() == 60
    assert "market-investor-flow-refresh" in jobs
    assert "hour='18'" in str(jobs["market-investor-flow-refresh"].trigger)
    assert "minute='30'" in str(jobs["market-investor-flow-refresh"].trigger)
