from __future__ import annotations

import csv
import io
from dataclasses import dataclass


LEGAL_DONG_CODE_SOURCE = "import:molit-legal-dong-code"
REGION_ALIAS_SOURCE = "import:region-registry-alias"

_SIDO_SHORT_LABELS = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원특별자치도": "강원",
    "강원도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전북특별자치도": "전북",
    "전라북도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주특별자치도": "제주",
}


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


def build_real_estate_region_alias_requests(
    regions: list[RealEstateRegionImport | dict],
) -> list[dict]:
    candidates: list[dict] = []
    seen_per_target: set[tuple[str, str]] = set()
    alias_targets: dict[str, set[str]] = {}
    for region in regions:
        target_id = _region_value(region, "target_id", "targetId")
        display_name = _region_value(region, "display_name", "displayName")
        region_level = _region_value(region, "region_level", "regionLevel")
        if not target_id or not display_name:
            continue
        for alias, alias_type, confidence in _region_alias_candidates(display_name, region_level):
            normalized = _alias_key(alias)
            if len(normalized) < 2:
                continue
            key = (target_id, normalized)
            if key in seen_per_target:
                continue
            seen_per_target.add(key)
            alias_targets.setdefault(normalized, set()).add(target_id)
            candidates.append(
                {
                    "targetType": "region",
                    "targetId": target_id,
                    "alias": alias,
                    "aliasType": alias_type,
                    "source": REGION_ALIAS_SOURCE,
                    "evidenceUrl": None,
                    "confidence": confidence,
                    "reviewState": "approved",
                    "createdBy": "system",
                    "ambiguous": False,
                }
            )

    for alias in candidates:
        normalized = _alias_key(alias["alias"])
        if len(alias_targets.get(normalized, set())) > 1 and _is_context_free_region_alias(alias):
            alias["reviewState"] = "candidate"
            alias["ambiguous"] = True

    return sorted(
        candidates,
        key=lambda item: (
            item["targetId"],
            item["reviewState"] != "approved",
            item["aliasType"],
            item["alias"],
        ),
    )


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


def _region_alias_candidates(display_name: str, region_level: str | None) -> list[tuple[str, str, float]]:
    name = " ".join(display_name.split())
    tokens = name.split()
    if not name or not tokens:
        return []

    aliases: list[tuple[str, str, float]] = [(name, "official", 0.96)]
    if len(tokens) >= 2:
        prefix = _SIDO_SHORT_LABELS.get(tokens[0], _strip_region_suffix(tokens[0]))
        if prefix:
            aliases.append((f"{prefix} {' '.join(tokens[1:])}", "context_name", 0.90))

    if region_level != "sido" and len(tokens) >= 2:
        terminal = tokens[-1]
        aliases.append((terminal, "terminal_name", 0.86))
        short_terminal = _strip_region_suffix(terminal)
        if short_terminal and _alias_key(short_terminal) != _alias_key(terminal):
            aliases.append((short_terminal, "short_name", 0.72))
        aliases.append((f"{tokens[-2]} {terminal}", "nearby_area", 0.88))

    return aliases


def _strip_region_suffix(value: str) -> str:
    for suffix in (
        "특별자치시",
        "특별자치도",
        "특별시",
        "광역시",
        "자치구",
        "자치시",
        "시",
        "군",
        "구",
        "읍",
        "면",
        "동",
        "리",
        "가",
        "도",
    ):
        if value.endswith(suffix) and len(value) > len(suffix):
            return value[: -len(suffix)]
    return value


def _is_context_free_region_alias(alias: dict) -> bool:
    alias_type = str(alias.get("aliasType") or "")
    alias_text = str(alias.get("alias") or "")
    return alias_type in {"terminal_name", "short_name"} and " " not in alias_text


def _alias_key(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _region_value(region: RealEstateRegionImport | dict, snake_key: str, camel_key: str) -> str:
    if isinstance(region, RealEstateRegionImport):
        return str(getattr(region, snake_key) or "").strip()
    return str(region.get(camel_key) or region.get(snake_key) or "").strip()
