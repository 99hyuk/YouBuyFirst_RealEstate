from pathlib import Path

from youbuyfirst_pipeline.realestate_regions import parse_molit_legal_dong_code_csv


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
