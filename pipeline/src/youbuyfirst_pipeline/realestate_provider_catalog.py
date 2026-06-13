from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PublicDataDataset:
    dataset_id: str
    provider: str
    provider_name: str
    owner_org: str
    display_name: str
    fact_type: str
    access_method: str
    format: str
    source_url: str
    endpoint_url: str | None
    target_granularity: str
    date_granularity: str
    refresh_interval: str
    stale_after_hours: int
    priority: int
    backfill_required: bool
    enabled_for_backfill: bool
    source_row_count: int | None = None
    notes: str | None = None

    def to_payload(self) -> dict:
        return {
            "datasetId": self.dataset_id,
            "provider": self.provider,
            "providerName": self.provider_name,
            "ownerOrg": self.owner_org,
            "displayName": self.display_name,
            "factType": self.fact_type,
            "accessMethod": self.access_method,
            "format": self.format,
            "sourceUrl": self.source_url,
            "endpointUrl": self.endpoint_url,
            "targetGranularity": self.target_granularity,
            "dateGranularity": self.date_granularity,
            "refreshInterval": self.refresh_interval,
            "staleAfterHours": self.stale_after_hours,
            "priority": self.priority,
            "backfillRequired": self.backfill_required,
            "enabledForBackfill": self.enabled_for_backfill,
            "sourceRowCount": self.source_row_count,
            "notes": self.notes,
        }


PUBLIC_DATA_DATASETS: tuple[PublicDataDataset, ...] = (
    PublicDataDataset(
        dataset_id="molit_apt_trade",
        provider="molit",
        provider_name="국토교통부",
        owner_org="국토교통부",
        display_name="아파트 매매 실거래가",
        fact_type="apt_trade",
        access_method="openapi",
        format="xml",
        source_url="https://www.data.go.kr/data/15126469/openapi.do",
        endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade",
        target_granularity="sigungu",
        date_granularity="month",
        refresh_interval="daily-check",
        stale_after_hours=72,
        priority=10,
        backfill_required=True,
        enabled_for_backfill=True,
        notes="LAWD_CD and DEAL_YMD based collection. Store observedAt/asOf separately.",
    ),
    PublicDataDataset(
        dataset_id="molit_apt_rent",
        provider="molit",
        provider_name="국토교통부",
        owner_org="국토교통부",
        display_name="아파트 전월세 실거래가",
        fact_type="apt_rent",
        access_method="openapi",
        format="xml",
        source_url="https://www.data.go.kr/data/15126474/openapi.do",
        endpoint_url="https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent",
        target_granularity="sigungu",
        date_granularity="month",
        refresh_interval="daily-check",
        stale_after_hours=72,
        priority=20,
        backfill_required=True,
        enabled_for_backfill=True,
        notes="Deposit/monthly-rent facts are normalized into market_facts.",
    ),
    PublicDataDataset(
        dataset_id="molit_official_apartment_price_csv",
        provider="molit",
        provider_name="국토교통부",
        owner_org="국토교통부",
        display_name="공동주택 호별 공시가격",
        fact_type="official_apartment_price",
        access_method="file",
        format="csv_zip",
        source_url="https://www.data.go.kr/data/3073746/fileData.do",
        endpoint_url=None,
        target_granularity="complex_unit",
        date_granularity="year",
        refresh_interval="annual",
        stale_after_hours=24 * 370,
        priority=30,
        backfill_required=True,
        enabled_for_backfill=True,
        source_row_count=15580435,
        notes="Large CSV; import through raw landing and staging, not spreadsheet tooling.",
    ),
    PublicDataDataset(
        dataset_id="reb_real_estate_statistics",
        provider="reb",
        provider_name="한국부동산원",
        owner_org="한국부동산원",
        display_name="부동산통계 조회 서비스",
        fact_type="price_index",
        access_method="openapi",
        format="json_xml",
        source_url="https://www.data.go.kr/data/15134761/openapi.do",
        endpoint_url=None,
        target_granularity="region",
        date_granularity="week_or_month",
        refresh_interval="weekly-monthly",
        stale_after_hours=24 * 45,
        priority=40,
        backfill_required=True,
        enabled_for_backfill=True,
        notes="Use for price index, demand/supply mood, transaction statistics, and regional market context.",
    ),
    PublicDataDataset(
        dataset_id="molit_unsold_housing_stat",
        provider="molit_stat",
        provider_name="국토교통 통계누리",
        owner_org="국토교통부",
        display_name="미분양주택현황보고",
        fact_type="unsold_housing",
        access_method="stat_file_or_api",
        format="csv_json_xml",
        source_url="https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=32",
        endpoint_url=None,
        target_granularity="region",
        date_granularity="month",
        refresh_interval="monthly",
        stale_after_hours=24 * 65,
        priority=50,
        backfill_required=True,
        enabled_for_backfill=True,
        notes="Published around the end of the following month; separate unsold and completed-unsold facts.",
    ),
    PublicDataDataset(
        dataset_id="molit_housing_permit_stat",
        provider="molit_stat",
        provider_name="국토교통 통계누리",
        owner_org="국토교통부",
        display_name="주택 인허가 실적",
        fact_type="housing_permit",
        access_method="file",
        format="csv",
        source_url="https://www.data.go.kr/data/15068726/fileData.do",
        endpoint_url=None,
        target_granularity="region",
        date_granularity="month_or_year",
        refresh_interval="monthly",
        stale_after_hours=24 * 65,
        priority=60,
        backfill_required=True,
        enabled_for_backfill=True,
        notes="Supply leading indicator; later split permits, starts, completions when provider layouts are confirmed.",
    ),
    PublicDataDataset(
        dataset_id="molit_buildinghub_housing_approval",
        provider="molit_buildinghub",
        provider_name="국토교통부 건축HUB",
        owner_org="국토교통부",
        display_name="주택건설사업계획승인 정보",
        fact_type="supply_event",
        access_method="openapi",
        format="json_xml",
        source_url="https://www.data.go.kr/data/15136560/openapi.do",
        endpoint_url=None,
        target_granularity="parcel_or_project",
        date_granularity="event",
        refresh_interval="weekly-check",
        stale_after_hours=24 * 30,
        priority=70,
        backfill_required=False,
        enabled_for_backfill=False,
        notes="Reference source until project key mapping and complex linkage are verified.",
    ),
)


def public_data_catalog_payload() -> dict:
    return {
        "items": [
            dataset.to_payload()
            for dataset in sorted(PUBLIC_DATA_DATASETS, key=lambda item: item.priority)
        ]
    }


def public_data_catalog_seed_sql(*, timestamp: str = "2026-06-12 00:00:00") -> str:
    columns = (
        "dataset_id, provider, provider_name, owner_org, display_name, fact_type, access_method, response_format,\n"
        "    source_url, endpoint_url, target_granularity, date_granularity, refresh_interval, stale_after_hours,\n"
        "    priority, backfill_required, enabled_for_backfill, source_row_count, notes, created_at, updated_at"
    )
    rows = []
    for dataset in sorted(PUBLIC_DATA_DATASETS, key=lambda item: item.priority):
        values = [
            dataset.dataset_id,
            dataset.provider,
            dataset.provider_name,
            dataset.owner_org,
            dataset.display_name,
            dataset.fact_type,
            dataset.access_method,
            dataset.format,
            dataset.source_url,
            dataset.endpoint_url,
            dataset.target_granularity,
            dataset.date_granularity,
            dataset.refresh_interval,
            dataset.stale_after_hours,
            dataset.priority,
            dataset.backfill_required,
            dataset.enabled_for_backfill,
            dataset.source_row_count,
            dataset.notes,
            timestamp,
            timestamp,
        ]
        rows.append(f"    ({', '.join(_sql_value(value) for value in values)})")
    return (
        "insert into real_estate_public_data_datasets (\n"
        f"    {columns}\n"
        ") values\n"
        + ",\n".join(rows)
        + ";"
    )


def enabled_backfill_dataset_ids() -> list[str]:
    return [
        dataset.dataset_id
        for dataset in sorted(PUBLIC_DATA_DATASETS, key=lambda item: item.priority)
        if dataset.enabled_for_backfill
    ]


def _sql_value(value: str | int | bool | None) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    escaped = value.replace("'", "''")
    return f"'{escaped}'"
