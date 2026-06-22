from __future__ import annotations

import calendar
import csv
import hashlib
import io
import math
import os
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol

import httpx

DATA_GO_SERVICE_KEY_ENV = "DATA_GO_SERVICE_KEY"

_OK_RESULT_CODES = {"00", "000", "INFO-000"}


class PublicDataProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class MolitPublicDataDataset:
    dataset_id: str
    fact_type: str
    endpoint_url: str


MOLIT_APT_TRADE_DATASET = MolitPublicDataDataset(
    dataset_id="molit_apt_trade",
    fact_type="apt_trade",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade",
)

MOLIT_APT_RENT_DATASET = MolitPublicDataDataset(
    dataset_id="molit_apt_rent",
    fact_type="apt_rent",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent",
)

MOLIT_OFFI_TRADE_DATASET = MolitPublicDataDataset(
    dataset_id="molit_offi_trade",
    fact_type="offi_trade",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade",
)

MOLIT_OFFI_RENT_DATASET = MolitPublicDataDataset(
    dataset_id="molit_offi_rent",
    fact_type="offi_rent",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent",
)

MOLIT_RH_TRADE_DATASET = MolitPublicDataDataset(
    dataset_id="molit_rh_trade",
    fact_type="rh_trade",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade",
)

MOLIT_RH_RENT_DATASET = MolitPublicDataDataset(
    dataset_id="molit_rh_rent",
    fact_type="rh_rent",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent",
)

MOLIT_SH_TRADE_DATASET = MolitPublicDataDataset(
    dataset_id="molit_sh_trade",
    fact_type="sh_trade",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade",
)

MOLIT_SH_RENT_DATASET = MolitPublicDataDataset(
    dataset_id="molit_sh_rent",
    fact_type="sh_rent",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcSHRent/getRTMSDataSvcSHRent",
)

MOLIT_SILV_TRADE_DATASET = MolitPublicDataDataset(
    dataset_id="molit_silv_trade",
    fact_type="silv_trade",
    endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcSilvTrade/getRTMSDataSvcSilvTrade",
)

MOLIT_OFFICIAL_APARTMENT_PRICE_DATASET_ID = "molit_official_apartment_price_csv"


@dataclass(frozen=True)
class RealEstateMarketFact:
    fact_type: str
    provider: str
    provider_dataset: str
    provider_object_id: str
    legal_dong_code: str
    observed_at: date
    as_of: date
    ingested_at: datetime
    value_json: dict
    target_type: str = "region"
    target_id: str | None = None
    source_updated_at: datetime | None = None
    data_status: str = "ok"
    stale: bool = False

    def to_ingestion_dict(self) -> dict:
        return {
            "targetType": self.target_type,
            "targetId": self.target_id,
            "factType": self.fact_type,
            "provider": self.provider,
            "providerDataset": self.provider_dataset,
            "providerObjectId": self.provider_object_id,
            "legalDongCode": self.legal_dong_code,
            "observedAt": self.observed_at.isoformat(),
            "asOf": self.as_of.isoformat(),
            "ingestedAt": _iso(self.ingested_at),
            "sourceUpdatedAt": None if self.source_updated_at is None else _iso(self.source_updated_at),
            "valueJson": self.value_json,
            "dataStatus": self.data_status,
            "stale": self.stale,
        }


@dataclass(frozen=True)
class RealEstatePublicDataRawIngestion:
    run_key: str
    provider_dataset: str
    lawd_code: str
    deal_ym: str
    started_at: datetime
    finished_at: datetime
    facts: tuple[RealEstateMarketFact, ...]
    status: str = "completed"

    def to_request_dict(self) -> dict:
        requested_from = _parse_deal_ym(self.deal_ym)
        requested_to = date(
            requested_from.year,
            requested_from.month,
            calendar.monthrange(requested_from.year, requested_from.month)[1],
        )
        return {
            "run": {
                "runKey": self.run_key,
                "providerDataset": self.provider_dataset,
                "runType": "backfill",
                "requestedFrom": requested_from.isoformat(),
                "requestedTo": requested_to.isoformat(),
                "requestParams": {
                    "LAWD_CD": self.lawd_code,
                    "DEAL_YMD": self.deal_ym,
                },
                "status": self.status,
                "startedAt": _iso(self.started_at),
                "finishedAt": _iso(self.finished_at),
            },
            "items": [_raw_item_payload(fact) for fact in self.facts],
        }

    def _item_payload(self, fact: RealEstateMarketFact) -> dict:
        return _raw_item_payload(fact)


@dataclass(frozen=True)
class RealEstatePublicDataFileRawIngestion:
    run_key: str
    provider_dataset: str
    requested_from: date
    requested_to: date
    request_params: Mapping[str, str]
    started_at: datetime
    finished_at: datetime
    facts: tuple[RealEstateMarketFact, ...]
    status: str = "completed"

    def to_request_dict(self) -> dict:
        return {
            "run": {
                "runKey": self.run_key,
                "providerDataset": self.provider_dataset,
                "runType": "backfill",
                "requestedFrom": self.requested_from.isoformat(),
                "requestedTo": self.requested_to.isoformat(),
                "requestParams": dict(self.request_params),
                "status": self.status,
                "startedAt": _iso(self.started_at),
                "finishedAt": _iso(self.finished_at),
            },
            "items": [_raw_item_payload(fact) for fact in self.facts],
        }


@dataclass(frozen=True)
class OfficialApartmentPriceCsvInspection:
    provider_dataset: str
    source_label: str | None
    base_date: date
    batch_size: int
    total_rows: int
    valid_rows: int
    invalid_rows: int
    sample_provider_object_ids: tuple[str, ...]
    error_samples: tuple[dict, ...]

    @property
    def batch_count(self) -> int:
        return math.ceil(self.valid_rows / self.batch_size) if self.valid_rows else 0

    @property
    def first_run_key(self) -> str | None:
        if not self.valid_rows:
            return None
        return _official_apartment_price_run_key(self.base_date, 1)

    @property
    def last_run_key(self) -> str | None:
        if not self.valid_rows:
            return None
        return _official_apartment_price_run_key(self.base_date, self.batch_count)

    def to_payload(self) -> dict:
        return {
            "providerDataset": self.provider_dataset,
            "sourceLabel": self.source_label,
            "baseDate": self.base_date.isoformat(),
            "batchSize": self.batch_size,
            "totalRows": self.total_rows,
            "validRows": self.valid_rows,
            "invalidRows": self.invalid_rows,
            "batchCount": self.batch_count,
            "firstRunKey": self.first_run_key,
            "lastRunKey": self.last_run_key,
            "sampleProviderObjectIds": list(self.sample_provider_object_ids),
            "errorSamples": list(self.error_samples),
        }


@dataclass(frozen=True)
class RegionalStatCsvInspection:
    provider_dataset: str
    source_label: str | None
    batch_size: int
    total_rows: int
    valid_rows: int
    invalid_rows: int
    batch_count: int
    first_run_key: str | None
    last_run_key: str | None
    sample_provider_object_ids: tuple[str, ...]
    error_samples: tuple[dict, ...]

    def to_payload(self) -> dict:
        return {
            "providerDataset": self.provider_dataset,
            "sourceLabel": self.source_label,
            "batchSize": self.batch_size,
            "totalRows": self.total_rows,
            "validRows": self.valid_rows,
            "invalidRows": self.invalid_rows,
            "batchCount": self.batch_count,
            "firstRunKey": self.first_run_key,
            "lastRunKey": self.last_run_key,
            "sampleProviderObjectIds": list(self.sample_provider_object_ids),
            "errorSamples": list(self.error_samples),
        }


PublicDataFetcher = Callable[[str, Mapping[str, str]], str]


class MolitRealEstatePublicDataReader(Protocol):
    def fetch_apt_trades(
        self,
        lawd_code: str,
        deal_ym: str,
        page_no: int = 1,
        num_rows: int = 100,
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        ...

    def fetch_apt_rents(
        self,
        lawd_code: str,
        deal_ym: str,
        page_no: int = 1,
        num_rows: int = 100,
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        ...

    def fetch_offi_trades(
        self,
        lawd_code: str,
        deal_ym: str,
        page_no: int = 1,
        num_rows: int = 100,
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        ...


class MolitRealEstatePublicDataClient:
    def __init__(
        self,
        service_key: str,
        fetcher: PublicDataFetcher | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        normalized_key = service_key.strip()
        if not normalized_key:
            raise ValueError(f"{DATA_GO_SERVICE_KEY_ENV} is required")
        self.service_key = normalized_key
        self.timeout_seconds = timeout_seconds
        self.fetcher = fetcher or self._fetch

    def fetch_apt_trades(
        self,
        lawd_code: str,
        deal_ym: str,
        page_no: int = 1,
        num_rows: int = 100,
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        return self.fetch_dataset(
            MOLIT_APT_TRADE_DATASET,
            lawd_code=lawd_code,
            deal_ym=deal_ym,
            page_no=page_no,
            num_rows=num_rows,
            now=now,
        )

    def fetch_apt_rents(
        self,
        lawd_code: str,
        deal_ym: str,
        page_no: int = 1,
        num_rows: int = 100,
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        return self.fetch_dataset(
            MOLIT_APT_RENT_DATASET,
            lawd_code=lawd_code,
            deal_ym=deal_ym,
            page_no=page_no,
            num_rows=num_rows,
            now=now,
        )

    def fetch_offi_trades(
        self,
        lawd_code: str,
        deal_ym: str,
        page_no: int = 1,
        num_rows: int = 100,
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        return self.fetch_dataset(
            MOLIT_OFFI_TRADE_DATASET,
            lawd_code=lawd_code,
            deal_ym=deal_ym,
            page_no=page_no,
            num_rows=num_rows,
            now=now,
        )

    def fetch_offi_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        return self.fetch_dataset(MOLIT_OFFI_RENT_DATASET, lawd_code=lawd_code, deal_ym=deal_ym, page_no=page_no, num_rows=num_rows, now=now)

    def fetch_rh_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        return self.fetch_dataset(MOLIT_RH_TRADE_DATASET, lawd_code=lawd_code, deal_ym=deal_ym, page_no=page_no, num_rows=num_rows, now=now)

    def fetch_rh_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        return self.fetch_dataset(MOLIT_RH_RENT_DATASET, lawd_code=lawd_code, deal_ym=deal_ym, page_no=page_no, num_rows=num_rows, now=now)

    def fetch_sh_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        return self.fetch_dataset(MOLIT_SH_TRADE_DATASET, lawd_code=lawd_code, deal_ym=deal_ym, page_no=page_no, num_rows=num_rows, now=now)

    def fetch_sh_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        return self.fetch_dataset(MOLIT_SH_RENT_DATASET, lawd_code=lawd_code, deal_ym=deal_ym, page_no=page_no, num_rows=num_rows, now=now)

    def fetch_silv_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        return self.fetch_dataset(MOLIT_SILV_TRADE_DATASET, lawd_code=lawd_code, deal_ym=deal_ym, page_no=page_no, num_rows=num_rows, now=now)

    def fetch_dataset(
        self,
        dataset: MolitPublicDataDataset,
        lawd_code: str,
        deal_ym: str,
        page_no: int = 1,
        num_rows: int = 100,
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        _validate_lawd_code(lawd_code)
        _parse_deal_ym(deal_ym)
        params = {
            "serviceKey": self.service_key,
            "LAWD_CD": lawd_code,
            "DEAL_YMD": deal_ym,
            "pageNo": str(page_no),
            "numOfRows": str(num_rows),
        }
        xml_text = self.fetcher(dataset.endpoint_url, params)
        return parse_molit_public_data_xml(
            dataset,
            xml_text,
            lawd_code=lawd_code,
            deal_ym=deal_ym,
            ingested_at=now or datetime.now(timezone.utc),
        )

    def _fetch(self, url: str, params: Mapping[str, str]) -> str:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as exc:
            raise PublicDataProviderError(f"MOLIT public data request failed: {url}") from exc


def build_molit_public_data_client_from_env() -> MolitRealEstatePublicDataClient:
    service_key = os.getenv(DATA_GO_SERVICE_KEY_ENV)
    if not service_key:
        raise ValueError(f"{DATA_GO_SERVICE_KEY_ENV} is required")
    return MolitRealEstatePublicDataClient(service_key=service_key)


def collect_molit_real_estate_market_facts(
    client: MolitRealEstatePublicDataReader,
    lawd_code: str,
    deal_ym: str,
    datasets: list[str] | tuple[str, ...] | set[str],
    page_size: int = 100,
    max_pages: int = 1000,
    now: datetime | None = None,
) -> list[RealEstateMarketFact]:
    collected_at = now or datetime.now(timezone.utc)
    normalized_datasets = {_normalize_dataset_name(dataset) for dataset in datasets}
    facts: list[RealEstateMarketFact] = []
    # Iterate in a stable order so multi-dataset runs are deterministic.
    for dataset_name in [name for name in _DATASET_FETCH_METHODS if name in normalized_datasets]:
        method_name = _DATASET_FETCH_METHODS[dataset_name]
        fetch_method = getattr(client, method_name, None)
        if fetch_method is None:
            continue
        facts.extend(
            _fetch_paginated_molit_facts(
                lambda page_no, fetch_method=fetch_method: fetch_method(
                    lawd_code,
                    deal_ym,
                    page_no=page_no,
                    num_rows=page_size,
                    now=collected_at,
                ),
                page_size=page_size,
                max_pages=max_pages,
            )
        )
    return facts


_DATASET_FETCH_METHODS: dict[str, str] = {
    "trade": "fetch_apt_trades",
    "rent": "fetch_apt_rents",
    "offi-trade": "fetch_offi_trades",
    "offi-rent": "fetch_offi_rents",
    "rh-trade": "fetch_rh_trades",
    "rh-rent": "fetch_rh_rents",
    "sh-trade": "fetch_sh_trades",
    "sh-rent": "fetch_sh_rents",
    "silv-trade": "fetch_silv_trades",
}


def _fetch_paginated_molit_facts(
    fetch_page: Callable[[int], list[RealEstateMarketFact]],
    page_size: int,
    max_pages: int,
) -> list[RealEstateMarketFact]:
    if page_size < 1:
        raise ValueError("page_size must be greater than 0")
    if max_pages < 1:
        raise ValueError("max_pages must be greater than 0")

    facts: list[RealEstateMarketFact] = []
    for page_no in range(1, max_pages + 1):
        page_facts = fetch_page(page_no)
        facts.extend(page_facts)
        if len(page_facts) < page_size:
            break
    return facts


def collect_molit_real_estate_market_facts_from_data_targets(
    client: MolitRealEstatePublicDataReader,
    data_targets: list[dict],
    deal_ym: str,
    page_size: int = 100,
    max_pages: int = 1000,
    now: datetime | None = None,
) -> list[RealEstateMarketFact]:
    datasets_by_lawd_code: dict[str, set[str]] = {}
    for target in data_targets:
        if target.get("enabled") is False:
            continue
        if str(target.get("provider", "")).strip().lower() != "molit":
            continue
        lawd_code = str(target.get("lawdCode", "")).strip()
        if not lawd_code:
            continue
        dataset = _normalize_dataset_name(str(target.get("providerDataset", "")))
        datasets_by_lawd_code.setdefault(lawd_code, set()).add(dataset)

    facts: list[RealEstateMarketFact] = []
    collected_at = now or datetime.now(timezone.utc)
    for lawd_code in sorted(datasets_by_lawd_code):
        facts.extend(
            collect_molit_real_estate_market_facts(
                client,
                lawd_code=lawd_code,
                deal_ym=deal_ym,
                datasets=datasets_by_lawd_code[lawd_code],
                page_size=page_size,
                max_pages=max_pages,
                now=collected_at,
            )
        )
    return facts


def build_molit_raw_ingestions(
    facts: list[RealEstateMarketFact],
    lawd_code: str,
    deal_ym: str,
    started_at: datetime,
    finished_at: datetime | None = None,
) -> list[RealEstatePublicDataRawIngestion]:
    _validate_lawd_code(lawd_code)
    _parse_deal_ym(deal_ym)
    facts_by_dataset: dict[str, list[RealEstateMarketFact]] = {}
    for fact in facts:
        facts_by_dataset.setdefault(fact.provider_dataset, []).append(fact)
    completed_at = finished_at or started_at
    ingestions: list[RealEstatePublicDataRawIngestion] = []
    for provider_dataset, dataset_facts in facts_by_dataset.items():
        if not dataset_facts:
            continue
        ingestions.append(
            RealEstatePublicDataRawIngestion(
                run_key=f"{provider_dataset}:{lawd_code}:{deal_ym}",
                provider_dataset=provider_dataset,
                lawd_code=lawd_code,
                deal_ym=deal_ym,
                started_at=started_at,
                finished_at=completed_at,
                facts=tuple(dataset_facts),
            )
        )
    return ingestions


def iter_official_apartment_price_market_facts(
    csv_source: str | Iterable[str],
    ingested_at: datetime,
) -> Iterator[RealEstateMarketFact]:
    source = io.StringIO(csv_source.lstrip("\ufeff")) if isinstance(csv_source, str) else csv_source
    reader = csv.DictReader(source)
    for raw_row in reader:
        cleaned_raw = _official_price_raw_row(raw_row)
        if not cleaned_raw:
            continue
        normalized_row = {
            _normalize_csv_header(key): value
            for key, value in cleaned_raw.items()
        }
        yield _official_apartment_price_fact(cleaned_raw, normalized_row, ingested_at)


def build_official_apartment_price_raw_ingestions(
    facts: Iterable[RealEstateMarketFact],
    base_date: date,
    started_at: datetime,
    batch_size: int = 1000,
    source_label: str | None = None,
    finished_at: datetime | None = None,
) -> Iterator[RealEstatePublicDataFileRawIngestion]:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    completed_at = finished_at or started_at
    batch: list[RealEstateMarketFact] = []
    batch_index = 1
    for fact in facts:
        batch.append(fact)
        if len(batch) >= batch_size:
            yield _official_apartment_price_raw_ingestion(
                tuple(batch),
                base_date,
                started_at,
                completed_at,
                batch_index,
                source_label,
            )
            batch = []
            batch_index += 1

    if batch:
        yield _official_apartment_price_raw_ingestion(
            tuple(batch),
            base_date,
            started_at,
            completed_at,
            batch_index,
            source_label,
        )


def iter_regional_stat_market_facts(
    csv_source: str | Iterable[str],
    *,
    provider: str,
    provider_dataset: str,
    fact_type: str,
    ingested_at: datetime,
    default_unit: str | None = None,
) -> Iterator[RealEstateMarketFact]:
    source = io.StringIO(csv_source.lstrip("\ufeff")) if isinstance(csv_source, str) else csv_source
    reader = csv.DictReader(source)
    for raw_row in reader:
        cleaned_raw = _official_price_raw_row(raw_row)
        if not cleaned_raw:
            continue
        normalized_row = {
            _normalize_csv_header(key): value
            for key, value in cleaned_raw.items()
        }
        yield _regional_stat_fact(
            cleaned_raw,
            normalized_row,
            provider=provider,
            provider_dataset=provider_dataset,
            fact_type=fact_type,
            ingested_at=ingested_at,
            default_unit=default_unit,
        )


def build_regional_stat_raw_ingestions(
    facts: Iterable[RealEstateMarketFact],
    *,
    provider_dataset: str,
    started_at: datetime,
    batch_size: int = 1000,
    source_label: str | None = None,
    finished_at: datetime | None = None,
) -> Iterator[RealEstatePublicDataFileRawIngestion]:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    completed_at = finished_at or started_at
    batch: list[RealEstateMarketFact] = []
    current_as_of: date | None = None
    batch_index = 1
    for fact in facts:
        if current_as_of is None:
            current_as_of = fact.as_of
        if fact.as_of != current_as_of:
            yield _regional_stat_raw_ingestion(
                tuple(batch),
                provider_dataset,
                current_as_of,
                started_at,
                completed_at,
                batch_index,
                source_label,
            )
            batch = []
            current_as_of = fact.as_of
            batch_index = 1
        elif len(batch) >= batch_size:
            yield _regional_stat_raw_ingestion(
                tuple(batch),
                provider_dataset,
                current_as_of,
                started_at,
                completed_at,
                batch_index,
                source_label,
            )
            batch = []
            batch_index += 1

        batch.append(fact)

    if batch and current_as_of is not None:
        yield _regional_stat_raw_ingestion(
            tuple(batch),
            provider_dataset,
            current_as_of,
            started_at,
            completed_at,
            batch_index,
            source_label,
        )


def inspect_official_apartment_price_csv(
    csv_source: str | Iterable[str],
    *,
    base_date: date,
    batch_size: int,
    ingested_at: datetime,
    source_label: str | None = None,
    max_samples: int = 5,
    max_error_samples: int = 5,
) -> OfficialApartmentPriceCsvInspection:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    source = io.StringIO(csv_source.lstrip("\ufeff")) if isinstance(csv_source, str) else csv_source
    reader = csv.DictReader(source)
    total_rows = 0
    valid_rows = 0
    invalid_rows = 0
    sample_provider_object_ids: list[str] = []
    error_samples: list[dict] = []

    for row_number, raw_row in enumerate(reader, start=1):
        total_rows += 1
        try:
            cleaned_raw = _official_price_raw_row(raw_row)
            normalized_row = {
                _normalize_csv_header(key): value
                for key, value in cleaned_raw.items()
            }
            fact = _official_apartment_price_fact(cleaned_raw, normalized_row, ingested_at)
        except Exception as exc:
            invalid_rows += 1
            if len(error_samples) < max_error_samples:
                error_samples.append({"rowNumber": row_number, "message": str(exc)})
            continue

        valid_rows += 1
        if len(sample_provider_object_ids) < max_samples:
            sample_provider_object_ids.append(fact.provider_object_id)

    return OfficialApartmentPriceCsvInspection(
        provider_dataset=MOLIT_OFFICIAL_APARTMENT_PRICE_DATASET_ID,
        source_label=source_label,
        base_date=base_date,
        batch_size=batch_size,
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        sample_provider_object_ids=tuple(sample_provider_object_ids),
        error_samples=tuple(error_samples),
    )


def inspect_regional_stat_csv(
    csv_source: str | Iterable[str],
    *,
    provider: str,
    provider_dataset: str,
    fact_type: str,
    batch_size: int,
    ingested_at: datetime,
    source_label: str | None = None,
    default_unit: str | None = None,
    max_samples: int = 5,
    max_error_samples: int = 5,
) -> RegionalStatCsvInspection:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    source = io.StringIO(csv_source.lstrip("\ufeff")) if isinstance(csv_source, str) else csv_source
    reader = csv.DictReader(source)
    total_rows = 0
    valid_rows = 0
    invalid_rows = 0
    batch_count = 0
    first_run_key: str | None = None
    last_run_key: str | None = None
    period_counts: dict[date, int] = {}
    sample_provider_object_ids: list[str] = []
    error_samples: list[dict] = []

    for row_number, raw_row in enumerate(reader, start=1):
        total_rows += 1
        try:
            cleaned_raw = _official_price_raw_row(raw_row)
            normalized_row = {
                _normalize_csv_header(key): value
                for key, value in cleaned_raw.items()
            }
            fact = _regional_stat_fact(
                cleaned_raw,
                normalized_row,
                provider=provider,
                provider_dataset=provider_dataset,
                fact_type=fact_type,
                ingested_at=ingested_at,
                default_unit=default_unit,
            )
        except Exception as exc:
            invalid_rows += 1
            if len(error_samples) < max_error_samples:
                error_samples.append({"rowNumber": row_number, "message": str(exc)})
            continue

        valid_rows += 1
        previous_count = period_counts.get(fact.as_of, 0)
        period_counts[fact.as_of] = previous_count + 1
        if previous_count % batch_size == 0:
            batch_count += 1
        batch_index = math.ceil(period_counts[fact.as_of] / batch_size)
        run_key = _regional_stat_run_key(provider_dataset, fact.as_of, batch_index)
        first_run_key = first_run_key or run_key
        last_run_key = run_key
        if len(sample_provider_object_ids) < max_samples:
            sample_provider_object_ids.append(fact.provider_object_id)

    return RegionalStatCsvInspection(
        provider_dataset=provider_dataset,
        source_label=source_label,
        batch_size=batch_size,
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        batch_count=batch_count,
        first_run_key=first_run_key,
        last_run_key=last_run_key,
        sample_provider_object_ids=tuple(sample_provider_object_ids),
        error_samples=tuple(error_samples),
    )


def parse_molit_public_data_xml(
    dataset: MolitPublicDataDataset,
    xml_text: str,
    lawd_code: str,
    deal_ym: str,
    ingested_at: datetime,
) -> list[RealEstateMarketFact]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise PublicDataProviderError(f"invalid XML from {dataset.dataset_id}") from exc

    result_code = _first_text(root, "resultCode")
    if result_code and result_code not in _OK_RESULT_CODES:
        result_msg = _first_text(root, "resultMsg") or "unknown provider error"
        raise PublicDataProviderError(f"{dataset.dataset_id} failed with {result_code}: {result_msg}")

    as_of = _parse_deal_ym(deal_ym)
    facts = []
    for item in _elements(root, "item"):
        fields = _item_fields(item)
        facts.append(_market_fact_from_item(dataset, fields, lawd_code, deal_ym, as_of, ingested_at))
    return facts


def _market_fact_from_item(
    dataset: MolitPublicDataDataset,
    fields: dict[str, str],
    lawd_code: str,
    deal_ym: str,
    as_of: date,
    ingested_at: datetime,
) -> RealEstateMarketFact:
    observed_at = _observed_date(fields)
    legal_dong_code = fields.get("sggCd") or lawd_code
    value_json = _rent_value_json(fields) if dataset.fact_type.endswith("_rent") else _trade_value_json(fields)
    value_json["raw"] = dict(sorted((key, value) for key, value in fields.items() if value))
    return RealEstateMarketFact(
        fact_type=dataset.fact_type,
        provider="molit",
        provider_dataset=dataset.dataset_id,
        provider_object_id=_provider_object_id(dataset, legal_dong_code, deal_ym, fields),
        legal_dong_code=legal_dong_code,
        observed_at=observed_at,
        as_of=as_of,
        ingested_at=ingested_at,
        value_json=value_json,
    )


def _trade_value_json(fields: dict[str, str]) -> dict:
    return _without_empty_values(
        {
            "apartmentName": fields.get("aptNm") or fields.get("offiNm") or fields.get("mhouseNm"),
            "legalDongName": fields.get("umdNm"),
            "jibun": fields.get("jibun"),
            "dealAmountManwon": _int_from_text(fields.get("dealAmount")),
            "exclusiveAreaM2": _float_from_text(fields.get("excluUseAr")),
            "floor": _int_from_text(fields.get("floor")),
            "builtYear": _int_from_text(fields.get("buildYear")),
            "dealingType": fields.get("dealingGbn"),
        }
    )


def _rent_value_json(fields: dict[str, str]) -> dict:
    return _without_empty_values(
        {
            "apartmentName": fields.get("aptNm") or fields.get("offiNm") or fields.get("mhouseNm"),
            "legalDongName": fields.get("umdNm"),
            "jibun": fields.get("jibun"),
            "depositAmountManwon": _int_from_text(fields.get("deposit")),
            "monthlyRentAmountManwon": _int_from_text(fields.get("monthlyRent")),
            "exclusiveAreaM2": _float_from_text(fields.get("excluUseAr")),
            "totalFloorAreaM2": _float_from_text(fields.get("totalFloorAr")),
            "houseType": fields.get("houseType"),
            "floor": _int_from_text(fields.get("floor")),
            "builtYear": _int_from_text(fields.get("buildYear")),
            "contractType": fields.get("contractType"),
            "contractTerm": fields.get("contractTerm"),
        }
    )


def _official_apartment_price_fact(
    cleaned_raw: dict[str, str],
    normalized_row: dict[str, str],
    ingested_at: datetime,
) -> RealEstateMarketFact:
    sigungu_code = _cell(normalized_row, "시군구코드", "sigunguCd")
    dong_code = _cell(normalized_row, "법정동코드", "bjdongCd")
    legal_dong_code = _join_legal_dong_code(sigungu_code, dong_code) or "unknown"
    notice_date = _date_from_text(_cell(normalized_row, "공시기준일", "기준일자", "기준일"))
    if notice_date is None:
        raise PublicDataProviderError("official apartment price row has no notice/base date")

    price_won = _int_from_text(_cell(normalized_row, "공동주택가격(원)", "공시가격", "주택가격"))
    value_json = _without_empty_values(
        {
            "sidoName": _cell(normalized_row, "시도", "시도명"),
            "sigunguName": _cell(normalized_row, "시군구", "시군구명"),
            "legalDongName": _cell(normalized_row, "동리", "법정동명"),
            "jibun": _jibun(_cell(normalized_row, "번", "본번"), _cell(normalized_row, "지", "부번")),
            "complexName": _cell(normalized_row, "단지명", "건물명"),
            "dongName": _cell(normalized_row, "동명", "동명칭"),
            "hoName": _cell(normalized_row, "호명", "호명칭"),
            "exclusiveAreaM2": _float_from_text(_cell(normalized_row, "전용면적(㎡)", "전용면적", "전유면적")),
            "officialPriceWon": price_won,
            "buildingLedgerPk": _cell(normalized_row, "관리건축물대장PK", "관리_건축물대장_PK", "mgmBldrgstPk"),
            "raw": cleaned_raw,
        }
    )
    return RealEstateMarketFact(
        fact_type="official_apartment_price",
        provider="molit",
        provider_dataset=MOLIT_OFFICIAL_APARTMENT_PRICE_DATASET_ID,
        provider_object_id=_official_apartment_price_provider_object_id(
            legal_dong_code,
            notice_date,
            normalized_row,
        ),
        legal_dong_code=legal_dong_code,
        observed_at=notice_date,
        as_of=notice_date,
        ingested_at=ingested_at,
        value_json=value_json,
        target_type="complex_unit",
        data_status="ok" if price_won is not None else "partial",
    )


def _official_apartment_price_provider_object_id(
    legal_dong_code: str,
    notice_date: date,
    row: Mapping[str, str],
) -> str:
    seed = "|".join(
        [
            MOLIT_OFFICIAL_APARTMENT_PRICE_DATASET_ID,
            legal_dong_code,
            notice_date.isoformat(),
            _cell(row, "관리건축물대장PK", "관리_건축물대장_PK", "mgmBldrgstPk") or "",
            _cell(row, "단지명", "건물명") or "",
            _cell(row, "동명", "동명칭") or "",
            _cell(row, "호명", "호명칭") or "",
            _cell(row, "번", "본번") or "",
            _cell(row, "지", "부번") or "",
            _cell(row, "전용면적(㎡)", "전용면적", "전유면적") or "",
            _cell(row, "공동주택가격(원)", "공시가격", "주택가격") or "",
        ]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"{MOLIT_OFFICIAL_APARTMENT_PRICE_DATASET_ID}:{legal_dong_code}:{notice_date.isoformat()}:{digest}"


def _regional_stat_fact(
    cleaned_raw: dict[str, str],
    normalized_row: Mapping[str, str],
    *,
    provider: str,
    provider_dataset: str,
    fact_type: str,
    ingested_at: datetime,
    default_unit: str | None,
) -> RealEstateMarketFact:
    period_date, period_key = _regional_stat_period(normalized_row)
    region_code = _cell(
        normalized_row,
        "지역코드",
        "법정동코드",
        "시군구코드",
        "행정구역코드",
        "regionCode",
        "legalDongCode",
    ) or "unknown"
    region_name = _cell(normalized_row, "지역명", "행정구역", "시도", "시군구", "regionName")
    metric_name = _cell(normalized_row, "항목", "지표", "통계항목", "metric", "metricName") or fact_type
    unit = _cell(normalized_row, "단위", "unit") or default_unit
    value = _number_from_text(
        _cell(
            normalized_row,
            "값",
            "지표값",
            "통계값",
            "value",
            "호",
            "건수",
            "지수",
            "가격지수",
        )
    )
    value_json = _without_empty_values(
        {
            "regionName": region_name,
            "metricName": metric_name,
            "value": value,
            "unit": unit,
            "periodYm": period_key if len(period_key) == 6 else None,
            "raw": cleaned_raw,
        }
    )
    return RealEstateMarketFact(
        fact_type=fact_type,
        provider=provider,
        provider_dataset=provider_dataset,
        provider_object_id=_regional_stat_provider_object_id(
            provider_dataset,
            region_code,
            period_key,
            metric_name,
            value,
        ),
        legal_dong_code=region_code,
        observed_at=period_date,
        as_of=period_date,
        ingested_at=ingested_at,
        value_json=value_json,
        data_status="ok" if value is not None else "partial",
    )


def _regional_stat_period(row: Mapping[str, str]) -> tuple[date, str]:
    value = _cell(row, "기준월", "년월", "연월", "기간", "period", "periodYm", "baseYm", "기준일", "일자", "date")
    if not value:
        raise PublicDataProviderError("regional stat row has no period")
    cleaned = value.strip()
    if re.fullmatch(r"\d{6}", cleaned):
        return date(int(cleaned[:4]), int(cleaned[4:]), 1), cleaned
    if re.fullmatch(r"\d{8}", cleaned):
        return date(int(cleaned[:4]), int(cleaned[4:6]), int(cleaned[6:])), cleaned
    normalized = cleaned.replace(".", "-").replace("/", "-")
    if re.fullmatch(r"\d{4}", normalized):
        return date(int(normalized), 1, 1), normalized
    parsed = date.fromisoformat(normalized)
    return parsed, parsed.isoformat()


def _regional_stat_provider_object_id(
    provider_dataset: str,
    region_code: str,
    period_key: str,
    metric_name: str,
    value: int | float | None,
) -> str:
    seed = "|".join([provider_dataset, region_code, period_key, metric_name, "" if value is None else str(value)])
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"{provider_dataset}:{region_code}:{period_key}:{digest}"


def _official_apartment_price_raw_ingestion(
    facts: tuple[RealEstateMarketFact, ...],
    base_date: date,
    started_at: datetime,
    finished_at: datetime,
    batch_index: int,
    source_label: str | None,
) -> RealEstatePublicDataFileRawIngestion:
    formatted_index = f"{batch_index:06d}"
    request_params = {
        "baseDate": base_date.isoformat(),
        "batchIndex": formatted_index,
    }
    if source_label:
        request_params["sourceLabel"] = source_label
    return RealEstatePublicDataFileRawIngestion(
        run_key=_official_apartment_price_run_key(base_date, batch_index),
        provider_dataset=MOLIT_OFFICIAL_APARTMENT_PRICE_DATASET_ID,
        requested_from=base_date,
        requested_to=base_date,
        request_params=request_params,
        started_at=started_at,
        finished_at=finished_at,
        facts=facts,
    )


def _official_apartment_price_run_key(base_date: date, batch_index: int) -> str:
    return f"{MOLIT_OFFICIAL_APARTMENT_PRICE_DATASET_ID}:{base_date:%Y%m%d}:{batch_index:06d}"


def _regional_stat_raw_ingestion(
    facts: tuple[RealEstateMarketFact, ...],
    provider_dataset: str,
    as_of: date,
    started_at: datetime,
    finished_at: datetime,
    batch_index: int,
    source_label: str | None,
) -> RealEstatePublicDataFileRawIngestion:
    request_params = {
        "period": as_of.isoformat(),
        "batchIndex": f"{batch_index:06d}",
    }
    if source_label:
        request_params["sourceLabel"] = source_label
    return RealEstatePublicDataFileRawIngestion(
        run_key=_regional_stat_run_key(provider_dataset, as_of, batch_index),
        provider_dataset=provider_dataset,
        requested_from=as_of,
        requested_to=as_of,
        request_params=request_params,
        started_at=started_at,
        finished_at=finished_at,
        facts=facts,
    )


def _regional_stat_run_key(provider_dataset: str, as_of: date, batch_index: int) -> str:
    return f"{provider_dataset}:{as_of:%Y%m%d}:{batch_index:06d}"


def _raw_item_payload(fact: RealEstateMarketFact) -> dict:
    raw_payload = fact.value_json.get("raw")
    if not isinstance(raw_payload, dict):
        raw_payload = fact.value_json
    return {
        "providerDataset": fact.provider_dataset,
        "providerObjectId": fact.provider_object_id,
        "legalDongCode": fact.legal_dong_code,
        "targetId": fact.target_id,
        "observedAt": fact.observed_at.isoformat(),
        "asOf": fact.as_of.isoformat(),
        "sourceUpdatedAt": None if fact.source_updated_at is None else _iso(fact.source_updated_at),
        "rawPayload": raw_payload,
        "landingStatus": "landed",
        "staging": {
            "targetType": fact.target_type,
            "targetId": fact.target_id,
            "legalDongCode": fact.legal_dong_code,
            "factType": fact.fact_type,
            "observedAt": fact.observed_at.isoformat(),
            "asOf": fact.as_of.isoformat(),
            "valueJson": fact.value_json,
            "validationStatus": "valid" if fact.data_status == "ok" else fact.data_status,
            "validationMessage": None,
        },
    }


def _provider_object_id(
    dataset: MolitPublicDataDataset,
    legal_dong_code: str,
    deal_ym: str,
    fields: dict[str, str],
) -> str:
    seed = "|".join(
        [
            dataset.dataset_id,
            legal_dong_code,
            deal_ym,
            fields.get("aptNm", ""),
            fields.get("umdNm", ""),
            fields.get("jibun", ""),
            fields.get("dealYear", ""),
            fields.get("dealMonth", ""),
            fields.get("dealDay", ""),
            fields.get("floor", ""),
            fields.get("excluUseAr", ""),
            fields.get("dealAmount", ""),
            fields.get("deposit", ""),
            fields.get("monthlyRent", ""),
        ]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"{dataset.dataset_id}:{legal_dong_code}:{deal_ym}:{digest}"


def _observed_date(fields: dict[str, str]) -> date:
    year = _int_from_text(fields.get("dealYear"))
    month = _int_from_text(fields.get("dealMonth"))
    day = _int_from_text(fields.get("dealDay"))
    if year is None or month is None or day is None:
        raise PublicDataProviderError("MOLIT item has no deal date")
    return date(year, month, day)


def _official_price_raw_row(raw_row: Mapping[str | None, str | None]) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in raw_row.items():
        if key is None:
            continue
        cleaned_key = key.replace("\ufeff", "").strip()
        cleaned_value = (value or "").strip()
        if cleaned_key and cleaned_value:
            values[cleaned_key] = cleaned_value
    return values


def _normalize_csv_header(value: str) -> str:
    return (
        value.replace("\ufeff", "")
        .replace(" ", "")
        .replace("_", "")
        .strip()
        .lower()
    )


def _cell(row: Mapping[str, str], *aliases: str) -> str | None:
    for alias in aliases:
        value = row.get(_normalize_csv_header(alias))
        if value:
            return value
    return None


def _join_legal_dong_code(sigungu_code: str | None, dong_code: str | None) -> str | None:
    normalized_sigungu = "" if sigungu_code is None else re.sub(r"\D", "", sigungu_code)
    normalized_dong = "" if dong_code is None else re.sub(r"\D", "", dong_code)
    if len(normalized_dong) == 10:
        return normalized_dong
    if len(normalized_sigungu) == 5 and len(normalized_dong) == 5:
        return f"{normalized_sigungu}{normalized_dong}"
    if normalized_sigungu:
        return normalized_sigungu
    if normalized_dong:
        return normalized_dong
    return None


def _jibun(bun: str | None, ji: str | None) -> str | None:
    if bun and ji:
        return f"{bun}-{ji}"
    return bun or ji


def _date_from_text(value: str | None) -> date | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if re.fullmatch(r"\d{8}", cleaned):
        return date(int(cleaned[:4]), int(cleaned[4:6]), int(cleaned[6:]))
    return date.fromisoformat(cleaned)


def _parse_deal_ym(value: str) -> date:
    if not re.fullmatch(r"\d{6}", value):
        raise ValueError("deal_ym must be YYYYMM")
    year = int(value[:4])
    month = int(value[4:])
    return date(year, month, 1)


def _validate_lawd_code(value: str) -> None:
    if not re.fullmatch(r"\d{5}", value):
        raise ValueError("lawd_code must be a 5 digit legal-dong prefix")


def _normalize_dataset_name(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"trade", "apt-trade", "molit-apt-trade"}:
        return "trade"
    if normalized in {"rent", "apt-rent", "molit-apt-rent", "lease"}:
        return "rent"
    if normalized in {"offi-trade", "offi", "officetel", "officetel-trade", "molit-offi-trade"}:
        return "offi-trade"
    if normalized in {"offi-rent", "officetel-rent", "molit-offi-rent"}:
        return "offi-rent"
    if normalized in {"rh-trade", "rh", "rowhouse-trade", "molit-rh-trade", "yeollip-trade"}:
        return "rh-trade"
    if normalized in {"rh-rent", "rowhouse-rent", "molit-rh-rent", "yeollip-rent"}:
        return "rh-rent"
    if normalized in {"sh-trade", "sh", "singlehouse-trade", "molit-sh-trade", "danok-trade"}:
        return "sh-trade"
    if normalized in {"sh-rent", "singlehouse-rent", "molit-sh-rent", "danok-rent"}:
        return "sh-rent"
    if normalized in {"silv-trade", "silv", "presale", "presale-trade", "bunyang", "molit-silv-trade"}:
        return "silv-trade"
    raise ValueError(f"unsupported real-estate public data dataset: {value}")


def _item_fields(item: ET.Element) -> dict[str, str]:
    return {
        _local_name(child.tag): (child.text or "").strip()
        for child in list(item)
        if _local_name(child.tag) and (child.text or "").strip()
    }


def _elements(root: ET.Element, local_name: str) -> list[ET.Element]:
    return [element for element in root.iter() if _local_name(element.tag) == local_name]


def _first_text(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if _local_name(element.tag) == local_name and element.text:
            return element.text.strip()
    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _int_from_text(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = value.replace(",", "").replace(" ", "").strip()
    if not cleaned or cleaned == "-":
        return None
    return int(cleaned)


def _float_from_text(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.replace(",", "").replace(" ", "").strip()
    if not cleaned or cleaned == "-":
        return None
    return float(cleaned)


def _number_from_text(value: str | None) -> int | float | None:
    if value is None:
        return None
    cleaned = value.replace(",", "").replace(" ", "").strip()
    if not cleaned or cleaned == "-":
        return None
    number = float(cleaned)
    return int(number) if number.is_integer() else number


def _without_empty_values(values: dict) -> dict:
    return {key: value for key, value in values.items() if value is not None and value != ""}


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")
