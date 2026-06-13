from __future__ import annotations

import csv
import io
from dataclasses import dataclass


LEGAL_DONG_CODE_SOURCE = "import:molit-legal-dong-code"


@dataclass(frozen=True)
class RealEstateRegionImport:
    target_id: str
    display_name: str
    slug: str
    region_level: str
    parent_target_id: str | None
    legal_dong_code: str
    region_code: str
    source: str = LEGAL_DONG_CODE_SOURCE

    def to_import_dict(self) -> dict:
        return {
            "targetId": self.target_id,
            "displayName": self.display_name,
            "slug": self.slug,
            "regionLevel": self.region_level,
            "parentTargetId": self.parent_target_id,
            "legalDongCode": self.legal_dong_code,
            "regionCode": self.region_code,
            "source": self.source,
        }


@dataclass(frozen=True)
class RealEstateMarketDataTargetImport:
    target_id: str
    provider_dataset: str
    lawd_code: str
    provider: str = "molit"
    enabled: bool = True
    refresh_interval_hours: int = 24
    stale_after_hours: int = 72

    def to_import_dict(self) -> dict:
        return {
            "targetId": self.target_id,
            "provider": self.provider,
            "providerDataset": self.provider_dataset,
            "lawdCode": self.lawd_code,
            "enabled": self.enabled,
            "refreshIntervalHours": self.refresh_interval_hours,
            "staleAfterHours": self.stale_after_hours,
        }


def parse_molit_legal_dong_code_csv(csv_text: str) -> list[RealEstateRegionImport]:
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    regions = []
    for raw_row in reader:
        row = _normalize_row(raw_row)
        code = row.get("법정동코드", "")
        name = row.get("법정동명", "")
        if not code or not name or not _is_active_region(row):
            continue
        region = _build_region(code=code, name=name)
        if region is not None:
            regions.append(region)
    return regions


def build_molit_region_market_data_targets(
    regions: list[RealEstateRegionImport],
    *,
    datasets: list[str] | None = None,
) -> list[RealEstateMarketDataTargetImport]:
    provider_datasets = [_normalize_molit_provider_dataset(dataset) for dataset in (datasets or ["trade", "rent"])]
    targets: list[RealEstateMarketDataTargetImport] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for region in regions:
        if region.region_level != "sigungu" or len(region.legal_dong_code) != 5:
            continue
        for provider_dataset in provider_datasets:
            key = (region.target_id, provider_dataset, region.legal_dong_code)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            targets.append(
                RealEstateMarketDataTargetImport(
                    target_id=region.target_id,
                    provider_dataset=provider_dataset,
                    lawd_code=region.legal_dong_code,
                )
            )
    return targets


def _normalize_row(row: dict[str | None, str | None]) -> dict[str, str]:
    normalized = {}
    for key, value in row.items():
        if key is None:
            continue
        normalized[key.strip().lstrip("\ufeff")] = (value or "").strip()
    return normalized


def _is_active_region(row: dict[str, str]) -> bool:
    status = row.get("폐지여부", "")
    if not status:
        return True
    return status == "존재"


def _build_region(code: str, name: str) -> RealEstateRegionImport | None:
    digits = "".join(ch for ch in code if ch.isdigit())
    if len(digits) != 10:
        return None

    if digits[2:] == "00000000":
        legal_dong_code = digits[:2] + "000"
        region_code = digits[:2]
        region_level = "sido"
        parent_target_id = None
    elif digits[5:] == "00000":
        legal_dong_code = digits[:5]
        region_code = digits[:5]
        region_level = "sigungu"
        parent_target_id = f"region-{digits[:2]}000"
    else:
        legal_dong_code = digits
        region_code = digits
        region_level = "eupmyeondong"
        parent_target_id = f"region-{digits[:5]}"

    target_id = f"region-{legal_dong_code}"
    return RealEstateRegionImport(
        target_id=target_id,
        display_name=name,
        slug=target_id,
        region_level=region_level,
        parent_target_id=parent_target_id,
        legal_dong_code=legal_dong_code,
        region_code=region_code,
    )


def _normalize_molit_provider_dataset(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"trade", "apt-trade", "molit-apt-trade"}:
        return "molit_apt_trade"
    if normalized in {"rent", "apt-rent", "molit-apt-rent", "lease"}:
        return "molit_apt_rent"
    raise ValueError(f"unsupported MOLIT region dataset: {value}")
