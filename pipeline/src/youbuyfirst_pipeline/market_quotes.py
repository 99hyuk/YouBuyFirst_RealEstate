from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable, Protocol


DEFAULT_QUOTE_CACHE_TTL_SECONDS = 10 * 60
DEFAULT_SYMBOLS = ["005930.KS", "000660.KS", "069500.KS", "AAPL", "NVDA"]


class QuoteProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class QuoteBar:
    timestamp: datetime
    close: Decimal
    volume: int
    previous_close: Decimal | None = None


@dataclass(frozen=True)
class InstrumentMetadata:
    symbol: str
    name: str
    market: str
    currency: str


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    name: str
    market: str
    currency: str
    price: Decimal
    change: Decimal
    change_pct: Decimal
    volume: int
    as_of: datetime
    provider: str
    delay_label: str
    stale: bool
    data_status: str

    def to_api_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "currency": self.currency,
            "price": _decimal_number(self.price),
            "change": _decimal_number(self.change),
            "changePct": _decimal_number(self.change_pct),
            "volume": self.volume,
            "asOf": _iso(self.as_of),
            "provider": self.provider,
            "delayLabel": self.delay_label,
            "stale": self.stale,
            "dataStatus": self.data_status,
        }


class QuoteHistoryClient(Protocol):
    def history(self, symbol: str) -> list[QuoteBar]:
        ...


class MetadataProvider(Protocol):
    def resolve(self, symbol: str) -> InstrumentMetadata:
        ...


class YFinanceHistoryClient:
    def __init__(self, period: str = "1d", interval: str = "5m") -> None:
        self.period = period
        self.interval = interval

    def history(self, symbol: str) -> list[QuoteBar]:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise QuoteProviderError("yfinance is required for quote snapshots") from exc

        ticker = yf.Ticker(symbol)
        frame = ticker.history(period=self.period, interval=self.interval, auto_adjust=False)
        if frame is None or frame.empty:
            raise QuoteProviderError(f"empty yfinance history for {symbol}")
        if "Close" not in frame.columns:
            raise QuoteProviderError(f"yfinance history for {symbol} has no Close column")

        frame = frame.dropna(subset=["Close"])
        if frame.empty:
            raise QuoteProviderError(f"no usable yfinance bars for {symbol}")

        latest_timestamp = _as_utc_datetime(frame.index[-1])
        latest_row = frame.iloc[-1]
        previous_row = frame.iloc[-2] if len(frame) >= 2 else latest_row
        fast_info = ticker.fast_info
        close = _fast_info_decimal(fast_info, "lastPrice") or Decimal(str(latest_row["Close"]))
        previous_close = (
            _fast_info_decimal(fast_info, "regularMarketPreviousClose")
            or _fast_info_decimal(fast_info, "previousClose")
            or Decimal(str(previous_row["Close"]))
        )
        volume = _fast_info_int(fast_info, "lastVolume")
        if volume is None:
            volume = int(latest_row.get("Volume", 0) or 0)
        return [
            QuoteBar(timestamp=latest_timestamp, close=previous_close, volume=0),
            QuoteBar(timestamp=latest_timestamp, close=close, volume=volume, previous_close=previous_close),
        ]


class FinanceDataReaderMetadataProvider:
    def __init__(self, stock_listing_loader: Callable[[], object] | None = None) -> None:
        self.stock_listing_loader = stock_listing_loader
        self._krx_listing = None

    def resolve(self, symbol: str) -> InstrumentMetadata:
        normalized = symbol.strip().upper()
        market, currency = _infer_market_currency(normalized)
        known = _KNOWN_METADATA.get(normalized)
        if known:
            return known

        if market == "KR":
            name = self._krx_name(_krx_code(normalized))
            if name and _usable_name(name):
                return InstrumentMetadata(symbol=normalized, name=name, market=market, currency=currency)

        return InstrumentMetadata(symbol=normalized, name=normalized, market=market, currency=currency)

    def _krx_name(self, code: str) -> str | None:
        listing = self._load_krx_listing()
        if listing is None:
            return None

        try:
            code_series = listing["Code"].astype(str).str.zfill(6)
            matches = listing[code_series == code.zfill(6)]
            if matches.empty:
                return None
            row = matches.iloc[0]
            value = row.get("Name") or row.get("NameEng")
            return str(value) if value else None
        except Exception:
            return None

    def _load_krx_listing(self):
        if self._krx_listing is not None:
            return self._krx_listing
        if self.stock_listing_loader is not None:
            self._krx_listing = self.stock_listing_loader()
            return self._krx_listing
        try:
            import FinanceDataReader as fdr
        except ImportError:
            return None
        self._krx_listing = fdr.StockListing("KRX")
        return self._krx_listing


class MarketQuoteProvider:
    def __init__(
            self,
            history_client: QuoteHistoryClient | None = None,
            metadata_provider: MetadataProvider | None = None,
            cache_ttl_seconds: int = DEFAULT_QUOTE_CACHE_TTL_SECONDS,
            stale_after_hours: int = 36,
    ) -> None:
        self.history_client = history_client or YFinanceHistoryClient()
        self.metadata_provider = metadata_provider or FinanceDataReaderMetadataProvider()
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.stale_after = timedelta(hours=stale_after_hours)
        self._cache: dict[str, tuple[datetime, QuoteSnapshot]] = {}

    def snapshot(self, symbol: str, now: datetime | None = None) -> QuoteSnapshot:
        current_time = _as_utc_datetime(now or datetime.now(timezone.utc))
        normalized = symbol.strip().upper()
        cached = self._cache.get(normalized)
        if cached and current_time - cached[0] < self.cache_ttl:
            return cached[1]

        bars = sorted(self.history_client.history(normalized), key=lambda bar: bar.timestamp)
        if not bars:
            raise QuoteProviderError(f"no quote bars for {normalized}")
        current = bars[-1]
        previous = bars[-2] if len(bars) >= 2 else current
        previous_close = current.previous_close or previous.close
        change = current.close - previous_close
        change_pct = Decimal("0")
        if previous_close != 0:
            change_pct = (change / previous_close) * Decimal("100")

        metadata = self.metadata_provider.resolve(normalized)
        stale = current_time - _as_utc_datetime(current.timestamp) > self.stale_after
        snapshot = QuoteSnapshot(
            symbol=metadata.symbol,
            name=metadata.name,
            market=metadata.market,
            currency=metadata.currency,
            price=current.close,
            change=change,
            change_pct=change_pct,
            volume=current.volume,
            as_of=_as_utc_datetime(current.timestamp),
            provider=_provider_name(metadata.market),
            delay_label=_delay_label(metadata.symbol, metadata.market),
            stale=stale,
            data_status="STALE" if stale else "OK",
        )
        self._cache[normalized] = (current_time, snapshot)
        return snapshot

    def snapshots(self, symbols: list[str], now: datetime | None = None) -> list[QuoteSnapshot]:
        return [self.snapshot(symbol, now=now) for symbol in symbols]


def configured_quote_symbols(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_SYMBOLS
    return [symbol.strip().upper() for symbol in value.split(",") if symbol.strip()]


def _infer_market_currency(symbol: str) -> tuple[str, str]:
    if symbol.endswith(".KS") or symbol.endswith(".KQ") or _krx_code(symbol).isdigit():
        return "KR", "KRW"
    return "US", "USD"


def _krx_code(symbol: str) -> str:
    return symbol.split(".", 1)[0]


def _provider_name(market: str) -> str:
    if market == "KR":
        return "yfinance+FinanceDataReader"
    return "yfinance"


def _delay_label(symbol: str, market: str) -> str:
    if symbol.endswith(".KS") or symbol.endswith(".KQ") or market == "KR":
        return "Yahoo Finance delayed up to 30 min"
    return "Yahoo Finance 10 min refresh snapshot"


def _usable_name(value: str) -> bool:
    return "\ufffd" not in value and value.strip() != ""


def _fast_info_decimal(fast_info, key: str) -> Decimal | None:
    try:
        value = fast_info.get(key)
    except Exception:
        return None
    if value is None:
        return None
    return Decimal(str(value))


def _fast_info_int(fast_info, key: str) -> int | None:
    try:
        value = fast_info.get(key)
    except Exception:
        return None
    if value is None:
        return None
    return int(value)


def _as_utc_datetime(value) -> datetime:
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, time.min)
    if not isinstance(value, datetime):
        raise TypeError(f"expected datetime-like value, got {type(value)!r}")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _decimal_number(value: Decimal) -> int | float:
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if quantized == quantized.to_integral_value():
        return int(quantized)
    return float(quantized)


def _iso(value: datetime) -> str:
    return _as_utc_datetime(value).isoformat().replace("+00:00", "Z")


_KNOWN_METADATA = {
    "005930.KS": InstrumentMetadata("005930.KS", "Samsung Electronics", "KR", "KRW"),
    "000660.KS": InstrumentMetadata("000660.KS", "SK hynix", "KR", "KRW"),
    "069500.KS": InstrumentMetadata("069500.KS", "KODEX 200", "KR", "KRW"),
    "AAPL": InstrumentMetadata("AAPL", "Apple", "US", "USD"),
    "NVDA": InstrumentMetadata("NVDA", "NVIDIA", "US", "USD"),
}
