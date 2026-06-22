import io
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from youbuyfirst_pipeline.realestate_public_data import (
    DATA_GO_SERVICE_KEY_ENV,
    MOLIT_APT_RENT_DATASET,
    MOLIT_APT_TRADE_DATASET,
    MOLIT_OFFI_TRADE_DATASET,
    MOLIT_RH_TRADE_DATASET,
    MOLIT_SH_RENT_DATASET,
    MOLIT_SILV_TRADE_DATASET,
    MolitRealEstatePublicDataClient,
    PublicDataProviderError,
    RebRoneMainSnapshotClient,
    RebRoneMonthlyAptSalePriceIndexClient,
    RebRoneRegionalMapClient,
    build_reb_rone_region_lookup_from_regional_map_json,
    build_official_apartment_price_raw_ingestions,
    build_molit_raw_ingestions,
    build_molit_public_data_client_from_env,
    collect_reb_rone_main_snapshot_facts,
    collect_reb_rone_monthly_price_index_change_facts,
    collect_reb_rone_regional_map_facts,
    collect_molit_real_estate_market_facts,
    collect_molit_real_estate_market_facts_from_data_targets,
    inspect_official_apartment_price_csv,
    inspect_regional_stat_csv,
    iter_official_apartment_price_market_facts,
    iter_regional_stat_market_facts,
    parse_molit_public_data_xml,
    parse_reb_rone_main_snapshot,
    parse_reb_rone_monthly_price_index_changes,
    parse_reb_rone_regional_map,
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


def test_molit_offi_rent_maps_offi_name_and_rent_fields():
    def fetcher(url, params):
        return (
            "<response><header><resultCode>000</resultCode></header><body><items>"
            "<item><offiNm>마르세움</offiNm><deposit>500</deposit><monthlyRent>145</monthlyRent>"
            "<excluUseAr>34.72</excluUseAr><floor>10</floor><buildYear>2004</buildYear>"
            "<contractType>신규</contractType><dealYear>2026</dealYear><dealMonth>5</dealMonth><dealDay>26</dealDay>"
            "<umdNm>논현동</umdNm><sggCd>11680</sggCd></item></items><totalCount>1</totalCount></body></response>"
        )

    client = MolitRealEstatePublicDataClient(service_key="k", fetcher=fetcher)
    facts = client.fetch_offi_rents(lawd_code="11680", deal_ym="202605")

    payload = facts[0].to_ingestion_dict()
    assert payload["factType"] == "offi_rent"
    assert payload["providerDataset"] == "molit_offi_rent"
    assert payload["valueJson"]["apartmentName"] == "마르세움"
    assert payload["valueJson"]["depositAmountManwon"] == 500
    assert payload["valueJson"]["monthlyRentAmountManwon"] == 145


def test_molit_rh_trade_maps_mhouse_name():
    def fetcher(url, params):
        return (FIXTURE_DIR / "molit_rh_trade_sample.xml").read_text(encoding="utf-8")

    client = MolitRealEstatePublicDataClient(service_key="k", fetcher=fetcher)
    facts = client.fetch_rh_trades(lawd_code="11680", deal_ym="202605")

    payload = facts[0].to_ingestion_dict()
    assert payload["factType"] == "rh_trade"
    assert payload["providerDataset"] == "molit_rh_trade"
    # 연립다세대명(mhouseNm)을 단지명으로 매핑해 단지 화면 파이프라인을 재사용한다
    assert payload["valueJson"]["apartmentName"] == "에이트"
    assert payload["valueJson"]["dealAmountManwon"] == 49301
    assert payload["valueJson"]["exclusiveAreaM2"] == 28.49


def test_molit_silv_trade_maps_apt_name():
    def fetcher(url, params):
        return (
            "<response><header><resultCode>000</resultCode></header><body><items>"
            "<item><aptNm>디에이치 퍼스티어 아이파크</aptNm><dealAmount>343,000</dealAmount>"
            "<dealYear>2026</dealYear><dealMonth>5</dealMonth><dealDay>29</dealDay>"
            "<excluUseAr>84.99</excluUseAr><floor>8</floor><umdNm>개포동</umdNm><sggCd>11680</sggCd>"
            "</item></items><totalCount>1</totalCount></body></response>"
        )

    client = MolitRealEstatePublicDataClient(service_key="k", fetcher=fetcher)
    facts = client.fetch_silv_trades(lawd_code="11680", deal_ym="202605")

    payload = facts[0].to_ingestion_dict()
    assert payload["factType"] == "silv_trade"
    assert payload["valueJson"]["apartmentName"] == "디에이치 퍼스티어 아이파크"
    assert payload["valueJson"]["dealAmountManwon"] == 343000


def test_molit_sh_rent_has_no_name_but_keeps_house_fields():
    def fetcher(url, params):
        return (FIXTURE_DIR / "molit_sh_rent_sample.xml").read_text(encoding="utf-8")

    client = MolitRealEstatePublicDataClient(service_key="k", fetcher=fetcher)
    facts = client.fetch_sh_rents(lawd_code="11680", deal_ym="202605")

    payload = facts[0].to_ingestion_dict()
    assert payload["factType"] == "sh_rent"
    # 단독/다가구는 단지명이 없어 apartmentName이 비어 단지 지도에는 표출되지 않는다
    assert "apartmentName" not in payload["valueJson"]
    assert payload["valueJson"]["houseType"] == "다가구"
    assert payload["valueJson"]["depositAmountManwon"] == 1000
    assert payload["valueJson"]["monthlyRentAmountManwon"] == 66


def test_collect_routes_new_housing_datasets():
    class _Fake:
        def __init__(self):
            self.calls = []

        def fetch_rh_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
            self.calls.append("rh_trade")
            return ["rh"]

        def fetch_silv_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
            self.calls.append("silv")
            return ["silv"]

    client = _Fake()
    facts = collect_molit_real_estate_market_facts(
        client, lawd_code="11680", deal_ym="202605", datasets=["rh_trade", "silv_trade"]
    )
    assert sorted(facts) == ["rh", "silv"]
    assert sorted(client.calls) == ["rh_trade", "silv"]


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


def test_reb_rone_main_snapshot_parser_normalizes_major_stats_to_market_facts():
    html_text = """
    <script>
    doEvent.changeMajorStat('A_2024_00045', 'MM', '매매가격지수 변동률', 'PR', '%', '아파트', '2026년 5월', '0.25', '전국주택가격동향조사')
    doEvent.changeMajorStat('A_2024_00050', 'MM', '전세가격지수 변동률', 'PR', '%', '아파트', '2026년 5월', '0.45', '전국주택가격동향조사')
    doEvent.changeMajorStat('A_2024_00554', 'MM', '아파트 매매거래호수', 'OD', '호수', '', '2026년 4월', '53,177', '부동산거래현황')
    doEvent.changeMajorStat('A_2024_00903', 'MM', '지가변동률', 'OD', '%', '', '2026년 4월', '0.204', '전국지가변동률조사')
    </script>
    """

    facts = parse_reb_rone_main_snapshot(
        html_text,
        ingested_at=datetime(2026, 6, 15, 1, 0, tzinfo=timezone.utc),
    )

    payloads = [fact.to_ingestion_dict() for fact in facts]
    assert [payload["factType"] for payload in payloads] == [
        "sale_price_index_change_pct",
        "jeonse_price_index_change_pct",
        "apartment_trade_volume",
    ]
    assert payloads[0]["provider"] == "reb"
    assert payloads[0]["providerDataset"] == "reb_rone_main_snapshot"
    assert payloads[0]["legalDongCode"] == "00000"
    assert payloads[0]["observedAt"] == "2026-05-01"
    assert payloads[0]["asOf"] == "2026-05-01"
    assert payloads[0]["valueJson"]["regionName"] == "전국"
    assert payloads[0]["valueJson"]["value"] == 0.25
    assert payloads[0]["valueJson"]["unit"] == "%"
    assert payloads[2]["observedAt"] == "2026-04-01"
    assert payloads[2]["valueJson"]["value"] == 53177
    assert payloads[2]["valueJson"]["unit"] == "호수"


def test_reb_rone_main_snapshot_client_fetches_public_page_with_same_clock():
    calls = []

    def fetcher(url):
        calls.append(url)
        return """
        doEvent.changeMajorStat('A_2024_00045', 'MM', '매매가격지수 변동률', 'PR', '%', '아파트', '2026년 5월', '0.25', '전국주택가격동향조사')
        """

    client = RebRoneMainSnapshotClient(fetcher=fetcher)

    facts = collect_reb_rone_main_snapshot_facts(
        client,
        now=datetime(2026, 6, 15, 1, 5, tzinfo=timezone.utc),
    )

    assert calls == ["https://www.reb.or.kr/r-one/portal/main/indexPage.do"]
    assert len(facts) == 1
    assert facts[0].to_ingestion_dict()["ingestedAt"] == "2026-06-15T01:05:00Z"


def test_reb_rone_regional_map_parser_normalizes_price_change_rows():
    json_text = """
    {
      "data": [
        {
          "statblId": "A_2024_00045",
          "datano": 500001,
          "viewItmNm": "전국",
          "geoCd": "10",
          "uiNm": "%",
          "wrttimeIdtfrId": "202605",
          "dtaVal": 0.25,
          "pdDtaVal": 0.25,
          "odRnk": 0
        },
        {
          "statblId": "A_2024_00045",
          "datano": 500008,
          "viewItmNm": "서울",
          "geoCd": "11",
          "uiNm": "%",
          "wrttimeIdtfrId": "202605",
          "dtaVal": 1.06,
          "pdDtaVal": 1.08,
          "odRnk": 1
        },
        {
          "statblId": "A_2024_00045",
          "datano": 500009,
          "viewItmNm": "경기",
          "geoCd": "41",
          "uiNm": "%",
          "wrttimeIdtfrId": "202605",
          "dtaVal": 0.41,
          "pdDtaVal": 0.42,
          "odRnk": 2
        },
        {
          "statblId": "A_2024_00045",
          "datano": 500123,
          "viewItmNm": "마포구",
          "geoCd": "11440",
          "uiNm": "%",
          "wrttimeIdtfrId": "202605",
          "dtaVal": 0.33,
          "pdDtaVal": 0.35,
          "odRnk": 8
        }
      ]
    }
    """

    facts = parse_reb_rone_regional_map(
        json_text,
        ingested_at=datetime(2026, 6, 15, 2, 0, tzinfo=timezone.utc),
    )

    payloads = [fact.to_ingestion_dict() for fact in facts]
    assert [payload["factType"] for payload in payloads] == [
        "sale_price_index_change_pct",
        "sale_price_index_change_pct",
        "sale_price_index_change_pct",
        "sale_price_index_change_pct",
    ]
    assert payloads[0]["targetId"] is None
    assert payloads[0]["legalDongCode"] == "00000"
    assert payloads[0]["valueJson"]["regionName"] == "전국"
    assert payloads[1]["targetId"] == "region-seoul"
    assert payloads[1]["legalDongCode"] == "11"
    assert payloads[1]["observedAt"] == "2026-05-01"
    assert payloads[1]["valueJson"]["value"] == 1.06
    assert payloads[1]["valueJson"]["sourceLabel"] == "한국부동산원 R-ONE 전국주택가격동향조사 매매가격지수 변동률"
    assert payloads[2]["targetId"] == "region-gyeonggi"
    assert payloads[2]["legalDongCode"] == "41"
    assert payloads[2]["valueJson"]["topologyRegionCode"] == "31"
    assert payloads[3]["targetId"] is None
    assert payloads[3]["legalDongCode"] == "11440"


def test_reb_rone_regional_map_client_uses_selected_geo_code_with_same_clock():
    calls = []

    def fetcher(url, params):
        calls.append((url, dict(params)))
        return """
        {
          "data": [
            {
              "statblId": "A_2024_00045",
              "datano": 500008,
              "viewItmNm": "서울",
              "geoCd": "11",
              "uiNm": "%",
              "wrttimeIdtfrId": "202605",
              "dtaVal": 1.06,
              "pdDtaVal": 1.08,
              "odRnk": 1
            }
          ]
        }
        """

    client = RebRoneRegionalMapClient(fetcher=fetcher)

    facts = collect_reb_rone_regional_map_facts(
        client,
        geo_cd="10",
        now=datetime(2026, 6, 15, 2, 5, tzinfo=timezone.utc),
    )

    assert calls == [
        (
            "https://www.reb.or.kr/r-one/portal/main/searchRegionalStatusMap.do",
            {
                "statblId": "A_2024_00045",
                "dtacycleCd": "MM",
                "itmDatano": "100001",
                "geoCd": "10",
                "dtadvsCd": "PR",
                "itmTag": "C",
                "clsDatano": "",
            },
        )
    ]
    assert len(facts) == 1
    assert facts[0].to_ingestion_dict()["ingestedAt"] == "2026-06-15T02:05:00Z"


def test_reb_rone_monthly_price_index_parser_backfills_changes_and_skips_unmatched_regions():
    regional_map_json = """
    {
      "data": [
        {
          "statblId": "A_2024_00045",
          "viewItmNm": "마포구",
          "geoCd": "11440",
          "uiNm": "%",
          "wrttimeIdtfrId": "202605",
          "dtaVal": 0.86
        },
        {
          "statblId": "A_2024_00045",
          "viewItmNm": "파주시",
          "geoCd": "41480",
          "uiNm": "%",
          "wrttimeIdtfrId": "202605",
          "dtaVal": -0.12
        }
      ]
    }
    """
    monthly_json = """
    {
      "DATA": [
        {
          "CATE1": "서울",
          "CATE2": "강북지역",
          "CATE3": "서북권",
          "CATE4": "마포구",
          "COL_202603100001OD": "101.32",
          "COL_202604100001OD": "101.91",
          "COL_202605100001OD": "102.79"
        },
        {
          "CATE1": "충남",
          "CATE2": "서천군",
          "CATE3": "서천군",
          "CATE4": "서천군",
          "COL_202603100001OD": "99.10",
          "COL_202604100001OD": "99.00",
          "COL_202605100001OD": "98.80"
        }
      ]
    }
    """
    lookup = build_reb_rone_region_lookup_from_regional_map_json(regional_map_json)

    facts = parse_reb_rone_monthly_price_index_changes(
        monthly_json,
        ingested_at=datetime(2026, 6, 16, 1, 0, tzinfo=timezone.utc),
        region_lookup=lookup,
    )

    payloads = [fact.to_ingestion_dict() for fact in facts]
    assert len(payloads) == 2
    assert {payload["legalDongCode"] for payload in payloads} == {"11440"}
    assert payloads[0]["providerDataset"] == "reb_rone_monthly_apt_sale_price_index"
    assert payloads[0]["targetId"] is None
    assert payloads[0]["observedAt"] == "2026-04-01"
    assert payloads[0]["valueJson"]["periodYm"] == "202604"
    assert payloads[0]["valueJson"]["previousPeriodYm"] == "202603"
    assert payloads[0]["valueJson"]["value"] == pytest.approx(0.5823)
    assert payloads[1]["observedAt"] == "2026-05-01"
    assert payloads[1]["valueJson"]["value"] == pytest.approx(0.8635)


def test_reb_rone_monthly_price_index_client_fetches_table_and_region_lookup_with_same_clock():
    calls = []
    monthly_json = """
    {
      "DATA": [
        {
          "CATE1": "서울",
          "CATE2": "강북지역",
          "CATE3": "서북권",
          "CATE4": "마포구",
          "COL_202604100001OD": "101.91",
          "COL_202605100001OD": "102.79"
        }
      ]
    }
    """
    regional_map_json = """
    {
      "data": [
        {
          "statblId": "A_2024_00045",
          "viewItmNm": "마포구",
          "geoCd": "11440",
          "uiNm": "%",
          "wrttimeIdtfrId": "202605",
          "dtaVal": 0.86
        }
      ]
    }
    """

    def fetcher(url, latest_months):
        calls.append((url, latest_months))
        return monthly_json, regional_map_json

    client = RebRoneMonthlyAptSalePriceIndexClient(fetcher=fetcher, latest_months=6)

    facts = collect_reb_rone_monthly_price_index_change_facts(
        client,
        now=datetime(2026, 6, 16, 1, 5, tzinfo=timezone.utc),
    )

    assert calls == [("https://www.reb.or.kr/r-one/portal/stat/easyStatPage/A_2024_00045.do", 6)]
    assert len(facts) == 1
    payload = facts[0].to_ingestion_dict()
    assert payload["ingestedAt"] == "2026-06-16T01:05:00Z"
    assert payload["legalDongCode"] == "11440"
    assert payload["valueJson"]["sourceLabel"] == "한국부동산원 R-ONE 월간 아파트 매매가격지수"


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
