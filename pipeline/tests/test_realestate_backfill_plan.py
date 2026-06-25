import pytest

from youbuyfirst_pipeline.realestate_backfill_plan import (
    build_molit_backfill_plan,
    build_molit_backfill_plan_from_data_targets,
    chunk_molit_backfill_plan,
    load_molit_backfill_plan_manifest,
)


def test_build_molit_backfill_plan_splits_months_lawd_codes_and_datasets():
    plan = build_molit_backfill_plan(
        lawd_codes=["11110", "26000"],
        start_ym="202601",
        end_ym="202602",
        datasets=["trade", "rent", "offi-trade"],
    )

    assert [item.run_key for item in plan] == [
        "molit_apt_trade:11110:202601",
        "molit_apt_rent:11110:202601",
        "molit_offi_trade:11110:202601",
        "molit_apt_trade:26000:202601",
        "molit_apt_rent:26000:202601",
        "molit_offi_trade:26000:202601",
        "molit_apt_trade:11110:202602",
        "molit_apt_rent:11110:202602",
        "molit_offi_trade:11110:202602",
        "molit_apt_trade:26000:202602",
        "molit_apt_rent:26000:202602",
        "molit_offi_trade:26000:202602",
    ]


def test_build_molit_backfill_plan_payload_contains_import_run_contract_fields():
    plan = build_molit_backfill_plan(
        lawd_codes=["11110"],
        start_ym="202606",
        end_ym="202606",
        datasets=["trade"],
    )

    assert plan[0].to_payload() == {
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


def test_build_molit_backfill_plan_rejects_invalid_range():
    with pytest.raises(ValueError, match="start_ym must be before or equal to end_ym"):
        build_molit_backfill_plan(
            lawd_codes=["11110"],
            start_ym="202602",
            end_ym="202601",
            datasets=["trade"],
        )


def test_build_molit_backfill_plan_from_backend_data_targets_filters_and_dedupes_molit_targets():
    plan = build_molit_backfill_plan_from_data_targets(
        [
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
            {
                "targetId": "region-11110",
                "provider": "molit",
                "providerDataset": "molit_offi_trade",
                "lawdCode": "11110",
                "enabled": True,
            },
            {
                "targetId": "region-11680",
                "provider": "molit",
                "providerDataset": "molit_apt_trade",
                "lawdCode": "11680",
                "enabled": False,
            },
            {
                "targetId": "region-26440",
                "provider": "reb",
                "providerDataset": "reb_real_estate_statistics",
                "lawdCode": "26440",
                "enabled": True,
            },
        ],
        start_ym="202605",
        end_ym="202606",
    )

    assert [item.run_key for item in plan] == [
        "molit_apt_trade:11110:202605",
        "molit_apt_rent:11110:202605",
        "molit_offi_trade:11110:202605",
        "molit_apt_trade:11110:202606",
        "molit_apt_rent:11110:202606",
        "molit_offi_trade:11110:202606",
    ]


def test_chunk_molit_backfill_plan_splits_large_manifest_into_resume_units():
    plan = build_molit_backfill_plan(
        lawd_codes=["11110", "26000"],
        start_ym="202606",
        end_ym="202606",
        datasets=["trade", "rent"],
    )

    chunks = chunk_molit_backfill_plan(plan, chunk_size=3)

    assert [chunk.to_payload() for chunk in chunks] == [
        {
            "chunkIndex": 1,
            "chunkKey": "molit_backfill_chunk:000001",
            "runCount": 3,
            "firstRunKey": "molit_apt_trade:11110:202606",
            "lastRunKey": "molit_apt_trade:26000:202606",
            "items": [item.to_payload() for item in plan[:3]],
        },
        {
            "chunkIndex": 2,
            "chunkKey": "molit_backfill_chunk:000002",
            "runCount": 1,
            "firstRunKey": "molit_apt_rent:26000:202606",
            "lastRunKey": "molit_apt_rent:26000:202606",
            "items": [plan[3].to_payload()],
        },
    ]


def test_load_molit_backfill_plan_manifest_flattens_chunk_manifest(tmp_path):
    plan = build_molit_backfill_plan(
        lawd_codes=["11110", "26000"],
        start_ym="202606",
        end_ym="202606",
        datasets=["trade"],
    )
    manifest_path = tmp_path / "chunked-plan.json"
    manifest_path.write_text(
        __import__("json").dumps(
            {
                "chunkSize": 1,
                "chunkCount": 2,
                "chunks": [
                    {
                        "chunkIndex": 1,
                        "items": [plan[0].to_payload()],
                    },
                    {
                        "chunkIndex": 2,
                        "items": [plan[1].to_payload(), plan[1].to_payload()],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    loaded = load_molit_backfill_plan_manifest(manifest_path)

    assert [task.run_key for task in loaded] == [
        "molit_apt_trade:11110:202606",
        "molit_apt_trade:26000:202606",
    ]
