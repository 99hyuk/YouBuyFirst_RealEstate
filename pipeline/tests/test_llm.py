from youbuyfirst_pipeline.llm import MockLLMProvider
from youbuyfirst_pipeline.models import Mention


def test_mock_llm_resolves_real_stock_mention_with_reaction_direction():
    provider = MockLLMProvider()

    decisions = provider.resolve_mentions(
        title="테슬라 강하다",
        content="TSLA 실적 기대감 때문에 매수세가 붙는 듯",
        mentions=[Mention(market="US", symbol="TSLA", matched_text="테슬라")],
    )

    assert len(decisions) == 1
    assert decisions[0].is_mentioned is True
    assert decisions[0].market == "US"
    assert decisions[0].symbol == "TSLA"
    assert decisions[0].reaction_direction == "bullish"
    assert 0 <= decisions[0].confidence <= 1


def test_mock_llm_rejects_candidate_when_context_is_not_a_stock_mention():
    provider = MockLLMProvider()

    decisions = provider.resolve_mentions(
        title="애플 먹고 싶다",
        content="사과 가격이 너무 비싸서 장보기 힘들다",
        mentions=[Mention(market="US", symbol="AAPL", matched_text="애플")],
    )

    assert len(decisions) == 1
    assert decisions[0].is_mentioned is False
    assert decisions[0].reaction_direction == "neutral"
