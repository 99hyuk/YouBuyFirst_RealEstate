import io
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from youbuyfirst_pipeline.realestate_public_data import (
    DATA_GO_SERVICE_KEY_ENV,
    MOLIT_APT_RENT_DATASET,
    MOLIT_APT_TRADE_DATASET,
    MOLIT_OFFI_TRADE_DATASET,
    MolitRealEstatePublicDataClient,
    PublicDataProviderError,
    build_official_apartment_price_raw_ingestions,
    build_molit_raw_ingestions,
    build_molit_public_data_client_from_env,
    collect_molit_real_estate_market_facts,
    collect_molit_real_estate_market_facts_from_data_targets,
    inspect_official_apartment_price_csv,
    inspect_regional_stat_csv,
    iter_official_apartment_price_market_facts,
    iter_regional_stat_market_facts,
    parse_molit_public_data_xml,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "realestate"


class _FakeMolitClient:
    def __init__(self) -> None:
        self.calls = []

    def fetch_apt_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        self.calls.append(("trade", lawd_code, deal_ym, now))
        return ["trade-fact"]

    def fetch_apt_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        self.calls.append(("rent", lawd_code, deal_ym, now))
        return ["rent-fact"]


def test_molit_client_builds_trade_request_and_normalizes_market_fact():
    calls = []

    def fetcher(url, params):
        calls.append((url, dict(params)))
        return (FIXTURE_DIR / "molit_apt_trade_sample.xml").read_text(encoding="utf-8")

    client = MolitRealEstatePublicDataClient(
        service_key="secret-service-key",
        fetcher=fetcher,
    )

    facts = client.fetch_apt_trades(
        lawd_code="11110",
        deal_ym="202606",
        now=datetime(2026, 6, 11, 0, 5, tzinfo=timezone.utc),
    )

    assert calls == [
        (
            MOLIT_APT_TRADE_DATASET.endpoint_url,
            {
                "serviceKey": "secret-service-key",
                "LAWD_CD": "11110",
                "DEAL_YMD": "202606",
                "pageNo": "1",
                "numOfRows": "100",
            },
        )
    ]
    assert len(facts) == 1

    payload = facts[0].to_ingestion_dict()
    assert payload["factType"] == "apt_trade"
    assert payload["provider"] == "molit"
    assert payload["providerDataset"] == "molit_apt_trade"
    assert payload["legalDongCode"] == "11110"
    assert payload["observedAt"] == "2026-06-03"
    assert payload["asOf"] == "2026-06-01"
    assert payload["ingestedAt"] == "2026-06-11T00:05:00Z"
    assert payload["dataStatus"] == "ok"
    assert payload["stale"] is False
    assert payload["providerObjectId"].startswith("molit_apt_trade:11110:202606:")
    assert payload["valueJson"] == {
        "apartmentName": "Sajik Palace",
        "legalDongName": "Sajik-dong",
        "jibun": "1-1",
        "dealAmountManwon": 82500,
        "exclusiveAreaM2": 84.97,
        "floor": 12,
        "builtYear": 2015,
        "dealingType": "brokered",
        "raw": {
            "aptNm": "Sajik Palace",
            "buildYear": "2015",
            "dealAmount": "82,500",
            "dealDay": "3",
            "dealMonth": "6",
            "dealYear": "2026",
            "dealingGbn": "brokered",
            "excluUseAr": "84.97",
            "floor": "12",
            "jibun": "1-1",
            "sggCd": "11110",
            "umdNm": "Sajik-dong",
        },
    }


def test_molit_client_fetches_offi_trade_and_maps_offi_name():
    calls = []

    def fetcher(url, params):
        calls.append((url, dict(params)))
        return (FIXTURE_DIR / "molit_offi_trade_sample.xml").read_text(encoding="utf-8")

    client = MolitRealEstatePublicDataClient(service_key="secret-service-key", fetcher=fetcher)

    facts = client.fetch_offi_trades(
        lawd_code="11680",
        deal_ym="202605",
        now=datetime(2026, 6, 22, 0, 0, tzinfo=timezone.utc),
    )

    assert calls[0][0] == MOLIT_OFFI_TRADE_DATASET.endpoint_url
    assert len(facts) == 2

    payload = facts[0].to_ingestion_dict()
    assert payload["factType"] == "offi_trade"
    assert payload["providerDataset"] == "molit_offi_trade"
    assert payload["legalDongCode"] == "11680"
    assert payload["observedAt"] == "2026-05-28"
    assert payload["providerObjectId"].startswith("molit_offi_trade:11680:202605:")
    # offiNm is mapped onto apartmentName so it flows through the existing UI pipeline
    assert payload["valueJson"]["apartmentName"] == "사이룩스"
    assert payload["valueJson"]["legalDongName"] == "수서동"
    assert payload["valueJson"]["dealAmountManwon"] == 28000
    assert payload["valueJson"]["exclusiveAreaM2"] == 40.88


def test_collect_offi_trade_dataset_routes_to_offi_fetch():
    class _OffiFakeClient:
        def __init__(self):
            self.calls = []

        def fetch_apt_trades(self, *args, **kwargs):
            self.calls.append("trade")
            return []

        def fetch_apt_rents(self, *args, **kwargs):
            self.calls.append("rent")
            return []

        def fetch_offi_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
            self.calls.append(("offi", lawd_code, deal_ym))
            return ["offi-fact"]

    client = _OffiFakeClient()
    facts = collect_molit_real_estate_market_facts(
        client,
        lawd_code="11680",
        deal_ym="202605",
        datasets=["offi_trade"],
    )

    assert facts == ["offi-fact"]
    assert client.calls == [("offi", "11680", "202605")]


def test_molit_rent_parser_preserves_deposit_monthly_rent_and_contract_fields():
    xml_text = (FIXTURE_DIR / "molit_apt_rent_sample.xml").read_text(encoding="utf-8")

    facts = parse_molit_public_data_xml(
        MOLIT_APT_RENT_DATASET,
        xml_text,
        lawd_code="11110",
        deal_ym="202606",
        ingested_at=datetime(2026, 6, 11, 0, 7, tzinfo=timezone.utc),
    )

    assert len(facts) == 1
    payload = facts[0].to_ingestion_dict()
    assert payload["factType"] == "apt_rent"
    assert payload["providerDataset"] == "molit_apt_rent"
    assert payload["observedAt"] == "2026-06-05"
    assert payload["asOf"] == "2026-06-01"
    assert payload["valueJson"]["depositAmountManwon"] == 45000
    assert payload["valueJson"]["monthlyRentAmountManwon"] == 120
    assert payload["valueJson"]["contractType"] == "renewal"
    assert payload["valueJson"]["contractTerm"] == "202606-202806"


def test_molit_parser_raises_provider_error_for_non_ok_response():
    xml_text = """
    <response>
      <header>
        <resultCode>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</resultCode>
        <resultMsg>bad key</resultMsg>
      </header>
      <body><items /></body>
    </response>
    """

    with pytest.raises(PublicDataProviderError, match="SERVICE_KEY_IS_NOT_REGISTERED_ERROR"):
        parse_molit_public_data_xml(
            MOLIT_APT_TRADE_DATASET,
            xml_text,
            lawd_code="11110",
            deal_ym="202606",
            ingested_at=datetime(2026, 6, 11, tzinfo=timezone.utc),
        )


def test_build_molit_public_data_client_from_env_requires_service_key(monkeypatch):
    monkeypatch.delenv(DATA_GO_SERVICE_KEY_ENV, raising=False)

    with pytest.raises(ValueError, match=DATA_GO_SERVICE_KEY_ENV):
        build_molit_public_data_client_from_env()

    monkeypatch.setenv(DATA_GO_SERVICE_KEY_ENV, "secret-service-key")

    client = build_molit_public_data_client_from_env()

    assert client.service_key == "secret-service-key"


def test_collect_molit_real_estate_market_facts_fetches_selected_datasets_with_same_clock():
    client = _FakeMolitClient()
    now = datetime(2026, 6, 11, 0, 30, tzinfo=timezone.utc)

    facts = collect_molit_real_estate_market_facts(
        client,
        lawd_code="11110",
        deal_ym="202606",
        datasets=["trade", "rent"],
        now=now,
    )

    assert facts == ["trade-fact", "rent-fact"]
    assert client.calls == [
        ("trade", "11110", "202606", now),
        ("rent", "11110", "202606", now),
    ]


def test_collect_molit_real_estate_market_facts_from_backend_targets_groups_by_lawd_code():
    client = _FakeMolitClient()
    now = datetime(2026, 6, 11, 0, 35, tzinfo=timezone.utc)

    facts = collect_molit_real_estate_market_facts_from_data_targets(
        client,
        [
            {
                "provider": "molit",
                "providerDataset": "molit_apt_trade",
                "lawdCode": "11110",
                "enabled": True,
            },
            {
                "provider": "molit",
                "providerDataset": "molit_apt_rent",
                "lawdCode": "11110",
                "enabled": True,
            },
        ],
        deal_ym="202606",
        now=now,
    )

    assert facts == ["trade-fact", "rent-fact"]
    assert client.calls == [
        ("trade", "11110", "202606", now),
        ("rent", "11110", "202606", now),
    ]


def test_collect_molit_real_estate_market_facts_paginates_until_partial_page():
    class PaginatedClient:
        def __init__(self) -> None:
            self.trade_calls = []

        def fetch_apt_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
            self.trade_calls.append(
                {
                    "lawd_code": lawd_code,
                    "deal_ym": deal_ym,
                    "page_no": page_no,
                    "num_rows": num_rows,
                    "now": now,
                }
            )
            pages = {
                1: ["trade-page-1-a", "trade-page-1-b"],
                2: ["trade-page-2-a"],
            }
            return pages.get(page_no, [])

        def fetch_apt_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
            raise AssertionError("rent dataset was not requested")

    client = PaginatedClient()
    now = datetime(2026, 6, 13, 3, 0, tzinfo=timezone.utc)

    facts = collect_molit_real_estate_market_facts(
        client,
        lawd_code="11110",
        deal_ym="202606",
        datasets=["trade"],
        page_size=2,
        max_pages=5,
        now=now,
    )

    assert facts == ["trade-page-1-a", "trade-page-1-b", "trade-page-2-a"]
    assert client.trade_calls == [
        {
            "lawd_code": "11110",
            "deal_ym": "202606",
            "page_no": 1,
            "num_rows": 2,
            "now": now,
        },
        {
            "lawd_code": "11110",
            "deal_ym": "202606",
            "page_no": 2,
            "num_rows": 2,
            "now": now,
        },
    ]


def test_build_molit_raw_ingestions_groups_facts_by_dataset_for_raw_staging_api():
    trade_xml = (FIXTURE_DIR / "molit_apt_trade_sample.xml").read_text(encoding="utf-8")
    rent_xml = (FIXTURE_DIR / "molit_apt_rent_sample.xml").read_text(encoding="utf-8")
    ingested_at = datetime(2026, 6, 12, 0, 0, tzinfo=timezone.utc)
    facts = [
        *parse_molit_public_data_xml(
            MOLIT_APT_TRADE_DATASET,
            trade_xml,
            lawd_code="11110",
            deal_ym="202606",
            ingested_at=ingested_at,
        ),
        *parse_molit_public_data_xml(
            MOLIT_APT_RENT_DATASET,
            rent_xml,
            lawd_code="11110",
            deal_ym="202606",
            ingested_at=ingested_at,
        ),
    ]

    ingestions = build_molit_raw_ingestions(
        facts,
        lawd_code="11110",
        deal_ym="202606",
        started_at=ingested_at,
    )

    assert [ingestion.run_key for ingestion in ingestions] == [
        "molit_apt_trade:11110:202606",
        "molit_apt_rent:11110:202606",
    ]
    payload = ingestions[0].to_request_dict()
    assert payload["run"] == {
        "runKey": "molit_apt_trade:11110:202606",
        "providerDataset": "molit_apt_trade",
        "runType": "backfill",
        "requestedFrom": "2026-06-01",
        "requestedTo": "2026-06-30",
        "requestParams": {
            "LAWD_CD": "11110",
            "DEAL_YMD": "202606",
        },
        "status": "completed",
        "startedAt": "2026-06-12T00:00:00Z",
        "finishedAt": "2026-06-12T00:00:00Z",
    }
    assert payload["items"][0]["landingStatus"] == "landed"
    assert payload["items"][0]["rawPayload"]["aptNm"] == "Sajik Palace"
    assert payload["items"][0]["staging"]["validationStatus"] == "valid"
    assert payload["items"][0]["staging"]["valueJson"]["dealAmountManwon"] == 82500


def test_official_apartment_price_csv_parser_normalizes_row_to_market_fact():
    csv_text = """시도,시군구,시군구코드,법정동코드,읍면,동리,특수지명,번,지,단지명,동명,호명,전용면적(㎡),공동주택가격(원),공시기준일,관리건축물대장PK
서울특별시,강남구,11680,10300,,개포동,,12,0,대치아파트,216동,1201호,84.97,"825,000,000",2025-01-01,11680-3633202
"""
    ingested_at = datetime(2026, 6, 12, 1, 0, tzinfo=timezone.utc)

    facts = list(
        iter_official_apartment_price_market_facts(
            io.StringIO(csv_text),
            ingested_at=ingested_at,
        )
    )

    assert len(facts) == 1
    payload = facts[0].to_ingestion_dict()
    assert payload["targetType"] == "complex_unit"
    assert payload["targetId"] is None
    assert payload["factType"] == "official_apartment_price"
    assert payload["provider"] == "molit"
    assert payload["providerDataset"] == "molit_official_apartment_price_csv"
    assert payload["legalDongCode"] == "1168010300"
    assert payload["observedAt"] == "2025-01-01"
    assert payload["asOf"] == "2025-01-01"
    assert payload["ingestedAt"] == "2026-06-12T01:00:00Z"
    assert payload["providerObjectId"].startswith(
        "molit_official_apartment_price_csv:1168010300:2025-01-01:"
    )
    assert payload["valueJson"] == {
        "sidoName": "서울특별시",
        "sigunguName": "강남구",
        "legalDongName": "개포동",
        "jibun": "12-0",
        "complexName": "대치아파트",
        "dongName": "216동",
        "hoName": "1201호",
        "exclusiveAreaM2": 84.97,
        "officialPriceWon": 825000000,
        "buildingLedgerPk": "11680-3633202",
        "raw": {
            "시도": "서울특별시",
            "시군구": "강남구",
            "시군구코드": "11680",
            "법정동코드": "10300",
            "동리": "개포동",
            "번": "12",
            "지": "0",
            "단지명": "대치아파트",
            "동명": "216동",
            "호명": "1201호",
            "전용면적(㎡)": "84.97",
            "공동주택가격(원)": "825,000,000",
            "공시기준일": "2025-01-01",
            "관리건축물대장PK": "11680-3633202",
        },
    }


def test_build_official_apartment_price_raw_ingestions_chunks_large_file_rows():
    csv_text = """시도,시군구,시군구코드,법정동코드,동리,번,지,단지명,동명,호명,전용면적(㎡),공동주택가격(원),공시기준일,관리건축물대장PK
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1201호,84.97,"825,000,000",2025-01-01,11680-3633202
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1202호,84.97,"826,000,000",2025-01-01,11680-3633203
"""
    started_at = datetime(2026, 6, 12, 1, 5, tzinfo=timezone.utc)
    facts = iter_official_apartment_price_market_facts(
        io.StringIO(csv_text),
        ingested_at=started_at,
    )

    ingestions = list(
        build_official_apartment_price_raw_ingestions(
            facts,
            base_date=date(2025, 1, 1),
            started_at=started_at,
            batch_size=1,
            source_label="sample.csv",
        )
    )

    assert [ingestion.run_key for ingestion in ingestions] == [
        "molit_official_apartment_price_csv:20250101:000001",
        "molit_official_apartment_price_csv:20250101:000002",
    ]
    payload = ingestions[0].to_request_dict()
    assert payload["run"] == {
        "runKey": "molit_official_apartment_price_csv:20250101:000001",
        "providerDataset": "molit_official_apartment_price_csv",
        "runType": "backfill",
        "requestedFrom": "2025-01-01",
        "requestedTo": "2025-01-01",
        "requestParams": {
            "baseDate": "2025-01-01",
            "batchIndex": "000001",
            "sourceLabel": "sample.csv",
        },
        "status": "completed",
        "startedAt": "2026-06-12T01:05:00Z",
        "finishedAt": "2026-06-12T01:05:00Z",
    }
    assert payload["items"][0]["providerDataset"] == "molit_official_apartment_price_csv"
    assert payload["items"][0]["rawPayload"]["호명"] == "1201호"
    assert payload["items"][0]["staging"]["targetType"] == "complex_unit"
    assert payload["items"][0]["staging"]["factType"] == "official_apartment_price"
    assert payload["items"][0]["staging"]["valueJson"]["officialPriceWon"] == 825000000


def test_inspect_official_apartment_price_csv_returns_batch_manifest_without_ingesting():
    csv_text = """시도,시군구,시군구코드,법정동코드,동리,번,지,단지명,동명,호명,전용면적(㎡),공동주택가격(원),공시기준일,관리건축물대장PK
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1201호,84.97,"825,000,000",2025-01-01,11680-3633202
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1202호,84.97,"826,000,000",2025-01-01,11680-3633203
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1203호,84.97,"827,000,000",,11680-3633204
"""
    ingested_at = datetime(2026, 6, 12, 1, 10, tzinfo=timezone.utc)

    manifest = inspect_official_apartment_price_csv(
        io.StringIO(csv_text),
        base_date=date(2025, 1, 1),
        batch_size=1,
        source_label="official-prices.csv",
        ingested_at=ingested_at,
    )

    assert manifest.to_payload() == {
        "providerDataset": "molit_official_apartment_price_csv",
        "sourceLabel": "official-prices.csv",
        "baseDate": "2025-01-01",
        "batchSize": 1,
        "totalRows": 3,
        "validRows": 2,
        "invalidRows": 1,
        "batchCount": 2,
        "firstRunKey": "molit_official_apartment_price_csv:20250101:000001",
        "lastRunKey": "molit_official_apartment_price_csv:20250101:000002",
        "sampleProviderObjectIds": [
            manifest.sample_provider_object_ids[0],
            manifest.sample_provider_object_ids[1],
        ],
        "errorSamples": [
            {
                "rowNumber": 3,
                "message": "official apartment price row has no notice/base date",
            }
        ],
    }


def test_regional_stat_csv_parser_normalizes_monthly_public_stats_to_market_facts():
    csv_text = """기준월,지역코드,지역명,항목,값,단위
202604,11680,서울 강남구,준공후 미분양,17,호
"""
    ingested_at = datetime(2026, 6, 12, 2, 0, tzinfo=timezone.utc)

    facts = list(
        iter_regional_stat_market_facts(
            io.StringIO(csv_text),
            provider="molit_stat",
            provider_dataset="molit_unsold_housing_stat",
            fact_type="unsold_housing",
            ingested_at=ingested_at,
        )
    )

    assert len(facts) == 1
    payload = facts[0].to_ingestion_dict()
    assert payload["targetType"] == "region"
    assert payload["factType"] == "unsold_housing"
    assert payload["provider"] == "molit_stat"
    assert payload["providerDataset"] == "molit_unsold_housing_stat"
    assert payload["legalDongCode"] == "11680"
    assert payload["observedAt"] == "2026-04-01"
    assert payload["asOf"] == "2026-04-01"
    assert payload["providerObjectId"].startswith("molit_unsold_housing_stat:11680:202604:")
    assert payload["valueJson"] == {
        "regionName": "서울 강남구",
        "metricName": "준공후 미분양",
        "value": 17,
        "unit": "호",
        "periodYm": "202604",
        "raw": {
            "기준월": "202604",
            "지역코드": "11680",
            "지역명": "서울 강남구",
            "항목": "준공후 미분양",
            "값": "17",
            "단위": "호",
        },
    }


def test_inspect_regional_stat_csv_returns_batch_manifest_and_error_samples():
    csv_text = """기준월,지역코드,지역명,항목,값,단위
202604,11680,서울 강남구,미분양,17,호
,11650,서울 서초구,미분양,8,호
202604,11710,서울 송파구,미분양,22,호
"""
    ingested_at = datetime(2026, 6, 12, 2, 5, tzinfo=timezone.utc)

    manifest = inspect_regional_stat_csv(
        io.StringIO(csv_text),
        provider="molit_stat",
        provider_dataset="molit_unsold_housing_stat",
        fact_type="unsold_housing",
        batch_size=1,
        source_label="molit-unsold.csv",
        ingested_at=ingested_at,
    )

    assert manifest.to_payload() == {
        "providerDataset": "molit_unsold_housing_stat",
        "sourceLabel": "molit-unsold.csv",
        "batchSize": 1,
        "totalRows": 3,
        "validRows": 2,
        "invalidRows": 1,
        "batchCount": 2,
        "firstRunKey": "molit_unsold_housing_stat:20260401:000001",
        "lastRunKey": "molit_unsold_housing_stat:20260401:000002",
        "sampleProviderObjectIds": [
            manifest.sample_provider_object_ids[0],
            manifest.sample_provider_object_ids[1],
        ],
        "errorSamples": [
            {
                "rowNumber": 2,
                "message": "regional stat row has no period",
            }
        ],
    }
