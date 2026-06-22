from datetime import date, datetime, timezone

from youbuyfirst_pipeline.realestate_complex_registry import (
    build_real_estate_complex_registry_from_market_facts,
)
from youbuyfirst_pipeline.realestate_public_data import RealEstateMarketFact


def test_build_complex_registry_prefixes_display_name_for_ambiguous_standalone_complex_name():
    ingested_at = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
    fact = RealEstateMarketFact(
        fact_type="apt_trade",
        provider="molit",
        provider_dataset="molit_apt_trade",
        provider_object_id="molit_apt_trade:11110:202606:trade-doosan",
        legal_dong_code="11110",
        observed_at=date(2026, 6, 3),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "Doosan",
            "legalDongName": "Sajik",
            "jibun": "3",
        },
    )

    registry = build_real_estate_complex_registry_from_market_facts(
        [fact],
        region_targets_by_lawd_code={"11110": "region-seoul-jongno"},
    )

    assert registry.targets[0]["displayName"] == "Sajik Doosan"
    aliases = {alias["alias"]: alias for alias in registry.aliases}
    assert aliases["Doosan"]["reviewState"] == "candidate"
    assert aliases["Sajik Doosan"]["reviewState"] == "approved"


def test_build_complex_registry_deduplicates_trade_and_rent_facts_for_same_apartment():
    ingested_at = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
    trade_fact = RealEstateMarketFact(
        fact_type="apt_trade",
        provider="molit",
        provider_dataset="molit_apt_trade",
        provider_object_id="molit_apt_trade:11110:202606:trade-1",
        legal_dong_code="11110",
        observed_at=date(2026, 6, 3),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "Sajik Palace",
            "legalDongName": "Sajik-dong",
            "jibun": "1-1",
            "builtYear": 2015,
        },
    )
    rent_fact = RealEstateMarketFact(
        fact_type="apt_rent",
        provider="molit",
        provider_dataset="molit_apt_rent",
        provider_object_id="molit_apt_rent:11110:202606:rent-1",
        legal_dong_code="11110",
        observed_at=date(2026, 6, 5),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "Sajik Palace",
            "legalDongName": "Sajik-dong",
            "jibun": "1-1",
            "depositAmountManwon": 45000,
        },
    )

    registry = build_real_estate_complex_registry_from_market_facts(
        [trade_fact, rent_fact],
        region_targets_by_lawd_code={"11110": "region-seoul-jongno"},
    )

    assert [target["targetType"] for target in registry.targets] == ["complex"]
    assert registry.targets[0]["displayName"] == "Sajik Palace"
    assert registry.targets[0]["targetId"].startswith("complex-molit-11110-")
    assert registry.complexes == [
        {
            "targetId": registry.targets[0]["targetId"],
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
    assert registry.aliases == [
        {
            "targetType": "complex",
            "targetId": registry.targets[0]["targetId"],
            "alias": "Sajik Palace",
            "aliasType": "official",
            "source": "molit:market-fact",
            "evidenceUrl": None,
            "confidence": 0.92,
            "reviewState": "approved",
            "createdBy": "system",
            "ambiguous": False,
        },
        {
            "targetType": "complex",
            "targetId": registry.targets[0]["targetId"],
            "alias": "Sajik-dong Sajik Palace",
            "aliasType": "nearby_area",
            "source": "molit:market-fact",
            "evidenceUrl": None,
            "confidence": 0.78,
            "reviewState": "approved",
            "createdBy": "system",
            "ambiguous": False,
        },
    ]
    assert registry.edges == [
        {
            "fromTargetType": "region",
            "fromTargetId": "region-seoul-jongno",
            "toTargetType": "complex",
            "toTargetId": registry.targets[0]["targetId"],
            "edgeType": "contains",
            "confidence": 0.74,
            "source": "molit:market-fact",
            "reviewState": "approved",
        }
    ]


def test_build_complex_registry_generates_compound_brand_short_aliases_for_community_matching():
    ingested_at = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
    fact = RealEstateMarketFact(
        fact_type="apt_trade",
        provider="molit",
        provider_dataset="molit_apt_trade",
        provider_object_id="molit_apt_trade:11440:202606:trade-1",
        legal_dong_code="11440",
        observed_at=date(2026, 6, 3),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "마포 래미안 푸르지오",
            "legalDongName": "아현동",
            "jibun": "777",
            "builtYear": 2014,
        },
    )

    registry = build_real_estate_complex_registry_from_market_facts(
        [fact],
        region_targets_by_lawd_code={"11440": "region-seoul-mapo"},
    )

    aliases = {
        alias["alias"]: alias
        for alias in registry.aliases
    }
    assert aliases["마래푸"] == {
        "targetType": "complex",
        "targetId": registry.targets[0]["targetId"],
        "alias": "마래푸",
        "aliasType": "short_name",
        "source": "molit:market-fact",
        "evidenceUrl": None,
        "confidence": 0.68,
        "reviewState": "approved",
        "createdBy": "system",
        "ambiguous": False,
    }
    assert aliases["아현동 마래푸"]["aliasType"] == "nearby_short_name"


def test_build_complex_registry_generates_short_alias_for_compact_brand_names():
    ingested_at = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
    fact = RealEstateMarketFact(
        fact_type="apt_trade",
        provider="molit",
        provider_dataset="molit_apt_trade",
        provider_object_id="molit_apt_trade:11440:202606:trade-compact",
        legal_dong_code="11440",
        observed_at=date(2026, 6, 3),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "마포래미안푸르지오",
            "legalDongName": "아현동",
            "jibun": "777",
            "builtYear": 2014,
        },
    )

    registry = build_real_estate_complex_registry_from_market_facts(
        [fact],
        region_targets_by_lawd_code={"11440": "region-seoul-mapo"},
    )

    aliases = {alias["alias"]: alias for alias in registry.aliases}
    assert aliases["마래푸"] == {
        "targetType": "complex",
        "targetId": registry.targets[0]["targetId"],
        "alias": "마래푸",
        "aliasType": "short_name",
        "source": "molit:market-fact",
        "evidenceUrl": None,
        "confidence": 0.68,
        "reviewState": "approved",
        "createdBy": "system",
        "ambiguous": False,
    }
    assert aliases["아현동 마래푸"]["aliasType"] == "nearby_short_name"


def test_build_complex_registry_generates_nearby_core_alias_for_compact_brand_names():
    ingested_at = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
    fact = RealEstateMarketFact(
        fact_type="apt_trade",
        provider="molit",
        provider_dataset="molit_apt_trade",
        provider_object_id="molit_apt_trade:11440:202606:trade-compact-core",
        legal_dong_code="11440",
        observed_at=date(2026, 6, 3),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "마포래미안푸르지오",
            "legalDongName": "아현동",
            "jibun": "778",
            "builtYear": 2014,
        },
    )

    registry = build_real_estate_complex_registry_from_market_facts(
        [fact],
        region_targets_by_lawd_code={"11440": "region-seoul-mapo"},
    )

    aliases = {alias["alias"]: alias for alias in registry.aliases}
    assert aliases["아현동 래미안 푸르지오"] == {
        "targetType": "complex",
        "targetId": registry.targets[0]["targetId"],
        "alias": "아현동 래미안 푸르지오",
        "aliasType": "nearby_core_name",
        "source": "molit:market-fact",
        "evidenceUrl": None,
        "confidence": 0.66,
        "reviewState": "approved",
        "createdBy": "system",
        "ambiguous": False,
    }


def test_build_complex_registry_generates_nearby_core_alias_for_location_prefixed_names():
    ingested_at = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
    fact = RealEstateMarketFact(
        fact_type="apt_trade",
        provider="molit",
        provider_dataset="molit_apt_trade",
        provider_object_id="molit_apt_trade:11440:202606:trade-2",
        legal_dong_code="11440",
        observed_at=date(2026, 6, 4),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "마포 래미안 푸르지오",
            "legalDongName": "아현동",
            "jibun": "888",
            "builtYear": 2014,
        },
    )

    registry = build_real_estate_complex_registry_from_market_facts(
        [fact],
        region_targets_by_lawd_code={"11440": "region-seoul-mapo"},
    )

    aliases = {alias["alias"]: alias for alias in registry.aliases}
    assert aliases["아현동 래미안 푸르지오"] == {
        "targetType": "complex",
        "targetId": registry.targets[0]["targetId"],
        "alias": "아현동 래미안 푸르지오",
        "aliasType": "nearby_core_name",
        "source": "molit:market-fact",
        "evidenceUrl": None,
        "confidence": 0.66,
        "reviewState": "approved",
        "createdBy": "system",
        "ambiguous": False,
    }

def test_build_complex_registry_marks_generic_brand_like_official_alias_as_ambiguous():
    ingested_at = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
    fact = RealEstateMarketFact(
        fact_type="apt_trade",
        provider="molit",
        provider_dataset="molit_apt_trade",
        provider_object_id="molit_apt_trade:11110:202606:trade-generic-brand",
        legal_dong_code="11110",
        observed_at=date(2026, 6, 3),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "삼성",
            "legalDongName": "무악동",
            "jibun": "1",
        },
    )

    registry = build_real_estate_complex_registry_from_market_facts(
        [fact],
        region_targets_by_lawd_code={"11110": "region-seoul-jongno"},
    )

    aliases = {alias["alias"]: alias for alias in registry.aliases}
    assert aliases["삼성"]["ambiguous"] is True
    assert aliases["삼성"]["reviewState"] == "candidate"
    assert aliases["무악동 삼성"]["ambiguous"] is False
    assert aliases["무악동 삼성"]["reviewState"] == "approved"


def test_build_complex_registry_marks_broad_region_name_official_alias_as_ambiguous():
    ingested_at = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
    fact = RealEstateMarketFact(
        fact_type="apt_trade",
        provider="molit",
        provider_dataset="molit_apt_trade",
        provider_object_id="molit_apt_trade:11110:202606:trade-region-name",
        legal_dong_code="11110",
        observed_at=date(2026, 6, 3),
        as_of=date(2026, 6, 1),
        ingested_at=ingested_at,
        value_json={
            "apartmentName": "세종",
            "legalDongName": "당주동",
            "jibun": "2",
        },
    )

    registry = build_real_estate_complex_registry_from_market_facts(
        [fact],
        region_targets_by_lawd_code={"11110": "region-seoul-jongno"},
    )

    aliases = {alias["alias"]: alias for alias in registry.aliases}
    assert aliases["세종"]["ambiguous"] is True
    assert aliases["세종"]["reviewState"] == "candidate"
    assert aliases["당주동 세종"]["ambiguous"] is False
    assert aliases["당주동 세종"]["reviewState"] == "approved"

