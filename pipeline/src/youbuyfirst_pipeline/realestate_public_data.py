from __future__ import annotations

import calendar
import csv
import hashlib
import io
import json
import math
import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol

import httpx

DATA_GO_SERVICE_KEY_ENV = "DATA_GO_SERVICE_KEY"

_OK_RESULT_CODES = {"00", "000", "INFO-000"}
_RETRYABLE_HTTP_STATUS_CODES = {502, 503, 504}


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

MOLIT_OFFICIAL_APARTMENT_PRICE_DATASET_ID = "molit_official_apartment_price_csv"
REB_RONE_MAIN_SNAPSHOT_DATASET_ID = "reb_rone_main_snapshot"
REB_RONE_MAIN_URL = "https://www.reb.or.kr/r-one/portal/main/indexPage.do"
REB_RONE_REGIONAL_MAP_DATASET_ID = "reb_rone_regional_price_change"
REB_RONE_REGIONAL_MAP_URL = "https://www.reb.or.kr/r-one/portal/main/searchRegionalStatusMap.do"
REB_RONE_MONTHLY_APT_SALE_PRICE_INDEX_DATASET_ID = "reb_rone_monthly_apt_sale_price_index"
REB_RONE_EASY_STAT_PAGE_URL = "https://www.reb.or.kr/r-one/portal/stat/easyStatPage/A_2024_00045.do"
REB_RONE_EASY_STAT_DATA_URL = "https://www.reb.or.kr/r-one/portal/stat/sttsDataPreviewList.do"
REB_RONE_APT_SALE_PRICE_STATBL_ID = "A_2024_00045"

_REB_RONE_PROVINCE_BY_CODE_PREFIX = {
    "11": "서울",
    "26": "부산",
    "27": "대구",
    "28": "인천",
    "29": "광주",
    "30": "대전",
    "31": "울산",
    "36": "세종",
    "41": "경기",
    "42": "강원",
    "43": "충북",
    "44": "충남",
    "45": "전북",
    "46": "전남",
    "47": "경북",
    "48": "경남",
    "50": "제주",
    "51": "강원",
    "52": "전북",
}

_REB_RONE_SIDO_TARGETS_BY_NAME = {
    "서울": ("region-seoul", "11"),
    "부산": ("region-busan", "21"),
    "대구": ("region-daegu", "22"),
    "인천": ("region-incheon", "23"),
    "광주": ("region-gwangju", "24"),
    "대전": ("region-daejeon", "25"),
    "울산": ("region-ulsan", "26"),
    "세종": ("region-sejong", "29"),
    "경기": ("region-gyeonggi", "31"),
    "강원": ("region-gangwon", "32"),
    "충북": ("region-chungbuk", "33"),
    "충남": ("region-chungnam", "34"),
    "전북": ("region-jeonbuk", "35"),
    "전남": ("region-jeonnam", "36"),
    "경북": ("region-gyeongbuk", "37"),
    "경남": ("region-gyeongnam", "38"),
    "제주": ("region-jeju", "39"),
}


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
    error_message: str | None = None

    def to_request_dict(self) -> dict:
        requested_from = _parse_deal_ym(self.deal_ym)
        requested_to = date(
            requested_from.year,
            requested_from.month,
            calendar.monthrange(requested_from.year, requested_from.month)[1],
        )
        run = {
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
        }
        if self.error_message:
            run["errorMessage"] = self.error_message
        return {
            "run": run,
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
    error_message: str | None = None

    def to_request_dict(self) -> dict:
        run = {
            "runKey": self.run_key,
            "providerDataset": self.provider_dataset,
            "runType": "backfill",
            "requestedFrom": self.requested_from.isoformat(),
            "requestedTo": self.requested_to.isoformat(),
            "requestParams": dict(self.request_params),
            "status": self.status,
            "startedAt": _iso(self.started_at),
            "finishedAt": _iso(self.finished_at),
        }
        if self.error_message:
            run["errorMessage"] = self.error_message
        return {
            "run": run,
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
SimpleTextFetcher = Callable[[str], str]


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


class RebRoneMainSnapshotClient:
    def __init__(
        self,
        fetcher: SimpleTextFetcher | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.fetcher = fetcher or self._fetch

    def fetch_main_snapshot(self, now: datetime | None = None) -> list[RealEstateMarketFact]:
        html_text = self.fetcher(REB_RONE_MAIN_URL)
        return parse_reb_rone_main_snapshot(html_text, ingested_at=now or datetime.now(timezone.utc))

    def _fetch(self, url: str) -> str:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise PublicDataProviderError(f"REB R-ONE main snapshot request failed: {url} error=timeout") from exc
        except httpx.HTTPStatusError as exc:
            raise PublicDataProviderError(
                f"REB R-ONE main snapshot request failed: {url} status={exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise PublicDataProviderError(
                f"REB R-ONE main snapshot request failed: {url} error={exc.__class__.__name__}"
            ) from exc


class RebRoneRegionalMapClient:
    def __init__(
        self,
        fetcher: Callable[[str, Mapping[str, str]], str] | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.fetcher = fetcher or self._fetch

    def fetch_regional_map(
        self,
        geo_cd: str = "10",
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        params = {
            "statblId": REB_RONE_APT_SALE_PRICE_STATBL_ID,
            "dtacycleCd": "MM",
            "itmDatano": "100001",
            "geoCd": geo_cd,
            "dtadvsCd": "PR",
            "itmTag": "C",
            "clsDatano": "",
        }
        json_text = self.fetcher(REB_RONE_REGIONAL_MAP_URL, params)
        return parse_reb_rone_regional_map(json_text, ingested_at=now or datetime.now(timezone.utc))

    def _fetch(self, url: str, params: Mapping[str, str]) -> str:
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                client.get(REB_RONE_MAIN_URL)
                response = client.post(
                    url,
                    data=params,
                    headers={
                        "Referer": REB_RONE_MAIN_URL,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                )
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException as exc:
            raise PublicDataProviderError(f"REB R-ONE regional map request failed: {url} error=timeout") from exc
        except httpx.HTTPStatusError as exc:
            raise PublicDataProviderError(
                f"REB R-ONE regional map request failed: {url} status={exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise PublicDataProviderError(
                f"REB R-ONE regional map request failed: {url} error={exc.__class__.__name__}"
            ) from exc


class RebRoneMonthlyAptSalePriceIndexClient:
    def __init__(
        self,
        fetcher: Callable[[str, int], tuple[str, str]] | None = None,
        timeout_seconds: float = 20,
        latest_months: int = 13,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.latest_months = max(2, latest_months)
        self.fetcher = fetcher or self._fetch

    def fetch_monthly_price_index_changes(
        self,
        now: datetime | None = None,
    ) -> list[RealEstateMarketFact]:
        table_json, regional_map_json = self.fetcher(REB_RONE_EASY_STAT_PAGE_URL, self.latest_months)
        lookup = build_reb_rone_region_lookup_from_regional_map_json(regional_map_json)
        return parse_reb_rone_monthly_price_index_changes(
            table_json,
            ingested_at=now or datetime.now(timezone.utc),
            region_lookup=lookup,
        )

    def _fetch(self, url: str, latest_months: int) -> tuple[str, str]:
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                page_response = client.get(url)
                page_response.raise_for_status()
                fir_param = _reb_rone_fir_param(page_response.text)
                params = dict(_parse_query_pairs(fir_param))
                params["wrttimeLastestVal"] = str(latest_months)
                data_response = client.post(
                    REB_RONE_EASY_STAT_DATA_URL,
                    data=params,
                    headers={
                        "Referer": str(page_response.url),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                )
                data_response.raise_for_status()
                regional_map_response = client.post(
                    REB_RONE_REGIONAL_MAP_URL,
                    data={
                        "statblId": REB_RONE_APT_SALE_PRICE_STATBL_ID,
                        "dtacycleCd": "MM",
                        "itmDatano": "100001",
                        "geoCd": "10",
                        "dtadvsCd": "PR",
                        "itmTag": "C",
                        "clsDatano": "",
                    },
                    headers={
                        "Referer": REB_RONE_MAIN_URL,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                )
                regional_map_response.raise_for_status()
            return data_response.text, regional_map_response.text
        except httpx.TimeoutException as exc:
            raise PublicDataProviderError(f"REB R-ONE monthly price index request failed: {url} error=timeout") from exc
        except httpx.HTTPStatusError as exc:
            raise PublicDataProviderError(
                f"REB R-ONE monthly price index request failed: {url} status={exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise PublicDataProviderError(
                f"REB R-ONE monthly price index request failed: {url} error={exc.__class__.__name__}"
            ) from exc


class MolitRealEstatePublicDataClient:
    def __init__(
        self,
        service_key: str,
        fetcher: PublicDataFetcher | None = None,
        timeout_seconds: float = 20,
        max_retries: int = 0,
        retry_backoff_seconds: float = 1,
    ) -> None:
        normalized_key = service_key.strip()
        if not normalized_key:
            raise ValueError(f"{DATA_GO_SERVICE_KEY_ENV} is required")
        self.service_key = normalized_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
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
        attempts = self.max_retries + 1
        last_status: int | None = None
        last_error = "unknown"
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(url, params=params)
                last_status = response.status_code
                if response.status_code in _RETRYABLE_HTTP_STATUS_CODES and attempt < self.max_retries:
                    last_error = f"http_{response.status_code}"
                    self._sleep_before_retry(attempt)
                    continue
                response.raise_for_status()
                return response.text
            except httpx.TimeoutException as exc:
                last_error = "timeout"
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                raise PublicDataProviderError(
                    f"MOLIT public data request failed: {url} error=timeout attempts={attempts}"
                ) from exc
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                last_status = status
                last_error = f"http_{status}"
                if status in _RETRYABLE_HTTP_STATUS_CODES and attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                raise PublicDataProviderError(
                    f"MOLIT public data request failed: {url} status={status} attempts={attempts}"
                ) from exc
            except httpx.HTTPError as exc:
                last_error = exc.__class__.__name__
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                raise PublicDataProviderError(
                    f"MOLIT public data request failed: {url} error={last_error} attempts={attempts}"
                ) from exc
        status_part = f" status={last_status}" if last_status is not None else ""
        raise PublicDataProviderError(
            f"MOLIT public data request failed: {url}{status_part} error={last_error} attempts={attempts}"
        )

    def _sleep_before_retry(self, attempt: int) -> None:
        if self.retry_backoff_seconds <= 0:
            return
        time.sleep(self.retry_backoff_seconds * (attempt + 1))


def build_molit_public_data_client_from_env() -> MolitRealEstatePublicDataClient:
    service_key = os.getenv(DATA_GO_SERVICE_KEY_ENV)
    if not service_key:
        raise ValueError(f"{DATA_GO_SERVICE_KEY_ENV} is required")
    timeout_seconds = float(
        os.getenv("REALESTATE_PUBLIC_DATA_TIMEOUT_SECONDS")
        or os.getenv("DATA_GO_TIMEOUT_SECONDS")
        or "20"
    )
    max_retries = int(
        os.getenv("REALESTATE_PUBLIC_DATA_MAX_RETRIES")
        or os.getenv("DATA_GO_MAX_RETRIES")
        or "1"
    )
    retry_backoff_seconds = float(
        os.getenv("REALESTATE_PUBLIC_DATA_RETRY_BACKOFF_SECONDS")
        or os.getenv("DATA_GO_RETRY_BACKOFF_SECONDS")
        or "1"
    )
    return MolitRealEstatePublicDataClient(
        service_key=service_key,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )


def build_reb_rone_main_snapshot_client_from_env() -> RebRoneMainSnapshotClient:
    timeout_seconds = float(
        os.getenv("REALESTATE_REB_RONE_TIMEOUT_SECONDS")
        or os.getenv("REALESTATE_PUBLIC_DATA_TIMEOUT_SECONDS")
        or "20"
    )
    return RebRoneMainSnapshotClient(timeout_seconds=timeout_seconds)


def build_reb_rone_regional_map_client_from_env() -> RebRoneRegionalMapClient:
    timeout_seconds = float(
        os.getenv("REALESTATE_REB_RONE_TIMEOUT_SECONDS")
        or os.getenv("REALESTATE_PUBLIC_DATA_TIMEOUT_SECONDS")
        or "20"
    )
    return RebRoneRegionalMapClient(timeout_seconds=timeout_seconds)


def collect_reb_rone_main_snapshot_facts(
    client: RebRoneMainSnapshotClient,
    now: datetime | None = None,
) -> list[RealEstateMarketFact]:
    return client.fetch_main_snapshot(now=now)


def collect_reb_rone_regional_map_facts(
    client: RebRoneRegionalMapClient,
    geo_cd: str = "10",
    now: datetime | None = None,
) -> list[RealEstateMarketFact]:
    return client.fetch_regional_map(geo_cd=geo_cd, now=now)


def build_reb_rone_monthly_price_index_client_from_env() -> RebRoneMonthlyAptSalePriceIndexClient:
    timeout_seconds = float(
        os.getenv("REALESTATE_REB_RONE_TIMEOUT_SECONDS")
        or os.getenv("REALESTATE_PUBLIC_DATA_TIMEOUT_SECONDS")
        or "20"
    )
    latest_months = int(os.getenv("REALESTATE_REB_RONE_MONTHLY_PRICE_INDEX_MONTHS") or "13")
    return RebRoneMonthlyAptSalePriceIndexClient(
        timeout_seconds=timeout_seconds,
        latest_months=latest_months,
    )


def collect_reb_rone_monthly_price_index_change_facts(
    client: RebRoneMonthlyAptSalePriceIndexClient,
    now: datetime | None = None,
) -> list[RealEstateMarketFact]:
    return client.fetch_monthly_price_index_changes(now=now)


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
    if "trade" in normalized_datasets:
        facts.extend(
            _fetch_paginated_molit_facts(
                lambda page_no: client.fetch_apt_trades(
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
    if "rent" in normalized_datasets:
        facts.extend(
            _fetch_paginated_molit_facts(
                lambda page_no: client.fetch_apt_rents(
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


def parse_reb_rone_main_snapshot(
    html_text: str,
    ingested_at: datetime,
) -> list[RealEstateMarketFact]:
    facts: list[RealEstateMarketFact] = []
    for args in _reb_rone_major_stat_args(html_text):
        fact = _reb_rone_major_stat_fact(args, ingested_at=ingested_at)
        if fact is not None:
            facts.append(fact)
    if not facts:
        raise PublicDataProviderError("REB R-ONE main snapshot contained no supported major stats")
    return facts


def parse_reb_rone_regional_map(
    json_text: str,
    *,
    ingested_at: datetime,
) -> list[RealEstateMarketFact]:
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise PublicDataProviderError("REB R-ONE regional map response is not JSON") from exc

    rows = payload.get("data")
    if not isinstance(rows, list):
        result = payload.get("RESULT")
        if isinstance(result, Mapping):
            code = result.get("CODE") or "unknown"
            message = result.get("MESSAGE") or "unknown provider error"
            raise PublicDataProviderError(f"REB R-ONE regional map failed with {code}: {message}")
        raise PublicDataProviderError("REB R-ONE regional map response has no data rows")

    facts: list[RealEstateMarketFact] = []
    seen_provider_object_ids: set[str] = set()
    for raw_row in rows:
        if not isinstance(raw_row, Mapping):
            continue
        row = {str(key): "" if value is None else str(value) for key, value in raw_row.items()}
        fact = _reb_rone_regional_map_fact(row, ingested_at=ingested_at)
        if fact is None or fact.provider_object_id in seen_provider_object_ids:
            continue
        facts.append(fact)
        seen_provider_object_ids.add(fact.provider_object_id)

    if not facts:
        raise PublicDataProviderError("REB R-ONE regional map contained no supported rows")
    return facts


def build_reb_rone_region_lookup_from_regional_map_json(
    json_text: str,
) -> dict[tuple[str, str], dict[str, str | None]]:
    facts = parse_reb_rone_regional_map(json_text, ingested_at=datetime.now(timezone.utc))
    lookup: dict[tuple[str, str], dict[str, str | None]] = {}
    for fact in facts:
        payload = fact.to_ingestion_dict()
        value_json = payload.get("valueJson", {})
        region_name = str(value_json.get("regionName") or "").strip()
        legal_dong_code = str(payload.get("legalDongCode") or "").strip()
        if not region_name or not legal_dong_code or region_name == "전국":
            continue
        province_name = _reb_rone_province_for_legal_dong_code(legal_dong_code)
        if not province_name:
            continue
        lookup[(province_name, region_name)] = {
            "legalDongCode": legal_dong_code,
            "targetId": payload.get("targetId"),
        }
    return lookup


def parse_reb_rone_monthly_price_index_changes(
    json_text: str,
    *,
    ingested_at: datetime,
    region_lookup: Mapping[tuple[str, str], Mapping[str, str | None]],
) -> list[RealEstateMarketFact]:
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise PublicDataProviderError("REB R-ONE monthly price index response is not JSON") from exc

    rows = payload.get("DATA")
    if not isinstance(rows, list):
        raise PublicDataProviderError("REB R-ONE monthly price index response has no DATA rows")

    facts: list[RealEstateMarketFact] = []
    seen_provider_object_ids: set[str] = set()
    for raw_row in rows:
        if not isinstance(raw_row, Mapping):
            continue
        row = {str(key): "" if value is None else str(value) for key, value in raw_row.items()}
        row_facts = _reb_rone_monthly_price_index_row_facts(
            row,
            ingested_at=ingested_at,
            region_lookup=region_lookup,
        )
        for fact in row_facts:
            if fact.provider_object_id in seen_provider_object_ids:
                continue
            facts.append(fact)
            seen_provider_object_ids.add(fact.provider_object_id)

    if not facts:
        raise PublicDataProviderError("REB R-ONE monthly price index table contained no supported rows")
    return facts


def _reb_rone_monthly_price_index_row_facts(
    row: Mapping[str, str],
    *,
    ingested_at: datetime,
    region_lookup: Mapping[tuple[str, str], Mapping[str, str | None]],
) -> list[RealEstateMarketFact]:
    province_name = str(row.get("CATE1") or "").strip()
    region_name = _reb_rone_monthly_region_name(row)
    if not province_name or not region_name:
        return []

    target = region_lookup.get((province_name, region_name))
    if not target:
        return []

    legal_dong_code = str(target.get("legalDongCode") or "").strip()
    if not legal_dong_code:
        return []

    month_values = _reb_rone_monthly_index_values(row)
    facts: list[RealEstateMarketFact] = []
    for index, (period_key, index_value) in enumerate(month_values):
        if index == 0:
            continue
        previous_period_key, previous_index_value = month_values[index - 1]
        if previous_index_value is None or index_value is None or previous_index_value == 0:
            continue
        change_pct = round(((index_value - previous_index_value) / previous_index_value) * 100, 4)
        observed_at, _ = _reb_rone_period(period_key)
        provider_object_id = (
            f"{REB_RONE_MONTHLY_APT_SALE_PRICE_INDEX_DATASET_ID}:"
            f"{REB_RONE_APT_SALE_PRICE_STATBL_ID}:{period_key}:{legal_dong_code}"
        )
        source_label = "한국부동산원 R-ONE 월간 아파트 매매가격지수"
        facts.append(
            RealEstateMarketFact(
                fact_type="sale_price_index_change_pct",
                provider="reb",
                provider_dataset=REB_RONE_MONTHLY_APT_SALE_PRICE_INDEX_DATASET_ID,
                provider_object_id=provider_object_id,
                legal_dong_code=legal_dong_code,
                observed_at=observed_at,
                as_of=observed_at,
                ingested_at=ingested_at,
                value_json=_without_empty_values(
                    {
                        "regionName": region_name,
                        "provinceName": province_name,
                        "metricName": "매매가격지수 변동률",
                        "housingType": "아파트",
                        "surveyName": "전국주택가격동향조사",
                        "value": change_pct,
                        "unit": "%",
                        "periodYm": period_key,
                        "previousPeriodYm": previous_period_key,
                        "indexValue": index_value,
                        "previousIndexValue": previous_index_value,
                        "sourceLabel": source_label,
                        "sourceUrl": REB_RONE_EASY_STAT_PAGE_URL,
                        "raw": {
                            "CATE1": row.get("CATE1"),
                            "CATE2": row.get("CATE2"),
                            "CATE3": row.get("CATE3"),
                            "CATE4": row.get("CATE4"),
                        },
                    }
                ),
                target_type="region",
                target_id=target.get("targetId"),
                data_status="ok",
            )
        )
    return facts


def _reb_rone_monthly_region_name(row: Mapping[str, str]) -> str:
    for key in ("CATE4", "CATE3", "CATE2", "CATE1"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _reb_rone_monthly_index_values(row: Mapping[str, str]) -> list[tuple[str, float | None]]:
    values: list[tuple[str, float | None]] = []
    for key, value in row.items():
        match = re.match(r"COL_(\d{6})", key)
        if not match:
            continue
        values.append((match.group(1), _number_from_text(value)))
    return sorted(values, key=lambda item: item[0])


def _reb_rone_province_for_legal_dong_code(legal_dong_code: str) -> str | None:
    if legal_dong_code == "00000":
        return None
    return _REB_RONE_PROVINCE_BY_CODE_PREFIX.get(legal_dong_code[:2])


def _reb_rone_regional_map_fact(
    row: Mapping[str, str],
    *,
    ingested_at: datetime,
) -> RealEstateMarketFact | None:
    stat_id = row.get("statblId", "").strip()
    if stat_id != REB_RONE_APT_SALE_PRICE_STATBL_ID:
        return None

    geo_cd = row.get("geoCd", "").strip()
    region_name = row.get("viewItmNm", "").strip()
    period_date, period_key = _reb_rone_period(row.get("wrttimeIdtfrId", ""))
    value = _number_from_text(row.get("dtaVal"))
    target_id, topology_region_code = _reb_rone_target_for_row(region_name)
    legal_dong_code = _reb_rone_legal_dong_code(geo_cd)
    source_label = "한국부동산원 R-ONE 전국주택가격동향조사 매매가격지수 변동률"

    value_json = _without_empty_values(
        {
            "regionName": region_name,
            "metricName": "매매가격지수 변동률",
            "housingType": "아파트",
            "surveyName": "전국주택가격동향조사",
            "value": value,
            "unit": row.get("uiNm") or "%",
            "periodYm": period_key,
            "roneGeoCode": geo_cd,
            "topologyRegionCode": topology_region_code,
            "previousPeriodValue": _number_from_text(row.get("pdDtaVal")),
            "rank": _int_from_text(row.get("odRnk")),
            "sourceLabel": source_label,
            "sourceUrl": REB_RONE_MAIN_URL,
            "raw": dict(row),
        }
    )
    provider_object_id = (
        f"{REB_RONE_REGIONAL_MAP_DATASET_ID}:{stat_id}:{period_key}:"
        f"{geo_cd or row.get('datano') or region_name}"
    )
    return RealEstateMarketFact(
        fact_type="sale_price_index_change_pct",
        provider="reb",
        provider_dataset=REB_RONE_REGIONAL_MAP_DATASET_ID,
        provider_object_id=provider_object_id,
        legal_dong_code=legal_dong_code,
        observed_at=period_date,
        as_of=period_date,
        ingested_at=ingested_at,
        value_json=value_json,
        target_type="region",
        target_id=target_id,
        data_status="ok" if value is not None and geo_cd else "partial",
    )


def _reb_rone_target_for_row(region_name: str) -> tuple[str | None, str | None]:
    if region_name == "전국":
        return None, None
    return _REB_RONE_SIDO_TARGETS_BY_NAME.get(region_name, (None, None))


def _reb_rone_legal_dong_code(geo_cd: str) -> str:
    if not geo_cd:
        return "unknown"
    if geo_cd == "10":
        return "00000"
    return geo_cd


def _reb_rone_major_stat_args(html_text: str) -> Iterator[tuple[str, ...]]:
    pattern = re.compile(r"doEvent\.changeMajorStat\((.*?)\)", re.DOTALL)
    for match in pattern.finditer(html_text):
        parsed = _parse_js_string_args(match.group(1))
        if parsed:
            yield parsed


def _reb_rone_fir_param(html_text: str) -> str:
    match = re.search(r'id="firParam"[^>]*value="([^"]+)"', html_text)
    if not match:
        raise PublicDataProviderError("REB R-ONE easy stat page has no firParam")
    return match.group(1)


def _parse_query_pairs(value: str) -> list[tuple[str, str]]:
    return urllib.parse.parse_qsl(value, keep_blank_values=True)


def _parse_js_string_args(raw_args: str) -> tuple[str, ...]:
    values: list[str] = []
    current: list[str] = []
    in_string = False
    escaped = False
    for char in raw_args:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == "'":
            if in_string:
                values.append("".join(current).strip())
                current = []
                in_string = False
            else:
                in_string = True
            continue
        if in_string:
            current.append(char)
    return tuple(values)


def _reb_rone_major_stat_fact(
    args: tuple[str, ...],
    *,
    ingested_at: datetime,
) -> RealEstateMarketFact | None:
    if len(args) < 9:
        return None
    stat_code, period_code, metric_name, value_kind, unit, housing_type, period_label, value_text, survey_name = args[:9]
    fact_type = _reb_rone_fact_type(metric_name, housing_type, survey_name)
    if fact_type is None:
        return None
    observed_at, period_key = _reb_rone_period(period_label)
    value = _number_from_text(value_text)
    raw = {
        "statCode": stat_code,
        "periodCode": period_code,
        "metricName": metric_name,
        "valueKind": value_kind,
        "unit": unit,
        "housingType": housing_type,
        "periodLabel": period_label,
        "value": value_text,
        "surveyName": survey_name,
    }
    value_json = _without_empty_values(
        {
            "regionName": "전국",
            "metricName": metric_name,
            "surveyName": survey_name,
            "housingType": housing_type,
            "value": value,
            "unit": unit,
            "periodLabel": period_label,
            "periodYm": period_key,
            "sourceUrl": REB_RONE_MAIN_URL,
            "raw": raw,
        }
    )
    return RealEstateMarketFact(
        fact_type=fact_type,
        provider="reb",
        provider_dataset=REB_RONE_MAIN_SNAPSHOT_DATASET_ID,
        provider_object_id=f"{REB_RONE_MAIN_SNAPSHOT_DATASET_ID}:{stat_code}:{period_key}",
        legal_dong_code="00000",
        observed_at=observed_at,
        as_of=observed_at,
        ingested_at=ingested_at,
        value_json=value_json,
        target_type="region",
        target_id=None,
        data_status="ok" if value is not None else "partial",
    )


def _reb_rone_fact_type(metric_name: str, housing_type: str, survey_name: str) -> str | None:
    normalized_metric = metric_name.strip()
    normalized_housing = housing_type.strip()
    normalized_survey = survey_name.strip()
    if (
        normalized_metric == "매매가격지수 변동률"
        and normalized_housing == "아파트"
        and normalized_survey == "전국주택가격동향조사"
    ):
        return "sale_price_index_change_pct"
    if (
        normalized_metric == "전세가격지수 변동률"
        and normalized_housing == "아파트"
        and normalized_survey == "전국주택가격동향조사"
    ):
        return "jeonse_price_index_change_pct"
    if normalized_metric == "아파트 매매거래호수" and normalized_survey == "부동산거래현황":
        return "apartment_trade_volume"
    return None


def _reb_rone_period(period_label: str) -> tuple[date, str]:
    cleaned = period_label.strip()
    if re.fullmatch(r"\d{6}", cleaned):
        year = int(cleaned[:4])
        month = int(cleaned[4:])
        return date(year, month, 1), cleaned
    match = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월", period_label)
    if not match:
        raise PublicDataProviderError(f"unsupported REB R-ONE period label: {period_label}")
    year = int(match.group(1))
    month = int(match.group(2))
    return date(year, month, 1), f"{year:04d}{month:02d}"


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
    value_json = _trade_value_json(fields) if dataset.fact_type == "apt_trade" else _rent_value_json(fields)
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
            "apartmentName": fields.get("aptNm"),
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
            "apartmentName": fields.get("aptNm"),
            "legalDongName": fields.get("umdNm"),
            "jibun": fields.get("jibun"),
            "depositAmountManwon": _int_from_text(fields.get("deposit")),
            "monthlyRentAmountManwon": _int_from_text(fields.get("monthlyRent")),
            "exclusiveAreaM2": _float_from_text(fields.get("excluUseAr")),
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
