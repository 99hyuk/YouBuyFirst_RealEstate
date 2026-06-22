from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Iterable

from youbuyfirst_pipeline.realestate_complex_registry import RealEstateComplexRegistryPayload
from youbuyfirst_pipeline.realestate_matcher import RealEstateAliasRule, RealEstatePostForMatching


COMMUNITY_COMPLEX_SEED_SOURCE = "community:observed-complex-seed"
COMMUNITY_TRADE_TABLE_SOURCE = "community:structured-trade-table"
COMMUNITY_COMPLEX_COORDINATE_PROVIDER = "kakao_local_search:keyword"
COMMUNITY_COMPLEX_COORDINATE_AS_OF = "2026-06-16T00:00:00Z"
GENERIC_COMPLEX_NAME_KEYS = {
    "자이",
    "래미안",
    "푸르지오",
    "아이파크",
    "힐스테이트",
    "롯데캐슬",
    "더샵",
    "e편한세상",
    "두산",
    "송촌",
}


@dataclass(frozen=True)
class CommunityComplexSeed:
    target_id: str
    display_name: str
    slug: str
    region_target_id: str
    aliases: tuple[str, ...]
    legal_dong_code: str | None = None
    address_hint: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    coordinate_provider: str | None = None
    coordinate_as_of: str | None = None
    coordinate_status: str = "candidate"
    source: str = COMMUNITY_COMPLEX_SEED_SOURCE
    review_state: str = "approved"
    alias_type: str | None = None
    alias_confidence: float = 0.74
    edge_confidence: float = 0.62


COMMUNITY_COMPLEX_SEEDS: tuple[CommunityComplexSeed, ...] = (
    CommunityComplexSeed(
        target_id="complex-community-banpo-trini-one",
        display_name="반포 트리니원",
        slug="community-banpo-trini-one",
        region_target_id="region-seoul-seocho",
        aliases=("반포 트리니원", "트리니원"),
        legal_dong_code="11650",
        address_hint="서울 서초구 반포동 일대",
        latitude=37.5004804,
        longitude=126.9888776,
        coordinate_provider=COMMUNITY_COMPLEX_COORDINATE_PROVIDER,
        coordinate_as_of=COMMUNITY_COMPLEX_COORDINATE_AS_OF,
    ),
    CommunityComplexSeed(
        target_id="complex-community-dongtan-lotte-castle",
        display_name="동탄역 롯데캐슬",
        slug="community-dongtan-lotte-castle",
        region_target_id="region-gyeonggi-hwaseongsi",
        aliases=("동탄역 롯데캐슬",),
        legal_dong_code="41590",
        address_hint="경기 화성시 동탄역권 일대",
        latitude=37.1991684,
        longitude=127.0973091,
        coordinate_provider=COMMUNITY_COMPLEX_COORDINATE_PROVIDER,
        coordinate_as_of=COMMUNITY_COMPLEX_COORDINATE_AS_OF,
    ),
    CommunityComplexSeed(
        target_id="complex-community-helio-city",
        display_name="헬리오시티",
        slug="community-helio-city",
        region_target_id="region-seoul-songpa",
        aliases=("헬리오시티", "헬리오"),
        legal_dong_code="11710",
        address_hint="서울 송파구 가락동 일대",
        latitude=37.4996101,
        longitude=127.1116109,
        coordinate_provider=COMMUNITY_COMPLEX_COORDINATE_PROVIDER,
        coordinate_as_of=COMMUNITY_COMPLEX_COORDINATE_AS_OF,
    ),
    CommunityComplexSeed(
        target_id="complex-community-imun-ipark-xi",
        display_name="이문아이파크자이",
        slug="community-imun-ipark-xi",
        region_target_id="region-seoul-dongdaemun",
        aliases=("이문아이파크자이", "이문 아이파크 자이"),
        legal_dong_code="11230",
        address_hint="서울 동대문구 이문동 일대",
        latitude=37.5981862,
        longitude=127.0634688,
        coordinate_provider=COMMUNITY_COMPLEX_COORDINATE_PROVIDER,
        coordinate_as_of=COMMUNITY_COMPLEX_COORDINATE_AS_OF,
    ),
    CommunityComplexSeed(
        target_id="complex-community-olympic-park-foreon",
        display_name="올림픽파크포레온",
        slug="community-olympic-park-foreon",
        region_target_id="region-seoul-gangdong",
        aliases=("올림픽파크포레온", "둔촌주공"),
        legal_dong_code="11740",
        address_hint="서울 강동구 둔촌동 일대",
        latitude=37.5238551,
        longitude=127.1404115,
        coordinate_provider=COMMUNITY_COMPLEX_COORDINATE_PROVIDER,
        coordinate_as_of=COMMUNITY_COMPLEX_COORDINATE_AS_OF,
    ),
    CommunityComplexSeed(
        target_id="complex-community-raemian-lagrande",
        display_name="래미안라그란데",
        slug="community-raemian-lagrande",
        region_target_id="region-seoul-dongdaemun",
        aliases=("래미안라그란데", "래미안 라그란데"),
        legal_dong_code="11230",
        address_hint="서울 동대문구 이문동 일대",
        latitude=37.6000844,
        longitude=127.0602306,
        coordinate_provider=COMMUNITY_COMPLEX_COORDINATE_PROVIDER,
        coordinate_as_of=COMMUNITY_COMPLEX_COORDINATE_AS_OF,
    ),
    CommunityComplexSeed(
        target_id="complex-community-ricenz",
        display_name="리센츠",
        slug="community-ricenz",
        region_target_id="region-seoul-songpa",
        aliases=("리센츠",),
        legal_dong_code="11710",
        address_hint="서울 송파구 잠실동 일대",
        latitude=37.5127529,
        longitude=127.0884194,
        coordinate_provider=COMMUNITY_COMPLEX_COORDINATE_PROVIDER,
        coordinate_as_of=COMMUNITY_COMPLEX_COORDINATE_AS_OF,
    ),
    CommunityComplexSeed(
        target_id="complex-community-trimage",
        display_name="트리마제",
        slug="community-trimage",
        region_target_id="region-seoul-seongdong",
        aliases=("트리마제",),
        legal_dong_code="11200",
        address_hint="서울 성동구 성수동 일대",
        latitude=37.5387425,
        longitude=127.0447999,
        coordinate_provider=COMMUNITY_COMPLEX_COORDINATE_PROVIDER,
        coordinate_as_of=COMMUNITY_COMPLEX_COORDINATE_AS_OF,
    ),
)


def build_observed_community_complex_seed_registry(
    posts: Iterable[RealEstatePostForMatching | dict],
    *,
    seeds: Iterable[CommunityComplexSeed] = COMMUNITY_COMPLEX_SEEDS,
    existing_aliases: Iterable[RealEstateAliasRule | dict] = (),
) -> RealEstateComplexRegistryPayload:
    post_list = list(posts)
    existing_alias_list = list(existing_aliases)
    existing_alias_index = _existing_complex_alias_index(existing_alias_list)
    existing_alias_keys_by_target = _existing_alias_keys_by_target(existing_alias_list)
    fixed_seeds = list(seeds)
    observed_seed_ids = _observed_seed_ids(post_list, fixed_seeds)
    observed_seeds = sorted(
        [seed for seed in fixed_seeds if seed.target_id in observed_seed_ids],
        key=lambda seed: seed.target_id,
    )
    observed_seeds.extend(
        _observed_trade_table_complex_seeds(
            post_list,
            existing_alias_list,
            existing_complex_alias_index=existing_alias_index,
        )
    )

    targets = []
    complexes = []
    aliases = []
    edges = []
    observed_target_ids = []
    for seed in observed_seeds:
        existing_target_id = _existing_target_id_for_seed(seed, existing_alias_index)
        if existing_target_id:
            observed_target_ids.append(existing_target_id)
            existing_alias_keys = existing_alias_keys_by_target.get(existing_target_id, set())
            if existing_target_id == seed.target_id:
                complexes.append(_complex_payload(seed))
            aliases.extend(
                _alias_payload(seed, alias, target_id=existing_target_id)
                for alias in seed.aliases
                if _match_key(alias) not in existing_alias_keys
            )
            continue
        observed_target_ids.append(seed.target_id)
        targets.append(_target_payload(seed))
        complexes.append(_complex_payload(seed))
        aliases.extend(_alias_payload(seed, alias) for alias in seed.aliases)
        edges.append(_edge_payload(seed))
    return RealEstateComplexRegistryPayload(
        targets=targets,
        complexes=complexes,
        aliases=aliases,
        edges=edges,
        observed_target_ids=tuple(observed_target_ids),
    )


def _observed_seed_ids(
    posts: Iterable[RealEstatePostForMatching | dict],
    seeds: Iterable[CommunityComplexSeed],
) -> set[str]:
    seed_list = list(seeds)
    observed: set[str] = set()
    for post in posts:
        text = _post_text(post)
        normalized_text = _match_key(text)
        if not normalized_text:
            continue
        for seed in seed_list:
            if seed.target_id in observed:
                continue
            if any(_match_key(alias) in normalized_text for alias in seed.aliases):
                observed.add(seed.target_id)
    return observed


def _existing_target_id_for_seed(seed: CommunityComplexSeed, alias_index: dict[str, str]) -> str | None:
    for alias in seed.aliases:
        target_id = alias_index.get(_match_key(alias))
        if target_id:
            return target_id
    return None


def _existing_complex_alias_index(existing_aliases: Iterable[RealEstateAliasRule | dict]) -> dict[str, str]:
    index: dict[str, str] = {}
    for alias in existing_aliases:
        row = _existing_alias_row(alias)
        if row is None:
            continue
        index.setdefault(_match_key(row["alias"]), row["target_id"])
    return index


def _existing_alias_keys_by_target(existing_aliases: Iterable[RealEstateAliasRule | dict]) -> dict[str, set[str]]:
    aliases_by_target: dict[str, set[str]] = {}
    for alias in existing_aliases:
        row = _existing_alias_row(alias)
        if row is None:
            continue
        aliases_by_target.setdefault(row["target_id"], set()).add(_match_key(row["alias"]))
    return aliases_by_target


def _observed_trade_table_complex_seeds(
    posts: Iterable[RealEstatePostForMatching | dict],
    existing_aliases: Iterable[RealEstateAliasRule | dict],
    *,
    existing_complex_alias_index: dict[str, str],
) -> list[CommunityComplexSeed]:
    region_alias_index = _existing_region_alias_index(existing_aliases)
    if not region_alias_index:
        return []

    observed: dict[tuple[str, str], CommunityComplexSeed] = {}
    for post in posts:
        for complex_name, region_target_id in _extract_trade_table_complex_mentions(_post_text(post), region_alias_index):
            complex_key = _match_key(complex_name)
            if not complex_key or complex_key in existing_complex_alias_index:
                continue
            observed.setdefault(
                (region_target_id, complex_key),
                _candidate_trade_table_seed(
                    display_name=complex_name,
                    region_target_id=region_target_id,
                ),
            )
    return sorted(observed.values(), key=lambda seed: (seed.region_target_id, seed.display_name))


def _extract_trade_table_complex_mentions(
    text: str,
    region_alias_index: dict[str, str],
    *,
    max_mentions: int = 30,
) -> list[tuple[str, str]]:
    tokens = [_clean_table_token(token) for token in re.split(r"\s+", text.strip())]
    tokens = [token for token in tokens if token]
    mentions: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index in range(0, max(0, len(tokens) - 2)):
        region_target_id = region_alias_index.get(_match_key(tokens[index + 1]))
        if not region_target_id:
            continue
        complex_name = tokens[index]
        if not _looks_like_complex_name(complex_name):
            continue
        if not _nearby_trade_row_signature(tokens[index + 2 : index + 8]):
            continue
        key = (region_target_id, _match_key(complex_name))
        if key in seen:
            continue
        seen.add(key)
        mentions.append((complex_name, region_target_id))
        if len(mentions) >= max_mentions:
            break
    return mentions


def _candidate_trade_table_seed(*, display_name: str, region_target_id: str) -> CommunityComplexSeed:
    digest = hashlib.sha1(f"{region_target_id}:{_match_key(display_name)}".encode("utf-8")).hexdigest()[:12]
    return CommunityComplexSeed(
        target_id=f"complex-community-observed-{digest}",
        display_name=display_name,
        slug=f"community-observed-{digest}",
        region_target_id=region_target_id,
        aliases=(display_name,),
        source=COMMUNITY_TRADE_TABLE_SOURCE,
        review_state="candidate",
        alias_type="community_observed_trade_table",
        alias_confidence=0.66,
        edge_confidence=0.58,
    )


def _existing_region_alias_index(existing_aliases: Iterable[RealEstateAliasRule | dict]) -> dict[str, str]:
    index: dict[str, str] = {}
    for alias in existing_aliases:
        row = _existing_alias_row_for_type(alias, target_type="region")
        if row is None:
            continue
        index.setdefault(_match_key(row["alias"]), row["target_id"])
    return index


def _existing_alias_row(alias: RealEstateAliasRule | dict) -> dict[str, str] | None:
    return _existing_alias_row_for_type(alias, target_type="complex")


def _existing_alias_row_for_type(alias: RealEstateAliasRule | dict, *, target_type: str) -> dict[str, str] | None:
    if isinstance(alias, RealEstateAliasRule):
        actual_target_type = alias.target_type
        target_id = alias.target_id
        alias_text = alias.alias
        review_state = alias.review_state
        ambiguous = alias.ambiguous
    else:
        actual_target_type = str(alias.get("targetType") or alias.get("target_type") or "")
        target_id = str(alias.get("targetId") or alias.get("target_id") or "")
        alias_text = str(alias.get("alias") or "")
        review_state = str(alias.get("reviewState") or alias.get("review_state") or "approved")
        ambiguous = bool(alias.get("ambiguous", False))
    if actual_target_type.strip() != target_type:
        return None
    if review_state.strip().lower() != "approved" or ambiguous:
        return None
    normalized_alias = _match_key(alias_text)
    if not target_id.strip() or len(normalized_alias) < 2:
        return None
    return {"target_id": target_id.strip(), "alias": alias_text.strip()}


def _target_payload(seed: CommunityComplexSeed) -> dict:
    return {
        "targetId": seed.target_id,
        "targetType": "complex",
        "displayName": seed.display_name,
        "slug": seed.slug,
        "reviewState": seed.review_state,
        "dataStatus": "community_observed",
    }


def _complex_payload(seed: CommunityComplexSeed) -> dict:
    return {
        "targetId": seed.target_id,
        "regionTargetId": seed.region_target_id,
        "legalDongCode": seed.legal_dong_code,
        "roadAddress": None,
        "jibunAddress": seed.address_hint,
        "normalizedAddress": _match_key(f"{seed.address_hint or ''}{seed.display_name}"),
        "builtYear": None,
        "householdCount": None,
        "source": seed.source,
        "latitude": seed.latitude,
        "longitude": seed.longitude,
        "coordinateProvider": seed.coordinate_provider,
        "coordinateAsOf": seed.coordinate_as_of,
        "coordinateStatus": seed.coordinate_status,
        "markerTone": "flat",
        "priceSummary": "확인 필요",
        "changeLabel": "unknown",
        "reactionSummary": "반응 지표 연결 전",
        "markerNote": "커뮤니티에서 관측된 단지 후보입니다. 좌표는 지도 표시용 후보값이며 시장 fact 검증이 필요합니다.",
        "markerDataStatus": "community_observed",
        "markerStale": True,
    }


def _alias_payload(seed: CommunityComplexSeed, alias: str, *, target_id: str | None = None) -> dict:
    alias_type = seed.alias_type
    if alias_type is None:
        alias_type = "community_observed" if alias == seed.display_name else "community_alias"
    return {
        "targetType": "complex",
        "targetId": target_id or seed.target_id,
        "alias": alias,
        "aliasType": alias_type,
        "source": seed.source,
        "evidenceUrl": None,
        "confidence": seed.alias_confidence,
        "reviewState": seed.review_state,
        "createdBy": "system",
        "ambiguous": False,
    }


def _edge_payload(seed: CommunityComplexSeed) -> dict:
    return {
        "fromTargetType": "region",
        "fromTargetId": seed.region_target_id,
        "toTargetType": "complex",
        "toTargetId": seed.target_id,
        "edgeType": "contains",
        "confidence": seed.edge_confidence,
        "source": seed.source,
        "reviewState": seed.review_state,
    }


def _post_text(post: RealEstatePostForMatching | dict) -> str:
    if isinstance(post, RealEstatePostForMatching):
        return f"{post.title} {post.content_snippet}"
    return f"{post.get('title') or ''} {post.get('contentSnippet') or post.get('content_snippet') or ''}"


def _match_key(value: object) -> str:
    if value is None:
        return ""
    return "".join(char.lower() for char in str(value) if char.isalnum())


def _clean_table_token(value: str) -> str:
    return value.strip(" \t\r\n|,;[](){}<>")


def _looks_like_complex_name(value: str) -> bool:
    key = _match_key(value)
    if len(key) < 2:
        return False
    if key.isdigit():
        return False
    if re.fullmatch(r"\d+단지", value.strip(), flags=re.IGNORECASE):
        return False
    if re.fullmatch(r"[\d.,/-]+", value):
        return False
    if key in {_match_key(item) for item in GENERIC_COMPLEX_NAME_KEYS}:
        return False
    blocked = {
        "아파트",
        "아파트이름",
        "동이름",
        "전용면적",
        "가격",
        "날짜",
        "매매",
        "전세",
        "최근",
        "등록된",
    }
    return key not in {_match_key(item) for item in blocked}


def _nearby_trade_row_signature(tokens: list[str]) -> bool:
    if not tokens:
        return False
    has_date = any(re.fullmatch(r"\d{4}[./-]\d{1,2}[./-]\d{1,2}", token) for token in tokens)
    has_numeric = sum(1 for token in tokens if re.search(r"\d", token)) >= 3
    return has_date and has_numeric
