from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_matcher import (
    RealEstateAliasRule,
    RealEstatePostForMatching,
    RealEstateTargetMatcher,
    build_real_estate_alias_coverage_report,
)


def test_matcher_ignores_short_official_complex_aliases_that_pollute_crawl_mentions():
    matcher = RealEstateTargetMatcher(
        [
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-noisy-short-name",
                alias="미래",
                alias_type="official",
                review_state="approved",
            ),
            RealEstateAliasRule(
                target_type="region",
                target_id="region-gyeonggi",
                alias="경기",
                alias_type="short_name",
                review_state="approved",
            ),
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-mrp",
                alias="마래푸",
                alias_type="community_slang",
                review_state="approved",
            ),
        ]
    )
    post = RealEstatePostForMatching(
        source="DCINSIDE",
        external_id="post-1",
        published_at=datetime(2026, 6, 17, 0, 0, tzinfo=timezone.utc),
        title="경기 전세 미래 얘기보다 마래푸 이야기가 많음",
        content_snippet="",
    )

    result = matcher.match_post(post)

    assert [(mention.target_type, mention.target_id, mention.matched_text) for mention in result.mentions] == [
        ("complex", "complex-mrp", "마래푸"),
        ("region", "region-gyeonggi", "경기"),
    ]


def test_matcher_ignores_generic_standalone_complex_brand_aliases():
    matcher = RealEstateTargetMatcher(
        [
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-generic-hillstate",
                alias="힐스테이트",
                alias_type="official",
                review_state="approved",
            ),
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-nonhyeon-hillstate",
                alias="논현동 힐스테이트",
                alias_type="nearby_area",
                review_state="approved",
            ),
        ]
    )

    generic_post = RealEstatePostForMatching(
        source="NAVER_CAFE",
        external_id="post-generic-brand",
        published_at=datetime(2026, 6, 17, 0, 0, tzinfo=timezone.utc),
        title="힐스테이트 브랜드는 전세 글마다 언급되네요",
        content_snippet="",
    )
    specific_post = RealEstatePostForMatching(
        source="NAVER_CAFE",
        external_id="post-specific-complex",
        published_at=datetime(2026, 6, 17, 0, 0, tzinfo=timezone.utc),
        title="논현동 힐스테이트 실거래 이야기",
        content_snippet="",
    )

    assert matcher.match_post(generic_post).mentions == []
    assert [(mention.target_type, mention.target_id, mention.matched_text) for mention in matcher.match_post(specific_post).mentions] == [
        ("complex", "complex-nonhyeon-hillstate", "논현동 힐스테이트"),
    ]


def test_alias_coverage_report_does_not_count_short_official_complex_noise():
    aliases = [
        RealEstateAliasRule(
            target_type="complex",
            target_id="complex-noisy-short-name",
            alias="미래",
            alias_type="official",
            review_state="approved",
        ),
        RealEstateAliasRule(
            target_type="region",
            target_id="region-gyeonggi",
            alias="경기",
            alias_type="short_name",
            review_state="approved",
        ),
    ]
    posts = [
        RealEstatePostForMatching(
            source="DCINSIDE",
            external_id="post-1",
            published_at=datetime(2026, 6, 17, 0, 0, tzinfo=timezone.utc),
            title="경기 침체보다 집값 미래가 문제",
            content_snippet="",
        )
    ]

    report = build_real_estate_alias_coverage_report(posts, aliases)

    assert report["totals"]["mentionCount"] == 1
    assert report["sources"][0]["topTargets"] == [
        {
            "targetType": "region",
            "targetId": "region-gyeonggi",
            "mentionCount": 1,
            "aliasTypes": ["short_name"],
            "matchedTexts": ["경기"],
        }
    ]
