from __future__ import annotations

import io
import logging
import math
import re
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Callable, Protocol

import pandas as pd
import requests
from youbuyfirst_pipeline.market_quotes import FinanceDataReaderMetadataProvider, MetadataProvider

DEFAULT_INVESTOR_FLOW_SYMBOLS = ["005930.KS", "000660.KS", "069500.KS"]
DEFAULT_INVESTOR_FLOW_HISTORY_LIMIT = 20
DEFAULT_INVESTOR_FLOW_PROVIDER = "naver-finance"

_INDIVIDUAL = "\uac1c\uc778"
_FOREIGN_TOTAL = "\uc678\uad6d\uc778\ud569\uacc4"
_FOREIGN = "\uc678\uad6d\uc778"
_INSTITUTION_TOTAL = "\uae30\uad00\ud569\uacc4"
_INSTITUTION = "\uae30\uad00"


class InvestorFlowProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class InvestorFlowLeg:
    net_amount: Decimal | None
    net_volume: int
    derived: bool = False

    def to_api_dict(self) -> dict:
        return {
            "netAmount": None if self.net_amount is None else _decimal_number(self.net_amount),
            "netVolume": self.net_volume,
            "derived": self.derived,
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


@dataclass(frozen=True)
class InvestorFlowHistoryRow:
    trade_date: date
    individual: InvestorFlowLeg
    foreign: InvestorFlowLeg
    institution: InvestorFlowLeg


class PykrxInvestorFlowClient:
    provider_name = "pykrx"
    source_label = "KRX investor trading by date via pykrx"
    delay_label = "Previous trading day investor flow"

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


class NaverFinanceInvestorFlowClient:
    provider_name = "naver-finance"
    source_label = "Naver Finance investor trend; individual is residual from foreign and institution"
    delay_label = "Previous trading day investor trend"

    def __init__(self, fetcher: Callable[[str], str] | None = None) -> None:
        self.fetcher = fetcher or self._fetch

    def flow(self, code: str, trade_date: date) -> tuple[InvestorFlowLeg, InvestorFlowLeg, InvestorFlowLeg]:
        for row in self.history(code, end_date=trade_date, limit=1):
            if row.trade_date == trade_date:
                return row.individual, row.foreign, row.institution
        raise InvestorFlowProviderError(f"empty Naver Finance investor trend for {code} on {trade_date:%Y%m%d}")

    def history(
            self,
            code: str,
            end_date: date,
            limit: int = DEFAULT_INVESTOR_FLOW_HISTORY_LIMIT,
    ) -> list[InvestorFlowHistoryRow]:
        bounded_limit = max(1, min(limit, 120))
        max_pages = max(1, min(math.ceil(bounded_limit / 20) + 1, 8))
        rows_by_date: dict[date, InvestorFlowHistoryRow] = {}
        for page in range(1, max_pages + 1):
            try:
                html = self.fetcher(_naver_investor_url(code, page))
                parsed_rows = _parse_naver_investor_rows(html)
            except InvestorFlowProviderError:
                raise
            except Exception as exc:
                raise InvestorFlowProviderError(f"Naver Finance investor trend failed for {code}") from exc

            for row in parsed_rows:
                if row.trade_date <= end_date and row.trade_date not in rows_by_date:
                    rows_by_date[row.trade_date] = row
            if len(rows_by_date) >= bounded_limit:
                break
        rows = sorted(rows_by_date.values(), key=lambda row: row.trade_date, reverse=True)
        if not rows:
            raise InvestorFlowProviderError(f"empty Naver Finance investor trend for {code}")
        return rows[:bounded_limit]

    @staticmethod
    def _fetch(url: str) -> str:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        response.raise_for_status()
        if response.apparent_encoding:
            response.encoding = response.apparent_encoding
        return response.text


def build_investor_flow_client(provider_name: str | None = None) -> InvestorFlowClient:
    normalized = (provider_name or DEFAULT_INVESTOR_FLOW_PROVIDER).strip().lower().replace("_", "-")
    if normalized in {"naver", "naver-finance", "naverfinance"}:
        return NaverFinanceInvestorFlowClient()
    if normalized == "pykrx":
        return PykrxInvestorFlowClient()
    raise ValueError(f"unsupported investor flow provider: {provider_name}")


class MarketInvestorFlowProvider:
    def __init__(
            self,
            flow_client: InvestorFlowClient | None = None,
            metadata_provider: MetadataProvider | None = None,
            stale_after_hours: int = 96,
    ) -> None:
        self.flow_client = flow_client or build_investor_flow_client()
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
        except Exception as exc:
            raise InvestorFlowProviderError(f"investor flow provider failed for {normalized} on {target_date}") from exc

        return _snapshot(
            symbol=metadata.symbol,
            name=metadata.name,
            market=metadata.market,
            currency=metadata.currency,
            trade_date=target_date,
            as_of=as_of,
            stale=stale,
            data_status=status,
            provider=_provider_name(self.flow_client),
            source_label=_source_label(self.flow_client),
            delay_label=_delay_label(self.flow_client),
            individual=individual,
            foreign=foreign,
            institution=institution,
        )

    def snapshots(
            self,
            symbols: list[str],
            trade_date: date | None = None,
            limit: int = DEFAULT_INVESTOR_FLOW_HISTORY_LIMIT,
            now: datetime | None = None,
    ) -> list[InvestorFlowSnapshot]:
        snapshots: list[InvestorFlowSnapshot] = []
        for symbol in symbols:
            snapshots.extend(self.history(symbol, trade_date=trade_date, limit=limit, now=now))
        return snapshots

    def history(
            self,
            symbol: str,
            trade_date: date | None = None,
            limit: int = DEFAULT_INVESTOR_FLOW_HISTORY_LIMIT,
            now: datetime | None = None,
    ) -> list[InvestorFlowSnapshot]:
        current_time = _as_utc_datetime(now or datetime.now(timezone.utc))
        target_date = trade_date or previous_weekday(current_time.date())
        normalized = symbol.strip().upper()
        metadata = self.metadata_provider.resolve(normalized)
        if metadata.market != "KR":
            return []
        history_method = getattr(self.flow_client, "history", None)
        if callable(history_method):
            try:
                rows = history_method(_krx_code(normalized), end_date=target_date, limit=limit)
            except InvestorFlowProviderError:
                return []
            snapshots = []
            for row in rows:
                as_of = datetime.combine(row.trade_date, time.min, tzinfo=timezone.utc)
                stale = current_time - as_of > self.stale_after
                snapshots.append(_snapshot(
                    symbol=metadata.symbol,
                    name=metadata.name,
                    market=metadata.market,
                    currency=metadata.currency,
                    trade_date=row.trade_date,
                    as_of=as_of,
                    stale=stale,
                    data_status="STALE" if stale else "OK",
                    provider=_provider_name(self.flow_client),
                    source_label=_source_label(self.flow_client),
                    delay_label=_delay_label(self.flow_client),
                    individual=row.individual,
                    foreign=row.foreign,
                    institution=row.institution,
                ))
            return snapshots

        snapshots: list[InvestorFlowSnapshot] = []
        for candidate in recent_weekdays(target_date, limit):
            try:
                snapshot = self.snapshot(symbol, trade_date=candidate, now=current_time)
            except InvestorFlowProviderError:
                continue
            if snapshot.data_status in {"OK", "STALE"}:
                snapshots.append(snapshot)
        return snapshots


def configured_investor_flow_symbols(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_INVESTOR_FLOW_SYMBOLS
    return [symbol.strip().upper() for symbol in value.split(",") if symbol.strip()]


def previous_weekday(today: date) -> date:
    candidate = today - timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def recent_weekdays(end_date: date, limit: int) -> list[date]:
    bounded_limit = max(1, min(limit, 120))
    days: list[date] = []
    candidate = end_date
    while len(days) < bounded_limit:
        if candidate.weekday() < 5:
            days.append(candidate)
        candidate -= timedelta(days=1)
    return days


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
        delay_label: str = "Previous trading day investor flow",
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
        delay_label=delay_label,
        as_of=as_of,
        stale=stale,
        data_status=data_status,
        individual=individual or zero,
        foreign=foreign or zero,
        institution=institution or zero,
    )


def _provider_name(flow_client: InvestorFlowClient) -> str:
    return getattr(flow_client, "provider_name", "pykrx")


def _source_label(flow_client: InvestorFlowClient) -> str:
    return getattr(flow_client, "source_label", "KRX investor trading by date via pykrx")


def _delay_label(flow_client: InvestorFlowClient) -> str:
    return getattr(flow_client, "delay_label", "Previous trading day investor flow")


def _naver_investor_url(code: str, page: int) -> str:
    return f"https://finance.naver.com/item/frgn.nhn?code={code}&page={page}"


def _parse_naver_investor_rows(html: str) -> list[InvestorFlowHistoryRow]:
    try:
        frames = pd.read_html(io.StringIO(html))
    except ValueError as exc:
        raise InvestorFlowProviderError("Naver Finance investor trend table not found") from exc

    rows: list[InvestorFlowHistoryRow] = []
    for frame in frames:
        if len(frame.columns) != 9:
            continue
        table = frame.dropna(how="all")
        for _, row in table.iterrows():
            trade_date = _parse_naver_date(row.iloc[0])
            if trade_date is None:
                continue
            institution_volume = _parse_naver_int(row.iloc[5])
            foreign_volume = _parse_naver_int(row.iloc[6])
            individual_volume = -(foreign_volume + institution_volume)
            rows.append(InvestorFlowHistoryRow(
                trade_date=trade_date,
                individual=InvestorFlowLeg(None, individual_volume, derived=True),
                foreign=InvestorFlowLeg(None, foreign_volume),
                institution=InvestorFlowLeg(None, institution_volume),
            ))
    if not rows:
        raise InvestorFlowProviderError("Naver Finance investor trend table has no rows")
    return rows


def _parse_naver_date(value) -> date | None:
    if pd.isna(value):
        return None
    match = re.search(r"(\d{4})[.\-/](\d{2})[.\-/](\d{2})", str(value))
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _parse_naver_int(value) -> int:
    if pd.isna(value):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    normalized = re.sub(r"[^0-9\-]", "", str(value))
    if normalized in {"", "-"}:
        return 0
    return int(normalized)


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
