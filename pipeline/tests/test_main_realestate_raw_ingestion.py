import asyncio
import json
import sys
from datetime import date, datetime, timezone

from youbuyfirst_pipeline import main as pipeline_main
from youbuyfirst_pipeline.realestate_public_data import PublicDataProviderError, RealEstateMarketFact


class _FakeMolitClient:
    def __init__(self) -> None:
        self.trade_calls = []
        self.rent_calls = []

    def fetch_apt_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        self.trade_calls.append((lawd_code, deal_ym))
        return [
            RealEstateMarketFact(
                fact_type="apt_trade",
                provider="molit",
                provider_dataset="molit_apt_trade",
                provider_object_id=f"molit_apt_trade:{lawd_code}:{deal_ym}:raw-1",
                legal_dong_code=lawd_code,
                observed_at=date(2026, 6, 3),
                as_of=date(2026, 6, 1),
                ingested_at=now or datetime(2026, 6, 12, tzinfo=timezone.utc),
                value_json={
                    "apartmentName": "Sajik Palace",
                    "dealAmountManwon": 82500,
                    "raw": {"aptNm": "Sajik Palace", "dealAmount": "82,500"},
                },
            )
        ]

    def fetch_apt_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        self.rent_calls.append((lawd_code, deal_ym))
        return []


class _FakeSpringClient:
    def __init__(self) -> None:
        self.raw_ingestions = []
        self.market_facts = []
        self.promote_requests = []
        self.market_data_targets = []
        self.import_runs = []
        self.targets = []
        self.complexes = []
        self.aliases = []
        self.target_edges = []
        self.regions = []

    def publish_real_estate_market_facts(self, facts) -> None:
        self.market_facts.extend(fact.to_ingestion_dict() for fact in facts)

    def publish_real_estate_public_data_raw_ingestion(self, ingestion) -> None:
        self.raw_ingestions.append(ingestion.to_request_dict())

    def publish_real_estate_targets(self, targets) -> None:
        self.targets.extend(targets)

    def publish_real_estate_complexes(self, complexes) -> None:
        self.complexes.extend(complexes)

    def publish_real_estate_aliases(self, aliases) -> None:
        self.aliases.extend(aliases)

    def publish_real_estate_target_edges(self, edges) -> None:
        self.target_edges.extend(edges)

    def promote_real_estate_public_data_staging(
        self,
        *,
        provider_dataset=None,
        run_key=None,
        validation_status="valid",
        limit=1000,
    ):
        self.promote_requests.append(
            {
                "provider_dataset": provider_dataset,
                "run_key": run_key,
                "validation_status": validation_status,
                "limit": limit,
            }
        )
        return {"promotedFacts": 1}

    def list_real_estate_market_data_targets(self, enabled=True):
        return self.market_data_targets

    def list_real_estate_regions(self, *, region_level=None, limit=500):
        if region_level is None:
            return self.regions
        return [region for region in self.regions if region.get("regionLevel") == region_level]

    def list_real_estate_public_data_import_runs(
        self,
        *,
        run_keys=None,
        provider_dataset=None,
        status=None,
        limit=100,
    ):
        return [
            run
            for run in self.import_runs
            if (not run_keys or run.get("runKey") in run_keys)
            and (provider_dataset is None or run.get("providerDataset") == provider_dataset)
            and (status is None or run.get("status") == status)
        ][:limit]


def test_realestate_market_facts_raw_push_command_publishes_raw_ingestion(monkeypatch):
    fake_client = _FakeSpringClient()
    provider = _FakeMolitClient()
    monkeypatch.setattr(pipeline_main, "build_molit_public_data_client_from_env", lambda: provider)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-code",
            "11110",
            "--realestate-deal-ym",
            "202606",
            "--realestate-datasets",
            "trade",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert len(fake_client.raw_ingestions) == 1
    payload = fake_client.raw_ingestions[0]
    assert payload["run"]["runKey"] == "molit_apt_trade:11110:202606"
    assert payload["items"][0]["providerObjectId"] == "molit_apt_trade:11110:202606:raw-1"
    assert payload["items"][0]["staging"]["factType"] == "apt_trade"


def test_reb_rone_main_snapshot_push_command_publishes_market_facts(monkeypatch):
    fake_client = _FakeSpringClient()
    fixed_fact = RealEstateMarketFact(
        fact_type="sale_price_index_change_pct",
        provider="reb",
        provider_dataset="reb_rone_main_snapshot",
        provider_object_id="reb_rone_main_snapshot:A_2024_00045:202605",
        legal_dong_code="00000",
        observed_at=date(2026, 5, 1),
        as_of=date(2026, 5, 1),
        ingested_at=datetime(2026, 6, 15, 1, 0, tzinfo=timezone.utc),
        value_json={"regionName": "전국", "metricName": "매매가격지수 변동률", "value": 0.25, "unit": "%"},
    )
    monkeypatch.setattr(pipeline_main, "build_reb_rone_main_snapshot_client_from_env", lambda: object())
    monkeypatch.setattr(pipeline_main, "collect_reb_rone_main_snapshot_facts", lambda _provider: [fixed_fact])
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-reb-rone-main-snapshot-push",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert len(fake_client.market_facts) == 1
    assert fake_client.market_facts[0]["factType"] == "sale_price_index_change_pct"
    assert fake_client.market_facts[0]["providerDataset"] == "reb_rone_main_snapshot"


def test_realestate_market_facts_raw_push_command_backfills_multiple_lawd_codes_and_months(monkeypatch):
    fake_client = _FakeSpringClient()
    provider = _FakeMolitClient()
    monkeypatch.setattr(pipeline_main, "build_molit_public_data_client_from_env", lambda: provider)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-codes",
            "11110",
            "11680",
            "--realestate-start-ym",
            "202605",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert provider.trade_calls == [
        ("11110", "202605"),
        ("11680", "202605"),
        ("11110", "202606"),
        ("11680", "202606"),
    ]
    assert [payload["run"]["runKey"] for payload in fake_client.raw_ingestions] == [
        "molit_apt_trade:11110:202605",
        "molit_apt_trade:11680:202605",
        "molit_apt_trade:11110:202606",
        "molit_apt_trade:11680:202606",
    ]


def test_realestate_market_facts_raw_push_can_backfill_backend_market_data_targets(monkeypatch):
    fake_client = _FakeSpringClient()
    fake_client.market_data_targets = [
        {
            "targetId": "region-11110",
            "provider": "molit",
            "providerDataset": "molit_apt_trade",
            "lawdCode": "11110",
            "enabled": True,
        },
        {
            "targetId": "region-11110",
            "provider": "molit",
            "providerDataset": "molit_apt_rent",
            "lawdCode": "11110",
            "enabled": True,
        },
    ]
    provider = _FakeMolitClient()
    monkeypatch.setattr(pipeline_main, "build_molit_public_data_client_from_env", lambda: provider)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-use-backend-targets",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert provider.trade_calls == [("11110", "202606")]
    assert provider.rent_calls == [("11110", "202606")]
    assert [payload["run"]["runKey"] for payload in fake_client.raw_ingestions] == [
        "molit_apt_trade:11110:202606",
        "molit_apt_rent:11110:202606",
    ]


def test_realestate_market_facts_raw_push_can_promote_each_backfill_run(monkeypatch):
    fake_client = _FakeSpringClient()
    provider = _FakeMolitClient()
    monkeypatch.setattr(pipeline_main, "build_molit_public_data_client_from_env", lambda: provider)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-codes",
            "11110",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "--realestate-promote-after-raw-push",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert [payload["run"]["runKey"] for payload in fake_client.raw_ingestions] == [
        "molit_apt_trade:11110:202606",
    ]
    assert fake_client.promote_requests == [
        {
            "provider_dataset": "molit_apt_trade",
            "run_key": "molit_apt_trade:11110:202606",
            "validation_status": "valid",
            "limit": 1000,
        }
    ]


def test_realestate_market_facts_raw_push_prints_execution_manifest(monkeypatch, capsys):
    fake_client = _FakeSpringClient()
    provider = _FakeMolitClient()
    monkeypatch.setattr(pipeline_main, "build_molit_public_data_client_from_env", lambda: provider)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-codes",
            "11110",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "rent",
            "--realestate-promote-after-raw-push",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "taskCount": 2,
        "publishedRuns": 2,
        "publishedItems": 1,
        "emptyRuns": 1,
        "failedRuns": 0,
        "promotedRuns": 2,
        "items": [
            {
                "runKey": "molit_apt_trade:11110:202606",
                "providerDataset": "molit_apt_trade",
                "lawdCode": "11110",
                "dealYm": "202606",
                "fetchedFacts": 1,
                "rawItems": 1,
                "empty": False,
                "status": "completed",
                "providerError": None,
                "promoted": True,
                "promotedFacts": 1,
            },
            {
                "runKey": "molit_apt_rent:11110:202606",
                "providerDataset": "molit_apt_rent",
                "lawdCode": "11110",
                "dealYm": "202606",
                "fetchedFacts": 0,
                "rawItems": 0,
                "empty": True,
                "status": "completed",
                "providerError": None,
                "promoted": True,
                "promotedFacts": 1,
            },
        ],
    }


def test_realestate_market_facts_raw_push_records_empty_provider_result(monkeypatch):
    fake_client = _FakeSpringClient()
    provider = _FakeMolitClient()
    monkeypatch.setattr(pipeline_main, "build_molit_public_data_client_from_env", lambda: provider)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-code",
            "11680",
            "--realestate-deal-ym",
            "202605",
            "--realestate-datasets",
            "rent",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert provider.rent_calls == [("11680", "202605")]
    assert len(fake_client.raw_ingestions) == 1
    payload = fake_client.raw_ingestions[0]
    assert payload["run"]["runKey"] == "molit_apt_rent:11680:202605"
    assert payload["run"]["status"] == "completed"
    assert payload["items"] == []


def test_realestate_market_facts_raw_push_records_provider_error_and_continues(monkeypatch, capsys):
    class PartiallyFailingMolitClient(_FakeMolitClient):
        def fetch_apt_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
            self.trade_calls.append((lawd_code, deal_ym))
            if lawd_code == "11110":
                raise PublicDataProviderError("MOLIT public data request failed: endpoint status=502")
            return super().fetch_apt_trades(lawd_code, deal_ym, page_no, num_rows, now)

    fake_client = _FakeSpringClient()
    provider = PartiallyFailingMolitClient()
    monkeypatch.setattr(pipeline_main, "build_molit_public_data_client_from_env", lambda: provider)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-codes",
            "11110",
            "11680",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "--realestate-promote-after-raw-push",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["publishedRuns"] == 2
    assert payload["failedRuns"] == 1
    assert payload["promotedRuns"] == 1
    assert [item["status"] for item in payload["items"]] == ["provider_error", "completed"]
    assert "status=502" in payload["items"][0]["providerError"]
    assert fake_client.raw_ingestions[0]["run"]["status"] == "provider_error"
    assert "status=502" in fake_client.raw_ingestions[0]["run"]["errorMessage"]
    assert fake_client.raw_ingestions[1]["run"]["status"] == "completed"
    assert fake_client.promote_requests == [
        {
            "provider_dataset": "molit_apt_trade",
            "run_key": "molit_apt_trade:11680:202606",
            "validation_status": "valid",
            "limit": 1000,
        }
    ]


def test_realestate_market_facts_raw_push_accepts_public_data_pagination_options(monkeypatch, capsys):
    class PaginatedMolitClient:
        def __init__(self) -> None:
            self.trade_calls = []

        def fetch_apt_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
            self.trade_calls.append((lawd_code, deal_ym, page_no, num_rows))
            if page_no == 1:
                suffixes = ["raw-1", "raw-2"]
            elif page_no == 2:
                suffixes = ["raw-3"]
            else:
                suffixes = []
            return [
                RealEstateMarketFact(
                    fact_type="apt_trade",
                    provider="molit",
                    provider_dataset="molit_apt_trade",
                    provider_object_id=f"molit_apt_trade:{lawd_code}:{deal_ym}:{suffix}",
                    legal_dong_code=lawd_code,
                    observed_at=date(2026, 6, 3),
                    as_of=date(2026, 6, 1),
                    ingested_at=now or datetime(2026, 6, 12, tzinfo=timezone.utc),
                    value_json={
                        "apartmentName": "Sajik Palace",
                        "dealAmountManwon": 82500,
                        "raw": {"aptNm": "Sajik Palace", "dealAmount": "82,500"},
                    },
                )
                for suffix in suffixes
            ]

        def fetch_apt_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
            raise AssertionError("rent dataset was not requested")

    fake_client = _FakeSpringClient()
    provider = PaginatedMolitClient()
    monkeypatch.setattr(pipeline_main, "build_molit_public_data_client_from_env", lambda: provider)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-code",
            "11110",
            "--realestate-deal-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "--realestate-public-data-page-size",
            "2",
            "--realestate-public-data-max-pages",
            "5",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert provider.trade_calls == [
        ("11110", "202606", 1, 2),
        ("11110", "202606", 2, 2),
    ]
    assert payload["publishedItems"] == 3
    assert payload["items"][0]["fetchedFacts"] == 3


def test_realestate_market_facts_raw_push_skips_completed_runs_before_building_provider(monkeypatch, capsys):
    fake_client = _FakeSpringClient()
    fake_client.import_runs = [
        {
            "runKey": "molit_apt_trade:11110:202606",
            "providerDataset": "molit_apt_trade",
            "status": "completed",
        }
    ]
    monkeypatch.setattr(
        pipeline_main,
        "build_molit_public_data_client_from_env",
        lambda: (_ for _ in ()).throw(AssertionError("provider should not be built")),
    )
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-code",
            "11110",
            "--realestate-deal-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "--realestate-skip-completed-runs",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "plannedRuns": 1,
        "skippedCompletedRuns": ["molit_apt_trade:11110:202606"],
        "taskCount": 0,
        "publishedRuns": 0,
        "publishedItems": 0,
        "emptyRuns": 0,
        "failedRuns": 0,
        "promotedRuns": 0,
        "items": [],
    }
    assert fake_client.raw_ingestions == []


def test_realestate_market_facts_promote_staging_command_calls_backend(monkeypatch, capsys):
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-promote-staging",
            "--realestate-provider-dataset",
            "molit_apt_rent",
            "--realestate-run-key",
            "molit_apt_rent:11110:202606",
            "--realestate-validation-status",
            "valid",
            "--realestate-promote-limit",
            "10",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert fake_client.promote_requests == [
        {
            "provider_dataset": "molit_apt_rent",
            "run_key": "molit_apt_rent:11110:202606",
            "validation_status": "valid",
            "limit": 10,
        }
    ]
    assert '"promotedFacts": 1' in capsys.readouterr().out


def test_realestate_complex_registry_push_builds_complex_aliases_and_edges_from_market_facts(monkeypatch, tmp_path):
    market_facts_path = tmp_path / "market-facts.jsonl"
    market_facts_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "factType": "apt_trade",
                        "legalDongCode": "11110",
                        "valueJson": {
                            "apartmentName": "Sajik Palace",
                            "legalDongName": "Sajik-dong",
                            "jibun": "1-1",
                            "builtYear": 2015,
                        },
                    }
                ),
                json.dumps(
                    {
                        "factType": "apt_rent",
                        "legalDongCode": "11110",
                        "valueJson": {
                            "apartmentName": "Sajik Palace",
                            "legalDongName": "Sajik-dong",
                            "jibun": "1-1",
                            "depositAmountManwon": 45000,
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    fake_client = _FakeSpringClient()
    fake_client.market_data_targets = [
        {
            "targetId": "region-seoul-jongno",
            "provider": "molit",
            "providerDataset": "molit_apt_trade",
            "lawdCode": "11110",
            "enabled": True,
        }
    ]
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-complex-registry-push",
            "--realestate-market-facts-jsonl",
            str(market_facts_path),
            "--realestate-use-backend-targets",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert len(fake_client.targets) == 1
    assert fake_client.targets[0]["targetType"] == "complex"
    assert fake_client.complexes == [
        {
            "targetId": fake_client.targets[0]["targetId"],
            "regionTargetId": "region-seoul-jongno",
            "legalDongCode": "11110",
            "roadAddress": None,
            "jibunAddress": "Sajik-dong 1-1",
            "normalizedAddress": "11110Sajikdong11SajikPalace",
            "builtYear": 2015,
            "householdCount": None,
            "source": "molit:market-fact",
            "markerDataStatus": "partial",
            "markerStale": True,
        }
    ]
    assert [alias["alias"] for alias in fake_client.aliases] == [
        "Sajik Palace",
        "Sajik-dong Sajik Palace",
    ]
    assert fake_client.target_edges == [
        {
            "fromTargetType": "region",
            "fromTargetId": "region-seoul-jongno",
            "toTargetType": "complex",
            "toTargetId": fake_client.targets[0]["targetId"],
            "edgeType": "contains",
            "confidence": 0.74,
            "source": "molit:market-fact",
            "reviewState": "approved",
        }
    ]


def test_realestate_complex_registry_push_links_complex_to_eupmyeondong_region(monkeypatch, tmp_path):
    market_facts_path = tmp_path / "market-facts.jsonl"
    market_facts_path.write_text(
        json.dumps(
            {
                "factType": "apt_trade",
                "legalDongCode": "11440",
                "valueJson": {
                    "apartmentName": "마포 래미안 푸르지오",
                    "legalDongName": "아현동",
                    "jibun": "777",
                },
            }
        ),
        encoding="utf-8",
    )
    fake_client = _FakeSpringClient()
    fake_client.market_data_targets = [
        {
            "targetId": "region-seoul-mapo",
            "provider": "molit",
            "providerDataset": "molit_apt_trade",
            "lawdCode": "11440",
            "enabled": True,
        }
    ]
    fake_client.regions = [
        {
            "targetId": "region-1144010100",
            "targetType": "region",
            "displayName": "서울특별시 마포구 아현동",
            "regionLevel": "eupmyeondong",
            "parentTargetId": "region-seoul-mapo",
            "legalDongCode": "1144010100",
            "regionCode": "1144010100",
        }
    ]
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-complex-registry-push",
            "--realestate-market-facts-jsonl",
            str(market_facts_path),
            "--realestate-use-backend-targets",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert fake_client.complexes[0]["regionTargetId"] == "region-1144010100"
    assert fake_client.target_edges[0]["fromTargetId"] == "region-1144010100"


def test_realestate_official_apartment_prices_raw_push_streams_csv_batches(monkeypatch, tmp_path):
    csv_path = tmp_path / "official-prices.csv"
    csv_path.write_text(
        """시도,시군구,시군구코드,법정동코드,동리,번,지,단지명,동명,호명,전용면적(㎡),공동주택가격(원),공시기준일,관리건축물대장PK
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1201호,84.97,"825,000,000",2025-01-01,11680-3633202
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1202호,84.97,"826,000,000",2025-01-01,11680-3633203
""",
        encoding="utf-8",
    )
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-official-apartment-prices-raw-push",
            "--realestate-official-apartment-price-csv",
            str(csv_path),
            "--realestate-official-apartment-price-base-date",
            "2025-01-01",
            "--realestate-official-apartment-price-batch-size",
            "1",
            "--realestate-promote-after-raw-push",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert [payload["run"]["runKey"] for payload in fake_client.raw_ingestions] == [
        "molit_official_apartment_price_csv:20250101:000001",
        "molit_official_apartment_price_csv:20250101:000002",
    ]
    assert fake_client.raw_ingestions[0]["run"]["requestParams"] == {
        "baseDate": "2025-01-01",
        "batchIndex": "000001",
        "sourceLabel": str(csv_path),
    }
    assert fake_client.raw_ingestions[0]["items"][0]["staging"]["factType"] == "official_apartment_price"
    assert fake_client.raw_ingestions[0]["items"][0]["staging"]["valueJson"]["officialPriceWon"] == 825000000
    assert fake_client.promote_requests == [
        {
            "provider_dataset": "molit_official_apartment_price_csv",
            "run_key": "molit_official_apartment_price_csv:20250101:000001",
            "validation_status": "valid",
            "limit": 1000,
        },
        {
            "provider_dataset": "molit_official_apartment_price_csv",
            "run_key": "molit_official_apartment_price_csv:20250101:000002",
            "validation_status": "valid",
            "limit": 1000,
        },
    ]


def test_realestate_official_apartment_prices_inspect_command_prints_manifest(monkeypatch, tmp_path, capsys):
    csv_path = tmp_path / "official-prices.csv"
    csv_path.write_text(
        """시도,시군구,시군구코드,법정동코드,동리,번,지,단지명,동명,호명,전용면적(㎡),공동주택가격(원),공시기준일,관리건축물대장PK
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1201호,84.97,"825,000,000",2025-01-01,11680-3633202
서울특별시,강남구,11680,10300,개포동,12,0,대치아파트,216동,1202호,84.97,"826,000,000",2025-01-01,11680-3633203
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-official-apartment-prices-inspect",
            "--realestate-official-apartment-price-csv",
            str(csv_path),
            "--realestate-official-apartment-price-base-date",
            "2025-01-01",
            "--realestate-official-apartment-price-batch-size",
            "1",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["providerDataset"] == "molit_official_apartment_price_csv"
    assert payload["totalRows"] == 2
    assert payload["validRows"] == 2
    assert payload["batchCount"] == 2
    assert payload["firstRunKey"] == "molit_official_apartment_price_csv:20250101:000001"
    assert payload["lastRunKey"] == "molit_official_apartment_price_csv:20250101:000002"


def test_realestate_regional_stat_csv_raw_push_streams_batches(monkeypatch, tmp_path):
    csv_path = tmp_path / "molit-unsold.csv"
    csv_path.write_text(
        """기준월,지역코드,지역명,항목,값,단위
202604,11680,서울 강남구,준공후 미분양,17,호
202604,11710,서울 송파구,준공후 미분양,22,호
""",
        encoding="utf-8",
    )
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-regional-stat-csv-raw-push",
            "--realestate-stat-csv",
            str(csv_path),
            "--realestate-provider",
            "molit_stat",
            "--realestate-provider-dataset",
            "molit_unsold_housing_stat",
            "--realestate-fact-type",
            "unsold_housing",
            "--realestate-stat-batch-size",
            "1",
            "--realestate-promote-after-raw-push",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert [payload["run"]["runKey"] for payload in fake_client.raw_ingestions] == [
        "molit_unsold_housing_stat:20260401:000001",
        "molit_unsold_housing_stat:20260401:000002",
    ]
    assert fake_client.raw_ingestions[0]["items"][0]["staging"]["factType"] == "unsold_housing"
    assert fake_client.raw_ingestions[0]["items"][0]["staging"]["valueJson"]["value"] == 17
    assert fake_client.promote_requests == [
        {
            "provider_dataset": "molit_unsold_housing_stat",
            "run_key": "molit_unsold_housing_stat:20260401:000001",
            "validation_status": "valid",
            "limit": 1000,
        },
        {
            "provider_dataset": "molit_unsold_housing_stat",
            "run_key": "molit_unsold_housing_stat:20260401:000002",
            "validation_status": "valid",
            "limit": 1000,
        },
    ]
