from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from youbuyfirst_pipeline.realestate_public_data import RealEstateMarketFact


APARTMENT_BRAND_TOKENS = {
    "래미안",
    "푸르지오",
    "자이",
    "힐스테이트",
    "더샵",
    "롯데캐슬",
    "아이파크",
    "디에이치",
    "e편한세상",
    "이편한세상",
    "포레나",
    "센트럴",
    "트리마제",
    "파크리오",
}

AMBIGUOUS_STANDALONE_COMPLEX_ALIASES = {
    "Doosan",
    "두산",
    "Samsung",
    "푸르지오",
    "자이",
    "래미안",
    "아이파크",
    "힐스테이트",
    "롯데캐슬",
    "삼성",
    "현대",
    "서울",
    "부산",
    "대구",
    "인천",
    "광주",
    "대전",
    "울산",
    "세종",
    "경기",
    "강원",
    "충북",
    "충남",
    "전북",
    "전남",
    "경북",
    "경남",
    "제주",
}


@dataclass(frozen=True)
class RealEstateComplexRegistryPayload:
    targets: list[dict]
    complexes: list[dict]
    aliases: list[dict]
    edges: list[dict]
    observed_target_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        payload = {
            "targets": self.targets,
            "complexes": self.complexes,
            "aliases": self.aliases,
            "edges": self.edges,
        }
        if self.observed_target_ids:
            payload["observedTargetIds"] = list(self.observed_target_ids)
        return payload


def build_real_estate_complex_registry_from_market_facts(
    facts: Iterable[RealEstateMarketFact | dict],
    *,
    region_targets_by_lawd_code: dict[str, str] | None = None,
) -> RealEstateComplexRegistryPayload:
    region_targets = region_targets_by_lawd_code or {}
    groups: dict[tuple[str, str, str, str], list[RealEstateMarketFact | dict]] = {}
    for fact in facts:
        values = _value_json(fact)
        apartment_name = _text(values.get("apartmentName") or values.get("complexName"))
        legal_dong_code = _text(_fact_value(fact, "legal_dong_code") or _fact_value(fact, "legalDongCode"))
        legal_dong_name = _text(values.get("legalDongName"))
        jibun = _text(values.get("jibun"))
        if not apartment_name or not legal_dong_code:
            continue
        key = (
            legal_dong_code,
            _match_key(legal_dong_name),
            _match_key(jibun),
            _match_key(apartment_name),
        )
        groups.setdefault(key, []).append(fact)

    targets: list[dict] = []
    complexes: list[dict] = []
    aliases: list[dict] = []
    edges: list[dict] = []
    seen_aliases: set[tuple[str, str]] = set()
    seen_edges: set[tuple[str, str]] = set()

    for key in sorted(groups):
        group = groups[key]
        first_values = _value_json(group[0])
        legal_dong_code, legal_dong_name_key, jibun_key, apartment_name_key = key
        apartment_name = _text(first_values.get("apartmentName") or first_values.get("complexName"))
        legal_dong_name = _first_text(group, "legalDongName")
        jibun = _first_text(group, "jibun")
        built_year = _first_int(group, "builtYear")
        target_id = _complex_target_id(legal_dong_code, legal_dong_name_key, jibun_key, apartment_name_key)
        region_target_id = _region_target_id_for_complex(
            legal_dong_code,
            legal_dong_name,
            region_targets,
        )
        jibun_address = _join_address(legal_dong_name, jibun)
        display_name = _complex_display_name(apartment_name, legal_dong_name)

        targets.append(
            {
                "targetId": target_id,
                "targetType": "complex",
                "displayName": display_name,
                "slug": target_id.removeprefix("complex-"),
                "reviewState": "approved",
                "dataStatus": "partial",
            }
        )
        complexes.append(
            {
                "targetId": target_id,
                "regionTargetId": region_target_id,
                "legalDongCode": legal_dong_code,
                "roadAddress": None,
                "jibunAddress": jibun_address,
                "normalizedAddress": _match_key(f"{legal_dong_code}{legal_dong_name}{jibun}{apartment_name}"),
                "builtYear": built_year,
                "householdCount": None,
                "source": "molit:market-fact",
                "markerDataStatus": "partial",
                "markerStale": True,
            }
        )

        for alias, alias_type, confidence in _aliases(apartment_name, legal_dong_name):
            alias_key = (target_id, _match_key(alias))
            if alias_key in seen_aliases:
                continue
            seen_aliases.add(alias_key)
            ambiguous = _is_ambiguous_standalone_complex_alias(alias, alias_type)
            aliases.append(
                {
                    "targetType": "complex",
                    "targetId": target_id,
                    "alias": alias,
                    "aliasType": alias_type,
                    "source": "molit:market-fact",
                    "evidenceUrl": None,
                    "confidence": confidence,
                    "reviewState": "candidate" if ambiguous else "approved",
                    "createdBy": "system",
                    "ambiguous": ambiguous,
                }
            )

        if region_target_id:
            edge_key = (region_target_id, target_id)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append(
                    {
                        "fromTargetType": "region",
                        "fromTargetId": region_target_id,
                        "toTargetType": "complex",
                        "toTargetId": target_id,
                        "edgeType": "contains",
                        "confidence": 0.74,
                        "source": "molit:market-fact",
                        "reviewState": "approved",
                    }
                )

    return RealEstateComplexRegistryPayload(
        targets=targets,
        complexes=complexes,
        aliases=aliases,
        edges=edges,
    )


def _region_target_id_for_complex(
    legal_dong_code: str,
    legal_dong_name: str | None,
    region_targets: dict[str, str],
) -> str | None:
    normalized_dong_name = _match_key(legal_dong_name)
    lookup_codes = [legal_dong_code]
    if len(legal_dong_code) >= 5:
        lookup_codes.append(legal_dong_code[:5])

    if normalized_dong_name:
        for code in lookup_codes:
            target_id = region_targets.get(f"{code}:{normalized_dong_name}")
            if target_id:
                return target_id

    for code in lookup_codes:
        target_id = region_targets.get(code)
        if target_id:
            return target_id
    return None


def market_fact_payloads_to_complex_registry_facts(payloads: Iterable[dict]) -> list[dict]:
    result: list[dict] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        fact_type = str(payload.get("factType") or payload.get("fact_type") or "").strip()
        if fact_type not in {"apt_trade", "apt_rent", "official_apartment_price"}:
            continue
        result.append(payload)
    return result


def load_real_estate_complex_registry_market_facts(path: str | Path) -> list[dict]:
    return market_fact_payloads_to_complex_registry_facts(_load_json_records(path))


def _aliases(apartment_name: str, legal_dong_name: str | None) -> list[tuple[str, str, float]]:
    result = [(apartment_name, "official", 0.92)]
    if legal_dong_name:
        result.append((f"{legal_dong_name} {apartment_name}", "nearby_area", 0.78))
        core_name = _location_prefixed_core_name(apartment_name)
        if core_name and _match_key(core_name) != _match_key(apartment_name):
            result.append((f"{legal_dong_name} {core_name}", "nearby_core_name", 0.66))
    short_alias = _compound_korean_short_alias(apartment_name)
    if short_alias:
        result.append((short_alias, "short_name", 0.68))
        if legal_dong_name:
            result.append((f"{legal_dong_name} {short_alias}", "nearby_short_name", 0.62))
    return result


def _complex_display_name(apartment_name: str, legal_dong_name: str | None) -> str:
    if legal_dong_name and _is_ambiguous_standalone_complex_alias(apartment_name, "official"):
        return f"{legal_dong_name} {apartment_name}"
    return apartment_name


def _location_prefixed_core_name(apartment_name: str) -> str | None:
    tokens = [
        token
        for token in apartment_name.replace("/", " ").replace("-", " ").split()
        if token
    ]
    if len(tokens) < 3:
        tokens = _compact_brand_hangul_tokens(apartment_name)
    if len(tokens) < 3:
        return None
    leading = tokens[0]
    if _is_common_apartment_brand_token(leading):
        return None
    core = " ".join(tokens[1:]).strip()
    if len(_match_key(core)) < 4:
        return None
    return core


def _is_common_apartment_brand_token(token: str) -> bool:
    normalized = _match_key(token).lower()
    return normalized in {_match_key(brand).lower() for brand in APARTMENT_BRAND_TOKENS}


def _is_ambiguous_standalone_complex_alias(alias: str, alias_type: str) -> bool:
    if alias_type != "official":
        return False
    return _match_key(alias).lower() in {
        _match_key(value).lower()
        for value in AMBIGUOUS_STANDALONE_COMPLEX_ALIASES
    }


def _compound_korean_short_alias(apartment_name: str) -> str | None:
    tokens = _spaced_hangul_tokens(apartment_name)
    if len(tokens) < 3:
        tokens = _compact_brand_hangul_tokens(apartment_name)
    if len(tokens) < 3:
        return None
    alias = "".join(token[0] for token in tokens if token)
    if len(alias) < 3 or len(alias) > 6:
        return None
    return alias


def _spaced_hangul_tokens(value: str) -> list[str]:
    return [
        token
        for token in value.replace("/", " ").replace("-", " ").split()
        if _contains_hangul(token)
    ]


def _compact_brand_hangul_tokens(value: str) -> list[str]:
    compact = "".join(value.replace("/", " ").replace("-", " ").split())
    if not _contains_hangul(compact):
        return []
    hits: list[tuple[int, int, str]] = []
    for brand in APARTMENT_BRAND_TOKENS:
        start = compact.find(brand)
        while start >= 0:
            hits.append((start, start + len(brand), brand))
            start = compact.find(brand, start + 1)
    if not hits:
        return []

    selected: list[tuple[int, int, str]] = []
    last_end = -1
    for start, end, brand in sorted(hits, key=lambda hit: (hit[0], -(hit[1] - hit[0]))):
        if start < last_end:
            continue
        selected.append((start, end, brand))
        last_end = end
    if len(selected) < 2:
        return []

    first_start = selected[0][0]
    prefix = compact[:first_start]
    tokens = [prefix] if _contains_hangul(prefix) else []
    tokens.extend(brand for _, _, brand in selected)
    return tokens


def _load_json_records(path: str | Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        if isinstance(payload, dict) and "items" in payload:
            records = payload.get("items", [])
        elif isinstance(payload, dict):
            records = [payload]
        else:
            records = payload
    if not isinstance(records, list):
        raise ValueError("market fact payload must be a JSON array, {items: []}, or JSONL")
    return [record for record in records if isinstance(record, dict)]


def _complex_target_id(
    legal_dong_code: str,
    legal_dong_name_key: str,
    jibun_key: str,
    apartment_name_key: str,
) -> str:
    seed = "|".join([legal_dong_code, legal_dong_name_key, jibun_key, apartment_name_key])
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"complex-molit-{legal_dong_code[:10]}-{digest}"


def _value_json(fact: RealEstateMarketFact | dict) -> dict:
    if isinstance(fact, RealEstateMarketFact):
        return fact.value_json
    value = fact.get("valueJson") or fact.get("value_json") or {}
    return value if isinstance(value, dict) else {}


def _fact_value(fact: RealEstateMarketFact | dict, name: str):
    if isinstance(fact, RealEstateMarketFact):
        if name in {"legal_dong_code", "legalDongCode"}:
            return fact.legal_dong_code
        return getattr(fact, name, None)
    return fact.get(name)


def _first_text(facts: list[RealEstateMarketFact | dict], key: str) -> str | None:
    for fact in facts:
        value = _text(_value_json(fact).get(key))
        if value:
            return value
    return None


def _first_int(facts: list[RealEstateMarketFact | dict], key: str) -> int | None:
    for fact in facts:
        value = _value_json(fact).get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
    return None


def _join_address(legal_dong_name: str | None, jibun: str | None) -> str | None:
    parts = [part for part in [legal_dong_name, jibun] if part]
    return " ".join(parts) if parts else None


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _match_key(value: object) -> str:
    if value is None:
        return ""
    return "".join(char for char in str(value) if _match_char(char))


def _match_char(char: str) -> bool:
    return char.isalnum()


def _contains_hangul(value: str) -> bool:
    return any("가" <= char <= "힣" for char in value)
