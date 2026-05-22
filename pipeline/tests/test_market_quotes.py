from datetime import datetime, timezone
from decimal import Decimal

from youbuyfirst_pipeline.market_quotes import (
    ChartCandleBar,
    InstrumentMetadata,
    MarketChartCandleProvider,
    MarketQuoteProvider,
    QuoteBar,
    YFinanceChartCandleClient,
    YFinanceHistoryClient,
)


class _FakeHistoryClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def history(self, symbol: str) -> list[QuoteBar]:
        self.calls.append(symbol)
        return [
            QuoteBar(
                timestamp=datetime(2026, 5, 18, tzinfo=timezone.utc),
                close=Decimal("195.00"),
                volume=39000000,
            ),
            QuoteBar(
                timestamp=datetime(2026, 5, 19, tzinfo=timezone.utc),
                close=Decimal("198.12"),
                volume=42123456,
            ),
        ]


class _FakeMetadataProvider:
    def resolve(self, symbol: str) -> InstrumentMetadata:
        return InstrumentMetadata(symbol=symbol, name="Apple", market="US", currency="USD")


class _FakeKoreaMetadataProvider:
    def resolve(self, symbol: str) -> InstrumentMetadata:
        return InstrumentMetadata(symbol=symbol, name="Samsung Electronics", market="KR", currency="KRW")


class _FakeChartCandleClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def candles(self, symbol: str, chart_range: str, interval: str) -> list[ChartCandleBar]:
        self.calls.append((symbol, chart_range, interval))
        return [
            ChartCandleBar(
                date="2026-05-20",
                open=Decimal("280000"),
                high=Decimal("301000"),
                low=Decimal("279000"),
                close=Decimal("295500"),
                volume=24688716,
            ),
            ChartCandleBar(
                date="2026-05-21",
                open=Decimal("295500"),
                high=Decimal("302000"),
                low=Decimal("292000"),
                close=Decimal("297750"),
                volume=22059084,
            ),
        ]


def test_market_quote_provider_builds_frontend_snapshot_and_uses_cache():
    history = _FakeHistoryClient()
    provider = MarketQuoteProvider(
        history_client=history,
        metadata_provider=_FakeMetadataProvider(),
        cache_ttl_seconds=300,
    )

    first = provider.snapshot("AAPL", now=datetime(2026, 5, 19, 1, tzinfo=timezone.utc))
    second = provider.snapshot("AAPL", now=datetime(2026, 5, 19, 1, 1, tzinfo=timezone.utc))

    assert history.calls == ["AAPL"]
    assert first == second
    assert first.to_api_dict() == {
        "symbol": "AAPL",
        "name": "Apple",
        "market": "US",
        "currency": "USD",
        "price": 198.12,
        "change": 3.12,
        "changePct": 1.6,
        "volume": 42123456,
        "asOf": "2026-05-19T00:00:00Z",
        "provider": "yfinance",
        "delayLabel": "Yahoo Finance 10 min refresh snapshot",
        "stale": False,
        "dataStatus": "OK",
    }


def test_market_quote_provider_default_cache_refreshes_after_ten_minutes():
    history = _FakeHistoryClient()
    provider = MarketQuoteProvider(
        history_client=history,
        metadata_provider=_FakeMetadataProvider(),
    )

    provider.snapshot("AAPL", now=datetime(2026, 5, 19, 1, tzinfo=timezone.utc))
    provider.snapshot("AAPL", now=datetime(2026, 5, 19, 1, 9, tzinfo=timezone.utc))
    provider.snapshot("AAPL", now=datetime(2026, 5, 19, 1, 10, 1, tzinfo=timezone.utc))

    assert history.calls == ["AAPL", "AAPL"]


def test_market_quote_provider_labels_korea_quotes_as_up_to_thirty_minutes_delayed():
    provider = MarketQuoteProvider(
        history_client=_FakeHistoryClient(),
        metadata_provider=_FakeKoreaMetadataProvider(),
    )

    snapshot = provider.snapshot("005930.KS", now=datetime(2026, 5, 19, 1, tzinfo=timezone.utc))

    assert snapshot.to_api_dict()["delayLabel"] == "Yahoo Finance delayed up to 30 min"


def test_market_quote_provider_uses_previous_close_for_daily_change():
    history = _FakeHistoryClient()
    history.history = lambda symbol: [
        QuoteBar(
            timestamp=datetime(2026, 5, 19, tzinfo=timezone.utc),
            close=Decimal("199.00"),
            volume=0,
        ),
        QuoteBar(
            timestamp=datetime(2026, 5, 19, 1, tzinfo=timezone.utc),
            close=Decimal("203.00"),
            volume=100,
            previous_close=Decimal("200.00"),
        ),
    ]
    provider = MarketQuoteProvider(
        history_client=history,
        metadata_provider=_FakeMetadataProvider(),
    )

    snapshot = provider.snapshot("AAPL", now=datetime(2026, 5, 19, 1, 10, tzinfo=timezone.utc))

    assert snapshot.to_api_dict()["change"] == 3
    assert snapshot.to_api_dict()["changePct"] == 1.5


def test_yfinance_history_client_defaults_to_intraday_quote_bars():
    client = YFinanceHistoryClient()

    assert client.period == "1d"
    assert client.interval == "5m"


def test_market_chart_candle_provider_builds_display_only_contract():
    client = _FakeChartCandleClient()
    provider = MarketChartCandleProvider(
        candle_client=client,
        metadata_provider=_FakeKoreaMetadataProvider(),
    )

    response = provider.chart("005930.KS", chart_range="3M", interval="1d").to_api_dict()

    assert client.calls == [("005930.KS", "3M", "1d")]
    assert response == {
        "symbol": "005930.KS",
        "name": "Samsung Electronics",
        "market": "KR",
        "currency": "KRW",
        "range": "3M",
        "interval": "1d",
        "provider": "yfinance+FinanceDataReader",
        "delayLabel": "Yahoo Finance delayed up to 30 min",
        "asOf": "2026-05-21T00:00:00Z",
        "stale": False,
        "dataStatus": "OK",
        "bars": [
            {
                "date": "2026-05-20",
                "open": 280000,
                "high": 301000,
                "low": 279000,
                "close": 295500,
                "volume": 24688716,
            },
            {
                "date": "2026-05-21",
                "open": 295500,
                "high": 302000,
                "low": 292000,
                "close": 297750,
                "volume": 22059084,
            },
        ],
        "displayPolicy": {
            "displayOnly": True,
            "rawMinute": False,
            "downloadable": False,
            "maxBars": 66,
        },
    }
    assert "individual" not in str(response)
    assert "foreign" not in str(response)
    assert "institution" not in str(response)


def test_market_chart_candle_provider_rejects_minute_interval():
    provider = MarketChartCandleProvider(
        candle_client=_FakeChartCandleClient(),
        metadata_provider=_FakeKoreaMetadataProvider(),
    )

    try:
        provider.chart("005930.KS", chart_range="3M", interval="5m")
    except ValueError as exc:
        assert "unsupported chart interval" in str(exc)
    else:
        raise AssertionError("minute interval should be rejected")


def test_yfinance_chart_candle_client_maps_public_range_to_yfinance_period():
    client = YFinanceChartCandleClient()

    assert client.period_for("3M") == "3mo"
    assert client.period_for("1Y") == "1y"
    assert client.period_for("3Y") == "5y"
