from pathlib import Path

from youbuyfirst_pipeline.realestate_regions import (
    build_real_estate_region_alias_requests,
    parse_molit_legal_dong_code_csv,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "realestate"


def test_parse_molit_legal_dong_code_csv_keeps_active_regions_and_builds_hierarchy():
    csv_text = (FIXTURE_DIR / "molit_legal_dong_codes_sample.csv").read_text(encoding="utf-8")

    regions = parse_molit_legal_dong_code_csv(csv_text)

    assert [region.to_import_dict() for region in regions] == [
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
        {
            "targetId": "region-2635010100",
            "displayName": "부산광역시 해운대구 우동",
            "slug": "region-2635010100",
            "regionLevel": "eupmyeondong",
            "parentTargetId": "region-26350",
            "legalDongCode": "2635010100",
            "regionCode": "2635010100",
            "source": "import:molit-legal-dong-code",
        },
    ]


def test_build_real_estate_region_alias_requests_promotes_specific_child_regions():
    aliases = build_real_estate_region_alias_requests(
        [
            {
                "targetId": "region-gyeonggi-paju",
                "displayName": "경기도 파주시",
                "regionLevel": "sigungu",
            },
            {
                "targetId": "region-seoul-gwangjin-guui",
                "displayName": "서울특별시 광진구 구의동",
                "regionLevel": "eupmyeondong",
            },
        ]
    )

    alias_by_target = {
        (alias["targetId"], alias["alias"]): alias
        for alias in aliases
    }

    assert alias_by_target[("region-gyeonggi-paju", "경기도 파주시")]["reviewState"] == "approved"
    assert alias_by_target[("region-gyeonggi-paju", "경기 파주시")]["reviewState"] == "approved"
    assert alias_by_target[("region-gyeonggi-paju", "파주시")]["reviewState"] == "approved"
    assert alias_by_target[("region-gyeonggi-paju", "파주")]["reviewState"] == "approved"
    assert alias_by_target[("region-seoul-gwangjin-guui", "서울특별시 광진구 구의동")]["reviewState"] == "approved"
    assert alias_by_target[("region-seoul-gwangjin-guui", "광진구 구의동")]["reviewState"] == "approved"
    assert alias_by_target[("region-seoul-gwangjin-guui", "구의동")]["reviewState"] == "approved"


def test_build_real_estate_region_alias_requests_marks_duplicate_terminal_aliases_ambiguous():
    aliases = build_real_estate_region_alias_requests(
        [
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
    )

    terminal_aliases = [
        alias
        for alias in aliases
        if alias["alias"] == "중구"
    ]
    contextual_aliases = {
        alias["alias"]: alias
        for alias in aliases
        if alias["alias"] in {"서울 중구", "부산 중구"}
    }

    assert len(terminal_aliases) == 2
    assert {alias["reviewState"] for alias in terminal_aliases} == {"candidate"}
    assert {alias["ambiguous"] for alias in terminal_aliases} == {True}
    assert contextual_aliases["서울 중구"]["reviewState"] == "approved"
    assert contextual_aliases["부산 중구"]["reviewState"] == "approved"
