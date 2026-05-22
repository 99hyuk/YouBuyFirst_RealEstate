from __future__ import annotations

import io
import logging
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Protocol

from youbuyfirst_pipeline.market_quotes import FinanceDataReaderMetadataProvider, MetadataProvider

DEFAULT_INVESTOR_FLOW_SYMBOLS = ["005930.KS", "000660.KS", "069500.KS"]

_INDIVIDUAL = "\uac1c\uc778"
_FOREIGN_TOTAL = "\uc678\uad6d\uc778\ud569\uacc4"
_FOREIGN = "\uc678\uad6d\uc778"
_INSTITUTION_TOTAL = "\uae30\uad00\ud569\uacc4"
_INSTITUTION = "\uae30\uad00"


class InvestorFlowProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class InvestorFlowLeg:
    net_amount: Decimal
    net_volume: int

    def to_api_dict(self) -> dict:
        return {
            "netAmount": _decimal_number(self.net_amount),
            "netVolume": self.net_volume,
        }


@dataclass(frozen=True)
class InvestorFlowSnapshot:
    symbol: str
    name: str
    market: str
    currency: str
    trade_date: date
    provider: str
    source_label: str
    delay_label: str
    as_of: datetime
    stale: bool
    data_status: str
    individual: InvestorFlowLeg
    foreign: InvestorFlowLeg
    institution: InvestorFlowLeg

    def to_api_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "currency": self.currency,
            "tradeDate": self.trade_date.isoformat(),
            "provider": self.provider,
            "sourceLabel": self.source_label,
            "delayLabel": self.delay_label,
            "asOf": _iso(self.as_of),
            "stale": self.stale,
            "dataStatus": self.data_status,
            "individual": self.individual.to_api_dict(),
            "foreign": self.foreign.to_api_dict(),
            "institution": self.institution.to_api_dict(),
        }

    def to_request_dict(self) -> dict:
        payload = self.to_api_dict()
        payload.pop("stale")
        return payload


class InvestorFlowClient(Protocol):
    def flow(self, code: str, trade_date: date) -> tuple[InvestorFlowLeg, InvestorFlowLeg, InvestorFlowLeg]:
        ...


class PykrxInvestorFlowClient:
    def flow(self, code: str, trade_date: date) -> tuple[InvestorFlowLeg, InvestorFlowLeg, InvestorFlowLeg]:
        date_key = trade_date.strftime("%Y%m%d")
        previous_logging_disable = logging.root.manager.disable
        try:
            logging.disable(logging.INFO)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                try:
                    from pykrx import stock
                except ImportError as exc:
                    raise InvestorFlowProviderError("pykrx is required for investor flow snapshots") from exc

                value_frame = stock.get_market_trading_value_by_date(date_key, date_key, code)
                volume_frame = stock.get_market_trading_volume_by_date(date_key, date_key, code)
        except InvestorFlowProviderError:
            raise
        except Exception as exc:
            raise InvestorFlowProviderError(f"pykrx investor flow failed for {code} on {date_key}") from exc
        finally:
            logging.disable(previous_logging_disable)

        if value_frame is None or volume_frame is None or value_frame.empty or volume_frame.empty:
            raise InvestorFlowProviderError(f"empty pykrx investor flow for {code} on {date_key}")

        value_row = value_frame.iloc[-1]
        volume_row = volume_frame.iloc[-1]
        return (
            InvestorFlowLeg(
                net_amount=_decimal_from_column(value_row, [_INDIVIDUAL]),
                net_volume=_int_from_column(volume_row, [_INDIVIDUAL]),
            ),
            InvestorFlowLeg(
                net_amount=_decimal_from_column(value_row, [_FOREIGN_TOTAL, _FOREIGN]),
                net_volume=_int_from_column(volume_row, [_FOREIGN_TOTAL, _FOREIGN]),
            ),
            InvestorFlowLeg(
                net_amount=_decimal_from_column(value_row, [_INSTITUTION_TOTAL, _INSTITUTION]),
                net_volume=_int_from_column(volume_row, [_INSTITUTION_TOTAL, _INSTITUTION]),
            ),
        )


class MarketInvestorFlowProvider:
    def __init__(
            self,
            flow_client: InvestorFlowClient | None = None,
            metadata_provider: MetadataProvider | None = None,
            stale_after_hours: int = 96,
    ) -> None:
        self.flow_client = flow_client or PykrxInvestorFlowClient()
        self.metadata_provider = metadata_provider or FinanceDataReaderMetadataProvider()
        self.stale_after = timedelta(hours=stale_after_hours)

    def snapshot(
            self,
            symbol: str,
            trade_date: date | None = None,
            now: datetime | None = None,
    ) -> InvestorFlowSnapshot:
        current_time = _as_utc_datetime(now or datetime.now(timezone.utc))
        normalized = symbol.strip().upper()
        metadata = self.metadata_provider.resolve(normalized)
        target_date = trade_date or previous_weekday(current_time.date())
        as_of = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        stale = current_time - as_of > self.stale_after

        if metadata.market != "KR":
            return _snapshot(
                symbol=metadata.symbol,
                name=metadata.name,
                market=metadata.market,
                currency=metadata.currency,
                trade_date=target_date,
                as_of=as_of,
                stale=True,
                data_status="INSUFFICIENT",
                provider="none",
                source_label="Domestic investor flow only",
            )

        try:
            individual, foreign, institution = self.flow_client.flow(_krx_code(normalized), target_date)
            status = "STALE" if stale else "OK"
        except Exception:
            individual = foreign = institution = InvestorFlowLeg(Decimal("0"), 0)
            status = "PROVIDER_ERROR"

        return _snapshot(
            symbol=metadata.symbol,
            name=metadata.name,
            market=metadata.market,
            currency=metadata.currency,
            trade_date=target_date,
            as_of=as_of,
            stale=stale,
            data_status=status,
            provider="pykrx",
            source_label="KRX investor trading by date via pykrx",
            individual=individual,
            foreign=foreign,
            institution=institution,
        )

    def snapshots(
            self,
            symbols: list[str],
            trade_date: date | None = None,
            now: datetime | None = None,
    ) -> list[InvestorFlowSnapshot]:
        return [self.snapshot(symbol, trade_date=trade_date, now=now) for symbol in symbols]


def configured_investor_flow_symbols(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_INVESTOR_FLOW_SYMBOLS
    return [symbol.strip().upper() for symbol in value.split(",") if symbol.strip()]


def previous_weekday(today: date) -> date:
    candidate = today - timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def _snapshot(
        *,
        symbol: str,
        name: str,
        market: str,
        currency: str,
        trade_date: date,
        as_of: datetime,
        stale: bool,
        data_status: str,
        provider: str,
        source_label: str,
        individual: InvestorFlowLeg | None = None,
        foreign: InvestorFlowLeg | None = None,
        institution: InvestorFlowLeg | None = None,
) -> InvestorFlowSnapshot:
    zero = InvestorFlowLeg(Decimal("0"), 0)
    return InvestorFlowSnapshot(
        symbol=symbol,
        name=name,
        market=market,
        currency=currency,
        trade_date=trade_date,
        provider=provider,
        source_label=source_label,
        delay_label="Previous trading day investor flow",
        as_of=as_of,
        stale=stale,
        data_status=data_status,
        individual=individual or zero,
        foreign=foreign or zero,
        institution=institution or zero,
    )


def _krx_code(symbol: str) -> str:
    return symbol.split(".", 1)[0]


def _decimal_from_column(row, names: list[str]) -> Decimal:
    for name in names:
        if name in row:
            return Decimal(str(row[name]))
    raise InvestorFlowProviderError(f"missing investor flow amount columns: {names}")


def _int_from_column(row, names: list[str]) -> int:
    for name in names:
        if name in row:
            return int(row[name])
    raise InvestorFlowProviderError(f"missing investor flow volume columns: {names}")


def _decimal_number(value: Decimal):
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _as_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc_datetime(value).isoformat().replace("+00:00", "Z")
