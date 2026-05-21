from youbuyfirst_pipeline.market_scheduler import MarketRefreshJob
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
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str, str]] = []

    def charts(self, symbols: list[str], chart_range: str, interval: str) -> list[str]:
        self.calls.append((symbols, chart_range, interval))
        return [f"chart:{symbol}:{chart_range}:{interval}" for symbol in symbols]


class _Client:
    def __init__(self) -> None:
        self.quote_batches: list[list[str]] = []
        self.chart_batches: list[list[str]] = []

    def publish_quote_snapshots(self, snapshots: list[str]) -> None:
        self.quote_batches.append(snapshots)

    def publish_chart_candles(self, candle_sets: list[str]) -> None:
        self.chart_batches.append(candle_sets)


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

    configure_scheduler(
        scheduler,
        pipeline=_Pipeline(),
        crawl_interval_minutes=30,
        market_refresh_job=market_job,
        market_interval_minutes=10,
    )

    jobs = {job.id: job for job in scheduler.get_jobs()}
    assert jobs["community-crawl"].trigger.interval.total_seconds() == 30 * 60
    assert jobs["market-refresh"].trigger.interval.total_seconds() == 10 * 60
