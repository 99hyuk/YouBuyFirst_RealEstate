from human_indicator_worker.llm import MockLLMProvider
from human_indicator_worker.models import Mention


def test_mock_llm_returns_structured_sentiment_for_each_mention():
    provider = MockLLMProvider()

    analyses = provider.analyze(
        title="테슬라 강하다",
        content="TSLA 실적 기대감 때문에 매수세가 붙는 듯",
        mentions=[Mention(market="US", symbol="TSLA", matched_text="테슬라")],
    )

    assert len(analyses) == 1
    assert analyses[0].market == "US"
    assert analyses[0].symbol == "TSLA"
    assert analyses[0].sentiment in {"bullish", "bearish", "neutral"}
    assert 0 <= analyses[0].confidence <= 1

