from youbuyfirst_pipeline.realestate_provider_catalog import (
    PUBLIC_DATA_DATASETS,
    enabled_backfill_dataset_ids,
    public_data_catalog_payload,
)

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]


def test_public_data_catalog_confirms_first_wave_sources():
    dataset_ids = {dataset.dataset_id for dataset in PUBLIC_DATA_DATASETS}

    assert {
        "molit_apt_trade",
        "molit_apt_rent",
        "molit_official_apartment_price_csv",
        "reb_real_estate_statistics",
        "molit_unsold_housing_stat",
        "molit_housing_permit_stat",
    }.issubset(dataset_ids)


def test_public_data_catalog_uses_readable_korean_provider_labels():
    payload_by_id = {
        item["datasetId"]: item
        for item in public_data_catalog_payload()["items"]
    }

    assert payload_by_id["molit_apt_trade"]["providerName"] == "국토교통부"
    assert payload_by_id["molit_apt_trade"]["displayName"] == "아파트 매매 실거래가"
    assert payload_by_id["molit_apt_rent"]["displayName"] == "아파트 전월세 실거래가"
    assert payload_by_id["molit_official_apartment_price_csv"]["displayName"] == "공동주택 호별 공시가격"
    assert payload_by_id["reb_real_estate_statistics"]["providerName"] == "한국부동산원"
    assert payload_by_id["molit_unsold_housing_stat"]["providerName"] == "국토교통 통계누리"


def test_public_data_catalog_marks_large_csv_as_file_backfill_source():
    dataset = next(
        dataset
        for dataset in PUBLIC_DATA_DATASETS
        if dataset.dataset_id == "molit_official_apartment_price_csv"
    )

    assert dataset.provider == "molit"
    assert dataset.access_method == "file"
    assert dataset.format == "csv_zip"
    assert dataset.fact_type == "official_apartment_price"
    assert dataset.backfill_required is True
    assert dataset.source_row_count == 15580435


def test_public_data_catalog_payload_is_api_safe():
    payload = public_data_catalog_payload()

    assert payload["items"][0]["datasetId"]
    assert payload["items"][0]["provider"]
    assert "serviceKey" not in str(payload)
    assert payload["items"] == sorted(payload["items"], key=lambda item: item["priority"])


def test_enabled_backfill_dataset_ids_excludes_reference_only_sources():
    assert enabled_backfill_dataset_ids() == [
        "molit_apt_trade",
        "molit_apt_rent",
        "molit_official_apartment_price_csv",
        "reb_real_estate_statistics",
        "molit_unsold_housing_stat",
        "molit_housing_permit_stat",
    ]


def test_backend_public_data_dataset_seed_matches_catalog_without_broken_korean():
    migration = (
        REPO_ROOT
        / "backend/src/main/resources/db/migration/V27__real_estate_public_data_catalog_and_raw_ingestion.sql"
    ).read_text(encoding="utf-8")

    for dataset in PUBLIC_DATA_DATASETS:
        assert f"'{dataset.dataset_id}'" in migration
        assert dataset.provider_name in migration
        assert dataset.display_name in migration

    assert "援?" not in migration
    assert "?꾪" not in migration
    assert "국토교통부" in migration
    assert "공동주택 호별 공시가격" in migration
