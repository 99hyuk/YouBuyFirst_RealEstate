from youbuyfirst_pipeline.matcher import InstrumentMatcher
from youbuyfirst_pipeline.models import Instrument, InstrumentAliasRule


def test_matches_korean_aliases_and_us_tickers_without_duplicates():
    matcher = InstrumentMatcher(
        [
            Instrument(market="KR", symbol="005930", name="삼성전자", aliases=["삼전"]),
            Instrument(market="US", symbol="TSLA", name="Tesla", aliases=["테슬라"]),
            Instrument(market="US", symbol="NVDA", name="NVIDIA", aliases=["엔비디아", "엔비"]),
        ]
    )

    mentions = matcher.match("삼전은 쉬고 TSLA랑 엔비디아, NVDA는 강하다. 테슬라도 언급됨")

    assert {(m.market, m.symbol, m.matched_text) for m in mentions} == {
        ("KR", "005930", "삼전"),
        ("US", "TSLA", "TSLA"),
        ("US", "TSLA", "테슬라"),
        ("US", "NVDA", "엔비디아"),
        ("US", "NVDA", "NVDA"),
    }


def test_matches_short_alias_when_it_appears_again_outside_long_alias():
    matcher = InstrumentMatcher(
        [
            Instrument(market="US", symbol="NVDA", name="NVIDIA", aliases=["엔비디아", "엔비"]),
        ]
    )

    mentions = matcher.match("엔비디아는 강하고 엔비도 같이 언급됨")

    assert [(m.market, m.symbol, m.matched_text) for m in mentions] == [
        ("US", "NVDA", "엔비디아"),
        ("US", "NVDA", "엔비"),
    ]


def test_ascii_tickers_require_token_boundaries():
    matcher = InstrumentMatcher(
        [
            Instrument(market="US", symbol="TSLA", name="Tesla", aliases=["테슬라"]),
        ]
    )

    mentions = matcher.match("TSLAX와 myTSLAwatch는 제외하고 tsla는 언급")

    assert [(m.market, m.symbol, m.matched_text) for m in mentions] == [
        ("US", "TSLA", "TSLA"),
    ]


def test_review_aliases_are_candidates_not_confirmed_mentions():
    matcher = InstrumentMatcher(
        [
            Instrument(market="US", symbol="TSLA", name="Tesla", aliases=["테슬라"]),
        ],
        review_aliases=[
            InstrumentAliasRule(
                market="US",
                symbol="TSLA",
                alias="슬라",
                status="REVIEW",
                confidence=0.45,
                ambiguous=False,
                source="community-seed",
            )
        ],
    )

    text = "슬라 실적 기대감 때문에 오늘 게시판에서 계속 언급됨"

    assert matcher.match(text) == []
    candidates = matcher.alias_candidates(text)
    assert [(candidate.alias, candidate.suggested_market, candidate.suggested_symbol, candidate.reason) for candidate in candidates] == [
        ("슬라", "US", "TSLA", "review-alias")
    ]


def test_blocked_aliases_are_not_candidates_even_when_ambiguous():
    matcher = InstrumentMatcher(
        [
            Instrument(market="US", symbol="AAPL", name="Apple", aliases=["애플"]),
        ],
        review_aliases=[
            InstrumentAliasRule(
                market="US",
                symbol="AAPL",
                alias="사과",
                status="BLOCKED",
                confidence=0.2,
                ambiguous=True,
                source="seed",
            )
        ],
    )

    assert [(mention.market, mention.symbol, mention.matched_text) for mention in matcher.match("사과 먹고 애플은 관망")] == [
        ("US", "AAPL", "애플")
    ]
    assert matcher.alias_candidates("사과 먹고 애플은 관망") == []
