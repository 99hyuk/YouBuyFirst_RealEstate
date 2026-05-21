from datetime import datetime, timezone
from decimal import Decimal

from youbuyfirst_pipeline.market_quotes import (
    InstrumentMetadata,
    MarketQuoteProvider,
    QuoteBar,
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
