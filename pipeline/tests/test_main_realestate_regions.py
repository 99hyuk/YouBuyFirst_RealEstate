import asyncio
import json
import sys
from pathlib import Path

from youbuyfirst_pipeline import main as pipeline_main

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "realestate"


class _FakeSpringClient:
    def __init__(self) -> None:
        self.region_batches = []
        self.alias_batches = []
        self.regions = []

    def publish_real_estate_regions(self, regions) -> None:
        self.region_batches.append([region.to_import_dict() for region in regions])

    def list_real_estate_regions(self, *, region_level=None, limit=500):
        if region_level is None:
            return self.regions
        return [
            region
            for region in self.regions
            if region.get("regionLevel") == region_level
        ]

    def publish_real_estate_aliases(self, aliases) -> None:
        self.alias_batches.append(list(aliases))


def test_realestate_regions_import_command_reads_csv_and_publishes(monkeypatch, tmp_path):
    csv_path = tmp_path / "legal-dong.csv"
    csv_path.write_text(
        "\n".join([
            "법정동코드,법정동명,폐지여부",
            "2600000000,부산광역시,존재",
            "2635000000,부산광역시 해운대구,존재",
        ]),
        encoding="utf-8",
    )
    fake_client = _FakeSpringClient()

    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-regions-import",
            "--legal-dong-code-csv",
            str(csv_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert fake_client.region_batches == [
        [
            {
                "targetId": "region-26000",
                "displayName": "부산광역시",
                "slug": "region-26000",
                "regionLevel": "sido",
                "parentTargetId": None,
                "legalDongCode": "26000",
                "regionCode": "26",
                "source": "import:molit-legal-dong-code",
            },
            {
                "targetId": "region-26350",
                "displayName": "부산광역시 해운대구",
                "slug": "region-26350",
                "regionLevel": "sigungu",
                "parentTargetId": "region-26000",
                "legalDongCode": "26350",
                "regionCode": "26350",
                "source": "import:molit-legal-dong-code",
            },
        ]
    ]


def test_realestate_region_aliases_push_command_reads_backend_regions_and_publishes(monkeypatch, capsys):
    fake_client = _FakeSpringClient()
    fake_client.regions = [
        {
            "targetId": "region-gyeonggi-paju",
            "displayName": "경기도 파주시",
            "regionLevel": "sigungu",
        },
        {
            "targetId": "region-seoul-jung",
            "displayName": "서울특별시 중구",
            "regionLevel": "sigungu",
        },
        {
            "targetId": "region-busan-jung",
            "displayName": "부산광역시 중구",
            "regionLevel": "sigungu",
        },
    ]

    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-region-aliases-push",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    aliases = {
        (alias["targetId"], alias["alias"]): alias
        for alias in fake_client.alias_batches[0]
    }
    assert payload["regionCount"] == 3
    assert payload["publishedAliases"] == len(fake_client.alias_batches[0])
    assert aliases[("region-gyeonggi-paju", "파주시")]["reviewState"] == "approved"
    assert aliases[("region-gyeonggi-paju", "파주")]["reviewState"] == "approved"
    assert aliases[("region-seoul-jung", "중구")]["reviewState"] == "candidate"
    assert aliases[("region-busan-jung", "중구")]["ambiguous"] is True
    assert aliases[("region-seoul-jung", "서울 중구")]["reviewState"] == "approved"


def test_realestate_regions_inspect_command_writes_backfill_manifest(monkeypatch, capsys, tmp_path):
    csv_path = FIXTURE_DIR / "molit_legal_dong_codes_sample.csv"
    manifest_path = tmp_path / "molit-region-plan.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-regions-inspect",
            "--legal-dong-code-csv",
            str(csv_path),
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "rent",
            "--realestate-backfill-plan-output",
            str(manifest_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["regionCount"] == 3
    assert payload["regionLevelCounts"] == {"sido": 1, "sigungu": 1, "eupmyeondong": 1}
    assert payload["marketDataTargetCount"] == 2
    assert payload["backfillPlan"] == {
        "plannedRuns": 2,
        "period": {"startYm": "202606", "endYm": "202606"},
        "datasets": ["molit_apt_trade", "molit_apt_rent"],
        "lawdCodes": ["26350"],
    }
    assert [item["runKey"] for item in file_payload["items"]] == [
        "molit_apt_trade:26350:202606",
        "molit_apt_rent:26350:202606",
    ]
    assert payload["sampleMarketDataTargets"] == [
        {
            "targetId": "region-26350",
            "provider": "molit",
            "providerDataset": "molit_apt_trade",
            "lawdCode": "26350",
            "enabled": True,
            "refreshIntervalHours": 24,
            "staleAfterHours": 72,
        },
        {
            "targetId": "region-26350",
            "provider": "molit",
            "providerDataset": "molit_apt_rent",
            "lawdCode": "26350",
            "enabled": True,
            "refreshIntervalHours": 24,
            "staleAfterHours": 72,
        },
    ]
