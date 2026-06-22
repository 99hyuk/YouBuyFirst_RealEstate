from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_matcher import (
    RealEstateAliasRule,
    RealEstatePostForMatching,
    RealEstateTargetMatcher,
    build_real_estate_alias_coverage_report,
    load_real_estate_alias_rules,
    load_real_estate_posts_for_matching,
    suggest_real_estate_alias_candidates,
)


def test_real_estate_target_matcher_matches_approved_aliases_and_prefers_title_source():
    matcher = RealEstateTargetMatcher(
        [
            RealEstateAliasRule(
                target_type="region",
                target_id="region-daejeon",
                alias="대전",
                alias_type="official",
                review_state="approved",
                confidence=0.95,
            ),
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-dunsan-xi",
                alias="둔산자이",
                alias_type="short_name",
                review_state="approved",
                confidence=0.87,
            ),
        ]
    )
    post = RealEstatePostForMatching(
        source="PPOMPPU:house",
        external_id="post-1",
        published_at=datetime(2026, 6, 11, 0, 10, tzinfo=timezone.utc),
        title="둔산자이랑 대전 서구 이야기 많네요",
        content_snippet="대전 쪽 교통 호재 언급이 계속 늘고 있습니다.",
        url="https://example.test/post-1",
    )

    result = matcher.match_post(post)

    assert result.to_dict() == {
        "source": "PPOMPPU:house",
        "externalId": "post-1",
        "publishedAt": "2026-06-11T00:10:00Z",
        "url": "https://example.test/post-1",
        "title": "둔산자이랑 대전 서구 이야기 많네요",
        "contentSnippet": "대전 쪽 교통 호재 언급이 계속 늘고 있습니다.",
        "matched": True,
        "mentions": [
            {
                "targetType": "complex",
                "targetId": "complex-dunsan-xi",
                "matchedText": "둔산자이",
                "matchSource": "title",
                "confidence": 0.87,
                "reviewState": "approved",
                "aliasType": "short_name",
            },
            {
                "targetType": "region",
                "targetId": "region-daejeon",
                "matchedText": "대전",
                "matchSource": "title",
                "confidence": 0.95,
                "reviewState": "approved",
                "aliasType": "official",
            },
        ],
    }


def test_real_estate_target_matcher_excludes_unapproved_ambiguous_and_single_character_aliases():
    matcher = RealEstateTargetMatcher(
        [
            RealEstateAliasRule(
                target_type="region",
                target_id="region-seoul",
                alias="서울",
                review_state="candidate",
                confidence=0.5,
            ),
            RealEstateAliasRule(
                target_type="region",
                target_id="region-jungang",
                alias="중앙",
                review_state="approved",
                confidence=0.7,
                ambiguous=True,
            ),
            RealEstateAliasRule(
                target_type="region",
                target_id="region-busan",
                alias="부",
                review_state="approved",
                confidence=0.9,
            ),
            RealEstateAliasRule(
                target_type="region",
                target_id="region-gangwon",
                alias="강원",
                review_state="approved",
                confidence=0.91,
            ),
        ]
    )
    post = RealEstatePostForMatching(
        source="DCINSIDE:immovables",
        external_id="post-2",
        published_at=datetime(2026, 6, 11, 0, 15, tzinfo=timezone.utc),
        title="서울 중앙 부 강원 모두 언급된 글",
        content_snippet="검수 전 별칭은 지표에 섞이면 안 됩니다.",
    )

    result = matcher.match_post(post)

    assert [mention.target_id for mention in result.mentions] == ["region-gangwon"]


def test_real_estate_target_matcher_matches_spacing_and_punctuation_variants():
    matcher = RealEstateTargetMatcher(
        [
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-maraepu",
                alias="마래푸",
                alias_type="community_slang",
                review_state="approved",
                confidence=0.88,
            )
        ]
    )
    post = RealEstatePostForMatching(
        source="PPOMPPU:house",
        external_id="post-slang-1",
        published_at=datetime(2026, 6, 11, 0, 30, tzinfo=timezone.utc),
        title="마 래-푸 전세 불안 얘기 다시 많아짐",
        content_snippet="마포 래미안 푸르지오라고 길게 안 쓰고 다들 저렇게 부름",
    )

    result = matcher.match_post(post)

    assert result.mentions[0].to_dict() == {
        "targetType": "complex",
        "targetId": "complex-maraepu",
        "matchedText": "마 래-푸",
        "matchSource": "title",
        "confidence": 0.88,
        "reviewState": "approved",
        "aliasType": "community_slang",
    }


def test_real_estate_target_matcher_counts_same_complex_once_across_aliases_and_sources():
    matcher = RealEstateTargetMatcher(
        [
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-maraepu",
                alias="마포 래미안 푸르지오",
                alias_type="official",
                review_state="approved",
                confidence=0.92,
            ),
            RealEstateAliasRule(
                target_type="complex",
                target_id="complex-maraepu",
                alias="마래푸",
                alias_type="short_name",
                review_state="approved",
                confidence=0.68,
            ),
        ]
    )
    post = RealEstatePostForMatching(
        source="PPOMPPU:house",
        external_id="post-maraepu-duplicate",
        published_at=datetime(2026, 6, 14, 0, 20, tzinfo=timezone.utc),
        title="마래푸 전세 불안 얘기 다시 늘었네요",
        content_snippet="마포 래미안 푸르지오라고 안 쓰고 다들 마래푸로 부르는 분위기",
    )

    result = matcher.match_post(post)

    assert [mention.to_dict() for mention in result.mentions] == [
        {
            "targetType": "complex",
            "targetId": "complex-maraepu",
            "matchedText": "마래푸",
            "matchSource": "title",
            "confidence": 0.68,
            "reviewState": "approved",
            "aliasType": "short_name",
        }
    ]


def test_load_real_estate_alias_rules_and_posts_from_jsonl(tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        "\n".join(
            [
                '{"targetType":"region","targetId":"region-daejeon","alias":"대전","aliasType":"official","reviewState":"approved","confidence":0.95}',
                '{"targetType":"complex","targetId":"complex-dunsan-xi","alias":"둔산자이","reviewState":"approved"}',
            ]
        ),
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"post-1","publishedAt":"2026-06-11T00:10:00Z","title":"대전 둔산자이","contentSnippet":"교통 이야기","url":"https://example.test/post-1"}',
        encoding="utf-8",
    )

    aliases = load_real_estate_alias_rules(aliases_path)
    posts = load_real_estate_posts_for_matching(posts_path)

    assert aliases[0] == RealEstateAliasRule(
        target_type="region",
        target_id="region-daejeon",
        alias="대전",
        alias_type="official",
        review_state="approved",
        confidence=0.95,
    )
    assert posts == [
        RealEstatePostForMatching(
            source="PPOMPPU:house",
            external_id="post-1",
            published_at=datetime(2026, 6, 11, 0, 10, tzinfo=timezone.utc),
            title="대전 둔산자이",
            content_snippet="교통 이야기",
            url="https://example.test/post-1",
        )
    ]


def test_suggest_real_estate_alias_candidates_from_parenthesized_slang_near_known_alias():
    aliases = [
        RealEstateAliasRule(
            target_type="complex",
            target_id="complex-mrp",
            alias="Mapo Raemian Prugio",
            alias_type="official",
            review_state="approved",
            confidence=0.96,
        )
    ]
    posts = [
        RealEstatePostForMatching(
            source="PPOMPPU:house",
            external_id="post-mrp-1",
            published_at=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
            title="Mapo Raemian Prugio(MRP) rent anxiety",
            content_snippet="people keep calling MRP a bellwether",
            url="https://example.test/post-mrp-1",
        ),
        RealEstatePostForMatching(
            source="DCINSIDE:immovables",
            external_id="post-mrp-2",
            published_at=datetime(2026, 6, 13, 1, 5, tzinfo=timezone.utc),
            title="Mapo Raemian Prugio (MRP) supply debate",
            content_snippet="same slang repeated",
            url="https://example.test/post-mrp-2",
        ),
    ]

    candidates = suggest_real_estate_alias_candidates(posts, aliases)

    assert [candidate.to_request_dict() for candidate in candidates] == [
        {
            "targetType": "complex",
            "targetId": "complex-mrp",
            "alias": "MRP",
            "aliasType": "community_slang",
            "source": "community:auto-candidate:PPOMPPU:house",
            "evidenceUrl": "https://example.test/post-mrp-1",
            "confidence": 0.62,
            "reviewState": "candidate",
            "createdBy": "system",
            "ambiguous": False,
        }
    ]


def test_suggest_real_estate_alias_candidates_ignores_existing_approved_aliases():
    aliases = [
        RealEstateAliasRule(
            target_type="complex",
            target_id="complex-mrp",
            alias="Mapo Raemian Prugio",
            review_state="approved",
        ),
        RealEstateAliasRule(
            target_type="complex",
            target_id="complex-mrp",
            alias="MRP",
            alias_type="community_slang",
            review_state="approved",
        ),
    ]
    posts = [
        RealEstatePostForMatching(
            source="PPOMPPU:house",
            external_id="post-mrp-1",
            published_at=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
            title="Mapo Raemian Prugio(MRP) rent anxiety",
            content_snippet="already known slang",
        )
    ]

    assert suggest_real_estate_alias_candidates(posts, aliases) == []


def test_build_real_estate_alias_coverage_report_groups_match_quality_by_source():
    aliases = [
        RealEstateAliasRule(
            target_type="region",
            target_id="region-daejeon",
            alias="Daejeon",
            alias_type="official",
            review_state="approved",
            confidence=0.95,
        ),
        RealEstateAliasRule(
            target_type="complex",
            target_id="complex-mrp",
            alias="Mapo Raemian Prugio",
            alias_type="official",
            review_state="approved",
            confidence=0.96,
        ),
    ]
    posts = [
        RealEstatePostForMatching(
            source="PPOMPPU:house",
            external_id="post-1",
            published_at=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
            title="Daejeon traffic and rent anxiety",
            content_snippet="Daejeon keeps getting mentioned",
            url="https://example.test/post-1",
        ),
        RealEstatePostForMatching(
            source="PPOMPPU:house",
            external_id="post-2",
            published_at=datetime(2026, 6, 13, 1, 5, tzinfo=timezone.utc),
            title="Unknown neighborhood discussion",
            content_snippet="people are using a nickname we do not know yet",
            url="https://example.test/post-2",
        ),
        RealEstatePostForMatching(
            source="DCINSIDE:immovables",
            external_id="post-3",
            published_at=datetime(2026, 6, 13, 1, 10, tzinfo=timezone.utc),
            title="Mapo Raemian Prugio(MRP) rent anxiety",
            content_snippet="MRP is used as slang in comments",
            url="https://example.test/post-3",
        ),
    ]

    report = build_real_estate_alias_coverage_report(posts, aliases)

    assert report["totals"] == {
        "sourceCount": 2,
        "postCount": 3,
        "matchedPostCount": 2,
        "unmatchedPostCount": 1,
        "matchRate": 0.6667,
        "mentionCount": 2,
        "targetCount": 2,
        "candidateAliasCount": 1,
    }
    assert report["sources"][0]["source"] == "DCINSIDE:immovables"
    assert report["sources"][0]["matchRate"] == 1.0
    assert report["sources"][0]["candidateAliasCount"] == 1
    assert report["sources"][0]["candidateAliases"][0]["alias"] == "MRP"
    assert report["sources"][1]["source"] == "PPOMPPU:house"
    assert report["sources"][1]["matchRate"] == 0.5
    assert report["sources"][1]["topTargets"] == [
        {
            "targetType": "region",
            "targetId": "region-daejeon",
            "mentionCount": 1,
            "aliasTypes": ["official"],
            "matchedTexts": ["Daejeon"],
        }
    ]
    assert report["sources"][1]["unmatchedExamples"] == [
        {
            "externalId": "post-2",
            "publishedAt": "2026-06-13T01:05:00Z",
            "title": "Unknown neighborhood discussion",
            "url": "https://example.test/post-2",
        }
    ]
