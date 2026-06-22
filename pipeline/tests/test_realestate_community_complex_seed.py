from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_community_complex_seed import (
    CommunityComplexSeed,
    build_observed_community_complex_seed_registry,
)
from youbuyfirst_pipeline.realestate_matcher import RealEstatePostForMatching


def test_build_observed_community_complex_seed_registry_only_publishes_observed_complexes():
    registry = build_observed_community_complex_seed_registry(
        [
            RealEstatePostForMatching(
                source="DCINSIDE",
                external_id="post-1",
                published_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
                title="서울 거래량 순위 1위 헬리오시티 2위 리센츠",
                content_snippet="",
                url="https://example.test/post-1",
            ),
            RealEstatePostForMatching(
                source="PPOMPPU",
                external_id="post-2",
                published_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
                title="동탄역 롯데캐슬 신고가 얘기 많네요",
                content_snippet="",
                url="https://example.test/post-2",
            ),
        ]
    )

    assert [target["targetId"] for target in registry.targets] == [
        "complex-community-dongtan-lotte-castle",
        "complex-community-helio-city",
        "complex-community-ricenz",
    ]
    assert registry.observed_target_ids == (
        "complex-community-dongtan-lotte-castle",
        "complex-community-helio-city",
        "complex-community-ricenz",
    )
    assert {target["dataStatus"] for target in registry.targets} == {"community_observed"}
    assert {complex_row["coordinateProvider"] for complex_row in registry.complexes} == {"kakao_local_search:keyword"}
    assert {complex_row["coordinateStatus"] for complex_row in registry.complexes} == {"candidate"}
    assert all(complex_row["latitude"] is not None for complex_row in registry.complexes)
    assert all(complex_row["longitude"] is not None for complex_row in registry.complexes)
    assert {alias["reviewState"] for alias in registry.aliases} == {"approved"}
    assert {alias["ambiguous"] for alias in registry.aliases} == {False}
    assert {
        (edge["fromTargetId"], edge["toTargetId"])
        for edge in registry.edges
    } == {
        ("region-gyeonggi-hwaseongsi", "complex-community-dongtan-lotte-castle"),
        ("region-seoul-songpa", "complex-community-helio-city"),
        ("region-seoul-songpa", "complex-community-ricenz"),
    }


def test_build_observed_community_complex_seed_registry_ignores_generic_brand_mentions():
    registry = build_observed_community_complex_seed_registry(
        [
            RealEstatePostForMatching(
                source="DCINSIDE",
                external_id="post-1",
                published_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
                title="반포 래미안이랑 자이 브랜드 아파트 얘기",
                content_snippet="정확한 단지명 없이 브랜드만 언급됨",
                url="https://example.test/post-1",
            ),
        ]
    )

    assert registry.targets == []
    assert registry.aliases == []
    assert registry.edges == []


def test_build_observed_community_complex_seed_registry_reuses_existing_official_complex_target():
    seed = CommunityComplexSeed(
        target_id="complex-community-mrp",
        display_name="Mapo Raemian Prugio",
        slug="community-mrp",
        region_target_id="region-seoul-mapo",
        aliases=("Mapo Raemian Prugio", "MRP"),
        legal_dong_code="11440",
        address_hint="Seoul Mapo Ahyeon",
    )
    registry = build_observed_community_complex_seed_registry(
        [
            RealEstatePostForMatching(
                source="PPOMPPU",
                external_id="post-mrp-1",
                published_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
                title="MRP rent anxiety",
                content_snippet="Mapo buyers mention MRP again",
                url="https://example.test/post-mrp-1",
            ),
        ],
        seeds=[seed],
        existing_aliases=[
            {
                "targetType": "complex",
                "targetId": "complex-molit-mrp",
                "alias": "Mapo Raemian Prugio",
                "aliasType": "official",
                "reviewState": "approved",
                "confidence": 0.96,
                "ambiguous": False,
            }
        ],
    )

    assert registry.targets == []
    assert registry.complexes == []
    assert registry.edges == []
    assert registry.observed_target_ids == ("complex-molit-mrp",)
    assert registry.aliases == [
        {
            "targetType": "complex",
            "targetId": "complex-molit-mrp",
            "alias": "MRP",
            "aliasType": "community_alias",
            "source": "community:observed-complex-seed",
            "evidenceUrl": None,
            "confidence": 0.74,
            "reviewState": "approved",
            "createdBy": "system",
            "ambiguous": False,
        }
    ]


def test_build_observed_community_complex_seed_registry_updates_existing_seed_complex_coordinates():
    seed = CommunityComplexSeed(
        target_id="complex-community-mrp",
        display_name="Mapo Raemian Prugio",
        slug="community-mrp",
        region_target_id="region-seoul-mapo",
        aliases=("Mapo Raemian Prugio", "MRP"),
        legal_dong_code="11440",
        address_hint="Seoul Mapo Ahyeon",
        latitude=37.5536,
        longitude=126.9564,
        coordinate_provider="kakao_local_search:keyword",
        coordinate_as_of="2026-06-16T00:00:00Z",
    )
    registry = build_observed_community_complex_seed_registry(
        [
            RealEstatePostForMatching(
                source="PPOMPPU",
                external_id="post-mrp-1",
                published_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
                title="MRP rent anxiety",
                content_snippet="Mapo buyers mention MRP again",
                url="https://example.test/post-mrp-1",
            ),
        ],
        seeds=[seed],
        existing_aliases=[
            {
                "targetType": "complex",
                "targetId": "complex-community-mrp",
                "alias": "Mapo Raemian Prugio",
                "aliasType": "community_observed",
                "reviewState": "approved",
                "confidence": 0.96,
                "ambiguous": False,
            }
        ],
    )

    assert registry.targets == []
    assert registry.complexes == [
        {
            "targetId": "complex-community-mrp",
            "regionTargetId": "region-seoul-mapo",
            "legalDongCode": "11440",
            "roadAddress": None,
            "jibunAddress": "Seoul Mapo Ahyeon",
            "normalizedAddress": "seoulmapoahyeonmaporaemianprugio",
            "builtYear": None,
            "householdCount": None,
            "source": "community:observed-complex-seed",
            "latitude": 37.5536,
            "longitude": 126.9564,
            "coordinateProvider": "kakao_local_search:keyword",
            "coordinateAsOf": "2026-06-16T00:00:00Z",
            "coordinateStatus": "candidate",
            "markerTone": "flat",
            "priceSummary": "확인 필요",
            "changeLabel": "unknown",
            "reactionSummary": "반응 지표 연결 전",
            "markerNote": "커뮤니티에서 관측된 단지 후보입니다. 좌표는 지도 표시용 후보값이며 시장 fact 검증이 필요합니다.",
            "markerDataStatus": "community_observed",
            "markerStale": True,
        }
    ]
    assert registry.edges == []
    assert registry.observed_target_ids == ("complex-community-mrp",)


def test_build_observed_community_complex_seed_registry_extracts_structured_trade_table_complexes():
    registry = build_observed_community_complex_seed_registry(
        [
            {
                "source": "PPOMPPU",
                "externalId": "trade-table-1",
                "publishedAt": "2026-06-16T00:00:00Z",
                "title": "weekly apartment trade list",
                "contentSnippet": (
                    "서울특별시강서구 최근 등록된 아파트 매매 5건 "
                    "아파트이름 동이름 전용면적 층 가격 날짜 "
                    "대림e편한세상 서울특별시강서구 화곡동 110.26 10 82,000 2026/6/11 "
                    "우장산숲아이파크 서울특별시강서구 화곡동 59.9983 4 134,500 2026/6/9"
                ),
                "url": "https://example.test/trade-table-1",
            }
        ],
        existing_aliases=[
            {
                "targetType": "region",
                "targetId": "region-seoul-gangseo",
                "alias": "서울특별시강서구",
                "aliasType": "official",
                "reviewState": "approved",
                "confidence": 0.98,
                "ambiguous": False,
            }
        ],
    )

    assert {target["displayName"] for target in registry.targets} == {
        "대림e편한세상",
        "우장산숲아이파크",
    }
    assert {complex_row["regionTargetId"] for complex_row in registry.complexes} == {"region-seoul-gangseo"}
    assert {
        (alias["alias"], alias["aliasType"], alias["reviewState"])
        for alias in registry.aliases
    } == {
        ("대림e편한세상", "community_observed_trade_table", "candidate"),
        ("우장산숲아이파크", "community_observed_trade_table", "candidate"),
    }
    assert {
        (edge["fromTargetId"], edge["toTargetId"], edge["reviewState"])
        for edge in registry.edges
    } == {
        ("region-seoul-gangseo", target["targetId"], "candidate")
        for target in registry.targets
    }


def test_build_observed_community_complex_seed_registry_ignores_generic_trade_table_names():
    registry = build_observed_community_complex_seed_registry(
        [
            {
                "source": "PPOMPPU",
                "externalId": "trade-table-generic",
                "publishedAt": "2026-06-16T00:00:00Z",
                "title": "weekly apartment trade list",
                "contentSnippet": (
                    "SeoulGangseo recent apartment trades "
                    "Apartment Region Dong Area Floor Price Date "
                    "1단지 SeoulGangseo Hwagokdong 59.99 4 134500 2026/6/9 "
                    "푸르지오 SeoulGangseo Hwagokdong 84.11 9 120000 2026/6/9 "
                    "우장산숲아이파크 SeoulGangseo Hwagokdong 59.99 4 134500 2026/6/9"
                ),
                "url": "https://example.test/trade-table-generic",
            }
        ],
        existing_aliases=[
            {
                "targetType": "region",
                "targetId": "region-seoul-gangseo",
                "alias": "SeoulGangseo",
                "aliasType": "official",
                "reviewState": "approved",
                "confidence": 0.98,
                "ambiguous": False,
            }
        ],
    )

    assert {target["displayName"] for target in registry.targets} == {"우장산숲아이파크"}
