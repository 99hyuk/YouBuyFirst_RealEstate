from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_matcher import (
    RealEstateMatchedPost,
    RealEstateTargetMention,
)
from youbuyfirst_pipeline.realestate_reaction_classifier import (
    RuleBasedRealEstateReactionClassifier,
    classify_real_estate_reaction_observations,
    load_real_estate_matched_posts,
)


def test_rule_based_classifier_turns_matched_posts_into_reaction_observations():
    post = RealEstateMatchedPost(
        source="PPOMPPU:house",
        external_id="post-1",
        published_at=datetime(2026, 6, 11, 0, 10, tzinfo=timezone.utc),
        url="https://example.test/post-1",
        title="둔산자이 GTX 호재 기대감이 큽니다",
        content_snippet="대전 교통 개선 이야기와 역세권 기대가 계속 나옵니다.",
        mentions=[
            RealEstateTargetMention(
                target_type="complex",
                target_id="complex-dunsan-xi",
                matched_text="둔산자이",
                match_source="title",
                confidence=0.87,
                review_state="approved",
                alias_type="short_name",
            )
        ],
    )

    observations = classify_real_estate_reaction_observations(
        [post],
        classifier=RuleBasedRealEstateReactionClassifier(),
    )

    assert len(observations) == 1
    observation = observations[0]
    assert observation.target_type == "complex"
    assert observation.target_id == "complex-dunsan-xi"
    assert observation.source == "PPOMPPU:house"
    assert observation.external_id == "post-1"
    assert observation.matched_text == "둔산자이"
    assert observation.reaction_direction == "expectation"
    assert observation.confidence == 0.73
    assert observation.issues == [
        {
            "issueKey": "transport",
            "label": "교통",
            "direction": "expectation",
            "summary": "교통 호재와 접근성 기대가 함께 언급됨",
            "confidence": 0.78,
        }
    ]


def test_rule_based_classifier_detects_concern_issues_and_keeps_neutral_when_signal_is_weak():
    posts = [
        RealEstateMatchedPost(
            source="DCINSIDE:immovables",
            external_id="post-2",
            published_at=datetime(2026, 6, 11, 0, 20, tzinfo=timezone.utc),
            url=None,
            title="서울 전세 불안이랑 대출 부담 얘기",
            content_snippet="금리 때문에 매수 부담이 크다는 반응이 많습니다.",
            mentions=[
                RealEstateTargetMention(
                    target_type="region",
                    target_id="region-seoul",
                    matched_text="서울",
                    match_source="title",
                    confidence=0.95,
                    review_state="approved",
                    alias_type="official",
                )
            ],
        ),
        RealEstateMatchedPost(
            source="PPOMPPU:house",
            external_id="post-3",
            published_at=datetime(2026, 6, 11, 0, 25, tzinfo=timezone.utc),
            url=None,
            title="대전 실거래 공유",
            content_snippet="최근 거래 사례만 정리합니다.",
            mentions=[
                RealEstateTargetMention(
                    target_type="region",
                    target_id="region-daejeon",
                    matched_text="대전",
                    match_source="title",
                    confidence=0.95,
                    review_state="approved",
                    alias_type="official",
                )
            ],
        ),
    ]

    observations = classify_real_estate_reaction_observations(
        posts,
        classifier=RuleBasedRealEstateReactionClassifier(),
    )

    assert [(item.target_id, item.reaction_direction, item.confidence) for item in observations] == [
        ("region-seoul", "concern", 0.79),
        ("region-daejeon", "neutral", 0.55),
    ]
    assert observations[0].issues == [
        {
            "issueKey": "jeonse",
            "label": "전세",
            "direction": "concern",
            "summary": "전세 가격과 보증금 부담 우려가 언급됨",
            "confidence": 0.78,
        },
        {
            "issueKey": "loan_rate",
            "label": "대출·금리",
            "direction": "concern",
            "summary": "대출, 금리, 상환 부담 우려가 언급됨",
            "confidence": 0.78,
        },
    ]
    assert observations[1].issues == []


def test_load_real_estate_matched_posts_reads_target_match_output(tmp_path):
    path = tmp_path / "matches.json"
    path.write_text(
        """
        {
          "items": [
            {
              "source": "PPOMPPU:house",
              "externalId": "post-1",
              "publishedAt": "2026-06-11T00:10:00Z",
              "url": "https://example.test/post-1",
              "title": "둔산자이 GTX 호재",
              "contentSnippet": "대전 교통 기대",
              "matched": true,
              "mentions": [
                {
                  "targetType": "complex",
                  "targetId": "complex-dunsan-xi",
                  "matchedText": "둔산자이",
                  "matchSource": "title",
                  "confidence": 0.87,
                  "reviewState": "approved",
                  "aliasType": "short_name"
                }
              ]
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    posts = load_real_estate_matched_posts(path)

    assert posts[0].title == "둔산자이 GTX 호재"
    assert posts[0].content_snippet == "대전 교통 기대"
    assert posts[0].mentions[0].target_id == "complex-dunsan-xi"
