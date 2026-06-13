import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakeSpringClient:
    def __init__(self) -> None:
        self.import_run_requests = []

    def list_real_estate_market_data_targets(self, enabled=True):
        return [
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

    def list_real_estate_public_data_import_runs(
        self,
        *,
        run_keys=None,
        provider_dataset=None,
        status=None,
        limit=100,
    ):
        self.import_run_requests.append(
            {
                "run_keys": run_keys,
                "provider_dataset": provider_dataset,
                "status": status,
                "limit": limit,
            }
        )
        if "molit_apt_trade:11110:202606" in (run_keys or []) and status == "completed":
            return [
                {
                    "runKey": "molit_apt_trade:11110:202606",
                    "providerDataset": "molit_apt_trade",
                    "status": "completed",
                }
            ]
        return []

    def publish_real_estate_public_data_raw_ingestion(self, _ingestion):
        raise AssertionError("raw ingestion should not be published before large-run confirmation")

    def promote_real_estate_public_data_staging(self, **_kwargs):
        raise AssertionError("staging should not be promoted before large-run confirmation")


def test_realestate_market_facts_backfill_plan_command_prints_tasks(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-backfill-plan",
            "--realestate-lawd-codes",
            "11110",
            "26000",
            "--realestate-start-ym",
            "202601",
            "--realestate-end-ym",
            "202601",
            "--realestate-datasets",
            "trade",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)

    assert payload == {
        "items": [
            {
                "runKey": "molit_apt_trade:11110:202601",
                "provider": "molit",
                "providerDataset": "molit_apt_trade",
                "factType": "apt_trade",
                "lawdCode": "11110",
                "dealYm": "202601",
                "requestedFrom": "2026-01-01",
                "requestedTo": "2026-01-31",
                "requestParams": {
                    "LAWD_CD": "11110",
                    "DEAL_YMD": "202601",
                },
            },
            {
                "runKey": "molit_apt_trade:26000:202601",
                "provider": "molit",
                "providerDataset": "molit_apt_trade",
                "factType": "apt_trade",
                "lawdCode": "26000",
                "dealYm": "202601",
                "requestedFrom": "2026-01-01",
                "requestedTo": "2026-01-31",
                "requestParams": {
                    "LAWD_CD": "26000",
                    "DEAL_YMD": "202601",
                },
            },
        ]
    }


def test_realestate_market_facts_backfill_plan_command_can_use_backend_targets(monkeypatch, capsys):
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-backfill-plan",
            "--realestate-use-backend-targets",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)

    assert [item["runKey"] for item in payload["items"]] == [
        "molit_apt_trade:11110:202606",
        "molit_apt_rent:11110:202606",
    ]


def test_realestate_market_facts_backfill_plan_command_can_skip_completed_runs(monkeypatch, capsys):
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-backfill-plan",
            "--realestate-use-backend-targets",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-skip-completed-runs",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)

    assert payload["plannedRuns"] == 2
    assert payload["remainingRuns"] == 1
    assert payload["skippedCompletedRuns"] == ["molit_apt_trade:11110:202606"]
    assert [item["runKey"] for item in payload["items"]] == [
        "molit_apt_rent:11110:202606",
    ]
    assert fake_client.import_run_requests == [
        {
            "run_keys": [
                "molit_apt_trade:11110:202606",
                "molit_apt_rent:11110:202606",
            ],
            "provider_dataset": None,
            "status": "completed",
            "limit": 100,
        },
    ]


def test_realestate_market_facts_backfill_plan_command_can_limit_selected_runs(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-backfill-plan",
            "--realestate-lawd-codes",
            "11110",
            "26000",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "rent",
            "--realestate-run-limit",
            "2",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)

    assert payload["plannedRuns"] == 4
    assert payload["remainingRuns"] == 2
    assert payload["omittedByRunLimit"] == 2
    assert payload["runLimit"] == 2
    assert [item["runKey"] for item in payload["items"]] == [
        "molit_apt_trade:11110:202606",
        "molit_apt_rent:11110:202606",
    ]


def test_realestate_market_facts_backfill_plan_command_can_write_manifest(monkeypatch, capsys, tmp_path):
    manifest_path = tmp_path / "molit-plan.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-backfill-plan",
            "--realestate-lawd-codes",
            "11110",
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

    printed_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert printed_payload == file_payload
    assert file_payload["items"][0]["runKey"] == "molit_apt_trade:11110:202606"
    assert file_payload["items"][1]["runKey"] == "molit_apt_rent:11110:202606"


def test_realestate_market_facts_backfill_plan_command_can_print_chunk_manifest(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-backfill-plan",
            "--realestate-lawd-codes",
            "11110",
            "26000",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "rent",
            "--realestate-backfill-chunk-size",
            "3",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)

    assert payload["plannedRuns"] == 4
    assert payload["remainingRuns"] == 4
    assert payload["chunkSize"] == 3
    assert payload["chunkCount"] == 2
    assert [chunk["runCount"] for chunk in payload["chunks"]] == [3, 1]
    assert payload["chunks"][0]["firstRunKey"] == "molit_apt_trade:11110:202606"
    assert payload["chunks"][0]["lastRunKey"] == "molit_apt_trade:26000:202606"
    assert payload["chunks"][1]["items"][0]["runKey"] == "molit_apt_rent:26000:202606"


def test_realestate_public_data_preflight_can_use_backfill_plan_manifest(monkeypatch, capsys, tmp_path):
    manifest_path = tmp_path / "molit-plan.json"
    manifest_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "runKey": "molit_apt_trade:11110:202606",
                        "provider": "molit",
                        "providerDataset": "molit_apt_trade",
                        "factType": "apt_trade",
                        "lawdCode": "11110",
                        "dealYm": "202606",
                        "requestedFrom": "2026-06-01",
                        "requestedTo": "2026-06-30",
                        "requestParams": {
                            "LAWD_CD": "11110",
                            "DEAL_YMD": "202606",
                        },
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("DATA_GO_SERVICE_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-public-data-preflight",
            "--realestate-backfill-plan-json",
            str(manifest_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)

    assert payload["ready"] is False
    assert payload["plannedRuns"] == 1
    assert payload["remainingRuns"] == 1
    assert payload["datasets"] == ["molit_apt_trade"]
    assert payload["lawdCodes"] == ["11110"]
    assert payload["period"] == {"startYm": "202606", "endYm": "202606"}


def test_realestate_market_facts_raw_push_requires_confirmation_for_manifest_large_run(monkeypatch, tmp_path):
    manifest_path = tmp_path / "molit-plan.json"
    manifest_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "runKey": "molit_apt_trade:11110:202606",
                        "provider": "molit",
                        "providerDataset": "molit_apt_trade",
                        "factType": "apt_trade",
                        "lawdCode": "11110",
                        "dealYm": "202606",
                        "requestedFrom": "2026-06-01",
                        "requestedTo": "2026-06-30",
                        "requestParams": {"LAWD_CD": "11110", "DEAL_YMD": "202606"},
                    },
                    {
                        "runKey": "molit_apt_rent:11110:202606",
                        "provider": "molit",
                        "providerDataset": "molit_apt_rent",
                        "factType": "apt_rent",
                        "lawdCode": "11110",
                        "dealYm": "202606",
                        "requestedFrom": "2026-06-01",
                        "requestedTo": "2026-06-30",
                        "requestParams": {"LAWD_CD": "11110", "DEAL_YMD": "202606"},
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATA_GO_SERVICE_KEY", "secret-test-value")
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_molit_public_data_client_from_env",
        lambda: (_ for _ in ()).throw(AssertionError("public data provider should not be created")),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-backfill-plan-json",
            str(manifest_path),
            "--realestate-large-run-threshold",
            "1",
        ],
    )

    try:
        asyncio.run(pipeline_main.async_main())
    except SystemExit as exc:
        assert "selected 2 runs, above threshold 1" in str(exc)
    else:
        raise AssertionError("manifest raw-push should require explicit confirmation")


def test_realestate_public_data_preflight_reports_missing_service_key(monkeypatch, capsys):
    monkeypatch.delenv("DATA_GO_SERVICE_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-public-data-preflight",
            "--realestate-lawd-codes",
            "11110",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "rent",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)

    assert payload == {
        "ready": False,
        "missing": ["DATA_GO_SERVICE_KEY"],
        "checks": {
            "dataGoServiceKey": "missing",
            "backendTargets": "not_required",
            "completedRunSkip": "not_requested",
        },
        "plannedRuns": 2,
        "remainingRuns": 2,
        "skippedCompletedRuns": [],
        "willCallPublicApi": False,
        "promoteAfterRawPush": False,
        "largeRunThreshold": 50,
        "largeRunRequiresConfirmation": False,
        "pageSize": 100,
        "maxPages": 1000,
        "period": {
            "startYm": "202606",
            "endYm": "202606",
        },
        "datasets": ["molit_apt_trade", "molit_apt_rent"],
        "lawdCodes": ["11110"],
    }


def test_realestate_public_data_preflight_omits_secret_and_skips_completed_runs(monkeypatch, capsys):
    fake_client = _FakeSpringClient()
    monkeypatch.setenv("DATA_GO_SERVICE_KEY", "secret-test-value")
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-public-data-preflight",
            "--realestate-use-backend-targets",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-skip-completed-runs",
            "--realestate-promote-after-raw-push",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    captured = capsys.readouterr().out
    payload = json.loads(captured)

    assert "secret-test-value" not in captured
    assert payload["ready"] is True
    assert payload["missing"] == []
    assert payload["checks"] == {
        "dataGoServiceKey": "configured",
        "backendTargets": "used",
        "completedRunSkip": "used",
    }
    assert payload["plannedRuns"] == 2
    assert payload["remainingRuns"] == 1
    assert payload["skippedCompletedRuns"] == ["molit_apt_trade:11110:202606"]
    assert payload["willCallPublicApi"] is True
    assert payload["promoteAfterRawPush"] is True
    assert payload["datasets"] == ["molit_apt_rent"]
    assert payload["lawdCodes"] == ["11110"]


def test_realestate_public_data_preflight_reports_large_run_confirmation_need(monkeypatch, capsys):
    monkeypatch.setenv("DATA_GO_SERVICE_KEY", "secret-test-value")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-public-data-preflight",
            "--realestate-lawd-codes",
            "11110",
            "26000",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "rent",
            "--realestate-large-run-threshold",
            "1",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)

    assert payload["ready"] is True
    assert payload["plannedRuns"] == 4
    assert payload["remainingRuns"] == 4
    assert payload["largeRunThreshold"] == 1
    assert payload["largeRunRequiresConfirmation"] is True


def test_realestate_market_facts_raw_push_requires_confirmation_for_large_selected_runs(monkeypatch):
    monkeypatch.setenv("DATA_GO_SERVICE_KEY", "secret-test-value")
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_molit_public_data_client_from_env",
        lambda: (_ for _ in ()).throw(AssertionError("public data provider should not be created")),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-market-facts-raw-push",
            "--realestate-lawd-codes",
            "11110",
            "26000",
            "--realestate-start-ym",
            "202606",
            "--realestate-end-ym",
            "202606",
            "--realestate-datasets",
            "trade",
            "rent",
            "--realestate-large-run-threshold",
            "1",
        ],
    )

    try:
        asyncio.run(pipeline_main.async_main())
    except SystemExit as exc:
        assert str(exc) == (
            "realestate-market-facts-raw-push selected 4 runs, above threshold 1. "
            "Use --realestate-run-limit for sample runs or --realestate-confirm-large-run to execute all selected runs."
        )
    else:
        raise AssertionError("large raw-push should require explicit confirmation")
